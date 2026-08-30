# ADR-052: every rule requiring an ADR names Security, and Security did not sign what an ADR is

**Status:** Proposed. Written after the measurement below and before the code.
**Zero model calls.**
**Seats:** Security / Red Team (the ADR requirement on the adversarial corpus,
which it holds alone) · Platform Engineering (the gate mechanism) · AI Quality
(the rules list)

ADR-051 moved the meaning of "plus an ADR" out of the PR body and into
`adr_records`. It did not move the key.

## The threat

Four rules in `pave/twokey.py` set `requires_adr`. **All four name `security`,
and `quality/adversarial/` names it alone** — CLAUDE.md states that one in as
many words: *"the adversarial corpus is Security alone plus an ADR."*

The rule covering the module that now decides what discharges all four named
`ai-quality` and `platform-eng`.

This was harmless until ADR-051. The ADR half was `ADR_RE.search(body)` plus
`is_file()`, which every tracked file satisfied — there was no strength in there
to weaken, and no definition to sign. `adr_records` is a definition.

## The measurement

On `6589827`, one diff, two files:

```
pave/twokey.py            substance bar 6 -> 1      (v3's defect, which four seats defeated)
pave/tests/test_twokey.py delete the 4 assertions that catch it:
                            test_the_substance_bar_is_the_calibrated_one
                            test_repetition_does_not_clear_the_substance_bar
                            test_the_repos_own_supersession_convention_is_not_refused
                            test_a_near_miss_is_still_named_when_the_count_is_short

2208 passed     ruff: All checks passed
keys needed:    ai-quality, platform-eng
requires_adr:   False
```

The ADR requirement on Security's own corpus goes back to a citation the gate
cannot verify, on two keys, neither of them Security's.

**The second file is not a bystander.** `pave/tests/test_twokey.py` was on no
rule, so the weakening and the deletion of everything that catches it fit in one
diff. Guarding the module alone leaves the tests removable; ADR-044 measured that
asymmetry twice and named it *"the thermometer protected and the thermostat
not."* Here it is the reverse and the same shape.

## Decision 1 — `security` joins the rule, and the test file joins it

```
"the two-key rules themselves — and the definition of what discharges one"
^(pave/twokey\.py|pave/tests/test_twokey\.py|\.github/workflows/two-key\.yml)$
ai-quality, platform-eng, security
```

`requires_adr` stays **off**. The rules list changes for routine reasons — a new
path, a widened alternation — and ADR-030's reasoning for `evals/comparators.json`
applies unchanged: an ADR per rule edit prices tightenings high enough to
discourage them, which is the pressure that gets tightenings reverted. This ADR
ships anyway, because a seat-set change is a G9 decision and `test_twokey_seats`
says so in its own failure message.

## Decision 2 — the requirement is derived, not copied

`test_the_definition_of_a_decision_record_carries_every_adr_rules_seats` reads
`twokey.RULES` live: the file defining `adr_records` must collect every seat any
`requires_adr` rule names. A rule that gives a NEW seat an ADR requirement turns
this red until that seat can also defend what satisfying it means. That is the
property; the current three-seat answer is its output, not its input.

The same file already records why: an earlier pin derived its expectation from
the constant an attacker is editing, so both sides moved together and the
comparison was vacuous under exactly the attack it was written for.

## The audit, and the two checks it made stronger

Seven mutations, deletions **and** weakenings. Three were silent on the first
run, and none of the three was redundancy:

```
drop `security` from the rule                     3 failed   caught
drop pave/tests/test_twokey.py from the pattern   1 failed   caught by the PIN only
delete the three ADR043_SEATS entries             SILENT     173 passed
neuter the derived test's requires_adr filter     SILENT     173 passed
```

- **The pin thinned by three is silent** because `len(ADR043_SEATS) >= 8` does not
  bite on a constant of thirty-odd entries. ADR-044's ratchet — every rule must
  name required paths — is the mechanism that does, and the rule is enumerated
  there now, member by member, for the reason ADR-044 gives: an alternation
  narrows by a few characters and loses a member silently.
- **The plant did not catch the narrowing.** It asserted the union of seats over
  both files, so `pave/twokey.py` alone still supplied all three. It now asserts
  each file alone as well. A test whose subject is two files must not be
  satisfiable by one of them.
- **The derived test was vacuous when neutered** with its own emptiness guard
  relaxed in the same edit. It now anchors on `security` specifically, drawn from
  a fact outside the module — CLAUDE.md's sentence about the corpus.

