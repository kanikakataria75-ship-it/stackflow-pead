"""BACKTEST REPLAY — the forward screens re-played on REAL historical data.

Until the forward record has filings of its own, the forward screens (Observatory, Signal Tape,
Positions, Performance) can be switched to show the corrected backtest as it stood on a past
date, REPLAY_AS_OF. Everything here is real research data, read-only:
  * filings   — research/pead_v2/corrected/pead_v2_events_corrected.csv (real SUE, real quintile)
  * decisions — research/pead_v2/corrected/trade_ledger_corrected.csv (the frozen 30-slot book)
  * prices    — the same calendar-filtered price files the backtest used (pead/cache/px)
  * NAV       — research/pead_v2/corrected/nav_daily_corrected.csv
Each ex-ante threshold is recomputed with the scanner's own function, using only filings made
before that filing. Every payload carries "demo": true and "stamp": "BACKTEST REPLAY": this is
seen, in-sample data and NEVER forward evidence. Nothing here is written anywhere.
(Module and flag keep the name `demo` for API compatibility.)
"""
from __future__ import annotations

import functools
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import settings
from .frozen import FROZEN
from .signal import exante_thresholds

REPLAY_AS_OF = date(2026, 6, 30)            # mid-way through the Mar-quarter results season
WINDOW_DAYS = 60
DEMO_TODAY = REPLAY_AS_OF                   # name kept for api.py
STAMP = {"demo": True, "stamp": "BACKTEST REPLAY", "replay_as_of": REPLAY_AS_OF.isoformat()}
C = settings.PEAD_V2 / "corrected"
PX = settings.STACKFLOW / "pead" / "cache" / "px"


@functools.lru_cache(maxsize=1)
def _events() -> pd.DataFrame:
    return pd.read_csv(C / "pead_v2_events_corrected.csv", parse_dates=["filing_ts", "event_day", "entry_date", "period_end"])


@functools.lru_cache(maxsize=1)
def _ledger() -> pd.DataFrame:
    return pd.read_csv(C / "trade_ledger_corrected.csv", parse_dates=["entry_date", "exit_date", "event_day"])


@functools.lru_cache(maxsize=1)
def _sessions() -> pd.DatetimeIndex:
    b = pd.read_csv(settings.BENCH_PANEL, index_col=0, parse_dates=True)["NIFTY 500"].dropna()
    return b.index


@functools.lru_cache(maxsize=1)
def _bench() -> pd.Series:
    return pd.read_csv(settings.BENCH_PANEL, index_col=0, parse_dates=True)["NIFTY 500"].dropna()


@functools.lru_cache(maxsize=512)
def _close(sym: str) -> pd.Series:
    f = PX / f"{sym}.csv"
    if not f.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(f, index_col=0, parse_dates=True)["Close"].sort_index()
    return d[d.index.isin(_sessions())]


def _exit_after(entry: pd.Timestamp) -> str:
    s = _sessions()
    i = s.searchsorted(entry)
    return s[min(i + FROZEN.holding_sessions, len(s) - 1)].date().isoformat()


