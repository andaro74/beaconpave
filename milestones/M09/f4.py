#!/usr/bin/env python
"""M09's F4, read from the committed goldens control run rather than from a sentence.

PR 4 read F1, F2, F3 and F5 and printed **F4 DEFERRED** — it needs the goldens
control run, which PR 4 does not take. This is that reading.

**F4 as SPEC/09 states it, and the order of its clauses matters:**

> the goldens control run shows a ≤3-call answered sample **over 7700** that was
> under it at M08b; **or a case that passed 3-of-3 at M08b fails by majority; or a
> case that failed 0-of-3 at M08b passes by majority**

Three clauses, each of which fails the claim on its own. **The count `N` is not one
of them.** It was moved out of F4 and into *Beside the claim* as a side-prediction
(SPEC/09's falsifier table; ADR-075 amendment 1 §5 ask 3), because `N` is a sum over
25 cases and is insensitive to compensating movement — three cases newly failing and
three newly passing leaves `N` where it was, inside the band, with six cases having
moved. This reader prints `N` **after** the three clauses and labels it, so that a
reader cannot mistake the side-prediction for the falsifier.

**Why this reader exists beside `milestones/M08b/fresh_join.py` rather than inside
it.** `fresh_join.py` is run over this directory and produces
`milestones/M09/fresh-join.json`, which carries clause 1 exactly: its `claim` section
computes every answered ≤3-call sample over the ceiling from the rows, and it is the
committed reader at the committed 7700. But its `count` section compares against
`milestones/M08/rescore-join.json` — **M08's** re-reading — because that is the
comparison M08b needed and the path is a module constant. F4's two direction clauses
are against **M08b**, the run this one is the control for. A reader that took
`fresh-join.json`'s `falsifiers` block at face value would report F4's direction
clauses against the wrong baseline and call it clean. So clause 1 is read out of the
committed record and clauses 2 and 3 are computed here, against the M08b baseline
`evals/history/m08b-tools-goldens.json` publishes.

**The baseline is the published entry, not a list in this file.** Every case's M08b
bracket is read from that entry, which is the one `README_GOLDENS` pins the `m08b`
row to; the named causes are read from `milestones/M08b/fresh-join.json`'s triggers
and `milestones/M08b/goldens-run-refusals.json`'s census. The one hand-held literal
is ADR-074 decision 2's seven browse-gap cases, which no record carries by name;
`tests/test_m09_f4.py` holds it to seven real case ids.

**Nothing here can move a number.** It reads; it writes no record, edits no case, and
takes no ceiling argument. Zero model calls.

Owning seats: AI Quality (what a verdict means) · PM (the falsifiers).
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "milestones" / "M08b"))

import fresh_join  # noqa: E402 — the committed reader, never re-implemented

M08B_ENTRY = ROOT / "evals" / "history" / "m08b-tools-goldens.json"
M08B_JOIN = ROOT / "milestones" / "M08b" / "fresh-join.json"
M08B_REFUSALS = ROOT / "milestones" / "M08b" / "goldens-run-refusals.json"
M09_JOIN = HERE / "fresh-join.json"
M09_SCORE = HERE / "goldens-score.txt"
M09_REFUSALS = HERE / "goldens-run-refusals.json"

#: SPEC/09 *Beside the claim*: `N/25` with 8 ≤ N ≤ 12, predicted 10. A
#: **side-prediction** in all three of its sites. Not F4.
COUNT_BAND = (8, 12)
PREDICTED_N = 10
#: SPEC/01's refusal band, at the ceiling M08b measured. Also a side-prediction.
REFUSAL_BAND = (0, 2)

#: ADR-074 decision 2's seven browse-gap cases, verbatim and by name. The only
#: hand-held list in this file: `fresh-join.json` counts them (`m08_count.cases`:
#: 7) and does not name them, and the M08 journal that does is prose.
#: `tests/test_m09_f4.py::test_the_seven_browse_gap_cases_are_seven_real_cases`
#: holds it.
BROWSE_GAP_SEVEN = ("recommend-003", "recommend-013", "recommend-014",
                    "grounded-018", "grounded-019", "multi-023", "edge-025")


def _load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def m08b_baseline() -> dict[str, list[str]]:
    """Each case's M08b bracket, from the entry `README_GOLDENS` pins the row to.

    The published entry rather than `fresh-join.json`'s `count.per_case`: the
    entry is what the `m08b` row's **10/25** is checked against by
    `pave/history.py::check_readme`, so a baseline read from it cannot disagree
    with the number this run is being compared to.
    """
    return {c["id"]: list(c["samples"]) for c in _load(M08B_ENTRY)["cases"]}


def m09_brackets() -> dict[str, dict]:
    """Each case's M09 majority and bracket, parsed out of the k=3 transcript by
    the committed reader's own parser — not a second parser written here."""
    blocks = fresh_join.parse_transcript(M09_SCORE.read_text(encoding="utf-8"))
    k3 = next((b for b in blocks if b["sample"] is None), None)
    if k3 is None or k3["count"] is None:
        raise SystemExit(f"{M09_SCORE} carries no k=3 block with a count line")
    return {"cases": k3["cases"], "count": k3["count"]}


