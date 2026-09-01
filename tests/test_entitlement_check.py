"""
`entitlement-check`, against the cases that specify it.

**The golden suite is this tool's specification, so the table below is generated
from it rather than written beside it.** Twelve committed cases assert an
`entitlement` verdict; each names a title through `must_cite` and a viewer through
`viewer`, which is exactly the tool's input. A hand-written expectation table would
be a second copy of the spec, free to drift from the one the gate actually scores —
the two-registry smell `ADR-030` was written about.

That also means these tests fail if a golden case changes, which is intended: a
case is AI Quality's and is never edited to make a run pass, so a red here after a
case edit is the question "did the tool's contract just change?" being asked at the
right moment.

Hermetic (G8): the committed fixture, no clock of its own, no network.
Owning seat: Tool Owner · AI Quality (what a reason means).
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name: str, path: pathlib.Path):
    """Load a bundle module by path, under a name of its own.

    **Not `sys.path.insert` + a bare import, and the difference is not style.**
    That is what this file did first, and because the insert is permanent and at
    position 0, `tools/entitlement-check/` sat ahead of `tools/catalog-search/` for
    the whole session. It was invisible until this tool gained a `server.py`: from
    that moment `test_mcp_server.py`'s bare `import server` resolved to the WRONG
    TOOL's server, and three of its tests failed while passing in isolation. Two
    bundles both containing `server.py` cannot share a namespace, so neither
    should claim one."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


entitlement = _load("entitlement_check_logic",
                    ROOT / "tools" / "entitlement-check" / "entitlement.py")

