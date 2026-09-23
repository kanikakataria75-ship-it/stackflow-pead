# StackFlow Layer 4 — Results: Concall Trigger Words, Mood and Forward Returns

**Run date:** 2026-09-22
**Judged against `layer4/pre_registration.md`, written and saved before any text feature
was joined to any return.**

---

## VERDICT

> **Concall text does NOT predict forward returns beyond the earnings surprise, at any
> horizon tested, on this sample.**
>
> - **0 of 11 pre-registered features survive FDR at q ≤ 0.10 on discovery.**
> - **0 features reach "finding" status** under the three-part holdout rule.
> - In the surprise control, **mood is completely flat (β = 0.0017, p = 0.977)** while
>   **earnings surprise itself is significant (β = 0.0045, p = 0.048)**.
>
> The positive control works and the text does not. That is the cleanest possible form of
> this null: the machinery can detect a real effect in the same data, and finds none in
> the tone.

No magnitude is quoted against the 0.585% round-trip cost, because nothing cleared the bar
to warrant one.

---

## 1. Coverage (Part A)

**A silent 9-month gap was found and closed.** NSE changed its announcement taxonomy
during 2022; the category name visible today returns **exactly 0 rows for Mar–Nov 2022**.
A supplementary sweep on the `Transcript of…` category recovered it — **2022 went from
256 → 2,634 transcripts.** Same class as the 20-row API default and the placeholder XBRL
URLs in earlier layers.

Cap check: the endpoint returns a bare list with no `totalCount`, so this was verified by
halving a window — 1,537 + 806 = 2,343 exactly. **No cap, 0 failed windows across 69 months.**

| year | transcripts found | companies |
|---|---|---|
| 2021 | 845 | 355 |
| 2022 | 2,634 | 814 |
| 2023 | 3,241 | 928 |
| 2024 | 3,797 | 1,052 |
| 2025 | 4,209 | 1,186 |
| 2026 | 3,443 | 1,250 |
| **total** | **18,169** | **1,540 unique** |

**Gate (≥2,000): PASSED.** Filter precision on a manual 30-sample: **83% raw**, ~96% after
the ≥400-word extraction gate removes cover letters.

### Processed sample — smaller than targeted, and why

**675 transcripts processed → 588 usable events across 442 companies.** The
pre-registration targeted 3,000 in a seed-42 shuffle and stated the sample is
**compute-bound, not result-bound**; that holds — selection never depended on content.

Profiling showed **FinBERT at 5.9s/transcript (87% of runtime)**, not the 1.5s an earlier
benchmark on short synthetic sentences suggested. `MAX_SENT` was cut 150 → 50 and recorded
as a dated addendum. **This makes each mood estimate noisier, which biases mood toward zero
and works against finding an effect** — it cannot manufacture one.

| events by entry year | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| n | 39 | 78 | 105 | 131 | 130 | 105 |

**Discovery 223 · Holdout 365.** Horizon completeness: 5d/10d 100%, 30d 97%, **6m 88%** —
incomplete 6M windows left NaN, never partially filled.

---

## 2. The universe-composition confound — present and large, as in every prior layer

| horizon | raw return | vs Nifty 500 | **vs event-universe mean** |
|---|---|---|---|
| 5d | −0.213% | −0.500% | **0.000%** |
| 10d | +0.592% | +0.010% | **0.000%** |
| 30d | +1.806% | +0.136% | **0.000%** |
| **6m** | **+9.699%** | **+3.053%** | **0.000%** |

Companies that hold concalls returned **+9.7% raw and +3.1% vs Nifty 500 over 6 months**.
Neither is a text effect — it is who holds calls, plus the dividend-adjusted-stock vs
price-index mismatch. **Measured against the equal-weight event-universe mean it is exactly
zero by construction**, which is why the pre-registration made that the primary metric.
Reporting the +3.05% as a "concall effect" would have been a textbook version of the
confound that appeared in all four prior StackFlow tests.

---

## 3. Mood buckets (FinBERT terciles, `xs_univ` %)

**Management remarks**

