"""
M08b's residual reader: A, B, E, S and the two identities, pinned on a planted
run before the calibration call is made (SPEC/08b, PR 2; ADR-074 decision 3 §4).

`milestones/M08b/residual_attribution.py` reads the fresh run's round-1
`tokens_in` on the calibration case (A), the calibration call's (B), and the
census's estimates by key (E, S), and writes D = B − E, F = A − B − S with
signs and shares, plus each later round's growth against the replayed
transcript. These tests pin the record over the planted run, check the
arithmetic, and plant what the reader must refuse or must read as a finding:
a calibration that offered tools, round-1 figures that disagree across
samples, a calibration on a case the rule did not name, and the two fallbacks
SPEC/08b pre-registers — B from the audit record's copy, and the call
re-issued on `entitlement-010`.

Hermetic (G8). Seats: AI Quality · Platform Engineering · Security.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
READER = ROOT / "milestones" / "M08b" / "residual_attribution.py"
PLANTED = ROOT / "tests" / "fixtures" / "m08b" / "planted"
RECORD = PLANTED / "residual-attribution.json"

NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}


@pytest.fixture(scope="module")
def reader():
    spec = importlib.util.spec_from_file_location("residual_attribution", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["residual_attribution"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def planted(tmp_path):
    copy = tmp_path / "planted"
    shutil.copytree(PLANTED, copy)
    return copy


def _rewrite(path: pathlib.Path, fn) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def test_the_record_is_what_the_planted_inputs_produce(reader):
    produced = json.dumps(reader.record(PLANTED), indent=2, ensure_ascii=False) + "\n"
    assert produced == RECORD.read_text(encoding="utf-8"), (
        "residual-attribution.json under the planted fixture is not what the reader produces; "
        "re-run `python milestones/M08b/residual_attribution.py --dir tests/fixtures/m08b/planted`")


def test_the_two_identities_and_the_reading(reader):
    rec = reader.record(PLANTED)
    est, att = rec["estimates"], rec["attribution"]
    assert rec["case"] == "blackout-008" and not rec["fallback_taken"]
    assert rec["B_read_from"] == "usage.calls[0].tokens_in"
    # E and S by key from the census record: the system block's estimate plus
    # the case's own viewer turn at the census's chars-per-token; the specs' total.
    assert est["system_prompt_tokens_est"] == 909 and est["S"] == 552
    assert est["viewer_turn_tokens_est"] == 37 and est["E"] == 946
    assert est["E_band"] == [942, 947] and est["S_band"] == [549, 552]
    # **A and B are MEASURED and did not move.** Everything above is estimated from
    # HEAD's committed prompt, and M09 PR 4 moved that prompt — so every estimate
    # on this record was re-priced by an edit in a later milestone while the two
    # figures the run actually produced stood still. That contrast is the point of
    # asserting them together.
    assert att["A"] == 1980 and att["A_values"] == [1980, 1980, 1980] and att["B"] == 1470
    assert att["D"] == 524 and att["F"] == -42
    assert att["residual_A_minus_E_minus_S"] == 482 == att["D"] + att["F"]
    assert att["identity_holds"]
    assert att["F_sign"] == "negative" and att["D_sign"] == "non-negative"
    assert att["shares_of_abs"] == {"D": 0.926, "F": 0.074}
    assert att["reading"].startswith("tokeniser density")
    assert att["downward_trigger"]["armed"] is False
    growth = rec["per_round_growth"]
    assert growth["available"] and growth["chars_per_token_measured"] == 2.372
    assert len(growth["rows"]) == 121 and len(growth["more_than_a_quarter_unexplained"]) == 18
    assert growth["finding"].startswith("dated finding")


#: What this record read before M09 PR 4 moved `TOOL_SYSTEM`, and what it reads
#: after. **No run was taken between the two.**
PRE_FIX_SHARES = {"D": 0.071, "F": 0.929}
POST_FIX_SHARES = {"D": 0.214, "F": 0.786}


def test_the_estimates_are_priced_against_heads_prompt_and_this_record_has_no_era_guard(reader):
    """**The finding PR 4 leaves behind, asserted so it cannot be forgotten.**

    `milestones/M08/residual-differential.json` carries an `m02_era_text` block:
    it rebuilds the prompt as it stood at the run's commit, compares it to HEAD,
    and sets `identical_to_head`. When M09 PR 4 moved `TOOL_SYSTEM`, that record
    went red on its own guard and the divergence is now on the record.

    **This record has no such block.** `E` and `S` are estimated from HEAD's
    committed prompt and joined to `A` and `B`, which M08b measured. Moving the
    prompt therefore re-prices M08b's published attribution with nothing to say
    it happened: the committed record read *"the residual is provider-side
    framing, 501 of 463 signed (92.9%)"* and re-derives to **552 of 402 (78.6%)**
    after a prompt edit in a later milestone. On the planted fixture the same
    edit moved the shares from `{PRE_FIX_SHARES}` to `{POST_FIX_SHARES}`.

    Two sibling records, one input, one identical hazard — and only one of them
    guarded. That is CLAUDE.md's *stated and absent* ranking with the roles
    reversed: here the protection is not stated at all, which is the honest
    failure, and the reason this test states it.

    **It asserts the gap rather than closing it.** Closing it means giving this
    reader an era block, which edits a file under `milestones/M08b/` that SPEC/09's
    Definition of done reserves to re-production — so it is a dated debt (Platform
    Engineering + AI Quality; trigger: the next PR that opens
    `milestones/M08b/residual_attribution.py`) and this is the check that makes
    the next reader meet it."""
    committed = json.loads(RECORD.read_text(encoding="utf-8"))
    assert "m02_era_text" not in committed and "era_text" not in committed, (
        "this record has grown an era block. If a PR closed the debt, delete this test "
        "in that diff and assert the guard instead — a pointer to a paid debt is the "
        "same stale sentence one milestone later.")

    differential = json.loads(
        (ROOT / "milestones" / "M08" / "residual-differential.json").read_text(encoding="utf-8"))
    assert differential["m02_era_text"]["identical_to_head"] is False, (
        "the sibling's era guard reports identity with HEAD, so the divergence this "
        "test describes is gone and the contrast it draws is stale")

    # And the record really is priced against HEAD's prompt rather than the run's:
    # the estimate follows the committed text, so it moved when the text did.
    assert committed["estimates"]["system_prompt_tokens_est"] == 909, (
        "the system-prompt estimate is not the post-fix one, so this record is not "
        "being derived from HEAD's prompt and the hazard above is not the live one")
    assert PRE_FIX_SHARES != POST_FIX_SHARES


def test_a_calibration_that_offered_tools_is_refused(reader, planted):
    _rewrite(planted / "calibration.json", lambda c: c.update(tools="present"))
    with pytest.raises(SystemExit, match="tools were absent"):
        reader.record(planted)


def test_round_1_figures_that_disagree_across_samples_are_a_finding_not_a_number(reader, planted):
    def bend(answers):
        answers["blackout-008"]["usage"]["calls"][0]["tokens_in"] = 1990
        answers["blackout-008"]["usage"]["tokens_in"] += 10
    _rewrite(planted / "goldens-run-2.json", bend)
    att = reader.record(planted)["attribution"]
    assert att["A"] is None and att["A_values"] == [1980, 1990, 1980]
    assert att["reading"].startswith("unreadable") and "disagree" in att["finding"]


def test_b_falls_back_to_the_audit_records_copy_when_the_turn_was_refused(reader, planted):
    def refused(c):
        c["decision"] = "blocked"
        c["mechanism"] = "guardrail"
        c["usage"] = {"tokens_in": 0, "tokens_out": 0, "latency_ms": None}
    _rewrite(planted / "calibration.json", refused)
    rec = reader.record(planted)
    assert rec["B_read_from"].startswith("record_usage.calls[0].tokens_in")
    assert rec["attribution"]["B"] == 1470 and rec["calibration_decision"] == "blocked"


def test_a_calibration_whose_shape_says_tools_were_offered_is_refused(reader, planted):
    """Tool Owner seat, round 1: `tools: absent` is a literal the producer
    writes, so the guard on it can never disagree with the producer. The turn's
    shape can: a trajectory, or a second round, is proof the event carried tools."""
    _rewrite(planted / "calibration.json",
             lambda c: c.update(trajectory=[{"round": 1, "seq": 1, "tool": "catalog-search",
                                             "args": {"query": "derby"}, "decision": "allowed",
                                             "executed": True}]))
    with pytest.raises(SystemExit, match="carries a trajectory"):
        reader.record(planted)


def test_a_calibration_with_two_rounds_is_refused(reader, planted):
    _rewrite(planted / "calibration.json",
             lambda c: c["usage"]["calls"].append({"tokens_in": 2000, "tokens_out": 50, "latency_ms": 900}))
    with pytest.raises(SystemExit, match="a tools-absent turn is one round"):
        reader.record(planted)


def test_b_unreadable_from_either_copy_is_refused(reader, planted):
    def gone(c):
        c["usage"] = {"tokens_in": 0, "tokens_out": 0, "latency_ms": None}
        c["record_usage"] = {"tokens_in": 0, "tokens_out": 0, "latency_ms": None}
    _rewrite(planted / "calibration.json", gone)
    with pytest.raises(SystemExit, match="B is unreadable"):
        reader.record(planted)


def test_the_fallback_case_reads_a_from_the_same_case(reader, planted):
    _rewrite(planted / "calibration.json", lambda c: c.update(case="entitlement-010"))
    rec = reader.record(planted)
    assert rec["case"] == "entitlement-010" and rec["fallback_taken"]
    assert rec["attribution"]["A"] == 1980
    assert rec["estimates"]["viewer_turn_chars"] != reader.record(PLANTED)["estimates"]["viewer_turn_chars"]


def test_a_calibration_on_any_other_case_is_refused(reader, planted):
    _rewrite(planted / "calibration.json", lambda c: c.update(case="brand-020"))
    with pytest.raises(SystemExit, match="pre-registered on blackout-008"):
        reader.record(planted)


def test_a_planted_estimate_moves_the_record(reader, planted, tmp_path, monkeypatch):
    """E is read by key from the census record and never re-estimated: move the
    key and D moves by exactly that much, with F unchanged."""
    census = json.loads(reader.CENSUS.read_text(encoding="utf-8"))
    census[reader.COMPONENTS]["per_call_text"]["system_prompt"]["tokens_est"] += 100
    moved = tmp_path / "context-census.json"
    moved.write_text(json.dumps(census), encoding="utf-8")
    before = reader.record(planted)["attribution"]
    monkeypatch.setattr(reader, "CENSUS", moved)
    after = reader.record(planted)["attribution"]
    assert after["D"] == before["D"] - 100 and after["F"] == before["F"]
    assert after["residual_A_minus_E_minus_S"] == before["residual_A_minus_E_minus_S"] - 100


def test_the_reader_imports_no_network_module_and_cannot_reach_the_store():
    from test_m08b_fresh_join import ALLOWED_IMPORTS, imported_roots, store_reach

    tree = ast.parse(READER.read_text(encoding="utf-8"))
    imported = imported_roots(tree)
    assert not imported & NETWORK_MODULES
    # Security seat, round 1: a `from core import withheld` planted here
    # survived the whole suite, because no G4 root reached `milestones/`.
    # Round 2: the reflection doors, and an import allowlist.
    assert store_reach(tree) == [], f"the reader can reach the refused-content store: {store_reach(tree)}"
    assert imported <= ALLOWED_IMPORTS["residual_attribution"], sorted(imported)


def test_a_calibration_whose_audit_record_was_not_fetched_is_refused(reader, planted):
    """Platform Engineering seat, round 2: the producer swallows a fetch error
    into `record_resolved: false` and B was read from the response alone, with
    the reading printed and no mention that the witness was absent."""
    def unresolved(c):
        c["record_resolved"] = False
        c["record_usage"] = None
    _rewrite(planted / "calibration.json", unresolved)
    with pytest.raises(SystemExit, match="audit record was not fetched"):
        reader.record(planted)


def test_the_identity_field_is_computed_not_literal(reader):
    est = {"E": 800, "S": 600}
    assert reader.attribute([1500] * 3, 870, est)["identity_holds"] is True
    import re
    source = READER.read_text(encoding="utf-8")
    assert not re.search(r"identity_holds\s*[=:]\s*True", source), "the identity is a literal"
    assert "assert d + f" not in source, "the identity is an assert, stripped under -O"


def test_the_share_threshold_is_the_pre_registered_seventy_percent(reader):
    """AI Quality seat, round 1: `SHARE_NAMES` moved to 0.51 with the suite
    green, because the planted shares are 0.872 and 0.128. Pinned literally and
    exercised at the boundary: 70 of 100 names density, 69 names both, and a
    negative component's share is of its magnitude."""
    assert reader.SHARE_NAMES == 0.70
    est = {"E": 800, "S": 600}
    # A = 1500 + ...: choose A and B so D and F land where the case needs them.
    density = reader.attribute([1570] * 3, 870, est)      # D = 70, F = 100 - ... recomputed below
    assert density["D"] == 70 and density["F"] == 100 and density["reading"].startswith("both")
    exact = reader.attribute([1500] * 3, 870, est)        # D = 70, F = 30
    assert exact["D"] == 70 and exact["F"] == 30 and exact["reading"].startswith("tokeniser density")
    just_under = reader.attribute([1500] * 3, 869, est)   # D = 69, F = 31
    assert just_under["D"] == 69 and just_under["F"] == 31 and just_under["reading"].startswith("both")
    negative = reader.attribute([1330] * 3, 870, est)     # D = 70, F = -140
    assert negative["F"] == -140 and negative["F_sign"] == "negative"
    assert negative["shares_of_abs"] == {"D": 0.333, "F": 0.667} and negative["reading"].startswith("both")
    framing = reader.attribute([1300] * 3, 800, est)      # D = 0, F = -100
    assert framing["reading"].startswith("provider-side framing")


