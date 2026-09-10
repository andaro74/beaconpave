"""
The registry chain reader, and `rules/schema.json`'s two halves of G7.

**Claim 6's row 1a is this file's subject.** *A traceable chain, not a claimed
one*: a reader walks `rules/MER-AI-0001.yaml` -> `disposition.controls[].ref` ->
the pack -> the case -> the assert, **with no step supplied by hand**. The
temptation SPEC/09 constraint 7 tells the seat round to plant is a reader that
falls back to the pack's conventional path when a ref does not resolve, because
that makes a broken disposition render exactly like a working one — and then row
1a measures nothing at all.

**`rules/schema.json`'s two halves, and why only one of them can live in the
schema.**

*No immortal rules* is enforceable there and now is: `source.effective` is
required, so ADR-053's plant — `effective` deleted, `status: enforced`,
`review_by: "2099-01-01"`, measured at 2079 passed — is refused **by name at the
missing key**.

*No orphan rules* is not, because JSON Schema cannot resolve a path. ADR-053
recorded that the term had to be **defined** first, in one sense, or M07 would be
handed an obligation whose name meant two things and would close the cheap one.
The definition lives in the schema's `description`; `pave/rules.py::orphan_rules`
enforces that sentence; and the two are asserted below to say the same thing.

**A plant per sense**, which is what makes the definition load-bearing rather
than decorative:

- **the orphaning sense** — a control ref that does not resolve — is red, and the
  message says *orphan rule*;
- **the missing-fields sense** — a rule with no `owner_seat` — is also red, and
  its message must **not** say *orphan rule*. That second assertion is the one
  that proves the word stopped straddling: a term meaning two things lets the
  cheap half be closed while the expensive half is reported as done.

**Vacuity, stated rather than discovered.** `orphan_rules` bites on **no
committed rule today**: `MER-AI-0001`'s only control is an explicit reasoned
`no-control` record, which the schema names as a permitted disposition and which
is emphatically not orphaning. The check is exercised here on planted registries
under `tmp_path`, so the *test* is not vacuous even while the *live data* gives
it nothing to refuse — and it starts biting at the disposition PR, which is the
first time an enforcing ref exists. Recorded here because a check whose live
input cannot exercise it is one the deletability audit will report as silent, and
a reader should meet that fact in the file rather than in the audit table.

Hermetic (G8), zero model calls.

Owning seats: Legal/S&P (the registry) · Security (its counterweight) · Platform
Engineering (the mechanism).
"""
from __future__ import annotations

import json
import pathlib
import sys

import jsonschema
import pytest
import yaml

from pave import rules

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "rules"
SCHEMA = json.loads((REGISTRY / "schema.json").read_text(encoding="utf-8"))
COMMITTED = yaml.safe_load((REGISTRY / "MER-AI-0001.yaml").read_text(encoding="utf-8"))
PACK_REF = "services/highlights-agent/evals/disclosure/cases.yaml"

#: Steps that RECORD something about the disposition rather than being a link
#: of the walk: the rule's scope and its excluded sense, the revival condition,
#: and the disposition's limits. They are printed with the chain — a boundary a
#: reader does not meet is a boundary that is not recorded — and they do not
#: change what the walk reached.
ANNOTATIONS = ("scope", "excludes", "revives", "limit")


def _registry(tmp_path: pathlib.Path, rule: dict) -> pathlib.Path:
    directory = tmp_path / "rules"
    directory.mkdir(exist_ok=True)
    (directory / f"{rule['rule']}.yaml").write_text(
        yaml.safe_dump(rule, sort_keys=False), encoding="utf-8")
    return directory


def _disposed(ref: str = PACK_REF) -> dict:
    """The committed rule as the disposition PR will leave it: enforced, with an
    eval-pack control. Built here rather than committed, because PR 2 disposes
    nothing — the rule stays `proposed` until the run PR."""
    rule = json.loads(json.dumps(COMMITTED))
    rule["status"] = "enforced"
    rule["disposition"]["decided_by"] = "legal-sp"
    rule["disposition"]["controls"] = [
        {"type": "eval_pack", "ref": ref, "layer": "L3"}]
    return rule


# --- no immortal rules --------------------------------------------------------

def test_source_effective_is_required_by_the_schema():
    assert "effective" in SCHEMA["properties"]["source"]["required"]


