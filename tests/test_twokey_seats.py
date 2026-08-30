"""
The seat sets ADR-043 decided, and the plants that measured why they were needed.

**Every case below is a violating-tree test, not an honest-tree assertion.** Each
one names a diff that was measured on `07e8cd1` to leave the suite green and
collect no key, and asserts that it now collects the seats ADR-043 named. An
assertion that a rule exists proves nothing about the rule doing anything; ADR-042
prediction 7b failed for four of ten checks on its first implementation for
exactly that reason.

**Why this file AND `pave/tests/test_twokey.py`.** This one is on the enumerated
protection-test rule alongside `test_arm_scoping` and `test_history_append_only`,
which takes `ai-quality`, `security` and `platform-eng` -- because it pins the
seat sets of two rules that name **security**, and a test that holds Security's
key must not be removable without it. The Security seat measured that removing the
adversarial-corpus rule entirely, with a plausible rationale, was blocked only by
tests living in Security-keyed files.

This paragraph read *"Why this file and not `pave/tests/test_twokey.py`. That file
is on no rule"* until ADR-052. That was true, and harmless while the file held
parser cases; it stopped being harmless when ADR-051 moved the definition of a
decision record into `adr_records` and every assertion defending it into that
file. Measured: the weakening and the deletion of all four assertions that catch
it, in one diff, at 2208 passed and two keys. The sentence is corrected here
rather than left standing, because a stated reason for a gap is what stops the
next reader looking for it -- ADR-035's finding, in the file that records it.

Hermetic (G8): reads committed files, calls nothing.
Owning seat: Security / Red Team (the invariants) - Platform Engineering (the
mechanism) - AI Quality (the rules list).
"""
from __future__ import annotations

import ast
import inspect
import json
import pathlib
import re
import subprocess
import sys

import yaml

from pave import twokey

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROLES = ROOT / "docs" / "governance" / "ROLES.md"

#: The seat sets ADR-043 decided, pinned so that dropping one is red HERE rather
#: than silent. A seat stripped from a three-seat rule previously produced a
#: single failure, in a zero-key file.
ADR043_SEATS = {
    "pave/infra.py": {"security", "platform-eng"},
    "tests/test_iam_assertions.py": {"security", "platform-eng"},
    "platform/gateway/core/cedar.py": {"platform-eng", "security", "tool-owner", "legal-sp"},
    "tests/test_cedar_policy.py": {"platform-eng", "security", "tool-owner", "legal-sp"},
    "tools/publish-highlight/schema.in.json": {"platform-eng", "security", "tool-owner", "legal-sp"},
    "tools/catalog-search/schema.out.json": {"platform-eng", "security", "tool-owner", "legal-sp"},
    "tests/conftest.py": {"platform-eng", "security"},
    "pyproject.toml": {"platform-eng", "security"},
    "conftest.py": {"platform-eng", "security"},
    "pave/tests/conftest.py": {"platform-eng", "security"},
    "pytest.ini": {"platform-eng", "security"},
    "tests/test_twokey_seats.py": {"ai-quality", "security", "platform-eng",
                                   "tool-owner", "legal-sp"},
    "platform/gateway/core/toolplane.py": {"platform-eng", "security", "tool-owner"},
    "tests/test_toolplane.py": {"platform-eng", "security", "tool-owner"},
    # --- ADR-044 ---
    #
    # Pinned in the SAME constant rather than a parallel one, deliberately. A
    # second dict would need its own copy of the ratchet below, and the ratchet is
    # the thing that stops a pin being emptied -- two mechanisms guarding two lists
    # is how `.github/CODEOWNERS` and this module drifted twice (ADR-037).
    "tests/test_contracts.py": {"ai-quality", "platform-eng"},
    "tests/test_calibration_corpus.py": {"ai-quality", "platform-eng"},
    "tests/test_judge.py": {"ai-quality", "platform-eng"},
    "tests/test_tool_loop.py": {"platform-eng", "security"},
    "tests/test_gateway_core.py": {"platform-eng", "security"},
    "tests/test_gateway_run_parity.py": {"platform-eng", "security"},
    # ADR-048: added to ADR-042's enumerated protection-test rule, whose
    # membership ADR-044 pins member by member.
    "tests/test_transport_parity.py": {"ai-quality", "security", "platform-eng"},
    # ADR-045: the floors and their pins, weakened together or not at all.
    "pave/floors.py": {"platform-eng", "ai-quality", "security"},
    "tests/test_floors.py": {"platform-eng", "ai-quality", "security"},
    # ADR-046: the verifier, its refusal table and the producer for every row.
    "pave/manifest.py": {"ai-quality", "security", "platform-eng"},
    "pave/verify.py": {"ai-quality", "security", "platform-eng"},
    "tests/test_manifest_verify.py": {"ai-quality", "security", "platform-eng"},
    # ADR-046: what a service declares about itself. Two seats, and the reason
    # Security is not among them is recorded as an OPEN QUESTION on the rule
    # itself -- the reference manifest now declares a `publish`-consequence tool.
    "services/highlights-agent/pave.manifest.yaml": {"ai-quality", "tool-owner"},
    # ADR-047: the scaffold, and the pairwise tests that are its only drift
    # detector. Pinned member by member for ADR-044's measured reason -- an
    # alternation narrows by a few characters and the rule loses a member silently.
    "templates/agent-tools/pave.manifest.yaml.tmpl":
        {"platform-eng", "ai-quality", "tool-owner", "security"},
    "templates/agent-tools/gateway_client.py.tmpl":
        {"platform-eng", "ai-quality", "tool-owner", "security"},
    "templates/agent-tools/evals/golden/cases.yaml.tmpl":
        {"platform-eng", "ai-quality", "tool-owner", "security"},
    "pave/scaffold.py": {"platform-eng", "ai-quality", "tool-owner", "security"},
    "tests/test_scaffold.py": {"platform-eng", "ai-quality", "tool-owner", "security"},
    # ADR-049: three rows SPEC/05's seat table stated and no PR built, closed at
    # the M05 close with the measurement beside each. The register and its check
    # are pinned as a pair for ADR-043 decision 1's reason -- data guarded and
    # instrument free is the asymmetry ADR-044 exists to refuse.
    "docs/governance/recordings.json": {"platform-eng", "ai-quality"},
    "tests/test_demo_recordings.py": {"platform-eng", "ai-quality"},
    # Deleting the `OBSERVATIONS` guard: 2072 passed. `check:` reduced to
    # `@echo ok`: 2072 passed. Both on zero keys.
    "Makefile": {"platform-eng", "ai-quality"},
    # Deleting the file outright: 2059 passed, zero failures -- the only tie
    # between the committed ceilings and the measurement they were derived from.
    "tests/test_budget_derivation.py": {"ai-quality", "platform-eng"},
    # ADR-052: the rules list, the workflow that runs it, and the file holding
    # every assertion that defends `adr_records`. Pinned member by member, and
    # `pave/tests/test_twokey.py` is a member for the reason the measurement gives:
    # restoring the substance bar to `< 1` AND deleting the four assertions that
    # catch it was ONE diff, 2208 passed, keys `ai-quality` and `platform-eng`.
    # Security is on all four rules that require an ADR and alone on
    # `quality/adversarial/`, and was not asked.
    "pave/twokey.py": {"ai-quality", "platform-eng", "security"},
    "pave/tests/test_twokey.py": {"ai-quality", "platform-eng", "security"},
    ".github/workflows/two-key.yml": {"ai-quality", "platform-eng", "security"},
    # ADR-052 round 2, both from the Security seat. `__init__.py` is 0 bytes and
    # runs on any `pave.X` import -- a shim rebinding `adr_records`, guarded by
    # `if "pytest" not in sys.modules`, made the live gate mint a record for a file
    # the PR never touched at 2219 passed, zero keys. The fixtures hold the replay
    # that justifies ADR-051's largest reversal and the CRLF corpus: inflating the
    # replay 60 -> 300 rows was 2219 passed, zero keys.
    "pave/__init__.py": {"ai-quality", "platform-eng", "security"},
    "pave/tests/fixtures/adr_bar_replay.json": {"ai-quality", "platform-eng", "security"},
    "pave/tests/fixtures/pr_bodies.json": {"ai-quality", "platform-eng", "security"},
    # **What these pins buy, precisely.** Against a NARROWED alternation the
    # ratchet above is what bites, and five of six ADR-052 entries here are
    # redundant to it -- measured, deleting five leaves 177 passed, because
    # `covered` needs only one representative per rule. They earn their place
    # against a rule SPLIT, where a path moves to a new rule with a thinner seat
    # set and no alternation narrows at all.
    #
    # ADR-052. A shim in `pave/cli.py` rebinding `twokey.adr_records` and
    # `twokey.evaluate` left 2222 passed -- the exact baseline -- with the live gate
    # printing SATISFIED and exiting 0 on zero keys. The first remedy KEYED that
    # file; ADR-041 decision 7 refuses exactly that, so the gate moved to
    # `pave/twokeycli.py`, which the workflow runs directly, and `pave/cli.py` is out
    # of the process rather than harder to edit. `gate.py` holds `EXIT_QUALITY`,
    # whose 1 -> 0 makes every rule report BLOCKED and exit 0. Two seats: Security
    # because it owns every ADR-requiring rule, Platform Engineering the mechanism.
    "pave/twokeycli.py": {"platform-eng", "security"},
    "pave/gate.py": {"platform-eng", "security"},
    "pave/verdict.py": {"platform-eng", "security"},
}


