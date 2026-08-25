"""What a service manifest must satisfy, and what to say when it does not.

**Mechanism only.** Every number, level and vocabulary refused on here is imported
from `pave/floors.py`, which carries its content owner's key — the line
`pave/gate.py`'s docstring draws and ADR-045 kept: Platform Engineering owns the
code that reads a criterion, AI Quality owns the criterion that produces a FAIL.
Grep this file for a literal threshold and there is none.

**Why a verifier at all.** `pave.manifest.yaml` is a ten-field file that the
repository read and never checked. Measured on `6af17d2`: deleting **six of the
ten** fields is *1861 passed, zero failures*, and the four that went red went red
incidentally — a `KeyError` raised by a test reading the field for some other
purpose, never a refusal naming it. `gates.eval_min_cases: 20 -> 0`, the
milestone's opening finding, was green.

**The refusal table is the commitment** (`ROWS` below, SPEC/05 item 29). Anything
not in it is deferred by name rather than by silence, and the deferrals are listed
in `DEFERRED`.

**What this does not do.** It does not run at deploy time and it does not make
`attestations.manifest_signature` true. ADR-046 records that cut.

Hermetic (G8): reads committed files, calls no model, opens no socket.
Owning seats: Platform Engineering (this file) · AI Quality + Security (the
criteria it imports).
"""
from __future__ import annotations

import dataclasses
import pathlib

import yaml

from pave import floors

ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVICES = ROOT / "services"
REGISTRY = ROOT / "platform" / "registry" / "tools.yaml"

#: The file this module verifies, and the glob that finds every one of them.
#:
#: **The glob is load-bearing.** No test in this repository enumerated
#: `services/*` before ADR-046, and both CI evaluation steps are hard-coded to
#: `highlights-agent` — so a service the repository had never heard of stayed
#: invisible, which is the premise M05 exists to remove. `services()` below is the
#: only way in, and `tests/test_manifest_verify.py` asserts its result is non-empty
#: (a glob that matches nothing verifies nothing, silently and forever).
MANIFEST_NAME = "pave.manifest.yaml"

#: Where a service's golden pack lives, relative to the service directory.
GOLDEN_PACK = ("evals", "golden", "cases.yaml")

#: The one shape this file is read under.
API_VERSION = "pave/v1"

#: ADR-003's declared values, so a runtime move is a manifest edit.
RUNTIMES = ("lambda", "ecs", "agentcore")

#: The ten fields, and **the thing that reads each one**. The refusal names the
#: reader, because "required" with no reader is a rule nobody can argue with — and
#: six of these ten were deletable at zero failures precisely because no reader was
#: ever named.
#:
#: Dotted paths are nested requirements. `owners.oncall` with no value is a red
#: gate that reaches nobody, which is the same outage as no `owners` block at all.
REQUIRED_FIELDS = {
    "apiVersion":
        "this verifier — it decides which shape the file is read under, and there "
        f"is exactly one ({API_VERSION!r}).",
    "service":
        "the directory match (row 7) and both halves of the Cedar grant check "
        "(rows 3 and 4): `callers:` in the registry names services, so with no "
        "`service` there is no name to match a grant against.",
    "template":
        "the scaffold's provenance — which revision of `templates/agent-tools/` "
        "rendered this tree, and therefore what a template fix does and does not "
        "reach.",
    "brand":
        "`evals/judge.py` — the rubric axis `brand_tone:<brand>` every judged case "
        "is scored against. A brand with no axis is a service nothing can judge.",
    "classification":
        "`classify.route`'s `declared` argument (G5), against the declarable "
        "vocabulary in `pave/floors.py`.",
    "owners.team":
        "the pager. A red gate with no team reaches nobody.",
    "owners.oncall":
        "the pager. `webhook:<name>` is the miniature of PagerDuty (ADR-007).",
    "runtime":
        f"ADR-003's migration path, one of {list(RUNTIMES)} — so a runtime move is "
        "a manifest edit rather than a rewrite.",
    "tools":
        "the Cedar grant bijection (rows 2, 3 and 4). The registry generates policy "
        "from `callers:`; this list is the other half, and nothing compared them.",
    "gates.eval_min_cases":
        "the floor beneath which a service deploys unevaluated (rows 8 and 10).",
    "gates.budgets":
        "the per-suite ceilings the eval runner and `tests/test_contracts.py` "
        "decide on (row 12).",
    "attestations":
        "CI writes these and the deploy is supposed to verify them. ADR-046 records "
        "that nothing verifies `manifest_signature` here, and this field is a "
        "placeholder with a stated reason rather than a silent one.",
}

