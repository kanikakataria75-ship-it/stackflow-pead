"""PEAD prices - full XBRL universe, from 2018 so 2019 events have prior history."""
import os, time, warnings
warnings.filterwarnings("ignore")
import pandas as pd, yfinance as yf
ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/pead"
PX = os.path.join(ROOT, "cache", "px"); os.makedirs(PX, exist_ok=True)
XB = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl/cache"
e = pd.read_csv(os.path.join(XB, "extract_universe.csv"))
syms = sorted(set(e.symbol.astype(str)))
need = [s for s in syms if not os.path.exists(os.path.join(PX, s.replace("&","and").replace("/","_")+".csv"))]
print("universe=%d  to fetch=%d" % (len(syms), len(need)), flush=True)
ok = 0
for i, s in enumerate(need, 1):
    fn = os.path.join(PX, s.replace("&","and").replace("/","_")+".csv")
    try:
        h = yf.Ticker(s+".NS").history(start="2018-01-01", interval="1d", auto_adjust=True)
    except Exception:
        h = None
    if h is not None and len(h) > 300:
        d = h[["Open","Close","Volume"]].dropna()
        d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
        d[~d.index.duplicated(keep="last")].sort_index().to_csv(fn); ok += 1
    if i % 60 == 0: print("  ...%d/%d ok=%d" % (i, len(need), ok), flush=True)
    time.sleep(0.2)
print("fetched %d / %d" % (ok, len(need)))
