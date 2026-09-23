"""Data loader for XBRL quarterly financials, timestamps, price series, and benchmark."""
import os
import glob
import warnings
import numpy as np
import pandas as pd
from .config import XBRL_CACHE, PX_CACHE, BENCHMARK_FILE, CUTOFF, MIN_TURNOVER, MIN_PRICE

warnings.filterwarnings("ignore")


def load_timestamps():
    """Load exact filing timestamps from filing_index.csv and filing_index_integrated.csv."""
    rows = []
    # 1. Standard filing index
    f1 = os.path.join(XBRL_CACHE, "filing_index.csv")
    if os.path.exists(f1):
        df1 = pd.read_csv(f1)
        df1 = df1[df1.has_xml == True]
        ts1 = pd.to_datetime(df1.filing_date, format="%d-%b-%Y %H:%M", errors="coerce")
        to_date1 = pd.to_datetime(df1.to_date, format="%d-%b-%Y", errors="coerce")
        rows.append(pd.DataFrame({"symbol": df1.symbol, "basis": df1.basis, "to_date": to_date1, "ts": ts1}))

    # 2. Integrated filing index
    f2 = os.path.join(XBRL_CACHE, "filing_index_integrated.csv")
    if os.path.exists(f2):
        df2 = pd.read_csv(f2)
        df2 = df2[(df2.filing_type == "Integrated Filing- Financials") & (df2.has_xml == True)]
        ts2 = pd.to_datetime(df2.broadcast, format="%d-%b-%Y %H:%M:%S", errors="coerce")
        to_date2 = pd.to_datetime(df2.qe_date, format="%d-%b-%Y", errors="coerce")
        rows.append(pd.DataFrame({"symbol": df2.symbol, "basis": df2.basis, "to_date": to_date2, "ts": ts2}))

    combined = pd.concat(rows, ignore_index=True).dropna(subset=["symbol", "to_date"])
    # Pick the earliest timestamp per symbol and period_end
    earliest = combined.sort_values("ts").groupby(["symbol", "to_date"], as_index=False).first()
    return earliest


def load_benchmark():
    """Load Nifty 500 series from sector_close_panel.csv."""
    df = pd.read_csv(BENCHMARK_FILE, index_col=0, parse_dates=True)
    nifty500 = df["NIFTY 500"].dropna()
    nifty500.index = pd.to_datetime(nifty500.index).normalize()
    return nifty500.sort_index()


def load_prices():
    """Load all daily OHLCV price series into a dictionary {symbol: DataFrame}.
    
    Fix 6: Validates every price file against the verified NSE trading calendar
    and filters out phantom zero-volume sessions (2026-01-15, 05-01, 05-28, 06-26, 09-14).
    """
    px_dict = {}
    pattern = os.path.join(PX_CACHE, "*.csv")
    files = glob.glob(pattern)
    bench = load_benchmark()
    valid_sessions = set(bench.index)
    
    for f in files:
        sym = os.path.basename(f)[:-4]
        try:
            df = pd.read_csv(f, index_col=0, parse_dates=True)
            if len(df) > 100 and {"Open", "Close", "Volume"}.issubset(df.columns):
                # Ensure index is sorted DatetimeIndex without timezone
                df.index = pd.to_datetime(df.index).normalize()
                # Drop phantom sessions not in verified NSE trading calendar
                df = df[df.index.isin(valid_sessions)]
                px_dict[sym] = df.sort_index()
        except Exception:
            continue
    return px_dict


def load_raw_xbrl_pat():
    """Load raw quarterly filings with valid PAT from extract_universe.csv."""
    fpath = os.path.join(XBRL_CACHE, "extract_universe.csv")
    df = pd.read_csv(fpath)
    df = df[(df.period == "Quarterly") & df.pat.notna()].copy()
    df["period_end"] = pd.to_datetime(df.period_end, errors="coerce")
    df["filing_date"] = pd.to_datetime(df.filing_date, errors="coerce")
    df = df[df.period_end.notna() & df.filing_date.notna()].copy()
    
    # Merge exact timestamps
    ts_df = load_timestamps()
    merged = df.merge(ts_df.rename(columns={"to_date": "period_end", "basis": "basis_ts"}),
                      on=["symbol", "period_end"], how="left")
    return merged
