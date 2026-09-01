# The second tool gets a transport, and the conformance suite stops covering one tool

M06b step 2, second half. **Zero model calls.** Adds `entitlement-check/server.py`,
closes the ADR-043 shape Tool Owner named in the `SPEC/06b` review, and fixes a
latent path collision the previous PR planted.

## What lands

**`tools/entitlement-check/server.py`** — the MCP transport, structurally
`catalog-search/server.py`'s: same ADR-019 subset, same `dispatch`-is-the-protocol
shape, same two channels for the two kinds of failure (a JSON-RPC `error` means the
server could not answer; an `isError` *result* means the tool answered and the
answer is a failure, and `handler._call_tool` maps those to `routing` and `schema`).

It authorizes nothing. That is the invariant, and it is now asserted at class scope.

**The clock is deployment configuration**, per the previous PR's design.
`entitlement.check(args, catalog, now)` takes the instant as a required parameter;
`server.py` holds the deployed value and `serverInfo.clock` reports it as
provenance, for the same reason `serverInfo.catalog` reports the fixture — a tool
whose clock can move silently is an instrument that can move silently.

## `test_mcp_server.py` covered one tool, and could only ever cover one

Not an oversight in it. **Two bundles cannot both answer `import server`**: a hyphen
cannot be a package name, so the bundle root goes on `sys.path` and the last insert
wins. So the suite proving a tool speaks the dialect `handler._call_tool` sends was
structurally limited to the first tool, and the second tool's conformance was
nobody's test — an instance closed and the class open.

`tests/test_tool_servers.py` closes the class. It **discovers tools from
`platform/registry/tools.yaml`**, so a tool added there is covered the day it is
added rather than the day someone remembers to widen a tuple, and loads each server
**by path under its own module name** — the way the Lambda runtime resolves them.

## It found a third instance on its first run

`publish-highlight` is registered, carries a generated Cedar policy and a shipped
contract, and has **no implementation** — the same shape `entitlement-check` had for
four milestones.

Its absence is deliberate, so the check distinguishes *declared* from *accidental*
rather than being softened. `UNBUILT` carries the tool and the reason, and
`test_an_unbuilt_tool_is_declared_and_unreachable` makes the exemption load-bearing
in both directions:

- the entry must still be **registered** — a stale exemption is dead text that would
  silently cover a future tool of the same name;
- its consequence class must be in `cedar.GATED_CONSEQUENCES`, so **an exemption
  cannot quiet a tool a caller could reach**. `publish-highlight` is `publish`, so
  the generated policy carries a `forbid`;
- and if it ever *gains* a server, the test fails and tells you to remove it from
  `UNBUILT` so the conformance tests start covering it.

## A latent collision the previous PR planted, and this PR triggered

`test_entitlement_check.py` did `sys.path.insert(0, tools/entitlement-check)` at
module level and never removed it. Harmless while that folder had no `server.py`.

**Adding one made it live**: from that moment `test_mcp_server.py`'s bare `import
server` resolved to the *wrong tool's* server, and three of its tests failed in the
full suite while passing in isolation. The fix is the same technique the new file
uses — load by path under a name of its own — and it is verified under both
orderings, not just the one that happens to pass.

Worth stating plainly: I introduced this in PR 81 and it was invisible until the
file that collides with it existed.

## Two keys, and why

`tests/test_gateway_run_parity.py` — `('platform-eng', 'security')`. The previous
PR's `server.py` docstring said its `CLOCK` was *"pinned against the arms by
`test_gateway_run_parity.py`"*, and that test loops over three arm files, so the
claim was false as written. **Rather than soften the claim, the loop is widened** to
cover `tools/*/server.py`, discovered by glob so the next tool needing a clock is
covered when it is written. The arm-specific half of that test (no arm builds its
own user turn) is scoped away from tool servers, which do not build one.

## Deletability

Nine mutations, **nine caught**, none silent:

| mutation | caught by |
|---|---|
| `entitlement-check`'s server deleted | `test_every_registered_tool_has_an_implementation` (+8) |
| transport kept, logic deleted | same test, cleanly (8 failed); collection error too |
| a server learns to authorize (`from core import cedar`) | `test_no_tool_server_can_authorize` |
| `TOOL_NAME` stops matching the registry | `test_the_server_name_is_the_registry_id_verbatim` (+3) |
| **the server's clock drifts by a day** | `test_the_evaluation_clock_is_the_same_everywhere_it_appears` |
| published schema restated instead of read | `test_tools_list_publishes_the_committed_schema…` |
| an unbuilt tool quietly gains a server | `test_an_unbuilt_tool_is_declared_and_unreachable` |
| an unbuilt tool is made reachable (`publish` → `read`) | same |
| the exemption loses its reason | same |

The clock row is the one that proves the widening is not decorative.

## What this does not do

- **It does not deploy anything.** No `gateway-stack.ts`, no snapshot regeneration,
  no `TOOL_SPECS_SHA256` move, no routing-table pin. `TOOL_FUNCTIONS` is still
  `['catalog-search']`.
- **It does not touch `test_mcp_server.py`.** That suite is Tool Owner's and remains
  the deep instance-level coverage of `catalog-search`; the new file is the class,
  beside it rather than instead of it.
- **It does not close B11** — `entitled` is still deletable from the four-seat output
  contract on a green suite.
- **It does not build `publish-highlight`**, whose deployment is refused and whose
  scope question is open (ADR-055).
- **It scores nothing.** No comparator, threshold, golden case, history entry or
  instrument digest moves.

## Verification

```
$ python -m pytest -q      2358 passed, 6 skipped     # COLLECTED_FLOOR = 2255
$ python -m ruff check .   All checks passed!
```

Plus the ordering check the collision made necessary:

```
$ pytest -q tests/test_mcp_server.py                                     15 passed
$ pytest -q test_entitlement_check test_tool_servers test_mcp_server     55 passed
$ pytest -q test_tool_servers test_mcp_server test_entitlement_check     55 passed
```

Hermetic, no network, no new dependency.

Two-Key-Disposition: platform-eng
Two-Key-Disposition: security
Two-Key-Rationale: The only keyed file is tests/test_gateway_run_parity.py and the
  change to it is a widening, not a relaxation: the evaluation-clock parity loop now
  covers tool servers as well as the three arms, because the second tool must answer
  not-yet-started and therefore holds a clock, and the module holding it is one more
  place that value can drift. Discovered by glob over tools/*/server.py rather than
  listed, so the next tool needing a clock is covered when it is written rather than
  when someone remembers. The arm-specific clause in the same test, which forbids an
  arm building its own user turn, is scoped away from tool servers because they do
  not build one and asserting it there would be a check that cannot fail. The
  widening was planted: drifting the server's clock by one day goes red on exactly
  that assertion, so it is enforcing rather than decorating. This also makes true a
  claim the previous PR's docstring already made, that the tool server's clock is
  pinned by this test, which was false as written. No threshold, baseline, golden
  case, comparator or instrument digest moves, and nothing is deployed.
