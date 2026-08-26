"""What `pave new` renders, and the two steps it deliberately cannot take.

**Creates-only.** This module writes files that do not exist and never edits one
that does. `platform/registry/tools.yaml` and the generated Cedar set are the two
things a new service needs and this command will not touch: the registry line is a
`tool-owner` + `legal-sp` decision, and a scaffolder that granted itself tool
access would be the authorization hole the tool plane exists to close, arriving
through the front door.

**The scaffold does not pass its own gate, by design.** A freshly rendered service
earns exactly two refusals from `pave verify`, and each one *is* an onboarding
step: row 3 (the registry grant is missing) and row 8 (nobody has written a golden
case yet). A scaffold that verified clean would teach a team that the gate means
nothing — and an unknown service was already green on all 1861 tests before
ADR-046, which is the state this whole milestone exists to end.

**Five files, and the list is the commitment.** The reference service is 14 files;
nine are measurement harnesses from M01-M04 that no scaffold should emit. It
renders no `run_probes*.py` in particular: that path is on an existing
`(security, platform-eng)` rule, so emitting one would hand every team a file it
could never edit alone.

Hermetic (G8): reads committed templates, writes local files, calls no model.
Owning seats: Platform Engineering (the mechanism) · Service Team (what a team
meets first) · AI Quality + Tool Owner (what the rendered manifest may claim).
"""
from __future__ import annotations

import pathlib
import re

from pave import floors, twokey

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "agent-tools"
SERVICES = ROOT / "services"

#: `(template, destination)`, relative to `TEMPLATES` and to the service directory.
#:
#: **All five are `.tmpl`, and two of them were nearly not.** SPEC/05 listed
#: `evals/answer.schema.json` and `evals/golden/README.md` as rendered *verbatim*.
#: Both carry the reference service's identity — the schema's `$id` and `title`,
#: and the README's heading — so two scaffolded services would have collided on one
#: `$id`, which is the field a JSON-Schema resolver keys on.
RENDERED = (
    ("pave.manifest.yaml.tmpl", "pave.manifest.yaml"),
    ("gateway_client.py.tmpl", "gateway_client.py"),
    ("evals/answer.schema.json.tmpl", "evals/answer.schema.json"),
    ("evals/golden/cases.yaml.tmpl", "evals/golden/cases.yaml"),
    ("evals/golden/README.md.tmpl", "evals/golden/README.md"),
)

#: Every substitution a template may ask for. A template naming anything else is a
#: rendering failure rather than a file with `{{typo}}` in it — see `render`.
PLACEHOLDERS = ("service", "brand", "brand_title", "team", "oncall")

#: A service name is a directory name, a Cedar principal and a `callers:` entry.
SERVICE_NAME = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

#: The suffix the ungoverned control uses. A service claiming it would sit beside
#: `services/highlights-agent-baseline/` and read as a control that is not one.
RESERVED_SUFFIX = "-baseline"

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


class ScaffoldError(Exception):
    """A refusal. Carries the message a team reads; never a traceback."""


def brand_title(brand: str) -> str:
    """`meridian-sports` -> `Meridian Sports`, for prose inside rendered files.

    Derived rather than passed, so a caller cannot supply a display name that
    disagrees with the brand the manifest declares and the judge scores."""
    return " ".join(part.capitalize() for part in brand.split("-"))


def render(text: str, values: dict[str, str]) -> str:
    """Substitute `{{name}}`, and refuse to emit a file that still holds one.

    **`str.replace`, not `str.format` and not a template engine.** `.format` would
    collide with the rendered Python's own `{schema}` and `{catalog}` runtime
    placeholders, and a template engine is a dependency CLAUDE.md would want an ADR
    line for.

    The leftover check is the half that matters: without it, adding a placeholder
    to a template and forgetting to supply it emits a service whose manifest reads
    `owners: {team: {{team}}}` — valid YAML, a string, and wrong."""
    for name, value in values.items():
        text = text.replace("{{" + name + "}}", value)
    leftover = sorted({m.group(1) for m in _PLACEHOLDER.finditer(text)})
    if leftover:
        raise ScaffoldError(
            f"the template still holds {leftover} after rendering. Every placeholder "
            f"a template uses must be in `scaffold.PLACEHOLDERS` ({list(PLACEHOLDERS)}) "
            "and supplied by the caller — an unrendered one is a literal `{{name}}` in "
            "a deployed file, which is valid YAML and wrong.")
    return text


def check(service: str, brand: str) -> None:
    """Raise `ScaffoldError` unless this service can be created. Writes nothing."""
    if not SERVICE_NAME.match(service):
        raise ScaffoldError(
            f"{service!r} is not a usable service name. It becomes a directory, a Cedar "
            "principal and a `callers:` entry, so it must be lowercase letters, digits "
            "and single hyphens, starting with a letter — e.g. `sportscast-agent`.")
    if service.endswith(RESERVED_SUFFIX):
        raise ScaffoldError(
            f"{service!r} ends in {RESERVED_SUFFIX!r}, which this repository uses for "
            "ungoverned controls (`services/highlights-agent-baseline/`). A service "
            "there would read as a control that is not one, and baseline honesty "
            "depends on that distinction being visible in the path.")
    if brand not in floors.SUPPORTED_BRANDS:
        raise ScaffoldError(
            f"brand {brand!r} is not one the judge can score. Supported: "
            f"{list(floors.SUPPORTED_BRANDS)}.\n"
            "A brand is supported when the rubric under `quality/judge/` carries its "
            f"`brand_tone:{brand}` axis — `evals/judge.py` raises without it, so every "
            "judged case in the service would be scored against a rubric that does not "
            "mention it. Adding one is a judge re-freeze (two-key `ai-quality`) plus "
            "superseding history entries; ADR-047 records why that is M08's and not a "
            "flag on this command.")
    target = SERVICES / service
    if target.exists():
        raise ScaffoldError(
            f"`services/{service}/` already exists. `pave new` is creates-only: it will "
            "not overwrite a file a team has edited, and re-running it is not how a "
            "template fix reaches an existing service. Delete the directory yourself if "
            "that is what you meant.")


