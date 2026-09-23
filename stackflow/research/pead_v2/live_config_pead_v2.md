# StackFlow PEAD V2 — Frozen Live Strategy Configuration

**Configuration Date:** 2026-09-22  
**Status:** **FROZEN & LOCKED FOR FORWARD MONITORING**  
**Evidence Level:** **Signal confirmed; strategy is a forward-test candidate.**  
**No-Backfill Rule:** Hard code rule. Any event dated on or before 2026-09-22 is backtest data and CANNOT be entered into the forward record.

---

## 1. Core Specification

| Parameter | Frozen Specification | Rule / Rationale |
|---|---|---|
| **Universe** | NSE Listed Equities with quarterly XBRL PAT | 20-day historical turnover $\ge$ INR 1 Crore, Price $>$ INR 50. |
| **Sector Filter** | **Non-Financials Only** | Banks, NBFCs, and insurance excluded (`is_fin == False`) due to structural provision lumpiness. |
| **Signal Metric** | **Standardized Unexpected Earnings (SUE)** | $SUE_t = \frac{\text{PAT}_t - \text{PAT}_{t-4}}{\sigma(\Delta \text{YoY PAT}_{t-8 \dots t-1})}$. Minimum 6 prior YoY differences required. |
| **Ex-Ante Threshold** | **Model M1: Rolling 365 Days** | Quintile cuts determined exclusively from qualifying events in trailing 365 days prior to event day. |
| **Signal Trigger** | **Top Quintile (Q5)** | $SUE \ge q_{80}$ historical rolling threshold. |
| **Filing Timestamp** | Exchange Broadcast Timestamp | 100% point-in-time verified. |
| **Event Day** | Session $T$ | Filing $\le$ 15:30 IST $\to$ Day $T$; Filing $>$ 15:30 IST $\to$ Next Trading Day. |
| **Entry Session** | Session $T+1$ (or $T+2$) **OPEN** | Next trading day Open price. Never announcement-day close. |
| **Exit Session** | **60 Trading Days** from Entry | Closed at session $T_{\text{entry}} + 60$ Market Close. |
| **Position Sizing** | Equal Weight Sleeve | $1 / N_{\text{slots}} = 1 / 30 = 3.333\%$ of initial sleeve equity. |
| **Max Capacity** | **30 Concurrent Slots** | SUE-Rank Priority queue if candidates exceed available slots on any day. |
| **Transaction Cost** | **0.585% Round-Trip** | Standard NSE LeadFlow cost model deducted from every realized trade. |
| **Benchmark** | NIFTY 500 Index | Loaded daily from official NSE index provider. |

---

## 2. Forward Record Schema

All forward live tracking must populate `forward_record_pead_v2.csv` with the following columns:

```text
signal_id,symbol,period_end,filing_timestamp,event_day,sue_value,rolling_q80_threshold,is_taken,skip_reason,entry_date,entry_price,exit_date,exit_price,holding_sessions,gross_return,net_return,cost_deducted,nifty500_excess_return,status
```

### Queue Rejection Codes:
- `FULL_QUEUE`: All 30 slots occupied.
- `LOWER_SUE_RANK`: More candidates arrived than available slots; candidate had lower SUE than chosen entrants.
- `FINANCIAL_SECTOR`: Bank or NBFC filing excluded by sector rule.
- `LIQUIDITY_FILTER`: 20-day turnover $<$ INR 1 Cr or Price $\le$ INR 50.