def test_a_response_usage_that_disagrees_with_the_record_is_refused(reader, planted):
    """Platform Engineering seat, round 1: the producer writes that the two
    must agree, and nothing compared them — a 400-token disagreement was
    returned silently as B on a residual bounded at 422–537."""
    _rewrite(planted / "calibration.json",
             lambda c: c["record_usage"]["calls"][0].update(tokens_in=1870))
    with pytest.raises(SystemExit, match="the two must agree before B is readable"):
        reader.record(planted)


def test_the_committed_record_is_what_the_calibration_and_the_run_produce(reader):
    """PR 3's replacement for `test_the_real_directory_has_no_calibration_yet`,
    which asserted the call had not been made. It has, on `blackout-008` with
    tools absent, and the record it produces is pinned byte for byte.

    A, B, E and S, the two identities and the signed shares are all in here, so
    a moved estimate, a re-read calibration or a substituted case is red. The
    fix is to find which input moved, never to edit the record to match."""
    produced = json.dumps(reader.record(reader.HERE), indent=2, ensure_ascii=False) + "\n"
    assert produced == (reader.HERE / "residual-attribution.json").read_text(encoding="utf-8"), (
        "milestones/M08b/residual-attribution.json is not what the committed calibration and "
        "run produce; re-run `python milestones/M08b/residual_attribution.py` and find which "
        "input moved")


