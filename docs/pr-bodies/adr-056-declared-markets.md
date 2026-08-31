# A tool may declare the markets it accepts, and only the complete list

ADR-056, executing `SPEC/06b` Decision 8. **Zero model calls.** Removes one of the
two blockers on M06b's second step.

## The problem

`entitlement-check`'s input schema `dma` enum **is** `data/catalog.json`'s market
list, verbatim, and `handler.py:150-160` ships every routed tool's whole input
contract to Bedrock. So deploying the tool put six market names in front of the
model and turned `test_the_catalog_is_gone_from_everything_the_model_receives` red —
**the test `SPEC/06b`'s own *"what M06b must not do"* list cites as the
enforcement.** A tool cannot state which markets it accepts without naming them.

## What was decided

**A registered tool may name markets in its declared input vocabulary. Nothing else
changes.** Measured before deciding (`docs/M06b-B8-blackout-vocabulary.md`):

```
the six market names   : True        <- what the enum adds
the event name         : False
which markets are dark : False       <- the mapping SPEC/02 removed stays out
any title id or title  : False
```

`SPEC/02` refused inlining the table because it lets the agent infer entitlement
from its own context — and **inferring needs the mapping**, which a bare vocabulary
does not carry. The model is also already told the viewer's own market on every
request (`gateway_client.py:125`), identically in both arms, pinned three ways.

**The enum stays rather than the schema being loosened**, because it is the only
thing refusing a nonexistent market at the plane:

| probe | enum | pattern | bare string |
|---|---|---|---|
| `atlantis` | **refused at the plane** | accepted | accepted |
| `../../etc/passwd` | refused | refused | accepted |

Dropping it moves a check from the governed edge inward, and costs a *second*
four-seat change: `schema.out.json` has no `unknown-dma`, so a tool accepting
`atlantis` could not say what happened to it. Whether `unknown-dma` belongs there is
**left open** and is the Tool Owner's.

## The rule comes out narrower in one direction and stricter in two

| | before | after |
|---|---|---|
| titles, title ids | banned everywhere | unchanged |
| event names | banned everywhere | unchanged, now asserted separately |
| markets in the **system prompt** | banned | **unchanged — banned** |
| markets in a **tool spec** | banned | permitted **only** as enum values, and only where the enum is the **complete** list |
| markets in a spec's prose | banned by the same substring scan | **banned structurally, by path** |

**The hole this opens is closed in the same diff.** Permitting a market enum permits
a *narrowed* one, and `["jefferson-city", "port-william"]` is exactly the derby
blackout — the mapping re-expressed as a schema. The old substring scan closed that
only by accident, by banning every market outright. So an enum naming any market must
name them **all**: publishing the vocabulary is safe precisely because it
distinguishes nothing, and a subset distinguishes only the markets that matter.

## What it survived

Eight plants, each through the real assertion against the **committed contract**
rather than a fixture:

| plant | expected | got |
|---|---|---|
| baseline, only `catalog-search` routed | pass | pass |
| **`entitlement-check` deployed, full market enum** | **pass** | **pass** |
| enum narrowed to the blacked-out markets | fail | fail |
| a market named in a spec `description` | fail | fail |
| the event name declared as a tool input | fail | fail |
| the blackout table inlined in the prompt | fail | fail |
| a single bare market name in the prompt | fail | fail |
| a catalog title/id smuggled into a spec | fail | fail |

**All eight are committed as tests**, because a plant in a scratch file does not
exist. Deletability audited — each clause deleted in turn, plus one weakened from
`==` to `<=`: **five mutations, five caught**, each by the test written for it, none
silent. The file was restored byte-exact and verified against its backup rather than
against `HEAD`.

## A caution worth stating rather than banking

**This diff collects two keys. The alternatives would have collected four.**
`twokey.triggered` over the changed set returns `('platform-eng', 'security')`,
because C deliberately does not touch `tools/entitlement-check/schema.in.json` —
which is the path carrying the four-seat rule.

So the option that leaves the schema alone is also the option that collects the
fewest keys, and it was proposed by the party the blocked control was blocking. That
is ADR-035's shape and G9's whole subject. It is recorded here, in the ADR, and in
the memo that proposed it, because the mitigation cannot be the reasoning — it has to
be the diff. What the diff actually does is ship two assertions **stricter** than
what it replaced and exercise its new permission on exactly one committed enum whose
exactness is now checked.

## What this does not do

- **It does not deploy the tool.** `TOOL_FUNCTIONS` is still `['catalog-search']`
  and `tools/entitlement-check/` still has no implementation.
- **B9 stands.** The audit record still cannot say a tool actually ran, and
  Security's recorded position is that step 2 must not land first under any
  ordering. One blocker removed, not two.
- **It does not generalise to "anything a schema declares"** — the relaxation is
  markets only, and an event name declared as an input is still refused, tested.
- **It does not settle `unknown-dma`.**

## Verification

```
$ python -m pytest -q      2290 passed, 6 skipped     # COLLECTED_FLOOR = 2255
$ python -m ruff check .   All checks passed!
```

Hermetic, no network, no new dependency. No `evals/history/` entry, no comparator, no
threshold, no golden case, no instrument digest, no recorded number moved. No tool
schema, registry entry or generated contract is touched — `policy generate --check`
has nothing to regenerate.

Two-Key-Disposition: platform-eng
Two-Key-Disposition: security
Two-Key-Rationale: The only keyed file is tests/test_gateway_run_parity.py, and
  what moves in it is the rule deciding what may reach the model. The change is a
  relaxation on one half of that rule and a tightening on two others, and every
  clause is exercised by a committed plant rather than described: the deployed
  tool's full market enum now passes, while a subset enum, a market named in spec
  prose, an event name declared as an input, the table inlined in the prompt, a bare
  market name in the prompt, and a catalog title in a spec all fail. Five mutations
  of the new clauses were planted and all five went red, none silent. The
  justification is that inferring entitlement needs the mapping and the vocabulary
  does not carry it, measured on the surface the tool adds: no event name, and no
  which-markets-are-dark. The viewer's own market already reaches the model on every
  request in both arms and is pinned three ways, so this widens what the model sees
  from one market to the list of all of them and by nothing else. The subset clause
  is the reason that is safe, and it closes a hole the old substring scan closed only
  by accident. Security is asked because the question of what a model can infer from
  a closed vocabulary is that seat's, and because the diff collects fewer keys than
  the alternatives would have, which is stated in the body rather than left to be
  noticed.

ADR: docs/adr/ADR-056-a-tool-may-declare-the-markets-it-accepts.md
