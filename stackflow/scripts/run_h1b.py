"""
StackFlow H1b - sector EXCLUSION filter.
Executes exactly the procedure frozen in pre_registration_h1b.md.

Panel   : C (23-sector strict non-overlapping, from Part A)
Ranking : trailing RS vs EQUAL-WEIGHT SECTOR UNIVERSE mean (not Nifty 500)
Forward : excess vs EQUAL-WEIGHT SECTOR UNIVERSE mean (not Nifty 500)
Output  : BINARY - excluded (bottom tercile) vs passed-through (everything else)
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

sys.path.insert(0, r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import (LOOKBACKS, FORWARDS, MIN_SECTORS_PER_DATE, BENCHMARK,
                     CACHE_DIR, RESULTS_DIR, sanity_check_units)
BN = BENCHMARK

panel = pd.read_csv(os.path.join(CACHE_DIR,"sector_close_panel.csv"),
                    index_col=0, parse_dates=True).sort_index()
PC = json.load(open(os.path.join(CACHE_DIR,"panels.json")))["C"]
SEC = [c for c in PC if c in panel.columns]
idx = panel.index
bench = panel[BN].to_numpy(float)
mats = {s: panel[s].to_numpy(float) for s in SEC}
pos = pd.Series(np.arange(len(idx)), index=idx).groupby([idx.year, idx.month]).last().values

def ret(a,i0,i1):
    x0,x1=a[i0],a[i1]
    return np.nan if not (np.isfinite(x0) and np.isfinite(x1) and x0>0) else x1/x0-1.0

def cell(N,M):
    recs=[]
    for i in pos:
        if i-N<0 or i+M>=len(idx): continue
        rows=[]
        for s in SEC:
            a=mats[s]; tr,fw=ret(a,i-N,i),ret(a,i,i+M)
            if np.isfinite(tr) and np.isfinite(fw): rows.append([s,tr,fw])
        K=len(rows)
        if K<MIN_SECTORS_PER_DATE: continue
        tr=np.array([r[1] for r in rows]); fw=np.array([r[2] for r in rows])
        U_tr, U_fw = tr.mean(), fw.mean()          # equal-weight universe baselines
        rs = tr - U_tr                              # ranking baseline = UNIVERSE
        order=np.argsort(-rs); k=K//3
        exc = order[-k:]                            # EXCLUDED  = bottom tercile
        pss = order[:K-k]                           # PASSED THROUGH = the rest
        bnr = ret(bench,i,i+M)
        recs.append(dict(date=idx[i], year=idx[i].year, K=K,
            excluded  = float(fw[exc].mean()-U_fw),
            passed    = float(fw[pss].mean()-U_fw),
            excl_raw_vs_n500 = float(fw[exc].mean()-bnr),
            pass_raw_vs_n500 = float(fw[pss].mean()-bnr),
            universe_vs_n500 = float(U_fw-bnr)))
    return pd.DataFrame(recs)

def main():
    sanity_check_units()
    print(f"\nH1b PANEL C: {len(SEC)} sectors")
    print(f"Ranking baseline : equal-weight sector universe mean")
    print(f"Forward baseline : equal-weight sector universe mean\n")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows={}; store={}
    for N in LOOKBACKS:
        for M in FORWARDS:
            d=cell(N,M); store[(N,M)]=d
            f=d.groupby("year")[["excluded","passed"]].mean()
            ex_worst=f.excluded.drop(f.excluded.idxmin())
            rows[(N,M)]=dict(N=N,M=M,n=len(d),medK=int(d.K.median()),
                excluded=d.excluded.mean(), passed=d.passed.mean(),
                gap=d.passed.mean()-d.excluded.mean(),
                excl_raw=d.excl_raw_vs_n500.mean(),
                univ_drift=d.universe_vs_n500.mean(),
                folds=len(f),
                folds_excl_neg=(f.excluded<0).mean(),
                excl_ex_worst=float(ex_worst.mean()),
                obs_hit=(d.excluded<0).mean())
            d.to_csv(os.path.join(RESULTS_DIR,f"h1b_cell_N{N}_M{M}.csv"),index=False)
    g=pd.DataFrame(rows.values())
    g.to_csv(os.path.join(RESULTS_DIR,"h1b_grid_summary.csv"),index=False)
    disp=g.copy()
    for c in ["excluded","passed","gap","excl_raw","univ_drift","excl_ex_worst"]:
        disp[c]=(disp[c]*100).round(3)
    for c in ["folds_excl_neg","obs_hit"]: disp[c]=(disp[c]*100).round(1)
    pd.set_option("display.width",260)
    print("="*132)
    print("H1b FULL GRID - all 16 cells. 'excluded'/'passed' are vs EQUAL-WEIGHT UNIVERSE (%)")
    print("="*132)
    print(disp.to_string(index=False))
    print("\nEXCLUDED bucket vs universe (%)  [negative = filter works]")
    print((g.pivot(index='N',columns='M',values='excluded')*100).round(3).to_string())
    print("\nfolds with excluded<0 (%)  [pre-registered bar = 65%]")
    print((g.pivot(index='N',columns='M',values='folds_excl_neg')*100).round(1).to_string())
    print("\nEXCLUDED vs universe, dropping single worst fold (%)  [KB2]")
    print((g.pivot(index='N',columns='M',values='excl_ex_worst')*100).round(3).to_string())
    print("\nPASSED-THROUGH bucket vs universe (%)")
    print((g.pivot(index='N',columns='M',values='passed')*100).round(3).to_string())

    e=g.excluded*100; fn=g.folds_excl_neg*100
    print("\n--- ADJUDICATION INPUTS ---")
    print(f"cells with excluded<0            : {int((e<0).sum())}/16")
    print(f"mean excluded vs universe        : {e.mean():.3f}%")
    print(f"mean folds-negative              : {fn.mean():.1f}%   (bar 65%)")
    print(f"cells meeting >=65% folds-neg    : {int((fn>=65).sum())}/16")
    print(f"cells still negative ex-worst-fold: {int((g.excl_ex_worst<0).sum())}/16")

    for c in [(20,20),(60,60),(20,90),(90,90),(90,20)]:
        d=store[c]; f=d.groupby('year').agg(n=('excluded','size'),
            excluded=('excluded','mean'), passed=('passed','mean'))
        ff=f.copy(); ff['excluded']=(ff.excluded*100).round(2); ff['passed']=(ff.passed*100).round(2)
        print("\n"+"="*80); print(f"H1b FOLD-BY-FOLD  N={c[0]} M={c[1]}  [%]"); print("="*80)
        print(ff.to_string())
        print(f"  folds excluded<0: {(f.excluded<0).sum()}/{len(f)} ({(f.excluded<0).mean()*100:.1f}%)")
        f.to_csv(os.path.join(RESULTS_DIR,f"h1b_folds_N{c[0]}_M{c[1]}.csv"))

if __name__=="__main__":
    main()