def majority(samples: list[str]) -> str:
    return "PASS" if samples.count("PASS") * 2 > len(samples) else "FAIL"


def named_causes() -> dict[str, list[str]]:
    """M08b's named causes, each read from the record that names it.

    The question F4's count half asks is not *how many failed* but *did any fail
    for a reason M08b did not already own*. A failure against a named cause is
    the milestone reproducing a debt somebody else holds; a failure against no
    named cause is the prompt delta's, and is the one worth printing loudly.
    """
    join = _load(M08B_JOIN)
    tokens_out = join["triggers"]["tokens_out_five"]
    five = sorted(cid for cid, v in tokens_out["cases"].items() if v["fails_by_majority"])
    widened = sorted(tokens_out["failing_by_majority_outside_the_five"])
    refused = sorted((_load(M08B_REFUSALS).get("census") or {}).get("cases_by_majority") or [])
    return {
        "guardrail_topic_refusal": refused,
        "tokens_out_at_unchanged_tiers": sorted(set(five) | set(widened)),
        "browse_gap": sorted(BROWSE_GAP_SEVEN),
    }


def cause_of(case_id: str, scored: dict, causes: dict[str, list[str]],
             refused_now: list[str]) -> str:
    """Why this case failed **here**, stated against M08b's list.

    Read from the failing asserts the scorer itself printed, in the order the
    causes bite: a refusal happens before scoring; a budget assert is a tier or
    the ceiling; anything else is content. The case's membership in M08b's named
    lists is appended, so a reader sees both what failed and whose debt it is.
    """
    kinds = set(scored.get("asserts") or {})
    budget = (scored.get("asserts") or {}).get("budget", "")
    lists = [name for name, members in causes.items() if case_id in members]
    tail = f" [M08b: {', '.join(lists)}]" if lists else " [M08b: named by no cause]"
    if case_id in refused_now:
        return "refused by the guardrail before scoring" + tail
    if "tokens_in" in budget:
        return f"the ceiling: {budget}" + tail
    if "tokens_out" in budget:
        return f"tokens_out at an unchanged tier: {budget}" + tail
    if kinds:
        return "answer content: " + ", ".join(sorted(kinds)) + tail
    return "no failing assert printed" + tail


# --- F4's three clauses, each a named predicate ------------------------------
# **Functions, not three expressions inside `main`.** The deletability audit
# measured what the inline version bought: a test that recomputes a predicate
# beside the reader stays green when the reader's copy of it is deleted, which is
# the shape ADR-075 amendment 3 §8 found in four checks and the one this file
# would otherwise have shipped. `tests/test_m09_f4.py` calls these; nothing
# re-implements them.

def clause_1(join: dict, m08b_join: dict) -> list[str]:
    """A ≤3-call answered sample over the ceiling **that was under it at M08b**.

    Read out of the record M08b's committed reader wrote over this run: its
    `claim` section computes every answered ≤3-call sample over the ceiling from
    the rows, never from an assertion. The M08b narrowing is applied here, and
    `main` prints the unnarrowed list beside it so a reader can see which of the
    two conditions is doing the work."""
    m08b_over = set(m08b_join["claim"]["3_call_or_fewer_samples_over"])
    return [s for s in join["claim"]["3_call_or_fewer_samples_over"] if s not in m08b_over]


def clause_2(base: dict[str, list[str]], now: dict[str, dict]) -> list[str]:
    """A case that passed **3-of-3 at M08b** and fails by majority here."""
    return [c for c in base
            if all(s == "PASS" for s in base[c]) and now[c]["result"] != "PASS"]


def clause_3(base: dict[str, list[str]], now: dict[str, dict]) -> list[str]:
    """A case that failed **0-of-3 at M08b** and passes by majority here."""
    return [c for c in base
            if all(s == "FAIL" for s in base[c]) and now[c]["result"] == "PASS"]


def same_case_set(base: dict, now: dict) -> None:
    """F4 compares case for case; a baseline missing a case makes every clause
    quietly narrower, and the narrower reading is the clean one."""
    if set(base) != set(now):
        raise SystemExit(f"the baseline names {len(base)} cases and the control run "
                         f"{len(now)}; F4 compares case for case and cannot compare these")


