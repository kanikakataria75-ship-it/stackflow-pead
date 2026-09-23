"""Step 2.1 - Filing discovery.

Enumerates ALL NSE financial-results filings (quarterly + annual) from 2019-01-01
onward via the bulk API, and caches the full index.

Design notes:
- The API is keyed by FILING-DATE window across ALL companies, not by company. So one
  pass over windows builds the index for every symbol at once - this is the same work
  Step 2.4 needs, so it is done once here rather than per-company.
- ALL rows are stored, including both Consolidated and Non-Consolidated, and including
  any duplicate (symbol, period) filings. The consolidated preference (D1) and the
  restatement check (D5) are applied downstream, NOT here - discovery must not discard
  evidence those steps need.
- Rows whose xbrl field is the literal placeholder '-' are kept but flagged, so the
  2017/18-style gap stays visible instead of silently vanishing.
"""
import os
import re
import sys
import time
import json
import warnings

warnings.filterwarnings("ignore")
import pandas as pd
import requests

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl"
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)
INDEX = os.path.join(CACHE, "filing_index.csv")

START_YEAR = 2019
API = "https://www.nseindia.com/api/corporates-financial-results"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                      "Accept-Language": "en-US,en;q=0.9",
                      "Connection": "keep-alive"})
    s.get("https://www.nseindia.com/", timeout=30)
    s.get("https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
          timeout=30)
    s.headers.update({"Accept": "application/json",
                      "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results"})
    return s


def windows(start_year, end):
    """Filing-date windows, one calendar quarter each."""
    out = []
    y, q = start_year, 1
    while True:
        m0 = 3 * (q - 1) + 1
        a = pd.Timestamp(y, m0, 1)
        b = (a + pd.offsets.QuarterEnd(0)).normalize()
        if a > end:
            break
        out.append((a, min(b, end)))
        q += 1
        if q > 4:
            q, y = 1, y + 1
    return out


def taxonomy(url):
    if not url or not url.endswith(".xml"):
        return ""
    m = re.match(r"^([A-Z_]+?)_\d", url.split("/")[-1])
    return m.group(1) if m else "?"


def fetch(s, a, b, period, tries=3):
    p = {"index": "equities", "from_date": a.strftime("%d-%m-%Y"),
         "to_date": b.strftime("%d-%m-%Y"), "period": period}
    for t in range(tries):
        try:
            r = s.get(API, params=p, timeout=120)
            if r.status_code == 200 and r.text.strip().startswith("["):
                return r.json()
        except Exception:
            pass
        time.sleep(5 + 5 * t)
        try:
            s = session()
        except Exception:
            pass
    return None


def main():
    end = pd.Timestamp("2026-09-30")
    s = session()
    rows = []
    fails = []
    for period in ("Quarterly", "Annual"):
        for a, b in windows(START_YEAR, end):
            j = fetch(s, a, b, period)
            if j is None:
                fails.append((period, str(a.date()), str(b.date())))
                print("  FAIL %s %s..%s" % (period, a.date(), b.date()), flush=True)
                continue
            for x in j:
                url = x.get("xbrl") or ""
                rows.append(dict(
                    symbol=x.get("symbol"), company=x.get("companyName"),
                    period=x.get("period"), relating_to=x.get("relatingTo"),
                    from_date=x.get("fromDate"), to_date=x.get("toDate"),
                    filing_date=x.get("filingDate"),
                    broadcast=x.get("broadCastDate"), disseminated=x.get("exchdisstime"),
                    basis=x.get("consolidated"), audited=x.get("audited"),
                    ind_as=x.get("indAs"), isin=x.get("isin"), seq=x.get("seqNumber"),
                    xbrl=url, taxonomy=taxonomy(url),
                    has_xml=bool(url.endswith(".xml"))))
            print("  %-9s %s..%s  rows=%d" % (period, a.date(), b.date(), len(j)), flush=True)
            time.sleep(1.2)

    d = pd.DataFrame(rows)
    before = len(d)
    d = d.drop_duplicates(subset=["symbol", "period", "from_date", "to_date",
                                  "basis", "filing_date", "seq"])
    d.to_csv(INDEX, index=False)
    print("\nrows fetched=%d  after dedupe=%d  windows failed=%d" % (before, len(d), len(fails)))
    if fails:
        json.dump(fails, open(os.path.join(CACHE, "discovery_failed_windows.json"), "w"), indent=1)
    print("index written: %s" % INDEX)


if __name__ == "__main__":
    main()
