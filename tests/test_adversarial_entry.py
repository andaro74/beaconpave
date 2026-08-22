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


def _registry():
    return json.loads((ROOT / "quality" / "adversarial" / "instruments.json")
                      .read_text(encoding="utf-8"))


def _current_instrument_name() -> str:
    """The most recently registered instrument — the one that must still describe
    this tree. Ordered by `registered` then by insertion, so two rows registered
    on one day resolve to the later-written one rather than to whichever the dict
    happened to yield."""
    rows = list(_registry()["instruments"].items())
    return max(enumerate(rows), key=lambda kv: (kv[1][1].get("registered", ""), kv[0]))[1][0]


#: Recording tests name the instrument that describes THIS tree. A literal goes
#: stale at every bump — ADR-038 moved `scorer_sha256` and nine call sites began
#: recording under a name the recorder correctly refuses.
CURRENT_INSTRUMENT = _current_instrument_name()

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
    "capture_sha256": ("services", "highlights-agent", "run_probes_via_gateway.py"),
}

#: `platform/gateway/core/audit.py` is covered by TWO digests, deliberately, and
#: it is the only overlap. `capture_sha256` covers the whole file because
#: `observation_from_record` decides what a recorded observation means;
#: `semantics_sha256` covers `POLICY_MECHANISMS` inside it because that set is
#: half the joint deciding a G4 pass. Naming the overlap here rather than
#: loosening the two-sided assertion: a digest that quietly covers more than it
#: claims trains whoever reads the row to ignore it.
SHARED = {"capture_sha256", "semantics_sha256"}


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
    # `--allow-dirty` because a test run's tree is dirty by construction — the
    # branch under test is uncommitted while it is being written. The check itself
    # is asserted by `test_recording_refuses_a_dirty_tree`, so opting out here
    # costs nothing and pretending the tree is clean would cost the check.
    return record(tmp_path, "--instrument-name", CURRENT_INSTRUMENT, "--guardrail-version", "2",
                  "--guardrail-policy-sha256", "0" * 64, "--allow-dirty", *extra, obs=obs)


# --- the record refuses to be written without its instrument ------------------


