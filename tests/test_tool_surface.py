"""
`tool_surface` — the routed set a golden entry records, and the check that it is
the surface at the entry's own commit.

ADR-061, discharging the precondition ADR-058 recorded: twelve of the twenty-five
golden cases carry `expect_tool_before_answer`, so the routed set decides how
they can score, and until this field existed two runs taken either side of a
deployment produced entries indistinguishable in every field a reader compares.

**The check is vacuous on the committed tree and that is why this file exists.**
No entry carries `tool_surface` yet — the first will be the M06b scored run — so
`check_tool_surface()` returns `[]` today whether it works or not. A check with no
data to check is the *stated and absent* shape this repository keeps finding, so
every assertion below plants an entry and proves the check is reachable rather
than asserting it is present.

Hermetic (G8): the plants are built in `tmp_path`; nothing runs a model, and the
only network-shaped thing is `git show`, against this repository.

Owning seat: AI Quality (what a recorded number means) · Platform Engineering
(the derivation and the snapshot) · Security.
"""
import json
import pathlib
import shutil
import subprocess

import jsonschema
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "evals" / "history" / "schema.json").read_text(encoding="utf-8"))


def _head() -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True, check=False)
    return out.stdout.strip()


def _history(tmp_path: pathlib.Path) -> pathlib.Path:
    """A history directory holding only what a test plants.

    Deliberately not a copy of the real one: every committed entry predates this
    field, so a copy adds twenty entries the check skips and hides which row
    produced a problem."""
    h = tmp_path / "history"
    h.mkdir()
    shutil.copy(ROOT / "evals" / "history" / "schema.json", h / "schema.json")
    return h


def _entry(sha: str, surface: dict | None) -> dict:
    entry = {
        "sha": sha,
        "suite": "goldens",
        "target": "highlights-agent",
        "recorded_at": "2026-09-01T00:00:00+00:00",
        "scores": {"total": 25, "passed": 19, "failed": 6},
    }
    if surface is not None:
        entry["tool_surface"] = surface
    return entry


def _plant(history: pathlib.Path, name: str, entry: dict) -> None:
    (history / name).write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")


# --- the derivation agrees with the pin that already exists --------------------

def test_the_recorder_and_the_parity_pin_compute_the_same_digest():
    """One source of truth, exercised twice.

    `tests/test_gateway_run_parity.py` pins `TOOL_SPECS_SHA256` as a literal and
    `evals.run_evals.tool_surface` derives it. Two copies of one expression drift;
    this asserts they agree, so moving the pin without moving the derivation — or
    the reverse — is red rather than a silent disagreement about what the model
    reads."""
    from evals.run_evals import tool_surface
    from tests.test_gateway_run_parity import TOOL_SPECS_SHA256

    surface = tool_surface()
    assert surface is not None, "the snapshot and contracts are both committed; this cannot be None"
    assert surface["tool_specs_sha256"] == TOOL_SPECS_SHA256


def test_the_routed_set_is_sorted_and_names_both_tools():
    """The set half, which is what a reader diffs.

    Sorted deliberately: a reordering of the deployment table is not a change of
    surface, and `tool_specs_sha256` is the half that carries order."""
    from evals.run_evals import tool_surface

    routed = tool_surface()["routed"]
    assert routed == sorted(routed)
    assert routed == ["catalog-search", "entitlement-check"], (
        "ADR-058 routed the second tool. If this changed, the surface twelve golden "
        "cases are scored against changed with it."
    )


# --- the check is reachable, proved by planting ---------------------------------

def test_a_truthful_surface_passes(tmp_path):
    """The control. Without it every red below could be a check that always fails."""
    from evals.run_evals import tool_surface
    from pave.history import check_tool_surface

    h = _history(tmp_path)
    _plant(h, "m06b-goldens.json", _entry(_head(), tool_surface()))
    assert check_tool_surface(h, ROOT) == []


def test_a_fabricated_routed_set_is_red(tmp_path):
    """The attack the field exists to refuse: an entry claiming a surface its own
    commit does not have — a run recorded as though the tool were routed when it
    was not, which is worth six of twelve cases."""
    from evals.run_evals import tool_surface
    from pave.history import check_tool_surface

    h = _history(tmp_path)
    surface = dict(tool_surface(), routed=["catalog-search"])
    _plant(h, "m06b-goldens.json", _entry(_head(), surface))

    problems = check_tool_surface(h, ROOT)
    assert problems, "an entry claiming a surface its commit does not have is green"
    assert any("routes" in p and "m06b-goldens.json" in p for p in problems)


def test_a_fabricated_specs_digest_is_red(tmp_path):
    """The other half. A digest is where a tool-description rewrite would hide —
    `entitlement-check` shipped one that coached the model into calling it, and it
    reached no pin while the tool was unrouted (ADR-058)."""
    from evals.run_evals import tool_surface
    from pave.history import check_tool_surface

    h = _history(tmp_path)
    surface = dict(tool_surface(), tool_specs_sha256="0" * 64)
    _plant(h, "m06b-goldens.json", _entry(_head(), surface))

    problems = check_tool_surface(h, ROOT)
    assert any("tool_specs_sha256" in p for p in problems)