After: all four are red, three of them naming three failures rather than one.

## The instance of the gate that CI runs was tested at the module boundary

Every assertion defending `adr_records` stopped at `twokey`. `pave/cli.py` is what
CI invokes and what computes both endpoints, and it is on **no rule**. Measured on
this branch, three one-line edits, each run against the full suite:

```
head_sha = None                              2214 passed   SILENT   (baseline 2214)
base_sha = None                              2214 passed   SILENT
filter ADR problems out of `evaluate`'s      2214 passed   SILENT
  return before the exit code
```

The first re-enables the one-revision comparison where `git diff <base>` reads the
**working tree** — the defect ADR-051 added `--head` to close, four lines below the
refusal written for its twin. The third discards a correct refusal between the
gate and the exit code.

`test_the_head_endpoint_excludes_what_is_not_committed_to_it` proves `adr_records`
honours the endpoint it is handed. Nothing proved the CLI hands it one: *"the
module is right"* and *"the caller calls it right"* are different claims and the
second was unmade. Two tests now go through `cli.main`, and all three mutations
fail by name.

**The tests are the fix here; the key is not.** `pave/cli.py` holds `pave new`,
`pave verify`, `pave policy` and the gate commands, so a three-seat rule over it
taxes every CLI change to buy one property — and unlike `evals/comparators.json`,
where over-broad was chosen deliberately as the fail-closed direction, this file's
other subcommands have owning seats of their own. Whether the gate subcommands
should move to a module of their own that can be keyed is a Platform Engineering
decision this ADR states rather than takes.

## The Platform Engineering round, and the one finding an assertion cannot close

Seven findings, every one a planted diff and a measured suite. Six are fixed here.

```
inspect vs hasattr   move adr_records to pave/_adr.py, re-export     175 passed  SILENT
                     -> now 2 failed (see the withdrawal below)
seat filter          {s for s in rule.seats if s == "security"}       20 passed  SILENT
                     -> still silent; see below
normalization        lstrip("./") mangles BOTH sides symmetrically     1 passed  SILENT
                     -> now 5 failed
ratchet lookup       rename a rule onto an EARLIER required key        1 passed  SILENT
                     -> now 1 failed, named
ratchet forgotten    a rule enumerated with no path list           bare StopIteration
                     -> now a named failure
CLI output assert    satisfied by the RULE'S OWN NAME in the header    1 passed  SILENT
                     -> anchored on `and writes 0 (none)`, plus a control
wrong citation       "ADR-042's reasoning for comparators.json"        it is ADR-030's
```

Two deserve saying out loud. **`hasattr(twokey, "adr_records")` asserted that a name
is bound, not where it is defined** — the definition could be moved to an un-keyed
module and re-exported, at 175 passed. `inspect.getfile` follows it. And **the
normalization test this ADR's own diff rewrote was vacuous**: an equality between
two calls to the code under test cannot fail when that code fails symmetrically, and
the assertion carried a message claiming it distinguished the case it could not see.
Replacing a hardcoded assertion with a vacuous one is worse than leaving it.

### The seat filter cannot be closed by a better assertion, and is not left open

Decision 2's derivation is an expression, and the edit that computes a set can
filter it. Measured, on this branch:

```
collapse the per-rule difference                              175 passed  SILENT
collapse BOTH shapes (two lines)                              175 passed  SILENT
both, plus a new `requires_adr` rule naming only `legal-sp`   175 passed  SILENT
```

A second, differently-shaped derivation is added — a set difference over every rule
beside the per-rule containment — which takes the attack from one line to two and
is worth exactly that much. **No third shape helps.** Any assertion is defeated by
an edit to itself; that is true of every check in this repository and pretending
otherwise here would be the overclaim this register exists to catch.

What actually holds it is the file. `tests/test_twokey_seats.py` takes **five
seats**, and the plant's own victim is among them: the diff that gives `legal-sp` an
ADR requirement it cannot defend must be signed by `legal-sp`. That is G9 satisfied
by the seat set rather than by cleverness, which is the answer ADR-044 reached for
the identical class — *"what stops that is the pin in `tests/test_twokey_seats.py`,
which turns that diff red and is itself five-key."*

## The Security round: the key did not reach three of the ways in

Fifteen attacks, six landed. Nine were correctly refused and are listed at the end,
because a defence that holds is a result.

