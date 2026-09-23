# StackFlow PEAD V2 — Master Research Report

**Document Date:** 2026-09-22 (Audited & Reconciled)  
**Auditor / Researcher:** Antigravity (Lead Quantitative Researcher & Research-Engineering Agent)  
**Project Directory:** `stackflow/research/pead_v2/`  
**Classification:** **Signal confirmed; strategy is a forward-test candidate.**

---

## 1. Executive Summary

This research program evaluated whether Post-Earnings-Announcement Drift (PEAD) in the National Stock Exchange (NSE) universe constitutes a **genuinely tradeable, point-in-time correct anomaly** or an artifact of look-ahead quintile grouping and portfolio capacity distortion.

### Core Headline Results (Audited & Reconciled):
1. **The Cross-Sectional Signal is Confirmed (+2.77% Spread):**
   When quintiles are assigned **strictly ex-ante using rolling historical percentiles from preceding 365 calendar days**, the 60-day cross-sectional excess spread (Q5 − Q1) is **+2.77%** ($p = 3.88 \times 10^{-7}$) across 7,818 qualifying events, with **85.0% of quarterly folds positive** (17 of 20 folds).
2. **Strategy Headline Numbers (Dual Reporting):**
   - **Out-of-Sample Holdout (2024–2026):** **+7.55% CAGR vs. +7.41% Nifty 500 (+0.14% Excess)** net of 0.585% transaction costs, with annualized volatility of **17.44%**, Sharpe of **0.51**, and max drawdown of **-25.12%**. (Trade-level arithmetic: +7.68% CAGR, +0.28% excess).
   - **Full In-Sample Period (2021–2026):** **+16.83% CAGR vs. +10.26% Nifty 500 (+5.78% Excess)** net of 0.585% transaction costs, with annualized volatility of **16.82%**, Sharpe of **1.02**, and max drawdown of **-25.12%** (vs -18.84% for Nifty 500).
3. **The V1 Portfolio Failure Diagnosed:**
   The failure of the V1 15-position FIFO long-only book (+8.38% CAGR vs +10.91% Nifty 500) was driven by early-filer adverse selection:
   - Early filers ($\le 25$ days from quarter-end) are predominantly large caps where the 60-day spread is only **+0.48%** ($p = 0.70$).
   - Mid and late filers ($> 25$ days) are mid/small caps where the spread is **+3.10% to +3.84%** ($p < 0.01$).
   - A 15-slot FIFO book filled immediately with early large caps, locking capital for 60 trading days and skipping 80% of eligible trades (specifically the higher-alpha names).
4. **Classification & Forward Status:**
   Because the 2024–2026 holdout was already inspected in V1 and informed the grid choice (30 slots, SUE-rank, Non-Financials), the trading strategy cannot claim pure out-of-sample validation. It is classified as:
   > **"Signal confirmed; strategy is a forward-test candidate."**

---

## 2. Research Questions & Hypotheses

### Primary Question:
> Does an ex-ante, point-in-time earnings surprise signal (SUE) generate persistent, monotonic post-announcement excess returns over 60 trading days that survive realistic portfolio execution, capacity bottlenecks, and transaction frictions?

### Secondary Questions Answered:
- **Monotonicity:** Does forward return increase monotonically across Q1..Q5? (**Yes**, $\le 1$ inversion across all tested horizons).
- **Size Dependency:** Is PEAD an illiquidity artifact? (**No**; Small caps = +3.941%, Mid caps = +2.113%, Large caps = +2.110%).
- **Sector Inversion:** Does the financial sector reversal persist under ex-ante thresholds? (**Yes**, Financials = -3.956%, Non-Financials = +3.475%).
- **Adversarial Robustness:** Does the anomaly vanish under outlier removal or cost stress? (**No**, 0 of 7 kill tests triggered).

---

## 3. Data & Baseline Reconciliation (V1 vs. V2)

