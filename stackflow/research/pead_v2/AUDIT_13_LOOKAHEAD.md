# AUDIT 13: Look-Ahead and Information Flow Audit

**Audit Date:** 2026-09-22  
**Scope:** Static Code Audit and Data Pipeline Information Flow Inspection  
**Files Audited:** `src/sue_engine.py`, `src/portfolio_engine.py`, `src/data_loader.py`, `scripts/build_v2_dataset.py`, `scripts/audit_ex_ante_thresholds.py`  
**Status:** **PASSED (Zero Future Leakage in V2 Ex-Ante Specification)**

---

## 1. Information Flow Architecture

```
[Raw XBRL Filing Timestamp (ts)]
           │
           ▼
    [15:30 IST Cutoff Filter]
     ├── If ts <= 15:30: Event Day T = Filing Day
     └── If ts > 15:30:  Event Day T = Next Trading Day
           │
           ▼
 [Point-in-Time SUE Calculation]
  (PAT_t - PAT_{t-4}) / SD(Prior 8 YoY Changes strictly < T)
           │
           ▼
[Rolling Ex-Ante Quintile Cutoffs]
  Percentiles computed strictly from [T - 365d, T)
  (Hard assertion: max(Hist_Dates) < T verified on 7,818 events)
           │
           ▼
[Trade Entry Execution]
  Executed at OPEN of T+1 (or T+2 for post-15:30 filings)
  (Filing day intraday price jump is 100% excluded)
           │
           ▼
[60-Day Holding Window]
  Close-to-Close daily revaluation from Entry to Exit
  (Zero future prices accessed prior to respective trading days)
```

---

## 2. Forensic Code Inspection Findings

| Component | Code Inspection Target | Finding | Risk Level |
|---|---|---|:---:|
| **Pandas Shift Operations** | Search for `.shift(-...)` in signal generation | **Zero instances found** in strategy or signal scripts. | **NONE** |
| **Quantile Assignment** | Groupby calendar quarter (V1 flaw) vs. Rolling ex-ante (V2) | V1 contained look-ahead (`groupby('qtr')`). **V2 uses strictly causal rolling window `dates_dt < t_cur`**. | **RESOLVED** |
| **Price Execution Timing** | Entry price indexing | Always uses `Open` of session following event day close. Announcement-day jump excluded. | **NONE** |
| **SUE Standardization** | Denominator historical lookback | Uses `yoy[max(0, i-8):i]` strictly before index $i$. No concurrent quarter in denominator. | **NONE** |
| **Merge / Join Duplications** | Event table joins | Validated 1-to-1 cardinality. Zero row multiplication. | **NONE** |
| **Benchmark Synchronization** | Matching entry and exit index | Aligned on exact trading calendar without forward offsets. | **NONE** |

---

## 3. Comparison of V1 Flaw vs. V2 Resolution

1. **The V1 Look-Ahead Flaw:**
   - In PEAD V1, `assign_v1_quarterly_quintiles()` grouped all filings by calendar quarter `qtr` (e.g., `2023Q2`) and applied `pd.qcut()`.
   - A company filing on July 15 had its quintile threshold determined partly by earnings filed in late August.
2. **The V2 Ex-Ante Fix:**
   - In PEAD V2 (`src/sue_engine.py`), `assign_ex_ante_quintiles_rolling()` constructs thresholds exclusively using historical events filed in the preceding 365 calendar days ($[T - 365, T)$).
   - In `AUDIT_05_POINT_IN_TIME.csv`, 7,818 events were tested with the hard assertion:
     $$\max(\text{Historical Timestamps Used}) < \text{Event Timestamp}$$
   - **0 violations** were detected across all 7,818 events.

**Conclusion:** PEAD V2 is entirely free from forward-looking information leakage in its signal, thresholding, and execution pipelines.
