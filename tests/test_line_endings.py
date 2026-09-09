r"""The index is uniform, and every digest is a digest of what the index holds.

**Why this is a test and not a comment in `.gitattributes`.** That file's own
header records what a mixed tree cost once: ADR-041 pinned the SHA-256 digests of
three committed history entries -- the anchor every arm-scoping check rests on --
and took them from a tree where one entry was LF and two were CRLF, against three
pure-LF blobs. No uniform checkout could satisfy all three, so CI failed an honest
tree and accused the PR of rewriting append-only history. The header then says the
line that matters here: *"This exists so the NEXT byte-level check does not have
to rediscover it."* A sentence cannot do that. These three checks can.

`.gitattributes` is upstream of every SHA-256 pin in this repository -- the
entry digests in `evals/history/`, the seven instrument digests in
`quality/adversarial/instruments.json`, the five in `quality/judge/frozen.json`
and the `inputs_sha256` maps of the five milestone records -- because it decides
what bytes the index holds, and every one of those pins is a digest OF those
bytes. Deleting four characters (`eol=lf`) is a one-line diff whose damage lands
in somebody else's PR: 191 CRLF blobs in the index and every digest recorded
before that day naming a file it no longer matches. The file is on a two-key rule
since M08b PR 4 (`platform-eng` + `ai-quality`) and this file is on the same rule,
because a check that is deletable in the diff that weakens what it checks is the
inversion `tests/test_g4_capture_boundary.py` sits on `core/audit.py`'s rule to
avoid.

**Three checks, and each fails differently.**

1. **The attribute** -- every tracked path resolves to `text=auto eol=lf`. This is
   the one that catches the four-character deletion and any per-path override
   added beneath it.
2. **The index** -- no tracked blob carries `\r\n` unless it is genuinely binary,
   which is decided by the blob containing a NUL byte and never by a name list.
   An earlier draft pinned the three committed `.mp4` recordings by name; that is
   the guard-coupled-to-its-own-data shape this repository has already paid for,
   red the day a fourth recording lands and silent about the thing it watches for.
3. **The readers** -- a planted CRLF copy of a committed evidence file digests to
   the committed pin, through every reader that digests one. Checks 1 and 2 say
   the index is clean today; check 3 says a Windows working tree cannot produce a
   different number tomorrow, which is the half `pave/history.py::normalised`
   exists for and the half the `milestones/M08*` readers re-implement over bytes.

**What check 3 does not claim.** It does not claim a digest is stable under any
other edit -- that is what the pins themselves are for. It claims one property:
line endings are not content, and no reader here treats them as content.

Hermetic (G8): `git` against the local object database, committed files, no
network and no model.
Owning seats: Platform Engineering (the attribute and the checkout) - AI Quality
(`evals/history/` semantics, the digests ADR-041 broke on).
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The attribute set every tracked path must resolve to, as `git ls-files --eol`
#: renders it. `text=auto` normalises on the way in; `eol=lf` decides the way out.
#: Both halves, because `text=auto` alone leaves the checkout to `core.autocrlf`,
#: which is `true` in the system gitconfig on the machine this is developed on and
#: `false` in this repository -- the mixed state the header describes.
REQUIRED_ATTR = "text=auto eol=lf"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def _tracked_eol() -> list[tuple[str, str, str]]:
    """`(index eol, attribute, path)` for every tracked file.

    `git ls-files --eol` is the only reading that answers this question about the
    INDEX rather than about the working tree. The working tree is a checkout
    artifact -- 191 files are CRLF locally today and no committed digest depends
    on any of them -- so a check that read the tree would be measuring the
    operator's `git config` and calling it a property of the repository.
    """
    out = _git("ls-files", "--eol").stdout.decode("utf-8", "replace")
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        fields, path = line.split("\t", 1)
        parts = fields.split()
        index = parts[0].removeprefix("i/")
        attr = " ".join(p.removeprefix("attr/") for p in parts[2:])
        rows.append((index, attr, path))
    return rows


TRACKED = _tracked_eol()


def test_the_reading_found_the_tree():
    """The vacuity guard for both checks below.

    `git ls-files --eol` returning nothing -- no `git` on PATH, a bare directory,
    a parse that silently matched no line -- makes every assertion here green over
    an empty set, which is the shape `tests/test_g4_capture_boundary.py`'s own
    guard was written for and the shape ADR-043 recorded four of ten planted
    weakenings surviving under."""
    assert len(TRACKED) >= 400, (
        f"`git ls-files --eol` produced {len(TRACKED)} rows; this repository tracks "
        "hundreds of files, so the reading, not the tree, is what is wrong.")


def test_every_tracked_path_resolves_to_the_committed_attribute():
    """**Check 1: the four-character deletion.**

    `* text=auto eol=lf` is one line and it is the whole of the control. Dropping
    `eol=lf`, or adding any per-path override beneath the `*`, changes what a
    checkout materialises for the paths it reaches -- and the next commit from a
    Windows tree carries those bytes into the index, past every digest already
    recorded. Asserted per path rather than by reading `.gitattributes` as text,
    because what matters is what git RESOLVES, and an override three lines further
    down is invisible to a substring check on the first line."""
    wrong = [(path, attr) for _index, attr, path in TRACKED if attr != REQUIRED_ATTR]
    assert not wrong, (
        f"{len(wrong)} tracked path(s) do not resolve to `{REQUIRED_ATTR}`, so the bytes "
        f"in the index are decided per path rather than uniformly: {wrong[:10]}. Every "
        "SHA-256 pin in this repository is a digest of what this attribute produced.")


@pytest.mark.parametrize("path", [p for _i, _a, p in TRACKED], ids=lambda p: p)
def test_no_tracked_blob_carries_crlf_unless_it_is_binary(path: str):
    r"""**Check 2: what is actually in the index.**

    Check 1 asks git what it would do; this asks what it did. They come apart
    exactly once -- a blob written into the index by something other than a normal
    `git add` under the current attribute (a merge from a tree without this file,
    `update-index --cacheinfo`, a commit made before the attribute existed) keeps
    its bytes and no attribute reading reports it.

    **Binary is decided by content, never by a name.** A NUL byte is git's own
    heuristic and it is the honest one here: the three committed `.mp4` recordings
    carry `\r\n` runs because a video container carries every byte pattern, and a
    list of their names would go red the day a fourth act is recorded while saying
    nothing about a CRLF text file smuggled in under a `-text` override."""
    blob = _git("cat-file", "blob", f":{path}").stdout
    if b"\x00" in blob:
        return
    assert b"\r\n" not in blob, (
        f"the index blob for `{path}` carries CRLF while resolving to `{REQUIRED_ATTR}` "
        "and holding no NUL byte, so it is text that was committed unnormalised. Every "
        "digest taken over it before today names bytes it no longer holds.")


# --- check 3: the readers ------------------------------------------------------

def _load(name: str, rel: str):
    """Import a `milestones/` reader by path, leaving `sys.path` as it was found.

    **The restore is load-bearing, and it was found by breaking three tests in
    another file.** These readers are scripts rather than a package, and they put
    what they need on the path themselves at import time --
    `milestones/M08/context_census.py` inserts `tools/catalog-search` and then
    `tools/entitlement-check`, so the SECOND one lands at `sys.path[0]` and the
    bare name `server` stops meaning what `tests/conftest.py` arranged for it to
    mean. `tests/test_mcp_server.py` does a top-level `import server` and three of
    its cases then read the entitlement tool's contract while asserting against
    the catalog tool's.

    Today nothing collides with that, by accident rather than by design:
    `tests/test_m08_census.py` imports the same module inside a module-scoped
    fixture, so it executes after every test module has been imported and
    `server` is already bound. This file's table is built at import time, which
    is collection time, and collection reaches `test_line_endings` before
    `test_mcp_server`. Restoring the path is this file's business either way -- a
    helper that imports a script must not leak the script's idea of where things
    are into the rest of the session.

    Recorded rather than fixed at the source: `milestones/M08/` is on the census
    rule and nothing under it moves in this milestone. The hazard is that the
    ordering accident is the only thing holding, and a second lazy importer would
    find it again.
    """
    saved = list(sys.path)
    try:
        spec = importlib.util.spec_from_file_location(name, ROOT / rel)
        module = importlib.util.module_from_spec(spec)
        sys.modules.setdefault(name, module)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved


def _json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _crlf_copy(source: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    """`source`'s bytes with every line ending made CRLF, written verbatim.

    Normalise first and then expand, so a file that is already mixed -- which is
    the state ADR-041's three entries were in -- becomes uniformly CRLF rather
    than acquiring `\\r\\r\\n`."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    body = source.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    destination.write_bytes(body)
    return destination


