"""StackFlow Layer 3 - H3 / H3-inv, factor 1 (YoY EPS growth).
Executes exactly the procedure frozen in layer3/pre_registration.md.
Universe = Layer 1 pass-through (point-in-time). NOT any Layer 2 output.
Signal usable only from its ACTUAL announcement date -> no reporting-lag look-ahead.
"""
import os, sys, glob, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

L1 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
L2 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2/cache"
ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer3"
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)
FORWARDS = [60, 90, 120, 180]
MIN_STOCKS = 30
MAX_STALE = 200          # calendar days; older announcement is dropped as stale
_RNG = np.random.default_rng(11)

IND2SEC = {
    "FINANCIAL SERVICES": ["NIFTY BANK", "NIFTY PSU BANK", "NIFTY NBFC",
                           "NIFTY HOUSING FINANCE", "NIFTY INSURANCE"],
    "CONSUMER GOODS": ["NIFTY FMCG", "NIFTY CONSUMER DURABLES"],
    "INDUSTRIAL MANUFACTURING": ["NIFTY CAPITAL GOODS"],
    "PHARMA": ["NIFTY HEALTHCARE"],
    "AUTOMOBILE": ["NIFTY AUTO"],
    "CONSTRUCTION": ["NIFTY CONSTRUCTION", "NIFTY REALTY"],
    "SERVICES": ["NIFTY COMMERCIAL & TRANSPORT SERVICES", "NIFTY CONSUMER SERVICES"],
    "IT": ["NIFTY IT"],
    "METALS": ["NIFTY METAL"],
    "CHEMICALS": ["NIFTY CHEMICALS"],
    "OIL & GAS": ["NIFTY OIL & GAS"],
    "CEMENT & CEMENT PRODUCTS": ["NIFTY CEMENT"],
    "POWER": ["NIFTY POWER"],
    "FERTILISERS & PESTICIDES": ["NIFTY CHEMICALS"],
    "MEDIA & ENTERTAINMENT": ["NIFTY MEDIA"],
    "HEALTHCARE SERVICES": ["NIFTY HOSPITALS"],
    "TELECOM": ["NIFTY TELECOMMUNICATIONS"],
}


def key(s):
    return str(s).replace("&", "and").replace("/", "_")


def perm_p(vals, side):
    v = np.asarray([x for x in vals if np.isfinite(x)], float)
    if len(v) < 3:
        return np.nan
    obs = v.mean()
    N = 20000
    dist = (_RNG.choice([-1.0, 1.0], size=(N, len(v))) * np.abs(v)).mean(axis=1)
    return float((dist <= obs).mean()) if side == "neg" else float((dist >= obs).mean())


def industry_passes(passed):
    return {i: (sum(1 for s in secs if s in passed) * 2 >= len(secs))
            for i, secs in IND2SEC.items()}


