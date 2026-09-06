# ADR-071: where refused text goes, and why the record cannot name it

**Status: PROPOSED in M07 PR 3; ACCEPTED when that PR merges. Zero model
calls to write; nothing deployed.** ADR-070 decision 3 split the G4 sink out
of the redesign — *"the refused text goes to a store the audit record does not
point to and `observation_from_record` does not read"* — and dated the store,
its reader and ADR-069's four residual routes to this record and this PR.
Everything here is built against the pre-registration in SPEC/07's PR 3 row and
`What it builds`, and the one difference is in the last section.

**Seats:** Security / Red Team (G4's boundary moves with any capture) ·
Platform Engineering (the gateway, the stack, the reader) · AI Quality (what a
scorer may read — nothing here, asserted) · Data Governance (one question,
carried from ADR-070 amendment 3 and answered below).

## Context

Under option B the gateway holds, on every blocked turn, the text the
assessment refused: the model's output on `tool_request` or `answer`, the
serialised payload on `tool_output`, the viewer's turn on `question`. PR 2 made
that text travel under `TurnOutcome.refused` and nowhere else, described it in
the record as `withheld` — present, length, one-way digest — and wrote none of
it anywhere. M06b's *What's next* asked M07 to prove *that the platform can see
what its own controls refuse*. Seeing is reading the text. G4 says no scorer
may. Both are true of the design below.

## Decision 1 — the store: a second bucket, keyed by `record_id`, put-only

A second S3 bucket in `gateway-stack.ts`, `WithheldStore`: versioned,
block-public, SSL-enforced, `RETAIN`, its own `CfnOutput`
(`WithheldStoreBucket`), its name in the gateway's environment
(`WITHHELD_STORE_BUCKET`, read with **no default** — a gateway that cannot name
its store refuses to start rather than block silently and hold nothing). The
gateway role holds `grantPut` and nothing else on it: **the gateway writes what
it refused to return and cannot read it back.**

One object per block. **The key is the record's `record_id`, verbatim** — one
id, two buckets, no derivation a reader has to know. The body is the refused
text as UTF-8, `text/plain`: no JSON, no framing, no field a later reader could
grow into a second record. S3 metadata carries what the record already says —
channel, `assessed`, guardrail id and version, `sha256`, `chars`,
classification — so an object can be checked against its record without
reading the record, and no more than that.

`core/withheld.py`, pure, builds the put and checks the read-back:
`held_object(bucket, record, text)` refuses a text whose fingerprint differs
from the record's `withheld` (recomputed by `guardrail.fingerprint_text`, the
same function), refuses a record that is not `blocked`, and refuses an empty
bucket name; `verify(record, body, metadata)` names each way an object can fail
to describe its record — `missing`, digest, length, channel. A store object that
disagrees with its record is worse than a missing one, because it looks like
evidence.

## Decision 2 — why the record cannot name the store

The store points at the record. Nothing points at the store. That is not a
convention; it is three closed sets:

1. `core.audit.WITHHELD_FIELDS` is `{present, chars, sha256}` and
   `build_record` refuses a fourth key.
2. `audit.schema.json` sets `additionalProperties: false` on the fragment, on
   a two-key file.
3. `tests/test_g4_capture_boundary.py` plants every spelling of a pointer —
   `key`, `store`, `bucket`, `url`, `text` — and asserts each is refused, and
   walks a real blocked record for the store's vocabulary and finds none.

A reader goes record → store by the id it already holds. **`observation_from_record`
is byte-identical before and after this PR**, because `core/audit.py` is not
touched; the planted-text test runs a real turn through `run_turn` on each of
the four channels, builds the record the way the handler's pinned branch builds
it, and asserts the observation is the same as for a different text and as for
no `withheld` at all.

## Decision 3 — the write is best-effort and cannot fail a block

`handler._hold` runs **after** `_write`, so the store is keyed by an id the lake
has accepted and an object can never exist for a record that does not. Its put
is wrapped: a failure is printed to the function's log and the block is
returned as the block it is.

