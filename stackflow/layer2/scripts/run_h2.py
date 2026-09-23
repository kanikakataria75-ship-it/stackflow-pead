"""StackFlow Layer 2 - H2 / H2b grid test.
Executes exactly the procedure frozen in layer2/pre_registration.md.

PRIMARY  : universe fixed at 2020-07-25, window 2020-08 onward  -> CLEAN
SECONDARY: same universe, pre-2020-07 window                    -> CONTAMINATED (labelled)
"""
import os,sys,json,glob,warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

ROOT=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2"
L1=r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
RES=os.path.join(ROOT,"results"); os.makedirs(RES,exist_ok=True)
LOOKBACKS=[20,60,120,250]; FORWARDS=[20,60,120]
MIN_STOCKS=30
PIT_CUT=pd.Timestamp("2020-07-25")
_RNG=np.random.default_rng(7)

def perm_p(vals, side):
    """One-sided permutation p that the MEAN of fold values differs from 0,
    by sign-flipping fold units (autocorrelation-safe: folds are the units)."""
    v=np.asarray([x for x in vals if np.isfinite(x)],dtype=float)
    if len(v)<4: return np.nan
    obs=v.mean(); n=len(v); N=20000
    flips=_RNG.choice([-1.0,1.0],size=(N,n))
    dist=(flips*np.abs(v)).mean(axis=1)
    return float((dist<=obs).mean()) if side=="neg" else float((dist>=obs).mean())

IND2SEC={
 "FINANCIAL SERVICES":["NIFTY BANK","NIFTY PSU BANK","NIFTY NBFC","NIFTY HOUSING FINANCE","NIFTY INSURANCE"],
 "CONSUMER GOODS":["NIFTY FMCG","NIFTY CONSUMER DURABLES"],
 "INDUSTRIAL MANUFACTURING":["NIFTY CAPITAL GOODS"],
 "PHARMA":["NIFTY HEALTHCARE"],
 "AUTOMOBILE":["NIFTY AUTO"],
 "CONSTRUCTION":["NIFTY CONSTRUCTION","NIFTY REALTY"],
 "SERVICES":["NIFTY COMMERCIAL & TRANSPORT SERVICES","NIFTY CONSUMER SERVICES"],
 "IT":["NIFTY IT"],
 "METALS":["NIFTY METAL"],
 "CHEMICALS":["NIFTY CHEMICALS"],
 "OIL & GAS":["NIFTY OIL & GAS"],
 "CEMENT & CEMENT PRODUCTS":["NIFTY CEMENT"],
 "POWER":["NIFTY POWER"],
 "FERTILISERS & PESTICIDES":["NIFTY CHEMICALS"],
 "MEDIA & ENTERTAINMENT":["NIFTY MEDIA"],
 "HEALTHCARE SERVICES":["NIFTY HOSPITALS"],
 "TELECOM":["NIFTY TELECOMMUNICATIONS"],
}

def load():
    U=pd.read_csv(os.path.join(ROOT,"cache","pit_universe_2020.csv"))
    U["Industry"]=U.Industry.str.strip().str.upper()
    U=U[U.Industry.isin(IND2SEC)]
    px={}
    for f in glob.glob(os.path.join(ROOT,"cache","stocks","*.csv")):
        sym=os.path.basename(f)[:-4]
        try:
            s=pd.read_csv(f,index_col=0,parse_dates=True).iloc[:,0]
            if len(s)>=250: px[sym]=s
        except Exception: pass
    keep=[s for s in U.Symbol if str(s).replace("&","and").replace("/","_") in px]
    panel=pd.DataFrame({s:px[str(s).replace("&","and").replace("/","_")] for s in keep}).sort_index()
    ind=dict(zip(U.Symbol,U.Industry))
    L1p=pd.read_csv(os.path.join(ROOT,"cache","layer1_passthrough_pit.csv"),parse_dates=["date"])
    bench=pd.read_csv(os.path.join(L1,"sector_close_panel.csv"),index_col=0,parse_dates=True)["NIFTY 500"].dropna()
    return panel,ind,L1p,bench,U

def industry_passes(passed_set):
    out={}
    for ind,secs in IND2SEC.items():
        ok=sum(1 for s in secs if s in passed_set)
        out[ind]= ok*2>=len(secs)     # strict majority, ties -> PASS
    return out

def reversal_years(bench):
    yrs={}
    for y,g in bench.groupby(bench.index.year):
        if len(g)<100: continue
        w=bench[(bench.index>=pd.Timestamp(y,1,1)-pd.Timedelta(days=183))&(bench.index<=g.index[-1])]
        dd=(w/w.cummax()-1).min()
        yrs[y]= (dd<=-0.15) and (g.iloc[-1]/g.iloc[0]-1>=0.10)
    return sorted(k for k,v in yrs.items() if v)