CATALOG = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
CASES = yaml.safe_load(
    (ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml")
    .read_text(encoding="utf-8"))

#: The one evaluation clock, read from the arm rather than restated. `ADR-021`:
#: no arm may define a second clock, and a test that typed the literal would be
#: one more place it could drift from.
CLOCK = next(
    line.split("=", 1)[1].strip().strip('"')
    for line in (ROOT / "services" / "highlights-agent" / "gateway_client.py")
    .read_text(encoding="utf-8").splitlines()
    if line.startswith("CLOCK ="))


def _specified():
    """`(case_id, args, expected)` for every case that asserts a verdict."""
    for case in CASES:
        verdict = next((a["entitlement"] for a in case.get("asserts", [])
                        if "entitlement" in a), None)
        if verdict is None:
            continue
        cited = next((a["must_cite"] for a in case.get("asserts", []) if "must_cite" in a), [])
        viewer = case.get("viewer") or {}
        # `entitlement-012` asserts `unknown-title` and cites nothing, because the
        # title it asks about is not in the catalog. Its input is the point.
        title_id = cited[0] if cited else "t999"
        yield case["id"], {"title_id": title_id, **viewer}, verdict


SPECIFIED = list(_specified())


def test_the_table_is_not_empty_and_covers_every_reason():
    """A parametrised suite that silently collected nothing is the vacuity this
    repository keeps paying for. This asserts the corpus is real AND that it
    exercises the whole enum — a table missing `not-yet-started` would let the
    clock rule be anything at all."""
    assert len(SPECIFIED) == 12, f"{len(SPECIFIED)} cases specify a verdict; expected 12"
    reasons = {expected["reason"] for _, _, expected in SPECIFIED}
    schema = json.loads((ROOT / "tools" / "entitlement-check" / "schema.out.json")
                        .read_text(encoding="utf-8"))
    assert reasons == set(schema["properties"]["reason"]["enum"]), (
        f"the golden cases exercise {sorted(reasons)} and the contract declares "
        f"{sorted(schema['properties']['reason']['enum'])} — a reason no case pins is a "
        "reason the tool could get wrong in silence")


@pytest.mark.parametrize("case_id,args,expected", SPECIFIED, ids=[c for c, _, _ in SPECIFIED])
def test_the_tool_answers_what_the_golden_case_asserts(case_id, args, expected):
    """Every committed expectation, through the real function at the real clock."""
    got = entitlement.check(args, CATALOG, CLOCK)
    assert got["entitled"] == expected["entitled"], f"{case_id}: {got}"
    assert got["reason"] == expected["reason"], f"{case_id}: {got}"


def test_a_blackout_outranks_a_plan_gap():
    """`blackout-001` and `multi-023` fix this: a base-plan viewer in a blacked-out
    market is told `blackout`, not `upgrade-required`. Buying the upgrade would not
    let them watch it, so naming the upgrade would be advice that does not work."""
    got = entitlement.check(
        {"title_id": "t001", "plan": "base", "dma": "jefferson-city"}, CATALOG, CLOCK)
    assert got["reason"] == "blackout" and got["blackout"] is True


def test_a_plan_gap_outranks_the_clock():
    """`entitlement-002` and `edge-024`: a base viewer asking about a future
    sports-tier event is told to upgrade, not to wait. The upgrade is true now and
    stays true; the wait resolves on its own."""
    got = entitlement.check(
        {"title_id": "t005", "plan": "base", "dma": "north-haven"}, CATALOG, CLOCK)
    assert got["reason"] == "upgrade-required"


def test_the_clock_is_required_and_has_no_default():
    """A defaulted clock is a second clock definition wearing a keyword argument —
    correct at one instant and silently wrong afterwards. `ADR-021` forbids the
    second definition; this is the shape it would arrive in."""
    with pytest.raises(TypeError):
        entitlement.check({"title_id": "t001", "plan": "base", "dma": "north-haven"}, CATALOG)


def test_the_verdict_moves_when_the_clock_does():
    """The clock is load-bearing, proved rather than assumed. An implementation
    that ignored `now` would pass every case above except this one, because at the
    evaluation instant `t005` is the only title whose verdict the clock decides."""
    before = entitlement.check(
        {"title_id": "t005", "plan": "sports-tier", "dma": "cedar-point"}, CATALOG, CLOCK)
    after = entitlement.check(
        {"title_id": "t005", "plan": "sports-tier", "dma": "cedar-point"},
        CATALOG, "2026-09-20T18:00:00Z")
    assert before["reason"] == "not-yet-started" and before["entitled"] is False
    assert after["reason"] == "ok" and after["entitled"] is True


def test_an_unknown_title_claims_nothing_about_a_title_it_cannot_see():
    """`blackout` and `required_entitlement` are optional in the contract exactly so
    a verdict can decline to make them. Reporting `blackout: false` for a title that
    does not exist would be a claim about nothing."""
    got = entitlement.check({"title_id": "t999", "plan": "base", "dma": "lake-adair"},
                            CATALOG, CLOCK)
    assert got == {"entitled": False, "reason": "unknown-title"}


def test_every_answer_validates_against_the_committed_output_contract():
    """The tool may not emit a shape its own schema forbids —
    `additionalProperties: false`, so an extra explanatory field is a contract
    break rather than a courtesy."""
    import jsonschema
    schema = json.loads((ROOT / "tools" / "entitlement-check" / "schema.out.json")
                        .read_text(encoding="utf-8"))
    for _case_id, args, _ in SPECIFIED:
        jsonschema.validate(entitlement.check(args, CATALOG, CLOCK), schema)


def _reads_key(path, key):
    """Does this module USE `key` as data, as opposed to mentioning it in prose?

    **The first version of this was a substring check and it was wrong**, in the
    way this repository keeps finding: `search.py`'s docstring names `blackouts`
    four times to explain that it never reads them, so `"blackouts" in source` says
    the opposite of the truth. Docstrings are stripped and the remaining string
    constants are what count."""
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None and node.body:
                docstrings.add(id(node.body[0]))
    return any(
        isinstance(n, ast.Constant) and n.value == key
        for stmt in ast.walk(tree)
        if id(stmt) not in docstrings
        for n in ([stmt] if isinstance(stmt, ast.Constant) else [])
    ) or any(
        isinstance(n, ast.Constant) and n.value == key
        for top in tree.body if id(top) not in docstrings
        for n in ast.walk(top)
    )


def test_it_reads_the_blackout_table_and_catalog_search_does_not():
    """The split `SPEC/02` insisted on, asserted from both sides. If this tool
    stopped reading `blackouts` the trajectory eval would still see a tool call
    while the verdict came from somewhere else; if `catalog-search` started
    reading them, one tool would answer both questions and the split would be
    decorative."""
    tools = ROOT / "tools"
    assert _reads_key(tools / "entitlement-check" / "entitlement.py", "blackouts"), (
        "entitlement-check must read the blackout table — it is the only component "
        "permitted to, and the verdict is meaningless without it")
    assert not _reads_key(tools / "catalog-search" / "search.py", "blackouts"), (
        "catalog-search must never read the blackout table (SPEC/02)")
