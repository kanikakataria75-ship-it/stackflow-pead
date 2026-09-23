# StackFlow PEAD V2 — Phase 7: Portfolio Specification

**Document Date:** 2026-09-22  
**Status:** LOCKED BEFORE RUNNING PORTFOLIO EXPERIMENTS  
**Rule:** Every single cell in the grid below will be executed and reported without post-hoc omissions.

---

## 1. Strategy Architecture
- **Trading Style:** Event-driven, long-only, point-in-time ex-ante SUE signal.
- **Execution Session:** Strictly the **OPEN** of the trading session following the event day.
- **Position Sizing:** Equal-weight sleeves ($1 / N_{\text{slots}}$). Unallocated capital remains in cash (0% return, realistic cash drag).
- **Transaction Cost:** Round-trip transaction cost of **0.585%** deducted from every trade (LeadFlow NSE standard).
- **Benchmarks:** NIFTY 500 Index (daily close-to-close) and Equal-Weight Event Universe.

---

## 2. Locked Evaluation Grid

### Dimension 1: Signal Threshold
- **S1 (Q5 Only):** Top ex-ante SUE quintile (highest 20% surprise).
- **S2 (Q4 + Q5):** Top two ex-ante SUE quintiles (upper 40% surprise).

### Dimension 2: Concurrent Position Capacity ($N_{\text{slots}}$)
- **10 Slots:** Concentrated portfolio (10% per sleeve).
- **20 Slots:** Moderate diversification (5% per sleeve).
- **30 Slots:** Broad diversification (3.33% per sleeve).

### Dimension 3: Holding Horizon ($H$)
- **20 Trading Days** (~1 calendar month)
- **40 Trading Days** (~2 calendar months)
- **60 Trading Days** (~3 calendar months, V1 primary baseline)
- **90 Trading Days** (~4.5 calendar months)

### Dimension 4: Queueing Policy
- **P1: FIFO (First-Come First-Served):** Baseline V1 mechanism.
- **P2: SUE-Rank Priority:** On any entry day with more candidates than available slots, candidates with higher ex-ante SUE receive slot allocation.

### Dimension 5: Sector Scope
- **All Eligible Universe** (incorporates Financials).
- **Non-Financials Scope** (tests removal of the structural banking anomaly).

Total Core Cells: 2 signals $\times$ 3 slot counts $\times$ 4 horizons = **24 cells per queue policy**.
All cells will be saved to `PHASE_08_PORTFOLIO_RESULTS.csv`.
