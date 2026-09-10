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

import pathlib
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


@dataclass(frozen=True)
class Step:
    """One link of the chain, and what reading it established."""

    kind: str
    ref: str
    detail: str = ""
    resolved: bool = True


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
    if root.resolve() not in candidate.parents and candidate != root.resolve():
        return False
    return candidate.exists()


def _pack_cases(path: pathlib.Path) -> list[dict]:
    """The cases in an eval pack, or `[]` if it holds none."""
    if yaml is None:  # pragma: no cover
        return []
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [c for c in doc if isinstance(c, dict)] if isinstance(doc, list) else []


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
            # Located, and walked as far as this type permits. RESOLVED: a control
            # that is enforcing must not make the chain read as unresolved.
            steps.append(Step(kind, ref, "located; the deeper walk for this control "
                                         "type is not built"))
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
        detail = f"{mark}{step.detail}" if step.detail else ""
        lines.append(f"  {step.kind:<10} {step.ref}{detail}")

    cases = [s for s in chain.steps if s.kind == "case"]
    if cases:
        lines.append(f"  {'cases':<10} {len(cases)}")
    for defect in chain.defects:
        lines.append(f"  [BROKEN] {defect}")
    lines.append("")
    lines.append(f"chain: {'RESOLVED' if chain.resolved else 'NOT RESOLVED'}")
    return "\n".join(lines)
