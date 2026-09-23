# StackFlow PEAD V2 — Data Validation Report

**Audit Date:** 2026-09-22  
**Status:** PASSED — ALL CRITICAL INTEGRITY ASSERTIONS VERIFIED

---

## 1. Raw XBRL Financial Filings
- **Extract Source:** `data_pipeline/xbrl/cache/extract_universe.csv`
- **Total Quarterly PAT Filings:** 13,150
- **Unique Symbols Covered:** 451
- **Filing Timestamp Availability:** 100.00% (13,150 / 13,150)
- **Restatement / De-duplication Rule:** Earliest parseable filing per `(symbol, period_end)` locked upstream.

---

## 2. Market Price & Benchmark Coverage
- **Price Series Available:** 434 stocks with full daily OHLCV history in `pead/cache/px/`.
- **Benchmark Series:** NIFTY 500 loaded from `cache/sector_close_panel.csv`.
- **Benchmark Span:** 1996-01-01 to 2026-09-18 (7,628 sessions).
- **Price Adjustments:** Daily prices are split and bonus adjusted.

---

## 3. SUE Calculation Integrity
- **Total SUE Observations Computed:** 8,644
- **Dropped for Insufficient Prior History (< 6 YoY changes):** 4,506
- **Dropped for Zero/Degenerate Historical Volatility:** 0
- **Negative Base Earnings:** Numerator is simple YoY difference; sign flips handled without division distortion.

---

## 4. Automated Assertion Checklist

| Assertion | Condition | Status |
|---|---|---|
| `assert total_filings > 10,000` | Minimum raw filings | **PASSED** (13,150) |
| `assert unique_symbols > 400` | Universe breadth | **PASSED** (451) |
| `assert ts_pct > 99.0` | Timestamp completeness | **PASSED** (100.00%) |
| `assert num_px >= 400` | Price availability | **PASSED** (434) |
| `assert valid_sues > 7,000` | Valid SUE events | **PASSED** (8,644) |
| `assert len(benchmark) > 5,000` | Benchmark history | **PASSED** (7,628 bars) |

---
**Verdict:** Dataset integrity is certified for PEAD V2 research execution.
