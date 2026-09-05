"""
G9 — whoever feels a control's pain never solely controls its strength.

The two-key rule was designed to be enforced by CODEOWNERS: a threshold change
requires the owning seat *plus* AI Quality. That works when two humans exist.
GitHub does not let a pull request's author approve their own PR, so with one
operator the second key is not merely inconvenient — it is unobtainable, and the
rule silently degrades into a comment in `ROLES.md`.

So the second key is machine-checked instead. A PR touching a two-key path must
record the owning seat's disposition and its reasoning in the PR body:

    Two-Key-Disposition: ai-quality
    Two-Key-Rationale: raising the groundedness floor to 0.8 now that M03's
      calibration run published an agreement number that supports it

This is weaker than two humans and stronger than a convention. It cannot be
satisfied by clicking; it produces a written reason attached to the diff forever;
and because the check is required and unbypassable, it cannot be skipped quietly.
The failure mode it is built against is the one `ROLES.md` names: "update the
baseline" as the standard way eval gates get neutered.

AT SCALE: delete this check, put the seats back in CODEOWNERS, and require code
owner review. The path list here and the path list there are the same list — the
interface already matches.

Owning seat: AI Quality (the rules) · Platform Engineering (the mechanism).
"""
from __future__ import annotations

import pathlib
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass

#: A rationale is measured by SUBSTANCE, not by length.
#:
#: It used to be `len(rationale) < 24`, and the failure message published that
#: number. Measured: `"see commit abc123"` was rejected at 17 characters and
#: `"see commit abc123def4567890"` sailed through at 27 — the identical
#: non-rationale, padded. A gate that states its own numeric bar in the refusal
#: is not enforcing a standard, it is issuing instructions for clearing one, and
#: the thing it was defending (G9: the written reasoning attached to the diff) is
#: exactly what padding removes.
#:
#: So the check counts words that carry meaning after references and connective
#: tissue are removed. A pointer collapses to nothing under that count no matter
#: how long it is, and a genuine rationale clears it without trying: measured
#: across this repo's committed rationales and a corpus of pointer forms, the two
#: populations sit at 9–11 and 0–1 with nothing in between.
MIN_SUBSTANTIVE_WORDS = 6

#: Words that a rationale can be built entirely out of while saying nothing:
#: deictic lead-ins ("see", "per", "refer"), the nouns of pointing ("commit",
#: "reference", "details"), and ordinary English glue.
RATIONALE_FILLER = frozenset({
    "a", "above", "an", "and", "as", "at", "be", "below", "by", "cf", "commit",
    "commits", "context", "detail", "details", "discussed", "for", "from", "in",
    "is", "it", "its", "of", "on", "or", "per", "pr", "previous", "ref",
    "refer", "reference", "see", "submitted", "that", "the", "their", "there",
    "these", "this", "to", "up", "was", "were", "what", "when", "where",
    "which", "why", "with"
})

PLACEHOLDER_RATIONALES = {"n/a", "na", "none", "-", "--", "tbd", "see above", "as discussed"}

DISPOSITION_RE = re.compile(r"^Two-Key-Disposition:[ \t]*(?P<seat>[a-z-]+)[ \t]*$", re.MULTILINE)
RATIONALE_RE = re.compile(r"^Two-Key-Rationale:[ \t]*(?P<text>.+?)(?=^\s*[A-Z][A-Za-z-]*:|\Z)", re.MULTILINE | re.DOTALL)
ADR_RE = re.compile(r"^ADR:[ \t]*(?P<ref>\S+)[ \t]*$", re.MULTILINE)


def substantive_words(rationale: str) -> list[str]:
    """The words in a rationale that carry its reasoning.

    References are stripped first — a SHA, a URL, an issue number, an ADR id, a
    file path — because pointing at one is the move being refused, and a rule
    that counted them would be satisfied by pointing harder.
    """
    text = re.sub(r"\b[0-9a-f]{7,40}\b", " ", rationale, flags=re.IGNORECASE)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"#\d+", " ", text)
    text = re.sub(r"\bADR-\d+\S*", " ", text)
    text = re.sub(r"\b\S+\.(?:md|py|json|ya?ml|ts|yml)\b", " ", text)
    words = re.findall(r"[A-Za-z][A-Za-z_-]+", text.lower())
    return [w for w in words if w not in RATIONALE_FILLER]


#: What an `ADR:` line is allowed to point at, and what a decision record is.
#:
#: Until M06 the ADR half was `ADR_RE.search(body)` plus `is_file()`, and **every
#: tracked file satisfied it** -- 374 when that was first measured, 379 on this
#: tree, and the count is beside the point: `ADR: LICENSE` discharged the adversarial
#: corpus, and so did `ADR: README.md` and `ADR: ruff.toml`. Three rules promise
#: "the owning seat, plus an ADR" and CLAUDE.md names the corpus as the model for
#: that promise, so the promise was the whole of the protection.
ADR_PATH_RE = re.compile(r"^docs/adr/ADR-(\d{3})-[a-z0-9-]+\.md$")
ADR_TITLE_RE = re.compile(r"^#\s+ADR-(\d{3})\b")
#: `[ \t]`, not `\s`: `\s` matches a newline, so a bare `##` on its own line with
#: prose two lines below satisfied `^##+\s+\S`. Found by WEAKENING the regex
#: rather than deleting it, which is the class of mutation an earlier audit here
#: did not run.
ADR_SECTION_RE = re.compile(r"^##+[ \t]+\S", re.MULTILINE)
#: `git diff` reports a rename as `dir/{old.md => new.md}`; the record is the new
#: path.
RENAME_RE = re.compile(r"^(.*)\{([^}]*?) => ([^}]*)\}(.*)$")


def adr_defect(ref: str, repo_root: pathlib.Path | None) -> str | None:
    """Why `ref` is not an ADR, or None if it is one.

    Structural, never a size. A size bar is the `24+ characters` mistake one field
    over: it publishes the number to pad to.

    Measured ON THIS TREE, which is the one that ships and includes this PR's own
    ADR: all **46** committed ADRs match this filename pattern AND open with a
    matching `# ADR-NNN` title; `docs/adr/README.md`, the only other file in that
    directory, matches neither. All 46 carry at least three `##` headings, so
    requiring one leaves every real ADR a 3x margin. A required-sections list was
    refused by measurement -- the most common heading, `## Consequences`, appears
    in **39 of 46**, so any list would turn away seven real ADRs.

    The tree is named because these numbers were stale: they said 45, and 38 of
    45, measured before this PR added the 46th. A seat re-measured them.
    """
    shaped = ADR_PATH_RE.match(ref)
    if not shaped:
        return (f"`{ref}` is not an ADR. An ADR is `docs/adr/ADR-NNN-<slug>.md`; "
                f"every tracked file used to satisfy this, which made 'plus an ADR' "
                f"a promise rather than a requirement.")
    if repo_root is None:
        return None
    path = repo_root / ref
    if not path.is_file():
        return f"`{ref}` does not exist in this tree."
    # `utf-8-sig`: a BOM survives `str.strip()` and would hide the title. `cli.py`
    # reads the PR body that way already, one function over.
    text = path.read_text(encoding="utf-8-sig")
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    titled = ADR_TITLE_RE.match(first)
    if not titled or titled.group(1) != shaped.group(1):
        return (f"`{ref}` does not open with a matching `# ADR-{shaped.group(1)}` "
                f"title. An empty file at an ADR path is not an ADR.")
    if not ADR_SECTION_RE.search(text):
        return (f"`{ref}` has a title and no sections. An ADR records a decision; "
                f"every ADR in this tree has at least three `##` headings.")
    return None


def _git(repo_root: pathlib.Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=str(repo_root), capture_output=True,
                              text=True, check=False, encoding="utf-8",
                              errors="replace").stdout
    except OSError:  # pragma: no cover - git absent is a broken checkout
        return ""


