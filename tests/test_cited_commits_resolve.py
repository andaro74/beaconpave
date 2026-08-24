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
`docs/` or `SPEC/` resolves AND is reachable from some ref. Hermetic (G8): local
object database only, no network.

**Audited by deletion.** Removing the reachability assertion and keeping
`cat-file -t` leaves all 35 green with every tag deleted -- existence in the
object database is not the property that failed, and a check for it alone is
decoration. With the assertion restored and the tags gone, six go red and name
the documents. Only the reachability half is load-bearing; `cat-file` is kept
for the clearer message on a typo'd SHA, not because it catches anything the
other does not.

**The path half is deliberately absent, and measured rather than assumed.** A
first version checked backticked repo-relative paths too and produced 46
failures, of which one was real. The rest were prose shorthand (`core/audit.py`
for `platform/gateway/core/audit.py`), forward references a spec is supposed to
make (`pave/manifest.py`, `tests/test_manifest_verify.py` -- M05 builds them),
and deliberately-nonexistent plant paths (`pave/tests/conftest.py`). Separating
those needs an exemption list, which is the denylist shape ADR-043 named as its
own weakest decision. Recorded as owed instead of shipped with 45 exemptions.
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
    refs = _git("for-each-ref", "--contains", sha, "--format=%(refname:short)")
    assert refs.stdout.strip(), (
        f"{rel} cites `{sha}`, which no branch or tag contains. It survives only until "
        f"`git gc` and is absent from every fresh clone. Tag it (see `drafts-spec-05`, "
        f"`drafts-adr-042`) or stop citing it.")
