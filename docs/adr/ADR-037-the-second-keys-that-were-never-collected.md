# ADR-037: three second keys were recorded in the file that cannot collect them, and in none of the files that can

**Status:** Proposed. Written before the change; the change costs nothing to run
and spends no model calls.
**Seats:** AI Quality (the two-key rules) · Platform Engineering (the mechanism) ·
Security / Red Team (named as a second key on all three paths in question)

**Supersedes nothing.** ADR-013 decided that the second key is machine-checked
rather than collected through CODEOWNERS, and that decision is unchanged and
still correct. This ADR is about the two path lists that decision left behind.

## Context: the interface that was asserted to match, and does not

`pave/twokey.py` explains its own scaling story in its module docstring:

> *"AT SCALE: delete this check, put the seats back in CODEOWNERS, and require
> code owner review. **The path list here and the path list there are the same
> list — the interface already matches.**"*

They are not the same list. Measured, by resolving every CODEOWNERS path that
carries **two or more handles** — a second handle being the only way that file
expresses a second key — against `twokey.triggered()`:

```
/platform/infra/lib/gateway-stack.ts     handles=2  twokey -> ('security','ai-quality') +ADR
/evals/adversarial.py                    handles=2  twokey -> *** NO TWO-KEY RULE ***
/tests/test_adversarial_scoring.py       handles=2  twokey -> *** NO TWO-KEY RULE ***
/platform/gateway/core/audit.py          handles=2  twokey -> *** NO TWO-KEY RULE ***
```

**One of four.** Three paths were given a deliberate second handle at M04, each
with a comment in CODEOWNERS explaining at length why the second handle is the
point:

> *"**Both handles on each line, and that is the point.** CODEOWNERS is
> last-match-wins: a line naming only Security here would REPLACE `/evals/`'s AI
> Quality ownership rather than adding to it… Every handle resolves to the same
> person on a one-operator repo (ADR-001), so nothing changes in practice today —
> **the doctrine changes, and the doctrine is what scales.**"*

The doctrine does not scale from a file that cannot enforce it. ADR-013's whole
premise is that on a one-operator repo CODEOWNERS collects nothing, because
GitHub will not let a PR's author approve their own PR — *"the second key is not
merely inconvenient, it is unobtainable."* So a second handle added to CODEOWNERS
and nowhere else is a second key recorded in the one place that provably cannot
collect it. Today all three are decorative.

**This is the fourth arrival of the same fault, and the first three are all
recorded in these same files.** `pave/twokey.py`'s comment on
`evals/comparators.json`: *"three separate places asserted this rule existed
before it did… which is worse than an unguarded path, because a stated protection
stops anyone looking for the real one."* CODEOWNERS on `gateway-stack.ts`: *"a
change to the deployed guardrail auto-requested the seat that operates it and not
the seat that owns it, behind a line that read as though it were covered… Third
arrival, third seat, third file."* CLAUDE.md carries the summary of the same
finding. Each time the fix closed the instance and not the class.

**What made this one visible** was the ADR-036 four-seat review. The AI Quality
seat asked a different question — *does the enforced list agree with CLAUDE.md's
summary?* — and found `evals/adversarial.py` resolving to no rule at all. The
module that computes every instrument digest and decides what a probe passing
means is editable on **one key, by any seat.**

## The three paths, and why each was given a second key

Taken from the CODEOWNERS comments and the modules' own docstrings, not invented
here.

**`evals/adversarial.py`** — docstring: *"Owning seat: Security / Red Team."*
CODEOWNERS: it *"names this seat in its own docstring and matched only `/evals/`,
which is AI Quality's. So the module deciding whether a guardrail block counts,
and the suite that is the only thing able to see it widen, both sat with the seat
that feels a probe score rather than the seat that defends it. **That is G9 read
backwards.**"* It also holds `instrument_digests()`, `CEDAR_MECHANISMS`, and the
two `pass_when` literals.

