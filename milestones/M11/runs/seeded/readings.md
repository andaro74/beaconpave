# M11 PR 3: the seeded run, and its readings

**Taken once, in a fresh clone of `m11-pr3-arc`** (ADR-080 amendment 4; cold review D19),
cloned from `origin` at B = `52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a` (`main`). The seed
commit, S = `10283eb264ca7d436df60f373ca0bb860cd3f003`, deletes cue `c007` from
`drill/fixtures/jefferson-derby/captions.vtt` and nothing else.

**The key.** Before anything else, the key file's sha256 was taken through
`pave.drill.load_key` on the bytes `$(cat ~/.beaconpave/m11-drill-key.txt)` yields: 64 bytes,
`cb16e839a08a5a747ed8764c4983ce8ce5190283806d5dc20fb8e29d373129b4`, equal to the first line
of `milestones/M11/pre-registration/key.sha256`. The key's value is printed nowhere below.

**The shell.** Git Bash, Python 3.14.3. Every command below ran from the clone's root after:

```text
export PYTHONIOENCODING=utf-8
export BEACONPAVE_DRILL_KEY="$(cat ~/.beaconpave/m11-drill-key.txt)"
```

Each command is printed as `$ command`, followed by its combined stdout and stderr and
`exit N`. F3's three copies were written to `../f3/`, a scratch directory outside the
repository, and are not committed.

## Readings, in SPEC/11's order

| reading | registered expectation | read | verdict |
|---|---|---|---|
| the run's exit | `pave drill` exit 1, NO-GO written | exit 1 | as expected |
| **seeded validity:** `drill verify` on R1 | exit 0, `signature: OK` | exit 0, `signature: OK` | **holds** |
| **seeded validity:** `signature.key_id` | the first 16 hex of `key.sha256` | `cb16e839a08a5a74` both | **holds** |
| **F3 liveness** | exit 0, `signature: OK`, not evidence | exit 0, `signature: OK` | live |
| **F1** | `decision=NO-GO`, findings exactly `caption-check/max-gap/c006/c008` | `decision=NO-GO`; one line, `finding=caption-check/max-gap/c006/c008` | **does not fire** |
| **F2**, seeded half | `owner.seat=service-team`, `owner.oncall=webhook:player-captions`, `fix_window_s=129600` | all three equal | **does not fire** |
| **F3**, copy 1: `decision` → `GO` | `cmp` differs; `verify` exit 1, `signature: MISMATCH` | `cmp` differs at line 8; exit 1, MISMATCH | refused |
| **F3**, copy 2: `owner.oncall` → `webhook:someone-else` | same | `cmp` differs at line 23; exit 1, MISMATCH | refused |
| **F3**, copy 3: `fix_by` year + 1 | same | `cmp` differs at line 25; exit 1, MISMATCH | refused |
| **F3** | fires on any copy not refused | all three refused | **does not fire** |

The seeded validity row's other clauses (`mode=full`, `git diff --name-only B S`) and the
all-three row are read in `milestones/M11/runs/validity.md`. `mode=full` and
`tree_clean=true` are in the `drill read` output below.

## The transcript

The script that produced it is `seeded.sh`, run once. Its output is below, unedited.

