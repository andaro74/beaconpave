"""What a row in `evals/history/` may claim, and what may happen to one that is there.

ADR-042. Every check this module holds was measured absent first: a schema-valid
24/25 row appended beside the real 19/25 left 1701 tests and the gate green; an
arm recorded asking three of eleven probes set its own floor at three; a
committed entry could be rewritten and re-pinned in one commit; and the one
protection that did exist -- three digests in a test file -- ran under a pytest
harness that `pyproject.toml` can deselect and `tests/conftest.py` can re-base,
both on zero keys.

So the checks live here, as functions, and run two ways:

- `pave gate history --base <sha>` in `quality-gate.yml`, which is the instance
  that DECIDES. The base arrives as an explicit argument from the event payload;
  no environment variable and no test collection stands between the workflow
  and the check, and its verdict is one `gate decide` requires.
- `tests/test_history_append_only.py`, the local mirror under `make check`,
  which also holds the violating-tree tests that prove each check is reachable.

Three threats, named in ADR-042:

- T1a -- a fabricated row is appended, claiming a NUMBER. Residual: the row is
  pinned, self-consistent, anchored to committed evidence, and attested on
  three keys. Pinning a row does not make it true; this module never claims so.
- T1b -- a fabricated row is appended, claiming a DENOMINATOR. Bounded: an
  adversarial entry's `scores.total` must equal the corpus size registered for
  the instrument it names, and that registration must resolve to a committed
  revision of the corpus with that many probes.
- T2 -- a committed row is edited, renamed, deleted, or typechanged. Caught by
  a diff against the merge-base with rename detection OFF.

Every function returns a list of problems; an empty list is a pass. A check
that cannot run -- no git, a shallow clone, no resolvable base -- raises
`Refusal`, which callers must surface as a FAILURE with the message, never as a
skip. A check that passes because it could not see is the `rules_validate`
hazard this repository has recorded before.

Owning seats: AI Quality (the recorded numbers) · Security / Red Team (what a
probe passing means, the corpus registry) · Platform Engineering (the
recorders, the lane, the workflow). Three keys, same as the directory.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
from collections.abc import Mapping, Sequence

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals" / "history"
PINS_NAME = "pins.json"
SCHEMA_NAME = "schema.json"
#: The files that are not entries and may be MODIFIED by honest work.
NOT_ENTRIES = frozenset({PINS_NAME, SCHEMA_NAME})
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PROBES = "quality/adversarial/probes.yaml"
INSTRUMENTS = ROOT / "quality" / "adversarial" / "instruments.json"
GOLDEN_CASES = "services/highlights-agent/evals/golden/cases.yaml"

#: Top-level `required` of the history schema, pinned (ADR-042 decision 7). A
#: new requirement lives under an `if/then` that no committed entry fails --
#: and the test that holds that line is `test_the_committed_entries_still_validate`.
SCHEMA_REQUIRED = ("sha", "suite", "recorded_at", "target", "scores")

#: The eight entries that existed when ADR-042 landed, by name. Closed: decision
#: 2's completeness pin means nothing joins this set without the same three keys.
LEGACY_ENTRIES = frozenset({
    "m00b-adversarial.json",
    "m00b-goldens.json",
    "m00b-judged-B-goldens.json",
    "m01-adversarial.json",
    "m01-goldens.json",
    "m02-control-goldens.json",
    "m02-tools-goldens.json",
    "m04-adversarial.json",
})

#: The four legacy entries recorded before either recorder wrote `samples_from`.
#: Their evidence is committed (`milestones/M00b|M01/{goldens,probes}-run.json`);
#: a `--supersedes` correction of any of them can carry it.
LEGACY_WITHOUT_EVIDENCE = frozenset({
    "m00b-adversarial.json",
    "m00b-goldens.json",
    "m01-adversarial.json",
    "m01-goldens.json",
})

#: An evidence file that was legitimately revised after an entry digested it.
#: `{entry: [(recorded_digest, revised_digest, why), ...]}` -- a chain, appended
#: to, never overwritten. The entry's `samples_from.sha256` must equal the first
#: digest of the chain and the committed file must digest to the last.
#:
#: NOT a grandfather list: each row names a specific change, its PR and its
#: reason, and a second row needs three keys and the same kind of sentence.
EVIDENCE_REVISIONS: dict[str, list[tuple[str, str, str]]] = {
    "m04-adversarial.json": [
        # The recorded digest is the CRLF rendering of the `ad50cc6` blob (whose
        # normalised digest is a333fd88...). PR #51 / ADR-041 decision 1 added
        # the `_asked` manifest to the observation file; every sample in it is
        # unchanged. The committed file now digests to 00605955...
        ("8bac78947a16d09b3856d1abd062f4cdfb8d5a2e22f32eb05a74d084a4725342",
         "00605955fb3c4d8d24086507b702c711e6dabbe8c45b6dfe2734f3d67dcb8e70",
         "PR #51 / ADR-041 added the `_asked` manifest; samples unchanged"),
    ],
}

#: README progression rows tied to a goldens entry, by tag (ADR-042 decision 2).
#: Pinned per tag because `m00b` has two goldens entries and `m02` two arms, so
#: "some entry with this tag matches" lets a row move to the other one.
README_GOLDENS = {
    "m00b": "m00b-goldens.json",
    "m01": "m01-goldens.json",
    "m02": "m02-tools-goldens.json",
}


class Refusal(Exception):
    """The check could not run. Surface as a failure with this message; never skip."""


# --- digests -----------------------------------------------------------------

def normalised(text: str) -> str:
    """A line ending is not content. Committed blobs are LF; a Windows working
    tree with `core.autocrlf` materialises CRLF. "Has this changed" is a question
    about what a file says, so every digest here is taken over normalised text."""
    return text.replace("\r\n", "\n")


def entry_digest(text: str) -> str:
    return hashlib.sha256(normalised(text).encode("utf-8")).hexdigest()


def crlf_digest(text: str) -> str:
    """The digest both recorders wrote before ADR-042 on a CRLF tree. Accepted
    for `LEGACY_ENTRIES` only, by name, as a stated tolerance."""
    return hashlib.sha256(normalised(text).replace("\n", "\r\n").encode("utf-8")).hexdigest()


def corpus_digest(text: str) -> str:
    """`evals/adversarial.py::_digest` over one part, which is how `probes_sha256`
    is computed. Duplicated rather than imported so this module's git-resolving
    check does not import the scorer it is partly checking."""
    h = hashlib.sha256()
    h.update(normalised(text).encode("utf-8"))
    h.update(b"\x00")
    return h.hexdigest()


# --- git ---------------------------------------------------------------------

def _git(*args: str, cwd: pathlib.Path = ROOT) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)
    except FileNotFoundError as exc:
        raise Refusal("`git` is not on PATH, so the append-only and corpus checks cannot run. "
                      "That is a refusal, not a pass.") from exc


def _out(proc: subprocess.CompletedProcess) -> str:
    return proc.stdout.decode("utf-8", errors="replace")


def require_repository(cwd: pathlib.Path = ROOT) -> None:
    """Refuse outside a repository and on a shallow clone. Asks git rather than
    testing for a `.git` directory: in a worktree `.git` is a FILE, and the first
    draft of this check would have refused every tree this ADR was reviewed in."""
    inside = _git("rev-parse", "--git-dir", cwd=cwd)
    if inside.returncode != 0:
        raise Refusal(f"{cwd} is not inside a git repository, so committed history cannot be "
                      "compared against anything. Refused, not passed.")
    shallow = _out(_git("rev-parse", "--is-shallow-repository", cwd=cwd)).strip()
    if shallow == "true":
        raise Refusal("this is a shallow clone, and a check that cannot see the base would pass "
                      "over anything. Run `git fetch --unshallow` (CI: `fetch-depth: 0`).")


def resolve_base(explicit: str | None = None, env: Mapping[str, str] | None = None,
                 cwd: pathlib.Path = ROOT) -> str:
    """The merge-base side of the diff, in a stated order.

    An explicit base (the workflow passes `github.event.pull_request.base.sha`)
    wins. Else `PAVE_BASE` if set -- and if it is set and does not resolve, that
    is a REFUSAL with its name, never a fall-through: a typo'd explicit input
    must not read as "use the default" (`cli.py`'s `_flag_values` lesson). Else
    `origin/$GITHUB_BASE_REF`, `origin/main`, `main`."""
    env = os.environ if env is None else env

    def resolves(ref: str) -> bool:
        return _git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", cwd=cwd).returncode == 0

    if explicit:
        if not resolves(explicit):
            raise Refusal(f"the explicit base {explicit!r} does not resolve to a commit.")
        return explicit
    pave_base = env.get("PAVE_BASE")
    if pave_base:
        if not resolves(pave_base):
            raise Refusal(f"PAVE_BASE={pave_base!r} is set and does not resolve. An explicit base "
                          "that cannot be found is refused, not replaced with a default.")
        return pave_base
    candidates = []
    if env.get("GITHUB_BASE_REF"):
        candidates.append(f"origin/{env['GITHUB_BASE_REF']}")
    candidates += ["origin/main", "main"]
    for ref in candidates:
        if resolves(ref):
            return ref
    raise Refusal(f"no base resolves (tried {', '.join(candidates)}). Fetch the base branch or "
                  "set PAVE_BASE to a commit.")


def append_only_violations(base: str, cwd: pathlib.Path = ROOT) -> list[str]:
    """ADR-042 decision 3. Every committed entry at the merge-base must be
    untouched by the PR -- not modified, deleted, renamed or typechanged.

    `--no-renames` is load-bearing: with detection on, a rename plus a rewrite
    under ~50% reports `R097` and a deletion filter sees nothing, and git's
    heuristic gives up hardest on the largest rewrites -- the bigger the lie,
    the more append-only it looks. `--diff-filter=a` EXCLUDES Added and keeps
    every other verb: enumerating the bad verbs (`MDR`) missed `T`, a committed
    entry replaced by a symlink. Three dots, so the diff is against the
    merge-base and an honest branch behind an advanced `main` is not accused of
    renaming someone else's entry."""
    require_repository(cwd)
    proc = _git("diff", "--name-status", "--no-renames", "--diff-filter=a",
                f"{base}...HEAD", "--", "evals/history/", cwd=cwd)
    if proc.returncode != 0:
        raise Refusal(f"`git diff {base}...HEAD` failed: {proc.stderr.decode(errors='replace').strip()}")
    problems = []
    for line in _out(proc).splitlines():
        if not line.strip():
            continue
        status, _, path = line.partition("\t")
        name = path.rsplit("/", 1)[-1]
        if status.startswith("M") and name in NOT_ENTRIES:
            continue
        verb = {"M": "modified", "D": "deleted", "T": "typechanged"}.get(status[:1], f"changed ({status})")
        problems.append(
            f"{path} existed at the base and this change {verb} it. History is append-only "
            "(CLAUDE.md): a recorded number is what was measured on the day, and a wrong entry "
            "gets a superseding entry (`--supersedes`), never an edit. Entries created in this "
            "change may be fixed freely; entries on the base may not.")
    return problems


# --- the directory ------------------------------------------------------------

def enumerate_entries(history: pathlib.Path = HISTORY) -> tuple[list[pathlib.Path], list[str]]:
    """THE enumerator (ADR-042 decision 2). An entry is a regular file -- not a
    symlink -- named `*.json` directly under the directory, other than the
    schema and the pins; and the directory holds nothing else."""
    problems = []
    entries = []
    if not history.is_dir():
        return [], [f"{history} is not a directory. The whole of history is missing, and a check "
                    "over zero entries reports success identically to one over all of them."]
    for child in sorted(history.iterdir()):
        if child.is_symlink():
            problems.append(f"{child.name} is a symlink; an entry is a regular file, because a link "
                            "is read as its target and pinned as its target.")
            continue
        if child.is_dir():
            problems.append(f"{child.name}/ is a subdirectory of evals/history/; the directory holds "
                            "entries and nothing else, so a reader browsing it sees only rows.")
            continue
        if child.suffix != ".json":
            problems.append(f"{child.name} is not a `.json` file; evals/history/ holds entries and "
                            "nothing else.")
            continue
        if child.name in NOT_ENTRIES:
            continue
        entries.append(child)
    return entries, problems


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pins(history: pathlib.Path = HISTORY) -> dict[str, str]:
    path = history / PINS_NAME
    if not path.is_file():
        return {}
    return _load(path)


def write_pin(entry_path: pathlib.Path, text: str) -> str:
    """Record an entry's digest beside it. Called by both recorders. `pins.json`
    is located from the entry's own directory so `--history-dir` and a
    monkeypatched `HISTORY` carry the pin with them and a test never writes
    into the tracked directory."""
    pins_path = entry_path.parent / PINS_NAME
    pins = _load(pins_path) if pins_path.is_file() else {}
    digest = entry_digest(text)
    pins[entry_path.name] = digest
    with open(pins_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(pins, indent=2, sort_keys=True) + "\n")
    return digest


def check_pins(history: pathlib.Path = HISTORY) -> list[str]:
    """Decision 2: the pinned set equals the set on disk, every pin is 64 hex
    (no empty-string pin -- a seat planted one and rewrote the entry behind it),
    and every digest matches. Two messages, because "unpinned on disk" has a
    remedy and "pinned but missing" is the violation, and one message for both
    is ADR-041's B-0 false accusation."""
    entries, problems = enumerate_entries(history)
    pins = load_pins(history)
    if not isinstance(pins, dict):
        return problems + [f"{PINS_NAME} is not an object of {{entry: sha256}}."]
    on_disk = {p.name: p for p in entries}
    for name, digest in sorted(pins.items()):
        if not isinstance(digest, str) or not HEX64.match(digest):
            problems.append(f"{PINS_NAME}: {name} has pin {digest!r}, which is not a sha256. An "
                            "empty or malformed pin is a pin that matches nothing and guards nothing.")
    for name in sorted(set(on_disk) - set(pins)):
        problems.append(
            f"{name} is on disk and not in {PINS_NAME}. If you just ran `--record`, the recorder "
            f"writes the pin -- so this entry was written some other way. Its normalised digest "
            f"is {entry_digest(on_disk[name].read_text(encoding='utf-8'))}; add that line to "
            f"{PINS_NAME} (three keys) only if the row is a real measurement.")
    for name in sorted(set(pins) - set(on_disk)):
        problems.append(
            f"{name} is pinned in {PINS_NAME} and not on disk. History is append-only: a removed "
            "or renamed entry is a rewrite, not a cleanup, and there is no remedy but restoring it.")
    for name in sorted(set(pins) & set(on_disk)):
        actual = entry_digest(on_disk[name].read_text(encoding="utf-8"))
        if isinstance(pins[name], str) and HEX64.match(pins[name]) and actual != pins[name]:
            problems.append(
                f"{name} has changed: pinned {pins[name][:12]}..., on disk {actual[:12]}.... History "
                "is append-only (CLAUDE.md) -- a wrong entry gets a superseding entry, never an edit.")
    return problems


# --- what a row may claim -------------------------------------------------------

def _entries(history: pathlib.Path) -> dict[str, dict]:
    entries, _ = enumerate_entries(history)
    return {p.name: _load(p) for p in entries}


def derive_scores(entry: dict) -> dict:
    """What `scores` must say, given `cases` (decision 2 item 4), key for key
    what `evals/deterministic.py::tally` and `evals/adversarial.py::tally` write.

    The one key `cases` cannot determine is not derived: `model_declined_unscored`
    comes from `model_complied`, which `cases` does not record. The adversarial
    `pass_rate` is over SCORED probes -- `total` minus `OUT_OF_SCOPE` -- because
    a probe the arm was never asked established nothing; the AI Quality seat
    measured an honest ADR-041 arm (10 of 11 asked) refused by a derivation
    over `total`."""
    cases = entry.get("cases") or []
    results = [c.get("result") for c in cases]
    total = len(cases)
    passed = results.count("PASS")
    out = {
        "total": total,
        "passed": passed,
        "failed": results.count("FAIL"),
        "infra": results.count("INFRA"),
    }
    if entry.get("suite") == "adversarial":
        out_of_scope = results.count("OUT_OF_SCOPE")
        scored = total - out_of_scope
        out["pass_rate"] = round(passed / scored, 4) if scored else 0.0
        out["unearned"] = sum(1 for c in cases if c.get("unearned"))
        out["earned"] = passed - out["unearned"]
        out["unstable"] = sum(1 for c in cases if c.get("unstable"))
        if out_of_scope or "out_of_scope" in (entry.get("scores") or {}):
            out["out_of_scope"] = out_of_scope
            out["scored"] = scored
    else:
        out["pass_rate"] = round(passed / total, 4) if total else 0.0
        sampled = [c for c in cases if c.get("samples")]
        if sampled:
            all_samples = [s for c in sampled for s in c["samples"]]
            out["pooled_pass_rate"] = round(all_samples.count("PASS") / len(all_samples), 4)
    return out


def _majority(samples: list) -> str:
    """`run_evals.summarise`'s rule: a strict majority, else ADVISORY."""
    for verdict in ("PASS", "FAIL"):
        if samples.count(verdict) * 2 > len(samples):
            return verdict
    return "ADVISORY"


def check_derivable(history: pathlib.Path = HISTORY) -> list[str]:
    problems = []
    for name, entry in _entries(history).items():
        scores = entry.get("scores") or {}
        for key, want in derive_scores(entry).items():
            if key in scores and scores[key] != want:
                problems.append(f"{name}: scores.{key} is {scores[key]!r} but its cases derive "
                                f"{want!r}. A row's summary must be what its cases say.")
            elif key not in scores and (name not in LEGACY_ENTRIES or key in ("total", "passed", "failed")):
                # A new row carries every derivable key: the recorders always
                # write them, and a row with only three is a row someone typed.
                problems.append(f"{name}: scores has no {key}.")
        k = entry.get("k")
        for case in entry.get("cases") or []:
            samples = case.get("samples")
            if not samples:
                continue
            if k is not None and len(samples) != k:
                problems.append(f"{name}: case {case.get('id')} records {len(samples)} sample(s) "
                                f"against k={k}.")
            if entry.get("suite") == "adversarial":
                unanimous = "PASS" if all(s == "PASS" for s in samples) else (
                    "INFRA" if any(s == "INFRA" for s in samples) else "FAIL")
                if case.get("result") != unanimous:
                    problems.append(f"{name}: case {case.get('id')} is {case.get('result')} over "
                                    f"samples {samples}; an adversarial result is their unanimity.")
                if bool(case.get("unstable")) != (len(set(samples)) > 1):
                    problems.append(f"{name}: case {case.get('id')} unstable={case.get('unstable')!r} "
                                    f"over samples {samples}.")
            else:
                # A goldens result is the strict majority of its samples (ADR-027,
                # `summarise`). A seat flipped one FAIL to PASS over
                # `['FAIL','FAIL','FAIL']`, recomputed `scores`, and was green.
                if case.get("result") != _majority(samples):
                    problems.append(f"{name}: case {case.get('id')} is {case.get('result')} over "
                                    f"samples {samples}; a goldens result is their strict majority.")
    return problems


def check_case_ids(history: pathlib.Path = HISTORY, cwd: pathlib.Path = ROOT) -> list[str]:
    """A goldens entry scores the golden file AT ITS OWN SHA -- not today's, which
    would turn every committed entry red the day a case is added."""
    import yaml
    require_repository(cwd)
    problems = []
    for name, entry in _entries(history).items():
        if entry.get("suite") != "goldens":
            continue
        proc = _git("show", f"{entry['sha']}:{GOLDEN_CASES}", cwd=cwd)
        if proc.returncode != 0:
            raise Refusal(f"{name}: `git show {entry['sha'][:7]}:{GOLDEN_CASES}` failed; the golden "
                          "file at the entry's commit is unreachable.")
        ids = {c["id"] for c in yaml.safe_load(normalised(_out(proc)))}
        recorded = {c.get("id") for c in entry.get("cases") or []}
        if ids != recorded:
            problems.append(f"{name}: its cases are {sorted(recorded ^ ids)} apart from the golden "
                            f"file at {entry['sha'][:7]}.")
    return problems


def _identity(entry: dict) -> tuple:
    return (entry.get("sha"), entry.get("suite"))


def check_second_rows(history: pathlib.Path = HISTORY) -> list[str]:
    """Decision 7: two rows under one (sha, suite) must differ in `arm`, differ
    in `instrument` (absent versus present counts), or carry `supersedes`; and
    `supersedes` names a file on disk, not itself, same suite, unique across the
    directory, with the same instrument and different numbers. Legibility, not
    truth: an invented `arm` satisfies this, and the ADR says so."""
    entries = _entries(history)
    problems = []
    superseded_by: dict[str, str] = {}
    for name, entry in entries.items():
        target = entry.get("supersedes")
        if target is None:
            continue
        if target == name:
            problems.append(f"{name} supersedes itself.")
            continue
        if target not in entries:
            problems.append(f"{name} supersedes {target!r}, which is not an entry on disk. A "
                            "correction names the filename it corrects (ADR-027 rule 3).")
            continue
        if target in superseded_by:
            problems.append(f"{name} and {superseded_by[target]} both supersede {target}. Corrections "
                            "are a linear chain: correct the correction.")
        superseded_by[target] = name
        old = entries[target]
        if old.get("suite") != entry.get("suite"):
            problems.append(f"{name} supersedes {target}, a different suite.")
        if old.get("arm") != entry.get("arm"):
            problems.append(f"{name} supersedes {target} under a different arm.")
        if old.get("instrument") != entry.get("instrument"):
            problems.append(f"{name} supersedes {target} under a different instrument; a different "
                            "instrument is a second reading, not a correction.")
        if old.get("scores") == entry.get("scores") and old.get("cases") == entry.get("cases"):
            problems.append(f"{name} supersedes {target} with identical scores and cases. A "
                            "correction that corrects nothing is a second row with the same number "
                            "under one sha, which is the ambiguity ADR-027 forbids.")
    groups: dict[tuple, list[str]] = {}
    for name, entry in entries.items():
        groups.setdefault(_identity(entry), []).append(name)
    for key, names in groups.items():
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                ea, eb = entries[a], entries[b]
                differs = (ea.get("arm") != eb.get("arm")
                           or (ea.get("instrument") or {}).get("name") != (eb.get("instrument") or {}).get("name")
                           or ("instrument" in ea) != ("instrument" in eb)
                           or ea.get("supersedes") == b or eb.get("supersedes") == a)
                if not differs:
                    problems.append(f"{a} and {b} share sha {key[0][:7]} and suite {key[1]} and declare "
                                    "no difference -- not arm, not instrument, not supersedes. A reader "
                                    "cannot tell why the second exists.")
    return problems


def _milestone_dir(tag: str | None) -> str | None:
    if not tag:
        return None
    return tag[0].upper() + tag[1:]


def check_evidence(history: pathlib.Path = HISTORY, root: pathlib.Path = ROOT) -> list[str]:
    """Decision 5: a row points at a committed file that has not changed since.
    Required beyond the legacy eight; digest normalised for new rows, normalised
    or its CRLF rendering for legacy rows by name; `EVIDENCE_REVISIONS` for a
    file legitimately revised after it was digested. Plus the cheap narrowings:
    the path sits under the entry's own milestone directory, an adversarial
    row's evidence is the `probes-run.json` the two-key rule names, and no two
    non-correction rows cite the same file."""
    entries = _entries(history)
    problems = []
    cited: dict[str, str] = {}
    for name, entry in sorted(entries.items()):
        sources = entry.get("samples_from")
        if not sources:
            if name in LEGACY_WITHOUT_EVIDENCE:
                continue
            problems.append(f"{name} carries no samples_from. Every row beyond the legacy eight "
                            "names the committed evidence it was summarised from.")
            continue
        mdir = _milestone_dir(entry.get("tag"))
        for i, src in enumerate(sources):
            path = src.get("path", "")
            if mdir and not path.startswith(f"milestones/{mdir}/"):
                problems.append(f"{name}: samples_from[{i}] is {path}, outside milestones/{mdir}/ -- "
                                "an entry cites its own milestone's evidence.")
            if entry.get("suite") == "adversarial" and not re.fullmatch(r"milestones/[^/]+/probes-run\.json", path):
                problems.append(f"{name}: adversarial evidence must be milestones/<M>/probes-run.json "
                                f"(the file the two-key rule names), not {path}.")
            if "supersedes" not in entry:
                if path in cited:
                    problems.append(f"{name} and {cited[path]} both cite {path}. One run is one row.")
                cited[path] = name
            file = root / path
            if not file.is_file():
                problems.append(f"{name}: samples_from[{i}] names {path}, which is not committed.")
                continue
            text = file.read_text(encoding="utf-8")
            recorded = src.get("sha256")
            accepted = {entry_digest(text)}
            if name in LEGACY_ENTRIES:
                accepted.add(crlf_digest(text))
            chain = EVIDENCE_REVISIONS.get(name, [])
            if chain:
                # A chain: the entry recorded the first digest, the committed file
                # is the last, and every link hands over to the next.
                linked = all(chain[i][1] == chain[i + 1][0] for i in range(len(chain) - 1))
                if linked and recorded == chain[0][0] and entry_digest(text) == chain[-1][1]:
                    accepted.add(recorded)
            if recorded not in accepted:
                problems.append(
                    f"{name}: samples_from[{i}] recorded {str(recorded)[:12]}... for {path}, which now "
                    f"digests to {entry_digest(text)[:12]}.... The evidence moved under a recorded "
                    "number. If that was a legitimate revision, record it in EVIDENCE_REVISIONS "
                    "with its PR and reason (three keys).")
    return problems


def check_registry(history: pathlib.Path = HISTORY, cwd: pathlib.Path = ROOT) -> list[str]:
    """Decision 6: every registered `probes_sha256` is the digest of a committed
    revision of the corpus, and `corpus_size` is that revision's probe count; an
    entry's instrument digests equal the registry row it names; and the corpus
    at the entry's own sha digests to that row's `probes_sha256`. "Registered
    under Security's key" bounds nothing on a one-operator repo -- a mid-registry
    row with a fabricated digest and `corpus_size: 3` recorded a 3/3 arm green.
    The blob at a digest has the probes it has."""
    import yaml
    require_repository(cwd)
    registry = _load(INSTRUMENTS)["instruments"]
    listing = _git("rev-list", "--all", "--objects", "--", PROBES, cwd=cwd)
    if listing.returncode != 0:
        raise Refusal("`git rev-list --all --objects` failed; the corpus's committed revisions "
                      "are unreachable.")
    sizes: dict[str, int] = {}
    for line in _out(listing).splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[1] == PROBES:
            blob = _git("cat-file", "-p", parts[0], cwd=cwd)
            text = _out(blob)
            sizes[corpus_digest(text)] = len(yaml.safe_load(normalised(text)) or [])
    problems = []
    for name, row in registry.items():
        digest = (row.get("digests") or {}).get("probes_sha256")
        size = row.get("corpus_size")
        if digest not in sizes:
            problems.append(f"instrument {name}: probes_sha256 {str(digest)[:12]}... is the digest of "
                            "no committed revision of the corpus. An instrument that read a corpus "
                            "nobody committed read nothing.")
            continue
        if size != sizes[digest]:
            problems.append(f"instrument {name}: corpus_size is {size!r}; the corpus at its digest has "
                            f"{sizes[digest]} probes.")
    for name, entry in _entries(history).items():
        inst = entry.get("instrument")
        if not inst or entry.get("suite") != "adversarial":
            continue
        row = registry.get(inst.get("name"))
        if row is None:
            problems.append(f"{name} names instrument {inst.get('name')!r}, which is not registered.")
            continue
        for key, value in (row.get("digests") or {}).items():
            if inst.get(key) != value:
                problems.append(f"{name}: instrument.{key} differs from the registry row for "
                                f"{inst['name']}; a name identifies the code that read the run, "
                                "and this row's digests say different code did.")
        if entry.get("supersedes"):
            continue   # a correction copies its sha; the tie was checked on the original
        at_sha = _git("show", f"{entry['sha']}:{PROBES}", cwd=cwd)
        if at_sha.returncode != 0:
            raise Refusal(f"{name}: the corpus at {entry['sha'][:7]} is unreachable.")
        if corpus_digest(_out(at_sha)) != row["digests"]["probes_sha256"]:
            problems.append(f"{name}: the corpus at its sha {entry['sha'][:7]} is not the corpus its "
                            f"instrument {inst['name']} registers. The name an entry declares is "
                            "the corpus snapshot it ran under, or it is not that instrument.")
        total = (entry.get("scores") or {}).get("total")
        if total != row.get("corpus_size"):
            problems.append(f"{name}: scores.total is {total!r}; instrument {inst['name']} registers "
                            f"a corpus of {row.get('corpus_size')!r}. An arm asks the whole corpus.")
    return problems


def check_schema(history: pathlib.Path = HISTORY) -> list[str]:
    """Decision 7's ratchet: top-level `required` is exactly the five, and every
    entry on disk validates against the schema as it stands."""
    import jsonschema
    schema = _load(history / SCHEMA_NAME)
    problems = []
    if tuple(schema.get("required", [])) != SCHEMA_REQUIRED:
        problems.append(f"schema.json top-level required is {schema.get('required')}; it is pinned to "
                        f"{list(SCHEMA_REQUIRED)}. A new requirement lives under an if/then that no "
                        "committed entry fails.")
    for name, entry in _entries(history).items():
        try:
            jsonschema.validate(entry, schema)
        except jsonschema.ValidationError as exc:
            problems.append(f"{name} no longer validates: {exc.message}. The schema may not gain a "
                            "requirement a committed entry does not meet.")
    return problems


def check_readme(history: pathlib.Path = HISTORY, readme: pathlib.Path | None = None) -> list[str]:
    """Decision 2: the README's bold goldens rows match the entry pinned per tag,
    and a row with a tag and no number has no goldens entry carrying that tag."""
    text = (readme or ROOT / "README.md").read_text(encoding="utf-8")
    entries = _entries(history)
    problems = []
    rows = {}
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        m = re.search(r"`(m\d\d[a-z]?)`", line)
        if m:
            rows[m.group(1)] = line
    def goldens_cell(row: str) -> str:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        return cells[4] if len(cells) >= 5 else ""

    # Exact-set, both directions: every row publishing a bold n/m is pinned to
    # an entry, and every pinned tag publishes one. A row filled in with a
    # number and no entry behind it was green under a one-directional check.
    published = {tag for tag, row in rows.items() if re.search(r"\*\*\d+/\d+\*\*", goldens_cell(row))}
    for tag in sorted(published - set(README_GOLDENS)):
        problems.append(f"README's {tag} row publishes a goldens number and README_GOLDENS pins it to "
                        "no entry. A published number is a claim; name the entry that backs it.")
    for tag in sorted(set(README_GOLDENS) - published):
        problems.append(f"README_GOLDENS pins {tag} and its row publishes no bold goldens number.")
    for tag, name in README_GOLDENS.items():
        entry = entries.get(name)
        row = rows.get(tag)
        if entry is None or row is None:
            problems.append(f"README tie for {tag}: entry {name} or its row is missing.")
            continue
        claim = f"**{entry['scores']['passed']}/{entry['scores']['total']}**"
        if claim not in goldens_cell(row):
            problems.append(f"README's {tag} row does not carry {claim}, which {name} records.")
    tagged = {e.get("tag") for e in entries.values() if e.get("suite") == "goldens"}
    for tag in sorted((tagged & set(rows)) - set(README_GOLDENS)):
        problems.append(f"{tag} has a goldens entry on disk and README's {tag} row is pinned to none. "
                        "Either pin the row to it or the entry contradicts the published claim.")
    return problems


# --- everything, for the gate -------------------------------------------------

def run_all(base: str | None, history: pathlib.Path = HISTORY,
            cwd: pathlib.Path = ROOT) -> tuple[list[str], list[str]]:
    """Returns (problems, refusals). Either non-empty is a FAIL; a refusal is
    reported under its own heading so the remedy is the named one."""
    problems: list[str] = []
    refusals: list[str] = []
    _, dir_problems = enumerate_entries(history)
    problems += dir_problems
    problems += check_pins(history)
    problems += check_derivable(history)
    problems += check_second_rows(history)
    problems += check_evidence(history, cwd)
    problems += check_schema(history)
    problems += check_readme(history)
    for check in (lambda: check_case_ids(history, cwd), lambda: check_registry(history, cwd),
                  lambda: append_only_violations(resolve_base(base, cwd=cwd), cwd)):
        try:
            problems += check()
        except Refusal as exc:
            refusals.append(str(exc))
    return problems, refusals


def render(problems: Sequence[str], refusals: Sequence[str]) -> str:
    lines = []
    if refusals:
        lines.append("[pave history] REFUSED -- a check could not run, and that is not a pass:")
        lines += [f"  ! {r}" for r in refusals]
    if problems:
        lines.append(f"[pave history] FAIL -- {len(problems)} problem(s):")
        lines += [f"  x {p}" for p in problems]
    if not problems and not refusals:
        lines.append("[pave history] PASS -- every entry pinned, derivable, anchored; nothing on the "
                     "base touched.")
    return "\n".join(lines)
