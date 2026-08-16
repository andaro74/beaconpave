"""
L1 contract tests: no AWS account identifier is committed to this repo.

The repo went public on 2026-08-15. From M00b it starts writing eval history and
journals from real runs; at M01 it grows an audit lake whose records the
adversarial suite greps, and CDK synth output that names real resources. Every
one of those is a plausible route for an account ID to arrive in a diff —
pasted into a journal to show a command that worked, captured in a fixture,
copied out of a console.

A leaked account ID cannot be taken back by a later commit. It stays in the
history, and rewriting the history of a public repo that other clones already
have is not a fix. So the check has to exist before the first thing that could
leak, which is now.

**Scope, and the one judgement call in it.** Two rules:

1. No 12-digit account ID anywhere in a committed file.
2. No **account-qualified** ARN — one whose account field is populated.

An ARN with an *empty* account field (`arn:aws:bedrock:us-west-2::foundation-
model/...`) is permitted by design, and that is a narrowing of the rule as
originally stated. Those ARNs identify a public, service-owned resource; they
carry nothing about this account, and M01's IAM assertions will need to name
one to express what the gateway role may invoke. A guard that fails on them
would have to be weakened the first time it fires, under deadline, by whoever
is least inclined to argue with it — and a guard that everyone expects to
weaken is not a guard. Widening this to all `arn:aws:` strings is a Data
Governance decision and wants an ADR, not a quiet edit here.

This module is excluded from its own scan: it has to spell out the patterns it
searches for.

Hermetic (G8): reads committed files, no network.
Owning seat: Data Governance.
"""
import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SELF = pathlib.Path(__file__).resolve()

#: Twelve digits, not part of a longer number and not the fraction of a decimal.
#: The `(?<![\d.])` matters: a duration like `0.123456789012` is not an account
#: ID, and a false positive here reds `main` for a reason nobody can act on —
#: which is how a guard gets deleted. A real account ID is preceded by `:`, `/`,
#: whitespace, or nothing; never by a decimal point.
ACCOUNT_ID = re.compile(r"(?<![\d.])\d{12}(?!\d)")

#: `arn:<partition>:<service>:<region>:<account>:...` with a non-empty account
#: field. The empty-account form is deliberately not matched — see the module
#: docstring.
QUALIFIED_ARN = re.compile(r"arn:aws[a-z0-9-]*:[a-z0-9-]*:[a-z0-9-]*:(?P<account>[^:\s]+):")

#: Directories that are never committed but may exist in a working tree, for the
#: fallback walk below.
UNTRACKED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__",
                  ".pytest_cache", ".ruff_cache", "cdk.out", "dist", "build"}


def _tracked_via_git():
    proc = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        return None
    names = proc.stdout.decode("utf-8", "replace").split("\0")
    return [ROOT / name for name in names if name]


def _tracked_via_walk():
    """Fallback for a tree exported without git (a tarball, a build sandbox). The
    check must not silently skip itself just because `git` is missing — a guard
    that no-ops outside CI is worth nothing on the machine where the paste
    happens."""
    found = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if UNTRACKED_DIRS.intersection(path.relative_to(ROOT).parts):
            continue
        found.append(path)
    return found


def committed_files():
    paths = _tracked_via_git()
    if paths is None:
        paths = _tracked_via_walk()
    return [p for p in sorted(paths) if p.is_file() and p.resolve() != SELF]


def read_text(path):
    """Returns None for anything that is not decodable text — an image or an
    archive cannot hold a greppable account ID, and refusing to decode it is
    cheaper than guessing at an encoding."""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


FILES = committed_files()
IDS = [str(p.relative_to(ROOT)).replace("\\", "/") for p in FILES]


def test_the_scan_covers_the_repository():
    """A scan over zero files passes while proving nothing. If `git ls-files`
    starts failing in CI and the fallback walk also comes back empty, that must
    surface here rather than as a permanently green check."""
    assert len(FILES) >= 20, (
        f"only {len(FILES)} committed file(s) found — the leakage scan below is vacuous. "
        "Check that `git ls-files` works in this environment."
    )


@pytest.mark.parametrize("path", FILES, ids=IDS)
def test_no_committed_file_contains_an_aws_account_id(path):
    """The repo is public. An account ID in a journal, a fixture, or a captured
    command output is published permanently — git history keeps it after any
    later fix, so there is no cleanup, only prevention."""
    text = read_text(path)
    if text is None:
        pytest.skip("not decodable as text")
    hits = sorted(set(ACCOUNT_ID.findall(text)))
    assert not hits, (
        f"{path.relative_to(ROOT)} contains {len(hits)} account-ID-shaped string(s). "
        "Redact to <ACCOUNT_ID> before committing. If this is a false positive on a "
        "12-digit number that is not an account ID, that is a Data Governance call — "
        "narrow the pattern in its own PR with the reasoning, do not add an inline skip."
    )


@pytest.mark.parametrize("path", FILES, ids=IDS)
def test_no_committed_file_contains_an_account_qualified_arn(path):
    """Belt to the account-ID rule's braces: catches an ARN whose account field is
    populated with something that is not twelve plain digits. Account-less ARNs
    are permitted — see the module docstring for why that narrowing is
    deliberate."""
    text = read_text(path)
    if text is None:
        pytest.skip("not decodable as text")
    hits = sorted({m.group(0) for m in QUALIFIED_ARN.finditer(text)})
    assert not hits, (
        f"{path.relative_to(ROOT)} contains account-qualified ARN(s): {hits}. "
        "Use the account-less form (`arn:aws:service:region::resource`) where the resource "
        "is service-owned, or a CDK token where it is ours."
    )
