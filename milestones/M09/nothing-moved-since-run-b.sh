#!/usr/bin/env bash
# PR 4b's precondition, executed rather than asserted.
#
# PR 4b's goldens run is a CONTROL: the question it answers is whether PR 4's one
# disclosure sentence moved the twenty-five. That question is only answerable if
# **nothing else the model sees moved between run B and this run**. So the path
# list here is PR 4's list PLUS the two model-facing sites that PR 4 itself moved
# — `TOOL_SYSTEM` in `gateway_client.py` and `answer.schema.json`'s
# `ai_disclosure` description. In PR 4 those two were excluded because they WERE
# the fix; here they must be frozen, because the fix is the one variable under
# test and a second edit to it would make this run read against a prompt run B
# never sent.
#
# BASE is PR 4's merge (369c8ba) and HEAD is this branch's tip. Empty, no
# carve-out. Output committed beside it as `nothing-moved-since-run-b.txt`.
set -e
BASE=369c8ba   # M09 PR 4's merge — the commit run B's prompt was committed at
HEAD=$(git rev-parse HEAD)
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
services/highlights-agent/evals/answer.schema.json
services/highlights-agent/gateway_client.py
"
echo "# BASE=$BASE (PR 4's merge)  HEAD=$HEAD"
echo "# git diff --stat BASE..HEAD -- <guardrail, policy, corpora, tiers, topics, catalog, TOOL_SYSTEM, answer.schema.json>"
git diff --stat $BASE..$HEAD -- $PATHS
echo "(nothing printed above means no line moved)"
echo
echo "# per path, name-only:"
for p in $PATHS; do
  n=$(git diff --name-only $BASE..$HEAD -- "$p" | wc -l | tr -d ' ')
  echo "  $p -> $n changed file(s)"
done
echo
echo "# and the WORKING TREE against HEAD over the same paths — a run reads the"
echo "# tree, not the commit, so an uncommitted edit is the same defect:"
git status --porcelain -- $PATHS
echo "(nothing printed above means the tree equals HEAD over these paths)"
