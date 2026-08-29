# ADR-050: the assertions enforcing "only with an ADR" were on a rule that required neither Security nor an ADR

**Status:** Proposed. **Zero model calls.**
**Seats:** Security (the control these assertions guard) · AI Quality and
Platform Engineering (the rule they used to sit on)

`pave/twokey.py` says of the adversarial corpus:

```
"the adversarial corpus — only Security may downgrade a probe, and only with an ADR"
```

Eight assertions make that sentence true. Until this change all eight lived in
`tests/test_contracts.py`, whose rule is:

```
^tests/(test_contracts|test_calibration_corpus|test_judge)\.py$   ai-quality, platform-eng   requires_adr=False
```

**No Security key, and no ADR.** Two of the eight say otherwise in their own
docstrings:

- `test_no_probe_can_pass_on_model_behaviour` — *"Adding a value to
  `G4_PASS_SEMANTICS` is a Security-seat change and needs an ADR."*
- `test_every_probe_is_blocking_unless_an_adr_downgrades_it` — *"Only the Security
  seat may downgrade a probe to advisory, and only with an ADR."*

A protection **stated and absent** is worse than one that is missing, because it
stops anyone looking for the real one. ADR-035 found the thermometer guarded twice
and the thermostat not. ADR-037 found three second keys written in the one file
that provably cannot collect them. This is that shape a third time, and it landed
on G4 — the invariant CLAUDE.md names as the one most often violated by
well-meaning changes.

## Decision — the eight assertions get a file, and the file gets a rule

`tests/test_adversarial_contracts.py`, on a rule of its own:

```
^tests/test_adversarial_contracts\.py$   security, ai-quality, platform-eng   requires_adr=True
```

## What was actually open, which is not what it first looked like

The finding was reported as *"Security is not on the file that enforces Security's
own rule."* That half was **not** the hole. A counterweight is supposed to exclude
the seat it counterweights, and the downgrade already cost three seats:

```
downgrade one probe to advisory:  16 failed
   tests/test_adversarial_entry.py   15    (ai-quality, platform-eng, security)
   tests/test_contracts.py            1    (ai-quality, platform-eng)
```

`tests/test_adversarial_entry.py` **is** Security-keyed and does not fold on
Security's key — re-seating `probes_sha256` across all five instruments made it
worse, not better (`18 failed`), so the fifteen are not clearable by their owner.

**The open route was the other direction.** `ai-quality` and `platform-eng` could
delete the tripwire in one PR, without Security, with no ADR; a later Security PR
could do the downgrade. No seat ever had to justify the combination. Measured
across the two modules:

```
the guard alone, on main   (tests/test_contracts.py)             ai-quality, platform-eng    adr=False
the guard alone, here      (tests/test_adversarial_contracts.py) ai-quality, platform-eng,
                                                                 security                    adr=True
```

Three seats closes it in both directions: the seat that would like a probe
downgraded cannot weaken the guard alone, and the two seats that do not feel that
control's pain cannot quietly remove the instrument without the seat that does.

## Why the split, rather than adding Security to the existing rule

Measured, before choosing:

```
tests in tests/test_contracts.py:               47
   about probes / adversarial / G4:              8
   about everything else:                       39
commits touching the file:                      13
   of those, also touching quality/adversarial/: 2
```

Adding `security` to `^tests/(test_contracts|test_calibration_corpus|test_judge)\.py$`
would hand Security a key over 39 assertions it has no stake in — the registry,
the manifest, Cedar, the golden suite, the CODEOWNERS agreement test. That dilutes
G9 rather than enforcing it: a seat with keys everywhere is a seat whose key means
nothing in particular.

The underlying defect is that the rule bundles three files with nothing in common,
so its scope was drawn by convenience and these eight were carried along. The fix
is a rule whose scope is a subject. **At scale, replace with: one rule per control
surface, generated from the seat table rather than hand-maintained; the interface
already matches — `RULES` is a tuple of `(what, pattern, seats, requires_adr)`.**

The remaining bundle is not repaired here. `test_calibration_corpus` and
`test_judge` still share a pattern with `test_contracts`, and whether that is one
subject or three is AI Quality's call, not this ADR's.

## What this ADR does not do

- It does not add a CODEOWNERS line. `test_every_second_codeowners_handle_has_a_rule_that_can_collect_it`
  is one-directional on purpose and says why: a second handle there collects
  nothing on a one-operator repo (ADR-013), so writing one would be decoration.
- It does not move `tests/test_adversarial_entry.py`, `test_adversarial_scoring.py`
  or `test_adversarial_lane.py`, which already carry Security.
- It does not change any probe, any severity, or `G4_PASS_SEMANTICS` itself. The
  corpus on disk is byte-identical.

## Consequences

A change to the adversarial corpus's contracts now costs three dispositions and a
written decision. That is the cost this repo already believed it was paying.

`test_g4s_semantics_allowlist_lives_wherever_securitys_key_reaches` is written
against the **constant**, not the filename, so moving `G4_PASS_SEMANTICS` back
into a file on a weaker rule fails rather than silently restoring the gap. Its
first draft matched itself — the search string is an occurrence of what it
searches for — and demanded a Security key on the file doing the asking; it is
anchored at column 0 now.
