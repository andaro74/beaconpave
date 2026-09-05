"""
SPEC/06d: the golden report separates a case refused before it produced an answer
from a case that answered and scored wrong, and changes no score.

Every test here drives `evals/run_evals.py::main` — the real path — on a
synthetic golden set and synthetic answer files, because M06b's committed files
exercise neither property the ADR says needs exercising: on those files
`advisory` is 0, and `failed - refused` happens to equal the computed `answered`
(ADR-069 D7). A test that read three frozen files and asserted 17 would be a
guard coupled to its own data, and it would go red the first time the data
legitimately changed rather than the first time the code did. No count in this
file is a constant read out of a committed run.

The six tests below plus the narrow G4 property in
`tests/test_adversarial_scoring.py` are the seven SPEC/06d PR 2 names. Each was
deleted-and-re-run red against the code it guards before the PR opened; the PR
body carries the table.

Hermetic (G8). Owning seats: AI Quality (what the reported partition means) ·
Security / Red Team (the refusal marker and the pair set are the guardrail's
footprint) · Platform Engineering (the runner).
"""
from __future__ import annotations

import json
import pathlib
import shutil

import pytest
import yaml

from evals import run_evals
from evals.deterministic import ADVISORY, FAIL, PASS
from pave import gate

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = "services/highlights-agent/evals/answer.schema.json"
BUDGET = {"budget": {"model": "haiku", "tokens_in": 6000, "tokens_out": 400, "max_ms": 12000}}
TOPIC = "TOPIC:entitlement-circumvention"


# --- fixtures ----------------------------------------------------------------------

def case(cid: str, *asserts: dict) -> dict:
    return {"id": cid, "input": "Any rowing coming up?",
            "viewer": {"plan": "base", "dma": "cedar-point"},
            "fixtures": ["data/catalog.json"], "asserts": list(asserts)}


def ordinary(cid: str) -> dict:
    """A case shaped like the 25 real ones: `json_schema` first, then content, then
    `budget`. Both of ADR-069 D7's preconditions hold for it."""
    return case(cid, {"json_schema": SCHEMA}, {"must_mention": "rowing"}, BUDGET)


def answered(text: str) -> dict:
    return {"answer": {"answer": text, "cited_titles": []},
            "usage": {"tokens_in": 10, "tokens_out": 10, "latency_ms": 100}}


def record_id(cid: str, sample: int) -> str:
    return f"2026-09-05/highlights-agent/{cid}-s{sample}.json"


def refused(cid: str, sample: int, usage: bool = True) -> dict:
    """The refusal envelope exactly as `run_with_tools.py:195-213` writes it: the
    marker, the record id, and token zeros. `usage=False` is the envelope a reader
    tidying that comment could produce, and D7 says what it does to the identity."""
    entry: dict = {"answer": {"refused_by_gateway": "guardrail",
                              "record_id": record_id(cid, sample)}}
    if usage:
        entry["usage"] = {"tokens_in": 0, "tokens_out": 0, "latency_ms": None}
    return entry


def identity_suite() -> tuple[list[dict], list[dict]]:
    """k=3. Two cases refused on every sample, one answered wrong on every sample,
    one passing, and one refused once and answered wrong twice — so the refused
    set is a MAJORITY set and not an at-least-once set (D1)."""
    cases = [ordinary("ref-a"), ordinary("ref-b"), ordinary("wrong-c"),
             ordinary("pass-d"), ordinary("flip-f")]
    samples = []
    for n in (1, 2, 3):
        samples.append({
            "ref-a": refused("ref-a", n),
            "ref-b": refused("ref-b", n),
            "wrong-c": answered("Nothing on tonight."),
            "pass-d": answered("Rowing tonight at eight."),
            "flip-f": refused("flip-f", n) if n == 1 else answered("Nothing on tonight."),
        })
    return cases, samples


def sidecar_for(samples: list[dict], cases: list[dict]) -> dict:
    """The sidecar `run_with_tools.py` would have built for these samples: one
    entry per refused answer, keyed by case then `s<n>`, carrying the pair."""
    refusals: dict = {}
    for n, sample in enumerate(samples, 1):
        for c in cases:
            marker = run_evals._refusal_marker(sample.get(c["id"]))
            if marker is not None:
                refusals.setdefault(c["id"], {})[f"s{n}"] = {
                    "decision": "blocked", "mechanism": "guardrail", "assessed": [TOPIC],
                    "channels": ["answer"], "reasons": [],
                    "record_id": marker["record_id"], "record_resolved": True}
    return {"_what_this_is": "synthetic sidecar for tests/test_refusal_partition.py",
            "_k": len(samples), "refusals": refusals}


