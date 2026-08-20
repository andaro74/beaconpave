"""
The deterministic half of the eval harness (ADR-012).

M00b scores the control with this; M03 adds the judge and re-scores the same
commit, appending a history entry that supersedes the deterministic-only one.

Two properties matter more than anything else here.

**It never calls a model.** Scoring is a pure function of (case, answer,
catalog). The model call lives in the baseline agent, which ADR-011 quarantines
as the only direct-model path in the repo. Keeping the runner model-free is what
lets it sit inside the hermetic suite (G8) and be proven correct against
committed fixtures before anything non-deterministic exists.

**It never reads the judge rubric.** `quality/judge/rubric-sports.md` exists and
the cases reference it; at M00b it is not consulted and judge axes are recorded
`ADVISORY`, never scored. A judge with no published agreement number cannot
produce a blocking score — that is G9, and it applies to the control exactly as
it applies to everything else.

Owning seat: AI Quality (scoring semantics) · Platform Engineering (mechanism).
"""
from __future__ import annotations

import json
import math
import pathlib
from dataclasses import dataclass, field

import jsonschema

#: Results a case can carry. Mirrors the enum in `evals/history/schema.json`.
#:
#: The FAIL/INFRA split is the same one `pave gate decide` makes, for the same
#: reason: "the service answered wrongly" and "the harness could not establish
#: whether it answered wrongly" page different people. Collapsing them is how a
#: flaky harness gets routed around instead of fixed.
PASS = "PASS"
FAIL = "FAIL"
ADVISORY = "ADVISORY"
INFRA = "INFRA"

#: Asserts recorded but NOT scored, and why each one cannot yet mean anything.
#:
#: `entitlement_source` joined this list after the m00b run (ADR-016). It reads a
#: field the model fills in, and the control claimed the `entitlement-check` tool
#: it does not have in 10 of the 11 cases asserting provenance — it finds the
#: enum in its own prompt. No stricter string fixes that: any value the assert
#: accepts is a value the model can emit. M06's trajectory eval can check whether
#: the tool was actually invoked; until then this measures candour.
#:
#: The cases keep the assert. It is the contract M06 must satisfy, so deleting it
#: would lose the requirement while scoring it credits a claim.
DEFERRED_ASSERTS = {
    "entitlement_source": "reads a self-report; verifiable only by M06's trajectory eval (ADR-016)",
}


@dataclass(frozen=True)
class AssertResult:
    kind: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class CaseResult:
    id: str
    result: str
    asserts: tuple[AssertResult, ...] = ()
    deferred: tuple[AssertResult, ...] = ()
    advisory_axes: tuple[str, ...] = ()
    unearned: bool = False
    unearned_reason: str = ""

    @property
    def failures(self) -> list[AssertResult]:
        return [a for a in self.asserts if not a.passed]


