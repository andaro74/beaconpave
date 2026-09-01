"""
entitlement-check over MCP: JSON-RPC messages, no transport opinion.

The second server, and the first that has to answer *"what time is it"*. Everything
structural here is `catalog-search/server.py`'s — same subset (ADR-019), same
`dispatch`-is-the-protocol shape, same two channels for the two kinds of failure.
Read that file for why any of that is the way it is; this docstring covers only
what differs.

**This server authorizes nothing**, exactly as its sibling does not. Authorization
is the tool plane's (G3). Nothing here imports `cedar` or `toolplane`, and a test
pins it.

**The clock is deployment configuration, and it is reported as provenance.**
`entitlement.check` takes `now` as a required parameter with no default, because
`reason: not-yet-started` cannot be computed without an instant and the three
places one could come from are not equivalent:

  - the caller — refused, and this is the important one. `schema.in.json` is
    `additionalProperties: false` over `title_id`, `plan`, `dma`, and the caller is
    the model. A tool that let the model supply the instant it is judged against
    would hand back the decision `schema.out.json` calls *"the tool's, never the
    model's"*.
  - invented here — refused. `ADR-021` widened the parity rule to *"no arm may
    define a second clock"*, and what that rule actually enforces is that anything
    defining `CLOCK` defines the SAME one. So `CLOCK` below is pinned against the
    arms by `tests/test_gateway_run_parity.py`, not exempt from them.
  - deployment configuration — taken. `ADR-023`'s shape one component over: the
    Cedar principal is deployment configuration, never the caller's field.

`serverInfo.clock` reports it for the same reason `serverInfo.catalog` reports the
fixture — a tool whose clock can move silently is an instrument that can move
silently, and a recorded run has to be able to say which instant produced it.

Owning seat: Tool Owner.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import entitlement

#: The registry id, used verbatim as the MCP tool name and the model-facing name.
#: `tests/test_mcp_server.py` pins it against the registry.
TOOL_NAME = "entitlement-check"

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

PROTOCOL_VERSION = "2024-11-05"

#: **The one evaluation clock.** Not a second definition: the parity test asserts
#: every module defining `CLOCK` defines this same value, so this is one more place
#: it is pinned rather than one more clock. A suite whose clock drifted would start
#: failing on its own once the fixture events pass, and the first instinct would be
#: to edit the cases — the one thing the golden set forbids.
CLOCK = "2026-09-13T18:00:00Z"

#: Overridable for the same reason the catalog is: a drill or a replay may need a
#: different instant without a second code path. Deployment configuration, never a
#: request parameter.
CLOCK_ENV = "BEACONPAVE_CLOCK"

CATALOG_ENV = "BEACONPAVE_CATALOG"
CATALOG_CANDIDATES = (HERE / "catalog.json", ROOT / "data" / "catalog.json")

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def clock() -> str:
    """The instant verdicts are computed against.

    Resolved per call rather than at import so a replay can move it without
    reloading the module — the same reason `catalog_path` resolves per call."""
    return os.environ.get(CLOCK_ENV) or CLOCK


def catalog_path() -> pathlib.Path:
    """Bundle copy first, source tree second, and refuse rather than return a path
    that is not there. See `catalog-search/server.py` for what the old ordering
    cost: a deployment fault filed as a contract violation on every case."""
    declared = os.environ.get(CATALOG_ENV)
    if declared:
        path = pathlib.Path(declared)
        if not path.is_file():
            raise FileNotFoundError(
                f"{CATALOG_ENV}={declared!r} does not resolve. This is deployment "
                "configuration, not a request parameter, so a wrong value is a broken "
                "deployment rather than a bad call."
            )
        return path
    for candidate in CATALOG_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"no catalog found. Set {CATALOG_ENV}, or place one at "
        + " or ".join(str(c) for c in CATALOG_CANDIDATES)
    )


def _schema(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def _error(request_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _result(request_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def descriptor() -> dict:
    """The tool as `tools/list` publishes it, read from the committed contract
    rather than restated — a second copy of a schema is a second thing to forget to
    update, and the model would be the one reading the stale one."""
    schema = _schema("schema.in.json")
    return {
        "name": TOOL_NAME,
        "description": schema["description"],
        "inputSchema": {k: v for k, v in schema.items()
                        if k in ("type", "required", "properties", "additionalProperties")},
    }


def dispatch(request: dict) -> dict | None:
    """Handle one JSON-RPC request. Returns `None` for a notification."""
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        request_id = request.get("id") if isinstance(request, dict) else None
        return _error(request_id, INVALID_REQUEST, "expected a JSON-RPC 2.0 request object")

    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params")

    # No id is a notification and takes no response, for every method. An explicit
    # `"id": null` IS a request, so membership is what distinguishes them.
    if "id" not in request:
        return None

    if params is None:
        params = {}
    elif not isinstance(params, dict):
        return _error(request_id, INVALID_PARAMS, "this server takes named params only")

    if method == "initialize":
        try:
            catalog = str(catalog_path().name)
        except OSError as exc:
            return _error(request_id, INTERNAL_ERROR, f"catalog unavailable: {exc}")
        return _result(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": TOOL_NAME, "version": "0.1.0",
                           "catalog": catalog, "clock": clock()},
        })

    if method == "tools/list":
        return _result(request_id, {"tools": [descriptor()]})

    if method == "tools/call":
        name = params.get("name")
        if name != TOOL_NAME:
            return _error(request_id, INVALID_PARAMS, f"this server does not serve {name!r}")
        arguments = params.get("arguments")
        if not isinstance(arguments, dict):
            return _error(request_id, INVALID_PARAMS, "arguments must be an object")

        # The published contract's own `required` list, read rather than retyped.
        # `check` would raise `KeyError` on a missing field, and a KeyError escaping
        # into `isError` names a Python detail where the protocol has a way to say
        # "your call did not match the contract I published". The plane validates
        # first, so reaching here means the transport was addressed directly — the
        # stdio path, or a test — and that is exactly when a clear answer matters.
        missing = [f for f in _schema("schema.in.json")["required"] if f not in arguments]
        if missing:
            return _result(request_id, {
                "content": [{"type": "text",
                             "text": f"{TOOL_NAME} requires {', '.join(missing)}"}],
                "isError": True,
            })

        # A broken deployment and a bad call take different channels: a JSON-RPC
        # `error` says the server could not answer, an `isError` result says the
        # tool answered and the answer is a failure. `handler._call_tool` maps the
        # first to `routing` and the second to `schema`.
        try:
            catalog = entitlement.load_catalog(catalog_path())
        except OSError as exc:
            return _error(request_id, INTERNAL_ERROR, f"catalog unavailable: {exc}")

        try:
            result = entitlement.check(arguments, catalog, clock())
        except (ValueError, TypeError, KeyError) as exc:
            return _result(request_id, {
                "content": [{"type": "text", "text": f"{TOOL_NAME} failed: {exc}"}],
                "isError": True,
            })
        return _result(request_id, {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
            "structuredContent": result,
            "isError": False,
        })

    return _error(request_id, METHOD_NOT_FOUND, f"unknown method {method!r}")


def handler(event, context=None):
    """Lambda entry point. The event *is* the JSON-RPC request, so the deployed
    tool speaks the same messages as the stdio one.

    Nothing escapes as an unhandled fault: a Lambda that raises returns no protocol
    response at all, and the plane in front cannot record what it was."""
    try:
        return dispatch(event)
    except Exception as exc:  # noqa: BLE001 — the boundary is the point
        request_id = event.get("id") if isinstance(event, dict) else None
        return _error(request_id, INTERNAL_ERROR, f"{type(exc).__name__}: {exc}")


def main(stdin=None, stdout=None) -> int:
    """Line-delimited JSON-RPC over stdio. Not the path the gateway uses (ADR-019)."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = _error(None, PARSE_ERROR, "invalid JSON")
        else:
            try:
                response = dispatch(request)
            except Exception as exc:  # noqa: BLE001 — one bad request must not end the session
                request_id = request.get("id") if isinstance(request, dict) else None
                response = _error(request_id, INTERNAL_ERROR, f"{type(exc).__name__}: {exc}")
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
