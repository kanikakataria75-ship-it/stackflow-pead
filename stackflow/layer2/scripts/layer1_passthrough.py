"""Reproduces the FROZEN Layer 1 filter point-in-time.
Reads Layer 1's cached sector index levels READ-ONLY. Writes only into layer2/cache/.
Frozen config (live_config_layer1.md): Panel C, N=20, M=90, month-end, bottom tercile
excluded, ranking baseline = equal-weight sector universe mean, min 9 sectors.
NOTE: only closes <= t are used to decide t's exclusion, so this is genuinely
point-in-time. M is irrelevant to the DECISION (it only scored the outcome).
"""
import os, json, numpy as np, pandas as pd
L1=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
L2=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2/cache"
N=20; MIN_SECTORS=9
panel=pd.read_csv(os.path.join(L1,"sector_close_panel.csv"),index_col=0,parse_dates=True).sort_index()
PC=[s for s in json.load(open(os.path.join(L1,"panels.json")))["C"] if s in panel.columns]
idx=panel.index
mats={s:panel[s].to_numpy(float) for s in PC}
pos=pd.Series(np.arange(len(idx)),index=idx).groupby([idx.year,idx.month]).last().values
def ret(a,i,j):
    x,y=a[i],a[j]
    return np.nan if not(np.isfinite(x) and np.isfinite(y) and x>0) else y/x-1
rows=[]
for i in pos:
    if i-N<0: continue
    live=[(s,ret(mats[s],i-N,i)) for s in PC]
    live=[(s,v) for s,v in live if np.isfinite(v)]
    K=len(live)
    if K<MIN_SECTORS: continue
    tr=np.array([v for _,v in live]); rs=tr-tr.mean()
    o=np.argsort(-rs); k=K//3
    exc=sorted(live[j][0] for j in o[-k:]); pas=sorted(live[j][0] for j in o[:K-k])
    rows.append(dict(date=idx[i].date(),K=K,n_excluded=k,
                     excluded="|".join(exc),passed="|".join(pas)))
d=pd.DataFrame(rows)
d.to_csv(os.path.join(L2,"layer1_passthrough_pit.csv"),index=False)
print(f"Layer 1 point-in-time pass-through: {len(d)} month-end dates")
print(f"  {d.date.min()} -> {d.date.max()}")
print(f"  median sectors live={int(d.K.median())}, median excluded={int(d.n_excluded.median())}")
print("\nMost recent 3 decisions:")
for _,r in d.tail(3).iterrows():
    print(f"  {r.date}  EXCLUDED({r.n_excluded}): {r.excluded}")
