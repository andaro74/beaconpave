"""What `pave new` renders, and whether the template still matches the service it
was cut from.

**The pairwise half is the one that decays.** A template is a copy, and a copy of a
living file is wrong the moment the original moves. Nothing in this repository
compared `templates/agent-tools/` to `services/highlights-agent/` before ADR-047 —
the template directory held one README — so a template could have drifted for four
milestones without a single test noticing.

**Two of the five pairs round-trip byte-identically**, which is stronger than the
"byte-identical" SPEC/05 asked for and different in kind: the template carries
placeholders, so it *cannot* equal the reference. What is asserted instead is that
rendering the template **with the reference service's own values** reproduces the
reference exactly. That catches an edit to either side, and it is only possible
because both files were derived rather than retyped.

**The scaffold must FAIL `pave verify`.** `test_a_fresh_scaffold_is_refused_with_the
_onboarding_steps` is the pre-registered prediction 8, and it asserts the *exact*
row set rather than "some findings" — a scaffold that failed for an extra reason
would be a scaffold with a defect in it, and "not green" would hide that.

Hermetic (G8): renders into `tmp_path`, reads committed files, calls no model.
Owning seats: Platform Engineering (the mechanism) · Service Team (what a team meets
first) · AI Quality + Tool Owner (what the rendered manifest claims).
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest
import yaml

from pave import floors, scaffold, twokey
from pave import manifest as manifest_mod

ROOT = pathlib.Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "services" / "highlights-agent"
TEMPLATES = scaffold.TEMPLATES

#: The reference service's own values, so a template can be rendered back into it.
REFERENCE_VALUES = {
    "service": "highlights-agent",
    "brand": "meridian-sports",
    "brand_title": "Meridian Sports",
    "team": "beacon-sports-discovery",
    "oncall": "webhook:sports-disc",
}


def render_as_reference(template_rel: str) -> str:
    return scaffold.render((TEMPLATES / template_rel).read_text(encoding="utf-8"),
                           REFERENCE_VALUES)


def scaffold_into(tmp_path, service="sportscast-agent", brand=None, monkeypatch=None):
    """Render a service under `tmp_path` rather than into the repository."""
    brand = brand or floors.SUPPORTED_BRANDS[0]
    monkeypatch.setattr(scaffold, "SERVICES", tmp_path / "services")
    return scaffold.create(service, brand, "beacon-example", "webhook:example")


# --- the file list is the commitment --------------------------------------------

def test_it_renders_exactly_five_files_and_no_sixth(tmp_path, monkeypatch):
    """Prediction 7. The reference service is 14 files; nine are M01-M04 measurement
    harnesses no scaffold should emit."""
    written = scaffold_into(tmp_path, monkeypatch=monkeypatch)
    root = tmp_path / "services" / "sportscast-agent"
    on_disk = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    assert on_disk == sorted(dest for _, dest in scaffold.RENDERED), on_disk
    assert len(written) == 5


def test_it_renders_no_probe_runner(tmp_path, monkeypatch):
    """**The one omission with a governance reason rather than a scope reason.**
    `^services/[^/]+/run_probes(_via_gateway)?\\.py$` is on a `(security,
    platform-eng)` rule, so emitting one would hand every team a file it could never
    edit alone — and the adversarial lane's own onboarding message used to tell a
    scaffolded service to run exactly that file."""
    scaffold_into(tmp_path, monkeypatch=monkeypatch)
    root = tmp_path / "services" / "sportscast-agent"
    probes = [p.name for p in root.rglob("run_probes*.py")]
    assert not probes, probes
    for _, destination in scaffold.RENDERED:
        assert not twokey.triggered([f"services/sportscast-agent/{destination}"]) or \
            destination == "pave.manifest.yaml" or destination.startswith("evals/"), (
            f"{destination} lands on a two-key rule a scaffolding team cannot satisfy")


# --- the pairwise checks: template vs the service it was cut from ----------------

def test_the_answer_schema_round_trips_to_the_reference():
    """Byte-identical after rendering with the reference's own values.

    SPEC/05 listed this file as rendered *verbatim*. It cannot be: line 3 is
    `"$id": ".../services/highlights-agent/evals/answer.schema.json"`, and two
    scaffolded services sharing one `$id` collide on the field a JSON-Schema
    resolver keys on."""
    assert render_as_reference("evals/answer.schema.json.tmpl") == \
        (REFERENCE / "evals" / "answer.schema.json").read_text(encoding="utf-8")


def test_the_golden_readme_round_trips_to_the_reference():
    """Also listed as verbatim, and also carrying identity — its heading names the
    service and the brand. 174 lines of assert vocabulary that a scaffolded team
    reads before writing a single case, so drift here is drift in what a team is
    taught the vocabulary is."""
    assert render_as_reference("evals/golden/README.md.tmpl") == \
        (REFERENCE / "evals" / "golden" / "README.md").read_text(encoding="utf-8")


def test_the_manifest_template_has_the_reference_key_set():
    """Keys and nesting, never values — the values are what a new service changes.

    `gates.budgets`' keys are compared and must not be erased: an absent ceiling is
    not a generous ceiling, and `pave verify` row 12 refuses it."""
    rendered = yaml.safe_load(render_as_reference("pave.manifest.yaml.tmpl"))
    reference = yaml.safe_load((REFERENCE / "pave.manifest.yaml").read_text(encoding="utf-8"))
    assert set(rendered) == set(reference), (
        f"template-only keys: {sorted(set(rendered) - set(reference))}; "
        f"reference-only keys: {sorted(set(reference) - set(rendered))}")
    for block in ("owners", "gates", "attestations"):
        assert set(rendered[block]) == set(reference[block]), block
    assert set(rendered["gates"]["budgets"]) == set(reference["gates"]["budgets"])
    assert set(rendered["gates"]["budgets"]) == set(floors.REQUIRED_BUDGET_KEYS)


def test_the_gateway_client_template_sends_the_pinned_viewer_turn():
    """The `ast.JoinedStr` technique from `tests/test_transport_parity.py`, applied
    across the template boundary.

    Every service this template renders sends the same viewer sentence as the
    governed arm and the ungoverned control. That sentence is the wire text of every
    observation a service is judged on, and **no instrument digest covers the
    transport** — so a template that drifted here would silently give every future
    service a different payload shape from the one the platform's numbers were
    measured with."""
    def skeletons(text):
        out = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.JoinedStr):
                out.add("".join(part.value if isinstance(part, ast.Constant) else "{?}"
                                for part in node.values))
        return out

    template = skeletons((TEMPLATES / "gateway_client.py.tmpl").read_text(encoding="utf-8"))
    reference = skeletons((REFERENCE / "gateway_client.py").read_text(encoding="utf-8"))
    shared = {s for s in template & reference if "Evaluation clock" in s}
    assert shared, (
        "the template and the reference no longer render the same viewer sentence.\n"
        f"  template:  {sorted(s for s in template if '{?}' in s)}\n"
        f"  reference: {sorted(s for s in reference if '{?}' in s)}")


def test_the_scaffold_pack_uses_only_the_closed_case_vocabulary():
    """The scaffold teaches by example, so an example carrying a key the runner
    ignores teaches a case that reports PASS while checking nothing."""
    cases = yaml.safe_load(render_as_reference("evals/golden/cases.yaml.tmpl"))
    assert cases, "the scaffold pack is empty"
    for case in cases:
        unknown = sorted(set(case) - floors.CASE_TOP_LEVEL_KEYS)
        assert not unknown, f"{case['id']}: {unknown}"


def test_the_pair_list_covers_every_rendered_file():
    """**The vacuity guard for this whole section.** Four pairwise tests over five
    rendered files would leave one template comparable to nothing, and the one left
    out is the one that drifts."""
    covered = {"pave.manifest.yaml", "gateway_client.py", "evals/answer.schema.json",
               "evals/golden/cases.yaml", "evals/golden/README.md"}
    assert covered == {dest for _, dest in scaffold.RENDERED}, (
        "a rendered file has no pairwise test. A template compared to nothing is a "
        "copy that is wrong the moment the original moves, which is the state this "
        "repository was in for four milestones.")


# --- what the scaffold may cite --------------------------------------------------

def test_the_scaffold_cites_only_committed_catalog_titles():
    """**The sports cut, as a check rather than a sentence.**

    SPEC/05 said M05 scaffolds a sports service and left it at that; the Service
    Team seat measured that the real constraint is narrower and brand-blind. A
    *fictional sports* title with an event, a start time and `sports-tier` is the
    identical **16 failures** — the catalog is embedded model-facing in the judge
    prompt and digested into `quality/judge/frozen.json`, so any new content runs
    through a judge re-freeze whatever brand it carries.

    So the green path is: reuse the committed titles. This asserts the scaffold does,
    and it is red the day a title id is renamed — which is exactly when the scaffold
    would start emitting a pack whose first run fails for a reason no one caused."""
    catalog = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    known = {t["id"] for t in catalog["titles"]}
    sports = {t["id"] for t in catalog["titles"] if t["brand"] == "meridian-sports"}
    cases = yaml.safe_load(render_as_reference("evals/golden/cases.yaml.tmpl"))
    cited = {i for case in cases for a in case["asserts"]
             if isinstance(a, dict) and "must_cite" in a for i in a["must_cite"]}
    assert cited, "the scaffold pack cites nothing, so this check examined nothing"
    assert cited <= known, f"scaffold cites titles absent from the catalog: {cited - known}"
    assert cited <= sports, (
        f"the scaffold cites non-sports titles {cited - sports}; `--brand` accepts only "
        f"{list(floors.SUPPORTED_BRANDS)} and the judge would score them against a "
        "rubric that does not mention their brand.")


# --- prediction 8: the scaffold does not pass its own gate -----------------------

def test_a_fresh_scaffold_is_refused_with_the_onboarding_steps(tmp_path, monkeypatch):
    """**Prediction 8, and the row set is asserted exactly.**

    Draft 4's definition of done implied the scaffold is green, which proves nothing:
    an unknown service was 1861 passed before ADR-046 — invisible rather than
    passing. And "it fails" is not enough either: a scaffold failing for a *third*
    reason has a defect in it, and a loose assertion would hide that.

    Row 3 is the registry grant and row 8 is the golden pack. Both are steps the
    command prints and neither is one it may take."""
    directory = scaffold_into(tmp_path, monkeypatch=monkeypatch)[0].parent
    registry = manifest_mod.load(manifest_mod.REGISTRY)
    findings = manifest_mod.verify(directory, registry=registry)
    assert sorted(f.row for f in findings) == [3, 8], (
        "the scaffold's refusals are not the two onboarding steps:\n"
        + "\n".join(f.render() for f in findings))
    text = "\n".join(f.message for f in findings)
    assert "callers" in text and floors.SCAFFOLD_AUTHOR in text


def test_the_printed_steps_name_both_refusals_and_the_computed_seat_count():
    """The banner is what a team acts on, and its seat count was wrong in the spec.

    SPEC/05 said **five** seats; the Service Team and Tool Owner seats independently
    measured **three**. `security` and `platform-eng` entered that count solely
    through the probe-runner rule, and this command renders no probe runner.
    `twokey.evaluate()` reports only *missing* seats, so two surplus dispositions
    would have passed silently — a banner over-stating the cost teaches every team to
    attest past rules it never triggered.

    So the count is computed at print time, and this asserts the computation rather
    than a number."""
    steps = scaffold.next_steps("sportscast-agent")
    seats = scaffold.onboarding_seats("sportscast-agent")
    assert seats == ["ai-quality", "legal-sp", "tool-owner"], seats
    assert f"{len(seats)} SEAT ATTESTATION(S): {', '.join(seats)}" in steps
    assert "row 3" in steps and "row 8" in steps
    assert "- id: catalog-search" in steps
    assert "Do NOT add yourself under `- id: publish-highlight`" in steps


def test_the_banner_anchors_on_an_id_and_never_on_a_line_number():
    """During the SPEC/05 review a seat following the vaguer instruction **granted
    itself the publish-class tool.** A line number shifts when any tool is added, and
    all three `callers:` lines in the registry are byte-identical — so quoting "the
    line" is ambiguous in both available forms."""
    steps = scaffold.next_steps("sportscast-agent")
    assert "never on the line itself" in steps
    registry = (ROOT / "platform" / "registry" / "tools.yaml").read_text(encoding="utf-8")
    callers = [ln.strip() for ln in registry.splitlines() if ln.strip().startswith("callers:")]
    assert len(set(callers)) < len(callers), (
        "the `callers:` lines are no longer byte-identical, so this test's premise has "
        "changed. The `- id:` anchor is still correct; update the reasoning, not the "
        "instruction.")


