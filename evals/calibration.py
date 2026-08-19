"""
The calibration corpus selection rule (SPEC/03).

**Why this is a committed, deterministic rule and not a hand-picked list.**
An agreement number is only worth reading if the items it was measured on were
not chosen to produce it. "We picked 30 representative items" is unfalsifiable;
"these 30 are what this function returns" is checkable by anyone, and
`tests/test_calibration_corpus.py` checks it on every run.

**The salt was fixed before any item was drawn.** It is the SHA the commit
carrying `SPEC/03-evals.md` had at the moment of the draw — the same commit that
pre-registered the thresholds, the corpus size and the split. That closes the
obvious cherry-pick door: choosing a salt after seeing which items it selects is
re-rolling. The draw was run once. If its output had looked awkward it would have
been recorded as-drawn, which is the same rule that governs a run of the golden
set.

**Corrected after the rebase: a commit SHA is not a stable name for a commit.**
The branch was rebased onto `main` when the account-ID guard fix (#21) merged, and
the spec commit's SHA moved from `6a851c0…` to `815b172…`. The salt still reads
`6a851c0…`, which now names a commit that is **not reachable from this branch and
was never pushed** — so no reader can look it up. That is not a value to quietly
update: changing the salt redraws the corpus, and redrawing after the items and
their labels are written is precisely the re-roll this device exists to prevent.

What survives is the part that was load-bearing. The spec content that fixed the
thresholds is verifiable at the rebased commit, byte-identical, because a rebase
changes a commit's parents and not its patch:

    git rev-parse 815b172:SPEC/03-evals.md
    9f8212c731e52fcc27e1420257fe312a79faa34a

So the pre-registration is still checkable by anyone with the branch; only the
name it was recorded under is stale. **The general lesson, worth more than this
instance: a commit SHA identifies a commit only on a branch that will never be
rebased, which is not a branch this repo has.** A content hash — of the spec file,
or of the thresholds themselves — would have survived. That is the shape to reach
for next time and it is written up in the corpus README.

**At scale, replace with:** a salt derived from the pre-registration's content
hash rather than from its commit SHA. The interface already matches — a fixed
string committed before the draw — and only its derivation changes.

**What an item is.** A (run, case-id, axis) triple pointing at an answer that was
already committed by an earlier milestone — never a fresh model call, never an
authored answer. Authored band anchors sit where their author put them; real
answers bring the awkward cases with them, which is why the corpus is drawn from
`milestones/M00b`, `milestones/M01` and M02's six run files.

Hermetic (G8): committed answers, no model, no network. The *rule* lives here so
it can be tested; its frozen *output* lives in `quality/judge/calibration/`,
which is a two-key path (AI Quality). Changing this file without regenerating
that one fails the contract test, and regenerating it changes a two-key file —
so the corpus cannot move quietly in either direction.

Owning seat: AI Quality.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import asdict, dataclass

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "quality" / "judge" / "calibration" / "items.json"

#: Fixed before the draw: the SHA that the commit carrying `SPEC/03-evals.md` —
#: the branch's first commit, which pre-registered every threshold below — held at
#: the moment the items were drawn.
#:
#: **It no longer names a reachable commit.** The rebase onto #21 moved the spec
#: commit to `815b172…`, and this SHA was never pushed. It is deliberately not
#: updated: the salt's value *is* the draw, so changing it redraws a corpus whose
#: labels are already written. The spec content it pinned is still verifiable —
#: `git rev-parse 815b172:SPEC/03-evals.md` is `9f8212c7…`, byte-identical,
#: because a rebase changes parents and not patches. See the module docstring.
SALT = "6a851c0e876b90d19184ea7ca3ea6b9aea5e63a5"

#: Every committed answer file, in a fixed order. `m01` is here even though
#: SPEC/03 cuts it from the *judged re-score* — being disqualified as a
#: comparator (n = 1, ADR-021) says nothing about whether its answers are useful
#: material for calibrating a judge, and excluding them would narrow the corpus
#: for a reason that does not apply to it.
RUNS: tuple[tuple[str, str], ...] = (
    ("m00b", "milestones/M00b/goldens-run.json"),
    ("m01", "milestones/M01/goldens-run.json"),
    ("m02-control-1", "milestones/M02/runs/m02-control-1.json"),
    ("m02-control-2", "milestones/M02/runs/m02-control-2.json"),
    ("m02-control-3", "milestones/M02/runs/m02-control-3.json"),
    ("m02-tools-1", "milestones/M02/runs/m02-tools-1.json"),
    ("m02-tools-2", "milestones/M02/runs/m02-tools-2.json"),
    ("m02-tools-3", "milestones/M02/runs/m02-tools-3.json"),
)

#: Items per axis, stratified in proportion to the golden set's own axis
#: frequency (groundedness 23, completeness 16, brand_tone 14, concision 7 —
#: 60 axis-instances over 25 cases, halved to 30). Held-out counts are the ones
#: the demotion thresholds key on, so they are named rather than derived.
#:
#: `brand_tone` (4) and `concision` (3) fall below SPEC/03's five-held-out-item
#: floor and are therefore demoted before their agreement is computed. That is
#: the insufficient-evidence rule working as written, not a defect in the draw:
#: the rule was fixed before these counts were known.
QUOTAS: tuple[tuple[str, int, int], ...] = (
    # axis, total, held-out
    ("groundedness", 11, 7),
    ("completeness", 8, 6),
    ("brand_tone:meridian-sports", 7, 4),
    ("concision", 4, 3),
)

#: Refusal items, drawn deliberately. A refused answer carries no prose, so the
#: judge must return *not-applicable* rather than a band — and the only way to
#: know it does is to have some in the corpus. They already FAIL deterministically,
#: so they never reach the veto; they are here to pin behaviour, not to score it.
REFUSAL_ITEMS = 3

#: No more than this many items may share one (run, case-id), or one run. A draw
#: that concentrated on a handful of answers would measure the judge's opinion of
#: those answers rather than of the corpus.
MAX_PER_ANSWER = 2
MAX_PER_RUN = 5


@dataclass(frozen=True)
class Item:
    id: str
    run: str
    case_id: str
    axis: str
    split: str
    refusal: bool
    answer_sha256: str


def _load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def answer_digest(answer) -> str:
    """Pins the exact bytes an item refers to.

    Without it a label points at a case id, and a case id points at whatever the
    answer file says today. The label would then survive an edit to the thing it
    was a label *of*, which is the quiet version of relabelling."""
    return hashlib.sha256(
        json.dumps(answer, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _draw(run: str, case_id: str, axis: str) -> str:
    return hashlib.sha256(f"{SALT}|{run}|{case_id}|{axis}".encode()).hexdigest()


def candidates(cases: list) -> list[dict]:
    """Every (run, case, axis) triple, in canonical order with its draw value.

    Canonical means: runs in `RUNS` order, cases in `cases.yaml` order, axes
    sorted. The golden set lists axes inconsistently — `[groundedness,
    completeness, brand_tone]` in one case and `[brand_tone, groundedness]` in
    another — so sorting is what stops the corpus depending on the order somebody
    happened to type."""
    found = []
    for run, rel in RUNS:
        answers = _load(rel)
        for case in cases:
            record = answers.get(case["id"])
            if not isinstance(record, dict) or not isinstance(record.get("answer"), dict):
                continue
            answer = record["answer"]
            for axis in sorted(set(case.get("judge", {}).get("axes", ()))):
                found.append({
                    "run": run,
                    "case_id": case["id"],
                    "axis": axis,
                    "refusal": "refused_by_gateway" in answer,
                    "answer_sha256": answer_digest(answer),
                    "draw": _draw(run, case["id"], axis),
                })
    return found


def select(cases: list) -> list[Item]:
    """The 30 items, drawn once and reproducible forever.

    Two passes, and the order matters. Refusals are drawn **first**, against the
    same quotas, because drawing them last would mean taking them only from
    whatever the axis quotas had left over — which would make "the corpus
    contains refusals" true by luck rather than by rule."""
    pool = candidates(cases)
    quota = {axis: total for axis, total, _ in QUOTAS}
    taken: list[dict] = []
    per_answer: dict[tuple[str, str], int] = {}
    per_run: dict[str, int] = {}

    def accept(item) -> bool:
        key = (item["run"], item["case_id"])
        if quota.get(item["axis"], 0) <= 0:
            return False
        if per_answer.get(key, 0) >= MAX_PER_ANSWER or per_run.get(item["run"], 0) >= MAX_PER_RUN:
            return False
        quota[item["axis"]] -= 1
        per_answer[key] = per_answer.get(key, 0) + 1
        per_run[item["run"]] = per_run.get(item["run"], 0) + 1
        taken.append(item)
        return True

    for item in sorted((c for c in pool if c["refusal"]), key=lambda c: c["draw"]):
        if sum(1 for t in taken if t["refusal"]) >= REFUSAL_ITEMS:
            break
        accept(item)

    for item in sorted((c for c in pool if not c["refusal"]), key=lambda c: c["draw"]):
        accept(item)

    short = {axis: n for axis, n in quota.items() if n > 0}
    if short:
        # Recorded as a failure rather than quietly returning a smaller corpus.
        # A corpus that silently shrinks is the exact direction ADR-009 says
        # matters, and it would show up later as a better agreement from a
        # narrower measurement.
        raise SystemExit(f"error: the draw could not fill every stratum: {short}")

    items: list[Item] = []
    for axis, _total, held in QUOTAS:
        stratum = sorted((t for t in taken if t["axis"] == axis), key=lambda c: c["draw"])
        dev = len(stratum) - held
        for n, entry in enumerate(stratum):
            items.append(Item(
                id="",
                run=entry["run"],
                case_id=entry["case_id"],
                axis=axis,
                split="dev" if n < dev else "held-out",
                refusal=entry["refusal"],
                answer_sha256=entry["answer_sha256"],
            ))
    # Ids are assigned last, over the whole corpus in a stable order, so that an
    # item's id never encodes which stratum or split it landed in. A labeller
    # reading `cal-07` should not be able to infer that it is held-out.
    ordered = sorted(items, key=lambda i: _draw(i.run, i.case_id, i.axis))
    return [
        Item(f"cal-{n:02d}", i.run, i.case_id, i.axis, i.split, i.refusal, i.answer_sha256)
        for n, i in enumerate(ordered, 1)
    ]


