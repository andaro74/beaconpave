"""
The `p95_ms` rule's failed premise, disposed by a condition this file evaluates.

**The debt as M08b handed it over.** The mandated shape's own p95 went
**3769 -> 5241**, 41 ms over the 5200 ceiling derived from it, so the rule's
premise — *the mandated shape's tail is stable across runs* — is what failed, and
the pooled reading isolates no share.

Re-deriving by ADR-014's unchanged constants from the fresh population is the
obvious move and it is the one that must not be made blind. M08b published pooled
**6633**; a point re-derived from 5241 lands above it, so the last published OVER
reading would become *within*. **A gate moved to clear a reading is the trade G9
exists to refuse.**

**The condition, pre-registered in ADR-075 decision 5 §4 and executed here:**

> `p95_ms` moves only if the point ADR-014's unchanged rule derives from the most
> recent fresh mandated-shape population **still leaves the run that population
> came from OVER the gate.**

**Which reading of "the run reads OVER", because the sentence admits two and the
reason differs.**

1. *Same-population*: the mandated p95 against the point derived from it. The
   point is the midpoint of `[1.15·p95, 1.60·p95]` — that is `1.375·p95` — which
   is **strictly above the p95 it came from** for any positive p95. Under this
   reading the condition is **unsatisfiable by construction**, and a rule that
   cannot fire is not a rule. Asserted below as a property, not as an outcome on
   this data.
2. *What the gate actually prints*: `suite_latency` over the whole run — the
   **pooled** p95, the number in `suite latency OVER p95=6633ms over 5200ms`.
   Under this reading the condition is real and says something worth saying: the
   gate may move only if `pooled > 1.375 × mandated`.

**The spec means reading 2**, and it says so. Both give the same answer on this
data — the condition does **not** hold — and recording which one is meant is what
the next milestone inherits.

**The answer, computed rather than quoted: `gates.budgets.p95_ms` stays 5200.**
ADR-014's stability sentence is withdrawn (ADR-014 amendment 4), the gate is
re-described as a fixed ceiling with a recorded derivation, and the re-derivation
is dated to **09c** — the first scheduled milestone that re-runs the goldens and
does not read its own p95 against a number it just chose.

**And the finding that is stronger than the outcome.** At M07 the rule took *"the
only population under which the run in view fails the gate"*, and that fact is
what made an in-view derivation survivable. **Here there is no such
population** — all five read *within* — so the rule's own selection criterion has
no solution on this data. That is what a failed premise looks like when you try
to re-apply the rule that rested on it.

Nothing here reads a number out of a journal sentence: the population is read
from the answer files through `context_census.mandated_calls()` and
`evals.deterministic.suite_latency` — the scorer's own percentile, so this test
and the gate cannot disagree about what a p95 is.

Zero model calls, hermetic (G8).

Owning seats: AI Quality (the ceiling) · Platform Engineering (the latency the
gate reads) · Security (what a recorded number means).
"""
from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import sys

import pytest
import yaml

from evals.deterministic import suite_latency

ROOT = pathlib.Path(__file__).resolve().parents[1]
CENSUS_READER = ROOT / "milestones" / "M08" / "context_census.py"
RUNS = [ROOT / "milestones" / "M08b" / f"goldens-run-{n}.json" for n in (1, 2, 3)]
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"

#: ADR-014's budget band, unchanged. Named here so a diff that widens it to make
#: the condition fire is a visible edit rather than an arithmetic accident.
FLOOR_X, ROOF_X = 1.15, 1.60

#: Where the gate stands, and where it stays.
CEILING_MS = 5200

#: The five populations, computed on `479972e` and pinned member by member. Every
#: constant is planted in the deletability audit; a table that agrees with
#: whatever the reader produces today measures nothing.
#:
#: population -> (n, p95, floor, roof, unrounded midpoint, point)
POPULATIONS = {
    "mandated shape": (38, 5241, 6027.15, 8385.60, 7206.375, 7200),
    "as-run <=3 call": (58, 5683, 6535.45, 9092.80, 7814.125, 7800),
    "pooled": (70, 6633, 7627.95, 10612.80, 9120.375, 9100),
    "above mandate": (32, 7223, 8306.45, 11556.80, 9931.625, 9900),
    ">=4 call": (12, 8437, 9702.55, 13499.20, 11600.875, 11600),
}

