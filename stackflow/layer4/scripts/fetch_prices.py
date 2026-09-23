"""Layer 4 - daily OHLCV for the transcript universe (need volume for the turnover filter)."""
import os, sys, time, warnings
warnings.filterwarnings("ignore")
import pandas as pd, yfinance as yf
ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer4"
PX = os.path.join(ROOT, "cache", "px"); os.makedirs(PX, exist_ok=True)
c = pd.read_csv(os.path.join(ROOT, "cache", "transcript_candidates.csv"))
syms = sorted(set(c.symbol.astype(str)))
print("symbols:", len(syms), flush=True)
done = 0; miss = []
for i, s in enumerate(syms, 1):
    fn = os.path.join(PX, s.replace("&", "and").replace("/", "_") + ".csv")
    if os.path.exists(fn) and os.path.getsize(fn) > 800:
        done += 1; continue
    got = None
    for a in range(2):
        try:
            h = yf.Ticker(s + ".NS").history(start="2020-06-01", interval="1d", auto_adjust=True)
        except Exception:
            h = None
        if h is not None and len(h) > 200 and "Close" in h.columns:
            d = h[["Open", "Close", "Volume"]].dropna()
            d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
            d = d[~d.index.duplicated(keep="last")].sort_index()
            d.to_csv(fn); got = d; break
        time.sleep(2)
    if got is None: miss.append(s)
    else: done += 1
    if i % 100 == 0: print("  ...%d/%d ok=%d" % (i, len(syms), done), flush=True)
    time.sleep(0.25)
print("\nwith prices: %d / %d   missing: %d" % (done, len(syms), len(miss)))
pd.Series(miss, name="symbol").to_csv(os.path.join(ROOT, "cache", "px_missing.csv"), index=False)
