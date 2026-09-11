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


#: `disposition.decided_by` as the registry carried it from M00a until PR 4 --
#: the state the `^unassigned\b` arm of the schema exists to keep sayable.
#: **A literal, not a read of the committed rule.** Every assertion in this file
#: that named the live registry's UNDISPOSED shape went red the moment PR 4
#: disposed it, which is a guard coupled to its own data rather than to the
#: property it names: the schema must accept an undisposed rule whether or not
#: this registry happens to hold one today.
UNDISPOSED_DECIDED_BY = "unassigned \u2014 logged by Legal/S&P, awaiting disposition"


def _undisposed() -> dict:
    """The committed rule as it stood BEFORE the disposition: `proposed`, with one
    explicit reasoned `no-control` record.

    Built here for the same reason `_disposed` was built here before PR 4 -- and
    the mirror image of it. PR 4 flipped the registry, so the branches that read
    the undisposed shape have to be planted or they stop being exercised at all;
    deleting them instead would retire the `no-control` walk, `BY DESIGN`, and the
    schema's `unassigned` arm together, in the diff that made them unreachable
    from the live data."""
    rule = json.loads(json.dumps(COMMITTED))
    rule["status"] = "proposed"
    rule["disposition"]["decided_by"] = UNDISPOSED_DECIDED_BY
    rule["disposition"]["decided_on"] = "2026-08-15"
    rule["disposition"]["controls"] = [
        {"type": "no-control",
         "ref": "none yet \u2014 the disposition PR replaces this with the L3 eval pack"}]
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


def test_a_no_control_record_is_not_orphaning(tmp_path):
    """Reading a `no-control` record as orphaning would refuse the very
    disposition the schema names as permitted — the honest *we have not enforced
    this yet* record MER-AI-0001 carried from M00a to M09 PR 4.

    **Planted, because PR 4 disposed the only rule in the registry.** Until then
    this read `enforcing_controls(COMMITTED) == []` off the live file, and the
    disposition made it red — the assertion was about this registry's state and
    not about the property. The property is that a `no-control` record is not an
    orphan, and it is now asserted on a rule that has one."""
    assert rules.enforcing_controls(_undisposed()) == [], (
        "a `no-control` record is being read as an enforcing control, so the honest "
        "undisposed record would be reported as an orphan rule")
    assert rules.orphan_rules(_registry(tmp_path, _undisposed()), ROOT) == []


def test_the_committed_rules_enforcing_control_resolves_and_is_not_an_orphan():
    """The other side of the same coin, on the live registry after PR 4.

    `orphan_rules` bit on nothing while the only rule carried a `no-control`
    record — this file's own module docstring recorded that vacuity and dated its
    end to *"the disposition PR, which is the first time an enforcing ref
    exists."* This is that assertion: the ref is enforcing, it resolves, and the
    check that would refuse it has live input at last."""
    controls = rules.enforcing_controls(COMMITTED)
    assert [c["type"] for c in controls] == ["eval_pack"], controls
    assert controls[0]["ref"] == PACK_REF and controls[0]["layer"] == "L3", controls[0]
    assert rules._resolves(controls[0]["ref"], ROOT), (
        f"the disposition names {controls[0]['ref']!r} and it does not resolve in this "
        "tree — a named control that is not there is the orphan-rule shape")
    assert rules.orphan_rules(REGISTRY, ROOT) == []


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

def test_the_undisposed_rule_traces_as_far_as_it_goes_and_says_so(tmp_path):
    """The walk over a `proposed` rule whose only record is `no-control`: it stops
    at the control and reaches no case and no assert.

    **NOT RESOLVED, and exit 1.** A lookup that reported a resolved chain over
    the undisposed state would be reporting success over the very thing the
    milestone exists to change — and the first version of `Chain.resolved` did
    exactly that, because it asked only whether there were defects.

    **Planted at PR 4**, where it had read the committed registry. The rule is
    disposed now, so reading it live would assert the opposite of what the file
    says; the branch is the thing worth keeping, and it needs a rule in that state
    to walk."""
    chain = rules.trace("MER-AI-0001", _registry(tmp_path, _undisposed()), ROOT)
    assert chain.rule is not None and not chain.defects
    assert not chain.resolved
    kinds = [s.kind for s in chain.steps if s.kind not in ANNOTATIONS]
    assert kinds == ["source", "owner", "control"]
    assert "NOT RESOLVED" in rules.render(chain)


