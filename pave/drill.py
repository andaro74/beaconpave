"""
The drill's writer: run the caption check for one event, write a signed go/no-go artifact.

SPEC/11 and ADR-080 are the rules. This module is the only thing that applies them to an
event, and it is claim 11's subject: what it decides is what the falsifiers read.

**What it will not do**, each a SPEC/11 constraint:

1. **Route anything through `pave.verdict.build`**, or read the verdict schema. It imports
   no `pave` module at all. The artifact has its own schema,
   `quality/drill/go-no-go.schema.json`.
3. **Default a claim value.** The owner, the fix-by window, the gap threshold and the
   event's caption source come from `drill/scenarios/caption-check.json` at run time. A
   missing one exits 2 and writes nothing.
4. **Write without a key.** No key, no artifact.

It also **never overwrites an artifact.** SPEC/11 repeats no run, so an `--out` that
already exists exits 2 and leaves the file untouched.

**The readers share nothing with it** (constraint 6). `pave drill read` and
`pave drill verify` live in `pave/drill_read.py` and re-state the canonical form from
SPEC/11's pin, so a canonical form here that dropped a field would be refused there.

**A delta drill** (`--delta PRIOR`) builds on a NO-GO. It requires:
- the prior's signature verifies;
- the prior is for the same event and tier;
- the prior names at least one finding.

It then re-runs the scenarios those findings name **against the bytes on disk now**, and
records `prior_sha256` over the prior file's bytes. It carries nothing forward from the
prior: not its findings, not its owner, not its fix-by time. A delta that re-checked only
changed paths, or trusted the prior's findings, is the defect F4 exists to catch.

Exit codes, pinned in SPEC/11: 0 GO written, 1 NO-GO written, 2 nothing written.

Hermetic: one scenario file, one caption file, and git. No network, no model.
Owning seat: Platform Engineering (the writer) - AI Quality (what it decides).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "quality" / "drill" / "go-no-go.schema.json"
SCENARIO_FILE = "drill/scenarios/caption-check.json"
KEY_ENV = "BEACONPAVE_DRILL_KEY"
MIN_KEY_BYTES = 32

EXIT_GO = 0
EXIT_NO_GO = 1
EXIT_NOTHING = 2

UTC_SECOND = "%Y-%m-%dT%H:%M:%SZ"
_STAMP = r"(?:(\d+):)?(\d{2}):(\d{2})\.(\d{3})"
_TIMING = re.compile(rf"^{_STAMP}[ \t]+-->[ \t]+{_STAMP}(?:[ \t].*)?$")


class Refused(Exception):
    """A reason the writer writes nothing. The command exits 2."""


@dataclass(frozen=True)
class Scenario:
    name: str
    rule: str
    threshold_ms: int
    seat: str
    oncall: str
    windows: dict
    events: dict

    def window_for(self, tier: int) -> int:
        window = self.windows.get(str(tier))
        if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
            raise Refused(f"the scenario file has no fix-by window for tier {tier}, and the "
                          "writer has no default for it (SPEC/11 constraint 3)")
        return window

    def captions_for(self, event: str) -> str:
        entry = self.events.get(event)
        source = entry.get("captions") if isinstance(entry, dict) else None
        if not isinstance(source, str) or not source:
            raise Refused(f"the scenario file names no caption source for event {event!r}, and "
                          "the writer has no default for it (SPEC/11 constraint 3)")
        return source


def _required(data: dict, *path: str):
    node = data
    for part in path:
        if not isinstance(node, dict) or part not in node:
            raise Refused(f"the scenario file has no `{'.'.join(path)}`, and the writer has no "
                          "default for it (SPEC/11 constraint 3)")
        node = node[part]
    return node


def _text(data: dict, *path: str) -> str:
    value = _required(data, *path)
    if not isinstance(value, str) or not value:
        raise Refused(f"the scenario file's `{'.'.join(path)}` is not a non-empty string")
    return value


def load_scenario(root: pathlib.Path) -> Scenario:
    path = root / SCENARIO_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Refused(f"cannot read the scenario file {SCENARIO_FILE}: {exc}") from exc
    if not isinstance(data, dict):
        raise Refused(f"the scenario file {SCENARIO_FILE} is not a JSON object")
    threshold = _required(data, "max_gap_s")
    if isinstance(threshold, bool) or not isinstance(threshold, int | float) or threshold < 0:
        raise Refused("the scenario file's `max_gap_s` is not a non-negative number of seconds")
    rule = _text(data, "rule")
    if rule != "max-gap":
        raise Refused(f"the scenario file names rule {rule!r}; this writer implements `max-gap`")
    windows = _required(data, "fix_by_window_s")
    events = _required(data, "events")
    if not isinstance(windows, dict) or not isinstance(events, dict):
        raise Refused("the scenario file's `fix_by_window_s` and `events` must be objects")
    return Scenario(
        name=_text(data, "scenario"),
        rule=rule,
        threshold_ms=round(threshold * 1000),
        seat=_text(data, "owner", "seat"),
        oncall=_text(data, "owner", "oncall"),
        windows=windows,
        events=events,
    )


def _ms(hours, minutes, seconds, millis) -> int:
    return (int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(millis)


def parse_cues(text: str) -> list[tuple[str, int, int]]:
    """`(cue id, start ms, end ms)` in file order. A cue with no id is refused: a finding
    names the cues either side of a gap, and an unnamed cue cannot be named."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("WEBVTT"):
        raise Refused("the caption file is not WebVTT: its first line is not `WEBVTT`")
    body = lines[1:]
    # The header runs to the first blank line.
    while body and body[0].strip():
        body = body[1:]
    blocks, current = [], []
    for line in body:
        if line.strip():
            current.append(line.rstrip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    cues, seen = [], set()
    for block in blocks:
        if block[0].startswith(("NOTE", "STYLE", "REGION")):
            continue
        timing = [i for i, line in enumerate(block) if "-->" in line]
        if not timing:
            raise Refused(f"a caption block has no timing line: {block[0]!r}")
        if timing[0] != 1:
            raise Refused(f"a cue has no id, so no finding could name it: {block[timing[0]]!r}")
        cue_id = block[0].strip()
        match = _TIMING.match(block[1].strip())
        if not match:
            raise Refused(f"cue {cue_id}: unreadable timing line {block[1]!r}")
        stamps = match.groups()
        start, end = _ms(*stamps[:4]), _ms(*stamps[4:])
        if end < start:
            raise Refused(f"cue {cue_id} ends before it starts")
        if cue_id in seen:
            raise Refused(f"cue id {cue_id} appears twice")
        seen.add(cue_id)
        cues.append((cue_id, start, end))
    return cues


def max_gap_findings(cues, threshold_ms: int, scenario: str, rule: str) -> list[dict]:
    """One finding per pair of consecutive cues whose gap is GREATER than the threshold."""
    findings = []
    for (after, _, after_end), (before, before_start, _) in zip(cues, cues[1:], strict=False):
        gap = before_start - after_end
        if gap > threshold_ms:
            findings.append({"scenario": scenario, "rule": rule, "after_cue": after,
                             "before_cue": before, "gap_s": gap / 1000})
    return findings


def _git(root: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def head_commit(root: pathlib.Path) -> str:
    result = _git(root, "rev-parse", "HEAD")
    sha = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise Refused(f"cannot name the commit under drill at {root}: {result.stderr.strip()}")
    return sha


def tree_is_clean(root: pathlib.Path) -> bool:
    result = _git(root, "status", "--porcelain")
    if result.returncode != 0:
        raise Refused(f"cannot read the tree state at {root}: {result.stderr.strip()}")
    return result.stdout.strip() == ""


def load_key(env) -> bytes:
    raw = env.get(KEY_ENV) or ""
    key = raw.encode("utf-8")
    if not key:
        raise Refused(f"no key in {KEY_ENV}: no key, no artifact (SPEC/11 constraint 4)")
    if len(key) < MIN_KEY_BYTES:
        raise Refused(f"the key in {KEY_ENV} is {len(key)} bytes; SPEC/11 pins at least "
                      f"{MIN_KEY_BYTES}")
    return key


def sign(artifact: dict, key: bytes) -> dict:
    unsigned = {name: value for name, value in artifact.items() if name != "signature"}
    message = json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return {"alg": "HMAC-SHA256",
            "key_id": hashlib.sha256(key).hexdigest()[:16],
            "value": hmac.new(key, message, hashlib.sha256).hexdigest()}


def load_prior(path, key: bytes, event: str, tier: int) -> tuple[str, set]:
    """The prior's sha256 and the scenarios its findings name, or Refused."""
    try:
        raw = pathlib.Path(path).read_bytes()
        prior = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Refused(f"cannot read the prior artifact {path}: {exc}") from exc
    if not isinstance(prior, dict):
        raise Refused(f"the prior artifact {path} is not a JSON object")
    held, expected = prior.get("signature"), sign(prior, key)
    if not (isinstance(held, dict) and held.get("alg") == expected["alg"]
            and held.get("key_id") == expected["key_id"]
            and isinstance(held.get("value"), str)
            and hmac.compare_digest(held["value"].encode("utf-8"),
                                    expected["value"].encode("utf-8"))):
        raise Refused(f"the prior artifact's signature does not verify: a delta drill does not "
                      f"build on an artifact it cannot trust ({path})")
    if prior.get("event") != event or prior.get("tier") != tier:
        raise Refused(f"the prior artifact is for event {prior.get('event')!r} tier "
                      f"{prior.get('tier')!r}, not event {event!r} tier {tier!r}")
    findings = prior.get("findings")
    if not isinstance(findings, list) or not findings:
        raise Refused("the prior artifact names no finding: a delta drill re-runs what a NO-GO "
                      "named, and a GO names nothing")
    scenarios = {f.get("scenario") for f in findings if isinstance(f, dict)}
    return hashlib.sha256(raw).hexdigest(), scenarios


def build_artifact(*, event, tier, mode, commit, tree_clean, ran_at, findings, scenario,
                   window_s, caption_sha256, prior_sha256) -> dict:
    artifact = {
        "event": event,
        "tier": tier,
        "mode": mode,
        "commit": commit,
        "tree_clean": tree_clean,
        "ran_at": ran_at.strftime(UTC_SECOND),
        "decision": "NO-GO" if findings else "GO",
        "findings": findings,
        "inputs": {"caption_sha256": caption_sha256},
    }
    if findings:
        artifact["owner"] = {"seat": scenario.seat, "oncall": scenario.oncall}
        artifact["fix_by"] = (ran_at + dt.timedelta(seconds=window_s)).strftime(UTC_SECOND)
    if prior_sha256 is not None:
        artifact["prior_sha256"] = prior_sha256
    return artifact


def run(event: str, tier: int, out, delta=None, *, root=None, env=None, now=None) -> dict:
    """Write one artifact and return it, or raise Refused having written nothing."""
    root = pathlib.Path(ROOT if root is None else root)
    env = os.environ if env is None else env
    out = pathlib.Path(out)

    key = load_key(env)
    if out.exists():
        raise Refused(f"{out} already exists: an artifact is never overwritten, and SPEC/11 "
                      "repeats no run")
    scenario = load_scenario(root)
    window = scenario.window_for(tier)
    source = scenario.captions_for(event)

    prior_sha256 = None
    if delta is not None:
        prior_sha256, named = load_prior(delta, key, event, tier)
        if named != {scenario.name}:
            raise Refused(f"the prior's findings name scenario(s) {sorted(map(str, named))}; "
                          f"this writer runs {scenario.name!r}")

    try:
        caption_bytes = (root / source).read_bytes()
        captions = caption_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refused(f"cannot read the caption file {source}: {exc}") from exc
    findings = max_gap_findings(parse_cues(captions), scenario.threshold_ms,
                                scenario.name, scenario.rule)

    commit = head_commit(root)
    clean = tree_is_clean(root)
    ran_at = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    artifact = build_artifact(
        event=event, tier=tier, mode="full" if delta is None else "delta", commit=commit,
        tree_clean=clean, ran_at=ran_at.replace(microsecond=0), findings=findings,
        scenario=scenario, window_s=window,
        caption_sha256=hashlib.sha256(caption_bytes).hexdigest(), prior_sha256=prior_sha256)
    artifact["signature"] = sign(artifact, key)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft7Validator(schema).iter_errors(artifact), key=str)
    if errors:
        raise Refused(f"the artifact does not conform to quality/drill/go-no-go.schema.json, "
                      f"so nothing is written: {errors[0].message}")

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "xb") as handle:
        handle.write((json.dumps(artifact, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return artifact


def main(argv) -> int:
    parser = argparse.ArgumentParser(
        prog="pave drill",
        description="Run the caption check for an event and write a signed go/no-go "
                    "artifact. Exit 0 GO written, 1 NO-GO written, 2 nothing written.")
    parser.add_argument("--event", required=True)
    parser.add_argument("--tier", required=True, type=int)
    parser.add_argument("--out", required=True)
    parser.add_argument("--delta", metavar="PRIOR")
    try:
        args = parser.parse_args(list(argv))
    except SystemExit:
        # A malformed command, or --help: nothing written, so 2 -- never 0, which means GO.
        return EXIT_NOTHING

    try:
        artifact = run(args.event, args.tier, args.out, args.delta)
    except Refused as exc:
        print(f"drill: nothing written - {exc}", file=sys.stderr)
        return EXIT_NOTHING
    except Exception as exc:  # noqa: BLE001 - any crash writes nothing, and 1 means NO-GO
        print(f"drill: nothing written - unexpected {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return EXIT_NOTHING

    for finding in artifact["findings"]:
        print(f"  finding: {finding['scenario']}/{finding['rule']} gap {finding['gap_s']:.3f} s "
              f"between {finding['after_cue']} and {finding['before_cue']}")
    if artifact["decision"] == "NO-GO":
        print(f"drill: NO-GO - owner {artifact['owner']['seat']} "
              f"({artifact['owner']['oncall']}), fix by {artifact['fix_by']}; "
              f"written {args.out}")
        return EXIT_NO_GO
    print(f"drill: GO - written {args.out}")
    return EXIT_GO
