# M09b — journal notes, kept as the milestone runs

**Not the journal.** The journal is written at the close by `close-milestone`. This
file holds findings that must not wait for it — corrections to already-merged text,
measurements taken between PRs, and anything a later PR would otherwise re-derive.
Append-only in practice: an entry that turns out wrong gets a superseding entry
beneath it, never an edit.

---

## PR 1d (2026-09-12) — a correction to PR 1c's merged body, measured

**PR 1c's body attributes its check-count delta to its own citations, and the
attribution is wrong.** `docs/pr-bodies/m09b-pr1c.md:5-9` reads:

> `make check`: **4492 passed, 8 skipped**, PASS — against **4481 on `main` at
> 74cdd27** … The +11 are all `test_cited_commits_resolve`: three cases from the SHAs
> the amendment cites, **eight more from this body file**, each SHA generating a
> resolve and a reachability case.

**Measured at PR 1d, against the merged tree:**

- **The body file contributes five parameterized cases, not eight.** The scanner at
  `tests/test_cited_commits_resolve.py:89` matches **backticked** hex runs only:

  ```
  SHA = re.compile(r"`([0-9a-f]{7,40})`")
  ```

  and `SHA_CITATIONS` is one entry **per occurrence per file**.
  `docs/pr-bodies/m09b-pr1c.md` carries five such occurrences: `479972e` **twice**,
  `33e5871`, `d625033`, `850728e`.
- **`74cdd27` appears in that file unbackticked and matches nothing.** It is the one
  SHA the sentence's arithmetic would have needed.
- **One occurrence generates one case, not two.** There is a single parameterized test
  over `(doc, sha)` —
  `test_every_cited_commit_is_reachable_from_a_ref` at
  `tests/test_cited_commits_resolve.py:172` — which asserts `cat-file -t` and
  reachability inside one case. *"A resolve and a reachability case"* describes two
  assertions in one case, not two cases.
- **The amendment's own contribution is two, not three.** ADR-076's added lines carry
  two backticked SHAs, `479972e` and `850728e`; the audit note's *"three SHAs the
  amendment cites (d625033, 3f81fe6, 850728e)"* names two that sit inside a fenced
  measurement block and are not backticked. The count 3 in
  `milestones/M09b/pr1c-deletability-audit.txt` matches the observed 4481 → 4484 step;
  the three SHAs it names do not explain it.

**So the sentence's account of the +11 does not hold, and no replacement attribution
is offered here.** Seven of the eleven are accounted for by backticked citations in
the two added documents; the remaining four are not attributed, and attributing them
after the fact from a tree that has since moved would be the same error one level
down.

**Disposition: recorded, not corrected in place.** No PR is opened against the merged
PR 1c body. A merged PR body is a dated artifact and this repository annotates those
rather than rewriting them (ADR-035 amendment 9's treatment of the M02 record). What
changes going forward is the rule, and it is in `SPEC/09b`'s Definition of done for
PR 1d and in every later PR body:

> **Give the count and the commit, or give nothing.** `make check`: *N* passed, *M*
> skipped, at *commit*. No attributed delta unless each contributing case is named and
> the attribution was measured rather than reasoned.

**Owner:** PM + Platform Engineering. **Trigger:** none — this is closed by the rule
above being followed, and a PR body publishing an attributed delta without the
per-case measurement is the finding.

---

## PR 1d (2026-09-12) — `phrasings.yaml` declared no `frozen_before`

Recorded here because it crosses two documents. ADR-076 amendment 1's *four corpora
that declare no freeze* states *"Every other corpus in `quality/adversarial/` declares
both"*; `phrasings.yaml` declared `frozen_at: 2026-08-20` and `frozen_because` and no
`frozen_before`, so it was a fifth instance. The declaration is added at PR 1d — with
the measurement rather than an inference — because ADR-077 makes `PHR-002`, `PHR-003`,
`PHR-004` and `PHR-005` admissibility gates and the declaration becomes load-bearing.
The reasoning is ADR-077's appendix; the pointer is at the end of ADR-076. **The four
corpora the amendment names are unaffected and stay owed to Security / Red Team.**
