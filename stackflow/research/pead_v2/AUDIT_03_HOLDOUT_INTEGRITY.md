# StackFlow PEAD V2 Audit — Document 03: Holdout Integrity & Overfitting Audit

> [!WARNING]
> **RETRACTED AUDIT NOTICE & CORRECTION PENDING**  
> The headline figures previously referenced in this document (+17.73% CAGR, Sharpe 7.55–11.97, −11.0% Max DD, ₹15–40 Cr capacity) were artifacts of linear return smoothing, same-day slot-recycling leverage, and unadjusted price index benchmark mismatch.  
> Following the forensic independent audit, these claims have been permanently retracted. Please refer to [`CORRECTED_REPORT.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/CORRECTED_REPORT.md) for the verified, reproducible, cash-accounted metrics (revision 2; regenerate with `scripts/build_corrected_dataset.py` + `scripts/run_corrected_strategy.py`).

**Audit Date:** 2026-09-22  
**Purpose:** Forensic assessment of researcher degrees of freedom, parameter selection timing, and whether 2024–2026 holdout data contaminated final strategy choices.

---

## 1. Parameter Selection & Overfitting Audit Table

| Parameter | Final Value in Live Config | Alternatives Tested | Was Final Value Selected After Seeing Results? | Evidence & Impact on Validity | Holdout Contamination Status |
|---|---|---|---|---|---|
| **SUE Mathematical Formula** | Seasonal random walk (prior 8 quarters YoY $\Delta$, min 6) | None (kept identical to V1) | **NO** | Fixed before any V1 or V2 return was joined. Pre-registered in `pead/pre_registration.md` (16:00) and `research/pead_v2/PRE_REGISTRATION.md` (18:42). | **CLEAN** |
| **Ex-Ante Threshold Lookback** | Model M1: Rolling 365 Calendar Days | M2: 730d (8Q), M3: Expanding | **NO** (Pre-designated baseline) | M1 was pre-designated as primary cell in `PRE_REGISTRATION.md` (§3.3) before computing Phase 2 returns. (Note: M2 and M3 yielded similar spreads: +2.91% and +2.89%). | **CLEAN** |
| **Filing Timestamp Cutoff & Entry** | 15:30 IST; Next-Day Open Entry | None (locked rule) | **NO** | Standard locked rule from Layer 1/4 and V1. Prevents same-day leakage. | **CLEAN** |
| **Holding Horizon** | 60 Trading Days | 20d, 40d, 90d | **PARTIALLY** | 60d was the primary horizon from V1 pre-registration. However, Phase 8 grid evaluated 20d, 40d, 60d, 90d. 60d was retained because it showed the strongest excess CAGR (+6.68%). | **BORDERLINE / INFORMED BY V1** |
| **Financial Sector Exclusion** | Non-Financials Only (`is_fin == False`) | All Sectors (Full Universe) | **YES** | The inversion in financials (-4.85%) was discovered in V1 diagnostics. Excluding them in V2 was motivated by V1 results. Although pre-registered as a grid variant, selecting Non-Financials as the *sole live strategy* was informed by seeing that All Sectors underperformed. | **HOLD OUT CONTAMINATED (SECTOR)** |
| **Position Capacity (Slots)** | 30 Concurrent Slots | 10 slots, 20 slots | **YES** | 10, 20, 30 slots were pre-registered in the Phase 7 grid. However, 30 slots was selected for `live_config_pead_v2.md` **after** Phase 8 results showed that 30 slots gave the highest CAGR (+17.73% vs +17.02% for 10 slots and +15.15% for 20 slots). | **HOLDOUT CONTAMINATED (CAPACITY)** |
| **Queueing Policy** | SUE-Rank Priority | FIFO (First-Come) | **YES** | SUE-rank priority was conceived in response to V1's FIFO bottleneck. Selecting SUE-rank for the live config was finalized after seeing it outperformed FIFO in Phase 8 (+17.73% vs +12.38%). | **HOLDOUT CONTAMINATED (QUEUE)** |
| **Transaction Cost** | 0.585% Round-Trip | 0.300%, 1.000% | **NO** | 0.585% was the pre-existing NSE LeadFlow standard fixed before testing. | **CLEAN** |

---

## 2. Holdout Period Visibility Timeline

- **Definition:**
  - **Discovery Period:** Events occurring on or before 2023-12-31.
  - **Holdout Period:** Events occurring from 2024-01-01 to 2026-08-17.
- **The Core Violation:**
  When `run_phase8_portfolio.py` executed its 96 backtests, the simulation span for every run was **the entire dataset (2021-08-10 to 2026-08-17)**.
  - The CAGR of +17.73% was calculated over the *combined* 2021–2026 period.
  - Therefore, the choice of the 30-slot, SUE-rank, Non-Financials configuration for `live_config_pead_v2.md` was informed by data spanning both Discovery AND Holdout.
  - The Holdout period was **NOT kept in a sealed vault** during strategy parameter selection; it was part of the optimization surface of Phase 8!

---

## 3. What Does and Does Not Survive This Contamination?

1. **The Signal Itself is NOT Contaminated:**
   - In Phase 10 (`PHASE_10_HOLDOUT_VALIDATION.md`), the cross-sectional 60d spread on Holdout was evaluated at **+2.29%** ($p = 0.0013$) using the rolling 365-day threshold model locked beforehand.
   - The existence of the post-earnings drift anomaly in 2024–2026 is an independent, un-manipulated fact.
2. **The Portfolio Strategy Selection IS Contaminated:**
   - The headline claim "+17.73% CAGR validated strategy" must be downgraded to:
     > **"An in-sample parameter fit across a 96-cell grid on 2021–2026 data."**
   - When the 30-slot strategy is evaluated strictly on the Holdout period alone (as shown in Phase 10), its CAGR drops from +28.6% (Discovery) to **+7.68% (Holdout)**, which is essentially in line with Nifty 500 (+7.40% over that specific window, excess +0.28%).
   - The strategy does **NOT** achieve +17.73% out-of-sample; that number is the blended in-sample result of the chosen best cell.
