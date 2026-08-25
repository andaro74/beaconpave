"""ADR-042: what a new row in `evals/history/` may claim, and what may happen to a row that is there.

Two kinds of test, deliberately in one three-key file:

- **The mirror.** Each check in `pave/history.py` run against the committed
  tree, so `make check` is red on the operator's machine for the same reason CI
  is. The instance that DECIDES is `pave gate history` in the workflow, because
  this file runs under a harness `tests/conftest.py` and `pyproject.toml`
  control on zero keys -- `test_the_deciding_step_is_in_the_workflow` pins that.
- **The violating trees.** Every protection planted against, in a copy, so
  that deleting the check produces a failure somewhere. Six of ten weakenings
  survived ADR-041's first registered commit because the check they removed
  was reachable on no honest tree.

Owning seats: AI Quality · Security / Red Team · Platform Engineering.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

from pave import history, twokey
from pave.history import (
    EVIDENCE_REVISIONS,
    LEGACY_ENTRIES,
    Refusal,
    append_only_violations,
    check_case_ids,
    check_derivable,
    check_evidence,
    check_pins,
    check_readme,
    check_registry,
    check_schema,
    check_second_rows,
    entry_digest,
    enumerate_entries,
    resolve_base,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals" / "history"
THREE = {"ai-quality", "security", "platform-eng"}


def _copy_history(tmp_path: pathlib.Path) -> pathlib.Path:
    dst = tmp_path / "history"
    shutil.copytree(HISTORY, dst)
    return dst


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _repo(tmp_path: pathlib.Path, keep: set | None = None) -> pathlib.Path:
    """A throwaway repository holding a copy of `evals/history/`, with one commit
    on `main`. Tests branch from it and plant.

    `keep` narrows it to named entries: the committed shas do not exist in a
    throwaway repo, so a test about reachability or about a corpus at a sha must
    hold only the entry it is about."""
    repo = tmp_path / "repo"
    (repo / "evals").mkdir(parents=True)
    shutil.copytree(HISTORY, repo / "evals" / "history")
    if keep is not None:
        for child in (repo / "evals" / "history").glob("*.json"):
            if child.name not in keep | {"schema.json", "pins.json"}:
                child.unlink()
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "t@example.invalid", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    _git("config", "core.autocrlf", "false", cwd=repo)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)
    _git("checkout", "-q", "-b", "pr", cwd=repo)
    return repo


# --- the mirror ---------------------------------------------------------------

def test_the_committed_tree_passes_every_check():
    assert enumerate_entries()[1] == []
    assert check_pins() == []
    assert check_derivable() == []
    assert check_second_rows() == []
    assert check_evidence() == []
    assert check_schema() == []
    assert check_readme() == []


def test_the_git_resolving_checks_pass_and_never_skip():
    """Refusal is a FAILURE with the named remedy. `pytest.skip` here would be
    the depth-1 defect `test_judged_entry.py` records: asserted nowhere that
    mattered."""
    try:
        assert check_case_ids() == []
        assert check_registry() == []
        base = resolve_base(env=_env_without_conftest_reach())
        assert append_only_violations(base) == []
    except Refusal as exc:
        pytest.fail(f"a history check REFUSED, which is not a pass: {exc}")


def _env_without_conftest_reach() -> dict:
    """Under GitHub Actions the mirror must not take its base from the
    environment at all -- `tests/conftest.py` can set it (Security plant C).
    Locally, `PAVE_BASE` and the fallbacks apply."""
    env = dict(os.environ)
    if env.get("GITHUB_ACTIONS"):
        env.pop("GITHUB_BASE_REF", None)
        if not env.get("PAVE_BASE"):
            pytest.fail("under GITHUB_ACTIONS the mirror refuses an environment-derived base; the "
                        "workflow sets PAVE_BASE from the event payload, and it is unset")
    return env


def test_the_legacy_set_is_closed_and_every_member_is_on_disk():
    names = {p.name for p in enumerate_entries()[0]}
    assert names >= LEGACY_ENTRIES
    for name in EVIDENCE_REVISIONS:
        assert name in names


# --- decision 2: complete, exact, self-consistent ---------------------------

def test_an_appended_row_is_unpinned_and_red(tmp_path):
    """Prediction 1. The plant draft 1 missed: a schema-valid 24/25 beside the
    real 19/25, same sha. 1701 green before this file existed."""
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["scores"]["passed"] = 24
    (h / "m01-goldens-corrected.json").write_text(json.dumps(row), encoding="utf-8")
    problems = check_pins(h)
    assert any("m01-goldens-corrected.json is on disk and not in pins.json" in p for p in problems)
    assert any("normalised digest is" in p for p in problems), "the remedy must print the digest"


def test_a_pinned_entry_missing_from_disk_gets_its_own_message(tmp_path):
    h = _copy_history(tmp_path)
    (h / "m01-goldens.json").unlink()
    problems = check_pins(h)
    assert any("m01-goldens.json is pinned in pins.json and not on disk" in p for p in problems)
    assert not any("is on disk and not in" in p for p in problems)


def test_an_empty_string_pin_is_not_a_pin(tmp_path):
    """Security plant: `"mzz-adversarial.json": ""` plus a rewrite behind it was
    green under an `if v` filter."""
    h = _copy_history(tmp_path)
    pins = json.loads((h / "pins.json").read_text(encoding="utf-8"))
    pins["m01-goldens.json"] = ""
    (h / "pins.json").write_text(json.dumps(pins), encoding="utf-8")
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["scores"]["passed"] = 99
    (h / "m01-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("is not a sha256" in p for p in check_pins(h))


def test_a_rewritten_entry_is_red(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["scores"]["passed"] = 24
    (h / "m01-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("m01-goldens.json has changed" in p for p in check_pins(h))


@pytest.mark.parametrize("plant", ["corrections/m01-goldens.json", "m01-goldens.json.new"])
def test_the_directory_holds_entries_and_nothing_else(tmp_path, plant):
    h = _copy_history(tmp_path)
    target = h / plant
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")
    assert enumerate_entries(h)[1], f"{plant} was enumerated as nothing"


def test_a_symlinked_entry_is_refused(tmp_path):
    h = _copy_history(tmp_path)
    link = h / "mzz-goldens.json"
    try:
        os.symlink(h / "m01-goldens.json", link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this filesystem; the git-level typechange test covers it")
    assert any("symlink" in p for p in enumerate_entries(h)[1])


def test_the_directory_deleted_is_not_a_pass(tmp_path):
    assert check_pins(tmp_path / "nowhere")


def test_scores_must_be_what_the_cases_say(tmp_path):
    """The fabricated row did not even have to be internally consistent:
    `passed: 24` beside `pass_rate: 0.76` validated."""
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["scores"]["passed"] = 24
    (h / "m01-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("scores.passed is 24" in p for p in check_derivable(h))
    adv = json.loads((h / "m04-adversarial.json").read_text(encoding="utf-8"))
    adv["scores"]["total"] = 3
    (h / "m04-adversarial.json").write_text(json.dumps(adv), encoding="utf-8")
    assert any("scores.total is 3" in p for p in check_derivable(h))


def test_an_adversarial_result_is_the_unanimity_of_its_samples(tmp_path):
    h = _copy_history(tmp_path)
    adv = json.loads((h / "m04-adversarial.json").read_text(encoding="utf-8"))
    split = next(c for c in adv["cases"] if c.get("unstable"))
    split["result"] = "PASS"
    (h / "m04-adversarial.json").write_text(json.dumps(adv), encoding="utf-8")
    assert any("is their unanimity" in p for p in check_derivable(h))


def test_the_readme_row_is_tied_to_the_pinned_entry_not_any_entry(tmp_path):
    """`m00b` has two goldens entries (15 and 18) and `m02` two arms (17 and
    16): "some entry with this tag matches" let the row move to the other."""
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    for before, after in (("**15/25**", "**18/25**"), ("**16/25**", "**17/25**"), ("**19/25**", "**24/25**")):
        assert before in text
        moved = tmp_path / "README.md"
        moved.write_text(text.replace(before, after, 1), encoding="utf-8")
        assert check_readme(readme=moved), f"{before} -> {after} was green"
    assert check_readme(readme=readme) == []


def test_a_goldens_entry_for_a_row_that_publishes_no_number_is_red(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["tag"] = "m04"
    (h / "m04-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("m04 has a goldens entry on disk" in p for p in check_readme(h))


# --- decision 3: the merge-base diff ----------------------------------------

def _commit_all(repo, msg):
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", msg, cwd=repo)


def test_an_honest_two_commit_pr_does_not_fire(tmp_path):
    """Prediction 4. Record, then fix a field after review: the shape draft 1's
    commit count fired on, teaching the squash that hides the real attack."""
    repo = _repo(tmp_path)
    new = repo / "evals" / "history" / "mzz-goldens.json"
    row = json.loads((new.parent / "m01-goldens.json").read_text(encoding="utf-8"))
    row["tag"] = "mzz"
    new.write_text(json.dumps(row, indent=2), encoding="utf-8")
    _commit_all(repo, "record mzz")
    row["recorded_at"] = "2026-08-23T00:00:00-07:00"
    new.write_text(json.dumps(row, indent=2), encoding="utf-8")
    (new.parent / "schema.json").write_text(
        (new.parent / "schema.json").read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _commit_all(repo, "fix timezone, touch schema")
    assert append_only_violations("main", cwd=repo) == []


def test_a_branch_behind_an_advanced_main_is_not_accused(tmp_path):
    """Two-dot diffs against the tip: `R097 mzz-goldens.json -> zz-honest...`.
    Three-dot diffs against the merge-base."""
    repo = _repo(tmp_path)
    new = repo / "evals" / "history" / "zz-honest-goldens.json"
    new.write_text((new.parent / "m01-goldens.json").read_text(encoding="utf-8"), encoding="utf-8")
    _commit_all(repo, "honest")
    _git("checkout", "-q", "main", cwd=repo)
    other = repo / "evals" / "history" / "mzz-goldens.json"
    other.write_text((other.parent / "m01-goldens.json").read_text(encoding="utf-8"), encoding="utf-8")
    _commit_all(repo, "main advanced")
    _git("checkout", "-q", "pr", cwd=repo)
    assert append_only_violations("main", cwd=repo) == []


@pytest.mark.parametrize("shape", ["modify", "delete", "rename", "squash-rename"])
def test_touching_a_committed_entry_fires(tmp_path, shape):
    """Prediction 3. `--no-renames` is what makes the rename a `D`: with
    detection on it is `R097`, and git gives up hardest on the largest
    rewrites -- the bigger the lie, the more append-only it looks."""
    repo = _repo(tmp_path)
    entry = repo / "evals" / "history" / "m01-goldens.json"
    if shape == "modify":
        row = json.loads(entry.read_text(encoding="utf-8"))
        row["scores"]["passed"] = 24
        entry.write_text(json.dumps(row, indent=2), encoding="utf-8")
    elif shape == "delete":
        entry.unlink()
    else:
        _git("mv", str(entry), str(entry.with_name("m01-goldens-reread.json")), cwd=repo)
        row = json.loads(entry.with_name("m01-goldens-reread.json").read_text(encoding="utf-8"))
        row["scores"]["passed"] = 24
        entry.with_name("m01-goldens-reread.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    _commit_all(repo, shape)
    if shape == "squash-rename":
        _git("reset", "-q", "--soft", "main", cwd=repo)
        _git("commit", "-q", "-m", "squashed", cwd=repo)
    problems = append_only_violations("main", cwd=repo)
    assert any("m01-goldens.json existed at the base" in p for p in problems), problems


def test_a_symlink_typechange_fires(tmp_path):
    """`--diff-filter=MDR` missed `T`. Two seats, independently."""
    repo = _repo(tmp_path)
    blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], input="m02-tools-goldens.json",
                          cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    _git("update-index", "--cacheinfo", f"120000,{blob},evals/history/m01-goldens.json", cwd=repo)
    _git("commit", "-q", "-m", "typechange", cwd=repo)
    problems = append_only_violations("main", cwd=repo)
    assert any("typechanged" in p for p in problems), problems


def test_an_evil_merge_fires(tmp_path):
    repo = _repo(tmp_path)
    (repo / "note.txt").write_text("x", encoding="utf-8")
    _commit_all(repo, "side")
    _git("checkout", "-q", "main", cwd=repo)
    (repo / "other.txt").write_text("y", encoding="utf-8")
    _commit_all(repo, "main moves")
    _git("checkout", "-q", "pr", cwd=repo)
    _git("merge", "-q", "--no-commit", "--no-ff", "main", cwd=repo)
    entry = repo / "evals" / "history" / "m01-goldens.json"
    row = json.loads(entry.read_text(encoding="utf-8"))
    row["scores"]["passed"] = 24
    entry.write_text(json.dumps(row, indent=2), encoding="utf-8")
    _commit_all(repo, "evil merge")
    assert append_only_violations("main", cwd=repo)


def test_refusals_are_named_and_never_passes(tmp_path, monkeypatch):
    """Prediction 5."""
    # outside any repository
    outside = tmp_path / "plain"
    outside.mkdir()
    with pytest.raises(Refusal, match="not inside a git repository"):
        append_only_violations("main", cwd=outside)
    # inside a worktree, `.git` is a FILE: must NOT refuse
    repo = _repo(tmp_path)
    wt = tmp_path / "wt"
    _git("worktree", "add", "-q", str(wt), "main", cwd=repo)
    try:
        assert append_only_violations("main", cwd=wt) == []
    finally:
        _git("worktree", "remove", "--force", str(wt), cwd=repo)
    # shallow clone
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo.as_posix()}", str(shallow)],
                   check=True, capture_output=True)
    with pytest.raises(Refusal, match="shallow"):
        append_only_violations("HEAD", cwd=shallow)
    # PAVE_BASE set and unresolvable: refuse, never fall through
    with pytest.raises(Refusal, match="PAVE_BASE='typo'"):
        resolve_base(env={"PAVE_BASE": "typo"}, cwd=repo)
    # no base at all
    with pytest.raises(Refusal, match="no base resolves"):
        _no_main(tmp_path)
    # git absent from PATH
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    with pytest.raises(Refusal, match="not on PATH"):
        append_only_violations("main", cwd=repo)


def _no_main(tmp_path):
    repo = tmp_path / "nomain"
    repo.mkdir()
    _git("init", "-q", "-b", "trunk", cwd=repo)
    _git("config", "user.email", "t@example.invalid", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    (repo / "a").write_text("a", encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "a", cwd=repo)
    return resolve_base(env={}, cwd=repo)


# --- decision 4: the collector ------------------------------------------------

def test_the_two_key_collector_diffs_without_rename_detection():
    """`git mv evals/run_adversarial.py evals/record_adversarial.py` + edit was
    "two-key: not required", exit 0. The workflow is two-key; this file is
    three-key, so removing the flag is red in a file with more keys."""
    workflow = (ROOT / ".github" / "workflows" / "two-key.yml").read_text(encoding="utf-8")
    diff_lines = [ln for ln in workflow.splitlines() if "git diff" in ln and "--name-only" in ln]
    assert diff_lines, "the collector's diff line moved"
    for line in diff_lines:
        assert "--no-renames" in line, line
    # and the rule still collects on the OLD path, which is what --no-renames reports
    assert twokey.triggered(["evals/run_adversarial.py", "evals/record_adversarial.py"])


def test_the_deciding_step_is_in_the_workflow():
    """Decision 3: the instance that decides takes its base from the event
    payload as an argument, writes its own verdict, and that verdict is one
    `gate decide` requires."""
    gate = (ROOT / ".github" / "workflows" / "quality-gate.yml").read_text(encoding="utf-8")
    assert "fetch-depth: 0" in gate
    assert re.search(r'gate history --base "\$\{\{ github\.event\.pull_request\.base\.sha \}\}" --out verdict-history\.json', gate)
    for step in ("gate decide", "gate comment"):
        line = next(ln for ln in gate.splitlines() if step in ln and "--verdicts" in ln)
        assert "verdict-history.json" in line, line


def test_pave_check_cannot_be_deselected_from_pyproject():
    source = (ROOT / "pave" / "cli.py").read_text(encoding="utf-8")
    start = source.index("def check(")
    body = source[start:source.index("\ndef ", start + 1)]
    assert '"-o", "addopts="' in body
    assert "deselected" in body
    # **The exact argv, not a substring.** The Platform seat measured that the
    # substring assertion is one-directional -- it requires a token to be PRESENT
    # and constrains nothing added beside it. Appending
    # `--ignore=tests/test_iam_assertions.py` kept `-o addopts=` in place, dropped
    # 24 tests, and left `pave check` PASS at exit 0 with `pave/cli.py` on no rule
    # (`test_ordinary_pr_is_not_gated` asserts it must stay that way, so the pin
    # lives here, in a three-key file, instead).
    argv = body[body.index("Popen(["):]
    argv = argv[argv.index("["):argv.index("]") + 1]
    assert argv == '[sys.executable, "-m", "pytest", "-q", "-o", "addopts="]', (
        f"`pave check` invokes pytest as {argv}. Any argument added here can drop tests "
        "without tripping the zero-collected or deselected guards. Changing the invocation "
        "is a gate-mechanism decision: amend this pin in the same diff and say why."
    )


# --- decision 5: the evidence anchor ------------------------------------------

def test_a_new_row_without_evidence_is_red(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["tag"] = "mzz"
    (h / "mzz-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("mzz-goldens.json carries no samples_from" in p for p in check_evidence(h))


def test_a_row_citing_another_milestones_evidence_is_red(tmp_path):
    """Security plant B: a fabricated mzz over M04's real evidence, 10/10."""
    h = _copy_history(tmp_path)
    row = json.loads((h / "m04-adversarial.json").read_text(encoding="utf-8"))
    row["tag"] = "mzz"
    row["arm"] = "rerun"
    (h / "mzz-adversarial.json").write_text(json.dumps(row), encoding="utf-8")
    problems = check_evidence(h)
    assert any("outside milestones/Mzz/" in p for p in problems)
    assert any("both cite milestones/M04/probes-run.json" in p for p in problems)


