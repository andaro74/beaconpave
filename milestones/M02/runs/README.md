# M02 run evidence

Every run of both arms, committed as-run. Nothing here is edited, and a discarded
run would stay beside its replacement — SPEC/02's INFRA rule exists so that "we
re-ran it" is a thing a reader can check rather than a thing they are told. No run
was discarded: all six returned 25/25 cases.

Both arms ran on **2026-08-19**, against the same deployed gateway, the same
pinned guardrail version 1, and the same model profile.

Scored with `python -m evals.run_evals --answers <file> --target highlights-agent`;
summarised across k with repeated `--answers` plus `--arm`; diffed with
`--against`.

## The result

| | control (frozen M01 arm) | tools (M02 arm) | delta |
|---|---|---|---|
| sample 1 | 18/25 | 14/25 | |
| sample 2 | 16/25 | 15/25 | |
| sample 3 | 14/25 | 14/25 | |
| **majority (k=3)** | **17/25** | **16/25** | **−1** |
| pooled | 48/75 = 0.6400 (16.0/25) | 43/75 = 0.5733 (14.3/25) | −1.7 |
| guardrail refusals | 19/75 | 7/75 | **−12** |
| p95 latency | 3171 ms | 8437 ms | +5266 ms |

**Paired per-case diff, control → tools** — the result ADR-021 designates:

```
lost   3: blackout-008, recommend-013, recommend-014
gained 2: blackout-007, concise-022
net    -1
```

## The pre-registered prediction is falsified

SPEC/02 predicted **10/25 ± 4**, a delta of **−6 to −13**. The measured delta is
**−1** by majority and **−1.7** pooled. Both are far outside the band, and both
are in the direction that flatters the system under test.

Recorded as-run. Nothing is adjusted, and the prediction in SPEC/02 stays exactly
as written — a prediction edited after the run is not a prediction.

Three reasons, and the first is a methodological error worth naming precisely.

### 1. Loss mechanism #3 went the other way, and it was the largest effect

SPEC/02 pre-registered *"mid-loop guardrail refusals"* as a loss: a longer turn
hands the guardrail more of the model's own reasoning to assess, and the pilot
measured refusals rising 2/15 → 5/15 after the retrieval narrowing.

Refusals **fell**, 19/75 → 7/75. The control arm inlines the whole catalog —
including the blackout table and the DMA list — and that is entitlement-flavoured
text sitting in every single prompt. `TOPIC:entitlement-circumvention` fires on
it. Taking the catalog out of the prompt took the trigger out with it.

> **CORRECTION, 2026-08-21. The paragraph above is wrong, and the rest of this
> file is not.** It is left standing because a milestone record edited to look
> right afterwards is not a record; this is what was believed on the day, and this
> is what is now known.
>
> The claim cannot be true as arithmetic. The control inlines that catalog on
> **every** call, so a guardrail assessing it would have refused **75 of 75, not
> 19**. It does not assess it — `converse` never sees the system block as content,
> which M04's channel control and ADR-035's pre-flight both measure directly, and
> which is why the M02 control arm ran at all.
>
> What the refusal surface actually was, measured under the same guardrail version
> ADR-035 kept alive (`milestones/ADR-035/topic-baseline-v2.json`, `k=3`,
> unanimous): **2 of 25 user turns** blocked at `INPUT` (`blackout-001`,
> `blackout-009`) and **2 of 22 committed answers** blocked at `OUTPUT`
> (`blackout-007`, `multi-023`). The viewer's question and the platform's own
> correct reply — not the prompt.
>
> **Which of those two channels produced the 19 → 7 difference cannot be
> recovered.** M02's audit records carry no channel field: `core/guardrail.py`'s
> `interpret` reads both `inputAssessment` and `outputAssessments` and flattens
> them into one list, discarding which side fired (ADR-035 amendment 8). So the
> honest state of this row is *the numbers, with no mechanism* — and the mechanism
> it used to assert was the flattering one, because it made a control look
> understood.
>
> The measured delta, the falsified prediction and every count in this file stand
> unchanged.

**The error was in how the mechanism was derived.** The pilot measured the tools
arm twice — before and after the retrieval narrowing — and never measured the
*control's* refusal rate on the same cases on the same day. A within-arm
comparison was written down and then applied as a between-arm one. The number
2/15 → 5/15 is real; it is just not the number the delta needed.

This is a benefit of the tool plane that nobody registered, and it is the single
biggest term in the result: roughly four cases per sample that the control loses
to a guardrail false positive and the tools arm keeps.

### 2. The comparator moved, and half the predicted delta was against a baseline
that does not exist

The prediction of 10/25 was framed against M01's recorded 19/25. The re-measured
control is **17/25** by majority and **16.0/25** pooled. A −9 prediction against
19 is a −7 prediction against 16 before anything else is counted.

SPEC/02 disqualified 19/25 for being n=1 and was right to; what it did not do was
carry that correction into the number it predicted.

### 3. Mechanism #4 held, partly, and exactly where it was checkable

`recommend-013` and `recommend-014` both lost, as pre-registered, on
contract-cannot-express. `recommend-003` did not — the smoke test on 2026-08-19
had already shown it retrieving `t003` through the structured filters, and that
observation is recorded in SPEC/02 before this run. `multi-023` fails in **both**
arms, so it is not a loss the tool plane caused.

## Things a reader should not misread

**The tools majority (16) is above every individual tools sample (14, 15, 14).**
That is arithmetic, not a bug: the majority is taken per *case*, and different
cases fail in different samples, so a case passing 2-of-3 counts as a pass even
though no single run contained all of them. It is the clearest demonstration in
this milestone of why AI Quality insisted the pooled mean be recorded beside the
majority — the two answer different questions and they differ by 1.7 cases here.

**Both majorities exceed their pooled means**, which is the polarization derived
before the run (`3p² − 2p³`). It did not widen the delta as predicted; with both
arms above p = 0.5 per case it lifted both.

**The control arm's four-point spread is the finding that justifies k = 3.** Three
samples of an identical system — same prompt, same guardrail version, same day —
returned 18, 16 and 14. The tools arm returned 14, 15, 14. A single sample of
either arm could have produced a headline anywhere from −4 to +1.

**The guardrail refusal rate breaches SPEC/01's threshold on the control arm.**
0–2 was pre-registered as expected and **≥3 as a miscalibrated guardrail**. The
control produced 5, 6 and 8. That belongs to the guardrail configuration and not
to the tool plane, and it is not tuned here.

**Refusals did not rise monotonically in the tools arm** (2, 3, 2) the way they did
in the control (5, 6, 8). The monotone pattern flagged after the control arm ran
is therefore not a property of the service on the day — it did not reproduce.

**Latency.** p95 rose from 3171 ms to 8437 ms against a 2500 ms budget: a third
consecutive milestone of breach, now much larger, and the tools figure **excludes
the tool round-trip** (`tool_ms` is reported separately, because `max_ms` was
derived from a harness that called the tool in-process — SPEC/02 records the gap).
Not raised.

**No tool call was denied by the plane on the golden set**, across all three
samples. 35 tool calls in sample 1 over 25 cases, maximum 4 in one turn, against
bounds of 6 rounds and 12 calls. The plane's refusals are evidenced by the runtime
G3 artifact, not by this suite.
