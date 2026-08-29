"""
G9 enforcement: the two-key rule, machine-checked.

These tests pin the ways a threshold or baseline change could reach `main`
without a recorded second key. ROLES.md names the failure mode directly —
"update the baseline" is the standard way eval gates get neutered — so the
important tests here are the ones that try to sneak such a change through.

Owning seat: AI Quality (rules) · Platform Engineering (mechanism).
"""
import json
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


# --- a pointer is not a reason, at any length -----------------------------------
#
# The check used to be `len(rationale) < 24` and the refusal message published
# that number. Measured: `"see commit abc123"` was rejected at 17 characters and
# `"see commit abc123def4567890"` passed at 27 — the identical non-rationale,
# padded to clear a bar the gate had just announced. The rule counts substance
# now, so padding a pointer makes it longer and no more of a reason.

GATED = ["quality/judge/rubric-sports.md"]


def _body(rationale: str) -> str:
    """A minimal attested body. Built without escapes on purpose — the newline
    is the only structure the trailer parser needs."""
    return "Two-Key-Disposition: ai-quality" + chr(10) + "Two-Key-Rationale: " + rationale


@pytest.mark.parametrize("pointer", [
    "see commit abc123",
    "see commit abc123def4567890",              # the same pointer, padded past 24
    "see commit abc123 for the details",
    "per the ADR",
    "refer to the commit message",
    "as discussed in the previous PR",
    "https://github.com/andaro74/beaconpave/pull/28",
    "#28",
])
def test_a_pointer_rationale_blocks_however_long_it_is(pointer):
    problems = twokey.evaluate(GATED, _body(pointer))
    assert problems, f"{pointer!r} was accepted as reasoning"
    assert "points at a reason" in problems[0]


def test_the_refusal_does_not_publish_the_bar_it_enforces():
    """A gate that states its own numeric threshold in the refusal is issuing
    instructions for clearing one. The message names the defect instead."""
    problems = twokey.evaluate(GATED, _body("see commit abc123"))
    assert problems
    assert str(twokey.MIN_SUBSTANTIVE_WORDS) not in problems[0]
    assert "character" not in problems[0].lower()
    assert "word" not in problems[0].lower()


def test_padding_a_pointer_never_helps():
    """The property, stated directly: length is orthogonal to substance."""
    short = "see commit abc123"
    padded = short + " for the details as discussed above in the previous PR " * 6
    assert len(padded) > 300
    for text in (short, padded):
        assert twokey.evaluate(GATED, _body(text)), (
            f"a {len(text)}-character pointer was accepted")


def test_a_real_rationale_clears_it_without_trying():
    """The other half. A rule that rejects pointers and also rejects genuine
    reasoning has moved the problem rather than solved it."""
    real = ("The comparator moves because ADV-010 blocked under guardrail v2 and did "
            "not under v1; the pin is derived from the recorded entry rather than typed.")
    assert twokey.evaluate(GATED, _body(real)) == []


def test_references_do_not_count_toward_substance():
    """Pointing harder must not satisfy a rule about not pointing."""
    stuffed = ("see 9274f97 and 63572ae and 883183f and ADR-031 and ADR-032 and "
               "ADR-033 and #28 and #29 and SPEC/04-gate.md")
    assert twokey.evaluate(GATED, _body(stuffed)), (
        "a rationale made entirely of references was accepted")

# --- what the gate READS: the committed corpus is the arbiter --------------------
#
# Three versions of this check were verified against bodies its author wrote by
# hand, and a seat defeated each one with a body he had not thought to write. The
# corpus below is every merged PR body in this repository that mentions an
# attestation, stored as the BYTES GitHub delivered -- CRLF and all -- with what
# `main`'s parser read from each one pinned beside it. The expectation is main's
# behaviour, so this file cannot silently record whatever the change happens to do.

CORPUS = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "pr_bodies.json").read_text(encoding="utf-8")
)