def adr_records(repo_root: pathlib.Path | None, base: str | None, head: str | None = None,
                changed: Sequence[str] | None = None) -> tuple[list[str], list[str]]:
    """The decision records THIS diff writes, and the near-misses worth naming.

    Three earlier versions asked the PR BODY -- does an `ADR:` line name a tracked
    file, is the cited path in the diff, are there N of them -- and seats defeated
    every one, twice with the SAME defect in a new shape. This asks the diff, and
    each clause below is a route somebody planted and ran:

      - `-w --ignore-blank-lines` -- `printf '\n' >> ADR-001-solo-seats.md`, a 2023
        ADR about role subagents, discharged a rule at 45 keystrokes; three of them
        discharged three, in one PR moving G1's allowlist, the deployed guardrail
        policy and the adversarial corpus together.
      - `--diff-filter=AMR` -- a TYPECHANGE reports `1  9`: one line added, nine
        lines of a decision record deleted. An earlier version removed this filter
        as "redundant with `added > 0`" because deleting it left the suite green.
        That measured test coverage, not necessity.
      - `--find-renames` plus `RENAME_RE` -- a content-free `git mv` produces a
        deletion AND an addition, so it paid twice.
      - `seen` -- `docs/adr/{a => ADR-001-old}.md` x3 resolve to ONE untouched ADR.
        Also removed once as "unreachable".
      - `changed` -- the workflow's file list and this diff must describe the same
        PR. They did not: `git diff <base>` with one revision compares base to the
        WORKING TREE, which on `pull_request` is `refs/pull/N/merge`, so an ADR
        that landed on `main` after the base sha was credited to a PR containing
        none.
      - `substantive_words` -- one non-blank byte cleared `added > 0`. Measured
        across all 69 content-adding ADR edits in this repository's history, the
        LEANEST carries 18 substantive words; `x`, a zero-width space, a symlink's
        target and a 17-byte stub all score 0. A bar of 6 refuses none of the 69.
    """
    if repo_root is None or not base:
        return [], []
    endpoints = [base] + ([head] if head else [])
    out = _git(repo_root, "diff", "-w", "--ignore-blank-lines", "--numstat",
               "--diff-filter=AMR", "--find-renames", *endpoints, "--", "docs/adr/")
    in_diff = set(normalize_paths(changed or []))

    records, defects, seen = [], [], set()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, _deleted, path = parts
        renamed = RENAME_RE.match(path)
        # BOTH sides of a rename, because the body diff below needs them to pair
        # the change the way `--numstat` already did.
        was = None
        if renamed:
            pre, old_mid, new_mid, post = renamed.groups()
            was, path = pre + old_mid + post, pre + new_mid + post
        if path in seen or not ADR_PATH_RE.match(path):
            continue
        seen.add(path)
        # `-` is git's marker for a binary file: not a decision record.
        if added in ("0", "-"):
            continue
        if changed is not None and path not in in_diff:
            # The ADR evidence and the changed-file list must describe one PR.
            continue
        # **The pathspec carries the OLD path too, and that is the whole of it.**
        # `--numstat` above is given the whole directory, so git pairs a rename and
        # reports the truth: `1  0`. This call was scoped to the NEW path alone,
        # where git cannot see the deletion of the old one and reads the file as
        # brand new -- so every line of a 2023 ADR counted as written by this diff.
        # Measured: a slug typo-fix plus the character `x` scored 47 added lines
        # and 10 distinct substantive words, discharged the corpus rule, and made
        # `render` print a decision record that does not exist. With both paths it
        # scores 1 line and 0 words.
        #
        # Two diffs describing one change and disagreeing about it is the same
        # defect as the base/head endpoints one function up, in the same function,
        # found by a different seat.
        paths = [path] if was is None else [was, path]
        body = _git(repo_root, "diff", "-w", "--ignore-blank-lines", "-U0",
                    "--find-renames", *endpoints, "--", *paths)
        written = "\n".join(ln[1:] for ln in body.splitlines()
                             if ln.startswith("+") and not ln.startswith("+++"))
        # DISTINCT, and the distinctness is not decoration. The flat count is the
        # rationale bar's, and the rationale bar's known weakness came with it:
        # four seats refused an earlier version of that bar partly because it was
        # "cleared by nonsense", and `banana banana banana banana banana banana`
        # clears a flat six exactly the same way here. Measured across the same 69
        # content-adding ADR edits: the leanest carries 17 DISTINCT substantive
        # words, so a distinct bar of six refuses none of them and leaves a 2.8x
        # margin, while repetition collapses to one.
        #
        # It does not close the class. `lorem ipsum dolor sit amet consectetur`
        # counts six distinct words, and so does this module's own BLOCKED message
        # pasted back. No word count separates prose from meaningless prose --
        # that is a judgement, and it belongs to the seat reviewing the PR, which
        # `render` now actually shows what was accepted.
        if len(set(substantive_words(written))) < MIN_SUBSTANTIVE_WORDS:
            defects.append(
                f"`{path}` is in this diff and adds no reasoning to it. A decision "
                f"record is prose about a decision, not a line."
            )
            continue
        defect = adr_defect(path, repo_root)
        if defect:
            defects.append(defect)
        else:
            records.append(path)
    return sorted(records), defects


@dataclass(frozen=True)
class Rule:
    """One two-key path class, straight out of docs/governance/ROLES.md."""

    what: str
    pattern: re.Pattern
    seats: tuple[str, ...]
    requires_adr: bool = False


