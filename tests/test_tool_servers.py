"""
Every registered tool, as a class rather than as an instance.

`test_mcp_server.py` is thorough and covers exactly one tool, by literal path:
`ROOT / "tools" / "catalog-search" / "server.py"`, reached through a bare
`import server`. That is not an oversight in it — **two bundles cannot both answer
`import server`**, because a hyphen cannot be a package name so the bundle root
goes on `sys.path` and the last one inserted wins. So the suite that proves a tool
speaks the dialect `handler._call_tool` sends could only ever prove it for one
tool, and the second tool's conformance was nobody's test.

That is the ADR-043 shape the Tool Owner seat named during the `SPEC/06b` review:
an instance closed and the class left open. This file closes the class. It
discovers tools from `platform/registry/tools.yaml` — the registry is the list, so
a tool added there is covered here the day it is added, without anyone remembering
to widen a tuple.

Modules are loaded **by path** under distinct names, with the bundle root on
`sys.path` for the duration, which is how the Lambda runtime resolves them and why
`server.py` can say `import entitlement` rather than `from . import entitlement`.

Hermetic (G8). Owning seat: Tool Owner.
"""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import json
import pathlib
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = yaml.safe_load(
    (ROOT / "platform" / "registry" / "tools.yaml").read_text(encoding="utf-8"))
TOOL_IDS = [t["id"] for t in REGISTRY]

#: Registered tools that deliberately have no implementation, and why.
#:
#: **The point of this list is that it is a declaration rather than a silence.** The
#: first run of this file found `publish-highlight` registered, carrying a generated
#: Cedar policy and a shipped contract, with nothing behind it -- the same shape
#: `entitlement-check` had for four milestones. That is a fact worth stating in the
#: tree rather than discovering again.
#:
#: An entry here is not an excuse: `test_an_unbuilt_tool_is_declared_and_unreachable`
#: refuses any tool whose consequence class does not make it unreachable, so this
#: cannot be used to quiet a tool a caller could actually get to.
UNBUILT = {
    "publish-highlight": (
        "Deployment refused by Legal/S&P (`SPEC/06` Decisions 1); whether that refusal "
        "is standing or was scoped to M06 is an open question for that seat (ADR-055). "
        "Consequence class `publish` is in `cedar.GATED_CONSEQUENCES`, so the generated "
        "policy carries a `forbid` and no caller can reach it in any case."
    ),
}

BUILT = [t for t in TOOL_IDS if t not in UNBUILT]


def bundle(tool_id: str) -> pathlib.Path:
    return ROOT / "tools" / tool_id


@contextlib.contextmanager
def _on_path(directory: pathlib.Path):
    sys.path.insert(0, str(directory))
    try:
        yield
    finally:
        with contextlib.suppress(ValueError):
            sys.path.remove(str(directory))


def load_server(tool_id: str):
    """The tool's server module, under a name of its own.

    Distinct names matter: importing two `server` modules under one name would
    leave whichever loaded second in `sys.modules`, and every test after it would
    silently exercise the wrong tool."""
    path = bundle(tool_id) / "server.py"
    spec = importlib.util.spec_from_file_location(f"toolserver_{tool_id.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    with _on_path(bundle(tool_id)):
        spec.loader.exec_module(module)
    return module


def rpc(module, method, params=None, request_id=1):
    request = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        request["params"] = params
    return module.dispatch(request)


def test_the_registry_is_not_empty_and_this_file_covers_all_of_it():
    """A discovery suite that discovered nothing is the vacuity this repository
    keeps paying for, and it would look identical to a passing run."""
    assert len(BUILT) >= 2, (
        f"{len(BUILT)} built tool(s); this file exists to cover the CLASS, and with "
        "fewer than two it proves nothing test_mcp_server.py did not")
    assert set(UNBUILT) <= set(TOOL_IDS), "UNBUILT names a tool that is not registered"


@pytest.mark.parametrize("tool_id", BUILT)
def test_every_registered_tool_has_an_implementation(tool_id):
    """**The gap this file was written for.** `entitlement-check` was registered,
    permitted by Cedar and shipped in the generated contract for four milestones
    while `tools/entitlement-check/` held a README and two schemas and no code.
    Routing a Lambda at nothing is green: the deployment succeeds, the tool answers
    nothing, and no test says a word."""
    directory = bundle(tool_id)
    assert directory.is_dir(), f"{tool_id} is registered and has no bundle at {directory}"
    assert (directory / "server.py").is_file(), (
        f"{tool_id} is registered with no server. A registered tool the plane can "
        "authorize and nothing can answer is a route to a 500. If it is deliberately "
        "unbuilt, say so in UNBUILT with the reason.")
    modules = [p.name for p in directory.glob("*.py") if p.name != "server.py"]
    assert modules, (
        f"{tool_id} has a transport and no logic. `server.py` is the wire; the tool "
        "is whatever it calls.")


@pytest.mark.parametrize("tool_id", sorted(UNBUILT))
def test_an_unbuilt_tool_is_declared_and_unreachable(tool_id):
    """An exemption may not quiet a tool a caller could reach.

    Every entry in `UNBUILT` must still be registered — a stale exemption for a tool
    nobody registers any more is dead text that would silently cover a future tool
    of the same name — and its consequence class must make it unreachable, so the
    declaration cannot become a way to ship a live tool with nothing behind it."""
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "platform" / "gateway"))
    try:
        from core import cedar
    finally:
        with contextlib.suppress(ValueError):
            _sys.path.remove(str(ROOT / "platform" / "gateway"))

    assert tool_id in TOOL_IDS, f"{tool_id} is exempted and not registered; drop the entry"
    assert UNBUILT[tool_id].strip(), f"{tool_id} is exempted with no reason"
    entry = next(t for t in REGISTRY if t["id"] == tool_id)
    assert entry["consequence"] in cedar.GATED_CONSEQUENCES, (
        f"{tool_id} is declared unbuilt but its consequence class `{entry['consequence']}` "
        "is not gated, so a caller could be permitted to reach a tool that does not "
        "exist. Build it or gate it; do not exempt it.")
    assert not (bundle(tool_id) / "server.py").is_file(), (
        f"{tool_id} now HAS a server. Remove it from UNBUILT so the class-level "
        "conformance tests start covering it.")


