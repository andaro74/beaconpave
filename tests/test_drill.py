"""
The drill's writer, `pave/drill.py`, on synthetic captions only.

Each SPEC/11 constraint the writer carries is held by a case that plants the defect:
  1. nothing goes through `pave.verdict.build` -- the writer imports no `pave` module;
  2. the schema holds no claim value;
  3. no default for the owner, the window, the threshold or the caption source -- each
     one missing writes nothing;
  4. no key, no artifact.
Also ADR-080 decision 2's defect the arc cannot see: **a delta drill after an edit that
does not fix the gap still writes NO-GO.**

**Synthetic, never the arc.** Every case builds its own git repository, scenario and
captions under `tmp_path`. The values differ from SPEC/11's pins on purpose:
- another event and tier;
- another owner;
- a 2 s threshold;
- cue ids `s01`..`s04`.

So no case here is a reading of the seeded, control or fixed run, and a writer that
hard-coded the pins fails. The committed scenario and fixture are read only by
`tests/test_drill_pins.py`, which compares their shape to SPEC/11 and runs no drill.

Hermetic (G8): git on temporary repositories; no network, no model.
Owning seat: Platform Engineering (the writer) - AI Quality (what it decides).
"""
from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import hmac
import json
import pathlib
import subprocess

import jsonschema
import pytest

from pave import drill

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "quality" / "drill" / "go-no-go.schema.json"
KEY = "synthetic-test-key-never-a-run-key-0000"
ENV = {"BEACONPAVE_DRILL_KEY": KEY}
NOW = dt.datetime(2030, 1, 2, 3, 4, 5, tzinfo=dt.timezone.utc)
CAPTIONS = "drill/fixtures/synthetic/captions.vtt"
SCENARIO = {
    "scenario": "caption-check",
    "rule": "max-gap",
    "max_gap_s": 2.0,
    "owner": {"seat": "synthetic-seat", "oncall": "webhook:synthetic-oncall"},
    "fix_by_window_s": {"7": 7200, "8": 60},
    "events": {"synthetic-event": {"captions": CAPTIONS},
               "other-event": {"captions": CAPTIONS}},
}
#: four 3 s cues, contiguous: no gap
CLEAN = [("s01", 0, 3000), ("s02", 3000, 6000), ("s03", 6000, 9000), ("s04", 9000, 12000)]
#: `s02` removed: a 3 s gap between `s01` and `s03`, above the 2 s threshold
GAPPED = [CLEAN[0], CLEAN[2], CLEAN[3]]