def test_adr_053s_own_plant_is_refused_by_name():
    """**The plant ADR-053 measured, verbatim**: `effective` deleted,
    `status: enforced`, `review_by: "2099-01-01"` — a literally immortal enforced
    rule, green at 2079 passed. It is now refused, and the refusal names the
    field."""
    plant = json.loads(json.dumps(COMMITTED))
    del plant["source"]["effective"]
    plant["status"] = "enforced"
    plant["review_by"] = "2099-01-01"
    with pytest.raises(jsonschema.ValidationError) as exc:
        jsonschema.validate(plant, SCHEMA)
    assert "effective" in str(exc.value), (
        f"the plant is refused but not by name: {exc.value.message}. A refusal that does "
        "not say which field is missing sends the next reader to the wrong place.")


def test_the_committed_registry_still_validates():
    """The requirement may not be one the committed registry fails — a schema
    that refuses its own data is a red check nobody can act on."""
    jsonschema.validate(COMMITTED, SCHEMA)
    assert COMMITTED["source"]["effective"] == "2026-10-01"


def test_the_enforced_clock_exemption_is_recorded_as_still_open():
    """**Named rather than closed quietly.**

    Requiring `effective` shuts the omit-the-field door. It does not shut the
    other one ADR-053 named: `tests/test_contracts.py`'s review-by assertion is
    guarded `rule["status"] != "enforced"`, so an *enforced* rule may still carry
    a distant `review_by`. Bounding that needs a horizon Legal/S&P chooses, and
    inventing one here would be this repository's own *"a remedy built against
    the plant you were shown"*.

    Asserted as a live gap so that nobody reads *no immortal rules* as fully
    discharged, and so the day it IS closed this test is what says so."""
    still_immortal = json.loads(json.dumps(COMMITTED))
    still_immortal["status"] = "enforced"
    still_immortal["review_by"] = "2099-01-01"
    jsonschema.validate(still_immortal, SCHEMA)  # the schema permits it
    text = (REGISTRY / "schema.json").read_text(encoding="utf-8")
    assert "exempts `status: enforced`" in text, (
        "the schema no longer records that the enforced-clock door is open. Either it "
        "was closed — update this test in that diff — or the admission was dropped, "
        "which leaves a stated protection that is absent.")


# --- no orphan rules, in one sense --------------------------------------------

def test_the_schema_and_the_check_state_the_same_definition():
    """One sense, in both places. ADR-053's owe was the definition before the
    build, and a definition in the schema that the check does not implement is
    two senses with extra steps."""
    schema_text = SCHEMA["description"]
    check_text = rules.orphan_rules.__doc__
    for phrase in ("enforcing control", "no-control", "does not resolve"):
        assert phrase in schema_text, f"the schema's definition omits {phrase!r}"
        assert phrase in check_text, f"the check's docstring omits {phrase!r}"
    assert "orphan" in schema_text.lower() and "orphan" in check_text.lower()


def test_the_orphaning_sense_is_red_and_named(tmp_path):
    """Sense one: the rule is written down, the control is named, the control is
    not there."""
    directory = _registry(tmp_path, _disposed("services/highlights-agent/evals/nope.yaml"))
    problems = rules.orphan_rules(directory, ROOT)
    assert len(problems) == 1
    assert "orphan rule" in problems[0] and "nope.yaml" in problems[0]


def test_the_missing_fields_sense_is_red_but_is_not_called_orphaning(tmp_path):
    """**The assertion that proves the word stopped meaning two things.**

    A rule with no owner is refused — by the schema's `required`, which is where
    that sense belongs — and the refusal does **not** say *orphan rule*. If both
    senses answered to one word, closing the cheap half would let the expensive
    half be reported as done, which is precisely the inheritance ADR-053 refused
    to hand M07."""
    plant = json.loads(json.dumps(COMMITTED))
    del plant["owner_seat"]
    with pytest.raises(jsonschema.ValidationError) as exc:
        jsonschema.validate(plant, SCHEMA)
    assert "owner_seat" in str(exc.value)
    assert "orphan" not in exc.value.message.lower(), (
        f"the missing-fields refusal calls itself orphaning: {exc.value.message}")
    # and the orphan check has nothing to say about it, because it is not that
    directory = _registry(tmp_path, _disposed())
    assert rules.orphan_rules(directory, ROOT) == []


