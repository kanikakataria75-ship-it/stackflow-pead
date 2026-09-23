# StackFlow PEAD V2 — Master Pre-Registration

**Document Date:** 2026-09-22  
**Status:** LOCKED BEFORE ANY V2 EX-ANTE RESULT IS GENERATED OR EXAMINED  
**Commitment:** No parameter changes after seeing results. A null result is an acceptable, publication-grade research result.

---

## 1. Research Questions & Hypotheses

### 1.1 Primary Hypothesis
> Stocks with unusually positive point-in-time earnings surprises (top SUE quintile) subsequently outperform stocks with unusually negative earnings surprises (bottom SUE quintile) over medium-term horizons (60 trading days) after controlling for the contemporaneous event universe and transaction costs, **when buckets are assigned strictly ex-ante using rolling historical thresholds**.

### 1.2 Secondary Research Questions
1. **Monotonicity:** Does forward return increase monotonically from Q1 through Q5?
2. **Ex-Ante Survival:** Does the V1 confirmed effect (+2.50%) survive when look-ahead quarterly quintiles are replaced by strictly ex-ante rolling historical thresholds?
3. **Horizon Profile:** Does the drift expand monotonically across holding periods (5d, 20d, 40d, 60d, 90d, 126d)?
4. **Size Robustness:** Is the effect genuine across market-cap/liquidity segments (Small, Mid, Large), or an illiquidity artifact?
5. **Sector Dynamics:** Does the previously observed reversal in Financials (Banks/NBFCs, -4.85%) persist under ex-ante thresholds, and does it survive the same robustness bar?
6. **Filing Timing & Capacity:** Does the first-come filling of slots in a capped book systematically select early-filing large-caps with weaker alpha, explaining the V1 portfolio failure?
7. **Tradeability & Portfolio Viability:** Can a realistic, cost-adjusted long-only portfolio outperform Nifty 500 and the event universe after deducting round-trip transaction costs?

---

## 2. Locked SUE Definition (Seasonal Random Walk)

The SUE calculation is preserved exactly from the confirmed V1 specification:

$$SUE_t = \frac{\text{PAT}_t - \text{PAT}_{t-4}}{\sigma(\Delta \text{YoY PAT}_{t-8 \dots t-1})}$$

### Rules and Edge-Case Specifications:
- **Financial Metric:** Profit After Tax (`pat`) from official quarterly XBRL filings.
- **Reporting Basis:** Consolidated first (`basis == 'Consolidated'`); Standalone used if Consolidated is unavailable. If a company switches basis, decisions from D13 apply upstream.
- **Quarterly Matching:** Compares quarter $t$ against the identical quarter from the prior fiscal year ($t-4$).
- **History Requirement:** Requires at least 6 historical YoY changes ($\ge 6$ observations in the denominator). If $<6$, the event is dropped and accounted for in coverage logs.
- **Zero or Non-Finite Denominator:** If $\sigma(\Delta \text{YoY PAT}) \le 0$ or non-finite, SUE is assigned `NaN` and dropped.
- **Negative Base Earnings:** Because the numerator is a simple difference ($\text{PAT}_t - \text{PAT}_{t-4}$) and the denominator is the standard deviation of historical changes, sign flips (e.g. from loss to profit or vice versa) are handled naturally without sign distortion.
- **Winsorisation:** SUE values will **NOT** be winsorised for bucket sorting. Rank-based quintile assignment naturally insulates against outliers.
- **Analyst Estimates:** No analyst consensus estimates will be introduced.

---

## 3. Point-in-Time Ex-Ante Bucket Construction

This is the core methodological upgrade in PEAD V2.

### 3.1 Strict Prohibition of Ex-Post Grouping
Events must never be bucketed against peers filing later in the same calendar quarter. 

### 3.2 Rolling Historical Thresholds
For any qualifying event occurring at date $T$:
1. Identify all qualifying historical events whose filing occurred strictly before date $T$.
2. Form quintile cutoff boundaries $(q_{20}, q_{40}, q_{60}, q_{80})$ using these prior events over a fixed lookback window.
3. Assign the event at date $T$ into Quintiles 1 to 5 based on these historical boundaries.

### 3.3 Locked Rolling Window Grid
To avoid post-hoc selection of the threshold window, the following three configurations are locked and will be reported:
- **Baseline Ex-Ante Model (M1 - 4 Quarters):** Rolling historical window of all qualifying events filed in the preceding 365 calendar days ($T-365 \le \text{filing} < T$). Requires $\ge 200$ historical events.
- **Robustness Ex-Ante Model (M2 - 8 Quarters):** Rolling historical window of preceding 730 calendar days ($T-730 \le \text{filing} < T$).
- **Expanding Historical Model (M3):** All qualifying events from the start of the sample up to date $T$ (minimum burn-in of 4 quarters).