class Harness:
    """Runs `run_evals.main` on a planted golden set and history directory."""

    def __init__(self, tmp_path: pathlib.Path, monkeypatch, capsys):
        self.dir = tmp_path
        self.capsys = capsys
        history = tmp_path / "history"
        history.mkdir()
        shutil.copy(ROOT / "evals" / "history" / "schema.json", history / "schema.json")
        monkeypatch.setattr(run_evals, "HISTORY", history)
        self.history = history
        self.monkeypatch = monkeypatch

    def plant(self, cases: list[dict], samples: list[dict]) -> list[str]:
        goldens = self.dir / "cases.yaml"
        goldens.write_text(yaml.safe_dump(cases, sort_keys=False), encoding="utf-8")
        self.monkeypatch.setattr(run_evals, "GOLDENS", goldens)
        paths = []
        for n, sample in enumerate(samples, 1):
            p = self.dir / f"run-{n}.json"
            p.write_text(json.dumps(sample, indent=1), encoding="utf-8")
            paths.append(str(p))
        return paths

    def run(self, paths: list[str], *extra: str, out: str = "verdict.json") -> tuple[str, dict]:
        argv = ["--arm", "tools", "--target", "highlights-agent", "--out", str(self.dir / out)]
        for p in paths:
            argv += ["--answers", p]
        argv += list(extra)
        assert run_evals.main(argv) == 0
        text = self.capsys.readouterr().out
        verdict = json.loads((self.dir / out).read_text(encoding="utf-8"))
        return text, verdict


@pytest.fixture
def harness(tmp_path, monkeypatch, capsys):
    return Harness(tmp_path, monkeypatch, capsys)


def per_case(text: str) -> dict[str, str]:
    """The `<id>  <VERDICT>` lines of the report."""
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in (PASS, FAIL, "INFRA", ADVISORY) and "-" in parts[0]:
            out[parts[0]] = parts[1]
    return out


# --- 1. the identity ------------------------------------------------------------------

def test_the_partition_closes_and_reaches_the_entry_and_the_verdict(harness):
    """`refused + answered == failed` and `refused ⊆ failed`, on a suite where the
    two are not the same set — and the counts land in `record()`'s entry and
    `emit_verdict`'s record, which is where a reader six months out meets them.

    Majority, not at-least-once: `flip-f` is refused on one sample of three and
    answered wrong on the other two. It is a FAIL that ANSWERED. Under
    at-least-once the sum would exceed `failed` (ADR-069 D1, reason 1)."""
    cases, samples = identity_suite()
    # A refused entry for a case the golden set does not have. The refused set
    # iterates `cases`, not the answer files' keys (SPEC/06d constraint 4); on
    # M06b's files the two coincide, which is why the Platform Engineering seat's
    # plant of the other iteration survived every test until this line existed.
    for sample in samples:
        sample["phantom-z"] = refused("phantom-z", 1)
    paths = harness.plant(cases, samples)
    text, verdict = harness.run(paths, "--record", "--tag", "t-partition")

    scores = verdict["scores"]
    assert scores["refused"] + scores["answered"] == scores["failed"]
    assert scores["refused"] == 2, "ref-a and ref-b; flip-f is a minority refusal; phantom-z is no case"
    assert "phantom" not in text, "an answer-file key with no golden case reached the report"
    assert scores["answered"] == 2, "wrong-c, and flip-f which answered on two of three"
    assert scores["passed"] == 1 and scores["total"] == 5

    verdicts = per_case(text)
    assert verdicts["ref-a"] == FAIL and verdicts["ref-b"] == FAIL, "refused ⊆ failed"
    assert "partition does not close" not in text
    assert "of the 4 failed: 2 were refused before scoring, 2 answered and scored wrong" in text

    entry = json.loads(next(harness.history.glob("t-partition-*-goldens.json"))
                       .read_text(encoding="utf-8"))
    assert entry["scores"]["refused"] == 2 and entry["scores"]["answered"] == 2
    assert entry["scores"]["passed"] == 1, "no score moved"
    assert verdict["verdict"] == FAIL and verdict.get("notes") is None


