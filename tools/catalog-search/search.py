"""
catalog-search: the Beacon catalog, as a tool rather than as a prompt.

This is the component that ends the control's shape. Every milestone up to M01
answered by inlining the whole catalog into the system prompt; from M02 the model
gets rows it asked for, and only those.

**Rows only, and never the blackout table.** `data/catalog.json` carries `dmas`
and `blackouts` beside `titles`, and this module reads none of them — the
committed output schema says why in its own description: *"This tool never decides
entitlement or blackout — that is entitlement-check's job, and splitting them is
what makes the trajectory eval meaningful at M06."* Serving the blackout map here
would collapse two tools into one and let the agent keep inferring entitlement
from context while a tool call in the trajectory made it look as though a tool had
answered. SPEC/02 rejects that on the record.

**Pure, and inside the hermetic surface.** No SDK import, no network, no clock.
The same function backs the MCP server and the tests, so what `make check` proves
is what the deployed tool does. Determinism is not a nicety here: two runs of the
golden set must differ by the model's sampling and nothing else, so identical
arguments must always return identical rows in an identical order.

**The bundle-root layout is the gateway's, for the gateway's reason.** `tools/
catalog-search/` is a deployment bundle, not an installed package — the directory
goes on `sys.path` and this resolves as `search`, exactly as it will in the MCP
server process.

Owning seat: Tool Owner (the tool and its schemas) · Platform Engineering (the
plane it is reached through).
"""
from __future__ import annotations

import json
import pathlib

#: Fields a result row may carry, mirroring `schema.out.json`, which sets
#: `additionalProperties: false`. Listed rather than copied from the catalog so a
#: field added to the fixture cannot silently start reaching the model — the
#: blackout table is the reason that matters.
RESULT_FIELDS = ("id", "title", "brand", "type", "entitlement", "event", "starts")

#: Free text matches the metadata a viewer would actually say out loud. `id` is
#: excluded because nobody searches for "t003"; `starts` because a timestamp is
#: not a search term; and `entitlement` because it is a policy attribute rather
#: than a discovery one — "what do I get on sports-tier" is an entitlement
#: question, and entitlement questions are not this tool's to answer.
SEARCHABLE_FIELDS = ("title", "event", "brand", "type")

#: A term this short carries no signal and matches most of the catalog. Dropping
#: it is what stops "is the derby on" from behaving like a wildcard.
MIN_TERM_LENGTH = 3

DEFAULT_LIMIT = 5
MAX_LIMIT = 10


def load_catalog(path: str | pathlib.Path) -> dict:
    """Read a catalog fixture. Kept separate from `search` so the function that
    decides what the model sees takes data rather than a filename — which is what
    lets the adversarial run point it at `data/catalog_poisoned.json` without a
    second code path."""
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _terms(query: str) -> list[str]:
    return [t for t in str(query or "").lower().split() if len(t) >= MIN_TERM_LENGTH]


def _haystack(title: dict) -> str:
    return " ".join(str(title.get(f, "")) for f in SEARCHABLE_FIELDS).lower()


def _row(title: dict) -> dict:
    """Project a catalog entry onto the output contract.

    An allowlist, not a copy with deletions. A field added to the fixture is
    invisible here until somebody adds it to `RESULT_FIELDS` and to the schema —
    which is the point, because the fixture is where the blackout table lives."""
    return {f: title[f] for f in RESULT_FIELDS if f in title}


def search(args: dict, catalog: dict) -> dict:
    """Search the catalog. Returns `{"results": [...]}` per `schema.out.json`.

    `brand` and `type` are structured filters; `query` is free text over the
    fields a viewer would name. Ranking is by how many query terms a title
    matches, and ties keep catalog order — so the result is a pure function of
    (args, catalog) with no dependence on dict iteration or on when it ran.

    **A query with no usable terms returns nothing, not everything.** The input
    schema says it "deliberately cannot express 'give me everything' — an
    unbounded query is how the whole catalog ends up back in the model's context,
    which is the failure mode M02 exists to remove." A degenerate query that
    quietly matched every row would reintroduce exactly that, and it would do it
    on the request the model is most likely to send when it has no idea what to
    ask for."""
    terms = _terms(args.get("query", ""))
    limit = args.get("limit")
    limit = DEFAULT_LIMIT if limit is None else min(int(limit), MAX_LIMIT)

    scored = []
    for position, title in enumerate(catalog.get("titles", [])):
        if args.get("brand") and title.get("brand") != args["brand"]:
            continue
        if args.get("type") and title.get("type") != args["type"]:
            continue
        hay = _haystack(title)
        hits = sum(1 for term in terms if term in hay)
        if hits:
            scored.append((-hits, position, title))

    scored.sort(key=lambda s: (s[0], s[1]))
    return {"results": [_row(title) for _, _, title in scored[:limit]]}
