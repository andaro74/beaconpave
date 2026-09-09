"""A citation that resolves in the author's clone and nowhere else.

`ADR-042:17` says *"Draft 3 is at `33e5871`"* and `SPEC/05-paved-road.md:18` said
drafts 1-3 were *"preserved at `scratchpad/SPEC-05-draft{1,2,3}.md`"*. Neither
resolved on `main`:

- **The SHA was reachable from no ref.** `spec-05-paved-road` and
  `adr-042`-era branches were squash-merged, GitHub deleted them, and the draft
  commits survived only in the author's reflog until gc. A fresh clone gets
  `fatal: bad object`.
- **The path never existed in the repo at all.** It was a session scratch
  directory, and it is deleted when the session ends.

Both documents claim in prose that the superseded reasoning is preserved, which
is the repo's stated reason for keeping drafts. The claim was true locally and
false for every reader -- CLAUDE.md's "stated and absent" shape, arriving through
squash-merge rather than through anyone deciding anything.

This pins the half of that which can be checked honestly: every commit cited in
`docs/` or `SPEC/` resolves AND is reachable **from `main` or from a tag**.

**"Some ref" was too weak, and M08b PR 4 tightened it.** `git for-each-ref
--contains` counts every ref in the local clone, including the remote-tracking
branch of a PR that has been merged and whose branch was never deleted -- which
is this repository's own convention (`close-milestone` step 7: *"Do not delete
the merged branch"*). So a document citing a commit on its own feature branch
passed here forever in the author's clone, and in a fresh clone that ref is a
remote-tracking branch that a reader following the citation may or may not have,
depending on their refspec and on whether the branch has since been pruned. The
fuse is longer than the deleted-branch one and it is the same fuse.

**Measured, at PR 4's branch point:** 114 SHA citations across 124 markdown
files, and **zero** go red under the tightened rule -- because ADR-074 amendment
3 was held to it by hand before PR 3 merged and closed the two exposed citations
with tags (`cited-m08b-pr2-r1`, `cited-m08b-pr2-r2`) rather than dating them. The
tightening is not vacuous: PR 3's own branch commits are found by two refs under
the old rule and by none under this one.

**`main` however it is spelled, and that is not laxity.** `refs/heads/main` in a
working clone, `refs/remotes/*/main` in a clone that has not checked it out, and
in this repository local `main` is routinely a few merges behind `origin/main` --
a rule anchored on the local branch alone would report a citation of a
just-merged commit as unreachable, which is a false red on the honest case the
rule exists to permit. What is excluded is every OTHER remote-tracking ref, which
is the class the fuse lives in.

**Audited by deletion.** Removing the reachability assertion and keeping
`cat-file -t` leaves all 35 green with every tag deleted -- existence in the
object database is not the property that failed, and a check for it alone is
decoration. With the assertion restored and the tags gone, six go red and name
the documents. Only the reachability half is load-bearing; `cat-file` is kept
for the clearer message on a typo'd SHA, not because it catches anything the
other does not.

**And audited again at the tightening.** Widening `REACHABLE_FROM` back to every
ref leaves a planted citation of a live feature-branch commit green, which is the
whole of what the tightening buys and is what
`test_a_commit_only_a_feature_branch_holds_is_not_reachable` asserts directly
rather than by hoping such a commit exists in the corpus.

**The path half is deliberately absent, and measured rather than assumed.** A
first version checked backticked repo-relative paths too and produced 46
failures, of which one was real. The rest were prose shorthand (`core/audit.py`
for `platform/gateway/core/audit.py`), forward references a spec is supposed to
make (`pave/manifest.py`, `tests/test_manifest_verify.py` -- M05 builds them),
and deliberately-nonexistent plant paths (`pave/tests/conftest.py`). Separating
those needs an exemption list, which is the denylist shape ADR-043 named as its
own weakest decision. Recorded as owed instead of shipped with 45 exemptions.

Hermetic (G8): local object database only, no network.
Owning seats: Platform Engineering (the mechanism) - PM (the citations a reader
follows); the debt SPEC/08b records names both.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Scanned for citations. `docs/` and `SPEC/` are what a reader is pointed at.
SCANNED = sorted(
    p for d in ("docs", "SPEC") for p in (ROOT / d).rglob("*.md")
)

#: A backticked 7-40 char lowercase hex run. Long enough not to catch `abc`, and
#: `[0-9a-f]` only, so `m04-gate` and `2500` never match.
SHA = re.compile(r"`([0-9a-f]{7,40})`")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def _reachable_from() -> list[str]:
    """The refs a fresh clone is guaranteed to have: `main`, and every tag.

    Built by listing rather than by pattern, so `for-each-ref --contains` is given
    concrete refs and a clone missing one of them does not silently widen the set
    -- `--contains` over a pattern that matches nothing returns nothing, which
    would make every citation unreachable rather than every citation reachable.
    That direction is the safe one, and `test_the_allowed_ref_set_is_not_empty`
    is what says it never happens quietly."""
    refs = _git("for-each-ref", "--format=%(refname)",
                "refs/heads/main", "refs/remotes/*/main", "refs/tags/").stdout.split()
    return refs


#: Every ref a citation may be reachable from. A remote-tracking FEATURE branch is
#: not one: it is what the merged-and-undeleted branch convention leaves behind,
#: and it is present in the author's clone and absent from a reader's.
REACHABLE_FROM = _reachable_from()


def test_the_allowed_ref_set_is_not_empty():
    """`--contains` over an empty ref list reports nothing contains anything, and
    every case below would go red naming the wrong cause -- a reader would go
    looking for a bad citation when the real fault is that `main` was not found.
    Both halves asserted, because a clone with tags and no `main` is a real state
    (a detached CI checkout) and it is not one this rule can be run under."""
    assert REACHABLE_FROM, (
        "no `main` and no tags in this clone, so the reachability rule has nothing to "
        "measure against. This is a broken checkout, not a broken citation.")
    assert any(r.endswith("/main") for r in REACHABLE_FROM), (
        f"no ref named `main` among {len(REACHABLE_FROM)} refs. Every citation would "
        "report unreachable, naming the documents rather than the checkout.")


def test_a_commit_only_a_feature_branch_holds_is_not_reachable():
    """**The tightening, asserted directly.**

    The corpus is supposed to contain no such citation -- that is the point -- so
    a test that waited for one to appear would be green on the day the rule was
    deleted. This constructs the condition instead: a commit on a branch that is
    neither `main` nor a tag must be reported unreachable HERE while
    `for-each-ref` over all refs still finds it. If both halves stop disagreeing,
    the rule has quietly gone back to counting every ref.

    Skipped rather than failed where no such commit exists (a fresh clone with one
    branch), because that is a property of the checkout and not of the rule."""
    heads = _git("for-each-ref", "--format=%(refname)", "refs/heads/").stdout.split()
    candidates = [h for h in heads if not h.endswith("/main")]
    for ref in candidates:
        sha = _git("rev-parse", ref).stdout.strip()
        if not sha:
            continue
        if _git("for-each-ref", "--contains", sha, *REACHABLE_FROM).stdout.strip():
            continue  # merged, or tagged: not a witness
        assert _git("for-each-ref", "--contains", sha).stdout.strip(), (
            "`for-each-ref` cannot see the branch it just listed")
        return
    pytest.skip("no unmerged, untagged branch in this clone to witness the tightening")


SHA_CITATIONS = [
    (p, m.group(1))
    for p in SCANNED
    for m in SHA.finditer(p.read_text(encoding="utf-8"))
]


def test_the_scanner_actually_finds_citations():
    """A scanner that matches nothing makes every test below vacuously green --
    the shape ADR-043's own anti-vacuity guard was found to have."""
    assert len(SHA_CITATIONS) >= 10, f"only {len(SHA_CITATIONS)} SHA citations found; the regex is stale"
    assert len(SCANNED) >= 20, f"only {len(SCANNED)} markdown files scanned"