# --- the cascade debt, re-dated at M09 PR 4b with a trigger that arrives in time ---
#
# ADR-075 amendment 5 §4(a) opened this debt and dated it *"the next PR that opens
# `milestones/M08b/residual_attribution.py`"*. **That trigger cannot arrive in
# time.** The hazard is not somebody opening the reader; it is somebody moving a
# prompt constant, which re-prices this record's estimates in silence and needs no
# one to open the reader at all — which is exactly how the 92.9% figure became
# 78.6% with no run taken in between. A trigger that fires after the damage is a
# record of the damage, not a guard against it.
#
# So the trigger is re-stated at M09 PR 4b (ADR-075 amendment 6) as **before the
# first PR that edits any prompt constant** — and it is this test, which is that
# PR's red check. Owner: AI Quality + Platform Engineering.
#
# The two constants are digested rather than described: `TOOL_SYSTEM` lives in
# `gateway_client.py` and the `ai_disclosure` description in `answer.schema.json`,
# and both reach this record through `milestones/M08/context-census.json`, whose
# digest is pinned beside them so a census re-produced for any other reason is red
# here too.
PROMPT_CONSTANTS_AT_M09_PR4B = {
    "services/highlights-agent/gateway_client.py":
        "83804329dc6cf3fcef2ef1f76a429c7a56e3352827b70a1575ea70c7e937eba8",
    "services/highlights-agent/evals/answer.schema.json":
        "fd301dc1722c2f38349aded4ff94c54c00f495be40dffafd58ee0965a4d39559",
    "milestones/M08/context-census.json":
        "d35c5aea98f8ae1108dd649b4a6d52efd32ce5506103a68c4ba0cc0a92885f7f",
}


