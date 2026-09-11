#!/usr/bin/env bash
# "Nothing else moved", executed rather than asserted — SPEC/09 row 1c and the
# PR 4 box's `git diff` clause.
#
# The claim is that the deployed service's red is traceable to the RULE. That only
# holds if nothing else about the system under measurement moved between the
# milestone's open and the run: a guardrail line, a Cedar policy, a probe corpus
# row, a topic's wording, a tier, the token ceiling, or the catalog would each give
# a red a second possible author, and F4's comparator would differ from M08b's run
# by more than the fix.
#
# **Empty with no carve-out.** SPEC/09 constraint 4 took the DMA rename out of the
# milestone precisely so that `data/catalog.json` needs no exception here.
#
# The two model-facing sites — `TOOL_SYSTEM` in `gateway_client.py` and
# `answer.schema.json`'s `ai_disclosure` description — are NOT in this list: they
# move in PR 4 and they **are** the fix (constraint 2). They are priced by
# `tests/test_m09_prompt_delta.py` and named line by line by
# `tests/test_gateway_run_parity.py`.
#
# Run from the repository root. Output committed beside it as
# `nothing-else-moved.txt`.
set -e
BASE=66bb114   # M09 PR 1's merge — the milestone's open
HEAD=6644c1d   # PR 4's branch point (PR 7's merge)
PATHS="
platform/gateway/core/guardrail.py
platform/gateway/handler.py
platform/gateway/core/
platform/gateway/policy/
platform/infra/lib/gateway-stack.ts
platform/infra/tests/fixtures/BeaconpaveGateway.template.json
quality/adversarial/
data/catalog.json
services/highlights-agent/pave.manifest.yaml
services/highlights-agent/evals/golden/cases.yaml
"
echo "# git diff --stat $BASE..$HEAD -- <the guardrail, policy, corpus, tiers, topics, catalog>"
git diff --stat $BASE..$HEAD -- $PATHS
echo "(nothing printed above means no line moved)"
echo
echo "# per path, name-only:"
for p in $PATHS; do
  n=$(git diff --name-only $BASE..$HEAD -- "$p" | wc -l | tr -d ' ')
  echo "  $p -> $n changed file(s)"
done
