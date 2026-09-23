# StackFlow PEAD V2 — Master Forensic Audit & Independent Validation Report

**Document Date:** 2026-09-22  
**Auditor:** Antigravity (Lead Quantitative Researcher & Forensic Research-Engineering Agent)  
**Strategy Audited:** StackFlow PEAD V2 (30-Slot, Non-Financials, SUE-Rank Priority, 60-Day Hold, 0.585% Friction)  
**Trade Ledger:** `trade_ledger_pead_v2_audited.csv` (579 Executed Trades)  

---

## 1. Executive Verdict

### **VERIFIED WITH CAVEATS**

The underlying quantitative anomaly—Post-Earnings-Announcement Drift (PEAD) driven by Standardized Unexpected Earnings (SUE)—is **statistically robust, point-in-time correct, and confirmed across Indian equities**. When computed strictly ex-ante using rolling historical percentiles from the preceding 365 calendar days, the 60-day cross-sectional excess spread (Q5 − Q1) is **+2.77%** ($p = 3.88 \times 10^{-7}$), with **85.0% of quarterly folds positive** and zero lookahead leakage across 7,818 audited events.

However, the initial reported trading strategy metrics and validation claims require **two fundamental corrections and downgrades**:
1. **The Initial Sharpe (7.5–12), CAGR (+17.73%), and Max Drawdown (-11.0%) Were Computationally Flawed:**
   Initial drafts smoothed trade returns linearly across holding days (`net_ret / 60`), artificially compressing portfolio daily volatility to near-zero (~1.5%) and creating impossible Sharpe ratios. Under true daily mark-to-market (MtM) accounting across all active positions and cash drag:
   - Authentic Strategy CAGR is **+16.83%** (vs. Nifty 500 **+11.05%**, **+5.78% Excess**).
   - Authentic Annualized Volatility is **16.82%** (not 1.5%).
   - Authentic Sharpe Ratio is **1.017** (not 7.5–12.0).
   - Authentic Maximum Drawdown is **-25.12%** (not -11.0%).
2. **The Portfolio Strategy Was Selected Post-Hoc Across a 96-Cell Grid (Holdout Contaminated):**
   While the cross-sectional signal was evaluated on 2021–2023 discovery data, the portfolio configuration (30 slots, SUE-rank priority, Non-Financial exclusion) was chosen after inspecting full-period (2021–2026) grid backtests. Therefore, the 2024–2026 holdout cannot be claimed as an unadulterated out-of-sample test for the strategy. In the holdout period, strategy excess return compressed to **+0.14% to +0.28%** (Sharpe 0.51).
   
**Official Reclassification:**
> **"Signal confirmed; strategy is a forward-test candidate."**

---

## 2. Headline Reconciliation Table

| Metric | Original / Draft Claim | Independently Reconstructed (Ledger MtM) | Numerical Difference | Audit Status | Explanation |
|---|---:|---:|---:|:---:|---|
| **Strategy CAGR (%)** | +17.73% | **+16.83%** | -0.90 pp | **RECONCILED** | Linear smoothing inflated CAGR slightly; MtM compounded return is +16.83%. |
| **Benchmark CAGR (%)** | +11.05% | **+11.05%** | 0.00 pp | **EXACT MATCH** | Nifty 500 Price Return series over 2021-08-04 to 2026-08-14. |
| **Excess CAGR (%)** | +6.68% | **+5.78%** | -0.90 pp | **RECONCILED** | Corrected net excess return over benchmark. |
| **Holdout Strategy CAGR (%)** | Not featured | **+7.55% to +7.68%** | — | **HEADLINE ADDED** | Holdout excess is +0.14% (MtM) to +0.28% (arithmetic). |
| **Holdout Excess CAGR (%)** | Not featured | **+0.14% to +0.28%** | — | **HEADLINE ADDED** | Severe decay from discovery excess (+10.18%). |
| **Max Drawdown (%)** | -11.0% | **-25.12%** | -14.12 pp | **CORRECTED** | Linear smoothing masked true peak-to-trough drawdowns during 2024–2025. |
| **Sharpe Ratio** | 7.5 to 12.0 | **1.017** | -6.5 to -11.0 | **CORRECTED** | Eliminated mathematical volatility compression error. |
| **Annualized Volatility (%)** | ~1.5% to 2.0% | **16.82%** | +15.0 pp | **CORRECTED** | True daily mark-to-market volatility. |
| **Total Executed Trades** | ~580 | **579** | -1 trade | **EXACT MATCH** | 579 individual discrete trades across 30 slots. |
| **Cumulative Strategy Return** | ~+125% | **+118.82%** | -6.18 pp | **RECONCILED** | Full 5.03-year compounded portfolio multiplier (2.188x). |
| **Round-Trip Friction** | 0.585% | **0.585% (58.5 bps)** | 0.00 bps | **EXACT MATCH** | Applied strictly to all 579 trades (Total: 338.7% notional debit). |

