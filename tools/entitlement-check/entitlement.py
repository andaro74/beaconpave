"""
entitlement-check: the authoritative answer to "can this viewer watch this now".

The tool the trajectory eval exists to make meaningful. `catalog-search` serves
rows and is forbidden from reading `dmas` or `blackouts`; this module is the only
component that reads them, and that split is what lets a trajectory distinguish an
agent that ASKED from one that inferred. `SPEC/02` rejected serving both from one
tool on the record, and `schema.out.json` says why in its own description: *"the
decision is the tool's, never the model's."*

**Pure, and inside the hermetic surface**, exactly like `search.py` — no SDK
import, no network. Unlike `search.py` it is not clock-free, and that difference is
the design problem this module had to solve rather than paper over.

**The clock is a parameter, never an argument the caller may choose.** `reason:
not-yet-started` cannot be computed without one, and there are only three places a
clock could come from:

  - the tool's input contract — refused. `schema.in.json` is `additionalProperties:
    false` over `title_id`, `plan`, `dma`, and the caller is the model. A tool that
    let the model supply the instant it is judged against would hand back the
    decision its own output schema says is the tool's, and every other verdict
    here would be conditional on a value the agent picked.
  - a constant in this module — refused. `ADR-021` widened the clock parity rule to
    *"no arm may define a second clock"*, and `tests/test_gateway_run_parity.py`
    enforces it across the arms. A third literal is a third instrument.
  - **deployment configuration** — taken. `ADR-023` established exactly this shape
    one component over: the Cedar principal is deployment configuration and never
    the caller's field. `server.py` holds the deployed value and passes it in; this
    function stays pure and testable, and the value is pinned against the arms'
    clock by the same parity test that pins them to each other.

Owning seat: Tool Owner (the tool and its schemas) · Platform Engineering (the
plane it is reached through) · AI Quality (what a reason means, because the golden
cases are the specification of it).
"""
from __future__ import annotations

import json
import pathlib

#: Reasons, in the order they are decided. **This order is the specification and it
#: is derived from the committed golden cases, not chosen here** — twelve cases
#: assert an `entitlement` verdict and between them they fix every precedence:
#:
#:   blackout-001   base plan, blacked-out DMA   -> blackout, NOT upgrade-required
#:   multi-023      base plan, blacked-out DMA   -> blackout
#:      => a blackout outranks a plan gap. A viewer who cannot watch it anywhere
#:         in this market is not told to buy an upgrade that would not help.
#:   entitlement-002, edge-024
#:                  base plan, future event      -> upgrade-required, NOT not-yet-started
#:      => a plan gap outranks the clock. The upgrade is true now and stays true.
#:   entitlement-010
#:                  right plan, future event     -> not-yet-started
#:   entitlement-012
#:                  a title not in the catalog   -> unknown-title, before anything else
#:
#: Any reordering breaks at least one committed case, which is what
#: `tests/test_entitlement_check.py` asserts case by case rather than in prose.
REASON_ORDER = ("unknown-title", "blackout", "upgrade-required", "not-yet-started", "ok")

#: Plans that satisfy an entitlement, most permissive last. `sports-tier` includes
#: everything `base` does; a `base` viewer is refused `sports-tier` content.
PLAN_COVERS = {"base": frozenset({"base"}),
               "sports-tier": frozenset({"base", "sports-tier"})}


def load_catalog(path: str | pathlib.Path) -> dict:
    """The fixture, read once. Mirrors `search.load_catalog` deliberately: two
    tools reading one fixture two different ways is a drift surface."""
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _title(catalog: dict, title_id: str) -> dict | None:
    return next((t for t in catalog.get("titles", []) if t.get("id") == title_id), None)


def _blacked_out(catalog: dict, title: dict, dma: str) -> bool:
    """Is this DMA dark for this title's event?

    Reads `blackouts` as a mapping from event to the markets that cannot see it. A
    title with no `event` can never be blacked out — blackouts attach to events,
    not to titles, which is why `t002`-`t004` are clear everywhere."""
    event = title.get("event")
    if not event:
        return False
    return dma in set(catalog.get("blackouts", {}).get(event, ()))


def _has_started(title: dict, now: str) -> bool:
    """**Same UTC calendar day counts as started, and that is a decision.**

    Both `t001` (+1h from the clock) and `t005` (+7d) are in the future at the
    evaluation instant, and the golden cases want `ok` for the first and
    `not-yet-started` for the second — so the boundary is not "has the start time
    passed". The golden README states the intent in words rather than as a rule:
    the clock is *"one hour before the Jefferson Derby kicks off, one week before
    the Cedar Point Rowing Finals ... what makes 'tonight's derby' coherent and
    'hasn't started yet' true."*

    Same-day is the narrowest rule that reproduces both, and it encodes "tonight"
    directly. **A 24-hour window reproduces them equally well**, and the two
    committed cases cannot distinguish the rules — nothing sits between +1h and
    +7d. Recorded as underdetermined rather than presented as derived: if a case is
    ever added at, say, +20h on the following day, the seats have to say which rule
    they meant, and this comment is where they will find that it was a choice.

    A title with no `starts` is not scheduled and is always available."""
    starts = title.get("starts")
    if not starts:
        return True
    return starts[:10] <= now[:10]


def check(args: dict, catalog: dict, now: str) -> dict:
    """The verdict, as `schema.out.json` describes it.

    `now` is required and has no default. A default would be a second clock
    definition wearing a keyword argument, and it would make every caller that
    forgot it silently correct at one instant and silently wrong afterwards."""
    title = _title(catalog, args["title_id"])
    if title is None:
        # No `blackout` and no `required_entitlement`: both would be claims about a
        # title this tool cannot see, and the schema marks them optional precisely
        # so a verdict can decline to make them.
        return {"entitled": False, "reason": "unknown-title"}

    required = title.get("entitlement")
    out = {"required_entitlement": required} if required else {}
    if title.get("event"):
        out["event"] = title["event"]

    blackout = _blacked_out(catalog, title, args["dma"])
    out["blackout"] = blackout
    if blackout:
        return {"entitled": False, "reason": "blackout", **out}

    if required and required not in PLAN_COVERS.get(args["plan"], frozenset()):
        return {"entitled": False, "reason": "upgrade-required", **out}

    if not _has_started(title, now):
        return {"entitled": False, "reason": "not-yet-started", **out}

    return {"entitled": True, "reason": "ok", **out}
