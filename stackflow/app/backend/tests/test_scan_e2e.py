"""End-to-end scan against a simulated NSE feed, parser and price source (research history is
the real, read-only extract). Exercises: discovery -> SUE -> ex-ante quintile -> timing ->
filters -> frozen allocation -> append-only record -> realised fills only when prices exist."""
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from drift import scanner, settings, xbrl
from drift.calendar import TradingCalendar
from drift.nse import NSEClient
from drift.prices import PriceStore

HOL = frozenset({date(2026, 10, 2), date(2026, 10, 20), date(2026, 11, 10), date(2026, 11, 24), date(2026, 12, 25)})
CAL = TradingCalendar(historical=frozenset(), holidays=HOL, hist_end=date(2026, 9, 18))


def filing(sym, name, broadcast, qe="30-SEP-2026", basis="Consolidated", sub="Original"):
    return {"symbol": sym, "cmName": name, "type": "Integrated Filing- Financials", "type_Sub": sub,
            "qe_Date": qe, "broadcast_Date": broadcast, "creation_Date": broadcast, "revised_Date": None,
            "consolidated": basis, "xbrl": f"https://nsearchives.nseindia.com/corporate/xbrl/INTEGRATED_FILING_INDAS_{sym}_1_WEB.xml"}


FEED = [
    filing("TITAN", "Titan Company Limited", "21-Oct-2026 16:40:00"),      # huge beat -> Q5 candidate
    filing("PIDILITIND", "Pidilite Industries Limited", "21-Oct-2026 11:05:00"),
    filing("HDFCBANK", "HDFC Bank Limited", "21-Oct-2026 17:10:00"),      # financial -> excluded
    filing("TCS", "Tata Consultancy Services Limited", None),             # not yet broadcast -> pending
]
PAT = {"TITAN": 4.0e10, "PIDILITIND": 5.0e9, "HDFCBANK": 4.0e11, "TCS": 1.4e11}


class FakeNSE(NSEClient):
    def __init__(self, feed):
        super().__init__(getter=self._g, pause=0)
        self.feed = feed

    def _g(self, url, params):
        if "integrated" in url:
            return {"data": self.feed if params["page"] == 1 else [], "totalCount": len(self.feed)}
        return []

    def holidays(self):
        return {"CM": []}


def fake_prices(ticker, start):
    idx = [pd.Timestamp(d) for d in pd.bdate_range(start, "2027-03-31") if CAL.is_session(d.date())]
    n = len(idx)
    base = 3000.0 if "TITAN" in ticker else 900.0
    close = base * np.exp(np.linspace(0, 0.08, n))
    df = pd.DataFrame({"Open": close * 0.999, "Close": close, "Volume": 250_000.0}, index=pd.DatetimeIndex(idx))
    return df, "INR"


def px_until(cutoff):
    def f(ticker, start):
        df, cur = fake_prices(ticker, start)
        return df[df.index <= pd.Timestamp(cutoff)], cur
    return f


@pytest.fixture(autouse=True)
def fake_parser(monkeypatch):
    monkeypatch.setattr(xbrl, "parse_quarterly", lambda url, pe: ({"pat": PAT[url.split("_")[-3]]}, None))
    monkeypatch.setattr(scanner, "build_calendar", lambda fetch=None: (CAL, {"validated": True}))


