"""
What a recorded adversarial entry has to say about the instrument that produced
it.

`instrument` in `evals/history/schema.json` was judge-shaped in every part —
`prompt_sha256`, `rubric_axes_sha256`, `calibrated_by`, and a `deterministic`
block requiring `cases_sha256`. A probe run can satisfy none of it: it has no
golden cases file and no judge.

**The tempting reading was that an adversarial entry therefore has no
instrument.** That is the flattering one and it is false. Five things read a
probe run, and every one can move without a recorded mark changing — the fifth
and sixth arrivals of ADR-018's hazard, which M03 recorded and left owed.

M03 recorded the same lesson three times in one milestone, under the name *a
field that asserts a distinction it cannot make*: `user_turn_sha256`,
`calibrated_by`, `instrument.deterministic`. Every failure ran toward the
flattering reading. So the load-bearing test here is
`test_each_digest_moves_when_its_own_input_moves` — a digest that does not move
is exactly such a field, and the only way to know is to move each input and look.

Hermetic (G8). Owning seats: AI Quality (the schema, two-key) · Security (what
the digests cover).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import jsonschema
import pytest
import yaml

from evals.adversarial import instrument_digests

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "evals" / "history" / "schema.json").read_text(encoding="utf-8"))
PROBES = yaml.safe_load(
    (ROOT / "quality" / "adversarial" / "probes.yaml").read_text(encoding="utf-8"))

BLOCKED = {"guardrail_blocked": True, "policy_denied": False, "audit_record": "k"}
NOTHING = {"guardrail_blocked": False, "policy_denied": False, "audit_record": "k2"}
CEDAR = {"policy_denied": True, "mechanism": "policy", "audit_record": "k3"}

#: Which file each digest is supposed to cover. The map is the test's subject,
#: not its fixture: it is the claim the schema makes in prose, made checkable.
COVERS = {
    "scorer_sha256": ("evals", "adversarial.py"),
    "probes_sha256": ("quality", "adversarial", "probes.yaml"),
    "g4_cases_sha256": ("quality", "adversarial", "g4-semantics.yaml"),
    "classify_sha256": ("platform", "gateway", "core", "classify.py"),
}


def observations(unstable_index: int | None = 1) -> dict:
    out = {}
    for i, probe in enumerate(PROBES):
        satisfying = CEDAR if probe["pass_when"].startswith("cedar") else BLOCKED
        samples = ([satisfying, NOTHING, satisfying] if i == unstable_index
                   else [satisfying, satisfying, satisfying])
        out[probe["id"]] = {"samples": samples}
    return out


def record(tmp_path, *extra, obs=None):
    """Run the real recorder into a temp history dir."""
    f = tmp_path / "obs.json"
    f.write_text(json.dumps(obs if obs is not None else observations()), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "evals.run_adversarial", "--observations", str(f),
         "--record", "--tag", "zz", "--target", "highlights-agent",
         "--history-dir", str(tmp_path), *extra],
        cwd=ROOT, capture_output=True, text=True)
    entry_path = tmp_path / "zz-adversarial.json"
    entry = json.loads(entry_path.read_text(encoding="utf-8")) if entry_path.is_file() else None
    return result, entry


def full(tmp_path, *extra, obs=None):
    return record(tmp_path, "--instrument-name", "m04-A", "--guardrail-version", "2",
                  *extra, obs=obs)


# --- the record refuses to be written without its instrument ------------------


@pytest.mark.parametrize("omit,expect", [
    (["--guardrail-version", "2"], "instrument-name"),
    (["--instrument-name", "m04-A"], "guardrail-version"),
])
def test_recording_is_refused_when_the_instrument_cannot_be_named(tmp_path, omit, expect):
    """ADR-027 rule 4: a row naming an instrument nobody can look up is a
    fingerprint of an object that does not exist.

    Refused in the recorder rather than left to schema validation, so the message
    says what is missing and why — a schema error names a JSON path and teaches
    nobody which milestone's lesson it is repeating."""
    result, entry = record(tmp_path, *omit)
    assert result.returncode == 2
    assert expect in result.stderr
    assert entry is None, "an entry was written despite the refusal"


def test_the_guardrail_version_is_asked_for_as_observed_not_intended(tmp_path):
    """The wording matters and is asserted.

    M03 recorded two dev passes whose instrument blocks were byte-identical
    because the enforced policy was not part of the instrument; the refusal rate
    differed and nothing in the record said why. A stack output is a statement of
    intent — only the record of the call that happened is evidence of what
    enforced it."""
    result, _ = record(tmp_path, "--instrument-name", "m04-A")
    assert "OBSERVED IN THE AUDIT RECORDS" in result.stderr


# --- the entry, and what it must carry ----------------------------------------


def test_a_recorded_entry_validates_and_carries_its_instrument(tmp_path):
    result, entry = full(tmp_path)
    assert result.returncode == 0, result.stderr
    jsonschema.validate(entry, SCHEMA)
    assert entry["suite"] == "adversarial"
    assert "supersedes" not in entry, (
        "a first recording is not a correction; `supersedes` means an entry was wrong")
    instrument = entry["instrument"]
    assert instrument["name"] == "m04-A"
    assert instrument["guardrail_version"] == "2"
    assert instrument["k"] == 3
    for field in ("scorer_sha256", "semantics_sha256", "probes_sha256",
                  "g4_cases_sha256", "classify_sha256"):
        assert len(instrument[field]) == 64, field


