# ADR-070: M07 takes the guardrail work, and the gateway applies the guardrail per channel

**Status: PROPOSED in M07 PR 1; ACCEPTED when that PR merges, which is the
operator's disposition.** Decision 1 is the operator's and is recorded here, not
argued. Decisions 2–6 are the design, written before the code, and the redesign
PR (PR 2) is the one the seats review. **Zero model calls to write** — every
number below is read out of files committed since M06b.

**Seats:** Security / Red Team (the control, and G4's boundary moves with any
capture) · Platform Engineering (the gateway and the loop) · AI Quality (the
instrument, and what a scorer may read) · PM (the roadmap shifts by one row).

## Decision 1 — M07 takes the guardrail work; the rules registry moves to M08

ADR-062:51 dates `ATK-003` to *"M07, the milestone that takes the guardrail
work."* `README.md:44` had M07 as *Rules registry + regdelta loop*, and the M06b,
M06c and M06d journals each carried *"M07 is claim 6 — unchanged."* Both could not
be true, and SPEC/06d flagged the disagreement for Security at M07's open.

**The operator resolved it in favour of ADR-062.** M07 is the guardrail
milestone. Claim 6's milestone — the rules registry and the regdelta loop — moves
to M08, and every later row shifts by one: surfaces to M09, the drill to M10,
self-heal to M11. Not relitigated here; recorded so the record and the table
agree again.

### Sites corrected in PR 1, and sites left as-run

Corrected, because they are live documents a reader consults for what is
scheduled: `README.md` (the progression table, the *Part two (M05–M11)* line,
the twelve-claims table's `M` column, and the M06c footnote that said *M07's
claim 6*), `BUILD.md` (the milestone table), `docs/governance/demo-script.md`
(Acts 3–5 name their milestones), `docs/governance/recordings.json` (Acts 3–5's
`owner_milestone` and `owed_by`), and `SPEC/README.md`.

**The obligation register is renumbered, not deferred.** An act's owner is *the
milestone that builds the thing the act records*; that milestone has a new
number and the same content. No milestone closed with any of the three acts
owed to it, so `deferred_from` is untouched and the ratchet
(`tests/test_demo_recordings.py::uncounted_deferrals`) has nothing to count.
Two keys, because the register is a two-key file and the check is the file's
own.

Left as-run, because they are records of what was believed when written:
ADR-062, ADR-064, ADR-066 and ADR-069 (their *M07* is the guardrail deadline
and was right), `milestones/M06b/README.md`, `milestones/M06c/README.md` and
`milestones/M06d/README.md` (*"M07 is claim 6"* is what those closes said),
`SPEC/05`, `SPEC/06b`, and every ADR that says *the second brand is M08's*.

Left for the next spec PR, and listed so it is a checkbox rather than a
discovery: four code and template sites say *M08* and mean the surfaces
milestone, now M09 — `pave/cli.py:699`, `pave/floors.py:338`,
`pave/manifest.py:142,324`, `pave/scaffold.py:123`, and
`templates/agent-tools/README.md:28`, with `tests/test_floors.py:250` beside
them. They sit on three different two-key rules, one of them four seats, and a
documents PR does not collect four seats to move a digit in a docstring. **The
SPEC/08 PR corrects them**, and this paragraph is the list.

## Decision 2 — what the defect is, on the committed evidence

The defect M07 fixes is the one `docs/M06b-guardrail-diagnosis.md` measured and
ADR-064 option D accepted: **`entitlement-circumvention` classifies the
platform's own structured, machine-produced content as a viewer's intent.**
Measured on the tool-output channel, the topic blocked `entitlement-check`'s
grants 5/5 and passed its denials 0/5, and the verdict flipped on key order and
on an unrelated field. Two calibrations were tried against the frozen corpora
and both were refuted — one doubled the false positives, the other unblocked two
attacks. **No third is proposed here.**

ADR-063 closed the half of that defect the gateway could already reach: the
`_inspect` path selects a topic-free policy for `tool_output`, deployed and
verified 8 → 0 on the real gateway (`docs/M06b-wiring-verified.md`). What
remains is read out of `milestones/M06b/goldens-run-refusals.json` and the three
trajectory files beside it:

```
50 refused samples across 3 runs, all mechanism=guardrail,
   all assessed=TOPIC:entitlement-circumvention, all channels=["answer"]

tools executed before the block        samples
  none                                     11     (blocked on the model's first output)
  catalog-search only                      31     (blocked on the output after retrieval)
  catalog-search + entitlement-check        8     (blocked on the output after a verdict)
```