def test_a_no_control_record_is_not_orphaning():
    """The committed rule's shape since M00a, and reading it as orphaning would
    refuse the very disposition the schema names as permitted — the honest
    *we have not enforced this yet* record."""
    assert rules.orphan_rules(REGISTRY, ROOT) == []
    assert rules.enforcing_controls(COMMITTED) == []


def test_a_ref_escaping_the_repository_does_not_resolve(tmp_path):
    """A ref that resolved outside the tree would make every rule non-orphaned by
    pointing away from it.

    **The target is created, and that is the whole of the fix.** The first version
    used `../../../etc/hosts`, which from this root resolves to a path that does
    not exist — so it measured *the file is not there* rather than *the guard
    refused it*, and deleting the containment check entirely was **silent at 4124
    passed** (Security seat, round 1). With the guard gone, a ref of
    `../../../pave/gate.py` — which does exist, outside the worktree — reported no
    orphan at all."""
    outside = tmp_path / "outside.yaml"
    outside.write_text("[]", encoding="utf-8")
    assert outside.exists() and ROOT.resolve() not in outside.resolve().parents, (
        "the plant is inside the tree, so it cannot exercise the containment guard")

    # A ref that climbs out of the root and lands on a file that IS there.
    import os
    escape = os.path.relpath(outside.resolve(), ROOT.resolve()).replace("\\", "/")
    assert escape.startswith(".."), escape
    assert not rules._resolves(escape, ROOT), (
        "a ref resolving to an existing path outside the repository root was accepted. "
        "Every rule can then be made non-orphaned by pointing away from the tree.")
    assert rules.orphan_rules(_registry(tmp_path, _disposed(escape)), ROOT), (
        "`orphan_rules` did not flag a control ref that escapes the tree")

    # and the in-tree control: a path that exists and does not escape
    assert rules._resolves(PACK_REF, ROOT)


def test_rules_validate_reports_both_halves(tmp_path, monkeypatch, capsys):
    """One command, both halves of G7. A validator that reported "valid" over a
    registry naming controls that are not there is the stated-protection-absent
    shape, one directory over from the empty-registry argument it already makes.

    **The banner is asserted AND the wiring is.** The first version of this
    checked only that the output said *no orphaned control refs* — so deleting
    the `orphan_rules` call from `rules_validate` left the banner intact and the
    mutation was **SILENT**. A check that reads the sentence a command prints
    about itself is measuring the sentence. The second assertion drives a real
    orphan through the command and requires it to die."""
    from pave import cli

    cli.rules_validate()
    assert "no orphaned control refs" in capsys.readouterr().out

    monkeypatch.setattr(cli.rules_mod, "orphan_rules",
                        lambda *a, **k: ["MER-AI-0001: orphan rule — planted"])
    with pytest.raises(SystemExit) as exc:
        cli.rules_validate()
    assert exc.value.code != 0
    captured = capsys.readouterr()
    # `_die` writes to stderr, so both streams are read: a check that looked only
    # at stdout would pass on a command that printed nothing at all.
    assert "orphan rule" in captured.out + captured.err, (
        "`rules_validate` no longer fails on an orphaned control ref — the command "
        "reports the registry valid over a rule naming a control that is not there.")


# --- the chain ----------------------------------------------------------------

def test_the_committed_rule_traces_as_far_as_it_goes_and_says_so():
    """PR 2 disposes nothing: the rule is `proposed` with a `no-control` record,
    so the walk stops at the control and reaches no case and no assert.

    **NOT RESOLVED, and exit 1.** A lookup that reported a resolved chain over
    the undisposed state would be reporting success over the very thing the
    milestone exists to change — and the first version of `Chain.resolved` did
    exactly that, because it asked only whether there were defects."""
    chain = rules.trace("MER-AI-0001", REGISTRY, ROOT)
    assert chain.rule is not None and not chain.defects
    assert not chain.resolved
    kinds = [s.kind for s in chain.steps if s.kind not in ANNOTATIONS]
    assert kinds == ["source", "owner", "control"]
    assert "NOT RESOLVED" in rules.render(chain)


