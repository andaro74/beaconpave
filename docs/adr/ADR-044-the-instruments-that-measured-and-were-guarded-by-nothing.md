# ADR-044: the file holding the only approver assertion, the only headroom check and the two-key agreement check was on no rule, and a duplicated registry id put a phantom principal in the deployed policy set for two keys

**Status:** Proposed. Written before the code. **Zero model calls.**
**Seats:** AI Quality (the eval-plane instruments, the rules list) · Security /
Red Team (G3's generator, G4's record contract, G5's witness) · Platform
Engineering (the mechanism) · Tool Owner (the registry) · Legal / S&P
(consequence classes, the disclosure flag)

Found during the SPEC/05 round-4 and round-5 reviews, **by planting against
`main`, not by reading.** None of it was introduced by M05, and none of it
appears in the twenty-one pre-flight findings SPEC/05 itself carried.

## How these were found

Six role subagents reviewed SPEC/05 across five rounds — 39 blocking findings on
draft 1, 31 on draft 2, 20 on draft 3, **55 on draft 4**, 49 on draft 5 — each
seat working in its own git worktree under one instruction: **do not read the
code, break it and run the suite.**

The count going *up* at draft 4 is the fact worth carrying. A falling count was
never evidence of convergence; drafts 1–3 were converging on a mechanism that
draft 4 then replaced wholesale, and the replacement had more exposure than what
it replaced.

**Two seats found finding 1 below independently, in the same round.** Neither was
looking for it.

## The threat

**T1 — the instrument that decides whether a control works is guarded less than
the control.** ADR-035's shape, a third time. There it was the probe corpus and
the comparator pins guarded twice while the control they measure was guarded
neither — the thermometer protected and the thermostat not. Here it is narrower
and worse: the thermometer is not protected either, and four separate protections
are wired through it.

**T2 — the registry can decide the same thing twice.** ADR-004 says "the registry
decides." It never said the registry may decide once per id. A duplicated entry is
not a policy edit, not a generator edit, and not a schema edit, so it reaches the
deployed policy set past every rule those three paths carry.

## What exists, measured

Every plant was run on a clean tree, full suite. The baseline is `6af17d2` at
**1861 passed**; plants re-measured during round 5 ran on a tree carrying two
additional review documents and report **1881 passed**, the difference being
entirely `tests/test_cited_commits_resolve.py`'s per-citation parametrisation.
Both totals are given where they were measured, unrewritten, per the
eval-discipline convention.

### 1. `tests/test_contracts.py` is on no rule, and four protections run through it

```
twokey.evaluate(["tests/test_contracts.py"], "")            -> []
twokey.evaluate(["tests/test_calibration_corpus.py"], "")   -> []
twokey.evaluate(["tests/test_judge.py"], "")                -> []
```

One diff — delete `test_golden_set_keeps_headroom` (the repository's **only**
headroom check), flip both `expect_near_threshold` cases to `false`, and delete
`test_a_disposition_is_all_or_nothing`:

```
python -m pytest -q   ->   1859 passed, zero failures, zero keys
```

That file is cited by four modules as *"the file that pins X"* —
`evals/adversarial.py:37,292`, `platform/gateway/core/audit.py:256`,
`platform/gateway/core/guardrail.py:200`,
`quality/adversarial/g4-semantics.yaml:66,488`. It also holds, at `:598-622`, the
assertion that `.github/CODEOWNERS` and `pave/twokey.py` agree — which CLAUDE.md
names as the thing that makes the next drift *"a red check rather than a fourth
discovery."* That assertion was itself unguarded.

### 2. The only assertion that a publish-class tool declares an approver restated the gated set as a literal

`tests/test_contracts.py:71` held `gated = {"publish", "irreversible"}` — a sixth
definition site that `grep GATED_CONSEQUENCES` does not find. Narrowing it to
`{"irreversible"}` and deleting `approval: stepfn:editorial-approver` from the
registry:

```
python -m pave.cli policy generate --check   ->   exit 0
platform/gateway/policy/tools.cedar:44       ->   // ... Declared approver: none
python -m pytest -q                          ->   1881 passed
seats collected                              ->   tool-owner, legal-sp
```

Two keys, from the registry line alone. The file that decides what an interlock
means contributed none.

### 3. A duplicated registry id reaches the deployed policy set for two keys, neither of them Security

```
# append a second `- id: catalog-search` with callers: [attacker-svc]
python -m pave.cli policy generate           ->   6 policies, 4 contracts
python -m pave.cli policy generate --check   ->   exit 0
platform/gateway/policy/tools.cedar:54       ->   principal == Service::"attacker-svc"
python -m pytest -q                          ->   1881 passed
seats collected                              ->   legal-sp, tool-owner
```

This is the same `permit(principal == Service::"attacker-svc", …)` in the deployed
set that ADR-043 put four seats on — reachable through the registry at half the
price, without touching the generator.

**The phantom-caller form is the weaker half.** A second `- id: publish-highlight`
carrying `consequence: read` and substituted schema paths **overwrites the real
entry** in the generated bundle:

```
publish-highlight consequence: read       (was: publish -- interlock gone)
ai_generated present in the bundle: False (MER-AI-0001 disclosure flag)
python -m pave.cli policy generate --check   ->   exit 0
```

The disclosure flag `legal-sp`'s key on `tools/*/schema.*.json` exists to protect
leaves the gateway bundle **without `schema.in.json` being touched.**

### 4. The drift check proves the artifact is a faithful build product of the generator, never that the generator is a faithful function of the registry

ADR-043 recorded this and closed the generator-edit route with four keys. It did
not close the registry route. Two lines in `generate()` still put a phantom
principal in the committed set at `--check` exit 0 — and a **set-level**
surjectivity assertion (*every principal in `tools.cedar` is a caller the registry
names*) does not close it either. Measured against a plant that granted every
registered caller every tool:

```
policy generate --check   ->   exit 0
surjectivity on principals ->  GREEN     (recap-agent IS a registry-named caller)
recap-agent now permitted on publish-highlight
only test that noticed: tests/test_toolplane.py::test_an_uninvited_caller_is_denied_by_policy
```

A phantom **grant** needs no phantom **principal**. And the one test that caught it
is the cross-tool control that M05 removes from the registry in the same milestone.

### 5. Three more instruments on no rule

```
tests/test_tool_loop.py          -> []   one of four files that fire on a POLICY_MECHANISMS widening
tests/test_gateway_core.py       -> []   :283 is the ONLY live witness of G5-by-design
tests/test_gateway_run_parity.py -> []   deleting it + rewording user_turn: 1862 passed, zero keys
```

`tests/test_gateway_core.py:283` is the only assertion that survives deleting
`classify.py:124-125`'s dedicated `sensitive` short-circuit; every other
classification assertion stays green, because the index comparison at `:127`
refuses independently. It witnesses *refused by design* rather than *the index
happened to agree*, and it does so by passing `declared="sensitive"`.

### 6. The enumerated protection-test rule could be narrowed by four characters

ADR-042 added `^tests/(test_arm_scoping|test_instrument_stability|test_adversarial_lane|test_adversarial_entry|test_history_append_only)\.py$`
at three seats. Nothing pinned its membership:

```
# delete four characters: `_lane`
tests/test_adversarial_lane.py seats  ->  []
python -m pytest -q                   ->  1881 passed
```

`tests/test_adversarial_lane.py` holds `G4_CASE_FLOOR`'s ratchet, which
`pave/floors.py`'s own docstring calls *"the half that does the work."* Three keys
to zero, silently, for four characters — the "weakened together or not at all"
separation ADR-043 decision 1 forbids, on the one rule ADR-043's ratchet did not
reach.

## Decisions

**Decision 1 — two rules, not one.** `tests/(test_contracts|test_calibration_corpus|test_judge).py`
takes `ai-quality` + `platform-eng`; `tests/(test_tool_loop|test_gateway_core|test_gateway_run_parity).py`
takes `platform-eng` + `security`. The split follows who feels the control's pain:
the first three decide what a golden case, a judge and a corpus draw must satisfy;
the second three decide what the gateway is observed to have done. A single
four-seat rule over all six would tax every routine eval change with Security's
key to protect a G5 witness in a different file.

**Decision 2 — pinned member by member, not "at least one path."** Every filename
in each alternation is required by `test_the_seat_pin_covers_every_rule_this_adr_added`.
Finding 6 is why: "at least one path matches" is exactly what let a four-character
narrowing pass.

**Decision 3 — ADR-042's alternation is pinned too, retroactively.** It is not this
ADR's rule, but it is this ADR's defect class and the fix is five lines. Leaving a
measured zero-key hole open because it belongs to a previous ADR is how ADR-037
happened twice.

**Decision 4 — the `(ai-quality, platform-eng)` pair is byte-identical to the seat
set on `pave/twokey.py` itself, and that is accepted, because the pin is what
closes it.** Those two seats can delete the eval-plane rule *and* the checks it
guards in one diff using dispositions they already sign — measured at 1879 passed.
What stops it is `tests/test_twokey_seats.py`, which turns that diff red and is
itself **five-key**. So the weakening still routes through a file three seats who
do not feel the pain must sign. Adding a third seat to the rule would tax every
routine edit to buy a property the pin already buys. **G9 is satisfied by the pin,
not by the seat count**, and that is stated here because the seat count is what a
reader will check first.

**Decision 5 — the duplicate-id hard-stop goes in `cedar.generate()`, the deploy
path, and is converted to a named FAIL by the CLI.** `generate()` is the single
funnel both `policy generate` and `--check` pass through, so the refusal cannot be
routed around by regenerating. It raises `ValueError`; `pave.cli.policy_generate`
converts that to `_die(..., EXIT_CONTRACT)`.

The conversion is not cosmetic. `pave check` wraps the drift gate in
`except SystemExit` **only**, and its own comment (`pave/cli.py:1137-1141`) records
why: an escaping exception aborts before pytest runs and before `--out` writes a
verdict, so CI blocks on an *absent* verdict — exit 2, "page the platform" — when
the finding is a contract regression that should page the team. A bare `ValueError`
also exits 1 rather than 2 and prints a traceback.

**Decision 6 — the permit/grant check is a bijection on pairs, not a surjection on
principals.** *Every `(principal, resource)` a `permit` names is a grant the
registry makes, and every grant is permitted.* Finding 4 is why the set form is
insufficient. It reads the **committed** policy set, so it catches a hand edit as
well as a generator that lies.

**Decision 7 — the equality pin and the non-vacuity assertion ship together with
the import.** `tests/test_contracts.py` now reads `cedar.GATED_CONSEQUENCES`
instead of restating it. **The import alone would make the test vacuous** — a loop
over `{"irreversible"}` matches no registered tool and the body never runs, 47
passed. That is precisely the vacuity SPEC/05 uses to *refuse* moving
`GATED_CONSEQUENCES` into the registry, and reading it from an imported constant is
the same shape. So the test also pins the constant's value (`PINNED_GATED_CONSEQUENCES`,
a pin and not a second authority — the loop reads the real constant) and asserts
that it examined at least one tool. `tests/test_cedar_policy.py:471-472` is the
compensating anti-vacuity guard on the registry side; it is on a different rule,
and anyone who "simplifies" it re-opens this.

