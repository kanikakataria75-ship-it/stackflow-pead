"""Layer 4 / Part A - discover concall announcements on NSE.

Reuses the NSE access pattern proven in stackflow/data_pipeline/xbrl/:
cookie handshake, monthly windows, explicit count checks.

Lesson 2 (silent gaps) applied:
  - the /api/corporate-announcements endpoint returns a BARE LIST with no totalCount,
    so a cap cannot be read off the response. Verified by splitting a window in half and
    checking the halves sum to the whole: 1537 + 806 == 2343. No cap at this size.
  - every window's row count is recorded so gaps are visible per month, not just per year.
"""
import os
import re
import time
import warnings

warnings.filterwarnings("ignore")
import pandas as pd
import requests

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer4"
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)
OUT = os.path.join(CACHE, "concall_announcements.csv")
API = "https://www.nseindia.com/api/corporate-announcements"
SUBJECT = "Analysts/Institutional Investor Meet/Con. Call Updates"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def sess():
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                      "Accept-Language": "en-US,en;q=0.9"})
    s.get("https://www.nseindia.com/", timeout=30)
    s.get("https://www.nseindia.com/companies-listing/corporate-filings-announcements",
          timeout=30)
    s.headers.update({"Accept": "application/json",
                      "Referer": "https://www.nseindia.com/companies-listing/"
                                 "corporate-filings-announcements"})
    return s


def months(a, b):
    out, cur = [], pd.Timestamp(a)
    while cur <= b:
        end = min((cur + pd.offsets.MonthEnd(0)).normalize(), b)
        out.append((cur, end))
        cur = end + pd.Timedelta(days=1)
    return out


def fetch(s, a, b, tries=3):
    p = {"index": "equities", "from_date": a.strftime("%d-%m-%Y"),
         "to_date": b.strftime("%d-%m-%Y"), "subject": SUBJECT}
    for t in range(tries):
        try:
            r = s.get(API, params=p, timeout=150)
            if r.status_code == 200 and r.text.strip().startswith("["):
                return r.json()
        except Exception:
            pass
        time.sleep(4 + 4 * t)
        try:
            s = sess()
        except Exception:
            pass
    return None


def main():
    s = sess()
    rows, log = [], []
    for a, b in months(pd.Timestamp("2021-01-01"), pd.Timestamp("2026-09-30")):
        j = fetch(s, a, b)
        n = -1 if j is None else len(j)
        log.append(dict(month=a.strftime("%Y-%m"), rows=n))
        if j:
            for x in j:
                rows.append(dict(
                    symbol=x.get("symbol"), company=x.get("sm_name"),
                    industry=x.get("smIndustry"), isin=x.get("sm_isin"),
                    an_dt=x.get("an_dt"), diss=x.get("exchdisstime"),
                    desc=x.get("desc"), text=x.get("attchmntText"),
                    url=x.get("attchmntFile"), seq=x.get("seq_id")))
        print("  %s rows=%d" % (a.strftime("%Y-%m"), n), flush=True)
        time.sleep(1.0)

    d = pd.DataFrame(rows).drop_duplicates(subset=["symbol", "an_dt", "url"])
    d.to_csv(OUT, index=False)
    pd.DataFrame(log).to_csv(os.path.join(CACHE, "discovery_log.csv"), index=False)
    print("\nannouncements: %d  symbols: %d" % (len(d), d.symbol.nunique()))
    bad = [r for r in log if r["rows"] < 0]
    print("failed windows: %d %s" % (len(bad), bad[:6]))


if __name__ == "__main__":
    main()