Every refusal is on the **output** side of `converse`. Thirty-nine of fifty fired
before `entitlement-check` ran at all, so the tool's grant is not what the
converse guardrail is reading in most samples. What it is reading is the model's
output on a round — and on a round that ends in `tool_use`, that output is a
**tool request**: text the viewer never sees, addressed to the platform, carrying
a JSON `input` the plane validates. Whether the blocked round was a tool request
or a final answer **the record cannot say**, because Bedrock reports every
round's output under one `outputAssessments` map and the gateway labels all of
it `answer`. That is the shape of the tool-output defect again — a viewer-facing
topic classifier over platform-internal structured content — one channel over,
where ADR-063's fix cannot reach.

**Two things this decision does not claim.** It does not claim the blocked
rounds *are* tool requests; that is the inference the census supports and PR 4
measures. And it does not claim the answer channel is clean: `OUT-010` and
`DEC-001` (ADR-067, ADR-068) show the topic firing on a refusal joined to its
alternative at `source=OUTPUT`, on constructed text. If PR 4 attributes the
refusals to the final answer, that finding stands and this ADR's mechanism does
not fix it.

## Decision 3 — option B, chosen over applying the guardrail per channel inside `converse`

The operator put two options on the table: **option B** (ADR-064: the gateway
stops passing `guardrailConfig` and applies the guardrail itself) and
**per-channel application** so structured tool output is not classified as user
intent. Read against the code, the second is not an alternative to the first.
**It is what the first is for.**

### What "per channel inside `converse`" can reach, and what it cannot

Bedrock offers three levers on a `converse` guardrail, and the census above
tells which channel needs one:

| lever | channel it moves | what the evidence says |
|---|---|---|
| `guardContent` blocks | input side only — which content of the user message is assessed | **0 of 50** refusals are on the input side. Nothing to fix there. |
| `outputAction: NONE` on the topic | output side, the whole of it | option E — **refused on measurement** (ADR-065): unblocks three genuine harms to recover one wrong refusal |
| nothing else | the model's output on one round versus another | **does not exist.** `converse` assesses each round's output under one policy and cannot tell a tool request from an answer, because it does not know which output the viewer will see. Only the loop knows: it branches on `stopReason` at `core/toolloop.py:405`. |

So the guardrail cannot be applied per channel to the model's own output from
inside `converse`. The only party that can separate `tool_request` from `answer`
is the gateway, and the gateway can only apply a policy to text it holds.
**Option B is the mechanism by which per-channel application becomes possible
on the output side.** Capture is what B also makes possible; it is not why B is
chosen.

### What B is, exactly

Four channels, one assessment each, applied by `handler._inspect` at a pinned
published version, selected by an explicit channel comparison at the call site
(ADR-063's two-call-site rule, kept):

| channel | content | policy | source | today |
|---|---|---|---|---|
| `question` | the viewer's turn, verbatim | main guardrail (v4 topics + filters) | `INPUT` | `converse` input assessment |
| `tool_output` | a tool's result, `_inspection_text` | tool-output guardrail (filters, no topics) | `INPUT` | unchanged (ADR-063) |
| `tool_request` | the model's output on a round ending `tool_use`: its text blocks and each `toolUse.input` through `_inspection_text` | **stage 1:** main guardrail · **stage 2:** tool-output guardrail (Decision 4) | **stage 1:** `OUTPUT` · **stage 2:** `INPUT` | `converse` output assessment, labelled `answer` |
| `answer` | the model's output on the final round, its text blocks | main guardrail | `OUTPUT` | `converse` output assessment |

`converse` is called with no `guardrailConfig`. Every round's output is assessed
before it is appended to the transcript or returned, and the `ANSWERED` outcome
carries only assessed text.

### ADR-066's four falsifiers, each answered before the code

ADR-066 priced B and registered the conditions under which it is refused. Each
is met or the ADR does not proceed.

**1. "Step 0 finds the text present → withdrawn."** It did not; the blocked
response carries the platform's own 73-character placeholder, digest for digest
(`milestones/M06c/blocked-response-fingerprint.json`). B's pricing stands and B
is what is built.

**2. "A coverage argument cannot be written for each of the four assessments →
refused."** Written here, one row each:

| what `converse` assessed | under B | coverage |
|---|---|---|
| the viewer's turn | `question` at `INPUT`, **before** the first model call | same policy, same source; stronger by one property — a blocked turn now spends no tokens |
| the model's intermediate reasoning, each round | `tool_request` at the round it is produced | same text, assessed once, at the moment it would enter the transcript |
| the accumulated transcript on later rounds, tool results included | every piece is assessed **once, on entry**: the turn on `question`, each result on `tool_output` (already), each request on `tool_request` | **this is the one coverage change.** Whether `converse` re-assesses the accumulation is unverified in this repository (`core/guardrail.py:190-196` says the input side covers "the whole input"; ADR-066 says "from round two onward the input is the transcript"; M02 measured refusals rising with turn length, which either reading predicts). What re-assessment could add is a block on a *conjunction* across pieces that each pass alone. The only conjunction this repository has measured firing is a refusal joined to its legitimate alternative (`DEC-001`) — a correct answer. Priced as a possible reduction, falsifier below. |
| the final answer | `answer` at `OUTPUT` | same policy, same source |

**Falsifier for the coverage change:** the probe corpus, run through the
deployed B gateway at k=3 in PR 4, must credit every probe the `m04` comparator
credits. A probe that passed on an `answer` block and stops passing is a
coverage loss; PR 4 stops there, and the milestone closes red with B reverted or
the loss dispositioned by Security in an amendment here. Nothing widens.

**3. "The G4 sink cannot be separated from the audit record → refused, or split
into its own diff with its own ADR."** Split. The refused text goes to a store
the audit record does not point to and `observation_from_record` does not read;
the record keeps ADR-066's content-free `withheld` fragment (three fields,
`additionalProperties: false`, unchanged) — now a digest of the **model's** text
rather than of Bedrock's placeholder. The store, its reader, and the four
residual G4 routes ADR-069 dated to M07 are **ADR-071 and PR 3**, and nothing in
PR 2 writes a byte of model text anywhere.

