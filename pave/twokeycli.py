"""`pave gate two-key` — the G9 interlock, in a file small enough to read.

**Why this is not in `pave/cli.py`.** ADR-041 decision 7 refused a two-key rule on
that file, and SPEC/06 refuses it again: it is the most-edited file in the
repository — every command, every remediation string — and gating it "teaches
people to attest past a rule without reading it". The decision prescribed the
remedy it had just used for the floors: move the protected thing into a small
module and key that one.

**Why it moved now.** ADR-052 measured a 20-line shim in `pave/cli.py`, guarded by
`if "pytest" not in sys.modules`, rebinding `twokey.adr_records` and
`twokey.evaluate`. The live gate printed `two-key: SATISFIED` and exited **0** while
naming a decision record for a file the PR never touched — at **2222 passed, the
exact baseline, on zero keys**. A shim has to be *in the process* to do that, so the
remedy is not to make `cli.py` harder to edit but to stop running it: this module is
what `.github/workflows/two-key.yml` invokes, and it does not import `pave.cli`.
`pave gate two-key` still works for humans, because `cli.py` imports from here.

Everything here is two-key (`ai-quality`, `platform-eng`, `security`) — the file is
short enough that signing it means having read it, which is the property ADR-041
said a rule on `cli.py` could not buy.

Owning seat: Platform Engineering (the mechanism) · Security (it decides whether an
enforcement path runs) · AI Quality (the rules list).
"""
from __future__ import annotations

import os
import pathlib
import sys

from pave import gate as gate_mod
from pave import twokey

#: The repository root. One definition, imported by `pave/cli.py` rather than
#: recomputed there -- two roots that agree from source and diverge under an
#: install is a defect this milestone already found once.
ROOT = pathlib.Path(__file__).resolve().parents[1]


def _console_safe(text: str, encoding: str) -> str:
    """Rewrite `text` so `encoding` can represent it, losing characters rather
    than raising.

    `pave gate two-key` prints U+2717 on its blocking path. A Windows console
    running cp1252 cannot encode that character, so the command died with a
    UnicodeEncodeError *instead of printing why it blocked* — the operator saw a
    traceback and exit 1, with the reason it exited nowhere on screen. CI never
    caught it because GitHub runners are UTF-8.

    That is the same class as M00a's BOM bug: a governance check that fails for a
    reason which is not the team's fault. Those are the failures that teach people
    to route around the gate, so the console's codepage must not get a vote in
    whether a blocked merge can explain itself.

    Characters the console *can* show are returned untouched, so nothing is
    degraded on a UTF-8 terminal or in a CI log."""
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        return text.encode(encoding, "replace").decode(encoding, "replace")
    return text

def _emit(text: str) -> None:
    """Print rendered gate output through `_console_safe`. Stdout's encoding is
    read at call time rather than cached: it differs between a console, a pipe,
    and a redirect to file, and the blocking path must survive all three."""
    print(_console_safe(text, getattr(sys.stdout, "encoding", None) or "utf-8"))

def _flag_values(argv, flag):
    """Collect the values following `--flag` up to the next `--option`.
    Returns [] when the flag is absent — `gate decide` treats that as blocking,
    so a typo'd flag can never be read as "nothing to check, therefore fine"."""
    if flag not in argv:
        return []
    rest = argv[argv.index(flag) + 1:]
    values = []
    for token in rest:
        if token.startswith("--"):
            break
        values.append(token)
    return values

def gate_two_key(argv):
    """G9: the second key, machine-checked. Exits 1 when a two-key path changed
    without the owning seat's recorded disposition and reasoning.

    Changed files come from `--changed`; the PR body from the PR_BODY environment
    variable (passed as env rather than interpolated into the workflow's shell,
    so a PR body cannot inject shell)."""
    # **Absence of `--changed` is blocking, not "nothing to check".** `_flag_values`
    # says in its own docstring that a typo'd flag "can never be read as 'nothing to
    # check, therefore fine'" — and that was true of `gate decide` and false here:
    # this command read [] as no changed files, found no rule triggered, and printed
    # `two-key: not required` in green. Measured at ADR-037 by running it with
    # `--base origin/main` on a diff that edits `pave/twokey.py` itself. A stated
    # protection that holds for one caller and not the other is the fault this ADR
    # is about, arriving in the parser that describes it.
    #
    # An EMPTY list stays legal: `--changed` with nothing after it is a PR that
    # changed nothing, which is vacuously compliant. What is refused is never being
    # told at all.
    if "--changed" not in argv:
        _emit(
            "two-key: BLOCKED — no `--changed` given, so nothing was checked. "
            "This command cannot report compliance for a file list it was never "
            "handed; pass `--changed <paths...>` (the workflow does)."
        )
        sys.exit(gate_mod.EXIT_QUALITY)
    changed = _flag_values(argv, "--changed")
    body = os.environ.get("PR_BODY", "")
    body_file = _flag_values(argv, "--body-file")
    if body_file:
        body = pathlib.Path(body_file[0]).read_text(encoding="utf-8-sig")

    # `--base` and `--head`. `evaluate` needs them to tell a decision record
    # from a trailing newline, and it fails CLOSED without a base: a run given
    # none refuses every rule that requires an ADR rather than waving it
    # through. An EMPTY value is refused here, the way `gate history` already
    # refuses one -- "a base that did not arrive is not a base to guess at".
    base = _flag_values(argv, "--base")
    head = _flag_values(argv, "--head")
    # BOTH endpoints refuse an empty value, and `--head` did not. An empty
    # `--head` was coerced to None, which `evaluate` reads as "one endpoint" --
    # and one endpoint makes `git diff <base>` compare against the WORKING TREE,
    # which is the exact defect `--head` was added to close. Measured: a rule
    # discharged by a decision record the PR did not write. The refusal for this
    # argument existed on one flag and not its twin.
    for flag, values in (("--base", base), ("--head", head)):
        if flag in argv and not (values and values[0].strip()):
            _emit(f"two-key: BLOCKED — `{flag}` was given with no value. An endpoint "
                  "that did not arrive is not an endpoint to guess at.")
            sys.exit(gate_mod.EXIT_QUALITY)
    base_sha = base[0] if base else None
    head_sha = head[0] if head and head[0].strip() else None
    problems = twokey.evaluate(changed, body, repo_root=ROOT,
                               base=base_sha, head=head_sha)
    records, _ = twokey.adr_records(ROOT, base_sha, head_sha, changed)
    _emit(twokey.render(changed, problems, records))
    if problems:
        sys.exit(gate_mod.EXIT_QUALITY)


def main(argv: list[str] | None = None) -> None:
    """`python -m pave.twokeycli --base <sha> --head <sha> --changed <paths...>`.

    A module entrypoint rather than a subcommand of `pave`, so the workflow can
    invoke the gate without importing the CLI surface it is protected from."""
    gate_two_key(list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":  # pragma: no cover - exercised by the workflow
    main()