def _seats_for(path: str) -> set:
    return {seat for rule, _ in twokey.triggered([path]) for seat in rule.seats}


def test_the_seat_sets_adr043_decided_are_exactly_these():
    """Not a subset check. A rule that gained a seat is a decision too, and a
    rule that lost one is the change this file exists to make visible."""
    assert len(ADR043_SEATS) >= 8, (
        f"ADR043_SEATS holds {len(ADR043_SEATS)} paths. Emptying or thinning it makes every "
        "assertion in this file vacuous — the Security seat measured `{}` at 1814 passed, "
        "and narrowing a rule plus neutering this loop at 1815."
    )
    for path, expected in ADR043_SEATS.items():
        assert _seats_for(path) == expected, (
            f"{path}: seats are {sorted(_seats_for(path))}, ADR-043 decided "
            f"{sorted(expected)}. Changing a rule's seat set is a G9 decision — "
            "amend the ADR, do not edit this constant to match the code."
        )


def test_the_seat_pin_covers_every_rule_this_adr_added():
    """**The audit did not reach this one and the Tool Owner seat did.**
    `ADR043_SEATS = {}` left 1814 passed -- every seat pin decision 5 rests on,
    and prediction 6's whole basis, deleted by one token.

    Ratcheted against `twokey.RULES` the way `HISTORY_DIGESTS` is ratcheted
    against `pins.json`: each pattern ADR-043 added must have at least one
    representative path pinned above, so emptying or thinning the constant is red
    rather than silent."""
    added = [r for r in twokey.RULES
             if any(k in r.what for k in ("G1's model-invoke allowlist",
                                          "the Cedar generator",
                                          "the test harness",
                                          "the seat-set pins",
                                          "the tool plane",
                                          # ADR-044
                                          "the eval-plane instruments",
                                          "the record-and-refusal instruments",
                                          # ADR-046
                                          "the manifest verifier",
                                          "what a service declares about itself",
                                          # ADR-047
                                          "the scaffold every future service",
                                          # ADR-049
                                          "the demo-act obligation register",
                                          "the developer entrypoints",
                                          "the budget derivation pin",
                                          # ADR-052
                                          "the definition of what discharges one",
                                          "the gate's own process"))]
    assert len(added) == 15, (
        f"expected ADR-043's five, ADR-044's two, ADR-046's two, ADR-047's one, "
        f"ADR-049's three and ADR-052's two, found "
        f"{[r.what[:40] for r in added]}. If a rule was renamed, update this ratchet in "
        "the same diff — it is what stops the pin below being emptied."
    )
    #: Paths each ADR-043 rule MUST still cover. "At least one path matches" let a
    #: regex be narrowed to drop the other file it names -- decision 1 says the G1
    #: constant and its pin are "weakened together or not at all", and a two-line
    #: diff separated them green.
    required = {
        "G1's model-invoke allowlist": ["pave/infra.py", "tests/test_iam_assertions.py"],
        "the Cedar generator": ["platform/gateway/core/cedar.py", "tests/test_cedar_policy.py",
                                "tools/publish-highlight/schema.in.json",
                                # `schema.out.json` too: narrowing `(in|out)` to `in` was a
                                # two-line diff removing every output schema from the rule,
                                # green — the separation decision 1 forbids, one file short.
                                "tools/catalog-search/schema.out.json"],
        "the test harness": ["tests/conftest.py", "pyproject.toml", "conftest.py", "pytest.ini",
                             # covered rather than measured when the rule was widened, so
                             # pinned here rather than left to a reader's trust
                             "tox.ini", "setup.cfg", ".pytest.ini"],
        "the seat-set pins": ["tests/test_twokey_seats.py"],
        "the tool plane": ["platform/gateway/core/toolplane.py", "tests/test_toolplane.py"],
        # ADR-044. Every filename in each alternation is required, for the reason
        # decision 1 gives above and for a second one measured here: the enumerated
        # `tests/(...)` rule ADR-042 added could be narrowed by deleting FOUR
        # CHARACTERS -- `_lane` -- taking `tests/test_adversarial_lane.py` from
        # three keys to zero, silently, at 1881 passed. Nothing pinned that rule's
        # membership. These two are pinned member by member from the start.
        "the eval-plane instruments": ["tests/test_contracts.py",
                                       "tests/test_calibration_corpus.py",
                                       "tests/test_judge.py"],
        "the record-and-refusal instruments": ["tests/test_tool_loop.py",
                                               "tests/test_gateway_core.py",
                                               "tests/test_gateway_run_parity.py"],
        # ADR-046, member by member for ADR-044's measured reason: an alternation
        # can be narrowed by deleting a few characters, and the rule that loses a
        # member loses it silently. `ROWS` and its producers are the two halves of
        # one control and neither may be un-keyed without the other.
        "the manifest verifier": ["pave/manifest.py", "pave/verify.py",
                                  "tests/test_manifest_verify.py"],
        # A path pattern, so the pin is a path a scaffolded service would produce
        # rather than only the committed one -- `pave new sportscast-agent` must
        # land on this rule the day it runs, not the day someone adds its name.
        "what a service declares about itself": [
            "services/highlights-agent/pave.manifest.yaml",
            "services/a-service-that-does-not-exist-yet/pave.manifest.yaml"],
        # Every rendered template AND both halves of its drift detector. The
        # `templates/` glob is checked at depth, because `templates/agent-tools/.+`
        # narrowed to `templates/agent-tools/[^/]+` would silently drop the three
        # files under `evals/` -- which are the golden pack and the assert
        # vocabulary, the two a scaffolded team reads first.
        "the scaffold every future service": [
            "templates/agent-tools/pave.manifest.yaml.tmpl",
            "templates/agent-tools/gateway_client.py.tmpl",
            "templates/agent-tools/evals/answer.schema.json.tmpl",
            "templates/agent-tools/evals/golden/cases.yaml.tmpl",
            "templates/agent-tools/evals/golden/README.md.tmpl",
            "templates/agent-tools/README.md",
            "pave/scaffold.py",
            "tests/test_scaffold.py"],
        # ADR-049, all three member by member. The register and the check that
        # reads it are one control -- ADR-043 decision 1's "weakened together or
        # not at all" -- and dropping `tests/test_demo_recordings.py` from the
        # alternation would leave the data guarded and the instrument free, which
        # is precisely the asymmetry ADR-044 was written about.
        "the demo-act obligation register": ["docs/governance/recordings.json",
                                             "tests/test_demo_recordings.py"],
        "the developer entrypoints": ["Makefile"],
        "the budget derivation pin": ["tests/test_budget_derivation.py"],
        # ADR-052. Enumerated here because the audit measured both narrowings
        # silent otherwise: deleting the three pin entries below left 173 passed,
        # and dropping `pave/tests/test_twokey.py` from the alternation was caught
        # only by the pin -- the plant unions seats across both files, so
        # `pave/twokey.py` alone still supplied all three. `len(ADR043_SEATS) >= 8`
        # does not bite on a constant of thirty-odd entries thinned by three.
        "the definition of what discharges one": [
            "pave/twokey.py",
            "pave/tests/test_twokey.py",
            ".github/workflows/two-key.yml",
            # Round 2. A path pattern for the fixtures, so a fixture added later
            # lands on the rule the day it is written rather than the day someone
            # remembers to enumerate it.
            "pave/__init__.py",
            "pave/tests/fixtures/adr_bar_replay.json",
            "pave/tests/fixtures/pr_bodies.json",
            "pave/tests/fixtures/a-fixture-that-does-not-exist-yet.json"],
        # Round 3, member by member. Narrowing `(cli|gate|verdict)` by four
        # characters takes the entrypoint CI runs off the rule, which is ADR-044's
        # measured `_lane` narrowing in a rule written after it.
        # `pave/twokeycli/__init__.py` is required as well as the `.py` form:
        # narrowing the pattern back to `\.py$` was **181 passed, SILENT**, and a
        # package shadowing the module is exactly the attack the arm exists to key.
        # A path that need not exist, like the scaffold's, so it pins the SHAPE.
        "the gate's own process": ["pave/twokeycli.py", "pave/gate.py",
                                   "pave/verdict.py",
                                   "pave/twokeycli/__init__.py",
                                   "pave/twokeycli/a-submodule-that-may-never-exist.py"],
    }
    # **A total pin, because the sentinel entries are one line deep.** Narrowing an
    # alternation AND deleting the entry that catches it is one diff, measured at 22
    # passed -- unlike `len(added) == 15` and `len(ADR043_SEATS) >= 8`, these path
    # lists had no pin of their own.
    total = sum(len(v) for v in required.values())
    assert total == 51, (
        f"`required` holds {total} paths across {len(required)} rules, expected "
        "51. Deleting a required path in the same diff that "
        "narrows a rule is the one-edit bypass this pin exists to make two — if a "
        "path was added on purpose, raise the constant in this diff and say why."
    )
    for rule in added:
        # **Exactly one, never the first match.** `next(...)` returned the FIRST
        # key contained in `rule.what`, so renaming a rule to also contain an
        # earlier key checked that key's path list and never looked at this
        # rule's -- measured: `"the developer entrypoints — and the definition of
        # what discharges one"` over `^(Makefile|pave/twokey\.py)$` checked
        # `["Makefile"]` and passed, with two files off the rule unexamined. And a
        # rule enumerated above with no entry here raised a bare `StopIteration`
        # in a ratchet whose every other failure carries its remediation.
        keys = [k for k in required if k in rule.what]
        assert len(keys) == 1, (
            f"the rule {rule.what[:60]!r} matches {len(keys)} key(s) in `required`: "
            f"{keys}. Zero means it was enumerated above and its path list was never "
            "written; more than one means a rename made it answer to another rule's "
            "list. Give it exactly one key and its own paths, in this diff."
        )
        key = keys[0]
        for path in required[key]:
            assert rule.pattern.search(path), (
                f"the rule {rule.what[:50]!r} no longer covers {path}. Narrowing a regex "
                "to drop one of the files it names is the two-line separation decision 1 "
                "forbids in as many words."
            )
        covered = [p for p in ADR043_SEATS if rule.pattern.search(p)]
        assert covered, (
            f"no path in ADR043_SEATS exercises the rule {rule.what[:60]!r}. An unpinned "
            "rule can have a seat removed with the suite green."
        )