def test_a_disposed_rule_walks_all_the_way_to_the_asserts(tmp_path):
    """The chain the disposition PR produces: rule -> control -> service -> every
    case -> the assert keys each carries. Every link read, none supplied."""
    directory = _registry(tmp_path, _disposed())
    chain = rules.trace("MER-AI-0001", directory, ROOT)
    assert chain.resolved, chain.defects
    kinds = [s.kind for s in chain.steps if s.kind not in ANNOTATIONS]
    assert kinds[:4] == ["source", "owner", "control", "binds"]
    cases = [s for s in chain.steps if s.kind == "case"]
    # Derived from the pack rather than pinned at a literal: round 1 added two
    # cases, and a hard-coded 5 would have made this test a number to bump rather
    # than a statement about the walk reaching every case.
    committed = yaml.safe_load(
        (ROOT / PACK_REF).read_text(encoding="utf-8"))
    assert len(cases) == len(committed) >= 5
    assert all("ai_disclosure" in s.detail for s in cases), [s.detail for s in cases]
    assert next(s for s in chain.steps if s.kind == "binds").ref == "highlights-agent"


def test_a_broken_ref_is_red_and_the_reader_supplies_no_step(tmp_path):
    """**SPEC/09 constraint 7's named plant.**

    A reader that fell back to the conventional pack path when `controls[].ref`
    did not resolve would render a broken disposition exactly like a working one.
    The chain must stop, name the ref, and reach **no case** — reaching cases from
    a ref that does not resolve is the reader supplying the step."""
    directory = _registry(tmp_path, _disposed("services/highlights-agent/evals/gone.yaml"))
    chain = rules.trace("MER-AI-0001", directory, ROOT)
    assert not chain.resolved
    assert chain.defects and "orphan rule" in chain.defects[0]
    assert not [s for s in chain.steps if s.kind == "case"], (
        "the reader reached cases through a ref that does not resolve — it supplied the "
        "step itself, which makes a broken disposition render like a working one")

    # **The RENDER must name the broken link, not merely report a broken chain.**
    # Stripping the `<--` marker, every step detail and every `[BROKEN]` line was
    # SILENT at 4124 passed (Security seat, round 1): the chain rendered as four
    # clean lines plus NOT RESOLVED, with no indication of which link failed. The
    # only assertions were `"gone.yaml" in render(...)`, which the control label
    # supplies regardless, and the trailer.
    rendered = rules.render(chain)
    assert "gone.yaml" in rendered
    assert "[BROKEN]" in rendered, (
        "the render no longer prints the defect line, so a reader is told the chain is "
        "broken and not where")
    assert "does not resolve" in rendered, "the failing step lost its detail"
    assert "<--" in rendered, "the marker that points at the failing step is gone"


def _planted_tree(tmp_path: pathlib.Path, pack: object | None, ref: str = PACK_REF) -> pathlib.Path:
    """A whole repository root under `tmp_path`, so a planted pack never touches
    committed bytes.

    `trace` takes its root as an argument precisely so this is possible. Writing a
    fixture into `tests/fixtures/` and deleting it in a `finally` would leave the
    working tree modified whenever a run is interrupted, which is the shape this
    repository has already paid for once."""
    target = tmp_path / "tree" / ref
    target.parent.mkdir(parents=True, exist_ok=True)
    if pack is not None:
        target.write_text(yaml.safe_dump(pack, sort_keys=False), encoding="utf-8")
    return tmp_path / "tree"


def _typed(kind: str, ref: str, layer: str = "L3") -> dict:
    rule = json.loads(json.dumps(COMMITTED))
    rule["status"] = "enforced"
    rule["disposition"]["decided_by"] = "legal-sp"
    rule["disposition"]["controls"] = [{"type": kind, "ref": ref, "layer": layer}]
    return rule


def test_an_enforcing_control_of_another_type_resolves_and_does_not_exit_one(tmp_path):
    """**Tool Owner, round 1 — dispatch on the declared TYPE, not the file
    extension.**

    The first version asked the filesystem what a control was. A `guardrail` or
    `cedar_policy` disposition — enforcing, correctly recorded — produced an
    unresolved step, so the chain read NOT RESOLVED with **zero defects** and
    `pave rules trace` exited 1. Adding a second, genuinely stronger control
    turned a chain that exits 0 into one that exits 1: **M09b would have made
    claim 6's own command red by strengthening the control it reports on.**"""
    root = _planted_tree(tmp_path, None)
    policy = root / "platform" / "gateway" / "policy" / "disclosure.cedar"
    policy.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text("forbid(principal, action, resource);", encoding="utf-8")
    directory = _registry(tmp_path, _typed(
        "cedar_policy", "platform/gateway/policy/disclosure.cedar", "L2"))
    chain = rules.trace("MER-AI-0001", directory, root)
    assert chain.resolved, chain.defects
    assert not chain.defects
    assert any(s.kind == "cedar_policy" for s in chain.steps)