def test_an_absent_surface_is_unknown_and_never_asserted_about(tmp_path):
    """Absence is not emptiness.

    Every entry recorded before this field existed lacks it. Scoring absence as
    "nothing was routed" would assert about runs nobody measured — ADR-057's rule
    for `tool.executed`, and the same hazard. This is the assertion that would
    fail if somebody later made the field required for old rows."""
    from pave.history import check_tool_surface

    h = _history(tmp_path)
    _plant(h, "m02-tools-goldens.json", _entry(_head(), None))
    assert check_tool_surface(h, ROOT) == []


def test_a_surface_without_a_sha_is_red(tmp_path):
    """There is no commit to check it against, so it is unverifiable rather than
    verified — and the two must not be reported the same way."""
    from evals.run_evals import tool_surface
    from pave.history import check_tool_surface

    h = _history(tmp_path)
    entry = _entry(_head(), tool_surface())
    del entry["sha"]
    _plant(h, "m06b-goldens.json", entry)

    problems = check_tool_surface(h, ROOT)
    assert any("no `sha`" in p for p in problems)


# --- the schema refuses a malformed surface -------------------------------------

@pytest.mark.parametrize("surface, why", [
    ({"routed": ["catalog-search"]}, "no tool_specs_sha256"),
    ({"tool_specs_sha256": "a" * 64}, "no routed set"),
    ({"routed": ["a"], "tool_specs_sha256": "not-a-digest"}, "digest is not sha256-shaped"),
    ({"routed": "catalog-search", "tool_specs_sha256": "a" * 64}, "routed is a string"),
    ({"routed": ["a", "a"], "tool_specs_sha256": "a" * 64}, "routed repeats a tool"),
    ({"routed": ["a"], "tool_specs_sha256": "a" * 64, "extra": 1}, "an undeclared field"),
])
def test_the_schema_refuses_a_malformed_surface(surface, why):
    """The recorder validates against this schema before writing, so a shape it
    accepts is a shape that lands in append-only history."""
    entry = _entry("deadbeef", surface)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(entry, SCHEMA)


def test_the_schema_accepts_a_well_formed_surface_and_its_absence():
    from evals.run_evals import tool_surface

    jsonschema.validate(_entry("deadbeef", tool_surface()), SCHEMA)
    jsonschema.validate(_entry("deadbeef", None), SCHEMA)


# --- the recorder actually attaches it ------------------------------------------

def test_the_recorder_attaches_the_surface_to_a_golden_entry():
    """Parsed, not run: `record` needs answer files and a git tree. What is
    asserted is that the entry-building block reads `tool_surface` and assigns it
    — the line whose deletion would make every assertion above true of a field
    nothing writes."""
    import ast

    src = (ROOT / "evals" / "run_evals.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    assigns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Subscript)
                and isinstance(t.value, ast.Name) and t.value.id == "entry"
                and isinstance(t.slice, ast.Constant) and t.slice.value == "tool_surface"
                for t in node.targets)
    ]
    assert assigns, (
        "nothing assigns `entry['tool_surface']` in the recorder. The check, the "
        "schema and the derivation are all still green, and no entry would ever "
        "carry the field."
    )


def test_the_derivation_returns_none_rather_than_guessing(tmp_path):
    """A missing input yields no field, so the caller omits the key.

    The alternative — an empty `routed` — would record "nothing was routed" as a
    measurement, which is the one reading this field must never produce."""
    from evals.run_evals import tool_surface

    assert tool_surface(tmp_path) is None


def test_the_check_is_registered_in_the_gate():
    """An unregistered check is the *stated and absent* shape exactly.

    Every assertion above calls `check_tool_surface` directly, so all sixteen stay
    green if the gate never runs it — the check would be correct, tested, and
    dead. `pave.history.run_all` is where it has to appear — `pave/cli.py`'s
    `gate_history` delegates to it, and that is the only path `pave check` takes
    to these checks. This reads the function's source rather than its result,
    because on the committed tree no entry carries the field and a behavioural
    assertion would be vacuous for the same reason this file exists.

    Written after the first version asserted against a `gate_history` in this
    module, which does not exist — the dispatch list lives in `run_all` and the
    CLI function of that name is one module up. A test deleted for being awkward
    would have left the registration unasserted, which is the whole failure
    mode."""
    import inspect

    from pave import history

    source = inspect.getsource(history.run_all)
    assert "check_tool_surface" in source, (
        "`check_tool_surface` is not in `run_all`'s dispatch list, so `pave check` "
        "never runs it and a fabricated tool surface reaches append-only history "
        "green."
    )
