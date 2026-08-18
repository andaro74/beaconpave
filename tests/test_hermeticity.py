"""
L1 contract tests: the hermetic suite must stay hermetic (G8).

`make check` is supposed to pass on a fresh clone with no AWS account and no
network. Today it does, trivially — there is no code in this repo that could
reach AWS. M00b changes that: it adds the first model call, and from then on a
developer machine has boto3 installed and a working `agentpave` profile sitting
in `~/.aws`. That is the exact condition under which `pave check` can start
quietly depending on credentials while still reporting green, because on the
machine that runs it the credentials are always there. The stranger who clones
the repo finds out instead.

So the guard has to land before the capability does. Three checks, deliberately
overlapping:

- a **static** scan, which fails on the code being *written* even if it never
  runs on this machine and even if boto3 is not installed here;
- a **runtime** `sys.modules` check, which catches the transitive case the
  static scan cannot see — a hermetic test importing something that imports
  something that imports boto3;
- a **coverage** check, because a scanner that finds zero files to scan reports
  success. Same argument as the empty rules registry in `pave.cli`.

This module is excluded from its own scans. It has to name `boto3` and the
`AWS_` prefix as data in order to look for them, and a scanner that flags its
own vocabulary is a scanner nobody can keep green.

Hermetic (G8): reads source files, imports nothing under test.
Owning seat: Platform Engineering.
"""
import ast
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SELF = pathlib.Path(__file__).resolve()

#: The hermetic surface: every module `pave check` imports or collects. Two
#: directories are deliberately NOT here, for the same reason and with the same
#: consequence — `services/highlights-agent-baseline/` (M00b's control) and
#: `platform/gateway/handler.py` (M01's boto3 adapter) both reach Bedrock. What
#: must stay true is that nothing in the hermetic suite *reaches* them; the
#: sys.modules check below is what enforces that.
#:
#: M01 adds `platform/gateway/core/` rather than excluding it. The gateway's
#: decisions are what G1, G4, and G5 rest on, so they are exactly the code that
#: has to be provable offline on a fresh clone — the split between `core/` and
#: `handler.py` exists so that growing this list was possible at all.
HERMETIC_ROOTS = (
    ROOT / "pave",
    ROOT / "tests",
    ROOT / "evals",
    ROOT / "platform" / "gateway" / "core",
)

#: Importing any of these means the module can talk to AWS.
AWS_SDK_ROOTS = frozenset({"boto3", "botocore", "aiobotocore", "aioboto3", "s3transfer", "awscli"})

#: Reading any of these means the module's behaviour depends on ambient AWS
#: configuration — which is the subtler half of the failure. A test that reads
#: `AWS_PROFILE` and skips when it is unset passes everywhere and tests nothing
#: on the machine where it matters.
AWS_ENV_PREFIX = "AWS_"
AWS_CONFIG_PATHS = ("~/.aws", ".aws/credentials", ".aws/config")


def hermetic_sources():
    """Every Python file in the hermetic surface, except this one."""
    for root in HERMETIC_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if path.resolve() != SELF:
                yield path


def _imported_roots(tree):
    """Top-level package name of every import in a parsed module."""
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _string_constants(tree):
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


SOURCES = list(hermetic_sources())
IDS = [str(p.relative_to(ROOT)).replace("\\", "/") for p in SOURCES]


def test_the_hermetic_surface_is_not_empty():
    """A scan over zero files is a pass that means nothing. If `pave/` or `tests/`
    is renamed, this fails loudly rather than letting the two scans below go
    quietly vacuous — the same reason `rules validate` rejects an empty registry."""
    assert len(SOURCES) >= 4, f"hermetic surface is {len(SOURCES)} file(s); the scan below proves nothing"


@pytest.mark.parametrize("path", SOURCES, ids=IDS)
def test_no_hermetic_module_imports_an_aws_sdk(path):
    """G8, statically. Fails on the import being written, whether or not boto3 is
    installed on this machine and whether or not the line is ever executed."""
    found = _imported_roots(ast.parse(path.read_text(encoding="utf-8"))) & AWS_SDK_ROOTS
    assert not found, (
        f"{path.relative_to(ROOT)} imports {sorted(found)} — the hermetic suite (G8) must run "
        "on a fresh clone with no AWS account. Move the code that needs an SDK behind a "
        "non-hermetic entry point, or add a fixture."
    )


@pytest.mark.parametrize("path", SOURCES, ids=IDS)
def test_no_hermetic_module_reads_aws_configuration(path):
    """The half that does not need an SDK: reading `AWS_PROFILE`, `AWS_REGION`, or
    `~/.aws` makes a test's result depend on the developer's machine. That is how
    a suite ends up green for its author and red for everyone else."""
    literals = _string_constants(ast.parse(path.read_text(encoding="utf-8")))
    env = sorted({s for s in literals if s.startswith(AWS_ENV_PREFIX) and s.isupper()})
    paths = sorted({s for s in literals if any(marker in s for marker in AWS_CONFIG_PATHS)})
    assert not env and not paths, (
        f"{path.relative_to(ROOT)} reads ambient AWS configuration {env + paths} — a hermetic "
        "test must not vary with the machine it runs on (G8). Use a committed fixture."
    )


def test_the_hermetic_test_session_never_imported_an_aws_sdk():
    """The transitive case, which the static scan cannot see. If any collected test
    imports M00b's baseline agent — directly, or through a helper, or through a
    module that grew an SDK import since it was last read — boto3 lands in
    `sys.modules` and this fails.

    Depends on collection order only in the sense that a *later* import would be
    missed; the parametrised scans above cover what is written, and this covers
    what was actually loaded. Between them there is no quiet path."""
    loaded = sorted(AWS_SDK_ROOTS & {name.split(".")[0] for name in sys.modules})
    assert not loaded, (
        f"the hermetic test session imported {loaded} — something under `tests/` or `pave/` "
        "reaches an AWS SDK transitively (G8). Find the import chain before this suite starts "
        "silently requiring credentials."
    )
