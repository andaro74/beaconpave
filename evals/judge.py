"""
The judge, hermetic half (SPEC/03).

**This module never calls a model.** It renders the prompt, and it turns committed
judge output into bands, vetoes, agreement figures and demotion decisions. The
model call lives in `services/highlights-agent/run_judge.py`, which goes through
the gateway (G1) and writes its raw output to a file that gets committed.

That split is the same one the agent already has, and it buys the same thing: the
part nobody can regenerate is committed, and everything downstream of it is a pure
function a stranger can re-derive with no AWS account.

## What composes with what, in order

Three summarisation layers, and `3p^2 - 2p^3` applies at the first and third:

1. **judge majority** — per (answer-sample, case, axis), the majority band across
   `k_judge`. Three bands, so a 1-1-1 split is reachable *here* and nowhere else.
2. **the veto** — per (answer-sample, case): the deterministic verdict AND no
   axis at `0.0`. The judge can only subtract; it never rescues a case the
   deterministic asserts failed.
3. **answer majority** — unchanged from M02's `summarise`.

## Two things that look like details and are not

**An undecided axis does not veto.** A veto is a decision, and a 1-1-1 split is
the absence of one. Undecided axes are counted and published instead, and too many
of them demotes the axis — a judge that cannot repeat itself is not calibrated by
the subset of answers where it happened to.

**A demoted axis does not enter `result` at all.** Not as `ADVISORY`: that token
already means "no strict majority" to `summarise`, and `emit_verdict` makes it
block. A demoted judge whose axes blocked would be strictly worse than a
calibrated one, which is the opposite of what demotion is for.

Owning seat: AI Quality.
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "quality" / "judge" / "rubric-sports.md"
PROMPT = ROOT / "quality" / "judge" / "prompt.md"
FROZEN = ROOT / "quality" / "judge" / "frozen.json"
CATALOG = ROOT / "data" / "catalog.json"

#: The golden set's fixed evaluation clock, the same instant the answers were
#: produced at. A judge reading "tonight" against a different clock would score a
#: correct answer wrong, and would do it silently.
CLOCK = "2026-09-13T18:00:00Z"

BANDS = (0.0, 0.5, 1.0)

#: Below this band an axis vetoes the case. Only `0.0` does: the rubric's `0.5` is
#: "accurate but flat", "reaches beyond what is cited", "padded but readable" —
#: quality signals, not failures. `0.0` is "contradicted by the catalog", "answers
#: a different question", "cruel, profane, hyperbolic".
VETO_BAND = 0.0

#: SPEC/03, fixed before the corpus was labelled and before any judge ran.
AGREEMENT_THRESHOLD = 0.75
MIN_SCORABLE_HELD_OUT = 5
MAX_UNDECIDED_FRACTION = 0.20


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rubric_axes() -> str:
    """The scoring criteria, and **only** the scoring criteria.

    Found by a test that asserted the prompt carries no answer key, and failed.
    Embedding `rubric-sports.md` whole ships its `## Headroom` section, which tells
    the model that two or three golden cases are *authored to sit near this
    rubric's threshold*. That is corpus metadata wearing the clothes of scoring
    criteria, and a judge told that some cases are deliberately borderline has been
    nudged about the answer before it has read one.

    The same cut drops the seat header, the M00a status note, the paragraph about
    `cited_titles` membership, and the ADV-005 boundary note for the Security seat.
    All of it is written for a reviewer and none of it defines a band.

    **This is M02's finding arriving exactly where SPEC/03 said it would.** M02
    shipped a reviewer-facing rationale as a tool `description` and called it
    coaching; the spec predicted the rubric becomes model-facing the moment the
    judge reads it. What it predicted was the digest pin. What it missed was that
    the file also had to be *cut*.

    The slice is `## Axes` up to `## Headroom`. Both digests are pinned: the whole
    file, so any change to it is visible, and the slice, so a change to what the
    model actually reads is visible separately."""
    text = RUBRIC.read_text(encoding="utf-8")
    # Anchored to line starts. The unanchored form matched the rubric's own prose
    # *about* the slice — "Everything from `## Axes` to `## Headroom` is sent to
    # the model verbatim" — and returned fourteen characters. The prompt still
    # rendered, the judge would still have returned bands, and every one of them
    # would have been scored against no rubric at all.
    start, end = text.find("\n## Axes\n"), text.find("\n## Headroom\n")
    # A renamed or deleted heading is the same failure as a bad slice, and `index`
    # would raise a ValueError naming neither the file nor the cause.
    sliced = text[start:end].strip() + "\n" if 0 <= start < end else ""
    # Loud rather than silent. A rubric that fails to slice is not a degraded
    # instrument, it is a different one, and it is the failure mode least likely
    # to be noticed from the output: the bands look exactly the same.
    missing = [a for a in ("groundedness", "completeness", "brand_tone:meridian-sports",
                           "concision") if a not in sliced]
    if missing or len(sliced) < 500:
        raise SystemExit(
            f"error: the rubric slice is {len(sliced)} characters and is missing {missing}. "
            "The judge would score against a rubric that is not there. Check the `## Axes` "
            "and `## Headroom` headings in quality/judge/rubric-sports.md."
        )
    return sliced


def render_prompt() -> str:
    """The judge's system prompt, with the rubric's axes and the catalog embedded.

    Embedding makes them **model-facing text**: a word changed in either changes
    every band the judge returns. Both are pinned, and `instrument()` records the
    digests that go into the history row."""
    template = PROMPT.read_text(encoding="utf-8").split("\n---\n", 1)[1]
    return template.format(
        rubric=rubric_axes(),
        catalog=CATALOG.read_text(encoding="utf-8"),
        clock=CLOCK,
    )


def instrument() -> dict:
    """What produced a set of bands, as it goes into a history entry.

    The judge is the first instrument in this repo whose output can move without a
    commit, so the row has to say which instrument it is — `supersedes` cannot,
    because it means *corrects a wrong entry* and a moved instrument corrects
    nothing (ADR-012's M03 amendment)."""
    return {
        "prompt_sha256": digest(PROMPT.read_text(encoding="utf-8")),
        "rubric_sha256": digest(RUBRIC.read_text(encoding="utf-8")),
        "rubric_axes_sha256": digest(rubric_axes()),
        "rendered_sha256": digest(render_prompt()),
    }


def frozen() -> dict:
    return json.loads(FROZEN.read_text(encoding="utf-8")) if FROZEN.is_file() else {}


def is_frozen() -> bool:
    """Whether the prompt now is the prompt that was frozen.

    The dev/held-out split is only worth having if the prompt stopped moving
    before the held-out half was looked at. Freezing is a commit — a recorded act
    — and `held_out_guard` refuses the measured half until it has happened."""
    marks = frozen()
    if not marks:
        return False
    now = instrument()
    return all(marks.get(k) == now[k]
               for k in ("prompt_sha256", "rubric_sha256", "rubric_axes_sha256"))


def held_out_guard() -> None:
    """Raises unless the prompt is frozen.

    This is the one place the spec's central discipline is enforced rather than
    promised: *an agreement number computed on the set the judge was tuned against
    measures nothing.* Iterating the prompt is allowed, on the 10 dev items, for as
    long as it takes. Looking at the other 20 first is not."""
    if not is_frozen():
        raise SystemExit(
            "error: the judge prompt is not frozen, so held-out items may not be scored.\n"
            "Iterate against the 10 dev items only. When the prompt stops moving, commit\n"
            "quality/judge/frozen.json with the current digests — freezing is a recorded\n"
            "act, and an agreement number measured on the set the judge was tuned against\n"
            "measures nothing (SPEC/03)."
        )


# --- bands --------------------------------------------------------------------


def majority_band(samples: list) -> float | None:
    """The band a judge returned in a strict majority of `k_judge` samples.

    `None` means **undecided** — no strict majority. With three bands and k=3 this
    is genuinely reachable, unlike the case-level tie M02 wrote the rule for and
    correctly predicted could not occur. Undecided is recorded, counted, and does
    not veto: a veto is a decision and this is the absence of one."""
    usable = [s for s in samples if s in BANDS]
    if not usable:
        return None
    counts = collections.Counter(usable)
    band, count = counts.most_common(1)[0]
    return band if count > len(samples) / 2 else None


def case_bands(axes: list, samples: list[dict]) -> dict:
    """Per-axis majority for one case across `k_judge` judge samples.

    `samples` is one dict per judge run: `{axis: band}`. An axis the judge failed
    to return is absent rather than guessed at — a missing band is evidence about
    the judge, and filling it in would destroy that evidence."""
    return {axis: majority_band([s.get(axis) for s in samples]) for axis in axes}


def veto(bands: dict, calibrated: set) -> tuple[bool, list]:
    """Does the judge subtract this case, and on which axes.

    **Only calibrated axes are consulted.** A demoted axis is not passed in, so it
    cannot reach `result` in any form — including as `ADVISORY`, which would
    block. Only `0.0` vetoes, and an undecided axis (`None`) never does."""
    hits = sorted(a for a, b in bands.items() if a in calibrated and b == VETO_BAND)
    return bool(hits), hits


# --- agreement ----------------------------------------------------------------


def cohens_kappa(labels: list, predictions: list) -> float | None:
    """Agreement corrected for the agreement two raters would reach by chance.

    Recorded beside raw agreement because **raw agreement on an imbalanced label
    set is inflated**, and this corpus is imbalanced by construction: three
    milestones of a governed sports agent produced no answer the rubric would call
    cruel or hyperbolic.

    **What it cannot correct for, and this matters more here than the imbalance:**
    kappa assumes the two raters err independently. The labels were drafted by one
    Anthropic model and the bands come from another, so correlated error is the
    expected failure mode and kappa rewards it exactly as it rewards genuine
    agreement. Published as the check on raw agreement, never as a defence of it.

    `None` when it is undefined — one rater used a single category, which makes
    expected agreement 1.0 and the correction a division by zero. That is not an
    error to hide: it is what `brand_tone` looks like, and it is the reason the
    axis is demoted on evidence rather than on this number."""
    if not labels or len(labels) != len(predictions):
        return None
    n = len(labels)
    observed = sum(1 for a, b in zip(labels, predictions, strict=True) if a == b) / n
    lab, pred = collections.Counter(labels), collections.Counter(predictions)
    expected = sum(lab[c] * pred[c] for c in set(lab) | set(pred)) / (n * n)
    if expected >= 1.0:
        return None
    return round((observed - expected) / (1 - expected), 4)


def agreement(items: list) -> dict:
    """Raw exact-band agreement and kappa over scorable items.

    `items` is `[{"axis":…, "label":…, "band":…}]`. **Items with no answer to
    grade never appear here.** A refusal, an undecodable turn and a missing answer
    are decided by the harness before any model call, so judge and label agree on
    them by construction — counting them would add automatic agreements and
    inflate every figure. They pin the harness's behaviour instead, which is what
    the corpus drew them for.

    An **undecided** band (no majority at `k_judge`) is a disagreement with any
    label. The judge was asked and did not answer the same way twice; scoring that
    as agreement would let an unrepeatable judge look calibrated."""
    labels = [i["label"] for i in items]
    bands = [i["band"] for i in items]
    exact = sum(1 for a, b in zip(labels, bands, strict=True) if a == b)
    return {
        "n": len(items),
        "exact": exact,
        "raw": round(exact / len(items), 4) if items else 0.0,
        "kappa": cohens_kappa(labels, bands),
        "undecided": sum(1 for b in bands if b is None),
        "label_distribution": {str(k): v for k, v in sorted(collections.Counter(labels).items())},
    }


def demotion(axis: str, stats: dict) -> dict:
    """Calibrated or advisory, by the three rules SPEC/03 fixed in advance.

    Order matters and is deliberate: **evidence first**. An axis without enough
    held-out items has no agreement worth reading, so reporting a figure and then
    demoting on a separate ground would invite someone to quote the figure."""
    reasons = []
    if stats["n"] < MIN_SCORABLE_HELD_OUT:
        reasons.append(
            f"{stats['n']} scorable held-out item(s), below the floor of "
            f"{MIN_SCORABLE_HELD_OUT}: not enough evidence is not calibration"
        )
    undecided_fraction = stats["undecided"] / stats["n"] if stats["n"] else 1.0
    if undecided_fraction > MAX_UNDECIDED_FRACTION:
        reasons.append(
            f"{undecided_fraction:.0%} of items undecided at k_judge, above "
            f"{MAX_UNDECIDED_FRACTION:.0%}: a judge that cannot repeat itself is not "
            "calibrated by the answers where it happened to"
        )
    if stats["raw"] < AGREEMENT_THRESHOLD:
        reasons.append(
            f"raw exact-band agreement {stats['raw']:.2f} below {AGREEMENT_THRESHOLD}"
        )
    return {
        "axis": axis,
        "status": "demoted" if reasons else "calibrated",
        "reasons": reasons,
        **stats,
    }
