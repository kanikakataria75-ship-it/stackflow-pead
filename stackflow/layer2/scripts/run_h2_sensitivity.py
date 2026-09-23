"""Pre-registered sensitivity: assign stocks to Panel C sectors by ACTUAL sectoral-index
membership (current lists) instead of the industry->sector majority-rule mapping.
Contaminated by present-day membership, but definitionally faithful. Reported regardless."""
import os,sys,json,glob,warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
sys.path.insert(0,r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2/scripts")
from run_h2 import load, LOOKBACKS, FORWARDS, MIN_STOCKS, PIT_CUT, perm_p, reversal_years, ROOT, RES

L1=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
memb=json.load(open(os.path.join(ROOT,"cache","panelC_stock_membership.json")))["membership"]
cons=json.load(open(os.path.join(L1,"constituents.json")))
sizes={k:len(v) for k,v in cons.items()}
# tie-break: most specific (smallest) sector
assign={s:min(v,key=lambda x:sizes.get(x,999)) for s,v in memb.items()}

panel,ind,L1p,bench,U=load()
RY=reversal_years(bench)
cols=[c for c in panel.columns if c in assign]
print(f"Sensitivity universe (stocks in an actual Panel C sectoral index, with prices): {len(cols)}")
panel=panel[cols]
idx=panel.index; bs=bench.reindex(idx).ffill().to_numpy(float)
mats={s:panel[s].to_numpy(float) for s in cols}
ipos={d.date():i for i,d in enumerate(idx)}
L1map={r.date.date():set(str(r.passed).split("|")) for _,r in L1p.iterrows()}
def ret(a,i,j):
    x,y=a[i],a[j]
    return np.nan if not(np.isfinite(x) and np.isfinite(y) and x>0) else y/x-1
rows=[]
for N in LOOKBACKS:
    for M in FORWARDS:
        recs=[]
        for d,passed in sorted(L1map.items()):
            if d not in ipos: continue
            i=ipos[d]
            if i-N<0 or i+M>=len(idx): continue
            cand=[]
            for s in cols:
                if assign[s] not in passed: continue
                a=mats[s]; t,f=ret(a,i-N,i),ret(a,i,i+M)
                if np.isfinite(t) and np.isfinite(f): cand.append((t,f))
            K=len(cand)
            if K<MIN_STOCKS: continue
            t=np.array([c[0] for c in cand]); f=np.array([c[1] for c in cand])
            rs=t-t.mean(); fe=f-f.mean()
            o=np.argsort(-rs); k=K//3
            recs.append(dict(date=pd.Timestamp(d),year=pd.Timestamp(d).year,K=K,
                topU=fe[o[:k]].mean(),botU=fe[o[-k:]].mean(),disp=fe.std(ddof=1)))
        df=pd.DataFrame(recs)
        sub=df[df.date>PIT_CUT] if len(df) else df
        if len(sub)<6: continue
        fo=sub.groupby("year")[["topU","botU"]].mean()
        rows.append(dict(N=N,M=M,n=len(sub),folds=len(fo),medK=int(sub.K.median()),
            topU=sub.topU.mean()*100, botU=sub.botU.mean()*100,
            topU_norm=sub.topU.mean()/sub.disp.mean(), botU_norm=sub.botU.mean()/sub.disp.mean(),
            f_topU_pos=(fo.topU>0).mean()*100, f_botU_neg=(fo.botU<0).mean()*100,
            topU_exbest=fo.topU.drop(fo.topU.idxmax()).mean()*100,
            botU_exworst=fo.botU.drop(fo.botU.idxmin()).mean()*100,
            p_top=perm_p(fo.topU.values,"pos"), p_bot=perm_p(fo.botU.values,"neg")))
g=pd.DataFrame(rows)
for c in ["topU","botU","topU_exbest","botU_exworst"]: g[c]=g[c].round(3)
for c in ["topU_norm","botU_norm"]: g[c]=g[c].round(3)
pd.set_option("display.width",250)
print("\nSENSITIVITY - CLEAN window, membership-based sector assignment")
print(g.to_string(index=False))
g.to_csv(os.path.join(RES,"h2_sensitivity_membership.csv"),index=False)
print(f"\ncells topU>0: {(g.topU>0).sum()}/{len(g)}   cells botU<0: {(g.botU<0).sum()}/{len(g)}")
print(f"cells topU>0 after dropping best fold: {(g.topU_exbest>0).sum()}/{len(g)}")
print(f"cells botU<0 after dropping worst fold: {(g.botU_exworst<0).sum()}/{len(g)}")
print(f"min p_top={g.p_top.min():.3f}  min p_bot={g.p_bot.min():.3f}")
