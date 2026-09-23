"""D3 diagnostic: is the ~2015 step an artifact of the panel changing?
Decisive test (pre-specified): re-run the frozen cell on a CONSTANT panel of
sectors present continuously since 2006. If the step survives, D3 is ruled out.
"""
import os,sys,json,warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
sys.path.insert(0,r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import CACHE_DIR, MIN_SECTORS_PER_DATE
N,M=20,90
panel=pd.read_csv(os.path.join(CACHE_DIR,"sector_close_panel.csv"),index_col=0,parse_dates=True).sort_index()
PC=[s for s in json.load(open(os.path.join(CACHE_DIR,"panels.json")))["C"] if s in panel.columns]

print("PANEL C entry dates (first close):")
entry={}
for s in sorted(PC):
    d=panel[s].dropna().index[0]; entry[s]=d
    print(f"  {s:40s} {d.date()}")
CONST=[s for s in PC if entry[s]<=pd.Timestamp("2006-12-31")]
LATE=[s for s in PC if entry[s]>pd.Timestamp("2006-12-31")]
print(f"\nCONSTANT panel (in since <=2006): {len(CONST)} sectors")
print(f"Late entrants: {len(LATE)} -> " + ", ".join(f"{s} ({entry[s].year})" for s in sorted(LATE,key=lambda x:entry[x])))

idx=panel.index
pos=pd.Series(np.arange(len(idx)),index=idx).groupby([idx.year,idx.month]).last().values
def ret(a,i,j):
    x,y=a[i],a[j]
    return np.nan if not(np.isfinite(x) and np.isfinite(y) and x>0) else y/x-1

def run(sectors,label):
    mats={s:panel[s].to_numpy(float) for s in sectors}
    rec=[]
    for i in pos:
        if i-N<0 or i+M>=len(idx): continue
        rr=[]
        for s in sectors:
            a=mats[s]; t,f=ret(a,i-N,i),ret(a,i,i+M)
            if np.isfinite(t) and np.isfinite(f): rr.append((s,t,f))
        K=len(rr)
        if K<MIN_SECTORS_PER_DATE: continue
        t=np.array([r[1] for r in rr]); f=np.array([r[2] for r in rr])
        rs=t-t.mean(); fe=f-f.mean()
        o=np.argsort(-rs); k=K//3
        rec.append(dict(year=idx[i].year,K=K,excl=fe[o[-k:]].mean(),disp=fe.std(ddof=1),
                        excl_names="|".join(sorted(rr[j][0] for j in o[-k:]))))
    d=pd.DataFrame(rec); d["norm"]=d.excl/d.disp
    e=d[d.year<2016]; l=d[d.year>=2016]
    print(f"\n--- {label} (n={len(sectors)} sectors) ---")
    print(f"  early 2005-2015 : mean {e.excl.mean()*100:+.3f}%   norm {e.norm.mean():+.3f}   folds_neg {(e.groupby('year').excl.mean()<0).mean()*100:.1f}%")
    print(f"  late  2016-2026 : mean {l.excl.mean()*100:+.3f}%   norm {l.norm.mean():+.3f}   folds_neg {(l.groupby('year').excl.mean()<0).mean()*100:.1f}%")
    print(f"  ratio early/late: raw {e.excl.mean()/l.excl.mean():.2f}x   normalised {e.norm.mean()/l.norm.mean():.2f}x")
    d["blk"]=pd.cut(d.year,[2004,2009,2014,2019,2026],labels=["2005-09","2010-14","2015-19","2020-26"])
    g=d.groupby("blk",observed=True).agg(n=("excl","size"),medK=("K","median"),excl=("excl","mean"),norm=("norm","mean"))
    g["excl"]=(g.excl*100).round(3); g["norm"]=g.norm.round(3)
    print(g.to_string())
    return d

dC=run(PC,"PANEL C (frozen, variable composition)")
dK=run(CONST,"CONSTANT PANEL (no composition change at all)")

print("\n"+"="*78)
print("D3 TIMING CHECK")
print("="*78)
print(f"  Step observed              : ~2015 (normalised -0.150 -> -0.050)")
print(f"  First Panel C entrant after 2006: {min(entry[s] for s in LATE).date()}")
print(f"  Panel C live-sector count by year (median):")
cnt=dC.groupby("year").K.median().astype(int)
print("   "+"  ".join(f"{y}:{v}" for y,v in cnt.items()))

print("\n"+"="*78)
print("D3 IDENTITY CHECK - which sectors populate the bottom tercile, pre vs post 2015")
print("="*78)
for lab,sub in [("2005-2015",dC[dC.year<2016]),("2016-2026",dC[dC.year>=2016])]:
    from collections import Counter
    c=Counter()
    for s in sub.excl_names: c.update(s.split("|"))
    tot=len(sub)
    print(f"\n  {lab}  ({tot} rebalances) - share of rebalances each sector was EXCLUDED:")
    for nm,v in c.most_common(10): print(f"    {nm:40s} {v/tot*100:5.1f}%")
dK.to_csv(os.path.join(CACHE_DIR,"diag_constant_panel.csv"),index=False)