# --- creates-only, and the refusals ---------------------------------------------

def test_it_refuses_to_overwrite_an_existing_service(tmp_path, monkeypatch):
    scaffold_into(tmp_path, monkeypatch=monkeypatch)
    with pytest.raises(scaffold.ScaffoldError, match="creates-only"):
        scaffold.create("sportscast-agent", floors.SUPPORTED_BRANDS[0], "t", "o")


def test_it_refuses_a_brand_the_judge_cannot_score(tmp_path, monkeypatch):
    """**Item 39 as a check, not a sentence.** Before this, `brand` was enforced by a
    `print()` in a creates-only command and `meridian-sports -> meridian-news` was
    1889 passed."""
    monkeypatch.setattr(scaffold, "SERVICES", tmp_path / "services")
    with pytest.raises(scaffold.ScaffoldError, match="brand_tone:meridian-news"):
        scaffold.create("sportscast-agent", "meridian-news", "t", "o")
    assert not (tmp_path / "services").exists(), "a refused scaffold wrote files"


@pytest.mark.parametrize("name", ["Sportscast", "sports_cast", "-leading", "9lives",
                                  "trailing-", "sports--cast"])
def test_it_refuses_a_name_that_is_not_a_usable_principal(name, tmp_path, monkeypatch):
    """The name becomes a directory, a Cedar principal and a `callers:` entry."""
    monkeypatch.setattr(scaffold, "SERVICES", tmp_path / "services")
    with pytest.raises(scaffold.ScaffoldError, match="usable service name"):
        scaffold.create(name, floors.SUPPORTED_BRANDS[0], "t", "o")


