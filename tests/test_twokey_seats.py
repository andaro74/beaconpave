"""
The seat sets ADR-043 decided, and the plants that measured why they were needed.

**Every case below is a violating-tree test, not an honest-tree assertion.** Each
one names a diff that was measured on `07e8cd1` to leave the suite green and
collect no key, and asserts that it now collects the seats ADR-043 named. An
assertion that a rule exists proves nothing about the rule doing anything; ADR-042
prediction 7b failed for four of ten checks on its first implementation for
exactly that reason.

**Why this file and not `pave/tests/test_twokey.py`.** That file is on no rule.
This one is on the enumerated protection-test rule alongside `test_arm_scoping`
and `test_history_append_only`, which takes `ai-quality`, `security` and
`platform-eng` -- because it pins the seat sets of two rules that name
**security**, and a test that holds Security's key must not be removable without
it. The Security seat measured that removing the adversarial-corpus rule
entirely, with a plausible rationale, was blocked only by tests living in
Security-keyed files.

Hermetic (G8): reads committed files, calls nothing.
Owning seat: Security / Red Team (the invariants) - Platform Engineering (the
mechanism) - AI Quality (the rules list).
"""
from __future__ import annotations

import pathlib
import re

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
                                          "the scaffold every future service"))]
    assert len(added) == 10, (
        f"expected ADR-043's five, ADR-044's two, ADR-046's two and ADR-047's one, found "
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
    }
    for rule in added:
        key = next(k for k in required if k in rule.what)
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