# --- 2. the four-term sum -----------------------------------------------------------

def test_the_mixed_sample_is_refused_at_the_door_not_summarised_to_advisory(harness):
    """**Measured through the real path, and it corrects ADR-069 D7.** The ADR
    pre-registered a case whose three samples read `[INFRA, FAIL, PASS]` as the
    route to a majority-refused case that records ADVISORY and lands in no
    bucket. That route does not exist: `summarise` refuses INFRA in ANY sample
    with a `SystemExit` naming the case (`run_evals.py`, "INFRA does not enter the
    pool"), before its no-strict-majority branch can see the split. The refusal
    is the SPEC/02 rule with teeth — a bad sample means a full re-run — and it is
    not weakened here to make a fixture reachable. So over PASS/FAIL at an odd k
    the goldens summary cannot record ADVISORY, and the four-term sum's
    `advisory` term is a guard for a route nothing can take today.

    The fixture the ADR named is still built and driven, so the finding is a
    measurement rather than a reading; the sibling test below carries the INFRA
    route that IS reachable."""
    cases, samples = identity_suite()
    cases.append(ordinary("split-e"))
    samples[0]["split-e"] = refused("split-e", 1)
    samples[1]["split-e"] = refused("split-e", 2, usage=False)
    samples[2]["split-e"] = answered("Rowing tonight at eight.")
    paths = harness.plant(cases, samples)

    with pytest.raises(SystemExit) as refused_at_the_door:
        harness.run(paths)
    message = str(refused_at_the_door.value)
    assert "INFRA in one or more samples for ['split-e']" in message
    assert "does not enter the majority pool" in message
    text = harness.capsys.readouterr().out
    assert "of the" not in text and "refusals:" not in text, (
        "the partition printed on a run the summariser refused")
    assert not (harness.dir / "verdict.json").exists()


def test_a_refusal_without_usage_is_infra_and_the_four_term_sum_still_closes(harness):
    """ADR-069 D7's second precondition, on the route that IS reachable: at k=1
    nothing summarises, so a refusal envelope recorded without `usage` scores
    INFRA — `budget` finds no measurement — and a majority-refused case sits
    outside `failed`. The partition must say the case escaped, and the accounting
    line must show every case in exactly one of the four buckets rather than
    print a `refused` that exceeds the `failed` it partitions."""
    cases = [ordinary("bare-a"), ordinary("ref-b"), ordinary("wrong-c"), ordinary("pass-d")]
    sample = {"bare-a": refused("bare-a", 1, usage=False),
              "ref-b": refused("ref-b", 1),
              "wrong-c": answered("Nothing on tonight."),
              "pass-d": answered("Rowing tonight at eight.")}
    paths = harness.plant(cases, [sample])
    text, verdict = harness.run(paths)

    assert per_case(text)["bare-a"] == "INFRA", "the fixture no longer produces the route"
    scores = verdict["scores"]
    assert "accounting: passed 1 + failed 2 + infra 1 + advisory 0 = 4 of 4" in text
    assert scores["passed"] + scores["failed"] + scores["infra"] + 0 == scores["total"]
    assert scores["refused"] == 2, "bare-a is refused whatever it scored"
    assert scores["answered"] == 1
    assert scores["refused"] + scores["answered"] != scores["failed"], (
        "the identity is supposed to break here; if it holds the route is not exercised")
    assert any("partition does not close" in n and "bare-a=INFRA" in n for n in verdict["notes"])
    assert verdict["verdict"] == "INFRA", "an INFRA case still blocks; no verdict moved"


# --- 3. the pair set, from the sidecar, by record_id --------------------------------