def test_it_refuses_the_baseline_suffix(tmp_path, monkeypatch):
    """`services/highlights-agent-baseline/` is the ungoverned control. A service
    named like one would read as a control that is not one, and CLAUDE.md's
    baseline-honesty rule depends on that distinction being visible in the path."""
    monkeypatch.setattr(scaffold, "SERVICES", tmp_path / "services")
    with pytest.raises(scaffold.ScaffoldError, match="ungoverned controls"):
        scaffold.create("sportscast-baseline", floors.SUPPORTED_BRANDS[0], "t", "o")


# --- the renderer itself ---------------------------------------------------------

def test_rendering_refuses_to_emit_an_unresolved_placeholder():
    """Without this, adding a placeholder to a template and forgetting to supply it
    emits `owners: {team: {{team}}}` — valid YAML, a string, and wrong."""
    with pytest.raises(scaffold.ScaffoldError, match="still holds"):
        scaffold.render("service: {{service}}\nteam: {{team}}\n", {"service": "x"})


def test_every_placeholder_a_template_uses_is_one_the_renderer_supplies():
    """The other direction, and the one a unit test cannot reach: a template may not
    invent a placeholder. Red the moment someone adds `{{region}}` to a template
    without teaching `pave new` what a region is."""
    import re
    used = set()
    for source, _ in scaffold.RENDERED:
        used |= set(re.findall(r"\{\{(\w+)\}\}",
                               (TEMPLATES / source).read_text(encoding="utf-8")))
    unknown = sorted(used - set(scaffold.PLACEHOLDERS))
    assert not unknown, f"templates use {unknown}, which `pave new` does not supply"
    assert used, "no template uses a placeholder, so the renderer is doing nothing"


