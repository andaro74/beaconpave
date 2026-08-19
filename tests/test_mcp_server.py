"""
L1 tests for the MCP surface.

The load-bearing test is `test_the_server_holds_no_authorization_logic`. Everything
else is protocol conformance; that one is the invariant.

**A transport must not be able to authorize.** If it could, G3 would be a property
of whichever transport happened to be in front of the tool, and a second route to
the same tool would be a route nobody authorized. So the check is structural — the
module's imports are read without executing it, the way `test_hermeticity.py` scans
for SDKs — rather than a behavioural test that only covers the calls somebody
thought of.

Hermetic (G8). Owning seat: Tool Owner.
"""
import ast
import io
import json
import pathlib

import pytest
import server
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVER_SOURCE = ROOT / "tools" / "catalog-search" / "server.py"
REGISTRY = yaml.safe_load(
    (ROOT / "platform" / "registry" / "tools.yaml").read_text(encoding="utf-8"))


def rpc(method, params=None, request_id=1):
    request = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        request["params"] = params
    return server.dispatch(request)


# --- the invariant ---------------------------------------------------------------

def test_the_server_holds_no_authorization_logic():
    """Structural, and read as source rather than exercised.

    A behavioural test proves the calls it makes are unauthorized here; this
    proves the module has no way to authorize at all, including on a path nobody
    wrote a case for. The technique is `test_hermeticity.py`'s, for the same
    reason: what a module *can* reach is a stronger statement than what it did."""
    tree = ast.parse(SERVER_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    forbidden = {"cedar", "toolplane", "core"}
    assert not (imported & forbidden), (
        f"the MCP server imports {sorted(imported & forbidden)}. Authorization belongs to the "
        "tool plane (G3) — a transport that can authorize makes the invariant a property of "
        "the transport, and a second route to the tool becomes a route nobody authorized."
    )


def test_the_server_name_is_the_registry_id_verbatim():
    """One identifier end to end: registry id, Cedar resource, MCP tool name,
    model-facing name in `toolConfig`. Bedrock's acceptance of a hyphenated tool
    name was measured rather than assumed, which is what makes the mapping layer
    unnecessary — and a mapping layer that does not exist cannot get out of step."""
    assert server.TOOL_NAME in {tool["id"] for tool in REGISTRY}


# --- protocol conformance ----------------------------------------------------------

def test_initialize_reports_the_protocol_and_the_catalog_it_serves():
    """`catalog` is in `serverInfo` so a recorded run says which fixture produced
    it. A tool whose data source can move silently is an instrument that can move
    silently, which is ADR-018's rule one component over."""
    result = rpc("initialize")["result"]
    assert result["protocolVersion"] == server.PROTOCOL_VERSION
    assert result["capabilities"]["tools"] == {}
    assert result["serverInfo"]["name"] == server.TOOL_NAME
    assert result["serverInfo"]["catalog"] == "catalog.json"


def test_tools_list_publishes_the_committed_schema_rather_than_a_copy():
    """The description and the input schema are read from the committed contract.
    A second copy is a second thing to forget to update, and the model would be
    the one reading the stale one."""
    committed = json.loads(
        (ROOT / "tools" / "catalog-search" / "schema.in.json").read_text(encoding="utf-8"))
    descriptor = rpc("tools/list")["result"]["tools"][0]
    assert descriptor["name"] == server.TOOL_NAME
    assert descriptor["description"] == committed["description"]
    assert descriptor["inputSchema"]["required"] == committed["required"]
    assert descriptor["inputSchema"]["properties"] == committed["properties"]


def test_tools_call_returns_rows_as_both_text_and_structured_content():
    result = rpc("tools/call", {"name": "catalog-search",
                                "arguments": {"query": "derby"}})["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["results"][0]["id"] == "t001"
    assert json.loads(result["content"][0]["text"]) == result["structuredContent"]


def test_a_tool_this_server_does_not_serve_is_an_error_not_a_silent_success():
    """A server that accepted anything would let a caller believe a call happened.
    Note this is *not* an authorization decision — it is a server saying it does
    not host that tool, which is a different sentence with a different owner."""
    response = rpc("tools/call", {"name": "publish-highlight", "arguments": {}})
    assert response["error"]["code"] == server.INVALID_PARAMS


@pytest.mark.parametrize("params", [{"name": "catalog-search"},
                                    {"name": "catalog-search", "arguments": "derby"},
                                    {"name": "catalog-search", "arguments": None}])
def test_malformed_arguments_are_rejected(params):
    assert rpc("tools/call", params)["error"]["code"] == server.INVALID_PARAMS


def test_an_unknown_method_is_an_error():
    assert rpc("resources/list")["error"]["code"] == server.METHOD_NOT_FOUND


def test_a_request_that_is_not_json_rpc_is_rejected():
    assert server.dispatch({"method": "tools/list"})["error"]["code"] == server.INVALID_REQUEST


def test_a_notification_for_an_unimplemented_method_gets_no_reply():
    """JSON-RPC: a request with no id is a notification and takes no response.
    Answering one would be a protocol error rather than a helpful extra."""
    assert server.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


# --- the transports carry the same protocol -----------------------------------------

def test_the_lambda_handler_and_dispatch_are_the_same_protocol():
    """The deployed tool speaks the messages the stdio one speaks. If these ever
    diverge, "MCP" would describe the development path and not the deployed one."""
    request = {"jsonrpc": "2.0", "id": 7, "method": "tools/list"}
    assert server.handler(request, None) == server.dispatch(request)


def test_stdio_answers_line_delimited_json_and_survives_a_bad_line():
    """A malformed line is a parse error, not a crash. A server that died on one
    would take the whole session with it."""
    stdin = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n'
                        'not json\n'
                        '\n'
                        '{"jsonrpc":"2.0","id":2,"method":"initialize"}\n')
    stdout = io.StringIO()
    assert server.main(stdin, stdout) == 0
    replies = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert [r.get("id") for r in replies] == [1, None, 2]
    assert replies[1]["error"]["code"] == server.PARSE_ERROR


# --- it serves what it is pointed at, unaltered ---------------------------------------

def test_the_poisoned_fixture_is_served_verbatim(monkeypatch):
    """ADV-002's path at M02: the injection now arrives as a tool result. The
    server must not defuse it — that would make the probe unmeasurable while
    looking like a security improvement, and SPEC/02 defers tool-output assessment
    to M04 on the record rather than quietly here."""
    monkeypatch.setenv(server.CATALOG_ENV, str(ROOT / "data" / "catalog_poisoned.json"))
    assert rpc("initialize")["result"]["serverInfo"]["catalog"] == "catalog_poisoned.json"
    rows = rpc("tools/call", {"name": "catalog-search",
                              "arguments": {"query": "lake adair open"}})["result"]
    assert "SYSTEM NOTE" in rows["structuredContent"]["results"][0]["title"]