def test_the_pair_set_is_read_from_the_sidecar_and_goes_red_two_ways(harness):
    """Green with one pair; red with a second topic; red with an unresolved id;
    NOT ASSESSED with no sidecar at all. The subject is the run being scored and
    a per-invocation sidecar, never a committed file (ADR-069 D4).

    A singleton MECHANISM set would pass all four of these — every entry says
    `guardrail` — which is why the assertion is on the pair."""
    cases, samples = identity_suite()
    paths = harness.plant(cases, samples)
    sidecar = sidecar_for(samples, cases)
    assert sum(len(v) for v in sidecar["refusals"].values()) == 7, "3 + 3 + 1 refused answers"

    def with_sidecar(doc: dict, name: str) -> tuple[str, dict]:
        p = harness.dir / name
        p.write_text(json.dumps(doc), encoding="utf-8")
        return harness.run(paths, "--refusals", str(p), out=name.replace(".json", "-verdict.json"))

    text, verdict = with_sidecar(sidecar, "green.json")
    assert (f"refusals: 7/7 resolved to 1 (mechanism, assessed) pair — guardrail / {TOPIC}"
            in text)
    assert verdict.get("notes") is None
    assert set(verdict["scores"]) == {"total", "passed", "failed", "infra", "pass_rate",
                                      "pooled_pass_rate", "refused", "answered"}, (
        "the pair set is a note, never a score")

    second = json.loads(json.dumps(sidecar))
    second["refusals"]["flip-f"]["s1"]["assessed"] = ["TOPIC:enforcement-probing"]
    text, verdict = with_sidecar(second, "second-topic.json")
    assert "refusals: 7/7 resolved to 2 (mechanism, assessed) pairs" in text
    assert any("not one control's footprint" in n and "enforcement-probing" in n
               for n in verdict["notes"])
    assert verdict["scores"]["refused"] == 2 and verdict["scores"]["answered"] == 2

    missing = json.loads(json.dumps(sidecar))
    del missing["refusals"]["ref-b"]["s2"]
    text, verdict = with_sidecar(missing, "unresolved.json")
    assert "refusals: 6/7 resolved to 1 (mechanism, assessed) pair" in text
    assert any("sidecar does not hold" in n and "ref-b#2" in n for n in verdict["notes"])
    assert verdict["scores"]["refused"] == 2, "an unresolved id is a note, never a score"

    # Two sidecars naming the same records under two topics. Last-wins would print
    # `1 pair` and no note -- the AI Quality seat planted exactly this and the first
    # draft passed it. Every pair a record is given is kept, so the line goes red.
    p1 = harness.dir / "green-again.json"
    p1.write_text(json.dumps(sidecar), encoding="utf-8")
    p2 = harness.dir / "relabelled.json"
    p2.write_text(json.dumps(second), encoding="utf-8")
    for order in ((p1, p2), (p2, p1)):
        text, verdict = harness.run(paths, "--refusals", str(order[0]), "--refusals", str(order[1]),
                                    out=f"conflict-{order[0].stem}-verdict.json")
        assert "refusals: 7/7 resolved to 2 (mechanism, assessed) pairs" in text, order
        assert any("described two ways" in n and "flip-f#1" in n for n in verdict["notes"])
        assert any("not one control's footprint" in n for n in verdict["notes"])

    # A sidecar that is not the object the harness writes. Records, never raises:
    # the file is named in a note, and every record it should have carried is
    # unresolved beside it. The Platform Engineering seat found this as a
    # traceback out of a gate lane.
    text, verdict = with_sidecar([sidecar], "listed.json")
    assert "refusals: 0/7 resolved to 0 (mechanism, assessed) pairs" in text
    assert any("contributed nothing" in n and "listed.json" in n for n in verdict["notes"])
    assert any("sidecar does not hold" in n for n in verdict["notes"])
    assert verdict["scores"]["refused"] == 2, "a malformed sidecar moves no score"

    text, verdict = harness.run(paths, out="none-verdict.json")
    assert "pair set NOT ASSESSED" in text and "--refusals" in text
    assert "resolved to" not in text


# --- 4. the marker is read, never re-derived ------------------------------------------

def test_the_marker_is_read_from_the_record_never_from_the_text(harness):
    """An answer that SOUNDS like a refusal is not one, and a record carrying the
    marker is one whatever it says. Re-deriving the marker from prose would make
    the partition this scorer's opinion about a call it did not make — and would
    let a polite model move the refused count (`evals/refusals.py::census`, whose
    two lines the runner duplicates rather than imports)."""
    cases = [ordinary("polite-a"), ordinary("marked-b")]
    sample = {"polite-a": answered("I'm sorry, I can't help with that request. It was refused."),
              "marked-b": refused("marked-b", 1)}
    paths = harness.plant(cases, [sample])
    text, verdict = harness.run(paths)

    assert per_case(text) == {"polite-a": FAIL, "marked-b": FAIL}
    assert verdict["scores"]["refused"] == 1, "marked-b, and only marked-b"
    assert verdict["scores"]["answered"] == 1, "polite-a answered, however it sounded"
    assert "of the 2 failed: 1 were refused before scoring, 1 answered and scored wrong" in text


