"""
`python -m evals.run_evals` — the deterministic scoring run (ADR-012).

Reads answers a service already produced; it does not produce them. That split
is the point: the model call belongs to the agent (ADR-011 quarantines the
baseline as the only direct-model path), and the scorer stays hermetic, so it can
be proven correct against committed fixtures before any non-deterministic thing
exists.

  python -m evals.run_evals --dryrun
      Resolve fixtures, load every case, validate the assert vocabulary. No
      answers needed and no scores produced.

  python -m evals.run_evals --answers run.json [--record --tag m00b] [--out verdict.json]
      Score, and optionally append a history entry and emit a gate verdict.

  python -m evals.run_evals --answers r1.json --answers r2.json --answers r3.json \
                            --arm tools --record --tag m02
      Score each sample INDEPENDENTLY through the same scorer, then record the
      per-case majority. `k` and `arm` go into the history entry, and the
      per-sample verdicts go in beside them so the majority is checkable rather
      than asserted.

The answers file is `{"<case-id>": {"answer": {...}, "usage": {...}}}`. A case
with no entry scores INFRA — absence blocks, exactly as it does in
`pave gate decide`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys
from dataclasses import replace

import yaml

from evals.deterministic import (
    ADVISORY,
    DEFERRED_ASSERTS,
    FAIL,
    INFRA,
    PASS,
    AssertResult,
    Scorer,
    suite_latency,
    tally,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals" / "history"
#: Read from its own constant rather than from `HISTORY`, so that pointing the
#: entries somewhere else does not also point the validator somewhere it will
#: not find a schema. A validation step that silently stops running is worse
#: than one that was never there.
HISTORY_SCHEMA = ROOT / "evals" / "history" / "schema.json"
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"
CATALOG = ROOT / "data" / "catalog.json"

#: Deliberately unused. The rubric is referenced by every case and read by
#: nothing until M03; naming it here is a reminder that leaving it unread is the
#: decision, not an omission (ADR-012).
RUBRIC = ROOT / "quality" / "judge" / "rubric-sports.md"


def _load(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) if path.suffix in {".yaml", ".yml"} else json.loads(text)


def _git_sha() -> str:
    import subprocess
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False,
        )
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def dryrun(cases: list) -> int:
    catalog = _load(CATALOG)
    print(f"loaded {len(cases)} golden cases, catalog has {len(catalog.get('titles', []))} titles")
    for case in cases:
        for fixture in case.get("fixtures", []):
            if not (ROOT / fixture).is_file():
                print(f"error: {case['id']}: fixture missing: {fixture}", file=sys.stderr)
                return 2
    print("dryrun: OK — fixtures resolve, cases load, no model was called")
    return 0


def _sources(paths) -> list[dict]:
    """Name and hash every answer file an entry was summarised from.

    **Normalised text, not raw bytes (ADR-042).** This hashed `read_bytes()`, and
    on a Windows tree with `core.autocrlf` every digest it ever wrote was of a
    CRLF rendering of an LF blob: seven of the ten `samples_from` records on
    `main` mismatched the committed file, and nothing read them. The same
    function the pin uses, so "has the evidence changed" is a question about
    what it says on every platform."""
    from pave import history
    found = []
    for path in paths:
        text = pathlib.Path(path).read_text(encoding="utf-8")
        found.append({"path": str(path).replace(chr(92), "/"),
                      "sha256": history.entry_digest(text)})
    return found


def write_entry(path: pathlib.Path, entry: dict) -> str:
    """The one writer both recorders use (ADR-042 decision 2). LF on disk so a
    pin taken by hand agrees with the recorder's; the pin written beside the
    entry from the entry's own directory, so `--history-dir` and a monkeypatched
    `HISTORY` carry it; the digest printed, because the previous recorder
    printed only a path and an operator hashing the CRLF file pinned the wrong
    number."""
    from pave import history
    text = json.dumps(entry, indent=2) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    digest = history.write_pin(path, text)
    print(f"pinned: {path.name} {digest}")
    return digest


def _load_superseded(history_dir: pathlib.Path, name: str, suite: str) -> dict:
    """Resolve `--supersedes <filename>` (ADR-042 decision 7). A correction names
    the file it corrects -- the append-only guard's key -- not a SHA, which
    identifies one to N entries and already identifies three."""
    target = history_dir / name
    if "/" in name or "\\" in name or not target.is_file():
        raise SystemExit(f"error: --supersedes {name!r} is not an entry in {history_dir}. A "
                         "correction names the filename it corrects.")
    old = json.loads(target.read_text(encoding="utf-8"))
    if old.get("suite") != suite:
        raise SystemExit(f"error: --supersedes {name} is a {old.get('suite')} entry; this recorder "
                         f"writes {suite}.")
    if any(json.loads(p.read_text(encoding="utf-8")).get("supersedes") == name
           for p in history_dir.glob("*.json") if p.name not in ("schema.json", "pins.json")):
        raise SystemExit(f"error: {name} is already superseded. Corrections are a linear chain: "
                         "correct the correction.")
    return old


def _correction_stem(history_dir: pathlib.Path, target: str, suite: str) -> str:
    base = target[: -len(f"-{suite}.json")]
    n = 1
    while (history_dir / f"{base}-correction{n}-{suite}.json").exists():
        n += 1
    return f"{base}-correction{n}"


def summarise(per_sample: list[list], ids: list[str]) -> tuple[list, dict]:
    """Per-case majority across k independently scored samples.

    **The sampling lives here and not in the instrument.** `evals/deterministic.py`
    is untouched, no scoring rule changes, and each sample is scored by exactly the
    code path a single run uses. M01's third owed tightening (sample k times *or*
    report the paired diff) remains owed; this is the second half of that "or".

    **But majority-of-k is a new suite-level estimator, and saying otherwise was
    wrong.** The first version of this docstring claimed "a reporting discipline,
    not a new scorer". That is true per case and false per suite: majority-of-3 is
    nonlinear. For a case with per-sample pass probability p, the recorded
    probability is 3p^2 - 2p^3, which *polarizes* rather than averages — it pushes
    p > 0.5 up and p < 0.5 down.

    On this milestone's own numbers (control 19/25 = 0.76, tools predicted
    10/25 = 0.40) that widens the expected delta from -9.0 to -12.6, toward the far
    end of a band this milestone pre-registered, and it makes the stated falsifier
    harder to trigger. The estimator did not exist when m01's 19/25 was recorded.

    So `pooled_pass_rate` is computed and recorded beside the majority, and the
    journal reports the paired delta both ways. If they agree the finding is
    robust; if they diverge, the divergence is the finding. Choosing which is the
    headline is a two-key call and it is made before the run, not after seeing
    which way it cut.

    **A representative sample carries the detail.** The recorded `CaseResult` is
    the first sample that agreed with the majority, so the failures printed and
    stored come from a run that actually happened rather than from a synthesised
    one. Averaging failure lists across samples would produce a case nobody ran.

    **INFRA does not enter the pool.** It means the harness could not establish
    anything, so summarising around it would let a network hiccup silently become
    a 2-of-2. The whole run is re-run and both runs are committed — the rule is
    written before the run, because an undesignated re-run is a cherry-pick door
    that opens the moment something times out."""
    infra = sorted({
        result.id
        for sample in per_sample
        for result in sample
        if result.result == INFRA
    })
    if infra:
        raise SystemExit(
            f"error: INFRA in one or more samples for {infra}. A sample that established "
            "nothing does not enter the majority pool: re-run the arm in full and commit "
            "both the discarded and the replacement run (SPEC/02). Summarising around it "
            "would let a network hiccup become a 2-of-2."
        )

    by_case: dict[str, list] = {}
    for sample in per_sample:
        for result in sample:
            by_case.setdefault(result.id, []).append(result)

    k = len(per_sample)
    if k % 2 == 0:
        # **An even k has no strict majority, and that is a bend path.** A 2-2 split
        # records ADVISORY, which `tally` does not count and `emit_verdict` turns
        # into PASS — so an operator whose sample 2 had one INFRA case could pass
        # samples 1 and 3 only, and every case where the pair disagreed would become
        # a non-blocking ADVISORY. Refused rather than documented, because the whole
        # point of the INFRA rule is that the answer to a bad sample is a full re-run.
        raise SystemExit(
            f"error: k={k} is even, so a tie has no strict majority. Use an odd k "
            "(SPEC/02 pre-registers k=3). Passing an even number of samples is how a "
            "discarded run becomes an ADVISORY that does not block."
        )
    needed = k // 2 + 1
    summary, samples = [], {}
    for case_id in ids:
        outcomes = by_case.get(case_id, [])
        verdicts = [r.result for r in outcomes]
        samples[case_id] = verdicts
        winner, count = "", 0
        for verdict in set(verdicts):
            if verdicts.count(verdict) > count:
                winner, count = verdict, verdicts.count(verdict)
        if count >= needed:
            summary.append(next(r for r in outcomes if r.result == winner))
        else:
            # No strict majority. Recorded as ADVISORY and named, never rounded
            # toward the flattering verdict — unreachable at M02 with k=3 over
            # PASS/FAIL, and reachable once the judge adds ADVISORY at M03.
            summary.append(replace(outcomes[0], result=ADVISORY))
    return summary, samples


def pooled_pass_rate(per_sample: list[list]) -> float:
    """Passes over every sample of every case, divided by k x cases.

    The linear counterpart to the majority, and the reason it is recorded: a
    majority polarizes and a mean does not, so reporting both says whether a
    reported delta is a property of the system or of the summariser. Recorded, not
    scored — `scores` in the history schema is `{string: number}`, so it needs no
    schema change, and nothing gates on it."""
    total = sum(len(sample) for sample in per_sample)
    if not total:
        return 0.0
    passed = sum(1 for sample in per_sample for result in sample if result.result == PASS)
    return round(passed / total, 4)


def paired_diff(control: list, tools: list) -> dict:
    """The per-case diff between two arms, which ADR-021 designates as **the
    result, not the total**.

    It had no harness. `run_evals.py` could print a total and nothing else, so
    "the diff is the result" was a sentence rather than a number — and whatever
    the tool prints is what gets reported.

    **Why the total is not enough**, in this repo's own evidence: M01's close
    showed three cases lost to the gateway and four gained by noise, and the
    headline +1 concealed a real −3. A net figure is the sum of two findings that
    point in opposite directions, and only one of them is usually the interesting
    one.

    Both arms must already be summarised the same way — same `k`, same majority
    rule — or the diff compares an estimate to a sample."""
    by_id = {r.id: r.result for r in control}
    other = {r.id: r.result for r in tools}
    missing = sorted(set(by_id) ^ set(other))
    if missing:
        raise SystemExit(
            f"error: the two arms do not cover the same cases: {missing}. A paired diff "
            "over a partial pairing is not a paired diff."
        )

    lost, gained, held = [], [], []
    for case_id in by_id:
        before, after = by_id[case_id], other[case_id]
        if before == after:
            held.append({"id": case_id, "result": before})
        elif before == PASS:
            lost.append({"id": case_id, "from": before, "to": after})
        elif after == PASS:
            gained.append({"id": case_id, "from": before, "to": after})
        else:
            held.append({"id": case_id, "result": f"{before}->{after}"})
    return {"lost": lost, "gained": gained, "unchanged": held,
            "net": len(gained) - len(lost)}


def print_diff(diff: dict, control_label: str, tools_label: str) -> None:
    print(f"\npaired per-case diff: {control_label} -> {tools_label}")
    print(f"  lost   {len(diff['lost'])}: " + ", ".join(c["id"] for c in diff["lost"]))
    print(f"  gained {len(diff['gained'])}: " + ", ".join(c["id"] for c in diff["gained"]))
    print(f"  net    {diff['net']:+d}")
    print("  The net is the sum of two findings that point in opposite directions. "
          "M01's headline +1 concealed a real -3 (ADR-021).")


def run(args) -> int:
    cases = _load(GOLDENS)
    if args.dryrun:
        return dryrun(cases)

    if not args.answers:
        print("error: --answers is required unless --dryrun", file=sys.stderr)
        return 2

    catalog = _load(CATALOG)
    paths = args.answers if isinstance(args.answers, list) else [args.answers]
    scorer = Scorer(root=ROOT)
    loaded = [_load(pathlib.Path(path)) for path in paths]
    per_sample = [scorer.score_suite(cases, answers, catalog) for answers in loaded]

    samples: dict[str, list[str]] = {}
    if len(per_sample) == 1:
        results, answers = per_sample[0], loaded[0]
    else:
        results, samples = summarise(per_sample, [case["id"] for case in cases])
        # Latency is pooled across every sample rather than taken from one. A p95
        # over one of three runs is a p95 over a third of the evidence, chosen
        # after the fact.
        answers = {f"{cid}#{n}": entry
                   for n, sample in enumerate(loaded, 1) for cid, entry in sample.items()}
        print(f"summarised {len(per_sample)} samples by per-case majority "
              f"(arm={args.arm or 'unnamed'})\n")

    # SPEC/00b's honesty clause, machine-recorded. The history schema has carried
    # `unearned` / `unearned_reason` since the starter and nothing populated them,
    # which left the clause as prose someone had to remember. Marks come from a
    # committed file rather than being inferred: deciding a pass is unearned is a
    # judgement, and it should be reviewable in a diff.
    if args.unearned:
        marks = _load(pathlib.Path(args.unearned)) or {}
        unknown = sorted(set(marks) - {r.id for r in results})
        if unknown:
            print(f"error: unearned marks name unknown case(s): {unknown}", file=sys.stderr)
            return 2
        wrong = sorted(cid for cid in marks if next(r.result for r in results if r.id == cid) != "PASS")
        if wrong:
            print(f"error: only a PASS can be unearned; these did not pass: {wrong}", file=sys.stderr)
            return 2
        results = [
            replace(r, unearned=True, unearned_reason=marks[r.id]) if r.id in marks else r
            for r in results
        ]

    # The judged half. Applied to `results` BEFORE `tally`, so the recorded score is
    # the judged one rather than a deterministic score with a note attached.
    judged_parts = None
    if args.judged:
        if not args.calibration:
            print("error: --judged needs --calibration: which axes may veto is decided by a "
                  "published agreement number, never by the run being scored", file=sys.stderr)
            return 2
        from evals import judged as judged_mod
        judged_parts = judged_mod.entry_parts(
            pathlib.Path(args.judged), _load(pathlib.Path(args.calibration)), args.k_judge)
        vetoed = judged_parts["vetoes"]
        unknown = sorted(set(vetoed) - {r.id for r in results})
        if unknown:
            print(f"error: the judge vetoed case(s) not in this suite: {unknown}", file=sys.stderr)
            return 2
        # A veto can only subtract. It turns a deterministic PASS into a judged FAIL
        # and never the reverse, which is what `judged <= deterministic` means as
        # code rather than as a promise (SPEC/03).
        # Appended to `asserts`, not to `failures`. `failures` is a derived property
        # over `asserts`, so `replace(r, failures=...)` raises - a test written for
        # the veto found it before the anchor was ever run against it.
        results = [
            replace(r, result=FAIL,
                    asserts=tuple(r.asserts) + tuple(
                        AssertResult(f"judge:{axis}", False,
                                     "vetoed by a calibrated axis at the published agreement")
                        for axis in vetoed[r.id]))
            if r.id in vetoed and r.result == PASS else r
            for r in results
        ]

    scores = tally(results)
    if len(per_sample) > 1:
        # Recorded beside the majority, never instead of it. A majority polarizes
        # and a mean does not, so the two together say whether a reported delta is
        # a property of the system or of the summariser (see `summarise`).
        scores["pooled_pass_rate"] = pooled_pass_rate(per_sample)

    width = max(len(r.id) for r in results)
    for r in results:
        # With k > 1 the per-sample verdicts print beside the majority, because
        # "PASS FAIL PASS -> PASS" and "PASS PASS PASS -> PASS" are different
        # findings and only one of them is stable.
        spread = f"  [{' '.join(samples[r.id])}]" if samples else ""
        print(f"{r.id:<{width}}  {r.result}{spread}")
        for failure in r.failures:
            print(f"{'':<{width}}    - {failure.kind}: {failure.detail}")
    print(
        f"\n{scores['passed']}/{scores['total']} passed "
        f"({scores['failed']} failed, {scores['infra']} infra) — "
        + (f"judge axes recorded {ADVISORY}, not scored (ADR-012)" if not judged_parts
           else f"judged by instrument {judged_parts['instrument']['name']}, "
                f"calibrated by {judged_parts['instrument']['calibrated_by']}: "
                f"{len(judged_parts['calibrated'])} calibrated axis(es), "
                f"{len(judged_parts['vetoes'])} case(s) vetoed")
    )
    latency = suite_latency(answers, _load(MANIFEST)["gates"]["budgets"].get("p95_ms"))
    print(f"suite latency  {'OK  ' if latency.passed else 'OVER'} {latency.detail}")
    deferred_hits = sum(len(r.deferred) for r in results)
    if deferred_hits:
        kinds = sorted({a.kind for r in results for a in r.deferred})
        print(f"deferred, evaluated but not scored: {deferred_hits} assert(s) across {kinds}")
        for kind in kinds:
            print(f"  {kind}: {DEFERRED_ASSERTS.get(kind, 'deferred')}")

    unearned = [r for r in results if r.unearned]
    if unearned:
        print(f"\n{len(unearned)} of those passes are marked UNEARNED (SPEC/00b):")
        for r in unearned:
            print(f"  {r.id}: {r.unearned_reason}")

    if args.record:
        # Every entry names and hashes the answers it read, at any k (ADR-042
        # decision 5). This was `if len(per_sample) > 1 or judged_parts`, and the
        # AI Quality seat measured that an honest k=1 `--record` -- and every
        # goldens `--supersedes` at k=1 -- was then refused by the evidence check
        # the same ADR adds. An entry that does not say which bytes it read
        # cannot be anchored to them.
        path = record(results, scores, args, len(per_sample), samples,
                      sources=_sources(paths), judged=judged_parts)
        try:
            shown = path.relative_to(ROOT)
        except ValueError:   # a test's HISTORY, or --history-dir on the twin
            shown = path
        print(f"recorded: {shown}")

    if args.against:
        # The other arm, scored and summarised by the identical path — never read
        # from a recorded row. A diff between a fresh summary and a history entry
        # would compare today's instrument against whatever produced that row,
        # which is the comparison ADR-016 exists to forbid.
        against_paths = args.against
        against_loaded = [_load(pathlib.Path(path)) for path in against_paths]
        against_samples = [scorer.score_suite(cases, a, catalog) for a in against_loaded]
        if len(against_samples) != len(per_sample):
            raise SystemExit(
                f"error: {len(per_sample)} sample(s) for this arm and {len(against_samples)} "
                "for the other. Both arms are summarised the same way or the diff compares "
                "an estimate to a sample (ADR-021)."
            )
        against_results = (against_samples[0] if len(against_samples) == 1
                           else summarise(against_samples, [c["id"] for c in cases])[0])
        diff = paired_diff(against_results, results)
        print_diff(diff, args.against_arm or "other arm", args.arm or "this arm")
        if args.diff_out:
            pathlib.Path(args.diff_out).write_text(
                json.dumps(diff, indent=2), encoding="utf-8")
            print(f"wrote paired diff: {args.diff_out}")

    if args.out:
        emit_verdict(results, scores, args.out)
        print(f"wrote verdict: {args.out}")

    # Reporting a score is not gating. `pave gate decide` owns the block/allow
    # decision, and it reads the verdict this writes.
    return 0


def record(results, scores, args, k=1, samples=None, sources=None, judged=None) -> pathlib.Path:
    """Append a history entry. Never edits: a correction is a new entry carrying
    `supersedes`, because the value of this file is that every row came from a
    real execution.

    `k` and `arm` are what let a reader six months out tell a single sample from a
    summarised one. Without them, "we designated the run in advance" is a social
    protection rather than a legible one — which is the state this repo converts
    into checks."""
    samples = samples or {}
    # The sha names **the commit that produced the answers**, not the commit that
    # scored them. For a fresh run those are the same and the default is right. For
    # a re-reading they are not: the m00b judged anchor reads answers produced at
    # the m00b commit, and recording HEAD would say the M03 branch produced them —
    # putting two readings of one commit under two shas, where the whole point is
    # that a reader sees them as one commit read twice (ADR-012, ADR-027).
    supersedes = getattr(args, "supersedes", None)
    superseded = _load_superseded(HISTORY, supersedes, "goldens") if supersedes else None
    # A correction copies the commit it corrects rather than re-deriving it; an
    # explicit --sha beside --supersedes is the one sanctioned way to correct a
    # row recorded against the WRONG commit (ADR-041's B-0 shape), and the
    # different-sha row is then not "a second row under one sha".
    sha = getattr(args, "sha", None) or (superseded["sha"] if superseded else _git_sha())
    if getattr(args, "sha", None) and not judged and not superseded:
        raise SystemExit(
            "error: --sha overrides the commit a score is recorded against, and is only "
            "meaningful for a re-reading of committed answers or a correction. A fresh run "
            "records the commit it ran at. Pass --judged or --supersedes, or drop --sha."
        )
    entry = {
        "sha": sha,
        "suite": "goldens",
        "target": args.target,
        "recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "scores": scores,
        "cases": [
            {"id": r.id, "result": r.result}
            | ({"unearned": True, "unearned_reason": r.unearned_reason} if r.unearned else {})
            # The per-sample verdicts, so a 2-1 majority is checkable in the entry
            # rather than asserted by whoever ran it. Omitted at k=1, where the
            # result is already the only sample there was.
            | ({"samples": samples[r.id]} if samples.get(r.id) else {})
            for r in results
        ],
    }
    if k > 1:
        entry["k"] = k
    if sources:
        # **What `k` alone could not say.** `k` is the number of files the operator
        # passed, not the number of runs that happened: running five and passing the
        # best three produced an entry byte-indistinguishable from an honest one,
        # and nothing tied a recorded score to a committed run file. Naming and
        # hashing them does not stop a cherry-pick — nothing here can — but it makes
        # one leave a trace, which is the difference between a social protection and
        # a legible one.
        entry["samples_from"] = sources
    if args.arm:
        entry["arm"] = args.arm
    if judged:
        # **No `supersedes`, ever, and this is the one place it could creep in.**
        # ADR-012 originally committed M03 to appending the judged anchor with
        # `supersedes` pointing at the deterministic entry. It means *corrects a
        # wrong entry*, and 15/25 is not wrong - it is a correct measurement taken
        # with the only instrument that existed at the time (ADR-027).
        entry["instrument"] = judged["instrument"]
        entry["judge_axes"] = judged["judge_axes"]
        entry["guardrail_refusals"] = judged["guardrail_refusals"]
    if args.tag:
        entry["tag"] = args.tag
    for key in ("tokens_in", "tokens_out"):
        value = getattr(args, key)
        if value is not None:
            entry[key] = value
    if superseded:
        entry["supersedes"] = supersedes
        # `supersedes` means *the earlier entry was wrong* (ADR-027). Identical
        # numbers correct nothing and put the same number twice under one sha.
        if superseded.get("scores") == entry["scores"] and superseded.get("cases") == entry["cases"]:
            raise SystemExit(f"error: this entry's scores and cases equal {supersedes}'s. A correction "
                             "that corrects nothing is refused (ADR-042 decision 7).")
        if superseded.get("instrument") != entry.get("instrument"):
            raise SystemExit("error: a correction carries the instrument of the entry it corrects; a "
                             "different instrument is a second reading, not a correction.")
        if superseded.get("arm") != entry.get("arm"):
            raise SystemExit("error: a correction carries the arm of the entry it corrects.")
        if superseded.get("tag") and "tag" not in entry:
            entry["tag"] = superseded["tag"]

    import jsonschema
    jsonschema.validate(entry, _load(HISTORY_SCHEMA))

    HISTORY.mkdir(parents=True, exist_ok=True)
    # The arm is in the filename because a milestone that runs two arms writes two
    # entries under one tag, and the append-only guard below would otherwise read
    # the second arm as an attempt to rewrite the first.
    # ADR-027 rule 3: the append-only guard keys on the filename, so two entries
    # under one tag need two names and the distinguishing component must be the
    # thing that actually differs - the instrument, not a number or a date.
    stem = f"{args.tag or sha[:7]}" + (f"-{args.arm}" if args.arm else "")
    if judged:
        stem += f"-judged-{judged['instrument']['name']}"
    if superseded:
        # ADR-027 rule 3: the component that differs is the thing that differs,
        # and what differs here is that this row is a correction.
        stem = _correction_stem(HISTORY, supersedes, "goldens")
    path = HISTORY / f"{stem}-goldens.json"
    if path.exists():
        raise SystemExit(
            f"error: {path.name} already exists. History is append-only — a correction is a new "
            "entry recorded with `--supersedes {path.name}`, never an edit (CLAUDE.md)."
        )
    write_entry(path, entry)
    return path


def emit_verdict(results, scores, out: str) -> None:
    from pave import verdict as verdict_mod
    blocked = any(r.result == INFRA for r in results)
    unresolved = any(r.result == ADVISORY for r in results)
    verdict_mod.write(out, verdict_mod.build(
        service="highlights-agent",
        surface="agent",
        suite="goldens",
        layer="L2",
        # **ADVISORY blocks.** It is not in `tally`'s passed/failed/infra counts, so
        # `FAIL if scores["failed"]` read an unresolved case as a clean PASS. A case
        # with no strict majority is a case the suite could not decide, and a gate
        # that waves those through is a gate that fails open on exactly the results
        # nobody understands yet. Unreachable at k=3 over PASS/FAIL; written while
        # nothing is riding on it, because the judge makes it reachable at M03.
        verdict=INFRA if blocked else (
            FAIL if (scores["failed"] or unresolved) else "PASS"),
        fail_closed=True,
        scores={k: v for k, v in scores.items()},
    ))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_evals", description=__doc__)
    p.add_argument("--dryrun", action="store_true", help="load and resolve only; no scoring")
    p.add_argument("--answers", action="append",
                   help="JSON produced by the agent under test; repeat for k samples")
    p.add_argument("--arm", help="which system produced these answers, when a milestone "
                                 "runs more than one (e.g. control | tools)")
    p.add_argument("--against", action="append",
                   help="answers from the OTHER arm; repeat for its k samples. Both arms are "
                        "summarised the same way and the paired per-case diff is reported, "
                        "which ADR-021 designates as the result rather than the total")
    p.add_argument("--diff-out", help="write the paired diff here as JSON")
    p.add_argument("--against-arm", help="label for the other arm in the diff output")
    p.add_argument("--sha", help="the commit that produced the ANSWERS, when re-reading "
                                 "committed answers under a new instrument. Requires --judged")
    p.add_argument("--judged", help="directory of committed judge output for this run: "
                                    "score it judged as well as deterministically")
    p.add_argument("--calibration", help="the published calibration report whose axes decide "
                                         "which axes may veto (required with --judged)")
    p.add_argument("--k-judge", dest="k_judge", type=int, default=3,
                   help="judge samples per case in --judged")
    p.add_argument("--record", action="store_true", help="append an entry to evals/history/")
    p.add_argument("--supersedes", metavar="ENTRY",
                   help="record this as a CORRECTION of an entry in evals/history/, named by "
                        "filename (ADR-027: the earlier entry was wrong). Copies its sha and "
                        "lands under a -correctionN- filename; never edits it.")
    p.add_argument("--tag", help="milestone tag, e.g. m00b")
    p.add_argument("--target", default="baseline", help="baseline | <service-name>")
    p.add_argument("--out", help="write a gate verdict record here")
    p.add_argument("--unearned", help="YAML/JSON of {case-id: reason} marking passes that are not credited to the system (SPEC/00b)")
    p.add_argument("--tokens-in", dest="tokens_in", type=int)
    p.add_argument("--tokens-out", dest="tokens_out", type=int)
    return run(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
