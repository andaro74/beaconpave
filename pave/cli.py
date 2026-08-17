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


def gate_comment(argv):
    """The score-diff comment body. M00a prints it (and appends to the GitHub
    step summary when running in Actions); M04 posts it to the PR and adds the
    baseline comparison that makes the gate teach rather than merely block.

    Always exits 0 — this is a reporter, not a decider. The workflow runs it with
    `if: always()`, so a non-zero exit here would mask which step actually failed."""
    body = gate_mod.summarize(_flag_values(argv, "--verdicts"))
    _emit(body)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(body + "\n")


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

    print("==> rules registry validation (G7)")
    try:
        rules_validate()
    except SystemExit as exc:
        if exc.code:
            failures.append(f"rules validation failed (exit {exc.code})")

    print("==> L0 unit + L1 contract (hermetic)")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    if proc.returncode == 5:
        failures.append("pytest collected zero tests — an empty suite is a failing suite, not a passing one")
    elif proc.returncode != 0:
        failures.append(f"pytest failed (exit {proc.returncode})")

    print("==> eval dry-run (no model calls)")
    _stub("evals dryrun", "load goldens, resolve fixtures, validate asserts — without calling a model (M03)")

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
                drifted.append(f"{template_path.name}: committed snapshot is stale")
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
    elif cmd == "evals":
        _stub("evals", f"run the pytest eval harness for {rest} against committed baselines, "
                       "emit a verdict record to the schema in quality/verdicts/schema.json")
    elif cmd == "adversarial":
        _stub("adversarial", f"run quality/adversarial/probes.yaml against {rest}; a probe passes "
                             "only if the guardrail blocked or policy denied AND an audit record exists (G4)")
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
    elif cmd == "infra" and rest[:1] == ["snapshot"]:
        infra_snapshot(rest[1:])
    elif cmd == "infra":
        _die("infra: expected `snapshot`", gate_mod.EXIT_CONTRACT)
    elif cmd == "check":
        check(rest)
    else:
        _die(f"unknown command: {cmd} {rest}")


def _entry():
    main(sys.argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
