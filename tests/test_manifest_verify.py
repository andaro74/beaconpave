"""The manifest verifier: every row of its refusal table, and the glob that finds
the services it runs on.

**The premise this file closes.** Nothing in this repository enumerated
`services/*` — both CI evaluation steps name `highlights-agent` literally, and
`tests/test_contracts.py` reads one hard-coded `MANIFEST` path. A second service
could be added with a manifest declaring a tool it is not granted, a brand nothing
can judge and `eval_min_cases: 0`, and no check would look at it. So
`test_the_service_glob_finds_something` is not a smoke test: a glob that matches
nothing verifies nothing, silently and forever, and it is the exact shape of the
`recap-agent` control ADR-048 found passing over zero constructible pairs.

**The producers are the commitment.** `PRODUCERS` holds one violating input per row
of `manifest.ROWS`, and `test_the_table_and_the_producers_agree` requires the two
sets to be equal in both directions — so a row added to the table with no producer
is red, and a producer for a row nobody wrote down is red. A refusal table
maintained as prose beside the code is how ADR-037's summary drifted twice.

**Every "row N fires" test is guarded by a vacuity test.** The good fixture must
produce zero findings; without that, a verifier that returned every row on every
input would pass all fourteen.

Hermetic (G8): builds its inputs in `tmp_path`, reads the committed tree, calls no
model, opens no socket.
Owning seats: Platform Engineering (the mechanism) · AI Quality (the criteria) ·
Security / Red Team (the grant bijection).
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from pave import floors
from pave import gate as gate_mod
from pave import manifest as manifest_mod
from pave import verify as verify_mod

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: **In-module, not a committed fixture.** ADR-048's lesson one component over: a
#: negative control resting on a committed registry line is a control that dies
#: quietly the day someone tidies the line away, and it took a real registry entry
#: with no service behind it to notice. Nothing outside this file can move these.
SYNTHETIC_REGISTRY = [
    {"id": "tool-a", "owner": "seat:tool-owner", "semver": "0.1.0",
     "consequence": "read", "callers": ["svc-one"]},
    {"id": "tool-b", "owner": "seat:tool-owner", "semver": "0.1.0",
     "consequence": "read", "callers": ["svc-two"]},
]


def good_manifest() -> dict:
    """A manifest that earns no refusal. Every producer below mutates one thing."""
    return {
        "apiVersion": manifest_mod.API_VERSION,
        "service": "svc-one",
        "template": "agent-tools@0.1.0",
        "brand": floors.SUPPORTED_BRANDS[0],
        "classification": floors.DECLARABLE_LEVELS[0],
        "owners": {"team": "beacon-example", "oncall": "webhook:example"},
        "runtime": manifest_mod.RUNTIMES[0],
        "tools": [{"id": "tool-a@^0"}],
        "gates": {
            "eval_min_cases": floors.PLATFORM_EVAL_MIN_CASES,
            "budgets": dict.fromkeys(floors.REQUIRED_BUDGET_KEYS, 1000),
        },
        "attestations": {"gate_verdict": "required", "manifest_signature": "required"},
    }


def good_cases() -> list[dict]:
    """A pack at the floor with headroom inside the band: 20 disposed, 2 near."""
    pack = [{"id": f"case-{n:02d}", "input": "q", "asserts": [],
             "provenance": {"author": "human"}}
            for n in range(floors.PLATFORM_EVAL_MIN_CASES)]
    for case in pack[:2]:
        case["expect_near_threshold"] = True
    return pack


def make_service(tmp_path: pathlib.Path, name: str = "svc-one",
                 manifest: dict | str | None = None,
                 cases: list | None = None) -> pathlib.Path:
    """Materialise a service tree. `manifest` as a `str` is written verbatim, which
    is the only way to express a duplicate key (row 1) — `yaml.safe_dump` of a
    Python dict cannot produce one."""
    directory = tmp_path / "services" / name
    # `exist_ok=True`: the forty-fifth sentinel this repository found was a bare
    # `.mkdir()` on a path a second call reaches.
    (directory / "evals" / "golden").mkdir(parents=True, exist_ok=True)
    body = manifest if isinstance(manifest, str) else yaml.safe_dump(
        good_manifest() if manifest is None else manifest, sort_keys=False)
    (directory / manifest_mod.MANIFEST_NAME).write_text(body, encoding="utf-8")
    (directory / "evals" / "golden" / "cases.yaml").write_text(
        yaml.safe_dump(good_cases() if cases is None else cases, sort_keys=False),
        encoding="utf-8")
    return directory


def _rows(directory: pathlib.Path, registry: list[dict] | None = None) -> list[int]:
    registry = SYNTHETIC_REGISTRY if registry is None else registry
    return [f.row for f in manifest_mod.verify(directory, registry=registry)]


# --- the fixture must be clean, or every test below passes for the wrong reason --

def test_the_good_fixture_earns_no_refusal(tmp_path):
    """**The vacuity guard for the whole file.** A `verify()` that returned every
    row on every input would satisfy all fourteen row tests. This is the only test
    here that would notice."""
    findings = manifest_mod.verify(make_service(tmp_path), registry=SYNTHETIC_REGISTRY)
    assert findings == [], (
        "the reference fixture earns refusals:\n"
        + "\n".join(f.render() for f in findings))


# --- the glob, which is the premise M05 removes ---------------------------------

def test_the_service_glob_finds_something():
    """**Not a smoke test.** Before ADR-046 nothing enumerated `services/*` at all;
    both CI evaluation steps name `highlights-agent` literally and
    `tests/test_contracts.py` reads one hard-coded path. If `services()` ever
    returns `[]`, `pave verify --all` verifies nothing and every test in this file
    that iterates it passes over an empty set — the shape ADR-048 found in the
    cross-tool control, which was green with zero pairs constructible."""
    found = manifest_mod.services()
    assert found, (
        f"`{manifest_mod.SERVICES}` holds no directory with a "
        f"`{manifest_mod.MANIFEST_NAME}`. Either the tree moved or the glob is "
        "stale — and a stale glob reports PASS over nothing.")
    assert all((d / manifest_mod.MANIFEST_NAME).is_file() for d in found)


def test_every_committed_service_verifies_clean():
    """The verifier must be green against the tree it ships with. It was not when
    it was written: `highlights-agent` was **granted** `publish-highlight` in the
    registry and declared two tools, so the reverse direction of the grant check
    fired on the only committed manifest. The manifest now declares it — measured,
    because the alternative is not a legal registry state: `callers: []` on
    `publish-highlight` is **4 failed**, one of them
    `test_every_registered_tool_declares_an_owner_and_consequence_class` saying in
    so many words that a tool with no callers is unreachable under G3."""
    registry = manifest_mod.load(manifest_mod.REGISTRY)
    for directory in manifest_mod.services():
        findings = manifest_mod.verify(directory, registry=registry)
        assert findings == [], (
            f"{directory.name} earns refusals:\n"
            + "\n".join(f.render() for f in findings))


# --- one producer per row of the table -----------------------------------------

def _row1(tmp_path):
    """A duplicate key. Written as text: `yaml.safe_dump` cannot emit one, which is
    the same reason `yaml.safe_load` cannot report one."""
    body = yaml.safe_dump(good_manifest(), sort_keys=False) + "\nruntime: ecs\n"
    return make_service(tmp_path, manifest=body), SYNTHETIC_REGISTRY


def _row2(tmp_path):
    m = good_manifest()
    m["tools"] = [{"id": "tool-zzz@^0"}]
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


def _row3(tmp_path):
    m = good_manifest()
    m["tools"] = [{"id": "tool-a@^0"}, {"id": "tool-b@^0"}]
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


def _row4(tmp_path):
    """The direction nothing in the repository had. The registry grants it; the
    manifest is silent; every check that existed looked only at what the manifest
    named."""
    registry = [dict(SYNTHETIC_REGISTRY[0]),
                {**SYNTHETIC_REGISTRY[1], "callers": ["svc-one"]}]
    return make_service(tmp_path), registry


def _row5(tmp_path):
    m = good_manifest()
    del m["template"]
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


def _row6(tmp_path):
    m = good_manifest()
    m["classification"] = "public"
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


def _row7(tmp_path):
    m = good_manifest()
    m["service"] = "svc-elsewhere"
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


def _row8(tmp_path):
    return make_service(tmp_path, cases=good_cases()[:5]), SYNTHETIC_REGISTRY


def _row9(tmp_path):
    flat = [{k: v for k, v in c.items() if k != "expect_near_threshold"}
            for c in good_cases()]
    return make_service(tmp_path, cases=flat), SYNTHETIC_REGISTRY


def _row10(tmp_path):
    """The milestone's opening finding. `gates.eval_min_cases: 20 -> 0` was
    **1881 passed, zero failures** on `6af17d2`."""
    m = good_manifest()
    m["gates"]["eval_min_cases"] = 0
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


def _row11(tmp_path):
    cases = good_cases()
    cases[3]["expect_near_treshold"] = True          # the typo the band absorbs at N=20
    return make_service(tmp_path, cases=cases), SYNTHETIC_REGISTRY


def _row12(tmp_path):
    m = good_manifest()
    del m["gates"]["budgets"][floors.REQUIRED_BUDGET_KEYS[0]]
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


def _row13(tmp_path):
    return make_service(tmp_path), SYNTHETIC_REGISTRY + [dict(SYNTHETIC_REGISTRY[0])]


def _row14(tmp_path):
    m = good_manifest()
    m["brand"] = "meridian-news"
    return make_service(tmp_path, manifest=m), SYNTHETIC_REGISTRY


#: One violating input per row. Kept beside `manifest.ROWS` and checked against it
#: in both directions, so neither list can drift past the other.
PRODUCERS = {
    1: _row1, 2: _row2, 3: _row3, 4: _row4, 5: _row5, 6: _row6, 7: _row7,
    8: _row8, 9: _row9, 10: _row10, 11: _row11, 12: _row12, 13: _row13, 14: _row14,
}

#: The "message names" column of SPEC/05's refusal table, as assertions. A row that
#: fires with a message naming none of these is a FAIL a reader cannot act on,
#: which is the `_die("check failed")` shape ADR-042 recorded: a tool name, a
#: number, and no next step.
MUST_NAME = {
    1: ["runtime", "line"],
    2: ["tool-zzz", "platform/registry/tools.yaml"],
    3: ["tool-b", "svc-one", "callers"],
    4: ["tool-b", "svc-one", "pave.manifest.yaml"],
    5: ["template", "read by"],
    6: ["public", "internal", "0 of 25"],
    7: ["svc-elsewhere", "svc-one"],
    8: ["5 disposed", str(floors.PLATFORM_EVAL_MIN_CASES), floors.SCAFFOLD_AUTHOR],
    9: ["0/20", "5%-10%", "disposed"],
    10: ["0", str(floors.PLATFORM_EVAL_MIN_CASES), "eval_min_cases"],
    11: ["expect_near_treshold", "Known keys"],
    12: [floors.REQUIRED_BUDGET_KEYS[0], "no ceiling"],
    13: ["tool-a", "cannot decide twice"],
    14: ["meridian-news", floors.SUPPORTED_BRANDS[0], "brand_tone"],
}


def test_the_table_and_the_producers_agree():
    """Both directions. A row in the table with no producer is a stated protection
    that fires on nothing — worse than an absent one, because it stops anyone
    looking for the real one. A producer for a row nobody wrote down is a refusal
    a team meets with no documentation to reach."""
    assert set(PRODUCERS) == set(manifest_mod.ROWS), (
        f"rows with no producer: {sorted(set(manifest_mod.ROWS) - set(PRODUCERS))}; "
        f"producers for no row: {sorted(set(PRODUCERS) - set(manifest_mod.ROWS))}.")
    assert set(MUST_NAME) == set(manifest_mod.ROWS)


@pytest.mark.parametrize("row", sorted(PRODUCERS))
def test_each_row_fires_on_its_own_input(row, tmp_path):
    directory, registry = PRODUCERS[row](tmp_path)
    fired = _rows(directory, registry)
    assert row in fired, (
        f"row {row} ({manifest_mod.ROWS[row]}) did not fire on the input built to "
        f"trip it. Rows that fired: {sorted(set(fired))}.")


@pytest.mark.parametrize("row", sorted(MUST_NAME))
def test_each_refusal_names_what_the_table_promises(row, tmp_path):
    directory, registry = PRODUCERS[row](tmp_path)
    text = "\n".join(f.message for f in manifest_mod.verify(directory, registry=registry)
                     if f.row == row)
    missing = [want for want in MUST_NAME[row] if want not in text]
    assert not missing, (
        f"row {row}'s message does not name {missing}. SPEC/05's table is the "
        f"commitment and this is it as an assertion.\n\nmessage:\n{text}")


def test_the_public_refusal_does_not_read_as_a_mitigation(tmp_path):
    """`public` is the one value a reader will assume is the safe choice, and it is
    an **outage**: measured, a service declaring it is allowed 0 of 25 committed
    golden cases, because `route` refuses every request that classifies above the
    declaration. A message that says only "not in the vocabulary" invites the exact
    reading this repository's baseline-honesty rule exists to prevent."""
    directory, registry = _row6(tmp_path)
    text = "\n".join(f.message for f in manifest_mod.verify(directory, registry=registry)
                     if f.row == 6)
    assert "outage" in text and "0 of 25" in text, text


