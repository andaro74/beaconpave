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


def derive(p95: int) -> tuple[float, float, float, int]:
    """ADR-014's unchanged rule: band, midpoint, point rounded to the nearest 100."""
    floor, roof = p95 * FLOOR_X, p95 * ROOF_X
    midpoint = (floor + roof) / 2
    return floor, roof, midpoint, round(midpoint / 100) * 100


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