def test_full_lifecycle():
    t1 = datetime(2026, 10, 21, 18, 30)
    rep = scanner.run_scan(client=FakeNSE(FEED), prices=PriceStore(CAL, fetcher=px_until(t1.date()), max_age_hours=0),
                           cal=CAL, scan_time=t1)
    assert rep["ok"], rep
    log = scanner.scan_ledger().rows().set_index("symbol")
    assert "TCS" not in log.index                                   # pending broadcast: not recorded yet
    assert log.loc["HDFCBANK", "is_fin"] == "True"
    # PIDILITIND filed 11:05 on the 21st (session) -> event 21st, entry 22nd; TITAN 16:40 -> event 22nd, entry 23rd
    assert (log.loc["PIDILITIND", "event_day"], log.loc["PIDILITIND", "planned_entry"]) == ("2026-10-21", "2026-10-22")
    assert (log.loc["TITAN", "event_day"], log.loc["TITAN", "planned_entry"]) == ("2026-10-22", "2026-10-23")
    for sym in log.index:                                           # thresholds never used a later filing
        assert float(log.loc[sym, "hist_events"]) >= 150
    assert log.loc["TITAN", "quintile"] == "5"
    # entry 23rd: same-day peers can still arrive until 22nd 15:30, so tonight it can only be QUEUED
    assert (log.loc["TITAN", "decision"], log.loc["TITAN", "reason"]) == ("QUEUED", "AWAITING_SAME_DAY_PEERS")
    # PIDILITIND (entry 22nd): its peer window closed at 21st 15:30 -> final decision tonight
    assert log.loc["PIDILITIND", "decision"] in ("ENTER", "NO_SIGNAL", "REJECTED")

    # next evening's scan: the 23rd's candidate set is closed -> TITAN is allocated
    t15 = datetime(2026, 10, 22, 18, 30)
    rep15 = scanner.run_scan(client=FakeNSE(FEED), prices=PriceStore(CAL, fetcher=px_until(t15.date()), max_age_hours=0),
                             cal=CAL, scan_time=t15)
    assert rep15["ok"], rep15
    st = scanner.latest_state(scanner.forward_ledger().rows()).set_index("symbol")
    assert st.loc["TITAN", "status"] == "ENTER" and st.loc["TITAN", "entry_date"] == "2026-10-23"
    assert st.loc["TITAN", "exit_date"] == CAL.add_sessions(date(2026, 10, 23), 60).isoformat()
    fwd = scanner.forward_ledger().rows()
    assert list(fwd[fwd.symbol == "TITAN"].status) == ["QUEUED", "ENTER"]    # history kept, nothing edited
    assert set(fwd.symbol) <= {"TITAN", "PIDILITIND", "HDFCBANK"}
    if "HDFCBANK" in set(fwd.symbol):
        assert fwd[fwd.symbol == "HDFCBANK"].skip_reason.iloc[-1] == "FINANCIAL_SECTOR"

    # later scan: TITAN entry open now exists -> OPEN (price filter checked at the real open)
    t2 = datetime(2026, 10, 26, 18, 30)
    rep2 = scanner.run_scan(client=FakeNSE([]), prices=PriceStore(CAL, fetcher=px_until(t2.date()), max_age_hours=0),
                            cal=CAL, scan_time=t2)
    assert rep2["ok"] and rep2["fills"]["opened"] >= 1
    st = scanner.latest_state(scanner.forward_ledger().rows()).set_index("symbol")
    assert st.loc["TITAN", "status"] == "OPEN" and float(st.loc["TITAN", "entry_price"]) > 50

    # far later: the exit close exists -> CLOSED with net = gross - 0.585%
    t3 = datetime(2027, 1, 29, 18, 30)
    rep3 = scanner.run_scan(client=FakeNSE([]), prices=PriceStore(CAL, fetcher=px_until(t3.date()), max_age_hours=0),
                            cal=CAL, scan_time=t3)
    assert rep3["ok"], rep3
    st = scanner.latest_state(scanner.forward_ledger().rows()).set_index("symbol")
    r = st.loc["TITAN"]
    assert r.status == "CLOSED"
    assert abs(float(r.net_return) - (float(r.gross_return) - 0.00585)) < 1e-12
    assert int(r.holding_sessions) == 60
    assert scanner.forward_ledger().verify()["ok"]


def test_nothing_is_recorded_before_the_freeze(monkeypatch):
    old = [filing("TITAN", "Titan", "22-Sep-2026 12:00:00", qe="31-DEC-2026")]
    rep = scanner.run_scan(client=FakeNSE(old), prices=PriceStore(CAL, fetcher=fake_prices, max_age_hours=0),
                           cal=CAL, scan_time=datetime(2026, 9, 23, 18, 30))
    assert rep["ok"]
    assert not (scanner.scan_ledger().rows().period_end == "2026-12-31").any()