# --- prediction 1: every one of the manifest's fields ---------------------------

@pytest.mark.parametrize("field", sorted(manifest_mod.REQUIRED_FIELDS))
def test_deleting_any_required_field_is_a_named_refusal(field, tmp_path):
    """**Six of the ten were deletable at 1861 passed, zero failures**, and the
    four that went red went red incidentally — a `KeyError` from a test reading the
    field for another purpose, never a refusal naming it.

    The message must also name **what reads the field**. "Required" with no reader
    is a rule nobody can argue with, and it is why six of these had no defender:
    nobody could say what would break."""
    body = good_manifest()
    cursor, *rest = field.split(".")
    if rest:
        del body[cursor][rest[0]]
    else:
        del body[cursor]
    directory = make_service(tmp_path, manifest=body)
    findings = [f for f in manifest_mod.verify(directory, registry=SYNTHETIC_REGISTRY)
                if f.row == 5 and f.where.endswith(field)]
    assert findings, (
        f"deleting {field!r} earned no row-5 refusal. Rows that fired: "
        f"{sorted(set(_rows(directory)))}.")
    assert "read by" in findings[0].message and len(findings[0].message) > 40


def test_every_field_the_reference_manifest_carries_is_required():
    """**A decorative field is worse than no field** (Tool Owner, on `semver:`): it
    reads as a control, is defended by nothing, and stops the next reader looking
    for the real one. So the committed manifest may not carry a top-level key this
    verifier has no reader for."""
    committed = manifest_mod.load(
        manifest_mod.SERVICES / "highlights-agent" / manifest_mod.MANIFEST_NAME)
    required_tops = {f.split(".")[0] for f in manifest_mod.REQUIRED_FIELDS}
    extra = sorted(set(committed) - required_tops)
    assert not extra, (
        f"the reference manifest carries {extra}, which `REQUIRED_FIELDS` names no "
        "reader for. Either name the reader or delete the field — a field the "
        "verifier ignores is a field a team will fill in believing it does "
        "something.")