All three models will be reported in the master results. Model M1 is pre-designated as the primary cell.

---

## 4. Event Timing & Trade Execution Rules

1. **One Event = One Company-Quarter Result:** Earliest parseable filing per company-period.
2. **Filing Timestamp Cutoff:**
   - Filing timestamp $\le$ 15:30 IST: Event day $T = \text{filing day}$ (if trading session; otherwise next trading session).
   - Filing timestamp $>$ 15:30 IST: Event day $T = \text{next trading session}$.
3. **Execution Session:** Strictly the **OPEN** of the session *following* the event day ($T+1$).
4. **Leakage Guard:** Neither the announcement intraday price change nor the announcement close-to-close return may be included in the forward holding return.
5. **Filters Evaluated as of Event Day:**
   - 20-day historical average turnover: $\ge \text{INR } 1 \text{ crore } (10^7 \text{ INR})$.
   - Entry price: $\text{Open} > \text{INR } 50$.

---

## 5. Primary Cell & Confirmation Standards

### 5.1 The Primary Evaluation Cell
> **Ex-Ante SUE (Model M1: 4-Quarter Rolling), Top Quintile (Q5) minus Bottom Quintile (Q1), 60 Trading Days holding, Excess Return vs Contemporaneous Event-Universe Mean.**

- **Discovery Period:** Events with event date $\le$ 2023-12-31.
- **Holdout Period:** Events with event date $\ge$ 2024-01-01 to latest completed window.

### 5.2 Confirmation Criteria (All 6 Must Pass)
1. **Discovery & Holdout Consistency:** Q5 minus Q1 spread must be positive on Discovery AND on Holdout.
2. **Quarterly Fold Positivity:** Positive spread in $\ge 65.0\%$ of calendar-quarter folds.
3. **Robustness to Best Fold:** Spread must remain positive after dropping the single highest-performing quarterly fold.
4. **Monotonicity:** Quintile ladder must be approximately monotonic ($Q1 < Q2 < Q3 < Q4 < Q5$), allowing at most **one** adjacent inversion.
5. **No 2020 Artifact:** Survives exclusion of 2020 (if present).
6. **Independence from Prior Seen Events:** Survives exclusion of the 203 `layer4_seen` events with positive spread and $\ge 65\%$ fold positivity.

---

## 6. Pre-Registered Subgroup & Diagnostic Grids

All subgroup analyses will be reported comprehensively:
- **Size Segmentation:** 20-day turnover split into 3 fixed terciles (Small, Mid, Large), recomputed rolling or at event date.
- **Sector Segmentation:** Financials (`is_fin = True`, Banking & NBFCs) vs Non-Financials (`is_fin = False`).
- **Filing Timing Cohorts:**
  - *Early Filers:* Days from quarter-end $\le 25$ days.
  - *Mid Filers:* Days from quarter-end $26 \dots 45$ days.
  - *Late Filers:* Days from quarter-end $> 45$ days.

---

## 7. Portfolio Backtest Grid & Execution Rules

The portfolio experiment will only evaluate pre-registered configurations:
- **Signals:** 
  - S1: Q5 only (Top Quintile)
  - S2: Q4 + Q5 (Top Two Quintiles)
- **Concurrent Position Caps:** 10 positions, 20 positions, 30 positions.
- **Holding Horizons:** 20, 40, 60, 90 trading days.
- **Queueing Policies:**
  - P1: First-In-First-Out (FIFO) - exact V1 replication.
  - P2: SUE-Rank Priority (higher SUE displaces lowest SUE or fills queue).
- **Cost Scenarios (Round-Trip):**
  - Low: 0.300%
  - Baseline: 0.585% (NSE LeadFlow benchmark)
  - Stress: 1.000%
- **Weighting:** Equal weight per sleeve ($1 / N_{\text{slots}}$). Unallocated capital earns 0% (cash drag).
- **Benchmarks:** Nifty 500 Total Return / Close, Equal-Weight Event Universe.

---

## 8. Final Verdict Classifications

The final report will conclude with exactly one of four pre-committed labels:
1. **VALIDATED TRADING STRATEGY:** Signal confirmed AND at least one pre-registered portfolio specification beats Nifty 500 after baseline transaction costs with positive excess return on holdout.
2. **VALIDATED SIGNAL:** Cross-sectional signal passes all 6 criteria, but portfolio implementation fails to beat benchmark net of costs.
3. **PROMISING BUT UNVALIDATED:** Evidence is positive but fails one or more robustness/fold bars.
4. **REJECTED:** Signal fails on holdout or collapses under ex-ante construction.
