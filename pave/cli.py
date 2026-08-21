"""
pave — the paved-road CLI for beaconpave.

Implemented: `rules validate` (G7), `gate decide` / `gate comment` (G2), `check`
(G8). The rest are stubs that print what they WOULD do and name the milestone
that implements them, so the repo stays runnable and self-documenting.

  pave new <name> --brand <b> --classification <c>   scaffold a governed service
  pave check                                          hermetic local checks
  pave evals run|dryrun <service>                     run/dry-run the eval harness
  pave adversarial run <service>                      run the L5 probe suite
  pave rules validate                                 validate the rules registry (G7)
  pave infra snapshot [--check] [--from <dir>]        record / verify the synth snapshot (G1)
  pave policy generate [--check]                      generate / verify Cedar from the registry (G3)
  pave gate comment|decide --verdicts ...             post score-diff / fail-closed
  pave drill --event <e> --tier <t>                   game-day readiness drill
  pave selfheal <service>                             classify red suite, propose repair
  pave exception request --rule <id> --ttl <d>        open a time-boxed exception
"""
import glob
import json
import os
import pathlib
import subprocess
import sys
import time

from pave import gate as gate_mod
from pave import twokey
from pave import verdict as verdict_mod

try:
    import yaml
except ImportError:
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _console_safe(text: str, encoding: str) -> str:
    """Rewrite `text` so `encoding` can represent it, losing characters rather
    than raising.

    `pave gate two-key` prints U+2717 on its blocking path. A Windows console
    running cp1252 cannot encode that character, so the command died with a
    UnicodeEncodeError *instead of printing why it blocked* — the operator saw a
    traceback and exit 1, with the reason it exited nowhere on screen. CI never
    caught it because GitHub runners are UTF-8.

    That is the same class as M00a's BOM bug: a governance check that fails for a
    reason which is not the team's fault. Those are the failures that teach people
    to route around the gate, so the console's codepage must not get a vote in
    whether a blocked merge can explain itself.

    Characters the console *can* show are returned untouched, so nothing is
    degraded on a UTF-8 terminal or in a CI log."""
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        return text.encode(encoding, "replace").decode(encoding, "replace")
    return text


def _emit(text: str) -> None:
    """Print rendered gate output through `_console_safe`. Stdout's encoding is
    read at call time rather than cached: it differs between a console, a pipe,
    and a redirect to file, and the blocking path must survive all three."""
    print(_console_safe(text, getattr(sys.stdout, "encoding", None) or "utf-8"))


def rules_validate():
    """G7 — no orphan rules, no immortal rules: every rule has an owner, a source,
    a disposition into at least one enforcing control, and a review-by date.

    Validated against `rules/schema.json` rather than a field list duplicated here.
    A second copy of the requirements is a second place to forget to update, and
    the two would drift silently in the direction of whichever is laxer.

    An empty registry is a FAILURE. `rules/` is the Legal/S&P seat's entire
    surface; a validator that reports success over zero files would report
    success after someone deletes the directory."""
    if yaml is None:
        _die("pyyaml not installed; pip install pyyaml")
    import json as _json

    import jsonschema

    schema = _json.loads((ROOT / "rules" / "schema.json").read_text(encoding="utf-8"))
    files = sorted(glob.glob(str(ROOT / "rules" / "*.yaml")))
    if not files:
        _die("no rule files found (rules/*.yaml) — an empty rules registry is a failure, not a pass (G7)")

    problems = []
    for f in files:
        name = pathlib.Path(f).name
        doc = yaml.safe_load(pathlib.Path(f).read_text(encoding="utf-8"))
        try:
            jsonschema.validate(doc, schema)
        except jsonschema.ValidationError as exc:
            where = "/".join(str(p) for p in exc.absolute_path) or "<root>"
            problems.append(f"{name}: {where}: {exc.message}")

    if problems:
        _die("rules registry invalid:\n  " + "\n  ".join(problems))
    print(f"rules registry valid: {len(files)} rule(s), all with owner + control + review-by")


def _flag_values(argv, flag):
    """Collect the values following `--flag` up to the next `--option`.
    Returns [] when the flag is absent — `gate decide` treats that as blocking,
    so a typo'd flag can never be read as "nothing to check, therefore fine"."""
    if flag not in argv:
        return []
    rest = argv[argv.index(flag) + 1:]
    values = []
    for token in rest:
        if token.startswith("--"):
            break
        values.append(token)
    return values


def gate_decide(argv):
    """G2: fail closed. Exits 1 on a quality FAIL, 2 on a contract/harness
    failure, 0 only on an affirmative pass. Never raises past this point — an
    uncaught exception would surface as an errored CI step, and the whole point
    of this command is that erroring and blocking are the same outcome."""
    decision = gate_mod.decide(_flag_values(argv, "--verdicts"))
    _emit(gate_mod.render(decision))
    sys.exit(decision.exit_code)


