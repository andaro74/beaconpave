"""`pave policy generate` — how it fails, and that it is byte-idempotent.

Two findings from the Tool Owner seat, both about the generator rather than the
policy it generates.

**How it fails.** `policy_generate` wraps `cedar.generate` in `except ValueError`
and says why in its own comment: an escaping exception aborts before pytest runs
and before `--out` writes a verdict, and CI then blocks on an ABSENT verdict —
paging the wrong seat for a contract regression. One screen later it read a
registry-named path with no guard at all. Registering a tool whose schema files do
not exist produced an unhandled `FileNotFoundError` at exit 1, which `gate.py`
renders as *"quality regression / owner: service team"* for a registry error that
is Platform's. pytest does catch the registration — 20 tests go red — but
`pave check` runs this drift gate first and never gets there. **A wrong red that
pages the wrong seat, not a green.**

**Byte-idempotence.** `write_text` without `newline=""` translates every line feed
to the platform's ending, so on Windows the generator emitted CRLF and left two
files reported as modified with an empty `git diff`. `--check` could not see it,
because `read_text` universal-newlines the comparison. The blast radius is
contained — `tool_specs_sha256` digests parsed JSON — but these are build products
that ship inside the Lambda bundle, and a generator that is not byte-idempotent
makes every reader ask whether a drift signal is real.

Hermetic (G8): runs the CLI in a subprocess against a temporary registry, no
network. **It never writes to the real registry** — the plant goes to a copied
tree, so a failing test cannot leave the repo's own registry modified. That is the
rule `audit-harness-must-not-restore-from-git` exists for, applied in advance.

Owning seat: Platform Engineering (the gate's process) · Tool Owner (what a
registry error means).
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "platform" / "registry" / "tools.yaml"
POLICY_SET = ROOT / "platform" / "gateway" / "policy" / "tools.cedar"
CONTRACT_SET = ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json"

#: `pave/gate.py`'s codes, read from the module so a renumbering cannot leave this
#: file asserting a number that used to mean something else.
sys.path.insert(0, str(ROOT))
from pave import gate as gate_mod  # noqa: E402

UNREGISTERED_TOOL = """
- id: catalog-purge
  version: 0.1.0
  consequence: publish
  summary: A tool registered with no contract on disk.
  schemas:
    input: tools/catalog-purge/schema.in.json
    output: tools/catalog-purge/schema.out.json
"""


def _sandbox(tmp_path: pathlib.Path) -> pathlib.Path:
    """A copy of everything the generator reads, so the plant never touches the repo."""
    root = tmp_path / "repo"
    for relative in ("platform/registry", "platform/gateway", "tools", "pave"):
        source = ROOT / relative
        if source.is_dir():
            shutil.copytree(source, root / relative,
                            ignore=shutil.ignore_patterns("__pycache__"))
    return root


def _run(root: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "pave.cli", "policy", "generate", *args],
                          cwd=root, capture_output=True, text=True)


def test_a_registered_tool_with_no_contract_is_a_contract_error_not_a_traceback(tmp_path):
    root = _sandbox(tmp_path)
    registry = root / "platform" / "registry" / "tools.yaml"
    before = registry.read_bytes()
    registry.write_text(registry.read_text(encoding="utf-8").rstrip("\n") + UNREGISTERED_TOOL,
                        encoding="utf-8", newline="")
    assert registry.read_bytes() != before, "the plant did not reach disk"

    result = _run(root, "--check")
    combined = result.stdout + result.stderr

    assert "Traceback" not in combined, (
        "an unregistered contract still escapes as an unhandled exception. The gate then "
        "exits on Python's default code and writes no verdict, so CI reports the wrong "
        "class of failure and pages the wrong seat.")
    assert result.returncode == gate_mod.EXIT_CONTRACT, (
        f"exit {result.returncode}, expected EXIT_CONTRACT={gate_mod.EXIT_CONTRACT}. "
        f"EXIT_QUALITY={gate_mod.EXIT_QUALITY} renders as a quality regression owned by "
        "the service team, which is not what a registry naming a missing schema is.")
    assert "catalog-purge" in combined and "schema.in.json" in combined, (
        "the error names neither the tool nor the path. A contract error a reader cannot "
        "locate is a traceback with better manners.")


def test_a_schema_that_is_not_json_is_the_same_class_of_error(tmp_path):
    """The other way a registry-named path fails, and it took the same guard.

    Both are "the registry names something that cannot be rendered", and both must
    reach the same exit code — otherwise the class of failure depends on how the
    file happens to be broken."""
    root = _sandbox(tmp_path)
    target = next(iter(json.loads(
        (root / "platform" / "gateway" / "policy" / "tools.contracts.json")
        .read_text(encoding="utf-8"))))
    schema = root / "tools" / target / "schema.in.json"
    if not schema.is_file():
        pytest.skip(f"no committed input schema for {target}")
    before = schema.read_bytes()
    schema.write_text("{not json", encoding="utf-8", newline="")
    assert schema.read_bytes() != before, "the plant did not reach disk"

    result = _run(root, "--check")
    assert "Traceback" not in (result.stdout + result.stderr)
    assert result.returncode == gate_mod.EXIT_CONTRACT


def test_generating_twice_changes_no_bytes(tmp_path):
    """The CRLF finding, asserted as the property rather than as a line ending.

    Checking for `\\r\\n` would pass on a platform that never emits it, which is
    every CI runner this repo uses and none of the machines the defect was found
    on. What matters is that running the generator on a clean tree leaves the
    build products byte-identical."""
    root = _sandbox(tmp_path)
    policy = root / POLICY_SET.relative_to(ROOT)
    contracts = root / CONTRACT_SET.relative_to(ROOT)
    before = (policy.read_bytes(), contracts.read_bytes())

    result = _run(root)
    assert result.returncode == 0, result.stderr

    assert (policy.read_bytes(), contracts.read_bytes()) == before, (
        "`policy generate` on a clean tree changed the bytes of its own output. A "
        "generator that is not byte-idempotent reports two files as modified with an "
        "empty `git diff`, and `--check` cannot see it because `read_text` "
        "universal-newlines the comparison.")


def test_the_committed_build_products_use_one_line_ending(tmp_path):
    """A direct check of the committed artifacts, which is what ships.

    The idempotence test above proves the generator does not introduce the drift;
    this proves the files in the repository do not already carry it."""
    for path in (POLICY_SET, CONTRACT_SET):
        raw = path.read_bytes()
        assert b"\r\n" not in raw, (
            f"{path.relative_to(ROOT)} carries CRLF. It ships inside the Lambda bundle and "
            "is compared as text by the drift gate; a mixed-ending build product makes "
            "every drift signal ambiguous.")
