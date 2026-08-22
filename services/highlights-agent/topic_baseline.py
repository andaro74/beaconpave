"""
`python services/highlights-agent/topic_baseline.py` — what does the deployed
guardrail do to the questions, the answers, and the attacks, right now?

**Zero model calls. It must run before Change A deploys, and it cannot be run
late.** A guardrail version is an immutable snapshot; once the version resource
is replaced, version 2 is not there to ask. Every number here is a control that
becomes unobtainable the moment the tightening lands.

**It scores nothing.** No gateway, no audit record, so nothing here satisfies
either half of G4, and no number it prints may enter a corpus, a comparator or a
history entry. Same standing as `inspect_context.py`, and the same reason: a
diagnostic that cannot be mistaken for a result is one that is safe to run
*before* a measurement.

## The three things it separates, and why each was owed

**1. The question channel (`--questions`).** The 25 golden user turns, at
`source=INPUT`. The Service Team seat found a contradiction the repo has been
carrying since M02: `README.md` attributes the golden refusals to the inlined
catalog tripping this topic, but the M02 control arm — which inlines the whole
catalog on every call — refused **19 of 75, not 75 of 75**. If the system block
were being assessed by `converse`, every call would have died. It is not. M04's
channel control says the same thing from the other side.

So the refusals come from the user turn, the model's own answer, or both, and
**nobody has ever measured which.** This separates them for 25 free calls.

**2. The answer channel (`--answers`).** The committed M01 answers, at
`source=OUTPUT`. These are the platform's own correct replies — "you can't watch
this tonight because of a blackout, and you'd need sports-tier" — which is the
exact sentence ADR-024 says a subject-matter topic fires on. If the topic blocks
them, then **the false-positive surface is the platform answering correctly**,
not viewers asking badly, and a definition reworded to be kinder to questions
fixes the smaller half.

**3. The attack corpus (`--attacks`).** `quality/adversarial/topic-attacks.yaml`,
at `source=INPUT`, frozen before either version was run against it. This is the
v2 control for over-narrowing: without it, a v3 allow can always be answered with
"v2 would have allowed it too", and that comparison is unrecoverable after the
deploy.

## What these numbers can and cannot support

They are `ApplyGuardrail` verdicts, not gateway refusals. A gateway refusal also
transits the classification router, writes an audit record, and can be caused by
controls this never touches. **They do not replace steps 0 and 4** and they are
not comparable to `evals/refusals.py`'s counts, which are per-run golden-case
refusals through the whole path. What they are is the decomposition the gateway
run structurally cannot give, taken before the thing being changed is gone.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/topic_baseline.py --all --out <file>

Outside the hermetic surface. Owning seat: Security / Red Team (the attacks and
what a verdict means) · Service Team (the questions and answers, and the channel
decomposition they were owed).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import boto3
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "platform" / "gateway"))

import gateway_client as gw  # noqa: E402
from core import guardrail  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
ATTACKS = ROOT / "quality" / "adversarial" / "topic-attacks.yaml"
HELDOUT = ROOT / "quality" / "adversarial" / "topic-attacks-heldout.yaml"
M01_ANSWERS = ROOT / "milestones" / "M01" / "goldens-run.json"

TOPIC = "TOPIC:entitlement-circumvention"


def _assess(runtime, guardrail_id, version, text, source, k, channel):
    """`k` samples, and the split is recorded rather than resolved.

    **This guardrail returns different verdicts on identical input** — 4 of 25
    anchor cases at M03, and `PHR-004` blocked in 1 of 3 identical calls, which is
    the datum this whole tightening exists for. A k=1 baseline of the thing being
    changed would be the same mistake in the same place. Unanimity decides, never
    majority (ADR-031): a control that stops something twice in three does not
    stop it, and a 2-1 split is evidence of instability rather than a verdict to
    round off."""
    blocked, per_sample = 0, []
    for _ in range(k):
        response = runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id, guardrailVersion=version,
            source=source, content=[{"text": {"text": text}}])
        # Read through the same `_blocked_names` every other verdict in this repo
        # is read through. A second reader that could disagree would split one
        # finding into two nobody joins up.
        outcome = guardrail.interpret_apply(response, channel=channel)
        blocked += int(outcome.intervened)
        per_sample.append(sorted(outcome.assessed))
    assessed = sorted({name for a in per_sample for name in a})
    return blocked, assessed, per_sample


def questions() -> list[tuple[str, str]]:
    """The 25 golden user turns, built exactly as `run_via_gateway.py` builds
    them — same `gw.user_turn`, same viewer plan and DMA. A retyped question is
    a different question."""
    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    out = []
    for case in cases:
        viewer = case.get("viewer") or {}
        out.append((case["id"], gw.user_turn(case["input"], viewer.get("plan"), viewer.get("dma"))))
    return out


def answers() -> list[tuple[str, str]]:
    """The committed M01 answers, verbatim out of the run file.

    Only the cases that were actually answered: a case the gateway refused has no
    answer, and inventing one would be measuring a reply nobody made."""
    run = json.loads(M01_ANSWERS.read_text(encoding="utf-8"))
    out = []
    for case_id, record in run.items():
        answer = record.get("answer")
        if isinstance(answer, dict) and "refused_by_gateway" in answer:
            continue
        out.append((case_id, json.dumps(answer, ensure_ascii=False)))
    return out


def attacks() -> list[tuple[str, str]]:
    corpus = yaml.safe_load(ATTACKS.read_text(encoding="utf-8"))
    return [(a["id"], " ".join(a["text"].split())) for a in corpus["attacks"]]


def heldout() -> list[tuple[str, str]]:
    """The held-out corpus, frozen before the wording it judges existed.

    **Its expectations run in BOTH directions and that is not decoration.** A
    corpus of nothing but `expect: blocked` is satisfied by a topic that blocks
    everything, which is what guardrail v2 did and what ADR-035 exists to undo. So
    the run prints the expectation beside the verdict: an `expect: allowed` row
    that blocks is a finding of exactly the same weight as an `expect: blocked`
    row that does not."""
    corpus = yaml.safe_load(HELDOUT.read_text(encoding="utf-8"))
    return [(r["id"], " ".join(r["text"].split())) for r in corpus["heldout"]]


def expectations() -> dict:
    corpus = yaml.safe_load(HELDOUT.read_text(encoding="utf-8"))
    return {r["id"]: r["expect"] for r in corpus["heldout"]}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="what the deployed guardrail does, per channel")
    p.add_argument("--questions", action="store_true")
    p.add_argument("--answers", action="store_true")
    p.add_argument("--attacks", action="store_true")
    p.add_argument("--heldout", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--k", type=int, default=3,
                   help="samples per item. k=1 is not a result against this guardrail")
    p.add_argument("--out")
    args = p.parse_args(argv)
    if args.all:
        args.questions = args.answers = args.attacks = args.heldout = True
    if not (args.questions or args.answers or args.attacks or args.heldout):
        p.error("nothing selected; pass --all or one of "
                "--questions/--answers/--attacks/--heldout")

    cf = boto3.client("cloudformation")
    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cf.describe_stacks(StackName="BeaconpaveGateway")["Stacks"][0]["Outputs"]}
    guardrail_id, version = outputs["PinnedGuardrailId"], outputs["PinnedGuardrailVersion"]
    runtime = boto3.client("bedrock-runtime")
    print(f"guardrail: {guardrail_id} version {version}\n")

    recorded = {"guardrail_id": guardrail_id, "guardrail_version": version,
                "k": args.k, "arms": {}}
    arms = []
    if args.questions:
        arms.append(("questions", "INPUT", questions(), guardrail.CHANNEL_QUESTION))
    if args.answers:
        arms.append(("answers", "OUTPUT", answers(), guardrail.CHANNEL_ANSWER))
    if args.attacks:
        arms.append(("attacks", "INPUT", attacks(), guardrail.CHANNEL_QUESTION))
    if args.heldout:
        arms.append(("heldout", "INPUT", heldout(), guardrail.CHANNEL_QUESTION))

    # **The channel is the arm's own, not `system` for all four (ADR-040).** This
    # file calls its modes "the question channel" and "the answer channel" in its
    # own docstring and passed `CHANNEL_SYSTEM` for every one of them, so a reader
    # of a committed artifact saw prose naming one channel beside a record naming
    # another. Harmless while `question` and `answer` were not legal values; the
    # moment they are, it is the two-spellings misread `CHANNELS` exists to stop.
    for arm, source, items, channel in arms:
        print(f"--- {arm} ({len(items)} items, source={source}) " + "-" * 26)
        results, blocked, unstable, by_topic = {}, 0, 0, 0
        for item_id, text in items:
            hits, assessed, per_sample = _assess(
                runtime, guardrail_id, version, text, source, args.k, channel)
            unanimous = hits in (0, args.k)
            results[item_id] = {"blocked_samples": hits, "unanimous": unanimous,
                                "assessed": assessed, "per_sample_assessed": per_sample}
            blocked += int(hits == args.k)
            unstable += int(not unanimous)
            by_topic += int(TOPIC in assessed)
            expected = expectations().get(item_id) if arm == "heldout" else None
            verdict = ("blocked" if hits == args.k else "allowed" if hits == 0
                       else f"unstable-{hits}/{args.k}")
            if expected is not None:
                # Both directions carry equal weight, so both are printed and
                # both can fail. A topic that blocks everything passes a
                # blocked-only corpus, and that is the failure ADR-035 exists to
                # undo rather than to repeat.
                mark = "  ok " if verdict == expected else "MISS "
                results[item_id]["expected"] = expected
                results[item_id]["met"] = verdict == expected
                print(f"  {mark} {item_id:20s} expect {expected:8s} got {verdict:14s} {assessed}")
            elif hits:
                label = "BLOCKED" if hits == args.k else f"UNSTABLE {hits}/{args.k}"
                print(f"  {label:12s} {item_id:20s} {assessed}")
        if arm == "heldout":
            missed = [i for i, r in results.items() if not r.get("met", True)]
            print(f"  {len(items) - len(missed)}/{len(items)} met their expectation"
                  + (f"   MISSED: {missed}" if missed else ""))
        else:
            print(f"  {blocked}/{len(items)} blocked unanimously, {unstable} unstable, "
                  f"{by_topic} naming the entitlement topic")
        print()
        recorded["arms"][arm] = {"source": source, "n": len(items), "k": args.k,
                                 "blocked_unanimously": blocked, "unstable": unstable,
                                 "named_the_topic": by_topic, "results": results}

    print("This scores nothing. No audit record was written and no model was called.")
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(recorded, indent=2) + chr(10),
                                          encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
