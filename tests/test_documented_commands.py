"""Every command a spec's *Demo artifact* prints is run, and its exit code is the
one the spec publishes beside it.

**Why this file exists.** SPEC/09's demo artifact shipped

    python -m pave.cli gate decide milestones/M09/verdict-pre-fix.json

for three PRs, published as the command that proves claim 6. The gate takes its
verdicts on `--verdicts`; a bare positional is parsed and then ignored, so the
command reports *"no verdict files supplied — the gate does not pass on an empty
argument list"* and exits **2**, the harness-failure code. The spec said exit 1
then exit 0. Nobody ran it: the run PR ran the correct form, committed its
transcript, and the spec's copy was never executed by anything.

That is this repository's most-repeated defect one level out — **a stated
protection that is absent** — in the one block a stranger is handed. A demo
artifact nobody runs is prose about a demo.

**Scope, asserted rather than described.** The set is *every fenced `bash` block
in a `## Demo artifact` section of `SPEC/*.md`*, and
`test_the_scope_is_every_spec_that_publishes_a_demo_block` requires the check to
have found one for every spec that has such a section — so a new milestone's demo
block joins the check by existing, not by anyone remembering to add it.

**And why not every command printed anywhere.** Measured before choosing: the
other command blocks in `SPEC/` and `README.md` are not of this kind, and running
them would make this check red on true documents or mutate the tree.

- `SPEC/06`'s blocks are `$`-prompted transcripts of **counterfactual trees** —
  *"Run as draft 8 wrote it — directory deleted, 22 pads"* — publishing `EXIT=1`
  for a state this tree is deliberately not in. Running them here asserts the
  opposite of what they say.
- `SPEC/05`'s block is a scaffolding how-to that runs `pave.cli policy generate`
  (which **writes** `platform/gateway/policy/`) and `git add`.
- `README.md`'s *Quick start* is the target developer experience: `pave new`,
  `pave drill` and `make core`, which deploy, and which are not on `PATH` in a
  clone at all.

Widening to those needs each block to declare the tree it is true of, which is a
document change and not a test change; it is recorded as a debt in
`milestones/M09/README.md` with an owner and a trigger rather than half-done
here. The demo blocks need no such declaration: they are true of `main`, they are
what `close-milestone` step 8 records, and they are read-only by construction.

**The unchecked region is now DECLARED rather than silent (M09b, debt 33).** The
paragraph above is an argument in prose, and prose was all that stood behind it:
the scope was *"every fenced `bash` block in a `## Demo artifact` section"* and a
block outside such a section was unchecked **and unnamed**, so a new one could
appear without anything going red. That was measured, and it had already happened:

> `SPEC/06c-instrument-repair.md` heads its section **`## The demo artifact`** —
> three words, not two. `DEMO_HEADING` matches the exact string, so that spec's
> `bash` block has never been run by this check, and
> `test_the_scope_is_every_spec_that_publishes_a_demo_block` did not notice
> because **both sides of its equality are derived from the same reader**. A spec
> the reader cannot see is absent from `publishing` and absent from `CASES`
> alike, and the sets agree on it by being empty on both sides.

That is `tests/test_topic_baseline.py`'s own recorded defect one file over — a
summary that reports a clean sheet having compared nothing — and it is this
repository's most-repeated shape, *a stated protection that is absent*.

So `UNRUN_BASH_BLOCKS` below names every `bash` block in `SPEC/*.md` and
`README.md` that this check does not run, with the reason it does not, and
`test_every_bash_block_is_run_or_declared_unrun` holds the declaration against the
measurement. It does not widen the run scope — SPEC/06c's block records an eval
history entry and README's Quick start deploys, and both are correctly out — it
removes the silence. **A new unrun block is red, and so is a stale declaration.**
Whether SPEC/06c's heading is itself repaired is a document change in a closed
milestone's spec and is a separate decision, carried as a finding, not taken here.

Hermetic (G8): every command in scope reads committed answer files and the
registry. No network, no model call, no write to the tree — asserted by
`test_no_demo_command_writes_to_the_tree`.

Owning seats: Platform Engineering (the CLI contract) · PM (the specs).
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "SPEC"
DEMO_HEADING = "## Demo artifact"

#: Every `bash` block in `SPEC/*.md` or `README.md` this check does NOT run, and
#: why. Keyed by repo-relative path to the NUMBER of such blocks in that file, so
#: adding a second unrun block to a file that already has one is red rather than
#: absorbed. Declared rather than derived: a reason is the thing a derived list
#: cannot carry, and the reason is what a later reader needs in order to decide
#: whether the exclusion still holds.
#:
#: **Nothing is exempted for being hard to run.** Each entry states a property of
#: the block that makes running it assert something false or mutate the tree.
UNRUN_BASH_BLOCKS: dict[str, str] = {
    "README.md":
        "the Quick start, which is the TARGET developer experience rather than a "
        "reading of this tree: `make bootstrap`/`make core` deploy, and `pave new` "
        "and `pave drill` are not on PATH in a clone at all. Running it would "
        "either fail on a true document or bill an AWS account from `make check`.",
    "SPEC/06c-instrument-repair.md":
        "`run_evals --record --tag m06c`, which APPENDS to `evals/history/`. Demo "
        "commands are read-only by construction (`test_no_demo_command_writes_to_"
        "the_tree`) and eval history is append-only and never rewritten (CLAUDE.md, "
        "G9), so a check that ran this on every `make check` would author the "
        "record it is measuring. **Out of scope on the block, not on the heading**: "
        "this spec spells its section `## The demo artifact` and was therefore "
        "invisible to this module until M09b measured it.",
}

#: A published expectation, written by the spec beside the command. `exit 1` on
#: its own line in the block that follows the commands, paired in order with the
#: commands that ask for one (`; echo "exit $?"`). A command that does not ask is
#: expected to succeed — a demo command that fails silently is the same defect.
_EXIT_LINE = re.compile(r"^exit\s+(\d+)\s*$")
_ECHO_EXIT = re.compile(r"\s*;\s*echo\s+\"exit \$\?\"\s*$")


def _fenced_blocks(section: str) -> list[tuple[str, str]]:
    """`(info string, body)` for every fenced block in `section`, in order."""
    blocks, info, body, inside = [], "", [], False
    for line in section.splitlines():
        if line.startswith("```"):
            if inside:
                blocks.append((info, "\n".join(body)))
                info, body, inside = "", [], False
            else:
                info, inside = line[3:].strip(), True
            continue
        if inside:
            body.append(line)
    return blocks


def _commands(block: str) -> list[str]:
    """The block's command lines, with `\\` continuations joined.

    The demo blocks wrap `run_evals` over four `--answers` arguments, so a
    line-per-command reader would run `python -m evals.run_evals --arm tools`
    with no answers and call the resulting refusal a documented exit."""
    joined, buf = [], ""
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.endswith("\\"):
            buf += line[:-1].strip() + " "
            continue
        joined.append((buf + line.strip()).strip())
        buf = ""
    if buf.strip():
        joined.append(buf.strip())
    return joined


def _demo_section(path: pathlib.Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if DEMO_HEADING not in text:
        return None
    return text.split(DEMO_HEADING, 1)[1].split("\n## ", 1)[0]


def _cases() -> list[tuple[str, str, int]]:
    """`(spec name, command, expected exit)` for every documented demo command.

    **The expectation comes from the block immediately after the commands**, and
    from nowhere else in the section. SPEC/09's section also carries a dated
    record of what `rules trace` printed *before* the disposition, ending `exit
    1` in prose — a reader scanning the whole section for exit codes would pair
    that historical reading with a live command and assert the pre-disposition
    answer forever."""
    out: list[tuple[str, str, int]] = []
    for spec in sorted(SPEC_DIR.glob("*.md")):
        section = _demo_section(spec)
        if section is None:
            continue
        blocks = _fenced_blocks(section)
        for i, (info, body) in enumerate(blocks):
            if info != "bash":
                continue
            commands = _commands(body)
            following = blocks[i + 1][1] if i + 1 < len(blocks) else ""
            published = [int(m.group(1)) for m in
                         (_EXIT_LINE.match(line) for line in following.splitlines()) if m]
            asked = [c for c in commands if _ECHO_EXIT.search(c)]
            assert len(published) == len(asked), (
                f"{spec.name}: {len(asked)} demo command(s) print their exit code "
                f"and the block after them publishes {len(published)}. A command "
                f"that asks `echo \"exit $?\"` and is answered by nothing is a "
                f"reader being shown a number with no claim attached to it.")
            expectations = iter(published)
            for command in commands:
                expected = next(expectations) if _ECHO_EXIT.search(command) else 0
                out.append((spec.name, _ECHO_EXIT.sub("", command), expected))
    return out


CASES = _cases()


def test_there_are_demo_commands_to_check():
    """The parser is not vacuous.

    Every assertion below is `for` a list this module derives from the specs. A
    reader-side change that silently stopped matching — a heading renamed, a
    fence info string changed from ```bash — would empty the list and leave the
    whole file green while checking nothing, which is the shape
    `test_the_progression_parser_is_not_vacuous` exists for one file over."""
    assert len(CASES) >= 10, (
        f"only {len(CASES)} demo command(s) parsed out of SPEC/. The specs "
        f"publish more than that; the reader has stopped matching.")


def test_the_scope_is_every_spec_that_publishes_a_demo_block():
    """**The scope is derived, not listed.**

    A spec with a `## Demo artifact` section carrying a `bash` block is in scope
    by having one. Listing the five specs here instead would be a second registry
    that drifts from the first the day M09b writes its own demo block — the
    two-registry smell `tests/milestone_status.py` was written against."""
    publishing = set()
    for spec in sorted(SPEC_DIR.glob("*.md")):
        section = _demo_section(spec)
        if section and any(info == "bash" for info, _ in _fenced_blocks(section)):
            publishing.add(spec.name)
    assert publishing == {name for name, _, _ in CASES}, (
        f"specs publishing a demo bash block: {sorted(publishing)}; specs this "
        f"check runs: {sorted({n for n, _, _ in CASES})}. A demo block outside "
        f"the check is a command nobody runs, which is the defect.")


@pytest.mark.parametrize(
    "spec,command,expected",
    CASES,
    ids=[f"{n}::{c[:60]}" for n, c, _ in CASES])
def test_a_documented_demo_command_runs_and_exits_as_documented(
        spec: str, command: str, expected: int) -> None:
    """Run it. Compare the exit code against what the spec prints.

    Not *does it parse* — SPEC/09's defect parsed. `gate decide FILE` was
    accepted by argparse and then ignored by the gate, which reported an empty
    argument list at exit 2. Only running it separates a command that works from
    a command whose shape is plausible."""
    argv = command.split()
    assert argv[0] == "python", (
        f"{spec}: demo command {command!r} does not start with `python`. This "
        f"check runs it with `sys.executable`; a command invoking anything else "
        f"is out of the scope this module documents and needs that scope "
        f"widened deliberately rather than by a silent pass.")
    proc = subprocess.run([sys.executable, *argv[1:]], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=300)
    assert proc.returncode == expected, (
        f"{spec}'s demo artifact publishes `{command}` at exit {expected}; it "
        f"exits {proc.returncode}.\n"
        f"--- stdout ---\n{proc.stdout[-2000:]}\n"
        f"--- stderr ---\n{proc.stderr[-2000:]}\n"
        f"A demo artifact is what a stranger is handed. One that does not run is "
        f"prose about a demo.")


def _unrun_bash_blocks() -> dict[str, int]:
    """`{repo-relative path: count}` for every `bash` block this module does not
    run — one outside a `## Demo artifact` section, by the same two readers the
    run scope is derived from.

    Derived from `_fenced_blocks` and `_demo_section` and from nothing else, so a
    reader-side change moves this and the run scope together. That is the whole
    point: the two must not be able to disagree silently, which is how SPEC/06c
    went eleven milestones without being run."""
    found: dict[str, int] = {}
    for path in [*sorted(SPEC_DIR.glob("*.md")), ROOT / "README.md"]:
        text = path.read_text(encoding="utf-8")
        everywhere = [body for info, body in _fenced_blocks(text) if info == "bash"]
        section = _demo_section(path)
        in_scope = [body for info, body in _fenced_blocks(section) if info == "bash"] \
            if section is not None else []
        outside = len(everywhere) - len(in_scope)
        if outside:
            found[path.relative_to(ROOT).as_posix()] = outside
    return found


def test_every_bash_block_is_run_or_declared_unrun():
    """**The unchecked region is named, with a reason, or the suite is red.**

    M09's debt 33: *only `Demo artifact` blocks are checked; blocks outside such a
    section are unchecked*. The defect it describes is not that those blocks are
    unrun — three of them should be — it is that being unrun was **invisible**.
    `DEMO_HEADING` is an exact string, and a spec that spells its heading
    differently drops out of the run scope AND out of
    `test_the_scope_is_every_spec_that_publishes_a_demo_block`, whose two sides
    are built by the same reader and therefore agree about a file neither can see.

    Measured, not predicted: `SPEC/06c-instrument-repair.md` has carried a `bash`
    demo block under `## The demo artifact` since M06c and this module has never
    once run it.

    This assertion cannot fix that by widening the scope — that block records an
    eval history entry, and a demo command that writes is a worse defect than a
    demo command nobody runs. What it fixes is the silence: every unrun block is
    declared in `UNRUN_BASH_BLOCKS` with the property that keeps it out, a new one
    is red, and a declaration whose block has gone is red too."""
    found = _unrun_bash_blocks()
    declared = {path: 1 for path in UNRUN_BASH_BLOCKS}
    assert found == declared, (
        f"bash blocks outside a `{DEMO_HEADING}` section, measured: {found}; "
        f"declared in UNRUN_BASH_BLOCKS: {declared}.\n"
        f"A block this check does not run and does not name is a command nobody "
        f"runs and nobody knows nobody runs — debt 33's shape. Add it to "
        f"UNRUN_BASH_BLOCKS with the property that keeps it out, or move it into "
        f"a `{DEMO_HEADING}` section and let it be run.")
    # **A floor, and it is worth exactly what a floor is worth.** It stops an
    # entry added with `""` or `"TODO"` and it is satisfiable by padding; no
    # deterministic check can tell an argument from twelve words of filler, and
    # this one does not claim to. Stated here rather than left for a reader to
    # discover, because a check that reads stronger than it is is the defect this
    # module is about.
    for path, reason in UNRUN_BASH_BLOCKS.items():
        assert len(reason.split()) >= 12, (
            f"{path}'s exclusion reason is {len(reason.split())} words. An "
            f"exemption without an argument is the prose this check replaced. "
            f"This floor stops an empty reason and nothing more — it cannot "
            f"tell an argument from padding, and a reviewer still has to read it.")


def test_no_demo_command_writes_to_the_tree():
    """**Read-only, asserted rather than assumed.**

    This check runs committed commands against the committed tree on every `make
    check`. If one of them wrote — a `policy generate` in a future demo block,
    say — the suite would be mutating the repository it is measuring, and the
    next reader would meet a dirty tree with no author. The whole scope is
    re-run once and `git status --porcelain` must be unchanged by it."""
    before = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                            capture_output=True, text=True).stdout
    for _, command, _ in CASES:
        subprocess.run([sys.executable, *command.split()[1:]], cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    after = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    assert before == after, (
        "a demo command changed the working tree. Demo artifacts are read-only "
        "by construction; one that writes turns `make check` into an author of "
        f"the state it checks.\nbefore:\n{before}\nafter:\n{after}")
