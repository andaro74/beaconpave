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
    # Evaluated and not scored **on purpose, and not for the same reason as the one
    # above.** `entitlement_source` is deferred because it cannot be made to mean
    # anything; this one means something already and is withheld because scoring it
    # would move every pinned comparator in one diff (SPEC/06b B7, Decision 11) and
    # because the source of the evidence it reads is still open (SPEC/06b Decision 3).
    #
    # **Un-deferring it is not a one-line change and must not be done as one.** Three
    # things land together or none do: the comparator movement, attested; the
    # re-adjudication SPEC/06b B13 names, since the four `m00b` marks were recorded
    # against `entitlement_source` under an instrument that scored it; and the
    # INFRA-not-FAIL mapping below, which a deferred assert structurally cannot
    # express.
    "tool_before_answer": "evidence path is open (SPEC/06b Decision 3) and scoring it moves every comparator (Decision 11)",
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

    #: What `ai_disclosure` may demand. Two values, and the pair is the assert:
    #: one half alone lets a fix that discloses on every answer pass everything
    #: (ADR-048 decision 3), which is the PR #13 defect in a fourth place.
    AI_DISCLOSURE_MODES = ("required", "not_required")

    @staticmethod
    def _visible(text: str) -> str:
        """`text` with everything a reader cannot see removed.

        **`str.strip()` is not enough, and the gap was measured rather than
        imagined.** The Legal/S&P seat drove `"\\u200b"` -- a zero-width space --
        through the real lane on `c917c11` and scored **5/5 PASS**: `strip()`
        removes ASCII whitespace and leaves every Unicode format character
        standing, so a disclosure nobody can see satisfied a rule whose title is
        *AI-generated recaps must carry a **visible** disclosure*. `"\\u00a0"`
        happened to fail and `"\\u200b"` happened to pass, which is the giveaway
        that the old check was reading an accident of `strip()`'s table rather
        than visibility.

        `Cf` (format), `Cc` (control) and `Cs` (surrogate) go; then whitespace.
        """
        import unicodedata
        return "".join(c for c in text
                       if unicodedata.category(c) not in ("Cf", "Cc", "Cs")).strip()

    def ai_disclosure(self, answer: dict, spec) -> AssertResult:
        """MER-AI-0001's executable control (M09; ADR-075 decision 3).

        `required` -- the key is PRESENT and holds a non-empty, non-whitespace
        string. `not_required` -- the key is PRESENT and is `null`.

        **Both test key presence rather than truthiness, and that is the whole of
        the negative half's value.** `ai_disclosure` is not in
        `answer.schema.json`'s `required` list and the answer object is
        `additionalProperties: false`, so an answer that never emits the key at
        all validates cleanly. A negative assert written as *no disclosure text
        is present* would therefore be satisfied by a model that simply stopped
        emitting the field -- a vacuous pass, and one that reads as the fix
        working. `not_required` demands the agent say *no disclosure is owed
        here* rather than say nothing. The vacuity plant SPEC/09 constraint 7
        names is exactly this, with ADR-075 amendment 1 fact 9's schema reading
        behind it.

        A whitespace-only string fails `required` for the same reason: `" "` is
        a present key carrying no disclosure, and a control satisfied by it is
        measuring the field's existence rather than the disclosure.

        An unknown mode is a FAILURE, never a skip. `test_contracts` holds the
        vocabulary, but a scorer that silently ignored a mode it did not know
        would report a passing case that checked nothing -- the shape the
        `unknown assert` branch in `score_case` exists to refuse, one level in.
        """
        # `spec` is either a mode string or `{mode: [tokens]}`. The TOKENS are
        # policy -- what a disclosure must actually say -- and they live in the
        # case file, not here, so that Legal/S&P's key reaches them: this module
        # is the goldens scorer at (ai-quality, platform-eng) and holds the
        # MECHANISM, on `pave/floors.py`'s criteria-versus-mechanism split. The
        # authoritative token list moves into `rules/MER-AI-0001.yaml` at the
        # disposition, where the rule's owner writes it.
        tokens: list = []
        if isinstance(spec, dict):
            if len(spec) != 1:
                return AssertResult("ai_disclosure", False,
                                    f"expected one mode, got {sorted(spec)}")
            mode, tokens = next(iter(spec.items()))
            tokens = list(tokens or [])
        else:
            mode = spec
        if mode not in self.AI_DISCLOSURE_MODES:
            return AssertResult(
                "ai_disclosure", False,
                f"unknown mode {mode!r}; expected one of {list(self.AI_DISCLOSURE_MODES)}",
            )
        present = "ai_disclosure" in answer
        value = answer.get("ai_disclosure")
        if mode == "required":
            if not present:
                return AssertResult("ai_disclosure", False,
                                    "the answer carries no `ai_disclosure` key at all")
            if not isinstance(value, str):
                return AssertResult("ai_disclosure", False,
                                    f"`ai_disclosure` is {value!r}; MER-AI-0001 requires "
                                    f"disclosure text on AI-authored editorial copy")
            visible = self._visible(value)
            if not visible:
                return AssertResult(
                    "ai_disclosure", False,
                    f"`ai_disclosure` is {value!r}, which renders to nothing a reader can "
                    f"see. MER-AI-0001 requires a VISIBLE disclosure.")
            missing = [t for t in tokens if t.lower() not in visible.lower()]
            if missing:
                # **A disclosure that does not say what it discloses is not one.**
                # Without this, `"."`, `"x"`, `"n/a"` and `"See terms and
                # conditions."` all scored PASS -- and so did the literal sentence
                # `answer.schema.json` currently instructs the model with. The
                # rule's subject is that the copy is AI-generated, so the assert
                # requires the answer to say so.
                return AssertResult(
                    "ai_disclosure", False,
                    f"`ai_disclosure` is {value!r} and does not mention {missing}. A "
                    f"disclosure that does not disclose what the rule is about clears the "
                    f"field's existence, not the obligation.")
            return AssertResult("ai_disclosure", True)
        if not present:
            return AssertResult(
                "ai_disclosure", False,
                "the answer carries no `ai_disclosure` key at all. This case requires the "
                "key PRESENT and null — an omitted key is not a recorded 'no disclosure "
                "owed', and accepting it would let a model satisfy the negative half by "
                "dropping the field (the field is not `required` in the schema)",
            )
        if value is not None:
            return AssertResult("ai_disclosure", False,
                                f"`ai_disclosure` is {value!r}; this case carries no "
                                f"AI-authored editorial copy and must not disclose")
        return AssertResult("ai_disclosure", True)

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

    def tool_before_answer(self, trajectory, expected: str) -> AssertResult:
        """Was `expected` actually invoked, as opposed to claimed?

        The assert `entitlement_source` has been waiting for since ADR-016. That one
        reads a field the model fills in; this one reads what the plane authorized,
        so no value the model can emit satisfies it.

        **Absence is not satisfaction, and that is the whole design.** The obvious
        implementation returns PASS when no trajectory was supplied -- "nothing to
        contradict" -- and SPEC/06b B3 measures that form as green, zero-key, and
        worthless: it also passes when the tool was *refused*, because filtering to
        allowed steps leaves an empty list that falls into the same branch. All three
        absences fail here instead, each with a distinguishable reason.

        **`no-evidence` is a different animal from the other two and is marked so.**
        `score_case`'s contract is that "the service answered wrongly" and "the
        harness could not establish whether it answered wrongly" page different
        people. A missing trajectory is the second. While this assert is deferred it
        cannot raise INFRA -- a deferred result reaches no case verdict by
        construction -- so the distinction is carried in the detail string, and the
        diff that scores this assert is the diff that must route `no-evidence` to
        INFRA rather than FAIL. Written down here because that mapping is the single
        easiest thing to lose between this milestone and the one that un-defers it."""
        if trajectory is None:
            return AssertResult(
                "tool_before_answer", False,
                f"no-evidence: no trajectory recorded, so whether {expected} was called "
                "was never established (INFRA, not FAIL, once this is scored)")
        # **`allowed` is not `ran`, and crediting it was the forgery.** `SPEC/06b` B9:
        # `handler._tool_probe` writes a full `decision: allowed` record for a call it
        # explicitly does not make, at a lake key it can share with a real one. An
        # assert that counted allowed steps credited that. `executed` (ADR-057) is the
        # field that separates them, so this requires it rather than the decision.
        called = {step.get("tool") for step in trajectory
                  if step.get("decision") == "allowed" and step.get("executed") is True}
        if expected in called:
            return AssertResult("tool_before_answer", True, "")
        # Authorized, and no witness that it ran. Distinguished from "never
        # authorized" because they are different failures with different owners:
        # this one is evidence the platform cannot produce, not a model that did
        # not call the tool. `is True` above, so an ABSENT witness lands here --
        # every record written before ADR-057 lacks the field, and absent means
        # unknown, which is not the same as credited.
        unwitnessed = [step for step in trajectory
                       if step.get("tool") == expected
                       and step.get("decision") == "allowed"
                       and step.get("executed") is not True]
        if unwitnessed:
            return AssertResult(
                "tool_before_answer", False,
                f"no-evidence: {expected} was authorized but nothing witnesses that it "
                f"ran (executed={unwitnessed[0].get('executed')!r}) (INFRA, not FAIL, "
                "once this is scored)")
        refused = [step for step in trajectory
                   if step.get("tool") == expected and step.get("decision") != "allowed"]
        if refused:
            return AssertResult(
                "tool_before_answer", False,
                f"{expected} was refused ({refused[0].get('mechanism')}) and never ran")
        # **The diagnostic reports what was AUTHORIZED, not what ran.** The pass
        # condition needs the witness; the failure message needs to tell a reader a
        # wrong tool from no tools at all, and narrowing this to executed steps
        # silently turned "authorized: ['catalog-search']" into "nothing".
        authorized = sorted({step.get("tool") for step in trajectory
                             if step.get("decision") == "allowed"})
        return AssertResult(
            "tool_before_answer", False,
            f"{expected} never called; authorized: {authorized or 'nothing'}")

    def budget(self, usage: dict, ceiling: dict) -> AssertResult:
        """Token-denominated (ADR-014). Dollars are rendered at report time and
        never block, because a vendor price change must not move a verdict.

        Latency here is `max_ms`, a hang guard — not a performance target. The
        per-case `p95_ms` it replaced was a category error: a p95 cannot be
        computed from one sample, and asserting it per case turned the tail it
        explicitly permits into a failure (ADR-016). The distributional statistic
        now lives at suite level, in `suite_latency`.

        **The call count rides the failure when the usage carries one (M08b
        PR 2, ADR-014 amendment 2's obligation).** `tokens_in=8181 over 7700`
        did not say it was a four-call turn, and the ceiling was placed below
        the next call count precisely to catch one; the hand-join M08 paid
        once in `rescore-join.json` is what this suffix retires. Read as the
        length of `usage.calls` — the per-round list the loop records — and
        omitted when the list is absent, so every committed answer file
        without one produces the verdict string it produced before."""
        over = []
        for key in ("tokens_in", "tokens_out"):
            limit, got = ceiling.get(key), usage.get(key)
            if limit is not None and got is not None and got > limit:
                over.append(f"{key}={got} over {limit}")
        limit_ms, got_ms = ceiling.get("max_ms"), usage.get("latency_ms")
        if limit_ms is not None and got_ms is not None and got_ms > limit_ms:
            over.append(f"latency_ms={got_ms} over max_ms {limit_ms} (stalled request)")
        detail = "; ".join(over)
        calls = usage.get("calls")
        if over and isinstance(calls, list) and calls:
            detail += f" (calls={len(calls)})"
        return AssertResult("budget", not over, detail)

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

        # Read off `case["trajectory"]`, a SIBLING of `asserts` rather than an entry
        # in it, so it is dispatched here rather than in the loop below. That shape is
        # why `evals/judged.py` had to be taught about it: the instrument's `scored`
        # and `deferred` lists walk `case["asserts"]` and would not have seen this.
        want = (case.get("trajectory") or {}).get("expect_tool_before_answer")
        if want:
            deferred.append(self.tool_before_answer(record.get("trajectory"), want))
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
                elif key == "ai_disclosure":
                    results.append(self.ai_disclosure(answer, value))
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


