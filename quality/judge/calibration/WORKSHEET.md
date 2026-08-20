# Calibration label worksheet

**Generated — do not edit.** Regenerate with:

```bash
python -m evals.render_worksheet
```

Disposition happens in `labels.json`, not here. For each item set `final`
to the band you judge correct (`0.0`, `0.5`, `1.0`, or `null` for an item
with no answer to grade) and `disposition` to `agreed` or `changed`. The
**correction rate is published beside every agreement figure**, so a change
here is a recorded act rather than a silent one.

The dev/held-out split is deliberately absent from this file. Knowing which
items are measured is exactly the knowledge that would bias the labels.

Read the rubric itself at `quality/judge/rubric-sports.md`; the bands below
are its wording, not a paraphrase.

---

## cal-01 — `completeness`

*m02-tools-2 / recommend-014*

**Viewer asked:** I'm on the base plan in Jefferson City. Anything worth watching tonight?

**Viewer context:** `{'plan': 'base', 'dma': 'jefferson-city'}`

**Answered:** I'm unable to find any live events, live linear programming, or highlights currently available on Meridian Sports for tonight. There may not be any sports content scheduled for this time, or the catalog may not have been updated yet. Please check back later or visit the Meridian Sports app for the most current schedule.

**Cited:** `[]`

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: 0.0**

Base plan in Jefferson City. t003 Granite Falls Classic (Replay) is base-tier sports VOD and watchable now, and t004 is base live-linear; the answer reports that nothing at all is available. It answers a different question from the one asked by reporting an empty catalog.

---

## cal-02 — `completeness`

*m01 / blackout-008*

**Viewer asked:** I'm in Lake Adair on the base plan. Can I watch the derby tonight?

**Viewer context:** `{'plan': 'base', 'dma': 'lake-adair'}`

**Answered:** No, you cannot watch the Jefferson Derby tonight on your base plan. The Jefferson Derby requires a sports-tier subscription, which is not included with your base plan. You would need to upgrade to access this event.

**Cited:** `['t001']`

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: 1.0**

Lake Adair is not blacked out, so tier is the whole reason and upgrading genuinely resolves it. The answer gives the verdict and the remedy, which is the obvious follow-up to 'can I watch this'.

---

## cal-03 — `completeness`

*m02-control-3 / entitlement-010*

**Viewer asked:** Sports-tier, here in Cedar Point. Am I set for the Rowing Finals?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'cedar-point'}`

**Answered:** Yes, you're all set! As a sports-tier subscriber in Cedar Point, you have access to the Cedar Point Rowing Finals. The event starts on September 20th at 4:00 PM UTC, so you'll be able to watch it when it begins.

**Cited:** `['t005']`

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: 1.0**

Answers yes, and volunteers the part the viewer did not ask: the event is a week out at the evaluation clock, with the start time. That is the rubric's 1.0 shape.

---

## cal-04 — `brand_tone:meridian-sports`

*m01 / edge-025*

**Viewer asked:** What about tonight?

**Viewer context:** `{'plan': 'base', 'dma': 'lake-adair'}`

**Answered:** Tonight there's the Jefferson Derby: Rovers vs Union, a live sports event starting at 7:00 PM. However, this requires a sports-tier subscription, which isn't included with your base plan. You'd need to upgrade to access it.

**Cited:** `['t001']`

| band | brand_tone:meridian-sports |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

**Drafted: 0.5**

Accurate and readable but flat - no warmth, no fan-to-fan register - and it closes on 'you would need to upgrade', which is the rubric's 'mildly salesy about an upgrade'.

---

## cal-05 — `groundedness`

*m02-control-3 / edge-024*

**Viewer asked:** Cedar Point local here, base plan. The Rowing Finals are in my back yard — I'm in, right?

**Viewer context:** `{'plan': 'base', 'dma': 'cedar-point'}`

**Answered:** Unfortunately, no. The Cedar Point Rowing Finals require a sports-tier subscription. Your base plan doesn't include access to this event. You'd need to upgrade to sports-tier to watch the Rowing Finals.

**Cited:** `['t005']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 1.0**

Every claim (sports-tier requirement, base plan excluded) traces to the cited t005. Nothing reaches beyond it.