def _post_pr_comment(body: str) -> None:
    """Upsert the gate's comment on the pull request. Never raises.

    **Upsert, not append.** A reviewer scrolling past six stale gate comments to
    find the current one is a gate that has stopped teaching, so a run replaces
    its own previous comment, found by the marker in the body.

    Silent no-op outside Actions, and silent on any failure. Claim 2's artifact is
    the blocked merge; the comment is how it teaches. A comment that could not be
    posted must never turn a correct decision into a red step for a reason that is
    not the team's fault - that is the failure mode `_console_safe` exists for,
    arriving over HTTP instead of through a codepage. `gate decide` runs
    separately and is the only thing that blocks."""
    import urllib.error
    import urllib.request

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not (token and repo and event_path and pathlib.Path(event_path).is_file()):
        return

    try:
        event = json.loads(pathlib.Path(event_path).read_text(encoding="utf-8"))
        number = event["pull_request"]["number"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return

    api = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "User-Agent": "beaconpave-gate"}

    def call(url, data=None, method="GET"):
        request = urllib.request.Request(
            url, method=method, headers=headers,
            data=json.dumps(data).encode("utf-8") if data is not None else None)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8") or "null")

    try:
        existing = call(f"{api}/issues/{number}/comments?per_page=100") or []
        mine = next((c for c in existing
                     if gate_mod.COMMENT_MARKER in (c.get("body") or "")), None)
        if mine:
            call(f"{api}/issues/comments/{mine['id']}", {"body": body}, method="PATCH")
            print(f"[pave gate] updated comment {mine['id']} on PR #{number}")
        else:
            call(f"{api}/issues/{number}/comments", {"body": body}, method="POST")
            print(f"[pave gate] posted a comment on PR #{number}")
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        # Reported, never raised. See the docstring.
        print(f"[pave gate] could not post the comment ({exc}); the decision is unaffected "
              "and `gate decide` still blocks", file=sys.stderr)


def gate_comment(argv):
    """The score-diff comment - claim 2's *teach* half.

    Prints the body, appends it to the GitHub step summary, and from M04 posts it
    to the pull request. The body carries every suite's scores and the runners'
    own account of what moved, because until now that account lived only in a CI
    log: the lane printed which probe moved and in which direction, the verdict
    recorded `FAIL`, and the reviewer got a red check with no way to see the
    difference without opening the run.

    Always exits 0 - this is a reporter, not a decider. The workflow runs it with
    `if: always()`, so a non-zero exit here would mask which step actually
    failed."""
    body = gate_mod.summarize(_flag_values(argv, "--verdicts"))
    _emit(body)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(body + "\n")
    if "--no-post" not in argv:
        _post_pr_comment(body)


def gate_two_key(argv):
    """G9: the second key, machine-checked. Exits 1 when a two-key path changed
    without the owning seat's recorded disposition and reasoning.

    Changed files come from `--changed`; the PR body from the PR_BODY environment
    variable (passed as env rather than interpolated into the workflow's shell,
    so a PR body cannot inject shell)."""
    changed = _flag_values(argv, "--changed")
    body = os.environ.get("PR_BODY", "")
    body_file = _flag_values(argv, "--body-file")
    if body_file:
        body = pathlib.Path(body_file[0]).read_text(encoding="utf-8-sig")

    problems = twokey.evaluate(changed, body, repo_root=ROOT)
    _emit(twokey.render(changed, problems))
    if problems:
        sys.exit(gate_mod.EXIT_QUALITY)


def evals_dryrun_cmd(argv=()):
    """`pave evals dryrun` — load and resolve, call nothing."""
    from evals.run_evals import GOLDENS, _load
    from evals.run_evals import dryrun as _dryrun
    return _dryrun(_load(GOLDENS))


def _suite_pin(pinned: dict, service: str, suite: str):
    """One suite's comparator for one service, or `None` if the file cannot supply it.

    `suites` arrived at M04, when the adversarial lane needed a pin and the
    alternative was a third place to keep one. Extracted before the L5 lane exists
    rather than after, because the second copy of a fragile reach is where the
    first copy's gaps get inherited.

    **`None` rather than an exception, for every malformed shape.** A lane that
    raises leaves no verdict file, which the gate blocks on (exit 2, "pages the
    platform") — so G2 holds either way. But an ABSENT verdict and an errored step
    page differently, and a comparator whose *content* is wrong is not a platform
    incident. The first version of this used `.get("suites", {})`, which supplies
    the default only when the key is missing: `suites: null` and `suites: []` went
    straight past it into an `AttributeError`. Enumerated by the Platform seat
    across nineteen shapes; the loop below is written so no shape reaches a raise
    and, more importantly, so no shape reaches a PASS."""
    node = pinned
    for key in ("services", service, "suites", suite):
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node if isinstance(node, dict) else None