def test_evidence_that_moved_under_a_recorded_number_is_red(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m02-tools-goldens.json").read_text(encoding="utf-8"))
    row["samples_from"][0]["sha256"] = "0" * 64
    (h / "m02-tools-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("The evidence moved under a recorded number" in p for p in check_evidence(h))


def test_the_crlf_tolerance_is_for_legacy_rows_only(tmp_path):
    """Seven of ten records on main are CRLF digests; a NEW row gets no such
    tolerance."""
    h = _copy_history(tmp_path)
    row = json.loads((h / "m02-tools-goldens.json").read_text(encoding="utf-8"))
    row["tag"] = "m02"
    row["arm"] = "tools-again"
    (h / "m02-again-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    problems = check_evidence(h)
    assert any("m02-again-goldens.json" in p and "evidence moved" in p for p in problems)
    assert not any("m02-tools-goldens.json" in p and "evidence moved" in p for p in problems)


def test_the_m04_revision_row_is_exactly_what_the_tree_says():
    first, last, _ = EVIDENCE_REVISIONS["m04-adversarial.json"][0]
    entry = json.loads((HISTORY / "m04-adversarial.json").read_text(encoding="utf-8"))
    assert entry["samples_from"][0]["sha256"] == first
    committed = (ROOT / "milestones" / "M04" / "probes-run.json").read_text(encoding="utf-8")
    assert entry_digest(committed) == last
    assert len(EVIDENCE_REVISIONS) == 1 and len(EVIDENCE_REVISIONS["m04-adversarial.json"]) == 1, (
        "a second revision row needs three keys and its own sentence")


# --- decision 6: the denominator ----------------------------------------------

def test_a_fabricated_instrument_with_a_small_corpus_is_red(tmp_path, monkeypatch):
    """Security plant A: `m04-A2` between A and B, probes_sha256 of nothing,
    corpus_size 3, a 3/3 arm green."""
    registry = json.loads(history.INSTRUMENTS.read_text(encoding="utf-8"))
    rows = list(registry["instruments"].items())
    fake = dict(rows[0][1])
    fake["digests"] = dict(fake["digests"], probes_sha256="2c97a6de" + "0" * 56)
    fake["corpus_size"] = 3
    rows.insert(1, ("m04-A2", fake))
    registry["instruments"] = dict(rows)
    planted = tmp_path / "instruments.json"
    planted.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(history, "INSTRUMENTS", planted)
    problems = check_registry()
    assert any("m04-A2" in p and "no committed revision" in p for p in problems), problems


def test_a_new_adversarial_row_without_an_instrument_is_red(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m04-adversarial.json").read_text(encoding="utf-8"))
    del row["instrument"]
    row["tag"] = "mzz"
    (h / "mzz-adversarial.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("mzz-adversarial.json names no instrument" in p for p in check_registry(h))


def test_a_corpus_committed_only_inside_the_pr_does_not_register(tmp_path, monkeypatch):
    """Platform plant: commit a three-probe corpus, restore it, register the
    throwaway blob. `--all` saw it; the base does not."""
    registry = json.loads(history.INSTRUMENTS.read_text(encoding="utf-8"))
    repo = tmp_path / "repo"
    (repo / "quality" / "adversarial").mkdir(parents=True)
    (repo / "evals" / "history").mkdir(parents=True)
    shutil.copy(ROOT / "quality" / "adversarial" / "probes.yaml", repo / "quality" / "adversarial" / "probes.yaml")
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "t@example.invalid", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)
    _git("checkout", "-q", "-b", "pr", cwd=repo)
    import yaml
    full = yaml.safe_load((repo / "quality" / "adversarial" / "probes.yaml").read_text(encoding="utf-8"))
    shrunk = yaml.safe_dump(full[:3], sort_keys=False)
    (repo / "quality" / "adversarial" / "probes.yaml").write_text(shrunk, encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "shrink", cwd=repo)
    shutil.copy(ROOT / "quality" / "adversarial" / "probes.yaml", repo / "quality" / "adversarial" / "probes.yaml")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "restore", cwd=repo)
    registry["instruments"]["m04-F"] = {**registry["instruments"]["m04-E"], "corpus_size": 3,
                                        "digests": {**registry["instruments"]["m04-E"]["digests"],
                                                    "probes_sha256": history.corpus_digest(shrunk)}}
    planted = tmp_path / "instruments.json"
    planted.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(history, "INSTRUMENTS", planted)
    problems = check_registry(repo / "evals" / "history", cwd=repo, base="main")
    assert any("m04-F" in p and "no committed revision" in p for p in problems), problems


def test_every_entry_sha_is_reachable_from_main_or_a_tag():
    """`fb52a8e` (m01) lived only on the unmerged `m01-gateway` branch; tagged
    `evidence-m01` so a branch cleanup cannot turn every PR into a refusal."""
    try:
        assert history.check_reachable() == [], history.check_reachable()
    except Refusal as exc:
        pytest.fail(str(exc))


def test_gate_history_never_raises_a_bare_traceback(tmp_path, monkeypatch):
    """Prediction 5: `{bad` in pins.json wrote no verdict and paged platform."""
    h = _copy_history(tmp_path)
    (h / "pins.json").write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(history, "HISTORY", h)
    out = tmp_path / "verdict.json"
    proc = subprocess.run([sys.executable, "-c",
                           "import pathlib, sys; from pave import history, cli; "
                           f"history.HISTORY = pathlib.Path({str(h)!r}); "
                           f"cli.gate_history(['--base', 'main', '--out', {str(out)!r}])"],
                          cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    assert "JSONDecodeError" in proc.stdout
    assert json.loads(out.read_text(encoding="utf-8"))["verdict"] == "FAIL"


def test_a_lowered_corpus_size_is_red(tmp_path, monkeypatch):
    registry = json.loads(history.INSTRUMENTS.read_text(encoding="utf-8"))
    registry["instruments"]["m04-E"]["corpus_size"] = 3
    planted = tmp_path / "instruments.json"
    planted.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(history, "INSTRUMENTS", planted)
    assert any("m04-E: corpus_size is 3" in p for p in check_registry())


def test_an_entry_whose_total_is_not_its_instruments_corpus_is_red(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m04-adversarial.json").read_text(encoding="utf-8"))
    row["scores"]["total"] = 3
    (h / "m04-adversarial.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("scores.total is 3; instrument m04-A registers a corpus of 10" in p
               for p in check_registry(h))


def test_the_floor_for_an_unenumerated_arm_comes_from_the_registry(tmp_path):
    """Prediction 8, at the function: `asked_floor(mzz, 11, registered=3)` was
    3. Now the registry says what the arm ran under and the entry's total must
    agree, or the lane fails with both numbers named."""
    from pave.floors import asked_floor, registered_denominator
    root = tmp_path / "root"
    (root / "evals" / "history").mkdir(parents=True)
    (root / "quality" / "adversarial").mkdir(parents=True)
    shutil.copy(history.INSTRUMENTS, root / "quality" / "adversarial" / "instruments.json")
    row = json.loads((HISTORY / "m04-adversarial.json").read_text(encoding="utf-8"))
    registry = json.loads(history.INSTRUMENTS.read_text(encoding="utf-8"))["instruments"]
    row["instrument"] = {**row["instrument"], "name": "m04-E", **registry["m04-E"]["digests"]}
    row["scores"]["total"] = 3
    (root / "evals" / "history" / "mzz-adversarial.json").write_text(json.dumps(row), encoding="utf-8")
    size, problem = registered_denominator("mzz", root)
    assert size is None
    assert "`scores.total` 3" in problem and "corpus of 11" in problem
    assert asked_floor("mzz", 11, size) == 11
    row["scores"]["total"] = 11
    (root / "evals" / "history" / "mzz-adversarial.json").write_text(json.dumps(row), encoding="utf-8")
    assert registered_denominator("mzz", root) == (11, None)


def test_the_lane_fails_an_unenumerated_arm_that_asked_three_of_eleven(tmp_path):
    """Prediction 8, through the real lane. Security recorded exactly this arm
    under draft 2 and got PASS, exit 0. The pin is otherwise consistent so that
    the floor is the reason, asserted on its message: with the floor read
    replaced by `return 1`, `returncode == 1` stayed green for three unrelated
    reasons."""
    scratch = tmp_path / "repo"
    for part in ("evals", "quality", "pave", "platform", "services", "data", "milestones"):
        shutil.copytree(ROOT / part, scratch / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules", "cdk.out"))
    m04 = json.loads((ROOT / "milestones" / "M04" / "probes-run.json").read_text(encoding="utf-8"))
    asked = ["ADV-001", "ADV-003", "ADV-004"]
    obs = {"_asked": asked, "_k": m04["_k"], "_guardrail_versions": m04.get("_guardrail_versions"),
           **{pid: m04[pid] for pid in asked}}
    # `exist_ok` because this is the forty-fifth sentinel and the only one that is
    # not a string literal. The scratch repo is copied from the real tree, so the
    # moment `milestones/<TAG>/` exists on disk this raised FileExistsError -- and
    # the failure named an arm-scoping lane rather than a directory, sending the
    # reader somewhere else entirely. Renaming the sentinel to `Mzz` fixes it on
    # its own; this is the belt, because PR 6 creates `milestones/Mzz/` for real.
    (scratch / "milestones" / "Mzz").mkdir(exist_ok=True)
    (scratch / "milestones" / "Mzz" / "probes-run.json").write_text(json.dumps(obs, indent=2), encoding="utf-8")
    entry = json.loads((ROOT / "evals" / "history" / "m04-adversarial.json").read_text(encoding="utf-8"))
    registry = json.loads(history.INSTRUMENTS.read_text(encoding="utf-8"))["instruments"]
    entry["tag"] = "mzz"
    entry["instrument"] = {**entry["instrument"], "name": "m04-E", **registry["m04-E"]["digests"]}
    entry["cases"] = [c for c in entry["cases"] if c["id"] in asked]
    entry["scores"] = {**entry["scores"], "total": 3, "passed": 3, "failed": 0, "earned": 3,
                       "unstable": 0, "pass_rate": 1.0}
    entry["samples_from"] = [{"path": "milestones/Mzz/probes-run.json",
                              "sha256": entry_digest((scratch / "milestones" / "Mzz" / "probes-run.json")
                                                     .read_text(encoding="utf-8"))}]
    (scratch / "evals" / "history" / "mzz-adversarial.json").write_text(json.dumps(entry, indent=2), encoding="utf-8")
    comp_path = scratch / "evals" / "comparators.json"
    comp = json.loads(comp_path.read_text(encoding="utf-8"))
    suite = comp["services"]["highlights-agent"]["suites"]["adversarial"]
    m04pin = suite["pins"]["m04"]
    suite["pins"]["mzz"] = {
        **m04pin,
        "observations": ["milestones/Mzz/probes-run.json"],
        "recorded_passed": 3, "expected_passed": 3, "expected_earned": 3, "expected_scored": 3,
        "expected_results": {pid: ("PASS" if pid in asked else "OUT_OF_SCOPE")
                             for pid in m04pin["expected_results"]},
        "expected_unstable": [], "expected_unearned": [],
        "why_they_differ": "planted by test_history_append_only: an arm that asked three probes",
    }
    suite["pins_expected"] = sorted(set(suite["pins_expected"]) | {"mzz"})
    comp_path.write_text(json.dumps(comp, indent=2), encoding="utf-8")

    lane = subprocess.run([sys.executable, "-m", "pave.cli", "adversarial", "run", "services/highlights-agent"],
                          cwd=scratch, capture_output=True, text=True)
    assert lane.returncode != 0, lane.stdout
    assert "beneath its floor of 11" in lane.stdout, lane.stdout + lane.stderr
    assert "registers a corpus of 11" in lane.stdout, lane.stdout


def test_an_honest_k1_goldens_record_passes_every_offline_check(tmp_path, monkeypatch):
    """The AI Quality seat measured the real `--record` at k=1 refused by
    `check_evidence`, because the recorder wrote `samples_from` only at k>1.
    The honest path must be green, or the control teaches hand-editing."""
    from evals import run_evals
    h = tmp_path / "history"
    h.mkdir()
    shutil.copy(HISTORY / "schema.json", h / "schema.json")
    monkeypatch.setattr(run_evals, "HISTORY", h)
    rc = run_evals.main(["--answers", "milestones/M01/goldens-run.json", "--record",
                         "--tag", "m01", "--target", "highlights-agent"])
    assert rc in (0, 1), rc
    assert (h / "m01-goldens.json").is_file()
    assert check_pins(h) == []
    assert check_derivable(h) == [], check_derivable(h)
    assert check_evidence(h, ROOT) == [], check_evidence(h, ROOT)
    assert check_schema(h) == []
    written = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    assert written["samples_from"][0]["sha256"] == entry_digest(
        (ROOT / "milestones" / "M01" / "goldens-run.json").read_text(encoding="utf-8"))


def test_a_goldens_result_must_be_the_majority_of_its_samples(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m02-tools-goldens.json").read_text(encoding="utf-8"))
    case = next(c for c in row["cases"] if c["result"] == "FAIL" and c["samples"].count("FAIL") == 3)
    case["result"] = "PASS"
    row["scores"] = {**row["scores"], **history.derive_scores(row)}
    (h / "m02-tools-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("strict majority" in p for p in check_derivable(h))


def test_an_honest_arm_that_asked_ten_of_eleven_derives(tmp_path):
    """`pass_rate` is over scored probes: an ADR-041 arm with one OUT_OF_SCOPE
    is an honest row and was refused by a derivation over `total`."""
    h = tmp_path / "history"
    h.mkdir()
    row = json.loads((HISTORY / "m04-adversarial.json").read_text(encoding="utf-8"))
    row["cases"].append({"id": "ADV-011", "result": "OUT_OF_SCOPE"})
    row["scores"] = {**row["scores"], "total": 11, "out_of_scope": 1, "scored": 10, "pass_rate": 0.7}
    (h / "m04-adversarial.json").write_text(json.dumps(row), encoding="utf-8")
    assert check_derivable(h) == [], check_derivable(h)


def test_a_published_number_with_no_entry_behind_it_is_red(tmp_path):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    # **`m06`, not the migrated sentinel.** This is the one of the forty-five that
    # reads the LIVE README progression table, so it needs a tag that actually has
    # a row -- `mzz` has none and `next()` would raise StopIteration. It needs a row
    # whose goldens cell is still `-`, which `mzz` will stop being at this
    # milestone's close. README.md's `m06` row is the next unclosed one.
    row = next(ln for ln in text.splitlines() if "`m06`" in ln and ln.lstrip().startswith("|"))
    cells = row.split("|")
    cells[5] = " **22/25** "
    moved = tmp_path / "README.md"
    moved.write_text(text.replace(row, "|".join(cells), 1), encoding="utf-8")
    assert any("m06 row publishes a goldens number" in p for p in check_readme(readme=moved))


def test_an_entry_whose_sha_is_on_no_ref_and_under_no_tag_is_red(tmp_path):
    """`check_reachable` was deletable in silence: `return []` left 1784 green.
    Its own subject -- `fb52a8e`, reachable only through a branch that
    squash-merged and would be deleted as routine -- is why it exists."""
    repo = _repo(tmp_path, keep={"m01-goldens.json"})
    entry = json.loads((repo / "evals" / "history" / "m01-goldens.json").read_text(encoding="utf-8"))
    entry["sha"] = "0" * 40
    (repo / "evals" / "history" / "m01-goldens.json").write_text(json.dumps(entry), encoding="utf-8")
    problems = history.check_reachable(repo / "evals" / "history", cwd=repo)
    assert any("on no branch that merges and under no tag" in p for p in problems), problems


def test_a_sha_reachable_only_from_head_is_not_reachable(tmp_path):
    """`HEAD` used to count. In CI that is the PR's own merge commit, so a commit
    made inside the PR was "reachable" -- and the PR's branch is exactly the one
    that may not survive as that sha."""
    repo = _repo(tmp_path, keep={"m01-goldens.json"})
    (repo / "note.txt").write_text("x", encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "inside the pr", cwd=repo)
    head = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    entry = json.loads((repo / "evals" / "history" / "m01-goldens.json").read_text(encoding="utf-8"))
    entry["sha"] = head
    (repo / "evals" / "history" / "m01-goldens.json").write_text(json.dumps(entry), encoding="utf-8")
    problems = history.check_reachable(repo / "evals" / "history", cwd=repo)
    assert any("m01-goldens.json" in p for p in problems), problems
    _git("tag", "evidence-test", head, cwd=repo)
    assert history.check_reachable(repo / "evals" / "history", cwd=repo) == [], (
        "a tagged commit is reachable; only an untagged PR-local one is not")


def test_an_entry_tracked_as_a_symlink_in_the_index_is_red(tmp_path):
    """`check_modes` had no reference outside `run_all` -- nothing asserted it on
    an honest tree, let alone a violating one. A 120000 blob resolves on a Linux
    runner and is pinned as its target."""
    repo = _repo(tmp_path)
    blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], input="m02-tools-goldens.json",
                          cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    _git("update-index", "--cacheinfo", f"120000,{blob},evals/history/m01-goldens.json", cwd=repo)
    problems = history.check_modes(cwd=repo)
    assert any("mode 120000" in p for p in problems), problems


def test_a_goldens_entry_whose_case_ids_disagree_with_its_own_commit_is_red(tmp_path):
    """`check_case_ids` was deletable in silence too."""
    repo = _repo(tmp_path, keep={"m01-goldens.json"})
    cases = repo / "services" / "highlights-agent" / "evals" / "golden"
    cases.mkdir(parents=True)
    (cases / "cases.yaml").write_text("- id: only-case\n", encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "a golden file", cwd=repo)
    sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    entry = json.loads((repo / "evals" / "history" / "m01-goldens.json").read_text(encoding="utf-8"))
    entry["sha"] = sha
    (repo / "evals" / "history" / "m01-goldens.json").write_text(json.dumps(entry), encoding="utf-8")
    problems = check_case_ids(repo / "evals" / "history", cwd=repo)
    assert any("apart from the golden file" in p for p in problems), problems


def test_the_asked_floor_literals_are_ratcheted_to_what_each_arm_recorded():
    """`ASKED_FLOOR` set to all zeros left 1784 green, in the file whose own
    docstring says "a floor is only half a floor without its ratchet". Each
    literal is what that arm's own published entry scored: an arm cannot be
    given an allowance below the run it recorded."""
    from pave.floors import ASKED_FLOOR
    for tag, floor in ASKED_FLOOR.items():
        entry = json.loads((HISTORY / f"{tag}-adversarial.json").read_text(encoding="utf-8"))
        scored = sum(1 for c in entry["cases"] if c["result"] != "OUT_OF_SCOPE")
        assert floor == scored, (
            f"{tag}'s floor is {floor} and its published entry scored {scored}. A floor beneath "
            "the run it describes is an allowance for probes to stop counting.")


def test_a_new_arm_may_not_name_a_superseded_instrument(tmp_path):
    """Security, against the code: `corpus_size` on the four stale registry rows
    made each a valid floor-setting denominator. A fabricated `mzz` naming
    `m04-A` claimed 10/10, was never asked ADV-011 -- the newest probe -- and
    every check was clean. The recorder refuses this; a hand-written row never
    goes through the recorder."""
    repo = _repo(tmp_path, keep=set())
    _git("checkout", "-q", "main", cwd=repo)   # the corpus belongs to the BASE
    shutil.copytree(ROOT / "quality", repo / "quality")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "corpus", cwd=repo)
    _git("checkout", "-q", "-b", "pr2", cwd=repo)
    registry = json.loads((repo / "quality" / "adversarial" / "instruments.json").read_text(encoding="utf-8"))
    stale = registry["instruments"]["m04-A"]
    row = json.loads((HISTORY / "m04-adversarial.json").read_text(encoding="utf-8"))
    row["tag"] = "mzz"
    # A sha that exists in this throwaway repo, so the corpus-at-sha tie can run
    # rather than refusing before the check under test is reached.
    row["sha"] = _git("rev-parse", "main", cwd=repo).stdout.strip()
    row["instrument"] = {**row["instrument"], "name": "m04-A", **stale["digests"]}
    (repo / "evals" / "history" / "mzz-adversarial.json").write_text(json.dumps(row), encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "a new arm on a superseded instrument", cwd=repo)
    problems = check_registry(repo / "evals" / "history", cwd=repo, base="main")
    assert any("is a new arm naming instrument" in p for p in problems), problems
    # and the committed arm, which legitimately names m04-A, stays green
    assert not any("m04-adversarial.json is a new arm" in p for p in check_registry())


def test_one_unreadable_file_does_not_erase_every_other_finding(tmp_path):
    """Security plant: a fabricated unpinned row plus one file containing
    `[1,2,3]` reported ONE problem naming the junk, because `_entries` raised
    out of the first check and the collected problems were discarded."""
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["scores"]["passed"] = 24
    (h / "mzz-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    (h / "m06-goldens.json").write_text("[1,2,3]", encoding="utf-8")
    problems, refusals = history.run_all(None, history=h, cwd=ROOT)
    assert any("m06-goldens.json is not a JSON object" in p for p in problems), problems
    assert any("mzz-goldens.json is on disk and not in pins.json" in p for p in problems), problems
    assert len(problems) > 3, problems


def test_gate_history_refuses_an_empty_base():
    """`--base ""` -- what the event expression expands to the day this workflow
    gains merge_group or push -- fell through to `origin/main` and printed PASS
    at exit 0."""
    proc = subprocess.run([sys.executable, "-m", "pave.cli", "gate", "history", "--base", ""],
                          cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout
    assert "was given no value" in proc.stdout


def test_the_schema_is_byte_pinned():
    """The ratchet refuses a requirement no entry meets and cannot see the schema
    LOOSENED -- a `pattern` dropped from `sha`, the instrument sub-schema removed."""
    assert entry_digest(
        (HISTORY / "schema.json").read_text(encoding="utf-8")) == history.SCHEMA_DIGEST


# --- decision 7: a second row must say why -----------------------------------

def test_a_second_row_under_one_sha_that_declares_nothing_is_refused(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["scores"]["passed"] = 25
    (h / "m01-again-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("declare no difference" in p for p in check_second_rows(h))


def test_the_canonical_m00b_pair_is_not_refused():
    """Instrument absent versus present counts as differing -- draft 2's
    wording would have turned `main` red on the repo's own judged anchor."""
    assert check_second_rows() == []


@pytest.mark.parametrize("target, expect", [
    ("m01-goldens.json", None),
    ("not-an-entry.json", "is not an entry on disk"),
    ("m01-adversarial.json", "a different suite"),
])
def test_supersedes_resolves_to_a_file_on_disk_of_the_same_suite(tmp_path, target, expect):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["scores"]["passed"] = 20
    row["cases"][0]["result"] = "PASS" if row["cases"][0]["result"] != "PASS" else "FAIL"
    row["supersedes"] = target
    (h / "m01-correction1-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    problems = check_second_rows(h)
    if expect is None:
        assert not any("m01-correction1" in p for p in problems), problems
    else:
        assert any(expect in p for p in problems), problems


def test_a_correction_that_corrects_nothing_and_a_self_supersede_are_refused(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["supersedes"] = "m01-goldens.json"
    (h / "m01-correction1-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("identical scores and cases" in p for p in check_second_rows(h))
    row["supersedes"] = "m01-correction1-goldens.json"
    (h / "m01-correction1-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("supersedes itself" in p for p in check_second_rows(h))


def test_two_corrections_of_one_entry_are_refused(tmp_path):
    h = _copy_history(tmp_path)
    row = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))
    row["supersedes"] = "m01-goldens.json"
    row["scores"]["passed"] = 20
    for n in (1, 2):
        (h / f"m01-correction{n}-goldens.json").write_text(json.dumps(row), encoding="utf-8")
    assert any("both supersede m01-goldens.json" in p for p in check_second_rows(h))


def test_a_correction_can_be_recorded_end_to_end(tmp_path, monkeypatch):
    """Prediction 11: a real `--supersedes` invocation of the goldens recorder
    lands under a `-correctionN-` filename, pinned, and the checks pass."""
    from evals import run_evals
    h = _copy_history(tmp_path)
    monkeypatch.setattr(run_evals, "HISTORY", h)
    original = json.loads((h / "m01-goldens.json").read_text(encoding="utf-8"))

    class Args:
        tag = "m01"
        target = original["target"]
        arm = None
        sha = None
        tokens_in = None
        tokens_out = None
        supersedes = "m01-goldens.json"

    class R:
        def __init__(self, id, result):
            self.id, self.result, self.unearned, self.unearned_reason = id, result, False, None

    # identical numbers: refused before anything is written
    with pytest.raises(SystemExit, match="corrects nothing"):
        run_evals.record([R(c["id"], c["result"]) for c in original["cases"]], original["scores"], Args())
    assert not (h / "m01-correction1-goldens.json").exists()

    results = [R(c["id"], c["result"]) for c in original["cases"]]
    results[0].result = "PASS" if results[0].result != "PASS" else "FAIL"
    scores = history.derive_scores({"suite": "goldens", "cases": [{"id": r.id, "result": r.result} for r in results]})
    sources = run_evals._sources([ROOT / "milestones" / "M01" / "goldens-run.json"])
    sources[0]["path"] = "milestones/M01/goldens-run.json"
    path = run_evals.record(results, scores, Args(), sources=sources)
    assert path.name == "m01-correction1-goldens.json"
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["supersedes"] == "m01-goldens.json" and written["sha"] == original["sha"]
    # every check that does not need git, on the directory the correction landed in
    assert check_pins(h) == [], check_pins(h)
    assert check_second_rows(h) == []
    assert check_schema(h) == []
    assert check_derivable(h) == []
    assert check_evidence(h, ROOT) == [], check_evidence(h, ROOT)
    # a second correction of the same entry: refused -- the chain is linear
    with pytest.raises(SystemExit, match="already superseded"):
        run_evals.record(results, scores, Args())
    # correcting the correction: counts, never nests, and the chain is one difference
    results[1].result = "PASS" if results[1].result != "PASS" else "FAIL"
    scores = history.derive_scores({"suite": "goldens", "cases": [{"id": r.id, "result": r.result} for r in results]})
    Args.supersedes = "m01-correction1-goldens.json"
    path = run_evals.record(results, scores, Args(), sources=sources)
    assert path.name == "m01-correction2-goldens.json"
    assert check_second_rows(h) == [], check_second_rows(h)


def test_the_schema_may_not_gain_a_requirement_a_committed_entry_fails(tmp_path):
    """Prediction 12. Both forms: a top-level required field, and a conditional
    keyed on `suite` -- which draft 3 thought was safe and is not."""
    h = _copy_history(tmp_path)
    schema = json.loads((h / "schema.json").read_text(encoding="utf-8"))
    schema["required"].append("samples_from")
    (h / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    problems = check_schema(h)
    assert any("top-level required" in p for p in problems)
    assert any("no longer validates" in p for p in problems)
    schema = json.loads((HISTORY / "schema.json").read_text(encoding="utf-8"))
    schema["allOf"].append({"if": {"properties": {"suite": {"const": "goldens"}}, "required": ["suite"]},
                            "then": {"required": ["samples_from"]}})
    (h / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    assert any("m01-goldens.json no longer validates" in p for p in check_schema(h))
    # a conditional keyed on a field only new rows declare: fine
    schema = json.loads((HISTORY / "schema.json").read_text(encoding="utf-8"))
    schema["allOf"].append({"if": {"required": ["supersedes"]}, "then": {"required": ["samples_from"]}})
    (h / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    # The byte pin fires (the file changed, deliberately, in this copy); what must
    # NOT fire is a committed entry ceasing to validate.
    assert not any("no longer validates" in p for p in check_schema(h)), check_schema(h)
    assert any("digests to" in p for p in check_schema(h))


# --- decision 8: every protection on the keys of what it protects -------------

@pytest.mark.parametrize("path", [
    "evals/history/mzz-goldens.json", "evals/history/schema.json", "evals/history/pins.json",
    "evals/history/goldens.json", "evals/history/sub/x.json", "evals/history/m00b-judged-B-goldens.json",
    "evals/run_evals.py", "evals/run_adversarial.py", "pave/history.py",
    "tests/test_history_append_only.py", "tests/test_arm_scoping.py", "tests/test_adversarial_entry.py",
    "pave/floors.py", "evals/comparators.json",
])
def test_every_protection_takes_at_least_the_three_keys(path):
    """Prediction 7, fourth time. A seat stripped `security` from every three-seat
    rule -- a two-key change -- and got one failure, in a zero-key file."""
    seats = {s for rule, _ in twokey.triggered([path]) for s in rule.seats}
    assert seats >= THREE, f"{path} takes {sorted(seats)}"


def test_goldens_evidence_and_the_corpus_registry_take_keys():
    for path, want in (("milestones/Mzz/goldens-run.json", {"ai-quality", "platform-eng"}),
                       ("milestones/M02/runs/m02-tools-1.json", {"ai-quality", "platform-eng"}),
                       ("quality/adversarial/instruments.json", {"security"})):
        seats = {s for rule, _ in twokey.triggered([path]) for s in rule.seats}
        assert want <= seats, f"{path} takes {sorted(seats)}"


def test_the_history_rule_requires_an_attestation_from_all_three():
    body = "\n".join(f"Two-Key-Disposition: {s}" for s in THREE) + (
        "\nTwo-Key-Rationale: recorded the milestone's golden run as measured, no threshold "
        "baseline or probe moved, every entry on disk pinned by the recorder\n")
    assert twokey.evaluate(["evals/history/mzz-goldens.json"], body) == []
    for missing in THREE:
        partial = "\n".join(f"Two-Key-Disposition: {s}" for s in THREE - {missing}) + body.split("\n", 3)[3]
        assert twokey.evaluate(["evals/history/mzz-goldens.json"], partial), f"green without {missing}"


def test_every_anchored_arm_cites_the_evidence_its_anchor_names():
    """Decision 5's `ARMS[tag][0] == entry.samples_from[0].path`."""
    from tests.test_arm_scoping import ARMS
    checked = 0
    for tag, (obs, entry_path) in ARMS.items():
        entry = json.loads((ROOT / entry_path).read_text(encoding="utf-8"))
        if "samples_from" not in entry:
            assert entry_path.rsplit("/", 1)[-1] in history.LEGACY_WITHOUT_EVIDENCE
            continue
        assert entry["samples_from"][0]["path"] == obs, tag
        checked += 1
    assert checked >= 1


def test_the_adversarial_anchor_agrees_with_the_complete_pin():
    from tests.test_arm_scoping import HISTORY_DIGESTS
    pins = history.load_pins()
    for name, digest in HISTORY_DIGESTS.items():
        assert pins.get(name) == digest, f"{name}: test_arm_scoping pins {digest[:12]}, pins.json {str(pins.get(name))[:12]}"


def test_no_recorded_number_moved():
    """Prediction 14, on the tree this file ships in."""
    m04 = json.loads((HISTORY / "m04-adversarial.json").read_text(encoding="utf-8"))
    assert m04["scores"]["passed"] == 7 and m04["scores"]["total"] == 10
    m01 = json.loads((HISTORY / "m01-goldens.json").read_text(encoding="utf-8"))
    assert m01["scores"]["passed"] == 19
    assert "**19/25**" in (ROOT / "README.md").read_text(encoding="utf-8")