def test_the_g1_allowlist_rule_requires_an_adr():
    """`pave/infra.py:64` and `tests/test_iam_assertions.py:118` both say adding an
    allowlist entry needs an ADR and the Security seat. The ADR half is a flag on
    the rule, and nothing else asserts it."""
    rules = [rule for rule, _ in twokey.triggered(["pave/infra.py"])]
    assert rules, "pave/infra.py is on no rule (ADR-043 decision 1)"
    assert any(rule.requires_adr for rule in rules), (
        "the G1 allowlist rule does not require an ADR. Adding an entry to "
        "MODEL_INVOKE_ROLE_PREFIXES *is* writing a G1 exception, and both the "
        "constant and its pin say so in prose."
    )


def test_every_seat_string_is_a_seat_roles_md_lists():
    """A rule naming a seat that does not exist is unsatisfiable, and produces no
    diagnostic — `DISPOSITION_RE` accepts any `[a-z-]+`, so the PR is simply
    blocked forever.

    The vocabulary is READ from `ROLES.md`'s `**Subagent:**` lines rather than
    pinned as a literal here. ROLES.md's own heading says eight seats; the eighth
    is Runtime Approvers, "a role, not a person", which holds no key and has no
    subagent. Reading the file means the two lists cannot drift the way ADR-037
    measured CODEOWNERS and `twokey.py` drifting."""
    known = set(re.findall(r"\.claude/agents/([a-z-]+)\.md", ROLES.read_text(encoding="utf-8")))
    assert len(known) >= 7, f"parsed only {sorted(known)} from ROLES.md — the parser is stale"
    used = {seat for rule in twokey.RULES for seat in rule.seats}
    assert used <= known, (
        f"twokey.RULES names seat(s) {sorted(used - known)}, which ROLES.md does not "
        "list. A typo'd seat is a rule no PR body can ever satisfy."
    )


def test_this_file_is_itself_on_a_rule_that_carries_securitys_key():
    """**The audit found this one silent.** Dropping `test_twokey_seats` from the
    enumerated protection-test regex left 1812 passed: the file that pins
    Security's key was removable without Security's key.

    ADR-042 closed the same shape by having `HISTORY_DIGESTS` assert its own
    relationship to `pins.json`. Self-referential and correct -- a protection
    test whose own rule can be deleted quietly protects nothing."""
    here = pathlib.Path(__file__).resolve().relative_to(ROOT).as_posix()
    seats = _seats_for(here)
    # **From the LIVE rule set, never from `ADR043_SEATS`.** The first version
    # derived the expectation from the constant an attacker is already editing --
    # both sides moved together, so the comparison was vacuous under exactly the
    # attack it was written for. The Legal/S&P seat measured it: dropping
    # `legal-sp` from two rules AND from the pin left 1815 passed with the seat
    # never collected.
    #
    # The live union is a real anchor because a seat survives in it as long as ANY
    # rule still names it -- `platform/registry/tools.yaml` has carried
    # `legal-sp` since M02 and no plant against this file touches it.
    #
    # Consequence, deliberately: a rule introducing a NEW seat turns this red until
    # that seat also guards this file. That is the property -- a file holding every
    # rule's seat set must be removable only by every seat it pins.
    pinned = {s for rule in twokey.RULES for s in rule.seats}
    missing = sorted(pinned - seats)
    assert not missing, (
        f"tests/test_twokey_seats.py is on rule(s) carrying {sorted(seats)}, but it pins "
        f"keys for {sorted(pinned)}. Seat(s) {missing} could be dropped from the rules "
        "below AND from this pin in one diff, without the seat losing the key ever being "
        "asked — the shape ADR-037 recorded and ADR-043 exists to close."
    )


# --- the plants, each measured green and keyless on 07e8cd1 --------------------

def _blocked_for(files: list, expected: set) -> None:
    """A diff over `files`, with an empty PR body, must demand exactly `expected`."""
    assert _seats_for_many(files) == expected, (
        f"{files}: collects {sorted(_seats_for_many(files))}, expected {sorted(expected)}"
    )
    problems = twokey.evaluate(files, "")
    assert problems, f"{files}: two-key reports NOT REQUIRED — the plant merges on zero keys"


def _seats_for_many(files: list) -> set:
    return {seat for rule, _ in twokey.triggered(files) for seat in rule.seats}


def test_widening_the_g1_allowlist_with_its_own_pin_collects_security():
    """Measured on 07e8cd1: `MODEL_INVOKE_ROLE_PREFIXES` widened to
    `("GatewayFn", "ScaffoldSmokeFn")` **and its own pin relaxed to match**, one
    diff — 1795 passed, `two-key: not required`.

    ADR-043 decision 4 is explicit that this rule makes the widening COLLECTABLE
    and not red: a self-pinning constant edited alongside its pin produces no
    failure, and only a second assertion at another path would."""
    _blocked_for(["pave/infra.py", "tests/test_iam_assertions.py"],
                 {"security", "platform-eng"})


def test_a_forged_permit_from_the_generator_collects_four_seats():
    """Measured: two lines in `cedar.py:generate()` put
    `permit(principal == Service::"attacker-svc", ...)` into the deployed policy
    set, `pave policy generate --check` exited **0**, 1795 passed, and
    `platform/registry/tools.yaml` — the two-key file — was never touched."""
    _blocked_for(["platform/gateway/core/cedar.py", "platform/gateway/policy/tools.cedar"],
                 {"platform-eng", "security", "tool-owner", "legal-sp"})


def test_dropping_publish_from_the_gated_consequences_collects_legal_sp():
    """Measured: removing `"publish"` from `GATED_CONSEQUENCES` emitted **zero**
    forbid clauses, made `publish-highlight` reachable with no approver, and the
    drift gate exited 0 — collecting no key at all, and never reaching Legal/S&P,
    the seat CLAUDE.md names for consequence classes.

    `legal-sp` is the assertion that matters here: the Security seat recommended a
    seat set without it in one review round and retracted that in the next, on
    this measurement."""
    seats = _seats_for("platform/gateway/core/cedar.py")
    assert "legal-sp" in seats, (
        "GATED_CONSEQUENCES decides which consequence classes get an approval "
        "interlock, and it lives in this file. Consequence classes are Tool Owner "
        "plus Legal/S&P (CLAUDE.md); the registry rule cannot collect a key for a "
        "constant that is not in the registry."
    )