**`platform/gateway/core/audit.py`** — docstring: *"Owning seat: Platform
Engineering (record shape) · Security (G4 semantics)."* It holds
`POLICY_MECHANISMS`, `build_record`'s consistency checks, and
`observation_from_record` — the function that turns a record into the observation
the scorer reads.

**`tests/test_adversarial_scoring.py`** — the test suite for the above. Listed in
CODEOWNERS with both handles for the same reason: a scorer weakened together with
the test that would have caught it is the shape G9 exists to make expensive.

## Decision

### The three paths get the rule CODEOWNERS already says they have

Added to `RULES` in `pave/twokey.py`, with the seat lists taken from the handles
CODEOWNERS already carries and the seats the modules' own docstrings already name:

| path | seats |
|---|---|
| `evals/adversarial.py`, `tests/test_adversarial_scoring.py` | `security`, `ai-quality` |
| `platform/gateway/core/audit.py` | `platform-eng`, `security` |

The scorer and its test are one rule, not two: they are weakened together or not
at all, and two rules would let a PR attest to one and quietly move the other.

### `requires_adr` stays **off** for all three

Deliberately, and for the reason `evals/comparators.json` already records: *"an
ADR per comparator move would price routine tightenings high enough to discourage
them, which is the pressure that gets tightenings reverted rather than the
pressure that keeps baselines honest."* These are code files that change often
and legitimately — ADR-036's corrections 3 and 4 both edit `audit.py`. The written
rationale in the PR body is the control; an ADR gate here would buy a form and
cost tightenings. `gateway-stack.ts` keeps its ADR requirement because a deployed
policy version is an instrument, not a routine edit.

### CLAUDE.md's summary stops enumerating, because enumerating is what drifted

CLAUDE.md says two-key is *"owning seat **plus** AI Quality"* over four named
paths. Neither half survives contact with the enforced list, which has ten rules
before this ADR:

- `quality/adversarial/` is **Security alone plus an ADR** — deliberate, and it
  is the row ROLES.md already carries as "probe downgrade to advisory".
- `platform/registry/tools.yaml` is **tool-owner + legal-sp**, no AI Quality.
- `evals/comparators.json` is **three seats**.

So the summary's shape is wrong, not just its list. It is rewritten to state the
principle, name the authority, and keep the two examples that are load-bearing —
rather than to hold a copy of a list that has now drifted twice. CLAUDE.md's own
sentence *"`pave/twokey.py` is the enforced list; this one is the summary, and
they must not disagree"* is retained and is the reason for the change.

ROLES.md's table gains the rows, because that table is what `twokey.py` says it
mirrors.

### A test asserts the two lists agree, so the fifth arrival is a red check

The class, not the instance. `tests/test_contracts.py` gains an assertion that
**every CODEOWNERS path carrying two or more handles resolves to a two-key rule**.
That is the exact query that found this, run every PR.

It is deliberately one-directional. A two-key rule with no multi-handle
CODEOWNERS line is fine — `evals/history/`, `quality/judge/` and the rest are
single-handle paths whose second key is AI Quality's by rule, and requiring a
second handle for each would be a CODEOWNERS change with no meaning on a
one-operator repo. The direction that matters is the one that failed: **a second
key stated in the unenforceable file and absent from the enforcing one.**

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | the new contract test **fails** on `main` as it stands today, and passes only after the three rules are added | it passes before the rules land — then it is not testing what found this, and it is decoration of exactly the kind this ADR is about |
| 2 | `pave gate two-key` on **this** PR requires `ai-quality` **and** `platform-eng`, because the PR edits `pave/twokey.py`, and blocks without both | it does not — then the rule protecting the rules does not fire on a change to the rules, which is a worse finding than the one this ADR fixes |
| 3 | the three new rules change no existing behaviour: the full suite is green and no other rule's resolution moves | a rule that previously matched now resolves differently — then a pattern is over-broad and is silently capturing paths it was not written for |
| 4 | after this lands, `evals/adversarial.py` requires two attestations, so **ADR-036's corrections cannot land on one key** | it still resolves to one seat — the pattern does not match the path, which is the failure mode `triggered()`'s own `lstrip` comment was written about |

