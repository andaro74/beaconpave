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
        """Scored, not skipped, and the distinction is deliberate.

        `expect_tool_before_answer` is skipped before M06 because it names a tool
        that does not exist — the question is malformed, and a constant green
        would be meaningless. This assert is different: the answer schema has a
        `source` field, the control fills it with `model-inference`, and the
        check evaluates correctly and fails. That constant FAIL is exactly the
        gap M06 closes, so recording it is what makes the improvement visible.
        Skipping it would flatter the control."""
        got = (answer.get("entitlement") or {}).get("source")
        ok = got == expected
        return AssertResult(
            "entitlement_source", ok,
            "" if ok else f"verdict came from {got!r}, not {expected!r}",
        )

    def budget(self, usage: dict, ceiling: dict) -> AssertResult:
        """Token-denominated (ADR-014). Dollars are rendered at report time and
        never block, because a vendor price change must not move a verdict."""
        over = []
        for key, measured_key in (("tokens_in", "tokens_in"), ("tokens_out", "tokens_out")):
            limit = ceiling.get(key)
            got = usage.get(measured_key)
            if limit is not None and got is not None and got > limit:
                over.append(f"{key}={got} over {limit}")
        limit_ms, got_ms = ceiling.get("p95_ms"), usage.get("latency_ms")
        if limit_ms is not None and got_ms is not None and got_ms > limit_ms:
            over.append(f"latency_ms={got_ms} over {limit_ms}")
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

        if record is None:
            return CaseResult(case["id"], INFRA, (), advisory)
        answer = record.get("answer")
        if not isinstance(answer, dict):
            return CaseResult(
                case["id"], INFRA,
                (AssertResult("answer", False, "no answer object recorded"),), advisory,
            )

        usage = record.get("usage") or {}
        results: list[AssertResult] = []
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
                elif key == "entitlement":
                    results.append(self.entitlement(answer, value))
                elif key == "entitlement_source":
                    results.append(self.entitlement_source(answer, value))
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
        return CaseResult(case["id"], FAIL if failed else PASS, tuple(results), advisory)

    def score_suite(self, cases: list, answers: dict, catalog: dict) -> list[CaseResult]:
        return [self.score_case(c, answers.get(c["id"]), catalog) for c in cases]


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
