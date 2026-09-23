"""Step 2.1b - Integrated Filing discovery (the 2025+ gap).

WHY THIS EXISTS
The legacy /api/corporates-financial-results endpoint stops carrying most filings from
~April 2025, when SEBI's Integrated Filing regime began. Measured on the legacy index:
quarterly rows fall 14,329 (2024) -> 3,960 (2025) -> 28 (2026); annual 3,558 -> 55 -> 7.
Without this second source the pipeline would silently lose the most recent ~1.5 years.

DIFFERENCES FROM THE LEGACY ENDPOINT
- different path: /api/integrated-filing-results
- response is {data, size, page, totalCount} - NOT a bare list
- PAGINATED. Default size is 20; &size=2000 is accepted. Ignoring this returns exactly
  20 rows per window, which looks like real (low) coverage rather than a cap.
- carries `type` (Financials vs Governance) and `type_Sub` (Original / New / Revision).
  Revision is a first-class restatement marker and is preserved for Step 2.3 (D5).
"""
import os
import re
import time
import warnings

warnings.filterwarnings("ignore")
import pandas as pd
import requests

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl"
CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(CACHE, "filing_index_integrated.csv")
API = "https://www.nseindia.com/api/integrated-filing-results"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
PAGE = 2000


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                      "Accept-Language": "en-US,en;q=0.9"})
    s.get("https://www.nseindia.com/", timeout=30)
    s.get("https://www.nseindia.com/companies-listing/corporate-integrated-filing", timeout=30)
    s.headers.update({"Accept": "application/json",
                      "Referer": "https://www.nseindia.com/companies-listing/corporate-integrated-filing"})
    return s


def taxonomy(url):
    if not url or not url.endswith(".xml"):
        return ""
    m = re.match(r"^([A-Z_]+?)_\d", url.split("/")[-1])
    return m.group(1) if m else "?"


def month_windows(a, b):
    out, cur = [], pd.Timestamp(a)
    while cur <= b:
        end = min((cur + pd.offsets.MonthEnd(0)).normalize(), b)
        out.append((cur, end))
        cur = end + pd.Timedelta(days=1)
    return out


def fetch_all(s, a, b):
    """Fetch every page for one window. Returns (rows, expected_total)."""
    rows, total, page = [], None, 1
    while True:
        p = {"index": "equities", "from_date": a.strftime("%d-%m-%Y"),
             "to_date": b.strftime("%d-%m-%Y"), "size": PAGE, "page": page}
        got = None
        for t in range(3):
            try:
                r = s.get(API, params=p, timeout=120)
                if r.status_code == 200 and r.text.strip().startswith("{"):
                    got = r.json()
                    break
            except Exception:
                pass
            time.sleep(4 + 4 * t)
        if got is None:
            return rows, total
        d = got.get("data") or []
        total = got.get("totalCount", total)
        rows.extend(d)
        if len(d) < PAGE or (total is not None and len(rows) >= total):
            return rows, total
        page += 1
        time.sleep(0.8)


def main():
    s = session()
    a0, b0 = pd.Timestamp("2025-01-01"), pd.Timestamp("2026-09-30")
    out, short = [], []
    for a, b in month_windows(a0, b0):
        rows, total = fetch_all(s, a, b)
        if total is not None and len(rows) < total:
            short.append((str(a.date()), len(rows), total))
        for x in rows:
            url = x.get("xbrl") or ""
            out.append(dict(
                symbol=x.get("symbol"), company=x.get("cmName"),
                filing_type=x.get("type"), type_sub=x.get("type_Sub"),
                qe_date=x.get("qe_Date"),
                broadcast=x.get("broadcast_Date"), creation=x.get("creation_Date"),
                revised_date=x.get("revised_Date"), revision_remark=x.get("revision_Remark"),
                basis=x.get("consolidated"), audited=x.get("audited"),
                seq=x.get("seq_Id"), xbrl=url, ixbrl=x.get("ixbrl"),
                taxonomy=taxonomy(url), has_xml=bool(url.endswith(".xml"))))
        print("  %s..%s  rows=%d  totalCount=%s" % (a.date(), b.date(), len(rows), total),
              flush=True)
        time.sleep(1.0)

    d = pd.DataFrame(out)
    d = d.drop_duplicates(subset=["symbol", "qe_date", "basis", "broadcast", "seq"])
    d.to_csv(OUT, index=False)
    print("\nrows=%d  windows short of totalCount=%d" % (len(d), len(short)))
    if short:
        print("  SHORT:", short[:10])
    print(d.filing_type.value_counts().to_string())
    print()
    print(d.type_sub.value_counts().to_string())
    print("written:", OUT)


if __name__ == "__main__":
    main()
