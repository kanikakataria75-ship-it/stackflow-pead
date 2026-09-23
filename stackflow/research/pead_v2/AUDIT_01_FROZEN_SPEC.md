# StackFlow PEAD V2 Audit — Document 01: Frozen Strategy Specification

> [!WARNING]
> **RETRACTED AUDIT NOTICE & CORRECTION PENDING**  
> The headline figures previously listed in this document (+17.73% CAGR, Sharpe 7.55–11.97, −11.0% Max DD, ₹15–40 Cr capacity) were artifacts of linear return smoothing, same-day slot-recycling leverage, and unadjusted price index benchmark mismatch.  
> Following the forensic independent audit, these claims have been permanently retracted. Please refer to [`CORRECTED_REPORT.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/CORRECTED_REPORT.md) for the verified, reproducible, cash-accounted metrics (revision 2; regenerate with `scripts/build_corrected_dataset.py` + `scripts/run_corrected_strategy.py`).

**Audit Date:** 2026-09-22  
**Purpose:** Independent capture and freeze of the exact PEAD V2 strategy being audited. Extracted directly from `live_config_pead_v2.md`, `src/config.py`, and `src/portfolio_engine.py`.

---

## 1. Core Strategy Parameters (Audited Target)

| Parameter | Frozen Specification | Exact Code / Config Reference |
|---|---|---|
| **Strategy Style** | Event-driven, long-only equity drift | `src/portfolio_engine.py` |
| **Universe Definition** | NSE equities with quarterly XBRL PAT | `src/data_loader.py:load_raw_xbrl_pat()` |
| **Liquidity & Price Filter** | 20-day historical turnover $\ge$ INR 1 Cr ($10^7$ INR), Entry Open $>$ INR 50 | `src/config.py:MIN_TURNOVER`, `MIN_PRICE` |
| **Financial Sector Exclusion** | Non-Financials only (`is_fin == False`); Banking, NBFC, Insurance excluded | `phase_08_backtest/` (`res_df[res_df.universe == "Non_Financials"]`) |
| **Size Treatment** | All size bands eligible (no explicit exclusion of Large/Mid/Small) | Evaluated across all size terciles |
| **Filing Timing Treatment** | All filing cohorts eligible (Early, Mid, Late) | No artificial filing window cutoff |
| **Signal Definition (SUE)** | Seasonal random walk: $\frac{\text{PAT}_t - \text{PAT}_{t-4}}{\sigma(\Delta \text{YoY PAT}_{t-8 \dots t-1})}$ | `src/sue_engine.py:compute_sue_series()` |
| **Minimum History for SUE** | $\ge 6$ prior YoY changes ($\ge 10$ quarters total history) | `src/config.py:MIN_PRIOR_YOY` |
| **Threshold Methodology** | Model M1: Rolling historical quantiles over preceding 365 calendar days ($T-365 \le \text{event} < T$) | `src/sue_engine.py:assign_ex_ante_quintiles_rolling()` |
| **Minimum Events for Threshold** | $\ge 150$ prior qualifying historical events | `src/sue_engine.py:min_events=150` |
| **Signal Trigger** | Top Quintile (Q5): $SUE \ge q_{80}$ historical rolling threshold | `ev.q_exante_4q == 5` |
| **Filing Timestamp Cutoff** | 15:30:00 IST | `src/config.py:CUTOFF` |
| **Event Day ($T$)** | If filing $\le$ 15:30 IST $\to$ Filing Day; If $>$ 15:30 IST $\to$ Next Trading Session | `src/timing.py`, `scripts/build_events.py` |
| **Entry Rule** | Strictly the **OPEN** of session $T+1$ (or $T+2$ if after-hours) | `px.Open.iloc[entry_idx]` |
| **Exit Rule** | Exactly **60 Trading Days** from entry session, at market Close ($T_{\text{entry}} + 60$) | `px.Close.iloc[exit_idx]` |
| **Holding Period** | 60 completed trading sessions (in stock's own calendar) | `holding_period=60` |
| **Maximum Capacity (Slots)** | **30 concurrent positions** | `max_slots=30` |
| **Position Sizing** | Equal-weight sleeve: $1 / N_{\text{slots}} = 1 / 30 = 3.333\%$ of portfolio equity per slot | `daily_sleeve_returns += (net_ret / max_slots) / len(w)` |
| **Queue / Ranking Policy** | **SUE-Rank Priority**: on days where eligible trades exceed open slots, higher SUE takes priority | `cands_df.groupby("entry_date").apply(sort by sue desc)` |
| **Cash Treatment** | Unallocated slots remain in cash earning 0.0% nominal return (cash drag) | Equal-weight sleeve arithmetic |
| **Transaction Cost** | **0.585% Round-Trip** deducted from every completed trade | `COST_BASE = 0.00585` |
| **Benchmark** | NIFTY 500 Index (daily close-to-close) | `cache/sector_close_panel.csv` |
| **Overlapping Positions** | Same stock can hold multiple slots if it files two consecutive quarters within 60 sessions | Modeled by unique trade ID |
| **Missing Prices** | If stock lacks price history at entry or exit, trade is dropped | `if exit_idx >= len(px): continue` |
| **Corporate Actions** | Daily OHLCV price series are split- and bonus-adjusted | Checked in price series |

---

## 2. Frozen Headline Claim to Audit

The target claim reported in `FINAL_PEAD_V2_REPORT.md` is:
- **Strategy CAGR:** **+17.73%**
- **Nifty 500 CAGR:** **+11.05%**
- **Excess CAGR:** **+6.68%**
- **Sharpe Ratio:** **8.48** (daily annualized)
- **Maximum Drawdown:** **-11.0%** (vs -18.8% for benchmark)
- **Win Rate:** **53.8%**
- **Trade Count:** **675 trades taken** (out of 1,244 eligible Q5 Non-Financial candidates)
- **Sample Window:** 2021-08-10 to 2026-08-17 (approx 5.0 years)

This exact configuration and set of claims will be independently audited.
