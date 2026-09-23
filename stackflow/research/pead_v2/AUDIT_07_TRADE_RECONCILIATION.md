# AUDIT 07: Trade-Level P&L and Slot Reconciliation

**Audit Date:** 2026-09-22  
**Ledger Audited:** `trade_ledger_pead_v2_audited.csv`  
**Total Trades Analyzed:** 579  
**Status:** **PASSED (Zero Trade Duplications, Zero Unexplained Exits, Zero Missing Trades)**

---

## 1. Trade Integrity Assertions

| Check | Assertion Description | Expected | Observed | Status |
|---|---|:---:|:---:|:---:|
| **Trade ID Uniqueness** | `trade_id.nunique() == len(df)` | 579 | 579 | **PASSED** |
| **Duplicate Trades** | Identical `(symbol, entry_date)` | 0 | 0 | **PASSED** |
| **Missing Prices** | `entry_price > 0` and `exit_price > 0` | 579 | 579 | **PASSED** |
| **Holding Duration** | `holding_days == 60` trading bars | 579 | 579 | **PASSED** |
| **Filing Date Validity** | `filing_timestamp <= entry_date` | 579 | 579 | **PASSED** |
| **Exit Reasons** | Explicitly classified exit reason | 100% `60D_HOLD_COMPLETE` | 579 | **PASSED** |
| **Entry Reasons** | Explicitly classified entry reason | 100% `Q5_SUE...` | 579 | **PASSED** |
| **Cost Application** | Round-trip cost deducted from net return | 0.00585 (0.585%) | 579 | **PASSED** |

---

## 2. Portfolio P&L vs. Sum of Trade P&L

In an event-driven multi-sleeve portfolio, total performance can be analyzed both additively (nominal cash P&L) and multiplicatively (compounded equity curve):

### 2.1 Additive Sleeve Accounting:
$$\text{Sum of Trade Net Returns} = \sum_{i=1}^{579} R_{\text{net}, i} = +2,435.43\% \quad (+24.3543)$$
$$\text{Portfolio Nominal P&L} = \sum_{i=1}^{579} \left( \frac{1}{30} \times R_{\text{net}, i} \right) = \frac{+2,435.43\%}{30} = \mathbf{+81.18\%}$$
- Mean net trade return: **+4.21%** (Gross: +4.80%, Cost: -0.585%).
- Median net trade return: **+2.48%**.
- Profitable trades: 335 of 579 (**57.86% win rate**).
- Unprofitable trades: 244 of 579 (**42.14% loss rate**).
- Average winning trade: **+13.41%**.
- Average losing trade: **-8.43%**.
- Profit Factor: $\frac{335 \times 13.41\%}{244 \times 8.43\%} = \mathbf{2.18}$.

### 2.2 Multiplicative Compounded Mark-to-Market:
When reinvesting sleeve capital dynamically over the 5.03-year period (2021-08-04 to 2026-08-14), geometric compounding lifts the final portfolio multiplier:
$$V_{\text{final}} = \prod_{t=1}^{T} (1 + R_{p, t}) = 2.1882 \implies \mathbf{+118.82\% \text{ Cumulative Return}}$$
$$\text{CAGR} = (2.1882)^{1 / 5.027} - 1 = \mathbf{+16.83\%}$$

---

## 3. Slot Occupancy & Concurrency Audit

The portfolio architecture limits concurrent exposure to at most 30 simultaneous positions ($S_1 \dots S_{30}$):
- **Discrete Slot Assignment:** Each entering trade is assigned the lowest available free integer slot $s \in [1, 30]$.
- **Overnight Concurrency Check:** Across all 1,236 trading days in the backtest:
  $$\max_{t, s} \text{ActivePositions}(t, s) = 1$$
  There are zero instances where two stocks occupied the same slot overnight.
- **Queue Handover:** When trade $A$ in slot $s$ reaches its 60th trading day, it exits at the 15:30 Close. Slot $s$ becomes eligible for a new trade $B$ entering at the next day's Open.
- **Priority Enforcement:** On days where available slots $k < \text{Candidates}$, candidates are strictly sorted by ex-ante SUE magnitude descending. The top $k$ candidates take the available slots, and candidate $k+1$ is dropped. Zero queue prioritization errors were found.

**Conclusion:** The trade ledger is fully reconciled, point-in-time verified, and mathematically complete.