def _stamp(ms: int) -> str:
    hours, rest = divmod(ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    seconds, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def _vtt(cues, texts=None) -> str:
    lines = ["WEBVTT", ""]
    for cue_id, start, end in cues:
        lines += [cue_id, f"{_stamp(start)} --> {_stamp(end)}",
                  (texts or {}).get(cue_id, f"synthetic line {cue_id}"), ""]
    return "\n".join(lines)


def _git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=drill-test",
         "-c", "user.email=drill-test@example.invalid", "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True)


def _commit(root, message="step"):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--allow-empty", "-m", message)


def _captions(root, text):
    path = root / CAPTIONS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _repo(base, scenario=SCENARIO, cues=CLEAN) -> pathlib.Path:
    root = base / "repo"
    root.mkdir(parents=True)
    _git(root, "init", "-q")
    _git(root, "config", "core.autocrlf", "false")
    (root / "drill" / "scenarios").mkdir(parents=True)
    (root / drill.SCENARIO_FILE).write_text(json.dumps(scenario), encoding="utf-8")
    _captions(root, _vtt(cues))
    _commit(root, "synthetic repository")
    return root


def _write(root, base, name, *, event="synthetic-event", tier=7, delta=None, env=ENV):
    out = base / "out" / name
    return out, drill.run(event, tier, out, delta, root=root, env=env, now=NOW)


def _refused(root, base, name="refused.json", match=None, **kwargs):
    out = base / "out" / name
    with pytest.raises(drill.Refused, match=match):
        drill.run(kwargs.pop("event", "synthetic-event"), kwargs.pop("tier", 7), out,
                  kwargs.pop("delta", None), root=root, env=kwargs.pop("env", ENV), now=NOW)
    assert not out.exists(), f"{out} was written by a run that was refused"


# --- the decision -------------------------------------------------------------

def test_a_file_with_no_gap_writes_go_with_no_owner_and_no_fix_by(tmp_path):
    root = _repo(tmp_path)
    out, artifact = _write(root, tmp_path, "go.json")
    assert json.loads(out.read_text(encoding="utf-8")) == artifact
    assert artifact["decision"] == "GO"
    assert artifact["findings"] == []
    assert artifact["mode"] == "full"
    assert "owner" not in artifact and "fix_by" not in artifact and "prior_sha256" not in artifact


def test_a_gap_above_the_threshold_writes_no_go_naming_both_cues_the_owner_and_the_window(tmp_path):
    root = _repo(tmp_path, cues=GAPPED)
    _, artifact = _write(root, tmp_path, "no-go.json")
    assert artifact["decision"] == "NO-GO"
    assert artifact["findings"] == [{"scenario": "caption-check", "rule": "max-gap",
                                     "after_cue": "s01", "before_cue": "s03", "gap_s": 3.0}]
    assert artifact["owner"] == {"seat": "synthetic-seat", "oncall": "webhook:synthetic-oncall"}
    assert artifact["ran_at"] == "2030-01-02T03:04:05Z"
    assert artifact["fix_by"] == "2030-01-02T05:04:05Z", "tier 7's window is 7200 s"


def test_the_window_is_the_tiers_own(tmp_path):
    root = _repo(tmp_path, cues=GAPPED)
    _, artifact = _write(root, tmp_path, "tier8.json", tier=8)
    assert artifact["fix_by"] == "2030-01-02T03:05:05Z", "tier 8's window is 60 s"


def test_a_gap_equal_to_the_threshold_is_not_a_finding_and_one_millisecond_more_is(tmp_path):
    at = _repo(tmp_path / "at", cues=[("s01", 0, 3000), ("s02", 5000, 8000)])
    assert _write(at, tmp_path, "at.json")[1]["decision"] == "GO"
    over = _repo(tmp_path / "over", cues=[("s01", 0, 3000), ("s02", 5001, 8000)])
    _, artifact = _write(over, tmp_path, "over.json")
    assert artifact["decision"] == "NO-GO"
    assert artifact["findings"][0]["gap_s"] == 2.001


def test_a_timestamp_with_no_hour_field_is_read(tmp_path):
    root = _repo(tmp_path)
    _captions(root, "WEBVTT\n\ns01\n00:00.000 --> 00:03.000\na\n\n"
                    "s02\n00:00:06.000 --> 01:00:00.000\nb\n")
    _commit(root)
    _, artifact = _write(root, tmp_path, "short.json")
    assert artifact["findings"] == [{"scenario": "caption-check", "rule": "max-gap",
                                     "after_cue": "s01", "before_cue": "s02", "gap_s": 3.0}]


@pytest.mark.parametrize("text, match", [
    ("not a caption file\n", "not WebVTT"),
    ("WEBVTT\n\n00:00:00.000 --> 00:00:03.000\nno id\n", "no id"),
    ("WEBVTT\n\ns01\n00:00:03.000 --> 00:00:01.000\nbackwards\n", "ends before it starts"),
    ("WEBVTT\n\ns01\n00:00:00.000 --> 00:00:01.000\na\n\ns01\n00:00:01.000 --> 00:00:02.000\nb\n",
     "appears twice"),
    ("WEBVTT\n\ns01\nlater\n", "no timing line"),
])
def test_an_unreadable_caption_file_writes_nothing(tmp_path, text, match):
    root = _repo(tmp_path)
    _captions(root, text)
    _commit(root)
    _refused(root, tmp_path, match=match)


# --- SPEC/11 constraint 3: no default for a claim value --------------------------

@pytest.mark.parametrize("path", [
    ("owner", "seat"), ("owner", "oncall"), ("owner",), ("max_gap_s",),
    ("fix_by_window_s", "7"), ("fix_by_window_s",), ("events", "synthetic-event"),
    ("events",), ("scenario",), ("rule",),
])
def test_a_missing_claim_value_writes_nothing(tmp_path, path):
    scenario = copy.deepcopy(SCENARIO)
    node = scenario
    for part in path[:-1]:
        node = node[part]
    del node[path[-1]]
    root = _repo(tmp_path, scenario=scenario, cues=GAPPED)
    _refused(root, tmp_path)


@pytest.mark.parametrize("field, value", [
    ("max_gap_s", "2.0"), ("max_gap_s", True), ("max_gap_s", -1), ("rule", "min-gap"),
    ("fix_by_window_s", {"7": 0}), ("fix_by_window_s", {"7": "7200"}),
    ("owner", {"seat": "", "oncall": "webhook:x"}),
])
def test_a_claim_value_of_the_wrong_shape_writes_nothing(tmp_path, field, value):
    root = _repo(tmp_path, scenario={**SCENARIO, field: value}, cues=GAPPED)
    _refused(root, tmp_path)


def test_a_missing_scenario_file_writes_nothing(tmp_path):
    root = _repo(tmp_path)
    (root / drill.SCENARIO_FILE).unlink()
    _commit(root)
    _refused(root, tmp_path, match="scenario file")


# --- SPEC/11 constraint 4, and an artifact never overwritten --------------------

@pytest.mark.parametrize("env", [{}, {"BEACONPAVE_DRILL_KEY": ""},
                                 {"BEACONPAVE_DRILL_KEY": "k" * 31}])
def test_no_key_no_artifact(tmp_path, env):
    root = _repo(tmp_path, cues=GAPPED)
    _refused(root, tmp_path, match="key", env=env)


def test_an_existing_artifact_is_never_overwritten(tmp_path):
    root = _repo(tmp_path)
    out = tmp_path / "out" / "taken.json"
    out.parent.mkdir(parents=True)
    out.write_bytes(b"the bytes already here")
    with pytest.raises(drill.Refused, match="already exists"):
        drill.run("synthetic-event", 7, out, root=root, env=ENV, now=NOW)
    assert out.read_bytes() == b"the bytes already here"


# --- conformance: a deliverable, not a claim term (SPEC/11) -----------------------

def test_the_artifact_is_validated_before_anything_is_written(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    real = drill.build_artifact
    monkeypatch.setattr(drill, "build_artifact", lambda **kw: {**real(**kw), "undeclared": 1})
    _refused(root, tmp_path, match="undeclared")


def test_the_schema_refuses_an_undeclared_key_at_every_level(tmp_path):
    root = _repo(tmp_path, cues=GAPPED)
    _, artifact = _write(root, tmp_path, "shape.json")
    validator = jsonschema.Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    assert not list(validator.iter_errors(artifact))
    for planted in ({**artifact, "extra": 1},
                    {**artifact, "owner": {**artifact["owner"], "extra": 1}},
                    {**artifact, "findings": [{**artifact["findings"][0], "extra": 1}]},
                    {**artifact, "inputs": {**artifact["inputs"], "extra": 1}},
                    {**artifact, "signature": {**artifact["signature"], "extra": 1}}):
        assert list(validator.iter_errors(planted)), planted


# --- the signature and the file ---------------------------------------------------

def test_the_signature_is_hmac_sha256_over_the_pinned_canonical_form(tmp_path):
    root = _repo(tmp_path, cues=GAPPED)
    _, artifact = _write(root, tmp_path, "signed.json")
    unsigned = {k: v for k, v in artifact.items() if k != "signature"}
    message = json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    key = KEY.encode("utf-8")
    assert artifact["signature"] == {
        "alg": "HMAC-SHA256",
        "key_id": hashlib.sha256(key).hexdigest()[:16],
        "value": hmac.new(key, message, hashlib.sha256).hexdigest(),
    }


def test_the_file_on_disk_is_the_pinned_layout(tmp_path):
    root = _repo(tmp_path, cues=GAPPED)
    out, artifact = _write(root, tmp_path, "layout.json")
    assert out.read_bytes() == (json.dumps(artifact, indent=2, ensure_ascii=False)
                                + "\n").encode("utf-8")


def test_the_commit_and_the_tree_state_are_recorded(tmp_path):
    root = _repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    _, clean = _write(root, tmp_path, "clean.json")
    assert clean["commit"] == head
    assert clean["tree_clean"] is True
    (root / "stray.txt").write_text("uncommitted", encoding="utf-8")
    _, dirty = _write(root, tmp_path, "dirty.json")
    assert dirty["tree_clean"] is False


def test_outside_a_git_repository_nothing_is_written(tmp_path):
    root = tmp_path / "plain"
    (root / "drill" / "scenarios").mkdir(parents=True)
    (root / drill.SCENARIO_FILE).write_text(json.dumps(SCENARIO), encoding="utf-8")
    _captions(root, _vtt(CLEAN))
    _refused(root, tmp_path, match="commit")


# --- the delta drill ----------------------------------------------------------------

def _seeded(base):
    """A NO-GO, then a commit that changes nothing but adds a file -- the shape of PR 3's
    commit between the seeded run and the control, on synthetic data."""
    root = _repo(base, cues=GAPPED)
    prior, first = _write(root, base, "seeded.json")
    (root / "log.txt").write_text("the seeded artifact, committed", encoding="utf-8")
    _commit(root)
    return root, prior, first


def test_a_delta_without_the_fix_stays_no_go_for_the_same_gap(tmp_path):
    root, prior, first = _seeded(tmp_path)
    _, control = _write(root, tmp_path, "control.json", delta=prior)
    assert control["mode"] == "delta"
    assert control["decision"] == "NO-GO"
    assert control["findings"] == first["findings"]
    assert control["commit"] != first["commit"]
    assert control["inputs"] == first["inputs"]
    assert control["prior_sha256"] == hashlib.sha256(prior.read_bytes()).hexdigest()
    assert control["owner"] == first["owner"]


def test_a_delta_after_an_edit_that_does_not_fix_the_gap_stays_no_go(tmp_path):
    """ADR-080 decision 2: the one defect the arc cannot catch. A delta drill that said GO on
    ANY change to the failing input passes all five falsifiers, because the fix is the only
    edit to the fixture. Here the file changes and the gap stays."""
    root, prior, first = _seeded(tmp_path)
    _captions(root, _vtt(GAPPED, texts={"s03": "reworded, and the gap is still there"}))
    _commit(root)
    _, edited = _write(root, tmp_path, "edited.json", delta=prior)
    assert edited["inputs"] != first["inputs"], "the plant did not change the caption file"
    assert edited["decision"] == "NO-GO"
    assert edited["findings"] == first["findings"]


def test_a_delta_after_the_fix_writes_go(tmp_path):
    root, prior, first = _seeded(tmp_path)
    _captions(root, _vtt(CLEAN))
    _commit(root)
    _, fixed = _write(root, tmp_path, "fixed.json", delta=prior)
    assert fixed["decision"] == "GO"
    assert fixed["findings"] == []
    assert "owner" not in fixed and "fix_by" not in fixed
    assert fixed["prior_sha256"] == hashlib.sha256(prior.read_bytes()).hexdigest()


def test_a_delta_refuses_a_prior_whose_signature_does_not_verify(tmp_path):
    root, prior, _ = _seeded(tmp_path)
    tampered = tmp_path / "tampered.json"
    tampered.write_bytes(prior.read_bytes().replace(b'"webhook:synthetic-oncall"',
                                                    b'"webhook:somewhere-else"'))
    assert tampered.read_bytes() != prior.read_bytes(), "the plant did not change the prior"
    _refused(root, tmp_path, match="signature", delta=tampered)


def test_a_delta_refuses_a_prior_signed_with_another_key(tmp_path):
    root, prior, _ = _seeded(tmp_path)
    _refused(root, tmp_path, match="signature", delta=prior,
             env={"BEACONPAVE_DRILL_KEY": "another-synthetic-key-of-enough-bytes-00"})


def test_a_delta_refuses_a_go_prior(tmp_path):
    root = _repo(tmp_path)
    prior, _ = _write(root, tmp_path, "go.json")
    _refused(root, tmp_path, match="no finding", delta=prior)


def _resigned(prior: pathlib.Path, **changes) -> pathlib.Path:
    """The prior with `changes` applied and signed again with the run's key: a document only
    a key holder could produce, so what it tests is the writer's checks, not the signature."""
    document = {**json.loads(prior.read_text(encoding="utf-8")), **changes}
    document["signature"] = drill.sign(document, KEY.encode("utf-8"))
    path = prior.with_name(f"resigned-{prior.name}")
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return path


def test_a_delta_refuses_a_signed_prior_that_does_not_conform(tmp_path):
    """Security seat, M11 PR 2, finding 5: the prior was never schema-validated."""
    root, prior, _ = _seeded(tmp_path)
    _refused(root, tmp_path, match="does not conform", delta=_resigned(prior, undeclared=1))


def test_a_delta_refuses_a_signed_prior_whose_tier_is_a_boolean(tmp_path):
    """`True == 1` in Python, so `tier: true` was accepted as tier 1."""
    scenario = {**SCENARIO, "fix_by_window_s": {"1": 60, "7": 7200}}
    root = _repo(tmp_path, scenario=scenario, cues=GAPPED)
    prior, _ = _write(root, tmp_path, "tier1.json", tier=1)
    _refused(root, tmp_path, delta=_resigned(prior, tier=True), tier=1)


def test_a_delta_refuses_a_signed_prior_naming_another_scenario(tmp_path):
    """Security seat, P16: a prior naming an extra scenario beside this one SURVIVED."""
    root, prior, first = _seeded(tmp_path)
    extra = {**first["findings"][0], "scenario": "blackout-sweep"}
    _refused(root, tmp_path, match="scenario",
             delta=_resigned(prior, findings=[*first["findings"], extra]))


def test_two_gaps_are_two_findings_in_file_order(tmp_path):
    """AI Quality seat, finding 3: a schema limit on `findings` (`maxItems`, `uniqueItems`)
    turns a second finding into a refusal -- INVALID where the run should read FALSE --
    and no case wrote more than one finding."""
    cues = [("s01", 0, 3000), ("s02", 6000, 9000), ("s03", 9000, 12000), ("s04", 15500, 18000)]
    root = _repo(tmp_path, cues=cues)
    _, artifact = _write(root, tmp_path, "two.json")
    assert [(f["after_cue"], f["before_cue"], f["gap_s"]) for f in artifact["findings"]] == [
        ("s01", "s02", 3.0), ("s03", "s04", 3.5)]


def test_the_writers_key_floor_is_32_bytes_not_32_characters(tmp_path):
    root = _repo(tmp_path)
    _, artifact = _write(root, tmp_path, "multibyte.json", env={"BEACONPAVE_DRILL_KEY": "é" * 16})
    assert artifact["decision"] == "GO"
    _refused(root, tmp_path, match="key", env={"BEACONPAVE_DRILL_KEY": "é" * 15 + "a"})


@pytest.mark.parametrize("event, tier", [("other-event", 7), ("synthetic-event", 8)])
def test_a_delta_refuses_a_prior_for_another_event_or_tier(tmp_path, event, tier):
    root, prior, _ = _seeded(tmp_path)
    _refused(root, tmp_path, match="is for event", delta=prior, event=event, tier=tier)


# --- the command ---------------------------------------------------------------------

def test_the_command_exits_0_on_go_1_on_no_go_and_2_when_nothing_is_written(tmp_path,
                                                                           monkeypatch):
    go_root = _repo(tmp_path / "go")
    no_go_root = _repo(tmp_path / "no-go", cues=GAPPED)
    args = ["--event", "synthetic-event", "--tier", "7", "--out"]
    monkeypatch.setenv("BEACONPAVE_DRILL_KEY", KEY)

    monkeypatch.setattr(drill, "ROOT", go_root)
    assert drill.main([*args, str(tmp_path / "a.json")]) == 0
    monkeypatch.setattr(drill, "ROOT", no_go_root)
    assert drill.main([*args, str(tmp_path / "b.json")]) == 1

    monkeypatch.delenv("BEACONPAVE_DRILL_KEY")
    assert drill.main([*args, str(tmp_path / "c.json")]) == 2
    assert not (tmp_path / "c.json").exists()
    monkeypatch.setenv("BEACONPAVE_DRILL_KEY", KEY)
    assert drill.main(["--event", "synthetic-event", "--tier", "7"]) == 2
    assert drill.main(["--help"]) == 2


def test_a_crash_is_exit_2_and_never_exit_1_which_means_no_go(tmp_path, monkeypatch):
    root = _repo(tmp_path, cues=GAPPED)
    monkeypatch.setenv("BEACONPAVE_DRILL_KEY", KEY)
    monkeypatch.setattr(drill, "ROOT", root)

    def boom(_text):
        raise RuntimeError("planted")

    monkeypatch.setattr(drill, "parse_cues", boom)
    out = tmp_path / "crash.json"
    assert drill.main(["--event", "synthetic-event", "--tier", "7", "--out", str(out)]) == 2
    assert not out.exists()


# --- SPEC/11 constraints 1 and 2, read from the code and the schema ------------------

WRITER_MAY_IMPORT = {"__future__", "argparse", "contextlib", "dataclasses", "datetime",
                     "hashlib", "hmac", "json", "os", "pathlib", "re", "subprocess", "sys",
                     "tempfile", "jsonschema"}


def _imported(path: pathlib.Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add("." if node.level else node.module.split(".")[0])
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == "__import__"):
            names.add("__import__")
    return names


def test_the_writer_imports_no_pave_module_so_nothing_goes_through_verdict_build():
    imported = _imported(ROOT / "pave" / "drill.py")
    assert imported <= WRITER_MAY_IMPORT, sorted(imported - WRITER_MAY_IMPORT)
    assert drill.SCHEMA_PATH == SCHEMA


def test_the_schema_holds_no_claim_value():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    forbidden, enums, words = [], [], []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"description", "title", "$comment"}:
                    continue
                here = (*path, key)
                if key in {"const", "if", "then", "else", "allOf", "anyOf", "oneOf", "not",
                           "dependencies", "default", "examples"}:
                    forbidden.append("/".join(here))
                if key == "enum":
                    enums.append("/".join(path))
                walk(value, here)
        elif isinstance(node, list):
            for item in node:
                walk(item, path)
        elif isinstance(node, str | int | float) and not isinstance(node, bool):
            words.append(str(node))

    walk(schema, ())
    assert not forbidden, f"the schema carries {forbidden}; SPEC/11 constraint 2"

    # **AI Quality seat, M11 PR 2, finding 3.** `maxItems: 1`, `uniqueItems` and a cue-id
    # `pattern` under `findings` each SURVIVED: a limit there refuses F1's false state
    # before it is written, so the run reads INVALID where it should read FALSE. Under
    # the subtrees the falsifiers read, the schema may say only type, shape and non-empty.
    limiting = {"pattern", "format", "maxItems", "minItems", "uniqueItems", "contains",
                "maxLength", "maxProperties", "minProperties", "propertyNames", "maximum",
                "minimum", "exclusiveMaximum", "exclusiveMinimum", "multipleOf"}
    limits = []

    def limits_in(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in limiting or (key == "minLength" and value != 1):
                    limits.append("/".join((*path, key)))
                limits_in(value, (*path, key))

    for field in ("findings", "owner"):
        limits_in(schema["properties"][field], ("properties", field))
    assert not limits, f"the schema limits what a falsifier reads: {limits}"
    assert sorted(enums) == ["properties/decision", "properties/mode",
                             "properties/signature/properties/alg"]
    text = " ".join(words)
    for claim_value in ("service-team", "webhook:", "player-captions", "129600", "4.0",
                        "c006", "c008", "caption-check", "max-gap"):
        assert claim_value not in text, f"the schema holds the claim value {claim_value!r}"


# --- publishing: whole or not at all (Platform Engineering seat, M11 PR 2, finding 1) ---

@pytest.mark.parametrize("fails", ["fsync", "link"])
def test_a_write_that_fails_leaves_no_artifact_and_no_partial_file(tmp_path, monkeypatch, fails):
    """`open(out, "xb")` created the artifact before writing it: a failed write left a
    0-byte file behind an exit 2, and every later run to that path was refused as
    `already exists`, which SPEC/11 does not allow to be retried. Measured by the seat:
    `exit=2 out_exists=True size=0`."""
    root = _repo(tmp_path, cues=GAPPED)
    out = tmp_path / "out" / "partial.json"

    def full_disk(*_args):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(drill.os, fails, full_disk)
    with pytest.raises(OSError):
        drill.run("synthetic-event", 7, out, root=root, env=ENV, now=NOW)
    assert not out.exists()
    assert list(out.parent.iterdir()) == [], "a partial file was left beside the artifact"

    monkeypatch.undo()
    _, artifact = _write(root, tmp_path, "partial.json")
    assert artifact["decision"] == "NO-GO", "the path was poisoned by the failed write"


def test_publishing_over_an_existing_file_refuses_and_leaves_it_untouched(tmp_path):
    out = tmp_path / "raced.json"
    out.write_bytes(b"written first by someone else")
    with pytest.raises(drill.Refused, match="already exists"):
        drill.publish(out, b"written second")
    assert out.read_bytes() == b"written first by someone else"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["raced.json"]


def test_the_exit_code_is_the_decision_even_when_the_console_cannot_print(tmp_path, monkeypatch):
    """Seat finding 5: the summary printed after the artifact was written, so a console that
    could not encode it raised, and the traceback exited 1 -- NO-GO -- over a written GO."""
    root = _repo(tmp_path)
    monkeypatch.setenv("BEACONPAVE_DRILL_KEY", KEY)
    monkeypatch.setattr(drill, "ROOT", root)
    real_print = print

    def cp1252_console(*args, **kwargs):
        if kwargs.get("file") is drill.sys.stdout:
            raise UnicodeEncodeError("charmap", "x", 0, 1, "planted")
        return real_print(*args, **kwargs)

    monkeypatch.setattr("builtins.print", cp1252_console)
    out = tmp_path / "go.json"
    assert drill.main(["--event", "synthetic-event", "--tier", "7", "--out", str(out)]) == 0
    assert out.exists()


def test_an_interrupt_before_publishing_is_exit_2_and_writes_nothing(tmp_path, monkeypatch):
    root = _repo(tmp_path, cues=GAPPED)
    monkeypatch.setenv("BEACONPAVE_DRILL_KEY", KEY)
    monkeypatch.setattr(drill, "ROOT", root)

    def interrupted(_text):
        raise KeyboardInterrupt

    monkeypatch.setattr(drill, "parse_cues", interrupted)
    out = tmp_path / "interrupted.json"
    assert drill.main(["--event", "synthetic-event", "--tier", "7", "--out", str(out)]) == 2
    assert not out.exists()
