"""Fetch prices for the 2020-07-25 point-in-time Nifty 500 universe.
Includes names that later delisted - those are exactly the cases H2b is about,
so any that cannot be retrieved are COUNTED and REPORTED, never silently dropped."""
import os,sys,time,warnings; warnings.filterwarnings("ignore")
import pandas as pd, yfinance as yf
ROOT=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2"
RAW=os.path.join(ROOT,"cache","stocks"); os.makedirs(RAW,exist_ok=True)
U=pd.read_csv(os.path.join(ROOT,"cache","pit_universe_2020.csv"))
MIN=250
rep=[]
todo=[]
for sym in U.Symbol:
    fn=os.path.join(RAW,str(sym).replace("&","and").replace("/","_")+".csv")
    if os.path.exists(fn):
        try:
            s=pd.read_csv(fn,index_col=0,parse_dates=True).iloc[:,0]
            if len(s)>=MIN:
                rep.append(dict(symbol=sym,n=len(s),start=str(s.index[0].date()),end=str(s.index[-1].date()))); continue
        except Exception: pass
    todo.append(sym)
print(f"cached already: {len(rep)}   to fetch: {len(todo)}",flush=True)
for i,sym in enumerate(todo,1):
    fn=os.path.join(RAW,str(sym).replace("&","and").replace("/","_")+".csv")
    got=None
    for a in range(2):
        try: h=yf.Ticker(str(sym)+".NS").history(period="max",interval="1d",auto_adjust=True)
        except Exception: h=None
        if h is not None and len(h)>=MIN and "Close" in h.columns:
            s=h["Close"].dropna(); s.index=pd.to_datetime(s.index).tz_localize(None).normalize()
            s=s[~s.index.duplicated(keep="last")].sort_index(); s.name=sym
            s.to_frame().to_csv(fn); got=s; break
        time.sleep(3)
    rep.append(dict(symbol=sym,n=len(got) if got is not None else 0,
                    start=str(got.index[0].date()) if got is not None else "",
                    end=str(got.index[-1].date()) if got is not None else ""))
    if i%50==0: print(f"  ...{i}/{len(todo)}",flush=True)
    time.sleep(0.4)
r=pd.DataFrame(rep); r.to_csv(os.path.join(ROOT,"cache","pit_stock_coverage.csv"),index=False)
ok=r[r.n>=MIN]
print(f"\n2020 PIT universe: {len(r)} names")
print(f"  retrieved     : {len(ok)}")
print(f"  MISSING       : {len(r)-len(ok)}  <-- reported, not hidden")
print(f"  with data covering 2020-08 onward: {(ok.end>='2026-01-01').sum()} still trading recently")
print(f"  delisted/stale (last close < 2026-01-01): {(ok.end<'2026-01-01').sum()}")
print("\nMissing:", ", ".join(map(str,r[r.n<MIN].symbol.tolist()))[:800])