def test_a_two_control_disposition_resolves(tmp_path):
    """The shape the committed rule's own header promises — the eval pack **and**
    the gateway guardrail — and the shape ADR-075 gives M09b."""
    root = _planted_tree(tmp_path, [{"id": "disclosure-101", "input": "x",
                                     "asserts": [{"ai_disclosure": {"required": ["AI"]}}]}])
    guard = root / "platform" / "gateway" / "policy" / "guardrail.json"
    guard.parent.mkdir(parents=True, exist_ok=True)
    guard.write_text("{}", encoding="utf-8")
    rule = _typed("eval_pack", PACK_REF)
    rule["disposition"]["controls"].append(
        {"type": "guardrail", "ref": "platform/gateway/policy/guardrail.json", "layer": "L1"})
    chain = rules.trace("MER-AI-0001", _registry(tmp_path, rule), root)
    assert chain.resolved, chain.defects
    assert [s.kind for s in chain.steps].count("case") == 1


def test_a_control_declared_one_type_and_pointing_at_another_is_red(tmp_path):
    """**The converse, and it is the worse half.**

    `type: cedar_policy` pointing at the eval pack reported `RESOLVED` at exit 0
    and printed the eval cases as the Cedar policy's chain — the `type` and
    `layer` enums decorative in the one reader that claims to walk them. That is
    G4's *a probe naming Cedar is not satisfied by a content filter*, one plane
    over: a registry lookup reporting a chain it did not walk."""
    root = _planted_tree(tmp_path, [{"id": "disclosure-101", "input": "x",
                                     "asserts": [{"ai_disclosure": {"required": ["AI"]}}]}])
    chain = rules.trace("MER-AI-0001", _registry(tmp_path, _typed(
        "cedar_policy", PACK_REF, "L2")), root)
    assert not chain.resolved
    assert any("declared" in d and "eval pack" in d for d in chain.defects), chain.defects
    assert not [s for s in chain.steps if s.kind == "case"], (
        "the reader printed eval cases as this control's chain")


def test_an_eval_pack_ref_that_is_not_a_case_file_is_red(tmp_path):
    """The mirror: declared an eval pack, and the artifact is a directory."""
    root = _planted_tree(tmp_path, None)
    (root / "services" / "highlights-agent" / "evals" / "disclosure").mkdir(
        parents=True, exist_ok=True)
    chain = rules.trace("MER-AI-0001", _registry(tmp_path, _typed(
        "eval_pack", "services/highlights-agent/evals/disclosure")), root)
    assert not chain.resolved
    assert any("is declared an eval pack and is not one" in d for d in chain.defects)


def test_binds_names_the_service_in_the_path_and_says_so_when_there_is_none(tmp_path):
    """**Tool Owner, round 1: `_binds` hard-coded to `highlights-agent` was
    invisible.** Every case used a `services/highlights-agent/...` ref, so a
    reader that guessed the only deployed service passed the whole file — the
    exact guess its own docstring refuses. Two refs it cannot guess from."""
    root = _planted_tree(tmp_path, [{"id": "disclosure-101", "input": "x",
                                     "asserts": [{"ai_disclosure": {"required": ["AI"]}}]}],
                         ref="services/other-svc/evals/disclosure/cases.yaml")
    chain = rules.trace("MER-AI-0001", _registry(tmp_path, _typed(
        "eval_pack", "services/other-svc/evals/disclosure/cases.yaml")), root)
    binds = [s for s in chain.steps if s.kind == "binds"]
    assert binds and binds[0].ref == "other-svc", [s.ref for s in binds]

    # and a ref that binds to no service says so rather than printing nothing
    root2 = _planted_tree(tmp_path / "b", [{"id": "d-1", "input": "x",
                                            "asserts": [{"ai_disclosure": {"required": ["AI"]}}]}],
                          ref="quality/packs/cases.yaml")
    chain2 = rules.trace("MER-AI-0001", _registry(tmp_path / "b", _typed(
        "eval_pack", "quality/packs/cases.yaml")), root2)
    stated = [s for s in chain2.steps if s.kind == "binds"]
    assert stated and "no service in this path" in stated[0].detail, (
        "a chain that binds to no service printed nothing about it, so a reader of the "
        "demo artifact cannot tell an absent binding from an unstated one")


