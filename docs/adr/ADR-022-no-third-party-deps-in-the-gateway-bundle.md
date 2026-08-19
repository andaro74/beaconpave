# ADR-022: The gateway bundle carries no third-party dependency; subsets are bounded by differential tests

**Status:** Accepted (M02)
**Seats:** Platform Engineering (the bundle) · Tool Owner (the contracts being
validated) · Security / Red Team (both subsets sit on control paths)

## Context

`platform/gateway/` deploys via `lambda.Code.fromAsset` with **no bundling step at
all** — the directory is zipped as it stands. Everything it imports is either the
Python standard library or something the Lambda runtime already provides, which
today means `boto3` and nothing else.

M02 put two libraries in the gateway's path for the first time. Cedar evaluation
wanted `cedarpy`; validating tool arguments and results against their committed
JSON Schemas wanted `jsonschema`. ADR-020 declined the first and gave its reasons.
The second arrived immediately afterwards and is not the same question — a schema
validator is far more ordinary than a policy engine, and `jsonschema` is already a
declared dependency of this repo, used by the eval runner and the contract tests.

What makes it the same *decision* is the deployment shape, not the library.

## Decision

**No third-party dependency enters the gateway bundle.** Where the bundle needs a
capability a library would provide, it implements the subset it actually uses, and
**the subset is bounded by a check rather than by a promise.**

Two checks, and both are needed:

- **A coverage check.** `unsupported_keywords` walks each committed tool schema
  and a test fails if it uses a construct the validator does not implement. This
  fires at check time, where an unsupported keyword is a five-minute conversation,
  rather than at run time, where it would be a tool call silently validated
  against less than its contract says.
- **A differential check.** A corpus of payloads is validated by both this
  validator and `jsonschema` — available in the tests, absent from the Lambda —
  and the two must agree on every verdict. A third test requires the corpus to
  contain both verdicts, because a corpus of only-valid payloads agrees with a
  validator that accepts everything.

`jsonschema` remains a repo dependency for the eval runner and the contract tests.
This ADR is about the bundle, not the repo.

### It worked before it was written

The coverage check found two committed schemas using `pattern`, which the first
draft of the validator did not implement, before a single call was made through
the plane. The response was to implement `pattern` and extend the differential
corpus, not to widen the accepted set — which is the loop this ADR exists to
create. A validator that had silently ignored `pattern` would have accepted
`title_id: "T001"` against a contract that requires `^t[0-9]{3}$`, and nothing
would have reported anything.

One detail is worth recording because getting it backwards is easy and silent:
`pattern` is an **unanchored search** in JSON Schema, so the implementation uses
`re.search` rather than `re.match`. A validator stricter than its schema is as
wrong as a lax one and harder to notice, because it only ever refuses.

### And then the check itself turned out not to bound the subset

Three seats independently found the same hole in the first draft: **the coverage
check tested keyword *names*, not shapes.** `additionalProperties` was a supported
name, but only its `false` form was implemented — so a schema-valued one reported
"fully covered" and its subschema was then silently unenforced. Tuple-form `items`
did the same and afterwards raised an `AttributeError` out of the authorization
path, where `validate` is documented to return decisions rather than raise.

So "bounded by a check rather than by a promise" was not true when it was written.
It is now: shapes are checked, and type *values* are checked too, because
`{"type": "str"}` passed as covered and then rejected every instance at run time
with a message that read like a validator bug rather than a schema typo.

The lesson is narrower than "we missed a case". A boundary expressed as a list of
names bounds the vocabulary and not the language — and it is the second time in
this milestone that a check has been weaker than the sentence describing it.

### A divergence from the JSON Schema spec that is deliberately not fixed

`^…$` is anchored per line in Python's `re`, so `"t001\n"` matches
`^t[0-9]{3}$`. Under the ECMA regex grammar the spec names, it does not.

**This is not corrected here**, because `jsonschema` shares Python's `re` and
therefore shares the behaviour: "fixing" it would make this validator *stricter
than its reference* and break the differential test, which is the mechanism the
whole subset rests on. The divergence is from the spec, not from the library, and
the scale-up does not close it either — a bundled `jsonschema` behaves the same
way. Recorded rather than silently carried, since it is exactly the sort of thing
a later reader would otherwise find and assume was an oversight.

## Consequences

**This does not generalize to arbitrary libraries.** The argument works because
both subsets are small, both are exercised by a closed set of committed inputs,
and both have a reference implementation to be checked against. A capability with
none of those properties — a crypto primitive, a date parser, an HTTP client —
does not get a hand-rolled subset; it gets a bundling step and an ADR saying so.

**The subsets are allowed to grow, and growth is visible.** Adding a keyword means
adding it to `SUPPORTED_KEYWORDS`, implementing it, and extending the corpus. The
coverage test makes the first two mandatory; the differential test makes the third
worth doing.

**Two validators exist and could disagree.** That is the real cost, and it is paid
down by the differential test rather than argued away. The failure mode it guards
is specific: the eval suite and the contract tests validate with `jsonschema`, the
gateway validates with this, and a divergence would mean a payload that passes
`make check` and is refused in production — or, worse, the reverse.

**At scale, replace with:** a bundled runtime built from a lockfile, with the same
schemas validated by the same library everywhere and these subsets deleted. The
interface already matches — the plane asks "does this conform" and gets a list of
problems — and only what answers changes.