def main() -> int:
    for path in (M09_JOIN, M09_SCORE, M09_REFUSALS):
        if not path.is_file():
            raise SystemExit(f"{path} does not exist; the control run has not been committed")
    join = _load(M09_JOIN)
    base = m08b_baseline()
    k3 = m09_brackets()
    now = k3["cases"]
    causes = named_causes()
    sidecar = _load(M09_REFUSALS)
    refused_now = sorted(c for c, s in (sidecar.get("per_sample_refused") or {}).items()
                         if sum(1 for x in s if x) >= 2)
    fired: list[str] = []

    same_case_set(base, now)

    print(f"ceiling {join['ceiling']}   cases {len(now)}   "
          f"baseline {M08B_ENTRY.relative_to(ROOT).as_posix()} (M08b, "
          f"{sum(1 for c in base.values() if majority(c) == 'PASS')}/{len(base)})")
    print()
    print(f"{'case':<17} {'M08b':<22} {'M09 control':<22} cause, if it fails here")
    for case_id in sorted(now, key=lambda c: list(base).index(c)):
        before, after = base[case_id], now[case_id]["samples"] or []
        cause = "" if now[case_id]["result"] == "PASS" else \
            cause_of(case_id, now[case_id], causes, refused_now)
        print(f"  {case_id:<15} {majority(before):<5}[{' '.join(s[0] for s in before)}]     "
              f"{now[case_id]['result']:<5}[{' '.join(s[0] for s in after)}]     {cause}")
    print()

    claim = join["claim"]
    newly_over = clause_1(join, _load(M08B_JOIN))
    print(f"F4.1  a <=3-call answered sample over {join['ceiling']} that was under it at M08b "
          f"..... {'FIRED' if newly_over else 'clean'}")
    print(f"        {claim['samples_at_3_calls_or_fewer']} samples at <=3 calls, max "
          f"{claim['largest_3_call_or_fewer_tokens_in']}; "
          f"{claim['samples_at_4_calls_or_more']} at >=4, min "
          f"{claim['smallest_4_call_or_more_tokens_in']}")
    for s in newly_over:
        print(f"        {s}")
    if newly_over:
        fired.append(f"F4.1 on {', '.join(newly_over)}")

    regressed = clause_2(base, now)
    print(f"F4.2  a case that passed 3-of-3 at M08b fails by majority "
          f"................. {'FIRED' if regressed else 'clean'}")
    print(f"        {sum(1 for c in base.values() if all(s == 'PASS' for s in c))} cases "
          f"passed 3-of-3 at M08b; all of them are read")
    for c in regressed:
        print(f"        {c}: M08b {base[c]} -> M09 {now[c]['samples']}")
    if regressed:
        fired.append(f"F4.2 on {', '.join(regressed)}")

    flipped = clause_3(base, now)
    print(f"F4.3  a case that failed 0-of-3 at M08b passes by majority "
          f"................ {'FIRED' if flipped else 'clean'}")
    print(f"        {sum(1 for c in base.values() if all(s == 'FAIL' for s in c))} cases "
          f"failed 0-of-3 at M08b; all of them are read")
    for c in flipped:
        print(f"        {c}: M08b {base[c]} -> M09 {now[c]['samples']}")
    if flipped:
        fired.append(f"F4.3 on {', '.join(flipped)}")

    print()
    print("F4    " + ("FIRED - " + "; ".join(fired) if fired else
                      "clean on all three clauses"))
    print()

    # --- and the count, AFTER the falsifier, labelled ------------------------
    n = k3["count"]["passed"]
    in_band = COUNT_BAND[0] <= n <= COUNT_BAND[1]
    print(f"SIDE-PREDICTION (not F4, not the claim)  count N = {n}/{k3['count']['total']} "
          f"against band {list(COUNT_BAND)}, predicted {PREDICTED_N}: "
          f"{'in band' if in_band else 'OUTSIDE THE BAND'}")
    print(f"        M08b was {sum(1 for c in base.values() if majority(c) == 'PASS')}/"
          f"{len(base)}; a miss is a finding about the band and does not fail the claim")
    moved = [c for c in base if majority(base[c]) != now[c]["result"]]
    print(f"        cases whose MAJORITY moved either way: {len(moved)} {sorted(moved)}")
    unnamed = [c for c in now
               if now[c]["result"] != "PASS"
               and not any(c in members for members in causes.values())]
    print(f"        failing cases named by no M08b cause: {len(unnamed)} {sorted(unnamed)}")
    print(f"SIDE-PREDICTION  refused by majority {len(refused_now)}/{len(now)} {refused_now} "
          f"against band {list(REFUSAL_BAND)}: "
          f"{'in band' if len(refused_now) <= REFUSAL_BAND[1] else 'OUTSIDE THE BAND'}")

    print()
    print("THE CLAIM IS FAILED. F1 fired on disclosure-103 at PR 4 (ADR-075 amendment 5) "
          "and a falsified claim is not re-read. F4's reading above is F4's; it does not "
          "offset F1 and no clean reading here makes the claim anything but FAILED.")
    # Exit 0 either way: this reader REPORTS. A non-zero exit would make a
    # correctly-recorded red close fail `make check`, which is how a red gets
    # quietly dropped (milestones/M09/falsifiers.py, same reason).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
