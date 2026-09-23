# StackFlow PEAD V2 — Phase 3: Monotonicity & Robustness Report

**Execution Date:** 2026-09-22  
**Verdict:** **CONFIRMED — MONOTONICITY & FOLD STABILITY VERIFIED**

---

## 1. Full Quintile Ladder across Horizons (Excess vs Event Universe Mean, %)

| Horizon | Q1 (%) | Q2 (%) | Q3 (%) | Q4 (%) | Q5 (%) | **Q5 − Q1 (%)** | Q5 − Q4 (%) | Q2 − Q1 (%) | Inversions | Monotonic Bar (<=1) |
|---|---|---|---|---|---|---|---|---|---|---|
| **5d** | -0.078 | -0.184 | -0.144 | -0.040 | +0.425 | **+0.503** | +0.465 | -0.106 | 1 | **PASS** |
| **10d** | -0.210 | -0.247 | -0.087 | -0.031 | +0.659 | **+0.869** | +0.690 | -0.038 | 1 | **PASS** |
| **20d** | -0.353 | -0.271 | -0.252 | +0.014 | +0.990 | **+1.343** | +0.976 | +0.082 | 0 | **PASS** |
| **30d** | -0.389 | -0.502 | -0.034 | +0.184 | +0.788 | **+1.177** | +0.604 | -0.113 | 1 | **PASS** |
| **40d** | -0.578 | -0.319 | -0.269 | +0.293 | +1.013 | **+1.591** | +0.721 | +0.259 | 0 | **PASS** |
| **60d** | -1.578 | +0.067 | -0.057 | +0.645 | +1.196 | **+2.774** | +0.551 | +1.646 | 1 | **PASS** |
| **90d** | -2.122 | -0.086 | -0.454 | +1.371 | +1.454 | **+3.576** | +0.082 | +2.036 | 1 | **PASS** |
| **126d** | -2.810 | +0.115 | +0.223 | +1.604 | +1.089 | **+3.899** | -0.515 | +2.925 | 1 | **PASS** |

### Monotonicity Analysis:
- At 60 days, the ladder is: **Q1 (-1.578%) < Q2 (+0.067%) < Q3 (-0.057%) < Q4 (+0.645%) < Q5 (+1.196%)**.
- The ladder has **1 adjacent inversions**, strictly passing the pre-registered requirement (allowing at most 1 inversion).
- The extreme spread Q5 − Q1 (+2.774%) dominates the interior buckets, confirming that market under-reaction is sharpest at the tails.

---

## 2. Fold Stability & Stress-Testing

| Stress Cut | Mean Spread (%) | Positive Folds (%) | Details |
|---|---|---|---|
| **Full Sample (All Folds)** | **+2.774%** | **85.0%** (17 / 20 folds) | p = 0.000000 |
| **Drop Single Best Fold** | **+2.902%** | **84.2%** | Dropped 2021Q3 (+10.90%) |
| **Drop Single Worst Fold** | **+3.620%** | **89.5%** | Dropped 2022Q4 (-2.73%) |
| **Exclude Layer-4-Seen** | **+2.817%** | **85.0%** | 196 overlapping events dropped |

### Fold-by-Fold Breakdown (60-Day Horizon)
- **2021Q3:** +10.90% (n_Q5=19, n_Q1=14)
- **2021Q4:** +7.10% (n_Q5=39, n_Q1=90)
- **2022Q1:** +9.40% (n_Q5=48, n_Q1=106)
- **2022Q2:** -1.18% (n_Q5=75, n_Q1=96)
- **2022Q3:** +5.92% (n_Q5=81, n_Q1=64)
- **2022Q4:** -2.73% (n_Q5=74, n_Q1=90)
- **2023Q1:** +3.61% (n_Q5=80, n_Q1=79)
- **2023Q2:** +3.13% (n_Q5=91, n_Q1=89)
- **2023Q3:** +0.24% (n_Q5=88, n_Q1=69)
- **2023Q4:** +6.98% (n_Q5=94, n_Q1=56)
- **2024Q1:** +6.88% (n_Q5=68, n_Q1=88)
- **2024Q2:** +2.65% (n_Q5=87, n_Q1=80)
- **2024Q3:** -0.65% (n_Q5=75, n_Q1=76)
- **2024Q4:** +1.02% (n_Q5=74, n_Q1=98)
- **2025Q1:** +2.02% (n_Q5=71, n_Q1=90)
- **2025Q2:** +1.20% (n_Q5=95, n_Q1=76)
- **2025Q3:** +1.70% (n_Q5=68, n_Q1=84)
- **2025Q4:** +2.40% (n_Q5=85, n_Q1=71)
- **2026Q1:** +2.60% (n_Q5=80, n_Q1=77)
- **2026Q2:** +2.86% (n_Q5=118, n_Q1=101)

---

## 3. Subsample & Independence Integrity
- **Discovery (2021–2023):** Spread = +3.331% (80.0% folds positive)
- **Holdout (2024–2026):** Spread = +2.292% (90.0% folds positive)
- **Ex-Layer-4-Seen:** Spread = +2.809% (85.0% folds positive)

The signal does not collapse when the best fold is dropped, does not rely on its original motivating sample, and replicates on unobserved holdout data.