#: `(name, kind, evidence file, committed pin, digest)` for every reader that
#: takes a SHA-256 of a committed evidence file.
#:
#: **`kind` is the boundary the reader is exercised at, and getting it wrong makes
#: the test prove the opposite of what it says.** A `path` reader is handed the
#: planted file and opens it itself -- the five `milestones/` readers do
#: `read_bytes().replace(b"\r\n", b"\n")`, and handing them a decoded string would
#: skip the line under test. A `text` reader is handed the planted file's bytes
#: DECODED WITHOUT newline translation, because that is what its own callers
#: produce: `pave/history.py` digests `git show` output as well as `read_text`,
#: and `normalised()` is what makes those two agree. Feeding a `text` reader
#: `read_text` output would hand it a string Python had already normalised, and
#: the assertion would pass with the reader's own normalisation deleted.
def _readers():
    import evals.judge as judge
    from pave import history

    census = _load("m08_context_census", "milestones/M08/context_census.py")
    rescore = _load("m08_rescore_join", "milestones/M08/rescore_join.py")
    fresh = _load("m08b_fresh_join", "milestones/M08b/fresh_join.py")
    residual = _load("m08b_residual_attribution", "milestones/M08b/residual_attribution.py")
    answer = _load("m08b_answer_channel", "milestones/M08b/answer_channel.py")

    instruments = _json("quality/adversarial/instruments.json")["instruments"]["m04-I"]["digests"]
    return [
        ("milestones/M08/context_census.py::_sha256", "path", "data/catalog.json",
         _json("milestones/M08/context-census.json")["inputs_sha256"]["data/catalog.json"],
         census._sha256),
        ("milestones/M08/rescore_join.py::_sha256", "path", "evals/history/m07-tools-goldens.json",
         _json("milestones/M08/rescore-join.json")
         ["inputs_sha256"]["evals/history/m07-tools-goldens.json"],
         rescore._sha256),
        ("milestones/M08b/fresh_join.py::_sha256", "path", "data/catalog.json",
         _json("milestones/M08b/fresh-join.json")["inputs_sha256"]["data/catalog.json"],
         fresh._sha256),
        ("milestones/M08b/residual_attribution.py::_sha256", "path",
         "milestones/M08/context-census.json",
         _json("milestones/M08b/residual-attribution.json")
         ["inputs_sha256"]["milestones/M08/context-census.json"],
         residual._sha256),
        ("milestones/M08b/answer_channel.py::_sha256", "path",
         "milestones/M08b/goldens-run-1.json",
         _json("milestones/M08b/answer-channel.json")
         ["inputs_sha256"]["milestones/M08b/goldens-run-1.json"],
         answer._sha256),
        # The entry digest ADR-041 took from a mixed tree, at the reader that
        # took it. The pin is the one `pave gate history` compares against.
        ("pave/history.py::entry_digest", "text", "milestones/M08b/goldens-run-1.json",
         _json("evals/history/m08b-tools-goldens.json")["samples_from"][0]["sha256"],
         history.entry_digest),
        ("pave/history.py::corpus_digest", "text", "quality/adversarial/probes.yaml",
         instruments["probes_sha256"], history.corpus_digest),
        # `judge.digest` does NOT normalise and is not asked to: its callers read
        # through `Path.read_text`, whose universal-newline translation is the
        # normalisation. The composition is what runs, so the composition is what
        # is checked -- and it is red if a caller ever moves to `read_bytes`.
        ("evals/judge.py::digest via read_text", "path", "quality/judge/prompt.md",
         _json("quality/judge/frozen.json")["prompt_sha256"],
         lambda p: judge.digest(p.read_text(encoding="utf-8"))),
    ]


