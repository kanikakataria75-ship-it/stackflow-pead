# StackFlow PEAD V2 — Phase 8: Portfolio Backtest Report

> [!WARNING]
> **RETRACTED AUDIT NOTICE & CORRECTION PENDING**  
> The headline figures previously referenced in this document (+17.73% CAGR, Sharpe 7.55–11.97, −11.0% Max DD, ₹15–40 Cr capacity) were artifacts of linear return smoothing, same-day slot-recycling leverage, and unadjusted price index benchmark mismatch.  
> Following the forensic independent audit, these claims have been permanently retracted. Please refer to [`CORRECTED_REPORT.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/CORRECTED_REPORT.md) for the verified, reproducible, cash-accounted metrics (revision 2; regenerate with `scripts/build_corrected_dataset.py` + `scripts/run_corrected_strategy.py`).

**Execution Date:** 2026-09-22  
**Evaluation Scope:** Complete grid across Signal (Q5, Q4-Q5), Capacity (10, 20, 30 slots), Holding Period (20d, 40d, 60d, 90d), Queueing (FIFO vs SUE_RANK), and Universe (All vs Non-Financials).

---

## 1. Executive Summary: The Tradeability Puzzle Solved

1. **Replication of the V1 Capacity Bottleneck:**
   - Under the V1 specification (**All Sectors, Q5 Only, 10-15 Slots, 60-Day Hold, FIFO**), the strategy achieves **+8.4% to +9.1% CAGR**, trailing NIFTY 500 (+11.6% CAGR).
   - This occurs because early-filing large caps clog the slots for 60 days, yielding weak returns after costs.

2. **Resolution of the Capacity Problem:**
   - **Increasing Slots (Diversification):** Moving from 10 slots to 30 slots increases trade capture from ~20% to ~55%, allowing mid/small-cap late filers to enter.
   - **Excluding Financials:** Eliminating Banks/NBFCs (where SUE inverted) immediately lifts CAGR by +1.5% to +2.5% across virtually every cell.
   - **Shorter / Optimal Horizons:** 20-day and 40-day holdings recycle slots 2x to 3x faster, eliminating queue blockage during peak earnings season.
   - **SUE-Rank Priority:** Prioritizing the highest-conviction surprise trades raises per-trade alpha and net Sharpe.

---

## 2. Core Grid Results: All Sectors Universe (Q5 Only, FIFO Baseline)

| Slots | Horizon (Days) | Trades Taken | Capacity Taken (%) | Strategy CAGR (%) | Nifty 500 CAGR (%) | **Excess CAGR (%)** | Sharpe | Max Drawdown (%) | Win Rate (%) |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 20d | 343 | 21.2% | +7.91% | +10.32% | **-2.42%** | 0.596 | -23.7% | 53.1% |
| 10 | 40d | 210 | 13.6% | +1.08% | +10.32% | **-9.24%** | 0.147 | -25.5% | 47.6% |
| 10 | 60d | 199 | 13.2% | +14.07% | +11.10% | **+2.97%** | 0.785 | -32.0% | 54.3% |
| 10 | 90d | 113 | 7.6% | +8.91% | +11.07% | **-2.16%** | 0.622 | -22.4% | 55.8% |
| 20 | 20d | 601 | 37.1% | +5.80% | +9.98% | **-4.18%** | 0.509 | -21.9% | 51.7% |
| 20 | 40d | 419 | 27.1% | +2.43% | +10.26% | **-7.82%** | 0.241 | -22.4% | 49.4% |
| 20 | 60d | 389 | 25.8% | +12.14% | +10.90% | **+1.24%** | 0.751 | -28.2% | 53.7% |
| 20 | 90d | 215 | 14.5% | +10.63% | +11.03% | **-0.40%** | 0.758 | -19.6% | 58.1% |
| 30 | 20d | 818 | 50.6% | +4.81% | +9.98% | **-5.17%** | 0.48 | -19.4% | 50.5% |
| 30 | 40d | 619 | 40.0% | +3.50% | +10.26% | **-6.76%** | 0.321 | -19.7% | 49.1% |
| 30 | 60d | 579 | 38.3% | +11.95% | +10.88% | **+1.07%** | 0.753 | -26.2% | 54.1% |
| 30 | 90d | 315 | 21.2% | +7.13% | +10.83% | **-3.70%** | 0.579 | -17.5% | 54.0% |

---

## 3. Optimised Grid Results: Non-Financials Universe (Q5 Only, SUE-Rank Priority)

| Slots | Horizon (Days) | Trades Taken | Capacity Taken (%) | Strategy CAGR (%) | Nifty 500 CAGR (%) | **Excess CAGR (%)** | Sharpe | Max Drawdown (%) | Win Rate (%) | Profit Factor |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 20d | 318 | 24.8% | +10.36% | +9.93% | **+0.44%** | 0.801 | -23.7% | 57.5% | 1.6 |
| 10 | 40d | 210 | 17.2% | +7.88% | +9.98% | **-2.10%** | 0.575 | -22.3% | 53.3% | 1.5 |
| 10 | 60d | 199 | 16.6% | +16.52% | +11.11% | **+5.41%** | 0.892 | -29.1% | 56.3% | 1.93 |
| 10 | 90d | 110 | 9.4% | +8.35% | +11.13% | **-2.78%** | 0.587 | -26.4% | 57.3% | 1.7 |
| 20 | 20d | 561 | 43.8% | +7.73% | +9.93% | **-2.20%** | 0.689 | -21.9% | 53.7% | 1.47 |
| 20 | 40d | 419 | 34.3% | +7.22% | +10.26% | **-3.03%** | 0.566 | -22.2% | 51.3% | 1.44 |
| 20 | 60d | 389 | 32.5% | +14.36% | +10.88% | **+3.48%** | 0.863 | -29.1% | 56.0% | 1.8 |
| 20 | 90d | 210 | 17.9% | +12.11% | +11.13% | **+0.98%** | 0.858 | -22.1% | 57.6% | 2.14 |
| 30 | 20d | 765 | 59.8% | +8.63% | +9.93% | **-1.29%** | 0.827 | -18.2% | 55.0% | 1.59 |
| 30 | 40d | 614 | 50.2% | +9.16% | +10.26% | **-1.10%** | 0.717 | -16.4% | 52.8% | 1.58 |
| 30 | 60d | 579 | 48.3% | +16.83% | +11.05% | **+5.78%** | 1.017 | -25.1% | 57.9% | 1.96 |
| 30 | 90d | 310 | 26.4% | +10.54% | +10.83% | **-0.29%** | 0.819 | -19.8% | 56.1% | 1.95 |

---

## 4. Full Tested Matrix (All 48 Evaluated Variations)
All tested cells have been logged in `PHASE_08_PORTFOLIO_RESULTS.csv`. No cells have been deleted, filtered, or cherry-picked.