# --- the loader ------------------------------------------------------------------

def test_the_loader_reports_both_line_numbers(tmp_path):
    """`yaml.safe_load` resolves a duplicated key to its LAST value in silence, so
    the block a human finds first is the one that does not apply. Both numbers,
    because pointing only at the winner sends a reader to the line they already
    read."""
    path = tmp_path / "m.yaml"
    path.write_text("gates:\n  eval_min_cases: 20\ngates:\n  eval_min_cases: 0\n",
                    encoding="utf-8")
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == {"gates": {"eval_min_cases": 0}}
    with pytest.raises(manifest_mod.DuplicateKey) as caught:
        manifest_mod.load(path)
    assert (caught.value.first_line, caught.value.second_line) == (1, 3)


def test_the_loader_reaches_nested_mappings(tmp_path):
    """A duplicate two levels down is the one a reviewer misses, and a loader that
    only guards the document root would pass it."""
    path = tmp_path / "m.yaml"
    path.write_text("gates:\n  budgets:\n    max_ms: 1\n    max_ms: 2\n",
                    encoding="utf-8")
    with pytest.raises(manifest_mod.DuplicateKey):
        manifest_mod.load(path)


# --- the command -----------------------------------------------------------------

def test_the_command_is_green_on_the_committed_tree():
    lines = []
    assert verify_mod.verify(("--all",), emit=lines.append) == gate_mod.EXIT_OK
    assert any("PASS highlights-agent" in line for line in lines), lines