### Closed here — the key was guarding the wrong boundary

**`pave/__init__.py` was 0 bytes, on no rule, and runs on any `pave.X` import.**
A 27-line shim rebinding `adr_records`, guarded by `if "pytest" not in
sys.modules`, made the live gate print a decision record for a 2023 file the PR
never touched — `two-key: SATISFIED`, exit 0, **2219 passed, zero keys**. Without
those four words the same shim failed 23 tests, so the guard was the whole attack.
This ADR's own thesis, one directory up.

**Relocation defeats an attribute check, and it defeated the fix for it.** The
first draft asserted `hasattr(twokey, "adr_records")` — a name being bound, not
where it is defined; the implementation moved to `pave/gate.py` with a forwarding
stub at 20 passed, and the two-PR chain ended with the substance bar back at `< 1`
on **zero** keys. The fix for that was `inspect.getfile`, and **it was defeated by
the same attack one turn later**: `getfile` follows a rebinding but not a 176-byte
stub in the keyed file delegating to a 6kB implementation in an unkeyed one. 20
passed again.

So the property is neither *"the name exists"* nor *"this file defines it"*. The
answer written here was an AST walk **outward from `pave/twokey.py`**, and round 3
measured it vacuous — see below. The corrected form walks inbound from the
entrypoint CI runs.

**The replay and the CRLF corpus were on no rule.** Inflating the replay 60 → 300
rows and fabricating every row but two: **2219 passed, zero keys**. Only four facts
are pinned and the rest is free text — the module now takes three keys and the
evidence for its largest reversal took none, which is ADR-035's shape for the
fourth time in this file's history. `pave/tests/fixtures/` joins the rule as a
prefix, so a fixture added later is covered the day it lands.

### The guard count in the first draft was one too high

The draft said **five** assertions catch the bar weakening. Measured: **four**. The
fifth, `test_the_replay_behind_the_citation_cut_is_in_the_tree`, reads committed
fixture data and never calls `adr_records`. It failed in the original measurement
because the regex that deleted the other four **swallowed the module-level `REPLAY`
constant with them** — the fifth failure was a `NameError` raised by the measuring
script, not a guard firing. Re-measured on `6589827` with the four removed by AST
range: **2208 passed, zero failures, ruff clean, keys `ai-quality` and
`platform-eng`.** Every number in this ADR is the corrected one.

A guard count one too high is a protection **stated and absent**, which CLAUDE.md
ranks worse than one merely missing — and the guard it overcounted is the one whose
data was rewritable at zero keys until this diff.

### Not closed here, and named rather than fixed

**A routine `git merge main` mints a decision record.** Against unmodified shipped
code: a PR that widens `quality/adversarial/` and writes no record, then merges
`main` and picks up an unrelated ADR someone else wrote, gets `two-key:
SATISFIED`, **exit 0**. ADR-051 decision 4 names this class in as many words and
closed it with two endpoints plus a changed-file cross-check — and **the
cross-check is vacuous**, because both sides are built from the same two-dot range:

```
workflow    git diff --name-only --no-renames BASE HEAD
adr_records git diff --numstat ...            BASE HEAD -- docs/adr/
```

Both list the other author's ADR, so they agree with each other and with nothing.
That is the failure this diff's own docstring warns about — *"both sides moved
together"* — recurring in the endpoint pair rather than the seat pin. Three-dot
does **not** help: `pull_request.base.sha` is frozen and already an ancestor.
`git merge-base main HEAD`, then `that..HEAD`, does: the same PR comes back
BLOCKED, correctly.

It is not fixed here because it changes what `two-key.yml` fetches and what every
gate run compares against, and a change to the base endpoint of the gate is not a
rider on a seat-set PR. It is the next PR, and it is the most serious open item in
this file.

**A renumber discharges a rule.** `git mv` a 2023 ADR to a new number and rewrite
only the title line: ACCEPTED. The body is recycled prose and the single added line
is a title, which is easily six distinct substantive words on its own. This lands
on ADR-051's stated residual — the gate does not check an ADR is *about* the
control it discharges — and confirms that residual is reachable in one command
rather than in theory.

### The nine that failed

