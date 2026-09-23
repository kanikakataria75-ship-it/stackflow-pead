# StackFlow PEAD V2 — Corrected Live Trading Specification & Forward Protocol

**Configuration Version:** `2.1.0-AUDIT-CORRECTED`  
**Effective Date:** 2026-09-23  
**Status:** **FROZEN FOR FORWARD TEST (NOT VALIDATED)**  
**Audit Reference:** [`CORRECTED_REPORT.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/CORRECTED_REPORT.md)

---

## 1. Frozen Operational Parameters

| Parameter | Specification | Execution & Accounting Rule |
|---|---|---|
| **Universe** | NSE Equities with quarterly XBRL PAT | 20-day historical turnover $\ge$ INR 1 Crore, Entry Open $>$ INR 50. |
| **Sector Exclusion** | **Non-Financials (Industry Classification)** | Banks, NBFCs, Housing Finance, Insurance, AMCs, Exchanges, Rating Agencies excluded. |
| **Signal Metric** | **Standardized Unexpected Earnings (SUE)** | $SUE_t = \frac{\text{PAT}_t - \text{PAT}_{\text{prior\_year}}}{\sigma(\Delta \text{YoY PAT}_{t-8 \dots t-1})}$. Matched by **exact fiscal quarter date**, min 6 prior YoY differences. |
| **Ex-Ante Threshold** | **Model M1: Rolling 365 Days** | History $T-365 \le \text{filing} < T$; minimum 150 events; empirical 80th percentile ($q_{80}$). |
| **Signal Trigger** | **Top Quintile (Q5)** | $SUE \ge q_{80}$. |
| **Cutoff Timestamp** | **15:30:00 IST** | Exchange broadcast timestamp strictly verified. |
| **Event Day ($T$)** | Trading Session | Filing $\le$ 15:30 IST $\to$ Session $D$; Filing $>$ 15:30 IST $\to$ Next Trading Session $D+1$. Weekend/holiday filings after 15:30 IST assign $T = D_2$. |
| **Entry Session** | Next Session Open | Session $T+1$ (or $T+2$ if after-hours) **OPEN**. Announcement-day close never used. |
| **Exit Session** | **60 Trading Days** from Entry | Closed at session $T_{\text{entry}} + 60$ Market Close. |
| **Position Sizing** | **Discrete Share & Cash Accounting** | Sized at entry Open to $\min(\text{Available Cash}, \text{NAV}_{t-1} / 30)$. Held at cost; zero leverage. |
| **Capacity Cap** | **30 Concurrent Slots** | Maximum 30 active holdings. Slot freed for new entries strictly from next session's Open. |
| **Queue Policy** | **FIFO across dates, SUE tie-break** | FIFO across entry dates; same-day ties allocated to highest SUE magnitude. No cross-day displacement. |
| **Friction / Cost** | **0.585% Round-Trip** | $0.2925\%$ charged on entry Open, $0.2925\%$ charged on exit Close. |
| **Benchmark** | NIFTY 500 Index & Event Universe | NIFTY 500 Price Return index (with footnote on ~1.0-1.5% dividend yield) and Equal-Weight Event Universe Mean. |

---

## 2. Documented Strategy Limitations & Known Weaknesses

1. **Thin Time Span:**  
   High-quality standardized Indian XBRL data with exact timestamps is only available from 2021 onward (~5 years of history).
2. **Short-Side Edge Uncaptured:**  
   The cross-sectional PEAD signal draws strong alpha from the short side (Q1: $-1.5\%$ to $-2.0\%$ underperformance), which cannot be captured in a long-only cash equity portfolio.
3. **Decay in Market-Level Excess:**  
   While the signal consistently beats the event-universe average across discovery and holdout, the long-only strategy produced negligible excess over the NIFTY 500 Price Return index in 2024–2026 ($+0.82\%$ excess on holdout-signalled trades before dividend adjustment, per `CORRECTED_REPORT.md` revision 2; $\le 0\%$ after dividend yield).
4. **Institutional Capacity Ceiling:**  
   At a 1% volume participation cap (where 90% of trades execute within 1% ADV), capacity is **INR ~1.6 Crore** (scales to ~INR 8 Crore at 5% participation; CORRECTED_REPORT.md revision 2). Sizing above INR 15 Cr forces severe price impact across the lower-liquidity half of the portfolio.
5. **Benchmark Dividend Mismatch:**  
   Reported benchmark is NIFTY 500 Price Return. Excess returns over a Total Return Index (TRI) are ~1.0–1.5 pp/yr lower.

---

## 3. Pre-Registered Forward Test Protocol

* **Evaluation Standard:**  
  Realized daily mark-to-market NAV using discrete share and cash accounting, evaluated against NIFTY 500 and the equal-weight event universe mean.
* **Minimum Forward Horizon:**  
  At least **4 to 6 earnings seasons** (minimum 12–18 calendar months of live forward records).
* **Explicit Kill Criteria:**  
  The strategy will be permanently killed if:
  1. Cumulative strategy return trails NIFTY 500 over 4 consecutive earnings seasons ($\text{Excess} \le 0\%$).
  2. Average Q5 net trade return trails the cross-sectional event-universe average ($\text{Excess vs Event Universe} \le 0\%$).
  3. Realized portfolio drawdown exceeds $-25.0\%$.

---

## 4. Forward Record Entry Schema

Each candidate trade taken or skipped must be recorded in [`forward_record_pead_v2.csv`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/forward_record_pead_v2.csv) with the following 20 schema columns:
```csv
signal_id,symbol,period_end,filing_timestamp,event_day,sue_value,rolling_q80_threshold,is_taken,skip_reason,entry_date,entry_price,exit_date,exit_price,holding_sessions,gross_return,net_return,cost_deducted,nifty500_excess_return,univ_excess_return,status
```