@dataclass
class Scorer:
    """Scores one service's golden set. `root` is the repo root; every path in a
    case is resolved against it, so the scorer has no notion of a current working
    directory and behaves the same from anywhere."""

    root: pathlib.Path
    _schemas: dict = field(default_factory=dict)

    # --- individual asserts ---------------------------------------------------
    #
    # Each returns an AssertResult. None of them raises on a badly shaped answer:
    # a missing field is an assertion failure, not a crash, because the control
    # is expected to produce badly shaped answers and the harness must score that
    # rather than die on it (SPEC/00b).

    def _schema(self, rel: str) -> dict:
        if rel not in self._schemas:
            self._schemas[rel] = json.loads((self.root / rel).read_text(encoding="utf-8"))
        return self._schemas[rel]

    def json_schema(self, answer: dict, rel: str) -> AssertResult:
        try:
            jsonschema.validate(answer, self._schema(rel))
        except jsonschema.ValidationError as exc:
            where = "/".join(str(p) for p in exc.absolute_path) or "<root>"
            return AssertResult("json_schema", False, f"{where}: {exc.message}")
        return AssertResult("json_schema", True)

    def must_mention(self, answer: dict, needle: str) -> AssertResult:
        prose = (answer.get("answer") or "").lower()
        ok = needle.lower() in prose
        return AssertResult("must_mention", ok, "" if ok else f"{needle!r} absent from answer")

    def must_not_claim(self, answer: dict, needle: str) -> AssertResult:
        prose = (answer.get("answer") or "").lower()
        ok = needle.lower() not in prose
        return AssertResult("must_not_claim", ok, "" if ok else f"{needle!r} present in answer")

    def must_cite(self, answer: dict, ids: list) -> AssertResult:
        cited = set(answer.get("cited_titles") or [])
        missing = sorted(set(ids) - cited)
        return AssertResult("must_cite", not missing, "" if not missing else f"not cited: {missing}")

    def cited_titles_in_fixture(self, answer: dict, catalog: dict, _v) -> AssertResult:
        """The groundedness check, deterministic on purpose. A cited id that is
        not in the catalog is a confabulation — no judge required, and this is
        the main place CLAUDE.md's preference for deterministic assertions pays."""
        known = {t["id"] for t in catalog.get("titles", [])}
        invented = sorted(set(answer.get("cited_titles") or []) - known)
        return AssertResult(
            "cited_titles_in_fixture", not invented,
            "" if not invented else f"cited ids absent from catalog (confabulated): {invented}",
        )

    def cites_at_least_one(self, answer: dict, _v) -> AssertResult:
        """The half of groundedness `cited_titles_in_fixture` cannot express.

        `cited_titles_in_fixture` computes `set(cited) - known`, which is
        **vacuously true on an empty citation list**: an answer that cites nothing
        confabulates nothing, so it passes a groundedness check by not attempting
        to be grounded. SPEC/02 pre-registered that for `grounded-019`; M02 then
        found the same shape hiding a real regression on `edge-025`, where the
        control cited `t001`, the tools arm cited nothing, and the paired diff
        recorded the case as *unchanged*.

        **This is additive on purpose.** `cited_titles_in_fixture` keeps its exact
        meaning — every cited id is real — because it is referenced by 25 cases and
        by recorded history, and an assert key whose meaning changes underneath a
        recorded score is ADR-016's hazard in its purest form. The missing
        requirement gets its own key instead, so each one means what its name says.

        Applied only where a citation is what grounding *means* for the case. Two
        cases ask about a subject the catalog does not contain, where citing
        nothing is the correct answer; they carry `cited_titles_empty` instead."""
        cited = answer.get("cited_titles") or []
        return AssertResult(
            "cites_at_least_one", bool(cited),
            "" if cited else "no title cited: an ungrounded answer passes "
                             "cited_titles_in_fixture vacuously",
        )

    def cited_titles_empty(self, answer: dict, _v) -> AssertResult:
        """The mirror, for a subject the catalog does not contain.

        `grounded-019` and `entitlement-012` both ask about the Harbor Bay
        Invitational, which is not in the catalog. The correct answer cites
        nothing — so requiring a citation would punish a right answer, and leaving
        `cited_titles_in_fixture` alone would credit a vacuous one.

        Stating it positively makes the same behaviour **falsifiable**: an answer
        that invents a citation for a title that does not exist now fails an assert
        that names exactly that failure, instead of passing one that could not
        detect it."""
        cited = answer.get("cited_titles") or []
        return AssertResult(
            "cited_titles_empty", not cited,
            "" if not cited else
            f"cited {sorted(cited)} for a subject absent from the catalog",
        )

    def entitlement(self, answer: dict, expected: dict) -> AssertResult:
        got = answer.get("entitlement")
        if not isinstance(got, dict):
            return AssertResult("entitlement", False, "answer carries no entitlement verdict")
        diffs = [
            f"{k}={got.get(k)!r} (expected {v!r})"
            for k, v in expected.items()
            if got.get(k) != v
        ]
        return AssertResult("entitlement", not diffs, "; ".join(diffs))

    def entitlement_source(self, answer: dict, expected: str) -> AssertResult:
        """Evaluated for the record; **not scored** until M06 (ADR-016).

        This reverses the call made when the runner was written, and the earlier
        reasoning is worth keeping because it was sound and still wrong. It ran:
        `expect_tool_before_answer` is unscorable because it names a tool that
        does not exist, whereas this assert is evaluable, so the control's
        constant FAIL is the gap M06 closes and skipping it would flatter the
        control.

        The premise was that the control would emit `model-inference`. It did
        not. It read the enum out of the schema in its own prompt and claimed
        `entitlement-check` in 10 of the 11 cases — turning the expected constant
        FAIL into an unearned PASS, the opposite error. An assert reading a
        self-report measures candour, and no stricter string helps: every value
        it accepts is one the model can emit.

        Scoring it is what exposed that, which is why the assert stays in the
        cases and keeps being evaluated here. Only its contribution to the score
        is withheld, until M06 can check whether the tool was really called."""
        got = (answer.get("entitlement") or {}).get("source")
        ok = got == expected
        return AssertResult(
            "entitlement_source", ok,
            "" if ok else f"verdict came from {got!r}, not {expected!r}",
        )

    def budget(self, usage: dict, ceiling: dict) -> AssertResult:
        """Token-denominated (ADR-014). Dollars are rendered at report time and
        never block, because a vendor price change must not move a verdict.

        Latency here is `max_ms`, a hang guard — not a performance target. The
        per-case `p95_ms` it replaced was a category error: a p95 cannot be
        computed from one sample, and asserting it per case turned the tail it
        explicitly permits into a failure (ADR-016). The distributional statistic
        now lives at suite level, in `suite_latency`."""
        over = []
        for key in ("tokens_in", "tokens_out"):
            limit, got = ceiling.get(key), usage.get(key)
            if limit is not None and got is not None and got > limit:
                over.append(f"{key}={got} over {limit}")
        limit_ms, got_ms = ceiling.get("max_ms"), usage.get("latency_ms")
        if limit_ms is not None and got_ms is not None and got_ms > limit_ms:
            over.append(f"latency_ms={got_ms} over max_ms {limit_ms} (stalled request)")
        return AssertResult("budget", not over, "; ".join(over))

    # --- case ------------------------------------------------------------------

    def score_case(self, case: dict, record: dict | None, catalog: dict) -> CaseResult:
        """Score one golden case against one recorded answer.

        `record` is `{"answer": {...}, "usage": {...}}`, or None when the agent
        produced nothing for this case. A missing or unparseable answer is INFRA,
        never a silent skip and never a FAIL: the harness could not establish
        anything, which pages the platform rather than the service team. Absence
        must block — the same contract `pave gate decide` enforces on verdicts."""
        advisory = tuple(case.get("judge", {}).get("axes", ()))

        # `advisory_axes=` by keyword, not positionally. Both INFRA returns passed
        # `advisory` - a tuple of axis-name STRINGS - into the fourth field, which is
        # `deferred` and holds `AssertResult`s. Any caller reading `.kind` off a
        # deferred entry then raises AttributeError, so a suite carrying both an
        # INFRA case and a deferred assert crashed instead of reporting INFRA.
        # `entitlement_source` is deferred on 11 of the 25 golden cases, so the
        # second condition is almost always true; it survived because no committed
        # run has ever had a missing answer.
        #
        # Neither field is scored, so no recorded number moves. Found by a test
        # written to drive the judge veto through the real runner rather than
        # reimplementing it.
        if record is None:
            return CaseResult(case["id"], INFRA, (), advisory_axes=advisory)
        answer = record.get("answer")
        if not isinstance(answer, dict):
            return CaseResult(
                case["id"], INFRA,
                (AssertResult("answer", False, "no answer object recorded"),),
                advisory_axes=advisory,
            )

        usage = record.get("usage") or {}
        results: list[AssertResult] = []
        deferred: list[AssertResult] = []
        for assertion in case.get("asserts", []):
            for key, value in assertion.items():
                if key == "json_schema":
                    results.append(self.json_schema(answer, value))
                elif key == "must_mention":
                    results.append(self.must_mention(answer, value))
                elif key == "must_not_claim":
                    results.append(self.must_not_claim(answer, value))
                elif key == "must_cite":
                    results.append(self.must_cite(answer, value))
                elif key == "cited_titles_in_fixture":
                    results.append(self.cited_titles_in_fixture(answer, catalog, value))
                elif key == "cites_at_least_one":
                    results.append(self.cites_at_least_one(answer, value))
                elif key == "cited_titles_empty":
                    results.append(self.cited_titles_empty(answer, value))
                elif key == "entitlement":
                    results.append(self.entitlement(answer, value))
                elif key == "entitlement_source":
                    # Evaluated for the record, kept out of the score (ADR-016).
                    deferred.append(self.entitlement_source(answer, value))
                elif key == "budget":
                    if not usage:
                        # An unmeasured budget is not a passed budget. Treating a
                        # missing measurement as satisfied is how a suite reports
                        # green over something it never checked.
                        return CaseResult(
                            case["id"], INFRA,
                            tuple(results) + (AssertResult("budget", False, "no usage recorded"),),
                            advisory,
                        )
                    results.append(self.budget(usage, value))
                else:
                    # Unreachable while `test_no_case_uses_an_undocumented_assert`
                    # holds. INFRA rather than a skip, so a vocabulary drift can
                    # never present as a pass.
                    return CaseResult(
                        case["id"], INFRA,
                        tuple(results) + (AssertResult(key, False, "unknown assert"),),
                        advisory,
                    )

        failed = [r for r in results if not r.passed]
        return CaseResult(
            case["id"], FAIL if failed else PASS, tuple(results), tuple(deferred), advisory)

    def score_suite(self, cases: list, answers: dict, catalog: dict) -> list[CaseResult]:
        return [self.score_case(c, answers.get(c["id"]), catalog) for c in cases]


