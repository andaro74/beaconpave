"""
M11's pre-registration is one set of values in three places, and they agree.

- `SPEC/11-drill-go-no-go.md` proposes the values (PR 1), amended once before the
  registration (ADR-080 amendment 1).
- `milestones/M11/pre-registration/falsifiers.json` commits them (PR 2).
- `drill/scenarios/caption-check.json` is what the writer reads at run time.

A pin moved in one and not the others is a threshold chosen after the fact. A pin moved in
all three is visible in SPEC/11's own text, which is where this reads it.

**Every falsifier and every validity row is held verbatim** (AI Quality seat, M11 PR 2,
finding 2). The first version of this file held only some of the registration: a
falsifier's `false_if` narrowed, F4's `runs` moved, a control validity check dropped, and
F3's liveness exit changed each SURVIVED. Now each row the registration carries must be a
row of SPEC/11's tables, and each table row must be carried. The structured fields a
reading uses (`runs`, `expect`, liveness) are pinned literally here, beside them.

**Also held:**
- The readers were shown emitting before the claim was committed. The last change to
  `readers.txt` descends from the last change to the writer, the readers, the schema and
  the dispatch; the last change to `falsifiers.json` descends from the last change to
  `readers.txt`. Read by ancestry, so a rebase merge keeps it, and a squash does not.
- The clean fixture had SPEC/11's shape, **read at the commit that added it**. PR 3 seeds
  the working-tree copy, and a pin on today's bytes would go red at the seed.

**Nothing here runs the drill.** It reads committed files and git history.

Owning seat: AI Quality (the pins) - Platform Engineering (the scenario file).
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC" / "11-drill-go-no-go.md"
REGISTRATION = ROOT / "milestones" / "M11" / "pre-registration" / "falsifiers.json"
READINGS = ROOT / "milestones" / "M11" / "pre-registration" / "readers.txt"
SCENARIO = ROOT / "drill" / "scenarios" / "caption-check.json"
READ = "python -m pave.cli drill read"
VERIFY = "python -m pave.cli drill verify"
#: What `readers.txt` must post-date: every file whose code a reading exercises.
READ_CODE = ("pave/drill.py", "pave/drill_read.py", "quality/drill/go-no-go.schema.json",
             "pave/cli.py")


def _registration() -> dict:
    return json.loads(REGISTRATION.read_text(encoding="utf-8"))


def _between(start: str, end: str) -> str:
    text = SPEC.read_text(encoding="utf-8")
    return text[text.index(start):text.index(end)]


def _pinned_section() -> str:
    return _between("\n### Pinned here, and nowhere later\n", "\n## Beside the claim, and not it\n")


def _table_rows(section: str, first_cells: tuple) -> list[str]:
    return [line for line in section.splitlines()
            if any(line.startswith(f"| {cell} |") for cell in first_cells)]


def _git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    assert result.returncode == 0, f"git {' '.join(args)}: {result.stderr.strip()}"
    return result.stdout.strip()


def _last_change(path: str) -> str:
    sha = _git("log", "-1", "--format=%H", "--", path)
    assert sha, f"{path} is not committed"
    return sha


def _descends(ancestor: str, descendant: str) -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", ancestor,
                           descendant], capture_output=True).returncode == 0


def test_every_pin_is_written_in_spec_11s_pinned_section():
    pins = _registration()["pins"]
    section = _pinned_section()
    expected = [
        f"`{pins['fixture']}`",
        f"cue `{pins['seed']['deleted_cue']}` deleted",
        f"cue `{pins['fix']['restored_cue']}` restored",
        f"`{pins['seeded_finding']}`",
        f"`owner.seat` = `{pins['owner']['seat']}`",
        f"`owner.oncall` = `{pins['owner']['oncall']}`",
        f"**{pins['fix_by_window_s']} s**",
        f"greater than {pins['max_gap_s']:.3f} s",
        f"\"alg\": \"{pins['signature']['alg']}\"",
        f"`{pins['signature']['key_env']}`",
        f"at least {pins['signature']['min_key_bytes']} bytes",
        f"`{pins['fixture_shape']['cues'][0]}`–`{pins['fixture_shape']['cues'][-1]}`",
        f"each {pins['fixture_shape']['cue_ms'] / 1000:.3f} s",
    ]
    missing = [literal for literal in expected if literal not in section]
    assert not missing, f"falsifiers.json pins values SPEC/11 does not write: {missing}"
    # **Exactly, not to the millisecond** (AI Quality seat, finding 4): 4.0004 in both the
    # registration and the scenario file printed as `4.000 s` and SURVIVED.
    assert float(f"{pins['max_gap_s']:.3f}") == pins["max_gap_s"]
    assert f"event `{pins['event']}` at tier {pins['tier']}" in SPEC.read_text(encoding="utf-8")


def test_the_scenario_file_the_writer_reads_carries_the_registered_values():
    pins = _registration()["pins"]
    scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
    assert scenario["scenario"] == pins["scenario"]
    assert scenario["rule"] == pins["rule"]
    assert scenario["max_gap_s"] == pins["max_gap_s"]
    assert type(scenario["max_gap_s"]) is type(pins["max_gap_s"])
    assert scenario["owner"] == pins["owner"]
    assert scenario["fix_by_window_s"][str(pins["tier"])] == pins["fix_by_window_s"]
    assert scenario["events"][pins["event"]]["captions"] == pins["fixture"]


def test_every_falsifier_row_is_spec_11s_row_verbatim():
    registration = _registration()
    spec_rows = _table_rows(_between("\n### The five falsifiers\n", "**F3's liveness"),
                            tuple(f"**F{n}**" for n in range(1, 6)))
    assert len(spec_rows) == 5, f"SPEC/11's falsifier table parsed to {len(spec_rows)} rows"
    carried = [entry["spec_row"] for entry in registration["falsifiers"]]
    assert carried == spec_rows, "falsifiers.json does not carry SPEC/11's five rows verbatim"
    for entry in registration["falsifiers"]:
        assert entry["spec_row"].startswith(f"| **{entry['id']}** |")


def test_every_validity_row_is_spec_11s_row_verbatim():
    registration = _registration()
    spec_rows = _table_rows(_between("**Validity is read before any falsifier.**",
                                     "\n## Beside the claim, and not it\n"),
                            ("all three", "seeded", "control", "fixed"))
    assert len(spec_rows) == 4, f"SPEC/11's validity table parsed to {len(spec_rows)} rows"
    carried = [entry["spec_row"] for entry in registration["validity"]["rows"]]
    assert carried == spec_rows, "falsifiers.json does not carry SPEC/11's validity rows verbatim"
    assert any("caption_sha256` equals `git show <commit>:" in row for row in carried), (
        "ADR-080 amendment 1's row -- each run's caption bytes are the committed fixture's -- "
        "is not registered")


def test_the_fields_a_reading_uses_are_pinned():
    registration = _registration()
    pins = registration["pins"]
    falsifiers = {entry["id"]: entry for entry in registration["falsifiers"]}
    assert list(falsifiers) == ["F1", "F2", "F3", "F4", "F5"]
    for entry in falsifiers.values():
        assert entry["reader"] in {READ, VERIFY}, entry["id"]
        assert entry["reader_lands"] == "PR 2", entry["id"]
    assert {fid: entry["runs"] for fid, entry in falsifiers.items()} == {
        "F1": ["seeded"], "F2": ["seeded", "control"], "F3": ["seeded"], "F4": ["control"],
        "F5": ["fixed"]}
    assert falsifiers["F1"]["expect"] == {"decision": "NO-GO", "finding": [pins["seeded_finding"]]}
    assert falsifiers["F2"]["expect"] == {"owner.seat": pins["owner"]["seat"],
                                          "owner.oncall": pins["owner"]["oncall"],
                                          "fix_window_s": str(pins["fix_by_window_s"])}
    assert falsifiers["F3"]["reader"] == VERIFY
    assert falsifiers["F3"]["expect"] == {"exit": 1, "line": "signature: MISMATCH"}
    assert falsifiers["F3"]["liveness"] | {} == {
        **falsifiers["F3"]["liveness"], "exit": 0, "line": "signature: OK", "evidence": False}
    assert [edit["field"] for edit in falsifiers["F3"]["edits"]] == ["decision", "owner.oncall",
                                                                   "fix_by"]
    assert falsifiers["F4"]["expect"] == {"decision": "NO-GO", "finding": "equal to the seeded run's"}
    assert falsifiers["F5"]["expect"] == {"decision": "GO", "finding": []}


def test_the_readers_were_shown_emitting_before_the_claim_was_committed():
    text = READINGS.read_text(encoding="utf-8")
    assert f"$ {READ} " in text and f"$ {VERIFY} " in text
    assert "signature: OK" in text and "signature: MISMATCH" in text
    assert text.index("signature: OK") < text.index("signature: MISMATCH"), (
        "F3's liveness check must come first (SPEC/11): verify exits 0 on the well-formed "
        "artifact before any edited copy is read")
    for line in ("decision=NO-GO", "decision=GO", "fix_window_s=", "owner.oncall=",
                 "prior_sha256=", "finding=", "sha256sum"):
        assert line in text, f"readers.txt shows no {line!r} emitted"

    readings = _last_change(READINGS.relative_to(ROOT).as_posix())
    for path in READ_CODE:
        assert _descends(_last_change(path), readings), (
            f"{path} changed after readers.txt was taken: the transcript does not show the "
            "readers as committed")
    registration = _last_change(REGISTRATION.relative_to(ROOT).as_posix())
    assert readings != registration, "readers.txt and falsifiers.json changed in one commit"
    assert _descends(readings, registration), (
        "the last change to falsifiers.json does not descend from the last change to "
        "readers.txt: the claim was committed before its readers were shown emitting")


def test_the_clean_fixture_had_specs_shape_at_the_commit_that_added_it():
    pins = _registration()["pins"]
    shas = _git("log", "--diff-filter=A", "--format=%H", "--", pins["fixture"]).split()
    assert shas, f"{pins['fixture']} is not committed"
    text = _git("show", f"{shas[-1]}:{pins['fixture']}")
    timing = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3}) --> (\d{2}):(\d{2}):(\d{2})\.(\d{3})$")
    lines = text.splitlines()
    assert lines[0] == "WEBVTT"
    cues = []
    for index, line in enumerate(lines):
        match = timing.match(line)
        if match:
            g = [int(x) for x in match.groups()]
            start = ((g[0] * 60 + g[1]) * 60 + g[2]) * 1000 + g[3]
            end = ((g[4] * 60 + g[5]) * 60 + g[6]) * 1000 + g[7]
            cues.append((lines[index - 1], start, end))
    shape = pins["fixture_shape"]
    assert [cue_id for cue_id, _, _ in cues] == shape["cues"]
    assert all(end - start == shape["cue_ms"] for _, start, end in cues)
    assert cues[0][1] == shape["start_ms"] and cues[-1][2] == shape["end_ms"]
    assert all(after[2] == before[1] for after, before in zip(cues, cues[1:], strict=False))
