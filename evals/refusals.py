"""
SPEC/01's guardrail-refusal band, asserted at suite level over committed runs.

SPEC/01 pre-registered **0–2 refused golden cases per run as expected, and ≥3 as a
miscalibrated guardrail — M01's finding rather than M04's surprise.** Until M03
that band was printed by `run_via_gateway.py` at run time and read by whoever was
watching. A threshold nobody re-evaluates is a threshold that only ever fires
once.

**Reporting only. This blocks nothing.** It sets no score, enters no verdict, and
is consumed by no gate. `tests/test_refusal_band.py` asserts that too, because
"reporting only" is a property that decays silently the first time somebody finds
it convenient. What the tests *do* assert is that the counts have not moved
without the record moving with them — a band with no assertion behind it is prose,
and prose is how M01's five phrasings ended up frozen under a guardrail version
that no longer existed.

**The mechanism is kept, never summed away.** A guardrail refusal and a
classification denial are different controls with different owners, and M03 found
the distinction load-bearing: three of the held-out judge refusals were the
classifier responding to a defect in the *instrument*, not the guardrail refusing
a topic. A single `refused` count would have sent that finding to the wrong seat.

Hermetic. Owning seats: Security / Red Team (the guardrail's configuration and
what a breach means) · AI Quality (that a recorded count cannot drift unnoticed).
"""
from __future__ import annotations

import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: SPEC/01, pre-registered before M01 ran. Inclusive upper bound: 2 is expected, 3
#: is a finding.
BAND = (0, 2)

#: Every committed golden run, listed rather than globbed, with whether a gateway
#: existed when it was produced. `m00b` is the **negative control for this sweep**:
#: it ran with no gateway, no guardrail and no classifier, so its count must be
#: exactly zero. Without it, "governed runs breach the band" would be a claim this
#: module could satisfy by counting nothing at all.
RUNS = (
    ("m00b", "milestones/M00b/goldens-run.json", False),
    ("m01", "milestones/M01/goldens-run.json", True),
    ("m02-control-1", "milestones/M02/runs/m02-control-1.json", True),
    ("m02-control-2", "milestones/M02/runs/m02-control-2.json", True),
    ("m02-control-3", "milestones/M02/runs/m02-control-3.json", True),
    ("m02-tools-1", "milestones/M02/runs/m02-tools-1.json", True),
    ("m02-tools-2", "milestones/M02/runs/m02-tools-2.json", True),
    ("m02-tools-3", "milestones/M02/runs/m02-tools-3.json", True),
)

#: What the runs above actually contain, as measured. Committed so a change to a
#: run file, or to how a refusal is recorded in one, fails a test rather than
#: quietly restating the finding. These are counts of *golden cases refused*, not
#: of judge calls — the judge's own refusals are a different population and live in
#: `guardrail_refusals` on the judged history entry.
OBSERVED = {
    "m00b": {},
    "m01": {"guardrail": 3},
    "m02-control-1": {"guardrail": 5},
    "m02-control-2": {"guardrail": 6},
    "m02-control-3": {"guardrail": 8},
    "m02-tools-1": {"guardrail": 2},
    "m02-tools-2": {"guardrail": 3},
    "m02-tools-3": {"guardrail": 2},
}


def census(path: str | pathlib.Path) -> dict:
    """Refused golden cases in one committed run, by mechanism.

    Read from the recorded answer rather than recomputed: whether a control
    refused a case is a fact about the run that happened, and re-deriving it from
    the text would be this harness's opinion about a call it did not make."""
    answers = json.loads((ROOT / path).read_text(encoding="utf-8"))
    mechanisms: collections.Counter = collections.Counter()
    for record in answers.values():
        answer = record.get("answer")
        if isinstance(answer, dict) and "refused_by_gateway" in answer:
            mechanisms[answer["refused_by_gateway"]] += 1
    return dict(sorted(mechanisms.items()))


def breaches(total: int) -> bool:
    return total > BAND[1]


def sweep() -> list[dict]:
    """Every committed run against the band, in a deterministic order."""
    out = []
    for label, path, governed in RUNS:
        mechanisms = census(path)
        total = sum(mechanisms.values())
        out.append({
            "run": label,
            "governed": governed,
            "mechanisms": mechanisms,
            "refused": total,
            "breaches": breaches(total),
        })
    return out


def render(rows: list[dict] | None = None) -> str:
    """The band as a human reads it. Called by nothing that scores anything."""
    rows = rows if rows is not None else sweep()
    lines = [f"SPEC/01 guardrail-refusal band: {BAND[0]}-{BAND[1]} expected, "
             f">{BAND[1]} is a miscalibrated guardrail (reporting only)"]
    for row in rows:
        state = "BREACH" if row["breaches"] else ("within" if row["governed"] else "ungoverned")
        lines.append(f"  {row['run']:16} {row['refused']:2} refused  {state:10} "
                     f"{row['mechanisms'] or ''}")
    governed = [r for r in rows if r["governed"]]
    breaching = [r for r in governed if r["breaches"]]
    lines.append(f"  {len(breaching)} of {len(governed)} governed runs breach the band")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())