def test_editing_a_tool_schema_collects_the_tool_owner_and_legal_sp():
    """Measured: deleting `ai_generated` — the MER-AI-0001 disclosure flag — and
    adding `skip_approval` to `publish-highlight`'s input schema travelled into
    `tools.contracts.json`, which ships inside the gateway bundle. `--check`
    exited 0, 1795 passed, two-key not required."""
    _blocked_for(["tools/publish-highlight/schema.in.json",
                  "platform/gateway/policy/tools.contracts.json"],
                 {"platform-eng", "security", "tool-owner", "legal-sp"})


def test_a_conftest_that_decides_what_the_suite_reports_collects_a_key():
    """Measured, both forms. `collect_ignore` dropped 1795 collected tests to
    **1656** with `pave check` printing "All checks passed!" at exit 0. Eight lines
    of `pytest_runtest_makereport` hookwrapper reported **1795** — the exact honest
    count — with a G1 pin genuinely failing.

    ADR-042 decision 8 listed this file as "none — stated", reasoning that it
    cannot reach the workflow step deciding the history checks. That holds for the
    history checks and for nothing else.

    **The residual, stated:** a key makes this collectable, never red. A harness
    that rewrites its own reports can report anything and no count sees it."""
    _blocked_for(["tests/conftest.py"], {"platform-eng", "security"})


# --- ADR-044's plants, measured green and keyless on 6af17d2 ------------------

def test_deleting_the_only_headroom_check_collects_ai_quality():
    """Measured on `6af17d2`, one diff: delete `test_golden_set_keeps_headroom`
    — the repository's only headroom check — flip both `expect_near_threshold`
    cases to false, and delete `test_a_disposition_is_all_or_nothing`.
    **1859 passed, zero failures, and `twokey.evaluate` returned `[]`.**

    Found by two seats independently in the SPEC/05 round-4 review, and in none
    of that review's twenty-one pre-flight findings."""
    _blocked_for(["tests/test_contracts.py"], {"ai-quality", "platform-eng"})


def test_removing_the_publish_class_approver_assertion_collects_a_key():
    """`tests/test_contracts.py` holds the ONLY assertion in this repository that
    a publish-class tool declares an approver, and it used to restate the gated
    set as a bare literal. Measured: narrowing that literal to `{"irreversible"}`
    and deleting `approval: stepfn:editorial-approver` from the registry shipped
    `// ... Declared approver: none` in the deployed policy set at **1881
    passed**, `policy generate --check` exit 0 — for the two keys the registry
    line collects, with this file contributing none.

    The file now reads `cedar.GATED_CONSEQUENCES` and pins its value; this rule
    is why the pin cannot be moved without the seat that owns the instruments."""
    assert "ai-quality" in _seats_for("tests/test_contracts.py")


def test_the_sole_g5_by_design_witness_collects_security():
    """`tests/test_gateway_core.py:283` is the only live witness that G5 refuses
    `sensitive` **by design** rather than by the index comparison happening to
    agree: deleting `classify.py`'s dedicated short-circuit leaves every other
    classification assertion green, and that one red.

    It is also the witness a singleton `DECLARABLE_LEVELS` cannot reach, because
    it passes `declared="sensitive"` — a value the manifest will refuse."""
    _blocked_for(["tests/test_gateway_core.py"], {"platform-eng", "security"})


def test_deleting_the_transport_parity_pin_collects_security():
    """Measured: deleting `tests/test_gateway_run_parity.py` and rewording
    `gateway_client.py`'s `user_turn` in one diff is **1862 passed, zero keys** —
    and `user_turn` composes the wire text of every governed adversarial
    observation, which `instrument_digests` does not cover. An instrument change
    invisible to the instrument registry."""
    _blocked_for(["tests/test_gateway_run_parity.py"], {"platform-eng", "security"})


def test_the_enumerated_protection_rule_cannot_be_narrowed_by_four_characters():
    """**ADR-042's rule, pinned by ADR-044 because nothing pinned it.**

    Measured on `6af17d2`: deleting four characters — `_lane` — from the
    enumerated `tests/(...)` alternation took `tests/test_adversarial_lane.py`,
    which holds `G4_CASE_FLOOR`'s ratchet, from three keys to **zero, silently,
    at 1881 passed**. The rule's membership was on no pin at all, so the
    separation ADR-043 decision 1 forbids was available for a four-character
    diff on the one rule ADR-043's ratchet did not reach."""
    for path in ("tests/test_arm_scoping.py", "tests/test_instrument_stability.py",
                 "tests/test_adversarial_lane.py", "tests/test_adversarial_entry.py",
                 "tests/test_history_append_only.py",
                 # ADR-048. The wire text of every governed adversarial observation
                 # is pinned here, and no instrument digest covers the transport.
                 "tests/test_transport_parity.py"):
        assert _seats_for(path) == {"ai-quality", "security", "platform-eng"}, (
            f"{path} is no longer on the enumerated protection-test rule. Narrowing that "
            "alternation is a two-key diff that silently un-keys a three-key file."
        )


def test_the_rename_bypass_stays_closed_for_the_new_rules():
    """ADR-042 decision 4 put `--no-renames` on the workflow's diff so a `git mv`
    reports the old path too. These rules name files, so the old path is what
    matches — verified here for the paths ADR-043 adds, because a rule that a
    rename walks around is the "stated and absent" shape one level out."""
    for old, new in (("pave/infra.py", "pave/iam_allowlist.py"),
                     ("platform/gateway/core/cedar.py", "platform/gateway/core/cedar_gen.py"),
                     ("tests/conftest.py", "tests/_conftest.py")):
        # `--no-renames` reports BOTH sides; the old path is the one on the rule.
        assert twokey.triggered([old, new]), (
            f"moving {old} -> {new} collects nothing. The workflow's diff uses "
            "--no-renames (ADR-042 decision 4) precisely so the old path still matches."
        )


# --- the adversarial corpus's own contracts (M06, Security's round-3 finding) ---

def test_the_probe_severity_guard_collects_security_and_owes_an_adr():
    """`quality/adversarial/probes.yaml` is "only Security may downgrade a probe,
    and only with an ADR". The eight assertions that make that sentence true sat
    in `tests/test_contracts.py`, whose rule is `ai-quality` and `platform-eng`
    with **no Security key and no ADR** — 47 tests about the registry, the
    manifest, Cedar and the golden suite, under a pattern drawn around three files
    with nothing in common.

    Measured before the split: downgrading one probe to advisory is `16 failed`,
    of which fifteen are `tests/test_adversarial_entry.py` (three seats,
    Security included) and exactly one is the semantic refusal — and that one was
    removable on two keys that are not Security's, with no ADR."""
    _blocked_for(["tests/test_adversarial_contracts.py"],
                 {"security", "ai-quality", "platform-eng"})
    problems = twokey.evaluate(
        ["tests/test_adversarial_contracts.py"],
        "Two-Key-Disposition: security\n"
        "Two-Key-Disposition: ai-quality\n"
        "Two-Key-Disposition: platform-eng\n"
        "Two-Key-Rationale: retiring the probe severity contract because the lane "
        "already refuses an advisory probe downstream\n",
    )
    assert problems and any("ADR" in p for p in problems), (
        "the rule that enforces 'only with an ADR' does not itself require one"
    )


def test_g4s_semantics_allowlist_lives_wherever_securitys_key_reaches():
    """Written against the CONSTANT rather than the filename, so moving
    `G4_PASS_SEMANTICS` back into a file on a weaker rule fails here rather than
    silently restoring the gap.

    G4 is the invariant CLAUDE.md names as most often violated by well-meaning
    changes, and its allowlist decides what "a probe passed" means. Its own
    docstring said adding a value "is a Security-seat change and needs an ADR"
    while the file it lived in demanded neither — a protection **stated and
    absent**, which this repo has now found three times (ADR-035, ADR-037, here).
    """
    root = ROOT
    # Anchored at column 0, which finds the DEFINITION and not this file, whose
    # search string is itself an occurrence. The first draft matched itself and
    # demanded a Security key on the file doing the asking.
    defines = re.compile(r"^G4_PASS_SEMANTICS\s*=", re.MULTILINE)
    homes = [p for p in (root / "tests").glob("test_*.py")
             if defines.search(p.read_text(encoding="utf-8"))]
    assert homes, "G4_PASS_SEMANTICS is defined in no test file — has it moved out of tests/?"
    for home in homes:
        rel = f"tests/{home.name}"
        hits = twokey.triggered([rel])
        seats = {s for rule, _ in hits for s in rule.seats}
        assert "security" in seats, (
            f"{rel} defines G4's pass-semantics allowlist and collects {sorted(seats)}"
        )
        assert any(rule.requires_adr for rule, _ in hits), f"{rel} owes an ADR and does not"