READERS = _readers()


@pytest.mark.parametrize("name,kind,rel,pin,digest", READERS, ids=[r[0] for r in READERS])
def test_a_planted_crlf_copy_digests_to_the_committed_pin(name, kind, rel, pin, digest, tmp_path):
    """**Check 3, per reader.** A line ending is not content.

    The plant is the state ADR-041's tree was in and the state 191 files in this
    working tree are in today: the same file, CRLF. If the digest moves, then the
    number recorded in `evals/history/`, `instruments.json`, `frozen.json` or a
    census record is a property of who checked the repository out, and a Windows
    author's honest commit is indistinguishable from a rewritten one."""
    planted = _crlf_copy(ROOT / rel, tmp_path / pathlib.Path(rel).name)
    assert b"\r\n" in planted.read_bytes(), (
        f"the plant did not take: {rel} has no line endings to expand, so this case "
        "checked nothing. Name a different evidence file.")
    got = digest(planted) if kind == "path" else digest(planted.read_bytes().decode("utf-8"))
    assert got == pin, (
        f"{name} digests a CRLF copy of `{rel}` to {got[:12]}..., but the committed pin "
        f"is {pin[:12]}.... A line ending is not content: this reader now reports a "
        "different number for the same file depending on how it was checked out.")


#: What `instrument_digests` reads out of the tree it is given. Read from the
#: function's own `root` parameter, which exists so a scratch tree can be
#: digested -- the docstring records that it used to ignore that argument for
#: `POLICY_MECHANISMS`, so a planted tree watched a digest not move.
INSTRUMENT_INPUTS = (
    "evals/adversarial.py",
    "quality/adversarial/probes.yaml",
    "quality/adversarial/g4-semantics.yaml",
    "platform/gateway/core/classify.py",
    "platform/gateway/core/guardrail.py",
    "platform/gateway/core/toolloop.py",
    "platform/gateway/core/audit.py",
    "services/highlights-agent/run_probes_via_gateway.py",
)


