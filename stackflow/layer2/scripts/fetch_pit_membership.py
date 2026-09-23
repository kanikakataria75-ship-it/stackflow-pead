"""Layer 2 - POINT-IN-TIME Nifty 500 membership + sector classification
from Wayback Machine snapshots of NSE's published constituent CSV.

This is genuine point-in-time data: each snapshot is the list as it stood on
that date, including companies later removed or delisted. It fixes BOTH
(a) survivorship in the universe and (b) look-ahead in sector classification.
"""
import os, sys, time, io, json, warnings
warnings.filterwarnings("ignore")
import requests, pandas as pd

ROOT=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2"
OUT=os.path.join(ROOT,"cache","pit"); os.makedirs(OUT,exist_ok=True)
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})

SRC=["https://www.nseindia.com/content/indices/ind_nifty500list.csv",
     "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
     "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv"]

def grab(stamp):
    fn=os.path.join(OUT,f"nifty500_{stamp}.csv")
    if os.path.exists(fn):
        try:
            d=pd.read_csv(fn)
            if len(d)>100: return d,"cached"
        except Exception: pass
    for src in SRC:
        for attempt in range(2):
            try:
                r=S.get(f"https://web.archive.org/web/{stamp}/{src}",timeout=60,allow_redirects=True)
                if r.status_code==200 and "Symbol" in r.text[:400]:
                    d=pd.read_csv(io.StringIO(r.text))
                    if len(d)>100:
                        d.to_csv(fn,index=False); return d,r.url
            except Exception:
                pass
            time.sleep(8)
    return None,None

rows=[]
for yr in range(2008,2027):
    for mm in ("0701","0101"):
        stamp=f"{yr}{mm}"
        d,src=grab(stamp)
        if d is not None:
            col=[c for c in d.columns if c.strip().lower()=="industry"]
            inds=d[col[0]].nunique() if col else 0
            rows.append(dict(stamp=stamp,n=len(d),industries=inds))
            print(f"  {stamp}: {len(d):4d} stocks, {inds:2d} industries   [{'cached' if src=='cached' else 'fetched'}]",flush=True)
            break
        time.sleep(3)
    else:
        print(f"  {yr}: no snapshot",flush=True)
    time.sleep(2)

r=pd.DataFrame(rows)
r.to_csv(os.path.join(ROOT,"cache","pit_coverage.csv"),index=False)
print(f"\nPoint-in-time snapshots obtained: {len(r)}")
if len(r): print(r.to_string(index=False))