def test_no_rendered_file_keeps_the_reference_services_identity(tmp_path, monkeypatch):
    """The whole reason all five files are `.tmpl`. Two were specified as verbatim
    and both carried `highlights-agent`'s name in a field that must be unique."""
    scaffold_into(tmp_path, monkeypatch=monkeypatch)
    root = tmp_path / "services" / "sportscast-agent"
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        leaks = [ln.strip()[:90] for ln in text.splitlines()
                 if "highlights-agent" in ln and "highlights-agent-baseline" not in ln
                 and not ln.lstrip().startswith(("#", "//"))]
        assert not leaks, f"{path.name} carries the reference service's identity: {leaks}"


def test_the_brand_title_is_derived_and_not_passed():
    """A caller supplying a display name could disagree with the brand the manifest
    declares and the judge scores."""
    assert scaffold.brand_title("meridian-sports") == "Meridian Sports"
    assert "brand_title" not in ("service", "brand", "team", "oncall")
    rendered = render_as_reference("gateway_client.py.tmpl")
    assert "Meridian Sports" in rendered


# --- the command wrapper, whose exit code IS the gate in `make core` ------------

def test_the_command_refuses_with_a_named_message_and_a_nonzero_exit(tmp_path, monkeypatch):
    """**Written before the audit, because PR 4b's one silent mutation was exactly
    this gap one component over**: `pave/verify.py`'s failing exit code was untested
    and returning 0 on findings was invisible at 1982 passed.

    A refusal that exits 0 is a refusal a script ignores, and a team meets this
    command before it meets anything else in the repository — so it must also be a
    named message rather than a traceback."""
    from pave import cli
    from pave import gate as gate_mod
    monkeypatch.setattr(scaffold, "SERVICES", tmp_path / "services")
    printed = []
    monkeypatch.setattr(cli, "_emit", printed.append)

    assert cli.scaffold_new(["Sportscast"]) == gate_mod.EXIT_CONTRACT
    assert cli.scaffold_new([]) == gate_mod.EXIT_CONTRACT
    assert cli.scaffold_new(["ok-agent", "--brand", "meridian-news"]) == gate_mod.EXIT_CONTRACT
    text = "\n".join(printed)
    assert "Traceback" not in text and "refused" in text
    assert not (tmp_path / "services").exists(), "a refused command wrote files"