def test_weakening_what_discharges_an_adr_collects_security():
    """**Measured on 6589827, one diff, both files.** Restore the substance bar in
    `adr_records` to `< 1` -- v3's defect, the one four seats defeated -- and
    delete the four assertions in `pave/tests/test_twokey.py` that catch it:
    `test_the_substance_bar_is_the_calibrated_one`,
    `test_repetition_does_not_clear_the_substance_bar`,
    `test_the_repos_own_supersession_convention_is_not_refused`,
    `test_a_near_miss_is_still_named_when_the_count_is_short`.

    **Four, and an earlier draft of this docstring said five.** The Security seat
    measured the bar weakening alone at 4 failed, not 5. The fifth name was
    `test_the_replay_behind_the_citation_cut_is_in_the_tree`, which reads committed
    fixture data and never calls `adr_records` -- it failed in the original
    measurement because the regex that deleted the other four swallowed the
    module-level `REPLAY` constant with them, so the fifth failure was `NameError`
    from the measuring script. A guard count one too high is a protection stated
    and absent, which CLAUDE.md ranks worse than one merely missing.

    **2208 passed, ruff clean, keys `ai-quality` and `platform-eng`.** The ADR
    half of `quality/adversarial/` -- Security's rule, Security alone -- went back
    to a citation without the Security seat being asked.

    Both files, because the weakening and the deletion of everything that catches
    it fit in one diff: guarding the module alone leaves the tests removable, and
    ADR-044 measured that exact asymmetry twice."""
    _blocked_for(["pave/twokey.py", "pave/tests/test_twokey.py"],
                 {"ai-quality", "platform-eng", "security"})
    # And EACH file alone. The two-file form unions their seats, so dropping
    # `pave/tests/test_twokey.py` from the rule left this assertion green --
    # measured, and the reason the per-file check is here rather than implied.
    _blocked_for(["pave/tests/test_twokey.py"], {"ai-quality", "platform-eng", "security"})
    _blocked_for(["pave/twokey.py"], {"ai-quality", "platform-eng", "security"})


def test_the_definition_of_a_decision_record_carries_every_adr_rules_seats():
    """Derived from the LIVE rule set, never from a copied seat list -- the
    mistake `test_the_seat_pin_covers_every_rule_this_adr_added` records, where
    both sides of a comparison moved together under the attack it was written for.

    `adr_records` decides what discharges `requires_adr` for every rule that sets
    it, so the file DEFINING it must collect every seat each of those rules names:
    a seat trusted to hold an ADR requirement must be able to defend what
    satisfying it means. A rule giving a NEW seat an ADR requirement turns this red
    until that seat also guards the definition.

    **Per rule, not over a union, and the file comes from `inspect`.** The Platform
    Engineering seat defeated both shortcuts in the first draft:

      - the union was a set comprehension, so `if s == "security"` collapsed it to
        exactly what the anti-vacuity anchor below checks -- 20 passed -- and a new
        `requires_adr` rule naming `legal-sp` then passed too, which is precisely
        the state this test exists to make red. There is no seat filter to collapse
        now, and `checked` counts the rules the loop actually reached.
      - `hasattr(twokey, "adr_records")` asserts a NAME IS BOUND, not where it is
        defined. Measured: move `adr_records` to `pave/_adr.py` and re-export it --
        175 passed, and `pave/_adr.py` is on no rule. `inspect.getfile` follows the
        definition to whatever file holds it, so walking it out of a keyed module
        is red here rather than a blind spot named in a docstring."""
    root = ROOT
    assert hasattr(twokey, "adr_records"), (
        "`adr_records` is gone — if the definition MOVED, this test follows it via "
        "`inspect` below; if it was DELETED, the ADR requirement has no meaning left"
    )
    home = pathlib.Path(inspect.getfile(twokey.adr_records)).resolve()
    assert home.is_relative_to(root), f"`adr_records` is defined outside the repo: {home}"
    home = home.relative_to(root).as_posix()
    defends = _seats_for(home)
    # **Two shapes of the same derivation, because one is collapsible.** The seat
    # filter the Platform Engineering seat used against the first draft --
    # `{s for s in ... if s == "security"}` -- survived being moved from the union
    # into the loop, since any expression computing `missing` can be filtered by
    # the edit that computes it. What raises the cost is that BOTH must be
    # neutered, and they are shaped differently: a set difference over every rule
    # at once, and a per-rule containment below.
    undefended = sorted({s for rule in twokey.RULES if rule.requires_adr
                         for s in rule.seats} - defends)
    assert not undefended, (
        f"seat(s) {undefended} are named by a rule requiring an ADR and are not "
        f"collected by {home}, which defines what discharges one — ADR-052."
    )
    checked = 0
    for rule in twokey.RULES:
        if not rule.requires_adr:
            continue
        checked += 1
        missing = sorted(set(rule.seats) - defends)
        assert not missing, (
            f"{home} defines what discharges an ADR requirement and collects "
            f"{sorted(defends)}, while the rule {rule.what[:50]!r} requires one and "
            f"names {sorted(rule.seats)}. Seat(s) {missing} hold an ADR requirement "
            "whose meaning they cannot defend — ADR-052."
        )
    # The loop emptied is the same two-line edit that defeated the first draft, so
    # the count is pinned the way ADR-044 pins its own. Four rules require an ADR
    # today; this is a floor, and a fifth is welcome.
    assert checked >= 4, (
        f"only {checked} rule(s) require an ADR. Either the requirement was removed "
        "from rules that had it, or this loop stopped reaching them."
    )
    # A concrete anchor as well. `security` is drawn from a fact outside this
    # module: CLAUDE.md names the adversarial corpus as "Security alone plus an
    # ADR", and that is the strictest ADR requirement in the file.
    assert "security" in defends, (
        f"{home} does not collect `security`, which holds the adversarial corpus rule "
        "alone. That rule is the model CLAUDE.md names for the whole promise."
    )
def _module_to_paths(dotted: str) -> tuple:
    """Both shapes a dotted name can take on disk, package first — Python's own
    order. `FileFinder` resolves `pave/twokeycli/` before `pave/twokeycli.py`."""
    stem = dotted.replace(".", "/")
    return (f"{stem}/__init__.py", f"{stem}.py")


def _path_to_module(rel: str) -> str:
    """`pave/x/__init__.py` -> `pave.x`, `pave/x.py` -> `pave.x`.

    The naive `rel[:-3].replace("/", ".")` produced `pave.twokeycli.__init__`, which
    imports fine and loads a name the walk never lists -- so an honest conversion of
    a module into a package was REFUSED. A false refusal is the failure ADR-051
    exists to remove, and it was in the check written to close a real one."""
    return (rel.removesuffix("/__init__.py") if rel.endswith("/__init__.py")
            else rel.removesuffix(".py")).replace("/", ".")


#: A recognised interpreter invocation naming a module. Deliberately a small,
#: literal set: `python`, `python3`, `py -3`, with `-m mod` or `-mmod`. An
#: interpreter behind a shell variable (`$PY -m ...`) does NOT match, because a
#: check cannot follow it and must not pretend to.
_INVOCATION = re.compile(
    r"^\s*(?:python[0-9.]*|py)(?:\s+-[0-9][0-9.]*)?\s+-m\s*([A-Za-z_][\w.]*)\b")


def _gate_invocations(root: pathlib.Path) -> list:
    """Every executable line in `two-key.yml` that mentions `pave`, comments out.

    **Lines, not the whole run block.** Round 5 stripped `#` comments and claimed
    "a decoy has nowhere to sit". It has: an `echo`, a quoted argument, a heredoc,
    or a step GitHub skips via `if:` -- which this parser reads and the runner does
    not. Round 6 measured `echo "running: python -m pave.twokeycli ..."` beside a
    real `python3 -m pave.cli` at **2230 passed, the exact baseline**, with the gate
    reporting `not required` on a change to the adversarial corpus."""
    doc = yaml.safe_load(
        (root / ".github" / "workflows" / "two-key.yml").read_text(encoding="utf-8"))
    lines = []
    for job in (doc.get("jobs") or {}).values():
        for step in (job.get("steps") or []):
            for line in (step.get("run") or "").splitlines():
                clean = re.sub(r"(?<!\S)#.*$", "", line)
                if re.search(r"\bpave\b", clean):
                    lines.append(clean)
    return lines


