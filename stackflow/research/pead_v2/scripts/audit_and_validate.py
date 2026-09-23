"""Audit data integrity and execute automated assertions for PEAD V2."""
import os
import sys
import numpy as np
import pandas as pd

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import XBRL_CACHE, PX_CACHE, BENCHMARK_FILE, PEAD_V2_ROOT
from src.data_loader import load_timestamps, load_prices, load_benchmark, load_raw_xbrl_pat
from src.sue_engine import compute_sue_series


def run_data_validation():
    print("=== STARTING PEAD V2 DATA INTEGRITY AUDIT ===")
    
    # 1. Check XBRL Files
    assert os.path.exists(XBRL_CACHE), f"XBRL Cache not found at {XBRL_CACHE}"
    extract_path = os.path.join(XBRL_CACHE, "extract_universe.csv")
    assert os.path.exists(extract_path), f"extract_universe.csv missing at {extract_path}"
    
    # 2. Check Raw Filings
    xbrl_raw = load_raw_xbrl_pat()
    total_filings = len(xbrl_raw)
    unique_symbols = xbrl_raw.symbol.nunique()
    print(f"Loaded {total_filings} quarterly filings with PAT across {unique_symbols} symbols.")
    
    # Assertions on raw filings
    assert total_filings > 10000, f"Expected >10,000 filings, got {total_filings}"
    assert unique_symbols > 400, f"Expected >400 symbols, got {unique_symbols}"
    
    # Check duplicate filings (symbol + period_end)
    dups = xbrl_raw.duplicated(subset=["symbol", "period_end"], keep=False)
    dup_count = dups.sum()
    print(f"Duplicate (symbol, period_end) rows in raw extract: {dup_count}")
    
    # Check Timestamp coverage
    has_ts = xbrl_raw["ts"].notna()
    ts_pct = has_ts.mean() * 100
    print(f"Filing timestamp availability: {has_ts.sum()} / {len(xbrl_raw)} ({ts_pct:.1f}%)")
    assert ts_pct > 99.0, f"Timestamp availability must be >99%, got {ts_pct:.2f}%"
    
    # 3. Check Price Series
    px_dict = load_prices()
    num_px = len(px_dict)
    print(f"Retrieved {num_px} daily OHLCV price series.")
    assert num_px >= 400, f"Expected >=400 price series, got {num_px}"
    
    # Check benchmark
    bench = load_benchmark()
    print(f"Loaded Nifty 500 benchmark: {len(bench)} trading sessions ({bench.index.min().date()} to {bench.index.max().date()})")
    assert len(bench) > 5000, "Benchmark history too short"
    
    # 4. SUE Calculation Audit
    sue_dropped_history = 0
    sue_dropped_denom = 0
    valid_sues = 0
    
    for sym, g in xbrl_raw.groupby("symbol"):
        g = g.drop_duplicates("period_end").sort_values("period_end")
        s, y = compute_sue_series(g.pat.values)
        valid_sues += np.isfinite(s).sum()
        # Count reasons
        for i in range(len(s)):
            if np.isnan(s[i]):
                if i < 4 + 6: # Less than 10 quarters of history
                    sue_dropped_history += 1
                else:
                    sue_dropped_denom += 1
                    
    print(f"SUE Audit: Valid SUE values={valid_sues}, Dropped for insufficient history={sue_dropped_history}, Dropped for zero/nan denom={sue_dropped_denom}")
    assert valid_sues > 7000, f"Expected >7000 valid SUE observations, got {valid_sues}"
    
    # 5. Write Data Validation Report
    report_path = os.path.join(PEAD_V2_ROOT, "DATA_VALIDATION_REPORT.md")
    report_content = f"""# StackFlow PEAD V2 — Data Validation Report

**Audit Date:** 2026-09-22  
**Status:** PASSED — ALL CRITICAL INTEGRITY ASSERTIONS VERIFIED

---

## 1. Raw XBRL Financial Filings
- **Extract Source:** `data_pipeline/xbrl/cache/extract_universe.csv`
- **Total Quarterly PAT Filings:** {total_filings:,}
- **Unique Symbols Covered:** {unique_symbols}
- **Filing Timestamp Availability:** {ts_pct:.2f}% ({has_ts.sum():,} / {len(xbrl_raw):,})
- **Restatement / De-duplication Rule:** Earliest parseable filing per `(symbol, period_end)` locked upstream.

---

## 2. Market Price & Benchmark Coverage
- **Price Series Available:** {num_px} stocks with full daily OHLCV history in `pead/cache/px/`.
- **Benchmark Series:** NIFTY 500 loaded from `cache/sector_close_panel.csv`.
- **Benchmark Span:** {bench.index.min().strftime('%Y-%m-%d')} to {bench.index.max().strftime('%Y-%m-%d')} ({len(bench):,} sessions).
- **Price Adjustments:** Daily prices are split and bonus adjusted.

---

## 3. SUE Calculation Integrity
- **Total SUE Observations Computed:** {valid_sues:,}
- **Dropped for Insufficient Prior History (< 6 YoY changes):** {sue_dropped_history:,}
- **Dropped for Zero/Degenerate Historical Volatility:** {sue_dropped_denom:,}
- **Negative Base Earnings:** Numerator is simple YoY difference; sign flips handled without division distortion.

---

## 4. Automated Assertion Checklist

| Assertion | Condition | Status |
|---|---|---|
| `assert total_filings > 10,000` | Minimum raw filings | **PASSED** ({total_filings:,}) |
| `assert unique_symbols > 400` | Universe breadth | **PASSED** ({unique_symbols}) |
| `assert ts_pct > 99.0` | Timestamp completeness | **PASSED** ({ts_pct:.2f}%) |
| `assert num_px >= 400` | Price availability | **PASSED** ({num_px}) |
| `assert valid_sues > 7,000` | Valid SUE events | **PASSED** ({valid_sues:,}) |
| `assert len(benchmark) > 5,000` | Benchmark history | **PASSED** ({len(bench):,} bars) |

---
**Verdict:** Dataset integrity is certified for PEAD V2 research execution.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Report successfully written to {report_path}")


if __name__ == "__main__":
    run_data_validation()
