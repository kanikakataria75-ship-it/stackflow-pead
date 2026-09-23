"""SUE (fiscal-quarter-matched YoY) and ex-ante quintile thresholds.

SUE is computed by the SAME function the corrected research uses
(research/pead_v2/src/sue_engine.py::compute_sue_series_datematched), imported, not copied.

Ex-ante thresholds for a filing with timestamp T use ONLY qualifying events whose filing
timestamp is strictly before T and within the trailing 365 days: [T-365d, T). Same-day peers
filed later than T are invisible by construction. (The research used event_day < T; the scanner
uses the stricter filing-timestamp rule required for live use.)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from . import settings
from .frozen import FROZEN

if str(settings.PEAD_V2) not in sys.path:
    sys.path.insert(0, str(settings.PEAD_V2))
from src.sue_engine import compute_sue_series_datematched  # noqa: E402  (research, read-only)


def sue_for_new_quarter(history: pd.DataFrame, period_end, pat: float) -> tuple[float, float | None, int]:
    """history: rows (period_end, pat) for ONE symbol, all strictly earlier quarters.
    Returns (sue, pat_same_quarter_last_year, n_prior_yoy_used)."""
    h = history[pd.to_datetime(history.period_end) < pd.Timestamp(period_end)]
    h = h.drop_duplicates("period_end").sort_values("period_end")
    pe = list(pd.to_datetime(h.period_end)) + [pd.Timestamp(period_end)]
    vals = np.array(list(h.pat.astype(float)) + [float(pat)])
    sue, yoy = compute_sue_series_datematched(pe, vals, min_prior=FROZEN.min_prior_yoy)
    q = pd.Timestamp(period_end).to_period("Q")
    ly = h[pd.to_datetime(h.period_end).dt.to_period("Q") == q - 4]
    pat_ly = float(ly.pat.iloc[0]) if len(ly) else None
    n_prior = int(np.isfinite(yoy[:-1][-8:]).sum()) if len(yoy) > 1 else 0
    return float(sue[-1]), pat_ly, n_prior


@dataclass
class Thresholds:
    q20: float | None
    q40: float | None
    q60: float | None
    q80: float | None
    n: int
    latest_ts_used: datetime | None

    @property
    def ok(self) -> bool:
        return self.q80 is not None


def exante_thresholds(pool_ts: np.ndarray, pool_sue: np.ndarray, ts: datetime) -> Thresholds:
    """pool_ts: datetime64[ns] filing timestamps of qualifying events; pool_sue: their SUE."""
    t = np.datetime64(pd.Timestamp(ts).tz_localize(None) if pd.Timestamp(ts).tzinfo else pd.Timestamp(ts), "ns")
    lo = t - np.timedelta64(FROZEN.lookback_days, "D")
    mask = (pool_ts < t) & (pool_ts >= lo) & np.isfinite(pool_sue)
    hist = pool_sue[mask]
    latest = pd.Timestamp(pool_ts[mask].max()).to_pydatetime() if mask.any() else None
    if len(hist) < FROZEN.min_history_events:
        return Thresholds(None, None, None, None, int(len(hist)), latest)
    q20, q40, q60, q80 = np.quantile(hist, [0.2, 0.4, 0.6, 0.8])
    return Thresholds(float(q20), float(q40), float(q60), float(q80), int(len(hist)), latest)


def quintile(sue: float, th: Thresholds) -> int | None:
    """Same boundary convention as the research: s <= q20 -> 1 ... s > q80 -> 5."""
    if not th.ok or not np.isfinite(sue):
        return None
    for i, cut in enumerate((th.q20, th.q40, th.q60, th.q80), start=1):
        if sue <= cut:
            return i
    return 5


def load_research_pool() -> pd.DataFrame:
    """Qualifying events from the corrected research dataset (all filed before the freeze)."""
    ev = pd.read_csv(settings.CORRECTED_EVENTS, usecols=["symbol", "filing_ts", "sue", "is_fin", "industry",
                                                         "period_end", "q_exante_4q", "event_day"],
                     parse_dates=["filing_ts", "period_end", "event_day"])
    ev["source"] = "research"
    return ev
