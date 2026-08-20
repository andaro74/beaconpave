<!--
The judge's user turn. **Owning seat: AI Quality. Two-key** — `quality/judge/` is
a two-key path, and this file is model-facing instrument text: a word changed
here changes every band the judge returns, and therefore every score derived
from them.

It lives in a file, and is hash-pinned by `user_turn_sha256` in
`quality/judge/frozen.json`, because for the whole of instrument A it did not.
The template was a Python string inside `evals/judge.py`, whose own docstring
said "this is instrument text, so it lives beside the prompt rather than in the
runner: a word changed here changes every band" — and no digest covered it.
`evals.judge.user_turn` could be replaced wholesale with unrelated text and
`is_frozen()` still returned `True`. Two different instruments would have
recorded the same fingerprint, which is the one thing the `instrument` field
exists to make impossible.

**Nothing from the case's `asserts` reaches this template.** A judge holding the
golden expectations is not scoring an answer, it is checking a diff — and it
would then agree with the deterministic half by construction, which is the one
result that could prove nothing at all.

**The labels avoid the classifier's vocabulary, and that is a constraint on this
file, not a coincidence.** Instrument A opened with `VIEWER QUESTION:` /
`VIEWER CONTEXT:`. `viewer` is a `SUBJECT_TERM` in
`platform/gateway/core/classify.py`, so a case whose recorded answer happened to
contain an `ATTRIBUTE_TERM` — `entitlement-012`'s answer says the event "may be
listed under a different name" — classified `sensitive` and was refused in 3 of
3 samples. The subject half came from the instrument; the attribute half came
from the answer. Identical text under these labels routes `allowed`.

The fix is here and **never** in `classify.py`: weakening a live control to
suit an instrument is the trade this repo exists to refuse. The control was
right — the judge really was sending it a subject term. `tests/test_judge.py`
pins that every golden case, rendered through this template against every
recorded answer, survives `classify.route`.

Everything below the `---` is sent to the model. This comment is not.
-->
---
QUESTION AS ASKED: {question}
REQUEST CONTEXT: plan={plan} dma={dma}

ANSWER AS RECORDED:
{answer}

CITED TITLE IDS: {cited_titles}

AXES: {axes}
