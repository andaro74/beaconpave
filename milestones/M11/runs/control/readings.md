# M11 PR 3: the control run, and its readings

**Taken once, in the same fresh clone as the seeded run**, at clean HEAD C =
`ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93`, which is S = `10283eb` plus the committed seeded
artifact and its readings. This is the delta drill without the fix: the fixture's bytes are the
seeded run's.

**The shell** is the one `milestones/M11/runs/seeded/readings.md` describes: Git Bash,
`PYTHONIOENCODING=utf-8`, and `BEACONPAVE_DRILL_KEY` exported from
`$(cat ~/.beaconpave/m11-drill-key.txt)`. The key's value is printed nowhere below.

## Readings

| reading | registered expectation | read | verdict |
|---|---|---|---|
| the run's exit | `pave drill` exit 1, NO-GO written | exit 1 | as expected |
| **control validity:** `drill verify` | exit 0 | exit 0, `signature: OK` | **holds** |
| **control validity:** `mode` | `delta` | `mode=delta` | **holds** |
| **control validity:** `prior_sha256` | equals `sha256sum R1` | `96cb3c3c…f0f4bb62` both | **holds** |
| **control validity:** `caption_sha256` | equals seeded's | `1449d4db…a3c0d3de` both | **holds** |
| **control validity:** C ≠ S | differ | `ce7b00f` ≠ `10283eb` | **holds** |
| **control validity:** `git diff --name-only S C` | lies under `milestones/M11/` | `milestones/M11/runs/seeded/go-no-go.json`, `milestones/M11/runs/seeded/readings.md` | **holds** |
| **F2**, control half | `owner.seat=service-team`, `owner.oncall=webhook:player-captions`, `fix_window_s=129600` | all three equal | **does not fire** |
| **F4** | `decision=NO-GO`, and `finding` lines equal to seeded's | `decision=NO-GO`; `finding=caption-check/max-gap/c006/c008` on both; `diff` of the two sets exits 0, empty | **does not fire** |

The all-three row (`tree_clean`, `caption_sha256` against the blob at C, ancestry) is read
in `milestones/M11/runs/validity.md`. `tree_clean=true` is in the `drill read` output below.

## The transcript

The script that produced it is `control.sh`, run once. Its output is below, unedited.

```text
## Before the run

$ git rev-parse HEAD
ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
exit 0

$ git status --porcelain
exit 0

$ git ls-files -v | cut -c1 | sort | uniq -c
    802 H
exit 0

$ python -c "import pave.drill, pave.drill_read; print(pave.drill.__file__); print(pave.drill_read.__file__)"
C:\Users\andar\AppData\Local\Temp\claude\c--Users-andar-code-beaconpave\22afb63c-c89b-4385-a31d-89553d920b2b\scratchpad\m11pr3\bp\pave\drill.py
C:\Users\andar\AppData\Local\Temp\claude\c--Users-andar-code-beaconpave\22afb63c-c89b-4385-a31d-89553d920b2b\scratchpad\m11pr3\bp\pave\drill_read.py
exit 0

## The control run

$ python -m pave.cli drill --event jefferson-derby --tier 3 --delta milestones/M11/runs/seeded/go-no-go.json --out milestones/M11/runs/control/go-no-go.json
  finding: caption-check/max-gap gap 5.000 s between c006 and c008
drill: NO-GO - owner service-team (webhook:player-captions), fix by 2026-09-16T02:05:47Z; written milestones/M11/runs/control/go-no-go.json
exit 1

## drill read

$ python -m pave.cli drill read milestones/M11/runs/control/go-no-go.json
decision=NO-GO
mode=delta
commit=ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
tree_clean=true
ran_at=2026-09-14T14:05:47Z
fix_by=2026-09-16T02:05:47Z
fix_window_s=129600
owner.seat=service-team
owner.oncall=webhook:player-captions
caption_sha256=1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de
prior_sha256=96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62
finding=caption-check/max-gap/c006/c008
exit 0

## drill verify (control validity clause)

$ python -m pave.cli drill verify milestones/M11/runs/control/go-no-go.json
signature: OK
schema: OK
exit 0

## F2: owner and window, control half

$ python -m pave.cli drill read milestones/M11/runs/control/go-no-go.json | grep -E '^(owner\.seat|owner\.oncall|fix_window_s)='
fix_window_s=129600
owner.seat=service-team
owner.oncall=webhook:player-captions
exit 0

## F4: decision, and the finding lines beside seeded's

$ python -m pave.cli drill read milestones/M11/runs/control/go-no-go.json | grep -E '^decision='
decision=NO-GO
exit 0

$ python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json | grep -E '^finding='
finding=caption-check/max-gap/c006/c008
exit 0

$ python -m pave.cli drill read milestones/M11/runs/control/go-no-go.json | grep -E '^finding='
finding=caption-check/max-gap/c006/c008
exit 0

$ diff <(python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json | grep -E '^finding=') <(python -m pave.cli drill read milestones/M11/runs/control/go-no-go.json | grep -E '^finding=')
exit 0

## Control validity row

$ python -m pave.cli drill read milestones/M11/runs/control/go-no-go.json | grep -E '^(mode|commit|prior_sha256|caption_sha256)='
mode=delta
commit=ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
caption_sha256=1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de
prior_sha256=96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62
exit 0

$ sha256sum milestones/M11/runs/seeded/go-no-go.json
96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62 *milestones/M11/runs/seeded/go-no-go.json
exit 0

$ python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json | grep -E '^(commit|caption_sha256)='
commit=10283eb264ca7d436df60f373ca0bb860cd3f003
caption_sha256=1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de
exit 0

$ git diff --name-only 10283eb264ca7d436df60f373ca0bb860cd3f003 ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
milestones/M11/runs/seeded/go-no-go.json
milestones/M11/runs/seeded/readings.md
exit 0

## After the readings

$ sha256sum milestones/M11/runs/control/go-no-go.json
12211e3f89e86b7b2c4f00563d1b05dbdea52e527e6d25558779c06373a7971c *milestones/M11/runs/control/go-no-go.json
exit 0

$ git status --porcelain
?? milestones/M11/runs/control/
exit 0

```

