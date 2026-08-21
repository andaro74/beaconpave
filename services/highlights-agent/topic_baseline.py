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
M01_ANSWERS = ROOT / "milestones" / "M01" / "goldens-run.json"

TOPIC = "TOPIC:entitlement-circumvention"


def _assess(runtime, guardrail_id, version, text, source):
    response = runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id, guardrailVersion=version,
        source=source, content=[{"text": {"text": text}}])
    # Read through the same `_blocked_names` every other verdict in this repo is
    # read through. A second reader that could disagree would split one finding
    # into two nobody joins up.
    outcome = guardrail.interpret_apply(response, channel=guardrail.CHANNEL_SYSTEM)
    return outcome.intervened, list(outcome.assessed)


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


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="what the deployed guardrail does, per channel")
    p.add_argument("--questions", action="store_true")
    p.add_argument("--answers", action="store_true")
    p.add_argument("--attacks", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--out")
    args = p.parse_args(argv)
    if args.all:
        args.questions = args.answers = args.attacks = True
    if not (args.questions or args.answers or args.attacks):
        p.error("nothing selected; pass --all or one of --questions/--answers/--attacks")

    cf = boto3.client("cloudformation")
    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cf.describe_stacks(StackName="BeaconpaveGateway")["Stacks"][0]["Outputs"]}
    guardrail_id, version = outputs["PinnedGuardrailId"], outputs["PinnedGuardrailVersion"]
    runtime = boto3.client("bedrock-runtime")
    print(f"guardrail: {guardrail_id} version {version}\n")

    recorded = {"guardrail_id": guardrail_id, "guardrail_version": version, "arms": {}}
    arms = []
    if args.questions:
        arms.append(("questions", "INPUT", questions()))
    if args.answers:
        arms.append(("answers", "OUTPUT", answers()))
    if args.attacks:
        arms.append(("attacks", "INPUT", attacks()))

    for arm, source, items in arms:
        print(f"--- {arm} ({len(items)} items, source={source}) " + "-" * 26)
        results, blocked, by_topic = {}, 0, 0
        for item_id, text in items:
            intervened, assessed = _assess(runtime, guardrail_id, version, text, source)
            results[item_id] = {"intervened": intervened, "assessed": assessed}
            blocked += int(intervened)
            by_topic += int(TOPIC in assessed)
            if intervened:
                print(f"  BLOCKED  {item_id:20s} {assessed}")
        print(f"  {blocked}/{len(items)} blocked, {by_topic} naming the entitlement topic\n")
        recorded["arms"][arm] = {"source": source, "n": len(items), "blocked": blocked,
                                 "named_the_topic": by_topic, "results": results}

    print("This scores nothing. No audit record was written and no model was called.")
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(recorded, indent=2) + chr(10),
                                          encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