def test_the_instrument_digests_survive_a_crlf_tree(tmp_path):
    """The seven digests that decide which instrument an adversarial entry was
    recorded under, taken over a whole tree that is uniformly CRLF.

    Whole-tree rather than per-file because `instrument_digests` composes several
    files into one digest (`guardrail_sha256` is `guardrail.py` and `toolloop.py`;
    `capture_sha256` is `audit.py` and the probe harness) and because
    `semantics_sha256` re-parses `audit.py` out of `root` for `POLICY_MECHANISMS`.
    A per-file check would leave the composition untested, and the composition is
    what a run records."""
    import evals.adversarial as adversarial

    for rel in INSTRUMENT_INPUTS:
        _crlf_copy(ROOT / rel, tmp_path / rel)
    got = adversarial.instrument_digests(tmp_path)
    pins = _json("quality/adversarial/instruments.json")["instruments"]["m04-I"]["digests"]
    moved = {k: (got.get(k), v) for k, v in pins.items() if got.get(k) != v}
    assert not moved, (
        f"{len(moved)} instrument digest(s) moved over a CRLF tree: {sorted(moved)}. An "
        "entry recorded under `m04-I` would no longer match the instrument it names, "
        "which is ADR-018's hazard arriving through the checkout rather than through "
        "an edit.")


# --- the vacuity guard for check 3 ---------------------------------------------

#: Every module that digests something, and every `sha256` function in it. A new
#: reader added to one of these modules is red here until it is either covered by
#: `READERS` above or named below with a reason -- which is the deletability
#: property this file's own audit turns on: `READERS = []` parametrises to nothing
#: and reports green, exactly as `ADR043_SEATS = {}` left 1814 passed.
DIGESTING_MODULES = (
    "pave/history.py", "evals/judge.py", "evals/adversarial.py",
    "milestones/M08/context_census.py", "milestones/M08/rescore_join.py",
    "milestones/M08b/fresh_join.py", "milestones/M08b/residual_attribution.py",
    "milestones/M08b/answer_channel.py",
)