def disclosure_sufficiency(cases: list) -> AssertResult:
    """Whether the disclosure pack still has both halves (ADR-048 decision 4).

    **A pack that has gone vacuous must not be able to do it silently.** The
    positive half alone is passed by a fix that emits a disclosure on every
    answer -- ADR-048 decision 3's sentence exactly, and the PR #13 defect this
    repository has now met in three places. The negative half alone is passed by
    a system that never discloses anything, which is the state the pack was
    written to find the service in.

    So the cheapest way to make a disclose-on-everything fix look correct is to
    delete the one negative case, and the cheapest way to make a
    disclose-on-nothing service look correct is to delete the positive ones.
    Both are one line. This returns FAIL for either, and the caller reports
    **INFRA** rather than FAIL -- the pack could not establish anything, which
    pages the platform rather than the service team, and is never a PASS.

    Counts MODES, not cases: five cases all carrying `required` is a pack with
    one half, however many rows it has.
    """
    modes = set()
    for case in cases:
        for assertion in case.get("asserts") or []:
            for key, spec in assertion.items():
                if key != "ai_disclosure":
                    continue
                # the assert takes either `mode` or `{mode: [tokens]}`; a
                # sufficiency check that understood only one shape would report a
                # pack half-empty the day the other shape was used
                modes.add(next(iter(spec)) if isinstance(spec, dict) else spec)
    # **A case that asserts no disclosure at all is a vacuous row**, and counting
    # modes alone could not see it: `score_case` returns PASS for an empty
    # `asserts` list, so a sixth case with `asserts: []` scored PASS and the lane
    # reported `passed 6, total 6` (AI Quality seat, round 1). Only a per-pack
    # test hard-coded to one service caught it; the instrument now refuses it, so
    # a second service's pack is covered by construction.
    vacuous = [case.get("id") for case in cases
               if not any("ai_disclosure" in a for a in case.get("asserts") or [])]
    if vacuous:
        return AssertResult(
            "disclosure_sufficiency", False,
            f"case(s) {vacuous} carry no `ai_disclosure` assert. A case in a disclosure "
            f"pack that does not assert a disclosure passes every run and measures nothing.")
    missing = [m for m in Scorer.AI_DISCLOSURE_MODES if m not in modes]
    if missing:
        return AssertResult(
            "disclosure_sufficiency", False,
            f"the pack carries no case asserting {', '.join(repr(m) for m in missing)}; "
            f"a pack with one half passes against nothing (ADR-048 decision 3). "
            f"Found modes: {sorted(modes) or 'none'} over {len(cases)} case(s)",
        )
    return AssertResult("disclosure_sufficiency", True,
                        f"{len(cases)} case(s), both halves present")


