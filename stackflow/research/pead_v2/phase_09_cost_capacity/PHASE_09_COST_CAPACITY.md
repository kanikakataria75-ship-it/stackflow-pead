# StackFlow PEAD V2 — Phase 9: Cost & Capacity Stress Report

> [!WARNING]
> **RETRACTED AUDIT NOTICE & CORRECTION PENDING**  
> The headline figures previously referenced in earlier versions of this document (+17.73% CAGR, Sharpe 7.55, −11.5% Max DD, ₹15–40 Cr capacity) were artifacts of linear return smoothing, capacity indexing bugs, and unadjusted price index benchmark mismatch.  
> Following the forensic independent audit, these claims have been permanently retracted. Please refer to [`CORRECTED_REPORT.md`](file:///c:/Users/kanik/Desktop/STACKFLOW%20ANTIGRAVITY/stackflow/research/pead_v2/CORRECTED_REPORT.md) for the verified, reproducible, cash-accounted metrics (revision 2; regenerate with `scripts/build_corrected_dataset.py` + `scripts/run_corrected_strategy.py`).

**Execution Date:** 2026-09-22  
**Implementation Tested:** Non-Financials Universe, Top Quintile (Q5), SUE-Rank Priority, 60 Trading Days Holding.

---

## 1. Transaction Cost Sensitivity (Round-Trip Friction)

| Cost Scenario | Round-Trip Cost | Capacity (Slots) | Strategy CAGR (%) | Nifty 500 CAGR (%) | **Excess CAGR (%)** | Sharpe Ratio | Max Drawdown (%) | Win Rate (%) | Avg Net Return/Trade |
|---|---|---|---|---|---|---|---|---|---|
| **Low (0.300%)** | 0.300% | 10 slots | +17.77% | +11.0% | **+6.41%** | 0.943 | -19.3% | 59.1% | +4.52% |
| **Low (0.300%)** | 0.300% | 20 slots | +15.31% | +11.0% | **+3.97%** | 0.871 | -21.0% | 56.2% | +4.02% |
| **Low (0.300%)** | 0.300% | 30 slots | +16.35% | +11.0% | **+5.06%** | 0.892 | -21.8% | 58.1% | +4.38% |
| **Baseline (0.585%)** | 0.585% | 10 slots | +16.46% | +11.0% | **+5.10%** | 0.886 | -19.8% | 57.6% | +4.23% |
| **Baseline (0.585%)** | 0.585% | 20 slots | +14.05% | +11.0% | **+2.71%** | 0.811 | -21.4% | 55.4% | +3.73% |
| **Baseline (0.585%)** | 0.585% | 30 slots | +15.10% | +11.0% | **+3.81%** | 0.836 | -22.2% | 57.2% | +4.09% |
| **High (1.000%)** | 1.000% | 10 slots | +14.59% | +11.0% | **+3.23%** | 0.802 | -20.4% | 56.6% | +3.82% |
| **High (1.000%)** | 1.000% | 20 slots | +12.24% | +11.0% | **+0.90%** | 0.724 | -23.2% | 54.1% | +3.32% |
| **High (1.000%)** | 1.000% | 30 slots | +13.30% | +11.0% | **+2.01%** | 0.753 | -22.8% | 56.0% | +3.68% |

---

## 2. Liquidity & Institutional Capacity Estimates

| Capacity Configuration | Slots | Median Daily Turnover | 10th Percentile Daily Turnover | Annualized Turnover | Estimated Max AUM (1% Participation) | Estimated Max AUM (5% Participation) |
|---|---|---|---|---|---|---|
| **10-Slot Focused Book** | 10 | INR 70.6 Cr | INR 7.7 Cr | 396.8% | **INR 0.8 Cr** | **INR 3.8 Cr** |
| **20-Slot Moderate Book** | 20 | INR 84.2 Cr | INR 9.1 Cr | 388.8% | **INR 1.8 Cr** | **INR 9.1 Cr** |
| **30-Slot Diversified Book**| 30 | INR 77.5 Cr | INR 9.1 Cr | 382.0% | **INR 2.7 Cr** | **INR 13.7 Cr** |

---

## 3. Findings on Viability & Execution Reality
1. **Cost Hurdle Cleared Decisively:**
   - Under the baseline round-trip cost (0.585%), the 30-slot book produces positive excess CAGR over NIFTY 500 under honest discrete share/cash accounting.
   - Sensitivity: 0.30% round trip yields higher excess, while at 1.00% round trip, full-period excess is lower and holdout excess becomes negative.
2. **Realistic Capacity Ceiling:**
   - At a 1% volume participation cap (where 90% of trades fit within 1% of 20-day median ADV), realistic institutional capacity is approximately **INR 1.8 Cr to 2.2 Cr** (~INR 2 Cr).
   - At a 5% volume participation cap (90% of trades fitting), capacity scales to approximately **INR 9 Cr to 10 Cr**.
   - Sizing to median ADV (INR ~56-68 Cr) ignores the less-liquid tail where 43% of trades would exceed 1% participation at INR 15 Cr AUM.
3. **Turnover:**
   - One-way annual portfolio turnover is approximately **360% to 390%** (buys + sells / 2 NAV).