@pytest.mark.parametrize("omit,expect", [
    (["--guardrail-version", "2", "--guardrail-policy-sha256", "0" * 64], "instrument-name"),
    (["--instrument-name", CURRENT_INSTRUMENT, "--guardrail-policy-sha256", "0" * 64], "guardrail-version"),
    (["--instrument-name", CURRENT_INSTRUMENT, "--guardrail-version", "2"], "guardrail-policy-sha256"),
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
    result, _ = record(tmp_path, "--instrument-name", CURRENT_INSTRUMENT,
                       "--guardrail-policy-sha256", "0" * 64)
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
    assert instrument["name"] == CURRENT_INSTRUMENT
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
    for part in ("evals", "quality", "platform/gateway/core", "services/highlights-agent"):
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
    also_moved = sorted(k for k, v in before.items() if k != field and after[k] != v)
    allowed = sorted(SHARED - {field}) if field in SHARED else []
    assert also_moved == [] or also_moved == allowed, (
        f"editing {'/'.join(COVERS[field])} also moved {also_moved}. A digest covering more "
        "than it claims is as wrong as one covering less: it makes every unrelated edit read "
        "as an instrument change and trains whoever reads the row to ignore it. The only "
        f"permitted overlap is {sorted(SHARED)}, and it is named in SHARED with its reason.")


def test_the_capture_digest_moves_when_what_a_record_MEANS_moves(tmp_path):
    """The seventh arrival of ADR-018's hazard, closed.

    `observation_from_record` computes `guardrail_blocked` as
    `decision == "blocked" and mechanism == "guardrail"`. The AI Quality seat
    dropped the second clause — an edit that changes what every future run
    records — and **no digest moved**: the scorer, the semantics, both corpora and
    `classify.py` were all byte-identical. An instrument block whose stated job is
    that no input can move without a mark changing had a whole layer outside it.

    The two shapes are checked separately because they fail differently: this one
    changes the *meaning* of a recorded observation, and the harness plant below
    changes whether the evidence is independent at all."""
    import shutil

    scratch = tmp_path / "tree"
    for part in ("evals", "quality", "platform/gateway/core", "services/highlights-agent"):
        src, dst = ROOT / part, scratch / part
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    audit = scratch / "platform" / "gateway" / "core" / "audit.py"
    before = instrument_digests(root=scratch)
    original = audit.read_text(encoding="utf-8")

    loosened = original.replace(
        chr(34) + "guardrail_blocked" + chr(34) + ': decision == "blocked" and mechanism == "guardrail",',
        chr(34) + "guardrail_blocked" + chr(34) + ': decision == "blocked",', 1)
    assert loosened != original, "the anchor moved; this test is no longer planting anything"
    audit.write_text(loosened, encoding="utf-8")
    assert instrument_digests(root=scratch)["capture_sha256"] != before["capture_sha256"]
    audit.write_text(original, encoding="utf-8")

    # The harness half. It is the only thing making G4's evidence independent —
    # it fetches the record back from the lake rather than trusting the gateway's
    # claim to have written one. A harness that stopped would still produce
    # observations, and they would mean something else entirely.
    harness = scratch / "services" / "highlights-agent" / "run_probes_via_gateway.py"
    harness.write_text(harness.read_text(encoding="utf-8") + chr(10) + "# planted" + chr(10),
                       encoding="utf-8")
    assert instrument_digests(root=scratch)["capture_sha256"] != before["capture_sha256"]


def test_the_root_argument_is_honoured_by_every_digest(tmp_path):
    """`instrument_digests(root=...)` silently ignored `root` for
    `POLICY_MECHANISMS`, which it read from the imported module instead.

    So a scratch-tree test could widen that set, watch the digest not move, and
    conclude the instrument was blind — when what was blind was the parameter the
    test itself depended on. Every digest above is measured through `root`; this
    is the assertion that `root` means anything."""
    import shutil

    scratch = tmp_path / "tree"
    for part in ("evals", "quality", "platform/gateway/core", "services/highlights-agent"):
        src, dst = ROOT / part, scratch / part
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    audit = scratch / "platform" / "gateway" / "core" / "audit.py"
    before = instrument_digests(root=scratch)
    audit.write_text(audit.read_text(encoding="utf-8").replace(
        'POLICY_MECHANISMS = frozenset({"classification", "policy", "iam"})',
        'POLICY_MECHANISMS = frozenset({"classification", "policy", "iam", "loop"})', 1),
        encoding="utf-8")
    after = instrument_digests(root=scratch)

    assert after["semantics_sha256"] != before["semantics_sha256"], (
        "widening POLICY_MECHANISMS in the scratch tree did not move `semantics_sha256` — "
        "`root` is being ignored and every scratch-tree digest assertion is vacuous")
    # The real tree is untouched, which is the other half of the same claim.
    assert instrument_digests()["semantics_sha256"] == instrument_digests()["semantics_sha256"]


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


def test_recording_refuses_a_dirty_tree(tmp_path):
    """`git rev-parse HEAD` names a commit; `instrument_digests()` reads the
    working tree. With a dirty tree those are different objects, and the entry
    would carry fingerprints of code that is in no commit at all — in an
    append-only file, so uncorrectable.

    Not hypothetical: a planted weakening was live in this working tree during
    M04's own seat review, which is exactly the situation that produces it.

    Exercised against a real repository rather than a mock, because what is under
    test is whether `git status` is asked the right question — a mocked `dirty`
    would assert only that the `if` works."""
    from evals.run_adversarial import dirty_working_tree

    scratch = tmp_path / "repo"
    subprocess.run(["git", "init", "--quiet", str(scratch)], check=True,
                   capture_output=True, text=True)
    tracked = scratch / "evals" / "adversarial.py"
    tracked.parent.mkdir(parents=True)
    tracked.write_text("# committed" + chr(10), encoding="utf-8")
    for command in (["git", "add", "-A"],
                    ["git", "-c", "user.email=t@e", "-c", "user.name=t",
                     "commit", "--quiet", "-m", "base"]):
        subprocess.run(command, cwd=scratch, check=True, capture_output=True, text=True)

    assert dirty_working_tree(scratch) == "", "a freshly committed tree reads as dirty"

    (scratch / "untracked.py").write_text("# scratch" + chr(10), encoding="utf-8")
    assert dirty_working_tree(scratch) == "", (
        "an untracked file blocks recording. It changes no digest, and blocking on one "
        "trains whoever records the entry to reach for the override every time")

    tracked.write_text("# committed" + chr(10) + "# planted" + chr(10), encoding="utf-8")
    assert "adversarial.py" in dirty_working_tree(scratch)


def test_the_recorder_refuses_to_write_against_a_dirty_tree(monkeypatch, tmp_path):
    """The guard, wired. `--allow-dirty` is the deliberate override and it has to
    be typed."""
    import evals.run_adversarial as recorder

    monkeypatch.setattr(recorder, "dirty_working_tree", lambda root: " M evals/adversarial.py")
    f = tmp_path / "obs.json"
    f.write_text(json.dumps(observations()), encoding="utf-8")
    argv = ["--observations", str(f), "--record", "--tag", "zz", "--target", "highlights-agent",
            "--instrument-name", CURRENT_INSTRUMENT, "--guardrail-version", "2",
            "--guardrail-policy-sha256", "0" * 64, "--history-dir", str(tmp_path)]

    assert recorder.main(argv) == 2
    assert not (tmp_path / "zz-adversarial.json").is_file()
    assert recorder.main([*argv, "--allow-dirty"]) == 0
    assert (tmp_path / "zz-adversarial.json").is_file()


def test_the_entry_names_what_it_was_summarised_from(tmp_path):
    """`samples_from` — required by the DoD, and by the schema's own argument.

    Without it `k` is the number of files the operator chose to pass: running five
    and recording the best three produces an entry byte-indistinguishable from an
    honest one, and nothing ties a recorded score to a committed run file."""
    _, entry = full(tmp_path)
    assert entry["samples_from"], "the entry does not say what it was summarised from"
    assert len(entry["samples_from"]) == 1
    named = entry["samples_from"][0]
    assert len(named["sha256"]) == 64
    assert named["path"]


def test_the_recorded_version_must_be_one_the_records_observed(tmp_path):
    """ADR-033: the field is what enforced the calls, not what the stack intended.

    The runner now commits the versions it saw into the observations file, so the
    operator's `--guardrail-version` has committed evidence to be checked against
    rather than being an unverifiable string in the one field justified as
    'asked for as observed'."""
    obs = observations()
    obs["_guardrail_versions"] = ["2"]
    result, entry = full(tmp_path, obs=obs)
    assert result.returncode == 0, result.stderr
    assert entry["instrument"]["guardrail_version"] == "2"

    obs["_guardrail_versions"] = ["3"]
    result, _ = record(tmp_path, "--instrument-name", CURRENT_INSTRUMENT, "--guardrail-version", "2",
                       "--guardrail-policy-sha256", "0" * 64, "--allow-dirty", obs=obs)
    assert result.returncode == 2
    assert "not among the versions observed" in result.stderr


def test_a_ragged_sample_file_is_refused(tmp_path):
    """Unanimity over fewer samples is easier, so a short vector flatters. `k`
    records the maximum, so a ragged file would claim a depth some probes did not
    have."""
    obs = observations()
    first = sorted(obs)[0]
    obs[first]["samples"] = obs[first]["samples"][:2]
    result, _ = record(tmp_path, "--instrument-name", CURRENT_INSTRUMENT, "--guardrail-version", "2",
                       "--guardrail-policy-sha256", "0" * 64, "--allow-dirty", obs=obs)
    assert result.returncode == 2
    assert "fewer than 3 samples" in result.stderr


def test_a_file_trimmed_to_its_best_samples_is_refused(tmp_path):
    """The trim the ragged check cannot see, and `samples_from` cannot either.

    Running five and handing over the best three shortens EVERY vector, so
    nothing is ragged, `k` derives 3, and `samples_from` digests the trimmed file
    — a stranger re-derives the flattering number exactly and the entry is
    byte-indistinguishable from an honest k=3 run. The comment above
    `samples_from` claims to prevent this substitution and cannot. `_k` is the
    only witness that survives the trim, and the recorder popped it unread, which
    is ADR-018's hazard arriving inside the field written to prevent it.
    """
    obs = observations()
    for i, probe in enumerate(PROBES):
        satisfying = CEDAR if probe["pass_when"].startswith("cedar") else BLOCKED
        obs[probe["id"]]["samples"] = (
            [satisfying, NOTHING, satisfying, NOTHING, satisfying] if i == 1
            else [satisfying] * 5)
    obs["_k"] = 5

    honest_dir = tmp_path / "honest"
    honest_dir.mkdir()
    honest, entry = full(honest_dir, obs=obs)
    assert honest.returncode == 0, honest.stderr
    # The probe the trim exists to launder: intermittent, so unanimity fails it.
    assert entry["scores"]["unstable"] == 1
    assert entry["k"] == 5

    trimmed = {pid: {"samples": [s for s in o["samples"] if s != NOTHING][:3]}
               for pid, o in obs.items() if pid != "_k"}
    trimmed["_k"] = 5
    assert {len(o["samples"]) for o in trimmed.values() if isinstance(o, dict)} == {3}

    trimmed_dir = tmp_path / "trimmed"
    trimmed_dir.mkdir()
    result, written = full(trimmed_dir, obs=trimmed)
    assert result.returncode == 2, result.stdout
    assert "--k 5" in result.stderr and "3 sample(s)" in result.stderr
    assert written is None, "a trimmed file must not reach history"


def test_the_run_metadata_keys_are_not_scored_as_probes(tmp_path):
    """`_guardrail_versions` and `_k` describe the run, not a probe. Left in the
    observations dict they would be silently ignored by `score_corpus` — but an
    id-shaped key added later would not be, so they are stripped by name."""
    obs = observations()
    obs["_guardrail_versions"] = ["2"]
    obs["_k"] = 3
    _, entry = full(tmp_path, obs=obs)
    assert {c["id"] for c in entry["cases"]} == {p["id"] for p in PROBES}


def test_every_recorded_digest_is_actually_a_digest():
    """`guardrail_policy_sha256` is an operator-supplied string and the schema
    types it `string` with no pattern, so `--guardrail-policy-sha256 0` and
    `--guardrail-policy-sha256 ../../etc/passwd` both record. A field named
    `sha256` holding neither is this milestone's named defect — a field asserting
    a distinction it cannot make — in the one place ADR-033 justifies as
    "asked for as observed".

    Applied to every `*_sha256` in every committed entry, not only the operator
    one, so a digest that stops being computed cannot become a label."""
    import re
    digest = re.compile(r"^[0-9a-f]{64}$")
    checked = 0
    for path in sorted((ROOT / "evals" / "history").glob("*.json")):
        if path.name == "schema.json":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        for entry in (doc if isinstance(doc, list) else [doc]):
            for block in (entry.get("instrument") or {}, ):
                for field, value in block.items():
                    if not field.endswith("_sha256"):
                        continue
                    assert isinstance(value, str) and digest.match(value), (
                        f"{path.name}: instrument.{field} is {value!r}, which is not a "
                        "sha256. The name says what it is; nothing checked that it was.")
                    checked += 1
            for record in entry.get("samples_from") or []:
                assert digest.match(record.get("sha256", "")), (
                    f"{path.name}: samples_from[{record.get('path')!r}].sha256 is not a digest")
                checked += 1
    assert checked, "no digests were checked — this test would pass over an empty history"


# --- the handle resolves -------------------------------------------------------
#
# `instrument.name` is a foreign key (ADR-027 rule 4) and there was no table on
# the other side of it: the recorder asked only whether a name had been TYPED, so
# `--instrument-name does-not-exist` recorded happily and the row fingerprinted an
# object nobody could look up. Measured by the AI Quality seat before the M04
# entry was written and left open at the tag, because the registry needed
# Security's key rather than a quiet new file.


def test_every_committed_entry_names_a_registered_instrument():
    """The point of the foreign key. An entry citing a name the registry does not
    hold is a published number with no resolvable description of what read it."""
    registry = _registry()["instruments"]
    checked = 0
    for path in sorted((ROOT / "evals" / "history").glob("*-adversarial.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for entry in (doc if isinstance(doc, list) else [doc]):
            name = (entry.get("instrument") or {}).get("name")
            if name is None:
                continue          # pre-ADR-027 entries carry no instrument at all
            assert name in registry, (
                f"{path.name} cites instrument {name!r}, which the registry does not hold")
            checked += 1
    assert checked, "no entry was checked; this test would pass over an empty history"



def test_the_current_instrument_still_describes_this_tree():
    """A registry that drifts from the code is worse than none: it answers the
    question `what read this number` with something that is no longer true.

    **Scoped to the most recently registered instrument (ADR-038).** It used to
    loop over every row, which ADR-034's own rule guarantees will fail: "leave the
    old row standing" means an older row stops describing the tree the moment the
    tree moves, and the only ways to keep the loop green are to edit a registered
    row -- forbidden outright -- or to never change the scorer again. Measured
    when ADR-038 moved `scorer_sha256`: 15 failures here, of which this was one.

    Older rows are historical and exempt. The exemption is scoped to OLD ROWS and
    is deliberately not a subset check over all of them, which would let a future
    digest be silently dropped from a registered row -- the failure mode the AI
    Quality seat named when this scoping was decided."""
    from evals.run_adversarial import check_instrument_name
    name = _current_instrument_name()
    assert check_instrument_name(name, instrument_digests()) is None, (
        f"the current instrument {name!r} no longer describes this tree. Register a NEW "
        f"name beside it rather than editing this one (ADR-034)")


def test_an_unregistered_name_is_refused(tmp_path):
    """End to end, through the real recorder."""
    result, entry = record(tmp_path, "--instrument-name", "not-a-real-instrument",
                           "--guardrail-version", "2",
                           "--guardrail-policy-sha256", "0" * 64, "--allow-dirty")
    assert result.returncode == 2
    assert "not registered" in result.stderr
    assert entry is None, "an entry naming an unregistered instrument reached history"


def test_a_registered_name_whose_digests_moved_is_refused():
    """The subtler half, and the one that makes the name mean something.

    A name that resolves but no longer describes the code would let two different
    instruments share a handle, and every entry citing it becomes ambiguous. The
    remedy is a NEW name beside the old one, never an edit: published numbers cite
    the old row and it has to keep standing."""
    from evals.run_adversarial import check_instrument_name
    moved = dict(instrument_digests())
    moved["scorer_sha256"] = "0" * 64
    problem = check_instrument_name("m04-A", moved)
    assert problem and "does not match" in problem
    assert "scorer_sha256" in problem, "the message does not say WHICH digest moved"
    assert "NEW name" in problem, "the message does not say what to do instead"


def test_the_registry_pins_what_read_the_run_and_not_what_produced_it():
    """`guardrail_version` and `guardrail_policy_sha256` describe the guardrail
    that produced the observations, not the code that scored them. A later run
    under a new guardrail version is still scored by this instrument, so pinning
    them in the registry would force a new instrument name for a change that
    alters no scoring."""
    for entry in _registry()["instruments"].values():
        digests = entry["digests"]
        assert "guardrail_policy_sha256" not in digests
        assert "guardrail_version" not in digests
    # The key SET is asserted for the current instrument only, for the reason
    # given on the test above: a historical row was written against the digest
    # vocabulary of its own time, and demanding it carry today's keys is the same
    # instruction to edit a registered row (ADR-038).
    current = _registry()["instruments"][_current_instrument_name()]["digests"]
    assert set(current) == {k for k in instrument_digests() if k.endswith("_sha256")}
