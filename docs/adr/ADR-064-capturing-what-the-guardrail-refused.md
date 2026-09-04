# ADR-064: capturing what the guardrail refused

**Status: PROPOSED. Not accepted, nothing built, nothing deployed.**
Written before the code, as ADR-063 was, and for the same reason: the last two
cheap fixes for this topic were both refuted by measurement, and one of them
would have shipped a security regression. **Zero model calls to write.**

**Seats it would need:** Security / Red Team (G4 is the constraint, and the
constraint is the whole difficulty) · Platform Engineering (the gateway and the
harness) · AI Quality (what a diagnostic may and may not enter).

## Why this is the remaining blocker

ADR-063 closed the tool-output half of the `entitlement-circumvention` false
positive: 8 refusal-samples to 0, verified on the deployed gateway
(`docs/M06b-wiring-verified.md`). The suite still scores 1/25, because the other
half — 16 of 25 cases refused on the **answer** channel — is untouched.

Nobody can see the text those answers were refused for. The audit record carries
`assessed`, `channels`, `action` and `usage`, and no content. That omission is
deliberate and mostly right: G4 exists so a probe cannot pass because the answer
looked polite, and `evals/adversarial.py` says in its own docstring that it
"cannot see the model's text at all". **Calibrating a filter whose decisions
nobody can inspect is guessing**, and this milestone has now spent two rounds
proving that guessing does not work.

## Two corrections to the diagnosis this proposal rests on

### 1. Two of the three "committed answers pass v4" figures were circular

`docs/M06b-guardrail-diagnosis.md` argues the answer-channel blocks are not
reproducible from committed text, citing M01 **0/22**, M02-tools **0/23**, M06
**0/25**. Counted properly:

```
milestones/M01/goldens-run.json        25 cases,  3 refused,  22 answers
milestones/M02/runs/m02-tools-1.json   25 cases,  2 refused,  23 answers
milestones/M06/goldens-run-1.json      25 cases,  0 refused,  25 answers
```

A refused case writes no answer. So the 22 and the 23 are **exactly the
survivors**, and testing them asked whether the cases that passed would pass.
Only M06's is a real datum, because that arm refused nothing — and it is the
**control** arm, with no tools.

This is the same circularity already caught once in that document, about M06b's
own answers, and struck there. It was not applied to the other two rows. **A
correction that fixes one instance and leaves its siblings standing is half a
correction**, and this is the second time on this branch that a measurement of
survivors was read as a measurement of the population.

The corrected claim is weaker and still supports the conclusion: **there is no
committed text for any answer-channel block, on any arm.** Not "the text passes"
— the text is absent.

### 2. The cases that pass are mostly passing for the wrong reason

Read the surviving answers from the wiring check rather than their verdicts:

```
entitlement-012  "The Harbor Bay Invitational is not available in the ... catalog"
recommend-014    "I'm unable to find any available content in the ... catalog"
grounded-019     "I was unable to find the Harbor Bay Invitational ..."
```

`cited_titles: []`, `entitlement: null`. **These cases are not blocked because
the model had nothing to say about entitlement.** Retrieval returned nothing, so
no verdict was stated, so the topic never fired.

That inverts the apparent pattern. It is not that 11 of the 12 cases carrying an
`entitlement` assert are blocked because the assert is hostile; it is that a case
which successfully retrieves a title goes on to state a verdict, and **stating
the verdict is what trips the topic**. The survivors survive by failing earlier.

## A separate defect found on the way, recorded and not fixed

`catalog-search` matches literal terms over `('title', 'event')` with
`MIN_TERM_LENGTH = 4`. Measured against the committed catalog:

```
query='derby'              -> 1 result
query='rowing'             -> 1 result
query='sports'             -> 0 results
query='game'               -> 0 results
query='match'              -> 0 results
query='highlights tonight' -> 0 results
```

