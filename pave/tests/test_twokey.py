"""
G9 enforcement: the two-key rule, machine-checked.

These tests pin the ways a threshold or baseline change could reach `main`
without a recorded second key. ROLES.md names the failure mode directly —
"update the baseline" is the standard way eval gates get neutered — so the
important tests here are the ones that try to sneak such a change through.

Owning seat: AI Quality (rules) · Platform Engineering (mechanism).
"""
import pathlib

import pytest

from pave import twokey

ROOT = pathlib.Path(twokey.__file__).resolve().parents[1]

GOOD_RATIONALE = "M03 published a judge agreement of 0.91, which supports raising the floor"

BODY_OK = f"""
Raises the groundedness floor for highlights-agent.

Two-Key-Disposition: ai-quality
Two-Key-Rationale: {GOOD_RATIONALE}
"""


# --- PRs that touch nothing two-key are unaffected -----------------------------

def test_ordinary_pr_is_not_gated():
    assert twokey.evaluate(["pave/cli.py", "README.md"], "") == []


def test_service_source_is_not_two_key():
    """Service teams own their own prompts and business logic outright."""
    assert twokey.evaluate(["services/highlights-agent/src/agent.py"], "") == []


# --- the paths that are gated --------------------------------------------------

@pytest.mark.parametrize(
    "path",
    [
        "services/highlights-agent/evals/golden/cases.yaml",
        "quality/judge/rubric-sports.md",
        "quality/verdicts/schema.json",
        "evals/history/2026-08-15-goldens.json",
        ".github/workflows/quality-gate.yml",
        "platform/registry/tools.yaml",
        "quality/adversarial/probes.yaml",
    ],
)
def test_two_key_paths_block_without_a_disposition(path):
    assert twokey.evaluate([path], "") != []


def test_baseline_reset_cannot_ride_along_unattested():
    """The named failure mode: a baseline edit buried in a feature PR."""
    changed = ["services/highlights-agent/src/agent.py", "evals/history/goldens.json"]
    problems = twokey.evaluate(changed, "Small refactor, no behaviour change.")
    assert problems and "ai-quality" in problems[0]


def test_correct_disposition_unblocks():
    assert twokey.evaluate(["quality/judge/rubric-sports.md"], BODY_OK) == []


# --- both keys, when a rule needs two ------------------------------------------

def test_gate_criteria_need_both_seats():
    one_key = f"Two-Key-Disposition: ai-quality\nTwo-Key-Rationale: {GOOD_RATIONALE}"
    problems = twokey.evaluate([".github/workflows/quality-gate.yml"], one_key)
    assert problems and "platform-eng" in problems[0]

    both = one_key + "\nTwo-Key-Disposition: platform-eng"
    assert twokey.evaluate([".github/workflows/quality-gate.yml"], both) == []


def test_consequence_class_change_needs_legal_sign_off():
    """Raising an action's blast radius is a compliance decision (ROLES.md seat 6)."""
    tool_only = f"Two-Key-Disposition: tool-owner\nTwo-Key-Rationale: {GOOD_RATIONALE}"
    problems = twokey.evaluate(["platform/registry/tools.yaml"], tool_only)
    assert problems and "legal-sp" in problems[0]


# --- the rationale has to be reasoning ------------------------------------------

def test_disposition_without_rationale_blocks():
    problems = twokey.evaluate(["quality/judge/rubric-sports.md"], "Two-Key-Disposition: ai-quality")
    assert problems and "rationale" in problems[0].lower()


@pytest.mark.parametrize("text", ["n/a", "none", "-", "TBD", "as discussed"])
def test_placeholder_rationale_blocks(text):
    body = f"Two-Key-Disposition: ai-quality\nTwo-Key-Rationale: {text}"
    assert twokey.evaluate(["quality/judge/rubric-sports.md"], body) != []


def test_short_rationale_blocks():
    body = "Two-Key-Disposition: ai-quality\nTwo-Key-Rationale: fixing it"
    assert twokey.evaluate(["quality/judge/rubric-sports.md"], body) != []


def test_multiline_rationale_is_accepted():
    body = (
        "Two-Key-Disposition: ai-quality\n"
        "Two-Key-Rationale: the calibration run published an agreement number\n"
        "  that supports this floor, and headroom stays at three cases\n"
    )
    assert twokey.evaluate(["quality/judge/rubric-sports.md"], body) == []


# --- probe corpus additionally needs an ADR --------------------------------------

def test_probe_corpus_change_requires_an_adr():
    body = f"Two-Key-Disposition: security\nTwo-Key-Rationale: {GOOD_RATIONALE}"
    problems = twokey.evaluate(["quality/adversarial/probes.yaml"], body)
    assert problems and "ADR" in problems[0]


def test_probe_corpus_change_with_a_real_adr_passes():
    body = (
        f"Two-Key-Disposition: security\nTwo-Key-Rationale: {GOOD_RATIONALE}\n"
        "ADR: docs/adr/ADR-013-solo-operator-enforcement.md\n"
    )
    assert twokey.evaluate(["quality/adversarial/probes.yaml"], body, repo_root=ROOT) == []


def test_citing_a_nonexistent_adr_blocks(tmp_path):
    body = (
        f"Two-Key-Disposition: security\nTwo-Key-Rationale: {GOOD_RATIONALE}\n"
        "ADR: docs/adr/ADR-999-imaginary.md\n"
    )
    problems = twokey.evaluate(["quality/adversarial/probes.yaml"], body, repo_root=tmp_path)
    assert problems and "does not exist" in problems[0]


# --- the rules cannot be weakened without tripping themselves --------------------

def test_editing_the_two_key_rules_is_itself_two_key():
    """Otherwise the first move against G9 is to delete G9's enforcement."""
    assert twokey.evaluate(["pave/twokey.py"], "") != []
    assert twokey.evaluate([".github/workflows/two-key.yml"], "") != []


# --- path normalisation ----------------------------------------------------------

def test_windows_separators_are_matched():
    """`git diff --name-only` gives forward slashes, but a local invocation may
    not. A path that fails to match is a path that silently skips the check."""
    assert twokey.evaluate(["quality\\judge\\rubric-sports.md"], "") != []


def test_render_names_the_seats_and_the_files():
    out = twokey.render(["quality/judge/rubric-sports.md"], ["missing disposition from ai-quality"])
    assert "ai-quality" in out and "rubric-sports.md" in out and "BLOCKED" in out
