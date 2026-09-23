"""Layer 3 - fetch announcement-dated reported EPS history.
This is the ONLY fundamental series available with real announcement dates,
which is what removes reporting-lag look-ahead. Isolated cache: layer3/cache/.
Reads Layer 2's universe file READ-ONLY; does not modify Layer 1 or Layer 2.
"""
import os,sys,glob,time,warnings; warnings.filterwarnings("ignore")
import pandas as pd, yfinance as yf
L2=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2/cache"
ROOT=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer3"
OUT=os.path.join(ROOT,"cache","earnings"); os.makedirs(OUT,exist_ok=True)

IND={'FINANCIAL SERVICES','CONSUMER GOODS','INDUSTRIAL MANUFACTURING','PHARMA','AUTOMOBILE',
     'CONSTRUCTION','SERVICES','IT','METALS','CHEMICALS','OIL & GAS','CEMENT & CEMENT PRODUCTS',
     'POWER','FERTILISERS & PESTICIDES','MEDIA & ENTERTAINMENT','HEALTHCARE SERVICES','TELECOM'}
u=pd.read_csv(os.path.join(L2,"pit_universe_2020.csv"))
u["Industry"]=u.Industry.str.strip().str.upper()
u=u[u.Industry.isin(IND)]
have={os.path.basename(f)[:-4] for f in glob.glob(os.path.join(L2,"stocks","*.csv"))}
def key(s): return str(s).replace("&","and").replace("/","_")
syms=[s for s in u.Symbol if key(s) in have]
print(f"universe with prices: {len(syms)}",flush=True)

done=0; miss=[]
for i,s in enumerate(syms,1):
    fn=os.path.join(OUT,key(s)+".csv")
    if os.path.exists(fn): done+=1; continue
    ed=None
    for a in range(2):
        try: ed=yf.Ticker(str(s)+".NS").earnings_dates
        except Exception: ed=None
        if ed is not None and len(ed)>0: break
        time.sleep(2)
    if ed is None or len(ed)==0:
        miss.append(s); continue
    col=[c for c in ed.columns if "Reported" in c]
    if not col: miss.append(s); continue
    d=ed[[col[0]]].copy(); d.columns=["reported_eps"]
    d.index=pd.to_datetime(d.index).tz_localize(None).normalize()
    d=d.dropna().sort_index()
    if len(d)<6: miss.append(s); continue
    d.to_csv(fn); done+=1
    if i%40==0: print(f"  ...{i}/{len(syms)} ok={done}",flush=True)
    time.sleep(0.5)
print(f"\nwith usable reported-EPS history: {done}/{len(syms)}")
print(f"missing/insufficient: {len(miss)}")
pd.Series(miss,name="symbol").to_csv(os.path.join(ROOT,"cache","earnings_missing.csv"),index=False)
