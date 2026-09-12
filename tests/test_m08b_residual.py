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
import subprocess
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


def test_the_era_debt_is_paid_and_the_guard_reports_the_divergence(reader):
    """**The debt this record carried since M09 PR 4, paid — and the guard asserted.**

    `E` and `S` are estimated from HEAD's committed prompt and joined to `A` and
    `B`, which M08b's run measured, so a prompt edit re-prices a published figure
    with no run taken. It happened: this record read *"provider-side framing, 501
    of 463 signed (92.9%)"* and re-derived to **552 of 402 (78.6%)** after M09 PR
    4 moved `TOOL_SYSTEM` and `answer.schema.json`'s `ai_disclosure` description.
    `A` and `B` did not move at all.

    The sibling `milestones/M08/residual_differential.py` had an `m02_era_text`
    block throughout and it fired correctly in that same diff. **This reader now
    has one** (M09b PR 1), and this is the check that it is load-bearing rather
    than decorative: the block must be present, must report the divergence rather
    than assert identity, and must name which inputs moved.

    This test replaces `test_the_estimates_are_priced_against_heads_prompt_and_this_record_has_no_era_guard`,
    which asserted the *absence* of the block and whose own docstring said to do
    exactly this when a PR closed the debt — a pointer to a paid debt is the same
    stale sentence one milestone later."""
    for record_path in (RECORD, ROOT / "milestones" / "M08b" / "residual-attribution.json"):
        committed = json.loads(record_path.read_text(encoding="utf-8"))
        era = committed.get("m08b_era_text")
        assert era, f"{record_path.name} has no era block; the guard has been deleted"
        assert era["commit"] == reader.M08B_ERA["commit"]
        assert era["identical_to_head"] is False, (
            "the era guard reports the prompt is what M08b's run sent. Either a prompt "
            "constant was reverted — in which case re-aim this test — or the pinned "
            "digests were re-pinned to the new text, which is the guard being deleted "
            "by the change it exists to catch.")
        assert era["inputs_that_moved"], "identical_to_head is false and nothing is named as moved"
        assert era["published_at_m08b"]["shares_of_abs"] == PRE_FIX_SHARES
        assert "artifact, not a correction" in era["what_the_attribution_below_is"]

    # And the record really is still derived from HEAD's prompt: the estimate
    # follows the committed text, so it moved when the text did. The era block
    # records that it happened; it does not restore the old number.
    #
    # `RECORD` is the PLANTED fixture, whose A and B are planted and whose shares
    # are therefore its own; the published shares belong to the real record. Both
    # read their estimates from the same committed census, which is why the
    # system-prompt estimate is asserted on the fixture and the shares are not.
    planted = json.loads(RECORD.read_text(encoding="utf-8"))
    assert planted["estimates"]["system_prompt_tokens_est"] == 909
    real = json.loads((ROOT / "milestones" / "M08b" / "residual-attribution.json").read_text(encoding="utf-8"))
    assert real["estimates"]["system_prompt_tokens_est"] == 909
    assert real["attribution"]["shares_of_abs"] == POST_FIX_SHARES
    assert PRE_FIX_SHARES != POST_FIX_SHARES


def test_the_era_figure_is_what_that_commit_actually_published(reader):
    """**92.9% is not editable prose.**

    `published_at_m08b` is a constant in the reader, and a constant can be
    quietly moved to match whatever the record says today — which would turn the
    guard into a number that always said the new thing, the exact failure the
    block exists to prevent. So it is checked against the record as that commit
    committed it, read out of the local object database.

    Hermetic (G8): `git show` against committed history, no network.
    `tests/test_cited_commits_resolve.py` reads the same way."""
    blob = subprocess.run(
        ["git", "show", f"{reader.M08B_ERA['commit']}:milestones/M08b/residual-attribution.json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if blob.returncode != 0:  # pragma: no cover - a clone without that object
        pytest.skip(f"{reader.M08B_ERA['commit'][:7]} is not in this clone's object database")
    era_record = json.loads(blob.stdout)
    published, att, est = reader.M08B_ERA["published_at_m08b"], era_record["attribution"], era_record["estimates"]

    assert (est["E"], est["S"]) == (published["E"], published["S"])
    for key in ("D", "F", "residual_A_minus_E_minus_S", "shares_of_abs"):
        assert att[key] == published[key], (
            f"published_at_m08b[{key!r}] is {published[key]!r} and "
            f"{reader.M08B_ERA['commit'][:7]} committed {att[key]!r}. The era figure is a "
            f"record of what that run read; it is not corrected, and it is not re-pinned.")
    assert era_record["per_round_growth"]["chars_per_token_measured"] == published["chars_per_token_measured"]
    assert (att["A"], att["B"]) == (reader.M08B_ERA["measured_and_unmoved"]["A"],
                                    reader.M08B_ERA["measured_and_unmoved"]["B"])

    # The point of the whole block: the measured figures are the ones that did
    # not move, and the estimated ones are the ones that did.
    head = json.loads((ROOT / "milestones" / "M08b" / "residual-attribution.json").read_text(encoding="utf-8"))
    assert (head["attribution"]["A"], head["attribution"]["B"]) == (att["A"], att["B"])
    assert (head["estimates"]["E"], head["estimates"]["S"]) != (est["E"], est["S"])


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


# --- the cascade debt, opened at M09 PR 4, re-dated at PR 4b, PAID at M09b PR 1 ---
#
# ADR-075 amendment 5 §4(a) opened it and dated it *"the next PR that opens
# `milestones/M08b/residual_attribution.py`"*. Amendment 6 §7 re-dated it to
# **before the first PR that edits any prompt constant**, because the hazard is
# not somebody opening the reader — it is somebody moving a prompt constant,
# which re-prices this record's estimates in silence and needs nobody to open the
# reader at all. That is exactly how 92.9% became 78.6% with no run in between.
#
# It was enforced by `PROMPT_CONSTANTS_AT_M09_PR4B`, three digests that went red
# on the next prompt edit and named the debt in the failure message. **That pin
# is retired here, in the diff that pays the debt**, and not before: a pin whose
# whole purpose is to force a fix outlives its purpose the moment the fix lands,
# and leaving it would mean the next legitimate prompt edit meets a red check
# pointing at work already done. The two tests above replace it — the reader has
# an era block, the block reports the divergence rather than asserting identity,
# and the era figure is held to what that commit actually committed.
#
# The remedy the pin named as inadmissible is still inadmissible: re-pinning the
# digests to a new prompt is the guard being deleted by the change it exists to
# catch. `M08B_ERA["inputs_sha256_at_m08b"]` is a record of one commit's text and
# is never updated; `identical_to_head` is supposed to be false and stay false.
#
# Owner: AI Quality + Platform Engineering.
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