#: The population ADR-014 amendment 3's rule takes, by name.
THE_RULES_POPULATION = "mandated shape"


@pytest.fixture(scope="module")
def census():
    spec = importlib.util.spec_from_file_location("context_census", CENSUS_READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["context_census"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rows(census):
    """Every answered sample of M08b's fresh run, with its mandate.

    From the ANSWER FILES through the census's own `mandated_calls`, never from
    `fresh-join.json`: a test that read the derived record would agree with that
    record by construction rather than with the run."""
    cases = {c["id"]: c for c in yaml.safe_load(CASES.read_text(encoding="utf-8"))}
    out = []
    for n, path in enumerate(RUNS, 1):
        for case_id, record in json.loads(path.read_text(encoding="utf-8")).items():
            usage = (record or {}).get("usage") or {}
            if not (usage.get("tokens_in") or 0) > 0:
                continue
            out.append({
                "id": f"{case_id} s{n}",
                # Carried as a field rather than parsed back out of `id`. The
                # single-sample reading below needs to partition by sample, and a
                # test that re-parses its own key is one rename from silent.
                "sample": n,
                "calls": len(usage.get("calls") or []),
                "mandated": census.mandated_calls(cases[case_id]),
                "latency_ms": usage.get("latency_ms"),
            })
    return out


def _population(rows: list[dict], name: str) -> list[dict]:
    if name == "mandated shape":
        return [r for r in rows if r["calls"] == r["mandated"]]
    if name == "as-run <=3 call":
        return [r for r in rows if r["calls"] <= 3]
    if name == "pooled":
        return list(rows)
    if name == "above mandate":
        return [r for r in rows if r["calls"] > r["mandated"]]
    if name == ">=4 call":
        return [r for r in rows if r["calls"] >= 4]
    raise AssertionError(f"unknown population {name!r}")


def _p95(population: list[dict]) -> int:
    """The SCORER's percentile, not a second one.

    `evals.deterministic.suite_latency` is what the gate prints, so a test using
    `statistics.quantiles` could disagree with the gate about what a p95 is and
    the disagreement would be invisible."""
    answers = {r["id"]: {"usage": {"latency_ms": r["latency_ms"]}} for r in population}
    detail = suite_latency(answers, None).detail
    return int(detail.split("p95=")[1].split("ms")[0])


#: The granularity ADR-014 rounds the derived point to. Named rather than
#: written twice, because `ROUNDING_SAFE_P95` below is computed FROM it: a
#: rounding rule and a bound on that rule's effect that can move independently
#: are two statements about one mechanism.
GRANULARITY = 100


def derive(p95: int) -> tuple[float, float, float, int]:
    """ADR-014's unchanged rule: band, midpoint, point rounded to the nearest 100."""
    floor, roof = p95 * FLOOR_X, p95 * ROOF_X
    midpoint = (floor + roof) / 2
    return floor, roof, midpoint, round(midpoint / GRANULARITY) * GRANULARITY


# --- the five populations -----------------------------------------------------

def test_the_five_populations_are_what_the_answer_files_produce(rows):
    """Every cell computed from committed evidence, pinned member by member.

    n = 38 at 5241 and n = 70 at 6633 reproduce ADR-074 amendment 3 exactly, so
    the population this reads is the one M08b read."""
    assert len(rows) == 70, f"{len(rows)} answered samples, not the 70 M08b recorded"
    for name, (n, p95, floor, roof, midpoint, point) in POPULATIONS.items():
        population = _population(rows, name)
        assert len(population) == n, f"{name}: n={len(population)}, pinned {n}"
        observed = _p95(population)
        assert observed == p95, f"{name}: p95={observed}, pinned {p95}"
        got_floor, got_roof, got_mid, got_point = derive(observed)
        assert round(got_floor, 2) == floor, f"{name}: floor {got_floor}, pinned {floor}"
        assert round(got_roof, 2) == roof, f"{name}: roof {got_roof}, pinned {roof}"
        assert round(got_mid, 3) == midpoint, f"{name}: midpoint {got_mid}, pinned {midpoint}"
        assert got_point == point, f"{name}: point {got_point}, pinned {point}"


def test_the_populations_partition_the_run_rather_than_overlapping_it(rows):
    """`mandated shape` and `above mandate` are disjoint and exhaust the run.

    Without this the table could carry five plausible rows over one badly
    computed filter, and every number in it would still 'reproduce'."""
    mandated = {r["id"] for r in _population(rows, "mandated shape")}
    above = {r["id"] for r in _population(rows, "above mandate")}
    assert not mandated & above
    assert mandated | above == {r["id"] for r in rows}
    assert not any(r["calls"] < r["mandated"] for r in rows), (
        "a sample answered in fewer calls than its case mandates would sit in neither "
        "population, and the two would stop exhausting the run")


# --- the condition ------------------------------------------------------------

def test_the_condition_does_not_hold_under_any_population(rows):
    """Reading 2 — the number the gate prints, against the point derived from
    each population. Not one of the five fires."""
    pooled = _p95(_population(rows, "pooled"))
    assert pooled == 6633
    for name in POPULATIONS:
        _, _, _, point = derive(_p95(_population(rows, name)))
        assert pooled <= point, (
            f"{name}: the derived point is {point} and the run reads {pooled}, which is "
            f"OVER it — the condition FIRES under this population and the gate may move. "
            f"That is a live decision, not a test failure: take it to the seats.")


#: Below this p95, rounding to the nearest 100 can put the derived point AT or
#: BELOW the p95 it came from, and the same-population reading stops being
#: unsatisfiable. `1.375·p` exceeds `p` by `0.375·p`; rounding moves the point by
#: at most 50; so the guarantee needs `0.375·p > 50`, i.e. `p >= 134`. Measured
#: below rather than trusted — the first version of this test asserted the
#: property for **any** positive p95 and the sweep refused it at p95 = 1 (point
#: 0) and again at p95 = 100 (point 100, equal). ADR-075 amendment 1 §4 states it
#: as unconditional; it is unconditional on the UNROUNDED midpoint and bounded on
#: the rounded point, and the spec is corrected to say so.
#:
#: **Pinned as a literal and checked against its derivation**, because the
#: deletability audit moved it 134 -> 400 with the suite green: every assertion
#: around it is one-sided, so the floor could drift upward without limit, and a
#: floor higher than the mechanism needs quietly widens the region the test
#: declares unguaranteed. The literal stays so a reader sees the number; the
#: derivation below is what makes it true.
ROUNDING_SAFE_P95 = 134


def test_the_unrounded_midpoint_is_strictly_above_its_own_p95():
    """Reading 1, the half that is unconditional.

    The point is the midpoint of `[1.15·p95, 1.60·p95]`, which is `1.375·p95`,
    strictly above the p95 it came from for **any** positive p95. So the run that
    population came from can never read OVER the point derived from it, and the
    same-population reading of the condition is unsatisfiable by construction.
    A rule that cannot fire is not a rule, and this is the half of the finding
    that outlives the data."""
    for p95 in list(range(1, 12000, 7)) + [3769, 5241, 5683, 6633, 7223, 8437]:
        _, _, midpoint, _ = derive(p95)
        assert midpoint > p95, f"p95={p95} derives a midpoint of {midpoint}"


def test_the_rounded_point_is_above_its_own_p95_only_above_a_stated_floor():
    """Reading 1, the half that is bounded — and the correction to §4's wording.

    Rounding to the nearest 100 can drop the point to or below its own p95 when
    the p95 is small: p95 = 1 derives **0**, and p95 = 100 derives **100**, equal
    rather than above. So *unsatisfiable by construction* is true of the
    unrounded midpoint unconditionally and of the derived point only for
    `p95 >= 134`.

    It changes nothing here — every latency this repository has ever recorded is
    in the thousands, and the whole five-population table sits three orders of
    magnitude above the floor — but a property asserted more broadly than it
    holds is a stated protection that is absent, and the next milestone inherits
    the sentence rather than the data."""
    for p95 in range(ROUNDING_SAFE_P95, 12000, 7):
        _, _, _, point = derive(p95)
        assert point > p95, f"p95={p95} derives a point of {point}, which is not above it"
    below = [p for p in range(1, ROUNDING_SAFE_P95) if derive(p)[3] <= p]
    assert below, (
        "no p95 below the stated floor breaks the property, so the floor is unnecessary "
        "and the unconditional claim would be correct — delete the floor and say so")
    assert min(POPULATIONS[name][1] for name in POPULATIONS) > ROUNDING_SAFE_P95 * 10, (
        "a measured population has come within an order of magnitude of the rounding "
        "floor; the bound stops being a footnote and becomes a live constraint")


def test_the_rounding_floor_is_derived_from_the_rule_rather_than_chosen():
    """**The audit moved `ROUNDING_SAFE_P95` from 134 to 400 and nothing noticed.**

    Every other assertion about it is one-sided — the sweep above it still holds,
    a breaking p95 still exists below it, the populations are still clear of it —
    so the floor could be raised without limit, and each raise silently widens the
    band of p95 values the suite declares *unguaranteed* while saying nothing has
    changed. The number is the smallest integer for which the guarantee is
    available, and it follows from exactly two things `derive` already knows: the
    midpoint's excess over its own p95, and the most rounding can take away.

    Written as a derivation rather than a second literal so that moving the BAND
    (ADR-014's `1.15`/`1.60`) or the rounding granularity moves the floor with it.
    A bound that does not track the mechanism it bounds is the stale-sentence
    shape this milestone has paid for four times."""
    excess = (FLOOR_X + ROOF_X) / 2 - 1              # 0.375 -- how far the midpoint clears p95
    worst_rounding = GRANULARITY / 2                 # 50 -- the most rounding can take back
    assert math.floor(worst_rounding / excess) + 1 == ROUNDING_SAFE_P95, (
        f"ROUNDING_SAFE_P95 is {ROUNDING_SAFE_P95}; the band ({FLOOR_X}, {ROOF_X}) "
        f"rounded to {GRANULARITY} makes the guarantee available from "
        f"{math.floor(worst_rounding / excess) + 1}. A floor above its own derivation "
        f"declares a band of p95 values unguaranteed that is not.")

    # ...and the derivation is sufficient, not merely arithmetic: AT the floor the
    # property holds, and the guarantee it rests on is the one stated.
    assert derive(ROUNDING_SAFE_P95)[3] > ROUNDING_SAFE_P95
    assert excess * ROUNDING_SAFE_P95 > worst_rounding


def test_no_population_meets_the_rules_own_selection_criterion(rows):
    """**The finding that is stronger than the condition's outcome.**

    ADR-014 amendment 3 recorded the fact that made the last derivation
    survivable: *"The rule takes the only population under which the run in view
    fails the gate."* Here every one of the five reads *within* the point derived
    from it, so the criterion selects nothing. The rule's own selection rule has
    no solution on this data — which is what a failed premise looks like when you
    try to re-apply the rule that rested on it."""
    pooled = _p95(_population(rows, "pooled"))
    failing = [name for name in POPULATIONS
               if pooled > derive(_p95(_population(rows, name)))[3]]
    assert failing == [], (
        f"population(s) {failing} now leave the run OVER the point derived from them, so "
        "the rule's selection criterion has a solution again. ADR-014 amendment 4 "
        "withdrew the stability sentence on the finding that it had none — re-open it "
        "rather than moving the gate on this.")


def test_the_gate_did_not_move(rows):
    """`gates.budgets.p95_ms` is 5200, and this diff did not move it.

    The condition not firing is the whole reason. SPEC/09 constraint 1 permits a
    move **if and only if** the condition yields one, and *What must not happen*
    forbids a number *"derived from a pooled p95 or from a population under which
    the run it came from would read within"* — which, on this data, is all five."""
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["gates"]["budgets"]["p95_ms"] == CEILING_MS, (
        f"p95_ms is {manifest['gates']['budgets']['p95_ms']}, not {CEILING_MS}. The "
        "condition did not fire, so nothing in this milestone authorises a move.")
    mandated_point = derive(_p95(_population(rows, THE_RULES_POPULATION)))[3]
    assert mandated_point == 7200 and mandated_point > CEILING_MS, (
        "the point the rule would derive is recorded beside the number that stands, so a "
        "reader can see what was NOT taken and why")


def test_the_records_that_digest_the_manifest_were_not_re_produced():
    """The conditional half of the Definition of done, resolved to its stricter
    branch.

    `milestones/M08/context-census.json` and `milestones/M08b/fresh-join.json`
    both carry `services/highlights-agent/pave.manifest.yaml` in `inputs_sha256`.
    The spec re-produces them **if and only if** the manifest moves; it did not,
    so both must still carry the digest of the committed manifest. This asserts
    the branch was taken rather than trusting that it was."""
    import hashlib
    digest = hashlib.sha256(
        MANIFEST.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")).hexdigest()
    for record in (ROOT / "milestones" / "M08" / "context-census.json",
                   ROOT / "milestones" / "M08b" / "fresh-join.json"):
        inputs = json.loads(record.read_text(encoding="utf-8"))["inputs_sha256"]
        assert inputs["services/highlights-agent/pave.manifest.yaml"] == digest, (
            f"{record.name} digests a manifest that is not the committed one. Either the "
            "manifest moved in a PR that may not move it, or the record was re-produced "
            "for a condition that did not fire.")


# --- the population, named by cardinality and provenance ----------------------
#
# **Decision 5 §4 said "the most recent fresh mandated-shape population", and that
# admits two readings.** Read as the most recent RUN SET, it is the mandated-shape
# rows of every sample of M08b's fresh run: n = 38. Read as the most recent
# SAMPLE, it is sample 3 alone: n = 14 -- and under that reading the condition
# FIRES and yields a point 1000 ms above the standing gate.
#
# The wording is corrected in ADR-075 decision 5 §4 and the single-sample reading
# is recorded there as considered and refused. These two tests are what make that
# a WORDING fix rather than a claim rewritten to match an outcome: the answer is
# 5200 under the five-population table AND under the corrected wording, so the
# narrowing runs fail-closed. Had it changed the answer, it would not be
# admissible -- a condition re-worded into a different result is the condition
# being chosen after the fact -- and the milestone would close red.

#: The corrected wording, executable: every sample of the run set, mandated-shape
#: rows only. Pinned so that re-reading it as one sample is a changed number here
#: rather than a changed sentence somewhere else.
RUN_SET_N = 38
SAMPLES = (1, 2, 3)

#: What the single-sample reading produces, as measured. Recorded because the
#: refusal has to carry its number: a reading refused without one is refused on
#: taste, and the next reader re-derives it.
SAMPLE_3_MANDATED_N = 14
SAMPLE_3_MANDATED_P95 = 4542
SAMPLE_3_DERIVED_POINT = 6200
SAMPLE_3_POOLED_P95 = 6315

#: Any population whose p95 falls strictly inside this window derives a point the
#: run's pooled p95 reads OVER, and the condition fires. The five-population table
#: never searched it -- every one of the five sits outside, which is why the table
#: could report "the condition holds under none of the five" and be true and
#: incomplete at the same time.
FIRING_WINDOW = (3782, 4824)


def _mandated(rows: list[dict], sample: int | None = None) -> list[dict]:
    population = _population(rows, "mandated shape")
    return [r for r in population if sample is None or r["sample"] == sample]


def test_the_corrected_wording_names_the_population_the_table_evaluated(rows):
    """**The wording fix, and the proof that it is only a wording fix.**

    The corrected sentence names the population by cardinality and provenance --
    the mandated-shape rows of every sample of the most recent fresh run set,
    M08b's, n = 38 -- rather than by an adjective two readings satisfy. This
    asserts that the population so named is the one the five-population table's
    first row already evaluated, so the correction moves no number: same n, same
    p95, same derived point, same outcome, same gate."""
    population = _mandated(rows)
    assert len(population) == RUN_SET_N, (
        f"the corrected wording names a population of {len(population)}, and the "
        f"table's mandated-shape row is {RUN_SET_N}. A wording fix that changes the "
        f"population is not a wording fix.")
    assert {r["sample"] for r in population} == set(SAMPLES), (
        "the run set is not every sample of the run -- the corrected wording says "
        "EVERY sample, and that is the half that refuses the single-sample reading")

    n, p95, floor, roof, midpoint, point = POPULATIONS["mandated shape"]
    assert _p95(population) == p95 and n == RUN_SET_N
    assert derive(_p95(population))[3] == point

    # ...and therefore the same answer. `pooled > point` is the condition.
    pooled = _p95(_population(rows, "pooled"))
    assert not pooled > point, (
        f"under the corrected wording the condition FIRES ({pooled} > {point}). It "
        f"does not fire under the table, so the correction would have changed the "
        f"answer -- which makes it a re-derivation dressed as a clarification, and "
        f"the milestone closes red rather than taking it.")
    assert yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))["gates"]["budgets"][
        "p95_ms"] == CEILING_MS


def test_the_single_sample_reading_fires_and_is_refused_with_its_number(rows):
    """**The reading the correction closes, recorded rather than deleted.**

    Sample 3's mandated-shape rows alone: n = 14, p95 4542, derived point 6200 --
    and the run's pooled p95 for that sample is 6315, which reads OVER. The
    condition fires and hands back a gate 1000 ms above the standing 5200. That is
    the trade G9 exists to refuse, reached entirely through a reading of the
    condition's own words.

    It is refused by cardinality and provenance, not by preference: a single
    sample is not a population for this rule. The numbers are asserted here so the
    refusal carries them -- a reading refused without its number is refused on
    taste, and the next reader has to re-derive it to find out whether the refusal
    was safe."""
    sample_3 = _mandated(rows, sample=3)
    assert len(sample_3) == SAMPLE_3_MANDATED_N
    assert _p95(sample_3) == SAMPLE_3_MANDATED_P95
    assert derive(SAMPLE_3_MANDATED_P95)[3] == SAMPLE_3_DERIVED_POINT

    pooled_3 = _p95([r for r in rows if r["sample"] == 3])
    assert pooled_3 == SAMPLE_3_POOLED_P95
    assert pooled_3 > SAMPLE_3_DERIVED_POINT, (
        "sample 3 alone no longer fires the condition. The refusal in ADR-075 "
        "decision 5 §4 rests on it firing -- if it stopped, the record is stale and "
        "says the wrong thing about why the wording was narrowed.")
    assert SAMPLE_3_DERIVED_POINT > CEILING_MS, (
        "the single-sample reading no longer moves the gate upward, so the reason "
        "given for refusing it is no longer the reason it was refused")

    # The narrowing runs FAIL-CLOSED: every single-sample reading is excluded, and
    # excluding them leaves the gate where it is rather than moving it.
    for sample in SAMPLES:
        assert len(_mandated(rows, sample=sample)) < RUN_SET_N, (
            f"sample {sample} alone is the whole run set, so the corrected wording "
            f"does not actually narrow anything")


def test_the_five_population_table_never_searched_the_firing_window(rows):
    """**Why the table could be true and incomplete at once.**

    The condition fires for any population whose p95 lands strictly inside
    (3782, 4824) -- below that the derived point sits under the pooled reading for
    a different reason, above it the point clears the pooled p95. All five of the
    table's populations sit outside that window, so *"the condition holds under
    none of the five"* was true and told nobody that a sixth reading of the same
    sentence lands inside it.

    Asserted rather than narrated, so that a future population drifting into the
    window is a red test and not a paragraph nobody re-read."""
    low, high = FIRING_WINDOW
    for name in POPULATIONS:
        p95 = _p95(_population(rows, name))
        assert not low < p95 < high, (
            f"population {name!r} has p95 {p95}, inside the firing window "
            f"{FIRING_WINDOW}. The condition now fires under a population the table "
            f"reports as not firing: the table and the rule disagree, and that is a "
            f"live decision for the seats rather than a test to relax.")
    assert low < SAMPLE_3_MANDATED_P95 < high, (
        "the recorded single-sample p95 is no longer inside the window the refusal "
        "names, so one of the two is wrong")