### 3.1 Reconciliation with Claude Code's PEAD V1 Report
1. **Fold Positivity (76.2% vs. 80.0%):**
   - In V1, 2021Q2 contained only 1 Q5 event and 1 Q1 event (spread was -20.50%).
   - If 2021Q2 is included (counting all 21 calendar quarters with $\ge 1$ event), exactly **16 of 21 folds are positive = 76.19% (76.2%)**.
   - If a standard statistical filter of $\ge 3$ events per bucket is applied, 2021Q2 is dropped as undersized, leaving **16 of 20 folds positive = 80.0%**. Both figures are mathematically reconciled.
2. **Sample Start (2019 vs. 2021):**
   - The initial pre-registration projected extending price history to 2018 to capture 2019 filings.
   - However, because the locked SUE formula requires at least 6 historical YoY PAT differences (10 consecutive historical quarters), filings prior to 2021 lacked sufficient XBRL history and were dropped upstream. The actual empirical sample begins in 2021.

---

## 4. Leakage Controls & Timing Protocol

To ensure 100% point-in-time validity:
1. **Cutoff Rule (15:30 IST):**
   - Filing timestamp $\le$ 15:30 IST $\to$ Event Day $T = \text{filing day}$. Entry at Open of $T+1$.
   - Filing timestamp $>$ 15:30 IST $\to$ Event Day $T = \text{next trading day}$. Entry at Open of $T+2$.
2. **Strict Open Entry:** Trades enter at the market `Open` price of the session *following* the event day close. Announcement-day price changes are 100% excluded.
3. **Ex-Ante Quantile Thresholds:** At any date $T$, quintile cuts ($q_{20}, q_{40}, q_{60}, q_{80}$) are calculated exclusively from events that filed in the window $[T - 365, T)$. No future information within the quarter is accessed.

---

## 5. Baseline vs. Ex-Ante Results Comparison

| Horizon / Model | V1 Baseline *(Look-Ahead)* | Ex-Ante M1 *(365d Rolling)* | Ex-Ante M2 *(730d Rolling)* | Ex-Ante M3 *(Expanding)* |
|---|---|---|---|---|
| **5-Day Spread** | +0.41% | **+0.50%** | +0.52% | +0.51% |
| **10-Day Spread** | +0.79% | **+0.87%** | +0.89% | +0.88% |
| **20-Day Spread** | N/A | **+1.34%** | +1.38% | +1.36% |
| **30-Day Spread** | +1.24% | **+1.18%** | +1.21% | +1.19% |
| **40-Day Spread** | N/A | **+1.59%** | +1.64% | +1.62% |
| **60-Day Spread** | **+2.50%** | **+2.77%** | **+2.91%** | **+2.89%** |
| **90-Day Spread** | N/A | **+3.58%** | +3.65% | +3.61% |
| **126-Day Spread** | +4.13% | **+3.90%** | +4.02% | +3.98% |
| **60d p-value** | $8.29 \times 10^{-6}$ | **$3.88 \times 10^{-7}$** | $1.05 \times 10^{-7}$ | $1.14 \times 10^{-7}$ |
| **Fold Positivity (%)** | 76.2% / 80.0% | **85.0%** | 84.2% | 85.0% |
| **Ex-Best Spread (%)** | +2.27% | **+2.90%** | +2.70% | +2.94% |

---

## 6. Monotonicity & Robustness Evidence

Across the 5 ex-ante quintiles at 60 trading days:
- **Q1 (Worst Misses):** **−1.58%**
- **Q2:** **+0.07%**
- **Q3 (Neutral):** **−0.06%**
- **Q4:** **+0.65%**
- **Q5 (Best Beats):** **+1.20%**
- **Total Inversions:** 1 (Q2 vs Q3, difference = 0.13pp). Passes pre-registered standard ($\le 1$ inversion).
- **Asymmetry:** Q1 underperformance (-1.58%) exceeds Q5 outperformance (+1.20%). The market punishes earnings misses more than it rewards beats.

---

## 7. Size & Sector Diagnostics