@functools.lru_cache(maxsize=4)
def demo_signals(universe=None, today: date = REPLAY_AS_OF, n_days: int = WINDOW_DAYS) -> list[dict]:
    ev = _events()
    ex = ev[ev.q_exante_4q.notna()]
    pool_ts = ex.filing_ts.values.astype("datetime64[ns]")
    pool_sue = ex.sue.values.astype(float)
    lo, hi = pd.Timestamp(today - timedelta(days=n_days)), pd.Timestamp(today) + pd.Timedelta(hours=23, minutes=59)
    win = ev[(ev.filing_ts > lo) & (ev.filing_ts <= hi)].sort_values("filing_ts")
    taken = {(r.symbol, r.entry_date) for r in _ledger().itertuples()}
    out = []
    for r in win.itertuples():
        th = exante_thresholds(pool_ts, pool_sue, r.filing_ts.to_pydatetime())
        q = None if pd.isna(r.q_exante_4q) else int(r.q_exante_4q)
        if q is None:
            dec, why = "REJECTED", "THRESHOLDS_UNAVAILABLE"
        elif q != 5:
            dec, why = "NO_SIGNAL", f"Q{q}"
        elif bool(r.is_fin):
            dec, why = "REJECTED", "FINANCIAL_SECTOR"
        elif (r.symbol, r.entry_date) in taken:
            dec, why = "ENTER", ""
        else:
            dec, why = "REJECTED", "FULL_QUEUE"      # the backtest book had no free slot for it
        out.append(dict(
            signal_id=f"REPLAY_{r.symbol}_{r.period_end:%Y%m%d}", symbol=r.symbol,
            industry=str(r.industry).title(), is_fin=bool(r.is_fin),
            filing_timestamp=r.filing_ts.isoformat(sep=" "), event_day=r.event_day.date().isoformat(),
            planned_entry=r.entry_date.date().isoformat(), planned_exit=_exit_after(r.entry_date),
            sue=round(float(r.sue), 4), quintile=q, q20=th.q20, q40=th.q40, q60=th.q60, q80=th.q80,
            hist_events=th.n, decision=dec, reason=why,
            scanned_at=f"{r.filing_ts.date().isoformat()} 18:30:00", **STAMP))
    return out


def demo_positions(signals=None, today: date = REPLAY_AS_OF) -> dict:
    L = _ledger()
    t = pd.Timestamp(today)
    s = _sessions()
    b = _bench()
    ind = _events().drop_duplicates("symbol").set_index("symbol").industry
    open_, closed = [], []
    for r in L.itertuples():
        base = dict(signal_id=r.trade_id, symbol=r.symbol, industry=str(ind.get(r.symbol, r.sector)).title(), sue=float(r.sue),
                    entry_date=r.entry_date.date().isoformat(), exit_date=r.exit_date.date().isoformat(),
                    entry_price=float(r.entry_price), holding_sessions=FROZEN.holding_sessions, **STAMP)
        if r.entry_date <= t <= r.exit_date:
            cl = _close(r.symbol)
            cl = cl[cl.index <= t]
            p1 = float(cl.iloc[-1]) if len(cl) else float(r.entry_price)
            held = int(((s > r.entry_date) & (s <= t)).sum())
            bret = float(b.asof(t) / b.asof(r.entry_date) - 1)
            open_.append(base | dict(current_price=p1, sessions_held=held, price_date=today.isoformat(),
                                     unrealised_return=p1 / r.entry_price - 1 - FROZEN.half_cost,
                                     excess_vs_nifty500=p1 / r.entry_price - 1 - bret))
        elif t - pd.Timedelta(days=WINDOW_DAYS) <= r.exit_date < t:
            closed.append(base | dict(exit_price=float(r.exit_price), net_return=float(r.net_return),
                                      excess_vs_nifty500=float(r.excess_vs_nifty500)))
    return {"open": open_, "planned": [], "closed": closed, "slots_used": len(open_), "slots": FROZEN.slots, **STAMP}


def demo_performance(today: date = REPLAY_AS_OF) -> dict:
    nav = pd.read_csv(C / "nav_daily_corrected.csv", parse_dates=["date"]).set_index("date")
    nav = nav[nav.index <= pd.Timestamp(today)]
    nav = nav[nav.index >= pd.Timestamp(today) - pd.Timedelta(days=183)]      # the last six months of the book
    n0, b0 = nav.strategy_nav.iloc[0], nav.nifty500.iloc[0]
    nv = nav.strategy_nav / n0
    series = [dict(date=d.date().isoformat(), nav=float(v), bench=float(bb / b0), positions=int(p), drawdown=float(dd))
              for d, v, bb, p, dd in zip(nav.index, nv, nav.nifty500, nav.positions_held, nv / nv.cummax() - 1)]
    return {"series": series, "note": "Backtest replay: the last six months of the corrected backtest book before "
            f"{today.isoformat()}. Seen data — not forward evidence.", **STAMP}