def test_the_committed_rule_traces_from_the_rule_to_its_asserts():
    """**Row 1a, over the real record.** The chain reader run on the registry as
    PR 4 disposed it, with no step supplied by hand and no planted fixture: rule ->
    `disposition.controls[].ref` -> a file that exists -> every case -> the assert
    keys each carries.

    This is the assertion the plan-walk table dates to PR 4 (*"a test walking
    `disposition.controls[].ref` to a file that exists"*), and it is the one
    reading in this file that would have been vacuous before the disposition and
    is not now.

    **And it reads ADR-075 decision 3's requirement off the render**, because that
    decision says the disposition must *"say plainly which service and which
    surface the rule binds"*: the service comes from the control's path and the
    surface from the `scope` record PR 2 wrote, and a reader of `pave rules trace`
    must meet both."""
    chain = rules.trace("MER-AI-0001", REGISTRY, ROOT)
    assert chain.rule is not None and not chain.defects, chain.defects
    assert chain.resolved, "the committed disposition does not walk to an assert"
    kinds = [s.kind for s in chain.steps if s.kind not in ANNOTATIONS]
    assert kinds[:4] == ["source", "owner", "control", "binds"], kinds

    committed_cases = yaml.safe_load((ROOT / PACK_REF).read_text(encoding="utf-8"))
    cases = [s for s in chain.steps if s.kind == "case"]
    assert len(cases) == len(committed_cases) >= 5, (
        f"the walk reached {len(cases)} of the pack's {len(committed_cases)} cases")
    assert all("ai_disclosure" in s.detail for s in cases), [s.detail for s in cases]

    rendered = rules.render(chain)
    assert "chain: RESOLVED" in rendered and "NOT RESOLVED" not in rendered
    # The service, named by the disposition rather than inferred by the reader.
    assert next(s for s in chain.steps if s.kind == "binds").ref == "highlights-agent"
    assert "highlights-agent" in rendered
    # The surface, named by the scope record the same lookup prints.
    assert "editorial copy" in rendered and "previews" in rendered, (
        "the lookup does not print the surface the rule binds, so a reader of the "
        "disposition meets the service and not what it covers (ADR-075 decision 3)")
    assert "status enforced" in rendered


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
    # **WALKED, the third state.** Not a defect — the control is enforcing and
    # correctly recorded, and `pave rules trace` exits 0 — and not RESOLVED
    # either, because the walk reached no case and no assert. Round 2 pulled this
    # both ways: Tool Owner refused a chain that exits 1 on a stronger control,
    # Platform Engineering refused a RESOLVED that never reached an assert.
    assert not chain.defects
    assert chain.walked and not chain.resolved
    assert any(s.kind == "cedar_policy" for s in chain.steps)
    assert "WALKED" in rules.render(chain)


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
    # An eval pack that reaches its asserts, PLUS a guardrail the reader cannot
    # follow: WALKED, because one control short of a full walk is not a full walk.
    assert not chain.defects
    assert chain.walked and not chain.resolved
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
    # The artifact check fires first now: a `cedar_policy` ref under `services/`
    # is not a Cedar policy, whatever it parses as. The defect names the declared
    # type and where that type's artifact lives.
    assert any("declared 'cedar_policy'" in d for d in chain.defects), chain.defects
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
    assert any("declared 'eval_pack'" in d for d in chain.defects), chain.defects


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
    """Driven through `rules_trace` rather than the subprocess, over a PLANTED
    disposed registry.

    It was written this way because the committed registry was undisposed and this
    branch had no committed input. PR 4 gave it one, and the planted form is kept
    rather than replaced: `test_the_committed_command_exits_zero_over_the_real_record`
    below is the subprocess reading over the live file, and this one keeps the
    branch exercised on a registry that is not this repository's, so the day the
    live rule is retired the exit-0 path still has a test."""
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


