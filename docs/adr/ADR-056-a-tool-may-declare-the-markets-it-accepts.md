# ADR-056: a tool may declare the markets it accepts, and only the complete list

**Status:** Accepted. **Zero model calls.**
**Amends:** `SPEC/02`'s prompt-vocabulary decision, and the test that enforces it.
**Seats:** Platform Engineering · Security · Tool Owner · Legal/S&P — the four
`tools/entitlement-check/schema.in.json` collects, and the decision is `SPEC/06b`
Decision 8.

M06b's second step deploys `entitlement-check`. Its input schema's `dma` enum **is**
`data/catalog.json`'s market list, verbatim, and `handler.py:150-160` ships each
routed tool's whole input contract to Bedrock. So routing the tool put six market
names in front of the model and turned
`tests/test_gateway_run_parity.py::test_the_catalog_is_gone_from_everything_the_model_receives`
red — the test `SPEC/06b`'s own *"what M06b must not do"* list cites as the
enforcement.

`SPEC/06b` B8 recorded that as blocking and refused to resolve it.
`docs/M06b-B8-blackout-vocabulary.md` measured it for the seats.

## What was decided

**A registered tool may name markets in its declared input vocabulary. Nothing else
changes.** The rule is rewritten to be narrower in one direction and stricter in
two others, and the amendment is scoped to tool specs alone.

| | before | after |
|---|---|---|
| titles, title ids | banned everywhere | unchanged |
| **event names** | banned everywhere | unchanged, and now asserted separately with its own message |
| market names in the **system prompt** | banned | **unchanged — banned** |
| market names in a **tool spec** | banned | permitted **only** as enum values, and only where the enum is the **complete** market list |
| market names in a spec's prose | banned by the same substring scan | **banned structurally**, by path, which the scan could not express |

### Why the vocabulary is not the table

`SPEC/02` refused inlining the blackout table as *"policy context"* because it lets
the agent infer entitlement from its own prompt while a tool call in the trajectory
makes it look as though a tool answered. **Inferring requires the mapping.**
Measured on the surface the tool would add:

```
the six market names   : True
the event name         : False
which markets are dark : False
any title id or title  : False
```

Six names with no event and no mapping distinguish nothing. And the model is
**already told the viewer's own market on every request** —
`gateway_client.py:125`, identical in both arms, pinned by two transport-parity
assertions and the scaffold template. The question was never whether a market name
may reach the model; it was whether the vocabulary may, given one member already
does.

### Why the enum stays, rather than the schema being loosened

The alternative — drop the enum for a pattern or a bare string — was refused on two
measurements. The enum is the **only** thing refusing a nonexistent market at the
plane boundary:

| probe | enum | pattern | bare string |
|---|---|---|---|
| `atlantis` | **refused at the plane** | accepted | accepted |
| `JEFFERSON-CITY` | refused | refused | accepted |
| `../../etc/passwd` | refused | refused | accepted |

Dropping it moves a check from the governed edge into the thing being governed,
which runs against this repo's thesis. And it is not one change but two:
`schema.out.json`'s `reason` enum is
`['ok','blackout','upgrade-required','not-yet-started','unknown-title']` — there is
no `unknown-dma`, so a tool that accepted `atlantis` could not say what happened to
it. **Whether `unknown-dma` belongs in the output contract is left open** and is the
Tool Owner's; it is now a question about the tool's completeness rather than a cost
of this decision.

### The hole this opens, closed in the same diff

Permitting a market enum permits a *narrowed* one, and
`["jefferson-city", "port-william"]` is exactly the derby blackout — the mapping
re-expressed as a schema the gateway hands straight to the model. **The old
substring scan closed this only by accident**, by banning every market name
outright.

So the rule requires **exactness**: an enum that names any market must name them
all. Publishing the vocabulary is safe precisely because it distinguishes nothing; a
subset distinguishes only the markets that matter.

## What it survived

Eight plants, each run through the real assertion against the real committed
contract rather than a fixture:

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

All eight are committed as tests, because a plant in a scratch file does not exist.
Deletability audited — every clause deleted in turn, and one weakened from `==` to
`<=`; **all five mutations caught**, each by the test written for it, none silent.

## What this does not do

**It does not deploy `entitlement-check`.** `TOOL_FUNCTIONS` is still
`['catalog-search']`, the tool still has no implementation, and `SPEC/06b` B9 — the
audit record cannot say a tool actually ran — remains open and is Security's
position that step 2 must not land first under any ordering. This removes one of two
blockers.

**It does not generalise to "anything a schema declares."** The relaxation is
markets only. Event names are still refused *as declared inputs*, tested.

**It does not settle `unknown-dma`.**

**A note on who proposed it.** The reading recommending this option came from the
party the blocked control was blocking, which is ADR-035's shape and what G9 exists
for. It is recorded because the operator took the decision knowing that, and because
the memo said so in its own text rather than being asked. The mitigation is in the
diff rather than the reasoning: the amendment ships two assertions stricter than
what it replaced, and its permission is exercised by exactly one committed enum
whose exactness is now checked.

At scale, what a tool may declare is a property of the registry rather than a
substring rule in a test — the vocabulary is published from the same catalog the
tool validates against, so an enum and a market list cannot disagree. The interface
already matches: the enum is generated into `tools.contracts.json` from the
registry's schema pointer, and `data/catalog.json` is already the single source of
the market list.
