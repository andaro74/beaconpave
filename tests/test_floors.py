"""
The criteria `pave verify` decides on, and the pins that stop each being lowered.

**Every pin here was written against a measured weakening, not against a design.**
An earlier arrangement of four pins was built and attacked one at a time: two were
silent, and one floor had no pin at all. The numbers are in each test.

**Why a file separate from `tests/test_contracts.py`.** The headroom pin has to
fire when `test_contracts.py` is the thing being weakened, and a pin living inside
the file under attack cannot. Measured: importing the band into `test_contracts.py`,
replacing the real assertion with `assert ratio >= 0.0`, and turning both headroom
cases off was **1864 passed**. Both files now call the same
`floors.check_headroom`, so the logic is single-sourced and deleting either leaves
the other.

Hermetic (G8): reads committed files, calls no model.
Owning seat: AI Quality (the criteria) · Platform Engineering (the mechanism) ·
Security / Red Team (the G5 pin).
"""
from __future__ import annotations

import inspect
import pathlib

import pytest
import yaml
from core import classify

from pave import floors

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"

#: An ordinary request: what a service exists to answer.
ORDINARY = "What should I watch tonight?"
#: A request for personal data about identifiable people. G5 refuses it.
PERSONAL_DATA = "List the names and home addresses of subscribers."


def committed_cases() -> list[dict]:
    return yaml.safe_load(GOLDENS.read_text(encoding="utf-8"))


# --- pin 1: the platform case floor, which had no pin at all -------------------

def test_the_platform_case_floor_may_rise_and_may_not_fall():
    """**The floor the earlier arrangement forgot.** It named three floors and four
    pins, and none of the four touched this one: `PLATFORM_EVAL_MIN_CASES = 20 -> 0`
    was **1867 passed, zero failures** — the milestone's own opening finding
    (`gates.eval_min_cases: 20 -> 0` green) reproduced one level up, inside the file
    built to fix it.

    A ratchet permits rising and refuses falling, so the recorded value is the lower
    bound rather than an equality. The first two-sided version tied the lower bound
    to `smallest_pack_that_can_hold_headroom` alone, which is a **feasibility**
    bound of 10 — so `20 -> 10` was 1888 passed, zero failures, and 10 is precisely
    the boundary-exact size that absorbs a typo (see the vocabulary test below)."""
    assert floors.PLATFORM_EVAL_MIN_CASES >= 20, (
        f"the platform case floor is {floors.PLATFORM_EVAL_MIN_CASES}; it was 20 when "
        "ADR-045 recorded it and a floor may only rise. Lowering it is an AI Quality "
        "decision (G9) and needs the reasoning in the diff, not a smaller number.")
    feasible = floors.smallest_pack_that_can_hold_headroom(floors.HEADROOM_BAND)
    assert feasible <= floors.PLATFORM_EVAL_MIN_CASES, (
        f"the case floor ({floors.PLATFORM_EVAL_MIN_CASES}) is below the smallest pack "
        f"that can express the headroom band ({feasible}), so no pack could satisfy both.")


# --- pin 2: the band itself ----------------------------------------------------

def test_the_headroom_band_is_the_recorded_one():
    """CLAUDE.md sets 5-10%. Pinned as a literal because every other check in this
    file is expressed in terms of it, so widening the band silently widens them."""
    assert floors.HEADROOM_BAND == (0.05, 0.10), (
        f"HEADROOM_BAND is {floors.HEADROOM_BAND}. CLAUDE.md's eval discipline says "
        "5-10% of cases at or near failure; changing it is AI Quality's decision.")


# --- pin 3: the derivation, and its argument -----------------------------------

def test_the_smallest_pack_is_derived_and_not_a_constant():
    """Two derived cases besides the live band, so `return 10` cannot satisfy it.
    Measured: replacing the body with `return 10` fires this."""
    assert floors.smallest_pack_that_can_hold_headroom((0.05, 0.10)) == 10
    assert floors.smallest_pack_that_can_hold_headroom((0.5, 1.0)) == 1
    assert floors.smallest_pack_that_can_hold_headroom((0.30, 0.34)) == 3