def test_the_command_refuses_an_empty_argument_list():
    """Fail-closed rather than defaulting to `--all`. A verifier whose scope is
    decided by an omitted argument is `gate decide`'s closed `--verdicts` list one
    component over, where an absent verdict is not "absent and blocking" but "not
    consulted"."""
    lines = []
    assert verify_mod.verify((), emit=lines.append) == gate_mod.EXIT_CONTRACT
    assert "--all" in "\n".join(lines)


def test_a_manifest_failure_pages_the_team_and_a_missing_service_pages_the_platform(
        monkeypatch, tmp_path):
    """`gate.py`'s split, kept. A bad manifest is `EXIT_QUALITY` — the service
    team's. A verifier that cannot find what it was asked about is `EXIT_CONTRACT`
    — the platform's, and it reaches a different pager.

    **The first version of this test asserted only the second half**, under this
    exact name. Measured in the deletability audit: replacing `if total:` with
    `if False:` — so a service with findings exits **0** — was **1982 passed,
    silent**. A test named for a protection it does not exercise is worse than an
    absent one, because it stops anyone looking for the real one, and this file's
    own docstring says so about a different check."""
    bad = make_service(tmp_path)                      # `tool-a` is in no real registry
    monkeypatch.setattr(manifest_mod, "SERVICES", bad.parent)
    lines = []
    assert verify_mod.verify(("--all",), emit=lines.append) == gate_mod.EXIT_QUALITY, (
        "a service with findings exited 0. `pave verify` is what `make core` puts "
        "before `cdk deploy` on one `&&`-joined line, so its exit code IS the gate "
        "there — a zero exit deploys the service it just refused.")
    assert any("FAIL" in line for line in lines), lines

    lines = []
    assert verify_mod.verify(("svc-that-does-not-exist",),
                             emit=lines.append) == gate_mod.EXIT_CONTRACT