def plan(service: str, brand: str, team: str, oncall: str) -> list[tuple[pathlib.Path, str]]:
    """`(destination, contents)` for every file, rendered but not written.

    Separated from `create` so the whole render can fail before the first byte is
    written. A scaffolder that writes three files and then raises leaves a
    half-service that `pave verify` reports on and nobody asked for."""
    values = {
        "service": service,
        "brand": brand,
        "brand_title": brand_title(brand),
        "team": team,
        "oncall": oncall,
    }
    unknown = sorted(set(values) - set(PLACEHOLDERS))
    assert not unknown, unknown
    out = []
    for source, destination in RENDERED:
        template = TEMPLATES / source
        if not template.is_file():
            raise ScaffoldError(
                f"the template `{template.relative_to(ROOT).as_posix()}` is missing, so "
                f"`{destination}` cannot be rendered. `pave new` emits five files or it "
                "emits none — a partial scaffold is a service nobody chose to create.")
        out.append((SERVICES / service / destination,
                    render(template.read_text(encoding="utf-8"), values)))
    return out


def create(service: str, brand: str, team: str, oncall: str) -> list[pathlib.Path]:
    """Render and write. Returns the paths written, in `RENDERED` order."""
    check(service, brand)
    written = []
    for destination, contents in plan(service, brand, team, oncall):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents, encoding="utf-8")
        written.append(destination)
    return written


def onboarding_seats(service: str) -> list[str]:
    """The seats a scaffolded service's first PR actually collects.

    **Computed from `pave/twokey.py`, never written down.** SPEC/05's draft of this
    banner named five seats, and the Service Team and Tool Owner seats independently
    measured three: `security` and `platform-eng` entered that count solely through
    the probe-runner rule, and this command renders no probe runner. `evaluate()`
    reports only *missing* seats, so two surplus dispositions pass silently — a
    banner over-stating the cost teaches every team to attest past rules they never
    triggered, which is the habit G9 depends on nobody having."""
    paths = [f"services/{service}/{destination}" for _, destination in RENDERED]
    paths += ["platform/registry/tools.yaml",
              "platform/gateway/policy/tools.cedar",
              "platform/gateway/policy/tools.contracts.json"]
    return sorted({seat for rule, _ in twokey.triggered(paths) for seat in rule.seats})


def next_steps(service: str) -> str:
    """The two things `pave new` cannot do, and the refusals that follow if you skip.

    **The registry block anchors on `- id:`, never on a line number and never on the
    line's own text.** A line number shifts when any tool is added, and all three
    `callers:` lines in the registry are byte-identical — so "the line" is ambiguous
    in both forms. During the SPEC/05 review a seat following the vaguer instruction
    **granted itself the publish-class tool**, which is why the refusal below is
    stated as loudly as the instruction."""
    seats = onboarding_seats(service)
    return f"""
Rendered {len(RENDERED)} files into services/{service}/.

`python -m pave.cli verify {service}` will REFUSE this service, with two findings.
That is expected: each one is a step below, and neither is something `pave new`
may take for you.

1. REGISTER THE SERVICE AS A CALLER  (refusal row 3)

   In platform/registry/tools.yaml, find the entry beginning `- id: catalog-search`
   and add {service} to THAT entry's callers list:

       - id: catalog-search
         ...
         callers: [highlights-agent, {service}]

   There are three `callers:` lines in that file and they read alike. Match on the
   `- id:` above the line, never on the line itself.

   Do NOT add yourself under `- id: publish-highlight`. Its consequence class is
   `publish`: adding a caller there grants your service a human-approval-interlocked
   tool, and that edit is a tool-owner + legal-sp decision. It is not a scaffolding
   step, and a seat reviewing this milestone made exactly that mistake.

   Then regenerate the policy the registry decides, and commit both artifacts:

       python -m pave.cli policy generate
       git add platform/gateway/policy/tools.cedar \\
               platform/gateway/policy/tools.contracts.json

   Skip the regenerate and `make check` is red with 3 failures, only one of which
   names this as the cause.

2. WRITE YOUR GOLDEN CASES  (refusal row 8)

   services/{service}/evals/golden/cases.yaml holds three worked examples, all
   marked `author: pave-template`. Template rows do not count toward the floor of
   {floors.PLATFORM_EVAL_MIN_CASES}, so the pack currently counts as zero.

   Read README.md in that directory first. Budget real time for this: the reference
   pack is 25 cases over ~510 lines with 138 asserts, and 4 of its 25 starter cases
   were authored with bans a CORRECT answer trips — by the person who wrote the
   assert vocabulary.

   Keep {int(floors.HEADROOM_BAND[0] * 100)}-{int(floors.HEADROOM_BAND[1] * 100)}% of
   your cases marked `expect_near_threshold: true`. A suite at 100% can only report
   "no change or regression".

YOUR PR WILL REQUIRE {len(seats)} SEAT ATTESTATION(S): {', '.join(seats)}
   See docs/governance/ROLES.md. This count is computed from pave/twokey.py at the
   moment you ran this command, not written into the banner.

If a rule genuinely blocks something your service must do, that is an exception
request, not a reason to weaken the rule — see docs/governance/ROLES.md.
""".rstrip() + "\n"
