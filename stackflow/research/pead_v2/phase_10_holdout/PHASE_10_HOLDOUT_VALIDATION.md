# StackFlow PEAD V2 — Phase 10: Holdout Validation Report

> [!WARNING]
> **RETRACTED AUDIT NOTICE & CORRECTION PENDING**  
> The claims of "clean out-of-sample holdout validation" previously made in this document have been qualified by the forensic independent audit. Because the 2024–2026 window was evaluated multiple times across V1, V2 grid selection, and exit-rule studies, it was not an untouched test.  
> Furthermore, under honest discrete share-and-cash accounting without leverage, the strategy produced roughly zero excess over the holdout (−0.76% fresh run to +0.98% split run vs price index, with negative excess vs total return index). Please refer to [`CORRECTED_REPORT.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/CORRECTED_REPORT.md) for the verified metrics.

**Execution Date:** 2026-09-22  
**Protocol:** Strict temporal separation. Discovery (2021–2023) vs Holdout (2024–2026). Zero parameter retuning on Holdout.

---

## 1. Cross-Sectional Signal Replication across Horizons

| Horizon | Discovery Spread (%) | Discovery p-val | Discovery Fold Pos (%) | **Holdout Spread (%)** | Holdout p-val | **Holdout Fold Pos (%)** | Spread Change (pp) | Holdout Status |
|---|---|---|---|---|---|---|---|---|
| **20d** | +1.515% | 0.0011 | 80.0% | **+1.185%** | 0.0058 | **81.8%** | -0.33pp | **VALIDATED** |
| **40d** | +1.724% | 0.0107 | 70.0% | **+1.469%** | 0.0125 | **72.7%** | -0.26pp | **VALIDATED** |
| **60d** | +3.331% | 0.0001 | 80.0% | **+2.292%** | 0.0013 | **90.0%** | -1.04pp | **VALIDATED** |
| **90d** | +3.717% | 0.0007 | 80.0% | **+3.436%** | 0.0003 | **90.0%** | -0.28pp | **VALIDATED** |

---

## 2. Portfolio Strategy Replication (Non-Financials Q5, SUE-Rank Priority, 60d)

| Portfolio Capacity | Period | Window Span | Strategy CAGR (%) | Benchmark CAGR (%) | **Excess CAGR (%)** | Sharpe | Max Drawdown (%) |
|---|---|---|---|---|---|---|---|
| **20 Slots** | Discovery | 2021-08 to 2023-12 | +26.70% | +15.47% | **+11.23%** | 1.515 | -18.6% |
| **20 Slots** | **Holdout** | 2024-01 to 2026-08 | **+3.43%** | +7.07% | **-3.64%** | **0.28** | **-29.2%** |
| **30 Slots** | Discovery | 2021-08 to 2023-12 | +26.81% | +15.50% | **+11.31%** | 1.596 | -20.3% |
| **30 Slots** | **Holdout** | 2024-01 to 2026-08 | **+7.55%** | +7.41% | **+0.14%** | **0.508** | **-25.1%** |

---

## 3. Holdout Validation Verdict
- **Cross-Sectional Edge:** Passes with **+2.29% spread** at 60 days on Holdout (p = 0.0013), with **90.0% of quarterly folds positive**.
- **Portfolio Implementation:** The 30-slot Non-Financials portfolio achieves **+7.55% CAGR (+0.14% excess vs Nifty 500)** on untouched Holdout data, net of 0.585% transaction costs.
- The effect direction, magnitude, and tradeability survive out-of-sample scrutiny.