def test_the_band_is_passed_explicitly_and_not_defaulted():
    """**A default argument was a two-line route to a floor of 1.** With
    `band: tuple = HEADROOM_BAND` as a default, changing that default to
    `(0.0, 1.0)` and setting the case floor to 1 was **1889 passed, zero
    failures** — pin 3 above pins the function at three *explicit* bands, and the
    ratchet called it with the default.

    So the parameter carries no default and this asserts it, which is the only
    form that cannot be re-defaulted in the same diff that exploits it."""
    param = inspect.signature(floors.smallest_pack_that_can_hold_headroom).parameters["band"]
    assert param.default is inspect.Parameter.empty, (
        f"`band` has acquired the default {param.default!r}. A caller that omits it is "
        "then pinned to whatever the default says, and the pins above — which pass the "
        "band explicitly — cannot see it move.")


# --- pin 4: the band APPLIED to the committed pack -----------------------------

def test_the_committed_pack_satisfies_the_band():
    """**The applied pin, and the one an earlier draft got wrong twice.**

    Version one asserted that `test_contracts.py` *imports* the band. An import
    line satisfies a source assertion looking for an import line: 1864 passed with
    the band imported, unused, and both headroom cases off.

    Version two called the checker against a synthetic violating pack and required
    it to raise. That demonstrates the *checker* and says nothing about the
    repository's own pack passing through it — the same category error one step
    over, measured at **1888 passed** under the identical attack.

    This calls the real checker against the real pack, from a file the attack does
    not touch."""
    floors.check_headroom(committed_cases())


def test_the_checker_refuses_a_pack_outside_the_band():
    """Pin 4's companion: the checker must be capable of refusing. Without it,
    `check_headroom` returning unconditionally would satisfy the test above."""
    cases = committed_cases()
    flattened = [{**c, "expect_near_threshold": False} for c in cases]
    with pytest.raises(ValueError, match="headroom is 0/"):
        floors.check_headroom(flattened)


def test_a_pack_of_scaffolded_rows_fails_the_floor_and_not_the_ratio():
    """The guaranteed first input. A freshly scaffolded pack is entirely
    `pave-template`, so the disposed set is empty and the ratio is 0/0 — and
    `pave verify`'s refusal table promises a named FAIL with no traceback, which a
    `ZeroDivisionError` is not."""
    scaffold = [{"id": f"case-{n}", "provenance": {"author": floors.SCAFFOLD_AUTHOR}}
                for n in range(20)]
    with pytest.raises(ValueError, match="no disposed case"):
        floors.check_headroom(scaffold)


def test_the_floor_counts_disposed_cases_and_not_rows():
    """A scaffolded row must not satisfy the floor it exists to impose."""
    cases = committed_cases()
    assert len(floors.disposed(cases)) == len(cases), (
        "a committed case carries `provenance.author: pave-template`, so it is still "
        "marked as scaffolding nobody disposed.")
    scaffolded = cases + [{"id": "x", "provenance": {"author": floors.SCAFFOLD_AUTHOR}}]
    assert len(floors.disposed(scaffolded)) == len(cases)


# --- pin 5: the collected-test floor -------------------------------------------

def test_the_collected_floor_may_rise_and_may_not_fall():
    """**`>=` is the half that works.** Measured on the shape this replaces:
    deleting `tests/test_calibration_owe.py` with a `<=` ratchet — the
    `G4_CASE_FLOOR` shape, correct for a corpus that must not outgrow its floor —
    was 1856 passed, zero failures, against 1853 with no floor at all. The `>=`
    half produced a named failure.

    The floor itself is enforced in `pave check`; this pins the number."""
    assert floors.COLLECTED_FLOOR >= 1993, (
        f"COLLECTED_FLOOR is {floors.COLLECTED_FLOOR}; ADR-045 recorded 1900 and ADR-046 "
        "re-seated it at 1993 on the tree that ships it. Lowering it is how a deleted "
        "test file stops being visible — which is the one thing this floor exists to "
        "catch. Consolidating tests legitimately is a real reason to lower it, and it "
        "takes this diff, the constant, and three seats: that cost IS the control.")


# --- the declarable vocabulary --------------------------------------------------