def _ci_gate_entrypoint(root: pathlib.Path | None = None) -> str:
    """The module `.github/workflows/two-key.yml` actually runs, read from it.

    **Exactly one executable line may mention `pave`, and it must be a recognised
    invocation.** Both halves are load-bearing and each was measured silent alone:

      - a second mention is a decoy -- an `echo`, or a step carrying `if: false`
        that this parser reads and the runner skips;
      - a single mention that is not `python -m <module>` is a real command this
        check cannot follow. `pave gate two-key`, the console script `pip install
        -e .` installs, runs through the unkeyed `pave/cli.py`; so do `python3 -m`,
        `python -mpave.cli` and `$PY -m`, none of which the old regex saw.

    Composed, they were **2230 passed, ruff clean**, with `two-key: not required`
    on a diff to the corpus rule Security holds alone.

    **A shadowing package is refused rather than resolved.** If both
    `pave/x/__init__.py` and `pave/x.py` exist the interpreter takes the package,
    and a check that picks one silently has already lost -- measured at 2232
    passed, zero keys, gate SATISFIED."""
    root = root or ROOT
    mentions = _gate_invocations(root)
    assert mentions, (
        "no executable line in two-key.yml mentions `pave`. The gate is invoked "
        "indirectly -- through a wrapper script, a composite action or a variable -- "
        "so this check cannot see what CI executes, and whatever now runs carries "
        "whatever rule that new file has. Name the module in the step."
    )
    listed = "\n  ".join(m.strip() for m in mentions)
    assert len(mentions) == 1, (
        f"two-key.yml has {len(mentions)} executable lines mentioning `pave`:\n  "
        f"{listed}\nExactly one is allowed, because a second is indistinguishable from "
        "a decoy: round 6 put an `echo` of the keyed command beside a real "
        "`python3 -m pave.cli` at the exact baseline. If a second invocation is "
        "genuinely needed, that is a decision to take in this file, not a check to widen."
    )
    found = _INVOCATION.search(mentions[0])
    assert found, (
        f"the one `pave` line in two-key.yml is not a recognised invocation:\n  "
        f"{mentions[0].strip()}\nIt must be `python -m <module>` (or `python3`/`py -3`). "
        "`pave gate two-key` runs the console script through `pave/cli.py`, which is on "
        "NO RULE by ADR-041 decision 7; an interpreter behind a variable cannot be "
        "followed at all. Both were measured green while the gate was disabled."
    )
    module = found.group(1)
    present = [rel for rel in _module_to_paths(module) if (root / rel).is_file()]
    assert present, f"{module} resolves to no file under {root}"
    assert len(present) == 1, (
        f"{module} resolves to BOTH {present}. A package shadows a same-named module, "
        "so the interpreter loads the package while a rule naming the module keys a file "
        "nothing executes -- measured at 2232 passed, zero keys, with the gate reporting "
        "SATISFIED. Delete one."
    )
    return present[0]


def _pave_modules_in_the_gates_process(start: str, root: pathlib.Path | None = None) -> set:
    """Every `pave/*.py` reachable by import from `start`, transitively.

    **Relative imports are resolved.** `from . import _adr` parses as
    `ImportFrom(module=None, level=1)`, and reading only `node.module` made every
    relative import invisible -- measured by the Security seat at 2224 passed, with
    the substance bar living in an unkeyed `pave/_adr.py`.

    `pave/__init__.py` is always included: it executes on ANY `pave.X` import."""
    root = root or ROOT
    seen, queue = set(), [start, "pave/__init__.py"]
    while queue:
        cur = queue.pop()
        if cur in seen:
            continue
        seen.add(cur)
        package = cur[:-3].split("/")[:-1]
        tree = ast.parse((root / cur).read_text(encoding="utf-8"), filename=cur)
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package[:len(package) - node.level + 1]
                    stem = ".".join([*base, node.module] if node.module else base)
                else:
                    stem = node.module or ""
                names = [stem] + [f"{stem}.{a.name}" for a in node.names if stem]
            for name in names:
                if name != "pave" and not name.startswith("pave."):
                    continue
                # **Both shapes.** `from pave import adrdef` with the
                # implementation in `pave/adrdef/__init__.py` is ordinary Python,
                # and guessing only `pave/adrdef.py` skipped it -- measured at 2224
                # passed with the definition on zero rules.
                stem = name.replace(".", "/")
                for cand in (f"{stem}.py", f"{stem}/__init__.py"):
                    if (root / cand).is_file():
                        queue.append(cand)
    return seen


