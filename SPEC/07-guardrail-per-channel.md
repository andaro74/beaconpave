# M07 — the guardrail, applied per channel

**Written before the branch is cut.** Owned by the PM seat. Branch
`m07-guardrail-per-channel`, tag `m07`.

**Deliberately short**, in SPEC/06d's shape. Every decision lives in ADR-070;
every "what broke" goes to the journal at close. This file states the milestone
and nothing else.

## Why

M06c accepted the tools-arm guardrail defect (ADR-064 option D) and M06d made the
report say so: `1/25`, *17 refused before scoring, 7 answered and scored wrong*.
M06b's *What's next* asked M07 to prove *that the platform can see what its own
controls refuse*. The operator has decided M07 takes the guardrail work; claim 6
moves to M08 (ADR-070 D1).

The defect is a viewer-facing topic classifier reading platform-internal
structured content. ADR-063 fixed it on the one channel the gateway held the
text for. Every one of M06b's 50 refusal samples is on the other side of
`converse`, where the gateway holds nothing and Bedrock cannot tell a tool
request from an answer (ADR-070 D2, D3).

**No claim in the twelve-claims table is assigned to it**; it unblocks claim 6's
measurement and serves claims 3 and 9 defensively.

## The one claim

**No golden case is refused by the viewer-facing topic policy for content the
viewer neither wrote nor would have been shown — measured on the tools arm
through the deployed gateway at k=3, with the probe suite and every frozen corpus
crediting what they credit today.**

Beside it, pre-registered and **not the claim** (ADR-070 D4): the majority-refused
count falls from 17 into SPEC/01's band, **0–2 of 25**. Falsifier: 3 or more.

## The plan, walked to the claim

| The claim needs | Provided by | Verified |
|---|---|---|
| A party that knows which of the model's outputs the viewer will see | `core/toolloop.py` branches on `stopReason` at `:405`; a `tool_use` round is a `tool_request`, the last round is the `answer` | PR 2, pure: a scripted `tool_use` round is handed to `inspect` as `tool_request`, the final round as `answer` |
| The guardrail applied by the gateway, per channel, at a pinned version | `converse` loses `guardrailConfig`; `handler._inspect` gains the `OUTPUT` source and the `tool_request` arm, explicit comparison, constant at the call site | PR 2, `tests/test_handler_wiring.py` rewritten pins; PR 4, every audit record names the deployed version |
| A record that says which channel | `CHANNEL_TOOL_REQUEST` in `core/guardrail.py`; `interpret_apply(channel=)`; `audit.schema.json` | PR 2 tests; PR 4 sidecar: every refusal's `channels` is one of the four |
| Each of the four assessments `converse` made, reproduced or its removal priced | ADR-070 D3's coverage table | PR 2: four plants, each deleting one assessment, each red; PR 4: the probe suite credits every `m04` probe |
| The refused text, where no scorer can read it | ADR-071 (PR 3): a store the record does not point to; the reader; ADR-069's four residual routes as tests | PR 3: a planted text leaves `observation_from_record`'s output unchanged; no reader under `evals/` or `pave/` |
| The count, on the real path | `run_with_tools.py` k=3 through the deployed gateway; `run_evals --refusals` (M06d) | PR 4 (stage 1, identical coverage) and PR 5 (stage 2), both committed as-run |
| Nothing else moved | `topic_baseline.py --all` (step 6b, `ApplyGuardrail`, real serialisation, deployed version); `run_probes_via_gateway.py` | PR 4 and PR 5, each |

## Pre-registered, in ADR-070

- **D1** — the ordering. Recorded, not argued.
- **D2** — the defect on the census: 50/50 on the output side, 39/50 before any
  entitlement verdict existed.
- **D3** — option B over per-channel-inside-`converse`, because per-channel on
  the output side is what B is for. ADR-066's four falsifiers answered.
- **D4** — two stages. Stage 1 keeps `tool_request` on the main guardrail at
  `OUTPUT` and predicts **14–20** refused; stage 2 moves it to the tool-output
  policy at `INPUT` **only if** at least half of stage 1's refused samples
  attribute to `tool_request`, and predicts **0–2**. Otherwise PR 5 is not built.
  **Outside 14–20 in either direction, the milestone stops at PR 4**: the count
  is committed as-run, ADR-070 records it as a finding about B, PR 5 is not
  built, and PR 6 closes red. PR 4 records the number; it does not explain it.
- **D5** — G1 and G4, and what checks each.
- **D6** — `ATK-003` is dispositioned in PR 4 with two keys and an ADR-062
  amendment: a scale cut or a signed extension. Never a checklist edit.

## Implementation constraints, binding

1. `converse` is called with no `guardrailConfig`. Every round's output is
   assessed before it is appended to the transcript or returned; the `ANSWERED`
   outcome carries only assessed text, and the refused text travels under its
   own attribute of `TurnOutcome`.
