"""
The rules registry, read as a chain rather than as a file.

Claim 6 is *rules have owners and dispositions*, and its proof artifact is a
diff: a rule delta disposed end-to-end into eval cases. What makes that a claim
rather than a filing habit is that a reader can walk **rule -> disposition ->
control -> case -> assert** with no step supplied by hand. This module is that
walk, and `pave/cli.py` carries only the dispatch line -- `pave/verify.py`'s
shape, and for `pave/verify.py`'s reason: the criteria live where a seat's key
reaches them, and ADR-041 decision 7 refuses to key `pave/cli.py`.

**No step is supplied by this module.** Every link is read out of the tree or
reported as missing. The temptation the seat round was told to plant is a reader
that falls back to the pack's conventional path when `controls[].ref` does not
resolve: it makes a broken disposition render exactly like a working one, which
turns the whole of row 1a into prose. `trace` therefore returns defects
alongside steps and `render` prints them, and a chain with any defect is
`resolved == False`.

**`orphan_rules` is the enforcement half of `rules/schema.json`'s definition.**
That definition -- *a rule whose disposition names an enforcing control whose
`ref` does not resolve to a path in this tree* -- lives in the schema's
`description`, in one sense, because ADR-053 refused to hand M07 a term meaning
two things. JSON Schema cannot express it, because it cannot resolve a path, so
the schema carries the sentence and this function carries the check, and the two
say the same sentence. A rule whose only control is an explicit reasoned
`no-control` record is **not** an orphan: the schema names that as a permitted
disposition, and reading it as orphaning would refuse the very shape
`MER-AI-0001` has carried since M00a on purpose.

Owning seat: Legal / Standards & Practices (the registry) - Platform
Engineering (the mechanism) - Security (the counterweight the registry rule
already carries).
"""
from __future__ import annotations

import ast
import pathlib
import re
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:  # pragma: no cover - surfaced by the CLI, which dies with a message
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "rules"

#: A control type that records a decision NOT to enforce yet. It is a disposition
#: the schema permits, so its `ref` is prose and is never resolved as a path.
NO_CONTROL = "no-control"

#: Where each enforcing control type's artifact must live, and what shape it must
#: have. **Read against the schema's own enum**, so a `type` outside it is refused
#: rather than treated as "some other control we do not walk".
#:
#: Round 2 measured why this is not optional: with the walk keyed only on
#: `path.exists()`, a `type: cedar_policy` control pointing at a **markdown design
#: document** reported a clean chain, `type: human-review` (outside the enum) was
#: accepted, `type: no_control` with an underscore was read as ENFORCING, and
#: `ref: "."` — the repository root — discharged every rule. The first fix made
#: correctly-typed controls stop reading as broken; it made anything that exists
#: read as fine, which is the same defect facing the other way.
#:
#: **A home ending in `/` is a directory prefix; any other home is one exact
#: path.** `guardrail` is the exact kind (M09b PR 3, SPEC/09b's fourth rule gap).
#: It pointed at `platform/gateway/`, where no guardrail is defined, and measured
#: there `platform/infra/lib/gateway-stack.ts` read *admissible: False* and
#: `platform/gateway/policy/tools.contracts.json` read *admissible: True*
#: (ADR-076 decision 4). The home is now the one file the stack synthesizes the
#: guardrail from, and the directory is dropped rather than kept beside it. The
#: walker below reads a topic definition out of whatever file the home admits, so
#: a home wider than that file would let a topic defined anywhere else walk clean.
#:
#: **The home and the walker land in one diff, because neither is safe alone.**
#: The home widened with no walker makes a guardrail control on the stack file
#: WALKED at exit 0 whatever its `selector` says. That is a control admissible
#: with nothing reading it, and ADR-076 decision 4 calls it a relaxation of row
#: 1a. The walker with no widened home is unreachable, because the stack file is
#: refused before the walk starts.
CONTROL_ARTIFACTS = {
    "eval_pack": ("services/", (".yaml", ".yml")),
    "guardrail": ("platform/infra/lib/gateway-stack.ts", (".ts",)),
    "cedar_policy": ("platform/gateway/", (".cedar", ".json")),
    "classification": ("platform/gateway/core/", (".py",)),
}

