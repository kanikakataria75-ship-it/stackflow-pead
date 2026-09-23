"""Daily prices for the forward period.

Forward fills use RAW exchange prices (auto_adjust=False) — the prices a real order would see.
Units are asserted, not assumed: the Yahoo currency must be INR for every .NS series and the
NIFTY 500 index, and 20-session traded value must fall in a plausible INR range. Rows on
non-sessions or with zero volume are dropped against the validated NSE calendar.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import settings
from .calendar import TradingCalendar, filter_to_sessions

BENCH_TICKER = "^CRSLDX"            # NIFTY 500 on Yahoo


class UnitError(AssertionError):
    """Price or turnover units are not INR / not plausible."""


def _yf_history(ticker: str, start: date) -> tuple[pd.DataFrame, str | None]:
    import yfinance as yf
    t = yf.Ticker(ticker)
    h = t.history(start=start.isoformat(), interval="1d", auto_adjust=False)
    cur = (t.history_metadata or {}).get("currency")
    if h is None or h.empty:
        return pd.DataFrame(columns=["Open", "Close", "Volume"]), cur
    h = h[["Open", "Close", "Volume"]].copy()
    h.index = pd.to_datetime(h.index).tz_localize(None).normalize()
    return h[~h.index.duplicated(keep="last")].sort_index(), cur


class PriceStore:
    def __init__(self, cal: TradingCalendar, fetcher=None, max_age_hours: float = 6.0):
        self.cal = cal
        self._fetch = fetcher or _yf_history
        self.max_age = timedelta(hours=max_age_hours)
        self.freshness: dict[str, str] = {}

    def _cache(self, sym: str):
        return settings.PX_DIR / f"{sym.replace('&', 'and').replace('^', '_')}.csv"

    def history(self, sym: str, start: date, is_index: bool = False) -> pd.DataFrame:
        f = self._cache(sym)
        if f.exists() and datetime.now() - datetime.fromtimestamp(f.stat().st_mtime) < self.max_age:
            df = pd.read_csv(f, index_col=0, parse_dates=True)
        else:
            ticker = sym if is_index else f"{sym}.NS"
            df, currency = self._fetch(ticker, start - timedelta(days=60))
            if len(df) and currency != "INR":
                raise UnitError(f"{ticker}: currency {currency!r} != 'INR' — refusing to use")
            if len(df):
                df.to_csv(f)
        if is_index:
            df = df[[self.cal.is_session(d.date()) for d in df.index]]
        else:
            df = filter_to_sessions(df, self.cal)
        if len(df):
            self.freshness[sym] = df.index.max().date().isoformat()
        return df[df.index >= pd.Timestamp(start) - pd.Timedelta(days=60)]

    def benchmark(self, start: date) -> pd.Series:
        """NIFTY 500 closes: validated research panel up to its end, Yahoo afterwards."""
        panel = pd.read_csv(settings.BENCH_PANEL, index_col=0, parse_dates=True)["NIFTY 500"].dropna()
        live = self.history(BENCH_TICKER, max(start, panel.index.max().date() - timedelta(days=10)), is_index=True)
        s = pd.concat([panel, live["Close"][live.index > panel.index.max()]]).sort_index()
        return s[s.index >= pd.Timestamp(start) - pd.Timedelta(days=10)]


def turnover20(px: pd.DataFrame, event_day: date, window: int = 20, min_sessions: int = 10) -> float | None:
    """Mean Close x Volume (INR) over the `window` sessions strictly before the event day."""
    w = px[px.index < pd.Timestamp(event_day)].tail(window)
    if len(w) < min_sessions:
        return None
    val = float((w["Close"] * w["Volume"]).mean())
    if not np.isfinite(val) or not (1e3 <= val <= 5e12):
        raise UnitError(f"20-session traded value {val:,.0f} is outside the plausible INR range")
    return val
