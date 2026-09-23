# StackFlow PEAD V2 Audit — Document 02: Research Timeline Reconstruction

> [!WARNING]
> **RETRACTED AUDIT NOTICE & CORRECTION PENDING**  
> The headline figures previously referenced in this timeline (+17.73% CAGR, Sharpe 7.55–11.97, −11.0% Max DD, ₹15–40 Cr capacity) were artifacts of linear return smoothing, same-day slot-recycling leverage, and unadjusted price index benchmark mismatch.  
> Following the forensic independent audit, these claims have been permanently retracted. Please refer to [`CORRECTED_REPORT.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/CORRECTED_REPORT.md) for the verified, reproducible, cash-accounted metrics (revision 2; regenerate with `scripts/build_corrected_dataset.py` + `scripts/run_corrected_strategy.py`).

**Audit Date:** 2026-09-22  
**Purpose:** Reconstruct the exact chronological history of how PEAD was conceived, tested in V1, evolved into V2, and how each strategy parameter was decided.

---

## 1. Timeline of Milestones & Repository Events

| Step | Timestamp (Local) | File / Artifact | Event & Decision | Classification |
|---|---|---|---|---|
| **1** | 2026-09-21 04:15 | `RESULTS_layer1.md` | Layer 1 (Sector Momentum) evaluated. Decayed after ~2015. | PRE-REGISTERED |
| **2** | 2026-09-21 15:59 | `layer2/results/RESULTS_h2.md` | Layer 2 (Stock-level momentum inside sectors) rejected. | PRE-REGISTERED |
| **3** | 2026-09-21 16:27 | `layer3/results/RESULTS_h3.md` | Layer 3 (Fundamentals as filter) rejected. | PRE-REGISTERED |
| **4** | 2026-09-22 15:14 | `layer4/results/RESULTS_layer4.md` | Layer 4 (Concall tone): Text mood had zero alpha ($p=0.977$), but earnings surprise control was significant ($\beta=0.0045, p=0.048$) on 203 events. **PEAD idea born here.** | **DISCOVERED DURING RESEARCH** |
| **5** | 2026-09-22 16:00 | `pead/pre_registration.md` | V1 Pre-Registration frozen: SUE seasonal random walk, 6 criteria, 15-slot FIFO book. | PRE-REGISTERED |
| **6** | 2026-09-22 16:09 | `pead/results/RESULTS_pead.md` | V1 Results: Primary cell confirmed (+2.50% spread), but tradeability fails (+8.38% vs +10.91% Nifty 500). Diagnostics reveal: Financials reverse (-4.85%), early filers clog 15 slots, small caps dominate. | **DISCOVERED DURING RESEARCH** |
| **7** | 2026-09-22 17:34 | User Request | User notes V1 results and prompts V2 investigation. | EXTERNAL TRIGGER |
| **8** | 2026-09-22 18:41 | Implementation Plan | Methodological flaw identified: V1 quintiles used quarterly `pd.qcut` (an ex-post look-ahead across the quarter). | **DISCOVERED DURING RESEARCH** |
| **9** | 2026-09-22 18:42 | `research/pead_v2/PRE_REGISTRATION.md` | PEAD V2 Pre-Registration written: specifies rolling 365d historical threshold, pre-registers grid (10/20/30 slots, 20/40/60/90d, FIFO vs SUE_RANK, All vs Non-Fin). | PRE-REGISTERED (GRID LEVEL) |
| **10** | 2026-09-22 18:46 | `phase_02_ex_ante/` | Phase 2 Ex-Ante run: 60d spread confirmed at +2.77% (clean point-in-time). | CONFIRMATORY |
| **11** | 2026-09-22 18:47 | `phase_04_size/` & `phase_05_sector/` | Size & Sector diagnostics confirm small cap superiority (+3.94%) and financial reversal (-3.96%). | CONFIRMATORY DIAGNOSTIC |
| **12** | 2026-09-22 18:48 | `phase_06_filing_timing/` | Filing timing proves early filers (+0.48%) clogged FIFO queue; late filers (+3.84%) skipped. | CONFIRMATORY DIAGNOSTIC |
| **13** | 2026-09-22 18:49 | `phase_08_backtest/` | 96-cell portfolio grid run. 30-slot Non-Financials SUE_RANK 60d produces +17.73% CAGR. | **POST-HOC SELECTION** |
| **14** | 2026-09-22 18:51 | `live_config_pead_v2.md` | Specific combination (30-slot, Non-Fin, SUE_RANK, 60d) frozen as the live strategy. | **POST-HOC SELECTION** |
| **15** | 2026-09-22 18:53 | `FINAL_PEAD_V2_REPORT.md` | Final report written declaring strategy "VALIDATED TRADING STRATEGY". | CONCLUSION |

---

## 2. Decisive Audit Finding on Research Discipline

There is a vital distinction between the **Signal** and the **Trading Strategy**:
1. **The Cross-Sectional Signal (+2.77% spread):**  
   Strictly **PRE-REGISTERED & CONFIRMATORY**. The rolling historical threshold methodology was locked in `PRE_REGISTRATION.md` before generating Phase 2 returns. The signal passed all 6 pre-registered criteria on both discovery and holdout.
2. **The Portfolio Strategy (+17.73% CAGR):**  
   **PARTIALLY POST-HOC**. While the parameter grid (10, 20, 30 slots; FIFO vs SUE_RANK; All vs Non-Fin) was formally specified in `PRE_REGISTRATION.md` and `PHASE_07_PORTFOLIO_SPEC.md`, the decision to crown the **30-slot Non-Financials SUE-Rank 60d** configuration as the single "Validated Trading Strategy" occurred **after seeing that it achieved the highest CAGR across the 96 tested cells**.
