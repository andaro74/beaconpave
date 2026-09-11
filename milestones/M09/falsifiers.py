#!/usr/bin/env python
"""M09's five falsifiers, read from the committed runs rather than from a sentence.

SPEC/09 pre-registered five falsifiers before the branch was cut. This reader
evaluates the four PR 4 is responsible for against the two committed disclosure
runs and the two gate transcripts, and says which fired. **F4 is PR 4b's and is
not read here** — it needs the goldens control run, which PR 4 does not take — so
it is printed as DEFERRED rather than as passing, because a falsifier reported
clean by a reader that cannot see its evidence is the vacuous pass this repository
has met in four places.

**Majority against majority** (SPEC/09, *The one claim*): a case's verdict is what
2 of its 3 samples say. The per-sample detail is printed beside every case anyway,
because F1 fired on a case whose three samples disagree and a reader deciding
whether to believe the reading needs to see that for itself.

Zero model calls. Every input is committed.

Owning seats: AI Quality (what a verdict means) - PM (the falsifiers).
"""
from __future__ import annotations

import json
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from evals.deterministic import Scorer  # noqa: E402

PACK = ROOT / "services" / "highlights-agent" / "evals" / "disclosure" / "cases.yaml"
CATALOG = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
PRE = [HERE / f"disclosure-pre-fix-{n}.json" for n in (1, 2, 3)]
POST = [HERE / f"disclosure-post-fix-{n}.json" for n in (1, 2, 3)]


def cases() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8")) or []


def mode(case: dict) -> str | None:
    """`required` (a disclosure is owed) or `not_required` (it is not)."""
    for assertion in case.get("asserts") or []:
        if "ai_disclosure" in assertion:
            spec = assertion["ai_disclosure"]
            return next(iter(spec)) if isinstance(spec, dict) else spec
    return None


def per_sample(paths: list[pathlib.Path]) -> dict[str, list[bool]]:
    """Each case's pass/fail on each sample, scored by the suite's own scorer.

    The scorer, not a re-implementation: a falsifier read by a second scoring path
    is a falsifier about that path. `pave evals disclosure` k-samples in the lane
    and this does the same thing one level up, which is why the per-case results
    here reproduce the committed verdicts exactly.
    """
    scorer = Scorer(root=ROOT)
    out: dict[str, list[bool]] = {c["id"]: [] for c in cases()}
    for path in paths:
        answers = json.loads(path.read_text(encoding="utf-8"))
        for case in cases():
            record = answers.get(case["id"])
            result = scorer.score_case(case, record, CATALOG)
            out[case["id"]].append(result.result == "PASS")
    return out


def majority(flags: list[bool]) -> bool:
    return sum(flags) * 2 > len(flags)


def disclosure_values(paths: list[pathlib.Path]) -> dict[str, list]:
    """What each case's `ai_disclosure` actually was, per sample.

    `KeyError`-free and absence-distinguishing: the sentinel `"<absent>"` is not a
    value the field can hold, and the difference between absent and null is the
    whole of the negative half (ADR-075 amendment 1 fact 9)."""
    out: dict[str, list] = {c["id"]: [] for c in cases()}
    for path in paths:
        answers = json.loads(path.read_text(encoding="utf-8"))
        for case in cases():
            answer = ((answers.get(case["id"]) or {}).get("answer")) or {}
            # `.get` with the sentinel, not `if key in`: present-and-null must read
            # as `None` and absent as `"<absent>"`, which is exactly what a default
            # gives. The difference between those two is the whole of the negative
            # half (ADR-075 amendment 1 fact 9).
            out[case["id"]].append(answer.get("ai_disclosure", "<absent>"))
    return out


def fired_f5(values: dict[str, list]) -> list[str]:
    """The negative cases that carried a disclosure after the fix.

    **Read on EVERY sample, not by majority, and it is a function so that the
    distinction is testable.** It was inline in `main` and the deletability audit
    measured the consequence: swapping this predicate for a majority reading was
    SILENT at 4313 passed, because the test beside it re-implemented the per-sample
    check rather than calling the reader's. A fix that disclosed on a factual
    entitlement answer one time in three would pass a majority reading and still
    be the disclose-on-everything failure ADR-048 decision 3 names — that is
    exactly the case a majority hides, so the predicate that refuses it has to be
    the one under test."""
    return [cid for cid, seen in values.items()
            if any(v is not None for v in seen)]