#: Where the frozen corpora a guardrail topic is measured against live.
CORPORA = "quality/adversarial/"

#: The row fields that NAME a guardrail topic, read by equality and never by
#: substring. Two spellings are committed: `phrasings.yaml` writes `topic:`, and
#: `topic-attacks-heldout.yaml` writes `act:` for the topic its row targets. A
#: substring match would let `selector: entitlement` claim every row of both
#: entitlement topics.
ROW_TOPIC_FIELDS = ("topic", "act")

#: Where the test that asserts a corpus lives.
TESTS = "tests/"

#: A DENY topic as `gateway-stack.ts` declares one: `name`, then `type: 'DENY'`,
#: then `definition`, read after comment lines are removed so a topic that exists
#: only in a comment is not defined.
DENY_TOPIC = re.compile(r"name:\s*'([^']+)',\s*type:\s*'DENY',\s*definition:")


def _at_home(ref: str, home: str) -> bool:
    """A `/`-terminated home admits every path under it; any other home admits
    exactly itself."""
    return ref.startswith(home) if home.endswith("/") else ref == home


def _deny_topics(path: pathlib.Path) -> set[str]:
    """The DENY topics a stack file defines, with `//` and `/* */` comments removed."""
    text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))
    return set(DENY_TOPIC.findall(code))


def _rows(node: object):
    """Every corpus row in a parsed corpus: a mapping carrying `id` and `expect`,
    at any depth, because the corpora nest their rows differently (`phrasings:`,
    `heldout:`, `pairs[].block`)."""
    if isinstance(node, dict):
        if "id" in node and "expect" in node:
            yield node
        for value in node.values():
            yield from _rows(value)
    elif isinstance(node, list):
        for value in node:
            yield from _rows(value)


