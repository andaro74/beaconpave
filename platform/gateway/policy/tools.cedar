// GENERATED FROM platform/registry/tools.yaml — DO NOT EDIT.
//
// Regenerate with `python -m pave.cli policy generate`. A hand edit is reverted by
// the next regeneration and fails `tests/test_cedar_policy.py` in the meantime,
// which is the point: a policy that disagrees with the registry makes the registry
// look authoritative while something else decides (ADR-004).
//
// Cedar's own semantics decide the outcome: an explicit `forbid` beats any
// `permit`, and a request matching no `permit` is denied. Nothing here grants a
// default.


// --- catalog-search (consequence: read) ---

permit(
  principal == Service::"highlights-agent",
  action == Action::"invoke",
  resource == Tool::"catalog-search"
);

permit(
  principal == Service::"recap-agent",
  action == Action::"invoke",
  resource == Tool::"catalog-search"
);

// --- entitlement-check (consequence: read) ---

permit(
  principal == Service::"highlights-agent",
  action == Action::"invoke",
  resource == Tool::"entitlement-check"
);

// --- publish-highlight (consequence: publish) ---

permit(
  principal == Service::"highlights-agent",
  action == Action::"invoke",
  resource == Tool::"publish-highlight"
);

// consequence >= publish: unreachable until an approval interlock
// grants approval_granted. Declared approver: stepfn:editorial-approver
forbid(
  principal,
  action == Action::"invoke",
  resource == Tool::"publish-highlight"
) unless { context has approval_granted && context.approval_granted == true };