def test_an_undisposed_rule_exits_one_and_says_it_is_by_design(tmp_path, monkeypatch):
    """Exit 1 is right — the chain does not resolve — but the OUTPUT must let a
    reader tell "working as intended" from "broken". While MER-AI-0001 was the
    only rule in the registry the command's success rate on real input was 0%, and
    a bare NOT RESOLVED read as a defect in the command.

    **Planted at PR 4, in the diff that ended that state.** This read the live
    registry and asserted exit 1; the disposition makes the live answer 0, so the
    reading moved to a rule in the state the assertion is about. Deleting it
    instead would have retired `BY DESIGN` — the whole of the distinction — in the
    diff that made it unreachable from committed data, which is this milestone's
    own *stated and absent* shape."""
    from pave import cli

    directory = _registry(tmp_path, _undisposed())
    real_trace = rules.trace
    monkeypatch.setattr(cli.rules_mod, "trace",
                        lambda *a, **k: real_trace("MER-AI-0001", directory, ROOT))
    with pytest.raises(SystemExit) as exc:
        cli.rules_trace(["MER-AI-0001"])
    assert exc.value.code == 1
    rendered = rules.render(real_trace("MER-AI-0001", directory, ROOT))
    assert "BY DESIGN" in rendered and "NOT RESOLVED" in rendered


def test_the_committed_command_exits_zero_over_the_real_record():
    """**The demo artifact's first command, run against the disposed registry.**

    `python -m pave.cli rules trace MER-AI-0001` in a subprocess — the real
    command, the real file, no monkeypatch and no `tmp_path`. Until PR 4 this
    command exited 1 on every input this repository had, and SPEC/09's *Demo
    artifact* section published that as correct-for-now. This is the reading that
    retires that sentence.

    The subprocess matters: `test_a_resolved_chain_exits_zero` drives
    `cli.rules_trace` in-process over a planted registry, so it cannot catch a
    module-level failure — an import error, a missing dependency, a `__main__`
    dispatch that never reaches the subcommand. This is the one assertion in the
    file that the demo command actually runs."""
    import subprocess

    completed = subprocess.run(
        [sys.executable, "-m", "pave.cli", "rules", "trace", "MER-AI-0001"],
        cwd=str(ROOT), capture_output=True, text=True)
    assert completed.returncode == 0, (
        f"`pave rules trace MER-AI-0001` exited {completed.returncode} over the "
        f"committed registry. MER-AI-0001 is disposed: a resolved chain exits 0, and "
        f"claim 6's own demo command going red is the failure mode the WALKED state "
        f"was introduced to avoid.\n{completed.stdout}\n{completed.stderr}")
    assert "chain: RESOLVED" in completed.stdout, completed.stdout


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


# --- guards that another guard was answering for ------------------------------
#
# Five checks in `pave/rules.py` and two in `rules/schema.json` deleted in silence
# in the deletability audit. Every one is a round-1 or round-2 remedy: the seat's
# plant proved the defect, the fix went in, and the fix was treated as its own
# witness. Where a guard looked tested, it was being answered for by the guard
# beside it -- `_resolves`' containment check is invisible because the byte-for-byte
# comparison after it raises `ValueError` on an escaping path and returns False
# anyway.

def test_the_repository_root_is_not_a_control():
    """`ref: "."` exists, is contained, and discharged every rule.

    The escape test above covers `../../etc/passwd`; this is the other direction
    and the containment line carries both. Removing that line leaves the escape
    test green -- the byte comparison below it raises `ValueError` on a path
    outside the root and returns False -- so `.` is what actually measures it."""
    for ref in (".", "./", "", "/"):
        assert not rules._resolves(ref, ROOT), (
            f"{ref!r} resolves as a control ref. A control that is 'the whole "
            f"repository' discharges every rule in the registry at once.")


def test_a_ref_that_is_not_the_path_it_names_does_not_resolve():
    """**Against the committed tree, not the filesystem.**

    `services/.../disclosure/../disclosure/cases.yaml` resolves to a real file and
    `exists()` says yes, but it is not a path in the tree -- and on a
    case-insensitive checkout neither is `SERVICES/.../CASES.YAML`, which is why
    *no orphan rules* meant two different things on Windows and on Linux CI. The
    `..`-traversing form is the one that measures the same on both."""
    pack = pathlib.Path(PACK_REF)
    detour = (pack.parent / ".." / pack.parent.name / pack.name).as_posix()
    assert (ROOT / detour).exists(), "the fixture path is wrong, not the check"
    assert not rules._resolves(detour, ROOT), (
        f"{detour!r} resolved. It names a file that is there by a route that is "
        f"not in the tree; a registry that accepts it cannot be re-derived from "
        f"a checkout.")
    assert rules._resolves(PACK_REF, ROOT), "the plain path must still resolve"