A symlink at an ADR path; a Cyrillic homoglyph in the slug; `.gitattributes`
`-diff` plus a one-word amendment; a UTF-16 ADR; add-then-delete across two
commits; a nested `docs/adr/sub/` path; a `conftest.py` planted anywhere, plus
`pytest.ini`, `tox.ini`, `setup.cfg` and `pyproject.toml` — all refused, the last
by ADR-043's harness rule, which held exactly as written. The derived property in
Decision 2 was attacked directly with a new `requires_adr` rule naming
`data-governance`: **2 failed**, correctly red.

## Round 3: the check written in round 2 was vacuous, and it was green

The round-2 property walked **outward** from `pave/twokey.py` — what the gate
imports. `twokey` imports nothing from `pave`, so the walk's fixed point was:

```
['pave/__init__.py', 'pave/twokey.py']
```

Both already members of the rule this ADR writes. The test iterated two paths and
compared them to themselves; it could not go red while `twokey` has no
intra-package import, and it shipped as a green tick. **The threat is inbound** —
a module that imports `twokey` and rebinds it before the gate uses it — and that
set is `pave/cli.py` and what it drags in, none of which the walk ever saw.

That is this ADR's own subject for the third time: a protection **stated and
absent**. Round 1 found it in `CODEOWNERS`-shaped prose, round 2 in a `hasattr`,
round 3 in the fix for the `hasattr`.

### What the walk could not see

```
pave/cli.py     shim rebinding twokey.adr_records AND twokey.evaluate,
                under `if "pytest" not in sys.modules`
                2222 passed -- THE EXACT BASELINE -- ruff clean, zero keys
                live gate: two-key: SATISFIED, exit 0, naming a decision
                record for a file the PR never touched
                (without the four-word guard: 75 failed)

pave/_adr.py    relocation behind `from . import _adr` inside a function body,
                MIN_SUBSTANTIVE_WORDS lowered under the same guard
                2224 passed, zero keys, live gate accepting a one-word
                amendment to a 2023 ADR

pave/gate.py    EXIT_QUALITY 1 -> 0: every rule reports BLOCKED and exits 0,
                the audit record intact and the enforcement gone
                CAUGHT at 13 failed -- but every exit-code assertion in
                `pave/tests/test_gate.py` compares against the SYMBOL, so
                both sides move together; the catch came from elsewhere
```

`from . import _adr` parses as `ImportFrom(module=None, level=1)`, and reading only
`node.module` made **every relative import invisible** to the walk. Putting it in a
function body meant a bare `import pave.twokey` never executed it, so the runtime
check missed it too. Two blind spots stacked.

### Decision 3 — the gate leaves `pave/cli.py`, and the property is its PROCESS

**The first remedy was a rule on `pave/cli.py`, and it was refused before it was
written.** ADR-041 decision 7 declined exactly that — three seats then — and
SPEC/06's `## What M06 does not build` declines it again, four more in round 5:

> The file has grown 1209 → 1616 lines and 21/128 → 26/139 commits since, so that
> argument is stronger now.

Their reasoning is that gating the most-edited file in the repository *"teaches
people to attest past a rule without reading it"*, and a rule everyone signs unread
is worse than none — you now believe you are protected. Decision 7 also names the
assertion it left behind to hold the line,
`test_ordinary_pr_is_not_gated`, which asserts a `pave/cli.py` diff is **not** gated.

**A draft of this ADR keyed the file and edited that test so the change would
pass.** Editing the test that holds a line in order to cross it is the worst move
available in this repository, and it is the one this register exists to catch.

Decision 7 also prescribed the remedy, which it had just used for the floors: move
the protected thing into a small module and key **that**. Applied here, it is
better than the rule it replaces — a shim has to be *inside* the process to work, so
the answer is not to make `cli.py` harder to edit but to stop running it.

`gate_two_key` and its three helpers move verbatim to **`pave/twokeycli.py`**, which
`.github/workflows/two-key.yml` now invokes as `python -m pave.twokeycli`. It does
not import `pave.cli`; `pave.cli` imports from it, so `pave gate two-key` still
works for humans and every existing caller and test keeps its symbol.

```
gate's process    11 modules -> 4      pave/{__init__,twokeycli,twokey,gate}.py
                                       every one of them keyed, with `security`

shim in pave/cli.py        old entrypoint `python -m pave.cli`      exit 0
                           CI entrypoint  `python -m pave.twokeycli` exit 1
shim in pave/twokeycli.py  both                                     exit 0
                           ...and that file collects platform-eng + security
```

