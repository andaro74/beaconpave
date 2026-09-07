"""
M08b's `recommend-003` reader: F against G, by the rule ADR-074 decision 3 §3
wrote before the run, reproducing the prior from M07's files (SPEC/08b, PR 2).

ADR-074 decision 3 §3 recorded the M07 prior by hand — G = 8, F = 1, a topic
question — so the fresh reading would be compared to something. ADR-074
amendment 1 (§2, row 4) found that a second hand count compared to the first
is not a reading. `milestones/M08b/answer_channel.py` produces both numbers
from the answer files, the refusals sidecar and the operator's grants file;
the first test here is the prior through that code path, and a disagreement
with the hand count is a finding about the hand count, recorded and not
silently fixed.

Hermetic (G8). No held text is read anywhere: the grants file carries a
boolean per refused sample and nothing else. Seats: AI Quality · Platform
Engineering · Security.
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
READER = ROOT / "milestones" / "M08b" / "answer_channel.py"
PLANTED = ROOT / "tests" / "fixtures" / "m08b" / "planted"
RECORD = PLANTED / "answer-channel.json"
M07 = ROOT / "milestones" / "M07"
PRIOR_GRANTS = ROOT / "milestones" / "M08b" / "prior-withheld-grants.json"

NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}


@pytest.fixture(scope="module")
def reader():
    spec = importlib.util.spec_from_file_location("answer_channel", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["answer_channel"] = module
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


def test_the_prior_is_reproduced_from_m07s_files(reader):
    """ADR-074 decision 3 §3, by the reader and not by hand: G = 8 — the seven
    by majority answer and `recommend-003` by its held grants — and F = 1."""
    grants = json.loads(PRIOR_GRANTS.read_text(encoding="utf-8"))["grants"]
    sidecar = json.loads((M07 / "goldens-run-refusals.json").read_text(encoding="utf-8"))
    result = reader.reading([M07 / f"goldens-run-{n}.json" for n in (1, 2, 3)], sidecar, grants)
    assert result["G"] == reader.PRIOR["G"] == 8
    assert result["G_cases"] == ["blackout-007", "blackout-009", "brand-020", "concise-022",
                                 "entitlement-011", "grounded-017", "headroom-005", "recommend-003"]
    assert result["F"] == reader.PRIOR["F"] == 1 and result["F_cases"] == ["recommend-003"]
    assert result["reading"] == reader.PRIOR["reading"] == "topic question"
    assert result["F_subset_of_G"] and result["dec001_cases"] == []
    assert result["mixed_grants_not_counted"] == []
    recommend = result["per_case"]["recommend-003"]
    assert recommend["answered_grants"] == 1 and recommend["held_grants"] == 2
    assert recommend["refused_on_answer_by_entitlement_topic"] == [1, 3]


def test_the_record_is_what_the_planted_inputs_produce(reader):
    produced = json.dumps(reader.record(PLANTED), indent=2, ensure_ascii=False) + "\n"
    assert produced == RECORD.read_text(encoding="utf-8"), (
        "answer-channel.json under the planted fixture is not what the reader produces; "
        "re-run `python milestones/M08b/answer_channel.py --dir tests/fixtures/m08b/planted`")


def test_the_planted_run_reads_as_a_topic_question(reader):
    rec = reader.record(PLANTED)
    assert rec["G"] == 5 and rec["G_cases"] == ["blackout-007", "blackout-009", "brand-020",
                                                 "entitlement-011", "recommend-003"]
    assert rec["F"] == 1 and rec["F_cases"] == ["recommend-003"] and rec["reading"] == "topic question"
    assert rec["prior_m07"] == reader.PRIOR
    # brand-020: refused once, on the answer channel, held text not a grant —
    # in G by its two answered grants, not in F (not refused by majority).
    brand = rec["per_case"]["brand-020"]
    assert brand["answered_grants"] == 2 and brand["held_grants"] == 0
    assert not brand["refused_by_majority"] and brand["in_G"] and not brand["in_F"]


def test_a_refused_sample_without_a_reading_is_refused(reader, planted):
    """A missing reading is not a non-grant: the operator must read the held
    text with `read_withheld.py --show` and record it before F exists."""
    _rewrite(planted / "withheld-grants.json", lambda g: g["grants"]["recommend-003"].pop("s3"))
    with pytest.raises(SystemExit, match="no reading for recommend-003 s3"):
        reader.record(planted)


def test_dec001s_shape_reads_as_neither_and_re_opens_adr_068(reader, planted):
    """Two plants, because the first alone was silent in the deletability
    audit: `recommend-003` leaves G whether or not DEC-001 is checked (one held
    grant is not a majority), so `brand-020` — in G by two answered grants — is
    the case that shows the check is load-bearing."""
    def mark(g):
        g["grants"]["recommend-003"]["s1"].update(dec001_shape=True)
        g["grants"]["brand-020"]["s1"].update(dec001_shape=True)
    _rewrite(planted / "withheld-grants.json", mark)
    rec = reader.record(planted)
    assert rec["dec001_cases"] == ["brand-020", "recommend-003"]
    for case in ("recommend-003", "brand-020"):
        assert case not in rec["F_cases"] and case not in rec["G_cases"]
    assert rec["F"] == 0 and rec["reading"] == "not reproduced"


def test_a_refusal_on_two_channels_still_counts_as_the_answer_channel(reader, planted):
    """Security seat, round 2: exact list equality read a two-channel block —
    the reason `channels` is a tuple — as no answer-channel block, and a
    stricter refusal turned the reading into *not reproduced*. Membership,
    and the multi-channel record surfaced beside the reading."""
    def widen(sidecar):
        sidecar["refusals"]["recommend-003"]["s3"]["channels"] = ["answer", "tool_output"]
    _rewrite(planted / "goldens-run-refusals.json", widen)
    rec = reader.record(planted)
    assert rec["F"] == 1 and rec["F_cases"] == ["recommend-003"] and rec["reading"] == "topic question"
    assert rec["multi_channel_refusals"] == ["recommend-003 s3 ['answer', 'tool_output']"]


@pytest.mark.parametrize("label,mutate,expect", [
    ("held text in _what_this_is", lambda g: g.update(_what_this_is="the viewer can watch it now: ..."),
     "not the one sentence"),
    ("held text in source", lambda g: g.update(source="the texts read: the viewer can watch the cited replay"),
     "not a short list of paths"),
    ("a source item over 80 characters", lambda g: g.update(source="milestones/M08/" + "a" * 80),
     "not a short list of paths"),
    ("seven sources", lambda g: g.update(source="; ".join(["ADR-074"] * 7)),
     "not a short list of paths"),
    ("read_on not a date", lambda g: g.update(read_on="read on the sixth; the texts said the viewer may watch"),
     "not a date"),
], ids=lambda x: x if isinstance(x, str) and " " in x else None)
def test_the_grants_files_metadata_carries_no_text(reader, planted, label, mutate, expect):
    """Legal/S&P seat, round 2: the vocabulary check refused text in the values
    and admitted it beside them, in three strings bounded by nothing while
    three docstrings said no held text could be here. `_what_this_is` is one
    sentence, `read_on` a date, `source` a short list of paths and ADR ids."""
    _rewrite(planted / "withheld-grants.json", mutate)
    with pytest.raises(SystemExit, match=expect):
        reader.record(planted)


def test_a_refusal_on_another_channel_does_not_count_toward_f(reader, planted):
    """F is refusals on the `answer` channel by the entitlement topic and no
    other: move one of `recommend-003`'s two refusals to `tool_output` and the
    case is neither F (one on-answer refusal is not a majority) nor G (one held
    grant is not either), so the question reads as not reproduced."""
    def move(sidecar):
        sidecar["refusals"]["recommend-003"]["s3"]["channels"] = ["tool_output"]
    _rewrite(planted / "goldens-run-refusals.json", move)
    # ...and with it the grants entry for that sample, which the shape check
    # would otherwise refuse first as a reading of a sample not refused on the
    # answer channel — the right refusal, and not the one under test here.
    _rewrite(planted / "withheld-grants.json", lambda g: g["grants"]["recommend-003"].pop("s3"))
    rec = reader.record(planted)
    assert rec["per_case"]["recommend-003"]["refused_on_answer_by_entitlement_topic"] == [1]
    assert rec["per_case"]["recommend-003"]["held_grants"] == 1
    assert "recommend-003" not in rec["G_cases"] and rec["F"] == 0
    assert rec["reading"] == "not reproduced"


def test_f_equals_g_reads_as_an_answer_policy_question(reader, planted):
    """Every grant the platform produced fired the topic: strip the answered
    grants so G is the held one alone."""
    for n in (1, 2, 3):
        def strip(answers):
            for case_id, entry in answers.items():
                verdict = (entry.get("answer") or {}).get("entitlement")
                if case_id != "recommend-003" and isinstance(verdict, dict) and verdict.get("entitled"):
                    verdict["entitled"] = False
        _rewrite(planted / f"goldens-run-{n}.json", strip)
    rec = reader.record(planted)
    assert rec["G"] == rec["F"] == 1 and rec["reading"] == "answer-policy question"


def test_no_majority_grant_anywhere_is_unreadable(reader, tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    for n in (1, 2, 3):
        (run / f"goldens-run-{n}.json").write_text(json.dumps({
            "blackout-001": {"answer": {"answer": "no", "cited_titles": [], "entitlement": None,
                                        "ai_disclosure": None},
                             "usage": {"tokens_in": 1, "tokens_out": 1, "latency_ms": 1}}}),
            encoding="utf-8")
    (run / "goldens-run-refusals.json").write_text(json.dumps({"refusals": {}, "per_sample_refused": {}}),
                                                   encoding="utf-8")
    (run / "withheld-grants.json").write_text(
        json.dumps({"_what_this_is": reader.GRANTS_WHAT_THIS_IS, "grants": {}}), encoding="utf-8")
    rec = reader.record(run)
    assert rec["G"] == 0 and rec["reading"].startswith("unreadable: G = 0")


def test_check_compares_and_writes_nothing(reader, planted):
    assert reader.main(["--dir", str(planted)]) == 0
    assert reader.main(["--dir", str(planted), "--check"]) == 0
    (planted / "answer-channel.json").unlink()
    assert reader.main(["--dir", str(planted), "--check"]) == 1
    assert not (planted / "answer-channel.json").exists()


def test_the_real_directory_has_no_run_yet(reader):
    with pytest.raises(SystemExit, match="does not exist"):
        reader.record(reader.HERE)


def test_the_reader_imports_no_network_module_and_opens_no_store():
    from test_m08b_fresh_join import ALLOWED_IMPORTS, imported_roots, store_reach

    tree = ast.parse(READER.read_text(encoding="utf-8"))
    imported = imported_roots(tree)
    assert not imported & NETWORK_MODULES
    assert imported <= ALLOWED_IMPORTS["answer_channel"], sorted(imported)
    # Structural, not textual: the first version of this assertion searched the
    # source for the store reader's name and went red on the docstring saying why
    # it must not be called (M06b's finding 7). Then the Security seat walked
    # through `importlib.import_module("core.withheld")` with the suite green
    # (round 1); the vocabulary check now refuses the dynamic-import door too.
    assert "withheld" not in imported and "read_withheld" not in imported
    assert "core" not in imported and "gateway_client" not in imported
    assert store_reach(tree) == [], f"the reader can reach the refused-content store: {store_reach(tree)}"


def test_the_prior_grants_file_is_pinned_byte_for_byte():
    """Legal/S&P seat, round 1: the prior was self-enforcing — the file and
    `PRIOR` could move together on the file's keys. The file's digest is a
    constant here, so the M07 reading is append-only in a second place."""
    import hashlib
    digest = hashlib.sha256(PRIOR_GRANTS.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert digest == "b3cb400ed088d58c5481b4eb7b767932b82e52cef8ae3c5f50bd992d551486df", (
        "milestones/M08b/prior-withheld-grants.json moved; the M07 reading is a record, "
        "and a correction to it is an ADR-074 amendment, not an edit")


# --- the grants file's vocabulary (Security seat, round 1) ---------------------------

def _grants_plant(planted, fn):
    _rewrite(planted / "withheld-grants.json", fn)


@pytest.mark.parametrize("label,mutate,expect", [
    ("held text beside the grant",
     lambda g: g["grants"]["recommend-003"]["s1"].update(text="the viewer can watch it now"),
     "must carry exactly"),
    ("the held text as the grant's value",
     lambda g: g["grants"]["recommend-003"]["s1"].update(grant="the viewer can watch it now"),
     "not a boolean; a string there is text"),
    ("the string 'false' as a grant",
     lambda g: g["grants"]["recommend-003"]["s3"].update(grant="false"),
     "not a boolean"),
    ("DEC-001 on a case never refused on the answer channel",
     lambda g: g["grants"].update({"blackout-001": {"s1": {"grant": False, "dec001_shape": True}}}),
     "not refused is refused"),
    ("a fabricated case",
     lambda g: g["grants"].update({"nonesuch-099": {"s1": {"grant": True, "dec001_shape": False}}}),
     "not refused is refused"),
    ("a sample never refused",
     lambda g: g["grants"]["recommend-003"].update({"s2": {"grant": True, "dec001_shape": False}}),
     "not refused is refused"),
    ("a missing key",
     lambda g: g["grants"]["recommend-003"]["s1"].pop("dec001_shape"),
     "must carry exactly"),
    ("a key outside the file's vocabulary",
     lambda g: g.update(notes="the texts read: ..."),
     "keys outside"),
], ids=lambda x: x if isinstance(x, str) and " " in x else None)
def test_the_grants_file_admits_two_booleans_per_refused_sample_and_nothing_else(
        reader, planted, label, mutate, expect):
    """Every value the reading uses is a boolean on a sample the sidecar says
    was refused on the answer channel by the entitlement topic. A string where
    a boolean belongs is refused before it can be truthy, so the file cannot
    carry held text as data and a `"false"` cannot count as a grant; an entry
    for a sample never refused is refused, not ignored."""
    _grants_plant(planted, mutate)
    with pytest.raises(SystemExit, match=expect):
        reader.record(planted)
