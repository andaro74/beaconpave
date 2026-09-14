# M11 PR 3: SPEC/11's demo block, run from a clean shell

**Run after the key was published**, at `1347096d41a776c9cbcd1edf3328d3bac8667c26` with a
clean tree, in the fresh clone of `m11-pr3-arc`, in a new shell where
`BEACONPAVE_DRILL_KEY` and `PYTHONIOENCODING` were both unset. The four commands are SPEC/11's
*Demo artifact* block, verbatim. Each is printed as `$ command`, followed by its output and
`exit N`. The output below is unedited.

**This block is Act 4's script** (`docs/governance/recordings.json`, Act 4). Its recording is
deferred to after M11's close.

**Against SPEC/11's predicted shape:**

| predicted | read | verdict |
|---|---|---|
| seeded: `decision=NO-GO` | `decision=NO-GO` | as predicted |
| seeded: one `finding=caption-check/max-gap/c006/c008` | exactly that line, once | as predicted |
| seeded: `owner.oncall=webhook:player-captions` | that line | as predicted |
| seeded: `fix_window_s=129600` | that line | as predicted |
| `signature: OK` | `signature: OK`, **then `schema: OK`** | as predicted; the second line was not in the prediction |
| control: `decision=NO-GO` with the same finding | `decision=NO-GO`, `finding=caption-check/max-gap/c006/c008` | as predicted |
| fixed: `decision=GO` with no finding | `decision=GO`, no `finding=` line | as predicted; **`fix_by`, `fix_window_s`, `owner.seat` and `owner.oncall` print `-`**, which SPEC/11's `read` row pins and the prediction did not mention |

**The first attempt was not this transcript.** It ran the same four commands under `set -x`,
which echoed the expanded `export` line, and so the key's value, to the terminal. That key was
already published at `1347096`, so nothing was disclosed. The trace is not the block's output,
so the block was run again, read-only, through the transcript helper. Both runs printed the
same lines.

```text
env before the block: BEACONPAVE_DRILL_KEY=<unset> PYTHONIOENCODING=<unset>
HEAD 1347096d41a776c9cbcd1edf3328d3bac8667c26, git status --porcelain: []

$ export BEACONPAVE_DRILL_KEY="$(cat milestones/M11/runs/drill-key.txt)"
exit 0

$ python -m pave.cli drill read   milestones/M11/runs/seeded/go-no-go.json
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

$ python -m pave.cli drill verify milestones/M11/runs/seeded/go-no-go.json
signature: OK
schema: OK
exit 0

$ python -m pave.cli drill read   milestones/M11/runs/control/go-no-go.json
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

$ python -m pave.cli drill read   milestones/M11/runs/fixed/go-no-go.json
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

```

## The published key's hash

Taken at `1347096`, immediately after the key was committed. The first line of
`milestones/M11/pre-registration/key.sha256` was committed before B.

```text
$ git ls-files --eol -- milestones/M11/runs/drill-key.txt
i/lf    w/lf    attr/text=auto eol=lf 	milestones/M11/runs/drill-key.txt
exit 0

$ wc -c milestones/M11/runs/drill-key.txt
65 milestones/M11/runs/drill-key.txt
exit 0

$ BEACONPAVE_DRILL_KEY="$(cat milestones/M11/runs/drill-key.txt)" python -c 'import hashlib, os; from pave import drill; k = drill.load_key(os.environ); print(len(k), hashlib.sha256(k).hexdigest())'
64 cb16e839a08a5a747ed8764c4983ce8ce5190283806d5dc20fb8e29d373129b4
exit 0

$ head -1 milestones/M11/pre-registration/key.sha256
cb16e839a08a5a747ed8764c4983ce8ce5190283806d5dc20fb8e29d373129b4  sha256 of the 64 bytes BEACONPAVE_DRILL_KEY holds for M11 PR 3's runs
exit 0

$ git show HEAD:milestones/M11/runs/drill-key.txt | cmp - milestones/M11/runs/drill-key.txt
exit 0

```
