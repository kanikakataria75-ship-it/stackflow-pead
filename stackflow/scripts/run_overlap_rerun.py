"""
Part A step 4-6: re-run the EXACT H1 grid on non-overlapping panels.
Robustness re-run of a closed hypothesis - no new pre-registration.
Same N x M, same terciles, same month-end rebalance, same calendar-year folds.

Panel A = original 27 (H1 as reported)
Panel B = 24, constituent-containment partition (>=80% of A's members inside B)
Panel C = 23, Panel B then collapse any remaining EXCESS-return corr >= 0.75
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

sys.path.insert(0, r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import LOOKBACKS, FORWARDS, MIN_SECTORS_PER_DATE, BENCHMARK, CACHE_DIR, RESULTS_DIR
BN = BENCHMARK

panel = pd.read_csv(os.path.join(CACHE_DIR,"sector_close_panel.csv"),
                    index_col=0, parse_dates=True).sort_index()
ALL = [c for c in panel.columns if c != BN]
part = json.load(open(os.path.join(CACHE_DIR,"partition.json")))
PB = [c for c in part["kept"] if c in ALL]

C = pd.read_csv(os.path.join(CACHE_DIR,"excess_corr_matrix.csv"), index_col=0)
hist = panel[ALL].notna().sum()
PC, dropped_c = [], {}
for n in sorted(PB, key=lambda x: -hist[x]):
    hi = [k for k in PC if n in C.index and k in C.columns
          and pd.notna(C.loc[n,k]) and C.loc[n,k] >= 0.75]
    if hi: dropped_c[n] = (hi[0], float(C.loc[n,hi[0]]))
    else: PC.append(n)

PANELS = {"A_orig_27": ALL, "B_containment": PB, "C_strict": PC}
print("PANELS")
for k,v in PANELS.items(): print(f"  {k:16s} n={len(v)}")
print("  Panel C additionally dropped:",
      {k:f"{v[0]} ({v[1]:.2f})" for k,v in dropped_c.items()})

idx = panel.index
bench = panel[BN].to_numpy(float)
pos = pd.Series(np.arange(len(idx)), index=idx).groupby([idx.year, idx.month]).last().values

def ret(a,i0,i1):
    x0,x1=a[i0],a[i1]
    return np.nan if not (np.isfinite(x0) and np.isfinite(x1) and x0>0) else x1/x0-1.0

def run(sectors, N, M):
    mats={s:panel[s].to_numpy(float) for s in sectors}
    recs=[]
    for i in pos:
        if i-N<0 or i+M>=len(idx): continue
        bt,bf=ret(bench,i-N,i),ret(bench,i,i+M)
        if not (np.isfinite(bt) and np.isfinite(bf)): continue
        rr=[]
        for s in sectors:
            a=mats[s]; tr,fw=ret(a,i-N,i),ret(a,i,i+M)
            if np.isfinite(tr) and np.isfinite(fw): rr.append((tr-bt,fw-bf))
        K=len(rr)
        if K<MIN_SECTORS_PER_DATE: continue
        rr.sort(key=lambda r:-r[0]); k=K//3
        top=np.mean([x[1] for x in rr[:k]]); bot=np.mean([x[1] for x in rr[-k:]])
        mid=np.mean([x[1] for x in rr[k:K-k]]); uni=np.mean([x[1] for x in rr])
        recs.append(dict(year=idx[i].year,K=K,top=top,mid=mid,bot=bot,uni=uni,
                         spread=top-bot, top_vs_uni=top-uni, bot_vs_uni=bot-uni))
    return pd.DataFrame(recs)

rows={}
store={}
for pname, sec in PANELS.items():
    out=[]
    for N in LOOKBACKS:
        for M in FORWARDS:
            d=run(sec,N,M); store[(pname,N,M)]=d
            f=d.groupby("year")[["top","spread","top_vs_uni","bot_vs_uni"]].mean()
            out.append(dict(N=N,M=M,n=len(d),medK=int(d.K.median()),
                top=d.top.mean(), spread=d.spread.mean(),
                universe=d.uni.mean(), top_vs_uni=d.top_vs_uni.mean(),
                bot_vs_uni=d.bot_vs_uni.mean(),
                folds_top_pos=(f.top>0).mean(),
                folds_botvu_neg=(f.bot_vs_uni<0).mean(),
                bot_vs_uni_ex_worst=float(f.bot_vs_uni.drop(f.bot_vs_uni.idxmin()).mean())))
    rows[pname]=pd.DataFrame(out)

pd.set_option("display.width",260)
for pname,g in rows.items():
    d=g.copy()
    for c in ["top","spread","universe","top_vs_uni","bot_vs_uni","bot_vs_uni_ex_worst"]:
        d[c]=(d[c]*100).round(3)
    for c in ["folds_top_pos","folds_botvu_neg"]: d[c]=(d[c]*100).round(1)
    print("\n"+"="*128); print(f"PANEL {pname}  (n={len(PANELS[pname])})"); print("="*128)
    print(d.to_string(index=False))
    g.to_csv(os.path.join(RESULTS_DIR,f"overlap_grid_{pname}.csv"),index=False)

print("\n"+"="*128)
print("SIDE BY SIDE - BOTTOM tercile vs equal-weight universe mean (%), the H1 survivor")
print("="*128)
piv={k:(v.pivot(index='N',columns='M',values='bot_vs_uni')*100).round(3) for k,v in rows.items()}
for k,v in piv.items(): print(f"\n[{k}]"); print(v.to_string())
print("\nSummary of bot_vs_uni across 16 cells:")
for k,v in rows.items():
    b=v.bot_vs_uni*100
    print(f"  {k:16s} mean {b.mean():7.3f}%  min {b.min():7.3f}%  max {b.max():7.3f}%  "
          f"cells negative {int((b<0).sum())}/16  mean folds-negative {v.folds_botvu_neg.mean()*100:.1f}%")
print("\nSummary of top_vs_uni (drift-corrected top edge) across 16 cells:")
for k,v in rows.items():
    t=v.top_vs_uni*100
    print(f"  {k:16s} mean {t.mean():7.3f}%  min {t.min():7.3f}%  max {t.max():7.3f}%  "
          f"cells positive {int((t>0).sum())}/16")

REPS=[(20,20),(60,60),(20,90),(90,20),(90,90)]
print("\n"+"="*128)
print("REPRESENTATIVE CELLS - fold positivity of TOP tercile vs Nifty500 (H1 sec.3 metric)")
print("="*128)
hdr=f"{'cell':10s}" + "".join(f"{k:>18s}" for k in PANELS)
print(hdr)
for N,M in REPS:
    line=f"N{N}/M{M:<5d}"
    for k in PANELS:
        d=store[(k,N,M)]; f=d.groupby('year').top.mean()
        line+=f"{(f>0).sum():>8d}/{len(f):<9d}"
    print(line)
json.dump({k:v for k,v in {"A":ALL,"B":PB,"C":PC}.items()},
          open(os.path.join(CACHE_DIR,"panels.json"),"w"),indent=1)