#: Digest functions in those modules that do NOT take a committed file's text, by
#: name and with the reason. Each is a digest of something composed in memory or
#: fetched from the cloud, where a line ending never enters.
NOT_A_FILE_DIGEST = {
    # A CRLF rendering, kept for `LEGACY_ENTRIES` by name -- the one function here
    # whose whole purpose is to NOT normalise, and covering it would assert the
    # opposite of what it does.
    "pave/history.py::crlf_digest",
    # The instrument block, exercised whole by the test above rather than per part.
    "evals/adversarial.py::_digest",
    "evals/adversarial.py::instrument_digests",
    # Composed in memory from parsed JSON, never from a file's bytes. Both
    # `tool_surface` and `check_tool_surface` digest a `json.dumps` of tool input
    # schemas parsed out of a blob, so the bytes they hash are Python's rendering
    # and not the file's; `judge.instrument` composes the five judge digests from
    # readers already covered above.
    "pave/history.py::tool_surface",
    "pave/history.py::check_tool_surface",
    "evals/judge.py::instrument",
}


def _sha256_functions(rel: str) -> set[str]:
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"), filename=rel)
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(isinstance(n, ast.Attribute) and n.attr == "sha256" for n in ast.walk(node)):
            found.add(f"{rel}::{node.name}")
    return found


def test_every_digesting_function_is_covered_or_named():
    """**The guard that makes check 3 non-deletable one row at a time.**

    A reader added to any module above, or a covered one quietly renamed, drops
    out of `READERS` with no failure -- the check would still pass, over fewer
    things. This finds the functions by parsing for `sha256` rather than by
    trusting the table, so the table has to keep up with the code."""
    live = set()
    for rel in DIGESTING_MODULES:
        live |= _sha256_functions(rel)
    assert len(live) >= 8, (
        f"the scan found {len(live)} digest function(s) across {len(DIGESTING_MODULES)} "
        "modules; the parse, not the tree, is what is wrong.")

    covered = {name.split(" via ")[0] for name, *_rest in READERS}
    covered |= {"evals/adversarial.py::_digest", "evals/adversarial.py::instrument_digests"}
    uncovered = sorted(live - covered - NOT_A_FILE_DIGEST)
    assert not uncovered, (
        f"{uncovered} digest something and are checked by nothing here. Either add the "
        "reader to `READERS` with the evidence file and pin it produces, or name it in "
        "`NOT_A_FILE_DIGEST` with the reason a line ending cannot reach it.")


def test_loading_a_reader_leaves_sys_path_as_it_found_it():
    """**The regression the reader table introduced, as a test rather than a
    story.**

    Building `READERS` imports five `milestones/` scripts, and those scripts put
    what they need on `sys.path` themselves. Measured before the restore in
    `_load`: importing `milestones/M08/context_census.py` leaves
    `tools/entitlement-check` at `sys.path[0]`, ahead of the
    `tools/catalog-search` that `tests/conftest.py` put there, and three cases in
    `tests/test_mcp_server.py` then compare the entitlement tool's contract
    against the catalog tool's and fail. The whole suite went from green to three
    red for a reason with nothing to do with line endings.

    Asserted on the real helper against a real reader, not on a copy of the
    restore logic."""
    before = list(sys.path)
    _load("m08_context_census_path_probe", "milestones/M08/context_census.py")
    assert sys.path == before, (
        "`_load` leaked a reader's `sys.path` entries into the session: "
        f"{[p for p in sys.path if p not in before]}. A bare `import server` after this "
        "resolves to whichever tool directory landed first, and the tests that do one "
        "fail while naming something else entirely.")


def test_the_reader_table_cannot_be_emptied():
    """`READERS = []` parametrises to zero cases and reports green. A count is the
    cheapest thing that makes deleting a row two edits instead of one, and this
    repository has recorded that bypass twice (`ADR043_SEATS`, `M06B_SEATS`)."""
    assert len(READERS) == 8, (
        f"READERS holds {len(READERS)} rows, expected 8. If a reader legitimately went "
        "away, change the number here and say which one in the same diff.")
    assert hashlib.sha256(b"").hexdigest().startswith("e3b0c442"), "sha256 is not sha256"