@pytest.mark.parametrize("tool_id", BUILT)
def test_no_tool_server_can_authorize(tool_id):
    """The invariant, at class scope. If a transport could authorize, G3 would be a
    property of whichever transport happened to be in front — and a second route to
    a tool is a route nobody authorized. Structural, so it also covers the paths
    nobody wrote a case for."""
    tree = ast.parse((bundle(tool_id) / "server.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"cedar", "toolplane", "core"}, (
        f"{tool_id}'s server imports {sorted(imported & {'cedar', 'toolplane', 'core'})}. "
        "Authorization is the plane's (G3); a transport that can authorize makes the "
        "invariant a property of the transport.")


@pytest.mark.parametrize("tool_id", BUILT)
def test_the_server_name_is_the_registry_id_verbatim(tool_id):
    """One identifier end to end — registry id, Cedar resource, MCP tool name,
    model-facing name — so there is no mapping layer to get out of step."""
    assert tool_id == load_server(tool_id).TOOL_NAME


@pytest.mark.parametrize("tool_id", BUILT)
def test_tools_list_publishes_the_committed_schema_rather_than_a_copy(tool_id):
    """A restated schema is a second copy, and the model reads the stale one."""
    module = load_server(tool_id)
    published = rpc(module, "tools/list")["result"]["tools"][0]
    committed = json.loads((bundle(tool_id) / "schema.in.json").read_text(encoding="utf-8"))
    assert published["name"] == tool_id
    assert published["description"] == committed["description"]
    assert published["inputSchema"]["properties"] == committed["properties"]
    assert published["inputSchema"]["required"] == committed["required"]


@pytest.mark.parametrize("tool_id", BUILT)
def test_initialize_reports_the_protocol_and_its_data_source(tool_id):
    """`serverInfo` is provenance: how a recorded run says what produced it."""
    info = rpc(module := load_server(tool_id), "initialize")["result"]
    assert info["protocolVersion"] == module.PROTOCOL_VERSION
    assert info["serverInfo"]["name"] == tool_id
    assert info["serverInfo"]["catalog"], "a server must name the fixture it serves"


@pytest.mark.parametrize("tool_id", BUILT)
def test_a_tool_this_server_does_not_serve_is_an_error_not_a_silent_success(tool_id):
    module = load_server(tool_id)
    reply = rpc(module, "tools/call", {"name": "not-this-one", "arguments": {}})
    assert "error" in reply


@pytest.mark.parametrize("tool_id", BUILT)
def test_an_unknown_method_is_an_error_and_a_notification_is_silence(tool_id):
    module = load_server(tool_id)
    assert "error" in rpc(module, "tools/nope")
    assert module.dispatch({"jsonrpc": "2.0", "method": "tools/list"}) is None


@pytest.mark.parametrize("tool_id", BUILT)
def test_the_lambda_handler_and_dispatch_are_the_same_protocol(tool_id):
    """The transport changes and the protocol does not — which is what lets the
    gateway speak MCP without a subprocess per call (ADR-019)."""
    module = load_server(tool_id)
    request = {"jsonrpc": "2.0", "id": 7, "method": "tools/list"}
    assert module.handler(request) == module.dispatch(request)


@pytest.mark.parametrize("tool_id", BUILT)
def test_a_call_missing_its_required_arguments_answers_rather_than_raises(tool_id):
    """An uncaught exception kills a stdio session outright and leaves no record of
    what was asked. The plane validates first, so reaching this means the transport
    was addressed directly — which is exactly when a clear answer matters."""
    module = load_server(tool_id)
    reply = rpc(module, "tools/call", {"name": tool_id, "arguments": {}})
    assert "result" in reply and reply["result"]["isError"] is True