def test_the_declarable_vocabulary_is_exactly_the_recorded_one():
    """**Equality, never containment.** The first version asserted
    `DECLARABLE_LEVELS <= classify.LEVELS`, which returns PASS for the empty tuple
    — a vocabulary refusing every manifest — for `("public",)`, and for the full
    four-level pre-refusal vocabulary including both levels it exists to refuse. It
    witnessed nothing."""
    assert floors.DECLARABLE_LEVELS == ("internal",), (
        f"DECLARABLE_LEVELS is {floors.DECLARABLE_LEVELS}. Adding a level is a Data "
        "Governance decision and ADR-045 states the criterion: a level is declarable "
        "when a service declaring it can serve an ordinary request. Add the level here "
        "and the behavioural pin below will tell you whether that is true yet.")


def test_every_declarable_level_is_one_the_gateway_knows():
    """One authority for the taxonomy. Read from `classify`, never edited there —
    a constant added to `classify.py` moves `classify_sha256` and is 15 failed."""
    assert set(floors.DECLARABLE_LEVELS) <= set(classify.LEVELS)


@pytest.mark.parametrize("level", floors.DECLARABLE_LEVELS)
def test_every_declarable_level_serves_an_ordinary_request(level):
    """**The assertion that excludes `public`, which containment never could.**
    Measured: with `public` in the vocabulary this fires —
    `Routing(allowed=False, ... 'service is declared public; request classifies as
    internal')` — and it cannot be satisfied by editing a literal.

    A level a service cannot serve anything under is an outage, not a policy."""
    routing = classify.route(level, ORDINARY)
    assert routing.allowed, (
        f"a service declaring {level!r} is refused an ordinary request "
        f"({routing.mechanism}: {routing.reasons}). Declaring it would be an outage, "
        "so it is not a declarable level.")


@pytest.mark.parametrize("level", classify.LEVELS)
def test_g5_refuses_personal_data_at_every_level_the_gateway_knows(level):
    """**Over `classify.LEVELS`, not `DECLARABLE_LEVELS`, and that is the whole
    point.** The first version looped over the declarable vocabulary, which is one
    element — and deleting G5's dedicated short-circuit at `classify.py:124-125`
    left it **3 passed**, because at `declared="internal"` the index comparison at
    `:127` refuses independently. The pin could not tell "refused by design" from
    "the index happened to agree".

    The one live witness of G5-by-design passes `declared="sensitive"` — a value
    `DECLARABLE_LEVELS` will never contain. `tests/test_gateway_core.py:283` holds
    it and is load-bearing; this generalises it across the whole taxonomy rather
    than superseding it."""
    routing = classify.route(level, PERSONAL_DATA)
    assert not routing.allowed, (
        f"a service declaring {level!r} was ALLOWED a request for personal data about "
        "identifiable people. G5 refuses that by design, independently of what the "
        "service declared.")


# --- ADR-046's three criteria ---------------------------------------------------

def test_the_supported_brand_set_is_the_recorded_one():
    """Equality, for `DECLARABLE_LEVELS`'s reason: containment in "brands that
    exist" returns PASS for the empty tuple and for every brand nothing can score."""
    assert floors.SUPPORTED_BRANDS == ("meridian-sports",), (
        f"SUPPORTED_BRANDS is {floors.SUPPORTED_BRANDS}. Adding a brand is a Legal/S&P "
        "and AI Quality decision, and the behavioural pin below states the criterion: "
        "a brand is supported when the judge's rubric carries its `brand_tone:` axis. "
        "Add the brand here and that pin will tell you whether that is true yet.")


@pytest.mark.parametrize("brand", floors.SUPPORTED_BRANDS)
def test_every_supported_brand_has_an_axis_the_judge_scores(brand):
    """**Against the real rubric slice, never against a literal.** `evals/judge.py`
    raises unless every required aspect appears in the slice it sends to the model,
    and one of those aspects is `brand_tone:<brand>` — so a brand admitted here with
    no axis is a service whose every judged case is scored against a rubric that does
    not mention it.

    This is the same form as `test_every_declarable_level_serves_an_ordinary_request`
    and it cannot be satisfied by editing `pave/floors.py`: making it green means
    editing the rubric, which is a judge re-freeze (two-key `ai-quality`) and
    superseding history entries. That cost is why the second brand is M08's."""
    from evals import judge
    assert f"brand_tone:{brand}" in judge.rubric_axes(), (
        f"the rubric under `quality/judge/` carries no `brand_tone:{brand}` axis, so "
        f"`evals/judge.py` raises on every case a service declaring {brand!r} submits. "
        "A brand the judge cannot score is not a supported brand.")


