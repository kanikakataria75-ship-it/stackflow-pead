# StackFlow Layer 4 — Pre-Registration: Concall Text, Mood and Forward Returns

**Written: 2026-09-22, BEFORE any text feature has been joined to any return.**
Part A (coverage) is complete and is reported below because the gate required it. **No
return has been computed, looked at, or joined at the time of writing.**

---

## A. Coverage actually achieved (the gate)

Source: NSE `/api/corporate-announcements`, reusing the cookie-handshake access pattern
from `data_pipeline/xbrl/`.

### A.1 A silent taxonomy change was found and fixed

NSE **changed its announcement category taxonomy during 2022**. Using only the category
name visible today returned **exactly 0 rows for March–November 2022** — a 9-month hole
that looked like real absence.

| period | category in use |
|---|---|
| 2021-01 → 2022-02 | `Analysts/Institutional Investor Meet/Con. Call Updates` |
| **2022-03 → 2022-11** | split into `Transcript of…` / `Schedule of…` / `Recording of…` |
| 2022-12 → 2026-09 | back to the combined name |

A supplementary sweep on `Transcript of Analysts/Institutional Investor Meet/Con. Call`
recovered the gap: **2022 went from 256 → 2,634**. This is the same class of silent gap as
the 20-row API default and the placeholder XBRL URLs.

**Cap check (Lesson 2):** this endpoint returns a bare list with no `totalCount`, so a cap
cannot be read off the response. Verified by halving a window — 1,537 + 806 = 2,343 exactly.
No cap. **0 failed windows** across all 69 months.

### A.2 Coverage

| year | transcripts | companies |
|---|---|---|
| 2021 | 845 | 355 |
| 2022 | 2,634 | 814 |
| 2023 | 3,241 | 928 |
| 2024 | 3,797 | 1,052 |
| 2025 | 4,209 | 1,186 |
| 2026 | 3,443 | 1,250 |
| **total** | **18,169** | **1,540 unique** |

Median transcripts per company: **14**. **Gate (≥2,000): PASSED.**

Coverage is uneven within 2022 (Mar 25, Sep 21, Dec 24 vs Aug 584, Nov 598) — reported as
found, not smoothed.

### A.3 Transcript filter precision — manual sample of 30

25 real transcripts, 5 non-transcripts, 0 scanned, 0 download failures → **83% raw
precision**. Four of the five misses are cover letters of 153–229 words, which the
extraction-time gate (§C.2) removes automatically. **Effective precision after that gate
is ~96%**; the one ambiguous case (PFS, 2,383 words) is counted as a miss.

---

## B. Processing scope — fixed now, for compute reasons only

Processing all 18,169 PDFs is not feasible in the available compute. **Pre-registered
rule:** transcripts are processed in a **seed-42 pseudo-random shuffle**, target **3,000**,
and the final N is reported. The order is fixed before any result exists, so the sample is
**compute-bound, never result-bound**. No transcript is skipped for what it contains.

FinBERT is capped at **150 evenly-spaced sentences per transcript** (up to 75 remarks + 75
Q&A) — benchmarked at 102 sentences/sec on CPU.

---

## C. Universe and text extraction

1. **Universe:** every company with a usable transcript. **Point-in-time by construction** —
   the transcript's existence on its date *is* the membership test. Today's index
   membership is never used.
2. **Extraction gate:** `pdfplumber`, falling back to PyMuPDF. A document is accepted only
   if it yields **≥400 words** and matches speaker-turn language
   (`moderator|ladies and gentlemen|question-and-answer|analyst`). **Scanned/image-only PDFs
   are skipped and counted, never OCR-ed silently.**
3. **Liquidity filter, applied point-in-time at each event** (INR units — verified against
   real NSE prices, which are quoted in rupees):
   - 20-day average turnover **≥ ₹1 crore** (close × volume)
   - price **> ₹50**
4. **Sections:** split into management remarks and analyst Q&A at the first
   moderator/Q&A marker. Where no split is detectable the transcript is marked
   `section=whole` and reported separately, never silently assigned to one side.

---

## D. Text features — the lexicon, fixed before any return is seen

### D.1 Loughran-McDonald categories

`negative`, `positive`, `uncertainty`, `litigious`, `constraining`, `strong_modal`,
`weak_modal`. Counted per section, **normalised per 1,000 words**.

### D.2 Hand-written Indian-concall phrase list, by theme

- **positive_guidance:** strong demand · order book · capacity expansion · margin expansion ·
  upgrade guidance · record quarter · market share gain · robust demand · healthy demand ·
  strong pipeline · operating leverage
