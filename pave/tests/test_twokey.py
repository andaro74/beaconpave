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
import subprocess

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
    """**`pave/cli.py` is the example on purpose, and it is ADR-041's line.**

    Decision 7 refused a two-key rule on that file -- three seats then, four more in
    SPEC/06 round 5 -- because it is the most-edited file in the repository and
    gating it "teaches people to attest past a rule without reading it". This
    assertion is what that decision left behind to hold the line.

    ADR-052 measured a shim in `pave/cli.py` making the live gate print SATISFIED
    and exit 0 at the exact baseline, on zero keys. A draft of that ADR keyed the
    file and rewrote this test to keep passing. That is editing the test that holds
    a line in order to cross it, so it is reverted: the gate moved to
    `pave/twokeycli.py`, which CI runs directly and which IS keyed, and `cli.py` is
    no longer in the gate's process to be shimmed."""
    assert twokey.evaluate(["pave/cli.py", "README.md"], "") == []


def test_the_gate_the_workflow_runs_does_not_import_the_cli():
    """The remedy above only holds while `pave/cli.py` stays OUT of the gate's
    process. `pave/twokeycli.py` importing it -- for one helper, at any depth --
    silently restores the shim, and `cli.py` is on no rule by ADR-041 decision 7.

    Asserted here rather than only in `tests/test_twokey_seats.py`'s import walk,
    because this is the direction that must not be reintroduced and the walk states
    a broader property that a future edit could narrow."""
    import ast
    import pathlib

    root = pathlib.Path(twokey.__file__).resolve().parents[1]
    # **Both shapes, because hardcoding one is a false refusal.** Converting the
    # module into a package is legitimate; the first draft read `pave/twokeycli.py`
    # unconditionally and went red on an honest conversion, which is the refusal
    # ADR-051 exists to remove — in a check written to catch a real attack.
    sources = [p for p in (root / "pave" / "twokeycli.py",
                           root / "pave" / "twokeycli" / "__init__.py") if p.is_file()]
    assert sources, "the gate module is gone from both `twokeycli.py` and `twokeycli/`"
    for node in ast.walk(ast.parse("\n".join(
            p.read_text(encoding="utf-8") for p in sources))):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""] + [
                f"{node.module}.{a.name}" for a in node.names if node.module]
        for name in names:
            assert name != "pave.cli" and not name.startswith("pave.cli."), (
                "`pave/twokeycli.py` imports `pave.cli`, which puts the CLI back into "
                "the gate's process — where ADR-052 measured a shim printing SATISFIED "
                "and exit 0 at the baseline, on zero keys. The dependency runs the "
                "other way: `cli.py` imports from here."
            )


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


# --- what discharges an ADR rule (M06) -------------------------------------------
#
# Three versions of this check asked the PR BODY -- does an `ADR:` line name a
# tracked file, is the cited path in the diff, are there N of them. Four seats
# defeated all three, twice with the SAME defect wearing a new shape. Every test
# below builds a real repository, makes a real commit and hands `evaluate` real
# endpoints, because every version verified against a hand-built body passed its
# own tests and lost its round. Hermetic (G8): local git, no network.

OLD_ADR = "# ADR-{n}: an old decision\n\n## Context\n\nsomething was decided here for a reason\n\n## Decision\n\nand recorded\n"
NEW_ADR = ("# ADR-{n}: a real decision\n\n## Context\n\nthe corpus needed a probe "
           "retired because two of them measure the same boundary\n\n## Decision\n\n"
           "retire the duplicate and record why here\n\n## Consequences\n\none fewer probe\n")

#: The three rules that require an ADR, one file each.
GUARDED = ["quality/adversarial/probes.yaml", "pave/infra.py",
           "platform/infra/lib/gateway-stack.ts"]
ALL_THREE = ("security", "ai-quality", "platform-eng")


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout


@pytest.fixture
def repo(tmp_path):
    """A scratch repository carrying three ADRs, committed. Yields (root, base)."""
    root = tmp_path / "r"
    (root / "docs" / "adr").mkdir(parents=True)
    for n, slug in (("001", "solo-seats"), ("007", "webhook-pager"), ("009", "corpus-sizes")):
        (root / "docs" / "adr" / f"ADR-{n}-{slug}.md").write_text(
            OLD_ADR.format(n=n), encoding="utf-8")
    (root / "docs" / "adr" / "README.md").write_text(
        "# Architecture Decision Records\n\n| ADR | Decision |\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    yield root, _git(root, "rev-parse", "HEAD").strip()


def _commit(root, message="change"):
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD").strip()


def _write_adr(root, num, slug, body=None):
    rel = f"docs/adr/ADR-{num}-{slug}.md"
    (root / rel).write_text(body if body is not None else NEW_ADR.format(n=num),
                            encoding="utf-8")
    return rel


def _attested_body(seats=("security",), adrs=(), rationale=GOOD_RATIONALE):
    out = "".join(f"Two-Key-Disposition: {s}\n" for s in seats)
    out += f"Two-Key-Rationale: {rationale}\n"
    return out + "".join(f"ADR: {a}\n" for a in adrs)


def _verdict(root, base, changed, body, head=None):
    return twokey.evaluate(changed, body, repo_root=root, base=base, head=head)


# --- a record is what the diff WRITES ---------------------------------------------

def test_an_adr_written_in_this_diff_discharges_the_rule(repo):
    root, base = repo
    rel = _write_adr(root, "050", "a-real-decision")
    _commit(root)
    assert _verdict(root, base, ["quality/adversarial/probes.yaml", rel],
                    _attested_body(["security"], [rel])) == []


def test_an_amendment_to_an_existing_adr_discharges_the_rule(repo):
    """The ADR index says superseded reasoning is marked, never deleted, so an
    amendment in place has to count."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    (root / rel).write_text(
        OLD_ADR.format(n="001") +
        "\n## Amendment\n\nthe reasoning changed because the measurement did\n",
        encoding="utf-8")
    _commit(root)
    assert _verdict(root, base, ["quality/adversarial/probes.yaml", rel],
                    _attested_body(["security"])) == []


def test_three_written_adrs_discharge_three_rules(repo):
    root, base = repo
    rels = [_write_adr(root, n, f"decision-{n}") for n in ("050", "051", "052")]
    _commit(root)
    assert _verdict(root, base, GUARDED + rels, _attested_body(ALL_THREE, rels)) == []


def test_one_written_adr_does_not_discharge_three_rules(repo):
    """The headline defect, which survived into its own fix twice. The second time
    it was `len(in_diff)` counting CITATIONS over a tuple that keeps duplicates, so
    pasting the same `ADR:` line three times discharged three rules."""
    root, base = repo
    rel = _write_adr(root, "050", "one-decision")
    _commit(root)
    problems = _verdict(root, base, GUARDED + [rel], _attested_body(ALL_THREE, [rel] * 3))
    assert problems and any("triggers 3 rule(s)" in p and "writes 1" in p for p in problems)


# --- the empty edits, one per git flag --------------------------------------------

@pytest.mark.parametrize("label,suffix", [
    ("a blank line", "\n"),
    ("one non-blank byte", "x\n"),
    ("a non-breaking space", "\u00a0\n"),
    ("a zero-width space", "\u200b\n"),
    ("a soft hyphen", "\u00ad\n"),
    ("an ideographic space", "\u3000\n"),
])
def test_an_empty_edit_to_an_old_adr_is_not_a_decision_record(repo, label, suffix):
    """`git`'s `-w` is ASCII-only, so five of these six clear `added > 0`; a seat
    found that after another seat had already found the blank line. The bar that
    refuses all six is SUBSTANCE, measured against the population rather than
    picked: across all 69 content-adding ADR edits in this repository's history the
    leanest carries 18 substantive words, and every string here carries none."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    with open(root / rel, "a", encoding="utf-8") as fh:
        fh.write(suffix)
    _commit(root)
    problems = _verdict(root, base, ["quality/adversarial/probes.yaml", rel],
                        _attested_body(["security"], [rel]))
    assert problems and any("writes 0" in p for p in problems), label


def test_a_whitespace_only_edit_to_an_existing_line_is_not_a_record(repo):
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    p = root / rel
    p.write_text(p.read_text(encoding="utf-8").replace("## Decision", "## Decision   "),
                 encoding="utf-8")
    _commit(root)
    problems = _verdict(root, base, ["quality/adversarial/probes.yaml", rel],
                        _attested_body(["security"], [rel]))
    assert problems and any("writes 0" in p for p in problems)


def test_three_touched_old_adrs_do_not_discharge_three_rules(repo):
    """One PR moving G1's model-invoke allowlist, the deployed guardrail policy and
    the adversarial corpus, discharged by ADRs about solo seats, a webhook pager
    and corpus sizes. The Files-changed tab read `3 files changed, 3 insertions`."""
    root, base = repo
    rels = ["docs/adr/ADR-001-solo-seats.md", "docs/adr/ADR-007-webhook-pager.md",
            "docs/adr/ADR-009-corpus-sizes.md"]
    for rel in rels:
        with open(root / rel, "a", encoding="utf-8") as fh:
            fh.write("\u00a0\n")
    _commit(root)
    problems = _verdict(root, base, GUARDED + rels, _attested_body(ALL_THREE, rels))
    # Every rule refuses on the count, and each touched ADR is named as the
    # near-miss it is. Both halves matter: the count alone tells a reader nothing
    # about which file failed to be a record.
    assert len([p for p in problems if "writes 0" in p]) == 3, problems
    for rel in rels:
        assert any(rel in p and "adds no reasoning" in p for p in problems), rel


def test_a_seventeen_byte_stub_is_not_a_decision_record(repo):
    """An earlier version accepted this and recorded it as a residual, arguing that
    no bar closes it because every structural bar is a shape to fill. True of
    structure; false of substance."""
    root, base = repo
    rel = _write_adr(root, "091", "stub", "# ADR-091\n## x\n")
    _commit(root)
    problems = _verdict(root, base, ["quality/adversarial/probes.yaml", rel],
                        _attested_body(["security"], [rel]))
    assert problems and any("adds no reasoning" in p for p in problems)


# --- the routes that are not about content ----------------------------------------

def test_a_content_free_rename_is_not_a_decision_record(repo):
    """A `git mv` produces a deletion AND an addition, so without rename detection
    it paid twice."""
    root, base = repo
    _git(root, "mv", "docs/adr/ADR-001-solo-seats.md",
         "docs/adr/ADR-001-solo-seats-and-review.md")
    _git(root, "commit", "-qm", "mv")
    changed = ["quality/adversarial/probes.yaml", "docs/adr/ADR-001-solo-seats.md",
               "docs/adr/ADR-001-solo-seats-and-review.md"]
    problems = _verdict(root, base, changed, _attested_body(["security"]))
    assert problems and any("writes 0" in p for p in problems)


def test_a_rename_with_a_real_rewrite_is_a_decision_record(repo):
    """The positive half. Without rename-target parsing the path stays in git's
    `{old => new}` form, matches no ADR pattern, and an honest rewrite is refused."""
    root, base = repo
    _git(root, "mv", "docs/adr/ADR-001-solo-seats.md",
         "docs/adr/ADR-001-solo-seats-and-review.md")
    new = root / "docs" / "adr" / "ADR-001-solo-seats-and-review.md"
    new.write_text(new.read_text(encoding="utf-8") +
                   "\n## Amendment\n\nthe reasoning changed because the measurement did\n",
                   encoding="utf-8")
    _commit(root)
    assert _verdict(root, base,
                    ["quality/adversarial/probes.yaml", "docs/adr/ADR-001-solo-seats.md",
                     "docs/adr/ADR-001-solo-seats-and-review.md"],
                    _attested_body(["security"])) == []


def test_deleting_an_unrelated_adr_mints_no_key(repo):
    """An earlier version read a missing file as a WITHDRAWAL without asking what
    had been withdrawn, so deleting a 2023 ADR bought a key. Its justification was
    a `revert` that turned out to be the commit which ADDED the ADR, and the test
    blessing it used an ADR number that has never existed in any commit."""
    root, base = repo
    _git(root, "rm", "-q", "docs/adr/ADR-007-webhook-pager.md")
    _git(root, "commit", "-qm", "rm")
    problems = _verdict(root, base,
                        ["quality/adversarial/probes.yaml", "docs/adr/ADR-007-webhook-pager.md"],
                        _attested_body(["security"], ["docs/adr/ADR-007-webhook-pager.md"]))
    assert problems and any("writes 0" in p for p in problems)


def test_a_typechange_that_deletes_a_record_is_not_a_record(repo):
    """`--diff-filter=AMR`. A typechange reports `1  9`: one line added, nine lines
    of a decision record deleted. An earlier version removed this filter as
    "redundant with `added > 0`" because deleting it left the suite green -- which
    measured test coverage, not necessity."""
    root, base = repo
    victim = root / "docs" / "adr" / "ADR-001-solo-seats.md"
    victim.unlink()
    try:
        victim.symlink_to("ADR-007-webhook-pager.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this filesystem")
    head = _commit(root)
    changed = ["quality/adversarial/probes.yaml", "docs/adr/ADR-001-solo-seats.md"]
    problems = _verdict(root, base, changed, _attested_body(["security"]), head=head)
    assert problems and any("writes 0" in p for p in problems)

    # ...and it is the FLAG that refuses it, not the substance bar downstream.
    # Asserting only the verdict left `--diff-filter=AMR` silent through two
    # audits: without it the typechange arrives as `1  9` -- one line added, nine
    # lines of a decision record deleted -- and the added line is the symlink's
    # target, a `.md` path that `substantive_words` strips to nothing. The
    # substance bar caught it and the flag went undefended. With the flag the row
    # never appears at all, so there is no near-miss to name.
    records, defects = twokey.adr_records(root, base, head, changed)
    assert records == []
    assert defects == [], "the typechange must be filtered by git, before the substance bar"


def test_one_adr_cannot_be_counted_three_times_through_rename_notation(repo):
    """`git diff --numstat` writes a rename as `dir/{old => new}`, and a FILENAME
    containing ` => ` parses the same way, so three junk files resolved to one
    untouched ADR and satisfied three rules. The dedup that stops it was removed
    once as unreachable."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    rows = [f"5\t0\tdocs/adr/{{{c} => ADR-001-solo-seats}}.md" for c in "abc"]
    resolved = []
    for row in rows:
        path = row.split("\t")[2]
        m = twokey.RENAME_RE.match(path)
        # groups: prefix, OLD middle, NEW middle, suffix -- the old middle was
        # added so the body diff can pair a rename; the record is still the new path
        resolved.append(m.group(1) + m.group(3) + m.group(4) if m else path)
    assert resolved == [rel] * 3, "three junk names must resolve to the one ADR"
    assert len(set(resolved)) == 1, "and the gate must count them once"


# --- the evidence and the file list must describe one PR ---------------------------

def test_an_adr_outside_the_changed_list_is_not_credited(repo):
    """`git diff <base>` with ONE revision compares base to the working tree, and
    on `pull_request` the working tree is `refs/pull/N/merge` -- so an ADR that
    landed on `main` after the base sha was credited to a PR containing none.
    Measured before this: ACCEPTED, with no ADR in the diff, none in the changed
    list and none on the Files-changed tab."""
    root, base = repo
    _write_adr(root, "051", "somebody-elses-decision")
    _commit(root, "somebody else's ADR lands on main")
    (root / "quality").mkdir(exist_ok=True)
    (root / "quality" / "probes.yaml").write_text("downgrade\n", encoding="utf-8")
    _commit(root, "corpus downgrade, no ADR")
    problems = _verdict(root, base, ["quality/adversarial/probes.yaml"],
                        _attested_body(["security"]))
    assert problems and any("writes 0" in p for p in problems)


def test_a_base_older_than_the_branch_point_mints_no_records(repo):
    """One commit of staleness minted three records before the changed-file list
    became part of the answer."""
    root, base0 = repo
    for n in ("052", "053", "054"):
        _write_adr(root, n, f"older-{n}")
    _commit(root, "three ADRs land")
    (root / "quality").mkdir(exist_ok=True)
    (root / "quality" / "probes.yaml").write_text("downgrade\n", encoding="utf-8")
    _commit(root, "downgrade with no ADR")
    problems = _verdict(root, base0, ["quality/adversarial/probes.yaml"],
                        _attested_body(["security"]))
    assert problems and any("writes 0" in p for p in problems)


def test_no_base_fails_closed(repo):
    root, _base = repo
    rel = _write_adr(root, "050", "a-real-decision")
    _commit(root)
    problems = _verdict(root, None, ["quality/adversarial/probes.yaml", rel],
                        _attested_body(["security"], [rel]))
    assert problems and any("no base commit" in p for p in problems)


# --- the citation stops discharging anything ---------------------------------------

def test_a_written_record_discharges_with_no_adr_line_at_all(repo):
    """The `ADR:` line stays in the body for a reader and the gate stops ruling on
    it. Requiring one CITATION per rule refuses 8 of the 18 merged PRs that owe an
    ADR, three of which `main` accepted -- PR #28 wrote three decision records and
    cited one."""
    root, base = repo
    rel = _write_adr(root, "050", "a-real-decision")
    _commit(root)
    assert _verdict(root, base, ["quality/adversarial/probes.yaml", rel],
                    _attested_body(["security"])) == []


def test_citing_a_tracked_file_discharges_nothing(repo):
    """A1: `ADR: LICENSE` cleared the adversarial corpus, and so did `ADR: ruff.toml`
    and `ADR: docs/adr/README.md`. All 374 tracked files satisfied `is_file()`."""
    root, base = repo
    (root / "LICENSE").write_text("a licence, at length, with many words in it\n",
                                  encoding="utf-8")
    _commit(root)
    for ref in ("LICENSE", "docs/adr/README.md", "ruff.toml"):
        problems = _verdict(root, base, ["quality/adversarial/probes.yaml", "LICENSE"],
                            _attested_body(["security"], [ref]))
        assert problems and any("writes 0" in p for p in problems), ref


def test_citing_an_adr_does_not_block_a_rule_that_needs_none(repo):
    """A false refusal an earlier version invented: citing `docs/adr/README.md` for
    context blocked a `quality/judge/` PR, which owes no ADR at all."""
    root, base = repo
    assert _verdict(root, base, ["quality/judge/rubric.yaml"],
                    _attested_body(["ai-quality"], ["docs/adr/README.md"])) == []


def test_editing_the_adr_index_is_neither_a_record_nor_a_defect(repo):
    root, base = repo
    index = root / "docs" / "adr" / "README.md"
    index.write_text(index.read_text(encoding="utf-8") + "| ADR-050 | a row |\n",
                     encoding="utf-8")
    rel = _write_adr(root, "050", "a-real-decision")
    _commit(root)
    assert _verdict(root, base,
                    ["quality/adversarial/probes.yaml", "docs/adr/README.md", rel],
                    _attested_body(["security"], [rel])) == []


# --- what an ADR is, structurally ---------------------------------------------------

def test_a_malformed_new_adr_is_named_not_just_counted(repo):
    """`adr_defect` is consulted for every candidate, and an earlier version put
    its message behind an early return -- so a malformed new ADR was told
    "writes 0" and never why."""
    root, base = repo
    rel = _write_adr(root, "050", "number-disagrees", NEW_ADR.format(n="097"))
    _commit(root)
    problems = _verdict(root, base, ["quality/adversarial/probes.yaml", rel],
                        _attested_body(["security"], [rel]))
    assert problems and any("matching `# ADR-050` title" in p for p in problems)


def test_a_near_miss_is_reported_once_not_once_per_rule(repo):
    """Two ADR-requiring rules printed the identical near-miss twice."""
    root, base = repo
    rel = _write_adr(root, "050", "number-disagrees", NEW_ADR.format(n="097"))
    _commit(root)
    problems = _verdict(root, base, GUARDED + [rel], _attested_body(ALL_THREE, [rel]))
    titles = [p for p in problems if "matching `# ADR-050` title" in p]
    assert len(titles) == 1, titles


def test_only_an_adr_shaped_path_is_an_adr(tmp_path):
    for ref in ("LICENSE", "README.md", "docs/adr/README.md", "ruff.toml",
                "docs/adr/ADR-13-short.md", "docs/adr/ADR-013.md"):
        assert "is not an ADR" in (twokey.adr_defect(ref, tmp_path) or ""), ref


def test_an_adr_needs_sections_not_just_a_title(tmp_path):
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    rel = "docs/adr/ADR-091-titled-only.md"
    (tmp_path / rel).write_text("# ADR-091\n", encoding="utf-8")
    assert "title and no sections" in (twokey.adr_defect(rel, tmp_path) or "")
    (tmp_path / rel).write_text(NEW_ADR.format(n="091"), encoding="utf-8")
    assert twokey.adr_defect(rel, tmp_path) is None


def test_a_bare_hash_hash_is_not_a_section(tmp_path):
    """`\\s` matches a newline, so a bare `##` on its own line with prose two lines
    below satisfied `^##+\\s+\\S`. Found by WEAKENING the regex, not deleting it."""
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    rel = "docs/adr/ADR-092-bare-marker.md"
    (tmp_path / rel).write_text("# ADR-092\n\n##\n\nprose\n", encoding="utf-8")
    assert "title and no sections" in (twokey.adr_defect(rel, tmp_path) or "")


def test_an_adrs_title_must_carry_its_own_number(tmp_path):
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    rel = "docs/adr/ADR-096-number-disagrees.md"
    (tmp_path / rel).write_text(NEW_ADR.format(n="097"), encoding="utf-8")
    assert "matching `# ADR-096` title" in (twokey.adr_defect(rel, tmp_path) or "")
    (tmp_path / rel).write_text(NEW_ADR.format(n="096"), encoding="utf-8")
    assert twokey.adr_defect(rel, tmp_path) is None


def test_a_byte_order_mark_does_not_hide_an_adr_title(tmp_path):
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    rel = "docs/adr/ADR-093-with-a-bom.md"
    (tmp_path / rel).write_bytes(b"\xef\xbb\xbf" + NEW_ADR.format(n="093").encode())
    assert twokey.adr_defect(rel, tmp_path) is None


def test_an_adr_at_a_valid_path_must_exist(tmp_path):
    assert "does not exist" in (twokey.adr_defect("docs/adr/ADR-999-imaginary.md", tmp_path) or "")


def test_the_render_names_the_records_it_accepted(repo):
    """The residual an earlier version stated -- "judging a record's quality belongs
    to the reviewing seat" -- had no channel: `render` took only `(changed,
    problems)`, so the seat was told what the gate accepted ONLY when it refused."""
    root, base = repo
    rel = _write_adr(root, "050", "a-real-decision")
    _commit(root)
    records, _ = twokey.adr_records(root, base, None,
                                    ["quality/adversarial/probes.yaml", rel])
    out = twokey.render(["quality/adversarial/probes.yaml", rel], [], records)
    assert "SATISFIED" in out and rel in out


def test_the_workflow_passes_both_endpoints():
    """`--base` alone compares base to the working tree. Both flags, or the
    evidence and the changed-file list stop describing the same PR."""
    wf = (ROOT / ".github" / "workflows" / "two-key.yml").read_text(encoding="utf-8")
    assert "--base \"$BASE_SHA\"" in wf
    assert "--head \"$HEAD_SHA\"" in wf

# --- the nine the audit found silent -----------------------------------------------
#
# The substance bar SUBSUMES the git flags for outcome: a whitespace touch has no
# substantive words either way, so dropping `-w` changed no verdict and the suite
# stayed green. An earlier round read exactly that silence as proof a check was
# redundant, deleted two of them, and both turned out load-bearing.
#
# The two layers do leave different traces, and that is what makes each one
# observable. A route git's flags filter never reaches the substance bar, so it
# produces NO defect message; a route that reaches the bar is NAMED as a
# near-miss. Asserting on which layer refused pins the flag rather than the
# outcome.

GIT_FILTERED = "filtered by git before the substance bar is consulted"


def _records(root, base, head, changed):
    return twokey.adr_records(root, base, head, changed)


def test_a_blank_line_is_filtered_by_git_not_by_the_substance_bar(repo):
    """`--ignore-blank-lines`. If this flag goes, the edit reaches the substance
    bar and is refused there instead -- same verdict, different layer, and the
    flag stops being defended."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    with open(root / rel, "a", encoding="utf-8") as fh:
        fh.write("\n")
    head = _commit(root)
    records, defects = _records(root, base, head, ["quality/adversarial/probes.yaml", rel])
    assert records == []
    assert defects == [], GIT_FILTERED


def test_a_whitespace_only_edit_is_filtered_by_git_not_by_the_substance_bar(repo):
    """`-w`, the same way."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    p = root / rel
    p.write_text(p.read_text(encoding="utf-8").replace("## Decision", "## Decision   "),
                 encoding="utf-8")
    head = _commit(root)
    records, defects = _records(root, base, head, ["quality/adversarial/probes.yaml", rel])
    assert records == []
    assert defects == [], GIT_FILTERED


def test_a_deletion_is_filtered_by_git_not_by_the_substance_bar(repo):
    """`--diff-filter=AMR`. Without it a deletion arrives with `added=0` and is
    filtered one line later, so the verdict is identical and the filter is
    undefended -- unless the LAYER is asserted, which is what this does."""
    root, base = repo
    _git(root, "rm", "-q", "docs/adr/ADR-007-webhook-pager.md")
    head = _commit(root, "rm")
    records, defects = _records(
        root, base, head,
        ["quality/adversarial/probes.yaml", "docs/adr/ADR-007-webhook-pager.md"])
    assert records == []
    assert defects == [], GIT_FILTERED


def test_a_binary_file_at_an_adr_path_is_filtered_before_the_substance_bar(repo):
    """`git diff --numstat` writes `-` for a binary file, which is not a number
    and must not be read as one."""
    root, base = repo
    rel = "docs/adr/ADR-094-binary.md"
    (root / rel).write_bytes(bytes(range(256)) * 8)
    head = _commit(root)
    records, defects = _records(root, base, head, ["quality/adversarial/probes.yaml", rel])
    assert records == []
    assert defects == [], GIT_FILTERED


# --- the substance bar is the CALIBRATED one, not any positive number --------------

def test_the_substance_bar_is_the_calibrated_one(repo):
    """Every other test here plants text worth ZERO substantive words, so a bar of
    1 would refuse them all and the calibrated value went undefended.

    The value is `MIN_SUBSTANTIVE_WORDS`, shared with the rationale bar and
    measured against the population rather than picked: across all 69
    content-adding ADR edits in this repository's history the leanest carries 18,
    so a bar of 6 refuses none of them and leaves a 3x margin."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"

    thin = "\nthe reasoning changed slightly today\n"           # 5 substantive words
    assert len(twokey.substantive_words(thin)) < twokey.MIN_SUBSTANTIVE_WORDS
    with open(root / rel, "a", encoding="utf-8") as fh:
        fh.write(thin)
    head = _commit(root)
    records, defects = _records(root, base, head, ["quality/adversarial/probes.yaml", rel])
    assert records == [] and defects, "a thin edit must be NAMED, not silently dropped"
    assert "adds no reasoning" in defects[0]


def test_a_real_amendment_clears_the_substance_bar_without_trying(repo):
    """The positive control. A bar nothing honest clears is a bar that will be
    removed by whoever hits it first."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    with open(root / rel, "a", encoding="utf-8") as fh:
        fh.write("\n## Amendment\n\nthe corpus rule now names the seat that owns "
                 "the control rather than the seat that measures it\n")
    head = _commit(root)
    records, defects = _records(root, base, head, ["quality/adversarial/probes.yaml", rel])
    assert records == [rel] and defects == []


# --- one ADR cannot be counted twice ------------------------------------------------

def test_one_adr_named_three_ways_is_one_record(monkeypatch, repo):
    """`git diff --numstat` writes a rename as `dir/{old => new}`, and a FILENAME
    containing ` => ` parses the same way -- so three files resolved to ONE
    untouched ADR and satisfied three rules. The dedup that stops it was deleted
    once as unreachable.

    Driven through a stubbed `git` because `>` is not legal in a Windows filename,
    and the gate runs on `ubuntu-latest` where it is."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    rows = "\n".join(f"9\t0\tdocs/adr/{{{c} => ADR-001-solo-seats}}.md" for c in "abc")

    real_git = twokey._git

    written = ("+the corpus rule now names the seat that owns the control\n"
               "+rather than the seat that measures it\n")

    def fake_git(repo_root, *args):
        if "--numstat" in args:
            return rows + "\n"
        if "-U0" in args:
            # Real reasoning, so the DEDUP is what decides here and not the
            # substance bar. Otherwise this passes for the wrong reason.
            return written
        return real_git(repo_root, *args)

    monkeypatch.setattr(twokey, "_git", fake_git)
    records, _ = _records(root, base, None, ["quality/adversarial/probes.yaml", rel])
    assert records == [rel], f"three names for one ADR produced {records}"


# --- the endpoints ------------------------------------------------------------------

def test_the_head_endpoint_excludes_what_is_not_committed_to_it(repo):
    """`git diff <base>` with ONE revision compares base to the WORKING TREE. On
    `pull_request` the working tree is `refs/pull/N/merge`, which carries whatever
    landed on `main` after the base sha -- so another PR's ADR was credited to a PR
    containing none. Here the uncommitted file stands in for that content."""
    root, base = repo
    committed = _write_adr(root, "050", "a-real-decision")
    head = _commit(root)
    # ...and something the PR head does NOT contain. STAGED, not committed: an
    # untracked file appears in no `git diff` at all, so leaving it untracked
    # would make the control assertion below pass for the wrong reason.
    _write_adr(root, "051", "not-in-this-pr")
    _git(root, "add", "-A")

    changed = ["quality/adversarial/probes.yaml", committed,
               "docs/adr/ADR-051-not-in-this-pr.md"]
    with_head, _ = _records(root, base, head, changed)
    without_head, _ = _records(root, base, None, changed)
    assert with_head == [committed]
    assert "docs/adr/ADR-051-not-in-this-pr.md" in without_head, (
        "the working-tree file must be visible without --head, or this test proves nothing"
    )


def test_a_dot_slash_prefixed_path_still_matches_its_rule():
    """`normalize_paths` strips `./`. It is NOT `lstrip("./")`, which eats the
    leading dot of `.github/...` -- but nothing planted the `./` case itself."""
    # Compared against the SAME path unprefixed rather than against a copied seat
    # list, which was a hardcoded `["ai-quality", "platform-eng"]` that ADR-052
    # turned red for a SEAT change -- a normalization test failing on a seat set is
    # asserting something it does not own.
    #
    # **Non-emptiness first, and that is the whole of it.** The Platform
    # Engineering seat defeated the equality alone: `lstrip("./")` mangles BOTH
    # sides to `github/workflows/...`, both reach no rule, and `[] == []` passed
    # while the exact defect the comment names was live. An equality between two
    # calls to the code under test cannot fail when the code fails symmetrically.
    for path in ("pave/twokey.py", ".github/workflows/two-key.yml"):
        hits = twokey.triggered(["./" + path])
        assert hits, (
            f"`./{path}` reached NO rule. `lstrip('./')` eats the leading dot of "
            "`.github/...`, which is the case that distinguishes it from a prefix strip"
        )
        assert hits == twokey.triggered([path]), f"`./{path}` and `{path}` differ"


def test_a_deletion_always_reports_zero_lines_added(repo):
    """The PREMISE that makes `D` redundant inside `--diff-filter=AMR`, pinned so
    the redundancy cannot rot.

    `AMR -> AMRD` is the one mutation in this module's audit that stays silent and
    is not a missing test: adding `D` back cannot change an outcome, because a
    deletion reports `0` added and is filtered one line later by `added in ("0",
    "-")`. That is git's behaviour, not an inference about it -- so it is asserted
    here rather than believed. `T` is a different matter and has its own test: a
    typechange reports `1  9` and the filter is the only thing that stops it.

    Twice in this milestone a check was deleted because removing it left the suite
    green, and both were load-bearing. The difference between that and this is a
    proof: there, the reasoning was "no test noticed"; here, it is "a deletion
    cannot report added > 0", and the line below is what makes that checkable."""
    root, base = repo
    _git(root, "rm", "-q", "docs/adr/ADR-007-webhook-pager.md")
    head = _commit(root, "rm")
    rows = _git(root, "diff", "-w", "--ignore-blank-lines", "--numstat",
                "--diff-filter=AMRD", "--find-renames", base, head, "--", "docs/adr/")
    entries = [ln.split("\t") for ln in rows.splitlines() if ln.count("\t") == 2]
    assert entries, "the deletion must appear at all once D is in the filter"
    for added, _deleted, path in entries:
        assert added == "0", f"{path} reports {added} added lines on a deletion"


def test_a_stale_citation_does_not_refuse_a_pr_that_wrote_a_record(repo):
    """The `ADR:` line is documentation for a reader; the gate rules on the DIFF.

    An `is_file()` check on the cited path survived the rewrite that moved the
    discharge from the body to the diff, because that replaced the top of
    `evaluate` and not its tail. It was live: a PR whose diff wrote a real
    decision record was refused because a stale path appeared elsewhere in its
    body. Nothing here caught it -- a rebase did, when the leftover showed up in a
    merged file."""
    root, base = repo
    rel = _write_adr(root, "050", "a-real-decision")
    head = _commit(root)
    changed = ["quality/adversarial/probes.yaml", rel]

    honest = _attested_body(["security"], [rel])
    assert _verdict(root, base, changed, honest, head=head) == []

    stale = _attested_body(["security"], ["docs/adr/ADR-999-a-stale-citation.md"])
    assert _verdict(root, base, changed, stale, head=head) == [], (
        "a citation the gate does not rule on must not be able to refuse a PR "
        "whose diff wrote the record"
    )


def test_repetition_does_not_clear_the_substance_bar(repo):
    """The bar counts DISTINCT substantive words, because the flat count is the
    rationale bar's and its known weakness came with it.

    Four seats refused an earlier rationale bar partly because it was "cleared by
    nonsense" -- thirty two-letter tokens, and the gate's own BLOCKED message
    pasted back. Reusing `substantive_words` for ADRs imported that: six
    repetitions of one word cleared a flat six. Measured across the same 69
    content-adding ADR edits, the leanest carries 17 DISTINCT substantive words,
    so distinctness costs nothing honest and collapses repetition to one."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    with open(root / rel, "a", encoding="utf-8") as fh:
        fh.write("\nbanana banana banana banana banana banana\n")
    head = _commit(root)
    records, defects = twokey.adr_records(
        root, base, head, ["quality/adversarial/probes.yaml", rel])
    assert records == []
    assert defects and "adds no reasoning" in defects[0]


def test_the_substance_bar_does_not_claim_to_measure_meaning(repo):
    """A RECORDED RESIDUAL. Six distinct words of `lorem ipsum` clear the bar, and
    so does this module's BLOCKED message pasted back. No word count separates
    prose from meaningless prose; the bar refuses EMPTY and REPETITIVE edits, not
    meaningless ones.

    Asserted rather than left implied, because the version of this PR that said it
    measured "reasoning" was overclaiming, and because `render` naming the accepted
    records is what makes the remaining judgement the reviewing seat's to make."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    with open(root / rel, "a", encoding="utf-8") as fh:
        fh.write("\nlorem ipsum dolor sit amet consectetur\n")
    head = _commit(root)
    records, _ = twokey.adr_records(
        root, base, head, ["quality/adversarial/probes.yaml", rel])
    assert records == [rel], "the residual is that this PASSES; if it stops, re-state it"


def test_a_rename_plus_one_character_is_not_a_decision_record(repo):
    """Security's finding, and the reason the body diff carries BOTH paths.

    `--numstat` is given the whole directory, so git pairs a rename and reports
    the truth: `1  0`. The per-file body diff was scoped to the NEW path alone,
    where git cannot see the deletion of the old one and reads the file as brand
    new -- so every line of a 2023 ADR counted as written by this diff. Measured
    before the fix: a slug typo-fix plus the character `x` scored 47 added lines
    and 10 distinct substantive words, discharged the corpus rule, and made
    `render` print a decision record that does not exist.

    The sibling test `test_a_rename_with_a_real_rewrite_is_a_decision_record`
    could not catch it: replacing its amendment payload with `x` left it green.
    Its name asserted a distinction the code did not make."""
    root, base = repo
    _git(root, "mv", "docs/adr/ADR-001-solo-seats.md", "docs/adr/ADR-001-solo-seat.md")
    with open(root / "docs" / "adr" / "ADR-001-solo-seat.md", "a", encoding="utf-8") as fh:
        fh.write("x\n")
    head = _commit(root, "slug typo + one character")
    changed = ["quality/adversarial/probes.yaml", "docs/adr/ADR-001-solo-seats.md",
               "docs/adr/ADR-001-solo-seat.md"]
    records, defects = twokey.adr_records(root, base, head, changed)
    assert records == [], f"a rename plus one character wrote {records}"
    assert defects and "adds no reasoning" in defects[0]


def test_an_adr_near_miss_does_not_refuse_a_rule_that_owes_no_adr(repo):
    """Platform Engineering's finding. `adr_records` runs on every gated PR, and
    the near-miss report sat OUTSIDE the `requires_adr` guard -- a rewrite moved it
    out of the rule loop to dedupe it and left the guard behind.

    Measured: an honest one-line copy-edit to an existing ADR, bundled with an
    `evals/comparators.json` change that owes no ADR at all, came back BLOCKED
    citing a rule that was never invoked."""
    root, base = repo
    rel = "docs/adr/ADR-001-solo-seats.md"
    with open(root / rel, "a", encoding="utf-8") as fh:
        fh.write("\nTypo fixed.\n")
    head = _commit(root, "copy-edit")
    changed = [rel, "evals/comparators.json"]
    assert not any(r.requires_adr for r, _ in twokey.triggered(changed)), "premise"

    body = ("Two-Key-Disposition: ai-quality\nTwo-Key-Disposition: platform-eng\n"
            "Two-Key-Disposition: security\n"
            f"Two-Key-Rationale: {GOOD_RATIONALE}\n")
    assert _verdict(root, base, changed, body, head=head) == [], (
        "a near-miss reported for a rule that was never invoked"
    )


def test_the_repos_own_supersession_convention_is_not_refused(repo):
    """`docs/adr/README.md`: *"Superseded ADRs are marked, never deleted."* So the
    shape this repository asks for is a NEW record plus a mark on the old one --
    and the mark is terse by convention: `**Status:** Accepted — superseded by
    ADR-NNN.` scores 3 distinct substantive words.

    Measured before the fix: the new record was found and counted, the rule was
    satisfied, and the near-miss on the supersession mark blocked the PR anyway. A
    near-miss EXPLAINS a refusal; it must not cause one."""
    root, base = repo
    new = _write_adr(root, "052", "a-real-decision")
    old = "docs/adr/ADR-001-solo-seats.md"
    p = root / old
    p.write_text(p.read_text(encoding="utf-8").rstrip("\n")
                 + "\n\n**Status:** superseded by ADR-052.\n", encoding="utf-8")
    head = _commit(root, "new record + supersession mark")

    changed = ["quality/adversarial/probes.yaml", new, old]
    records, defects = twokey.adr_records(root, base, head, changed)
    assert records == [new], records
    assert defects, "the mark is still correctly NOT counted as a record"
    assert _verdict(root, base, changed, _attested_body(["security"]), head=head) == []


def test_a_near_miss_is_still_named_when_the_count_is_short(repo):
    """The other half. When a PR owes a record and has none, the author must be
    told WHICH candidate failed and why -- otherwise the refusal says only
    `writes 0` and the author guesses."""
    root, base = repo
    old = "docs/adr/ADR-001-solo-seats.md"
    with open(root / old, "a", encoding="utf-8") as fh:
        fh.write("\n**Status:** superseded by ADR-052.\n")
    head = _commit(root, "mark only, no record written")
    problems = _verdict(root, base, ["quality/adversarial/probes.yaml", old],
                        _attested_body(["security"]), head=head)
    assert any("writes 0" in p for p in problems)
    assert any("adds no reasoning" in p and old in p for p in problems)


# --- the replay that carries Decision 3, committed ---------------------------------

REPLAY = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "adr_bar_replay.json").read_text(encoding="utf-8")
)


def test_the_replay_behind_the_citation_cut_is_in_the_tree():
    """A seat pointed out that the CRLF corpus was committed *"so the measurement
    and the gate see the same thing"*, while the replay carrying the decision to
    stop the `ADR:` line discharging anything lived only in a session. Two
    evidentiary standards in one file.

    This is the second one, brought up to the first. It records, per merged PR that
    triggers a rule requiring an ADR, what each gate would decide."""
    rows = REPLAY["rows"]
    assert REPLAY["merged_prs_fetched"] >= 57
    assert len(rows) >= 18, "the population that owes an ADR"

    regressions = [r["pr"] for r in rows if r["main_accepts"] and not r["new_accepts"]]
    improvements = [r["pr"] for r in rows if not r["main_accepts"] and r["new_accepts"]]
    assert regressions == [40], (
        f"the measured price of this change is PR #40 alone; now {regressions}"
    )
    assert 24 in improvements, "PR #24 wrote a record main could not see"

    # ...and #40 is refused for the stated reason: it wrote no record at all.
    forty = next(r for r in rows if r["pr"] == 40)
    assert forty["records_written"] == 0, forty
# --- the instance of the gate that CI actually runs (ADR-052) ------------------

def _run_two_key(monkeypatch, tmp_path, root, body, changed, base, head):
    """`python -m pave.twokeycli`, against a scratch repo — the exact entrypoint
    `.github/workflows/two-key.yml` invokes.

    Through the entrypoint and not `evaluate` directly, deliberately: the module
    computes both endpoints, and every assertion in this file until now stopped at
    the `twokey` boundary. It was `cli.main(["gate", "two-key", ...])` until ADR-052
    moved the gate out of `pave/cli.py`; going through the CLI now would test a path
    CI does not take. Returns (exit_code, output)."""
    from pave import twokeycli
    monkeypatch.setattr(twokeycli, "ROOT", root)
    bf = tmp_path / "body.md"
    bf.write_text(body, encoding="utf-8")
    argv = ["--body-file", str(bf), "--base", base]
    if head is not None:
        argv += ["--head", head]
    argv += ["--changed", *changed]
    try:
        twokeycli.main(argv)
    except SystemExit as exc:
        return int(exc.code or 0), ""
    return 0, ""


def test_the_cli_hands_the_gate_the_head_endpoint(repo, tmp_path, monkeypatch, capsys):
    """**Measured silent at 2214 passed, zero keys.** `head_sha = None` in
    `pave/cli.py` re-enables the one-revision comparison, where `git diff <base>`
    reads the WORKING TREE -- the exact defect ADR-051 added `--head` to close,
    four lines below the refusal written for its twin.

    Nothing tested it. `test_the_head_endpoint_excludes_what_is_not_committed_to_it`
    proves `adr_records` honours the endpoint it is handed; this proves the CLI
    hands it one. Two assertions, because "the module is right" and "the caller
    calls it right" are different claims and the second was unmade."""
    root, base = repo
    head = _commit(root, "no adr in this pr")
    # In the working tree and staged, NOT in `head` -- another PR's ADR, which is
    # the shape ADR-051 measured. Staged rather than untracked: an untracked file
    # appears in no `git diff` at all and the control would pass for that reason.
    rel = _write_adr(root, "051", "another-prs-decision")
    _git(root, "add", "-A")

    changed = ["quality/adversarial/probes.yaml", rel]
    body = _attested_body(seats=("security",))
    code, _ = _run_two_key(monkeypatch, tmp_path, root, body, changed, base, head)
    out = capsys.readouterr().out
    assert code != 0, (
        "the CLI accepted a PR whose head writes no decision record, crediting one "
        "the working tree happens to carry"
    )
    assert "adds no reasoning" in out or "record" in out, out

    # Control: without `--head` the same tree IS credited, or the assertion above
    # passes for a reason unrelated to the endpoint.
    code2, _ = _run_two_key(monkeypatch, tmp_path, root, body, changed, base, None)
    assert code2 == 0, (
        "the one-revision comparison did not credit the working-tree ADR, so the "
        "test above proves nothing about the endpoint"
    )


def test_the_cli_does_not_filter_what_the_gate_refused(repo, tmp_path, monkeypatch, capsys):
    """**Measured silent at 2214 passed, zero keys**: dropping every problem whose
    text mentions an ADR, between `evaluate` and the exit code, in the file CI
    runs. `evaluate` refuses correctly and the caller discards the refusal.

    **The output assertion names the record count, not the word "ADR".** The first
    draft accepted `"decision record" in out.lower() or "adr" in out.lower()`, which
    the Platform Engineering seat satisfied with the RULE'S OWN NAME -- `render`
    prints "only Security may downgrade a probe, and only with an ADR" on every
    block of that rule, so the assertion could not fail. Swapping the body for `""`
    blocked on a missing disposition and passed too. `and writes 0 (none)` is
    emitted only by the short-record branch.

    The control below is what makes the refusal attributable: the identical call
    with a decision record in the head must pass, or this test proves only that
    something blocked."""
    root, base = repo
    head = _commit(root, "touches security's corpus and writes no record")
    changed = ["quality/adversarial/probes.yaml"]
    body = _attested_body(seats=("security",))
    code, _ = _run_two_key(monkeypatch, tmp_path, root, body, changed, base, head)
    out = capsys.readouterr().out
    assert code != 0, "a rule requiring an ADR was discharged by a diff writing none"
    assert "BLOCKED" in out, out
    assert "and writes 0 (none)" in out, (
        f"the exit code refused and the output does not say the missing record is why: {out}"
    )

    # Control: the same rule, the same body, a diff that DOES write a record.
    rel = _write_adr(root, "053", "a-real-decision")
    head2 = _commit(root, "and now it writes one")
    code2, _ = _run_two_key(monkeypatch, tmp_path, root, body,
                            [*changed, rel], base, head2)
    out2 = capsys.readouterr().out
    assert code2 == 0, (
        f"a diff writing a real decision record was still refused, so the refusal "
        f"above is not attributable to the missing record: {out2}"
    )