#: The refusal table, as the code that produces it rather than as prose beside it.
#:
#: `tests/test_manifest_verify.py` iterates this dict and requires a distinct
#: producer for every row, so a row added here with no producer is red — the shape
#: this repository has recorded eight times as "a stated protection is worse than
#: an absent one, because it stops anyone looking for the real one".
ROWS = {
    1: "duplicate YAML key",
    2: "tool id not in the registry",
    3: "declared tool the service is not a `caller:` of",
    4: "registry grant with no matching declaration",
    5: "missing required field",
    6: "`classification` outside the declarable vocabulary",
    7: "`service` does not match its directory name",
    8: "golden pack below the platform case floor",
    9: "golden pack outside the headroom band",
    10: "`gates.eval_min_cases` below the platform floor",
    11: "unknown top-level key in a golden case",
    12: "`gates.budgets` missing a key",
    13: "duplicated registry id",
    14: "`brand` outside the set the judge can score",
}

#: Deferred **by name**, which is the whole of the commitment item 29 makes.
DEFERRED = {
    "range evaluation":
        "`@^0` and the registry's `semver:` are decorative. A grep for `\"semver\"` "
        "across the Python sources returns no matches, the one site parsing `@` "
        "throws the range away, and a manifest reading "
        "`catalog-search@not-a-range-at-all` with `semver:` deleted from every "
        "registry entry is `--check` exit 0 at 1861 passed. This verifier checks the "
        "id and says so in its own output. A range evaluator is M06's, or the field "
        "goes (SPEC/05 item 22).",
    "brand-with-no-pack":
        "row 14 refuses a brand the judge cannot score; it does not build the pack "
        "that would make a second brand scoreable. One fictional news title is 16 "
        "failed, because the catalog is embedded model-facing in the judge prompt "
        "and digested into `quality/judge/frozen.json`. The second brand is M08's.",
    "whether the declaration is honest":
        "`classification` is a declaration the repository refuses to merge when it "
        "is outside the vocabulary. `handler.py:309` still takes `declared` from the "
        "event, so this is a control on the repository and not on the runtime, and "
        "it is not a claim that the repository can tell a truthful declaration from "
        "a convenient one.",
}


@dataclasses.dataclass(frozen=True)
class Finding:
    """One refusal. `row` indexes `ROWS`; `where` is the file or field at fault."""

    row: int
    where: str
    message: str

    def render(self) -> str:
        return f"  [row {self.row:>2}] {self.where}\n           {self.message}"


class DuplicateKey(ValueError):
    """Row 1. Carries both line numbers, because "duplicate key `gates`" without
    them sends a reader to the first occurrence, which is the one that lost."""

    def __init__(self, key: object, first_line: int, second_line: int) -> None:
        self.key, self.first_line, self.second_line = key, first_line, second_line
        super().__init__(
            f"duplicate key {key!r} at line {second_line}; it was already set at line "
            f"{first_line}. YAML keeps the LAST value silently, so the block a reader "
            "finds first is the one that does not apply.")


class DuplicateRegistryId(ValueError):
    """Row 13, from the verifier's side. `cedar.generate()` produces it from the
    deploy side (ADR-044); both are needed, because they answer different questions
    — that one stops a phantom principal reaching the policy set, this one stops the
    verifier deciding rows 3 and 4 against whichever entry happened to come last."""

    def __init__(self, tool_id: str, first: int, second: int) -> None:
        self.tool_id, self.first, self.second = tool_id, first, second
        super().__init__(
            f"duplicate tool id {tool_id!r} in {REGISTRY.name}, at entries {first} and "
            f"{second}. The registry decides who may call a tool (ADR-004) and it "
            "cannot decide twice: this verifier would read `callers:` from whichever "
            "entry came last, and `cedar.generate()` would put a principal in the "
            "deployed policy set that no manifest names. Remove one entry.")


