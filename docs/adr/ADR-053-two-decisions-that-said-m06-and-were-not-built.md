# ADR-053: two decisions said "closes in M06" and neither was built

**Status:** Proposed. **Zero model calls.**
**Seats:** Legal / S&P (the rule registry) · Security (the counterweight on both) ·
AI Quality (the judge freeze it currently holds alone) · Platform Engineering (the
rules list)

`milestones/M06/register-mapping.md` mapped all 26 register entries against `main`
and found **five** carrying an operator decision that says they close in M06, none
of them built. This closes two, and says plainly which halves it does not.

A decision recorded and not executed is the failure this register exists to catch:
to the next reader it is indistinguishable from a thing already handled, and it
stops them looking for the real one.

## A19 — the judge freeze, refrozen on one key (decision 6)

Drafts 5–8 recorded this as explicitly **not** an attack, and the reasoning was
sound as far as it went: `quality/judge/frozen.json` is defended three layers deep
by `held_out_guard()`, `matching_instrument()` and two position/name pins.

All three defences are real. All three live in `evals/judge.py`, which is **FREE**.
And attacking them is the *expensive* route — neutering `is_frozen()` is 2 failed.

**The cheap route satisfies the guards rather than attacking them:**

```
edit quality/judge/prompt.md, recompute through judge.instrument():
  prompt_sha256    ef8c1ec7... -> a59bb5d6...
  rendered_sha256  843e2ee6... -> a4d4ae4f...
keep the instrument name "B"; append the previous B as a retired row ALSO named "B"

a real retune          15 failed, 2064 passed   loud
this refreeze           1 failed, 2078 passed   then clean, on ONE key
```

You do not rename; you shadow. **Decision: `quality/judge/` gains `security` as a
second key.** Not a third seat, and not `ai-quality` — decision 6 constrains it by
G9 and round 10 settled it on the standard this document set: the counterweight is
the seat with a concrete object to check. Security reads instrument digests already.
The seat that owns the rubric cannot be the only key on the freeze that decides what
its scores mean.

## A14 — `rules/` is zero-key, and `enforced` switches off its own clock (decision 12)

`rules/` is the Legal/S&P seat's entire surface and was on no rule at all.

```
MER-AI-0001: proposed -> enforced, only control `no-control`   2079 passed, NO KEYS
```

`tests/test_contracts.py`'s guard reads `if effective and rule["status"] !=
"enforced"`, so **declaring a rule enforced switches off its own review clock**.

**Decision: `rules/` joins as `(legal-sp, security)`, with `requires_adr=True`.**
The seat set is decision 12's, not this ADR's. Round 11 refused `data-governance`
because it had been chosen off a census and *What M06 must not do* forbids a rule
derived from one; the standard is decision 6's. `rules/schema.json` types
`disposition.controls[].type` as an enum including `guardrail`, and Security already
reads deployed guardrail evidence, so it has something to read when a rule disposes
into one. The counterweight cannot be `legal-sp`, which owns the registry.

`requires_adr` is **on**, against the usual reasoning in this file, because a rule's
status is a published governance claim rather than a routine edit — and decision 12
asks for it by name.

### What this does NOT close, because decision 12 is explicit

- **No immortal rules.** `rules/schema.json` requires only `["type","ref"]` under
  `source`; **`effective` is optional**, and the review-by assertion is guarded
  `if effective:`. A rule that simply omits the field is never examined. Planted:
  `effective` deleted, `status: enforced`, `review_by: "2099-01-01"` — **2079
  passed**, a literally immortal enforced rule, green. Making `effective` required
  is a `rules/schema.json` change and Legal/S&P's call.
- **No orphan rules.** Owed to M07, and the term needs defining first: the schema's
  own `description` uses a different sense from the ref-resolution one, so M07 would
  otherwise be handed an obligation whose name means two things and close the cheap
  one.

## Legal/S&P joined the definition rule, and it was not a choice

Giving `rules/` a `requires_adr` rule handed Legal/S&P an ADR requirement, and
`test_the_definition_of_a_decision_record_carries_every_adr_rules_seats` went red on
exactly that — `assert not ['legal-sp']`. ADR-052 decision 2 states the property in
as many words: *a rule that gives a NEW seat an ADR requirement turns this red until
that seat can also defend what satisfying it means.*

So the rule over `pave/twokey.py` and the rest of the gate's definition surface goes
to `(ai-quality, legal-sp, platform-eng, security)`. **That seat set is an output of
a mechanism, not a preference expressed here** — which is the first time in this
repository that a seat has been added because a check demanded it rather than
because an ADR argued for it.

## A fixture that was a trap, made loud

`quality/judge/rubric-sports.md` was the canonical *"a rule naming one seat"* example
in eleven tests. Giving that rule a second key failed all eleven — correctly, and for
a reason none of them was about.

Replacing the literal eleven times would have left the same trap for the next seat
change. `ONE_SEAT_PATH` is a named constant with
`test_the_one_seat_fixture_still_names_one_seat` holding its premise. Measured: widen
the rule behind it and the failure is **that test, by name**, instead of eleven
obscure ones.

## The audit

```
drop `security` from quality/judge/                2 failed   CAUGHT
delete the rules/ rule                             3 failed   CAUGHT
drop requires_adr from rules/                      1 failed   CAUGHT
narrow ^rules/ to ^rules/schema\.json$             3 failed   CAUGHT
drop legal-sp from the definition rule             3 failed   CAUGHT
widen the one-seat fixture's rule                 14 failed   CAUGHT, named first
delete either plant                              184 passed   silent (a test deletion)
```

The two silences are test deletions, silent everywhere; both plants live in
`tests/test_twokey_seats.py`, which takes five seats.

**One methodology defect found while running this, and it is worth recording.** The
audit's first pass reported a **5 failed baseline** — the worktree had a staged index
from an earlier loop, and `git checkout -- .` restores from the index, not from HEAD,
so every "clean" iteration was restoring mutated files. `git reset --hard` is the
correct reset and the baseline is 185. An audit whose baseline is not verified
measures nothing, which is this milestone's most repeated lesson arriving in the
tooling rather than in a fix.

## Residuals

- **Three decided-not-built entries remain**: A5 (eleven interlock assertions to
  delete), A12 (`classify.py`'s rule), A18 (the G1 template fixture).
- **`evals/judge.py` is still FREE**, and it holds all three of the freeze's
  defences. This ADR keys what the defences *protect*, per decision 6; keying the
  defences themselves is not what decision 6 asked for and is not taken here.
- **A14's two other halves**, as stated above.

**At scale, replace with:** a policy service holding the rule registry, where a
status transition is an API call carrying its approver rather than a file edit
carrying an attestation; the registry is already typed records with a schema, and
the seat list here and the reviewer list there are the same list — the interface
already matches.