#: Which estimator ADR-035 rows 7 and 8 are judged against, fixed in an amendment
#: **before** the spend so it cannot be chosen after seeing the data.
#:
#: Row 8's own words are "refuse AT LEAST ONCE". `evals/run_evals.py::summarise`
#: aggregates k samples by per-case MAJORITY. Both are defensible and they are not
#: the same number: on the three committed M02 control runs they are 8 of 25 and
#: 6 of 25, and the cases that separate them are `brand-020` and `recommend-013`,
#: each refused on exactly one sample of three.
#:
#: (The AI Quality seat's review named a third, `concise-022`. It was refused on
#: two samples of three, so majority catches it and it separates nothing — the
#: seat's counts, 8 and 6, were right and its list of names had one too many.
#: Recorded because `test_the_two_estimators_differ_on_the_committed_runs` pins
#: the names as well as the counts, and a reader comparing the two would
#: otherwise think this file had drifted.)
#:
#: At-least-once is the one that survives this repo's own evidence. The control
#: this measures is stochastic: it returned different verdicts on identical input
#: in 4 of 25 anchor cases, and `PHR-004` — the product's most basic question —
#: was blocked in 1 of 3 identical calls. A guardrail that refuses the basic
#: question one time in three is a finding, and majority reports it as a
#: non-event. Recording both is not hedging; it is so that a reader can see the
#: gap the choice was made across.
ADR_035_ESTIMATOR = "refused_at_least_once"


def census_from_samples(per_sample: dict[str, list], k: int) -> dict:
    """Both estimators over one k-sample run, computed rather than asserted.

    **This exists because an ADR cannot compute a number and a harness can.**
    Fixing the estimator in prose and then hand-counting the run afterwards is
    choosing it after seeing the data, which is the door a pre-registration is
    there to close. So the run writes both numbers, before anybody reads them,
    and the ADR says which one it is judged against.

    It also lives here rather than in the runner because the runner imports
    boto3 and this must be provable on a fresh clone with no account — the same
    split `core/` and `handler.py` make one layer down. The runner calls it; the
    hermetic suite checks it against the committed M02 runs, where the answer is
    already known.

    `per_sample` maps a case id to one entry per sample: `True` refused, `False`
    answered, `None` for a sample the harness never got — a call that failed is
    not evidence that the case was answered, and counting it as a non-refusal
    would flatter the number by exactly the calls that went wrong."""
    if k < 1:
        raise ValueError(f"k={k}; a case needs at least one sample")

    at_least_once, majority, unanimous, incomplete = [], [], [], []
    for case, samples in per_sample.items():
        seen = [s for s in samples if s is not None]
        if len(seen) < k:
            incomplete.append(case)
        if any(seen):
            at_least_once.append(case)
        # Majority is over the samples that HAPPENED, and `needed` is derived from
        # `k` rather than from `len(seen)`: a case with one lost sample must not
        # become easier to call refused than one with three.
        if sum(bool(s) for s in seen) > k // 2:
            majority.append(case)
        if seen and all(seen) and len(seen) == k:
            unanimous.append(case)

    return {
        "k": k,
        "n_cases": len(per_sample),
        "refused_at_least_once": len(at_least_once),
        "refused_by_majority": len(majority),
        "refused_unanimously": len(unanimous),
        "cases_at_least_once": sorted(at_least_once),
        "cases_by_majority": sorted(majority),
        # The cases the choice of estimator actually turns on. Printed so the gap
        # is visible in the artifact rather than reconstructable from it.
        "cases_separating_the_estimators": sorted(set(at_least_once) - set(majority)),
        # A run with lost samples is not a k-sample run, and the number must say
        # so rather than quietly being taken over fewer.
        "cases_with_missing_samples": sorted(incomplete),
        "estimator_for_adr_035": ADR_035_ESTIMATOR,
    }


def samples_from_runs(paths) -> dict[str, list]:
    """`per_sample` built from several committed answer files — one file per
    sample, which is M02's convention.

    Deliberately keyed on the union of case ids across the files rather than on
    the first file's: a case missing from one sample is a lost sample, not an
    absent case, and the distinction is what `cases_with_missing_samples`
    reports."""
    runs = [json.loads((ROOT / p).read_text(encoding="utf-8")) for p in paths]
    cases = sorted({case for run in runs for case in run})
    per_sample: dict[str, list] = {}
    for case in cases:
        row = []
        for run in runs:
            record = run.get(case)
            if record is None:
                row.append(None)
                continue
            answer = record.get("answer")
            row.append(isinstance(answer, dict) and "refused_by_gateway" in answer)
        per_sample[case] = row
    return per_sample