def as_json(items: list[Item]) -> str:
    return json.dumps(
        {"salt": SALT, "items": [asdict(i) for i in items]}, indent=2
    ) + "\n"


def committed() -> dict:
    return json.loads(CORPUS.read_text(encoding="utf-8"))


#: The rubric's own band wording, verbatim, so the review worksheet can carry a
#: reminder without a labeller having to hold two files open.
#: `tests/test_calibration_corpus.py` asserts every phrase below still appears in
#: `quality/judge/rubric-sports.md` — a summary of a hash-pinned instrument that
#: is allowed to drift from it is worse than no summary at all.
BANDS: dict[str, tuple[str, str, str]] = {
    "groundedness": (
        "Any claim contradicted by, or absent from, the catalog",
        "Claims are consistent with the catalog but reach beyond what is cited",
        "Every factual claim traces to a cited title",
    ),
    "completeness": (
        "Partial, evasive, or answers a different question",
        "Answers the question only",
        "Answers the question and the obvious follow-up",
    ),
    "brand_tone:meridian-sports": (
        "Cruel, profane, hyperbolic, or reads as an advertisement",
        "Accurate but flat, or mildly salesy about an upgrade",
        "On-brand and natural",
    ),
    "concision": (
        "Padded to the point of burying the answer",
        "Padded but readable",
        "Proportionate",
    ),
}


