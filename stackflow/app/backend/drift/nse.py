"""NSE filing discovery — both systems.

integrated  /api/integrated-filing-results   {data,size,page,totalCount}, PAGINATED (default 20!)
legacy      /api/corporates-financial-results  bare list (mostly empty after Apr-2025)

The integrated endpoint silently caps at the page size. This client always asks for
&size=2000, pages until exhausted, and then HARD-ASSERTS rows >= totalCount. A short fetch
raises IncompleteFetchError and the scan aborts — it can never look like "a quiet day".
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
PAGE_SIZE = 2000
INTEGRATED_API = "https://www.nseindia.com/api/integrated-filing-results"
LEGACY_API = "https://www.nseindia.com/api/corporates-financial-results"
HOLIDAY_API = "https://www.nseindia.com/api/holiday-master"


class IncompleteFetchError(RuntimeError):
    """Rows received < totalCount reported by NSE. Never swallowed."""


def assert_complete(rows_received: int, total_count, where: str) -> None:
    if total_count is None:
        raise IncompleteFetchError(f"{where}: response carried no totalCount; cannot prove completeness")
    if rows_received < int(total_count):
        raise IncompleteFetchError(f"{where}: received {rows_received} rows < totalCount {total_count}")


@dataclass
class FetchAudit:
    source: str
    window: str
    pages: int = 0
    rows: int = 0
    total_count: int | None = None
    asserted: bool = False
    at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class NSEClient:
    def __init__(self, getter: Callable | None = None, pause: float = 0.8):
        """`getter(url, params) -> dict|list` may be injected for tests."""
        self._getter = getter
        self._session = None
        self.pause = pause

    # ---------------------------------------------------------------- transport
    def _sess(self, referer: str) -> requests.Session:
        if self._session is None:
            s = requests.Session()
            s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            s.get("https://www.nseindia.com/companies-listing/corporate-integrated-filing", timeout=30)
            self._session = s
        self._session.headers.update({"Accept": "application/json", "Referer": referer})
        return self._session

    def _get(self, url: str, params: dict, referer: str):
        if self._getter is not None:
            return self._getter(url, params)
        last = None
        for attempt in range(3):
            try:
                r = self._sess(referer).get(url, params=params, timeout=90)
                if r.status_code == 200:
                    return r.json()
                last = f"HTTP {r.status_code}"
            except Exception as exc:          # retried, then surfaced
                last = repr(exc)
            self._session = None
            time.sleep(3 + 3 * attempt)
        raise ConnectionError(f"NSE request failed after retries: {url} {params} ({last})")

    # ---------------------------------------------------------------- endpoints
    def integrated(self, a: date, b: date) -> tuple[list[dict], FetchAudit]:
        window = f"{a:%d-%m-%Y}..{b:%d-%m-%Y}"
        audit = FetchAudit("integrated", window)
        rows, page = [], 1
        ref = "https://www.nseindia.com/companies-listing/corporate-integrated-filing"
        while True:
            got = self._get(INTEGRATED_API, {"index": "equities", "from_date": f"{a:%d-%m-%Y}",
                                             "to_date": f"{b:%d-%m-%Y}", "size": PAGE_SIZE, "page": page}, ref)
            if not isinstance(got, dict):
                raise IncompleteFetchError(f"integrated {window}: unexpected payload type {type(got).__name__}")
            data = got.get("data") or []
            audit.total_count = got.get("totalCount", audit.total_count)
            rows.extend(data)
            audit.pages += 1
            if len(data) < PAGE_SIZE or (audit.total_count is not None and len(rows) >= int(audit.total_count)):
                break
            page += 1
            time.sleep(self.pause)
        audit.rows = len(rows)
        assert_complete(len(rows), audit.total_count, f"integrated {window}")
        audit.asserted = True
        return rows, audit

    def legacy(self, a: date, b: date, period: str = "Quarterly") -> tuple[list[dict], FetchAudit]:
        window = f"{a:%d-%m-%Y}..{b:%d-%m-%Y} {period}"
        audit = FetchAudit("legacy", window)
        ref = "https://www.nseindia.com/companies-listing/corporate-filings-financial-results"
        got = self._get(LEGACY_API, {"index": "equities", "from_date": f"{a:%d-%m-%Y}",
                                     "to_date": f"{b:%d-%m-%Y}", "period": period}, ref)
        if not isinstance(got, list):
            raise IncompleteFetchError(f"legacy {window}: expected a list, got {type(got).__name__}")
        audit.pages, audit.rows = 1, len(got)
        # The legacy endpoint returns an un-paged list with no totalCount. A result of exactly a
        # round page size would indicate a hidden cap, so that is treated as incomplete.
        if len(got) in (20, 50, 100, 500, 1000, PAGE_SIZE):
            raise IncompleteFetchError(f"legacy {window}: {len(got)} rows looks like a silent page cap")
        audit.asserted = True
        return got, audit

    def holidays(self) -> dict:
        return self._get(HOLIDAY_API, {"type": "trading"}, "https://www.nseindia.com/resources/exchange-communication-holidays")
