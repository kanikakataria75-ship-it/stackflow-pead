# AUDIT 17: Discovery vs. Holdout Trade Ledger Audit

**Audit Date:** 2026-09-22  
**Temporal Partition:** Discovery (2021-08 to 2023-12) vs. Holdout (2024-01 to 2026-08)  
**Ledger Evaluated:** `trade_ledger_pead_v2_audited.csv`  
**Status:** **AUDITED (Substantial Edge Compression Documented Out-of-Sample)**

---

## 1. Trade Ledger Partition Metrics

The 579 executed trades were partitioned strictly by entry date into Discovery ($N = 279$) and Holdout ($N = 300$):

| Performance Metric | Discovery Period *(2021–2023)* | Holdout Period *(2024–2026)* | Full Backtest Period *(2021–2026)* | Out-of-Sample Retention |
|---|---:|---:|---:|:---:|
| **Trades Executed** | 279 | 300 | 579 | 107.5% volume |
| **Strategy CAGR (%)** | **+25.35%** | **+7.55% to +9.51%** | **+16.83%** | ~37% retention |
| **Nifty 500 Benchmark CAGR (%)** | **+15.18%** | **+7.32% to +7.41%** | **+11.05%** | — |
| **Net Excess CAGR (%)** | **+10.18 pp** | **+0.14 pp to +2.20 pp** | **+5.78 pp** | **Compresses sharply** |
| **MtM Sharpe Ratio** | **1.50** | **0.51 to 0.61** | **1.017** | ~38% retention |
| **Maximum Drawdown (%)** | **-20.32%** | **-25.12%** | **-25.12%** | Full drawdown in holdout |
| **Trade Win Rate (%)** | **62.4%** | **53.7%** | **57.9%** | -8.7 pp decay |
| **Average Net Return / Trade** | **+5.89%** | **+2.65%** | **+4.21%** | -3.24 pp decay |

---

## 2. Integrity & Contamination Audit

1. **Were Parameters Retuned on the Holdout?**
   - **No formal retuning:** The strategy rules (30 slots, SUE-rank, Non-Financials, 60d holding, 0.585% friction) were applied identically to both halves.
2. **Was the Holdout Contaminated During Grid Selection?**
   - **YES (Documented in AUDIT 03):** The 96-cell portfolio grid was evaluated over the full 2021–2026 period before selecting the 30-slot Non-Financials configuration as the headline winner.
   - While the underlying cross-sectional signal (SUE Q5 − Q1) was pre-registered in V1, the specific portfolio implementation (30 slots vs 10/20 slots; SUE ranking vs FIFO) was finalized after observing full-sample behavior.
   - Consequently, the 2024–2026 period was *not* a blind out-of-sample test for the portfolio parameters.

---

## 3. Empirical Verdict: Edge Decay and Reality Check

1. **The Signal Remains Directionally Positive:**
   - In the Holdout period, the cross-sectional 60-day spread remained statistically significant (+2.29%, $p = 0.0013$, 90% of quarterly folds positive).
   - In the portfolio implementation, the strategy generated positive excess return (+0.14% to +2.20% net of costs) and maintained a positive Sharpe (0.51 to 0.61).
2. **Alpha Halving:**
   - Strategy excess return dropped from **+10.18% in Discovery** to **+0.14% / +0.28% in Holdout**.
   - Average net trade return fell from **+5.89%** to **+2.65%**.
   - The entire maximum drawdown of the strategy (-25.12%) occurred during the 2024–2026 window.

**Conclusion:** The holdout analysis confirms that PEAD is a genuine anomaly, but realistic portfolio capture decays substantially out-of-sample. The downgrade from "Validated Trading Strategy" to **"Signal confirmed; strategy is a forward-test candidate"** is fully warranted.
