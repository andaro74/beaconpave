# catalog-search

The Beacon catalog, as a tool rather than as a prompt. Consequence class **read**.

Every milestone up to M01 answered by inlining the whole catalog into the system
prompt — the shape inherited from the ungoverned control. From M02 the model asks
for rows and gets the ones it asked for.

| | |
|---|---|
| Contract | [`schema.in.json`](schema.in.json) · [`schema.out.json`](schema.out.json) — committed, and not modified by M02 |
| Implementation | [`search.py`](search.py) — pure, hermetic, in `HERMETIC_ROOTS` |
| Registry | `platform/registry/tools.yaml`, callers `highlights-agent` and `recap-agent` |
| Reached through | the tool plane, which authorizes against the registry via Cedar (G3). Never called directly |

## What it will not do

**It does not serve the blackout table.** `data/catalog.json` carries `dmas` and
`blackouts` beside `titles`; this tool reads neither. Entitlement and blackout are
`entitlement-check`'s at M06, and splitting them is what makes the trajectory eval
meaningful — a tool that answered both would let the agent infer entitlement from
context while a tool call in the trajectory made it look as though a tool had
decided. Rows are projected onto an allowlist, so a field added to the fixture is
invisible until it is added to the schema too.

**It does not express "give me everything".** The input schema says so in its own
description, and a query with no usable terms returns nothing rather than
everything — the quiet way an unbounded query puts the whole catalog back into
the model's context is the failure mode M02 exists to remove.

**It does not sanitise what it serves.** Pointed at `data/catalog_poisoned.json`
it returns the injected title verbatim. Defusing it here would make ADV-002
unmeasurable while looking like a security improvement: the open path would stop
being visible without stopping being open. Whether tool output is assessed is the
tool plane's question, deferred to M04 on the record in SPEC/02, with the
observation committed as the evidence that the path is open.

**It does not decide anything.** No authorization, no entitlement, no policy. A
tool that authorized itself is not authorized.

## Layout

`tools/catalog-search/` is a deployment bundle, not an installed package — a
hyphen cannot appear in a Python package name. The directory goes on `sys.path`
and the module resolves as `search`, which is how the MCP server process resolves
it too. Same shape and same reason as `platform/gateway/`.

Owning seat: **Tool Owner** (the tool and its schemas) · Platform Engineering (the
plane it is reached through).