def test_the_corpus_is_the_real_thing_and_not_a_sample():
    """If this shrinks, every claim below covers less than it says.

    **The CRLF check reads the BYTES, not the `eol` label.** Committing this file
    printed `warning: CRLF will be replaced by LF the next time Git touches it`,
    and a guard that trusted the label would have gone on passing after a
    normalisation stripped the carriage returns out of the bodies -- leaving a
    corpus that no longer contains the one thing it was collected to contain. That
    is the shape SPEC/06 A24 registers: a fixture guarded by a marker instead of
    by its payload. The content survives here only because the bodies are
    JSON-escaped inside the strings, which is luck rather than design, so it is
    asserted rather than assumed."""
    assert len(CORPUS) >= 36
    assert sum(1 for r in CORPUS if r["seats"]) >= 35
    carriage_returns = [r["number"] for r in CORPUS if "\r\n" in r["body"]]
    assert len(carriage_returns) >= 6, (
        f"the CRLF bodies are the point of this corpus and only {carriage_returns} "
        f"still carry a carriage return"
    )
    labelled = [r["number"] for r in CORPUS if r["eol"] == "crlf"]
    assert carriage_returns == labelled, "the label and the bytes disagree"


@pytest.mark.parametrize("row", CORPUS, ids=lambda r: f"PR{r['number']}")
def test_every_merged_body_reads_exactly_as_it_did_before(row):
    """Tightening what counts as an attestation must refuse nothing this
    repository has ever written. That sentence was published once already and was
    false: the anchors moved from `^\\s*` to `^[ \\t]*`, `\\s` had been matching the
    `\\r` of a CRLF body, and six merged bodies -- including the two most recent --
    went invisible to the gate. The author had measured the same 36 bodies after
    reading them into normalised text, so the measurement agreed with the claim
    and both were wrong."""
    got = twokey.parse(row["body"])
    assert sorted(got.seats) == row["seats"]
    assert got.adr == row["adr"]


@pytest.mark.parametrize("row", [r for r in CORPUS if r["seats"]][:12],
                         ids=lambda r: f"PR{r['number']}")
def test_line_endings_cannot_change_what_the_gate_reads(row):
    """A body typed in the GitHub web editor arrives CRLF; one sent by
    `gh pr create --body-file` arrives LF. The same attestation must read the same
    either way, in both directions."""
    lf = row["body"].replace("\r\n", "\n")
    crlf = lf.replace("\n", "\r\n")
    cr = lf.replace("\n", "\r")
    assert twokey.parse(lf).seats == twokey.parse(crlf).seats == twokey.parse(cr).seats
    assert twokey.parse(lf).adr == twokey.parse(crlf).adr == twokey.parse(cr).adr


# --- and what it must NOT read ---------------------------------------------------

def _attest(seats=("security",), adr="docs/adr/ADR-001-solo-seats.md"):
    out = "".join(f"Two-Key-Disposition: {s}\n" for s in seats)
    out += f"Two-Key-Rationale: {GOOD_RATIONALE}\n"
    return out + (f"ADR: {adr}\n" if adr else "")


HIDDEN = {
    "a closed HTML comment": "Docs typo fix.\n\n<!--\n%s-->\n",
    "an UNTERMINATED HTML comment": "Docs typo fix.\n\n<!--\n%s",
    "a second comment after a closed one": "<!-- x -->\nDocs typo fix.\n<!--\n%s",
    "a script block": "Docs typo fix.\n<script>\n%s</script>\n",
    "a style block": "Docs typo fix.\n<style>\n%s</style>\n",
    "a backtick fence": "Here is what the gate wants:\n\n```\n%s```\n",
    "a tilde fence": "Here is what the gate wants:\n\n~~~\n%s~~~\n",
}


@pytest.mark.parametrize("label", sorted(HIDDEN), ids=lambda s: s.replace(" ", "_"))
def test_an_attestation_a_reviewer_cannot_see_is_not_an_attestation(label):
    """The unterminated comment is why this is a table and not one test. An
    earlier version stripped `<!-- ... -->` and shipped; two seats defeated it by
    deleting three characters, because an unclosed `<!--` is HTML block type 2 and
    runs to the end of the document. Fixing the instance left the class open."""
    body = HIDDEN[label] % _attest()
    got = twokey.parse(body)
    assert got.seats == frozenset(), label
    assert got.adr is None, label


def test_a_diff_context_line_is_not_an_attestation():
    """A diff CONTEXT line begins with a space, and the anchors allowed leading
    whitespace, so an illustrative hunk pasted into a body carried a live
    disposition. Measured across the corpus: no merged body indents an
    attestation, so refusing it costs nothing real."""
    body = "See the hunk:\n\n```diff\n Two-Key-Disposition: security\n+something\n```\n"
    assert twokey.parse(body).seats == frozenset()
    # ...and outside a fence, where the fence stripper cannot help
    assert twokey.parse("Example:\n\n    Two-Key-Disposition: security\n").seats == frozenset()
    assert twokey.parse("Example:\n\n    ADR: docs/adr/ADR-001-solo-seats.md\n").adr is None


