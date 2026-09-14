# M11 PR 3: validity, every row, all three runs

**Read before any falsifier** (SPEC/11, *Validity is read before any falsifier*). A run failing
one clause is INVALID, the claim is NOT MEASURED, and M11 closes RED with no re-run.
**No clause failed. All three runs are VALID.**

**Where it was read:** the fresh clone of `m11-pr3-arc` the three runs were taken in, at
`c15ff1333f04c8bb53afef0c800a476e849a67a0` (the fixed run's readings commit), with a clean
tree. Every command here is read-only.

- **B** = `52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a`, PR 3's branch point on `main`
- **S** = `10283eb264ca7d436df60f373ca0bb860cd3f003`, the seeded artifact's `commit`
- **C** = `ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93`, the control artifact's `commit`
- **F** = `a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70`, the fixed artifact's `commit`
- **R1** = `milestones/M11/runs/seeded/go-no-go.json`

## Every clause, its reader and its verdict

Each row of SPEC/11's validity table is split into its clauses. The reader column names the
command in the transcript below.

| run | clause, as SPEC/11 words it | reader | read | verdict |
|---|---|---|---|---|
| seeded | `tree_clean=true` | `drill read` | `tree_clean=true` | **holds** |
| seeded | `caption_sha256` equals `git show S:<fixture> \| sha256sum` | `drill read`, `git show`, `sha256sum` | `1449d4db…a3c0d3de` both | **holds** |
| control | `tree_clean=true` | `drill read` | `tree_clean=true` | **holds** |
| control | `caption_sha256` equals `git show C:<fixture> \| sha256sum` | same | `1449d4db…a3c0d3de` both | **holds** |
| fixed | `tree_clean=true` | `drill read` | `tree_clean=true` | **holds** |
| fixed | `caption_sha256` equals `git show F:<fixture> \| sha256sum` | same | `b9552728…525ea8b3ce` both | **holds** |
| all three | S, C and F lie in that order on PR 3's branch | `git merge-base --is-ancestor` | B→S, S→C, C→F and F→`m11-pr3-arc` each exit 0 | **holds** |
| seeded | `mode=full` | `drill read` | `mode=full` | **holds** |
| seeded | `git diff --name-only B S` is exactly the fixture | `git diff` | `drill/fixtures/jefferson-derby/captions.vtt`, alone | **holds** |
| seeded | `drill verify` on R1 exits 0 printing `signature: OK` | `drill verify` | exit 0, `signature: OK` | **holds** |
| seeded | `signature.key_id` equals the first 16 hex of `key.sha256` | `grep '"key_id"'` on R1, `head -c 16` on `key.sha256` | `cb16e839a08a5a74` both | **holds** |
| control | `mode=delta` | `drill read` | `mode=delta` | **holds** |
| control | `prior_sha256` equals `sha256sum R1` | `drill read`, `sha256sum` | `96cb3c3c…f0f4bb62` both | **holds** |
| control | `caption_sha256` equals seeded's | `drill read` | `1449d4db…a3c0d3de` both | **holds** |
| control | C ≠ S | `drill read` | `ce7b00f` ≠ `10283eb` | **holds** |
| control | `git diff --name-only S C` lies under `milestones/M11/` | `git diff` | two paths, both under `milestones/M11/runs/seeded/`; `grep -v '^milestones/M11/'` matches nothing (grep's exit 1) | **holds** |
| control | `drill verify` exits 0 | `drill verify` | exit 0, `signature: OK` | **holds** |
| fixed | `mode=delta` | `drill read` | `mode=delta` | **holds** |
| fixed | `prior_sha256` equals `sha256sum R1` | `drill read`, `sha256sum` | `96cb3c3c…f0f4bb62` both | **holds** |
| fixed | `git diff --name-only C F`, minus `milestones/M11/`, is exactly the fixture | `git diff` | `drill/fixtures/jefferson-derby/captions.vtt`, alone | **holds** |
| fixed | `git diff B F -- drill/fixtures/jefferson-derby/captions.vtt` is empty | `git diff` | 0 bytes | **holds** |
| fixed | `drill verify` exits 0 | `drill verify` | exit 0, `signature: OK` | **holds** |

**Beside the rows, and not a clause.**
- **The procedural remedy for D19.** Before each run, `git ls-files -v` showed every entry as
  `H`, with no `S` (skip-worktree) and no lowercase (assume-unchanged) entry: 800, 802 and 804
  entries. Each run's readings carry that line. It is not a registered clause (ADR-080
  amendment 4, item 4).
- **The imported writer and readers were the clone's own.** Each run's readings print
  `pave.drill.__file__` and `pave.drill_read.__file__` inside the clone.
- **The committed artifacts are the bytes that were read.** Their on-disk sha256 equals
  `git show HEAD:<path> | sha256sum` for all three (last section of the transcript).

## The transcript

The script that produced it is `validity.sh`, run once. Its output is below, unedited.

```text
## Where this was read

$ git rev-parse HEAD
c15ff1333f04c8bb53afef0c800a476e849a67a0
exit 0

$ git branch --show-current
m11-pr3-arc
exit 0

$ git status --porcelain
exit 0

## All three: tree_clean, and caption_sha256 against the fixture blob at the run's own commit

$ python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json | grep -E '^(commit|tree_clean|caption_sha256)='
commit=10283eb264ca7d436df60f373ca0bb860cd3f003
tree_clean=true
caption_sha256=1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de
exit 0

$ git show 10283eb264ca7d436df60f373ca0bb860cd3f003:drill/fixtures/jefferson-derby/captions.vtt | sha256sum
1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de *-
exit 0

$ python -m pave.cli drill read milestones/M11/runs/control/go-no-go.json | grep -E '^(commit|tree_clean|caption_sha256)='
commit=ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
tree_clean=true
caption_sha256=1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de
exit 0

$ git show ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93:drill/fixtures/jefferson-derby/captions.vtt | sha256sum
1449d4db5c81a50789f0231375d9933742d5f3af32f731020bbc5168a3c0d3de *-
exit 0

$ python -m pave.cli drill read milestones/M11/runs/fixed/go-no-go.json | grep -E '^(commit|tree_clean|caption_sha256)='
commit=a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70
tree_clean=true
caption_sha256=b9552728f7f7fd402980e3e8801f3f99a9b5c7c59278589b52fc6b525ea8b3ce
exit 0

$ git show a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70:drill/fixtures/jefferson-derby/captions.vtt | sha256sum
b9552728f7f7fd402980e3e8801f3f99a9b5c7c59278589b52fc6b525ea8b3ce *-
exit 0

## All three: S, C and F lie in that order on PR 3's branch

$ git merge-base --is-ancestor 52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a 10283eb264ca7d436df60f373ca0bb860cd3f003
exit 0

$ git merge-base --is-ancestor 10283eb264ca7d436df60f373ca0bb860cd3f003 ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
exit 0

$ git merge-base --is-ancestor ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93 a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70
exit 0

$ git merge-base --is-ancestor a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70 m11-pr3-arc
exit 0

$ git log --format='%h %s' 52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a..m11-pr3-arc
c15ff13 M11 PR 3 fixed run: the fix step's D21 reading, the artifact and its readings
a69e3a7 M11 PR 3 fix: cue c007 restored, the fixture's bytes equal to B's
9592fdc M11 PR 3 control run: the artifact and its readings
ce7b00f M11 PR 3 seeded run: the artifact and its readings
10283eb M11 PR 3 seed: cue c007 deleted from the fixture, and nothing else
exit 0

## Seeded: mode=full, git diff --name-only B S, verify on R1, key_id

$ python -m pave.cli drill read milestones/M11/runs/seeded/go-no-go.json | grep -E '^mode='
mode=full
exit 0

$ git diff --name-only 52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a 10283eb264ca7d436df60f373ca0bb860cd3f003
drill/fixtures/jefferson-derby/captions.vtt
exit 0

$ python -m pave.cli drill verify milestones/M11/runs/seeded/go-no-go.json
signature: OK
schema: OK
exit 0

$ grep '"key_id"' milestones/M11/runs/seeded/go-no-go.json
    "key_id": "cb16e839a08a5a74",
exit 0

$ head -c 16 milestones/M11/pre-registration/key.sha256
cb16e839a08a5a74exit 0

## Control: mode=delta, prior_sha256, caption_sha256 equal to seeded's, C != S, git diff --name-only S C, verify

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

$ git diff --name-only 10283eb264ca7d436df60f373ca0bb860cd3f003 ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93 | grep -v '^milestones/M11/'
exit 1

$ python -m pave.cli drill verify milestones/M11/runs/control/go-no-go.json
signature: OK
schema: OK
exit 0

## Fixed: mode=delta, prior_sha256, git diff --name-only C F minus milestones/M11/, git diff B F -- fixture, verify

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

$ git diff 52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70 -- drill/fixtures/jefferson-derby/captions.vtt | wc -c
0
exit 0

$ python -m pave.cli drill verify milestones/M11/runs/fixed/go-no-go.json
signature: OK
schema: OK
exit 0

## The three artifacts, as committed

$ sha256sum milestones/M11/runs/seeded/go-no-go.json milestones/M11/runs/control/go-no-go.json milestones/M11/runs/fixed/go-no-go.json
96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62 *milestones/M11/runs/seeded/go-no-go.json
12211e3f89e86b7b2c4f00563d1b05dbdea52e527e6d25558779c06373a7971c *milestones/M11/runs/control/go-no-go.json
8112435047d32dcabc9a61912472f82e3823266076eb3cd36a61719a4d2b41ca *milestones/M11/runs/fixed/go-no-go.json
exit 0

$ for p in milestones/M11/runs/seeded/go-no-go.json milestones/M11/runs/control/go-no-go.json milestones/M11/runs/fixed/go-no-go.json; do git show HEAD:$p | sha256sum; done
96cb3c3c18406984e974e2cf64b693376f4ac43bb348a01d976c869af0f4bb62 *-
12211e3f89e86b7b2c4f00563d1b05dbdea52e527e6d25558779c06373a7971c *-
8112435047d32dcabc9a61912472f82e3823266076eb3cd36a61719a4d2b41ca *-
exit 0

```

## The script, `validity.sh`, as it ran

```bash
# M11 PR 3: every validity row, for all three runs. Read-only. Run from the clone's root.
set -u
source ../show.sh
export PYTHONIOENCODING=utf-8
export BEACONPAVE_DRILL_KEY="$(cat ~/.beaconpave/m11-drill-key.txt)"
B=52b35f10e2bcdfbd84122ea1aab46e5aeaf1f31a
S=10283eb264ca7d436df60f373ca0bb860cd3f003
C=ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93
F=a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70
FX=drill/fixtures/jefferson-derby/captions.vtt
R1=milestones/M11/runs/seeded/go-no-go.json
R2=milestones/M11/runs/control/go-no-go.json
R3=milestones/M11/runs/fixed/go-no-go.json
KEYHASH=milestones/M11/pre-registration/key.sha256

echo '## Where this was read'
echo
run 'git rev-parse HEAD'
run 'git branch --show-current'
run 'git status --porcelain'

echo '## All three: tree_clean, and caption_sha256 against the fixture blob at the run'"'"'s own commit'
echo
run "python -m pave.cli drill read $R1 | grep -E '^(commit|tree_clean|caption_sha256)='"
run "git show $S:$FX | sha256sum"
run "python -m pave.cli drill read $R2 | grep -E '^(commit|tree_clean|caption_sha256)='"
run "git show $C:$FX | sha256sum"
run "python -m pave.cli drill read $R3 | grep -E '^(commit|tree_clean|caption_sha256)='"
run "git show $F:$FX | sha256sum"

echo '## All three: S, C and F lie in that order on PR 3'"'"'s branch'
echo
run "git merge-base --is-ancestor $B $S"
run "git merge-base --is-ancestor $S $C"
run "git merge-base --is-ancestor $C $F"
run "git merge-base --is-ancestor $F m11-pr3-arc"
run "git log --format='%h %s' $B..m11-pr3-arc"

echo '## Seeded: mode=full, git diff --name-only B S, verify on R1, key_id'
echo
run "python -m pave.cli drill read $R1 | grep -E '^mode='"
run "git diff --name-only $B $S"
run "python -m pave.cli drill verify $R1"
run "grep '\"key_id\"' $R1"
run "head -c 16 $KEYHASH"

echo '## Control: mode=delta, prior_sha256, caption_sha256 equal to seeded'"'"'s, C != S, git diff --name-only S C, verify'
echo
run "python -m pave.cli drill read $R2 | grep -E '^(mode|commit|prior_sha256|caption_sha256)='"
run "sha256sum $R1"
run "python -m pave.cli drill read $R1 | grep -E '^(commit|caption_sha256)='"
run "git diff --name-only $S $C"
run "git diff --name-only $S $C | grep -v '^milestones/M11/'"
run "python -m pave.cli drill verify $R2"

echo '## Fixed: mode=delta, prior_sha256, git diff --name-only C F minus milestones/M11/, git diff B F -- fixture, verify'
echo
run "python -m pave.cli drill read $R3 | grep -E '^(mode|commit|prior_sha256)='"
run "sha256sum $R1"
run "git diff --name-only $C $F"
run "git diff --name-only $C $F | grep -v '^milestones/M11/'"
run "git diff $B $F -- $FX | wc -c"
run "python -m pave.cli drill verify $R3"

echo '## The three artifacts, as committed'
echo
run "sha256sum $R1 $R2 $R3"
run "for p in $R1 $R2 $R3; do git show HEAD:\$p | sha256sum; done"
```