def test_a_control_type_outside_the_schemas_enum_is_red(tmp_path):
    """**Tool Owner, round 2 -- and the fix was itself unexercised.**

    `test_a_control_declared_one_type_and_pointing_at_another_is_red` covers a
    type IN the enum pointing at the wrong artifact. A type the schema does not
    permit takes a different branch: `CONTROL_ARTIFACTS.get` returns no home, the
    artifact check is skipped, and the control reads as enforcing and resolved.
    `type: human-review` and `type: no_control` (an underscore for the hyphen)
    both walked clean."""
    (tmp_path / "ok").mkdir()
    control = _typed("eval_pack", PACK_REF)
    clean = rules.trace(control["rule"], _registry(tmp_path / "ok", control),
                        _planted_tree(tmp_path / "ok",
                                      [{"id": "d-1", "asserts": [{"x": 1}]}]))
    assert clean.resolved and not clean.defects, "the fixture is wrong, not the check"

    # **The ref must NOT be an eval pack.** With the enum check disabled a
    # pack-shaped ref takes the `looks_like_pack` branch, which appends a defect
    # naming the same `kind` -- so the first version of this test passed under the
    # mutation for a reason that was not the enum. `classify.py` is a real file,
    # is not a pack, and is not the artifact home of any permitted type, so the
    # enum branch is the only thing that can refuse it.
    for kind in ("human-review", "no_control", "guardrail_v2"):
        rule = _typed(kind, "platform/gateway/core/classify.py")
        planted = tmp_path / kind
        planted.mkdir()
        tree = _planted_tree(planted, [{"id": "d-1", "asserts": [{"x": 1}]}])
        target = tree / "platform" / "gateway" / "core" / "classify.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("SENSITIVE_TERMS = ()\n", encoding="utf-8")
        chain = rules.trace(rule["rule"], _registry(planted, rule), tree)
        # **The DEFECT, not `resolved`.** `resolved` is False for any non-pack
        # control -- the walk reaches no case and no assert -- so asserting it
        # here passes whether or not the type was ever checked, and the
        # deletability audit measured exactly that: `if kind not in
        # _control_types():` -> `if False:` left the suite at 4184. A test that
        # passes because of the line next to the one it names is this
        # amendment's whole subject, written into the test closing it.
        assert chain.defects, (
            f"a control of type {kind!r} -- which `rules/schema.json` does not "
            f"permit -- produced no defect. A control the registry cannot name is "
            f"not a control it can be said to have.")
        assert any(kind in defect for defect in chain.defects), (
            f"the chain does not say that {kind!r} is the problem: {chain.defects}")
        assert not chain.resolved


def test_a_pack_that_is_not_a_list_and_a_case_with_no_id_are_both_red(tmp_path):
    """`_pack_cases` returns `[]` for either, and an empty pack is already red --
    so both were reached only through the empty-pack assertion, whose message says
    something else. The distinction matters to the reader who has to fix it: a
    mapping is a pack written wrongly, a case without an `id` is a chain whose
    last link cannot be named."""
    # `7` is the one that measures the `isinstance(doc, list)` guard. A mapping
    # and a string are both ITERABLE, so the comprehension below the guard already
    # refuses them by yielding keys and characters -- remove the guard and those
    # two still fail, which is why the audit reported it SILENT at 4184. A number
    # is not iterable and raises `TypeError` straight out of the reader.
    for label, pack in (("a mapping", {"id": "d-1", "asserts": []}),
                        ("a case with no id", [{"asserts": [{"x": 1}]}]),
                        ("a scalar string", "disclosure-101"),
                        ("a number", 7)):
        rule = _disposed()
        chain = rules.trace(rule["rule"], _registry(tmp_path, rule),
                            _planted_tree(tmp_path, pack))
        assert not chain.resolved, f"{label} read as a pack carrying cases"


# --- the schema's own halves --------------------------------------------------

def _validates(rule: dict) -> bool:
    try:
        jsonschema.validate(rule, SCHEMA, format_checker=jsonschema.FormatChecker())
    except jsonschema.ValidationError:
        return False
    return True