The plant is the same twenty lines in both rows, and the control with no plant is
exit 1 on both paths — so the difference is the split, not the plant. `pave/cli.py`
stays on **no rule**, `test_ordinary_pr_is_not_gated` is back to the assertion
ADR-041 gave it, and a new test refuses the one edit that would undo this: any
import of `pave.cli` from `pave/twokeycli.py`, at any depth.

### The seat, and why two rather than three

The walk starts at the entrypoint read out of `two-key.yml`, resolves relative
imports and subpackages, and the test asserts that **every `pave/` module loaded in
that process collects `security`**. After the split that is four modules rather than
eleven, and all four are keyed:

```
^pave/(twokeycli|gate|verdict)\.py$        platform-eng, security
```

**Two seats, not three.** The property bought is that *Security is asked* — it owns
every rule that requires an ADR and holds the adversarial corpus alone. Requiring
the gate's full seat set would reopen `pave/infra.py`'s seats, which ADR-043
decided, to buy nothing this ADR is about.

And the seat set is now affordable for the reason ADR-041 gave: `pave/twokeycli.py`
is short enough that signing it means having read it, which is precisely what a rule
on a 1616-line CLI could not buy.

The entrypoint is **read out of the workflow**, not written down here. A draft said
that meant a check and the thing it checks *"cannot drift apart"*; round 5 falsified
that and it is narrowed below.

### The ratchet that makes a collapse red

A vacuous walk passed as a green tick, so the test refuses one. The round-3 form —
*"the walk reaches something outside the pinned set"* — stopped working when the
split made every module in the process keyed, which is the goal; an unsatisfiable
anti-vacuity check is just a vacuous check wearing a hat.

The anchor is now a module the gate **cannot decide without**: `pave/twokey.py`
holds `RULES`, `evaluate` and `adr_records`, so a walk that does not reach it
followed no edge at all, whatever it returned. Derived from the entrypoint, not
written down. Measured — pointing the walk back at `pave/twokey.py` is **1
failed**, naming the collapse.

### The audit, and the one silence it found

```
cli.py shim                          2222 passed   SILENT -- and correct: the file
                                                   now collects platform-eng+security
relative relocation into pave/_adr    2 failed     CAUGHT
EXIT_QUALITY 1 -> 0                  13 failed     CAUGHT
walk pointed back at twokey.py        1 failed     CAUGHT by the ratchet
drop cli.py from the rule             1 failed     CAUGHT
delete the relative-import branch    2222 passed   SILENT
subpackage: pave/adrdef/__init__.py  2224 passed   SILENT -> now 2 failed
lazy importlib inside the body       2224 passed   SILENT -> now 2 failed
git mv fixtures -> pave/tests/data/  2220 passed   SILENT -> now collects the key
```

The shim being silent to tests is the right answer, not a gap: it is a deliberate
code change to a file that now collects Security's key, and what stops it is a seat
reading the diff. The gate is a review mechanism; a test that could recognise an
arbitrary shim is not the control being bought.

**Deleting the relative-import branch is silent because no module in this
repository uses a relative import today.** Green because nothing covers it — the
reasoning that deleted two load-bearing checks earlier in this milestone, arriving
in a check written to close a defect that silence enabled. It is pinned against a
synthetic package instead of trusted, and deleting it is now 1 failed.

## The evidence for round 2 was measuring the measuring script

**"44 failed / 43 failed" is withdrawn.** Platform Engineering reproduced both and
found that a relocation stub with broken plumbing — a missing name, so the moved
implementation raised — puts 43 of those 44 failures in `pave/tests/test_twokey.py`
for the wrong reason. A *correctly wired* stub was **1 failed**, and behind a
relative or subpackage import, **0**.

That is the identical artefact this ADR corrects two sections earlier, where the
fifth guard turned out to be a `NameError` from a deletion regex. Twice in one
document, in the closing evidence for the round's most serious finding. The lesson
is not "check the number"; it is that **a mutation must be shown still to work
before its failure count means anything**. Every figure below comes from a run that
first asserted the gate still produced a verdict.

Re-measured, four relocation shapes, each with the full namespace carried across
and the gate verified working (baseline **2223**):

```
from pave._adr import adr_records          2 failed   CAUGHT  static walk
from ._adr import adr_records              2 failed   CAUGHT  static walk
from pave import adrdef  (a PACKAGE)       2 failed   CAUGHT  static walk
importlib.import_module inside the body    2 failed   CAUGHT  runtime, while deciding
```