```text
## Before the run

$ git rev-parse HEAD
10283eb264ca7d436df60f373ca0bb860cd3f003
exit 0

$ git status --porcelain
exit 0

$ git ls-files -v | cut -c1 | sort | uniq -c
    800 H
exit 0

$ python -c "import pave.drill, pave.drill_read; print(pave.drill.__file__); print(pave.drill_read.__file__)"
C:\Users\andar\AppData\Local\Temp\claude\c--Users-andar-code-beaconpave\22afb63c-c89b-4385-a31d-89553d920b2b\scratchpad\m11pr3\bp\pave\drill.py
C:\Users\andar\AppData\Local\Temp\claude\c--Users-andar-code-beaconpave\22afb63c-c89b-4385-a31d-89553d920b2b\scratchpad\m11pr3\bp\pave\drill_read.py
exit 0

## The seeded run

$ python -m pave.cli drill --event jefferson-derby --tier 3 --out milestones/M11/runs/seeded/go-no-go.json
  finding: caption-check/max-gap gap 5.000 s between c006 and c008
drill: NO-GO - owner service-team (webhook:player-captions), fix by 2026-09-16T02:04:29Z; written milestones/M11/runs/seeded/go-no-go.json
exit 1

## drill read

$ python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json
decision=NO-GO
mode=full
commit=10283eb264ca7d436df60f373ca0bb860cd3f003
tree_clean=true
ran_at=2026-09-14T14:04:29Z
fix_by=2026-09-16T02:04:29Z
fix_window_s=129600
owner.seat=service-team
owner.oncall=webhook:player-captions
caption_sha256=1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de
prior_sha256=-
finding=caption-check/max-gap/c006/c008
exit 0

## drill verify on R1 (F3 liveness; seeded validity clause)

$ python -m pave.cli drill verify milestones/M11/runs/seeded/go-no-go.json
signature: OK
schema: OK
exit 0

## key_id against key.sha256 (seeded validity clause)

$ grep '"key_id"' milestones/M11/runs/seeded/go-no-go.json
    "key_id": "cb16e839a08a5a74",
exit 0

$ head -c 16 milestones/M11/pre-registration/key.sha256
cb16e839a08a5a74exit 0

## F1: decision and finding lines

$ python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json | grep -E '^(decision|finding)='
decision=NO-GO
finding=caption-check/max-gap/c006/c008
exit 0

## F2: owner and window

$ python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json | grep -E '^(owner\.seat|owner\.oncall|fix_window_s)='
fix_window_s=129600
owner.seat=service-team
owner.oncall=webhook:player-captions
exit 0

## F3: three sed copies in a scratch directory

$ sed 's/"decision": "NO-GO"/"decision": "GO"/' milestones/M11/runs/seeded/go-no-go.json > ../f3/decision.json
exit 0

$ cmp milestones/M11/runs/seeded/go-no-go.json ../f3/decision.json
milestones/M11/runs/seeded/go-no-go.json ../f3/decision.json differ: char 193, line 8
exit 1

$ diff milestones/M11/runs/seeded/go-no-go.json ../f3/decision.json
8c8
<   "decision": "NO-GO",
---
>   "decision": "GO",
exit 1

$ python -m pave.cli drill verify ../f3/decision.json
signature: MISMATCH
exit 1

$ sed 's/"oncall": "webhook:player-captions"/"oncall": "webhook:someone-else"/' milestones/M11/runs/seeded/go-no-go.json > ../f3/oncall.json
exit 0

$ cmp milestones/M11/runs/seeded/go-no-go.json ../f3/oncall.json
milestones/M11/runs/seeded/go-no-go.json ../f3/oncall.json differ: char 540, line 23
exit 1

$ diff milestones/M11/runs/seeded/go-no-go.json ../f3/oncall.json
23c23
<     "oncall": "webhook:player-captions"
---
>     "oncall": "webhook:someone-else"
exit 1

$ python -m pave.cli drill verify ../f3/oncall.json
signature: MISMATCH
exit 1

$ sed 's/"fix_by": "2026-/"fix_by": "2027-/' milestones/M11/runs/seeded/go-no-go.json > ../f3/fix_by.json
exit 0

$ cmp milestones/M11/runs/seeded/go-no-go.json ../f3/fix_by.json
milestones/M11/runs/seeded/go-no-go.json ../f3/fix_by.json differ: char 578, line 25
exit 1

$ diff milestones/M11/runs/seeded/go-no-go.json ../f3/fix_by.json
25c25
<   "fix_by": "2026-09-16T02:04:29Z",
---
>   "fix_by": "2027-09-16T02:04:29Z",
exit 1

$ python -m pave.cli drill verify ../f3/fix_by.json
signature: MISMATCH
exit 1

## After the readings

$ sha256sum milestones/M11/runs/seeded/go-no-go.json
96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62 *milestones/M11/runs/seeded/go-no-go.json
exit 0

$ git status --porcelain
?? milestones/M11/runs/
exit 0

```

