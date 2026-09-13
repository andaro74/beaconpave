"""
The drill's readers, `pave drill read` and `pave drill verify` (`pave/drill_read.py`).

Every SPEC/11 falsifier names one of these, so what is held here is what a falsifier can
see. **The artifacts below are built by hand in this file and signed by this file**, with
the canonical form written out a third time, so a reader that agreed with the writer by
sharing its code could not pass. Values are synthetic and differ from SPEC/11's pins, and
no case reads the arc.

Held:
- **`read` prints SPEC/11's lines, in SPEC/11's order,** with `-` for an absent field. It
  decides nothing: it prints an unsigned, schema-invalid document as readily as a good one.
- **F3's three edits, made as text substitutions on the file, each exit 1 with
  `signature: MISMATCH`.** Each plant is first shown to have changed the bytes.
- **The signature is checked before the schema** (constraint 5). An edit that also breaks
  the schema is refused as a MISMATCH, and the schema line is never reached.
- **The algorithm, the key id and the value must all hold.** A verifier comparing the key
  id alone is one of ADR-080 decision 2's named false states.
- **The readers import nothing from the writer** (constraint 6), and the two modules define
  no top-level name in common.

Hermetic (G8): committed schema, temporary files; no network, no model.
Owning seat: AI Quality (what a falsifier reads) - Platform Engineering (the code).
"""
from __future__ import annotations

import ast
import hashlib
import hmac
import json
import pathlib
import subprocess

import pytest

from pave import cli, drill, drill_read

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "synthetic-reader-key-never-a-run-key-00"
ENV = {"BEACONPAVE_DRILL_KEY": KEY}

NO_GO = {
    "event": "synthetic-event",
    "tier": 7,
    "mode": "full",
    "commit": "a" * 40,
    "tree_clean": True,
    "ran_at": "2030-01-02T03:04:05Z",
    "decision": "NO-GO",
    "findings": [{"scenario": "caption-check", "rule": "max-gap",
                  "after_cue": "s01", "before_cue": "s03", "gap_s": 3.0}],
    "owner": {"seat": "synthetic-seat", "oncall": "webhook:synthetic-oncall"},
    "fix_by": "2030-01-02T05:04:05Z",
    "inputs": {"caption_sha256": "b" * 64},
}
GO_DELTA = {
    "event": "synthetic-event",
    "tier": 7,
    "mode": "delta",
    "commit": "d" * 40,
    "tree_clean": False,
    "ran_at": "2030-01-02T06:00:00Z",
    "decision": "GO",
    "findings": [],
    "inputs": {"caption_sha256": "e" * 64},
    "prior_sha256": "c" * 64,
}