#: Mirrors the two-key table in ROLES.md. Adding a row here is an AI Quality
#: change; removing one is the change this whole module exists to make visible.
RULES: tuple[Rule, ...] = (
    Rule(
        "golden cases, eval thresholds, and headroom policy",
        re.compile(r"^services/[^/]+/evals/"),
        ("ai-quality",),
    ),
    Rule(
        # **Security joined at M06, closing SPEC/06 A19 and decision 6.** Drafts 5-8
        # recorded this as explicitly NOT an attack, because `frozen.json` is
        # defended three layers deep -- `held_out_guard()`, `matching_instrument()`
        # and two position/name pins. All three defences are real. The route that
        # matters does not attack them: it **satisfies** them.
        #
        # Measured: edit `quality/judge/prompt.md`, recompute the digests through
        # `judge.instrument()`, keep the instrument name `B`, and append the previous
        # B as a retired row also named `B` -- you do not rename, you shadow. A real
        # retune is loud (15 failed); the refreeze lands at **1 failed** and then
        # clean, on **one key**. Attacking the guards directly is dearer and noisier,
        # which is exactly why the one-key route is the cheap one.
        #
        # `security` rather than a third seat, on decision 6's standard and round
        # 10's settlement: the counterweight must be the seat with a concrete object
        # to check, and it may not be `ai-quality`, which owns the rubric whose
        # scores this freeze decides. Security reads instrument digests already.
        "judge rubric, calibration set, and agreement thresholds",
        re.compile(r"^quality/judge/"),
        ("ai-quality", "security"),
    ),
    Rule(
        "the verdict schema — the contract the gate decides on",
        re.compile(r"^quality/verdicts/"),
        ("ai-quality",),
    ),
    Rule(
        # **The whole directory, one prefix, no exclusion pattern (ADR-042).**
        # `pins.json` and `schema.json` included: the schema is a protection ON
        # the rows and the pins are the only thing that says the set on disk is
        # the set that was recorded. Three seats, because a fabricated `m04`
        # 10/10 row needed every seat but the one that owns what a probe passing
        # means (Security), and Platform Engineering owns the lane that reads an
        # entry into a gate decision and the recorder that writes one -- which
        # is an interest in dispositioning a bad entry quietly, not a
        # counterweight. Measured: a schema-valid 24/25 row appended beside the
        # real 19/25 left 1701 tests and the gate green on one key.
        "recorded history — a new row is a claim three seats attest; a reset is a "
        "decision, never a cleanup",
        re.compile(r"^evals/history/"),
        ("ai-quality", "security", "platform-eng"),
    ),
    # --- ADR-041: the arm-scoping mechanism, and the files it actually rests on ---
    #
    # An adversarial verdict now turns on which probes an arm's run recorded
    # ASKING. Four of the five files that decide that were on no rule at all,
    # which made the mechanism's own protections cheaper than the thing they
    # protect -- ADR-035's and ADR-037's finding arriving a seventh and eighth
    # time. Each was found by planting and running, not by reading.
    Rule(
        # The evidence every adversarial verdict is derived from, and the file a
        # scope attack deletes from. Measured: dropping one failing probe's
        # observation and its manifest entry took m04 from 7/10 to 7/9 -- 70.0% to
        # 77.8% -- with the lane PASS, the gate exit 0 and the whole suite green.
        # Security AND AI Quality: the seat that owns what a probe passing means,
        # plus the seat that owns the recorded number it is compared against.
        # **`tool-probes-run.json` is covered by the same rule** (ADR-060's arm,
        # observed). It is the tool-plane corpus's evidence and it is what a scope
        # attack deletes from for exactly the reason the model arm's is: dropping a
        # failing row's observation and its `_asked` entry shrinks the denominator
        # rather than raising INFRA. It landed on NO rule while the file beside it
        # took two keys, which is the gap ADR-060 closed one file over for the
        # producer -- so it is closed here, in the diff that creates the evidence.
        "committed adversarial evidence and the question set each arm recorded asking",
        re.compile(r"^milestones/.*/(tool-)?probes-run\.json$"),
        ("security", "ai-quality"),
    ),
    Rule(
        # `_asked` is written HERE. Relocating the scope fact from the probe to
        # the arm moved the knob out of a two-key file and into an unattested
        # one: a one-line edit building the manifest from `observations` instead
        # of from `probes` silently drops every unobserved probe out of the
        # denominator, and it survived the lane, the suite and six of seven
        # digests -- only `capture_sha256` moved, and the same PR re-registers
        # that.
        "the producer of an arm's observations and its question set",
        # Both producers, and the twin is here because it was missed once. The
        # ungoverned baseline writes m00b's evidence -- the control every later
        # delta is measured against -- and it was in no digest and on no rule
        # while its governed sibling was in both.
        #
        # **`run_tool_probes.py` is the third** (ADR-060). It is the arm for
        # `quality/adversarial/tool-plane-probes.yaml`, and it decides the same
        # thing the other two decide: which rows an arm recorded ASKING, written
        # into `_asked` by this file rather than derived from what came back. A
        # new producer landing on no rule while the corpus it runs takes two keys
        # plus an ADR is the ADR-035 / ADR-037 shape, and this milestone found
        # that shape twice already -- so the rule is widened in the same diff
        # that adds the producer, never in a follow-up.
        #
        # **`topic_baseline.py` is the fourth, and it was missed by that very
        # sentence** (the M06b seat round). It gained three arms in one milestone
        # -- `--output-attacks`, `--refusal-shapes`, `--decomposition` -- and is
        # the producer for three corpora that each take Security's key plus an
        # ADR, while its two named siblings were being widened onto this rule for
        # exactly that argument. Platform Engineering measured it re-wired to
        # `source="INPUT"` and reading the wrong corpus, both green; Security
        # found it deciding which rows carry an expectation at all. A producer
        # that chooses the channel its corpus is scored on is not a diagnostic
        # beside the corpus, it is half of it.
        # **And its guard, for the reason this rule keeps being widened.** The
        # seat round found four new guard files standing over two- and three-key
        # subjects on no rule at all, in the diffs that closed that shape three
        # times. `tests/test_topic_baseline.py` is the only reader of this
        # producer's arm table; leaving it one-key would be the fifth instance,
        # created by the diff fixing the first four.
        # **`read_withheld.py` (M06c, ADR-066 step 0).** It reads the audit lake
        # and decides, from a digest, whether ADR-066 is withdrawn or its pricing
        # stands. It writes no observation a scorer sees, so it is not a producer
        # in the narrow sense -- but it is the only reader of the field G4's
        # boundary was drawn around, and which side of that boundary a tool sits
        # on is exactly what this rule's two seats exist to decide together.
        # Added in the diff that creates it, never in a follow-up.
        re.compile(r"^(services/[^/]+/(run_(probes(_via_gateway)?|tool_probes)"
                   r"|topic_baseline|read_withheld)\.py|tests/test_topic_baseline\.py)$"),
        ("security", "platform-eng"),
    ),
    Rule(
        # Both recorders, and the same three seats as the directory they write
        # into (ADR-042 decision 1). The recorders enforce the schema, which takes
        # three; a recorder that can write a row the schema would refuse is a
        # schema change made in code, and relaxing it on fewer keys than the
        # schema is the pairwise inversion ADR-041 prediction 6 and ADR-042
        # prediction 7 audit for. `run_evals.py` was on NO rule while its twin
        # took two -- draft 1 of ADR-042 justified a seat by naming "both
        # recorders" and one of them was unguarded inside the sentence.
        "the recorders — what lands in append-only history, and the pin beside it",
        re.compile(r"^evals/run_(evals|adversarial)\.py$"),
        ("ai-quality", "security", "platform-eng"),
    ),
    Rule(
        # **The checks themselves, as functions, and the step that decides
        # (ADR-042 decision 3).** The deciding instance of the append-only check
        # cannot be a pytest: `tests/conftest.py` and `pyproject.toml` control the
        # harness on zero keys, and a seat measured both deselecting and re-basing
        # the three-key protection tests with `pave check` exit 0. So the checks
        # live in one module that `pave gate history --base <event sha>` runs
        # from the workflow, and that module takes the directory's own three keys.
        # A module on no rule would be ADR-042 prediction 7 failing a fourth time.
        #
        # **`tests/test_tool_surface.py` joins it (the M06b seat round).** The Tool
        # Owner seat neutered `check_tool_surface` with an early return and got
        # exactly three failures, all three in that one file and nowhere else. So
        # the only thing standing between a fabricated `tool_surface` and
        # append-only history was a file any single seat could edit, while all
        # three of its subjects -- this module, `evals/run_evals.py` and
        # `evals/history/schema.json` -- take three keys. The guard joins the
        # subject rather than the subject losing the guard.
        "the history checks — completeness, the evidence anchor, the corpus tie, the "
        "merge-base diff — and the test that is their only reader",
        re.compile(r"^(pave/history\.py|tests/test_tool_surface\.py)$"),
        ("ai-quality", "security", "platform-eng"),
    ),
    Rule(
        # **Goldens evidence, which took no key (ADR-042 decision 5).** The
        # adversarial evidence rule above names `probes-run.json` and nothing
        # else; `milestones/M05/goldens-run.json` and `milestones/M02/runs/*.json`
        # resolved to no rule at all, so "evidence that is itself under two keys"
        # was true for one filename. AI Quality owns the number the answers score
        # to; Platform Engineering owns the lane that re-scores them.
        "committed goldens evidence — the answers a recorded entry was summarised from",
        re.compile(r"^milestones/[^/]+/(goldens-run\.json|runs/[^/]+\.json)$"),
        ("ai-quality", "platform-eng"),
    ),
    Rule(
        # **ADR-049. The obligation register, and the check that reads it.** The
        # data half alone was SPEC/05's row; the test is here for ADR-043 decision
        # 1's reason -- an instrument and the thing it measures are weakened
        # together or not at all, which is ADR-044's whole subject. Measured at the
        # M05 close: re-deferring three acts one milestone was **2072 passed, zero
        # keys**, and `test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed`
        # cannot tell a first deferral from a fourth, so an act could slide forever
        # on nobody's signature. `deferred_from` counts the slides and this rule is
        # what makes each one cost two dispositions.
        #
        # **`docs/governance/demo-script.md` is deliberately NOT here, and that is a
        # stated residual.** Dropping an act by editing the prose is already red --
        # `test_every_act_in_the_script_is_tracked` compares the script's acts to
        # this registry's in both directions -- so the obligation cannot be deleted
        # from the script. What an unkeyed script still permits is rewriting an
        # act's CONTENT, which is a presentation change. Keying it would put two
        # seats on every wording fix.
        "the demo-act obligation register — a deferral is a decision, and the count of "
        "deferrals is the part that was free",
        re.compile(r"^(docs/governance/recordings\.json|tests/test_demo_recordings\.py)$"),
        ("platform-eng", "ai-quality"),
    ),
    Rule(
        # **ADR-049. SPEC/05 named this row and no PR built it.** Justified on
        # `evals:` and `adversarial:` -- the two `--record` entrypoints -- and above
        # all on the `OBSERVATIONS` guard, whose entire job is to stop a bare
        # `make adversarial` recording a second row over another milestone's
        # evidence. That is an append-only-history control living in a Makefile.
        # Measured at the M05 close: deleting the guard outright is **2072 passed**,
        # and reducing `check:` to `@echo ok` -- the `|| echo` shape this file's own
        # header records the repository shipping for its entire life -- is **2072
        # passed**. Both on zero keys.
        #
        # **Not justified on `core:`**, which is a deploy gate whose pain AI Quality
        # does not feel; SPEC/05 draft 4 cited it and the seat table corrected that.
        # The seat is here for the recorders, and it is the same pair the recorders'
        # own rule would collect minus Security, which owns what a probe passing
        # means and not where the recorder is invoked from.
        "the developer entrypoints — the two --record invocations and the guard that "
        "stops one overwriting another milestone's evidence",
        re.compile(r"^Makefile$"),
        ("platform-eng", "ai-quality"),
    ),
    Rule(
        # **ADR-049. The third row SPEC/05 stated and nothing built.** The file's own
        # docstring at `:124` says *"`gates.budgets` is a two-key path; a number that
        # moves there without a written derivation is the change this rule exists to
        # make visible"* -- and the file holding that sentence was on no rule at all.
        # The manifest half was closed by ADR-046's `services/*/pave.manifest.yaml`
        # row; the PIN half was not. Measured at the M05 close: deleting
        # `tests/test_budget_derivation.py` is **2059 passed, zero failures** -- the
        # only thing tying the committed ceilings to the committed measurement
        # ADR-014's amendment derived them from, gone in one file deletion on zero
        # keys. Exactly ADR-044's finding, in the one instrument its audit missed.
        #
        # Seats from the file's own docstring rather than chosen: *"AI Quality (the
        # ceilings -- two-key) - Platform Engineering (the loop bound)"*. SPEC/05
        # draft 4 paired it with `tool-owner`, contradicting the file.
        "the budget derivation pin — the committed ceilings tied to the committed "
        "measurement they were derived from",
        re.compile(r"^tests/test_budget_derivation\.py$"),
        ("ai-quality", "platform-eng"),
    ),
    Rule(
        # Gate CRITERIA, deliberately not in `pave/cli.py`: that file is ~1200
        # lines of command dispatch and `test_ordinary_pr_is_not_gated` names it
        # as the canonical UNGATED example. Gating all of it to protect three
        # constants teaches people to attest past a rule without reading it.
        # `pave/gate.py`'s docstring draws the line -- Platform Engineering owns
        # the mechanism, AI Quality owns the criteria that produce a FAIL.
        # **ADR-045 adds the test alongside the module**, for ADR-043 decision 1's
        # reason: they are weakened together or not at all. `pave/floors.py` now
        # holds `DECLARABLE_LEVELS`, `HEADROOM_BAND`, `PLATFORM_EVAL_MIN_CASES` and
        # `COLLECTED_FLOOR`, and every pin on those lives in `tests/test_floors.py`
        # — including the two that an earlier arrangement got wrong: the band shown
        # APPLIED to the committed pack, and the G5 pin over the whole taxonomy
        # rather than over the one-element declarable vocabulary.
        "the gate's floors — criteria, not mechanism",
        re.compile(r"^(pave/floors\.py|tests/test_floors\.py)$"),
        # **Security too, and on the merits rather than to balance a count.** The
        # floors here are statements about what a probe passing means: how many
        # G4 cases must still SCORE, and how many probes an arm must have been
        # asked. `g4-semantics.yaml` is Security's with an ADR, and a floor that
        # decides how much of it may stop counting is the same decision one level
        # out. Found by a pairwise audit: the floors protect `comparators.json`,
        # which takes three keys, and were removable on two.
        ("platform-eng", "ai-quality", "security"),
    ),
    Rule(
        # ADR-046. The verifier and its own tests, on one rule for ADR-043
        # decision 1's reason: they are weakened together or not at all. The
        # refusal table lives in `pave/manifest.py` as `ROWS` and the producer for
        # every row lives in `tests/test_manifest_verify.py`, so a row deleted
        # from one and the other is a refusal that stops existing with nothing
        # red -- and the file that would have caught it would be the one deleted
        # alongside.
        #
        # **Valid at three seats only because the verifier holds mechanism.**
        # Every number, level and vocabulary it refuses on is imported from
        # `pave/floors.py`, which is on its own rule with the same three seats;
        # `tests/test_manifest_verify.py` moves each of those criteria and
        # requires the verifier to follow, so an inlined copy is red rather than
        # a quiet relocation of AI Quality's key onto Platform Engineering's.
        #
        # Security, on the merits: rows 3 and 4 are the bijection between what a
        # service declares and what Cedar grants it, and row 4's direction --
        # every grant is declared -- is the one nothing in this repository had.
        # A grant nobody declared is a permission with no owner.
        "the manifest verifier and the refusals it commits to",
        re.compile(r"^(pave/(manifest|verify)\.py|tests/test_manifest_verify\.py)$"),
        ("ai-quality", "security", "platform-eng"),
    ),
    Rule(
        # ADR-046. What a service declares about itself: its tool set, its
        # classification, its brand and the floor it deploys above.
        #
        # **Not `data-governance`, and that seat's own argument is why.** ADR-045
        # made `classification` a singleton -- `("internal",)` -- so the only
        # edits this rule can gate on that field are edits the verifier already
        # refuses outright. A seat collected on a value with one legal setting is
        # collected on nothing, which is the decorative-second-key shape ADR-037
        # found three times in `.github/CODEOWNERS`.
        #
        # **Security is NOT here and that is an open question, not a decision.**
        # `highlights-agent`'s manifest now declares `publish-highlight`, whose
        # consequence class is `publish` -- so the complete path to granting a
        # scaffolded service the one human-approval-interlocked tool collects
        # `tool-owner` and `legal-sp` on the registry line and `ai-quality` and
        # `tool-owner` here, and Security on neither. A path rule cannot say
        # "when the declared set intersects GATED_CONSEQUENCES"; deciding whether
        # this rule takes Security unconditionally is owed by SPEC/05 and is
        # recorded in ADR-046 rather than settled here.
        "what a service declares about itself",
        re.compile(r"^services/[^/]+/pave\.manifest\.yaml$"),
        ("ai-quality", "tool-owner"),
    ),
    Rule(
        # ADR-047. **The default every service that does not exist yet inherits.**
        # A manifest edit changes one service; a template edit changes the tool
        # set, the case floor, the headroom expectation and the wire text of every
        # service anyone scaffolds from here on -- and none of those services can
        # review the diff, because none of them exists.
        #
        # `pave/scaffold.py` and `tests/test_scaffold.py` are on the SAME rule, for
        # ADR-043 decision 1's reason. The pairwise tests are the only thing that
        # notices a template drifting from the service it was cut from: nothing in
        # this repository compared `templates/agent-tools/` to
        # `services/highlights-agent/` for four milestones, because the template
        # directory held one README and nothing else. A template on a rule whose
        # drift detector is not is a template that can be silently un-checked.
        #
        # **Security, on the merits.** The template's `gateway_client.py.tmpl`
        # carries `user_turn` -- the wire text of every observation every scaffolded
        # service will ever be judged on -- and no instrument digest covers the
        # transport (ADR-048). It also decides which tool a new service declares by
        # default, which is an authorization claim made on behalf of teams that
        # cannot yet object.
        #
        # **Tool Owner** for the declared `tools:` block; **AI Quality** for
        # `gates.*`, the scaffold pack and the headroom example.
        "the scaffold every future service inherits",
        re.compile(r"^(templates/agent-tools/.+|pave/scaffold\.py"
                   r"|tests/test_scaffold\.py)$"),
        ("platform-eng", "ai-quality", "tool-owner", "security"),
    ),
    Rule(
        # **The tests that EXECUTE the protections, not merely declare them.**
        # Six of ten planted weakenings survived a fully registered commit for
        # one reason: the check they removed was unreachable on an honest tree,
        # so deleting it produced no failure anywhere. A two-key path on a check
        # nothing runs is the "stated protection is worse than an absent one"
        # pattern this repo has recorded eight times -- so the rule and the
        # violating-tree test are two halves of one control.
        #
        # Scoped to the two files that hold instrument and scope protections.
        # `tests/` at large is deliberately NOT here, for `pave/cli.py`'s reason.
        # `test_adversarial_lane.py` holds `G4_CASE_FLOOR`'s ratchet -- which
        # `floors.py`'s own docstring calls the half that does the work -- and
        # `test_adversarial_entry.py` holds the instrument-order fix. Both were
        # unguarded while `pave/floors.py`, which they protect, takes three keys.
        "the tests that execute the instrument and arm-scoping protections",
        # `test_history_append_only` holds ADR-042's completeness pin, the
        # merge-base diff, the evidence anchor, the schema ratchet and the
        # seat-set test -- every protection that ADR adds, in one file on the
        # rule, because its draft 2 named no file and every plausible name
        # resolved to no rule at all.
        re.compile(r"^tests/(test_arm_scoping|test_instrument_stability|test_adversarial_lane|test_adversarial_entry|test_history_append_only|test_transport_parity)\.py$"),
        # Platform Engineering joins because `PIN_FLOOR` lives here and duplicates
        # comparator values on purpose -- the lane that reads those pins is theirs,
        # and the duplication is what makes moving a pinned number take a code diff
        # as well as an attested comparator diff. Same pairwise audit.
        ("ai-quality", "security", "platform-eng"),
    ),
    Rule(
        # The number the L2 lane actually decides on, and it was the one artifact in
        # this table's neighbourhood that nothing covered. `evals/history/` is
        # protected and append-only; the comparator is neither, and it is the live
        # criterion. Three separate places asserted this rule existed before it did
        # -- the file's own `_comment`, the lane's failure message, and a PR body --
        # which is worse than an unguarded path, because a stated protection stops
        # anyone looking for the real one. Found by three seats independently.
        #
        # `evals/deterministic.py` and `data/catalog.json` are the lane's other two
        # inputs and are deliberately NOT here: a scorer change should be reviewable
        # as code, and it becomes visible the moment it moves a comparator, which now
        # needs this key. The point is that the loop cannot be closed unattested.
        #
        # **Security joined at M04, when the file stopped being only the L2
        # comparator.** The adversarial pins moved in here so the L5 lane would have
        # one place to read a pin from rather than a third; the effect was that a
        # probe number — Security's, under `quality/adversarial/`'s own rule — became
        # movable on two attestations, neither from the seat that owns G4. Three seats
        # named it independently on the PR that caused it, and it is the same shape as
        # the fault above: the rule's wording stayed put while its scope doubled.
        #
        # The seat list is the UNION of both suites' owners, because the pattern is a
        # path and the file holds two suites. That is over-broad for a purely golden
        # re-pin, deliberately: over-broad in the direction of more review is the
        # fail-closed direction, and a rule that cannot tell which suite moved must
        # not pretend it can. `requires_adr` stays off — the file's own `_comment`
        # already requires the PR body to name the instrument change and its
        # direction, and an ADR per comparator move would price routine tightenings
        # high enough to discourage them, which is the pressure that gets tightenings
        # reverted rather than the pressure that keeps baselines honest.
        "the gate's scoring comparators — what committed artifacts score under the "
        "current instrument, for both the golden suite (L2) and the probe corpus (L5)",
        re.compile(r"^evals/comparators\.json$"),
        ("ai-quality", "platform-eng", "security"),
    ),
    Rule(
        "gate criteria",
        re.compile(r"^\.github/workflows/quality-gate\.yml$"),
        ("ai-quality", "platform-eng"),
    ),
    Rule(
        # **Security joined when this module stopped describing an ADR and started
        # DEFINING one (ADR-052).** Until ADR-051 the `requires_adr` half was
        # `ADR_RE.search(body)` plus `is_file()` -- a citation, with nothing in
        # here to weaken. `adr_records` now decides what counts as a decision
        # record, and every one of the four rules that requires one names
        # `security`; `quality/adversarial/` names it ALONE. So the seat that owns
        # the strictest ADR requirement in the file did not sign the definition of
        # what discharges it.
        #
        # Measured on 6589827, one diff, these two files: restore the substance bar
        # to `< 1` -- v3's defect, the one four seats defeated -- and delete the
        # four assertions in `pave/tests/test_twokey.py` that catch it.
        # **2208 passed, ruff clean, keys `ai-quality` and `platform-eng`, and
        # `requires_adr` False.** The corpus rule's ADR requirement goes back to a
        # citation on two keys, neither of them the seat whose rule it is.
        #
        # `pave/tests/test_twokey.py` is here for the second half of that
        # measurement and not as tidiness: it holds every assertion defending
        # `adr_records`, and on no rule it was deletable in the same diff as the
        # weakening. `tests/test_twokey_seats.py` says in its own docstring that
        # this file is on no rule -- true and harmless when it held only parser
        # cases, and the sentence is corrected in this diff rather than left to
        # read as a decision.
        #
        # `requires_adr` stays off. The rules list changes for routine reasons --
        # a new path, a widened alternation -- and ADR-030's reasoning for
        # `comparators.json` applies unchanged: an ADR per rule edit prices
        # tightenings high enough to discourage them.
        "the two-key rules themselves — and the definition of what discharges one",
        # `pave/__init__.py` and the fixture directory are here because the
        # Security seat reached the same weakening around both (ADR-052 round 2):
        #
        #   - `__init__.py` is 0 bytes, was on no rule, and RUNS on any `pave.X`
        #     import. A 27-line shim rebinding `adr_records`, guarded by
        #     `if "pytest" not in sys.modules`, minted a decision record out of a
        #     2023 file the PR never touched -- `two-key: SATISFIED`, exit 0,
        #     **2219 passed, zero keys**. Guarding the definition and its tests
        #     and not the module that can rebind the definition at import is this
        #     rule's own thesis arriving one directory up.
        #   - Every non-source file under `pave/tests/` -- the replay that
        #     justifies ADR-051's
        #     largest reversal and the CRLF corpus. Inflating the replay 60 -> 300
        #     rows and fabricating all but two was **2219 passed, zero keys**: the
        #     module three keys, the evidence for it none. ADR-035's shape, which
        #     is why the whole directory is covered by a prefix rather than the
        #     two files enumerated -- a new fixture is covered the day it lands.
        re.compile(
            r"^(pave/__init__\.py|pave/twokey\.py|pave/tests/test_twokey\.py"
            r"|pave/tests/(?!.*\.py$).+|\.github/workflows/two-key\.yml)$"
        ),
        # **`legal-sp` joined at ADR-053, and it was not a choice.** Giving `rules/`
        # a `requires_adr` rule handed Legal/S&P an ADR requirement, and
        # `test_the_definition_of_a_decision_record_carries_every_adr_rules_seats`
        # turned red on exactly that -- `assert not ['legal-sp']`. ADR-052 decision 2
        # states the property in as many words: *a rule that gives a NEW seat an ADR
        # requirement turns this red until that seat can also defend what satisfying
        # it means.* The seat set here is an OUTPUT of that decision, not a preference
        # expressed in this file.
        ("ai-quality", "legal-sp", "platform-eng", "security"),
    ),
    Rule(
        # **The process that runs the gate, found by Security in ADR-052 round 3.**
        # The round-2 property walked OUTWARD from `pave/twokey.py`, which imports
        # nothing from `pave` -- so its fixed point was `{__init__, twokey}`, both
        # already on the rule above, and the check compared two paths to
        # themselves. The threat is INBOUND: a module that imports `twokey` and
        # rebinds it before the gate uses it.
        #
        # `.github/workflows/two-key.yml` runs `python -m pave.cli gate two-key`.
        # Measured on 729c01e: a 20-line shim in `pave/cli.py` rebinding
        # `twokey.adr_records` and `twokey.evaluate`, under `if "pytest" not in
        # sys.modules`, left **2222 passed** -- the exact baseline -- with the live
        # gate printing `two-key: SATISFIED`, **exit 0**, and naming a decision
        # record for a file the PR never touched. Zero keys. Without the four-word
        # guard the same shim is 75 failed.
        #
        # `gate.py` holds `EXIT_QUALITY`, and flipping it 1 -> 0 makes every rule
        # report BLOCKED and exit 0 -- the audit record intact, the enforcement
        # gone. That one IS caught (13 failed, two of them the CLI tests added
        # here), but every exit-code assertion in `pave/tests/test_gate.py`
        # compares against the SYMBOL, so both sides move together; the catch came
        # from elsewhere and the contract had no key of its own.
        #
        # Two seats, not three. The property this buys is that **Security is
        # asked** -- it owns every rule that requires an ADR and holds the corpus
        # rule alone -- and Platform Engineering owns the mechanism. Eight of the
        # eleven modules in the gate's process already collect `security`; these
        # three did not, and adding `ai-quality` here would tax `pave new` and
        # `pave verify` to buy a property neither needs.
        "the gate's own process — the entrypoint CI runs, the exit-code contract, "
        "and the verdict it writes",
        # `(\.py|/.+)` because a PACKAGE shadows a module: adding
        # `pave/twokeycli/__init__.py` beside `pave/twokeycli.py` makes Python
        # import the package, and `...\.py$` alone did not match it -- measured,
        # the gate ran from a file collecting NO KEYS. Caught by the runtime half
        # (1 failed), but a rule that does not cover the shape leaves that test as
        # the only thing standing between the two.
        re.compile(r"^pave/(twokeycli|gate|verdict)(\.py|/.+)$"),
        ("platform-eng", "security"),
    ),
    Rule(
        # **G7's registry, on no rule at all until M06 (SPEC/06 A14, decision 12).**
        # `rules/` is the Legal/S&P seat's entire surface, and flipping
        # `MER-AI-0001` from `proposed` to `enforced` while its only control is
        # `no-control` was **2079 passed** -- `tests/test_contracts.py`'s review-by
        # guard is written `if effective and rule["status"] != "enforced"`, so
        # declaring a rule enforced switches off its own clock.
        #
        # **`(legal-sp, security)`, and the seat choice is decision 12's.** Round 11
        # refused `data-governance`, which had been chosen off a census -- *What M06
        # must not do* forbids a rule derived from one. The standard this document
        # set is decision 6's: the seat with a concrete object to check.
        # `rules/schema.json` types `disposition.controls[].type` as an enum
        # including `guardrail`, Security owns guardrails and already reads deployed
        # guardrail evidence, so it has something to read when a rule disposes into
        # one. The counterweight cannot be `legal-sp`, which owns the registry.
        #
        # `requires_adr` ON, unlike most rules here: a rule's status is a published
        # governance claim, and decision 12 asks for the ADR by name.
        #
        # **This closes the KEY and nothing else, which decision 12 is explicit
        # about.** Two halves stay open and are recorded in ADR-053 rather than
        # quietly folded in: `effective` is optional in `rules/schema.json`, so a
        # rule that simply OMITS it is never examined by the review-by guard at all
        # (planted: enforced, `review_by: 2099-01-01`, field omitted -- 2079 passed,
        # a literally immortal enforced rule, green), and making it required is a
        # schema change that is Legal/S&P's call. "No orphan rules" is owed to M07
        # with its term still undefined.
        "the rule registry — a rule's status is a published claim, and `enforced` "
        "switches off its own review clock",
        re.compile(r"^rules/"),
        ("legal-sp", "security"),
        requires_adr=True,
    ),
    Rule(
        "consequence classes — raising one raises an action's blast radius",
        re.compile(r"^platform/registry/tools\.yaml$"),
        ("tool-owner", "legal-sp"),
    ),
    Rule(
        # **The control, not only the corpus that measures it.** Until the ADR-035
        # review this table protected `quality/adversarial/` — the probe corpus —
        # and `evals/comparators.json` — the pins those probes score against — and
        # left the deployed guardrail policy needing one attestation and no ADR.
        # The thermometer was guarded twice and the thermostat was guarded neither.
        #
        # G9: *whoever feels a control's pain never solely controls its strength.*
        # The person who wants the guardrail to stop refusing their questions is
        # the person who can widen it, and ADR-035 exists because that pressure is
        # real — the deployed topic refuses the product's most basic question 1 in
        # 3, and classifies the product's own catalog as circumvention. A change
        # that relieves that pain by a sentence is exactly the change that must not
        # be self-served.
        #
        # AI Quality joins because a guardrail change moves what every recorded
        # observation means without moving a single instrument digest — ADR-018's
        # hazard, and the seat that owns whether a before/after survives is the
        # seat that has to see it coming.
        #
        # `requires_adr` is ON, matching `quality/adversarial/` rather than
        # `evals/comparators.json`. A guardrail edit is a policy decision with a
        # measured cost on both sides, not a routine re-pin, and this repo has now
        # produced three ADRs about this one topic. If a tightening is worth
        # deploying it is worth a paragraph saying what it should break.
        # **The pin test joins the policy it guards (ADR-063).** The same shape as
        # the adversarial scorer and its test: weakened together or not at all.
        # `test_guardrail_pin_tracks_policy.py` is what makes a policy change
        # republish the version resource -- ADR-024's failure, caught by a plant --
        # and it was on NO rule while the policy it defends took two keys and an
        # ADR. It also asserted there was exactly ONE guardrail, so it would have
        # gone on passing for the main pair while a second pair's pin tracked
        # nothing. A guard editable on one key over a control that takes two is
        # ADR-035's and ADR-037's finding, and this is its next instance.
        "the deployed guardrail policy — the control itself, not the corpus that measures it",
        re.compile(
            r"^(platform/infra/lib/gateway-stack\.ts"
            r"|tests/test_guardrail_pin_tracks_policy\.py)$"),
        ("security", "ai-quality"),
        requires_adr=True,
    ),
    Rule(
        "the adversarial corpus — only Security may downgrade a probe, and only with an ADR",
        re.compile(r"^quality/adversarial/"),
        ("security",),
        requires_adr=True,
    ),
    Rule(
        # **The corpus rule above says "and only with an ADR". The assertions that
        # make that true lived on a rule that collected neither Security nor an
        # ADR.** They were eight tests inside `tests/test_contracts.py` -- 47 tests
        # about the registry, the manifest, Cedar and the golden suite, under a
        # pattern drawn around three files with nothing in common. Two of the eight
        # state the requirement in their own docstrings and were wrong about it:
        # "Adding a value to G4_PASS_SEMANTICS is a Security-seat change and needs
        # an ADR", and "Only the Security seat may downgrade a probe to advisory,
        # and only with an ADR".
        #
        # ADR-035 found the thermometer guarded twice and the thermostat not.
        # ADR-037 found three second keys written in the one file that cannot
        # collect them. This is the same shape a third time, and it lands on G4 --
        # the invariant CLAUDE.md flags as most often violated by well-meaning
        # changes.
        #
        # THREE SEATS, AND THE SECOND DIRECTION IS THE LIVE ONE. Security cannot
        # weaken the guard on its own control alone -- that half was already true,
        # because Security was not on the old rule at all. What was NOT true is the
        # other half: `ai-quality` and `platform-eng` could delete the tripwire in
        # one PR without Security, and a later Security PR could do the downgrade,
        # with no seat ever having to justify the combination. A guard is owed to
        # the seat whose control it guards even when that seat is the one it points
        # at.
        #
        # Measured cost of the extra key: of the 13 commits that have touched
        # `tests/test_contracts.py`, 2 also touched `quality/adversarial/`.
        "the adversarial corpus's own contracts and G4's semantics allowlist",
        re.compile(r"^tests/test_adversarial_contracts\.py$"),
        ("security", "ai-quality", "platform-eng"),
        requires_adr=True,
    ),
    Rule(
        # **The second key CODEOWNERS already recorded, in the file that can
        # collect it.** This module's own docstring says "the path list here and
        # the path list there are the same list — the interface already matches."
        # Measured at ADR-037: of the four CODEOWNERS paths carrying two handles,
        # ONE had a rule here. A second handle is the only way CODEOWNERS can say
        # "second key", and ADR-013 established that on a one-operator repo it can
        # collect none of them — so those three were second keys written in the one
        # place that provably cannot collect them.
        #
        # CODEOWNERS says why both seats: the module "names this seat in its own
        # docstring -- Owning seat: Security / Red Team -- and matched only
        # `/evals/`, which is AI Quality's. So the module deciding whether a
        # guardrail block counts ... sat with the seat that feels a probe score
        # rather than the seat that defends it. That is G9 read backwards."
        #
        # **The scorer and its test are ONE rule, not two.** They are weakened
        # together or not at all — a scorer relaxed in the same PR as the test that
        # would have caught it is the shape G9 makes expensive — and two rules would
        # let a PR attest to one and move the other quietly.
        #
        # `requires_adr` is OFF, for the reason `evals/comparators.json` above
        # already records: an ADR gate on a file that changes often and legitimately
        # prices routine tightenings high enough to discourage them. The written
        # rationale is the control here. `gateway-stack.ts` keeps its ADR because a
        # published policy version is an instrument, not a routine edit.
        "the adversarial scorer and its test — what a probe passing MEANS, and every "
        "instrument digest",
        re.compile(r"^(evals/adversarial\.py|tests/test_adversarial_scoring\.py)$"),
        ("security", "ai-quality"),
    ),
    Rule(
        # **ADR-060: the corpus and the test that says what its rows may claim.**
        # Same argument as the scorer rule above, one corpus down.
        # `quality/adversarial/` gives `tool-plane-probes.yaml` Security's key and
        # an ADR. But three of its six rows are refused by `schema`, which G4
        # deliberately does not accept, and the only thing standing between those
        # rows and a security pass is
        # `test_tool_plane_probes.py::test_no_argument_refusal_row_can_satisfy_g4`.
        # Reclassifying one row's `kind` is a one-word edit inside a file Security
        # already owns alone.
        #
        # So the test takes AI Quality too: the seat that owns what a recorded
        # number means is the seat that must co-sign a change letting three more
        # rows into it. G9 exactly -- the seat that would feel a probe corpus
        # scoring nothing is not the seat that may alone decide it scores.
        #
        # `requires_adr` is OFF for the reason the scorer rule records: the
        # written rationale is the control, and an ADR gate on a test file that
        # gains rows routinely prices tightenings high enough to discourage them.
        # **The M06b seat round, and the fourth instance of this shape in the
        # milestone that closed it three times.** AI Quality and Platform
        # Engineering independently planted a hand-written attribution into a
        # derived artifact and watched the finding change with the suite green:
        # `option-e-prediction.json`'s `measures` moved the readout from "option E
        # does not survive its own instrument" to the outcome its own corpus header
        # names "the case for the change", and `decomposition-cases.json`'s
        # `by_clause_type` -- the field the corpus calls "the discriminator" --
        # decided which reading ADR-068 published.
        #
        # These three files are now the only readers of those artifacts, and the
        # artifacts are the only published form of what three Security-owned
        # corpora measured. Same seats as the tool-plane rule below and for the
        # same reason: Security owns what an output-side verdict means, AI Quality
        # owns what a recorded number is allowed to claim. No ADR flag -- the
        # corpora carry that requirement and a guard is not a second decision.
        "the derived readings of the output-side corpora — the tie between a frozen "
        "row and the finding published from it",
        re.compile(r"^tests/test_(output_side_prediction|refusal_shapes|"
                   r"answer_decomposition)\.py$"),
        ("security", "ai-quality"),
    ),
    Rule(
        "what a tool-plane row may claim — the corpus's kinds and the G4 boundary "
        "between them",
        re.compile(r"^tests/test_tool_plane_probes\.py$"),
        ("security", "ai-quality"),
    ),
    Rule(
        # Same finding, same ADR. The docstring names both seats already:
        # "Owning seat: Platform Engineering (record shape) · Security (G4
        # semantics)." It holds `POLICY_MECHANISMS`, `build_record`'s consistency
        # checks, and `observation_from_record` — the function that turns a record
        # into the observation the scorer reads. The ADR-036 review measured that a
        # record can assert a guardrail block while its own attribution says nothing
        # fired, and score the probe PASS; the fix for that lands under this rule.
        "the audit record shape and the observation the scorer reads",
        re.compile(r"^platform/gateway/core/audit\.py$"),
        ("platform-eng", "security"),
    ),
    Rule(
        # **The decision path (ADR-040 decision 5).** From ADR-040 a G4 verdict
        # turns on which channel `interpret` derives and which channel
        # `toolloop.py` hands `interpret_apply` — and both files, plus the schema
        # validating the result, were one key, any seat, and in no digest. Three
        # seats found it independently across the ADR-036 and ADR-040 reviews, and
        # ADR-037 and ADR-039 each named it and declined to pre-empt it. This is
        # the change that makes the value scoring-relevant, so it is decided here
        # rather than owed a fourth time.
        #
        # `handler.py` is included because it is the other reader of the outcome,
        # and the place ADR-039 had to move logic OUT of after finding two lines
        # there that no test could reach.
        #
        # `requires_adr` off, for the reason `evals/comparators.json` records: an
        # ADR gate on files that change often and legitimately prices routine
        # tightenings high enough to discourage them.
        "the gateway decision path and the record contract — which channel a block is "
        "attributed to, and what shape may be written",
        # `tests/test_handler_wiring.py` is here for the reason the pin test is on
        # the guardrail rule: it is the ONLY thing asserting what `handler.py`
        # passes -- the file is imported by no test by design (it holds the boto3
        # clients), so this parses it instead. It was on no rule, and ADR-063 found
        # that its converse-path half had been inspecting nothing since it was
        # written. A guard that can be edited on one key over a two-key subject is
        # the same shape twice.
        re.compile(
            r"^(platform/gateway/(core/(guardrail|toolloop)\.py|handler\.py|audit\.schema\.json)"
            r"|tests/test_handler_wiring\.py)$"),
        ("platform-eng", "security"),
    ),
    Rule(
        # **The file that pins every other rule's seat set, on the union of the
        # seats it pins.** ADR-043 first put this on the enumerated
        # protection-test rule (ai-quality, security, platform-eng), and the
        # Legal/S&P seat measured the consequence: those three seats could drop
        # `legal-sp` from the generator rule AND edit the pin here in one diff, at
        # 1814 passed, with the seat losing its key never asked. That is ADR-037's
        # shape -- a protection guarded by a seat set excluding the seat it
        # protects -- on the very rule ADR-043 added to close it.
        #
        # Five seats on one small file is heavy and correct: its whole job is to
        # hold other rules' seat sets, so every seat whose key it pins signs its
        # removal. `ai-quality` is here because `twokey.py`'s own docstring names
        # it as the owner of the rules list.
        "the seat-set pins — every rule's seats, held where each of those seats must sign",
        re.compile(r"^tests/test_twokey_seats\.py$"),
        ("ai-quality", "security", "platform-eng", "tool-owner", "legal-sp"),
    ),
    Rule(
        # **The plane that RELEASES the interlock, found by Security against the
        # code.** `toolplane.py:1` says "nothing reaches a tool except through
        # here (G3)" and `:30` names three seats -- Platform Engineering
        # (mechanism), Tool Owner (the contracts), Security (it is an
        # authorization path). It was on no rule, and neither was its test.
        #
        # Measured: neutering `Approval.__post_init__`'s guard so `Approval("","")`
        # validates, plus the one test that catches it, left **1814 passed** and
        # `two-key: not required`. ADR-043 gave four keys to the constant that
        # DECLARES which classes are gated while the code that decides an approval
        # is good enough to RELEASE one kept zero -- the asymmetry ADR-035 was
        # written about, inside the ADR written to remove it.
        "the tool plane — nothing reaches a tool except through here, and what counts "
        "as an approval",
        re.compile(r"^(platform/gateway/core/toolplane\.py|tests/test_toolplane\.py)$"),
        ("platform-eng", "security", "tool-owner"),
    ),
    # --- ADR-043: paths that decide an invariant and collected no key ---
    #
    # All five were found by the six-seat SPEC/05 review PLANTING against `main`,
    # not by reading, and four of the five contradict a comment sitting in the
    # same file. None was introduced by M05.
    Rule(
        # **G1's allowlist, and the assertion that pins it.** Measured: widening
        # `MODEL_INVOKE_ROLE_PREFIXES` and relaxing its own pin in one diff left
        # 1795 passed and collected NO key -- against `pave/infra.py:64` ("it
        # needs an ADR and the Security seat rather than a commit") and
        # `tests/test_iam_assertions.py:118` ("Adding another is a G1 exception
        # (Security seat + ADR), not a test fix"). Two protections stated in the
        # two places a reader would look, enforced in neither.
        #
        # ONE rule over both files, deliberately: they are weakened together or
        # not at all, and two rules would let a PR attest to one and move the
        # other quietly -- the shape `evals/adversarial.py` and its test use.
        #
        # **Honest limit (ADR-043 decision 4):** this makes the widening
        # COLLECTABLE, never red. A self-pinning constant edited alongside its
        # own pin produces no failure, and only a second assertion at a different
        # path would. That residual is stated in the ADR rather than implied.
        "G1's model-invoke allowlist and the assertions defending it — adding an entry "
        "is writing an exception",
        re.compile(r"^(pave/infra\.py|tests/test_iam_assertions\.py)$"),
        ("security", "platform-eng"),
        requires_adr=True,
    ),
    Rule(
        # **The generator, its test, and the schemas it renders into the deployed
        # contract set.** Three measured, keyless paths to a G3 or claim-10
        # weakening:
        #
        #   - two lines in `generate()` put `permit(principal ==
        #     Service::"attacker-svc", ...)` into `tools.cedar`, with
        #     `policy generate --check` at exit 0, 1795 passed, and the two-key
        #     registry never touched. The drift gate is `generate(REGISTRY) ==
        #     COMMITTED` -- both sides call the same function, so it proves the
        #     artifact is a faithful build product OF the generator and never
        #     that the generator is a faithful function OF the registry. ADR-004
        #     says "the registry decides"; what was enforced is "the generator
        #     decides."
        #   - dropping `"publish"` from `GATED_CONSEQUENCES` removes EVERY forbid
        #     clause and makes `publish-highlight` reachable with no approver.
        #     That one IS caught by fifteen assertions -- and collected no key,
        #     so claim 10 could be weakened with no written reason, and the three
        #     files that catch it are the three a `collect_ignore` line disables.
        #   - deleting `ai_generated` from a tool's input schema and adding
        #     `skip_approval` travels into `tools.contracts.json`, which ships
        #     inside the gateway bundle: 1795 passed, no key.
        #
        # **`legal-sp` is here because `GATED_CONSEQUENCES` is a consequence-class
        # judgement and it lives in the generator.** The Security seat recommended
        # a seat set excluding it in one review round and retracted that in the
        # next, on this measurement -- CLAUDE.md assigns consequence classes to
        # Tool Owner plus Legal/S&P, and the registry rule alone cannot collect a
        # key for a constant that is not in the registry.
        #
        # Four seats on a generator that changes rarely is over-broad, and
        # over-broad in the direction of more review is the fail-closed direction
        # -- `evals/comparators.json` already records that argument.
        "the Cedar generator, its test, and the tool schemas — what the deployed policy "
        "set and contract set may say",
        re.compile(r"^(platform/gateway/core/cedar\.py|tests/test_cedar_policy\.py"
                   r"|tools/[^/]+/schema\.(in|out)\.json)$"),
        ("platform-eng", "security", "tool-owner", "legal-sp"),
    ),
    Rule(
        # **The harness the other ~1790 assertions run under.** ADR-042 decision 8
        # listed these as "none -- stated", on the reasoning that they cannot
        # touch the workflow step that decides the history checks. That reasoning
        # holds for the history checks and for nothing else.
        #
        # Measured: `collect_ignore` in `tests/conftest.py` drops 1795 collected
        # to 1656 with `pave check` printing "All checks passed!" at exit 0 --
        # `pave check` defends the `pyproject.toml` route (`-o addopts=`, and it
        # fails on any `deselected` count) but non-collection is neither. And
        # eight lines of `pytest_runtest_makereport` hookwrapper report the EXACT
        # honest count of 1795 with a G1 pin genuinely failing.
        #
        # **Five entry points, not two.** The first version named
        # `tests/conftest.py` and `pyproject.toml` -- the two the plant used --
        # and the Platform seat measured three equivalents at zero keys: a
        # repo-ROOT `conftest.py` (an ancestor of both testpaths, so its
        # hookwrapper applies to every item, 1814 passed with a G1 pin red), a
        # new `pave/tests/conftest.py` (`collect_ignore` dropping the two-key
        # mechanism's own test, 1743 passed), and a root `pytest.ini` (higher
        # precedence than `[tool.pytest.ini_options]`, 1734 passed), and
        # `.pytest.ini`, which outranks every name above it -- pytest prints
        # "ignoring pytest config in pyproject.toml" and `-o addopts=` does not
        # clear its `testpaths`, so two lines took the suite to 47 with
        # `pave check` still PASS at exit 0. `tox.ini` and `setup.cfg` are the
        # same precedence chain and are included rather than measured.
        #
        # **This enumeration is a DENYLIST and cannot be complete.** Six entry
        # points were found by three seats across two rounds, each after the
        # previous fix. The structural answer is ADR-042 decision 3's -- the
        # deciding instance must not be a pytest at all -- and it is recorded as
        # owed rather than claimed here.
        #
        # **Honest limit (ADR-043 decision 3):** a key makes that COLLECTABLE, not
        # red. A harness that rewrites its own reports can report anything and no
        # count sees it. Stated here and in the ADR rather than left to be
        # discovered a second time.
        "the test harness — a file that can decide what the suite reports",
        re.compile(r"^((.*/)?conftest\.py|pyproject\.toml|\.?pytest\.ini|tox\.ini|setup\.cfg)$"),
        ("platform-eng", "security"),
    ),
    # --- ADR-044: the instruments that measure, and were guarded by nothing ---
    #
    # Found by two seats independently in the SPEC/05 round-4 review, by planting
    # against `main`, and in none of that review's own twenty-one pre-flight
    # findings. ADR-035's shape a third time: the thermometer protected and the
    # thermostat not.
    Rule(
        # **The files that decide what "correct" means for the eval plane.**
        # `tests/test_contracts.py` is cited by four modules as "the file that
        # pins X" (`evals/adversarial.py:37,292`, `platform/gateway/core/audit.py:256`,
        # `platform/gateway/core/guardrail.py:200`,
        # `quality/adversarial/g4-semantics.yaml:66,488`) and collected no key.
        #
        # Measured on 6af17d2, one diff: delete `test_golden_set_keeps_headroom`
        # (the repository's ONLY headroom check), flip both `expect_near_threshold`
        # cases to false, and delete `test_a_disposition_is_all_or_nothing` --
        # **1859 passed, zero failures, zero keys**. The same file holds the only
        # assertion that a publish-class tool declares an approver, and the
        # assertion that `.github/CODEOWNERS` and this module's rule list agree,
        # which CLAUDE.md names as what makes the next drift "a red check rather
        # than a fourth discovery".
        #
        # `ai-quality` because these are its instruments; `platform-eng` because
        # it owns the mechanism. **That pair is byte-identical to the seat set on
        # this very module** (`pave/twokey.py`), so the two seats could delete
        # this rule and the checks it guards in one diff using the dispositions
        # they already sign -- measured at 1879 passed. What stops that is the
        # pin in `tests/test_twokey_seats.py`, which turns that diff red and is
        # itself five-key. A third seat here would tax every routine eval change
        # to buy a property the pin already buys.
        "the eval-plane instruments — the files that decide what a golden case, a "
        "judge and a corpus draw must satisfy",
        re.compile(r"^tests/(test_contracts|test_calibration_corpus|test_judge)\.py$"),
        ("ai-quality", "platform-eng"),
    ),
    Rule(
        # **The files that catch a change to what the gateway records and what a
        # block means.** All three collected no key.
        #
        #   - `tests/test_tool_loop.py` is one of the four files that fire when
        #     `POLICY_MECHANISMS` is widened (20 failed across four files plus the
        #     instrument digest); two of those four were on no rule at all.
        #   - `tests/test_gateway_core.py:283` is the repository's ONLY live
        #     witness that G5 refuses `sensitive` by design rather than by the
        #     index comparison happening to agree -- deleting `classify.py`'s
        #     dedicated short-circuit leaves every other classification assertion
        #     green.
        #   - `tests/test_gateway_run_parity.py` pins the governed and ungoverned
        #     arms against each other. Measured: deleting it and rewording
        #     `gateway_client.py`'s `user_turn` together is **1862 passed, zero
        #     keys** -- and `user_turn` composes the wire text of every governed
        #     adversarial observation, which no instrument digest covers.
        #
        # `security` rather than `ai-quality`: what these three defend is G4's
        # "something blocked" and G5's refusal, not a scoring threshold.
        "the record-and-refusal instruments — what the gateway is observed to have "
        "done, and the parity between the governed and ungoverned arms",
        re.compile(r"^tests/(test_tool_loop|test_gateway_core|test_gateway_run_parity)\.py$"),
        ("platform-eng", "security"),
    ),
)