Two of those four were **not** caught by the round-3 draft and are closed here:

- **A subpackage.** `from pave import adrdef` with the implementation in
  `pave/adrdef/__init__.py` is ordinary Python. The walk turned a dotted name into
  `pave/adrdef.py`, which is not a file, and skipped it; the runtime half guessed
  the same path and had `if not ...is_file(): continue`, which skips precisely the
  modules whose path it guessed wrong. **2224 passed, zero keys.**
- **A lazy dynamic import.** `importlib` is unreadable to a static walk, and
  importing the entrypoint never executes a function body, so neither half saw it.
  The runtime check now **runs `gate two-key`** on a path that triggers an
  ADR-requiring rule, and asserts the gate produced a verdict before believing what
  loaded.

**And the claim is narrowed to what that measures.** A draft said *"a module that
joins the gate's process while it decides cannot hide from that, whatever import
shape put it there."* Round 4 falsified it twice — a dynamic import on a branch this
one invocation never takes, which then unregisters itself from `sys.modules` (2225
passed), and a `types.ModuleType` aliased over a name the walk already saw with
`__file__ = None` (2223 passed, the exact baseline). The check is a post-hoc
snapshot of ONE invocation. What it proves is narrower and is what this ADR is
about: an **unkeyed** module cannot quietly become part of the gate's process. Both
falsifying plants needed a keyed file as their vehicle, so Security is asked either
way. It does not make the process tamper-evident.

### `__file__` is writable, so the check keys on names

Found while re-measuring: `pave._adr.__file__` came back as `.../pave/twokey.py`.
The relocated module had copied twokey's namespace and `dir()` carries `__file__`
along — so a module can claim to live in a keyed file. **A check that asks a module
where it lives is asking the module.**

`sys.modules` keys cannot be spoofed that way: to be imported as `pave.x` a module
must be named `pave.x`, and the walk yields exactly the names it reached. The
runtime half asserts on **names**; `__file__` is still read, but only to decide
which rule keys a module, never whether it is known.

### And the data could walk out of the rule by one directory

`pave/tests/fixtures/.+` covered the replay where it sits. `git mv` to
`pave/tests/data/` plus a one-word path edit is **2220 passed**, and the replay is
unkeyed permanently — the pin still passes, because `_seats_for` matches patterns
and never asks whether the file exists. The rule now covers every non-source file
under `pave/tests/`, so the data cannot leave by one directory. A move to an
entirely different tree still can, and is listed below.

## Round 5: the checked artifact and the executed artifact, separating

One class, three instances, found independently by the Security seat and by this
repository's own mutation loop — which costs no model tokens and reached the same
finding, so it is the cheaper of the two and not a substitute for either.

**A rule names a file. The interpreter is free to load a different one.**

### A package shadows the module the rule keys

`FileFinder` resolves `pave/twokeycli/` before `pave/twokeycli.py`. Adding
`pave/twokeycli/__init__.py` — two new files, nothing existing modified — leaves the
keyed module on disk as the thing every check inspects while the interpreter loads
the package:

```
live gate, CI entrypoint      two-key: SATISFIED    exit 0
suite                         2232 passed, 0 failed
keys on the two new files     NO KEYS
```

The strongest form composes `__file__ = <the keyed module>` into the package, and it
defeats both guards at once *with different halves of one plant*: the name check
cannot fire, because the loaded name **is** `pave.twokeycli`; and the `__file__`
check reads the decoy. Each guard was documented as covered by the other.

Three fixes, and the rule is the one that matters:

- `^pave/(twokeycli|gate|verdict)(\.py|/.+)$` — the package arm. Both shapes collect
  `platform-eng, security`, so the ambiguity costs a key either way.
- `_ci_gate_entrypoint` resolves a dotted name the way Python does, package first,
  and **refuses when both exist**. That ambiguity is not a thing to resolve; it is
  the attack, and a check that picks one silently has already lost.
- The seat assertion is keyed from the module NAME through the filesystem rather
  than from the module's own `__file__`. A check that asks a module where it lives
  is asking the module.

### "Read out of the workflow" was reading a comment

`re.findall(r"python -m (...)")` over the whole file follows a comment while the
step runs something else:

```
# python -m pave.twokeycli --base ... --changed ...
GATE=pave.cli
python -m "$GATE" gate two-key --base ...
```

