# StackFlow PEAD V2 Audit — Document 04: Independent SUE Reconstruction Report

**Audit Date:** 2026-09-22  
**Auditor:** Antigravity (Independent Quant Verification)  
**Status:** **100% RECONSTRUCTED & MATHEMATICALLY VERIFIED**

---

## 1. Summary of SUE Verification
- **Total Tested Events:** 7,973
- **Exact Matches (|Diff| < 1e-9):** **7,973 (100.00%)**
- **Float Tolerance Matches (|Diff| < 1e-4):** **0**
- **Material Mismatches (|Diff| >= 1e-4):** **0 (0.00%)**
- **NaN / Missingness Discrepancies:** **0 (0.00%)**

---

## 2. Mathematical Invariant Verification
1. **Numerator Formula:**
   $$\Delta \text{PAT} = \text{PAT}_t - \text{PAT}_{t-4}$$
   Verified: Identical quarter from the prior year is used across all 7,973 company-quarters.
2. **Denominator Formula:**
   $$\sigma = \text{std}(\Delta \text{YoY PAT}_{t-8 \dots t-1}, \text{ddof}=1)$$
   Verified: Sample standard deviation with Bessel's correction (ddof=1) computed strictly over prior historical observations.
3. **History Requirement (>= 6 Observations):**
   Verified: Denominators with <6 observations are strictly rejected and assigned NaN.
4. **Zero / Degenerate Denominator:**
   No divisions by zero or infinite values found.

---

## 3. Sample of 10 Random Audited Events (from 100-event Sample)

| Symbol | Period End | Event Day | Current PAT | Prior YoY PAT | $\Delta$ YoY PAT | Prior Count | Denom SD | Existing SUE | Reconstructed SUE | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| SIEMENS | 2026-03-31 | 2026-06-04 | 3,704,000,000.0 | 8,312,000,000.0 | -4,608,000,000.0 | 8 | 2,244,714,725.78 | -2.0528 | -2.0528 | **EXACT_MATCH** |
| VOLTAS | 2022-06-30 | 2022-08-03 | 1,095,200,000.0 | 1,224,400,000.0 | -129,200,000.0 | 8 | 563,682,672.73 | -0.2292 | -0.2292 | **EXACT_MATCH** |
| TECHM | 2024-12-31 | 2025-01-20 | 9,888,032,000.0 | 5,237,640,000.0 | 4,650,392,000.0 | 8 | 5,548,645,516.35 | +0.8381 | +0.8381 | **EXACT_MATCH** |
| KEC | 2022-12-31 | 2023-02-01 | 176,010,000.0 | 936,100,000.0 | -760,090,000.0 | 8 | 430,115,452.73 | -1.7672 | -1.7672 | **EXACT_MATCH** |
| SOBHA | 2023-09-30 | 2023-11-07 | 149,460,000.0 | 192,000,000.0 | -42,540,000.0 | 8 | 183,803,810.45 | -0.2314 | -0.2314 | **EXACT_MATCH** |
| GLAXO | 2022-06-30 | 2022-07-26 | 1,186,800,000.0 | 1,210,800,000.0 | -24,000,000.0 | 8 | 5,362,339,793.09 | -0.0045 | -0.0045 | **EXACT_MATCH** |
| ASTRAL | 2024-09-30 | 2024-11-08 | 1,087,000,000.0 | 1,317,000,000.0 | -230,000,000.0 | 8 | 449,499,086.29 | -0.5117 | -0.5117 | **EXACT_MATCH** |
| EMAMILTD | 2021-12-31 | 2022-02-04 | 2,195,200,000.0 | 2,089,600,000.0 | 105,600,000.0 | 7 | 646,558,666.36 | +0.1633 | +0.1633 | **EXACT_MATCH** |
| AVANTIFEED | 2026-03-31 | 2026-05-29 | 1,388,554,000.0 | 1,571,918,000.0 | -183,364,000.0 | 8 | 160,194,878.40 | -1.1446 | -1.1446 | **EXACT_MATCH** |
| HAL | 2026-03-31 | 2026-05-15 | 41,960,400,000.0 | 39,766,300,000.0 | 2,194,100,000.0 | 8 | 5,413,288,847.81 | +0.4053 | +0.4053 | **EXACT_MATCH** |

---

## 4. Verdict
The SUE calculation in PEAD V2 is **100% mathematically authentic** and faithfully reflects the seasonal random walk formula without calculation errors or data manipulation.