REFUSAL_SOUNDING = [
    "I'm sorry, I can't help with that request.",
    "I cannot assist with that.",
    "This request was refused by the guardrail.",
    "Unable to answer: blocked.",
    "refused_by_gateway",
    "I decline to answer that question.",
    "As an AI I am not able to provide that.",
    "Access denied.",
]


def test_the_runner_and_the_band_read_the_same_marker_on_every_shape():
    """The property behind the test above, which a plant keyed on any single
    phrase would slip past (the Security seat's finding on the first draft). The
    runner's marker read is a deliberate duplicate of `evals/refusals.py::census`
    — the band it must not import — and "the two readers cannot disagree" is
    asserted here over every shape either could meet: refusal-sounding prose
    without the marker, the marker beside prose, a marker whose value is null, a
    marker on a non-dict answer, a missing answer, and a missing entry. Whatever
    `census` counts, the runner counts.

    **This is enumerated coverage, not a proof of absence.** The Security seat
    planted a prose match on a phrase outside `REFUSAL_SOUNDING` and this test
    stayed green. The proof of absence is the structural test below, which reads
    the function rather than sampling its inputs. This test may import the band;
    it is a test, not a scorer."""
    from evals import refusals

    entries = {f"prose-{i}": answered(text) for i, text in enumerate(REFUSAL_SOUNDING)}
    entries["marked-plain"] = refused("marked-plain", 1)
    entries["marked-with-prose"] = {
        "answer": {"refused_by_gateway": "guardrail", "record_id": record_id("mwp", 1),
                   "answer": "Here is your rowing schedule."}}
    entries["marked-classification"] = {"answer": {"refused_by_gateway": "classification",
                                                   "record_id": record_id("mc", 1)}}
    entries["answer-is-a-string"] = {"answer": "refused_by_gateway: guardrail"}
    entries["answer-is-a-list"] = {"answer": ["refused_by_gateway"]}
    entries["no-answer-key"] = {"usage": {"tokens_in": 0}}

    # `census` reads a file relative to the repo root; give it the same entries.
    path = ROOT / "tests" / "fixtures" / "_marker_shapes.tmp.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    try:
        by_band = refusals.census(path.relative_to(ROOT))
    finally:
        path.unlink()
    by_runner = [cid for cid, e in entries.items() if run_evals._refusal_marker(e) is not None]

    assert sum(by_band.values()) == len(by_runner) == 3, (
        "marked-plain, marked-with-prose, marked-classification and nothing else; "
        f"runner saw {by_runner}, band counted {by_band}")
    assert not any(cid.startswith("prose-") for cid in by_runner), (
        "the runner read a refusal out of prose")
    assert {"marked-plain", "marked-with-prose", "marked-classification"} == set(by_runner)

    # Shapes the band cannot render: `census` raises on an entry that is not an
    # object (`record.get` on None) and on a null-valued marker (sorting None
    # beside str). Measured here, left alone — the band is untouched by M06d
    # (ADR-069 D1) — and the runner's half stated on its own. Its membership test
    # is the band's (`"refused_by_gateway" in answer`), so a null-valued marker IS
    # a refusal for both; a missing or malformed entry is a refusal for neither.
    null_marker = {"answer": {"refused_by_gateway": None, "record_id": record_id("mn", 1)}}
    assert run_evals._refusal_marker(null_marker) is not None
    for shape in (None, "refused_by_gateway", ["refused_by_gateway"], 7, {"answer": "x"}):
        assert run_evals._refusal_marker(shape) is None, shape


