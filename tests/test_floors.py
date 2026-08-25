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
    assert floors.COLLECTED_FLOOR >= 1900, (
        f"COLLECTED_FLOOR is {floors.COLLECTED_FLOOR}; it was 1900 when ADR-045 recorded "
        "it. Lowering it is how a deleted test file stops being visible — which is the "
        "one thing this floor exists to catch.")


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
