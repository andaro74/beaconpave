# The tool-output channel gets its own guardrail policy

Builds ADR-063, which was proposed, then verified against its own falsifiers,
then approved. **Nothing is deployed** — `cdk deploy` has not run.

## What it does

A second guardrail, `beaconpave-tool-output`: the gateway guardrail's policy with
`topicPolicyConfig` omitted, applied by `handler._inspect` to the tool-output
channel only. The model call still transits the guardrail with topics on it.

The measurement that justifies it, taken before the build on real tool payloads
at `k=5`:

```
                                    v4 today   topic-free policy
poisoned catalog-search output       5/5        5/5   ['PROMPT_ATTACK']
schema-valid hostile tool payload    5/5        5/5   ['PROMPT_ATTACK']
entitlement-check "entitled: true"   5/5        0/5
catalog-search normal output         0/5        0/5
```

**The topic was redundant on exactly the cases it was kept for.**
`PROMPT_ATTACK` already caught both injections; removing the topic loses no
protection on either and stops the tool's approvals being refused.

## Row 6, on the synth

```
guardrails: ['Guardrail', 'ToolOutputGuardrail']
  Guardrail            topics=True   filters=6
  ToolOutputGuardrail  topics=False  filters=6
existing Guardrail properties identical: True
resources ADDED: ['ToolOutputGuardrail', 'ToolOutputGuardrailVersion']  REMOVED: []
```

Corroborated independently by the pin file: the main pair's digests are unchanged
at policy ea66d6da36fe / description 71d7e4767fa3, computed from the snapshot by a
test that reads no TypeScript.

## Two defects this build found in the guards themselves

**A pin check that asserted there was one guardrail.**
`test_guardrail_pin_tracks_policy.py` took "the only guardrail" and would have
passed for the main pair while the new pair's pin tracked nothing — that file's
own subject, one layer out. Both pairs are pinned now, and a new test refuses a
third guardrail that nothing digests.

**A test that compared two paths and inspected one.**
`test_the_converse_path_and_the_inspection_path_pin_the_same_thing` looked for
`guardrailConfig` as a keyword of `converse(...)`. The handler builds
`kwargs = dict(..., guardrailConfig={...})` and calls `converse(**kwargs)`, so the
keyword was never there and the converse set was **always empty**. It has been
that way since the file was written; ADR-063 only made it visible by splitting the
inspection path. Now located by shape.

**And one in my own first attempt.** Binding `identifier, version` to locals
worked and silently defeated `test_handler_wiring.py`, which parses the handler
rather than importing it (G8) and can only see a pin at the call site. Two
explicit call sites now.

## Guards audited by planting — three for three

| plant | caught by |
|---|---|
| `converse` pins the tool-output version | `…pin_the_same_thing` |
| `apply_guardrail` uses a `"DRAFT"` literal | `…same_pinned_version_as_the_turn` |
| the guardrails differ by `blockedInputMessaging` | `…differ_only_by_the_topic_policy` |

## Fails closed

`TOOL_OUTPUT_GUARDRAIL_ID`/`_VERSION` read **with** a default, unlike every other
guardrail variable. Absent, both channels use the main guardrail — the
pre-ADR-063 behaviour. A missing id means *the older, stricter policy*; a missing
`GUARDRAIL_VERSION` would mean *no pin*. Opposite failures, opposite defaults.
Half a pair raises at cold start.

## Still owed, and stated because none of it is covered above

- **Deploy, then re-run rows 1–3 against the real gateway.** Rows 1–5 verified the
  *policy*; row 6 the *synthesised stack*. **Neither verifies the wiring** — that
  the gateway routes tool output to the new policy and everything else to the old.
  That is the claim with the worst failure mode and no measurement here touches it.
- **The instrument consequence.** A new guardrail version is an instrument
  (ADR-018). Every tool-output observation from here names a version the
  adversarial registry has no row for. AI Quality's, unsettled.
**Fixed here, having first been recorded as owed:** both guard files were on no
two-key rule while the controls they defend take two keys and an ADR. They now
join their own subjects' rules. That widening is what makes this a four-seat PR,
and the reasoning is in the attestation below.

## Counts

`main` at `ee47b66`: 2474 passed. This branch: **2483 passed, 6 skipped**.
`make check`: PASS. Zero model calls in the build; the pre-build verification
spent none either.

Two-Key-Disposition: security
Two-Key-Disposition: ai-quality
Two-Key-Disposition: platform-eng
Two-Key-Disposition: legal-sp
Two-Key-Rationale: Four seats, and the fourth is why this PR grew. `pave gate
  two-key` refused an earlier revision that put the new guardrail-composition
  tests in `tests/test_iam_assertions.py`: that triggered a SECOND ADR-requiring
  rule, and the checker's message is right — one decision record cannot stand for
  several controls. The tests were misplaced rather than under-documented. That
  file's rule is "G1's model-invoke allowlist and the assertions defending it",
  and these assert guardrail POLICY COMPOSITION, which is a different control.
  They moved to `tests/test_guardrail_pin_tracks_policy.py`, whose subject they
  actually are, and `tests/test_iam_assertions.py` is restored byte-identical to
  `main`. The fix was the move, not a second ADR written to satisfy a gate.
  .
  `pave/twokey.py` is edited here, which collects all four seats, and it closes a
  gap this PR itself recorded as owed: both guard files were on NO rule while the
  controls they defend take two keys and an ADR. They join their own subjects'
  rules, the way the adversarial scorer and its test already share one — weakened
  together or not at all. That is not incidental to this change: ADR-063 found
  that the pin test asserted there was exactly ONE guardrail, and that the handler
  wiring test's converse half had been inspecting nothing since it was written.
  Both were editable on one key.
  .
  Security's key is load-bearing because this REMOVES a policy from a channel. The
  justification is measured, not argued: the removed topic caught nothing
  PROMPT_ATTACK did not already catch, at k=5 on real payloads through the same
  API the gateway uses, and the frozen corpora are unmoved on the question channel
  because the main guardrail is byte-identical. AI Quality's is collected because a
  new guardrail version is an instrument (ADR-018) and every tool-output
  observation from here names it; that the adversarial registry owes it a row is
  recorded as OPEN, not decided. Platform Engineering owns the handler and the
  channel selection, which fails closed to the stricter policy when the new
  variables are absent. Legal/S&P is collected by the twokey rule and has nothing
  to refuse: no consequence class moves, no tool is deployed, claim 10 is
  untouched. No golden case, baseline, comparator, threshold or history entry
  moves, and NOTHING IS DEPLOYED by this diff.
