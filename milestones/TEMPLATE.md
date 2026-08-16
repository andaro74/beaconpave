# MNN — <milestone name>

**Branch:** `mNN-<slug>` · **Tag:** `mNN` · **Closed:** YYYY-MM-DD
**Spec:** `SPEC/NN-<name>.md` · **Claims advanced:** #N, #N

## What can I demo right now?

Commands, and what the viewer sees. Be concrete enough that someone else can
run it from a clean clone.

```bash
# ...
```

## What's the delta vs baseline?

| Metric | m00b (control) | mNN | Mechanism |
|---|---|---|---|
| Goldens | –/25 | –/25 | what actually caused the change |
| Adversarial | –/10 | –/10 | |
| p95 latency | – | – | |
| Cost/req | – | – | |

If a number improved and you cannot name the mechanism, say so. Unexplained
improvement usually means the test got easier, not the system better.

Unearned passes: <none, or list with reasons and the drafted tightening>

## What broke?

The honest section. Dead ends, wrong assumptions, things that only worked on the
third attempt, invariants that turned out to be inconvenient and why you kept
them anyway. A milestone journal with an empty "what broke" is not being written
honestly.

## Decisions

ADRs written or superseded in this milestone, with one line each on why.

## What's next

The single most load-bearing thing the next milestone must prove.