def evals_run(argv=()):
    """`pave evals run <service> [--out verdict.json]` — the L2 lane.

    **It scores committed answers and calls no model.** A lane that ran the agent
    per pull request would need model access in CI, which G1 and G8 both refuse,
    and would make every PR cost money and return a different number. What it can
    decide hermetically is the thing nothing else decides: **that the instrument
    has not moved underneath a published row.**

    The comparator is `evals/comparators.json` — what the committed answers score
    *today* — and never the recorded history number, which is what they scored on
    the day and does not move (ADR-016). Deviation in **either** direction fails.
    A drop is the obvious regression; a rise is the one this repo exists to catch,
    because the m00b control gained three cases from an instrument change with no
    system improvement at all, and a flattering control makes every later
    milestone unfalsifiable.

    Nothing here reads `evals/refusals.py`: the guardrail-refusal band is
    reporting-only and must never reach a gate decision."""
    import yaml as _yaml

    from evals.deterministic import Scorer, tally
    from evals.run_evals import summarise
    from pave import verdict as verdict_mod

    out = _flag_values(argv, "--out")
    # `--comparators` exists so a test can point at a copy. Without it
    # `tests/test_evals_lane.py` had to edit the tracked, two-key
    # `evals/comparators.json` in the real working tree and restore it in a
    # `finally` - twice per `make check`, with a killed run leaving a gate criterion
    # modified on disk. Against this repo's own history of a file changing between
    # being written and being committed, that is not a theoretical exposure.
    override = _flag_values(argv, "--comparators")
    consumed = {out[0] if out else None, override[0] if override else None}
    services = [a for a in argv if not a.startswith("--") and a not in consumed]
    service = pathlib.Path(services[0]).name if services else "highlights-agent"

    comparators = pathlib.Path(override[0]) if override else ROOT / "evals" / "comparators.json"
    pinned = json.loads(comparators.read_text(encoding="utf-8"))
    entry = _suite_pin(pinned, service, "goldens")
    if entry is None:
        # ABSENT, not PASS. The gate's own rule: a suite with nothing to decide on
        # is missing from the verdict list rather than reporting success.
        # Names what IS pinned. A typo'd service path was indistinguishable from a
        # service nobody has onboarded, and in CI both become an absent verdict that
        # pages the platform for a service-team typo.
        # `pinned.get(...)`, not `pinned['services']`. The reporting line read the
        # key the reader had just established might be missing, so a comparator
        # with no `services` at all crashed the lane *while telling the operator
        # it had nothing to report* — the ABSENT branch raising on its way to
        # explaining that nothing was absent.
        known = pinned.get("services") if isinstance(pinned, dict) else None
        names = ", ".join(sorted(known)) if isinstance(known, dict) and known else "none"
        _emit(f"[pave evals] no goldens comparator pinned for {service!r}; emitting nothing. "
              f"Pinned services: {names}")
        return 0

    cases = _yaml.safe_load(
        (ROOT / "services" / service / "evals" / "golden" / "cases.yaml").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    scorer = Scorer(root=ROOT)

    failures, scores = [], {}
    arms = {entry["arm"]: entry}
    for name, other in (entry.get("also_pinned") or {}).items():
        arms[name] = other

    # An arm disappearing from the comparator scored the remaining arm alone and
    # PASSED. Truncating the file fails closed - a missing `expected_passed` raises -
    # so deletion passing while truncation blocked was exactly the wrong way round,
    # and deletion is the easier edit to make by accident. The expected set is
    # declared beside the arms rather than inferred from them, because inferring it
    # from the file being checked is how a deletion becomes self-justifying.
    expected_arms = set(entry.get("arms_expected") or ["tools", "control"])
    dropped = sorted(expected_arms - set(arms))
    if dropped:
        failures.append(
            f"arm(s) missing from the comparator: {dropped}. M02's result is the paired "
            "diff, not the total (ADR-021); scoring one arm alone is a different "
            "measurement wearing the same number.")

    for arm, spec in arms.items():
        # Checked BEFORE loading. Reversed, the comprehension raised
        # `FileNotFoundError` first and this branch was unreachable dead code - so a
        # missing run produced a traceback, no verdict file, and an ABSENT evals
        # verdict that pages the platform, on a lane declaring `fail_closed=True`.
        # The designed behaviour is a FAIL naming which run vanished.
        missing = [r for r in spec["runs"] if not (ROOT / r).is_file()]
        if missing:
            failures.append(f"{arm}: committed run(s) missing {missing}")
            continue
        try:
            loaded = [json.loads((ROOT / r).read_text(encoding="utf-8")) for r in spec["runs"]]
        except json.JSONDecodeError as exc:
            failures.append(f"{arm}: a committed run is unreadable ({exc})")
            continue
        per_sample = [scorer.score_suite(cases, answers, catalog) for answers in loaded]
        results, _ = summarise(per_sample, [c["id"] for c in cases]) if len(per_sample) > 1             else (per_sample[0], {})
        passed = tally(results)["passed"]
        scores[f"{arm}_passed"] = passed
        expected = spec["expected_passed"]
        if passed != expected:
            direction = "below" if passed < expected else "ABOVE"
            failures.append(
                f"{arm}: {passed}/{len(cases)} is {direction} the pinned comparator "
                f"{expected}/{len(cases)}. The instrument has moved. If that is intended, the "
                "comparator moves in its own two-key PR stating which change moved it and in "
                "which direction — never in the same diff that moved it."
            )

    decided = "FAIL" if failures else "PASS"
    # The verdict is written BEFORE anything is printed. Reversed, a console that
    # cannot encode the summary line killed the process on the PASS path and left
    # no verdict file at all - a passing lane exiting 1 with a traceback.
    if out:
        verdict_mod.write(out[0], verdict_mod.build(
            service=service, surface="agent", suite="evals", layer="L2",
            verdict=decided, fail_closed=True, scores=scores, notes=failures,
            artifacts=[str(r) for spec in arms.values() for r in spec["runs"]]))

    for line in failures:
        _emit(f"    {line}")
    _emit(f"[pave evals] {service}: {decided} - "
          + ", ".join(f"{k} {v}" for k, v in sorted(scores.items())))
    if failures:
        _emit(f"    fix: re-derive locally with `python -m pave.cli evals run {service}`. "
              "If the move is intended, edit evals/comparators.json in its own PR with "
              "`Two-Key-Disposition: ai-quality` and `Two-Key-Disposition: platform-eng`, "
              "naming which of the three inputs moved - the golden cases, "
              "evals/deterministic.py, or data/catalog.json.")
    return 1 if failures else 0


def adversarial_run(argv=()):
    """`pave adversarial run <service> [--out verdict.json]` — the L5 lane.

    **Two things have to hold, and the second is why this lane is not simply the
    L2 lane with a different corpus.**

    1. **Every pinned probe result still holds.** Committed observations —
       fetched back from the audit lake on the day they were taken — re-scored
       through today's `score_probe`, per probe and in total, against
       `evals/comparators.json`. Deviation in **either** direction fails: a rise
       is the direction this repo exists to catch, and on the adversarial side it
       is a one-line edit away, because the easiest way to raise a probe score is
       to widen what counts as a refusal.

    2. **G4 still means what `quality/adversarial/g4-semantics.yaml` says.**
       The pins alone cannot see this. Measured before the lane was built:
       deleting the `and logged` half of `score_probe` moves neither the m01 pin
       nor the m00b control, because `refused` and `logged` never disagree
       anywhere in the committed corpora — every m01 observation carries a record
       and every m00b observation refuses nothing. That is structural, not a
       corpus to improve, so the semantics are checked from a corpus built to
       discriminate rather than inferred from a number.

    **It calls no model**, for ADR-029's reasons applied one layer over: a lane
    that ran probes per pull request would need model access in CI, which G1
    refuses, and would return a different number every time against a guardrail
    this repo has measured as stochastic on identical input.

    Exit codes follow `pave/gate.py`'s contract, and the split is the point.
    A moved probe result or a broken semantics case is a **quality** FAIL and
    pages the service team. A missing observation, an unreadable `pass_when` or
    an audit record that did not resolve is **INFRA** — the harness could not
    establish the fact, which is a different statement from the system failing,
    and it pages the platform.

    **A probe is never ADVISORY.** G4 has no "allowed" answer (ADR-028) and no
    "we could not tell" answer either; the second is INFRA, and INFRA blocks."""
    import yaml as _yaml

    from evals.adversarial import check_semantics, score_corpus
    from evals.deterministic import INFRA

    out = _flag_values(argv, "--out")
    override = _flag_values(argv, "--comparators")
    consumed = {out[0] if out else None, override[0] if override else None}
    services = [a for a in argv if not a.startswith("--") and a not in consumed]
    service = pathlib.Path(services[0]).name if services else "highlights-agent"

    comparators = pathlib.Path(override[0]) if override else ROOT / "evals" / "comparators.json"
    pinned = json.loads(comparators.read_text(encoding="utf-8"))
    suite = _suite_pin(pinned, service, "adversarial")
    if suite is None:
        # ABSENT, not PASS — the gate's own rule, and the same branch the L2 lane
        # takes. A suite with nothing to decide on is missing from the verdict
        # list rather than reporting success, and the gate blocks on the absence.
        known = pinned.get("services") if isinstance(pinned, dict) else None
        names = ", ".join(sorted(known)) if isinstance(known, dict) and known else "none"
        _emit(f"[pave adversarial] no adversarial comparator pinned for {service!r}; "
              f"emitting nothing. Pinned services: {names}")
        return 0

    probes = _yaml.safe_load((ROOT / "quality" / "adversarial" / "probes.yaml")
                             .read_text(encoding="utf-8"))
    semantics = _yaml.safe_load((ROOT / "quality" / "adversarial" / "g4-semantics.yaml")
                                .read_text(encoding="utf-8"))

    failures, infra, scores, moved = [], [], {}, []

    # --- what G4 means, before what any number says ---------------------------
    #
    # Checked first because it changes how a moved number reads. If the semantics
    # broke, a probe score that also moved is a consequence rather than a second
    # finding, and the operator should be told which one to fix.
    for failure in check_semantics(semantics):
        failures.append(f"G4 semantics: {failure}")

    # --- every pinned observation set, re-scored ------------------------------
    #
    # `PIN_FLOOR`'s argument in `tests/test_instrument_stability.py` applies here
    # too: the expected set is declared beside the pins AND defaulted, so removing
    # `pins_expected` cannot shrink what the lane checks. The default mirrors the
    # L2 lane's `arms_expected or [...]`.
    expected = sorted(set(suite.get("pins_expected") or ["m01", "m00b"]))
    absent = [tag for tag in expected if tag not in (suite.get("pins") or {})]
    if absent:
        failures.append(
            f"pin(s) expected and absent from the comparator: {absent}. A milestone that "
            "recorded a probe score keeps its pin — history is append-only and so is this.")

    for tag in expected:
        pin = (suite.get("pins") or {}).get(tag)
        if pin is None:
            continue
        missing = [o for o in pin["observations"] if not (ROOT / o).is_file()]
        if missing:
            # INFRA, not FAIL. The observations are gone, so nothing about the
            # system under test was established either way.
            infra.append(f"{tag}: committed observation file(s) missing {missing}")
            continue
        observations = {}
        try:
            for path in pin["observations"]:
                observations |= json.loads((ROOT / path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            infra.append(f"{tag}: a committed observation file is unreadable ({exc})")
            continue

        results = score_corpus(probes, observations)
        actual = {r.id: r.result for r in results}
        passed = sum(1 for r in results if r.result == "PASS")
        scores[f"{tag}_passed"] = passed

        # INFRA travels separately from FAIL, per probe. A probe the harness could
        # not score is not a probe the platform failed, and collapsing the two
        # would let a vanished observation read as a regression in the service.
        unscored = [r for r in results if r.result == INFRA]
        if unscored:
            infra.append(f"{tag}: {len(unscored)} probe(s) not scored — "
                         + "; ".join(f"{r.id} ({r.reason})" for r in unscored))

        expected_results = pin.get("expected_results") or {}
        for pid in sorted(set(expected_results) | set(actual)):
            was, now = expected_results.get(pid), actual.get(pid)
            if was != now:
                moved.append(f"{tag}/{pid}: {was or 'unpinned'} -> {now or 'gone'}")

        if passed != pin["expected_passed"]:
            direction = "below" if passed < pin["expected_passed"] else "ABOVE"
            failures.append(
                f"{tag}: {passed}/{len(probes)} is {direction} the pinned comparator "
                f"{pin['expected_passed']}/{len(probes)}. The adversarial instrument has "
                "moved. A RISE is the direction that matters here: the easiest way to raise "
                "a probe score is to widen what counts as a refusal.")

    if moved:
        failures.append("probe result(s) moved against the pin: " + ", ".join(moved)
                        + ". A total can hide a swap; the per-probe pin cannot.")

    # INFRA outranks a quality FAIL, matching `pave/gate.py`: if the lane cannot
    # trust its own inputs, that is the first thing to fix.
    decided = "INFRA" if infra else ("FAIL" if failures else "PASS")

    # Written BEFORE anything is printed, the ordering the L2 lane had to learn:
    # a console that cannot encode the summary killed the process on the PASS path
    # and left no verdict file at all.
    if out:
        verdict_mod.write(out[0], verdict_mod.build(
            service=service, surface="agent", suite="adversarial", layer="L5",
            verdict=decided, fail_closed=True, scores=scores, notes=infra + failures,
            artifacts=sorted({o for tag in expected
                              for o in ((suite.get("pins") or {}).get(tag) or {}).get(
                                  "observations", [])})))

    for line in infra + failures:
        _emit(f"    {line}")
    _emit(f"[pave adversarial] {service}: {decided} - "
          + ", ".join(f"{k} {v}" for k, v in sorted(scores.items()))
          + f"; {len(semantics.get('cases') or [])} G4 semantics case(s) checked")
    if failures or infra:
        _emit(f"    fix: re-derive locally with `python -m pave.cli adversarial run {service}`. "
              "A moved probe number is either a scorer change or a corpus change — say which "
              "in the PR body. If the move is intended, edit evals/comparators.json in its own "
              "PR with `Two-Key-Disposition:` from ai-quality, platform-eng AND security. "
              "Never edit quality/adversarial/g4-semantics.yaml to make this lane pass: that "
              "file is what a probe passing means, and changing it needs Security plus an ADR.")
    return 1 if (failures or infra) else 0


def check(argv=()):
    """Hermetic local checks (G8): no cloud, no network. The platform-neutral
    twin of `make check` — the Makefile's `2>/dev/null` and `rm -f` are POSIX-only,
    and this repo has to run on the machine it is developed on.

    Zero collected tests is a FAILURE, not a pass. pytest exits 5 when it collects
    nothing; treating that as green is how a suite reports success for months
    while testing nothing.

    With `--out`, emits a verdict record for the contract suite. That record is
    what the gate decides on: from M00a the gate is live against a suite that
    actually exists, rather than waiting for the eval harness at M03."""
    out = _flag_values(argv, "--out")
    started = time.monotonic()
    failures = []

    print("==> tool-plane drift (G3): the committed Cedar and contracts vs the registry")
    try:
        policy_generate(["--check"])
    except SystemExit:
        # Collected, not raised. Unwrapped, this aborted before the tests ran and
        # before `--out` wrote a verdict — so CI blocked on an ABSENT verdict
        # (exit 2, "the gate could not establish anything, page the platform")
        # when the actual finding is a contract regression that should page the
        # team. Fail-closed either way; the wrong pager is still the wrong pager.
        failures.append("tool-plane drift (G3)")

    print("==> rules registry validation (G7)")
    try:
        rules_validate()
    except SystemExit as exc:
        if exc.code:
            failures.append(f"rules validation failed (exit {exc.code})")

    print("==> style (ruff)")
    try:
        lint = subprocess.run([sys.executable, "-m", "ruff", "check", "."], cwd=ROOT)
        if lint.returncode != 0:
            failures.append(f"ruff failed (exit {lint.returncode})")
    except FileNotFoundError:
        # Loud, not skipped. `ruff.toml` selects six rule families, `pyproject.toml`
        # declares the dev dependency and CLAUDE.md names it as the Python style
        # rule — and nothing invoked it: not the Makefile, not this function, not
        # the gate workflow. A linter nobody runs is a linter that has been wrong,
        # silently, since the first commit that broke it. The same shape as the
        # Makefile's old `|| echo`, which reported green over zero tests for the
        # repo's whole life. Absent tooling is a failure, never a pass.
        failures.append("ruff is not installed — `pip install -e .` (it is a declared dev dep)")

    print("==> L0 unit + L1 contract (hermetic)")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    if proc.returncode == 5:
        failures.append("pytest collected zero tests — an empty suite is a failing suite, not a passing one")
    elif proc.returncode != 0:
        failures.append(f"pytest failed (exit {proc.returncode})")

    print("==> guardrail-refusal band (SPEC/01, reporting only)")
    try:
        # Printed, never collected into `failures`. This step cannot fail the check:
        # a refusal count reaching a pass/fail decision would let a guardrail
        # misconfiguration read as a service regression, and would let tuning the
        # guardrail move a recorded number. `tests/test_refusal_band.py` is where it
        # is asserted; this is where it is *reported*, because a reporting-only
        # number that prints nowhere reports nothing - which is what it did from M01
        # until here, inside a runner nobody re-executes.
        from evals import refusals
        _emit(refusals.render())
    except Exception as exc:  # noqa: BLE001
        # Not a failure either. The band is advisory; a broken reporter is a broken
        # reporter, and dressing it as a control finding would be the same category
        # error one level down.
        print(f"    (refusal band unavailable: {exc})")

    print("==> eval dry-run (no model calls)")
    try:
        # Was a `_stub` that printed a `==>` header in the same format as the three
        # real steps above it, so a skimmed green run read as four phases when three
        # ran — and it named M03 in its own output, which is how it became M03's.
        # `run_evals.dryrun` already did the work.
        from evals.run_evals import GOLDENS, _load
        from evals.run_evals import dryrun as evals_dryrun
        if evals_dryrun(_load(GOLDENS)):
            failures.append("eval dry-run failed — fixtures or cases do not resolve")
    except SystemExit as exc:
        if exc.code:
            failures.append(f"eval dry-run failed (exit {exc.code})")

    if out:
        verdict_mod.write(out[0], verdict_mod.build(
            service="beaconpave",
            surface="agent",
            suite="contract",
            layer="L1",
            verdict="FAIL" if failures else "PASS",
            fail_closed=True,
            duration_s=round(time.monotonic() - started, 3),
        ))
        print(f"wrote verdict: {out[0]}")

    if failures:
        _die("check failed:\n  " + "\n  ".join(failures))
    print("check: PASS (hermetic — no cloud, no network)")


#: Where `cdk synth` writes, and where the committed snapshot lives.
CDK_OUT = ROOT / "platform" / "infra" / "cdk.out"
SNAPSHOT_DIR = ROOT / "platform" / "infra" / "tests" / "fixtures"


#: The registry Cedar is generated from, and the generated set the gateway reads.
REGISTRY = ROOT / "platform" / "registry" / "tools.yaml"
POLICY_SET = ROOT / "platform" / "gateway" / "policy" / "tools.cedar"
CONTRACT_SET = ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json"


def policy_generate(argv):
    """Generate the Cedar policy set from the registry, or verify the committed one.

    ADR-004 makes generation the load-bearing half: a hand-written policy drifts
    from the registry, and one that disagrees with the registry is worse than no
    policy because it makes the registry look authoritative while something else
    decides.

    `--check` is the drift gate, and unlike its `infra snapshot` counterpart it is
    **hermetic** — regenerating needs the registry and nothing else, no Node and no
    AWS account. So the check runs inside `make check` rather than needing a CI job
    of its own, which makes it strictly harder to skip than the synth snapshot it
    is modelled on (ADR-017)."""
    import yaml

    sys.path.insert(0, str(ROOT / "platform" / "gateway"))
    from core import cedar, toolplane

    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    generated = cedar.generate(registry)

    # The contract set travels with the policy set because the plane needs both at
    # run time and the Lambda bundle is what deploys. Same source, same drift
    # check: the registry decides, and these are build products that happen to be
    # committed.
    schemas = {}
    for tool in registry:
        for rel in tool["schemas"].values():
            schemas[rel] = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    contracts = json.dumps(toolplane.generate_contracts(registry, schemas), indent=2) + "\n"

    if "--check" in argv:
        committed = POLICY_SET.read_text(encoding="utf-8") if POLICY_SET.is_file() else ""
        committed_contracts = (CONTRACT_SET.read_text(encoding="utf-8")
                               if CONTRACT_SET.is_file() else "")
        if committed != generated or committed_contracts != contracts:
            _die(
                "the committed tool-plane set is not what the registry generates. "
                "Run `python -m pave.cli policy generate` and commit the result. "
                "A policy set that disagrees with the registry makes the registry look "
                "authoritative while something else decides (ADR-004).",
                gate_mod.EXIT_CONTRACT,
            )
        print(f"tool plane current: {len(cedar.parse(generated))} policies and "
              f"{len(registry)} contract(s) from {len(registry)} registered tool(s)")
        return

    # Parse before write. A generator that emits something its own parser rejects
    # would otherwise leave the bad artifact on disk and fail afterwards, and the
    # next reader would find a policy set nothing can evaluate.
    policies = cedar.parse(generated)

    POLICY_SET.parent.mkdir(parents=True, exist_ok=True)
    POLICY_SET.write_text(generated, encoding="utf-8")
    CONTRACT_SET.write_text(contracts, encoding="utf-8")
    print(f"wrote {POLICY_SET.relative_to(ROOT)} and {CONTRACT_SET.relative_to(ROOT)}: "
          f"{len(policies)} policies, {len(registry)} contracts")


def infra_snapshot(argv):
    """Record the normalized synth snapshot, or verify the committed one (ADR-017).

    `--check` is the CI freshness job: it re-reads `cdk.out` after a synth and
    exits non-zero if the committed snapshot no longer matches. That job is the
    only thing standing between a committed template and a fiction, so it blocks
    rather than warns — the hermetic IAM assertions are only as true as the
    snapshot they read.

    With `--out`, emits a verdict record so the freshness check reaches the gate
    the same way every other suite does. It is not a bespoke CI step that fails
    the job on its own: `gate decide` stays the single decider (G2), and a
    missing `verdict-infra.json` blocks by absence exactly like any other.

    An absent `cdk.out` is INFRA, not FAIL. The harness could not establish
    anything — which pages the platform — rather than the infrastructure having
    regressed, which pages the team. G2 keeps those two distinguishable."""
    from pave import infra

    check = "--check" in argv
    out = _flag_values(argv, "--out")
    # `--from` because the CDK CLI takes an exclusive lock on its output
    # directory: a `cdk deploy` in another terminal makes `cdk synth` refuse, and
    # recording a snapshot should not require waiting on an unrelated deploy.
    source = _flag_values(argv, "--from")
    cdk_out = pathlib.Path(source[0]) if source else CDK_OUT
    started = time.monotonic()

    def emit(state):
        if out:
            verdict_mod.write(out[0], verdict_mod.build(
                service="beaconpave",
                surface="agent",
                suite="infra",
                layer="L1",
                verdict=state,
                fail_closed=True,
                duration_s=round(time.monotonic() - started, 3),
            ))
            print(f"wrote verdict: {out[0]}")

    templates = sorted(cdk_out.glob("*.template.json"))
    if not templates:
        emit("INFRA")
        _die(f"no synthesized templates in {cdk_out} — run `cdk synth` first", gate_mod.EXIT_CONTRACT)

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    drifted = []
    for template_path in templates:
        normalized = infra.normalize(infra.load(template_path))
        rendered = json.dumps(normalized, indent=2, sort_keys=True) + "\n"
        committed = SNAPSHOT_DIR / template_path.name

        if check:
            if not committed.is_file():
                drifted.append(f"{template_path.name}: no committed snapshot")
            elif committed.read_text(encoding="utf-8") != rendered:
                # Show WHAT drifted, not merely that something did. A drift
                # report you cannot read is one you re-record without reading,
                # which is the exact habit ADR-017 says lets an IAM grant in.
                # The first CI run of this job reported "stale" against a
                # snapshot that was byte-identical locally, and the message gave
                # nobody a way to tell an environment difference from a real one.
                import difflib
                diff = list(difflib.unified_diff(
                    committed.read_text(encoding="utf-8").splitlines(),
                    rendered.splitlines(),
                    fromfile=f"committed/{template_path.name}",
                    tofile=f"synthesized/{template_path.name}",
                    lineterm="",
                    n=1,
                ))
                shown = diff[:60]
                elided = len(diff) - len(shown)
                detail = ('\n' + '      ').join(shown)
                if elided > 0:
                    detail += '\n' + f'      ... {elided} more diff line(s)'
                drifted.append(
                    f'{template_path.name}: committed snapshot is stale'
                    + '\n' + '      ' + detail
                )
        else:
            committed.write_text(rendered, encoding="utf-8")
            print(f"recorded {committed.relative_to(ROOT)}")

    if not check:
        return

    emit("FAIL" if drifted else "PASS")
    if drifted:
        _die(
            "synth snapshot is out of date:\n  " + "\n  ".join(drifted)
            + "\n\nRun `cd platform/infra && npx cdk synth --quiet` then "
              "`python -m pave.cli infra snapshot`, and commit the result. The hermetic IAM "
              "assertions (G1) read the committed snapshot — a stale one asserts against "
              "infrastructure that no longer exists."
        )
    print(f"synth snapshot current: {len(templates)} template(s)")


def _stub(name, does):
    print(f"[pave {name}] (stub) would: {does}")
    print("  implement in the component referenced in README.md's repository map.")


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd, *rest = argv
    if cmd == "rules" and rest[:1] == ["validate"]:
        rules_validate()
    elif cmd == "new":
        _stub("new", f"scaffold service {rest} from templates/agent-tools with gate.yml, "
                     "CODEOWNERS, starter goldens, manifest; wire SDK; enable tracing")
    elif cmd == "evals" and rest[:1] == ["run"]:
        return evals_run(rest[1:])
    elif cmd == "evals" and rest[:1] == ["dryrun"]:
        return evals_dryrun_cmd(rest[1:])
    elif cmd == "evals":
        _stub("evals", f"unknown evals subcommand {rest}; try `run` or `dryrun`")
    elif cmd == "adversarial" and rest[:1] == ["run"]:
        return adversarial_run(rest[1:])
    elif cmd == "adversarial":
        _die(f"adversarial: expected `run`, got {rest}", gate_mod.EXIT_CONTRACT)
    elif cmd == "gate" and rest[:1] == ["decide"]:
        gate_decide(rest[1:])
    elif cmd == "gate" and rest[:1] == ["comment"]:
        gate_comment(rest[1:])
    elif cmd == "gate" and rest[:1] == ["two-key"]:
        gate_two_key(rest[1:])
    elif cmd == "gate":
        _die("gate: expected `decide`, `comment`, or `two-key`", gate_mod.EXIT_CONTRACT)
    elif cmd == "drill":
        _stub("drill", f"run drill/scenarios for {rest}: blackout sweep, caption check, alarm "
                       "self-test; emit a machine-signed go/no-go artifact")
    elif cmd == "selfheal":
        _stub("selfheal", f"classify the red suite for {rest} as drift-vs-defect; if drift, propose "
                          "a repair as an ai-proposed PR with reasoning (human disposes — G6)")
    elif cmd == "exception":
        _stub("exception", "open a time-boxed, dashboard-visible, auto-expiring exception with an "
                           "auto-drafted ADR for the owning seat to approve")
    elif cmd == "policy" and rest[:1] == ["generate"]:
        policy_generate(rest[1:])
    elif cmd == "policy":
        _die("policy: expected `generate`", gate_mod.EXIT_CONTRACT)
    elif cmd == "infra" and rest[:1] == ["snapshot"]:
        infra_snapshot(rest[1:])
    elif cmd == "infra":
        _die("infra: expected `snapshot`", gate_mod.EXIT_CONTRACT)
    elif cmd == "check":
        check(rest)
    else:
        _die(f"unknown command: {cmd} {rest}")


def _entry():
    # `main`'s return value was discarded here and below, so a command that
    # reported a failure by RETURNING a code exited 0 anyway. Every command until
    # M03 signalled failure by raising `SystemExit`, so nothing noticed — and the
    # first one that returned a code was the L2 evals lane, which would have
    # printed FAIL and exited green.
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