def _signed(document: dict, key: str = KEY) -> dict:
    secret = key.encode("utf-8")
    covered = {k: v for k, v in document.items() if k != "signature"}
    message = json.dumps(covered, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return {**covered, "signature": {"alg": "HMAC-SHA256",
                                     "key_id": hashlib.sha256(secret).hexdigest()[:16],
                                     "value": hmac.new(secret, message,
                                                       hashlib.sha256).hexdigest()}}


def _file(base: pathlib.Path, document: dict, name: str = "artifact.json") -> pathlib.Path:
    path = base / name
    path.write_bytes((json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return path


def _verify(path, capsys, env=ENV):
    code = drill_read.verify_main([str(path)], env=env)
    return code, capsys.readouterr().out.splitlines()


# --- read ----------------------------------------------------------------------------

def test_read_prints_specs_lines_in_specs_order_for_a_no_go(tmp_path, capsys):
    path = _file(tmp_path, _signed(NO_GO))
    assert cli.main(["drill", "read", str(path)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "decision=NO-GO",
        "mode=full",
        f"commit={'a' * 40}",
        "tree_clean=true",
        "ran_at=2030-01-02T03:04:05Z",
        "fix_by=2030-01-02T05:04:05Z",
        "fix_window_s=7200",
        "owner.seat=synthetic-seat",
        "owner.oncall=webhook:synthetic-oncall",
        f"caption_sha256={'b' * 64}",
        "prior_sha256=-",
        "finding=caption-check/max-gap/s01/s03",
    ]


def test_read_prints_a_dash_for_every_absent_field_of_a_go(tmp_path, capsys):
    path = _file(tmp_path, _signed(GO_DELTA))
    assert drill_read.read_main([str(path)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "decision=GO", "mode=delta", f"commit={'d' * 40}", "tree_clean=false",
        "ran_at=2030-01-02T06:00:00Z", "fix_by=-", "fix_window_s=-", "owner.seat=-",
        "owner.oncall=-", f"caption_sha256={'e' * 64}", f"prior_sha256={'c' * 64}",
    ]


def test_read_prints_one_finding_line_per_finding_in_file_order(tmp_path, capsys):
    second = {"scenario": "caption-check", "rule": "max-gap", "after_cue": "s07",
              "before_cue": "s09", "gap_s": 4.5}
    path = _file(tmp_path, {**NO_GO, "findings": [*NO_GO["findings"], second]})
    assert drill_read.read_main([str(path)]) == 0
    findings = [line for line in capsys.readouterr().out.splitlines()
                if line.startswith("finding=")]
    assert findings == ["finding=caption-check/max-gap/s01/s03",
                        "finding=caption-check/max-gap/s07/s09"]


def test_read_decides_nothing_it_prints_an_unsigned_invalid_document(tmp_path, capsys):
    path = _file(tmp_path, {**NO_GO, "undeclared": 1, "ran_at": "not a time"})
    assert drill_read.read_main([str(path)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert "decision=NO-GO" in out
    assert "fix_window_s=-" in out


@pytest.mark.parametrize("content", [b"not json", b"[1, 2]", b"\xff\xfe"])
def test_read_exits_2_on_an_unreadable_file(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_bytes(content)
    assert drill_read.read_main([str(path)]) == 2


def test_read_exits_2_on_a_missing_file_or_a_wrong_argument_count(tmp_path):
    assert drill_read.read_main([str(tmp_path / "absent.json")]) == 2
    assert drill_read.read_main([]) == 2
    assert drill_read.read_main(["a", "b"]) == 2


# --- verify --------------------------------------------------------------------------

def test_verify_exits_0_on_a_well_formed_artifact_signature_first(tmp_path, capsys):
    """F3's liveness: SPEC/11 runs this before any edited copy is read. It is not
    evidence -- one key and one canonical form make it true by construction."""
    code, out = _verify(_file(tmp_path, _signed(NO_GO)), capsys)
    assert (code, out) == (0, ["signature: OK", "schema: OK"])
    code, out = _verify(_file(tmp_path, _signed(GO_DELTA), "go.json"), capsys)
    assert (code, out) == (0, ["signature: OK", "schema: OK"])


@pytest.mark.parametrize("old, new", [
    (b'"decision": "NO-GO"', b'"decision": "GO"'),
    (b'"oncall": "webhook:synthetic-oncall"', b'"oncall": "webhook:someone-else"'),
    (b'"fix_by": "2030-', b'"fix_by": "2031-'),
])
def test_f3s_three_edits_each_exit_1_with_signature_mismatch(tmp_path, capsys, old, new):
    original = _file(tmp_path, _signed(NO_GO))
    edited = tmp_path / "edited.json"
    raw = original.read_bytes()
    assert raw.count(old) == 1, f"the plant's anchor {old!r} is not unique in the artifact"
    edited.write_bytes(raw.replace(old, new))
    assert edited.read_bytes() != raw, "the plant did not change the bytes"
    code, out = _verify(edited, capsys)
    assert (code, out) == (1, ["signature: MISMATCH"])


def test_the_signature_is_checked_before_the_schema(tmp_path, capsys):
    """Constraint 5. The same edit, an undeclared key, through both doors: unsigned it is
    a MISMATCH and the schema is never read; re-signed it passes the signature and is
    refused by the schema."""
    tampered = {**_signed(NO_GO), "undeclared": 1}
    code, out = _verify(_file(tmp_path, tampered, "unsigned.json"), capsys)
    assert (code, out) == (1, ["signature: MISMATCH"])

    resigned = _signed({**NO_GO, "undeclared": 1})
    code, out = _verify(_file(tmp_path, resigned, "resigned.json"), capsys)
    assert code == 2
    assert out[0] == "signature: OK"
    assert out[1].startswith("schema: INVALID")


def test_verify_reads_whitespace_as_nothing_and_content_as_everything(tmp_path, capsys):
    """The form that is signed is the canonical one, so re-indenting the file is not an
    edit and changing one value is."""
    document = _signed(NO_GO)
    compact = tmp_path / "compact.json"
    compact.write_text(json.dumps(document), encoding="utf-8")
    assert _verify(compact, capsys)[0] == 0


@pytest.mark.parametrize("mutate", [
    lambda sig: {**sig, "alg": "HMAC-SHA512"},
    lambda sig: {**sig, "key_id": "0" * 16},
    lambda sig: {**sig, "value": "0" * 64},
    lambda sig: {"alg": sig["alg"], "key_id": sig["key_id"]},
    lambda sig: "not an object",
])
def test_the_algorithm_the_key_id_and_the_value_must_all_hold(tmp_path, capsys, mutate):
    document = _signed(NO_GO)
    document["signature"] = mutate(document["signature"])
    assert _verify(_file(tmp_path, document), capsys) == (1, ["signature: MISMATCH"])


def test_a_missing_signature_is_a_mismatch_not_unreadable(tmp_path, capsys):
    assert _verify(_file(tmp_path, NO_GO), capsys) == (1, ["signature: MISMATCH"])


def test_another_key_is_a_mismatch(tmp_path, capsys):
    path = _file(tmp_path, _signed(NO_GO))
    other = {"BEACONPAVE_DRILL_KEY": "another-synthetic-key-of-enough-bytes-00"}
    assert _verify(path, capsys, env=other) == (1, ["signature: MISMATCH"])


@pytest.mark.parametrize("env", [{}, {"BEACONPAVE_DRILL_KEY": ""},
                                 {"BEACONPAVE_DRILL_KEY": "k" * 31}])
def test_no_key_exits_2_before_anything_is_read(tmp_path, capsys, env):
    code, out = _verify(_file(tmp_path, _signed(NO_GO)), capsys, env=env)
    assert (code, out) == (2, [])


def test_verify_exits_2_on_an_unreadable_file_or_a_wrong_argument_count(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"not json")
    assert _verify(bad, capsys) == (2, [])
    assert drill_read.verify_main([], env=ENV) == 2


def test_the_cli_dispatches_verify_with_the_process_environment(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BEACONPAVE_DRILL_KEY", KEY)
    assert cli.main(["drill", "verify", str(_file(tmp_path, _signed(NO_GO)))]) == 0
    assert capsys.readouterr().out.splitlines() == ["signature: OK", "schema: OK"]


# --- the writer's output, read by readers that share nothing with it -----------------

def _git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=drill-test",
         "-c", "user.email=drill-test@example.invalid", "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True)


def test_what_the_writer_writes_the_readers_verify_and_print(tmp_path, capsys):
    root = tmp_path / "repo"
    (root / "drill" / "scenarios").mkdir(parents=True)
    _git(root, "init", "-q")
    _git(root, "config", "core.autocrlf", "false")
    (root / drill.SCENARIO_FILE).write_text(json.dumps({
        "scenario": "caption-check", "rule": "max-gap", "max_gap_s": 1.0,
        "owner": {"seat": "synthetic-seat", "oncall": "webhook:synthetic-oncall"},
        "fix_by_window_s": {"7": 90},
        "events": {"synthetic-event": {"captions": "captions.vtt"}},
    }), encoding="utf-8")
    (root / "captions.vtt").write_bytes(
        b"WEBVTT\n\ns01\n00:00:00.000 --> 00:00:01.000\na\n\n"
        b"s02\n00:00:03.000 --> 00:00:04.000\nb\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "synthetic")
    out = tmp_path / "written.json"
    drill.run("synthetic-event", 7, out, root=root, env=ENV)

    assert _verify(out, capsys) == (0, ["signature: OK", "schema: OK"])
    assert drill_read.read_main([str(out)]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert "decision=NO-GO" in printed
    assert "fix_window_s=90" in printed
    assert "finding=caption-check/max-gap/s01/s02" in printed


# --- constraint 6, read from the code --------------------------------------------------

READERS_MAY_IMPORT = {"__future__", "datetime", "hashlib", "hmac", "json", "os", "pathlib",
                      "sys", "jsonschema"}


def _tree(name: str) -> ast.Module:
    return ast.parse((ROOT / "pave" / name).read_text(encoding="utf-8"))


def test_the_readers_import_nothing_from_the_writer_or_any_pave_module():
    imported = set()
    for node in ast.walk(_tree("drill_read.py")):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add("." if node.level else node.module.split(".")[0])
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id in {"__import__", "exec", "eval"}):
            imported.add(node.func.id)
    assert imported <= READERS_MAY_IMPORT, sorted(imported - READERS_MAY_IMPORT)


def _top_level_names(name: str) -> set:
    names = set()
    for node in _tree(name).body:
        if isinstance(node, ast.FunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_the_readers_and_the_writer_define_no_top_level_name_in_common():
    """No shared constant, even by copy-and-rename-later: a name both modules define is
    the first step to one importing it from the other."""
    shared = _top_level_names("drill_read.py") & _top_level_names("drill.py")
    assert not shared, f"pave/drill_read.py and pave/drill.py both define {sorted(shared)}"