def decide_disclosure(cases: list, results: list | None,
                      missing: list | None = None) -> tuple[str, dict, list]:
    """What a disclosure run decided: `(verdict, scores, notes)`.

    **This lives here and not in `pave/cli.py`, and three seats are the reason.**
    The first version put these branches in the CLI, which matches no
    `pave/twokey.py` rule -- and two seats independently measured what that
    bought: deleting the INFRA branch left **49 tests passing** while the lane
    reported `PASS` at exit 0 over a run where every case established nothing;
    flipping the sufficiency failure from INFRA to FAIL was **SILENT**; and
    stubbing `disclosure_sufficiency` to always-true was **SILENT at 92 passed**.
    Three of the four statements that decide what a disclosure verdict MEANS were
    editable on no key and checked by nothing. That is ADR-037's finding in a new
    place, and `pave/verify.py`'s precedent is the fix: the criteria live in the
    module the seats hold, the CLI keeps the dispatch.

    The order of the branches is the contract, and each is load-bearing:

    1. **A pack that cannot decide is INFRA**, never FAIL and never PASS. A
       one-sided pack establishes nothing about the service -- the positive half
       alone is passed by a disclose-on-everything fix -- so it pages the platform
       rather than the service team. FAIL would route it to the team as a quality
       regression they cannot fix.
    2. **A run that did not arrive is INFRA.**
    3. **Any case that established nothing makes the suite INFRA**, before any
       PASS/FAIL count is read. A run of five INFRA cases scored `passed 0,
       failed 0` and, without this, reported PASS.
    4. Only then FAIL on any failure, else PASS.
    """
    notes: list[str] = []
    scores: dict = {}

    sufficiency = disclosure_sufficiency(cases)
    if not sufficiency.passed:
        return INFRA, scores, [sufficiency.detail]
    if missing:
        return INFRA, scores, [f"committed run(s) missing {sorted(missing)}"]
    if not results:
        return INFRA, scores, ["nothing was scored"]

    # **`results` arrives already reduced across k, and this module must not know
    # how.** `test_the_sampling_did_not_touch_the_scorer` forbids this file from
    # naming the reduction at all, and it is right to: k-sampling is a reporting
    # discipline in the run harness, so moving it here would mean each sample
    # stops being scored by the code path a single run uses -- and the arms stop
    # being comparable to m00b and m01. The first version of this function took
    # the raw per-run lists and reduced them itself; that check caught it, which
    # is a protection test doing exactly its job on a file it did not anticipate.
    # The DECISION stays here, where the seats hold keys on it; the reduction
    # stays in the caller, as it does for the goldens lane.
    #
    # (The check is a substring scan over this source, so it cannot tell a comment
    # explaining the invariant from code breaking it. That is why this paragraph
    # is worded around the names rather than quoting them -- recorded as an
    # observation, not worked around: loosening a three-key protection test to
    # make a comment readable is the wrong trade.)
    counts = tally(results)
    scores = {"passed": counts["passed"], "total": len(cases),
              "failed": counts["failed"], "infra": counts["infra"]}

    for result in results:
        for assertion in result.asserts:
            if not assertion.passed:
                # The failing assert, named per case. Row 1a's chain ends here,
                # and a verdict recording only a count leaves the last link of it
                # to whoever writes the journal.
                notes.append(f"{result.id}: {assertion.kind} — {assertion.detail}")

    if counts["infra"]:
        notes.insert(0, f"{counts['infra']} of {len(cases)} case(s) established nothing")
        return INFRA, scores, notes
    return (FAIL if counts["failed"] else PASS), scores, notes


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
