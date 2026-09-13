# scenarios

One scenario exists: **`caption-check.json`**, claim 11's (`SPEC/11-drill-go-no-go.md`,
ADR-080). The blackout sweep and the alarm self-test that `BUILD.md` once named are cut
(ADR-080 decision 4).

The file carries the **claim values**: the event's caption source, the `max-gap`
threshold, the owner a NO-GO names, and the fix-by window per tier. `pave/drill.py`
reads them at run time and has **no default for any of them**: a missing one exits 2 and
writes nothing (SPEC/11 constraint 3).

**This directory is on two keys, AI Quality plus Platform Engineering** (`pave/twokey.py`).
The scenario is the thermostat: widening `max_gap_s` turns a NO-GO into a GO with every
other test green. The caption fixtures under `drill/fixtures/` are not on that rule. The
fix is the owning team's edit to its own captions.

```text
pave drill --event <event> --tier <tier> --out <path> [--delta <prior artifact>]
pave drill read   <artifact>     # print the fields every SPEC/11 falsifier reads
pave drill verify <artifact>     # check the signature, then the schema
```

Exit codes:
- `pave drill`: 0 GO written, 1 NO-GO written, 2 nothing written.
- `pave drill verify`: 0 `signature: OK`, 1 `signature: MISMATCH`, 2 unreadable or no key.

The key is `BEACONPAVE_DRILL_KEY`, at least 32 bytes, and is never committed before
M11's last reading.