class _NoDuplicateKeys(yaml.SafeLoader):
    """PyYAML only — no new dependency, which CLAUDE.md would want a line about.

    `yaml.safe_load` resolves a duplicated key to its last value without a word.
    That is how a manifest can carry two `gates:` blocks, pass every check in this
    module against the second, and read to a human as the first."""

    def construct_mapping(self, node, deep=False):
        seen: dict[object, int] = {}
        for key_node, _value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            line = key_node.start_mark.line + 1
            if key in seen:
                raise DuplicateKey(key, seen[key], line)
            seen[key] = line
        return super().construct_mapping(node, deep=deep)


def load(path: pathlib.Path) -> object:
    """Parse `path`, refusing duplicate keys anywhere in it (row 1)."""
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_NoDuplicateKeys)


def services() -> list[pathlib.Path]:
    """Every directory under `services/` holding a manifest, sorted.

    **The premise M05 removes lives in this function.** Before it, nothing in the
    repository enumerated `services/*`: both CI eval steps name `highlights-agent`
    literally, and a second service could be added with a broken manifest and no
    check would look at it. A caller that hard-codes a service name instead of
    calling this has re-created that, so `pave verify --all` has no other path and
    the test asserts this returns something."""
    if not SERVICES.is_dir():
        return []
    return sorted(d for d in SERVICES.iterdir() if (d / MANIFEST_NAME).is_file())


def grants(registry: list[dict]) -> dict[str, list[str]]:
    """`{tool id: [services the registry grants it to]}`, refusing a repeated id."""
    seen: dict[str, int] = {}
    out: dict[str, list[str]] = {}
    for index, tool in enumerate(registry):
        tool_id = tool["id"]
        if tool_id in seen:
            raise DuplicateRegistryId(tool_id, seen[tool_id], index)
        seen[tool_id] = index
        out[tool_id] = list(tool.get("callers") or [])
    return out


def _get(mapping: object, dotted: str):
    """`a.b` out of nested mappings, or `None` at the first hop that is not there."""
    cursor = mapping
    for part in dotted.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return None
        cursor = cursor[part]
    return cursor


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def verify(directory: pathlib.Path, registry: list[dict] | None = None) -> list[Finding]:
    """Every refusal `directory`'s manifest earns, in table order.

    **All of them, not the first.** A verifier that stops at the first fault makes a
    team's onboarding a sequence of single-fault round trips, and the round trip is
    the cost the paved road exists to remove. The one exception is a manifest that
    will not parse: there is nothing to check the rest of."""
    findings: list[Finding] = []
    path = directory / MANIFEST_NAME
    rel = _rel(path)

    try:
        manifest = load(path)
    except DuplicateKey as exc:
        return [Finding(1, rel, str(exc))]
    except yaml.YAMLError as exc:
        return [Finding(1, rel, f"this file is not valid YAML: {exc}")]
    if not isinstance(manifest, dict):
        return [Finding(5, rel, f"the manifest parsed as {type(manifest).__name__}, not a "
                                "mapping, so no field can be read from it.")]

    for field, reader in REQUIRED_FIELDS.items():
        if _get(manifest, field) is None:
            findings.append(Finding(5, f"{rel}:{field}", f"required, and read by {reader}"))

    findings += _check_identity(manifest, directory, rel)
    findings += _check_tools(manifest, rel, registry)
    findings += _check_gates(manifest, rel)
    findings += _check_pack(manifest, directory)
    return sorted(findings, key=lambda f: (f.row, f.where))