def test_a_ref_that_resolves_to_an_empty_pack_is_red(tmp_path):
    """A pack with nothing in it satisfies every assertion about it — the
    vacuity one link below orphaning, caught separately so the diagnosis names
    the right link."""
    root = _planted_tree(tmp_path, [])
    directory = _registry(tmp_path, _disposed())
    chain = rules.trace("MER-AI-0001", directory, root)
    assert not chain.resolved
    assert any("holds no cases" in d for d in chain.defects), chain.defects


def test_a_case_with_no_asserts_is_red(tmp_path):
    """A case that asserts nothing passes every run, and a chain ending at it
    would report a control the rule does not have."""
    root = _planted_tree(tmp_path, [{"id": "disclosure-999", "input": "x"}])
    directory = _registry(tmp_path, _disposed())
    chain = rules.trace("MER-AI-0001", directory, root)
    assert not chain.resolved
    assert any("carries no asserts" in d for d in chain.defects), chain.defects


def test_an_unknown_rule_id_names_what_is_known(tmp_path):
    chain = rules.trace("MER-XX-9999", REGISTRY, ROOT)
    assert chain.rule is None and not chain.resolved
    assert "MER-AI-0001" in chain.defects[0]


# --- the command's exit codes -------------------------------------------------
#
# **Untested until round 1, and the omission has a name here.** ADR-047 recorded
# it — *"nothing exercised the CLI wrapper's exit codes (the exact gap that
# produced ADR-046's one silent mutation)"* — and a new subcommand reintroduced
# it: the Service Team seat made `rules trace` exit **0** on an unresolved chain,
# the precise failure `rules_trace`'s own docstring names as the reason the code
# exists, and measured **3926 passed**.

def _trace_exit(rule_id: str, registry=None) -> int:
    import subprocess
    return subprocess.run(
        [sys.executable, "-m", "pave.cli", "rules", "trace", rule_id],
        cwd=str(ROOT), capture_output=True, text=True).returncode


def test_a_resolved_chain_exits_zero(tmp_path, monkeypatch):
    """Driven through `rules_trace` rather than the subprocess, because the
    committed registry is undisposed until PR 4 and this is the branch that has
    no committed input yet."""
    from pave import cli

    directory = _registry(tmp_path, _disposed())
    # The REAL function, captured before patching. Binding the lambda to
    # `rules.trace` after patching `cli.rules_mod.trace` makes it call itself —
    # `cli.rules_mod` IS `pave.rules`, so the patch rebinds the name the lambda
    # resolves. RecursionError, and a test that cannot run is a test that cannot
    # refuse anything.
    real_trace = rules.trace
    monkeypatch.setattr(cli.rules_mod, "trace",
                        lambda *a, **k: real_trace("MER-AI-0001", directory, ROOT))
    with pytest.raises(SystemExit) as exc:
        cli.rules_trace(["MER-AI-0001"])
    assert exc.value.code == 0


def test_an_undisposed_rule_exits_one_and_says_it_is_by_design():
    """Exit 1 is right — the chain does not resolve — but the OUTPUT must let a
    reader tell "working as intended" from "broken". Today this is the only rule
    in the registry, so the command's success rate on real input is 0%, and a
    bare NOT RESOLVED reads as a defect in the command."""
    assert _trace_exit("MER-AI-0001") == 1
    rendered = rules.render(rules.trace("MER-AI-0001", REGISTRY, ROOT))
    assert "BY DESIGN" in rendered and "NOT RESOLVED" in rendered