def _tests_reading(corpus: str, root: pathlib.Path) -> list[str]:
    """The test modules that read `corpus`, found structurally: a module under
    `tests/` defining at least one `test_` function and carrying the corpus's file
    name or path as a string constant. A comment or a docstring sentence naming the
    file is not a read, which is why this parses rather than searches."""
    wanted = {corpus, pathlib.PurePosixPath(corpus).name}
    found = []
    for module in sorted((root / TESTS).glob("test_*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        tests = [n for n in tree.body
                 if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        docstrings = {id(n.body[0].value) for n in [tree, *tests]
                      if n.body and isinstance(n.body[0], ast.Expr)
                      and isinstance(n.body[0].value, ast.Constant)}
        constants = {n.value for n in ast.walk(tree)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str)
                     and id(n) not in docstrings}
        if tests and constants & wanted:
            found.append(module.relative_to(root).as_posix())
    return found


def _walk_guardrail(rule_id: str, control: dict, ref: str, path: pathlib.Path,
                    root: pathlib.Path) -> tuple[list[Step], list[str]]:
    """Guardrail artifact -> `selector` -> the corpus rows naming that topic -> the
    test that reads them (ADR-076 decision 4; SPEC/09b PR 3).

    Every link is read out of the tree, and a missing one is a defect, never a
    WALKED step. WALKED was the honest state while no walker existed. Once one
    does, a guardrail control that stops short of a test is a chain that did not
    resolve."""
    steps: list[Step] = []
    selector = control.get("selector")
    if not isinstance(selector, str) or not selector.strip():
        steps.append(Step("topic", "—", "no selector", resolved=False))
        return steps, [
            f"{rule_id}: the guardrail control at {ref!r} names no `selector`. A guardrail "
            f"holds several topics, and a control that does not say which one is a claim "
            f"about all of them that nothing walks."]

    defined = _deny_topics(path)
    if selector not in defined:
        steps.append(Step("topic", selector, f"not defined in {ref}", resolved=False))
        return steps, [
            f"{rule_id}: the guardrail control names topic {selector!r}, and {ref} defines "
            f"no DENY topic by that name (it defines {sorted(defined)})."]
    steps.append(Step("topic", selector, f"DENY topic defined in {ref}"))

    defects: list[str] = []
    naming = {}
    for corpus in sorted((root / CORPORA).glob("*.yaml")):
        rows = [row for row in _rows(yaml.safe_load(corpus.read_text(encoding="utf-8")))
                if any(row.get(field) == selector for field in ROW_TOPIC_FIELDS)]
        if rows:
            naming[corpus.relative_to(root).as_posix()] = rows
    if not naming:
        steps.append(Step("rows", CORPORA, f"no row names {selector!r}", resolved=False))
        return steps, [
            f"{rule_id}: no row under {CORPORA} names topic {selector!r} in "
            f"{' or '.join(ROW_TOPIC_FIELDS)}. A guardrail control that no frozen row "
            f"measures is a claim with no reading behind it."]

    for corpus, rows in naming.items():
        blocked = sum(1 for row in rows if row.get("expect") == "blocked")
        allowed = sum(1 for row in rows if row.get("expect") == "allowed")
        steps.append(Step("rows", corpus, f"{len(rows)} name this topic "
                                          f"({blocked} blocked, {allowed} allowed)"))
        readers = _tests_reading(corpus, root)
        if not readers:
            steps.append(Step("asserted", corpus, "no test reads this corpus", resolved=False))
            defects.append(
                f"{rule_id}: {corpus} holds rows naming topic {selector!r}, and no test under "
                f"{TESTS} reads that file. Rows nothing asserts are rows, not a control.")
            continue
        for reader in readers:
            steps.append(Step("asserted", reader, f"reads {corpus}"))
    return steps, defects


@dataclass(frozen=True)
class Step:
    """One link of the chain, and what reading it established."""

    kind: str
    ref: str
    detail: str = ""
    resolved: bool = True
    #: A step that was located and walked as far as its control type permits, but
    #: reached no assert. Not a defect and not a resolution: `pave rules trace`
    #: exits 0 on a chain whose only shortfall is `walked`, and `Chain.resolved`
    #: stays false so that RESOLVED keeps meaning "a reader reached an assert".
    walked: bool = False


@dataclass(frozen=True)
class Chain:
    """A walk from one rule to the asserts its controls land in."""

    rule_id: str
    rule: dict | None = None
    steps: list[Step] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        """True only when every link was read out of the tree.

        **Every step, not just the absence of defects.** The first version of
        this was `bool(self.rule) and not self.defects and bool(self.steps)`, and
        it printed `chain: RESOLVED` over `MER-AI-0001` as committed -- a rule
        whose only disposition is an honest `no-control` record, whose walk stops
        at the control and reaches no case and no assert. Not a defect, correctly;
        but not a resolved chain either, and reporting one would have made the
        registry lookup report success over the undisposed state the whole
        milestone exists to change. An empty walk with no defect is the same
        vacuous pass one field over.
        """
        return (bool(self.rule) and not self.defects and bool(self.steps)
                and all(s.resolved for s in self.steps))

    @property
    def walked(self) -> bool:
        """Every link located, with at least one control the walk cannot follow
        further.

        The middle state between RESOLVED and broken. A `guardrail` or
        `cedar_policy` disposition is enforcing and correctly recorded, and the
        reader has no walker for it — so the chain is not a defect and it is not
        a proof of row 1a either."""
        return (bool(self.rule) and not self.defects and bool(self.steps)
                and not self.resolved
                and all(s.resolved or s.walked for s in self.steps))


def load_registry(registry: pathlib.Path = REGISTRY) -> dict[str, dict]:
    """Every committed rule, keyed by its id.

    An empty registry raises rather than returning `{}`, for the reason
    `rules_validate` gives: a reader that reports success over zero files reports
    success after somebody deletes the directory."""
    if yaml is None:  # pragma: no cover - the CLI dies before reaching here
        raise RuntimeError("pyyaml not installed; pip install pyyaml")
    files = sorted(registry.glob("*.yaml"))
    if not files:
        raise FileNotFoundError(
            f"no rule files found in {registry} — an empty rules registry is a failure, "
            "not a pass (G7)"
        )
    rules = {}
    for path in files:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and doc.get("rule"):
            rules[doc["rule"]] = doc
    return rules


def enforcing_controls(rule: dict) -> list[dict]:
    """The controls whose `ref` is a path, not prose.

    The `no-control` filter is the whole of the difference between orphaning and
    a recorded decision not to enforce, so it is one function that both
    `orphan_rules` and `trace` call rather than two `!=` comparisons that can
    drift apart."""
    controls = (rule.get("disposition") or {}).get("controls") or []
    return [c for c in controls if isinstance(c, dict) and c.get("type") != NO_CONTROL]


def orphan_rules(registry: pathlib.Path = REGISTRY, root: pathlib.Path = ROOT) -> list[str]:
    """Every orphan rule in the registry, in `rules/schema.json`'s one sense.

    **An orphan rule is a rule whose disposition names an enforcing control --
    any `controls[].type` other than `no-control` -- whose `ref` does not resolve
    to a path in this tree.** The rule is written down, the control is named, and
    the control is not there.

    That is the schema's `description` word for word, and it is the only sense
    this repository uses. The other sense the term used to carry -- a rule
    missing an owner, a disposition or a review-by date -- is enforced by the
    schema's `required` and by `minItems`, and is not called orphaning here,
    because a term meaning two things lets the cheap half be closed while the
    expensive half is reported as done (ADR-053, ADR-075 amendment 2).

    Returns problem strings rather than raising: `rules_validate` collects them
    beside the schema's, so one command reports both halves of G7.
    """
    problems = []
    for rule_id, rule in sorted(load_registry(registry).items()):
        for control in enforcing_controls(rule):
            ref = control.get("ref") or ""
            if not _resolves(ref, root):
                problems.append(
                    f"{rule_id}: orphan rule — the disposition names a "
                    f"{control.get('type')!r} control at {ref!r} and no such path exists in "
                    f"this tree. A named control that is not there is a stated protection "
                    f"that is absent, which is worse than a missing one."
                )
    return problems


def _resolves(ref: str, root: pathlib.Path) -> bool:
    """Whether a control `ref` names something in this tree.

    Anchored at the repository root and refused if it escapes: `../../etc/passwd`
    resolving would make every rule non-orphaned by pointing outside. `strict` is
    off because the point is to answer whether it exists, not to raise when it
    does not."""
    if not ref or not isinstance(ref, str):
        return False
    candidate = (root / ref).resolve()
    # `!= root` too: `ref: "."` resolves to the repository root, exists, and
    # discharged every rule. A control that is "the whole repository" is not a
    # control (Tool Owner and Legal/S&P, round 2).
    if root.resolve() not in candidate.parents or candidate == root.resolve():
        return False
    if not candidate.exists():
        return False
    # **Against the committed tree, not the filesystem.** `SERVICES/…/CASES.YAML`
    # and a ref with a trailing space both resolve on a Windows checkout and would
    # not on Linux CI, so "no orphan rules" meant two different things by
    # platform. A ref must be byte-identical to a path that is actually there.
    try:
        relative = candidate.relative_to(root.resolve()).as_posix()
    except ValueError:  # pragma: no cover - the containment check above precedes this
        return False
    return relative == ref.strip("/") and (root / relative).exists()


def _control_types() -> set:
    """The `controls[].type` enum, read out of `rules/schema.json`.

    One authority. A copy of an enum in the reader is the second vocabulary site
    ADR-045 decision 7 closed one file over: the narrower gate wins at runtime,
    which is exactly what makes that shape survive review."""
    import json
    schema = json.loads((ROOT / "rules" / "schema.json").read_text(encoding="utf-8"))
    controls = schema["properties"]["disposition"]["properties"]["controls"]
    return set(controls["items"]["properties"]["type"]["enum"])


def _pack_cases(path: pathlib.Path) -> list[dict]:
    """The cases in an eval pack, or `[]` if it does not hold a case list.

    **Case SHAPE, not "a YAML list of mappings."** The looser reading reported a
    real `.yml` guardrail config — also a list of mappings — as "reads as an eval
    pack", so a correct disposition rendered BROKEN (Tool Owner, round 2). An
    eval pack is a list of cases, and a case carries `id` and `asserts`; that is
    what `run_with_tools.py` validates one directory over."""
    if yaml is None:  # pragma: no cover
        return []
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, list):
        return []
    # An `id` makes it a case. The assert-less case keeps its OWN defect one
    # level down — folding it in here would report "holds no cases" for a pack
    # that holds one, which names the wrong link.
    return [c for c in doc if isinstance(c, dict) and c.get("id")]