def _check_identity(manifest: dict, directory: pathlib.Path, rel: str) -> list[Finding]:
    """Rows 5, 6, 7 and 14 — what the service says it is."""
    findings = []
    service = manifest.get("service")
    if service is not None and service != directory.name:
        findings.append(Finding(
            7, f"{rel}:service",
            f"declares {service!r} but sits in `services/{directory.name}/`. The "
            "registry's `callers:` names services, so the grant check would ask "
            f"about {service!r} while the deploy path uses {directory.name!r} — and "
            "one of the two would be checked against a service that does not exist."))

    declared = manifest.get("classification")
    if declared is not None and declared not in floors.DECLARABLE_LEVELS:
        detail = (
            " Measured over all 25 committed golden cases, a service declaring "
            "`public` is allowed **0 of 25** — `route` refuses every request that "
            "classifies above the declaration, so this is an outage and not a "
            "tightening. Do not read it as the safe choice."
            if declared == "public" else
            " `sensitive` is refused by G5 by design; `confidential` is behaviourally "
            "identical to `internal` and no detector produces it (ADR-045)."
            if declared in ("sensitive", "confidential") else "")
        findings.append(Finding(
            6, f"{rel}:classification",
            f"declares {declared!r}; the declarable vocabulary is "
            f"{list(floors.DECLARABLE_LEVELS)} (`pave/floors.py`, ADR-045).{detail}"))

    brand = manifest.get("brand")
    if brand is not None and brand not in floors.SUPPORTED_BRANDS:
        findings.append(Finding(
            14, f"{rel}:brand",
            f"declares {brand!r}; the judge can score {list(floors.SUPPORTED_BRANDS)}. "
            "A brand is supported when the rubric under `quality/judge/` carries a "
            f"`brand_tone:{brand}` axis — `evals/judge.py` raises without it, so every "
            "judged case in this service would be scored against a rubric that does "
            "not mention it. Building a second brand pack is M08's (ADR-046)."))

    api = manifest.get("apiVersion")
    if api is not None and api != API_VERSION:
        findings.append(Finding(
            5, f"{rel}:apiVersion",
            f"reads {api!r}; this verifier knows one shape, {API_VERSION!r}. A file "
            "declaring a shape nothing implements is checked against the only shape "
            "there is, which is worse than declaring nothing."))

    runtime = manifest.get("runtime")
    if runtime is not None and runtime not in RUNTIMES:
        findings.append(Finding(
            5, f"{rel}:runtime",
            f"reads {runtime!r}; ADR-003 declares {list(RUNTIMES)}. The value is "
            "recorded rather than dispatched on today — the migration path is a "
            "manifest edit, and a value outside the set is a migration to nowhere."))
    return findings


def _check_tools(manifest: dict, rel: str, registry: list[dict] | None) -> list[Finding]:
    """Rows 2, 3, 4 and 13 — the bijection between what a service declares and what
    the registry grants it.

    **Both directions, and the reverse one is the half nothing had.** Revoking
    `highlights-agent`'s grant on `entitlement-check` and regenerating cleanly left
    the manifest declaring `- id: entitlement-check@^0` with nothing red:
    `tests/test_contracts.py` checked only that the declared id *exists* in the
    registry, which a revoked grant does not disturb."""
    if registry is None:
        registry = load(REGISTRY)
    registry_rel = _rel(REGISTRY)
    try:
        granted = grants(registry)
    except DuplicateRegistryId as exc:
        return [Finding(13, registry_rel, str(exc))]

    service = manifest.get("service")
    declared_entries = manifest.get("tools")
    if not isinstance(declared_entries, list):
        return []

    findings = []
    declared_ids = []
    for entry in declared_entries:
        raw = entry.get("id") if isinstance(entry, dict) else entry
        if not isinstance(raw, str):
            findings.append(Finding(
                2, f"{rel}:tools", f"entry {entry!r} carries no `id:`."))
            continue
        # The range is split off and thrown away, and this module says so in its own
        # output (`DEFERRED`) rather than implying an evaluation it does not perform.
        tool_id = raw.split("@")[0]
        declared_ids.append(tool_id)
        if tool_id not in granted:
            findings.append(Finding(
                2, f"{rel}:tools",
                f"declares {tool_id!r}, which is not in {registry_rel}. Unregistered "
                "tools are unreachable (G3): the Cedar set is generated from that "
                "file, so this declaration grants nothing and reads as though it "
                "does."))
        elif service is not None and service not in granted[tool_id]:
            findings.append(Finding(
                3, f"{rel}:tools",
                f"declares {tool_id!r}, but {service!r} is not in that tool's "
                f"`callers:` in {registry_rel}. Cedar is generated from `callers:`, "
                "so the call is denied at the gateway while the manifest says the "
                f"service has the tool. Add {service!r} to the `- id: {tool_id}` "
                "block's `callers:`, or drop the declaration."))

    for tool_id, callers in granted.items():
        if service is not None and service in callers and tool_id not in declared_ids:
            findings.append(Finding(
                4, f"{registry_rel}:{tool_id}",
                f"grants {service!r} a tool its manifest ({rel}) does not declare. A "
                "grant nobody declared is a permission with no owner: it survives "
                "every review of the manifest, because it is not in the manifest. "
                f"Declare `- id: {tool_id}@^0` under `tools:`, or remove {service!r} "
                "from that entry's `callers:`."))
    return findings