@dataclass(frozen=True)
class Attestation:
    seats: frozenset[str]
    rationale: str
    adr: str | None


#: The gate must not read what the rendered page does not show.
#:
#: An attestation a reviewer cannot see satisfies the machine and shows a human
#: nothing, which defeats the half of G9 this module exists for -- the docstring
#: above says the point is "a written reason attached to the diff forever".
#: Measured before any of this was stripped: three dispositions and a rationale
#: inside `<!-- ... -->`, with the visible body reading "Docs typo fix", accepted.
#:
#: This is the CLASS and not the instance, because an earlier attempt at it fixed
#: one string and was defeated by deleting three characters. An UNTERMINATED
#: `<!--` is HTML block type 2: it runs to the end of the document and hides
#: everything after it, while a regex demanding `-->` strips nothing. `<script>`
#: and `<style>` are dropped whole by GitHub's sanitiser. A fenced block renders
#: as a SAMPLE of an attestation rather than as one, which is how a pasted diff
#: hunk smuggled a live disposition in as a context line -- a diff context line
#: begins with a space, and the anchors above used to allow leading whitespace.
#:
#: A hidden span is replaced by NOTHING, because that is what the renderer does
#: to it. An earlier draft replaced it with the newlines it contained, reasoning
#: that collapsing might pull a following line up and move an honest attestation
#: off column 0. The deletability audit found that choice undefended, and writing
#: the missing test found the reasoning backwards:
#:
#:     x<!--
#:     c
#:     -->Two-Key-Disposition: security
#:
#: renders as the single line `xTwo-Key-Disposition: security`, and the
#: newline-preserving form rewrote it into a clean column-0 attestation that the
#: gate accepted. Preserving structure the reader never sees MANUFACTURES an
#: attestation out of hidden markup, which is this function's own defect
#: appearing inside the function written to close it. Measured against the
#: committed corpus: collapsing changes how none of the 36 merged bodies reads.
#: ORDER IS LOAD-BEARING. Code comes out first, because text inside a fence or a
#: backtick span is not markup and a renderer never treats it as such. Getting
#: this backwards is not theoretical: THIS PR's own body, explaining that an
#: unterminated `<!--` hides the rest of a document, contains the characters
#: `<!--` inside a backtick span — and the comment pattern's `\Z` fallback ate
#: everything after it, attestations included. The gate refused the PR that fixes
#: the gate, and running the gate over its own body is the only reason that was
#: found before it merged rather than after.
HIDDEN_PATTERNS = (
    re.compile(r"^```.*?(?:^```|\Z)", re.DOTALL | re.MULTILINE),
    re.compile(r"^~~~.*?(?:^~~~|\Z)", re.DOTALL | re.MULTILINE),
    re.compile(r"`+[^`\n]*`+"),
    re.compile(r"<!--(?:.*?-->|.*\Z)", re.DOTALL),
    # `<script>` and `<style>` require their CLOSING tag, and the `|\Z` fallback
    # the comment pattern needs is deliberately absent here. An unterminated
    # `<!--` is HTML block type 2 and really does hide the rest of the document;
    # an unterminated `<script>` does not — GitHub's sanitiser drops the tag and
    # renders what follows. With `|\Z` this pattern ate everything after the
    # first mention of the tag, and THIS PR's own body mentions it in prose,
    # inside backticks, while explaining the rule. Running the gate over its own
    # PR body is what found it: the gate refused the PR that fixes the gate.
    re.compile(r"<script\b.*?</script>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<style\b.*?</style>", re.DOTALL | re.IGNORECASE),
)