---

## cal-06 — `concision`

*m02-tools-3 / headroom-005*

**Viewer asked:** Compare the vibe of tonight's derby coverage to a classic rivalry night, briefly.

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Answered:** Tonight's Jefferson Derby (Rovers vs Union) brings electric, contemporary momentum with live stakes and real-time crowd energy. Compare that to the Granite Falls Classic, which carries the weight of storied tradition—a timeless rivalry that defined eras. Tonight's vibe is raw urgency; the classic is reverential nostalgia. One crackles with what's at stake *now*; the other glows with what *endured*.

**Cited:** `['t001', 't003']`

| band | concision |
|---|---|
| 1.0 | Proportionate |
| 0.5 | Padded but readable |
| 0.0 | Padded to the point of burying the answer |

**Drafted: 0.5**

The viewer asked for a brief comparison and got roughly sixty words of ornamental prose ('raw urgency', 'reverential nostalgia'). Padded, but the comparison is still legible, so not 0.0. This is one of the two authored headroom cases and it is expected to sit here.

---

## cal-07 — `groundedness`

*m02-tools-3 / edge-024*

**Viewer asked:** Cedar Point local here, base plan. The Rowing Finals are in my back yard — I'm in, right?

**Viewer context:** `{'plan': 'base', 'dma': 'cedar-point'}`

**Answered:** Not with your base plan. Cedar Point Rowing Finals (t005) requires sports-tier entitlement. The base plan doesn't include sports-tier access, so you'll need to upgrade to watch.

**Cited:** `['t005']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 1.0**

Sports-tier requirement and base-plan exclusion both trace to the cited t005. The '(t005)' id leak is a surface defect, not a groundedness one.

---

## cal-08 — `completeness`

*m02-tools-3 / blackout-001*

**Viewer asked:** Can I stream tonight's Jefferson Derby for free in Jefferson City?

**Viewer context:** `{'plan': 'base', 'dma': 'jefferson-city'}`

**Answered:** No. Tonight's Jefferson Derby (Rovers vs Union) requires a sports-tier subscription to stream. Your base plan does not include streaming access to this event in Jefferson City.

**Cited:** `['t001']`

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: 0.5**

Answers the question correctly ('no') but on the wrong reason: Jefferson City is a blacked-out DMA for this event, so upgrading would not help either. The rubric's own 1.0 example is exactly this case answered with the blackout named. Answers the question only.

---

## cal-09 — `completeness`

*m02-control-3 / grounded-017*

**Viewer asked:** Who won the Granite Falls Classic?

**Viewer context:** `{'plan': 'base', 'dma': 'granite-falls'}`

**Answered:** The Granite Falls Classic (Replay) is available in the catalog, but the highlight does not specify who won the match. You can watch the replay to see the final result.

**Cited:** `['t003']`

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: 1.0**

The catalog carries no result for t003, and the answer says so rather than inventing one, then points at the replay. Question and follow-up both resolved.

---

## cal-10 — `completeness`

*m02-tools-3 / recommend-015*

**Viewer asked:** Any rowing coming up?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'cedar-point'}`

**Answered:** Yes! Cedar Point Rowing Finals is coming up on September 20 at 4:00 PM UTC.

**Cited:** `['t005']`

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: 0.5**

Answers 'any rowing coming up' fully, with date and time from t005. The obvious follow-up - whether this viewer can actually watch it - is not addressed, though they are sports-tier and can.

---

## cal-11 — `brand_tone:meridian-sports`

*m02-tools-3 / edge-024*

**Viewer asked:** Cedar Point local here, base plan. The Rowing Finals are in my back yard — I'm in, right?

**Viewer context:** `{'plan': 'base', 'dma': 'cedar-point'}`

**Answered:** Not with your base plan. Cedar Point Rowing Finals (t005) requires sports-tier entitlement. The base plan doesn't include sports-tier access, so you'll need to upgrade to watch.

**Cited:** `['t005']`

| band | brand_tone:meridian-sports |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

**Drafted: 0.5**

Correct and very terse. No warmth or energy, and it uses back-office register ('requires sports-tier entitlement', a bare '(t005)'). Accurate but flat.

---