---

## 3. Overfitting Assessment

| Strategy Parameter | Final Frozen Value | Alternatives Evaluated in Grid | Pre-Registered in V1? | Selected After Observing Results? | Contamination Classification |
|---|:---:|---|:---:|:---:|:---:|
| **Signal Definition** | SUE (YoY PAT / 8Q SD) | Revisions, EAR, raw PAT | **YES** | No | **CLEAN (Discovery-only)** |
| **Ex-Ante Lookback** | 365 Days Rolling | 730 Days, Expanding | No (V1 used Qtr) | Evaluated across 3 models | **CLEAN (Robust across all 3)** |
| **Portfolio Capacity** | **30 Slots** | 10 Slots, 20 Slots, 30 Slots | **NO** (V1 locked 10-15) | **YES** (Selected after 15 failed) | **HOLDOUT CONTAMINATED** |
| **Queue Policy** | **SUE-Rank Priority** | FIFO, Equal Probability | **NO** (V1 locked FIFO) | **YES** (Selected after FIFO failed) | **HOLDOUT CONTAMINATED** |
| **Sector Universe** | **Non-Financials Only** | All Sectors, Ex-IT | **NO** (V1 used All) | **YES** (Selected after Fin inverted) | **HOLDOUT CONTAMINATED** |
| **Holding Period** | **60 Trading Days** | 20d, 40d, 60d, 90d, 126d | **YES** (Primary V1 cell) | Verified across 5 horizons | **CLEAN (Pre-registered)** |
| **Entry Timing** | Next-Day Open ($T+1$) | Same-day Close, $T+2$ | **YES** | No | **CLEAN (Pre-registered)** |
| **Cost Assumption** | 0.585% Round-Trip | 0.300%, 1.000% | **YES** | Tested for sensitivity | **CLEAN (Standard NSE Model)** |

---

## 4. Leakage Assessment

1. **SUE Leakage: NONE FOUND.**  
   PAT is historical quarterly net profit. Denominator standard deviation uses strictly prior YoY differences (`yoy[max(0, i-8):i]`).
2. **Threshold Leakage: NONE FOUND.**  
   Verified in `AUDIT_05_POINT_IN_TIME.csv`. Across all 7,818 events, `max(historical_information_timestamp) < event_timestamp` passed with 0 violations.
3. **Filing Date Leakage: NONE FOUND.**  
   Exchange broadcast timestamps are strictly segregated at 15:30 IST. Post-15:30 filings enter at $T+2$ Open.
4. **Entry Price Leakage: NONE FOUND.**  
   All trades enter at official exchange `Open` strictly subsequent to event day close. Announcement-day jump is 100% excluded.
5. **Exit Price Leakage: NONE FOUND.**  
   Exits execute at session $T_{\text{entry}} + 60$ Close. No early stopping or peek-ahead exits.
6. **Universe Leakage: MINOR CAVEAT.**  
   Static 421-symbol list extracted from 2024–2026 XBRL cache introduces mild survivorship bias (~0.4% to 0.8%/year), though offset by strict liquidity ($ADV \ge 1\text{ Cr}$) and price ($P \ge 50$) criteria.
7. **Benchmark Leakage: NONE FOUND.**  
   Nifty 500 series aligned on identical calendar days from official index provider.
8. **Corporate Action Leakage: NONE FOUND.**  
   Price histories are backwards split/bonus adjusted from primary exchange feeds.

---

## 5. Trade Ledger Verification