def visible(body: str) -> str:
    r"""The PR body with everything a reader cannot see removed.

    **Line endings are normalised first, and that is not cosmetic.** A PR body
    written in the GitHub web editor arrives over the webhook with CRLF; one sent
    by `gh pr create --body-file` arrives with LF. The anchors above were
    tightened to column 0 to stop a diff context line counting as an attestation,
    and `[ \t]` does not match `\r` where `\s` did -- so without this line the
    tightening blinds the gate to every body typed in a browser. Measured against
    the committed corpus of all 36 merged PR bodies that MENTION an attestation --
    35 of which carry one a reader can see, the 36th quoting the gate's own error
    message: **6 are CRLF, including the two most recent**, and every one of them
    parses to zero seats without this normalisation.

    That defect was found by a seat and not by its author, who had measured the
    same 36 bodies after reading them into normalised text. The corpus is
    committed as bytes now, in `fixtures/pr_bodies.json`, so the measurement and
    the gate see the same thing.
    """
    text = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    for pattern in HIDDEN_PATTERNS:
        text = pattern.sub("", text)
    return text


def parse(body: str) -> Attestation:
    body = visible(body)
    seats = {m.group("seat") for m in DISPOSITION_RE.finditer(body)}
    # Rationales may wrap across lines; collapse each to a single line so a
    # multi-line reason is not read as several short ones.
    parts = [" ".join(m.group("text").split()) for m in RATIONALE_RE.finditer(body)]
    adr_match = ADR_RE.search(body)
    return Attestation(frozenset(seats), " ".join(parts).strip(), adr_match.group("ref") if adr_match else None)


