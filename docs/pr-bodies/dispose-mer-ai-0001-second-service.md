# MER-AI-0001 binds to `game-recap-agent`: a second disclosure pack, two readings in the fields the trace prints, and a control recorded as bound and unrun

Zero model calls. The second owed item from `docs/samples/game-recap-agent.md`,
discharged. The decision record is ADR-082, in this diff. Three seat rounds
(Legal/S&P, Security, AI Quality, Platform Engineering; advisory, G6) changed
the first draft in ways the ADR records under each decision.

## What it changes

- `services/game-recap-agent/evals/disclosure/cases.yaml` and its README: seven
  cases, five `required` and two `not_required`, each carrying `json_schema` and
  `ai_disclosure` and nothing else, on the reference pack's shape. The negative
  half is catalog facts, a kick-off time and a plan tier, because the service
  grants one read tool.
- `rules/MER-AI-0001.yaml`: a second `eval_pack` control bound to that pack; a
  dated reading appended inside `scope.covers` (a fact read off the catalog is
  not a summary; the line is summary versus bare fact, never the subject) and
  inside `scope.revives` (not triggered, and the state that would trigger it
  alone), each carrying its own date while `scope.decided_on` keeps the date of
  the operative sentences; a third `limits` entry recording the control as
  bound and unrun and the lane as manual, owed to the four seats that can close
  it; a fourth recording that the service sits outside the M09b guardrail, owed
  to Security. The operative sentences of `covers` and `excludes`, the
  phrasings and the scorer are unchanged.
- `tests/test_rules_trace.py`: the pin on the committed rule expects two
  `eval_pack` controls in order, both resolving; the walk test counts both
  packs and both `binds` lines; a cross-pack test asserts both halves, five
  required cases, identical phrasings across bound packs, the headroom
  exemption load-bearing and cited, own-service schema paths and a README per
  pack; a second test pins the two readings and the two limits by their
  sentences; a third pins the `revives` reading's premise in the manifest and
  the registry, so a second tool grant to the service is red citing the
  reading.
- `tests/test_m09_disclosure.py`: the five pack-quality tests and the three
  hermetic scoring tests parametrise over every `eval_pack` the rule binds; the
  module-level sufficiency assert is a test, so a struck control fails one test
  rather than aborting collection of the file.
- `docs/adr/ADR-082-…md` with a three-cell index row; the claim 6 row in the
  README now says two controls over fourteen cases; the sample record's owed
  bullet says what was done.

## Why

The rule is `enforced`, `blocking`, and binds to the service; its `covers`
reaches the previews, tiles and home-screen copy the second service writes.
Its only control bound to the reference service, so the trace printed one
`binds` line and the second service had no control at all.

## What this does not claim

ADR-075 disposed this rule by a delta someone read against a deployed service.
That cannot be repeated here: nothing can deploy `game-recap-agent`, and it has
no committed answers. The second control can fail the day a run exists and has
not been read against one. That is in the rule's limits, the pack, the ADR, and
here. No run, no claim, no history entry, no progression row.

## What the seat rounds found

Round one:

- **Legal/S&P.** The `revives` reading rested on a sentence false of the golden
  pack, was a YAML comment the trace cannot print, and did not name the state
  that fires the clause alone. One negative case sat inside `covers`. The
  third limit omitted the seats that can close it.
- **Security.** `required: [a]` on the second pack scored 7/7 PASS against the
  answer `"a"` with nothing red. The first draft's plant table credited the
  both-halves test with a catch it does not make. Seven pack-property plants
  were silent because the pack-quality tests were hard-scoped to the reference.
  The limit and the reading were deletable in silence.
- **AI Quality.** The pack header stated the headroom exemption inverted. Two
  viewers were blacked-out or unentitled for the title their case asked about.
- **Platform Engineering.** The index row had two cells; the both-halves test
  was vacuous on an empty control list and iterated every control type.

Round two:

- **Legal/S&P.** The ADR misstated which scope fields changed; the `covers`
  reading drew a subject-matter line; the scope date had moved when the
  readings carried their own; the pin held citations, not sentences.
- **Security.** The `revives` reading's premise, one tool granted, was
  detectable by nothing: a second registry-backed tool left `pave verify` PASS
  and the trace printing NOT triggered. The ADR said the reference pack's
  tokens were protected by its run; they are protected by three hermetic tests
  that were hard-scoped to it. The plant table credited a second-control plant
  with catches that never ran, because a module-level assert aborted collection.
  The limits were pinned by headline only.

Every one is fixed in this diff.