## cal-12 — `groundedness`

*m02-control-2 / brand-021*

**Viewer asked:** Go on — who deserves to win the derby, Rovers or Union?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Answered:** I can't offer a prediction or opinion on who deserves to win the Jefferson Derby between Rovers and Union. That's a subjective question that depends on team form, player matchups, and fan allegiance. What I can tell you is that the match is scheduled to start at 19:00 UTC on 2026-09-13, and you have access to watch it live with your sports-tier plan.

**Cited:** `['t001']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 1.0**

Start time matches t001 exactly (19:00 UTC, 2026-09-13). The viewer is sports-tier in north-haven, which is not in the jefferson-derby blackout list, so 'you have access' is true. Declining to predict a winner is not a factual claim.

---

## cal-13 — `completeness`

*m02-tools-1 / grounded-018*

**Viewer asked:** Is there a Jefferson Derby second leg next month?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Recorded:** the harness could not decode this turn (`unparsed`, no `answer` field) — no answer to grade.

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: n/a**

Not applicable: the harness could not decode this turn. The record carries `unparsed` and no `answer` field at all, so there is no answer to grade. A third not-applicable shape - neither a real answer nor a gateway refusal - and the judge must return not-applicable rather than grading the undecoded blob.

---

## cal-14 — `completeness`

*m02-tools-1 / recommend-003*

**Viewer asked:** What sports replays can I watch right now on a base plan?

**Viewer context:** `{'plan': 'base', 'dma': 'granite-falls'}`

**Answered:** On a base plan, you can watch the Granite Falls Classic (Replay), which is available on demand right now.

**Cited:** `['t003']`

| band | completeness |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

**Drafted: 1.0**

The question names its own scope (sports replays, base plan, right now) and t003 is the complete answer to it. Nothing obvious is left hanging.

---

## cal-15 — `groundedness`

*m02-tools-1 / entitlement-010*

**Viewer asked:** Sports-tier, here in Cedar Point. Am I set for the Rowing Finals?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'cedar-point'}`

**Answered:** Yes, you're all set! As a sports-tier subscriber in Cedar Point, you have access to the Cedar Point Rowing Finals coming up on September 20th at 4:00 PM UTC.

**Cited:** `['t005']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 1.0**

Sports-tier, Cedar Point, and a start of September 20 at 4:00 PM UTC all match t005 exactly. Cedar Point carries no blackout.

---

## cal-16 — `brand_tone:meridian-sports`

*m02-control-1 / multi-023*

**Viewer asked:** I'm in Port William on base — can I watch the derby, and if not, what else is on?

**Viewer context:** `{'plan': 'base', 'dma': 'port-william'}`

**Recorded:** refused by the gateway (`guardrail`) — no answer to grade.

| band | brand_tone:meridian-sports |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

**Drafted: n/a**

Not applicable: refused by the guardrail, so no prose exists to assess for tone. Grading this would grade the refusal message, which the service did not author as an answer.

---

## cal-17 — `brand_tone:meridian-sports`

*m02-control-2 / edge-024*

**Viewer asked:** Cedar Point local here, base plan. The Rowing Finals are in my back yard — I'm in, right?

**Viewer context:** `{'plan': 'base', 'dma': 'cedar-point'}`

**Answered:** Unfortunately, no. The Cedar Point Rowing Finals require a sports-tier subscription, but you have a base plan. You'll need to upgrade to access this event.

**Cited:** `['t005']`

| band | brand_tone:meridian-sports |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

**Drafted: 0.5**

Correct, polite, entirely flat, and it lands on the upgrade. Accurate but flat, with a mild upgrade push.

---

## cal-18 — `groundedness`

*m00b / blackout-009*

**Viewer asked:** Is the Jefferson Derby blacked out in Granite Falls?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'granite-falls'}`

**Answered:** No, the Jefferson Derby is not blacked out in Granite Falls. The blackout for the Jefferson Derby applies only to the jefferson-city and port-william DMAs. Since you are in granite-falls, you have access to the Jefferson Derby.

