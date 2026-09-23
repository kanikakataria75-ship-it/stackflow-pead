"""Validated NSE trading calendar and the frozen event-day / entry timing rule.

Sessions are defined by the EXCHANGE, never by price files:
  * historical: sessions on which the NIFTY 500 index printed (cache/sector_close_panel.csv);
  * forward: Mon-Fri minus NSE's official capital-market holiday list (/api/holiday-master).
Price rows on dates that are not sessions (e.g. the zero-volume holiday rows yfinance emits,
2026-01-15 / 05-01 / 05-28 / 06-26 / 09-14) are rejected by `filter_to_sessions`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable

import pandas as pd

from . import settings
from .frozen import FROZEN


@dataclass
class TradingCalendar:
    historical: frozenset          # date objects with a validated index print
    holidays: frozenset            # NSE CM holidays (date objects)
    hist_end: date                 # last date covered by the historical source
    special_sessions: frozenset = frozenset()   # weekend sessions (e.g. Budget / DR drills)

    def is_session(self, d: date) -> bool:
        if d <= self.hist_end:
            return d in self.historical
        if d in self.special_sessions:
            return True
        return d.weekday() < 5 and d not in self.holidays

    def next_session(self, d: date, inclusive: bool = False) -> date:
        cur = d if inclusive else d + timedelta(days=1)
        for _ in range(40):
            if self.is_session(cur):
                return cur
            cur += timedelta(days=1)
        raise RuntimeError(f"no NSE session within 40 days after {d}")

    def prev_session(self, d: date) -> date:
        cur = d - timedelta(days=1)
        for _ in range(40):
            if self.is_session(cur):
                return cur
            cur -= timedelta(days=1)
        raise RuntimeError(f"no NSE session within 40 days before {d}")

    def add_sessions(self, d: date, n: int) -> date:
        cur = d
        for _ in range(n):
            cur = self.next_session(cur)
        return cur

    def sessions_between(self, a: date, b: date) -> list[date]:
        """Sessions in (a, b]."""
        out, cur = [], a
        while True:
            cur = self.next_session(cur)
            if cur > b:
                return out
            out.append(cur)


def event_and_entry(filing_ts: datetime, cal: TradingCalendar) -> tuple[date, date]:
    """Frozen timing rule (TIMING_RULES.md, Cases A-C, as coded in the research pipeline).

    A  filing <= 15:30 IST on a session day D       -> event day D,  entry OPEN of next session
    B  filing  > 15:30 IST on a session day D       -> event day = next session, entry the session after
    C  filing on a non-session day:  <= 15:30 IST   -> event day D1 (first session after), entry D2
                                      > 15:30 IST   -> event day D2, entry D3   (conservative, as coded)
    `filing_ts` must be a naive IST wall-clock timestamp or tz-aware.
    """
    if filing_ts.tzinfo is not None:
        filing_ts = filing_ts.astimezone(settings.IST).replace(tzinfo=None)
    d = filing_ts.date()
    after = filing_ts.time() > FROZEN.cutoff_ist
    ev = cal.next_session(d, inclusive=True)        # first session on/after filing date
    if after:
        ev = cal.next_session(ev)                   # one session later (Case B, and Case C > 15:30)
    entry = cal.next_session(ev)
    return ev, entry


def entry_decision_deadline(entry: date, cal: TradingCalendar) -> datetime:
    """Latest moment a filing can still be assigned this entry date: 15:30 IST on the session
    before it. After this instant the candidate set for `entry` is closed and the slot
    allocation for that date can be finalised."""
    return datetime.combine(cal.prev_session(entry), FROZEN.cutoff_ist)


def filter_to_sessions(df: pd.DataFrame, cal: TradingCalendar) -> pd.DataFrame:
    """Drop price rows that are not NSE sessions, and zero-volume rows."""
    if df.empty:
        return df
    keep = [cal.is_session(ix.date()) for ix in df.index]
    out = df[keep]
    if "Volume" in out.columns:
        out = out[out["Volume"].fillna(0) > 0]
    return out


# ------------------------------------------------------------------ construction / validation
def _load_holidays(fetch=None) -> tuple[set, dict]:
    """NSE CM holiday list; cached. `fetch` is an optional callable returning the API JSON."""
    meta = {"source": "cache", "fetched_at": None}
    data = None
    if fetch is not None:
        try:
            data = fetch()
            settings.HOLIDAYS_FILE.write_text(json.dumps({"fetched_at": datetime.now().isoformat(), "data": data}))
            meta = {"source": "nse_api", "fetched_at": datetime.now().isoformat()}
        except Exception as exc:        # network failure: fall back to cache
            meta["error"] = str(exc)
    if data is None and settings.HOLIDAYS_FILE.exists():
        blob = json.loads(settings.HOLIDAYS_FILE.read_text())
        data, meta["fetched_at"] = blob["data"], blob.get("fetched_at")
    hol = set()
    for row in (data or {}).get("CM", []):
        hol.add(datetime.strptime(row["tradingDate"], "%d-%b-%Y").date())
    meta["n_holidays"] = len(hol)
    return hol, meta


def build_calendar(fetch_holidays=None) -> tuple[TradingCalendar, dict]:
    panel = pd.read_csv(settings.BENCH_PANEL, index_col=0, parse_dates=True)["NIFTY 500"].dropna()
    hist = frozenset(d.date() for d in panel.index)
    hist_end = max(hist)
    hol, meta = _load_holidays(fetch_holidays)
    cal = TradingCalendar(historical=hist, holidays=frozenset(hol), hist_end=hist_end,
                          special_sessions=frozenset(d for d in hist if d.weekday() >= 5))
    # validation: over the overlap year, does "weekdays minus holidays" reproduce the index sessions?
    yr_start = date(hist_end.year, 1, 1)
    rule = {yr_start + timedelta(days=i) for i in range((hist_end - yr_start).days + 1)}
    rule = {d for d in rule if d.weekday() < 5 and d not in hol}
    idx = {d for d in hist if d >= yr_start}
    meta.update({
        "historical_sessions": len(hist), "historical_end": hist_end.isoformat(),
        "validation_year": hist_end.year,
        "rule_minus_index": sorted(d.isoformat() for d in rule - idx),   # rule says open, index silent
        "index_minus_rule": sorted(d.isoformat() for d in idx - rule),   # special weekend sessions
    })
    meta["validated"] = bool(hol) and not meta["rule_minus_index"]
    return cal, meta
