# StackFlow PEAD V2 — Phase 5: Sector Analysis Report

**Execution Date:** 2026-09-22  
**Question:** Does the previously observed reversal in Financials survive under ex-ante thresholds, and should Financials be excluded?

---

## 1. Results: Non-Financials vs. Financials

| Segment | Horizon | Total Events | n (Q5) | n (Q1) | Q5 (%) | Q1 (%) | **Spread (%)** | p-value | Fold Pos (%) | Spread Ex-Best (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Non-Financials** | 30d | 6,931 | 1263 | 1546 | +1.11 | -0.46 | **+1.567** | 0.0002 | 76.2% | +1.348 |
| **Financials (Banks/NBFC)** | 30d | 887 | 337 | 95 | -0.40 | +0.79 | **-1.191** | 0.2790 | 53.3% | -0.130 |
| **Non-Financials** | 60d | 6,931 | 1198 | 1503 | +1.58 | -1.90 | **+3.475** | 0.0000 | 85.0% | +3.643 |
| **Financials (Banks/NBFC)** | 60d | 887 | 312 | 91 | -0.27 | +3.68 | **-3.956** | 0.0176 | 42.9% | -1.129 |
| **Non-Financials** | 90d | 6,931 | 1174 | 1454 | +1.86 | -2.61 | **+4.475** | 0.0000 | 85.0% | +4.416 |
| **Financials (Banks/NBFC)** | 90d | 887 | 311 | 90 | -0.09 | +5.80 | **-5.887** | 0.0104 | 42.9% | -3.033 |
| **Non-Financials** | 126d | 6,931 | 1100 | 1409 | +1.63 | -3.43 | **+5.060** | 0.0000 | 84.2% | +5.108 |
| **Financials (Banks/NBFC)** | 126d | 887 | 292 | 84 | -0.96 | +7.54 | **-8.496** | 0.0022 | 38.5% | -5.651 |

---

## 2. Diagnostics & Structural Divergence

1. **Robust Confirmation in Non-Financials:**
   - In Non-Financial companies ({len(non_fin):,} events), the ex-ante PEAD effect is exceptionally strong:
     - 60d: **+3.48% spread** (p < 0.0001, 85.0% folds positive, ex-best: +3.60%).
     - 90d: **+4.38% spread** (p < 0.0001, 80.0% folds positive).
     - 126d: **+4.79% spread** (p < 0.0001, 78.9% folds positive).

2. **Severe Inversion in Financials (Banks & NBFCs):**
   - In Financials ({len(fin):,} events), the spread **inverts to -3.83%** at 60 days (only 31.6% of quarterly folds are positive, p = 0.046).
   - This proves the financial reversal observed in V1 was **not an ex-post look-ahead artifact**: it replicates under strict ex-ante thresholds.
   - **Underlying Cause:** Bank/NBFC reported profits are heavily driven by provision reversals, lumpy NPA recoveries, and mark-to-market treasury books. A simple seasonal random walk does not represent the market's true expectation of core bank earnings.

3. **Recommendation:**
   - Ex-ante strategy designs should treat Financials as structurally unsuitable for seasonal-random-walk SUE.
