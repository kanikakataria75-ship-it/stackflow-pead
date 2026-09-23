"""Frozen timing rule on session, weekend and holiday cases; phantom-session rejection."""
from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from drift.calendar import TradingCalendar, entry_decision_deadline, event_and_entry, filter_to_sessions

HOL = {date(2026, 1, 15), date(2026, 1, 26), date(2026, 10, 2), date(2026, 11, 10)}   # NSE CM holidays (sample)


@pytest.fixture
def cal():
    return TradingCalendar(historical=frozenset(), holidays=frozenset(HOL), hist_end=date(2000, 1, 1))


@pytest.mark.parametrize("ts,event,entry", [
    # Case A: <= 15:30 on a session day -> same day; entry next session open
    ("2026-10-20 11:42:00", "2026-10-20", "2026-10-21"),
    ("2026-10-20 15:30:00", "2026-10-20", "2026-10-21"),       # exactly the cut-off counts as in-session
    # Case B: > 15:30 on a session day -> next session; entry the one after
    ("2026-10-20 15:30:01", "2026-10-21", "2026-10-22"),
    ("2026-10-23 19:30:00", "2026-10-26", "2026-10-27"),       # Friday evening -> Monday event, Tuesday entry
    # Case C: weekend filings
    ("2026-10-24 10:00:00", "2026-10-26", "2026-10-27"),       # Saturday <= 15:30 -> D1 Mon, entry D2 Tue
    ("2026-10-24 17:15:00", "2026-10-27", "2026-10-28"),       # Saturday  > 15:30 -> D2 Tue, entry D3 Wed
    ("2026-10-25 22:42:15", "2026-10-27", "2026-10-28"),       # Sunday night      -> D2, D3
    # holidays
    ("2026-01-15 11:00:00", "2026-01-16", "2026-01-19"),       # on a holiday, <= 15:30 -> next session
    ("2026-01-14 18:00:00", "2026-01-16", "2026-01-19"),       # after-hours before a holiday skips it
    ("2026-01-23 16:00:00", "2026-01-27", "2026-01-28"),       # Fri after-hours, Mon 26-Jan holiday
    ("2026-11-09 16:45:00", "2026-11-11", "2026-11-12"),       # after-hours into a mid-week holiday
])
def test_event_and_entry(cal, ts, event, entry):
    ev, en = event_and_entry(datetime.fromisoformat(ts), cal)
    assert (ev.isoformat(), en.isoformat()) == (event, entry)
    assert en > datetime.fromisoformat(ts).date()                # entry is always strictly after the filing date


def test_entry_is_never_the_reaction_session(cal):
    # sweep a fortnight minute-by-minute-ish: entry must be the session AFTER the event day, always
    t = datetime(2026, 10, 19, 0, 0)
    while t < datetime(2026, 11, 2):
        ev, en = event_and_entry(t, cal)
        assert cal.is_session(ev) and cal.is_session(en)
        assert en == cal.next_session(ev)
        assert ev >= t.date()
        t += timedelta(minutes=37)


def test_decision_deadline(cal):
    assert entry_decision_deadline(date(2026, 10, 27), cal) == datetime(2026, 10, 26, 15, 30)


def test_phantom_and_zero_volume_rows_rejected(cal):
    idx = pd.to_datetime(["2026-01-14", "2026-01-15", "2026-01-16", "2026-01-17", "2026-01-19"])
    df = pd.DataFrame({"Open": [1, 1, 1, 1, 1], "Close": [1, 1, 1, 1, 1], "Volume": [100, 0, 100, 50, 0]}, index=idx)
    out = filter_to_sessions(df, cal)
    assert list(out.index.strftime("%Y-%m-%d")) == ["2026-01-14", "2026-01-16"]


def test_historical_sessions_come_from_index_not_weekday_rule():
    # a validated weekend special session is honoured; a weekday absent from the index is not a session
    hist = frozenset({date(2024, 1, 19), date(2024, 1, 20), date(2024, 1, 23)})
    c = TradingCalendar(historical=hist, holidays=frozenset(), hist_end=date(2024, 1, 31))
    assert c.is_session(date(2024, 1, 20)) and not c.is_session(date(2024, 1, 22))
