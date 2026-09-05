"""The survivor census, re-derived — the check nobody was running.

**Why this file exists.** `docs/M06b-guardrail-diagnosis.md` carried, for four
documents and three ADRs, the claim that *"stating the verdict is what trips it —
the survivors survive by failing earlier."* A single case in the committed runs
contradicts it, and it had been sitting there the whole time. The AI Quality seat
found it by re-deriving the census by hand, because **eleven of the M06b run files
have no reader in this suite at all** and nothing computed what the documents
asserted.

That is the shape ADR-041 recorded and these tests were written for one directory
over: a recorded number with no reader is a number nobody notices going stale.
Here it was worse — a number nobody notices being *wrong from the start*.

**What is pinned, and why it cannot expire.** The three run files are committed
evidence of runs that happened. They are append-only by the same argument history
is: a run is not re-run, it is superseded. So a fact derived from them is stable by
construction, and this is not a guard coupled to data that legitimately moves.

Hermetic (G8): committed JSON only, no cloud and no network.
Owning seat: AI Quality (what a recorded number is allowed to claim).
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS = sorted((ROOT / "milestones" / "M06b").glob("goldens-run-[0-9].json"))

#: The scored run's census, derived from the three committed files and pinned so
#: the documents quoting it have a reader. `refused` counts cases whose answer is
#: a gateway refusal; `retrieved` counts survivors that cited at least one title.
CENSUS = {
    "goldens-run-1.json": {"cases": 25, "refused": 16, "retrieved": 4},
    "goldens-run-2.json": {"cases": 25, "refused": 17, "retrieved": 2},
    "goldens-run-3.json": {"cases": 25, "refused": 17, "retrieved": 3},
}

#: The case that refutes the mechanism, and the three properties that do it.
#:
#: It retrieved a title, called `entitlement-check`, stated the verdict in its
#: answer, and was **not refused** — in every run. Any one of those being false
#: would make it a different case and the correction would need re-deriving.
WITNESS = "headroom-026"


def _run(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _refused(record: dict) -> bool:
    answer = record.get("answer")
    return isinstance(answer, dict) and "refused_by_gateway" in answer


def test_the_three_scored_runs_are_all_present():
    assert [p.name for p in RUNS] == sorted(CENSUS), (
        f"the committed scored runs are {[p.name for p in RUNS]}, the census names "
        f"{sorted(CENSUS)}. A run file that disappears takes every number derived from "
        "it with it, and four documents quote these.")


@pytest.mark.parametrize("name", sorted(CENSUS))
def test_the_census_is_what_the_committed_run_holds(name):
    run = _run(ROOT / "milestones" / "M06b" / name)
    expected = CENSUS[name]

    assert len(run) == expected["cases"]
    refused = [case for case, record in run.items() if _refused(record)]
    assert len(refused) == expected["refused"], (
        f"{name}: {len(refused)} refused, census says {expected['refused']}")

    survivors = {case: record for case, record in run.items() if not _refused(record)}
    retrieved = [case for case, record in survivors.items()
                 if (record.get("answer") or {}).get("cited_titles")]
    assert len(retrieved) == expected["retrieved"], (
        f"{name}: {len(retrieved)} of {len(survivors)} survivors retrieved a title, census "
        f"says {expected['retrieved']}. This is the number 'the survivors survive by "
        "failing earlier' was asserted over, and it was never computed.")


@pytest.mark.parametrize("name", sorted(CENSUS))
def test_the_witness_against_the_verdict_mechanism_is_still_in_every_run(name):
    """`headroom-026` retrieved, stated a verdict, and was allowed. Three for three.

    `docs/M06b-guardrail-diagnosis.md` Correction 3 rests on this case. It is
    pinned rather than quoted so the correction cannot drift away from the
    evidence the way the claim it corrects did — that claim survived four
    documents and three ADRs with its own counterexample committed beside it."""
    record = _run(ROOT / "milestones" / "M06b" / name).get(WITNESS)
    assert record is not None, f"{name} no longer holds {WITNESS}"

    assert not _refused(record), (
        f"{name}: {WITNESS} is recorded as refused. Correction 3's whole argument is that "
        "it was ALLOWED while retrieving and stating a verdict.")
    answer = record.get("answer") or {}
    assert answer.get("cited_titles"), (
        f"{name}: {WITNESS} cites no title, so it no longer shows that retrieval succeeded.")
    entitlement = answer.get("entitlement") or {}
    assert entitlement.get("source") == "entitlement-check", (
        f"{name}: {WITNESS} carries no entitlement verdict from the tool, so it no longer "
        "shows that a verdict was stated and allowed.")


def test_no_survivor_population_is_mistaken_for_the_whole_suite():
    """The branch's signature error, asserted as a property rather than remembered.

    A refused case writes no answer, so any statistic over "the answers in a run
    file" is a statistic over survivors. This fails if a run is ever recorded with
    every case answered, because at that point the distinction this repository
    corrected three times stops being visible in the evidence and the next person
    reading these files has no reason to look for it."""
    for path in RUNS:
        run = _run(path)
        refused = [case for case, record in run.items() if _refused(record)]
        assert refused, (
            f"{path.name} records no refusals at all. Every earlier reading of these files "
            "turned on the gap between the answers present and the cases run; a file with "
            "no gap needs that stated somewhere a reader will find it.")
        assert len(refused) < len(run), f"{path.name} refused every case"
