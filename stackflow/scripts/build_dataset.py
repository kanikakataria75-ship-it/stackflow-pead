"""
StackFlow Layer 1 - dataset builder.
Source: niftyindices.com (NSE Indices Ltd) official published index levels.
Caches into stackflow/cache/ ONLY. Nothing is read from or written to LeadFlow.

Look-ahead discipline: stores raw daily closes only. No forward-looking
transform. Published index levels already embed point-in-time constituents.
"""
import os, sys, json, time, warnings
warnings.filterwarnings("ignore")
import pandas as pd
import requests

sys.path.insert(0, r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import SECTORS, BENCHMARK, CACHE_DIR, sanity_check_units

URL = "https://niftyindices.com/BackPage/getHistoricaldatatabletoString"
RAW = os.path.join(CACHE_DIR, "raw")
os.makedirs(RAW, exist_ok=True)
START, END = "01-Jan-1990", "21-Sep-2026"
MIN_ROWS = 500


def session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://niftyindices.com/reports/historical-data",
        "Origin": "https://niftyindices.com"})
    s.get("https://niftyindices.com/reports/historical-data", timeout=30)
    return s


def fetch(s, name, tries=3):
    fn = os.path.join(RAW, name.replace(" ", "_").replace("&", "and") + ".csv")
    if os.path.exists(fn):
        ser = pd.read_csv(fn, index_col=0, parse_dates=True).iloc[:, 0]
        if len(ser) >= MIN_ROWS:
            return ser
    body = {"cinfo": json.dumps({"name": name, "startDate": START,
                                 "endDate": END, "indexName": name})}
    for a in range(tries):
        try:
            r = s.post(URL, json=body, timeout=90)
            d = r.json()
        except Exception:
            d = None
        if isinstance(d, list) and len(d) >= MIN_ROWS:
            df = pd.DataFrame(d)
            df["date"] = pd.to_datetime(df["HistoricalDate"], format="%d %b %Y")
            df["close"] = pd.to_numeric(df["CLOSE"].astype(str).str.replace(",", ""),
                                        errors="coerce")
            ser = (df.dropna(subset=["close"]).set_index("date")["close"]
                     .sort_index())
            ser = ser[~ser.index.duplicated(keep="last")]
            ser.name = name
            ser.to_frame().to_csv(fn)
            return ser
        time.sleep(4 + 4 * a)
    return None


def main():
    sanity_check_units()
    s = session()
    report, series = [], {}

    bench = fetch(s, BENCHMARK)
    if bench is None:
        print("FATAL: benchmark unavailable."); sys.exit(1)
    report.append(dict(name=BENCHMARK, role="benchmark", n=len(bench),
                       start=str(bench.index[0].date()), end=str(bench.index[-1].date())))
    print(f"\n  {BENCHMARK:40s} {len(bench):6d}  {bench.index[0].date()} -> {bench.index[-1].date()}")

    for nm in SECTORS:
        ser = fetch(s, nm)
        if ser is None:
            report.append(dict(name=nm, role="sector", n=0, start="", end=""))
            print(f"  {nm:40s} {'UNAVAILABLE':>6s}")
        else:
            series[nm] = ser
            report.append(dict(name=nm, role="sector", n=len(ser),
                               start=str(ser.index[0].date()), end=str(ser.index[-1].date())))
            print(f"  {nm:40s} {len(ser):6d}  {ser.index[0].date()} -> {ser.index[-1].date()}",
                  flush=True)
        time.sleep(1.0)

    panel = pd.DataFrame(series)
    panel[BENCHMARK] = bench
    panel = panel.sort_index()
    # keep only days the benchmark traded (NSE trading calendar)
    panel = panel[panel[BENCHMARK].notna()]
    panel.to_csv(os.path.join(CACHE_DIR, "sector_close_panel.csv"))

    rep = pd.DataFrame(report).sort_values("n", ascending=False)
    rep.to_csv(os.path.join(CACHE_DIR, "coverage_report.csv"), index=False)
    pd.set_option("display.width", 200); pd.set_option("display.max_rows", 100)
    print("\n--- COVERAGE REPORT (sorted by history length) ---")
    print(rep.to_string(index=False))
    print(f"\nPanel shape: {panel.shape}   {panel.index[0].date()} -> {panel.index[-1].date()}")

    # how many sectors are live per year -> drives the >=9 tercile requirement
    cnt = panel[[c for c in panel.columns if c != BENCHMARK]].notna().sum(axis=1)
    per_year = cnt.groupby(cnt.index.year).median().astype(int)
    print("\nMedian sectors with data, per calendar year:")
    print(per_year.to_string())


if __name__ == "__main__":
    main()