**4. "The trust-boundary change cannot be made testable → refused."** Today
Bedrock guarantees blocked text never reaches the gateway. Under B the gateway
receives unapproved output and must not return it. That guarantee becomes a
property of pure code: `core/toolloop.py` builds the `ANSWERED` outcome from the
assessed output only, the refused text travels under its own attribute of
`TurnOutcome`, and `GuardrailOutcome.as_response_fields` — the one function
composing the guardrail-derived keys the handler returns on a block — carries no
text and is pinned to a fixed key set. PR 2 plants a blocking assessment on each
channel and asserts the caller-facing dict is text-free; `test_handler_wiring.py`
asserts the handler's blocked branch is composed from that function and
`record_id` and nothing else. "Trusted not to return it" is an assertion, in the
hermetic suite, on every run.

### What B costs, stated plainly

- **The in-call guarantee is replaced by the loop's.** A defect in
  `core/toolloop.py` can now return unassessed text; a defect in Bedrock's
  integration could not. The loop is pure, tested, and the property is pinned;
  it is still a weaker guarantee than the one it replaces, and this sentence is
  the concession.
- **One `ApplyGuardrail` per round, plus one for the viewer's turn.** Suite p95
  is already OVER at 11171 ms against 2500 ms (M06b); it will rise. Recorded,
  not accommodated, in `guard_ms` as today.
- **The instrument moves.** `core/toolloop.py` and `core/guardrail.py` are in
  `guardrail_sha256`; `core/audit.py` (PR 3) in `capture_sha256`. **`m04-H` is
  registered in PR 2, before the change** (ADR-038), beside `m04-G`, never
  editing it. `scorer_sha256`, `semantics_sha256` and `probes_sha256` do not
  move: the scorer reads what it read.
- **`test_handler_wiring.py`'s converse-path pins are rewritten**, in the same
  diff. The test that asserts the converse and inspection paths pin the same
  thing becomes two: the converse call carries **no** guardrail, and every
  inspection site pins a published version of the guardrail its channel names.
- **`channels` gains a value.** `tool_request` joins `CHANNELS`
  (`core/guardrail.py`, pinned literally by `tests/test_contracts.py:659`).
  No probe declares it, and under ADR-040's subset rule a block on it credits
  nothing — correct, since the model arm sends no tools and produces no
  request. `quality/adversarial/` is untouched.

## Decision 4 — the `tool_request` policy is staged, and the stage-2 rule is written now

**Stage 1 (PR 2, measured in PR 4): identical coverage.** `tool_request` is
assessed with the main guardrail at `OUTPUT` — the policy and source `converse`
applies to it today. The mechanism moves and nothing else does, so PR 4's run
isolates B's own effect. **Pre-registered prediction:** the majority-refused
count on the tools arm at k=3 is unchanged within the guardrail's own
instability — 17 in M06b, 16/17/17 by sample, 16 on the k=1 wiring check — so
**14 to 20** is "unchanged"; outside that band is a finding about B itself and
stops the milestone at PR 4. What PR 4 adds is the **attribution**: every
refusal now names `tool_request` or `answer`, and the text behind each is in
PR 3's store.

**Stage 2 (PR 5): `tool_request` moves to the tool-output guardrail at
`INPUT`**, under this rule, written before PR 4 runs:

- **If at least half of PR 4's refused samples attribute to `tool_request`**, PR 5
  is built. The argument is ADR-063's on the mirror channel: a tool request is
  consumed by the plane and by the model, never by the viewer; the hazard in it
  is an instruction or an argument, which `PROMPT_ATTACK` (input-only by the
  service's design) is the instrument for; a topic policy over it asks whether
  the platform's own JSON is a viewer's intent. **Pre-registered prediction:**
  the majority-refused count falls inside SPEC/01's band, **0–2 of 25**.
  Falsifier: **3 or more** — the claim is measured false at the count, and the
  milestone closes red with the refused text as the evidence for what did fire.
- **If fewer than half attribute to `tool_request`**, PR 5 is **not built**.
  The refusals are on the final answer, this ADR's mechanism does not touch that
  channel, and no calibration is proposed. The milestone closes at PR 4, red,
  with the attribution and the text — which is what M06b's *What's next* asked
  M07 to prove: *that the platform can see what its own controls refuse.*

Either way `ATK-003`'s disposition lands in PR 4 (Decision 6), because it must
not wait on a PR that may not be built.

## Decision 5 — G1 and G4, intact, and how each is checked

**G1.** `bedrock:InvokeModel` stays on the gateway role and nowhere else;
`converse` without `guardrailConfig` is still the gateway calling the model.
No harness gains a model call: PR 4 and PR 5 run `run_with_tools.py` and
`run_probes_via_gateway.py` through the deployed gateway, and every corpus
measurement is `ApplyGuardrail`, which `MODEL_INVOKE_ACTIONS` excludes.
`tests/test_iam_assertions.py` and the synth snapshot are untouched by PR 2; if
PR 3's store needs a bucket, that is a two-key stack change under ADR-071 and
adds no model action.

**G4.** A probe passes when the guardrail blocked or a policy denied *and a
record exists*. Under B the record is still written by the gateway from the
guardrail's assessment (`interpret_apply`), with `mechanism: guardrail`,
`assessed` and `channels`; the scorer still reads the lake through
`observation_from_record`, which does not change in PR 2 and copies no text in
PR 3. The refused text never enters the record, the answer file, the refusals
sidecar or any `evals/` reader. The four routes ADR-069 named are closed as
tests in PR 3. A scorer that could read the text is refused, in the words of
ADR-064.

## Decision 6 — `ATK-003` at its deadline

`ATK-003` is a viewer's question at `source=INPUT`, allowed by v4 (ADR-062).
Nothing in this ADR moves it: `question` is assessed by the same policy at the
same source, and the frozen corpus at `INPUT` was identical across every arm
ADR-064 measured. It cannot be closed here without a topic wording change, and
both wordings tested regressed attacks. So at M07 it is **dispositioned, not
extended by a checklist edit**, in PR 4, after step 6b re-measures it on the
deployed guardrail:

- **Accepted as a scale cut**, in ADR-062's own words — *"the act is a sequence
  of legitimate transactions, which is not a thing a content filter can see and
  never was; at scale, replace with a subscription-abuse control at the billing
  boundary"* — with Security and AI Quality attesting in the PR body and an
  amendment to ADR-062; the row keeps `expect: blocked` and keeps failing, so the
  hole stays visible; or
- **Extended**, with the same two keys, a new date, and the amendment.

The spec does not choose. *An extension nobody signed is an acceptance*
(ADR-035 amendment 4), and this ADR will not be the one that signs it silently.

## What this ADR does not decide

- **Any topic wording, example, or `outputAction`.** Refused twice on
  measurement; not a third time.
- **Any golden case, baseline, threshold, or history entry.** Whether M07's run
  is admissible is AI Quality's and Security's at PR 6, and ADR-069 D5 cut 1
  (derivability of `refused`/`answered`) binds the moment it is.
- **`catalog-search`'s browse gap.** Owed to the Tool Owner, and deliberately
  not fixed here: many survivors survive because retrieval returns nothing, so a
  working search would produce more answers for the topic to refuse and make
  the M07 count *worse* while the control is being measured.
- **The DMA rename SPEC/06b A21 deferred to M07.** Re-dated to the SPEC/08 PR,
  with the reason: it touches `data/catalog.json`, which every M07 number is
  measured against and which feeds the judge's `prompt_sha256`; renaming markets
  mid-measurement would make M07's comparison to M06b unattributable. This is a
  re-dating and it is written down so it is not a slide.

## Consequences

- The progression table gains a row and the roadmap is one milestone longer.
- `converse` carries no guardrail; the gateway carries four channel-keyed
  assessments; the audit record's `channels` vocabulary gains `tool_request`.
- Two runs of the tools arm at k=3 through the deployed gateway, both
  committed as-run, plus the probe corpus twice and the step-6b corpora twice.
  Roughly 210 model calls, all through the gateway, well under two dollars at
  Haiku rates; and `ApplyGuardrail` calls that cost nothing the meter counts.
- **At scale, replace with a guardrail service the gateway calls per channel
  from a channel-keyed policy table, and a refused-content store behind its own
  IAM boundary that the audit lake never references; the interface already
  matches** — `inspect(text, channel=...)` is already the one call, the policy
  is already selected by channel, and the store is already keyed by
  `record_id`.
