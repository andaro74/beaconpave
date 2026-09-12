"""
M09b's ordering check: no candidate wording is committed before, or with, a corpus
that judges it (SPEC/09b F4, third clause).

## Its limit, published here and not only in a PR body

**This test reads commit order. It constrains commitment, not authorship.** It
proves *when bytes were committed*; the hazard is *what the author had read*. An
author who has read every committed corpus can write a fitted candidate and commit
it in the right order, and this test goes green. No test can close that, because
the evidence does not exist in the repository (ADR-076 amendment 1, F-4). It is
closed structurally, by separating candidate authorship from the judging corpus, or
it is published.

Three narrower limits, each measured on this repository rather than assumed:

- **A squash merge erases order inside a pull request.** `main`'s merges are squash
  merges (`4710f31` has one parent, committed by GitHub), so a corpus and a
  candidate committed in order on one branch land in `main` as one commit, and this
  test then reads them as committed together, which is red. The order survives on
  `main` only across pull requests, or under a rebase merge.
- **It reads the history HEAD can reach, and a branch can be rewritten before it
  merges.** A candidate committed first and reordered by a rebase is invisible here.
- **It does not follow renames.** A corpus moved to a new path starts a new history
  under that path.

**A shallow clone fails this test rather than skipping it.** A truncated history
would make a candidate look like it has no corpus behind it or, worse, make an
early candidate look like it has none before it. CI checks out with
`fetch-depth: 0` (`.github/workflows/quality-gate.yml`).

Hermetic (G8): reads this repository's git history and builds throwaway
repositories under `tmp_path`. Owning seats: AI Quality · Platform Engineering ·
Security.
"""
from __future__ import annotations

import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The limit sentence the docstring must keep. Deleting the published limit is a
#: change to what this test claims, so it is red rather than an edit to prose.
LIMIT = "It constrains commitment, not authorship."

#: What SPEC/09b PR 3 commits and ADR-077 decision 2 fixes by digest.
CANDIDATES = "milestones/M09b/candidates.json"

#: Every file ADR-077 decision 3 licenses to strike a candidate, for either topic,
#: from its licence table. A candidate set covering both topics follows all of
#: them. `refusal-shapes.yaml`, `answer-decomposition.yaml`, `probes.yaml` and every
#: goldens answer file are absent on purpose: they judge nothing (decision 5).
JUDGING = (
    "quality/adversarial/topic-attacks.yaml",
    "quality/adversarial/topic-attacks-heldout.yaml",
    "quality/adversarial/topic-attacks-output.yaml",
    "quality/adversarial/phrasings.yaml",
    "quality/adversarial/disclosure-shapes.yaml",
    "data/catalog.json",
    "services/highlights-agent/evals/golden/cases.yaml",
)


def _git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def violations(repo: pathlib.Path, judged: str, corpora: tuple[str, ...]) -> list[str]:
    """Every commit touching `judged` at which some corpus was not already committed
    in a strictly earlier commit.

    Read at each such commit rather than against today's corpus, so a corpus
    legitimately edited after the candidates were judged does not turn this red:
    the property is the order at the moment of commitment."""
    found = []
    for commit in _git(repo, "log", "--format=%H", "--", judged).split():
        for corpus in corpora:
            latest = _git(repo, "log", "-1", "--format=%H", commit, "--", corpus)
            if not latest:
                found.append(f"{commit[:12]} commits {judged} before {corpus} exists")
            elif latest == commit:
                found.append(f"{commit[:12]} commits {judged} together with {corpus}")
    return found


def test_the_published_limit_is_still_published():
    assert LIMIT in (__doc__ or ""), (
        "this file's docstring no longer says what it cannot prove. SPEC/09b requires the "
        "limit beside the test, and a check that reads stronger than it is is the defect "
        "one level out.")


def test_this_repository_is_not_a_shallow_clone():
    assert _git(ROOT, "rev-parse", "--is-shallow-repository") == "false", (
        "a shallow clone cannot show what was committed before what. This fails rather than "
        "skips: a truncated history reads as a clean one.")


@pytest.mark.parametrize("corpus", JUDGING)
def test_every_judging_corpus_is_committed(corpus):
    """Anti-vacuity. A corpus with no history would make the order check below
    report every candidate commit as preceding it, which is loud; this names the
    corpus instead of the symptom."""
    assert _git(ROOT, "log", "-1", "--format=%H", "--", corpus), (
        f"{corpus} has no commit reachable from HEAD")


def test_no_candidate_is_committed_before_or_with_a_corpus_that_judges_it():
    assert not violations(ROOT, CANDIDATES, JUDGING), violations(ROOT, CANDIDATES, JUDGING)


# --- the plants, each in a throwaway repository ---------------------------------

def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "plant@example.invalid")
    _git(repo, "config", "user.name", "plant")
    _git(repo, "config", "commit.gpgsign", "false")
    return repo


def _commit(repo: pathlib.Path, files: dict[str, str], message: str) -> None:
    for name, text in files.items():
        (repo / name).write_text(text, encoding="utf-8", newline="\n")
        _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)


def test_a_candidate_committed_before_its_corpus_is_red(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, {"cand.json": "1"}, "candidate")
    _commit(repo, {"corpus.yaml": "1"}, "corpus")
    assert violations(repo, "cand.json", ("corpus.yaml",))


def test_a_candidate_committed_in_the_same_commit_as_its_corpus_is_red(tmp_path):
    """The seat plant SPEC/09b names for PR 3's rounds."""
    repo = _repo(tmp_path)
    _commit(repo, {"corpus.yaml": "1", "cand.json": "1"}, "both")
    assert violations(repo, "cand.json", ("corpus.yaml",))


def test_a_candidate_edited_together_with_its_corpus_is_red(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, {"corpus.yaml": "1"}, "corpus")
    _commit(repo, {"cand.json": "1"}, "candidate")
    _commit(repo, {"corpus.yaml": "2", "cand.json": "2"}, "refit")
    assert violations(repo, "cand.json", ("corpus.yaml",))


def test_a_candidate_committed_after_every_corpus_is_clean(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, {"corpus.yaml": "1", "other.yaml": "1"}, "corpora")
    _commit(repo, {"cand.json": "1"}, "candidate")
    assert violations(repo, "cand.json", ("corpus.yaml", "other.yaml")) == []


def test_a_corpus_edited_after_the_candidates_does_not_turn_it_red(tmp_path):
    """The property is the order at commitment. A check that read today's corpus
    would go red the first time the data legitimately changed."""
    repo = _repo(tmp_path)
    _commit(repo, {"corpus.yaml": "1"}, "corpus")
    _commit(repo, {"cand.json": "1"}, "candidate")
    _commit(repo, {"corpus.yaml": "2"}, "later edit")
    assert violations(repo, "cand.json", ("corpus.yaml",)) == []


def test_one_missing_corpus_among_several_is_red(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, {"corpus.yaml": "1"}, "corpus")
    _commit(repo, {"cand.json": "1"}, "candidate")
    _commit(repo, {"late.yaml": "1"}, "a judging corpus arriving late")
    assert violations(repo, "cand.json", ("corpus.yaml", "late.yaml"))
