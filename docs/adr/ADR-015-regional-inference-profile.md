# ADR-015: The regional (`us.`) inference profile, and the 10% premium it costs

**Status:** Accepted (pre-M00b)
**Seats:** Platform Engineering (model access path) · Data Governance (residency)

## Context

Haiku 4.5 cannot be invoked by its base model ID. It reports
`inferenceTypesSupported: [INFERENCE_PROFILE]`, so an on-demand call fails with
a `ValidationException` telling you to pass an inference profile instead. Two
profiles are `ACTIVE` for this account in `us-west-2`:

| Profile | Routing |
|---|---|
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Regional — traffic stays in US regions |
| `global.anthropic.claude-haiku-4-5-20251001-v1:0` | Global — dynamic routing for availability |

BUILD.md pinned the `us.` profile because it was the one verified by invoke.
That was a verification artifact, not a decision — nobody had compared it with
the alternative.

**Regional endpoints carry a documented 10% pricing premium over global**, for
Sonnet 4.5 and every model after it, which includes Haiku 4.5. So the pin that
arrived by accident is the more expensive one, and nothing in the repo said so.

## Decision

Keep `us.`, and record it as a choice rather than leaving it as an accident.

The premium buys guaranteed geographic routing. beaconpave models a media
company whose whole governance story is classification-driven routing (G5),
data-handling rules owned by a Data Governance seat, and an audit lake that
adversarial probes grep. A platform that claims to route by classification while
letting inference land wherever capacity happens to be would be telling two
different stories about where data goes. The regional profile makes the demo's
residency claim true rather than implied.

The cost is 10% on a workload that bills fractions of a cent per request and
nothing at all while idle (G10). At this scale the premium is real and
immaterial; the point of recording it is that the *ratio* is what survives
scaling, not the amount.

## Consequences

Every recorded cost figure carries the premium. Because budgets are
token-denominated (ADR-014), the premium never touches a blocking assert — it
appears only where dollars are rendered, and the rate table there must be the
regional one. Pricing a regional workload at global rates would understate spend
by 10% in exactly the artifact meant to report it honestly.

`global.` remains one string away. If a later milestone needs availability more
than residency — a drill, a load test, an outage — switching is a one-line
change, and this ADR is what tells the next reader that the switch has a cost
implication and a governance implication rather than being free.

BUILD.md keeps the single pinned ID and now points here for why.

**At scale, replace with:** the same regional pin, chosen per workload rather
than per repo, driven by the data classification already declared in each
service's `pave.manifest.yaml` — `sensitive` and `confidential` pinned
regionally, `public` free to route globally. That mapping is exactly what the
manifest's `classification` field exists to express, so the interface already
matches; only the routing table behind it is missing.