def test_a_scope_record_of_empty_strings_is_refused():
    """`minLength: 1` on every `scope` field. A scope whose `revives` is `""` is a
    rule re-scoped with no condition that would ever bring the excluded sense
    back -- the decision recorded as taken and its terms left blank, which is the
    field's whole subject."""
    rule = _disposed()
    assert _validates(rule), "the fixture is wrong, not the schema"
    for field in ("covers", "excludes", "revives", "decided_by", "decided_on"):
        planted = json.loads(json.dumps(rule))
        planted["scope"][field] = ""
        assert not _validates(planted), (
            f"`scope.{field}` accepts the empty string. A required field that "
            f"admits nothing is a field that is not required.")


def test_scope_and_disposition_decided_by_must_name_a_real_seat():
    """A seat that does not exist is a decision nobody took. `DISPOSITION_RE` in
    `pave/twokey.py` accepts any `[a-z-]+`, so the same typo one file over
    produces a PR that can never be satisfied -- ADR-037's shape, and the reason
    the enum is in the schema rather than in a reviewer's head."""
    for block in ("scope", "disposition"):
        rule = _disposed()
        assert _validates(rule), "the fixture is wrong, not the schema"
        for typo in ("legal-and-sp", "Legal/S&P", "whoever gets to it", ""):
            rule[block]["decided_by"] = typo
            assert not _validates(rule), (
                f"`{block}.decided_by` accepts {typo!r}, which is not a seat "
                f"`docs/governance/ROLES.md` lists.")

    # **And the undisposed state stays sayable.** `disposition.decided_by` is
    # `unassigned — …` on the committed rule and must remain so: PR 2 disposes
    # nothing, and a schema that refused the state the registry is actually in
    # would have been closed by loosening it back to any string at all.
    undisposed = _undisposed()
    assert undisposed["disposition"]["decided_by"].startswith("unassigned")
    assert _validates(undisposed), (
        "the schema refuses an undisposed disposition. PR 4 disposed the only rule in "
        "this registry and the arm must survive that: an undisposed rule is a state the "
        "registry will be in again, and a schema that refuses it gets loosened back to "
        "any string at all.")


def test_rules_validate_refuses_a_date_that_is_not_one(tmp_path, monkeypatch):
    """**The fix for this PR's own headline false claim, and nothing exercised it.**

    Draft-07 `format` is annotation-only without a `FormatChecker`, so
    `effective: ""`, `"whenever"` and `"2026-13-45"` all validated -- and the empty
    string additionally defeats `test_contracts.py`'s `if effective:` guard, which
    hands back ADR-053's immortal enforced rule. Amendment 2 said requiring the
    field closed that door; it closed one of two. The audit then set
    `checker = None` and the whole suite stayed at 4160."""
    from pave import cli

    registry = tmp_path / "rules"
    registry.mkdir()
    (registry / "schema.json").write_text(json.dumps(SCHEMA), encoding="utf-8")
    # `rules_validate` walks BOTH halves of G7 off the same root, so the planted
    # tree has to carry the control the planted rule names -- otherwise every case
    # below dies on the orphan half and the date half is never reached, which is
    # the masking this whole section exists to undo.
    pack = tmp_path / PACK_REF
    pack.parent.mkdir(parents=True, exist_ok=True)
    pack.write_text("- {id: disclosure-101, input: x, asserts: []}\n", encoding="utf-8")
    monkeypatch.setattr(cli, "ROOT", tmp_path)

    good = _disposed()
    (registry / f"{good['rule']}.yaml").write_text(
        yaml.safe_dump(good, sort_keys=False), encoding="utf-8")
    cli.rules_validate()                                  # the control: it passes

    for bad in ("", "whenever", "2026-13-45", "2026-02-30", "01/01/2026"):
        planted = json.loads(json.dumps(good))
        planted["source"]["effective"] = bad
        (registry / f"{planted['rule']}.yaml").write_text(
            yaml.safe_dump(planted, sort_keys=False), encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            cli.rules_validate()
        assert exc.value.code != 0, (
            f"`rules registry valid` over source.effective = {bad!r}. A rule whose "
            f"effective date is not a date has no clock, and `status: enforced` with "
            f"no clock is the immortal rule ADR-053 planted.")