2. Policy selection stays an explicit channel comparison with the pinned
   constant at the call site (ADR-063). `test_handler_wiring.py` parses the
   source and must be able to see every pin.
3. One serialisation per channel, all in `core/`: the viewer's turn verbatim;
   tool results and each `toolUse.input` through `_inspection_text`; text blocks
   joined. The handler serialises nothing.
4. Stage 1 assesses `tool_request` with the main guardrail at `OUTPUT`. Stage 2
   changes exactly that arm and nothing else, under D4's rule.
5. No text in the audit record. `withheld` keeps its three fields and its
   `additionalProperties: false`; the record carries no pointer to the store.
6. No scorer reads the store: no new argument on `run_evals`, no reader under
   `evals/` or `pave/`. `evals/refusals.py` gains `--sidecar`, which prints
   channel × assessed counts from the sidecar and nothing else.
7. `m04-H` registered in `quality/adversarial/instruments.json` in PR 2, before
   the change; `m04-F` and `m04-G` untouched.
8. `quality/adversarial/*.yaml` untouched. No probe declares `tool_request`.
9. Both runs are k=3, both committed as-run, majority against majority. No
   re-run selection, no case edit, no baseline reset, no threshold move. The
   one re-run that is not selection: a sample with an INFRA case is refused at
   the door by `run_evals` (SPEC/02's rule) and is re-run whole, once, with the
   bad sample committed beside it as `*-infra.json` and passed to nothing.
10. No topic wording, no `examples`, no `outputAction`.

## What it builds

**PR 1 (this):** this spec; ADR-070; the progression shift (`README.md`,
`BUILD.md`, `docs/governance/demo-script.md`, `docs/governance/recordings.json`,
`SPEC/README.md`). Zero model calls. Two keys on the register.

**PR 2 — the redesign. Seats review this PR and no other.** `core/toolloop.py`
assesses each round's output through `inspect` with `tool_request` or `answer`;
`core/guardrail.py` gains `CHANNEL_TOOL_REQUEST` and the `OUTPUT` reader;
`handler.py` drops `guardrailConfig` and gains the two arms; `audit.schema.json`
admits the channel; `test_handler_wiring.py` rewritten; pure tests: channel
labelling, the four coverage plants, text-free caller response on every
channel, and an AST pin that `handler.py` calls no serialiser (constraint 3);
`tests/test_contracts.py`'s `CHANNELS` pin; `m04-H`. ADR-070 amended
with what was built. Hermetic. No deploy.

**PR 3 — the store, ADR-071.** Where refused text goes, its reader
(`read_withheld.py` amended: a digest that differs from the placeholder is now
the expected case), the G4 boundary tests (planted text, unchanged observation,
no `evals/`/`pave/` reader), and ADR-069's four residual routes as tests. No
deploy.

**PR 4 — stage 1, measured.** `make core`; tools arm k=3; probe corpus k=3;
step 6b; committed under `milestones/M07/stage1/` as `goldens-run-{1,2,3}.json`,
its refusals sidecar, `probes-run.json` (on the existing evidence rule by that
name), `topic-baseline.json`;
`evals/refusals.py --sidecar`; `run_with_tools.py`'s pre-flight print and
sidecar header (Definition of done); a two-key rule for `goldens-run*.json` and
the sidecar (ADR-069's M07 debt), widened in the diff that creates the evidence;
`ATK-003`'s disposition (D6). ADR-070 amended with the attribution and D4's
reading. **If D4 says stage 2 is not built, or the probe suite credits less,
the milestone closes at PR 6.**

**PR 5 — stage 2, measured.** The `tool_request` arm moves to the tool-output
policy at `INPUT`; `make core`; the same three measurements, committed as
`milestones/M07/goldens-run-{1,2,3}.json` and siblings. ADR-070 amended with
the count against the prediction.

**PR 6 — close.** Journal, progression row, tag. If the seats judge the stage-2
run admissible: ADR-069 D5 cut 1 first (per-case `refused` in `cases`,
`evals/history/schema.json`, `pave/history.py` — three keys), then the entry.
If not: no entry, and the cell says why.

## What it does not build

Any topic wording, example or `outputAction` · a third calibration · a change
to `question` or `answer` policy · a probe declaring `tool_request` · a fix for
the final-answer conjunction (`DEC-001`, `OUT-010`) if that is what PR 4 finds ·
`catalog-search`'s browse gap (it would raise the count; ADR-070) · the DMA
rename (SPEC/06b A21; re-dated to the SPEC/08 PR, ADR-070) · ADR-069 D5 cut 2
(one arm runs; the paired diff has no second arm) · `usage.tokens_in: 0` · the
headroom check · any golden case, baseline or threshold · a history entry
unless PR 6's seats sign one · **the p95 ceiling.** Constraint 1 adds one
`ApplyGuardrail` per round. The suite is already OVER at 11171 ms against
2500 ms (M06b), PR 4's demo artifact will print a worse number, and the
`suite latency OVER` line is expected, recorded in `guard_ms`, and not this
milestone's to fix (ADR-070, *What B costs*).

## Obligations inherited

`ATK-003` — **due this milestone**, PR 4 (D6). ADR-069's four residual G4
routes — PR 3. A two-key rule for `goldens-run*.json` and the refusals sidecar
— PR 4. Derivability of `refused`/`answered` — PR 6, if an entry is recorded.
`enforcement-probing`'s trigger — re-read at close from PR 5's census (or
PR 4's). `entitlement-circumvention` — open Security finding (ADR-035 A11),
this milestone's subject. ADR-062:51 vs `README.md:44` — resolved, PR 1.

## Bounded

- **Cap: six PRs.** Reaching it closes the milestone, red if necessary. Closing
  early is a success condition; closing red is an available outcome.
- **Seats on PR 2 only.** Attestations wherever `pave/twokey.py` demands them.
- **Turns, not model calls.** The meter is broken (`usage.tokens_in` is 0 on
  every goldens record) and one k=3 tools run is 150–170 `converse` calls on
  M06b's trajectories, so calls are not what is counted. Pre-registered: **216
  turns** (75 goldens + 33 probes per stage), plus headroom of **one whole-sample
  re-run per stage** (75 each) for an INFRA sample, ceiling **366**. A second
  INFRA sample in one stage is not re-run: the stage closes with what it has and
  the milestone stops as for a count outside the band. All through the deployed
  gateway, in PR 4 and PR 5 only. PRs 1–3 and 6 are zero. `make check` stays
  hermetic.
- A discovered defect is recorded with a deadline and left alone.

## Demo artifact

```bash
python -m evals.run_evals --arm tools \
    --answers milestones/M07/goldens-run-1.json \
    --answers milestones/M07/goldens-run-2.json \
    --answers milestones/M07/goldens-run-3.json \
    --refusals milestones/M07/goldens-run-refusals.json
python -m evals.refusals --sidecar milestones/M07/goldens-run-refusals.json
```

Predicted, not yet measured:

```
N/25 passed (M failed, 0 infra) — judge axes recorded ADVISORY, not scored (ADR-012)
of the M failed: R were refused before scoring, A answered and scored wrong
refusals: S/S resolved to P (mechanism, assessed) pair(s) — …
channels: tool_request 0 · answer R' · question 0 · tool_output 0
```

with `R ≤ 2` and no `TOPIC:*` on `tool_request` or `tool_output`, and a
`suite latency  OVER` line above 11171 ms, which is expected. The same two
commands on the `stage1/` files print stage 1, where `R` is 14–20 and the channel
line is the attribution D4 reads.

## Definition of done

- [ ] ADR-070 merged before any gateway code.
- [ ] `converse` carries no `guardrailConfig`; every round's output assessed
      before it is appended or returned; `ANSWERED` carries assessed text only.
- [ ] Four channels labelled by the loop; `tool_request` in `CHANNELS` and the
      schema; each pin visible to `test_handler_wiring.py`.
- [ ] Four coverage plants, each red; text-free caller response on every
      channel, by test.
- [ ] `m04-H` registered before PR 2's code; `m04-F`, `m04-G` untouched.
- [ ] Refused text in a store the record does not name; planted text leaves the
      observation unchanged; no `evals/` or `pave/` reader; ADR-069's four
      routes closed as tests.
- [ ] PR 4's and PR 5's sessions print, **before the first call**: the deployed
      gateway function, `GUARDRAIL_VERSION` and `TOOL_OUTPUT_GUARDRAIL_VERSION`
      read from that function's configuration, and the source path of
      `_inspection_text` (`core/toolloop.py`); the sidecar header carries all
      three, and a run whose records name any other version is not a reading.
- [ ] Stage 1 run committed as-run; count read against 14–20; probe suite credits
      every `m04` probe; step 6b unmoved; attribution recorded in ADR-070. Outside
      the band: stopped, recorded, not diagnosed.
- [ ] `ATK-003` dispositioned with two keys and an ADR-062 amendment.
- [ ] Stage 2 built or not, per D4's rule, and the rule's reading recorded.
- [ ] If built: the count against 0–2, as-run, no `TOPIC:*` on `tool_request`
      or `tool_output`.
- [ ] `make check` green on every PR; attestations per `pave/twokey.py`.
- [ ] `close-milestone` in order; journal; progression row; tag `m07`. Six PRs
      or fewer.

## What must not happen

No topic wording moves. No case, baseline or threshold moves. No model text in
an audit record, an answer file, a sidecar, or anything under `evals/`. No
`skip_guardrail`, no default that runs a turn uninspected. No stage 2 without
stage 1's attribution in hand. No count re-run until it fits. No claim
rewritten to match the outcome. No diagnosis in PR 4: a count outside the band
is a finding about the pre-registration, and the milestone stops on it.