def test_the_command_states_its_limits_on_a_green_run():
    """A tool that lists what it did not check only when it fails is a tool whose
    limits are read by nobody who passed — and every deferral here is something a
    reader would otherwise assume from the PASS. Item 29's commitment is that a
    gap is deferred **by name**."""
    lines = []
    verify_mod.verify(("--all",), emit=lines.append)
    printed = "\n".join(lines)
    # **The names, not the count.** Iterating `DEFERRED` and asserting each entry is
    # printed cannot see an entry DELETED: the loop simply runs one fewer time, and
    # an emptiness guard only catches `{}`. That is "a count sees arithmetic, not
    # identity" (ADR-045 decision 5) reappearing inside a check written to state a
    # gap rather than close it.
    assert set(manifest_mod.DEFERRED) == {
        "range evaluation", "brand-with-no-pack", "whether the declaration is honest",
    }, (
        f"the deferral list is {sorted(manifest_mod.DEFERRED)}. Item 29's commitment "
        "is that a gap is deferred BY NAME — dropping a name does not close the gap, "
        "it stops the gap being stated, and the next reader takes the PASS at face "
        "value.")
    for what in manifest_mod.DEFERRED:
        assert what in printed, f"a green run does not mention the {what!r} deferral"


def test_the_range_is_not_evaluated_and_the_output_says_so(tmp_path):
    """`@^0` is decorative: no site in this repository parses a range, and the one
    that splits on `@` throws it away. The verifier must not imply otherwise —
    stating the gap is the whole of what M05 buys here (SPEC/05 item 22)."""
    m = good_manifest()
    m["tools"] = [{"id": "tool-a@not-a-range-at-all"}]
    assert _rows(make_service(tmp_path, manifest=m)) == [], (
        "the verifier refused a malformed range. It evaluates none, so refusing one "
        "form implies an evaluator that does not exist — and under the 0.x "
        "convention the form it would refuse first (`^0`) is the WIDEST caret, not "
        "the tightest.")
    assert "range" in "\n".join(manifest_mod.DEFERRED)


