"""
The drill's readers: `pave drill read` prints a go/no-go artifact's fields, `pave drill
verify` checks its signature.

Every SPEC/11 falsifier names one of these two commands, so **they share nothing with the
writer in `pave/drill.py`** (constraint 6):
- not a module;
- not a constant;
- not the canonical form;
- not the schema loader.

Each rule below is re-stated from SPEC/11's pinned table, on purpose. Suppose the writer's
canonical form dropped `decision`:
- a verifier importing that form would drop it too, and accept an edit to it;
- a verifier written from the pin refuses the edit, which is F3 firing.

**`read` decides nothing.** It prints what the file holds, `-` where a field is absent,
and computes one number, `fix_window_s`, from the two fields it prints beside it. It does
not verify and it does not validate.

**`verify` checks the signature before the schema** (constraint 5). An edit that also
breaks the schema must still be refused as a signature mismatch. If the schema were checked
first, a signature that never covered the edited field would hide behind a schema error,
and the edit would be refused through the wrong door.

**Both refuse a document they cannot read one way only** (Security seat, M11 PR 2).
- **Duplicate keys.** A key written twice is read as its last value by `json.loads`,
  and as its first value by `grep` or another parser. An edit placed ahead of the real
  key would pass `verify` while telling a human reader something else.
- **Values that cannot be serialised or printed** (a lone surrogate, nesting too deep to
  parse). They exit 2 with an error, never 1 with no `signature:` line, and never
  `signature: OK`.

Exit codes:
- `verify`, pinned by SPEC/11: 0 prints `signature: OK` and then `schema: OK`; 1 prints
  `signature: MISMATCH`; 2 means unreadable, or no key.
- `verify`, **decided here and not pinned**: a good signature over a schema-invalid
  artifact prints `schema: INVALID` and exits 2. The writer validates before it writes, so
  only someone holding the key can produce one.
- `read`, **decided here; SPEC/11 pins no exit code for it** (AI Quality seat, M11 PR 2):
  0 printed; 2 unreadable.

Owning seat: AI Quality (what a falsifier reads) - Platform Engineering (the code).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import pathlib
import sys

import jsonschema

REPO = pathlib.Path(__file__).resolve().parents[1]
GO_NO_GO_SCHEMA = REPO / "quality" / "drill" / "go-no-go.schema.json"
DRILL_KEY_VARIABLE = "BEACONPAVE_DRILL_KEY"
SHORTEST_KEY = 32
SECOND = "%Y-%m-%dT%H:%M:%SZ"

#: SPEC/11's `pave drill read` line order. `finding=` lines follow, one per finding.
PRINTED = ("decision", "mode", "commit", "tree_clean", "ran_at", "fix_by", "fix_window_s",
           "owner.seat", "owner.oncall", "caption_sha256", "prior_sha256")


class Unreadable(Exception):
    """A document these readers refuse to read. Exit 2."""


def _no_duplicate_keys(pairs):
    names = [name for name, _ in pairs]
    if len(names) != len(set(names)):
        twice = sorted({name for name in names if names.count(name) > 1})
        raise Unreadable(f"the key(s) {twice} appear more than once in one object, so "
                         "different readers would see different values")
    return dict(pairs)


def _open(path) -> dict:
    try:
        raw = pathlib.Path(path).read_bytes()
    except OSError as exc:
        raise Unreadable(f"cannot read {path}: {exc}") from exc
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except Unreadable as exc:
        raise Unreadable(f"{path}: {exc}") from exc
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Unreadable(f"{path} is not JSON: {type(exc).__name__}: {exc}") from exc
    if not isinstance(document, dict):
        raise Unreadable(f"{path} is not a JSON object")
    return document


def _at(document: dict, *keys: str):
    node = document
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _shown(value) -> str:
    if value is None:
        return "-"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _window_seconds(document: dict):
    try:
        opened = dt.datetime.strptime(document["ran_at"], SECOND)
        due = dt.datetime.strptime(document["fix_by"], SECOND)
    except (KeyError, TypeError, ValueError):
        return None
    return int((due - opened).total_seconds())


def lines_for(document: dict) -> list[str]:
    values = {
        "decision": _at(document, "decision"),
        "mode": _at(document, "mode"),
        "commit": _at(document, "commit"),
        "tree_clean": _at(document, "tree_clean"),
        "ran_at": _at(document, "ran_at"),
        "fix_by": _at(document, "fix_by"),
        "fix_window_s": _window_seconds(document),
        "owner.seat": _at(document, "owner", "seat"),
        "owner.oncall": _at(document, "owner", "oncall"),
        "caption_sha256": _at(document, "inputs", "caption_sha256"),
        "prior_sha256": _at(document, "prior_sha256"),
    }
    printed = [f"{name}={_shown(values[name])}" for name in PRINTED]
    findings = document.get("findings")
    for finding in findings if isinstance(findings, list) else []:
        parts = finding if isinstance(finding, dict) else {}
        printed.append("finding=" + "/".join(
            _shown(parts.get(part)) for part in ("scenario", "rule", "after_cue", "before_cue")))
    return printed


def read_main(argv) -> int:
    if len(argv) != 1:
        print("usage: pave drill read <artifact>", file=sys.stderr)
        return 2
    try:
        document = _open(argv[0])
        printed = lines_for(document)
        for line in printed:
            line.encode("utf-8")  # a lone surrogate is refused before anything is printed
    except (Unreadable, UnicodeError, RecursionError) as exc:
        print(f"error: {type(exc).__name__}: {exc!s}".encode("ascii", "backslashreplace")
              .decode("ascii"), file=sys.stderr)
        return 2
    try:
        for line in printed:
            print(line)
    except (UnicodeEncodeError, OSError) as exc:
        print(f"error: this console cannot print the artifact: {exc}", file=sys.stderr)
        return 2
    return 0


def signature_holds(document: dict, secret: bytes) -> bool:
    """SPEC/11's pin, re-stated: HMAC-SHA256 under `secret`, over the artifact minus
    `signature`, serialised with sorted keys, `(",", ":")` separators and
    `ensure_ascii=False`, as UTF-8; `key_id` is the first 16 hex of sha256(secret). The
    algorithm, the key id AND the value must all hold. A document this cannot serialise
    raises; the caller exits 2, and never prints OK."""
    held = document.get("signature")
    if not isinstance(held, dict) or held.get("alg") != "HMAC-SHA256":
        return False
    key_id, value = held.get("key_id"), held.get("value")
    if not isinstance(key_id, str) or not isinstance(value, str):
        return False
    covered = {name: part for name, part in document.items() if name != "signature"}
    message = json.dumps(covered, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    expected_value = hmac.new(secret, message, hashlib.sha256).hexdigest()
    expected_id = hashlib.sha256(secret).hexdigest()[:16]
    same_id = hmac.compare_digest(key_id.encode("utf-8", "surrogatepass"),
                                  expected_id.encode("utf-8"))
    same_value = hmac.compare_digest(value.encode("utf-8", "surrogatepass"),
                                     expected_value.encode("utf-8"))
    return same_id and same_value


def verify_main(argv, env=None) -> int:
    env = os.environ if env is None else env
    if len(argv) != 1:
        print("usage: pave drill verify <artifact>", file=sys.stderr)
        return 2
    secret = (env.get(DRILL_KEY_VARIABLE) or "").encode("utf-8")
    if len(secret) < SHORTEST_KEY:
        print(f"error: no key: {DRILL_KEY_VARIABLE} is unset or shorter than {SHORTEST_KEY} "
              "bytes", file=sys.stderr)
        return 2
    try:
        document = _open(argv[0])
    except Unreadable as exc:
        print(f"error: {exc!s}".encode("ascii", "backslashreplace").decode("ascii"),
              file=sys.stderr)
        return 2

    # The signature, first and alone. Nothing about the document is judged before this,
    # and a check that cannot complete is exit 2 -- never OK, never a silent exit 1.
    try:
        holds = signature_holds(document, secret)
    except Exception as exc:  # noqa: BLE001 - any failure to check is not a pass
        print(f"error: the signature could not be checked: {type(exc).__name__}", file=sys.stderr)
        return 2
    if not holds:
        print("signature: MISMATCH")
        return 1
    print("signature: OK")

    try:
        schema = json.loads(GO_NO_GO_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read the go/no-go schema: {exc}", file=sys.stderr)
        return 2
    problems = sorted(jsonschema.Draft7Validator(schema).iter_errors(document), key=str)
    if problems:
        print(f"schema: INVALID - {problems[0].message}")
        return 2
    print("schema: OK")
    return 0
