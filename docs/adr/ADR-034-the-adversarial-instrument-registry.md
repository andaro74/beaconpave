# ADR-034: `instrument.name` resolves in an adversarial registry

**Status:** Accepted (M04 follow-up, after the `m04-adversarial` entry, before a second one)
**Seats:** Security / Red Team (`quality/adversarial/` — two-key, and this ADR is
its price) · AI Quality (the history entry the name appears in)

## Context

ADR-027 rule 4 says a history entry's `instrument.name` is *"a foreign key to a
versioned instrument registry, and a row cannot be written naming an instrument
that does not exist."* For the judge that is true: `name` resolves in
`quality/judge/frozen.json`, and the `instruments` list there records every
instrument that has published a number.

**For the adversarial suite there was no table on the other side of the key.**
The recorder asked only whether a name had been *typed*:

```python
if not args.instrument_name:
    ...  # refuse
```

Measured by the AI Quality seat before the M04 entry was written:
`--instrument-name "an-instrument-that-does-not-exist"` records happily. The
refusal message even cites rule 4 by number — *"a row naming an instrument nobody
can look up is a fingerprint of an object that does not exist"* — and then checks
only non-emptiness. **A protection that is stated and absent is worse than one
that is missing, because it stops anyone looking for the real one.** That is
`pave/twokey.py`'s own comment, and M04 found the same fault four times inside the
milestone that diagnoses it.

It was left open at the tag deliberately. Closing it means creating a registry,
and where that registry lives decides which seat attests it — a decision, not a
cleanup.

## Decision

**A new file, `quality/adversarial/instruments.json`**, holding one row per named
adversarial instrument. `evals/run_adversarial.py --record` refuses a name that
does not resolve in it, and refuses a name that resolves but no longer describes
the tree.

### Why beside the corpus rather than in `frozen.json`

The single-registry argument is real, and it is the one ADR-033 used to reject a
second top-level `instrument` key: a reader asking *what read this run* should not
have to know which suite they are looking at before knowing where to look.

It loses here on ownership. `quality/judge/` is AI Quality's, and **what a probe
pass means is Security's** — `evals/adversarial.py`'s docstring says so, CODEOWNERS
routes it there, and ADR-030 gave Security a key on the comparator for the same
reason. `quality/adversarial/` is two-key with Security's key **and requires an
ADR**, so an adversarial instrument cannot be defined without the seat that owns
the definition and a written reason. Putting it in `frozen.json` would have let
Security's instrument be redefined under AI Quality's key alone.

`evals/comparators.json` was also considered and rejected: it already carries all
three seats, but it answers *what things score*, and this answers *what did the
scoring*. Merging them makes a single file where a reader cannot tell a
measurement from the instrument that produced it — which is the confusion
`instrument` was introduced to end.

### What a name identifies

**The code that read the run, and only that.** A name pins the six computed
digests: `scorer_sha256`, `semantics_sha256`, `probes_sha256`, `g4_cases_sha256`,
`classify_sha256`, `capture_sha256`.

`guardrail_version` and `guardrail_policy_sha256` are deliberately **not**
registered. They describe what *produced* the observations, not what scored them.
A later run under guardrail v3 is still read by this instrument, and pinning them
would force a new instrument name for a change that alters no scoring — which
would make the name track the environment instead of the code and destroy exactly
the comparison it exists to enable.

### A name is never edited

If any registered digest moves, that is a **different instrument**: register a new
name beside the old one and leave the old row standing. Editing digests in place
would silently redefine every published entry citing the name, which is ADR-018's
substitution with the sign reversed — there the enforced policy drifted from the
committed one, here the committed *description* would drift from what it
described.

The check therefore has two halves, and the second is the load-bearing one:
a name that resolves but no longer matches the tree is refused with the digest
that moved named, and the message says to register a new name rather than to fix
this one.

### Where the check lives, and why not beside the scorer

`check_instrument_name` is in `evals/run_adversarial.py`, **not** in
`evals/adversarial.py` — which is the natural home and the wrong one.
`evals/adversarial.py` is covered by `scorer_sha256`, the digest this function
exists to check. Adding it there would have moved that digest for a change that
alters how no probe is scored, and the first thing the new validator would have
reported is that `m04-A` no longer matches itself. **A validator that invalidates
the record it validates is the hazard running backwards.** Registry lookup is a
recording concern; scoring is not.

Verified rather than reasoned: no digest in the committed `m04-adversarial` entry
moved, so that entry still reproduces from this tree.

## Consequences

- `m04-A` is registered, with the digests the M04 entry recorded. The entry that
  was already published now resolves.
- Recording under a new name is a two-key act with Security's key **and** an ADR.
  That is the correct price for defining what read a published number, and it is
  the same price the G4 corpus pays for defining what a probe pass means.
- A tightening that changes the scorer, the semantics, the probe corpus, the G4
  corpus, `classify.py` or the capture path now needs a new instrument name. The
  owed `entitlement-circumvention` tightening does **not** — it changes the
  guardrail, which is not registered, so the resulting run is comparable to
  `m04-adversarial` under `m04-A`. That comparability is the whole point of
  keeping the guardrail out of the registry.
- Five tests, each verified against a planted defect: the recorder not consulting
  the registry, digest drift being ignored, and the registry drifting from the
  tree.

**At scale, replace with** a registry service keyed by content hash with the
instrument's full provenance graph — who changed it, under which review, and every
number published under it. The interface already matches: a name in, a set of
digests out, and an entry that cannot be written until the name resolves.