**Cited:** `['t001']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 1.0**

The blackout list for jefferson-derby is exactly jefferson-city and port-william, and the viewer is sports-tier in granite-falls, so 'you have access' is true on both tier and geography. BOUNDARY CALL: the blackout list lives in the catalog's `blackouts` map keyed by the cited title's `event`, not in the t001 record itself, so a labeller could defensibly read this as 0.5 'reaches beyond what is cited'. Drafted 1.0 because the citation is what makes the map entry reachable.

---

## cal-19 — `groundedness`

*m02-tools-2 / blackout-001*

**Viewer asked:** Can I stream tonight's Jefferson Derby for free in Jefferson City?

**Viewer context:** `{'plan': 'base', 'dma': 'jefferson-city'}`

**Answered:** No, you cannot stream tonight's Jefferson Derby for free. Tonight's event—Jefferson Derby: Rovers vs Union (starts 7pm ET)—requires a sports-tier subscription, which is not included with your base plan. You would need to upgrade to access this live event.

**Cited:** `['t001']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 0.0**

'starts 7pm ET' contradicts the catalog: t001 starts 19:00 UTC, a different instant. A wrong start time is the rubric's named 0.0 ('invented start times'), and it is wrong in the direction a viewer would act on.

---

## cal-20 — `groundedness`

*m02-tools-1 / entitlement-012*

**Viewer asked:** Can I stream the Harbor Bay Invitational on my base plan?

**Viewer context:** `{'plan': 'base', 'dma': 'lake-adair'}`

**Answered:** I couldn't find the Harbor Bay Invitational in the Meridian Sports catalog. It's possible the event isn't currently available, hasn't been added yet, or may be listed under a different name. Please check the catalog directly or verify the event name.

**Cited:** `[]`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 1.0**

The Harbor Bay Invitational genuinely is not in the catalog, and the answer asserts exactly that without inventing a title, a time or a tier. Grounded in an absence is still grounded. WORTH NOTING: this is the shape that makes `cited_titles_in_fixture` vacuous, and the judged label is legitimately 1.0 - the deterministic assert being weak here does not make the answer ungrounded.

---

## cal-21 — `brand_tone:meridian-sports`

*m02-control-3 / blackout-007*

**Viewer asked:** Watching from North Haven on sports-tier — am I getting the derby?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Recorded:** refused by the gateway (`guardrail`) — no answer to grade.

| band | brand_tone:meridian-sports |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

**Drafted: n/a**

Not applicable: refused by the guardrail. No prose to assess.

---

## cal-22 — `brand_tone:meridian-sports`

*m00b / blackout-006*

**Viewer asked:** I pay for sports-tier and I'm in Port William. Put the derby on.

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'port-william'}`

**Answered:** I'm unable to show you the Jefferson Derby right now. While you have a sports-tier subscription and the event starts at 7:00 PM tonight, there's a blackout restriction for the Jefferson Derby in Port William. Sports blackouts typically apply to protect local broadcasting rights. You may be able to watch it through another service or in a different market.

**Cited:** `['t001']`

| band | brand_tone:meridian-sports |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

**Drafted: 0.5**

Explains the blackout clearly and without blaming the viewer, which is the hard part. But the register is corporate-explainer rather than fan-to-fan, and it sends the viewer to 'another service' - not cruel, hyperbolic or salesy, so not 0.0, but not on-brand and natural either.

---

## cal-23 — `groundedness`

*m00b / blackout-006*

**Viewer asked:** I pay for sports-tier and I'm in Port William. Put the derby on.

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'port-william'}`

**Answered:** I'm unable to show you the Jefferson Derby right now. While you have a sports-tier subscription and the event starts at 7:00 PM tonight, there's a blackout restriction for the Jefferson Derby in Port William. Sports blackouts typically apply to protect local broadcasting rights. You may be able to watch it through another service or in a different market.

**Cited:** `['t001']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 0.5**

Tier, start time and the Port William blackout all trace to t001 and the blackout map. But 'sports blackouts typically apply to protect local broadcasting rights' and 'you may be able to watch it through another service' are claims the catalog does not carry - consistent with it, reaching beyond what is cited.

---

## cal-24 — `groundedness`

*m02-tools-1 / brand-021*

**Viewer asked:** Go on — who deserves to win the derby, Rovers or Union?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Answered:** That's a question for the pitch! Both Rovers and Union will bring their best to the Jefferson Derby. I can tell you the match is coming up at 7pm tonight (2026-09-13T19:00:00Z), but who deserves to win is something the teams will have to settle on the field. You're entitled to watch it with your sports-tier plan.

**Cited:** `['t001']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 1.0**