def test_the_registry_carries_the_dispositions_limit_and_the_lookup_prints_it():
    """**A disposition records its own boundary, in the registry.**

    Tool Owner, round 1: an L3 eval pack asserts `ai_disclosure` on the agent's
    ANSWER, and the publish-class action that puts editorial copy in front of
    viewers carries `ai_generated` — not `required`, and measurably flippable to
    false with every semantic check green. The operator accepted the L3
    disposition as sufficient for claim 6 (which is about tracing a rule to a
    failing assert) and required the limit to live in the rule's own disposition
    record rather than only in the ADR, so the registry carries it.

    **And the lookup must print it**, or the registry carries a boundary the one
    command a reader runs does not show — which is a limit recorded and absent."""
    limits = (COMMITTED["disposition"] or {}).get("limits") or []
    assert limits, (
        "MER-AI-0001's disposition records no limit. The eval pack does not reach the "
        "publish path, and a disposition that does not say so reports itself complete.")
    limit = limits[0]
    assert "publish" in limit["limit"], limit["limit"]
    assert set(limit["owed_to"]) == {"tool-owner", "legal-sp"}, limit["owed_to"]
    assert limit["dated"].strip(), "an undated limit is a residual nobody inherits"

    rendered = rules.render(rules.trace("MER-AI-0001", REGISTRY, ROOT))
    assert "limit" in rendered and "publish-highlight" in rendered, (
        "the registry carries the limit and `pave rules trace` does not print it. A "
        "reader takes the lookup for the disposition.")
    assert "tool-owner" in rendered, "the render does not say who owes the limit"
    # The LIMIT's own lines, not every line: the `no-control` row carries a long
    # ref-plus-detail of its own, and asserting over the whole render would have
    # been a check about that row wearing this one's name.
    body = [ln for ln in rendered.splitlines() if ln.startswith(" " * 15)]
    assert body, "the limit's prose was not wrapped onto continuation lines"
    assert max(len(line) for line in body) < 100, (
        "a limit is prose a human has to read, and an unwrapped line is one nobody "
        "reads — printing it would be a gesture rather than a disclosure")


def test_a_recorded_limit_does_not_make_the_chain_unresolved(tmp_path):
    """A limit is a boundary, not a defect. A disposed rule that records one still
    resolves — otherwise recording the honest thing would make the lookup red and
    nobody would record it."""
    rule = _disposed()
    rule["disposition"]["limits"] = [
        {"limit": "does not reach the publish path", "owed_to": ["tool-owner"],
         "dated": "the next milestone"}]
    root = _planted_tree(tmp_path, [{"id": "disclosure-101", "input": "x",
                                     "asserts": [{"ai_disclosure": {"required": ["AI"]}}]}])
    chain = rules.trace("MER-AI-0001", _registry(tmp_path, rule), root)
    assert chain.resolved, chain.defects
    assert any(s.kind == "limit" for s in chain.steps)


def test_the_cli_emits_the_readers_render_and_does_not_rewrite_it(capsys):
    """**The keyed reader is only worth its keys if the CLI defers to it.**

    `pave/cli.py` is deliberately on no rule (ADR-041 decision 7), and the whole
    justification is that the criteria live in `pave/rules.py` where a seat's key
    reaches them. Nothing asserted the twelve unkeyed lines actually *print what
    the reader returned*: the Security seat rewrote `NOT RESOLVED` to `RESOLVED`
    and exited 0 inside `rules_trace`, at **4124 passed** — ADR-052 round 2's
    attack on `twokey.adr_records`, one command over.

    Byte-identical, so a CLI that "helpfully" reformats is also caught."""
    from pave import cli

    with pytest.raises(SystemExit):
        cli.rules_trace(["MER-AI-0001"])
    printed = capsys.readouterr().out
    expected = rules.render(rules.trace("MER-AI-0001", REGISTRY, ROOT))
    assert expected.strip() in printed, (
        "the CLI's output is not the reader's render. The deciding text is produced in "
        "an unkeyed file, which is the arrangement keying `pave/rules.py` was meant to "
        "prevent.")


def test_an_unknown_rule_id_exits_two_and_not_one():
    """A typo is a CONTRACT failure, not a quality result. Sharing exit 1 with a
    real orphan made "you mistyped the id" indistinguishable from "this rule's
    control is not there" — the gate's own split, one command over."""
    assert _trace_exit("MER-XX-9999") == 2


def test_an_empty_registry_is_a_failure_not_a_pass(tmp_path):
    """`rules/` is Legal/S&P's entire surface; a reader reporting success over
    zero files reports success after somebody deletes the directory."""
    empty = tmp_path / "rules"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        rules.load_registry(empty)
