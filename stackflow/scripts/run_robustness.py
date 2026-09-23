"""
StackFlow Layer 1 - post-hoc robustness checks.
Declared as POST-HOC: these were run AFTER seeing the main grid. They are
reported regardless of whether they help or hurt H1.

R1 UNIVERSE-DRIFT CONFOUND (the important one): if the equal-weight mean of ALL
   sectors already beats Nifty 500, then every bucket is lifted by that drift
   and the top bucket's raw number overstates the actual rank edge. The honest
   signal is (top - universe_mean), not (top - 0).
R2 TOP vs MIDDLE separation, explicitly.
R3 2006+ subsample (first year with a full >=20 sector cross-section).
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

sys.path.insert(0, r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import LOOKBACKS, FORWARDS, MIN_SECTORS_PER_DATE, BENCHMARK, CACHE_DIR, RESULTS_DIR
BN = BENCHMARK

panel = pd.read_csv(os.path.join(CACHE_DIR, "sector_close_panel.csv"),
                    index_col=0, parse_dates=True).sort_index()
sect = [c for c in panel.columns if c != BN]
idx = panel.index
bench = panel[BN].to_numpy(float)
mats = {s: panel[s].to_numpy(float) for s in sect}
pos = pd.Series(np.arange(len(idx)), index=idx).groupby([idx.year, idx.month]).last().values

def ret(a, i0, i1):
    x0, x1 = a[i0], a[i1]
    return np.nan if not (np.isfinite(x0) and np.isfinite(x1) and x0 > 0) else x1/x0 - 1.0

rows = []
for N in LOOKBACKS:
    for M in FORWARDS:
        recs = []
        for i in pos:
            if i-N < 0 or i+M >= len(idx): continue
            bt, bf = ret(bench,i-N,i), ret(bench,i,i+M)
            if not (np.isfinite(bt) and np.isfinite(bf)): continue
            rr=[]
            for s in sect:
                a=mats[s]; tr, fw = ret(a,i-N,i), ret(a,i,i+M)
                if np.isfinite(tr) and np.isfinite(fw): rr.append((tr-bt, fw-bf))
            K=len(rr)
            if K < MIN_SECTORS_PER_DATE: continue
            rr.sort(key=lambda r:-r[0]); k=K//3
            top=np.mean([x[1] for x in rr[:k]]); bot=np.mean([x[1] for x in rr[-k:]])
            mid=np.mean([x[1] for x in rr[k:K-k]]); uni=np.mean([x[1] for x in rr])
            recs.append(dict(year=idx[i].year, top=top, mid=mid, bot=bot, uni=uni))
        d=pd.DataFrame(recs)
        d2=d[d.year>=2006]
        rows.append(dict(N=N, M=M,
            universe=d.uni.mean(), top=d.top.mean(),
            top_vs_uni=d.top.mean()-d.uni.mean(),
            top_minus_mid=d.top.mean()-d['mid'].mean(),
            mid_vs_uni=d['mid'].mean()-d.uni.mean(),
            bot_vs_uni=d.bot.mean()-d.uni.mean(),
            top_vs_uni_2006=d2.top.mean()-d2.uni.mean(),
            folds_tvu_pos=float((d.groupby('year').apply(lambda g: g.top.mean()-g.uni.mean())>0).mean())))

g=pd.DataFrame(rows)
for c in ['universe','top','top_vs_uni','top_minus_mid','mid_vs_uni','bot_vs_uni','top_vs_uni_2006']:
    g[c]=(g[c]*100).round(3)
g['folds_tvu_pos']=(g['folds_tvu_pos']*100).round(1)
pd.set_option('display.width',250)
print("="*120)
print("R1/R2/R3  (all figures %, forward excess vs NIFTY 500 unless '_vs_uni')")
print("  universe   = equal-weight ALL sectors' forward excess vs Nifty 500  <-- the confound")
print("  top_vs_uni = top tercile MINUS universe mean  <-- the real rank edge")
print("="*120)
print(g.to_string(index=False))
g.to_csv(os.path.join(RESULTS_DIR,'robustness.csv'),index=False)
print("\nMean universe drift across 16 cells: %.3f%%" % g.universe.mean())
print("Mean top_vs_uni across 16 cells    : %.3f%%" % g.top_vs_uni.mean())
print("Cells where top_vs_uni > 0         : %d/16" % (g.top_vs_uni>0).sum())
print("Cells where top_minus_mid > 0      : %d/16" % (g.top_minus_mid>0).sum())