### 7.1 Size Analysis: Coincidence Check on Identical +2.11% Spread
A forensic check was conducted on why Mid-Cap and Large-Cap spreads appeared identical (+2.11%):
- **Mid Caps:** Q5 = +1.5850%, Q1 = −0.5277%, Spread = **+2.1127%** (Median daily turnover: INR 45.0 Cr).
- **Large Caps:** Q5 = +0.8452%, Q1 = −1.2650%, Spread = **+2.1101%** (Median daily turnover: INR 206.7 Cr).
- **Small Caps:** Q5 = +1.2289%, Q1 = −2.7118%, Spread = **+3.9407%** (Median daily turnover: INR 8.7 Cr).
- **Diagnosis:** It is a **pure rounding coincidence** (+2.1127% vs +2.1101%), NOT a software bug. The underlying drivers are completely different: Mid-cap spread is propelled by strong Q5 earnings beats (+1.59%), whereas Large-cap spread is propelled by severe Q1 punishment (-1.26%).

### 7.2 Sector Breakdown (Financials vs Non-Financials)
- **Non-Financials (6,931 events):** 60d spread = **+3.475%** ($p < 0.0001$, 85.0% folds positive, ex-best: +3.64%).
- **Financials / Banks / NBFCs (887 events):** 60d spread = **−3.956%** ($p = 0.018$, only 42.9% folds positive).
*Conclusion:* Banks and NBFCs experience an inversion because accounting provisions distort random-walk SUE expectations. Financials are permanently excluded from strategy execution.

---

## 8. Filing-Timing Diagnostics & Portfolio Resolution

| Filing Cohort | Days from QE | Median Daily Turnover | Large-Cap Share | 60d Spread |
|---|---|---|---|---|
| **Early Filers** | $\le 25$ days | INR 97.0 Cr | 36.8% | **+0.48% (p = 0.70)** |
| **Mid Filers** | $26 \dots 45$ days | INR 42.1 Cr | 34.1% | **+3.10% (p = 0.000)** |
| **Late Filers** | $> 45$ days | INR 27.8 Cr | 27.9% | **+3.84% (p = 0.010)** |

### Post-Mortem of V1 FIFO Capacity Failure:
In V1, a 15-position FIFO queue accepted trades with median filing speed of 24 days, taking large caps with a realized excess return of **−0.65%**. The skipped trades (median 38 days) delivered **+1.64%**. The FIFO rule inadvertently acted as an adverse selection filter.

---

## 9. Portfolio Backtest Grid Results (True Mark-to-Market)

All portfolio simulations apply **0.585% round-trip transaction costs** and are computed from **daily mark-to-market valuations** across all open positions and cash:

| Configuration | Universe | Queue Policy | Slots | Horizon | MtM CAGR | Nifty 500 CAGR | **Excess CAGR** | MtM Sharpe | MtM Volatility | MtM Max DD | Win Rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **V1 Replicated** | All Sectors | FIFO | 10 | 60d | +14.07% | +11.10% | +2.97% | 0.785 | 17.9% | -31.97% | 52.3% |
| **V1 Replicated** | All Sectors | FIFO | 20 | 60d | +12.14% | +10.90% | +1.24% | 0.751 | 16.2% | -28.21% | 51.9% |
| **V2 Candidate** | **Non-Financials** | **SUE_RANK** | **30** | **60d** | **+16.83%** | **+11.05%** | **+5.78%** | **1.017** | **16.8%** | **-25.12%** | **53.8%** |
| **V2 Focused** | Non-Financials | SUE_RANK | 10 | 60d | +16.52% | +11.11% | +5.41% | 0.892 | 18.5% | -29.09% | 54.0% |
| **V2 Moderate**| Non-Financials | SUE_RANK | 20 | 60d | +14.36% | +10.88% | +3.48% | 0.863 | 16.6% | -29.15% | 53.2% |
| **V2 Long-Horizon**| Non-Financials | SUE_RANK | 20 | 90d | +12.11% | +11.13% | +0.98% | 0.858 | 14.1% | -22.06% | 54.4% |

---

## 10. Cost & Capacity Stress Testing (True Mark-to-Market)

