"""
catalog-search over MCP: JSON-RPC messages, no transport opinion.

**This server authorizes nothing.** It answers `tools/list` and `tools/call` and
that is all. Authorization is the tool plane's (G3), and it has to stay there or
the invariant becomes a property of whichever transport happened to be in front —
a tool reachable by a second route would be a tool nobody authorized. Nothing in
this module imports `cedar` or `toolplane`, and a test pins that.

**It sanitizes nothing either.** Pointed at the poisoned fixture it returns the
injected title verbatim. Defusing it here would make ADV-002 unmeasurable while
looking like a security improvement: the open path would stop being visible
without stopping being open. SPEC/02 defers tool-output assessment to M04 on the
record, with the observation committed as evidence.

**`dispatch` is the whole protocol; the transports are three lines each.** MCP is
a message format, not a socket, so the messages are implemented once and stdio
and Lambda both hand requests to the same function. That is what lets the gateway
speak MCP without paying for a subprocess per tool call — the wire format is real
even where the wire is not.

Subset, and ADR-019 says which: `initialize`, `tools/list`, `tools/call`, over
JSON-RPC 2.0. No SDK, no resources, no prompts, no sampling. Notifications are
recognised and correctly answered with silence.

Owning seat: Tool Owner.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import search

#: The registry id, used verbatim as the MCP tool name and as the model-facing
#: name in `toolConfig`. Measured before it was assumed: Bedrock accepts a
#: hyphenated tool name, so one identifier runs end to end — registry id, Cedar
#: resource, MCP tool, model-facing name — and there is no mapping layer to get
#: out of step. `tests/test_mcp_server.py` pins it against the registry.
TOOL_NAME = "catalog-search"

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

#: The protocol version this subset targets. Reported rather than negotiated: a
#: server that claimed to negotiate and then ignored the answer would be worse
#: than one that states what it implements.
PROTOCOL_VERSION = "2024-11-05"

#: Which catalog is served. Overridable so the adversarial run can point at the
#: poisoned fixture without a second code path, and **reported in `serverInfo`**
#: so a recorded run says which fixture produced it — a tool whose data source can
#: move silently is an instrument that can move silently (ADR-018's rule, applied
#: one component over).
CATALOG_ENV = "BEACONPAVE_CATALOG"

#: Where the catalog is looked for when the environment does not say.
#:
#: **Two candidates, bundle first, and the order is the fix.** `ROOT` is
#: `HERE.parents[1]`, which is the repo root only because the source tree has the
#: tool two levels down. The deployed bundle flattens that: `HERE` is
#: `/var/task`, so `ROOT` is `/` and the old default pointed at
#: `/data/catalog.json` — a path that exists nowhere. The deployed tool worked
#: solely because a literal in the CDK stack and a literal in the handler happened
#: to agree, with no test between them.
#:
#: When it stopped working it failed *softly*: a missing file raised `OSError`,
#: `dispatch` turned it into `isError`, and the tool plane recorded the whole
#: thing as `mechanism: schema` — a deployment fault filed as a contract
#: violation, on every case, which is exactly the misattribution `ROUTING` was
#: added to prevent. So the bundle's own copy is tried first and the source-tree
#: path second, and `catalog_path` refuses rather than returning something that
#: is not there.
CATALOG_CANDIDATES = (HERE / "catalog.json", ROOT / "data" / "catalog.json")

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def catalog_path() -> pathlib.Path:
    """Resolved per call rather than at import, so a test or a probe run can point
    the server somewhere else without reloading the module.

    **Raises when the catalog is not there, and names every place it looked.**
    Returning a path that does not resolve pushed the failure one layer out, where
    it arrived as an ordinary `isError` and was recorded as a contract violation.
    A tool that cannot find the data it exists to serve is broken, not
    misconfigured by the caller, and it should say which of the two it is."""
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
    """The tool as `tools/list` publishes it. The description and the input schema
    are the committed contract, read from disk rather than restated here — a
    second copy of a schema is a second thing to forget to update, and the model
    would be the one reading the stale one."""
    schema = _schema("schema.in.json")
    return {
        "name": TOOL_NAME,
        "description": schema["description"],
        "inputSchema": {k: v for k, v in schema.items()
                        if k in ("type", "required", "properties", "additionalProperties")},
    }


def dispatch(request: dict) -> dict | None:
    """Handle one JSON-RPC request. Returns `None` for a notification.

    Unknown methods are an error rather than a silent success. A server that
    accepted anything would let a caller believe a call happened."""
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        request_id = request.get("id") if isinstance(request, dict) else None
        return _error(request_id, INVALID_REQUEST, "expected a JSON-RPC 2.0 request object")

    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params")

    # A request with no id is a notification and takes no response — for EVERY
    # method, not only unrecognised ones. This check sat after dispatch, so
    # `tools/list` with no id got a full reply carrying `"id": null`: a protocol
    # violation, and a client tracking outstanding requests sees a response to
    # nothing.
    #
    # An *explicit* `"id": null` is a request, not a notification, and the spec
    # says it gets a response. `request.get("id") is None` cannot tell the two
    # apart, so the membership test is what distinguishes them.
    if "id" not in request:
        return None

    # JSON-RPC permits positional params. This server implements none, and saying
    # so is better than an AttributeError from treating a list as a mapping.
    if params is None:
        params = {}
    elif not isinstance(params, dict):
        return _error(request_id, INVALID_PARAMS, "this server takes named params only")

    if method == "initialize":
        try:
            catalog = str(catalog_path().name)
        except OSError as exc:
            # `serverInfo.catalog` is provenance: it is how a recorded run says
            # which fixture produced it (ADR-018's rule, one component over). A
            # server that cannot name its data source must not report a plausible
            # one, so this fails rather than defaulting.
            return _error(request_id, INTERNAL_ERROR, f"catalog unavailable: {exc}")
        return _result(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": TOOL_NAME, "version": "0.1.0", "catalog": catalog},
        })

    if method == "tools/list":
        return _result(request_id, {"tools": [descriptor()]})

    if method == "tools/call":
        name = params.get("name")
        if name != TOOL_NAME:
            # Not an authorization decision — this server simply does not serve
            # that tool. The plane is what decides whether a caller may reach the
            # one it does serve.
            return _error(request_id, INVALID_PARAMS, f"this server does not serve {name!r}")
        arguments = params.get("arguments")
        if not isinstance(arguments, dict):
            return _error(request_id, INVALID_PARAMS, "arguments must be an object")

        # `query` is `required` with `minLength: 1` in the schema this server
        # publishes through `tools/list`. Reporting success for a call its own
        # published contract rejects would be bad enough; the specific harm is
        # that an empty result set is indistinguishable from "searched, found
        # nothing" — which is the exact shape `grounded-019` is pre-registered
        # around. A model that omitted `query` would get the same signal as one
        # that asked about a title the catalog does not have.
        #
        # This is not the plane's contract validation moved into the transport:
        # it is the one distinction `search` already knows and discards, reported
        # through the error channel the protocol provides.
        # `minLength: 1` is what the published contract says, so that is what is
        # enforced. The first version rejected anything blank after `.strip()`,
        # which made the server STRICTER than the schema it publishes: `" "` is a
        # contract-valid query, and the plane had just validated it. `toolplane`
        # states the governing rule twice — "a validator stricter than its schema
        # is as wrong as a lax one, and harder to notice because it only ever
        # refuses" — and this was that, one component over.
        if not str(arguments.get("query") or ""):
            return _result(request_id, {
                "content": [{"type": "text",
                             "text": "catalog-search requires a non-empty `query`"}],
                "isError": True,
            })

        # **A broken deployment and a bad call take different channels**, and the
        # difference decides how the tool plane records it. A JSON-RPC `error` says
        # the server could not answer at all; an `isError` *result* says the tool
        # answered and the answer is a failure. `handler._call_tool` maps the first
        # to `routing` and the second to `schema`, so a missing catalog stops being
        # filed as a contract violation on every case.
        try:
            catalog = search.load_catalog(catalog_path())
        except OSError as exc:
            return _error(request_id, INTERNAL_ERROR, f"catalog unavailable: {exc}")

        try:
            result = search.search(arguments, catalog)
        except (ValueError, TypeError) as exc:
            # An argument the tool cannot use, or a malformed fixture row. The call
            # was answered; the answer is a failure. Reported through the protocol
            # rather than raised, because an uncaught exception kills the stdio
            # session outright and leaves no record of what was asked.
            return _result(request_id, {
                "content": [{"type": "text", "text": f"catalog-search failed: {exc}"}],
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
    tool speaks the same messages as the stdio one — the transport changes and the
    protocol does not.

    Nothing escapes as an unhandled fault. A Lambda that raises returns no
    protocol response at all, so the caller learns only that something went wrong
    somewhere — and the tool plane in front cannot record what it was."""
    try:
        return dispatch(event)
    except Exception as exc:  # noqa: BLE001 — the boundary is the point
        request_id = event.get("id") if isinstance(event, dict) else None
        return _error(request_id, INTERNAL_ERROR, f"{type(exc).__name__}: {exc}")


def main(stdin=None, stdout=None) -> int:
    """Line-delimited JSON-RPC over stdio, for anyone who wants to run this as an
    ordinary MCP server. Not the path the gateway uses; see ADR-019."""
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
