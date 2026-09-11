"""
The prompt delta, priced before a single call is spent.

M09's fix is one sentence in `TOOL_SYSTEM`, and `TOOL_SYSTEM` is in **every
request of every run this milestone takes**. That is the one way this milestone
can break M08b's standing per-sample claim that `tokens_in` holds at 7700, and it
is measurable with **no model call**, because the prompt is committed.

**What was wrong with the bound the spec shipped, and it is arithmetic rather
than a preference.** SPEC/09 as written asserted `6782 + delta < 7700` and called
the headroom 918 tokens. `usage.tokens_in` is the **sum across calls** — checked
below on all 70 answered M08b samples, total equals the sum of
`usage.calls[].tokens_in` in 70 of 70 — and 6782 is `headroom-005` sample 3 at
**three** calls. The system block is re-sent every round, so a delta of *d*
tokens lands *n* times in an *n*-call sample. The spec's form therefore compares
a per-sample total against a per-call delta and admits **delta ≤ 917**, where the
claim can survive **delta ≤ 306**. A 400-token disclosure sentence — a plausible
size for one that must say what to write and when — passes the spec's test, puts
`headroom-005` at **7982**, and falsifies F4 on the run the test exists to
protect.

That is a stated protection that is absent, which CLAUDE.md ranks worse than a
missing one because it stops anyone looking for the real one (ADR-075 amendment 1
fact 2, ask 2).

**The corrected bound reads the population, not the sentence about it.**
`max(tokens_in + delta × len(calls)) ≤ 7700` over M08b's answered ≤3-call
samples, computed from the committed answer files rather than from the single
published maximum.

**Why `<=` and not `<`.** `evals/deterministic.py::budget` compares `got > limit`,
so a sample landing exactly on 7700 passes. The boundary is asserted in both
directions below rather than assumed, because a bound that is off by one at the
edge is a bound nobody can use to price a fix.

**What this measures, and what it does not.** It measures **budget**: whether the
fix breaches a ceiling. Nothing hermetic can measure a prompt's effect on
*content*, and this test does not pretend to (ADR-075 amendment 1 §5). The
hermetic content guard on this fix is the line-by-line assert in
`tests/test_gateway_run_parity.py`, which names what the prompt gained; the
measured content guards are F4's two direction falsifiers, and they cost a model
call and are read at PR 4.

Zero model calls, hermetic (G8): committed answer files and committed prompt text.

Owning seats: AI Quality (the ceiling) · Platform Engineering (the loop) ·
Security (what a recorded number means).
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

from evals.deterministic import Scorer

ROOT = pathlib.Path(__file__).resolve().parents[1]
CENSUS_READER = ROOT / "milestones" / "M08" / "context_census.py"
RUNS = [ROOT / "milestones" / "M08b" / f"goldens-run-{n}.json" for n in (1, 2, 3)]

#: ADR-014's `tokens_in` ceiling, proven per sample on fresh samples at M08b. It
#: does not move in this milestone: SPEC/09 constraint 1, and *What must not
#: happen* — "if the prompt delta does not fit the headroom, the **fix** is
#: rewritten", never the ceiling.
CEILING = 7700

#: The call count above which a sample is outside the claim. M08b's claim is
#: "every answered sample at three calls or fewer under the ceiling"; the ≥4-call
#: samples are over it by design and are not what the fix must fit inside.
#:
#: **Not called "mandated".** `tests/test_m09_p95_condition.py::_population`
#: selects `calls == mandated` — the census's PER-CASE mandate, 2 or 3 — and this
#: file selects `calls <= 3`. n = 38 and n = 58 over the same run. Both were
#: called "the mandated shape" in prose, in one milestone, which the AI Quality
#: seat raised in round 1 and restated as still open in round 2; the first fix
#: reworded the comment and left the name. One of the two had to be renamed and
#: this is the one, because the p95 file's word is the census's own.
AT_MOST_THREE_CALLS = 3


@pytest.fixture(scope="module")
def census():
    """The census reader, imported the way `tests/test_m08_census.py` imports it.

    **This inserts two tool paths into `sys.path` for the whole session** — the
    reader does it at import time, and it is a standing Platform Engineering debt
    (SPEC/09's obligations table). It is not *this* file's exposure: importing the
    census is what `tests/test_m08_census.py` has done since M08 PR 3, so nothing
    new leaks. The debt is dated *"the next PR that opens the file"*, and PR 2
    opens it read-only; paying it would edit a file under `milestones/M08/`, which
    this milestone's Definition of done forbids and which the p95 condition — not
    firing — gives no other reason to touch."""
    spec = importlib.util.spec_from_file_location("context_census", CENSUS_READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["context_census"] = module
    spec.loader.exec_module(module)
    return module


def _samples() -> list[dict]:
    """Every sample of M08b's fresh run, from the committed answer files.

    Read from the ANSWER FILES, never from `fresh-join.json` and never from a
    journal sentence. The derived record would do for the numbers, and reading it
    would make this test agree with that record by construction rather than with
    the run — the compression error this repository has paid for repeatedly
    (ADR-075 amendment 1's opening rule: every number produced by running
    committed code over committed evidence)."""
    rows = []
    for n, path in enumerate(RUNS, 1):
        for case_id, record in json.loads(path.read_text(encoding="utf-8")).items():
            usage = (record or {}).get("usage") or {}
            calls = usage.get("calls") or []
            rows.append({
                "id": f"{case_id} s{n}",
                "tokens_in": usage.get("tokens_in") or 0,
                "calls": len(calls),
                "per_call": [c.get("tokens_in", 0) for c in calls],
            })
    return rows


def answered_within_mandate() -> list[dict]:
    """The population the bound is computed over: answered, ≤3 calls.

    `tokens_in > 0` is the census's own definition of answered — the harness
    writes `tokens_in: 0` for a refused sample, and averaging one in would
    understate every statistic."""
    return [r for r in _samples()
            if r["tokens_in"] > 0 and r["calls"] <= AT_MOST_THREE_CALLS]


def worst_case(delta: int, population: list[dict] | None = None) -> tuple[int, str]:
    """The largest `tokens_in` any sample would carry if the prompt grew by
    `delta` tokens per call, and which sample carries it."""
    rows = population if population is not None else answered_within_mandate()
    worst = max(rows, key=lambda r: r["tokens_in"] + delta * r["calls"])
    return worst["tokens_in"] + delta * worst["calls"], worst["id"]


def admissible_delta(population: list[dict] | None = None) -> int:
    """The largest per-call prompt delta the 7700 claim survives.

    Solved rather than searched: for each sample the delta it admits is
    `(CEILING - tokens_in) // calls`, and the population's bound is the smallest
    of those. A search over a range would have a range to get wrong."""
    rows = population if population is not None else answered_within_mandate()
    return min((CEILING - r["tokens_in"]) // r["calls"] for r in rows)


#: The bound, pinned. Moving it is moving what this milestone may spend on its
#: fix, and the number is derived from committed evidence — a diff that changes
#: it without changing the evidence is the finding.
ADMISSIBLE_DELTA = 306

#: The rendered tool prompt's token estimate BEFORE the fix, by the census's own
#: estimator, over the tree PR 2 merges.
#:
#: **This constant is not updated when the fix lands.** It is the baseline the
#: delta is measured against, and re-seating it in the PR that moves the prompt
#: would erase the measurement — the same move as re-pinning a comparator in the
#: diff that moved it, which `evals/comparators.json` refuses in as many words.
#: PR 4 leaves it alone and watches `test_the_committed_prompts_delta_fits` price
#: the fix.
PRE_FIX_RENDERED_TOKENS_EST = 1409
#
# **Re-seated once, in round 1, and the distinction is the whole point.** It was
# 793 — the system block alone. The Tool Owner seat measured that the routed tool
# specs are another ~616 tokens re-sent on every call, so 44% of the per-call
# surface was unpriced and `ADMISSIBLE_DELTA` was spendable twice. What changed
# here is the DEFINITION of the surface being priced, in a PR where no
# model-facing byte moved: the three digests below are unchanged from the tree
# this baseline was first taken on, which is exactly what distinguishes a widened
# measurement from the re-seat this constant exists to forbid. When the text
# moves, the digests move, and that is when re-seating is the erasure.

#: **What 793 is the estimate OF, so the number cannot be re-seated in silence.**
#:
#: The comment above says the baseline is not updated when the fix lands. Nothing
#: enforced that: the AI Quality seat added a real 135-token disclosure sentence
#: to `TOOL_SYSTEM`, re-seated 793 -> 928 and moved `TOOL_SYSTEM_SHA256`, and this
#: file passed **9 of 9** with `delta == 0` and the bound vacuous. The only reds
#: came from record digests PR 4 legitimately re-produces, so at that moment the
#: re-seat is completely silent — in the one PR the baseline exists to police.
#:
#: A number pinned to a literal can be moved by editing the literal. These pin it
#: to the TEXT, so re-seating requires stating which bytes it is no longer the
#: baseline for, and `test_the_baseline_is_the_estimate_of_the_text_it_names`
#: refuses a baseline whose text has moved.
PRE_FIX_TOOL_SYSTEM_SHA256 = "c5e0e50584613dbfa75b0dc991fda55e075709dfb07fd3c5f38db8e0a6818e38"
PRE_FIX_ANSWER_SCHEMA_SHA256 = "d4219cc724c5c17e94693d99992637de9c8f987e58632239ca2bbfccd0baa155"
#: The routed tool specs, digested as the payload the gateway serialises. A
#: reworded tool `description` is model-facing text on every call and moves
#: this; `TOOL_SPECS_SHA256` in `tests/test_gateway_run_parity.py` catches the
#: move, and this is what prices it.
PRE_FIX_TOOL_SPECS_SHA256 = "40152facb40524ae1d3a4d83d5dab8c785db036b47f72a434a20dfd77d272a34"

#: The estimator's denominator, pinned beside the numerator it divides.
#:
#: `calibration()` divides the chars of six ADR-014 anchor CASES by their measured
#: token counts, so the golden cases file — `(ai-quality)`, one key — moves this
#: ratio. Measured: padding the six anchor inputs by ~213 chars each, with no
#: prompt change at all, moved the rendered estimate 793 -> 752, a phantom -41.
#: It is red today only because the live assertion is `delta == 0`; the moment PR
#: 4 replaces that with the bound, a calibration shift mis-prices the fix in
#: either direction with nothing to say so.
PRE_FIX_CHARS_PER_TOKEN = 3.373


def routed_tools() -> tuple:
    """The tools the gateway routes, read from the committed synth snapshot.

    **This was a hand-written tuple under a comment claiming it was derived** —
    *"Read from the committed history entry rather than named here, so a routed
    tool added later is priced without this file being edited"* — which is the
    stated-and-absent shape, in the file whose whole subject is a bound that does
    not bound. `PRE_FIX_TOOL_SPECS_SHA256` could not catch the staleness either,
    because the digest is computed OVER the list.

    Measured by the Tool Owner seat: routing `publish-highlight` adds **422
    estimated tokens**, larger than `ADMISSIBLE_DELTA` on its own and entirely
    unpriced. `pave.infra.routed_tools` reads the snapshot ADR-017 already
    drift-gates against a re-synthesis, so the deployment is the authority."""
    from pave import infra
    snapshot = ROOT / "platform" / "infra" / "cdk.out" / "BeaconpaveGateway.template.json"
    return tuple(sorted(infra.routed_tools(json.loads(snapshot.read_text(encoding="utf-8")))))


def rendered_per_call_payload(census) -> str:
    """**Everything the model receives on every call**, not just the system block.

    `TOOL_SYSTEM.format(schema=answer.schema.json)` is the system block, and both
    sites M09 *plans* to edit are inside it. That is not the same as the
    model-facing surface, and the first version of this function claimed it was:
    *"Both of M09's model-facing sites are inside this string."* True of the plan,
    read as a claim about what is priced, and it is not one.

    `handler.tool_config` also hands Bedrock each routed tool's `description` and
    full `inputSchema`, **re-sent on every call of every turn** — so a delta there
    multiplies by the call count exactly as the system block does, which is the
    entire correction this file exists to make. Measured by the Tool Owner seat:
    the routed `toolConfig` is ~618 tokens against 793 for the system block, so
    **44% of the per-call surface was unpriced**, and `ADMISSIBLE_DELTA` was
    spendable twice — 1054 characters of prose added to a routed tool's
    description left this file at **9 passed**.

    The digest pins do fire on such a change, but a digest answers *did it move*,
    not *how much did it cost*, and ADR-058 has the PR that moves them re-pin
    them. Once re-pinned, nothing priced the growth."""
    template = ROOT / "services" / "highlights-agent" / "gateway_client.py"
    schema = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"
    import ast as _ast
    import json as _json
    tree = _ast.parse(template.read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, _ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], _ast.Name)
                and node.targets[0].id == "TOOL_SYSTEM"
                and isinstance(node.value, _ast.Constant)):
            system = node.value.value.format(schema=schema.read_text(encoding="utf-8"))
            # The tool specs, rebuilt exactly as `handler.tool_config` builds them
            # — the census already reproduces those six lines and its own test
            # pins the shape, so this reads the reproduction rather than making a
            # third copy.
            specs = _json.dumps(census.tool_config(routed_tools()), ensure_ascii=False,
                                sort_keys=True)
            return system + "\n" + specs
    raise AssertionError("gateway_client.py defines no string constant TOOL_SYSTEM")


def estimate_tokens(text: str, census=None) -> int:
    """`round(chars / PRE_FIX_CHARS_PER_TOKEN)` — the census's arithmetic, over a
    FROZEN ratio.

    **The ratio may not be recomputed while pricing the fix, and that is a
    measured defect rather than a preference** (AI Quality, round 2).
    `context_census.calibration()` divides the chars of ADR-014's six anchor
    prompts by token counts frozen on 2026-08-15 — and `control_prompt()`
    renders `answer.schema.json`, which is one of the two sites the fix edits.
    So growing the schema grows the ratio's numerator while its denominator is a
    constant, and the estimate stops being a function of size:

    | chars added to `answer.schema.json` | chars/token | estimate |
    |---|---|---|
    | 0 | 3.3730 | 793 |
    | 370 | 3.6875 | 826 |
    | 4 000 | 6.7915 | 983 |
    | 20 000 | 20.4550 | 1109 |

    A 20 000-character schema addition prices at **+316 tokens** against a true
    cost of roughly +5 900. `ADMISSIBLE_DELTA = 306` is arithmetically right and
    would gate nothing: the larger the fix, the cheaper the instrument reports it.
    (The seat that found this attributed it to `TOOL_SYSTEM`, where the ratio does
    NOT move — `control_prompt` renders `SYSTEM` — and read the estimate as
    falling. It rises; it just rises far too slowly. The mechanism is real and the
    site is the schema.)

    Freezing the ratio makes the estimate monotone in size, which is the only
    property a budget bound needs. `test_the_estimators_denominator_is_pinned_beside_the_numerator`
    still recomputes the live ratio and asserts it equals this constant, so an
    ADR-014 anchor edit is a named failure rather than a silently re-priced fix.
    """
    return round(len(text) / PRE_FIX_CHARS_PER_TOKEN)


# --- the population -----------------------------------------------------------

def test_the_population_is_m08bs_answered_three_call_samples():
    """n = 58, and the two counts that make the bound mean anything."""
    rows = answered_within_mandate()
    answered = [r for r in _samples() if r["tokens_in"] > 0]
    assert len(answered) == 70, f"{len(answered)} answered samples, not the 70 M08b recorded"
    assert len(rows) == 58, f"{len(rows)} samples at ≤3 calls, not 58"
    assert len([r for r in answered if r["calls"] >= 4]) == 12


def test_tokens_in_is_the_sum_across_calls_and_this_is_why_the_delta_multiplies():
    """The fact the corrected bound rests on, measured rather than asserted.

    If `usage.tokens_in` were a per-call figure the spec's `6782 + delta` would be
    right. It is a per-sample total: 70 of 70 answered samples have
    `tokens_in == sum(calls[].tokens_in)`. The system block is inside every one of
    those calls, so a delta of *d* lands `len(calls)` times."""
    answered = [r for r in _samples() if r["tokens_in"] > 0]
    agreeing = [r for r in answered if sum(r["per_call"]) == r["tokens_in"]]
    assert len(agreeing) == len(answered) == 70, (
        f"{len(agreeing)} of {len(answered)} samples have tokens_in equal to the sum over "
        "calls. The corrected bound multiplies the delta by the call count because of "
        "this fact; if it no longer holds, the bound is wrong and not the evidence.")


def test_the_published_maximum_is_a_three_call_sample():
    """6782 is `headroom-005` sample 3 at **three** calls, not one.

    This is the whole of the spec's error in one row: the number it treated as a
    per-call budget is a three-call total."""
    rows = answered_within_mandate()
    worst = max(rows, key=lambda r: r["tokens_in"])
    assert worst["tokens_in"] == 6782, f"the ≤3-call maximum is {worst['tokens_in']}, not 6782"
    assert worst["id"] == "headroom-005 s3", worst["id"]
    assert worst["calls"] == 3, f"the published maximum is at {worst['calls']} call(s)"


# --- the bound ----------------------------------------------------------------

def test_the_admissible_delta_is_the_population_form_not_the_published_maximum():
    """**306, not 917.** The correction, stated as the two numbers it lies
    between."""
    assert admissible_delta() == ADMISSIBLE_DELTA, (
        f"the population admits {admissible_delta()} tokens per call, not "
        f"{ADMISSIBLE_DELTA}. This number is the fix's budget; if the evidence moved, "
        "say which run moved and re-derive — never raise it to fit a fix.")
    spec_form = CEILING - 6782 - 1
    assert spec_form == 917 and spec_form > ADMISSIBLE_DELTA * 2, (
        "the bound SPEC/09 shipped admits three times the delta the claim can survive; "
        "that ratio is the reason the form was corrected and is asserted so the old "
        "form cannot quietly return.")


def test_the_worst_case_table_at_the_boundary_and_over_it():
    """Computed, both sides of 7700, including the exact boundary.

    `evals/deterministic.py::budget` compares `got > limit`, so 7700 exactly is a
    PASS. 307 is the first delta that is not."""
    assert worst_case(300) == (7682, "headroom-005 s3")
    assert worst_case(306) == (7700, "headroom-005 s3")
    assert worst_case(307) == (7703, "headroom-005 s3")
    assert worst_case(400) == (7982, "headroom-005 s3")
    assert worst_case(917) == (9533, "headroom-005 s3")
    assert worst_case(ADMISSIBLE_DELTA)[0] <= CEILING < worst_case(ADMISSIBLE_DELTA + 1)[0]


def test_a_four_hundred_token_fix_passes_the_specs_bound_and_falsifies_f4():
    """The concrete event the corrected test exists to prevent before a call.

    A 400-token sentence clears `6782 + delta < 7700` and puts `headroom-005` at
    7982 — a ≤3-call answered sample over 7700 that was under it at M08b, which
    is F4's first clause word for word."""
    delta = 400
    assert 6782 + delta < CEILING, "the spec's bound admits it"
    over, who = worst_case(delta)
    assert over > CEILING and who == "headroom-005 s3", (
        "and the run it was written to protect goes over the ceiling on that sample")


def test_the_bound_is_the_minimum_over_the_population_not_over_one_sample():
    """A sample with more calls can bind tighter than one with a bigger total,
    and a bound taken from the single largest total would not see it.

    **The plant discriminates, and the first version did not.** It planted one
    sample at 7690 over two calls — which is *also* the largest total — so a
    mutation replacing the population minimum with `max(rows, key=tokens_in)`
    returned the same answer and the mutation was SILENT. A plant that the
    defect passes measures nothing, which is this repository's own *verify the
    plant before the count*.

    So the two planted samples pull apart: **A** carries the largest total and
    the loosest bound (7000 over one call → 700), **B** a smaller total and the
    tightest (6900 over three calls → 266). The population's answer is 266; a
    reader taking the largest total answers 700."""
    loosest = {"id": "planted A", "tokens_in": 7000, "calls": 1, "per_call": [7000]}
    tightest = {"id": "planted B", "tokens_in": 6900, "calls": 3, "per_call": [2300] * 3}
    planted = answered_within_mandate() + [loosest, tightest]

    assert max(planted, key=lambda r: r["tokens_in"]) is loosest, (
        "the plant no longer discriminates: the tightest-binding sample is also the "
        "largest, so a bound read off the largest total would give the right answer "
        "for the wrong reason")
    assert admissible_delta([loosest]) == 700 and admissible_delta([tightest]) == 266
    assert admissible_delta(planted) == 266, (
        "the bound did not follow the tighter sample down — it is reading one sample "
        "rather than the population, which is the defect it was written to correct")


def test_the_boundary_is_the_scorers_and_not_this_files_arithmetic():
    """**Why `≤ 7700` and not `< 7700`, tied to the comparator that decides it.**

    `evals/deterministic.py::budget` compares `got > limit`, so a sample landing
    exactly on the ceiling PASSES, and the admissible delta is the one that
    reaches 7700 rather than the one that stops below it. Asserted against the
    scorer rather than restated here: a bound whose edge is justified by a
    sentence in its own file can drift from the thing it is a bound for, and the
    delta-0 committed prompt is nowhere near the edge, so nothing else in this
    file exercises the choice today. It starts biting at the fix's PR."""
    scorer = Scorer(root=ROOT)
    limits = {"model": "haiku", "tokens_in": CEILING, "tokens_out": 100_000, "max_ms": 100_000}
    at = scorer.budget({"tokens_in": CEILING, "tokens_out": 1, "latency_ms": 1}, limits)
    over = scorer.budget({"tokens_in": CEILING + 1, "tokens_out": 1, "latency_ms": 1}, limits)
    assert at.passed, (
        f"a sample at exactly {CEILING} now fails the scorer's budget assert, so the "
        "admissible delta is one token too generous — re-derive it against `got > limit`")
    assert not over.passed
    assert worst_case(ADMISSIBLE_DELTA)[0] == CEILING


# --- the committed prompt -----------------------------------------------------

def test_the_baseline_is_the_estimate_of_the_text_it_names(census):
    """**The baseline is pinned to its evidence, not to a literal.**

    Re-seating `PRE_FIX_RENDERED_TOKENS_EST` was measured silent: change the
    prompt, change the number, move the sha pin, and this file passed 9 of 9 with
    the bound vacuous. So the baseline now names the two blobs it is the estimate
    of, and moving the prompt without confronting that is red HERE — in the file
    whose whole job is to price the move — rather than only in record digests the
    fix's PR re-produces anyway.

    When PR 4 lands the fix, these two digests are what it must consciously
    change, and the reviewer sees a baseline being detached from its subject
    rather than a number quietly becoming a different number."""
    import hashlib

    def digest(text: str) -> str:
        return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()

    constants = census.client_constants()
    assert digest(constants["TOOL_SYSTEM"]) == PRE_FIX_TOOL_SYSTEM_SHA256, (
        "`TOOL_SYSTEM` has moved, so PRE_FIX_RENDERED_TOKENS_EST is no longer the "
        "estimate of the text it names. If this is the fix's PR: do NOT re-seat the "
        "baseline — record the delta, and detach these pins deliberately with the "
        "reason, which is the ADR-021 event `TOOL_SYSTEM_SHA256`'s docstring describes.")
    schema = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"
    assert digest(schema.read_text(encoding="utf-8")) == PRE_FIX_ANSWER_SCHEMA_SHA256, (
        "`answer.schema.json` has moved. It is rendered into the prompt through "
        "`{schema}`, so it is part of the delta and part of this baseline.")

    import json as _json
    specs = _json.dumps(census.tool_config(routed_tools()), ensure_ascii=False, sort_keys=True)
    assert digest(specs) == PRE_FIX_TOOL_SPECS_SHA256, (
        "the routed tool specs have moved. Their `description` and `inputSchema` are "
        "handed to the model on every call, so a reworded description is a per-call "
        "delta exactly as a prompt sentence is — that is the surface round 1 found "
        "unpriced, and it is inside this baseline now.")


def test_the_estimators_denominator_is_pinned_beside_the_numerator(census):
    """The calibration ratio is editable from a one-key data file.

    `calibration()` divides the chars of six ADR-014 anchor CASES by their
    measured token counts, and the golden cases file takes AI Quality's key
    alone. Padding those six inputs — no prompt change — moved the rendered
    estimate 793 → 752. A denominator that can move without the numerator moving
    prices the fix wrongly in whichever direction the edit happened to go."""
    import yaml as _yaml
    cases_path = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
    cases = {c["id"]: c for c in _yaml.safe_load(cases_path.read_text(encoding="utf-8"))}
    cal = census.calibration(census.client_constants(), cases)
    assert cal["chars_per_token"]["median"] == PRE_FIX_CHARS_PER_TOKEN, (
        f"the estimator's chars-per-token median is {cal['chars_per_token']['median']}, "
        f"pinned at {PRE_FIX_CHARS_PER_TOKEN}. Every token estimate in this file divides "
        "by it, so a move here re-prices the fix with no prompt change at all — check "
        "whether an ADR-014 anchor case was edited.")


def test_the_estimate_is_monotone_in_the_size_of_the_fix():
    """**The property a budget bound needs, and the one the live estimator lacked.**

    A bigger fix must price as more. With the ratio recomputed at read time it did
    not: `control_prompt()` renders `answer.schema.json`, which is one of the two
    sites the fix edits, so growing the schema grew the ratio and a 20 000-char
    addition priced at +316 tokens against a true cost near +5 900.

    Swept rather than argued, because the failure was in the shape of the function
    and not in one value."""
    base = "x" * 2675
    previous = estimate_tokens(base)

    # Non-decreasing at EVERY step, including steps smaller than one token. The
    # first version of this asserted a strict increase at one character and went
    # red on its own arithmetic: `round(1/3.373)` is 0, so a rounded estimator is
    # monotone non-decreasing, not strictly increasing. The property a bound needs
    # is that growth never prices as shrinkage.
    for extra in (1, 2, 3, 10, 370, 1000, 4000, 20000):
        grown = estimate_tokens(base + "y" * extra)
        assert grown >= previous, (
            f"adding {extra} characters DECREASED the estimate ({previous} -> {grown}). "
            "A bound whose instrument is not a function of size gates nothing, however "
            "correct its arithmetic.")
        previous = grown

    # And strictly increasing once the step exceeds the ratio, which is what makes
    # a real fix priceable rather than merely not mis-priced.
    for extra in (4, 100, 370, 4000):
        assert estimate_tokens(base + "y" * extra) > estimate_tokens(base), extra
    assert estimate_tokens("z" * 3373) - estimate_tokens("") == 1000


def test_the_committed_prompts_delta_fits(census):
    """**The assert PR 4 re-runs after the fix lands.**

    Today the delta is zero: PR 2 moves no model-facing text, which SPEC/09
    constraint 2 requires of every PR but the one carrying the fix. When PR 4
    adds the disclosure sentence to `TOOL_SYSTEM` — and rewrites
    `answer.schema.json`'s `ai_disclosure` description, the other model-facing
    site — this recomputes and refuses a fix that does not fit, with no model
    call spent.

    The baseline constant is **not** re-seated by that PR. Re-seating it there
    would erase the measurement."""
    estimated = estimate_tokens(rendered_per_call_payload(census))
    delta = estimated - PRE_FIX_RENDERED_TOKENS_EST
    assert delta == 0, (
        f"the rendered tool prompt now estimates {estimated} tokens against a pre-fix "
        f"baseline of {PRE_FIX_RENDERED_TOKENS_EST}, a delta of {delta}. If this is PR 2, "
        "model-facing text moved in a PR that may not move it (SPEC/09 constraint 2). If "
        "this is the fix's PR, replace this assertion with the bound below and record the "
        "delta in the PR body — do not re-seat the baseline.")
    over, who = worst_case(delta)
    assert delta <= ADMISSIBLE_DELTA and over <= CEILING, (
        f"a per-call delta of {delta} puts {who} at {over}, over the {CEILING} ceiling. "
        f"The admissible delta is {ADMISSIBLE_DELTA}. The ceiling does not move for a fix "
        "(SPEC/09 constraint 1): the FIX is rewritten.")