def _check_gates(manifest: dict, rel: str) -> list[Finding]:
    """Rows 10 and 12 — the numbers a deploy is allowed to happen beneath."""
    findings = []
    declared = _get(manifest, "gates.eval_min_cases")
    if isinstance(declared, int) and declared < floors.PLATFORM_EVAL_MIN_CASES:
        findings.append(Finding(
            10, f"{rel}:gates.eval_min_cases",
            f"declares {declared}; the platform floor is "
            f"{floors.PLATFORM_EVAL_MIN_CASES} (`pave/floors.py`, AI Quality's). A "
            "service may demand more of itself than the platform does and may not "
            "demand less — `eval_min_cases: 0` is a service deploying with no "
            "evaluated cases at all, and it was green on every check this repository "
            "had before ADR-046."))

    budgets = _get(manifest, "gates.budgets")
    if isinstance(budgets, dict):
        for key in floors.REQUIRED_BUDGET_KEYS:
            if budgets.get(key) is None:
                findings.append(Finding(
                    12, f"{rel}:gates.budgets",
                    f"is missing {key!r}. Every case in this service's pack is "
                    "checked against these ceilings; an absent one is not a generous "
                    "ceiling, it is no ceiling."))
    return findings


def _check_pack(manifest: dict, directory: pathlib.Path) -> list[Finding]:
    """Rows 8, 9 and 11 — the golden pack the gate decides on."""
    pack_path = directory.joinpath(*GOLDEN_PACK)
    pack_rel = _rel(pack_path)
    if not pack_path.is_file():
        return [Finding(8, pack_rel,
                        "no golden pack. A service with no cases clears every case "
                        "floor by having nothing to count, which is the one reading "
                        "a floor must never permit.")]
    try:
        cases = load(pack_path)
    except DuplicateKey as exc:
        return [Finding(1, pack_rel, str(exc))]
    if not isinstance(cases, list):
        return [Finding(11, pack_rel,
                        f"the pack parsed as {type(cases).__name__}, not a list of "
                        "cases.")]

    findings = []
    for case in cases:
        if not isinstance(case, dict):
            findings.append(Finding(11, pack_rel, f"case {case!r} is not a mapping."))
            continue
        unknown = sorted(set(case) - floors.CASE_TOP_LEVEL_KEYS)
        if unknown:
            findings.append(Finding(
                11, f"{pack_rel}:{case.get('id')}",
                f"carries unknown top-level key(s) {unknown}. The runner ignores what "
                "it does not recognise, so a misspelled key is a case reporting PASS "
                "while checking nothing. Known keys: "
                f"{sorted(floors.CASE_TOP_LEVEL_KEYS)}."))

    kept = floors.disposed([c for c in cases if isinstance(c, dict)])
    declared = _get(manifest, "gates.eval_min_cases")
    floor = max(floors.PLATFORM_EVAL_MIN_CASES,
                declared if isinstance(declared, int) else 0)
    if len(kept) < floor:
        findings.append(Finding(
            8, pack_rel,
            f"holds {len(kept)} disposed case(s) against a floor of {floor}. Rows "
            "`pave new` scaffolded carry `provenance.author: "
            f"{floors.SCAFFOLD_AUTHOR}` and do not count — the floor means cases a "
            f"seat stood behind, not rows in a file ({len(cases)} here)."))
    else:
        try:
            floors.check_headroom(kept)
        except ValueError as exc:
            findings.append(Finding(9, pack_rel, str(exc)))
    return findings