def normalize_paths(changed: Sequence[str]) -> list[str]:
    """Repo-relative, forward-slashed. Shared so the ADR-membership check and
    `triggered` cannot disagree about what a path is."""
    # NOT `lstrip("./")`: lstrip strips a character SET, so it eats the leading
    # dot of `.github/workflows/quality-gate.yml` and every gate-criteria change
    # silently stops matching. A path that fails to match here skips the check
    # entirely, which is the one failure mode this module cannot afford.
    out = []
    for p in changed:
        p = p.replace("\\", "/")
        out.append(p[2:] if p.startswith("./") else p)
    return out


def triggered(changed: Sequence[str]) -> list[tuple[Rule, list[str]]]:
    """Which two-key rules the diff touches, and the files that touched them."""
    normalized = normalize_paths(changed)
    hits = []
    for rule in RULES:
        matched = [p for p in normalized if rule.pattern.search(p)]
        if matched:
            hits.append((rule, matched))
    return hits


def evaluate(changed: Sequence[str], body: str, repo_root=None,
             base: str | None = None, head: str | None = None) -> list[str]:
    """Returns the reasons this PR is blocked. Empty list means it may merge.

    `base` and `head` are the PR's endpoints. `two-key.yml` already computes both
    to build the changed-file list, and `pave gate history --base` already takes
    one, so the interface they arrive through is one that existed before this
    change.
    """
    hits = triggered(changed)
    if not hits:
        return []

    att = parse(body)
    problems = []
    adr_rules_hit = sum(1 for rule, _ in hits if rule.requires_adr)
    records, adr_defects = adr_records(repo_root, base, head, changed)

    # The `ADR:` line no longer discharges anything, and that is the whole of this
    # change. It stays in the body for a reader; the gate stops ruling on it.
    #
    # Replayed against all 57 merged PRs through the corpus the gate actually
    # reads -- the PR BODY, which is not the commit message an earlier
    # measurement used -- 18 owe an ADR, and requiring one CITATION per rule
    # refuses 8 of them, three of which `main` accepted. PR #28 wrote three
    # decision records and cited one; #41 wrote two and cited one. The gate never
    # checked WHICH ADR discharges which rule -- that binding was measured and
    # refused, because it turns away 9 of 17 honest commit x rule pairs -- so the
    # citation was bookkeeping the gate could not verify, priced at two honest PRs.
    for rule, files in hits:
        missing = [s for s in rule.seats if s not in att.seats]
        if missing:
            problems.append(
                f"{rule.what}: changed {', '.join(sorted(files)[:3])}"
                f"{' …' if len(files) > 3 else ''} — missing disposition from "
                f"{', '.join(missing)}. Add `Two-Key-Disposition: <seat>` to the PR body."
            )
        if rule.requires_adr:
            if not base:
                # Fail closed. Without the base commit this cannot tell a decision
                # record from a trailing newline, and a check that quietly
                # downgrades when an argument goes missing is the shape this
                # module exists to refuse.
                problems.append(
                    f"{rule.what}: requires an ADR, and this run was given no base commit "
                    f"to compare against, so no ADR can be verified. Pass `--base <sha>` "
                    f"(the workflow does)."
                )
            elif len(records) < adr_rules_hit:
                have = ", ".join(f"`{r}`" for r in records) if records else "none"
                problems.append(
                    f"{rule.what}: this PR triggers {adr_rules_hit} rule(s) that each require "
                    f"an ADR and writes {len(records)} ({have}). One decision record cannot "
                    f"stand for several controls — write the ADR for this control, in this "
                    f"diff. An ADR this diff does not add reasoning to is not a record of it."
                )

    # Named once, after the loop, never once per rule: two ADR rules used to
    # print the identical near-miss twice in one refusal.
    #
    # **Only when a rule actually requires an ADR.** `adr_records` runs on every
    # gated PR, so without this guard a near-miss was reported for a rule that
    # was never invoked: an honest one-line copy-edit to an existing ADR,
    # bundled with an `evals/comparators.json` change that owes no ADR at all,
    # came back BLOCKED. That is the same false-refusal shape as the `is_file()`
    # leftover deleted eleven lines below -- a rewrite moved the reporting out of
    # the rule loop to dedupe it, and the guard stayed behind.
    # **Only when the count is actually SHORT.** A near-miss is an explanation
    # for a refusal, not a refusal of its own: it tells an author which candidate
    # failed to count when the PR is short of records. Once enough records exist
    # it is noise, and reporting it blocked this repository's OWN documented
    # convention -- `docs/adr/README.md` says superseded ADRs are marked, never
    # deleted, so writing a new record and appending `**Status:** ... superseded
    # by ADR-NNN.` to the old one is the shape the repo asks for. Measured: the
    # new record was found and counted, and the supersession mark blocked the PR
    # anyway.
    #
    # This is the third leftover of one class in this function -- a guard that
    # moved when the reporting moved, twice, and did not move the third time.
    if adr_rules_hit and len(records) < adr_rules_hit:
        problems.extend(dict.fromkeys(adr_defects))

    if problems:
        return problems

    # Seats are attested. Now the reasoning has to actually be reasoning.
    stripped = att.rationale.strip().rstrip(".").lower()
    if not att.rationale:
        problems.append(
            "disposition recorded with no rationale. Add `Two-Key-Rationale: <why>` — "
            "the written reason is the point of the second key, not the keyword."
        )
    elif (stripped in PLACEHOLDER_RATIONALES
          or len(substantive_words(att.rationale)) < MIN_SUBSTANTIVE_WORDS):
        # The message names the DEFECT, never the bar. The previous one said
        # "in at least 24 characters", which told the reader precisely how to
        # defeat it and nothing about what was wanted.
        problems.append(
            "rationale points at a reason instead of giving one. The second key's value "
            "is the written reasoning attached to THIS diff — a commit, a link or an "
            "issue number is where the reasoning lives, not the reasoning. Say which "
            "input moved, in which direction, and why that is correct, here in the body."
        )

    # The `ADR:` line is documentation for a reader and the gate does not rule on
    # it — see `adr_records`, which asks the diff instead. There used to be an
    # `is_file()` check here, left over from when the citation WAS the discharge,
    # and it survived the rewrite because that replaced the top of this function
    # and not its tail. It was live: a PR that wrote a genuine decision record was
    # refused because a stale path appeared somewhere else in its body. A rebase
    # is what surfaced it, not a test — so there is one now.
    return problems