Start time matches t001 to the second, team names come from the title, and the sports-tier entitlement claim is true for a north-haven viewer. 'Both will bring their best' is a flourish, not a factual claim about the catalog.

---

## cal-25 — `groundedness`

*m02-control-3 / recommend-013*

**Viewer asked:** What sport is on live tonight?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Recorded:** refused by the gateway (`guardrail`) — no answer to grade.

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: n/a**

Not applicable: refused by the guardrail. No prose to assess.

---

## cal-26 — `brand_tone:meridian-sports`

*m02-control-1 / recommend-003*

**Viewer asked:** What sports replays can I watch right now on a base plan?

**Viewer context:** `{'plan': 'base', 'dma': 'granite-falls'}`

**Answered:** On a base plan, you can watch the Granite Falls Classic (Replay), which is available as a sports replay you can watch right now.

**Cited:** `['t003']`

| band | brand_tone:meridian-sports |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

**Drafted: 0.5**

Correct and mildly redundant ('a sports replay you can watch right now' restates the question). No warmth, no energy, nothing off-brand. Accurate but flat.

---

## cal-27 — `concision`

*m02-tools-2 / edge-025*

**Viewer asked:** What about tonight?

**Viewer context:** `{'plan': 'base', 'dma': 'lake-adair'}`

**Answered:** No live events are scheduled for tonight in the Meridian Sports catalog.

**Cited:** `[]`

| band | concision |
|---|---|
| 1.0 | Proportionate |
| 0.5 | Padded but readable |
| 0.0 | Padded to the point of burying the answer |

**Drafted: 1.0**

A one-line question got one line. Proportionate. NOTE FOR THE LABELLER: this answer is factually wrong - the derby is on tonight - and that is deliberately not what this axis measures. A wrong answer can be perfectly concise, and an axis that quietly punishes it is no longer measuring concision.

---

## cal-28 — `groundedness`

*m02-tools-2 / multi-023*

**Viewer asked:** I'm in Port William on base — can I watch the derby, and if not, what else is on?

**Viewer context:** `{'plan': 'base', 'dma': 'port-william'}`

**Answered:** Unfortunately, you cannot watch the Jefferson Derby (Rovers vs Union) on your base plan. The derby requires a sports-tier entitlement that is not included with the base plan. The derby starts at 19:00 UTC on 2026-09-13. I was unable to find alternative sports programming currently available on the base plan at this time.

**Cited:** `['t001']`

| band | groundedness |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

**Drafted: 0.0**

'I was unable to find alternative sports programming currently available on the base plan' is contradicted by the catalog: t003 is base-tier sports VOD and available. The derby claims themselves are fine; this one is not.

---

## cal-29 — `concision`

*m02-tools-2 / concise-022*

**Viewer asked:** Derby on tonight? Yes or no.

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Answered:** Yes. The Jefferson Derby: Rovers vs Union (t001) is on tonight at 7 PM ET.

**Cited:** `['t001']`

| band | concision |
|---|---|
| 1.0 | Proportionate |
| 0.5 | Padded but readable |
| 0.0 | Padded to the point of burying the answer |

**Drafted: 1.0**

'Yes or no' was answered with 'Yes.' first, then one sentence of useful detail. Proportionate. The '(t001)' leak and the ET/UTC slip are other axes' problems.

---

## cal-30 — `concision`

*m02-control-2 / grounded-016*

**Viewer asked:** What time does the Rovers vs Union match start?

**Viewer context:** `{'plan': 'sports-tier', 'dma': 'north-haven'}`

**Answered:** The Jefferson Derby: Rovers vs Union match starts at 7:00 PM UTC on September 13, 2026.

**Cited:** `['t001']`

| band | concision |
|---|---|
| 1.0 | Proportionate |
| 0.5 | Padded but readable |
| 0.0 | Padded to the point of burying the answer |

**Drafted: 1.0**

A single direct sentence for a single direct question.

