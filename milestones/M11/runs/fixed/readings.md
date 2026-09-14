# M11 PR 3: the fix, the fixed run, and its readings

**Taken once, in the same fresh clone as the seeded and control runs.** The fix commit, F =
`a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70`, restores cue `c007` with
`git checkout B -- drill/fixtures/jefferson-derby/captions.vtt` and changes nothing else. Its
parent is `9592fdc`, which commits the control artifact and its readings onto C = `ce7b00f`.

**The shell** is the one `milestones/M11/runs/seeded/readings.md` describes: Git Bash,
`PYTHONIOENCODING=utf-8`, and `BEACONPAVE_DRILL_KEY` exported from
`$(cat ~/.beaconpave/m11-drill-key.txt)`. The key's value is printed nowhere below.

## D21: the fixture's line endings, read before it was touched

Cold review D21 carries a CRLF re-save of the fixture during the fix step as a way to make
the fixed run INVALID. It is read here, not committed separately. `git ls-files --eol` read
`i/lf w/lf attr/text=auto eol=lf` before the restore, after it, and again immediately before
the fixed run. The fix-step transcript is below the readings table.

## Readings

| reading | registered expectation | read | verdict |
|---|---|---|---|
| the run's exit | `pave drill` exit 0, GO written | exit 0 | as expected |
| **fixed validity:** `drill verify` | exit 0 | exit 0, `signature: OK` | **holds** |
| **fixed validity:** `mode` | `delta` | `mode=delta` | **holds** |
| **fixed validity:** `prior_sha256` | equals `sha256sum R1` | `96cb3c3c…f0f4bb62` both | **holds** |
| **fixed validity:** `git diff --name-only C F`, minus `milestones/M11/` | exactly the fixture | `drill/fixtures/jefferson-derby/captions.vtt` | **holds** |
| **fixed validity:** `git diff B F -- drill/fixtures/jefferson-derby/captions.vtt` | empty | empty, 0 bytes | **holds** |
| **F5** | `decision=GO`, and no `finding` line | `decision=GO`; `grep -c '^finding='` prints `0` (grep's exit 1 is its no-match code) | **does not fire** |

`owner`, `fix_by` and `fix_window_s` read `-` on the GO, as SPEC/11 pins: they are written on
a NO-GO only. The all-three row (`tree_clean`, `caption_sha256` against the blob at F,
ancestry) is read in `milestones/M11/runs/validity.md`. `tree_clean=true` is in the
`drill read` output below.

## The fix step's transcript

The script that produced it is `fix.sh`, run once. Its output is below, unedited. The commit
that followed it is F.

```text
## Before touching the fixture (D21, read and not committed)

$ git rev-parse HEAD
9592fdc8dd32fac023a43432976cdb97e4ec75c3
exit 0

$ git status --porcelain
exit 0

$ git ls-files --eol -- drill/fixtures/jefferson-derby/captions.vtt
i/lf    w/lf    attr/text=auto eol=lf 	drill/fixtures/jefferson-derby/captions.vtt
exit 0

## The restore

$ git checkout 52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a -- drill/fixtures/jefferson-derby/captions.vtt
exit 0

$ git ls-files --eol -- drill/fixtures/jefferson-derby/captions.vtt
i/lf    w/lf    attr/text=auto eol=lf 	drill/fixtures/jefferson-derby/captions.vtt
exit 0

$ git status --porcelain
M  drill/fixtures/jefferson-derby/captions.vtt
exit 0

$ git diff --cached --stat
 drill/fixtures/jefferson-derby/captions.vtt | 4 ++++
 1 file changed, 4 insertions(+)
exit 0

$ git diff --cached -- drill/fixtures/jefferson-derby/captions.vtt
diff --git a/drill/fixtures/jefferson-derby/captions.vtt b/drill/fixtures/jefferson-derby/captions.vtt
index b090c46..e265d5b 100644
--- a/drill/fixtures/jefferson-derby/captions.vtt
+++ b/drill/fixtures/jefferson-derby/captions.vtt
@@ -24,6 +24,10 @@ c006
 00:00:25.000 --> 00:00:30.000
 A corner is awarded.
 
+c007
+00:00:30.000 --> 00:00:35.000
+The corner is headed wide.
+
 c008
 00:00:35.000 --> 00:00:40.000
 Goal kick.
exit 0

```

## The fixed run's transcript

The script that produced it is `fixed.sh`, run once. Its output is below, unedited.

```text
## Before the run

$ git rev-parse HEAD
a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70
exit 0

$ git status --porcelain
exit 0

$ git ls-files -v | cut -c1 | sort | uniq -c
    804 H
exit 0

$ git ls-files --eol -- drill/fixtures/jefferson-derby/captions.vtt
i/lf    w/lf    attr/text=auto eol=lf 	drill/fixtures/jefferson-derby/captions.vtt
exit 0

$ python -c "import pave.drill, pave.drill_read; print(pave.drill.__file__); print(pave.drill_read.__file__)"
C:\Users\andar\AppData\Local\Temp\claude\c--Users-andar-code-beaconpave\22afb63c-c89b-4385-a31d-89553d920b2b\scratchpad\m11pr3\bp\pave\drill.py
C:\Users\andar\AppData\Local\Temp\claude\c--Users-andar-code-beaconpave\22afb63c-c89b-4385-a31d-89553d920b2b\scratchpad\m11pr3\bp\pave\drill_read.py
exit 0

## The fixed run

$ python -m pave.cli drill --event jefferson-derby --tier 3 --delta milestones/M11/runs/seeded/go-no-go.json --out milestones/M11/runs/fixed/go-no-go.json
drill: GO - written milestones/M11/runs/fixed/go-no-go.json
exit 0

## drill read

$ python -m pave.cli drill read milestones/M11/runs/fixed/go-no-go.json
decision=GO
mode=delta
commit=a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70
tree_clean=true
ran_at=2026-09-14T14:06:52Z
fix_by=-
fix_window_s=-
owner.seat=-
owner.oncall=-
caption_sha256=b9552728f7f7fd402980e3e8801f3f99a9b5c7c59278589b52fc6b525ea8b3ce
prior_sha256=96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62
exit 0

## drill verify (fixed validity clause)

$ python -m pave.cli drill verify milestones/M11/runs/fixed/go-no-go.json
signature: OK
schema: OK
exit 0

## F5: decision and finding lines

$ python -m pave.cli drill read milestones/M11/runs/fixed/go-no-go.json | grep -E '^decision='
decision=GO
exit 0

$ python -m pave.cli drill read milestones/M11/runs/fixed/go-no-go.json | grep -cE '^finding='
0
exit 1

## Fixed validity row

$ python -m pave.cli drill read milestones/M11/runs/fixed/go-no-go.json | grep -E '^(mode|commit|prior_sha256)='
mode=delta
commit=a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70
prior_sha256=96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62
exit 0

$ sha256sum milestones/M11/runs/seeded/go-no-go.json
96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62 *milestones/M11/runs/seeded/go-no-go.json
exit 0

$ git diff --name-only ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93 a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70
drill/fixtures/jefferson-derby/captions.vtt
milestones/M11/runs/control/go-no-go.json
milestones/M11/runs/control/readings.md
exit 0

$ git diff --name-only ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93 a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70 | grep -v '^milestones/M11/'
drill/fixtures/jefferson-derby/captions.vtt
exit 0

$ git diff 52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70 -- drill/fixtures/jefferson-derby/captions.vtt
exit 0

$ git diff 52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70 -- drill/fixtures/jefferson-derby/captions.vtt | wc -c
0
exit 0

## After the readings

$ sha256sum milestones/M11/runs/fixed/go-no-go.json
8112435047d32dcabc9a61912472f82e3823266076eb3cd36a61719a4d2b41ca *milestones/M11/runs/fixed/go-no-go.json
exit 0

$ git status --porcelain
?? milestones/M11/runs/fixed/
exit 0

```

## The scripts, as they ran

`fix.sh`:

```bash
# M11 PR 3: the fix step. Run from the clone's root, once, at clean HEAD after the control commit.
set -u
source ../show.sh
B=52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a
FX=drill/fixtures/jefferson-derby/captions.vtt

echo '## Before touching the fixture (D21, read and not committed)'
echo
run 'git rev-parse HEAD'
run 'git status --porcelain'
run "git ls-files --eol -- $FX"

echo '## The restore'
echo
run "git checkout $B -- $FX"
run "git ls-files --eol -- $FX"
run 'git status --porcelain'
run "git diff --cached --stat"
run "git diff --cached -- $FX"
```

`fixed.sh`:

```bash
# M11 PR 3: the fixed run and its readings. Run from the clone's root, once, at clean HEAD F.
set -u
source ../show.sh
export PYTHONIOENCODING=utf-8
export BEACONPAVE_DRILL_KEY="$(cat ~/.beaconpave/m11-drill-key.txt)"
B=52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a
C=ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
FX=drill/fixtures/jefferson-derby/captions.vtt
R1=milestones/M11/runs/seeded/go-no-go.json
R3=milestones/M11/runs/fixed/go-no-go.json

echo '## Before the run'
echo
run 'git rev-parse HEAD'
run 'git status --porcelain'
run 'git ls-files -v | cut -c1 | sort | uniq -c'
run "git ls-files --eol -- $FX"
run 'python -c "import pave.drill, pave.drill_read; print(pave.drill.__file__); print(pave.drill_read.__file__)"'

echo '## The fixed run'
echo
run "python -m pave.cli drill --event jefferson-derby --tier 3 --delta $R1 --out $R3"

echo '## drill read'
echo
run "python -m pave.cli drill read $R3"

echo '## drill verify (fixed validity clause)'
echo
run "python -m pave.cli drill verify $R3"

echo '## F5: decision and finding lines'
echo
run "python -m pave.cli drill read $R3 | grep -E '^decision='"
run "python -m pave.cli drill read $R3 | grep -cE '^finding='"

echo '## Fixed validity row'
echo
F=$(python -m pave.cli drill read "$R3" | sed -n 's/^commit=//p')
run "python -m pave.cli drill read $R3 | grep -E '^(mode|commit|prior_sha256)='"
run "sha256sum $R1"
run "git diff --name-only $C $F"
run "git diff --name-only $C $F | grep -v '^milestones/M11/'"
run "git diff $B $F -- $FX"
run "git diff $B $F -- $FX | wc -c"

echo '## After the readings'
echo
run "sha256sum $R3"
run 'git status --porcelain'
```
