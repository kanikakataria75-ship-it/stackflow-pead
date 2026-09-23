"""SUE calculation engine and point-in-time rolling ex-ante quintile assigner."""
import numpy as np
import pandas as pd
from .config import MIN_PRIOR_YOY


def compute_sue_series(vals, min_prior=MIN_PRIOR_YOY):
    """Compute SUE using seasonal random walk on an array of quarterly profit values.
    
    SUE_t = (PAT_t - PAT_{t-4}) / std(YoY changes over prior 8 quarters)
    Requires >= min_prior prior YoY changes.
    """
    n = len(vals)
    yoy = np.full(n, np.nan)
    for i in range(4, n):
        if np.isfinite(vals[i]) and np.isfinite(vals[i - 4]):
            yoy[i] = vals[i] - vals[i - 4]
            
    sue = np.full(n, np.nan)
    for i in range(n):
        # Look back up to 8 prior YoY observations strictly before index i
        hist = yoy[max(0, i - 8):i]
        hist = hist[np.isfinite(hist)]
        if len(hist) >= min_prior and np.isfinite(yoy[i]):
            sd = float(np.std(hist, ddof=1))
            if sd > 1e-12:
                sue[i] = yoy[i] / sd
    return sue, yoy


def compute_sue_series_datematched(period_ends, vals, min_prior=MIN_PRIOR_YOY):
    """Audit fix 5: SUE with the YoY change matched by fiscal quarter, not by row index.

    YoY_q = PAT_q - PAT_(same quarter one year earlier), only if that quarter exists.
    SUE_q = YoY_q / std(YoY over the 8 prior calendar quarters that exist), >= min_prior required.
    Gaps in the XBRL series no longer make row i-4 a different quarter (683 events were affected).
    """
    q = [pd.Timestamp(p).to_period("Q") for p in period_ends]
    pos = {k: i for i, k in enumerate(q)}
    n = len(vals)
    yoy = np.full(n, np.nan)
    for i, k in enumerate(q):
        j = pos.get(k - 4)
        if j is not None and np.isfinite(vals[i]) and np.isfinite(vals[j]):
            yoy[i] = vals[i] - vals[j]
    sue = np.full(n, np.nan)
    for i, k in enumerate(q):
        hist = np.array([yoy[pos[k - m]] for m in range(1, 9) if (k - m) in pos])
        hist = hist[np.isfinite(hist)]
        if len(hist) >= min_prior and np.isfinite(yoy[i]):
            sd = float(np.std(hist, ddof=1))
            if sd > 1e-12:
                sue[i] = yoy[i] / sd
    return sue, yoy


def assign_ex_ante_quintiles_rolling(df, date_col="event_day", sue_col="sue",
                                     lookback_days=365, min_events=150):
    """Assign SUE quintiles strictly ex-ante using rolling historical window.
    
    For an event at date T, thresholds are determined exclusively from qualifying
    events that occurred in [T - lookback_days, T).
    """
    df = df.sort_values(date_col).copy()
    dates = df[date_col].values
    sues = df[sue_col].values
    n = len(df)
    quintiles = np.full(n, np.nan)
    
    # Pre-convert dates to numpy datetime64[ns]
    dates_dt = pd.to_datetime(dates).values
    lookback_delta = np.timedelta64(lookback_days, 'D')
    
    for i in range(n):
        t_cur = dates_dt[i]
        t_start = t_cur - lookback_delta
        # Select prior events strictly before t_cur and within lookback window
        mask = (dates_dt < t_cur) & (dates_dt >= t_start)
        hist_sues = sues[mask]
        hist_sues = hist_sues[np.isfinite(hist_sues)]
        
        if len(hist_sues) >= min_events and np.isfinite(sues[i]):
            q20, q40, q60, q80 = np.quantile(hist_sues, [0.20, 0.40, 0.60, 0.80])
            s = sues[i]
            if s <= q20:
                quintiles[i] = 1
            elif s <= q40:
                quintiles[i] = 2
            elif s <= q60:
                quintiles[i] = 3
            elif s <= q80:
                quintiles[i] = 4
            else:
                quintiles[i] = 5
                
    return pd.Series(quintiles, index=df.index)


def assign_ex_ante_quintiles_expanding(df, date_col="event_day", sue_col="sue", min_events=200):
    """Assign SUE quintiles strictly ex-ante using all historical events prior to T."""
    df = df.sort_values(date_col).copy()
    dates = df[date_col].values
    sues = df[sue_col].values
    n = len(df)
    quintiles = np.full(n, np.nan)
    
    dates_dt = pd.to_datetime(dates).values
    
    for i in range(n):
        t_cur = dates_dt[i]
        mask = (dates_dt < t_cur)
        hist_sues = sues[mask]
        hist_sues = hist_sues[np.isfinite(hist_sues)]
        
        if len(hist_sues) >= min_events and np.isfinite(sues[i]):
            q20, q40, q60, q80 = np.quantile(hist_sues, [0.20, 0.40, 0.60, 0.80])
            s = sues[i]
            if s <= q20:
                quintiles[i] = 1
            elif s <= q40:
                quintiles[i] = 2
            elif s <= q60:
                quintiles[i] = 3
            elif s <= q80:
                quintiles[i] = 4
            else:
                quintiles[i] = 5
                
    return pd.Series(quintiles, index=df.index)


def assign_v1_quarterly_quintiles(df, qtr_col="qtr", sue_col="sue"):
    """V1 implementation: Quintiles grouped across the entire calendar quarter (contains look-ahead)."""
    def qcut_safe(g):
        try:
            return pd.qcut(g[sue_col].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        except Exception:
            return pd.Series(np.nan, index=g.index)
    return df.groupby(qtr_col, group_keys=False).apply(qcut_safe)