## What this does NOT do

**It does not make the eval-plane instruments red-on-weakening; it makes them
collectable.** A test deleted outright is invisible to pytest, and a key does not
change that. `COLLECTED_FLOOR` (SPEC/05 PR 4) closes the *net* deletion case —
`rm tests/test_adversarial_scoring.py` is 1821 passed, below any floor set at 1881
— and does **not** close deletion plus padding: the same deletion with one 60-case
parametrised file added is **1883 passed, above baseline**, with the entire G4
scoring protection gone and `pave check` reporting PASS. A count sees arithmetic,
not identity. **That residual is written here rather than discovered.**

**It does not add Security to `platform/registry/tools.yaml`.** Measured: with all
three guards in this ADR installed, adding `attacker-svc` to `publish-highlight`'s
`callers:` is one registry line, `--check` exit 0, 1862 passed, and
`['legal-sp', 'tool-owner']` — no duplicate id, no phantom grant, no generator
edit, so none of the three guards sees it. And the grant is real: the `forbid`
gates *when*, the `permit` gates *who*, so `attacker-svc` reaches the publish-class
tool on the same approval context the legitimate caller uses. **Whether the caller
allowlist needs Security's key is a G9 decision, it is owed, and it is recorded
here as open rather than closed by implication.**

**It does not touch `GATED_CONSEQUENCES`' location.** SPEC/05 draft 4 proposed
moving it into the registry; that is withdrawn, measured as a net de-keying from
four seats to two, dropping Security and Platform Engineering from the constant
that decides whether any approval interlock exists.

## Scale-up path

*At scale, replace the enumerated path lists with CODEOWNERS entries backed by
required reviews, and the duplicate-id hard-stop with a registry service that
enforces id uniqueness at write time rather than at render time; the interface
already matches — `generate()` takes the registry as a list and every caller
passes the parsed file.*
