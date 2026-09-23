# StackFlow PEAD V2 Audit — Document 19: Discovery Timeline Analysis

**Audit Date:** 2026-09-22  
**Purpose:** Precise accounting of when each empirical phenomenon was first observed vs when decisions were made.

---

## 1. Chronological Discovery & Decision Matrix

| Date / Time (IST) | Discovery / Observation | Information Available | Decision Made | Classification |
|---|---|---|---|---|
| **2026-09-22 15:14** | **PEAD first discovered** in Layer 4 surprise control regression ($\beta=0.0045, p=0.048$ on 203 events). | 203 company-quarter events (2021+). Concall tone flat; accounting surprise positive. | Formulate dedicated PEAD project. Pre-register test on full universe. | **DISCOVERED DURING RESEARCH** |
| **2026-09-22 16:00** | V1 Pre-Registration drafted. | Known: 203 events had positive beta. Unknown: full-universe returns. | Lock SUE formula, 6 criteria, 15-slot FIFO book, 0.585% cost. | **PRE-REGISTERED** |
| **2026-09-22 16:09** | **+2.50% V1 result known.** | Full run of 7,973 events. Primary cell confirmed (+2.50% spread, $p < 0.0001$). | Note that cross-sectional signal cleared bar. | **CONFIRMED FINDING** |
| **2026-09-22 16:09** | **Financials identified as problematic.** | Diagnostic cut showed Banks/NBFCs had -4.85% spread (31% positive folds). | Flagged as diagnostic finding; did NOT drop from V1 primary cell. | **DISCOVERED DURING RESEARCH** |
| **2026-09-22 16:09** | **Size effect identified.** | Diagnostic cut showed small caps +3.61% vs large caps +1.07%. | Documented in `RESULTS_pead.md`. | **DISCOVERED DURING RESEARCH** |
| **2026-09-22 16:09** | **FIFO failure identified.** | 15-slot book generated +8.38% CAGR vs Nifty 500 +10.91%. | V1 tradeability officially REJECTED. | **DISCOVERED DURING RESEARCH** |
| **2026-09-22 16:09** | **Filing timing identified.** | FIFO book took trades with median 23 days from QE vs 39 days for skipped. | Diagnosed as early-filer adverse selection. | **DISCOVERED DURING RESEARCH** |
| **2026-09-22 18:41** | **Ex-ante threshold issue identified.** | Code inspection revealed `ev.groupby("qtr").apply(qcut)` used full-quarter events. | Reject V1 quintiling as ex-post; mandate rolling historical thresholds for V2. | **METHODOLOGICAL AUDIT** |
| **2026-09-22 18:42** | V2 Pre-Registration written. | Full dataset already seen in V1. Ex-ante returns NOT yet computed. | Pre-register Model M1 (365d rolling), pre-register grid (10/20/30 slots, 20/40/60/90d, FIFO vs SUE_RANK, All vs Non-Fin). | **PRE-REGISTERED (GRID LEVEL)** |
| **2026-09-22 18:46** | Ex-ante signal evaluated. | 7,818 events with rolling 365d cuts. | 60d spread confirmed at +2.77% ($p = 3.88 \times 10^{-7}$). | **CONFIRMATORY SIGNAL** |
| **2026-09-22 18:49** | **17.73% CAGR first observed.** | 96-cell portfolio grid completed. Cell (Non-Fin, 30 slots, SUE_RANK, 60d) produced +17.73% CAGR. | Cell observed as highest CAGR in grid. | **GRID EXPLORATION** |
| **2026-09-22 18:51** | **30-slot & SUE-rank chosen as Strategy.** | All 96 grid cells visible. | Freeze (Non-Fin, 30 slots, SUE_RANK, 60d) into `live_config_pead_v2.md`. | **POST-HOC SELECTION** |

---

## 2. Definitive Summary
- **The Signal (+2.77% spread):** Born from Layer 4, pre-registered in V1, audited for look-ahead in V2, pre-registered with rolling thresholds, and confirmed on out-of-sample holdout data. **Genuine finding.**
- **The Portfolio Strategy (+17.73% CAGR):** Born from diagnosing why V1 failed (financials, early filers, tight capacity). While tested within a pre-registered grid, the exact winning configuration was designated as the strategy **after viewing all 96 portfolio backtest outcomes**. It must be evaluated as an in-sample optimized execution of a real underlying signal.
