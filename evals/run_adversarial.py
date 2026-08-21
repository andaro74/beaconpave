"""
`python -m evals.run_adversarial` — score the probe corpus under G4.

Reads observations produced by the agent under test and scores them. It never
sees the model's reply: `evals/adversarial.py` takes system observations only,
so a probe cannot pass because the answer looked polite.

  python -m evals.run_adversarial --observations probes-run.json [--record --tag m00b]

**Unanimity decides at k > 1** (ADR-031). An observation carrying a `samples`
list is summarised by `score_samples`: a probe passes only if every sample
passed, a split records FAIL with `unstable`, and one INFRA sample makes the
whole probe INFRA rather than being outvoted. The per-sample verdicts travel into
the entry, because `k` alone says a summary happened and not what it summarised.

**A recorded entry carries its instrument** (ADR-032). `instrument` in the
history schema is suite-conditional from M04: an adversarial entry names the
scorer, the two `pass_when` semantics and their mechanism sets, the probe corpus,
the G4 semantics corpus, `classify.py`, and the enforced guardrail version. Every
one of those can move without a recorded mark changing, which is ADR-018's hazard
arriving for the fifth and sixth time.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys
from dataclasses import replace

import yaml

from evals.adversarial import instrument_digests, score_corpus, tally

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals" / "history"
PROBES = ROOT / "quality" / "adversarial" / "probes.yaml"


def dirty_working_tree(root: pathlib.Path) -> str:
    """Tracked files differing from HEAD, or "" when there are none.

    Named rather than inlined so it can be exercised directly. Untracked files are
    ignored: a scratch script beside the repo does not change what any digest
    covers, and treating it as a blocker would train whoever records the entry to
    reach for the override every time.

    A git failure returns "" — the check is a guard against an honest mistake, not
    a security boundary, and refusing to record because git is unavailable would
    block the run for a reason unrelated to the evidence."""
    import subprocess
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                             cwd=root, capture_output=True, text=True, check=False)
    except OSError:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_adversarial")
    p.add_argument("--observations", required=True)
    p.add_argument("--record", action="store_true")
    p.add_argument("--tag")
    p.add_argument("--target", default="baseline")
    p.add_argument("--unearned", help="YAML/JSON of {probe-id: reason} marking passes that are "
                                      "not credited to the system (SPEC/00b honesty clause)")
    p.add_argument("--instrument-name", help="the handle this instrument is recorded under; "
                                             "required with --record (ADR-027 rule 4)")
    p.add_argument("--guardrail-version", help="the version observed in the audit records, "
                                               "not the one the stack intends (ADR-018)")
    p.add_argument("--guardrail-policy-sha256", help="digest of the policy that version pins, "
                                                     "fetched back from the deployed guardrail")
    # Exists for the same reason `pave evals run --comparators` does: without it a
    # test of the recording path has to write into the tracked, append-only,
    # two-key `evals/history/` and clean up in a `finally`. A killed run then
    # leaves a history entry on disk that no run produced, in the one directory
    # whose entire value is that every row came from a real execution.
    p.add_argument("--history-dir", help="where to append the entry (default evals/history/)")
    p.add_argument("--allow-dirty", action="store_true",
                   help="record even though the working tree differs from HEAD. The entry's "
                        "digests then fingerprint code that is in no commit.")
    args = p.parse_args(argv)

    probes = yaml.safe_load(PROBES.read_text(encoding="utf-8"))
    observations_path = pathlib.Path(args.observations)
    document = json.loads(observations_path.read_text(encoding="utf-8"))
    # Keys the runner records ABOUT the run rather than about a probe. Stripped
    # before scoring so they cannot be mistaken for an observation, and read below
    # so the entry's `guardrail_version` has committed evidence behind it.
    observed_versions = document.pop("_guardrail_versions", None)
    document.pop("_k", None)
    observations = document
    results = score_corpus(probes, observations)

    # The same guards `run_evals` applies to golden marks. Deciding that a pass is
    # unearned is a judgement and belongs in a committed diff, and a mark naming a
    # probe that did not pass would let this file quietly excuse a failure.
    if args.unearned:
        marks = yaml.safe_load(pathlib.Path(args.unearned).read_text(encoding="utf-8")) or {}
        known = {r.id for r in results}
        unknown = sorted(set(marks) - known)
        if unknown:
            print(f"error: unearned marks name unknown probe(s): {unknown}", file=sys.stderr)
            return 2
        wrong = sorted(m for m in marks if next(r for r in results if r.id == m).result != "PASS")
        if wrong:
            print(f"error: only a PASS can be unearned; these did not pass: {wrong}", file=sys.stderr)
            return 2
        results = [
            replace(r, unearned=True, unearned_reason=marks[r.id]) if r.id in marks else r
            for r in results
        ]

    scores = tally(results)

    for r in results:
        mark = "  [UNEARNED]" if r.unearned else ""
        vector = f"  {'/'.join(r.samples)}" if r.samples else ""
        print(f"{r.id:<10} {r.result:<8} {r.reason}{vector}{mark}")
    print(f"\n{scores['passed']}/{scores['total']} probes passed G4 "
          f"(blocked or denied AND logged)")
    if scores["unearned"]:
        print(f"{scores['unearned']} of those passes are marked UNEARNED (SPEC/00b): "
              f"{scores['earned']}/{scores['total']} are credited to the system.")
        for r in results:
            if r.unearned:
                print(f"  {r.id}: {r.unearned_reason}")
        print("The score above is recorded as-run. The marks travel into the history entry "
              "rather than being netted out of the number.")
    if scores["unstable"]:
        # Reported in its own paragraph rather than inside the failure count. A
        # guardrail that refuses an attack two times in three is a different
        # finding from one that never refuses it, and it is the finding a
        # k=1 run cannot produce at all.
        print(f"\n{scores['unstable']} probe(s) returned DIFFERENT verdicts across identical "
              "samples. Unanimity decides, so each records FAIL — but a control that is "
              "intermittent is not the same finding as a control that is absent:")
        for r in results:
            if r.unstable:
                print(f"  {r.id}: {'/'.join(r.samples)}")

    if scores["passed"] == 0:
        print("0 is the expected result at M00b: no gateway, no guardrail, no audit lake, "
              "so no probe can satisfy either half of G4. That is the control's score, "
              "not a harness limitation.")

    if args.record:
        sha = __import__("subprocess").run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip() or "unknown"
        # ADR-027 rule 4: a row naming an instrument nobody can look up is a
        # fingerprint of an object that does not exist. Refused here rather than
        # left to schema validation, so the message names what is missing and why.
        if not args.instrument_name:
            print("error: --instrument-name is required with --record. An entry whose "
                  "instrument has no handle cannot be compared with any other entry "
                  "(ADR-027 rule 4).", file=sys.stderr)
            return 2
        if not args.guardrail_policy_sha256:
            print("error: --guardrail-policy-sha256 is required with --record. The version "
                  "number alone is a name; this is what the name referred to, fetched back "
                  "from the deployed guardrail by verify_guardrail_pin.py. An entry naming a "
                  "version and nothing it pointed at cannot be compared with the next one "
                  "(ADR-033).", file=sys.stderr)
            return 2
        if not args.guardrail_version:
            print("error: --guardrail-version is required with --record, and it is the "
                  "version OBSERVED IN THE AUDIT RECORDS rather than the one the stack "
                  "intends. M03 recorded two dev passes whose instrument blocks were "
                  "byte-identical because the enforced policy was not part of the "
                  "instrument; the refusal rate differed and nothing in the record said "
                  "why (ADR-018).", file=sys.stderr)
            return 2

        # **A recorded entry must correspond to a commit.** `git rev-parse HEAD`
        # names the commit; `instrument_digests()` reads the WORKING TREE. With a
        # dirty tree those are different objects, and the entry would carry
        # fingerprints of code that is in no commit at all — append-only, so
        # uncorrectable. A planted weakening was live in this tree during M04's own
        # seat review, which is exactly how this arises.
        dirty = dirty_working_tree(ROOT)
        if dirty and not args.allow_dirty:
            print("error: the working tree is dirty, so `instrument` would fingerprint code "
                  "that is in no commit while `sha` names one. Commit first, or pass "
                  f"--allow-dirty deliberately.\n{dirty}", file=sys.stderr)
            return 2

        if observed_versions and args.guardrail_version not in observed_versions:
            print(f"error: --guardrail-version {args.guardrail_version!r} is not among the "
                  f"versions observed in the audit records ({observed_versions}). The field is "
                  "what enforced the calls, not what the stack intended (ADR-033).",
                  file=sys.stderr)
            return 2
        if observed_versions and len(observed_versions) > 1:
            print(f"error: the observations span guardrail versions {observed_versions}; a run "
                  "across two policies is not one measurement (ADR-018).", file=sys.stderr)
            return 2

        k = max((len(r.samples) for r in results if r.samples), default=1)
        ragged = sorted(r.id for r in results if r.samples and len(r.samples) != k)
        if ragged:
            # Unanimity over fewer samples is easier, so a short vector flatters.
            print(f"error: probe(s) {ragged} carry fewer than {k} samples. `k` would record the "
                  "maximum and the entry would claim a depth those probes did not have.",
                  file=sys.stderr)
            return 2
        instrument = dict(instrument_digests(),
                          name=args.instrument_name,
                          guardrail_version=args.guardrail_version,
                          k=k)
        instrument["guardrail_policy_sha256"] = args.guardrail_policy_sha256

        entry = {
            "sha": sha,
            "suite": "adversarial",
            "target": args.target,
            "recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "scores": scores,
            "instrument": instrument,
            # What this entry was summarised from, with a digest of each. `k` is
            # otherwise the number of files the operator chose to pass: running
            # five and recording the best three produces an entry
            # byte-indistinguishable from an honest one. `close-milestone` checks
            # the named files are committed and their hashes still match.
            "samples_from": [{
                "path": str(observations_path.relative_to(ROOT)
                            if observations_path.is_absolute() and ROOT in observations_path.parents
                            else observations_path).replace("\\", "/"),
                "sha256": __import__("hashlib").sha256(
                    observations_path.read_bytes()).hexdigest(),
            }],
            "cases": [
                {"id": r.id, "result": r.result}
                | ({"samples": list(r.samples)} if r.samples else {})
                | ({"unstable": True} if r.unstable else {})
                | ({"unearned": True, "unearned_reason": r.unearned_reason} if r.unearned else {})
                for r in results
            ],
        }
        if k > 1:
            entry["k"] = k
        if args.tag:
            entry["tag"] = args.tag
        import jsonschema
        jsonschema.validate(entry, json.loads((HISTORY / "schema.json").read_text(encoding="utf-8")))
        history = pathlib.Path(args.history_dir) if args.history_dir else HISTORY
        history.mkdir(parents=True, exist_ok=True)
        path = history / f"{args.tag or sha[:7]}-adversarial.json"
        if path.exists():
            print(f"error: {path.name} exists — history is append-only", file=sys.stderr)
            return 2
        path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        try:
            shown = path.relative_to(ROOT)
        except ValueError:
            shown = path
        print(f"recorded: {shown}")

    # Reporting is not gating, same as run_evals: `pave gate decide` owns the
    # block/allow decision and reads the verdict, not this exit code.
    return 0


if __name__ == "__main__":
    sys.exit(main())
