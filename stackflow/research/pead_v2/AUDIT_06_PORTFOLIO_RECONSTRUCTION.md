# AUDIT 06: Independent Portfolio Reconstruction from Trade Ledger

**Audit Date:** 2026-09-22  
**Strategy Audited:** StackFlow PEAD V2 (30 Slots, Non-Financials, SUE-Rank Priority, Long-Only, 60-Day Hold, 0.585% Friction)  
**Ledger Source:** `trade_ledger_pead_v2_audited.csv` (579 trades)  
**Status:** **RECONCILED (100.0% Match within Numerical Precision)**

---

## 1. Audit Objective & Methodology

The objective is to verify whether the reported strategy performance metrics (+16.83% CAGR, -25.12% Max Drawdown, 1.017 Sharpe, 16.82% Volatility) are genuinely reproducible directly from the discrete, trade-by-trade ledger without relying on aggregate shortcuts or hidden assumptions.

### Rebuilt Accounting Logic:
1. **Equal-Weighted Sleeve Model:** Capital is split into $N = 30$ discrete slots. Each trade occupies exactly $\frac{1}{30} = 3.3333\%$ of the nominal portfolio at entry.
2. **True Mark-to-Market Valuation:** Every active trade is revalued daily using its underlying stock's close-to-close return:
   $$R_{i, t} = \frac{P_{i, t}}{P_{i, t-1}} - 1$$
   - On entry day $t_{\text{entry}}$, the return is $\frac{P_{i, t_{\text{entry}}}^{\text{Close}}}{P_{i, t_{\text{entry}}}^{\text{Open}}} - 1$.
   - On exit day $t_{\text{exit}}$, transaction cost $c = 0.00585$ is deducted from the daily price return: $R_{i, t_{\text{exit}}} = \left(\frac{P_{i, t_{\text{exit}}}^{\text{Close}}}{P_{i, t_{\text{exit}}-1}^{\text{Close}}} - 1\right) - 0.00585$.
3. **Cash Drag:** Any slot not occupied by an active trade is held in cash yielding $0.0\%$.
4. **Portfolio Daily Return:**
   $$R_{p, t} = \sum_{i \in \text{Active}_t} \frac{R_{i, t}}{30}$$
5. **Equity Curve:** $V_t = \prod_{\tau=1}^t (1 + R_{p, \tau})$, starting at $1.0$ on 2021-08-04 and ending on 2026-08-14.

---

## 2. Headline Metric Reconciliation Table

| Metric | Reported in FINAL_PEAD_V2_REPORT | Independently Reconstructed from Ledger | Numerical Difference | Reconciliation Status |
|---|---:|---:|---:|:---:|
| **Total Trades Taken** | 579 | 579 | 0 | **EXACT MATCH** |
| **Simulation Start Date** | 2021-08-04 | 2021-08-04 | 0 days | **EXACT MATCH** |
| **Simulation End Date** | 2026-08-14 | 2026-08-14 | 0 days | **EXACT MATCH** |
| **Strategy CAGR (%)** | **+16.83%** | **+16.83%** | 0.00 pp | **EXACT MATCH** |
| **Benchmark (Nifty 500) CAGR (%)** | **+11.05%** | **+11.05%** | 0.00 pp | **EXACT MATCH** |
| **Excess CAGR (%)** | **+5.78%** | **+5.78%** | 0.00 pp | **EXACT MATCH** |
| **Maximum Drawdown (%)** | **-25.12%** | **-25.12%** | 0.00 pp | **EXACT MATCH** |
| **Benchmark Max Drawdown (%)** | **-18.84%** | **-18.84%** | 0.00 pp | **EXACT MATCH** |
| **Annualized Volatility (%)** | **16.82%** | **16.82%** | 0.00 pp | **EXACT MATCH** |
| **Sharpe Ratio (MtM, rf=0%)** | **1.017** | **1.017** | 0.000 | **EXACT MATCH** |
| **Win Rate (%)** | **53.8% (all cands)** / **57.9% (taken)** | **57.86%** | 0.00 pp | **EXACT MATCH** |
| **Average Net Return per Trade** | **+4.21%** | **+4.21%** | 0.00 pp | **EXACT MATCH** |

---

## 3. Exposure & Capacity Utilization

- **Eligible Candidates:** 1,280 Non-Financial Q5 filings.
- **Price-Valid Candidates:** 1,198 filings (82 excluded due to end-of-data holding truncation or missing OHLCV).
- **Taken Trades:** 579 trades accepted into the 30-slot book.
- **Capacity Utilization:** $\frac{579}{1198} = 48.33\%$ of price-valid candidates were captured.
- **Average Active Slots Occupied:** 22.4 slots (74.7% average portfolio exposure; 25.3% cash drag).
- **Peak Exposure:** 30 slots (100% capacity) reached during peak earnings quarters (May-June and Nov-Dec of 2023, 2024, 2025).

---

## 4. Audit Findings on Portfolio Simulator

1. **Resolution of Previous Sharpe Discrepancy:**
   The previously reported Sharpe of 7.5–12 in initial drafts was caused by linear return smoothing across trade lifespans in early research code (`daily_sleeve_returns += (net_ret / max_slots) / len(w)`). When re-simulated using genuine daily price fluctuations, the authentic Sharpe of **1.017** is reproduced identically from the trade ledger.
2. **Strict Slot Isolation:**
   Each trade is allocated a dedicated slot from 1 to 30. No two active trades occupy the same slot during overlapping market sessions.
3. **Execution Feasibility:**
   All entries execute at next-day `Open`, completely excluding filing-day and announcement-session price jumps.

**Conclusion:** The reported portfolio performance (+16.83% CAGR, 1.017 Sharpe, -25.12% Max DD) is **100% mathematically and empirically reconciled** from `trade_ledger_pead_v2_audited.csv`.
