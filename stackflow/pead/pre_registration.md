# StackFlow PEAD — Pre-Registration

**Written: 2026-09-22, BEFORE any surprise measure has been joined to any return.**
Part A (event counts and timing) is complete and reported below, as the brief required.
**No SUE value, no bucket, and no return has been computed or looked at.**

---

## 0. DISCLOSURE — this test is motivated by an already-seen result

The idea for this test came from Layer 4's surprise-control regression, where **earnings
surprise was significant (β = 0.0045, p = 0.048) on 203 events (2021+)** while concall text
was not. **Those 203 company-quarters are already "seen" data.** The hypothesis was not
formed independently of them.

Consequences, fixed now:

1. **The primary result must not rely on those events.** Criterion 6 (§D) requires the
   primary cell to survive their exclusion.
2. The 203 events are flagged `layer4_seen` in the event table and the main result is
   reported **with and without them**.
3. PEAD is nonetheless one of the most replicated effects in finance, so this is a test of
   a well-established external prior on new data — not a fishing expedition. That does not
   excuse the overlap; it is why the overlap is survivable rather than fatal.

---

## A. Coverage achieved (the gate) — reported before the hypothesis

Source: `data_pipeline/xbrl/` cache, read-only. All its locked rules already applied
upstream (earliest parseable filing per company-period, Consolidated-first /
Standalone-fallback, basis-switch exclusion, context rules, ratio tags banned).

| item | value |
|---|---|
| quarterly filings with PAT | 13,150 across 451 symbols |
| **filing timestamp availability** | **13,150 / 13,150 = 100%** |
| events surviving timing + liquidity filters | **5,902 across 247 symbols** |
| `ctx_inferred` among events | 34.6% |

Events by year (first build, price history from 2020-06):

| year | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| events | 520 | 913 | 868 | 943 | 985 | 946 | 727 |

~230–247 events per quarter from 2020Q3 onward. **This is an event study with thousands of
observations — the sample problem that sank Layers 2 and 3 does not apply here.**

Price history is being extended back to 2018 so 2019 events become usable; the final
counts are reported in `RESULTS_pead.md` as built, not as projected.

---

## B. Timing — the look-ahead-critical rules, fixed

1. **One event = one company-quarter result filing**, earliest filing per company-period
   (locked restatement rule D12).
2. **Event day:** filing timestamp **≤ 15:30 IST → that trading day**; **> 15:30 IST →
   next trading day**; no usable timestamp → next trading day (conservative). 100% of
   events have a timestamp, so the conservative branch is not load-bearing here.
3. **Entry: the OPEN of the trading day AFTER the event day.** Never the same-day close.
4. **Filters as of the event day:** 20-day average turnover **≥ ₹1 crore**, price **> ₹50**.
   Units are INR — NSE quotes in rupees, verified against real price levels.

---

## C. Surprise measures — fixed before any return is joined

### C.1 Primary: SUE (seasonal random walk)

```
SUE = (NetProfit_q − NetProfit_{q−4}) / std(YoY changes over the previous 8 quarters)
```

- Requires **≥ 6 prior YoY changes**; otherwise the event is **dropped** and counted.
- **No analyst estimates are used** — they are not available free. The expectation is
  simply the same quarter last year. **This is a real limitation**: a seasonal random walk
  is a weaker benchmark than consensus, and it will misclassify companies with strong
  trends or lumpy seasonality. Stated plainly rather than glossed.
- The formula does **not** divide by last year's profit, so loss-to-profit sign flips are
  handled naturally.

### C.2 Secondary (reported, never the headline)

- **Revenue SUE** — same formula on revenue from operations (bank `Income`).
- **EAR** — the stock's excess return from event day −1 to event day +1: the market's own
  reaction. Its subsequent drift is a **price-only** version of PEAD, independent of
  accounting-data quality, and therefore a useful cross-check on the XBRL pipeline itself.

All secondary tests carry **Benjamini–Hochberg FDR correction**.

---

## D. Buckets, primary cell, and pass/fail

- **Horizons:** 5, 10, 30, 60, 126 trading days after entry. Incomplete horizons are left
  **blank**, never partially filled.
- **Return columns:** raw; excess vs Nifty 500; **excess vs the equal-weight mean of all
  events entering in the same calendar month** — the primary metric, because this confound
  has been material in every prior StackFlow layer.
- **Buckets:** within **each calendar quarter**, sort that quarter's events into **quintiles
  by SUE**, so results are compared against contemporaneous peers rather than across regimes.

### THE PRIMARY CELL — one, fixed now

> **SUE, top quintile minus bottom quintile, 60 trading days, excess vs the event universe.**

Everything else is secondary and FDR-corrected.

**Discovery:** filings 2019 → 2023-12-31. **Holdout:** 2024 → latest completed.
Holdout is evaluated **once, as-is**.

**CONFIRMED only if ALL six hold:**

1. Top-minus-bottom spread **positive on discovery AND on holdout**
2. Positive in **≥ 65% of calendar-quarter folds** (bar unchanged from every StackFlow phase)
3. **Survives dropping the single best fold**
4. **Roughly monotonic** across quintiles (Q5 > Q4 > … > Q1, at most **one** adjacent inversion)
5. **Not explained by 2020** — reported with and without
6. **Survives excluding the 203 Layer-4-seen events**

**KILL:** spread ≤ 0 on holdout · carried by a single fold · reverses without 2020.
Otherwise **INCONCLUSIVE**, naming the failing criteria.

---

## E. Diagnostics — all reported, none optional

- `ctx_inferred %` and basis-switch rate among events used; **primary cell rerun on
  `ctx_inferred = False` events only**
- **Financials** (banks/NBFC/insurance) vs non-financials, separately
- **Large vs small** by 20-day turnover, split at median — PEAD is usually stronger in
  smaller, less-followed names, which is StackFlow's universe
- **Long vs short side:** is the spread driven by Q5 outperforming or Q1 underperforming?
  Layers 1–2 both found the weak side carried the effect; checked here explicitly
- **Dispersion-normalised effect** alongside raw
- **Break-point scan** for stability over time — never fixed blocks (the Phase 1c lesson)

---

## F. Tradeability — only if the primary cell is CONFIRMED

Long-only book: buy every top-quintile SUE event at next-day open, hold 60 trading days,
equal weight, **cap concurrent positions at 15**, apply **0.585% round-trip cost**
(LeadFlow's NSE cost model). Report CAGR, max drawdown, win rate, and excess vs Nifty 500
and vs the event-universe mean.

**Not reported at all if the primary cell is not confirmed.**

---

## G. Pre-committed reporting rule

The verdict is **CONFIRMED / REJECTED / INCONCLUSIVE**, with the failing criteria named and
the **real per-trade size compared against the 0.585% cost**. A sign and a p-value are not
a result.

**No combination with Layer 1, Layer 4 or LeadFlow signals in this task.** Combination is a
later, separately pre-registered question.

---

*(Addenda, if any, appear below this line with dates.)*