def test_a_prompt_constant_may_not_move_before_this_records_era_debt_is_paid():
    """**The trigger, as a red check rather than as a row in a table.**

    M08b's published attribution — *"provider-side framing, 501 of 463 signed
    (92.9%)"* — is **era-pinned to M08b's prompt**. Its `E` and `S` are estimated
    from HEAD's committed text and joined to `A` and `B`, which the run measured;
    so the moment a prompt constant moves, the join is over text the run never
    sent and the figure re-prices itself. It already did once: M09 PR 4's two
    model-facing edits moved it to 552 of 402 (78.6%) with no run taken between
    the two readings. **92.9% is correct for its era; 78.6% is the artifact.**

    M08's sibling record has an `m02_era_text` block and caught the same drift.
    This one has none, and closing the gap means editing
    `milestones/M08b/residual_attribution.py`, which SPEC/09's Definition of done
    reserves to re-production — so the fix is dated rather than taken, and this is
    what makes the date arrive.

    **When this goes red, do one of two things, not a re-pin:** give the reader an
    era block (the debt, AI Quality + Platform Engineering), or re-publish the
    figure with the era it belongs to named beside it. Re-pinning the digests here
    to the new prompt is the one move that is not allowed — it is the guard being
    deleted by the change it exists to catch."""
    import hashlib
    for name, pinned in PROMPT_CONSTANTS_AT_M09_PR4B.items():
        text = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(text).hexdigest() == pinned, (
            f"{name} has moved since M09 PR 4b. M08b's published attribution figure is "
            "estimated against HEAD's prompt with no era pin, so this edit has just "
            "re-priced a figure whose run predates it. Pay the debt first (an era block "
            "on milestones/M08b/residual_attribution.py, AI Quality + Platform "
            "Engineering) or re-publish the figure with its era named. ADR-075 "
            "amendment 6; do NOT re-pin this constant to the new text.")


def test_the_published_figure_names_its_era():
    """The one line PR 4b put beside the number, asserted so it cannot fall off.

    Without it a reader takes 92.9% for a standing property of the system rather
    than a reading of one prompt, and re-producing the record against a later
    prompt looks like a correction instead of a different question."""
    readme = (ROOT / "milestones" / "M08b" / "README.md").read_text(encoding="utf-8")
    assert "92.9%" in readme, "the published figure is gone; re-aim this test, do not delete it"
    assert "era-pinned" in readme and "amendment 5" in readme, (
        "milestones/M08b/README.md publishes 92.9% without the line saying the figure is "
        "era-pinned to M08b's prompt and that re-production against a later prompt yields "
        "a different figure by construction (ADR-075 amendment 6)")
