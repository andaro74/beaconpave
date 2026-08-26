# `pave new` was a stub advertising four things it did not do, and nothing had ever compared the template to the service it copies

ADR-047. M05's PR 5. **Zero model calls, no new dependency, no recorded number
moved, no threshold lowered.**

## What was open on `main`

- **`pave new` printed a sentence and exited 0**, advertising `gate.yml`,
  CODEOWNERS, "wire SDK" and "enable tracing". M05 builds no per-service lane,
  ADR-013 records that CODEOWNERS collects nothing here, and writing to
  `.github/CODEOWNERS` would contradict creates-only. A stub listing four things it
  does not do is worse than one listing none.
- **`templates/agent-tools/` was one README.** Nothing compared it to
  `services/highlights-agent/`, so a template could have drifted for four milestones
  with nothing red.
- **`brand` was enforced by a `print()`.** `meridian-sports → meridian-news` was
  1889 passed.
- **The adversarial lane's onboarding message was unfollowable.** It told a service
  with no comparator to run `services/<svc>/run_probes_via_gateway.py --k 3` — a file
  `pave new` does not render and that a team cannot write, because that path is on a
  `(security, platform-eng)` rule. The first instruction the lane gave a scaffolded
  service could not be followed.
- **The demo script's Act 1 was wrong in four ways**, including a
  `--classification` flag that does not exist and a claim of *"manifest verification
  at deploy"* that ADR-046 records as explicitly not built.

## What this adds

`pave/scaffold.py` (mechanism), five `.tmpl` files, `tests/test_scaffold.py`
(29 tests), and the `pave new` dispatch.

**All five files are `.tmpl`, and SPEC/05 said two were verbatim.** Both of those
carry the reference service's identity — `answer.schema.json`'s `$id` and `title`,
and the golden README's heading. Two services rendered verbatim would have collided
on the one field a JSON-Schema resolver keys on.

**The pairwise check is a round-trip, which is stronger than the byte-identity the
spec asked for and is the only form a placeholder-carrying file admits:** render the
template with the reference service's *own* values and you get the reference file
back, byte for byte. That catches an edit on either side. It is only expressible
because the templates were derived rather than retyped.
`test_the_pair_list_covers_every_rendered_file` asserts all five pairs are covered —
four tests over five files leaves one template comparable to nothing, and that is the
one that drifts.

**The scaffold fails its own gate, and the row set is asserted exactly.**
`pave verify` refuses a fresh scaffold with rows **3** (the registry grant) and **8**
(twenty golden cases nobody has written) — each an onboarding step `pave new` may not
take. Draft 4's DoD implied the scaffold is green, which proves nothing: an unknown
service was 1861 passed before ADR-046, invisible rather than correct. Asserting the
exact rows matters too — a scaffold failing for a *third* reason has a defect in it,
and "not green" would hide that.

**The onboarding seat count is computed from `twokey.RULES`, not written down.** The
spec's banner said **five**; it is **three** (`ai-quality`, `legal-sp`,
`tool-owner`). `security` and `platform-eng` entered that count solely through the
probe-runner rule, and this renders no probe runner. Over-stating is not the safe
direction: `evaluate()` reports only *missing* seats, so surplus dispositions pass
silently and a banner that over-states teaches every team to attest past rules it
never triggered.

**The sports cut becomes a check, and the cut itself was stated wrongly.** The
blocker is not the brand — a *fictional sports* title with an event, a start time and
`sports-tier` is the identical **16 failures**, because the cascade is the judge
freeze and it is brand-blind. The real cut is narrower: a scaffolded service may
reuse the committed catalog titles, and any service needing its own content is
blocked for any brand. Now asserted, and red the day a title id is renamed.

## The deletability audit

19 mutations, full suite each. **18 caught, 1 silent** — changing the template's
`provenance.author` away from `pave-template` was **2053 passed**. Prediction 8's
test could not see it: with three rows counting as disposed the pack is still 3
against a floor of 20, so row 8 still fires and the row set is unchanged. The test
read the **tally**; the defect was in the **marking**. That is ADR-045's "a count
sees arithmetic, not identity", arriving in a check written against it — and what it
would have cost is a template teaching, by example, that rows it wrote count toward
the floor a team must clear. Now caught.

Two further gaps were closed *before* the audit, both by writing the test rather
than reading: nothing exercised the CLI wrapper's exit codes (the exact gap that
produced ADR-046's one silent mutation), and `scaffold_new` called `relative_to`,
which raises `ValueError` — a traceback in the first command a team ever runs.

## Also in this PR

`docs/governance/demo-script.md` Act 1 is reconciled with what the command does,
including saying out loud that there is **no manifest verification at deploy**.
`recap-agent` stays as the scaffolded name deliberately: ADR-048 removed that
registry entry, and scaffolding a name the repository has never heard of is exactly
the case M05 exists to stop being invisible.

## What this does NOT do

**No deploy.** *"Deployed, traced, metered, guarded agent in minutes"* was never
true. **No second brand** — M08's. **No probe runner, no `gate.yml`, no CODEOWNERS
entry.** **No `pave update`**: a template fix does not reach an existing service, and
`template: agent-tools@0.1.0` sits in every rendered manifest unread. **It cannot
tell a real disposition from a flipped field** — `disposed()` makes the default
honest and the lie deliberate, not impossible.

## Verification

Full suite **2072 passed**, ruff clean, hermetic, zero model calls, no new
dependency. `pave verify --all` exit 0 on the committed tree; a scaffolded service
exits 1 with two named findings. `COLLECTED_FLOOR` re-seated 1993 → 2072 after
staging.

**This PR gates itself under the rule it adds** — five seats across four rules.

Two-Key-Disposition: platform-eng
Two-Key-Disposition: ai-quality
Two-Key-Disposition: tool-owner
Two-Key-Disposition: security
Two-Key-Disposition: legal-sp
Two-Key-Rationale: A template edit sets the default tool set, case floor, headroom
  expectation and wire text for every service that does not exist yet, and none of
  those services can review the diff — which is why the template takes four seats
  where a single service's manifest takes two. security joins on the merits rather
  than for balance: the template carries user_turn, the wire text of every
  observation every scaffolded service will ever be judged on, and no instrument
  digest covers the transport; it also decides which tool a new service declares by
  default, which is an authorization claim made for teams that cannot yet object.
  tool-owner for that declared tools block, ai-quality for the case floor and the
  scaffold pack, platform-eng for the mechanism. legal-sp arrives through the
  seat-set pin file rather than through a new rule. The diff moves no threshold
  downward and no recorded number: the one floor that changes rises, the scaffold is
  built to FAIL its own gate rather than pass it, and the onboarding attestation
  count is computed at print time so it cannot drift from the rules it describes.
