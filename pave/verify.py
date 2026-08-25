"""The `pave verify` invocation, and nothing else.

**Why its own file, when `pave/gate.py` would work.** It does work — Platform
Engineering measured the `gate.py` home at 50 passed with
`test_ordinary_pr_is_not_gated` intact, and refused it anyway. `gate.py`'s own
docstring draws the seat boundary the move would erase (*"Platform Engineering
(mechanism only — the criteria that produce a FAIL are AI Quality's)"*), and
putting a two-key rule on `gate.py` leaves `pave/tests/test_gate.py` — 21.7 KB
holding the entire pin on the exit-code contract — at zero keys while the file it
pins takes three. That is ADR-043 decision 1's *weakened together or not at all*,
arriving again.

**And not `pave/cli.py`**, for the reason `pave/floors.py`'s docstring records:
that file is ~1200 lines and a sixth of this repository's commits, and
`pave/tests/test_twokey.py::test_ordinary_pr_is_not_gated` names it as the
canonical ungated example. A file holding one invocation can be gated without
teaching anyone to attest past a rule they did not read.

**The exit codes are the gate's, and the split is deliberate.** A manifest with
findings is `EXIT_QUALITY` — the service team's to fix. A verifier that cannot
enumerate anything is `EXIT_CONTRACT` — the platform's, and it pages differently.
An empty glob returning PASS is the failure this whole component exists to remove,
so it is the loudest exit here.

Hermetic (G8): reads committed files, calls no model, opens no socket.
Owning seats: Platform Engineering (mechanism) · AI Quality + Security (criteria).
"""
from __future__ import annotations

from collections.abc import Callable

from pave import gate as gate_mod
from pave import manifest as manifest_mod

USAGE = ("usage: python -m pave.cli verify (--all | <service> [<service> ...])\n"
         "  --all       every service under services/ carrying a pave.manifest.yaml\n"
         "  <service>   a directory name under services/")


def verify(argv: tuple[str, ...] = (), emit: Callable[[str], None] = print) -> int:
    """Verify one service, or every one of them. Returns a process exit code.

    Returns rather than raises, because `pave check` calls the same underlying
    module through pytest and the CLI is the only place an exit code is wanted.
    """
    argv = tuple(argv)
    everything = "--all" in argv
    named = [a for a in argv if not a.startswith("-")]
    unknown = [a for a in argv if a.startswith("-") and a != "--all"]
    if unknown:
        emit(f"[pave verify] unknown option(s) {unknown}.\n{USAGE}")
        return gate_mod.EXIT_CONTRACT
    if not everything and not named:
        # Fail-closed rather than defaulting to `--all`. A verifier that verifies
        # everything when asked nothing is a verifier whose scope is decided by a
        # typo, and this repository already carries one component (`gate decide`)
        # whose closed `--verdicts` list means an omitted argument is not "absent
        # and blocking" but "not consulted".
        emit(f"[pave verify] name a service or pass --all.\n{USAGE}")
        return gate_mod.EXIT_CONTRACT

    found = manifest_mod.services()
    if everything and not found:
        emit("[pave verify] FAIL: no service under "
             f"`{manifest_mod.SERVICES.name}/` carries a "
             f"`{manifest_mod.MANIFEST_NAME}`. `--all` over an empty set is the one "
             "result this command must never report as PASS: before ADR-046 nothing "
             "in this repository enumerated services at all, and both CI evaluation "
             "steps named one service literally.")
        return gate_mod.EXIT_CONTRACT

    if everything:
        targets = found
    else:
        targets = []
        for name in named:
            directory = manifest_mod.SERVICES / name
            if not (directory / manifest_mod.MANIFEST_NAME).is_file():
                emit(f"[pave verify] FAIL: `services/{name}/"
                     f"{manifest_mod.MANIFEST_NAME}` does not exist. Services carrying "
                     f"a manifest: {[d.name for d in found]}.")
                return gate_mod.EXIT_CONTRACT
            targets.append(directory)

    registry = manifest_mod.load(manifest_mod.REGISTRY)
    total = 0
    for directory in targets:
        findings = manifest_mod.verify(directory, registry=registry)
        total += len(findings)
        if findings:
            emit(f"[pave verify] FAIL {directory.name} — {len(findings)} finding(s):")
            for finding in findings:
                emit(finding.render())
        else:
            emit(f"[pave verify] PASS {directory.name}")

    emit(_footer())
    if total:
        emit(f"[pave verify] {total} finding(s) across {len(targets)} service(s). "
             "Each names the field, what reads it, and the edit — see the row "
             "numbers against `pave/manifest.py`'s `ROWS`.")
        return gate_mod.EXIT_QUALITY
    return gate_mod.EXIT_OK


def _footer() -> str:
    """What the verifier did NOT check, printed on every run including green ones.

    On a green run especially. A tool that lists its limits only when it fails is a
    tool whose limits are read by nobody who passed, and every one of these is a
    thing a reader would otherwise assume from the PASS."""
    lines = ["[pave verify] not checked, by name:"]
    for what, why in manifest_mod.DEFERRED.items():
        lines.append(f"  - {what}: {why}")
    return "\n".join(lines)