def gate_exit(path: pathlib.Path) -> int:
    """The exit code the committed transcript records.

    Read from the transcript rather than re-run, so the number in the record and
    the number this reader reports cannot differ."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("exit "):
            return int(line.split()[1])
    raise AssertionError(f"{path} records no exit code")


def main() -> int:
    pack = cases()
    positives = [c["id"] for c in pack if mode(c) == "required"]
    negatives = [c["id"] for c in pack if mode(c) == "not_required"]
    pre, post = per_sample(PRE), per_sample(POST)
    pre_values, post_values = disclosure_values(PRE), disclosure_values(POST)
    fired: list[str] = []

    print(f"pack: {len(pack)} cases - {len(positives)} require a disclosure, "
          f"{len(negatives)} require its absence")
    print()
    print(f"{'case':<16} {'mode':<13} {'run A (pre-fix)':<22} {'run B (post-fix)':<22}")
    for case in pack:
        cid = case["id"]
        a = "".join("P" if f else "." for f in pre[cid])
        b = "".join("P" if f else "." for f in post[cid])
        print(f"  {cid:<14} {mode(case):<13} {a} -> {'PASS' if majority(pre[cid]) else 'FAIL':<12} "
              f"{b} -> {'PASS' if majority(post[cid]) else 'FAIL'}")
    print()

    # --- F1 ------------------------------------------------------------------
    # Scoped to the POSITIVE half, and the scoping is ADR-075 amendment 2's
    # correction: the negative cases assert the field is NOT disclosed and the
    # service already does not disclose, so unscoped F1 fires on them in every
    # possible world and measures nothing.
    f1 = [cid for cid in positives if majority(pre[cid])]
    print(f"F1  any POSITIVE case passes before the fix ....... "
          f"{'FIRED' if f1 else 'clean'}")
    for cid in f1:
        print(f"      {cid}: {sum(pre[cid])} of {len(pre[cid])} samples passed run A")
        for i, value in enumerate(pre_values[cid], 1):
            print(f"        sample {i}: {value!r}")
    if f1:
        fired.append(f"F1 on {', '.join(f1)}")
    # And the near miss, printed because a sample that passed on a case that
    # failed by majority is the same mechanism one vote short.
    near = [cid for cid in positives if any(pre[cid]) and not majority(pre[cid])]
    for cid in near:
        print(f"      (near miss) {cid}: {sum(pre[cid])} of {len(pre[cid])} samples passed, "
              f"so it fails by majority and F1 does not fire on it")

    # --- F2 ------------------------------------------------------------------
    f2 = [cid for cid in positives if not majority(post[cid])]
    print(f"F2  any positive case fails after the fix ......... "
          f"{'FIRED' if f2 else 'clean'}")
    if f2:
        fired.append(f"F2 on {', '.join(f2)}")
    imperfect = [cid for cid in positives if not all(post[cid])]
    for cid in imperfect:
        print(f"      (not 3-of-3) {cid}: {sum(post[cid])} of {len(post[cid])}; "
              f"values {post_values[cid]!r}")

    # --- F3 ------------------------------------------------------------------
    pre_exit = gate_exit(HERE / "gate-pre-fix.txt")
    post_exit = gate_exit(HERE / "gate-post-fix.txt")
    f3 = pre_exit != 1 or post_exit != 0
    print(f"F3  the gate does not block then permit ........... "
          f"{'FIRED' if f3 else 'clean'}   (pre exit {pre_exit}, post exit {post_exit})")
    if f3:
        fired.append(f"F3: pre exit {pre_exit}, post exit {post_exit}")

    # --- F4 ------------------------------------------------------------------
    print("F4  the fix moved something else ................. DEFERRED to PR 4b")
    print("      needs the goldens control run at k=3, which PR 4 does not take. Reported "
          "as deferred and NOT as clean.")

    # --- F5 ------------------------------------------------------------------
    f5 = fired_f5({cid: post_values[cid] for cid in negatives})
    print(f"F5  a negative case carries a disclosure after the fix  "
          f"{'FIRED' if f5 else 'clean'}")
    for cid in negatives:
        print(f"      {cid}: {post_values[cid]!r}")
    if f5:
        fired.append(f"F5 on {', '.join(f5)}")

    print()
    if fired:
        print("CLAIM: FAILED - " + "; ".join(fired))
        print("SPEC/09: a red claim stops the claim's reading and nothing else. The close "
              "writes the cross and names the case.")
    else:
        print("CLAIM: the four falsifiers PR 4 can read are clean; F4 decides it at PR 4b.")
    # Exit 0 either way: this reader REPORTS the falsifiers. A non-zero exit would
    # make a correctly-recorded red close fail `make check`, which is how a red
    # gets quietly dropped.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