def worksheet(cases: list, labels: dict) -> str:
    """The review aid the AI Quality seat disposes against.

    Generated rather than hand-written, and pinned by a contract test, because a
    labeller who reviews a stale copy of an answer has disposed of nothing. It
    carries the question, the answer as recorded, the axis being judged, the
    rubric's own band wording, and the drafted label with its reasoning.

    It does **not** carry the split. A labeller who can see which items are
    held-out can — consciously or not — label the measured half differently from
    the practice half, and that is the one bias this corpus cannot recover from."""
    by_case = {c["id"]: c for c in cases}
    answers = {label: _load(rel) for label, rel in RUNS}
    drafts = {row["item"]: row for row in labels["labels"]}

    out = [
        "# Calibration label worksheet",
        "",
        "**Generated — do not edit.** Regenerate with:",
        "",
        "```bash",
        "python -m evals.render_worksheet",
        "```",
        "",
        "Disposition happens in `labels.json`, not here. For each item set `final`",
        "to the band you judge correct (`0.0`, `0.5`, `1.0`, or `null` for an item",
        "with no answer to grade) and `disposition` to `agreed` or `changed`. The",
        "**correction rate is published beside every agreement figure**, so a change",
        "here is a recorded act rather than a silent one.",
        "",
        "The dev/held-out split is deliberately absent from this file. Knowing which",
        "items are measured is exactly the knowledge that would bias the labels.",
        "",
        "Read the rubric itself at `quality/judge/rubric-sports.md`; the bands below",
        "are its wording, not a paraphrase.",
        "",
    ]
    for item in committed()["items"]:
        row = drafts[item["id"]]
        case = by_case[item["case_id"]]
        answer = answers[item["run"]][item["case_id"]]["answer"]
        band_0, band_half, band_1 = BANDS[item["axis"]]
        drafted = "n/a" if row["drafted"] is None else f"{row['drafted']:.1f}"

        out += [
            "---",
            "",
            f"## {item['id']} — `{item['axis']}`",
            "",
            f"*{item['run']} / {item['case_id']}*",
            "",
            f"**Viewer asked:** {case['input']}",
            "",
            f"**Viewer context:** `{case.get('viewer')}`",
            "",
        ]
        if "refused_by_gateway" in answer:
            out += [f"**Recorded:** refused by the gateway "
                    f"(`{answer['refused_by_gateway']}`) — no answer to grade.", ""]
        elif "unparsed" in answer:
            out += ["**Recorded:** the harness could not decode this turn "
                    "(`unparsed`, no `answer` field) — no answer to grade.", ""]
        else:
            out += [
                f"**Answered:** {answer.get('answer')}",
                "",
                f"**Cited:** `{answer.get('cited_titles')}`",
                "",
            ]
        out += [
            f"| band | {item['axis']} |",
            "|---|---|",
            f"| 1.0 | {band_1} |",
            f"| 0.5 | {band_half} |",
            f"| 0.0 | {band_0} |",
            "",
            f"**Drafted: {drafted}**",
            "",
            f"{row['reason']}",
            "",
        ]
    return "\n".join(out) + "\n"


def correction_rate(labels: dict) -> dict:
    """What the AI Quality seat's disposition changed.

    **Derived, never written down by hand.** The correction rate is the only
    quantitative protection on an agreement number measured against ai-proposed
    labels (SPEC/03's amendment), so a hand-entered figure would be the one number
    in this milestone that nothing checks.

    It is a weak protection and the direction of its weakness is asymmetric. A
    **high** rate is informative: the seat read the drafts and disagreed, so the
    labels carry human judgement. A rate near **zero** is not: it cannot
    distinguish drafts that were right from a disposition that did not look hard,
    and no computation here can tell them apart. It is therefore published as a
    limitation of the measurement rather than as a property of the judge."""
    rows = labels["labels"]
    changed = [r["item"] for r in rows if r["disposition"] == "changed"]
    return {
        "disposed": len(rows),
        "changed": len(changed),
        "changed_items": changed,
        "rate": round(len(changed) / len(rows), 4) if rows else 0.0,
    }