def main():
    u = pd.read_csv(os.path.join(L2, "pit_universe_2020.csv"))
    u["Industry"] = u.Industry.str.strip().str.upper()
    u = u[u.Industry.isin(IND2SEC)]
    ind = dict(zip(u.Symbol, u.Industry))

    eps = {}
    for f in glob.glob(os.path.join(ROOT, "cache", "earnings", "*.csv")):
        s = os.path.basename(f)[:-4]
        try:
            d = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0].dropna().sort_index()
            d = d[~d.index.duplicated(keep="last")]
            if len(d) >= 6:
                eps[s] = d
        except Exception:
            pass

    px = {}
    for sym in u.Symbol:
        f = os.path.join(L2, "stocks", key(sym) + ".csv")
        if os.path.exists(f) and key(sym) in eps:
            try:
                s = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0].dropna()
                if len(s) >= 250:
                    px[sym] = s
            except Exception:
                pass
    panel = pd.DataFrame(px).sort_index()
    print("Universe with BOTH prices and EPS history: %d" % panel.shape[1])

    sig = {}
    dropped_neg = 0
    total = 0
    for sym in panel.columns:
        e = eps[key(sym)]
        vals = {}
        for i in range(4, len(e)):
            base = e.iloc[i - 4]
            cur = e.iloc[i]
            total += 1
            if not np.isfinite(base) or not np.isfinite(cur) or base <= 0:
                dropped_neg += 1
                continue
            vals[e.index[i]] = cur / base - 1.0
        if vals:
            sig[sym] = pd.Series(vals).sort_index()
    print("YoY observations: %d usable, %d dropped (base EPS <= 0)" % (total - dropped_neg, dropped_neg))
    spans = [s.index.min() for s in sig.values() if len(s)]
    if spans:
        print("signal start (median first announcement): %s" % pd.Series(spans).median().date())

    bench = pd.read_csv(os.path.join(L1, "sector_close_panel.csv"),
                        index_col=0, parse_dates=True)["NIFTY 500"].dropna()
    L1p = pd.read_csv(os.path.join(L2, "layer1_passthrough_pit.csv"), parse_dates=["date"])
    L1map = {r.date: set(str(r.passed).split("|")) for _, r in L1p.iterrows()}

    idx = panel.index
    bs = bench.reindex(idx).ffill().to_numpy(float)
    mats = {s: panel[s].to_numpy(float) for s in panel.columns}

    l1dates = sorted(L1map)
    qd = {}
    for d in l1dates:
        qd[(d.year, (d.month - 1) // 3)] = d      # last Layer-1 decision in each quarter
    rebal = sorted(qd.values())
    ipos = {d: i for i, d in enumerate(idx)}

    def near(d):
        c = idx[idx <= d]
        return ipos[c[-1]] if len(c) else None

    def ret(a, i, j):
        x, y = a[i], a[j]
        return np.nan if not (np.isfinite(x) and np.isfinite(y) and x > 0) else y / x - 1

    rows = []
    store = {}
    stale_tot = 0
    stale_drop = 0
    for M in FORWARDS:
        recs = []
        for d in rebal:
            i = near(d)
            if i is None or i + M >= len(idx):
                continue
            ip = industry_passes(L1map[d])
            vals = []
            fwd = []
            for s in panel.columns:
                if not ip.get(ind.get(s, ""), False):
                    continue
                if s not in sig:
                    continue
                ss = sig[s]
                ss = ss[ss.index <= d]
                if len(ss) == 0:
                    continue
                stale_tot += 1
                if (d - ss.index[-1]).days > MAX_STALE:
                    stale_drop += 1
                    continue
                f = ret(mats[s], i, i + M)
                if not np.isfinite(f):
                    continue
                vals.append(ss.iloc[-1])
                fwd.append(f)
            K = len(vals)
            if K < MIN_STOCKS:
                continue
            v = np.array(vals)
            f = np.array(fwd)
            lo, hi = np.percentile(v, [1, 99])
            v = np.clip(v, lo, hi)
            feU = f - f.mean()
            bf = ret(bs, i, i + M)
            o = np.argsort(-v)
            k = K // 3
            recs.append(dict(date=d, year=d.year, K=K,
                             strongU=feU[o[:k]].mean(),
                             midU=feU[o[k:K - k]].mean(),
                             weakU=feU[o[-k:]].mean(),
                             strongB=(f[o[:k]].mean() - bf),
                             weakB=(f[o[-k:]].mean() - bf),
                             disp=feU.std(ddof=1)))
        df = pd.DataFrame(recs)
        store[M] = df
        if len(df) < 4:
            continue
        fo = df.groupby("year")[["strongU", "weakU"]].mean()
        rows.append(dict(M=M, n=len(df), folds=len(fo), medK=int(df.K.median()),
                         strongU=df.strongU.mean(), midU=df.midU.mean(), weakU=df.weakU.mean(),
                         spread=df.strongU.mean() - df.weakU.mean(),
                         strongB=df.strongB.mean(), weakB=df.weakB.mean(),
                         disp=df.disp.mean(),
                         strongU_norm=df.strongU.mean() / df.disp.mean(),
                         weakU_norm=df.weakU.mean() / df.disp.mean(),
                         f_weak_neg=(fo.weakU < 0).mean(),
                         f_strong_pos=(fo.strongU > 0).mean(),
                         weakU_exworst=float(fo.weakU.drop(fo.weakU.idxmin()).mean()),
                         strongU_exbest=float(fo.strongU.drop(fo.strongU.idxmax()).mean()),
                         monotonic=bool(df.strongU.mean() > df.midU.mean() > df.weakU.mean()),
                         p_weak=perm_p(fo.weakU.values, "neg"),
                         p_strong=perm_p(fo.strongU.values, "pos")))
        df.to_csv(os.path.join(RES, "h3_f1_cell_M%d.csv" % M), index=False)

    print("stale-signal drops: %d/%d (%.1f%%)" % (stale_drop, stale_tot,
                                                  stale_drop / max(stale_tot, 1) * 100))
    g = pd.DataFrame(rows)
    if len(g) == 0:
        print("NO GRID CELLS PRODUCED - universe too small at this point "
              "(need >= %d stocks per rebalance). Not a result." % MIN_STOCKS)
        return
    g.to_csv(os.path.join(RES, "h3_f1_grid.csv"), index=False)
    pd.set_option("display.width", 250)
    d = g.copy()
    for c in ["strongU", "midU", "weakU", "spread", "strongB", "weakB", "disp",
              "weakU_exworst", "strongU_exbest"]:
        d[c] = (d[c] * 100).round(3)
    for c in ["f_weak_neg", "f_strong_pos"]:
        d[c] = (d[c] * 100).round(1)
    for c in ["strongU_norm", "weakU_norm"]:
        d[c] = d[c].round(3)
    print("\n" + "=" * 150)
    print("FACTOR 1 - YoY EPS GROWTH.  strongU/weakU = forward excess vs EQUAL-WEIGHT FILTERED UNIVERSE (%)")
    print("=" * 150)
    print(d.to_string(index=False))
    for M, df in store.items():
        if len(df) >= 4:
            fo = df.groupby("year").agg(n=("weakU", "size"), strong=("strongU", "mean"),
                                        mid=("midU", "mean"), weak=("weakU", "mean"))
            for c in ["strong", "mid", "weak"]:
                fo[c] = (fo[c] * 100).round(2)
            print("\nFOLD-BY-FOLD  M=%d  [%%]" % M)
            print(fo.to_string())
            fo.to_csv(os.path.join(RES, "h3_f1_folds_M%d.csv" % M))


if __name__ == "__main__":
    main()