def main():
    panel,ind,L1p,bench,U=load()
    print(f"Universe (2020 PIT, mappable): {len(U)} names;  with price data: {panel.shape[1]}")
    print(f"  MISSING price data: {len(U)-panel.shape[1]}")
    print(f"Panel span: {panel.index[0].date()} -> {panel.index[-1].date()}")
    RY=reversal_years(bench); print(f"REVERSAL YEARS (pre-registered rule): {RY}")

    idx=panel.index
    bs=bench.reindex(idx).ffill().to_numpy(float)
    mats={s:panel[s].to_numpy(float) for s in panel.columns}
    ipos={d.date():i for i,d in enumerate(idx)}
    L1map={r.date.date():set(str(r.passed).split("|")) for _,r in L1p.iterrows()}

    def ret(a,i,j):
        x,y=a[i],a[j]
        return np.nan if not (np.isfinite(x) and np.isfinite(y) and x>0) else y/x-1

    rows={}; store={}
    for N in LOOKBACKS:
        for M in FORWARDS:
            recs=[]
            for d,passed in sorted(L1map.items()):
                if d not in ipos: continue
                i=ipos[d]
                if i-N<0 or i+M>=len(idx): continue
                ip=industry_passes(passed)
                cand=[]
                for s in panel.columns:
                    if not ip.get(ind.get(s,""),False): continue
                    a=mats[s]; t,f=ret(a,i-N,i),ret(a,i,i+M)
                    if np.isfinite(t) and np.isfinite(f): cand.append((t,f))
                K=len(cand)
                if K<MIN_STOCKS: continue
                t=np.array([c[0] for c in cand]); f=np.array([c[1] for c in cand])
                bt,bf=ret(bs,i-N,i),ret(bs,i,i+M)
                rs=t-t.mean()                       # rank baseline = universe mean
                feU=f-f.mean()                      # forward vs FILTERED UNIVERSE  (primary)
                feB=f-bf                            # forward vs NIFTY 500          (continuity)
                o=np.argsort(-rs); k=K//3
                top,bot,mid=o[:k],o[-k:],o[k:K-k]
                recs.append(dict(date=pd.Timestamp(d),year=pd.Timestamp(d).year,K=K,
                    topU=feU[top].mean(),midU=feU[mid].mean(),botU=feU[bot].mean(),
                    topB=feB[top].mean(),botB=feB[bot].mean(),
                    disp=feU.std(ddof=1)))
            df=pd.DataFrame(recs); store[(N,M)]=df
            if len(df)==0: continue
            for tag,sub in [("CLEAN",df[df.date>PIT_CUT]),("CONTAM",df[df.date<=PIT_CUT])]:
                if len(sub)<6: continue
                fo=sub.groupby("year")[["topU","botU","topB"]].mean()
                rows[(N,M,tag)]=dict(N=N,M=M,win=tag,n=len(sub),folds=len(fo),medK=int(sub.K.median()),
                    topU=sub.topU.mean(),midU=sub.midU.mean(),botU=sub.botU.mean(),
                    topB=sub.topB.mean(),botB=sub.botB.mean(),
                    spreadU=sub.topU.mean()-sub.botU.mean(),
                    disp=sub.disp.mean(),
                    topU_norm=sub.topU.mean()/sub.disp.mean(),
                    botU_norm=sub.botU.mean()/sub.disp.mean(),
                    f_topU_pos=(fo.topU>0).mean(), f_botU_neg=(fo.botU<0).mean(),
                    topU_exbest=float(fo.topU.drop(fo.topU.idxmax()).mean()),
                    botU_exworst=float(fo.botU.drop(fo.botU.idxmin()).mean()),
                    monotonic=bool(sub.topU.mean()>sub.midU.mean()>sub.botU.mean()),
                    topU_exRY=sub[~sub.year.isin(RY)].topU.mean(),
                    botU_exRY=sub[~sub.year.isin(RY)].botU.mean(),
                    topU_foldmean=float(fo.topU.mean()), botU_foldmean=float(fo.botU.mean()),
                    p_top=perm_p(fo.topU.values,"pos"), p_bot=perm_p(fo.botU.values,"neg"))
    g=pd.DataFrame(rows.values())
    g.to_csv(os.path.join(RES,"h2_grid_summary.csv"),index=False)
    for (N,M),df in store.items():
        if len(df): df.to_csv(os.path.join(RES,f"h2_cell_N{N}_M{M}.csv"),index=False)
    json.dump({"reversal_years":RY,"universe":int(panel.shape[1])},open(os.path.join(RES,"h2_meta.json"),"w"))

    pd.set_option("display.width",280)
    for tag in ["CLEAN","CONTAM"]:
        d=g[g.win==tag].copy()
        if not len(d): continue
        for c in ["topU","midU","botU","topB","botB","spreadU","disp","topU_exbest","botU_exworst","topU_exRY","botU_exRY"]:
            d[c]=(d[c]*100).round(3)
        for c in ["f_topU_pos","f_botU_neg"]: d[c]=(d[c]*100).round(1)
        for c in ["topU_norm","botU_norm"]: d[c]=d[c].round(3)
        print("\n"+"="*140); print(f"{tag} WINDOW  ({'PRIMARY - point-in-time clean' if tag=='CLEAN' else 'SECONDARY - CONTAMINATED, not used for verdict'})"); print("="*140)
        print(d.drop(columns=["win"]).to_string(index=False))
    print("\nSTORE cells:",len(store))

if __name__=="__main__": main()