- **Cost Sensitivity (30-Slot Non-Financials, 60d, MtM):**
  - Low Friction (0.300%): **+18.11% CAGR (+7.06% excess), Sharpe: 1.083, Max DD: -24.70%**
  - Baseline Friction (0.585%): **+16.83% CAGR (+5.78% excess), Sharpe: 1.017, Max DD: -25.12%**
  - Severe Friction (1.000%): **+14.98% CAGR (+3.93% excess), Sharpe: 0.921, Max DD: -25.72%**
- **AUM Capacity Constraints:**
  - Annualized portfolio turnover is ~280% to 330%.
  - At 1% volume participation: **INR 15 Cr to 30 Cr**.
  - At 5% volume participation: **INR 80 Cr to 150 Cr**.

---

## 11. Holdout Performance & Adversarial Kill Tests

### 11.1 Discovery (2021–2023) vs. Holdout (2024–2026)
- **Cross-Sectional Spread:** Discovery = **+3.33%**; Holdout = **+2.29%** ($p = 0.0013$, **90.0% positive folds**).
- **Portfolio Strategy (30 Slots, MtM):**
  - **Discovery Period:** **+26.81% CAGR (+11.31% excess vs Nifty 500)**, Sharpe: **1.60**.
  - **Holdout Period:** **+7.55% CAGR (+0.14% excess vs Nifty 500)**, Sharpe: **0.51**, Max DD: **-25.12%**. (Trade-level arithmetic: +7.68% CAGR, +0.28% excess).

### 11.2 Kill Test Summary (0 of 7 Triggered)
- **KT1 (Drop Top-2 Folds):** Spread remains **+2.54%**, fold positivity **83.3%** (**PASSED**).
- **KT2 (Drop 2021 Burn-in):** Spread remains **+2.60%**, $p < 0.0001$ (**PASSED**).
- **KT3 (Mid & Large Caps Only):** Spread remains **+2.04%**, $p = 0.0021$ (**PASSED**).
- **KT4 (Exclude Layer-4 Seen):** Spread remains **+2.82%**, fold positivity **85.0%** (**PASSED**).
- **KT5 (1.000% Friction Stress):** Strategy CAGR remains positive at **+14.98%** (**PASSED**).
- **KT6 (Historical Window Stability):** 8Q = +2.91%, Expanding = +2.89% (**PASSED**).
- **KT7 (Horizon Jitter):** 40d = +1.59%, 90d = +3.58% (**PASSED**).

---

## 12. Limitations & Uncertainties

1. **Holdout Compression:** While the cross-sectional spread remained robust on holdout (+2.29%), portfolio CAGR compressed from +26.8% in Discovery to +7.55% in Holdout (barely matching Nifty 500's +7.41%).
2. **Absence of Consensus Analyst Estimates:** The model relies on a seasonal random walk. Fast-growing cyclical businesses may be misclassified.
3. **Long-Only Drag:** The short side (Q1 = -1.58%) contributes over half of the cross-sectional alpha. In a long-only portfolio, half of the economic edge cannot be directly captured.

---

## 13. Final Classification

> ### **FINAL VERDICT: Signal confirmed; strategy is a forward-test candidate.**
>
> The PEAD V2 research program confirms that Post-Earnings-Announcement Drift in Indian equities survives strict ex-ante point-in-time thresholding (+2.77% spread, $p = 3.88 \times 10^{-7}$, 85% positive folds).  
> The 30-slot, Non-Financials long-only strategy is a promising implementation that generated **+16.83% CAGR (+5.78% excess vs Nifty 500)** over the full period under authentic mark-to-market valuation (Sharpe: 1.02, Max DD: -25.12%), but compressed to **+7.55% CAGR (+0.14% excess)** in the 2024–2026 holdout.
>
> Because the strategy configuration was finalized after observing V1 diagnostics and the full-period grid, it is designated as a **Forward-Test Candidate**, frozen in [`live_config_pead_v2.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/live_config_pead_v2.md) and tracked forward in [`forward_record_pead_v2.csv`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/forward_record_pead_v2.csv).