Prediction 1 is the load-bearing one. A contract test written after the fix, that
would have passed before it, has proven nothing — and this repository has now
recorded the same class of fault four times precisely by fixing instances.

## Found during execution: the check reported green when it was handed nothing

Prediction 2 said `pave gate two-key` must block this PR without both
dispositions, because the PR edits `pave/twokey.py`. Run to confirm it, with a
flag this command does not take:

```
$ python -m pave.cli gate two-key --base origin/main
two-key: not required — this PR touches no two-key path
```

The rule protecting the rules, reporting that a diff editing the rules needs no
key. `--changed` is the flag; `--base` was silently ignored, `_flag_values`
returned `[]`, no rule triggered, and the command printed the reassuring thing.

**`_flag_values` asserts this cannot happen, in its own docstring:** *"Returns []
when the flag is absent — `gate decide` treats that as blocking, so a typo'd flag
can never be read as 'nothing to check, therefore fine'."* True of `gate decide`.
False of `gate two-key`, which is the caller where being wrong is worst. **A
protection stated generally and implemented in one of two callers** — the same
class as everything above, arriving in the parser that describes the class.

CI is unaffected: `two-key.yml` always passes `--changed "${CHANGED[@]}"`. The
exposure is a human running it locally, getting green, and believing it — which is
precisely what happened here, and the only reason it was caught is that a
pre-registered prediction said the opposite must occur.

Fixed in the same PR. Absence of `--changed` is now blocking; an **empty**
`--changed` stays legal, because a PR that changed nothing is vacuously compliant
and what is refused is never being told at all. `pave/tests/test_gate.py` pins
both halves.

**Prediction 2 stands as written and is confirmed** — the rule does require
`ai-quality` and `platform-eng` and does block without them, verified with
`--changed`. What the run falsified was not the rule but an assumption the ADR did
not state: that a green result from this command means the check ran.

## Consequences

- **ADR-036's corrections 3 and 4 become two-key.** They edit `audit.py`. That is
  the intended effect and it is why this lands first: a change to what a probe
  passing is must not land on one key, which is G9 stated plainly.
- **`evals/adversarial.py` becomes two-key**, so the carved-out unattributed-block
  fix (ADR-036 amendment 1, finding 1) needs Security **and** AI Quality. Also the
  intended effect.
- Nothing is re-scored, no threshold moves, no baseline moves, and no eval runs.
- Every handle still resolves to the same person (ADR-001). Nothing changes in
  practice today; the doctrine changes, and the doctrine is what scales.

## What this ADR does not do, and one open question it hands to the seats

It does not add a rule for any path that CODEOWNERS does not already carry a
second handle for. This is a reconciliation of two lists, not an expansion of
either — expansion is a separate decision with separate reasoning, and merging
the two would let a genuine judgment call ride in behind a bookkeeping fix.

**One path is left open, deliberately, because it is that separate decision.**
`platform/gateway/core/guardrail.py` names *"Owning seat: Security / Red Team"* in
its own docstring and carries **one** CODEOWNERS handle, matching `/platform/` —
Platform Engineering. That is not this ADR's fault shape (a second key stated and
uncollected); it is the *previous* one, `gateway-stack.ts`'s exactly: a docstring
naming a seat that no routing entry names. It matters now because ADR-036's
correction 1 edits that file, and because the ADR-036 review measured that
`_blocked_names` can be inverted with all six instrument digests holding and the
L5 lane still green.

Fixing it means a CODEOWNERS handle **and** a rule, and the question of whether
the gateway's decision path is two-key is a real one with a cost — `toolloop.py`
and `handler.py` sit on the same path and the same argument reaches them. **The
Security and Platform Engineering seats decide it; it is named here so that it is
carried by a document a checklist reads rather than by a docstring read only by
whoever has already decided to edit the function.**