@pytest.mark.parametrize("doc,sha", SHA_CITATIONS, ids=lambda v: v if isinstance(v, str) else v.name)
def test_every_cited_commit_is_reachable_from_a_ref(doc: pathlib.Path, sha: str):
    """Existing in the object database is not enough: an unreachable commit is
    collected by gc and is absent from every clone. `33e5871` passed
    `cat-file -t` in the author's checkout while being unreachable from any ref."""
    rel = doc.relative_to(ROOT).as_posix()
    kind = _git("cat-file", "-t", sha)
    assert kind.returncode == 0 and kind.stdout.strip() == "commit", (
        f"{rel} cites `{sha}`, which is not a commit in this repository. "
        f"A reader following it gets `fatal: bad object`.")
    refs = _git("for-each-ref", "--contains", sha, "--format=%(refname:short)",
                *REACHABLE_FROM)
    if refs.stdout.strip():
        return
    elsewhere = _git("for-each-ref", "--contains", sha, "--format=%(refname:short)")
    found = sorted(elsewhere.stdout.split())
    # `raise`, not `assert False`: under `python -O` an assertion is removed and
    # this branch would fall through to a silent pass, which is the failure mode
    # the whole file is about.
    raise AssertionError(
        f"{rel} cites `{sha}`, which neither `main` nor any tag contains"
        + (f" -- only {found}. Those are branch refs: in this clone they exist because "
           "the merged branch was kept (`close-milestone` step 7), and in a fresh clone "
           "they are remote-tracking refs a reader may not fetch and `git gc` may prune. "
           if found else
           ". It is reachable from no ref at all, so it survives only until `git gc`. ")
        + "Tag the commit before the PR merges -- `cited-<sha>` or `cited-<milestone>-<pr>` "
          "(see `cited-m08b-pr2-r1`, `drafts-adr-042`) -- or cite the merge commit on "
          "`main` instead.")
