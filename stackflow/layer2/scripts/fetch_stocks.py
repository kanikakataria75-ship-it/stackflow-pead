"""Layer 2 - stock price fetcher. Isolated cache: stackflow/layer2/cache/stocks/.
Does not touch Layer 1 files or LeadFlow."""
import os, sys, json, time, warnings
warnings.filterwarnings("ignore")
import pandas as pd, yfinance as yf

ROOT=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2"
RAW=os.path.join(ROOT,"cache","stocks"); os.makedirs(RAW,exist_ok=True)
U=json.load(open(os.path.join(ROOT,"cache","panelC_stock_membership.json")))["union"]
MIN_ROWS=250

done=rep=[]
rep=[]
for i,sym in enumerate(U,1):
    fn=os.path.join(RAW,sym.replace("&","and").replace("/","_")+".csv")
    if os.path.exists(fn):
        try:
            s=pd.read_csv(fn,index_col=0,parse_dates=True).iloc[:,0]
            if len(s)>=MIN_ROWS:
                rep.append(dict(symbol=sym,n=len(s),start=str(s.index[0].date()),end=str(s.index[-1].date())))
                continue
        except Exception: pass
    got=None
    for a in range(2):
        try:
            h=yf.Ticker(sym+".NS").history(period="max",interval="1d",auto_adjust=True)
        except Exception:
            h=None
        if h is not None and len(h)>=MIN_ROWS and "Close" in h.columns:
            s=h["Close"].dropna()
            s.index=pd.to_datetime(s.index).tz_localize(None).normalize()
            s=s[~s.index.duplicated(keep="last")].sort_index(); s.name=sym
            s.to_frame().to_csv(fn); got=s; break
        time.sleep(3)
    if got is None:
        rep.append(dict(symbol=sym,n=0,start="",end=""))
    else:
        rep.append(dict(symbol=sym,n=len(got),start=str(got.index[0].date()),end=str(got.index[-1].date())))
    if i%40==0: print(f"  ...{i}/{len(U)}",flush=True)
    time.sleep(0.4)

r=pd.DataFrame(rep)
r.to_csv(os.path.join(ROOT,"cache","stock_coverage.csv"),index=False)
ok=r[r.n>=MIN_ROWS]
print(f"\nStocks requested : {len(r)}")
print(f"Stocks retrieved : {len(ok)}   missing: {len(r)-len(ok)}")
print(f"Median history   : {int(ok.n.median())} rows")
print(f"With data from <=2006-01-01: {(ok.start<='2006-01-01').sum()}")
print(f"With data from <=2010-01-01: {(ok.start<='2010-01-01').sum()}")
print(f"With data from <=2015-01-01: {(ok.start<='2015-01-01').sum()}")
print("\nMissing symbols:", ", ".join(r[r.n<MIN_ROWS].symbol.tolist())[:600])