## The script, `control.sh`, as it ran

```bash
# M11 PR 3: the control run and its readings. Run from the clone's root, once, at clean HEAD.
set -u
source ../show.sh
export PYTHONIOENCODING=utf-8
export BEACONPAVE_DRILL_KEY="$(cat ~/.beaconpave/m11-drill-key.txt)"
S=10283eb264ca7d436df60f373ca0bb860cd3f003
R1=milestones/M11/runs/seeded/go-no-go.json
R2=milestones/M11/runs/control/go-no-go.json

echo '## Before the run'
echo
run 'git rev-parse HEAD'
run 'git status --porcelain'
run 'git ls-files -v | cut -c1 | sort | uniq -c'
run 'python -c "import pave.drill, pave.drill_read; print(pave.drill.__file__); print(pave.drill_read.__file__)"'

echo '## The control run'
echo
run "python -m pave.cli drill --event jefferson-derby --tier 3 --delta $R1 --out $R2"

echo '## drill read'
echo
run "python -m pave.cli drill read $R2"

echo '## drill verify (control validity clause)'
echo
run "python -m pave.cli drill verify $R2"

echo '## F2: owner and window, control half'
echo
run "python -m pave.cli drill read $R2 | grep -E '^(owner\.seat|owner\.oncall|fix_window_s)='"

echo '## F4: decision, and the finding lines beside seeded'"'"'s'
echo
run "python -m pave.cli drill read $R2 | grep -E '^decision='"
run "python -m pave.cli drill read $R1 | grep -E '^finding='"
run "python -m pave.cli drill read $R2 | grep -E '^finding='"
run "diff <(python -m pave.cli drill read $R1 | grep -E '^finding=') <(python -m pave.cli drill read $R2 | grep -E '^finding=')"

echo '## Control validity row'
echo
C=$(python -m pave.cli drill read "$R2" | sed -n 's/^commit=//p')
run "python -m pave.cli drill read $R2 | grep -E '^(mode|commit|prior_sha256|caption_sha256)='"
run "sha256sum $R1"
run "python -m pave.cli drill read $R1 | grep -E '^(commit|caption_sha256)='"
run "git diff --name-only $S $C"

echo '## After the readings'
echo
run "sha256sum $R2"
run 'git status --porcelain'
```