Why swallow, in a repository whose wiring test exists because a seat planted a
swallowed exception: the store is a diagnostic, not a control. If a store outage
raised, a correctly refused probe would score INFRA, and the store's
availability would move the adversarial score — the capture weakening G4, in
the one form ADR-064 named. `withheld_fingerprint` already makes this argument
about itself (*"a diagnostic that can raise would acquire the power to fail a
refusal that was otherwise correct"*). The lost write surfaces as `MISSING` in
the reader, which is the finding it should be. The swallow is pinned to exactly
that one put (`test_hold_puts_the_text_in_the_store_and_cannot_fail_the_block`),
and `test_no_handler_code_swallows_a_failed_inspection` still forbids one around
any assessment.

## Decision 4 — every channel is stored, the viewer's turn included

AI Quality's Q7, carried from ADR-070 amendment 3 as Data Governance's
question: a `question` block's `withheld` digests the viewer's own turn, which
is a lookup key into committed corpora, and under this ADR the store holds that
turn verbatim.

**One rule, no channel exemption.** An exemption for `question` is a default
that stores less than the record describes, and the record already carries
`request_id` and `probe_id`, which name the case outright — the digest adds no
linkability the record lacks. The viewer wrote the text; the platform already
held it in the transcript for the call; the object carries the record's
classification as metadata; and `sensitive` never reaches a model call (G5), so
never reaches the store. Recorded here as the author's answer for Data
Governance to overturn at PR 6; no seat is scheduled on this PR.

## Decision 5 — `tool.id` carrying model text (Tool Owner TO-5)

The record's `tool.id` is *"the registry tool id, or the id that was attempted
and is not in the registry"* — model-authored text, verbatim, when the model
asks for a tool that does not exist. After PR 2's S-2 the name is serialised
into the `tool_request` assessment, so **a name that reaches a tool record has
passed the guardrail** on that channel before the plane saw it — the same class
as `tool.args` on an allowed call (TO-6): assessed text, not refused text.
A name the guardrail refuses never reaches the plane: the loop returns
`BLOCKED` before `authorize`, writes no tool record, appends nothing to the
transcript, and the name travels under `outcome.refused` and from there only to
the store. `tests/test_tool_loop.py::
test_a_request_the_guardrail_refuses_leaves_its_name_in_no_record` pins it.

**Decision: `tool.id` unchanged.** Replacing an unregistered name with a digest
would make a denial unreconstructable (*"a refusal nobody can account for is
indistinguishable from a bug"*, the schema's own words) to protect text that
was assessed.

## Decision 6 — the reader

`services/highlights-agent/read_withheld.py` is amended, not replaced, and
stays the one reader. For every refused case in an answers file it fetches the
record from the lake, the object from the store under the record's id, and asks
`verify`. **A digest that differs from the placeholder is now the expected
case**: `HELD` (object found, describes the record), `MISSING` (a lost
best-effort write), `MISMATCH` (an object that disagrees with its record, with
the defects named), and `PLACEHOLDER` — the digest of the deployed guardrail's
own `blockedOutputsMessaging`, which under option B the gateway never receives,
so a record carrying it was written by a gateway that predates ADR-070 and the
run is not a reading of this gateway. The placeholder is still fetched from the
deployed guardrail rather than typed, for ADR-018's reason.

`--show` prints the text. `--out` writes the verification and the texts, for
the journal and PR 4's attribution. **That file is evidence for people.** The
reader refuses an `--out` under `evals/` or under a name a scorer's loader reads
(`goldens-run*`, `*-refusals.json`, `probes-run.json`), and its `_what_this_is`
says no scorer reads it. Where PR 4 commits it is PR 4's; the constraint is
this paragraph.

## Decision 7 — the boundary, as tests, and ADR-069's four residual routes

SPEC/07's PR 3 row: *a planted text leaves `observation_from_record`'s output
unchanged; no reader under `evals/` or `pave/`.* Both are in
`tests/test_g4_capture_boundary.py`, which joins `core/audit.py`'s two-key rule
in this diff (Platform Engineering, Security) — the doorway and the test that
plants through it are weakened together or not at all.

- **The plant, through the real path**, on all four channels, as decision 2
  describes. Mutation: `observation_from_record` copying `withheld` — red on
  every channel.
- **No reader.** Every module under `evals/`, `pave/` and `tools/` is parsed,
  and none may import the store module or its reader, name the bucket's output
  or environment variable, name the pure module's functions, or subscript the
  `withheld` record key. Fail-closed: a module that can *name* the store can
  read it one line later. And the store's importers across the repository are
  exactly two, the handler and the reader.

ADR-069 decision 5 named five routes from the goldens partition into an
adversarial verdict. **Route (2), scoring time through `score_one`, was closed
in M06d PR 2 by `tests/test_adversarial_scoring.py::
test_the_goldens_partition_keys_do_not_move_a_probe_verdict`.** The other four,
dated to M07, close here, each as a test that fails on the mechanism:

| route | closed by | red on |
|---|---|---|
| (1) `evals/adversarial.py` opening a goldens answer file | every way of opening a file raises while the whole scoring workload runs; and the module's only file reads are `instrument_digests` and `_policy_mechanisms` | a read in `score_probe` |
| (3) a `refused` key reaching `adv.tally` | `ProbeResult`'s fields pinned literally; `tally` reads only those attributes and no subscript; tally and results identical with and without the partition keys | a field populated from the observation |
| (4) a helper in `evals/deterministic.py` | the scorer's only `evals` import is `FAIL, INFRA, PASS` from that module, each a `str` | a function crossing the import |
| (5) capture time, `observation_from_record` | the plant above | the doorway copying the fragment |

## What this ADR does not decide

- **Retention.** Nothing expires from the store. At scale a refused-content
  store carries a retention policy and an access log; the interface already
  matches — the bucket is its own resource with its own grant.
- **Where PR 4 commits the reader's `--out`.** Constrained, not chosen.
- **Any digest.** `core/withheld.py` is in no instrument digest, deliberately:
  the store is not something a scorer reads, so it is not part of what read a
  run. `capture_sha256` and `guardrail_sha256` are byte-identical to `m04-H`'s.

## Consequences

- The gateway's environment gains one variable and its role one put grant; the
  synth snapshot is re-recorded; G1's assertions are unchanged and green.
- `handler.py` gains `_hold` and `WITHHELD_STORE`; the wiring pins that went red
  on them (`MODULE_FUNCTIONS`, `MODULE_NAMES`, the blocked branch's `refused`
  reader) were widened by exactly those names, and four new pins say what the
  store write is, where it sits, and that the store is not the lake.
- **At scale, replace with a refused-content service behind its own IAM
  boundary and retention, that the audit lake never references; the interface
  already matches** — `held_object` and `verify` are the write and the
  read-back check, keyed by the record id the lake already issues.

## Where this differs from what was pre-registered

ADR-070 decision 3 listed `core/audit.py (PR 3)` under `capture_sha256`. PR 3
does not touch it: the store's pure code is `core/withheld.py`, on the gateway
decision-path rule, and the doorway is byte-identical — which is the stronger
form of the boundary argument. No digest moves, `m04-H` stays the current
instrument, and nothing is registered. Recorded in ADR-070 amendment 4.
