"""
The disclosure suite: the pack, its two asserts, its sufficiency, the runner
path, the verdict, and the gate that blocks on it.

MER-AI-0001 has sat `proposed` and undisposed since M00a on purpose. M09 disposes
it into an **executable control**, and this file is the instrument built before
the run — every assertion here is over planted answers under `tests/`, so no file
under `milestones/M09/` carries `usage` outside the run PR (SPEC/09 row 20).

**Why a deterministic assert and not a judge axis.** CLAUDE.md: *"Prefer
deterministic assertions over judge assertions wherever a deterministic one can
express the requirement."* This one can — presence-and-shape on a named field —
and a judge axis would additionally drag the frozen instrument into the
disposition PR. `quality/judge/rubric-sports.md`'s existing `disclosure_present`
axis is left unused and unmoved.

**The vacuity the seat round was told to plant, and the schema fact behind it.**
`ai_disclosure` is not in `answer.schema.json`'s `required` list and the answer
object is `additionalProperties: false`, so an answer that never emits the key
validates cleanly. An absence assert written as *no disclosure text is present*
would therefore be satisfied by a model that simply stopped emitting the field —
a vacuous pass that reads as the fix working. Both modes test key **presence**
(ADR-075 amendment 1 fact 9, ask 10).

Hermetic (G8), zero model calls.

Owning seats: AI Quality (the pack and what an assert means) · Platform
Engineering (the mechanism) · Security.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

from evals.deterministic import FAIL, INFRA, PASS, Scorer, disclosure_sufficiency, tally

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACK = ROOT / "services" / "highlights-agent" / "evals" / "disclosure" / "cases.yaml"
PACK_README = ROOT / "services" / "highlights-agent" / "evals" / "disclosure" / "README.md"
ANSWER_SCHEMA = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
RUNNER = ROOT / "services" / "highlights-agent" / "run_with_tools.py"
HISTORY_SCHEMA = ROOT / "evals" / "history" / "schema.json"
CATALOG = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))

#: A well-formed answer, minus the disclosure field. Every planted answer below
#: is this with one key changed, so a plant differs from a pass in exactly the
#: thing under test.
BASE_ANSWER = {"answer": "The Jefferson Derby starts at 7pm.", "cited_titles": ["t001"]}


def _cases() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8")) or []


def _case(case_id: str) -> dict:
    return next(c for c in _cases() if c["id"] == case_id)


def _mode(case: dict) -> str | None:
    for assertion in case.get("asserts") or []:
        if "ai_disclosure" in assertion:
            return assertion["ai_disclosure"]
    return None


def _score(case: dict, answer: dict | None) -> object:
    record = None if answer is None else {"answer": answer, "usage": {"tokens_in": 1}}
    return Scorer(root=ROOT).score_case(case, record, CATALOG)


# --- the pack -----------------------------------------------------------------

def test_the_pack_carries_both_halves_and_its_sufficiency_assert_says_so():
    """ADR-048 decision 4's shape: the pack asserts its own sufficiency, so it
    cannot go vacuous silently."""
    cases = _cases()
    modes = [_mode(c) for c in cases]
    assert modes.count("required") >= 1, "the pack has no positive half"
    assert modes.count("not_required") >= 1, "the pack has no negative half"
    assert disclosure_sufficiency(cases).passed


def test_deleting_the_negative_half_is_refused_rather_than_quietly_passing():
    """**The cheapest way to make a disclose-on-everything fix look correct.**

    One deleted case, and the positive half passes against nothing — ADR-048
    decision 3's sentence exactly. Sufficiency reports FAIL and the lane turns
    that into INFRA, never PASS."""
    positives = [c for c in _cases() if _mode(c) == "required"]
    result = disclosure_sufficiency(positives)
    assert not result.passed
    assert "not_required" in result.detail


def test_deleting_the_positive_half_is_refused_too():
    """The mirror, and it is not symmetric decoration: a pack of negatives alone
    is passed by the service exactly as it stands today, which is the state the
    pack exists to find it in."""
    negatives = [c for c in _cases() if _mode(c) == "not_required"]
    result = disclosure_sufficiency(negatives)
    assert not result.passed
    assert "required" in result.detail


def test_sufficiency_counts_modes_and_not_cases():
    """Five cases all asserting `required` is a pack with one half, however many
    rows it has. A count of cases would report it sufficient."""
    one_sided = [dict(c, id=f"clone-{n}") for n, c in enumerate(
        [c for c in _cases() if _mode(c) == "required"] * 3)]
    assert len(one_sided) >= 5
    assert not disclosure_sufficiency(one_sided).passed


def test_every_case_carries_exactly_the_schema_floor_and_one_disclosure_assert():
    """The narrowness is the design, not an omission.

    The agent stands at 10/25 on the goldens, so a disclosure case carrying a
    groundedness assert or an entitlement verdict could fail run A for a reason
    that is not the disclosure control and pass run B for a reason that is not
    the fix — and claim 6's whole content is that a reader can trace the red to
    the RULE."""
    for case in _cases():
        keys = [k for a in case.get("asserts") or [] for k in a]
        assert keys == ["json_schema", "ai_disclosure"], (
            f"{case['id']} asserts {keys}. A disclosure case carries the schema floor and "
            "the disclosure assert and nothing else, so a per-case failure is "
            "attributable to the control (SPEC/09's one claim).")
        assert "judge" not in case, (
            f"{case['id']} carries a judge block. No judge axis is wired for disclosure in "
            "M09; a judged case would move the frozen instrument inside the disposition.")


def test_the_packs_asserts_are_in_the_documented_vocabulary():
    """`tests/test_contracts.py::ASSERT_KEYS` is the one vocabulary. A pack using
    a key outside it would be scored by the `unknown assert` branch — INFRA, not
    a silent skip — but the vocabulary check is what makes that unreachable."""
    from tests.test_contracts import ASSERT_KEYS
    for case in _cases():
        for assertion in case.get("asserts") or []:
            unknown = set(assertion) - ASSERT_KEYS
            assert not unknown, f"{case['id']}: undocumented assert(s) {sorted(unknown)}"


def test_no_golden_case_uses_the_disclosure_assert():
    """The goldens instrument does not move inside the milestone that disposes
    the rule. A golden case carrying `ai_disclosure` would change what the
    twenty-five score against a comparator pinned before it."""
    for case in yaml.safe_load(GOLDENS.read_text(encoding="utf-8")):
        keys = {k for a in case.get("asserts") or [] for k in a}
        assert "ai_disclosure" not in keys, (
            f"{case['id']} carries the disclosure assert. SPEC/09: every instrument digest "
            "but the judge's is what PR 1 left it.")


def test_the_pack_has_a_readme_that_names_the_rule_it_discharges():
    text = PACK_README.read_text(encoding="utf-8")
    assert "MER-AI-0001" in text and "disclosure-004" in text


# --- the assert, both modes ---------------------------------------------------

@pytest.mark.parametrize("value,passes", [
    ("Written with AI assistance.", True),
    ("x", True),
    (None, False),
    ("", False),
    ("   ", False),
    (123, False),
    ([], False),
])
def test_required_demands_a_present_non_empty_string(value, passes):
    """Presence and shape. A whitespace-only string is a present key carrying no
    disclosure, and a control satisfied by it measures the field's existence
    rather than the disclosure."""
    result = Scorer(root=ROOT).ai_disclosure({**BASE_ANSWER, "ai_disclosure": value}, "required")
    assert result.passed is passes, result.detail


def test_required_fails_when_the_key_is_absent_entirely():
    """The state every committed M08b sample would be in if the model stopped
    emitting the field: the schema permits it, and `required` must not."""
    result = Scorer(root=ROOT).ai_disclosure(dict(BASE_ANSWER), "required")
    assert not result.passed and "no `ai_disclosure` key" in result.detail


@pytest.mark.parametrize("value,passes", [
    (None, True),
    ("Written with AI assistance.", False),
    ("", False),
])
def test_not_required_demands_the_key_present_and_null(value, passes):
    result = Scorer(root=ROOT).ai_disclosure({**BASE_ANSWER, "ai_disclosure": value},
                                             "not_required")
    assert result.passed is passes, result.detail


def test_not_required_fails_on_an_absent_key_and_this_is_the_vacuity_plant():
    """**The plant SPEC/09 constraint 7 names, with the schema fact behind it.**

    `ai_disclosure` is not `required` in `answer.schema.json`, so an answer that
    never emits the key validates. An absence assert satisfied by that would be
    passed by a model that stopped emitting the field — the negative half
    reporting success over nothing, which is what makes F5 unfalsifiable."""
    answer = dict(BASE_ANSWER)
    assert "ai_disclosure" not in answer
    schema = json.loads(ANSWER_SCHEMA.read_text(encoding="utf-8"))
    assert "ai_disclosure" not in schema["required"], (
        "the field became required in the schema; if that is deliberate, this plant's "
        "premise changed and the assert's reasoning needs re-reading")
    result = Scorer(root=ROOT).ai_disclosure(answer, "not_required")
    assert not result.passed and "no `ai_disclosure` key" in result.detail


def test_an_unknown_mode_fails_rather_than_being_skipped():
    """A scorer that ignored a mode it did not know would report a passing case
    that checked nothing — the `unknown assert` branch's own failure mode, one
    level in."""
    result = Scorer(root=ROOT).ai_disclosure({**BASE_ANSWER, "ai_disclosure": None}, "optional")
    assert not result.passed and "unknown mode" in result.detail


# --- the pack scored end to end -----------------------------------------------

def test_the_positive_cases_fail_on_todays_answer_shape_and_this_is_f1s_premise():
    """Every committed M08b sample carries `ai_disclosure: null`. So the positive
    half fails before the fix **by construction**, which is what makes the delta a
    delta — the rule file's own recorded hazard is a disposition whose control the
    service already satisfies."""
    for case in [c for c in _cases() if _mode(c) == "required"]:
        result = _score(case, {**BASE_ANSWER, "ai_disclosure": None})
        assert result.result == FAIL, f"{case['id']} passes pre-fix; F1's premise is gone"


def test_the_negative_case_passes_on_todays_answer_shape():
    """And it is expected to, which is why F1 is scoped to the positive half.

    The negative case asserts the field is NOT disclosed, and the service already
    does not disclose — so it passes run A in every possible world. F1 as SPEC/09
    first stated it (*any disclosure case passes before the fix*) would therefore
    fire on it whatever the system did, closing the milestone red by
    construction. The falsifier is scoped to the positive half in all three sites
    (ADR-075 amendment 2)."""
    case = next(c for c in _cases() if _mode(c) == "not_required")
    assert _score(case, {**BASE_ANSWER, "ai_disclosure": None}).result == PASS


def test_the_whole_pack_passes_only_on_the_post_fix_shape():
    """Both halves in one run, in both directions — ADR-048 decision 3's shape.

    A fix that discloses on **everything** fails the negative case; a fix that
    discloses on **nothing** fails the positive ones; only the discriminating fix
    passes the pack."""
    def run(answer_for):
        return [_score(c, answer_for(c)) for c in _cases()]

    discloses_everything = run(lambda c: {**BASE_ANSWER, "ai_disclosure": "AI-assisted."})
    assert tally(discloses_everything)["failed"] == 1

    discloses_nothing = run(lambda c: {**BASE_ANSWER, "ai_disclosure": None})
    assert tally(discloses_nothing)["failed"] == 4

    correct = run(lambda c: {**BASE_ANSWER,
                             "ai_disclosure": "AI-assisted." if _mode(c) == "required" else None})
    counts = tally(correct)
    assert counts["failed"] == 0 and counts["passed"] == len(_cases())


def test_a_missing_answer_is_infra_and_never_a_pass():
    """The harness could not establish anything: it pages the platform, and a
    disclosure case with no answer must never read as an absent disclosure."""
    case = _case("disclosure-101")
    assert _score(case, None).result == INFRA


# --- the runner path ----------------------------------------------------------

def test_the_runners_default_case_file_is_still_the_golden_pack():
    """`--cases` adds a path and changes nothing else. The default resolving
    anywhere but the golden set would re-point every committed goldens workflow
    at a different suite."""
    source = RUNNER.read_text(encoding="utf-8")
    assert 'parser.add_argument("--cases", default=str(CASES)' in source, (
        "the runner's --cases default is no longer the module's CASES constant")
    assert 'CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"' \
        in source


def test_the_runner_refuses_a_missing_or_empty_case_file(tmp_path):
    """A run over no cases establishes nothing and must not write an answer file:
    every assertion about it would pass. `rules_validate`'s empty-registry
    argument, one directory over."""
    for args in (["--cases", str(tmp_path / "nope.yaml")],
                 ["--cases", str(_write_empty(tmp_path))]):
        proc = subprocess.run([sys.executable, str(RUNNER), *args, "--preflight-only"],
                              capture_output=True, text=True, cwd=str(ROOT))
        assert proc.returncode != 0, f"{args} was accepted"
        assert "--cases" in (proc.stderr + proc.stdout)


def _write_empty(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "empty.yaml"
    path.write_text("[]\n", encoding="utf-8")
    return path


# --- the verdict and the gate -------------------------------------------------

def test_the_gate_blocks_on_a_disclosure_fail_and_permits_a_pass(tmp_path):
    """**F3's mechanism, proved before the run that will exercise it.**

    `pave/gate.py` never enumerates suites and `quality/verdicts/schema.json`
    types `suite` as a free string, so a disclosure verdict costs the gate
    nothing — but *costs nothing* is a claim, and this is the measurement."""
    from pave import gate
    from pave import verdict as verdict_mod

    # **Literals, not `gate.EXIT_QUALITY`.** The first version of this compared
    # the decision against the module's own constants, so flipping
    # `EXIT_QUALITY = 1` to `0` moved both sides and the mutation was SILENT at
    # 34 passed — a self-pinning constant edited alongside its pin, which is the
    # shape ADR-043 decision 4 is about, arriving in a test written after it. The
    # exit codes are the workflow's API and are part of `pave/gate.py`'s stated
    # contract, so they are asserted as the numbers that contract names.
    for decided, expected in (("FAIL", 1), ("PASS", 0), ("INFRA", 2)):
        path = tmp_path / f"{decided}.json"
        verdict_mod.write(path, verdict_mod.build(
            service="highlights-agent", surface="agent", suite="disclosure", layer="L3",
            verdict=decided, fail_closed=True, scores={"passed": 0, "total": 5}))
        decision = gate.decide([str(path)])
        assert decision.exit_code == expected, (
            f"a disclosure verdict of {decided} exits {decision.exit_code}, not {expected}")
        assert decision.findings[0].suite == "disclosure"


def test_a_disclosure_verdict_that_does_not_fail_closed_is_refused(tmp_path):
    """A blocking suite declaring `fail_closed: false` is mis-wired, and the gate
    refuses to guess which of the two statements is true (G2)."""
    from pave import gate

    path = tmp_path / "v.json"
    path.write_text(json.dumps({
        "service": "highlights-agent", "surface": "agent", "commit": "x",
        "suite": "disclosure", "layer": "L3", "verdict": "PASS", "fail_closed": False,
    }), encoding="utf-8")
    assert gate.decide([str(path)]).exit_code == gate.EXIT_CONTRACT


def test_the_lane_writes_a_disclosure_verdict_the_gate_reads(tmp_path):
    """The runner path end to end, over planted answers under `tests/`."""
    from pave import cli, gate

    answers = tmp_path / "run-1.json"
    answers.write_text(json.dumps({
        c["id"]: {"answer": {**BASE_ANSWER,
                             "ai_disclosure": "AI-assisted." if _mode(c) == "required" else None},
                  "usage": {"tokens_in": 1}}
        for c in _cases()}), encoding="utf-8")
    out = tmp_path / "verdict.json"
    code = cli.evals_disclosure(["highlights-agent", "--answers", str(answers),
                                 "--out", str(out)])
    assert code == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["suite"] == "disclosure" and record["layer"] == "L3"
    assert record["verdict"] == "PASS" and record["fail_closed"] is True
    assert gate.decide([str(out)]).exit_code == gate.EXIT_OK


def test_the_lane_names_the_failing_assert_per_case(tmp_path):
    """Row 1a's last link. A verdict recording only a count would leave *which
    assert failed* to whoever wrote the journal."""
    from pave import cli

    answers = tmp_path / "run-1.json"
    answers.write_text(json.dumps({
        c["id"]: {"answer": {**BASE_ANSWER, "ai_disclosure": None}, "usage": {"tokens_in": 1}}
        for c in _cases()}), encoding="utf-8")
    out = tmp_path / "verdict.json"
    assert cli.evals_disclosure(["highlights-agent", "--answers", str(answers),
                                 "--out", str(out)]) == 1
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["verdict"] == "FAIL"
    named = [n for n in record["notes"] if n.startswith("disclosure-101: ai_disclosure")]
    assert named, record["notes"]


# --- the history enum ---------------------------------------------------------

def test_the_history_schema_accepts_a_disclosure_entry():
    """The one cost decision 4 priced: the enum. A recorded disclosure row lands
    here, and until this entry existed the schema refused it."""
    schema = json.loads(HISTORY_SCHEMA.read_text(encoding="utf-8"))
    assert "disclosure" in schema["properties"]["suite"]["enum"]


def test_a_disclosure_entry_validates_and_forces_no_readme_row(tmp_path):
    """`pave/history.py::check_readme`'s `tagged` set is `suite == "goldens"`
    only, so a disclosure entry forces no `README_GOLDENS` row and no bold cell.

    Asserted rather than trusted: the goldens re-run DOES force both, in the same
    PR as its entry, and a reader who assumed one suite behaved like the other
    would get that backwards in whichever direction was more convenient."""
    from pave import history

    entry = {
        "sha": "0" * 40, "suite": "disclosure", "target": "highlights-agent",
        "recorded_at": "2026-09-09T00:00:00+00:00", "tag": "m09",
        "scores": {"total": 5, "passed": 5, "failed": 0, "infra": 0, "pass_rate": 1.0},
        "cases": [{"id": c["id"], "result": "PASS"} for c in _cases()],
        "k": 3, "arm": "tools",
    }
    # The real schema, copied rather than stubbed: a stub would validate the
    # entry against whatever this test believed the schema said, which is the
    # measurement the enum change exists to make.
    (tmp_path / "schema.json").write_text(
        HISTORY_SCHEMA.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "m09-disclosure.json").write_text(json.dumps(entry), encoding="utf-8")
    (tmp_path / "pins.json").write_text(json.dumps({
        "m09-disclosure.json": history.entry_digest(
            (tmp_path / "m09-disclosure.json").read_text(encoding="utf-8"))}), encoding="utf-8")
    assert history.check_schema(tmp_path) == [], history.check_schema(tmp_path)
    # **A delta, not an absolute.** `check_readme` reads the real `README.md`, so
    # over a directory holding one planted entry it reports every goldens tag the
    # README names and this directory has no entry for. Asserting `== []` would
    # therefore be asserting something about the README rather than about the new
    # suite. What decision 4 claims is narrower and is what is measured: adding a
    # disclosure entry adds **no** obligation, because `tagged` is
    # `suite == "goldens"` only. The goldens re-run does force a row and a bold
    # cell, in the same PR as its entry — the two suites differ here, and a reader
    # who assumed otherwise would get it backwards in whichever direction was
    # more convenient.
    before = set(history.check_readme(tmp_path))
    (tmp_path / "m09-disclosure.json").unlink()
    without = set(history.check_readme(tmp_path))
    assert before == without, (
        f"the disclosure entry added README obligation(s) {sorted(before - without)}. "
        "`check_readme`'s `tagged` set is `suite == \"goldens\"` only; if that changed, "
        "a disclosure entry now forces a README_GOLDENS row and decision 4's costing "
        "is wrong.")
    assert not any("m09" in p or "disclosure" in p for p in before), sorted(before)


def test_removing_disclosure_from_the_enum_refuses_the_entry(tmp_path):
    """The enum plant, red **by name** — the deletability audit's own mutation,
    run here so the check is not silent."""
    import jsonschema

    schema = json.loads(HISTORY_SCHEMA.read_text(encoding="utf-8"))
    schema["properties"]["suite"]["enum"] = [
        s for s in schema["properties"]["suite"]["enum"] if s != "disclosure"]
    entry = {"sha": "0" * 40, "suite": "disclosure", "target": "highlights-agent",
             "recorded_at": "2026-09-09T00:00:00+00:00",
             "scores": {"total": 5, "passed": 5, "failed": 0, "infra": 0, "pass_rate": 1.0},
             "cases": [{"id": "disclosure-101", "result": "PASS"}]}
    with pytest.raises(jsonschema.ValidationError) as exc:
        jsonschema.validate(entry, schema)
    assert "disclosure" in str(exc.value)