def _fake_pave(tmp_path, files: dict):
    """Write a synthetic `pave/` package and return its root."""
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_the_walk_resolves_every_import_shape_that_has_hidden_a_definition():
    """**The walk is dead code on the honest tree, so it is exercised here.**

    `pave/twokey.py` imports no `pave` module, so on the real tree the walk returns
    its two seeds and nothing measures transitivity, the package/module distinction
    or the relative-import branch. The Platform Engineering seat replaced the entire
    body with `return {rel, "pave/__init__.py"}` at **2222 passed**.

    Every shape below is one a seat used to put `adr_records` — or the substance bar
    — in a file collecting no key, each measured green before it was closed:

      - `from . import _adr` / `from ._adr import x`  (level=1, module None or set)
      - `from pave import adrdef`, implemented in `pave/adrdef/__init__.py`
      - a second hop, because a definition can move twice
      - `from .. import x`, which leaves the package and must resolve to nothing

    Two of these were found only after the first fix shipped, which is why the
    check is pinned against a tree rather than trusted against this repository's
    current import graph."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = _fake_pave(pathlib.Path(tmp), {
            "pave/__init__.py": "",
            # relative, inside a function body: never executed by a bare import,
            # which is how it evaded the runtime half as well
            "pave/cli.py": (
                "from pave import adrdef\n"
                "def gate():\n"
                "    from . import _adr\n"
                "    from ._hop1 import thing\n"
                "    return _adr, thing, adrdef\n"),
            "pave/_adr.py": "",
            "pave/_hop1.py": "from pave import _hop2\n",   # the second hop
            "pave/_hop2.py": "",
            "pave/adrdef/__init__.py": "",                  # a PACKAGE, not a module
        })
        found = _pave_modules_in_the_gates_process("pave/cli.py", root=root)
        assert found == {
            "pave/__init__.py", "pave/cli.py", "pave/_adr.py",
            "pave/_hop1.py", "pave/_hop2.py", "pave/adrdef/__init__.py",
        }, (
            f"the walk found {sorted(found)}. Missing `_hop2` means it is not "
            "transitive; missing `_adr` or `_hop1` means `node.level` is unresolved; "
            "missing `adrdef/__init__.py` means a dotted name is only ever tried as "
            "`.py`, which is how an implementation hid in a subpackage at 2224 passed."
        )

    # An import that climbs OUT of the package resolves to nothing rather than to a
    # wrong path: `from .. import x` in `pave/cli.py` leaves `pave`.
    with tempfile.TemporaryDirectory() as tmp:
        root = _fake_pave(pathlib.Path(tmp), {
            "pave/__init__.py": "",
            "pave/cli.py": "from .. import escaped\n",
        })
        assert _pave_modules_in_the_gates_process("pave/cli.py", root=root) == {
            "pave/__init__.py", "pave/cli.py"}


def test_every_module_in_the_gates_process_collects_securitys_key():
    """**Three CRITICALs across two Security rounds, and they are one property.**

    Guarding `pave/twokey.py` guards where the decision is written. It does not
    guard the process the decision runs in -- anything loaded there can rebind it:

      - `pave/__init__.py`, 0 bytes and on no rule, running on any `pave.X` import:
        a shim rebinding `adr_records` made the live gate name a decision record for
        a file the PR never touched, at 2219 passed, zero keys.
      - `pave/cli.py`, which is what `two-key.yml` runs: the same shim rebinding
        `twokey.adr_records` AND `twokey.evaluate` left **2222 passed -- the exact
        baseline** -- with `two-key: SATISFIED` and **exit 0**. Zero keys.
      - Relocation behind a lazy relative import into `pave/_adr.py`, with
        `MIN_SUBSTANTIVE_WORDS` lowered under `if "pytest" not in sys.modules`:
        2224 passed, zero keys, the live gate accepting a one-word ADR amendment.

    **The first draft of this test walked the wrong way.** It started at
    `pave/twokey.py`, which imports nothing from `pave`, so its fixed point was
    `{__init__, twokey}` -- two paths already on the rule, compared to themselves.
    It could not go red, and it shipped a green tick. The threat is inbound, so the
    walk starts at the entrypoint CI runs and the ratchet refuses a collapse.

    **`security` specifically, not the gate's whole seat set.** Security owns every
    rule that requires an ADR and holds the adversarial corpus alone, so it is the
    seat that must be asked. Requiring the full set would reopen `pave/infra.py`'s
    seats, which ADR-043 decided, to buy nothing this ADR is about."""
    entry = _ci_gate_entrypoint()
    process = _pave_modules_in_the_gates_process(entry)
    _refuse_a_vacuous_walk(entry, process)
    for rel in sorted(process):
        seats = _seats_for(rel)
        assert "security" in seats, (
            f"{rel} is loaded in the process that runs the gate and collects "
            f"{sorted(seats) or 'NO KEYS'}. Anything in that process can rebind what "
            "`adr_records` decides, so it must not be editable without the seat that "
            "owns every ADR requirement -- ADR-052."
        )


def _refuse_a_vacuous_walk(entry: str, process: set) -> None:
    """Refuse a walk that proves nothing, and be exercisable while doing it.

    **The earlier form of this stopped working.** Round 3 asserted the walk reached
    something OUTSIDE the pinned set, because a walk returning its own seeds had
    passed as a green tick. Splitting the gate out of `pave/cli.py` took the process
    from eleven modules to four and keyed all four -- which is the goal, and it makes
    "reaches something unpinned" unsatisfiable. An anti-vacuity check that cannot
    fail is a vacuous check wearing a hat.

    The anchor is a module the gate CANNOT DECIDE WITHOUT. `twokey` holds `RULES`,
    `evaluate` and `adr_records`; a walk that does not reach it followed no edge at
    all, whatever it returned.

    A helper rather than four inline asserts, because inline they fire only when the
    walk is already broken -- neutering either was **2226 passed**, and an
    anti-vacuity guard nothing exercises is the shape it exists to refuse.
    `test_a_collapsed_walk_is_refused` calls this with the walks it must reject."""
    rules_module = pathlib.Path(twokey.__file__).resolve().relative_to(ROOT).as_posix()
    assert rules_module in process, (
        f"the walk from {entry} reached {sorted(process)} and not {rules_module}, which "
        "holds `RULES` and `evaluate` -- the gate cannot decide without it, so a walk "
        "missing it followed no edge at all. That is the round-3 defect, measured green."
    )
    assert entry in process and len(process) >= 4, (
        f"the walk from {entry} reached {len(process)} module(s): {sorted(process)}. "
        "The gate's process is the entrypoint, the package init, the rules module and "
        "the exit-code contract; fewer means imports moved out of REACH rather than out "
        "of the process."
    )


def test_the_entrypoint_is_read_from_the_workflow_not_written_down(tmp_path):
    """**Replacing the derivation with a constant is 2226 passed.** The whole point
    of reading `python -m <module>` out of `two-key.yml` is that the check follows CI
    when the invocation moves; a hardcoded `rel = "pave/twokeycli.py"` removes that
    silently while every assertion built on it stays green.

    Pinned against a synthetic workflow, because on the honest tree the derived
    answer and the constant are the same string -- the class of silence that deleted
    two load-bearing checks earlier in this milestone."""
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (tmp_path / "pave").mkdir()
    (tmp_path / "pave" / "elsewhere.py").write_text("", encoding="utf-8")
    (wf / "two-key.yml").write_text(
        "jobs:\n  two-key:\n    steps:\n      - run: |\n"
        "          python -m pave.elsewhere --base X --changed Y\n", encoding="utf-8")
    assert _ci_gate_entrypoint(root=tmp_path) == "pave/elsewhere.py", (
        "the entrypoint did not follow the workflow -- it is written down somewhere "
        "rather than read, so a moved invocation leaves the check guarding the old one"
    )

    # And a workflow naming no module is refused rather than guessed at.
    (wf / "two-key.yml").write_text(
        "jobs:\n  two-key:\n    steps:\n      - run: bash tools/run-gate.sh\n",
        encoding="utf-8")
    try:
        _ci_gate_entrypoint(root=tmp_path)
    except AssertionError:
        pass
    else:
        raise AssertionError(
            "a workflow running no `python -m` module produced an entrypoint anyway")

    # **A decoy in a comment must not be followed.** Round 5: the real command ran
    # through `GATE=pave.cli; python -m "$GATE"` while a comment above it read
    # `python -m pave.twokeycli` -- 2228 passed, the exact baseline, with the gate
    # SATISFIED at exit 0 out of an unkeyed file.
    (wf / "two-key.yml").write_text(
        "jobs:\n  two-key:\n    steps:\n      - run: |\n"
        "          # python -m pave.elsewhere --base ... --changed ...\n"
        "          GATE=pave.decoy\n"
        '          python -m "$GATE" gate two-key --base X\n', encoding="utf-8")
    try:
        followed = _ci_gate_entrypoint(root=tmp_path)
    except AssertionError:
        pass
    else:
        raise AssertionError(
            f"the derivation followed a COMMENT and returned {followed}; the step runs "
            "`python -m $GATE`, which names no module this check can see"
        )

    # **A package shadowing a same-named module is refused, not resolved.** The
    # interpreter takes the package, so a rule naming the module keys a file nothing
    # executes. Measured at 2232 passed, zero keys, with the gate SATISFIED.
    (wf / "two-key.yml").write_text(
        "jobs:\n  two-key:\n    steps:\n      - run: |\n"
        "          python -m pave.elsewhere --base X\n", encoding="utf-8")
    (tmp_path / "pave" / "elsewhere").mkdir()
    (tmp_path / "pave" / "elsewhere" / "__init__.py").write_text("", encoding="utf-8")
    try:
        _ci_gate_entrypoint(root=tmp_path)
    except AssertionError as exc:
        assert "shadows" in str(exc), exc
    else:
        raise AssertionError(
            "both `pave/elsewhere.py` and `pave/elsewhere/__init__.py` exist and the "
            "derivation picked one silently — that ambiguity IS the attack"
        )

    # ...and an honest conversion, with the module removed, resolves cleanly.
    (tmp_path / "pave" / "elsewhere.py").unlink()
    assert _ci_gate_entrypoint(root=tmp_path) == "pave/elsewhere/__init__.py"
    assert _path_to_module("pave/elsewhere/__init__.py") == "pave.elsewhere", (
        "`rel[:-3].replace('/', '.')` yields `pave.elsewhere.__init__`, which imports "
        "fine and loads a name the walk never lists — so an honest package conversion "
        "was REFUSED by the check written to catch a dishonest one"
    )


def test_a_collapsed_walk_is_refused():
    """Both guards in `_refuse_a_vacuous_walk`, called with what they must reject.

    Neutering either was **2226 passed** on the honest tree: they fire only when the
    walk is already broken, so nothing exercised them. Here they are exercised."""
    entry = _ci_gate_entrypoint()
    rules_module = pathlib.Path(twokey.__file__).resolve().relative_to(ROOT).as_posix()

    # The round-3 defect: a walk whose fixed point is its own seeds.
    for collapsed in ({entry}, {entry, "pave/__init__.py"}):
        try:
            _refuse_a_vacuous_walk(entry, collapsed)
        except AssertionError:
            continue
        raise AssertionError(f"a walk of {sorted(collapsed)} was accepted")

    # Long enough, and missing the module the gate cannot decide without -- so the
    # count is not what the anchor rests on.
    padded = {entry, "pave/__init__.py", "pave/gate.py", "pave/verdict.py",
              "pave/floors.py"} - {rules_module}
    try:
        _refuse_a_vacuous_walk(entry, padded)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"a walk of {len(padded)} modules missing {rules_module} "
                             "was accepted because it was long enough")

    # **Cases only the LENGTH guard can catch**, because the first audit of this
    # test left it silent: every collapsed walk above is refused by the rules-module
    # anchor before the length is looked at, so neutering the length assertion was
    # 25 passed. A walk that HOLDS the rules module and is still too short, and one
    # that omits the entrypoint itself, are what it alone rejects.
    for thin in ({entry, rules_module},
                 {rules_module, "pave/__init__.py", "pave/gate.py", "pave/verdict.py"}):
        try:
            _refuse_a_vacuous_walk(entry, thin)
        except AssertionError:
            continue
        raise AssertionError(
            f"a walk of {sorted(thin)} was accepted — it carries {rules_module}, so "
            "only the length-and-entrypoint guard can refuse it"
        )

    # And the honest walk is accepted, or these guards refuse everything and prove
    # nothing -- which is how a green anti-vacuity check goes wrong in the other
    # direction.
    _refuse_a_vacuous_walk(entry, _pave_modules_in_the_gates_process(entry))


def test_no_pave_module_loads_behind_the_static_walk():
    """**Runs the gate, rather than importing it.** The static walk reads `import`
    statements, so `importlib.import_module` slips past it; and importing the
    entrypoint never executes a function body, so a LAZY import of any shape --
    literal or computed -- was invisible to both halves. Measured with a correctly
    wired stub: absolute, relative and subpackage relocations were caught, and the
    lazy `importlib` one was caught only incidentally, by an unrelated test.

    So this subprocess invokes `gate two-key` on a path that triggers a rule
    requiring an ADR, which is what forces `adr_records` to run, and then asks the
    interpreter which `pave.*` modules are loaded and where each came from.

    **What this does NOT prove, because a draft of this docstring claimed it did.**
    It read *"a module that joins the gate's process while it decides cannot hide
    from that, whatever import shape put it there."* The Security seat falsified that
    twice: a dynamic import on a branch this one invocation never takes, which then
    `sys.modules.pop`s itself (2225 passed), and a `types.ModuleType` aliased over a
    name the walk already saw with `__file__ = None` (2223 passed -- the exact
    baseline). This is a post-hoc snapshot of ONE invocation: one rule, no PR body,
    no rename path, no error path.

    What it does prove is narrower and is the thing this ADR is about: an **unkeyed**
    module cannot quietly become part of the gate's process. Both falsifying plants
    needed a keyed file as their delivery vehicle -- `pave/twokey.py` and
    `pave/cli.py` -- so Security is asked either way. It does not make the process
    tamper-evident, and saying otherwise is the stated-and-absent failure this
    register exists to catch.

    A clean `sys.modules` is why it is a subprocess: once the suite has run,
    an in-process check sees everything pytest imported.

    Hermetic (G8): one local interpreter, local `git` only, no network."""
    root = ROOT
    entry = _ci_gate_entrypoint()
    module = _path_to_module(entry)
    program = (
        "import sys, json\n"
        f"import {module} as _entry\n"
        "try:\n"
        # A path on a rule that REQUIRES an ADR, so `adr_records` actually runs.
        # `--base HEAD` compares the head commit against itself: no records, a
        # refusal, and every code path this test exists to observe.
        "    _entry.main(['gate', 'two-key', '--base', 'HEAD', '--head', 'HEAD',\n"
        "                 '--changed', 'quality/adversarial/probes.yaml'])\n"
        "except SystemExit:\n"
        "    pass\n"
        "print(json.dumps({m: getattr(v, '__file__', None)\n"
        "                  for m, v in sys.modules.items()\n"
        "                  if m == 'pave' or m.startswith('pave.')}))\n"
    )
    out = subprocess.run([sys.executable, "-c", program], cwd=str(root),
                         capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, f"running {module} failed: {out.stderr}"
    tail = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""
    try:
        loaded = json.loads(tail)
    except ValueError as exc:
        raise AssertionError(
            f"the subprocess did not end with the JSON map this test reads. Last line "
            f"was {tail!r}. Something printed after it — an `atexit` hook or a banner "
            f"({exc})."
        ) from exc
    assert module in loaded, f"{module} did not load: {sorted(loaded)}"
    # The gate must actually have DECIDED, or this observes an import and nothing
    # more -- the weaker thing the first draft did while claiming the stronger one.
    assert "two-key" in out.stdout, (
        f"the gate produced no verdict, so nothing was observed deciding: {out.stdout!r}"
    )
    static = _pave_modules_in_the_gates_process(entry)
    # **Names first, because `__file__` is writable.** Re-measuring a relocation
    # produced `pave._adr.__file__ == ".../pave/twokey.py"` -- the module had copied
    # twokey's namespace and `dir()` carries `__file__` with it. A check that asks a
    # module where it lives is asking the module. `sys.modules` keys are not
    # spoofable that way: to be imported as `pave.x` it must be named `pave.x`.
    static_names = {_path_to_module(rel) for rel in static}
    for name in sorted(loaded):
        assert name in static_names, (
            f"`{name}` is loaded while the gate decides and the static walk never "
            f"reached it — it arrived dynamically, or through an import shape the walk "
            f"cannot resolve. The walk saw {sorted(static_names)}. A module in the "
            "gate's process must be visible to the check that keys it — ADR-052."
        )
    # **Keyed from the NAME, through the filesystem — never from the module.** The
    # seat check below reads `__file__`, and round 5 composed a package whose
    # `__init__.py` sets `__file__` to the keyed module it shadows: the name check
    # cannot fire (the name IS the same) and the `__file__` check reads the decoy, so
    # the two guards were each defeated by a different half of one plant while the
    # diff described each as covered by the other. A path computed from the dotted
    # name and checked against the disk asks nothing of the code being examined.
    for name in sorted(loaded):
        for rel in _module_to_paths(name):
            if not (root / rel).is_file():
                continue
            assert "security" in _seats_for(rel), (
                f"`{name}` loads while the gate decides and resolves on disk to {rel}, "
                f"which collects {sorted(_seats_for(rel)) or 'NO KEYS'} — ADR-052."
            )
    for name, filename in sorted(loaded.items()):
        # The interpreter's own `__file__`, never a path guessed from the dotted
        # name. The guess was `name.replace(".", "/") + ".py"` followed by
        # `if not ...is_file(): continue`, which skipped precisely the modules whose
        # path it got wrong -- `pave.adrdef` in `pave/adrdef/__init__.py` was waved
        # through at 2224 passed.
        if filename is None:
            continue  # a namespace package: no file to key
        path = pathlib.Path(filename).resolve()
        if not path.is_relative_to(root):
            continue  # an installed copy elsewhere; the tree is what carries rules
        rel = path.relative_to(root).as_posix()
        # `__file__` decides WHICH RULE keys a module, never whether it is known --
        # the name check above already settled that, and this one is spoofable.
        assert "security" in _seats_for(rel), (
            f"{name} loads from {rel} while the gate decides and collects "
            f"{sorted(_seats_for(rel)) or 'NO KEYS'} — ADR-052."
        )
def _workflow_running(tmp_path, *shell_lines):
    """Write a two-key workflow whose single step runs `shell_lines`."""
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    (tmp_path / "pave").mkdir(exist_ok=True)
    (tmp_path / "pave" / "elsewhere.py").write_text("", encoding="utf-8")
    (tmp_path / "pave" / "other.py").write_text("", encoding="utf-8")
    body = "".join(f"          {line}\n" for line in shell_lines)
    (wf / "two-key.yml").write_text(
        "jobs:\n  two-key:\n    steps:\n      - run: |\n" + body, encoding="utf-8")
    return tmp_path


def test_the_derivation_reads_execution_not_text(tmp_path):
    """**Round 6 reopened round 5's finding at the exact baseline.** Stripping `#`
    comments closed one SHAPE; the class stayed open because two gaps compose.

    A decoy sits anywhere a string can — an `echo`, a quoted argument, a heredoc, or
    a step GitHub skips via `if:` that this parser still reads. And the real command
    is invisible unless it is literally `python -m`: `python3 -m`, `python -mmod`,
    `$PY -m` and `pave ` — the console script `pip install -e .` creates, which runs
    through the unkeyed `pave/cli.py` — all evaded the old regex.

    Composed, they were **2230 passed, ruff clean**, with the live gate reporting
    `two-key: not required` on a change to `quality/adversarial/`, the rule Security
    holds alone.

    Pinned against synthetic workflows, because on the honest tree the strict and
    loose derivations return the same string — the silence this milestone has now
    paid for four times."""
    cases = [
        ("an echo decoy beside a real python3 run",
         ["echo 'running: python -m pave.elsewhere --base $SHA'",
          "python3 -m pave.other gate two-key --base X"]),
        ("the console script that `pip install -e .` creates",
         ["pave gate two-key --base X --changed Y"]),
        ("an interpreter behind a shell variable",
         ["PY=python3", "$PY -m pave.other gate two-key --base X"]),
        ("a second step disabled by `if:`, which the runner skips",
         ["pave gate two-key --base X", "# python -m pave.elsewhere"]),
    ]
    for why, lines in cases:
        root = _workflow_running(tmp_path, *lines)
        try:
            followed = _ci_gate_entrypoint(root=root)
        except AssertionError:
            continue
        raise AssertionError(
            f"{followed!r} was derived from a workflow whose real command is "
            f"{why} -- the check read text where it had to read execution"
        )

    # ...and the honest form is still accepted, or this refuses everything and
    # proves nothing, which is the other way a green check goes wrong.
    root = _workflow_running(
        tmp_path, 'python -m pave.elsewhere --base "$BASE" --changed "${C[@]}"')
    assert _ci_gate_entrypoint(root=root) == "pave/elsewhere.py"