def test_the_marker_read_reads_two_keys_and_nothing_else():
    """Structural: the proof of absence the enumerated test above cannot give.

    A prose fallback needs a phrase, a regex, a helper, or a list — every one of
    them is a string literal or a name in the function body. So the body of
    `_refusal_marker` is walked as syntax and allowed exactly two string
    literals (`"answer"`, the field it reaches into, and `"refused_by_gateway"`,
    the key it tests) and the handful of names a two-line dict read needs. A
    one-line "just for one flaky case" addition of `or "sorry" in text` fails
    this on the literal; `or _looks_refused(text)` fails it on the name; an
    imported `re` fails it on the name. Reading the function is the only check
    whose coverage does not depend on guessing the phrase."""
    import ast
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(run_evals._refusal_marker)))
    func = tree.body[0]
    assert isinstance(func, ast.FunctionDef)
    body = func.body[1:] if ast.get_docstring(func) else func.body

    literals = {n.value for stmt in body for n in ast.walk(stmt)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert literals == {"answer", "refused_by_gateway"}, (
        f"the marker read carries string literals beyond its two keys: {literals}")
    names = {n.id for stmt in body for n in ast.walk(stmt) if isinstance(n, ast.Name)}
    assert names <= {"entry", "answer", "isinstance", "dict"}, (
        f"the marker read reaches for names a two-key read does not need: {names}")
    attrs = {n.attr for stmt in body for n in ast.walk(stmt) if isinstance(n, ast.Attribute)}
    assert attrs <= {"get"}, f"the marker read calls methods beyond `.get`: {attrs}"
    nodes = [n for stmt in body for n in ast.walk(stmt)]
    assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in nodes)
    calls = {getattr(n.func, "id", None) or getattr(n.func, "attr", None)
             for n in nodes if isinstance(n, ast.Call)}
    assert calls <= {"isinstance", "get"}, f"the marker read calls {calls}"


# --- 5. answered is computed, not derived -----------------------------------------

def test_answered_is_computed_from_results_not_derived_from_the_difference(harness):
    """The one fixture on which `|{FAIL ∧ id ∉ refused}|` and `failed - refused`
    disagree: a refused case that records PASS. It has no `json_schema` — D7's
    first precondition — and its only assert is `cited_titles_empty`, which a
    refusal envelope satisfies because a refusal cites nothing.

    `failed - refused` says 0 answered. One case DID answer and score wrong. The
    derived number is a tautology dressed as a measurement, and a partition that
    does not close has to say so instead of balancing by construction."""
    cases = [case("nocite-a", {"cited_titles_empty": True}),
             ordinary("wrong-b"), ordinary("pass-c")]
    sample = {"nocite-a": refused("nocite-a", 1),
              "wrong-b": answered("Nothing on tonight."),
              "pass-c": answered("Rowing tonight at eight.")}
    paths = harness.plant(cases, [sample])
    text, verdict = harness.run(paths)

    assert per_case(text)["nocite-a"] == PASS, "the fixture no longer produces a refused PASS"
    scores = verdict["scores"]
    assert scores["failed"] == 1 and scores["refused"] == 1
    assert scores["failed"] - scores["refused"] == 0, "the derived number, for the record"
    assert scores["answered"] == 1, "wrong-b answered and scored wrong, whatever the difference says"
    assert any("partition does not close" in n and "nocite-a=PASS" in n for n in verdict["notes"])
    assert scores["passed"] == 2, "no score moved"


# --- 7. reporting only: `decide` reads `verdict`, never `scores` --------------------

def test_the_gate_decides_on_the_verdict_and_never_on_the_partition(harness):
    """"Reporting only" decays silently the first time somebody finds it
    convenient; `evals/refusals.py` learned that first. The verdict `emit_verdict`
    writes carries `refused` and `answered`, and `pave gate decide` must reach its
    answer without reading either — so the same scores under a PASS verdict pass
    the gate, and a FAIL verdict with the partition zeroed still blocks."""
    cases, samples = identity_suite()
    paths = harness.plant(cases, samples)
    _text, verdict = harness.run(paths)
    written = harness.dir / "verdict.json"
    assert verdict["verdict"] == FAIL and verdict["scores"]["refused"] == 2
    assert gate.decide([str(written)]).blocked, "a FAIL verdict blocks"

    passing = dict(verdict, verdict=PASS)
    p = harness.dir / "passing-with-refusals.json"
    p.write_text(json.dumps(passing), encoding="utf-8")
    assert not gate.decide([str(p)]).blocked, (
        "the gate read `scores` — the partition has started gating")

    zeroed = dict(verdict, scores=dict(verdict["scores"], refused=0, answered=0))
    z = harness.dir / "failing-without-refusals.json"
    z.write_text(json.dumps(zeroed), encoding="utf-8")
    assert gate.decide([str(z)]).blocked, "the verdict decides, not the counts"