def test_a_visible_attestation_still_parses():
    """The negative control for every case above. Without it they could all pass
    because the parser stopped working."""
    a = twokey.parse("Raising the floor.\n\n" + _attest(["security", "ai-quality"]))
    assert a.seats == frozenset({"security", "ai-quality"})
    assert a.adr == "docs/adr/ADR-001-solo-seats.md"
    assert "0.91" in a.rationale


def test_a_hidden_span_cannot_manufacture_an_attestation():
    """A hidden span is replaced by NOTHING, because that is what the renderer
    does to it.

    An earlier draft of this PR replaced each span with the newlines it contained,
    reasoning that collapsing would pull a following line up and move an honest
    attestation off column 0. The deletability audit found that choice undefended
    and writing this test found the reasoning backwards. The body below renders as
    the single line `xTwo-Key-Disposition: security`; the newline-preserving form
    rewrote it into `x\\n\\nTwo-Key-Disposition: security` and the gate read a
    disposition out of it. Structure the reader never sees must not become
    structure the parser trusts."""
    glued = "x<!--\nc\n-->Two-Key-Disposition: security\n"
    assert twokey.parse(glued).seats == frozenset()

    # ...and an honest body with a comment in the middle of it still reads.
    honest = "Context.\n<!--\na note\nspanning lines\n-->\n" + _attest()
    assert twokey.parse(honest).seats == frozenset({"security"})


def test_an_indented_rationale_is_not_the_rationale():
    """The disposition and `ADR:` anchors each had a test and the rationale's did
    not, so loosening it back to `^\\s*` was silent. A body that QUOTES the format
    in an indented example must not have that example become its reasoning."""
    quoted = (
        "Here is the shape the gate wants:\n"
        "\n"
        "    Two-Key-Rationale: raising the floor because the calibration run says so\n"
        "\n"
        "Two-Key-Disposition: ai-quality\n"
    )
    assert twokey.parse(quoted).rationale == ""
    # The continuation lines of a real rationale are still indented, and still read.
    real = (
        "Two-Key-Disposition: ai-quality\n"
        "Two-Key-Rationale: the calibration run published an agreement number\n"
        "  that supports this floor, and headroom stays at three cases\n"
    )
    assert "headroom stays at three cases" in twokey.parse(real).rationale


def test_markup_inside_a_code_span_is_not_markup():
    """ORDER IS LOAD-BEARING: code comes out before HTML, because text inside a
    fence or a backtick span is not markup and no renderer treats it as such.

    This test exists because the gate refused the PR that introduced it. That PR's
    body explains that an unterminated `<!--` hides the rest of a document, and
    writing that sentence puts those four characters in a backtick span -- where
    the comment pattern's end-of-document fallback matched them and ate every
    attestation below. A body cannot become unattestable by DESCRIBING the rule."""
    body = (
        "An unterminated `<!--` is HTML block type 2, and `<script>` is dropped\n"
        "whole by the sanitiser.\n"
        "\n"
        "```\n"
        "<!-- an example that is not a comment\n"
        "```\n"
        "\n" + _attest(["security", "ai-quality"])
    )
    got = twokey.parse(body)
    assert got.seats == frozenset({"security", "ai-quality"})
    assert got.adr == "docs/adr/ADR-001-solo-seats.md"


def test_an_unterminated_script_tag_does_not_hide_the_rest_of_the_body():
    r"""`<script>` and `<style>` require their closing tag; the `\Z` fallback that
    the comment pattern needs is deliberately absent. An unterminated `<!--` really
    does hide what follows it; an unterminated `<script>` does not -- GitHub's
    sanitiser drops the tag and renders the rest."""
    body = "Mentioning <script> in prose, unclosed.\n\n" + _attest()
    assert twokey.parse(body).seats == frozenset({"security"})
    # ...while a CLOSED script block still hides what it contains.
    hidden = "Docs typo fix.\n<script>\n" + _attest() + "</script>\n"
    assert twokey.parse(hidden).seats == frozenset()


def test_an_attestation_inside_a_backtick_span_is_a_sample():
    """Same rule as a fence, one line down: quoting the format is not using it."""
    assert twokey.parse("Write `Two-Key-Disposition: security` in the body.\n").seats == frozenset()
