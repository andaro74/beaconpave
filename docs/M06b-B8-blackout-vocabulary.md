# B8 — deploying `entitlement-check` re-inlines the blackout vocabulary

**A decision memo for four seats. Nothing here is decided.**
`tools/entitlement-check/schema.in.json` is `(platform-eng, security, tool-owner,
legal-sp)`. **Zero model calls; every number below was measured by running the
command beside it**, on `main` at `eca6726`.

M06b's second step deploys `entitlement-check`. It cannot be taken until this is
answered, and the answer is not the milestone's to give.

## The question

`SPEC/02` removed the blackout table from the model's prompt on the record and
refused two alternatives, one of them *"keeping the blackout table inline as 'policy
context'"*. `tests/test_gateway_run_parity.py:255` enforces it by forbidding every
DMA name, every blackout event and every blacked-out DMA from what the model
receives.

`entitlement-check`'s input schema `dma` enum **is** `data/catalog.json`'s `dmas`
list, verbatim. `handler.py:150-160`'s `tool_config()` ships each routed tool's whole
input contract to Bedrock as `inputSchema`. So routing the tool puts the enum in
front of the model and the test goes red — **the test this milestone's own spec
cites as the enforcement.**

## What actually leaks, measured

```
routed=[catalog-search]                    -> no leak
routed=[catalog-search,entitlement-check]  -> ['cedar-point','granite-falls','jefferson-city',
                                               'lake-adair','north-haven','port-william']

blackout mapping: {"jefferson-derby": ["jefferson-city","port-william"]}
in the enum surface:
  the six DMA names      : True
  the event name         : False
  which DMAs are blacked : False
  any title id / title   : False
```

**The enum reveals the vocabulary, not the table.** Six market names, with no event
and no mapping. Knowing all six does not tell the model which are dark for which
event — that is the thing `SPEC/02` removed, and it stays out.

## What the model already receives, measured

`services/highlights-agent/gateway_client.py:125`:

```python
return f"Viewer plan={plan} dma={dma}. Evaluation clock {CLOCK}.\n{prompt}"
```

**The viewer's own DMA is in the user turn on every request**, by design, *"in the
control's exact shape"* — identical in both arms. `rendered_model_surface()` inspects
the system prompt plus routed tools' input contracts and does not cover the user
turn, so the guarantee has always been about the *static* surface.

That is not a hole. It was tested: the blackout mapping and all six names planted
into `user_turn` are caught three ways —
`test_transport_parity.py::test_the_governed_arm_sends_the_pinned_viewer_turn`,
`::test_the_two_arms_send_the_same_viewer_turn`, and
`test_scaffold.py::test_the_gateway_client_template_sends_the_pinned_viewer_turn`.
The turn is pinned against a literal and across both arms and cannot be reworded.

**So the question is not "may a DMA name reach the model" — one already does, every
request. It is "may the model see the vocabulary when it already sees one member of
it."**

## What the enum buys, measured

Through the repo's own `toolplane.validate`:

| probe | TODAY enum | A shape pattern | C bare string |
|---|---|---|---|
| `jefferson-city` — a real DMA | accepted | accepted | accepted |
| **`atlantis` — a DMA that does not exist** | **REFUSED at the plane** | **accepted** | **accepted** |
| `JEFFERSON-CITY` — wrong case | REFUSED | REFUSED | accepted |
| `""` — empty | REFUSED | REFUSED | REFUSED |
| `../../etc/passwd` | REFUSED | REFUSED | accepted |

**The enum is the only thing that refuses a nonexistent DMA at the plane boundary.**
Remove it and that check moves from the governed edge into the thing being governed.

**And the tool cannot express what it would then have to.**
`tools/entitlement-check/schema.out.json`'s `reason` enum is
`['ok','blackout','upgrade-required','not-yet-started','unknown-title']` — there is
**no `unknown-dma`**. So options A and C are not one four-seat change; they are two,
because the output contract has to grow a value before the tool can answer
`atlantis` at all.

Also measured: `pattern` is in `SUPPORTED_KEYWORDS` (`toolplane.py:91`), so any
option is expressible; and **nothing in the tree reads the enum** — every `dma`
reference is to `data/catalog.json`'s list, to golden cases' `viewer.dma`, or to the
user-turn wrapper. Its only consumer is the plane's own validation.

## The options, priced

**A — drop the enum, keep a shape pattern.** Closes the leak. Loses plane-level
refusal of a nonexistent DMA. **Two four-seat changes**, because `unknown-dma` must
be added to the output contract. Moves a validation from the governed edge inward,
which is the direction this repo's thesis runs against.

**B — an opaque id the agent cannot compose.** Closes the leak. **Incoherent while
`user_turn` sends the DMA name in plain text** — the agent would receive the name and
be required to send an id it has no way to derive. Would need the user turn to change
too, and that is pinned across both arms and the scaffold template. Not recommended
by anyone; recorded so it is not re-proposed.

**C — keep the enum, amend `SPEC/02`'s rule.** Closes nothing by itself; it changes
what the rule forbids. Keeps every validation above. Requires amending a standing
decision and rewriting `test_the_catalog_is_gone_from_everything_the_model_receives`
so it forbids the **mapping and the event names** rather than the vocabulary — which
would make the test narrower in one direction and no weaker in the direction
`SPEC/02` actually argued about.

## A reading, and why you should discount it

On the measurements, **C is the one I would take**: the enum leaks vocabulary and
not the mapping, a DMA name already reaches the model every request, nothing reads
the enum but the plane, and A costs a second four-seat change while deleting the only
check that refuses `atlantis`.

**Discount that, because I am the wrong party to give it.** I am the seat that wants
this milestone to proceed, and I am recommending relaxing the control that blocks it.
That is ADR-035's shape — *"the seat that wants a guardrail to stop refusing its
questions is the seat that can widen it by a sentence"* — pointed at me. G9 exists
for this exact position.

If C is taken, it should make the rule **narrower and stronger**, not merely carve
out tool schemas: forbid the mapping and the event names explicitly, and keep the
vacuity guards the current test has.

## What each seat is being asked

- **Security** — can a model holding six market names, its own market, and no
  mapping infer a blackout? That is the question `SPEC/02` was actually arguing
  about, and it is yours.
- **Data Governance** — the DMA vocabulary as classified data, and whether G5's view
  of it differs from `SPEC/02`'s.
- **Tool Owner** — whether a `read`-class tool may take an unvalidated market
  identifier, and whether `unknown-dma` belongs in the output contract regardless of
  which option wins.
- **Legal/S&P** — whether amending a standing `SPEC/02` decision is in order here,
  and on what record. Related and separate: **no rule in `rules/` covers blackout or
  entitlement obligations at all** — `rules/` holds `MER-AI-0001.yaml` and
  `schema.json`. Disclosure has a rule; blackout does not, and this milestone
  deploys the authoritative blackout verdict.

## Notes

**A21 debt.** This memo quotes the six DMA names 9 times; four are real place names
in a rename `SPEC/06` defers to M07 in full. It cannot be written without them —
`SPEC/06` A5's standard is that a register quotes what it describes — and the count
is recorded so the rename knows.

**Not decided here, and not by this document:** whether the enum changes, whether
`SPEC/02` is amended, and whether `unknown-dma` is added. `SPEC/06b` Decision 8 stays
open until a seat records an answer.