- Master trade ledgers (`trade_ledger_pead_v2.csv` and `trade_ledger_pead_v2_audited.csv`) have been generated and independently reconstructed.
- **Completeness:** Contains exactly 579 executed trades with 26 standardized columns (`trade_id`, `symbol`, `filing_timestamp`, `entry_date`, `entry_price`, `exit_date`, `exit_price`, `holding_days`, `SUE`, `slot`, `gross_return`, `transaction_cost`, `net_return`, `portfolio_weight`, `portfolio_pnl`, etc.).
- **Traceability:** Every single trade traces from raw XBRL filing through point-in-time thresholding, slot assignment, and daily revaluation.
- **Random Sample:** 50 randomly sampled trades audited in `AUDIT_14_RANDOM_TRADES.csv` confirmed 100% data integrity with zero unexplained trades.

---

## 6. Research Chronology & Discovery Timeline

```
2026-09-22 (Early AM): Initial PEAD Discovery by Claude Code (V1 Report)
                       - Look-ahead quarterly grouping: +2.50% 60d spread.
                       - Discovery: 76.2% / 80.0% fold positivity.
                       - Capacity Failure: 15-slot FIFO book delivered only +8.38% CAGR (failed vs Nifty +10.91%).

2026-09-22 (Mid-Day):  PEAD V2 Program Executed
                       - Ex-ante rolling 365d thresholds implemented (+2.77% spread, p < 1e-6).
                       - Diagnostics reveal Financials inverted (-3.96%) and Early Filers diluted (+0.48%).
                       - 96-cell portfolio grid tested on full 2021–2026 dataset.
                       - 30-slot Non-Financials SUE-rank configuration chosen (+17.73% CAGR, -11.0% DD reported).

2026-09-22 (Evening):  Independent Forensic Audit & Anti-Overfitting Review
                       - Linear smoothing bug uncovered: Volatility corrected 1.5% -> 16.82%; Sharpe 12.0 -> 1.017; Max DD -11.0% -> -25.12%.
                       - Holdout contamination confirmed: 30 slots and SUE ranking selected post-hoc.
                       - Master trade ledger constructed (579 trades).
                       - Strategy formally downgraded to "Forward-Test Candidate".
```

---

## 7. What Survives

1. **The Cross-Sectional PEAD Anomaly in India is Real:**  
   The ex-ante drift spread is **+2.77%** over 60 trading days ($p = 3.88 \times 10^{-7}$), with **85.0% quarterly fold consistency**. It is not an artifact of lookahead grouping.
2. **Economic Transmission Mechanism is Confirmed:**  
   Monotonicity holds ($\le 1$ inversion across all tested horizons). Drift expands monotonically with horizon (+0.50% at 5d $\to$ +1.34% at 20d $\to$ +2.77% at 60d $\to$ +3.90% at 126d).
3. **The Strategy Beats the Benchmark Over 5 Years:**  
   Net of 0.585% transaction costs, the 30-slot Non-Financials strategy delivered **+16.83% CAGR vs. +11.05% Nifty 500 (+5.78% Excess)** with a **1.017 Sharpe ratio**.
4. **Execution Robustness:**  
   The strategy survives severe friction stress (at 100 bps cost, CAGR is +14.98%, excess +3.93%). Dropping the top 10 winning trades only reduces CAGR from +16.83% to +16.22%.

---

## 8. What Must Be Downgraded

1. **Downgrade Status from "Validated Trading Strategy" to "Forward-Test Candidate":**  
   Because the portfolio grid decisions were informed by full-period data that included 2024–2026, the portfolio cannot claim out-of-sample validation.
2. **Delete All Mentions of Sharpe 7.5–12.0 and -11.0% Max Drawdown:**  
   These figures were computational illusions resulting from daily return smoothing. The authentic metrics are **Sharpe 1.017** and **Max Drawdown -25.12%**.
3. **Mandate Dual Headline Reporting:**  
   Every presentation of PEAD V2 must pair the full-period figure (+16.83% CAGR, +5.78% excess) with the holdout figure (**+7.55% to +7.68% CAGR, +0.14% to +0.28% excess**).
4. **Account for Indian Small/Mid-Cap Beta:**  
   The strategy's outperformance was heavily concentrated in the 2023 small/mid-cap bull run (+50.32% vs +25.16% Nifty). In 2025, the strategy underperformed the Nifty 500 by -9.15 pp.