`recommend-014` — *"Anything worth watching?"* — issued **six** searches
(`highlights tonight`, `highlights`, `sports`, `game`, `match`) and found
nothing, then answered *"I'm unable to find any available content."* The catalog
has five titles. **The tool has no browse affordance, and the model's honest
response to that is a false statement about the catalog.**

Not this ADR's to fix, and not obviously a defect rather than a scale cut — but
it is currently *hiding* answer-channel blocks by preventing the answers that
would trip them, which makes it a confound for any calibration measured on this
suite. Owed to the Tool Owner seat.

## The options for capture

### A. A diagnostic arm that generates without the guardrail, then applies it offline

Call `converse` with no `guardrailConfig`, capture the raw output, hand it to
`ApplyGuardrail` — exactly how `topic_baseline.py` separates channels today.

- **Gives the text directly**, and the offline application says which topic fired
  on which span.
- **Requires a model call with no guardrail attached.** Through the gateway that
  means an off-switch on the control, which is the shape
  `tests/test_handler_wiring.py` exists because of — a seat planted
  `untrusted = ()` and watched the suite stay green. **A `skip_guardrail` flag on
  the gateway is refused on sight.**
- Outside the gateway it means a second implementation of the tool loop, and a
  diagnostic that reproduces the loop approximately is measuring its own
  approximation.

### B. Move the answer channel to explicit `ApplyGuardrail`, as the tool-output channel already is

Stop passing `guardrailConfig` to `converse`; call `ApplyGuardrail` on the model's
output instead, and refuse there.

- **It is not a coincidence that the tool-output half was diagnosable and this
  half was not.** That channel goes through `handler._inspect`, where the
  platform holds the text and decides. This channel is decided inside Bedrock,
  and the gateway is told only the verdict.
- Unifies two mechanisms that currently do the same job differently — the
  confusion that made this problem take three rounds to isolate.
- **It moves the trust boundary**, and that is the real cost. Today Bedrock
  guarantees blocked text never reaches the gateway. Under B the gateway receives
  unapproved model output and must be trusted not to return it. That is a
  strictly weaker guarantee, and it is exactly the kind of trade G9 exists to
  price.

### C. Capture only the assessment, not the text

Record which topic fired against which *span offsets*, if Bedrock's trace carries
them, without storing content.

- **Load-bearing assumption, and it is unverified**: this ADR does not know
  whether the converse guardrail trace carries offsets or only policy names.
  `core/guardrail.py` reads names and nothing else, so the repo has never looked.
  **Verifying this is step 0** and it is cheap.
- If offsets exist, this is the cheapest option by a wide margin and touches no
  trust boundary.

### D. Accept it and record M06b as blocked

Honest, and the correct answer if A–C all price badly. It costs the milestone its
close and leaves a documented, isolated defect for M07.

## Recommended sequence, cheapest first

1. **Step 0, free: find out what the trace actually carries.** One blocked turn,
   trace dumped. If it carries spans, take option C and stop. Nothing here should
   be designed before that is known, and this ADR deliberately does not choose
   between A, B and C without it.
2. If C is unavailable, **price B properly** — it is the architecturally right
   answer and the expensive one, and it needs its own ADR with the trust-boundary
   argument made explicitly rather than inside this list.
3. **A is refused in its gateway form** and only conditionally available in its
   standalone form.
4. **D stays available throughout**, and is not a failure.

## What this proposal does not do

- **It does not choose an option.** Step 0 decides between them and step 0 has
  not been run.
- **It does not weaken G4.** Whatever is captured must be unreachable by
  `evals/adversarial.py` and by the deterministic scorer. The existing pattern is
  `run_probes_via_gateway.py`'s `model_text`: evidence for the journal, carried
  in the observation file, structurally out of the scorer's reach. Any capture
  here inherits that shape or is refused.
- **It does not fix `catalog-search`**, and it names that as a confound for any
  calibration measured on this suite.
- **It does not re-open ADR-063**, which closed the half it claimed and was
  verified on the deployed gateway.