def _binds(ref: str) -> str | None:
    """The service a control's path binds the rule to, read off the path.

    `services/<name>/...` and nothing else. Returning `None` rather than guessing
    is the point: the demo prints `binds <service>`, and a reader that inferred
    the only deployed service would print the right answer today and a wrong one
    the day there are two."""
    parts = pathlib.PurePosixPath(ref).parts
    return parts[1] if len(parts) > 2 and parts[0] == "services" else None


def trace(rule_id: str, registry: pathlib.Path = REGISTRY,
          root: pathlib.Path = ROOT) -> Chain:
    """Walk one rule to the asserts its controls land in.

    Every link is read; none is supplied. A ref that does not resolve stops that
    control's walk with a defect naming it, and the walk does **not** fall back
    to a conventional pack path -- a reader that does makes a broken disposition
    render exactly like a working one, which is the plant this reader was written
    against."""
    steps: list[Step] = []
    defects: list[str] = []

    rules = load_registry(registry)
    rule = rules.get(rule_id)
    if rule is None:
        return Chain(rule_id, None, [], [
            f"{rule_id}: no such rule in the registry. Known: {sorted(rules)}."
        ])

    source = rule.get("source") or {}
    steps.append(Step("source", f"{source.get('type')} - {source.get('ref')}"))
    steps.append(Step(
        "owner",
        f"{rule.get('owner_seat')}",
        f"status {rule.get('status')}        review_by {rule.get('review_by')}",
    ))

    # **The scope, printed before the controls.** A rule re-scoped by its owning
    # seat is a decision a reader of the lookup must meet, and `title` is not it:
    # a scope narrowed by a quiet edit to the title cannot be audited, and the
    # excluded sense and its revival condition exist nowhere a reader looks.
    scope = rule.get("scope") or {}
    if scope:
        steps.append(Step("scope", str(scope.get("covers", "")).strip(),
                          f"{scope.get('decided_by')} {scope.get('decided_on')}"))
        steps.append(Step("excludes", str(scope.get("excludes", "")).strip()))
        steps.append(Step("revives", str(scope.get("revives", "")).strip()))

    # **The boundary, printed with the chain.** A disposition that records what
    # it does not reach is worth nothing if the lookup omits it: the registry
    # would carry the limit and `pave rules trace` would still show an unqualified
    # chain, which is the reading a human takes away. `resolved` is unaffected —
    # a limit is a recorded boundary, not a defect — but it is never silent.
    for limit in (rule.get("disposition") or {}).get("limits") or []:
        steps.append(Step("limit", str(limit.get("limit", "")).strip(),
                          f"owed to {', '.join(limit.get('owed_to') or [])} — "
                          f"{limit.get('dated')}"))

    controls = (rule.get("disposition") or {}).get("controls") or []
    enforcing = enforcing_controls(rule)
    if not enforcing:
        # Not a defect. An explicit reasoned `no-control` record is a disposition
        # the schema permits, and MER-AI-0001 has carried one since M00a on
        # purpose. The walk stops here and SAYS it stops here.
        for control in controls:
            steps.append(Step(
                "control", f"{control.get('type')}  {control.get('ref')}",
                "no enforcing control yet — undisposed BY DESIGN, not broken; "
                "the disposition PR replaces this record", resolved=False,
            ))
        return Chain(rule_id, rule, steps, defects)

    for control in enforcing:
        ref = control.get("ref") or ""
        layer = control.get("layer") or ""
        label = f"{control.get('type')}  {ref}" + (f"  {layer}" if layer else "")
        if control.get("type") == "guardrail" and control.get("selector"):
            label += f"  selector {control.get('selector')}"
        if not _resolves(ref, root):
            steps.append(Step("control", label, "does not resolve", resolved=False))
            defects.append(
                f"{rule_id}: orphan rule — the disposition names a "
                f"{control.get('type')!r} control at {ref!r} and no such path exists in "
                f"this tree."
            )
            continue
        steps.append(Step("control", label))

        service = _binds(ref)
        if service:
            steps.append(Step("binds", service))
        else:
            # **Stated, not silent.** A ref outside `services/` resolves fine and
            # binds to no service; printing nothing left a reader of the demo
            # artifact looking at a chain with no binding and no note that there
            # was one to make (Tool Owner, round 1).
            steps.append(Step("binds", "—", "no service in this path — the rule binds "
                                            "to the platform, not to a service"))

        path = (root / ref).resolve()
        kind = control.get("type")
        looks_like_pack = (not path.is_dir() and path.suffix in (".yaml", ".yml")
                           and bool(_pack_cases(path)))

        # **The declared type must be one the schema permits.** Read from the
        # schema rather than restated here, which is the discipline `orphan_rules`
        # already follows: two copies of an enum drift, and the narrower one wins
        # silently at runtime.
        if kind not in _control_types():
            steps.append(Step("control", label, f"type {kind!r} is not in the schema's "
                                                f"enum", resolved=False))
            defects.append(
                f"{rule_id}: the disposition declares a control of type {kind!r}, which "
                f"`rules/schema.json` does not permit. A control the registry cannot name "
                f"is not a control it can be said to have.")
            continue

        home, suffixes = CONTROL_ARTIFACTS.get(kind, (None, None))
        if home and not (_at_home(ref, home) and path.suffix in suffixes):
            steps.append(Step("control", label, f"declared {kind!r}; its artifact is not "
                                                f"one", resolved=False))
            defects.append(
                f"{rule_id}: the control at {ref!r} is declared {kind!r}, whose artifact "
                f"lives under {home!r} with suffix {suffixes}. A disposition that names "
                f"one kind of control and points at another reports a chain it did not "
                f"walk — G4's *a probe naming Cedar is not satisfied by a content filter*, "
                f"one plane over.")
            continue

        if kind == "guardrail":
            # **The walker (M09b PR 3).** A guardrail control resolves or is a
            # defect; it is never WALKED. See `CONTROL_ARTIFACTS` for why the home
            # and this branch land together.
            walked_steps, walked_defects = _walk_guardrail(rule_id, control, ref, path, root)
            steps.extend(walked_steps)
            defects.extend(walked_defects)
            continue

        if kind != "eval_pack":
            # **Dispatch on the declared TYPE, never on the file extension**
            # (Tool Owner, round 1). Two things were wrong when this branch keyed
            # off `path.suffix`:
            #
            # A `guardrail` or `cedar_policy` control — enforcing, correctly
            # disposed — produced a `resolved=False` step, so `Chain.resolved`
            # went false with **zero defects** and `pave rules trace` exited 1.
            # Adding a second, genuinely stronger control turned a chain that
            # exits 0 into one that exits 1: M09b would have made claim 6's own
            # command red by strengthening the control it reports on.
            #
            # And the converse was worse. `type: cedar_policy` pointing at the
            # eval pack reported RESOLVED at exit 0 and printed five L3 eval cases
            # as a Cedar policy's chain — the `type` and `layer` enums decorative
            # in the one reader that claims to walk them. That is G4's *a probe
            # naming Cedar is not satisfied by a content filter*, one plane over.
            if looks_like_pack:
                steps.append(Step("control", ref, f"declared {kind!r} but reads as an "
                                                  f"eval pack", resolved=False))
                defects.append(
                    f"{rule_id}: the control at {ref!r} is declared {kind!r} and its "
                    f"artifact is an eval pack. A disposition that names one kind of "
                    f"control and points at another reports a chain it did not walk.")
                continue
            # **Located, and walked as far as this type permits — which is a THIRD
            # state, not RESOLVED.** Round 2 pulled this in two directions and
            # both were right. Tool Owner: a `guardrail` or `cedar_policy` control
            # is enforcing, so it must not make the chain read as unresolved, or
            # M09b makes claim 6's command red by strengthening the control.
            # Platform Engineering: reporting RESOLVED for a walk that reached no
            # case and no assert relaxes what row 1a proves, and that is a cut
            # needing an ADR.
            #
            # `walked` satisfies both. The chain is not broken (no defect, and
            # `pave rules trace` does not exit 1 on it) and it is not RESOLVED
            # either: `Chain.resolved` still means *a reader got from the rule to
            # an assert*, which is the sentence claim 6 rests on.
            steps.append(Step(kind, ref, "located; this control type has no deeper "
                                         "walk built — the chain is WALKED, not "
                                         "resolved", resolved=False, walked=True))
            continue

        if path.is_dir() or path.suffix not in (".yaml", ".yml"):
            steps.append(Step("cases", ref, "declared 'eval_pack' and is not a case "
                                            "file", resolved=False))
            defects.append(
                f"{rule_id}: the control at {ref!r} is declared an eval pack and is not "
                f"one. The disposition names a control the artifact is not.")
            continue

        cases = _pack_cases(path)
        if not cases:
            steps.append(Step("cases", ref, "holds no cases", resolved=False))
            defects.append(
                f"{rule_id}: the control at {ref!r} holds no cases. A pack with nothing "
                f"in it satisfies every assertion about it and measures nothing."
            )
            continue

        for case in cases:
            keys = sorted({k for a in case.get("asserts") or [] for k in a})
            if not keys:
                defects.append(
                    f"{rule_id}: case {case.get('id')!r} in {ref} carries no asserts. A "
                    f"case that asserts nothing passes every run."
                )
            steps.append(Step("case", str(case.get("id")), ", ".join(keys),
                              resolved=bool(keys)))

    return Chain(rule_id, rule, steps, defects)