**2228 passed, the exact baseline**, gate SATISFIED at exit 0 out of unkeyed
`pave/cli.py`. The workflow edit collects `security`, so a seat is asked — but the
claim that a check and the thing it checks *"cannot drift apart"* was false, and it
was load-bearing in this decision. The derivation was changed to parse the YAML and read only `jobs.*.steps[*].run`
with comments stripped — which closed the shape and **not the class**; see round 6.

### And it refused an honest refactor

Converting `pave/twokeycli.py` into a package legitimately — the module removed —
went red, twice. `rel[:-3].replace("/", ".")` yields `pave.twokeycli.__init__`, a
name the walk never lists; and the import-direction guard read `pave/twokeycli.py`
unconditionally. **A false refusal is the failure ADR-051 exists to remove**, and
both were in checks written to catch a real attack. The honest conversion now
passes at 181, and the dishonest one is 3 failed.

### The audit

Ten mutations, every plant verified live before its count was believed:

```
package shadows the module, __file__ spoofed     3 failed   CAUGHT
`GATE=$var` + decoy comment in the workflow      3 failed   CAUGHT
drop the rule's package arm                    181 passed   SILENT -> now 1 failed
hardcode the entrypoint                        2226 passed  SILENT -> now 1 failed
neuter either anti-vacuity guard               2226 passed  SILENT -> now 1 failed
delete the shadow refusal                                   CAUGHT
narrow the rule                                  4 failed   CAUGHT
reach pave.cli through a third module            4 failed   CAUGHT
honest conversion to a package                 181 passed   correctly NOT refused
```

The four silences were all the same shape: green because nothing on an honest tree
exercises them. Each is pinned against a synthetic tree now, which is the third time
in this milestone that reasoning has had to be applied rather than trusted.

## Round 6: fixing a shape is not closing a class

Round 5's fix stripped `#` comments and this ADR claimed *"a decoy has nowhere to
sit."* False. The derivation still regexed the **text** of a run block, and two gaps
compose:

- **A decoy sits anywhere a string can** — an `echo`, a quoted argument, a heredoc,
  or a step GitHub skips via `if:` that the parser reads and the runner does not.
- **The real command is invisible unless it is literally `python -m`.** Measured
  against the old regex: `python3 -m`, `python  -m` (two spaces), `python -mpave.cli`,
  `$PY -m` and `pave gate two-key` — the console script `pip install -e .` creates —
  are all **INVISIBLE**. Either gap alone goes red; together they are silent.

```
echo "running: python -m pave.twokeycli ..."   the decoy the check follows
python3 -m pave.cli gate two-key ...           what CI actually runs

suite            2230 passed, ruff clean -- the exact baseline
live gate        two-key: not required          EXIT 0
on               a change to quality/adversarial/, the rule Security holds ALONE
pave/cli.py      NO KEYS
```

A second shape needs no `echo` at all: run the console script, and leave a step
marked `if: false` naming the keyed module. It reads as a migration commit.

**Why three keys on the workflow did not answer it.** The same mitigation was
available for round 5's comment decoy and round 5 fixed that anyway, correctly: *"a
seat is asked"* is not the property. The property is that **the check follows what
CI runs**, and the reviewer signing those three keys on a diff whose visible content
is "log the command we run" gets no signal that every downstream assertion has been
repointed at a file nothing executes.

### The fix asserts over executable lines

Exactly one line in the workflow may mention `pave` at all, and that line must be a
recognised interpreter invocation naming the module — `python`, `python3` or
`py -3`, with `-m mod` or `-mmod`. An interpreter behind a variable does **not**
match, because a check cannot follow one and must not pretend to.

A decoy makes two lines. An unrecognised real command makes one line that does not
match. Either is red, and both of round 6's plants are **3 failed**.

This is narrower than "read the text" and wider than "read one regex": it is still
not execution. Deriving from execution — running the step's own command line and
observing what loaded — is the only form that closes the class outright, and it is
recorded below rather than built, because a check that runs CI's command line inside
the suite is a larger change than this ADR should carry.

### Attacks that failed

Found by this repository's own mutation loop, which costs no model tokens:

```
rename to pave/TwoKeyCLI.py (rules case-sensitive, Windows git not)  4 failed
namespace package, no __init__.py -- a shape _module_to_paths
  never forms                                                        6 failed
a second JOB naming the keyed module as a decoy                      3 failed
a step disabled by `if: false` as the decoy                          2 failed
the gate step replaced by `python -c runpy`, no `python -m` token    4 failed
```