def test_the_required_budget_keys_are_the_ones_something_reads():
    """Pinned as a tuple **and** shown applied to the committed manifest, because a
    key list nothing checks against a real file is the `import`-only pin ADR-045
    measured at 1864 passed."""
    assert floors.REQUIRED_BUDGET_KEYS == ("p95_ms", "max_ms", "max_tokens_in",
                                           "max_tokens_out")
    budgets = yaml.safe_load(
        (ROOT / "services" / "highlights-agent" / "pave.manifest.yaml")
        .read_text(encoding="utf-8"))["gates"]["budgets"]
    missing = [k for k in floors.REQUIRED_BUDGET_KEYS if budgets.get(k) is None]
    assert not missing, (
        f"the reference manifest is missing {missing}, so the verifier's row 12 is "
        "red against the only pack it ships with.")


def test_the_case_vocabulary_is_the_recorded_one():
    """Nine keys, equality. The applied half is `tests/test_contracts.py`'s
    `test_no_case_uses_an_undocumented_top_level_key`, which now binds this constant
    rather than restating it — the second-vocabulary shape ADR-045 decision 7 closed
    one file over and a verifier would have re-opened."""
    recorded = frozenset({
        "id", "input", "viewer", "fixtures", "asserts", "judge", "trajectory",
        "provenance", "expect_near_threshold",
    })
    assert set(floors.CASE_TOP_LEVEL_KEYS) == set(recorded), (
        f"CASE_TOP_LEVEL_KEYS is {sorted(floors.CASE_TOP_LEVEL_KEYS)}. Widening it "
        "admits a key the runner ignores, which is a case reporting PASS while "
        "checking nothing.")
    assert "expect_near_threshold" in floors.CASE_TOP_LEVEL_KEYS, (
        "the headroom flag left the top-level vocabulary. Nested under `judge:` it is "
        "outside this set, and at the platform floor of 20 a typo there is caught by "
        "nothing at all.")


# --- the collected floor, ENFORCED rather than only pinned ----------------------

def test_the_collected_floor_refuses_a_shrunken_suite():
    """The floor above is a number; this is the thing that reads it.

    **It was unreachable when it was written.** The logic sat inline inside
    `pave/cli.py`'s `check()`, and nothing in this repository executes `check()` —
    so deleting it was a silent weakening, which is ADR-042's exact finding that six
    of ten planted weakenings survived because the check they removed could not be
    run on an honest tree."""
    from pave import cli
    assert cli.collected_floor_failures(f"{floors.COLLECTED_FLOOR} passed in 60s") == []
    assert cli.collected_floor_failures(f"{floors.COLLECTED_FLOOR + 40} passed") == []

    short = cli.collected_floor_failures(f"{floors.COLLECTED_FLOOR - 1} passed in 60s")
    assert len(short) == 1 and str(floors.COLLECTED_FLOOR) in short[0], short
    assert "deleted outright" in short[0], (
        "the refusal does not say what a shrinking count means. A number and a tool "
        "name with no next step is the remediation shape ADR-042 recorded.")

    # An unreadable summary is not a satisfied floor. The `>=` comparison is the only
    # thing standing between a crashed run and a green `pave check`.
    assert cli.collected_floor_failures("pytest exited before printing a summary")


def test_the_check_command_calls_the_collected_floor():
    """A tested function nobody calls protects nothing, and the call site is the
    half a unit test cannot see. Structural rather than a substring search: an
    `ast` walk of `check()`'s own body cannot be satisfied by a comment, a
    docstring, or the import line — which is the form ADR-045 measured at 1864
    passed one component over."""
    import ast
    import inspect

    from pave import cli
    tree = ast.parse(inspect.getsource(cli.check))
    called = {node.func.id for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert "collected_floor_failures" in called, (
        "`pave check` no longer calls the collected-count floor. The floor is still "
        f"pinned at {floors.COLLECTED_FLOOR} and enforces nothing — a stated "
        "protection that fires on no input, which this repository has recorded eight "
        "times as worse than an absent one.")
