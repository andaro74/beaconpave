"""
The comparator M01's golden score is read against, pinned so it cannot drift.

ADR-016 established that a score recorded before the instrument changed and one
recorded after it measure different things, and closed with the rule this module
enforces: *whenever the instrument changes, the row needs a footnote before the
number needs an explanation.* That was left as a discipline — something a person
remembers at milestone close. This makes it a check.

**M01 compares against 18/25, not the recorded 15/25.** The recorded entry is
correct and stays exactly as it is: 15/25 is what was measured on the day, with
the instrument as it then stood. 18/25 is the *same answers* scored by today's
runner, which is the only number an M01 score can honestly be read against.

That number is deliberately **not** in `evals/history/` — ADR-016 and the commit
that closed M00b both say so outright. It does not need to be. History exists for
numbers that cannot be regenerated, because a model produced them; the model's
output is the part that was committed (`milestones/M00b/goldens-run.json`), and
everything downstream of it is a pure function. Re-deriving 18/25 here is
stronger evidence than a recorded row, because a reader can watch it happen
rather than trust that it once did.

What this catches: the judge arrives at M03 (ADR-012), which moves the instrument
again. On that day this test fails, names the milestone whose footnote has gone
stale, and stops M01's progression row from quietly becoming false.

Hermetic (G8): committed answers, committed scorer, no model. Owning seat: AI
Quality.
"""
import json
import pathlib

import yaml

from evals.deterministic import Scorer, tally

ROOT = pathlib.Path(__file__).resolve().parents[1]
M00B_ANSWERS = ROOT / "milestones" / "M00b" / "goldens-run.json"
M00B_RECORDED = ROOT / "evals" / "history" / "m00b-goldens.json"

#: The m00b answers under the *current* instrument. M01's progression row reads
#: its 19/25 against this, and SPEC/01 pre-registered 18/25 +/- 2 against it.
M00B_UNDER_CURRENT_INSTRUMENT = 18

#: What was measured on the day. Never changes: it is not wrong, it is historical.
M00B_AS_RECORDED = 15


def rescore_m00b():
    cases = yaml.safe_load(
        (ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml")
        .read_text(encoding="utf-8")
    )
    catalog = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    answers = json.loads(M00B_ANSWERS.read_text(encoding="utf-8"))
    return tally(Scorer(root=ROOT).score_suite(cases, answers, catalog))


def test_the_m00b_answers_were_kept():
    """Everything below depends on them. Keeping a run's raw answers is what let
    M01 prove that its own +1 was four cases of variance hiding three cases of
    regression — a claim that would otherwise have been arguable prose."""
    assert M00B_ANSWERS.is_file(), (
        "m00b's raw answers are gone. Without them the comparator cannot be re-derived "
        "and every later milestone's golden delta becomes unfalsifiable."
    )


def test_the_recorded_m00b_entry_is_untouched():
    """History is append-only. 15/25 is not a mistake to be corrected — it is the
    correct measurement for the instrument that existed when it was taken, which
    is exactly why `supersedes` does not apply to it."""
    recorded = json.loads(M00B_RECORDED.read_text(encoding="utf-8"))
    assert recorded["scores"]["passed"] == M00B_AS_RECORDED
    assert "supersedes" not in recorded, (
        "the m00b entry has been marked as superseded. It was not wrong; the instrument "
        "moved underneath it. Marking a correct entry as corrected misleads every reader "
        "who later tries to work out which number was real."
    )


def test_the_comparator_still_scores_18_of_25():
    """The pin.

    If this fails, the instrument moved. That is allowed — ADR-016 is itself a
    record of it happening twice — but it is never allowed to happen silently.
    Before changing the number below, work out which recorded scores are no longer
    comparable, and footnote the progression table for each of them. The number
    here is the last line of defence for a footnote nobody remembered to write."""
    scores = rescore_m00b()
    assert scores["passed"] == M00B_UNDER_CURRENT_INSTRUMENT, (
        f"the m00b answers now score {scores['passed']}/25 under the current runner, not "
        f"{M00B_UNDER_CURRENT_INSTRUMENT}/25. The instrument has moved since M01. Every "
        "progression row comparing golden scores across that change needs a footnote, and "
        "M01's row currently reads its 19/25 against 18/25."
    )


def test_the_instrument_change_is_worth_three_points():
    """The concrete form of ADR-016's warning, kept executable.

    Three points of 'improvement' with no system change whatsoever. It is stated
    as a difference rather than two constants so that the gap itself is the thing
    under test — that gap is what a reader mistakes for progress."""
    assert M00B_UNDER_CURRENT_INSTRUMENT - M00B_AS_RECORDED == 3