| bucket | n | 5d | 10d | 30d | 6m |
|---|---|---|---|---|---|
| low | 199 | +0.191 | −0.234 | +0.633 | **+2.208** |
| mid | 209 | −0.524 | −0.114 | −0.267 | −0.778 |
| high | 180 | +0.394 | +0.390 | −0.375 | **−1.539** |

**Analyst Q&A**

| bucket | n | 5d | 10d | 30d | 6m |
|---|---|---|---|---|---|
| low | 156 | +0.472 | +0.091 | −0.683 | **−2.282** |
| mid | 191 | −0.350 | −0.165 | −0.298 | −1.235 |
| high | 107 | +0.485 | +0.700 | +1.400 | **+4.603** |

**The two sections point in opposite directions at 6M** — high remarks-mood is associated
with −1.54% and high Q&A-mood with +4.60%. A real tone effect should not reverse sign
depending on which half of the same call it is measured in. This is the signature of noise
in a small sample, not of two distinct mechanisms, and it is reported as such.

Correlations with `xs_univ` are negligible throughout: remarks −0.009 to −0.043,
Q&A +0.022 to +0.116, combined −0.009 to +0.019.

---

## 4. Trigger features — full table, all 11, discovery vs holdout

30-day horizon, `xs_univ`, high-vs-low split at the **discovery** median (holdout never
re-fitted).

| feature | disc effect % | disc p | **disc q (BH)** | hold effect % | hold p | hold fold-pos | status |
|---|---|---|---|---|---|---|---|
| theme_capital_actions | **+1.972** | 0.0097 | **0.1062** | +0.926 | 0.131 | 72.7% | not established |
| lm_positive | −1.224 | 0.110 | 0.603 | +0.905 | 0.140 | 63.6% | not established |
| theme_negative_caution | −1.000 | 0.192 | 0.703 | −0.518 | 0.398 | 45.5% | not established |
| theme_hedging_evasion | −0.841 | 0.273 | 0.750 | −0.748 | 0.222 | 36.4% | not established |
| lm_uncertainty | −0.502 | 0.513 | 0.788 | −0.330 | 0.591 | 36.4% | not established |
| lm_strong_modal | +0.465 | 0.545 | 0.788 | +0.879 | 0.151 | 72.7% | not established |
| lm_constraining | +0.447 | 0.560 | 0.788 | **+1.202** | **0.049** | **81.8%** | not established |
| lm_litigious | +0.432 | 0.573 | 0.788 | −0.387 | 0.527 | 45.5% | not established |
| lm_weak_modal | −0.294 | 0.702 | 0.833 | −0.424 | 0.489 | 54.5% | not established |
| theme_positive_guidance | +0.238 | 0.757 | 0.833 | +1.133 | 0.064 | 63.6% | not established |
| lm_negative | +0.028 | 0.971 | 0.971 | **−1.222** | **0.046** | 18.2% | not established |

**Survived FDR q ≤ 0.10 on discovery: 0 of 11.** Status counts: **11 × "not established", 0 findings.**

### Two near-misses, and why neither is promoted

- **`theme_capital_actions`** is the strongest: discovery p = 0.0097, same sign on holdout,
  **72.7% holdout fold positivity**. It fails on one thing — **q = 0.1062, just over the
  0.10 threshold**. The pre-registration fixed q ≤ 0.10 before any of this was visible, and
  0.1062 is not 0.10. Promoting it because it is close would be exactly the move this
  project has refused throughout. It is the single most interesting candidate for a larger
  sample, and it is reported as **not established**.
- **`lm_constraining` and `lm_negative`** look significant **on holdout** (p = 0.049 and
  0.046) — but both are statistical noise on discovery (q = 0.788, 0.971). Holdout is an
  evaluation set, not a second discovery set. Reading a holdout p-value as a finding would
  invert the entire point of the rule.

---

## 5. Earnings-surprise control (Part E) — the decisive test

203 events (35%) have a matched, filing-dated surprise from the XBRL cache.

