# `entitlement-check` gets an implementation, and the clock it needs is a parameter

M06b step 2, first half. **Zero model calls.** `twokey.triggered` → `[]`.

`tools/entitlement-check/` held a README and two schemas and **no code**. Its
registry entry, Cedar permit and generated contract have shipped since M02; the
thing they describe did not exist. Tool Owner's review of `SPEC/06b` measured the
consequence: a routed Lambda with nothing behind it is green, because nothing in
the suite checks that a registered tool has an implementation.

This adds the implementation and the tests that specify it. It does **not** deploy
it.

## The golden cases are the specification, so they generate the test table

Twelve committed cases assert an `entitlement` verdict. Each names a title through
`must_cite` and a viewer through `viewer` — which is exactly this tool's input. So
the expectation table is **derived from `cases.yaml` at import**, not written beside
it: a hand-written copy would be a second spec free to drift from the one the gate
actually scores, which is the two-registry smell ADR-030 was written about.

That cuts both ways on purpose. These tests go red if a golden case changes — and a
case is AI Quality's and is never edited to make a run pass, so a red here after a
case edit asks *"did the tool's contract just change?"* at the right moment.

## The precedence was derived, not chosen

The twelve cases fix every ordering between them:

| evidence | fixes |
|---|---|
| `blackout-001`, `multi-023` — base plan **and** a blacked-out market | **blackout > upgrade-required** |
| `entitlement-002`, `edge-024` — base plan, future event | **upgrade-required > not-yet-started** |
| `entitlement-010` — right plan, future event | `not-yet-started` |
| `entitlement-012` — a title not in the catalog | `unknown-title`, before anything |

Blackout outranking a plan gap is the one worth stating: a viewer who cannot watch
it *anywhere in this market* is not told to buy an upgrade that would not help.

## The clock, which is the actual design problem

`not-yet-started` cannot be computed without an instant, and there were only three
places one could come from:

- **The input contract — refused.** `schema.in.json` is `additionalProperties:
  false` over `title_id`, `plan`, `dma`, and the caller is the model. A tool letting
  the model supply the instant it is judged against hands back the decision its own
  output schema calls the tool's, and makes every other verdict conditional on a
  value the agent picked.
- **A constant in the module — refused.** ADR-021 widened the rule to *"no arm may
  define a second clock"*; `test_gateway_run_parity.py` enforces it. A third literal
  is a third instrument.
- **Deployment configuration — taken.** ADR-023 established this shape one component
  over: the Cedar principal is deployment configuration, never the caller's field.
  `check(args, catalog, now)` stays pure and testable; the deployed value arrives at
  the transport boundary.

**`now` has no default**, and a test pins that: a defaulted clock is a second clock
definition wearing a keyword argument — correct at one instant and silently wrong
afterwards.

## One rule is underdetermined, and it is recorded as such

Both `t001` (+1h) and `t005` (+7d) are in the future at the evaluation clock, and
the cases want `ok` for the first and `not-yet-started` for the second. So the
boundary is **not** "has the start time passed". The golden README states the intent
in words — the clock is *"one hour before the Jefferson Derby kicks off, one week
before the Cedar Point Rowing Finals … what makes 'tonight's derby' coherent and
'hasn't started yet' true"* — and never as a rule.

Implemented as **same UTC calendar day**, which is the narrowest rule reproducing
both and encodes "tonight" directly. **A 24-hour window fits the evidence equally
well and nothing committed can distinguish them** — there is no case between +1h and
+7d. That is written into the code as a choice rather than presented as derived, so
if a case ever lands at +20h on the following day, the seats find the note saying
they have to decide.

## What is asserted

20 tests. Beyond the twelve replayed cases:

- **The table is not empty and covers every reason** — a parametrised suite that
  silently collected nothing is the vacuity this repo keeps paying for, and a table
  missing `not-yet-started` would let the clock rule be anything at all. It asserts
  the reasons exercised equal the contract's `enum` exactly.
- **The verdict moves when the clock does** — an implementation ignoring `now` would
  pass every case above except this one, because `t005` is the only title the clock
  decides at the evaluation instant.
- **Every answer validates against the committed output contract**, which is
  `additionalProperties: false` — an extra explanatory field is a break, not a
  courtesy.
- **`unknown-title` claims nothing** about a title the tool cannot see: no
  `blackout`, no `required_entitlement`. Both are optional in the schema precisely so
  a verdict can decline to make them.
- **The `SPEC/02` split, from both sides** — this tool must read `blackouts` and
  `catalog-search` must not.

**That last one caught a mistake in its own first version.** It was a substring
check, and `search.py`'s docstring names `blackouts` four times to explain that it
never reads them — so `"blackouts" in source` said the exact opposite of the truth
and the test failed on a correct tree. It is now an AST check that strips docstrings
and looks at what the code uses, verified against five cases including a positive
control (`search.py` *does* read `titles`), so it is not simply returning `False`.

## What this does not do

- **It does not deploy the tool.** No `server.py`, no `gateway-stack.ts`, no
  snapshot regeneration, no routing pin. `TOOL_FUNCTIONS` is still
  `['catalog-search']`.
- **It does not generalise `test_mcp_server.py` over the registry.** Tool Owner
  measured that file as covering exactly one tool by literal path — the ADR-043
  shape, an instance closed and the class open. Generalising it belongs with the
  transport, because until `server.py` exists it would go red for the right reason.
- **It does not close B11** — `entitled` is still deletable from the four-seat
  output contract on a green suite.
- **It does not score anything.** No comparator, threshold, golden case, history
  entry or instrument digest moves.

## Verification

```
$ python -m pytest -q      2330 passed, 6 skipped     # COLLECTED_FLOOR = 2255
$ python -m ruff check .   All checks passed!
$ python -c "from pave import twokey; print(twokey.triggered([<changed>]))"
[]
```

Hermetic — the committed fixture, no clock of its own, no network, no new
dependency. Two files added and nothing existing modified.