- **negative_caution:** headwinds · margin pressure · subdued demand · inventory destocking ·
  slowdown · one-off · challenging environment · demand weakness · cost pressure ·
  de-growth · muted
- **hedging_evasion:** difficult to say · too early to comment · we will come back ·
  not in a position · let us see · cannot comment · hard to predict · wait and watch
- **capital_actions:** capex · fund raise · QIP · debt reduction · buyback · deleveraging ·
  preferential allotment

### D.3 FinBERT mood

`ProsusAI/finbert`, sentence-level. `mood = (n_positive − n_negative) / n_sentences`,
computed **separately for remarks and Q&A**. Also **mood change vs the same company's
previous call** (tone shift, not level).

### D.4 Data-driven discovery

L1-regularised linear model on TF-IDF 1–3 grams, **fitted on the discovery period only**.
No large model trained from scratch — the sample is thousands of calls, not millions.

---

## E. Returns

- **Event date / entry:** the **next trading day's open** after the call date.
  **Sensitivity:** repeat with the transcript's exchange filing date as the event date.
  Both reported.
- **Horizons:** 5, 10, 30, 126 trading days. **An incomplete horizon is left NaN and never
  partially filled.**
- **Three columns per horizon:**
  1. raw return
  2. excess vs Nifty 500
  3. **excess vs the equal-weight mean of all event stocks entering in the same month** —
     **this is the primary metric**, and it exists because the universe-drift confound has
     now appeared in all four prior StackFlow tests.
- **Cost reference:** 0.585% round trip (LeadFlow's NSE cost model).

---

## F. The holdout rule — mandatory

- **Discovery:** earliest transcript → **2023-12-31**
- **Holdout:** **2024-01-01** → latest date with completed returns

Word discovery, threshold choice and theme highlighting happen **on discovery only**.
Holdout is evaluated **once, as-is**.

**Benjamini–Hochberg FDR** across all trigger words tested on discovery; report how many
survive at **q = 0.10**.

A word or theme is a **finding** only if **all three** hold:

- **(a)** survives FDR on discovery (q ≤ 0.10)
- **(b)** **same sign** on holdout
- **(c)** correct sign in **≥65% of calendar-quarter folds** on holdout

Everything else is reported and labelled **"not established"**. Nothing is promoted on a
discovery number alone, however large.

---

## G. Earnings-surprise control — not optional

Concalls follow results, so a positive call usually follows good numbers. **Tone only adds
value if it predicts returns beyond the surprise.**

Surprise per event, from the XBRL cache (filing-dated, as-reported):

```
surprise = (PAT_q − PAT_{q−4}) / sd(past YoY changes for that company)
```

matched to the most recent filing **on or before the call date** (D4 point-in-time).

**Every mood and theme result is reported twice — raw, and controlling for surprise**
(OLS with surprise as covariate, plus a within-surprise-tercile comparison). If tone's
effect disappears once surprise is included, **that is stated plainly.**

**2020–21 is reported separately** where in range — 2020 dominated the Layer 3 result and
that is not repeated blind.

---

## H. Pre-committed verdict rule

Concall text is judged to predict returns beyond earnings surprise **only if**:

1. a mood or theme effect is present on **holdout** with the same sign as discovery, **and**
2. it holds in **≥65% of holdout quarter-folds**, **and**
3. it survives the **surprise control**, **and**
4. its magnitude **exceeds the 0.585% round-trip cost** at some horizon.

Failing any of these → reported as **not established**, with the failing condition named.
**A null is a valid result** and will be reported as plainly as H1's and H3's were.

---

*(Addenda, if any, appear below this line with dates.)*

---

## ADDENDUM — 2026-09-22, compute parameter revised (recorded, not hidden)

**§B pre-registered FinBERT at 150 sentences per transcript, based on a benchmark of
102 sentences/sec.** That benchmark used short synthetic sentences and was wrong for real
data: profiling actual transcripts gives **5.9s per transcript for FinBERT alone (87% of
total runtime)** — real concall sentences are far longer, so ~25 sentences/sec.

**Revised:** `MAX_SENT` 150 → **50** (25 per section), tokenizer `max_length` 96 → 64.

- This is a **compute parameter only**. It does not touch the lexicon, the holdout split,
  the FDR rule, the confirm/kill criteria, or any threshold that could shade a result.
- It makes each mood estimate **noisier** (a mean over 25 sentence classifications per
  section rather than 75). That is a real cost and is reported as a limitation, not
  waved away: it biases mood toward zero and **works against** finding an effect.
- No transcript is selected or skipped on content; the seed-42 order is unchanged.

**The final N processed is reported as-is.** The pre-registration already framed the
sample as compute-bound rather than result-bound, and that remains true.