## Three decisions this PR records for the operator and does not take

Named by the Legal/S&P seat, recorded in ADR-082 under *What this does NOT do*,
and not written as limits because each is a decision rather than a boundary:

- the rule's scope names news copy as in scope, and both bound services are
  sports-brand with no news case in either pack;
- limit 1 names `publish-highlight` as the publication action, and the second
  service declares no publish-class tool, so its in-scope copy has no governed
  publication route;
- limits 3 and 4 are dated to a milestone that deploys a second principal,
  which is unscheduled, while `review_by` is 2026-10-01.

The Security seat adds a pairing for the operator: Legal/S&P owns the `revives`
clause, and whether a narrowing of a guardrail-adjacent scope may ship is
Security's; both keys are on this PR.

## Checked

- `python -m pave.cli rules validate`: valid, no orphaned control refs.
- `python -m pave.cli rules trace MER-AI-0001`: both controls walked, both
  `binds` lines, both readings and all four limits printed, 14 cases,
  RESOLVED, exit 0.
- Planted one at a time in the working tree against
  `tests/test_rules_trace.py` and `tests/test_m09_disclosure.py`, restored
  byte-identical between plants from backups named by full path. The
  first-round harness of this round backed up two files sharing a basename and
  restored the reference pack over the new one; the table below is from the
  re-run after that was caught.

| plant | caught by |
|---|---|
| a second tool declared in the service's manifest | `test_the_revives_readings_premise_holds_in_the_registry_and_the_manifest`, citing the reading |
| limits 3 and 4 gutted to their first sentence | `test_the_second_bindings_boundary_is_written_where_the_trace_prints_it` |
| both packs' tokens weakened to `a` | the two scoring tests parametrised over each pack, the whole-words test, and the lane test |
| only the new pack's tokens weakened | the cross-pack phrasings equality and the new pack's own scoring test |
| the second control removed from the rule | the controls pin, the walk test, and the binding-sufficiency test; not the both-halves test, which iterates the controls that remain |
| an undocumented assert key in the new pack | five tests, four of them parametrised over this pack by name |
| the reference pack copied over the new one | the cross-pack test, schema path names another service |
| a judge block, a who-won positive, the question-shaped positive reworded, the README deleted | one parametrised or cross-pack test each, by name |
| the bound-and-unrun limit deleted, the `revives` reading deleted | the boundary test |

- `ruff check` clean. `tests/test_rules_trace.py` and
  `tests/test_m09_disclosure.py`: 129 passed. `make check`: see the commit.

**What no test here can catch, stated.** A positive case reworded into a
factual lookup that is not a summary keeps its `required` mode and passes every
check; the tests read shape and words, not authorship, and only a run reads
authorship. The `revives` conclusion is held by its premise, not by its
wording: a substring pin cannot tell NOT triggered from a rewrite around it,
which the Security seat showed. That is why the directory takes two keys and
the rule three.

## Attestations

Two-Key-Disposition: legal-sp
Two-Key-Rationale: the rule now binds to both services that author copy its scope reaches, the covers and revives clauses each carry a dated reading against the second service in the field the trace prints with the state that would fire revives alone named and its premise held by a check in the manifest and the registry, the scope date stays with the operative sentences, and the disposition records its boundary as two limits pinned by sentence rather than implying a second delta
Two-Key-Disposition: security
Two-Key-Rationale: the counterweight sees a control added and nothing weakened, the phrasings and the scorer untouched, the revives narrowing now falsifiable by a second tool grant that fails a named test, the reference pack scoring tests parametrised over every bound pack so a weak token fails directly and the cross-pack equality kept beside them, the two readings and two limits pinned by sentence including the G4 line, a struck control failing one test instead of aborting collection, and the M09b guardrail gap for this service written as a limit owed to this seat
Two-Key-Disposition: ai-quality
Two-Key-Rationale: seven cases on the reference pack shape with exactly two asserts each, a negative half of catalog facts because the service has one read tool, entitled viewers outside the blackout markets so the answers are about the copy and not access, groundable without a recap, the headroom exemption cited and not made, authored before any run and recorded as unrun
Two-Key-Disposition: platform-eng
Two-Key-Rationale: the trace test pins the control list by equality, the cross-pack test filters on eval_pack and refuses an empty control list, the both-halves check reuses the lane's own sufficiency function, the index row carries its scale-up cell, no history-ordering pin path is touched, and the ADR names the scaffold gap and ADR-045's enumeration debt it belongs to

🤖 Generated with [Claude Code](https://claude.com/claude-code)
