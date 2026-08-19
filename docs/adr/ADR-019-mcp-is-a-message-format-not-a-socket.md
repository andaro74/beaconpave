# ADR-019: MCP is implemented as messages, not as a transport

**Status:** Accepted (M02)
**Seats:** Tool Owner (the server) · Platform Engineering (how the gateway reaches
it) · Security / Red Team (a transport must not be able to authorize)

## Context

BUILD.md's M02 row calls for "`catalog-search` as an MCP tool", and the repository
map describes `tools/` as MCP tools. Neither says what that has to mean at a scale
where the whole catalog is five titles and the only caller is one Lambda.

The obvious reading is a server process the gateway talks to over stdio. That is
what MCP looks like on a developer's machine, and it is the wrong shape here: a
subprocess spawned per tool call inside a Lambda buys nothing, adds a cold start
to a suite whose p95 budget is already breached across two milestones, and puts a
process boundary in the middle of a control path for the sake of resembling a
diagram.

The opposite reading — "MCP means the tool has committed input and output schemas"
— is not defensible either. That is just a function with a contract, and calling
it MCP would be the kind of claim this repo exists not to make.

## Decision

**The protocol is implemented as messages. The transports are adapters over one
`dispatch` function.**

`tools/catalog-search/server.py` implements a JSON-RPC 2.0 subset — `initialize`,
`tools/list`, `tools/call` — and exposes it three ways: `dispatch(request)` for an
in-process caller, `main()` for line-delimited stdio, and `handler(event, context)`
for Lambda, where the event *is* the request. All three carry the same messages,
and a test asserts the Lambda path and the stdio path answer identically. Where
the wire is not real, the wire *format* still is.

**The subset is named rather than implied.** No SDK, no notifications beyond
ignoring them correctly, no resources, no prompts, no sampling. What is
implemented is what a tool plane needs to discover a tool and call it.

### The invariant this is really about

**A transport must not be able to authorize.** If the MCP server could, G3 would
become a property of whichever transport happened to be in front of the tool, and
a second route to the same tool would be a route nobody authorized. So the server
imports neither `cedar` nor `toolplane`, and the test that says so reads the
module's imports as source rather than exercising its behaviour — what a module
*can* reach is a stronger statement than what it did, and it covers the call
nobody wrote a case for. That is `test_hermeticity.py`'s technique, borrowed for
the same reason.

The corollary is that the server refusing `tools/call` for a tool it does not host
is **not** an authorization decision. It is a server saying it does not host that
tool. Different sentence, different owner, and worth stating because the two look
identical in a log.

### One identifier, end to end

The registry id `catalog-search` is used verbatim as the MCP tool name, the Cedar
resource, and the model-facing name in Bedrock's `toolConfig`. That was measured
before it was assumed — Bedrock accepts a hyphenated tool name — because the
alternative was a mapping layer between `catalog-search` and `catalog_search`, and
a mapping layer is a thing that gets out of step. The one that does not exist
cannot.

## Consequences

**`main()` is not the path the gateway uses**, and pretending otherwise would be
the dishonest version of this ADR. It exists because a tool that can only be
reached by the component that happens to embed it is not a tool, and because the
stdio path is what an outside MCP client would use. It is exercised by tests
rather than by production, and this sentence is here so that fact is recorded
rather than discovered.

**The tool deploys as its own function**, so the process boundary that matters —
the one that keeps the tool's role separate from the gateway's, and lets the
gateway hold `lambda:InvokeFunction` on exactly the tools the registry names —
exists where it does work, rather than around a subprocess where it would not.

**A second tool at M06 inherits all of this** by implementing three methods. If it
does not, the shape was wrong here.

**At scale, replace with:** Bedrock AgentCore Gateway or a hosted MCP server per
tool, with the same messages over HTTP and the plane in front of it unchanged. The
interface already matches — `dispatch` takes a request and returns a response, and
only what carries them changes.