def test_the_command_reports_what_it_wrote_and_exits_zero(tmp_path, monkeypatch):
    from pave import cli
    from pave import gate as gate_mod
    monkeypatch.setattr(scaffold, "SERVICES", tmp_path / "services")
    printed = []
    monkeypatch.setattr(cli, "_emit", printed.append)
    assert cli.scaffold_new(["sportscast-agent"]) == gate_mod.EXIT_OK
    text = "\n".join(printed)
    for _, destination in scaffold.RENDERED:
        assert destination in text, f"the command did not report writing {destination}"


def test_the_scaffold_pack_teaches_headroom(tmp_path, monkeypatch):
    """The band is the requirement teams miss first, and a pack with no worked
    example of it teaches by omission that it is optional.

    Asserted on the RENDERED pack rather than the template, so a placeholder that
    stopped resolving inside the flag would be caught too."""
    scaffold_into(tmp_path, monkeypatch=monkeypatch)
    pack = yaml.safe_load(
        (tmp_path / "services" / "sportscast-agent" / "evals" / "golden" / "cases.yaml")
        .read_text(encoding="utf-8"))
    near = [c for c in pack if c.get("expect_near_threshold")]
    assert near, (
        "the scaffold pack has no `expect_near_threshold` example. `pave verify` "
        f"enforces a band of {floors.HEADROOM_BAND} over a disposed pack, and a "
        "scaffold that never shows the flag teaches that the band is optional.")
    assert all("judge" not in c for c in pack if c.get("expect_near_threshold")), (
        "the headroom example carries a `judge:` block, which re-teaches the nesting "
        "ADR-045 removed — the flag is top-level and only top-level.")


def test_every_scaffolded_row_is_marked_as_scaffolding(tmp_path, monkeypatch):
    """**Found silent by the deletability audit.** Changing the template's
    `provenance.author` from `pave-template` to any other value was **2053 passed**.

    Prediction 8's test could not see it: with three rows counting as disposed the
    pack is still 3 against a floor of 20, so row 8 still fires and the row set is
    still `[3, 8]`. It is the same "a count sees arithmetic, not identity" shape
    ADR-045 recorded — a check reading the tally instead of the marking.

    What it would have cost: the template teaching, by example, that rows it wrote
    count toward the floor a team must clear. `disposed()` exists so the default is
    honest and the lie has to be deliberate; a template shipping pre-disposed rows
    inverts that on day one for every service anyone ever scaffolds."""
    scaffold_into(tmp_path, monkeypatch=monkeypatch)
    pack = yaml.safe_load(
        (tmp_path / "services" / "sportscast-agent" / "evals" / "golden" / "cases.yaml")
        .read_text(encoding="utf-8"))
    assert pack, "the scaffold pack is empty, so this check examined nothing"
    claimed = floors.disposed(pack)
    assert claimed == [], (
        "the scaffold pack ships rows that already count as disposed: "
        f"{[c['id'] for c in claimed]}. Every template row must carry "
        f"`provenance.author: {floors.SCAFFOLD_AUTHOR}` — the floor means cases a seat "
        "stood behind, and a scaffold cannot stand behind anything.")
    assert all((c.get("provenance") or {}).get("author") == floors.SCAFFOLD_AUTHOR
               for c in pack)