# --- the criteria stay single-sourced -------------------------------------------

def test_the_case_vocabulary_has_one_home():
    """`CASE_TOP_LEVEL_KEYS` moved to `pave/floors.py` because this verifier needed
    it and `tests/test_contracts.py` held it as a bare set literal. Two copies of a
    vocabulary is ADR-045 decision 7 and ADR-037, and the second copy is always the
    one nothing goes red about."""
    from tests import test_contracts
    assert test_contracts.CASE_KEYS is floors.CASE_TOP_LEVEL_KEYS, (
        "`tests/test_contracts.py` holds its own copy of the case vocabulary again. "
        "The narrower gate wins at runtime, so nothing goes red — which is exactly "
        "what makes that shape durable.")


#: Each criterion the verifier must READ rather than restate, the move that proves
#: it, and the row that move must produce. A criterion inlined in `pave/manifest.py`
#: is a criterion on Platform Engineering's key instead of AI Quality's.
CRITERIA_MOVES = {
    "PLATFORM_EVAL_MIN_CASES": (999, 8),
    "DECLARABLE_LEVELS": (("public",), 6),
    "SUPPORTED_BRANDS": (("meridian-elsewhere",), 14),
    "REQUIRED_BUDGET_KEYS": (("p95_ms", "max_ms", "max_tokens_in", "max_tokens_out",
                              "a_key_no_manifest_carries"), 12),
    "CASE_TOP_LEVEL_KEYS": (frozenset(), 11),
}


@pytest.mark.parametrize("name", sorted(CRITERIA_MOVES))
def test_the_verifier_follows_its_criteria_when_they_move(name, monkeypatch, tmp_path):
    """**Applied, not textual.** The first version of this test grepped
    `pave/manifest.py` for `floors.<NAME>` — and ADR-045 measured that exact shape
    at 1864 passed, because an import line satisfies a source assertion looking for
    an import line. So each criterion is *moved* and the verifier must follow it.

    An inlined copy passes the grep and fails this."""
    value, row = CRITERIA_MOVES[name]
    directory = make_service(tmp_path)
    assert manifest_mod.verify(directory, registry=SYNTHETIC_REGISTRY) == [], (
        "the fixture is not clean before the move, so the row below proves nothing")
    monkeypatch.setattr(floors, name, value)
    fired = _rows(directory)
    assert row in fired, (
        f"moving `floors.{name}` did not change what the verifier refuses (rows "
        f"fired: {sorted(set(fired))}). `pave/manifest.py` is deciding on a copy.")


def test_headroom_goes_through_the_shared_checker(monkeypatch, tmp_path):
    """`HEADROOM_BAND` is the one criterion `pave/manifest.py` never names, and that
    is correct: it delegates to `floors.check_headroom`, so the band and the ratio
    arithmetic are single-sourced with `tests/test_contracts.py`. Moving the constant
    would not prove that — `check_headroom` binds it as a default argument at import
    — so this proves the delegation directly."""
    sentinel = "the shared checker ran"

    def _boom(cases, *args, **kwargs):
        raise ValueError(sentinel)

    monkeypatch.setattr(floors, "check_headroom", _boom)
    findings = manifest_mod.verify(make_service(tmp_path), registry=SYNTHETIC_REGISTRY)
    assert [f.row for f in findings] == [9] and sentinel in findings[0].message, (
        "`pave/manifest.py` computes headroom itself instead of calling "
        "`floors.check_headroom`. Two implementations of one band is how the "
        "denominator can differ between the gate and the verifier without either "
        "going red.")