def suite_latency(answers: dict, ceiling_ms: int | None) -> AssertResult:
    """The distributional half of the latency budget (ADR-016).

    p95 belongs to a population of requests, not to one request. Compared here
    against the service manifest's `gates.budgets.p95_ms`, which is what that
    field always meant — and which the per-case ceilings quietly contradicted by
    treating the permitted 5% tail as 25 separate failures.

    Nearest-rank on the samples actually collected; with 25 cases the 95th
    percentile is one of the two slowest, so this is a coarse estimate and should
    be read as one. It is still a truer statement than comparing a p95 to n=1."""
    samples = sorted(
        a["usage"]["latency_ms"] for a in answers.values()
        if isinstance(a, dict) and (a.get("usage") or {}).get("latency_ms") is not None
    )
    if not samples:
        return AssertResult("suite_p95_ms", False, "no latency measurements recorded")
    # Nearest-rank: ceil(0.95 * n), 1-indexed. `int()` here is an off-by-one that
    # only shows when 0.95*n lands on a whole number — at n=20 it returns the
    # maximum and calls one slow request in twenty a p95 breach, which is the
    # exact confusion of tail-for-defect this ADR exists to remove.
    p95 = samples[max(0, math.ceil(0.95 * len(samples)) - 1)]
    if ceiling_ms is None:
        return AssertResult("suite_p95_ms", True, f"p95={p95}ms (no manifest ceiling)")
    ok = p95 <= ceiling_ms
    return AssertResult(
        "suite_p95_ms", ok,
        f"p95={p95}ms over {ceiling_ms}ms" if not ok
        else f"p95={p95}ms within {ceiling_ms}ms (n={len(samples)})",
    )


def tally(results: list[CaseResult]) -> dict:
    """Scores for the history entry. Plain counts plus a rate — `scores` in the
    history schema is `{string: number}`, so nothing structured belongs here."""
    total = len(results)
    passed = sum(1 for r in results if r.result == PASS)
    return {
        "total": total,
        "passed": passed,
        "failed": sum(1 for r in results if r.result == FAIL),
        "infra": sum(1 for r in results if r.result == INFRA),
        "pass_rate": round(passed / total, 4) if total else 0.0,
    }
