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

**Second narrowing (M03): twelve digits inside a hash are part of the hash.**

A sha256 is 64 hex characters, and roughly **17% of them contain a run of
twelve or more decimal digits** — `(10/16)^12` over 53 starting positions. This
repo commits digests on purpose: `evals/history/schema.json` has required
`samples_from[].sha256` since M02, and six were committed at that tag. Their
longest digit runs were 8, 8, 7, 7, 4 and 8, so **M02 had about a two-in-three
chance of hitting this and did not**. M03 commits thirty digests binding each
calibration label to the answer bytes it was written against, which made it a
certainty rather than a gamble.

That is a false positive of exactly the kind the decimal-fraction lookbehind
above was already written to prevent, arriving from a source nobody had listed. Left
alone, it reds `main` for a reason nobody can act on — the digest is not
editable, it is what the bytes hash to — and the guard's own message tells the
next person to narrow it under deadline. So it is narrowed here, deliberately,
in its own PR.

**The rule: a twelve-digit run wholly inside an unbroken hex token of 32 or more
characters is a hash, not an account ID.** Thirty-two is md5; sha1 is 40 and
sha256 is 64. An account ID is never embedded inside a longer hex token — it is
preceded by `:`, `/`, `-`, whitespace, or nothing, and a twelve-digit account ID
is itself a hex run of length twelve, far below the floor.

**What this does not defend against, stated rather than implied:** an account ID
deliberately padded with hex letters to 32 characters would now pass. This guard
prevents an accidental paste — from a console, a journal, a captured command —
and it has never claimed to stop someone who is trying. Widening it to that
threat model is a different guard and a different decision.

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

#: An unbroken hex token. A twelve-digit run wholly inside one of these, at or
#: above `HASH_MIN_HEX`, is part of a digest — see the module docstring for the
#: arithmetic that makes this inevitable rather than unlucky.
HEX_TOKEN = re.compile(r"[0-9a-fA-F]+")

#: md5 is 32, sha1 40, sha256 64. Below this a hex token is short enough that a
#: twelve-digit run inside it is most of the token, which is what an account ID
#: written in a hex-ish context actually looks like.
HASH_MIN_HEX = 32


def account_id_hits(text: str) -> list[str]:
    """Account-ID-shaped strings in `text`, excluding those inside a digest.

    Kept as a function rather than a cleverer regex because the containment test
    is the part a reader has to be able to check. A lookaround expressing "not
    inside a 32-character hex run" is writable and nobody would ever verify it."""
    digests = [
        (m.start(), m.end())
        for m in HEX_TOKEN.finditer(text)
        if m.end() - m.start() >= HASH_MIN_HEX
    ]
    hits = [
        m.group(0)
        for m in ACCOUNT_ID.finditer(text)
        if not any(start <= m.start() and m.end() <= end for start, end in digests)
    ]
    return sorted(set(hits))

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
    hits = account_id_hits(text)
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


# --- the narrowing, and its negative controls --------------------------------
#
# This module is excluded from its own scan (see `committed_files`), which is why
# these fixtures can spell out an account-ID-shaped string at all. Every one below
# is fictional.
#
# The controls come first and matter more than the narrowing they justify: a
# guard is only narrowed safely if the shapes it was built to catch are shown to
# still be caught, in the same commit, by tests that would fail if they were not.

#: Fictional, and never a real account. Twelve digits in the shapes an accidental
#: paste actually takes.
FAKE_ACCOUNT = "427449499283"

#: The digest that made this narrowing necessary: the sha256 of the answer M03's
#: calibration item `cal-05` binds its label to. It contains `FAKE_ACCOUNT` at
#: offset 14, purely by arithmetic. Used as the fixture rather than a hand-built
#: lookalike, because the collision that forced this change is the thing worth
#: pinning — M02 planted only shapes it already detected, and that is the lesson.
#:
#: It is not committed anywhere on this branch. It cannot be: the file carrying it
#: is blocked by the guard until this lands, which is the whole reason this PR is
#: separate and first.
DIGEST_WITH_A_TWELVE_DIGIT_RUN = (
    "4ad8ae31d1a8aa427449499283d4fd0d1c681dd46d31538b2c4e62b713d4d338"
)


@pytest.mark.parametrize("sample", [
    FAKE_ACCOUNT,
    f"arn:aws:s3:::bucket-{FAKE_ACCOUNT}-audit",
    f"arn:aws:iam::{FAKE_ACCOUNT}:role/GatewayRole",
    f"deployed to {FAKE_ACCOUNT} in us-west-2",
    f"{FAKE_ACCOUNT}.dkr.ecr.us-west-2.amazonaws.com",
    f"beaconpavegateway-auditlake-{FAKE_ACCOUNT}",
    f'{{"Account": "{FAKE_ACCOUNT}"}}',
])
def test_the_shapes_an_accidental_paste_takes_are_still_caught(sample):
    """The negative controls for the narrowing.

    M02's lesson, applied here: planting only shapes that are already detected
    proves nothing. These are the contexts an account ID actually arrives in —
    an ARN, a bucket name, an ECR host, a journal sentence, a captured JSON key —
    and none of them is inside a hex token long enough to be a digest."""
    assert account_id_hits(sample) == [FAKE_ACCOUNT]


def test_a_twelve_digit_run_inside_a_sha256_is_not_an_account_id():
    """The narrowing itself. The digest is not editable — it is what the bytes
    hash to — so a guard that fires here can only be satisfied by deleting the
    digest, which is the thing the digest exists to prevent."""
    assert FAKE_ACCOUNT in DIGEST_WITH_A_TWELVE_DIGIT_RUN
    assert account_id_hits(DIGEST_WITH_A_TWELVE_DIGIT_RUN) == []
    assert account_id_hits(f'{{"sha256": "{DIGEST_WITH_A_TWELVE_DIGIT_RUN}"}}') == []


def test_an_account_id_beside_a_digest_is_still_caught():
    """The failure mode that would make the narrowing worthless: a real ID in the
    same file, or the same line, as a digest."""
    line = f'{{"sha256": "{DIGEST_WITH_A_TWELVE_DIGIT_RUN}", "account": "{FAKE_ACCOUNT}"}}'
    assert account_id_hits(line) == [FAKE_ACCOUNT]


def test_a_short_hex_token_does_not_launder_an_account_id():
    """Only tokens at or above `HASH_MIN_HEX` are treated as digests. A short
    hex-ish context — a colour, a git short SHA, an id fragment — must not."""
    assert account_id_hits(f"ab{FAKE_ACCOUNT}cd") == [FAKE_ACCOUNT]
    assert account_id_hits(f"deadbeef{FAKE_ACCOUNT}") == [FAKE_ACCOUNT]


def test_the_decimal_narrowing_still_holds():
    """The first narrowing, unchanged. A duration is not an account ID."""
    assert account_id_hits("elapsed 0.123456789012 s") == []


def test_the_repo_actually_commits_digests():
    """The narrowing is justified by a real, recurring source of false positives
    rather than by one awkward file. If this ever finds no digests, the reasoning
    in the module docstring has gone stale and the narrowing should be re-argued."""
    schema = (ROOT / "evals" / "history" / "schema.json").read_text(encoding="utf-8")
    assert "sha256" in schema, (
        "the history schema no longer records digests; re-read the docstring's "
        "argument for this narrowing before keeping it"
    )