| model | mood β | mood p | surprise β | surprise p |
|---|---|---|---|---|
| mood alone | 0.0017 | **0.977** | — | — |
| mood + surprise | 0.0043 | **0.943** | **0.0045** | **0.048** |

**Mood has no explanatory power at all, before or after controlling for surprise.** It does
not "disappear once surprise is included" — it was never there. Meanwhile **earnings
surprise is significant on its own**, which is the positive control: the same 203 events,
same returns, same regression machinery **can** detect a real effect.

That asymmetry is the strongest single result in this layer. The null is about the **text**,
not about the method or the data.

---

## 6. Call-date vs filing-date sensitivity

| event date used | n | 5d | 10d | 30d | 6m |
|---|---|---|---|---|---|
| parsed call date | 229 | −0.140 | +0.081 | −0.078 | −0.455 |
| exchange filing date | 359 | +0.090 | −0.052 | +0.051 | +0.287 |

Both near zero; the choice does not change any conclusion. Call date was parseable from
transcript text in **39% of cases**; the rest fall back to the exchange filing date.

---

## 7. Regime note

The data begins in 2021, so **2020 — the reversal year that dominated Layer 3 — is out of
range entirely.** 2021 contributes only 39 events. There is no extreme-regime period inside
this sample large enough to split on, which is itself a limitation: this layer has **not**
been tested against the regime that has broken every prior StackFlow signal.

---

## 8. Deliverables

| file | rows | contents |
|---|---|---|
| `trigger_word_events.csv` | **4,454** | one row per (transcript × trigger phrase × section), with context snippet, theme, per-1000-word rate, FinBERT mood, surprise, and all 12 return columns |
| `call_events.csv` | **588** | one row per transcript: dates, word count, section moods, theme scores, surprise, all return columns |
| `trigger_word_summary.csv` | **11** | per feature: discovery/holdout effects, BH q-value, fold positivity, status |

---

## 9. Limitations — stated plainly

- **Sample is 588 events, not the ~3,000 targeted.** FinBERT cost was 4× my benchmark. This
  is the binding limitation: with 223 discovery events, only a large effect could clear FDR.
  **A null here is weak evidence of absence**, not proof of it.
- **Mood estimates are noisier** after the 150 → 50 sentence cut (addendum). Biases toward
  zero; works against the hypothesis.
- **Short history.** Transcript filing only became routine post-2021 LODR amendments, so
  there is no pre-2021 data and no extreme regime in range.
- **PDF extraction is imperfect.** ~1/3 of files needed the pdfplumber fallback; scanned
  PDFs were skipped, not OCR-ed.
- **Call date parsed in only 39% of transcripts**; the rest use filing date, which lags the
  call by days.
- **Surprise coverage is 35%**, limited by XBRL-cache overlap with this sample.
- **The lexicon is partly judgement.** The Indian-concall phrase list was hand-written by
  me before seeing returns — fixed in advance, but not derived from data.
- **Data-driven word discovery (§D.4) was not run.** With 223 discovery events, fitting an
  L1 model over TF-IDF 1–3 grams would overfit badly and could not survive FDR. Skipping it
  is the honest call; forcing it would have produced impressive-looking discovery words with
  no chance of holdout survival.

---

## 10. Plain answer to the question asked

**Does concall text predict returns beyond earnings surprise, at which horizons, and is the
size larger than the 0.585% round-trip cost?**

**No, at no horizon, and the cost question does not arise.** Mood is flat (p = 0.977),
no feature survives multiple-testing correction, remarks and Q&A contradict each other, and
the only thing in the data that does predict returns is the **earnings surprise itself**.

The most promising candidate for future work is **`theme_capital_actions`** (capex, fund
raise, QIP, buyback, deleveraging) — discovery p = 0.0097, correct sign on holdout, 72.7%
fold positivity, failing only at q = 0.1062. That is worth re-testing on the full 18,169
transcripts. **It is not a finding today.**

**The pipeline is reusable infrastructure**: 18,169 discovered transcripts with a fixed
taxonomy-gap fix, a working PDF→text→FinBERT path, and point-in-time returns. Re-running
the same pre-registered test at full sample is now a compute problem, not a research
problem.