## The script, `seeded.sh`, as it ran

```bash
# M11 PR 3: the seeded run and its readings. Run from the clone's root, once.
set -u
source ../show.sh
export PYTHONIOENCODING=utf-8
export BEACONPAVE_DRILL_KEY="$(cat ~/.beaconpave/m11-drill-key.txt)"
R1=milestones/M11/runs/seeded/go-no-go.json
KEYHASH=milestones/M11/pre-registration/key.sha256

echo '## Before the run'
echo
run 'git rev-parse HEAD'
run 'git status --porcelain'
run 'git ls-files -v | cut -c1 | sort | uniq -c'
run 'python -c "import pave.drill, pave.drill_read; print(pave.drill.__file__); print(pave.drill_read.__file__)"'

echo '## The seeded run'
echo
run "python -m pave.cli drill --event jefferson-derby --tier 3 --out $R1"

echo '## drill read'
echo
run "python -m pave.cli drill read $R1"

echo '## drill verify on R1 (F3 liveness; seeded validity clause)'
echo
run "python -m pave.cli drill verify $R1"
LIVE=$LAST_RC

echo '## key_id against key.sha256 (seeded validity clause)'
echo
run "grep '\"key_id\"' $R1"
run "head -c 16 $KEYHASH"

echo '## F1: decision and finding lines'
echo
run "python -m pave.cli drill read $R1 | grep -E '^(decision|finding)='"

echo '## F2: owner and window'
echo
run "python -m pave.cli drill read $R1 | grep -E '^(owner\.seat|owner\.oncall|fix_window_s)='"

echo '## F3: three sed copies in a scratch directory'
echo
if [ "$LIVE" -ne 0 ]; then
  echo "LIVENESS FAILED (exit $LIVE): the seeded run is INVALID and no copy is read."
  exit 0
fi
SC=../f3
rm -rf "$SC"; mkdir -p "$SC"
Y=$(sed -nE 's/^  "fix_by": "([0-9]{4})-.*/\1/p' "$R1")
run "sed 's/\"decision\": \"NO-GO\"/\"decision\": \"GO\"/' $R1 > $SC/decision.json"
run "cmp $R1 $SC/decision.json"
run "diff $R1 $SC/decision.json"
run "python -m pave.cli drill verify $SC/decision.json"

run "sed 's/\"oncall\": \"webhook:player-captions\"/\"oncall\": \"webhook:someone-else\"/' $R1 > $SC/oncall.json"
run "cmp $R1 $SC/oncall.json"
run "diff $R1 $SC/oncall.json"
run "python -m pave.cli drill verify $SC/oncall.json"

run "sed 's/\"fix_by\": \"$Y-/\"fix_by\": \"$((Y + 1))-/' $R1 > $SC/fix_by.json"
run "cmp $R1 $SC/fix_by.json"
run "diff $R1 $SC/fix_by.json"
run "python -m pave.cli drill verify $SC/fix_by.json"

echo '## After the readings'
echo
run "sha256sum $R1"
run 'git status --porcelain'
```

`show.sh`, sourced by it:

```bash
# Transcript helper for M11 PR 3's readings. Source it; never prints the key.
# run 'CMD' prints "$ CMD", runs it under pipefail, prints its combined output and "exit N".
# The exit code is also left in LAST_RC.
run() {
  printf '$ %s\n' "$1"
  ( set -o pipefail; eval "$1" ) 2>&1
  LAST_RC=$?
  printf 'exit %d\n\n' "$LAST_RC"
  return 0
}
```