def render(changed: Sequence[str], problems: Sequence[str],
           records: Sequence[str] = ()) -> str:
    hits = triggered(changed)
    if not hits:
        return "two-key: not required — this PR touches no two-key path"

    lines = ["two-key paths touched:"]
    for rule, files in hits:
        lines.append(f"  - {rule.what} [{', '.join(rule.seats)}]")
        lines.extend(f"      {f}" for f in sorted(files))

    if not problems:
        # Name the records. The residual this closes was stated in an earlier ADR
        # as "whether a stub is a decision record is a judgement about quality,
        # and that belongs to the reviewing seat" -- and the seat was told what
        # the gate accepted only when it REFUSED. A delegation with no channel.
        if records:
            lines.append("")
            lines.append("decision records this diff writes:")
            lines.extend(f"      {r}" for r in records)
        lines.append("\ntwo-key: SATISFIED — every owning seat disposed, with reasoning")
        return "\n".join(lines)

    lines.append("\ntwo-key: BLOCKED (G9)")
    lines.extend(f"  ✗ {p}" for p in problems)
    lines.append(
        "\nG9: whoever feels a control's pain never solely controls its strength.\n"
        "This is not a formality — a threshold or baseline change that cannot state\n"
        "its reasoning is the change this rule exists to stop."
    )
    return "\n".join(lines)
