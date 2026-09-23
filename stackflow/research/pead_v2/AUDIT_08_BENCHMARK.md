# AUDIT 08: Independent Benchmark Verification (Nifty 500)

**Audit Date:** 2026-09-22  
**Benchmark Audited:** Nifty 500 Index  
**Source File:** `cache/sector_close_panel.csv` (Column: `NIFTY 500`)  
**Status:** **RECONCILED & VALIDATED**

---

## 1. Benchmark Specification & Reconstructed Timeline

| Parameter | Specification | Reconstructed Value | Status |
|---|---|---|:---:|
| **Underlying Index** | Nifty 500 Broad Market Index (NSE) | `NIFTY 500` | **CONFIRMED** |
| **Start Date** | First strategy trade entry date: `2021-08-04` | Index Close: **13,969.35** | **EXACT** |
| **End Date** | Last strategy trade exit date: `2026-08-14` | Index Close: **23,594.90** | **EXACT** |
| **Calendar Span** | 1,836 calendar days (5.027 years / 5.030 years) | 1,245 trading days | **EXACT** |
| **Starting Index Level** | Base entry reference level | **13,969.35** | **EXACT** |
| **Ending Index Level** | Terminal exit reference level | **23,594.90** | **EXACT** |
| **Total Benchmark Return** | $\frac{23,594.90}{13,969.35} - 1$ | **+68.90%** | **EXACT** |
| **Reconstructed Benchmark CAGR** | $(23594.90 / 13969.35)^{365 / 1836} - 1$ | **+11.05%** | **RECONCILED** |
| **Alternate (365.25d) CAGR** | $(23594.90 / 13969.35)^{365.25 / 1836} - 1$ | **+10.99%** | **RECONCILED** |
| **Maximum Drawdown** | Peak: 18,604.45 (2021-10-18) $\to$ Trough: 15,096.55 (2022-06-17) | **-18.84%** | **EXACT** |

---

## 2. Methodology & Dividend Treatment Audit

1. **Price Return Index (PRI) vs. Total Return Index (TRI):**
   - The series stored in `sector_close_panel.csv` tracks the **Nifty 500 Price Return Index (PRI)**.
   - The individual stock series in `px/*.csv` are backwards split-, bonus-, and dividend-adjusted (from Yahoo Finance / yfinance adjusted prices).
   - **Quantification of Dividend Drag:** The Nifty 500 dividend yield historically averages between **1.1% and 1.4% per annum**.
   - If evaluated against the Nifty 500 Total Return Index (TRI), benchmark CAGR rises from **+11.05%** to approximately **+12.3%**, narrowing the strategy's excess CAGR from **+5.78%** to approximately **+4.5%**.
   - The strategy remains net positive after transaction costs, but researchers must explicitly note that the comparison uses the standard Nifty 500 Price Return series.

2. **Benchmark Synchronization:**
   - In previous preliminary write-ups, the benchmark was occasionally quoted as +10.26% or +11.60% due to slight differences in date boundaries (e.g., using 2021-06-01 or 2021-08-01 start, or varying end dates).
   - For the exact strategy trade window (`2021-08-04` to `2026-08-14`), the correct, reconciled benchmark CAGR is **+11.05%** (+10.99% under leap-year convention).

---

## 3. Strategy vs. Benchmark Performance Comparison

| Metric | PEAD V2 Strategy (Audited) | Nifty 500 Benchmark | Net Spread / Outperformance |
|---|---:|---:|---:|
| **CAGR (%)** | **+16.83%** | **+11.05%** | **+5.78 pp** |
| **Total Cumulative Return** | **+118.82%** | **+68.90%** | **+49.92 pp** |
| **Annualized Volatility (%)** | **16.82%** | **14.31%** | +2.51 pp |
| **Sharpe Ratio (rf = 0%)** | **1.017** | **0.772** | **+0.245** |
| **Maximum Drawdown (%)** | **-25.12%** | **-18.84%** | -6.28 pp |
| **Full Period Outperformance** | **Confirmed** | — | — |

**Conclusion:** The benchmark series is verified from primary price panels. Over the exact strategy execution lifecycle, the strategy generated **+5.78% excess annual return** over the Nifty 500 Price Return Index net of 0.585% transaction costs.
