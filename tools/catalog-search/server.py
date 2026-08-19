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
DEFAULT_CATALOG = ROOT / "data" / "catalog.json"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def catalog_path() -> pathlib.Path:
    """Resolved per call rather than at import, so a test or a probe run can point
    the server somewhere else without reloading the module."""
    return pathlib.Path(os.environ.get(CATALOG_ENV) or DEFAULT_CATALOG)


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
    if request_id is None:
        return None

    # JSON-RPC permits positional params. This server implements none, and saying
    # so is better than an AttributeError from treating a list as a mapping.
    if params is None:
        params = {}
    elif not isinstance(params, dict):
        return _error(request_id, INVALID_PARAMS, "this server takes named params only")

    if method == "initialize":
        return _result(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": TOOL_NAME,
                "version": "0.1.0",
                "catalog": str(catalog_path().name),
            },
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

        try:
            result = search.search(arguments, search.load_catalog(catalog_path()))
        except (OSError, ValueError, TypeError) as exc:
            # A missing or malformed catalog fixture, or an argument the tool
            # cannot use. Reported through the protocol's own error channel: an
            # uncaught exception here kills the stdio session outright and
            # surfaces from Lambda as an unhandled fault, leaving no JSON-RPC
            # record of what was asked.
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