def render(chain: Chain) -> str:
    """The chain, as `pave rules trace` prints it.

    Teaches rather than reports (claim 2): every line names what was read and
    where, and a defect is printed as a line of the walk rather than as a summary
    that leaves the reader to find which link broke."""
    if chain.rule is None:
        return "\n".join(f"  [BROKEN] {d}" for d in chain.defects)

    lines = [f"{chain.rule_id}  {chain.rule.get('title')}"]
    for step in chain.steps:
        mark = "        " if step.resolved else "  <-- "
        if step.kind in ("limit", "scope", "excludes", "revives"):
            # **Wrapped, and the boundary is the one step that earns the room.**
            # A limit is prose a human has to read, and a 500-character line in a
            # terminal is a line nobody reads — which would make printing it a
            # gesture rather than a disclosure.
            import textwrap
            # `.splitlines()[0]`: `detail` interpolates `limits[].dated`, an
            # unconstrained string. A newline in it injected arbitrary lines into
            # the render -- the Security seat produced a false `chain: RESOLVED`
            # line in the middle of a broken chain's output. The defect line and
            # the real trailer both survived, so it misleads a reader rather than
            # the gate; that is still the render's job to prevent.
            detail = (step.detail or "").splitlines()[0] if step.detail else ""
            mark = "" if step.resolved else "  <-- "
            lines.append(f"  {step.kind:<10} {detail}{mark}".rstrip())
            lines.extend(textwrap.wrap(step.ref, width=76,
                                       initial_indent=" " * 15, subsequent_indent=" " * 15))
            continue
        detail = f"{mark}{step.detail}" if step.detail else ""
        lines.append(f"  {step.kind:<10} {step.ref}{detail}")

    cases = [s for s in chain.steps if s.kind == "case"]
    if cases:
        lines.append(f"  {'cases':<10} {len(cases)}")
    for defect in chain.defects:
        lines.append(f"  [BROKEN] {defect}")
    lines.append("")
    state = "RESOLVED" if chain.resolved else ("WALKED" if chain.walked else "NOT RESOLVED")
    lines.append(f"chain: {state}")
    return "\n".join(lines)