def test_the_per_sample_verdicts_travel_into_the_entry(tmp_path):
    """`k` alone says a summary happened and not what it summarised.
    PASS/FAIL/PASS and PASS/PASS/PASS record the same verdict from very different
    evidence, and only one of them is a finding."""
    _, entry = full(tmp_path)
    assert entry["k"] == 3
    cases = {c["id"]: c for c in entry["cases"]}
    assert all(len(c["samples"]) == 3 for c in entry["cases"])
    split = [c for c in entry["cases"] if c.get("unstable")]
    assert len(split) == 1
    assert sorted(split[0]["samples"]) == ["FAIL", "PASS", "PASS"]
    assert split[0]["result"] == "FAIL", (
        "a split recorded as anything but FAIL is the majority rule arriving by the back door")
    assert cases[PROBES[0]["id"]].get("unstable") is None


def test_unstable_is_reported_in_the_scores_and_counted_inside_failed(tmp_path):
    _, entry = full(tmp_path)
    s = entry["scores"]
    assert s["unstable"] == 1
    assert s["failed"] == 1
    assert s["passed"] + s["failed"] + s["infra"] == s["total"]


def test_a_k_one_run_records_no_samples_and_no_k(tmp_path):
    """The committed corpora are `k = 1`. An entry that claimed a sample vector it
    did not have would make every earlier row look summarised."""
    flat = {p["id"]: (CEDAR if p["pass_when"].startswith("cedar") else BLOCKED)
            for p in PROBES}
    _, entry = full(tmp_path, obs=flat)
    assert "k" not in entry
    assert all("samples" not in c for c in entry["cases"])
    assert entry["instrument"]["k"] == 1


# --- the load-bearing one -----------------------------------------------------


@pytest.mark.parametrize("field", sorted(COVERS))
def test_each_digest_moves_when_its_own_input_moves(tmp_path, field):
    """**A digest that does not move is a field asserting a distinction it cannot
    make** — M03's lesson, recorded three times in one milestone, every failure
    running toward the flattering reading.

    Each input is edited in a scratch copy of the tree and the digests recomputed
    there. The assertion is two-sided: the named digest moves, and no other one
    does. A digest covering more than it claims is as wrong as one covering less,
    because it makes every unrelated edit read as an instrument change and trains
    whoever reads the row to ignore it."""
    import shutil

    scratch = tmp_path / "tree"
    for part in ("evals", "quality", "platform/gateway/core"):
        src = ROOT / part
        dst = scratch / part
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    before = instrument_digests(root=scratch)
    target = scratch.joinpath(*COVERS[field])
    target.write_text(target.read_text(encoding="utf-8") + "\n# planted\n", encoding="utf-8")
    after = instrument_digests(root=scratch)

    assert after[field] != before[field], (
        f"editing {'/'.join(COVERS[field])} did not move {field}. The entry would record the "
        "same fingerprint for two different instruments.")
    unchanged = {k: v for k, v in before.items() if k != field}
    assert {k: after[k] for k in unchanged} == unchanged, (
        f"editing {'/'.join(COVERS[field])} also moved "
        f"{sorted(k for k in unchanged if after[k] != unchanged[k])}")


def test_the_semantics_digest_moves_on_a_widened_mechanism_set():
    """`semantics_sha256` is the joint that decides a score, and it is pinned
    apart from `scorer_sha256` for a reason worth checking rather than asserting.

    A widening of `CEDAR_MECHANISMS` or `POLICY_MECHANISMS` raises probe scores
    with no system improving. Digesting the rendered membership rather than the
    source text means reordering a `frozenset` literal does not read as a policy
    change, while adding a member does."""
    import evals.adversarial as adv

    before = instrument_digests()["semantics_sha256"]
    original = adv.CEDAR_MECHANISMS
    try:
        adv.CEDAR_MECHANISMS = frozenset({"policy", "classification"})
        assert instrument_digests()["semantics_sha256"] != before
    finally:
        adv.CEDAR_MECHANISMS = original
    assert instrument_digests()["semantics_sha256"] == before


def test_the_schema_refuses_a_judge_shaped_instrument_on_a_probe_run():
    """The suite-conditional rule, from the side that matters.

    `oneOf` alone would let an adversarial entry carry the judge's fingerprints —
    which validates, means nothing, and is exactly the shape of a record that
    names an instrument it did not use."""
    entry = json.loads(
        (ROOT / "evals" / "history" / "m01-adversarial.json").read_text(encoding="utf-8"))
    entry["instrument"] = {
        "name": "B", "prompt_sha256": "a", "rubric_axes_sha256": "b",
        "user_turn_sha256": "c", "calibrated_by": "B",
        "deterministic": {"cases_sha256": "d", "scored": [], "deferred": []},
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(entry, SCHEMA)


def test_the_committed_entries_still_validate():
    """The schema gained a conditional. Every entry written before it existed must
    still be readable — append-only history that a schema change invalidates is
    history nobody can check."""
    for path in sorted((ROOT / "evals" / "history").glob("*.json")):
        if path.name == "schema.json":
            continue
        jsonschema.validate(json.loads(path.read_text(encoding="utf-8")), SCHEMA)


def test_history_stays_append_only(tmp_path):
    """Recording twice under one tag must refuse rather than overwrite."""
    full(tmp_path)
    result, _ = full(tmp_path)
    assert result.returncode == 2
    assert "append-only" in result.stderr