Two are worth keeping. **Python's importer verifies case even on Windows**, so
`import pave.twokeycli` will not load `pave/TwoKeyCLI.py` — that attack dies at the
import rather than at any check here. And the namespace-package and `runpy` shapes
both fail **closed**: `_module_to_paths` forms no candidate, and the derivation
asserts rather than guessing.

## Residuals, stated because they are not closed

- **Deleting a test outright is still silent**, as it is everywhere. What answers
  it is that both homes are now keyed: `tests/test_twokey_seats.py` takes five
  seats, and `pave/tests/test_twokey.py` takes three including Security as of this
  ADR. That is the defence ADR-044 named for the same class, not a new one.
- **`pave/tests/test_twokey.py` still collects no key for its own CONTENTS being
  wrong**, only for the paths being un-keyed. SPEC/06 A11 is unchanged.
- **Three ADR files have no row in `docs/adr/README.md`** — ADR-041, ADR-042 and
  ADR-051 — and nothing asserts the index is complete. ADR-002, 005, 006, 008 and
  010 have rows and no file, which is by design: for a one-line cut the row **is**
  the record, confirmed against history. So the invariant is one-directional, file
  ⇒ row, and it is unenforced. ADR-051's row is added here because this ADR rests
  on it. ADR-041's and ADR-042's are not: neither ADR carries the *"at scale,
  replace with X"* sentence the README says every row ends with, so writing their
  rows means writing that sentence for them, and inventing a scale-up path for
  someone else's decision is worse than a missing row. Owed to Platform
  Engineering as its own PR, with the check that would have caught it.
- **`pave/tests/test_gate.py` is on no rule**, and every exit-code assertion in
  it compares against the symbol `gate.EXIT_QUALITY` rather than a literal, so both
  sides of that contract move together. `pave/gate.py` is keyed here; its test is
  not, and the contract has no assertion that would fail on its own terms.
- **The derivation reads a command line, not an execution.** The remaining form of
  round 6's class is a step that invokes the gate in a way no static rule can
  follow. The check refuses what it cannot recognise, so it fails closed — but
  closing the class outright means running the step's own command in a subprocess
  and observing what loaded.
- **An extension module beats source in Python's loader order**, so
  `_module_to_paths`' two shapes are incomplete: a committed `pave/twokeycli.pyd`
  would be loaded ahead of the keyed `.py`. Not measured — it needs a committed
  binary, which is not a plausible silent diff here — and named rather than claimed.
- **`if not path.is_relative_to(root): continue`** in the runtime seat loop is a
  deliberate escape for an installed copy outside the tree, and the one remaining
  place where a dotted name and the file the rules key may diverge by design.
- **`pave gate two-key` — the command a person runs before pushing — is still
  shimmable on zero keys**, because it resolves through `pave/cli.py`. CI is not:
  it runs `pave.twokeycli`. So the local instrument can be made to lie while the
  required check still blocks, and ADR-041 decision 7 forecloses the obvious
  remedy. Stated rather than fixed.
- **`quality-gate.yml` runs `python -m pave.cli check` and `gate history`**, so
  `pave/cli.py` remains inside two other deciding processes on zero keys. This
  ADR does not make that worse and does not close it.
- **A fixture moved out of `pave/tests/` entirely is unkeyed again.** The rule
  covers that directory, not the concept "data the gate's tests replay", and
  nothing asserts a pinned path still exists — three pinned paths deliberately do
  not (`conftest.py` anywhere is a plant, not a file).
- **`pave/tests/test_gate.py` collects no key** and holds the exit-code contract's
  only assertions, every one comparing against the symbol `gate.EXIT_QUALITY`
  rather than a literal, so both sides of that contract move together.
- **A `git merge main` still discharges a rule with another author's ADR.**
  Measured above, on shipped code, exit 0. The fix is the live merge base rather
  than the event payload's frozen `base.sha`, and it is the next PR.
- **A renumbered 2023 ADR with a rewritten title discharges a rule.** One `git
  mv` and one line.
- **The gate still does not check that an ADR is *about* the control it
  discharges**, which is ADR-051's residual and is untouched here.

**At scale, replace with:** branch protection with code-owner review over the same
path list, so the seat set is enforced by the forge rather than by an attestation
the author writes. The path list here and the one there are the same list — the
interface already matches.
