"""Phase 3b - Interest Coverage and ROE grids.
Executes exactly what layer3/pre_registration_ic_roe.md fixed in advance.
Four hypotheses, two grids, all mandatory checks. No factor combination anywhere.
"""
import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

L1 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
L2 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2/cache"
XB = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl/cache"
RES = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer3/results"
os.makedirs(RES, exist_ok=True)
MIN_STOCKS = 30
_RNG = np.random.default_rng(23)

IND2SEC = {
    "FINANCIAL SERVICES": ["NIFTY BANK", "NIFTY PSU BANK", "NIFTY NBFC",
                           "NIFTY HOUSING FINANCE", "NIFTY INSURANCE"],
    "CONSUMER GOODS": ["NIFTY FMCG", "NIFTY CONSUMER DURABLES"],
    "INDUSTRIAL MANUFACTURING": ["NIFTY CAPITAL GOODS"], "PHARMA": ["NIFTY HEALTHCARE"],
    "AUTOMOBILE": ["NIFTY AUTO"], "CONSTRUCTION": ["NIFTY CONSTRUCTION", "NIFTY REALTY"],
    "SERVICES": ["NIFTY COMMERCIAL & TRANSPORT SERVICES", "NIFTY CONSUMER SERVICES"],
    "IT": ["NIFTY IT"], "METALS": ["NIFTY METAL"], "CHEMICALS": ["NIFTY CHEMICALS"],
    "OIL & GAS": ["NIFTY OIL & GAS"], "CEMENT & CEMENT PRODUCTS": ["NIFTY CEMENT"],
    "POWER": ["NIFTY POWER"], "FERTILISERS & PESTICIDES": ["NIFTY CHEMICALS"],
    "MEDIA & ENTERTAINMENT": ["NIFTY MEDIA"], "HEALTHCARE SERVICES": ["NIFTY HOSPITALS"],
    "TELECOM": ["NIFTY TELECOMMUNICATIONS"],
}


def key(s):
    return str(s).replace("&", "and").replace("/", "_")


def perm_p(vals, side):
    v = np.asarray([x for x in vals if np.isfinite(x)], float)
    if len(v) < 3:
        return np.nan
    obs = v.mean()
    d = (_RNG.choice([-1.0, 1.0], size=(20000, len(v))) * np.abs(v)).mean(axis=1)
    return float((d <= obs).mean()) if side == "neg" else float((d >= obs).mean())


def industry_passes(passed):
    return {i: (sum(1 for s in secs if s in passed) * 2 >= len(secs))
            for i, secs in IND2SEC.items()}


def reversal_years(bench):
    out = []
    for y, g in bench.groupby(bench.index.year):
        if len(g) < 100:
            continue
        w = bench[(bench.index >= pd.Timestamp(y, 1, 1) - pd.Timedelta(days=183))
                  & (bench.index <= g.index[-1])]
        if (w / w.cummax() - 1).min() <= -0.15 and (g.iloc[-1] / g.iloc[0] - 1) >= 0.10:
            out.append(y)
    return out


def drop_after_basis_switch(d, keycols):
    """D13: drop the single observation immediately after a basis change."""
    d = d.sort_values(keycols).copy()
    d["_prev"] = d.groupby("symbol").basis.shift(1)
    d["_switch"] = d._prev.notna() & (d._prev != d.basis)
    return d[~d._switch].drop(columns=["_prev", "_switch"]), int(d._switch.sum())


def load_prices(symbols):
    px = {}
    for s in symbols:
        f = os.path.join(L2, "stocks", key(s) + ".csv")
        if os.path.exists(f):
            try:
                v = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0].dropna()
                if len(v) >= 250:
                    px[s] = v
            except Exception:
                pass
    return pd.DataFrame(px).sort_index()


def build_signal(d, valcol, nper, datecol="filing_date"):
    """Rolling mean of the last `nper` filings, stamped at each filing date."""
    out = {}
    for sym, g in d.groupby("symbol"):
        g = g.sort_values(datecol)
        v = g[valcol].rolling(nper, min_periods=nper).mean()
        s = pd.Series(v.values, index=pd.to_datetime(g[datecol].values)).dropna()
        s = s[~s.index.duplicated(keep="last")]
        if len(s):
            out[sym] = s
    return out


def run_grid(fact, valcol, Ns, Ms, rebal_dates, panel, bench, L1map, ind,
             stale_days, label, subset=None):
    idx = panel.index
    bs = bench.reindex(idx).ffill().to_numpy(float)
    mats = {s: panel[s].to_numpy(float) for s in panel.columns}
    ipos = {d: i for i, d in enumerate(idx)}

    def near(d):
        c = idx[idx <= d]
        return ipos[c[-1]] if len(c) else None

    def ret(a, i, j):
        x, y = a[i], a[j]
        return np.nan if not (np.isfinite(x) and np.isfinite(y) and x > 0) else y / x - 1

    rows, cells = [], {}
    for N in Ns:
        sig = build_signal(fact if subset is None else fact[fact.symbol.isin(subset)],
                           valcol, N)
        for M in Ms:
            recs = []
            for d in rebal_dates:
                i = near(d)
                if i is None or i + M >= len(idx):
                    continue
                ip = industry_passes(L1map[d])
                vals, fwd, infl, bl = [], [], [], []
                for s, ss in sig.items():
                    if s not in panel.columns:
                        continue
                    if not ip.get(ind.get(s, ""), False):
                        continue
                    h = ss[ss.index <= d]
                    if len(h) == 0 or (d - h.index[-1]).days > stale_days:
                        continue
                    f = ret(mats[s], i, i + M)
                    if not np.isfinite(f):
                        continue
                    vals.append(h.iloc[-1])
                    fwd.append(f)
                K = len(vals)
                if K < MIN_STOCKS:
                    continue
                v = np.array(vals, float)
                f = np.array(fwd, float)
                lo, hi = np.percentile(v, [1, 99])
                v = np.clip(v, lo, hi)
                feU = f - f.mean()
                bf = ret(bs, i, i + M)
                o = np.argsort(-v)
                k = K // 3
                recs.append(dict(date=d, year=d.year, K=K,
                                 strongU=feU[o[:k]].mean(), midU=feU[o[k:K - k]].mean(),
                                 weakU=feU[o[-k:]].mean(),
                                 strongB=f[o[:k]].mean() - bf, weakB=f[o[-k:]].mean() - bf,
                                 disp=feU.std(ddof=1)))
            df = pd.DataFrame(recs)
            cells[(N, M)] = df
            if len(df) < 4:
                continue
            fo = df.groupby("year")[["strongU", "weakU"]].mean()
            rows.append(dict(
                N=N, M=M, n=len(df), folds=len(fo), medK=int(df.K.median()),
                strong=df.strongU.mean(), mid=df.midU.mean(), weak=df.weakU.mean(),
                spread=df.strongU.mean() - df.weakU.mean(),
                strongB=df.strongB.mean(), weakB=df.weakB.mean(), disp=df.disp.mean(),
                s_norm=df.strongU.mean() / df.disp.mean(),
                w_norm=df.weakU.mean() / df.disp.mean(),
                f_strong_pos=(fo.strongU > 0).mean(), f_weak_neg=(fo.weakU < 0).mean(),
                strong_exbest=float(fo.strongU.drop(fo.strongU.idxmax()).mean()),
                weak_exworst=float(fo.weakU.drop(fo.weakU.idxmin()).mean()),
                mono=bool(df.strongU.mean() > df.midU.mean() > df.weakU.mean()),
                p_strong=perm_p(fo.strongU.values, "pos"),
                p_weak=perm_p(fo.weakU.values, "neg")))
    return pd.DataFrame(rows), cells


def main():
    u = pd.read_csv(os.path.join(L2, "pit_universe_2020.csv"))
    u["Industry"] = u.Industry.str.strip().str.upper()
    u = u[u.Industry.isin(IND2SEC)]
    ind = dict(zip(u.Symbol, u.Industry))
    bench = pd.read_csv(os.path.join(L1, "sector_close_panel.csv"),
                        index_col=0, parse_dates=True)["NIFTY 500"].dropna()
    RY = reversal_years(bench)
    L1p = pd.read_csv(os.path.join(L2, "layer1_passthrough_pit.csv"), parse_dates=["date"])
    L1map = {r.date: set(str(r.passed).split("|")) for _, r in L1p.iterrows()}
    l1 = sorted(L1map)

    ic = pd.read_csv(os.path.join(XB, "factor_ic_quarterly.csv"))
    ic["filing_date"] = pd.to_datetime(ic.filing_date, errors="coerce")
    ic = ic[ic.filing_date.notna() & (ic.interest > 0)].copy()
    ic["val"] = (ic.pbt + ic.interest) / ic.interest
    ic, nsw_ic = drop_after_basis_switch(ic, ["symbol", "filing_date"])

    roe = pd.read_csv(os.path.join(XB, "factor_roe_annual.csv"))
    roe["filing_date"] = pd.to_datetime(roe.filing_date, errors="coerce")
    roe = roe[roe.filing_date.notna() & (roe.equity > 0)].copy()
    roe["val"] = roe.pat / roe.equity
    roe, nsw_roe = drop_after_basis_switch(roe, ["symbol", "filing_date"])

    panel = load_prices(sorted(set(u.Symbol)))
    qd = {}
    for d in l1:
        qd[(d.year, (d.month - 1) // 3)] = d
    q_reb = sorted(qd.values())
    ad = {}
    for d in l1:
        ad[d.year] = d
    a_reb = sorted(ad.values())

    meta = dict(reversal_years=RY,
                ic=dict(rows=len(ic), symbols=int(ic.symbol.nunique()),
                        ctx_inferred=float(ic.ctx_inferred.mean()),
                        basis_switch_rate=float((ic.groupby("symbol").basis.nunique() > 1).mean()),
                        dropped_after_switch=nsw_ic),
                roe=dict(rows=len(roe), symbols=int(roe.symbol.nunique()),
                         ctx_inferred=float(roe.ctx_inferred.mean()),
                         basis_switch_rate=float((roe.groupby("symbol").basis.nunique() > 1).mean()),
                         dropped_after_switch=nsw_roe))
    print(json.dumps(meta, indent=1))

    out = {}
    for name, fact, Ns, Ms, reb, stale in [
            ("IC", ic, [1, 2, 4], [60, 120, 180, 250], q_reb, 200),
            ("ROE", roe, [1, 2], [120, 180, 250], a_reb, 400)]:
        g, cells = run_grid(fact, "val", Ns, Ms, reb, panel, bench, L1map, ind, stale, name)
        g.to_csv(os.path.join(RES, "p3b_%s_grid.csv" % name), index=False)
        out[name] = (g, cells)
        # D11 sensitivity: exclude ctx_inferred rows
        g2, _ = run_grid(fact[~fact.ctx_inferred.astype(bool)], "val", Ns, Ms, reb,
                         panel, bench, L1map, ind, stale, name)
        g2.to_csv(os.path.join(RES, "p3b_%s_grid_noinfer.csv" % name), index=False)
        # D13 sensitivity: never-switch subset
        never = fact.groupby("symbol").basis.nunique()
        never = set(never[never == 1].index)
        g3, _ = run_grid(fact, "val", Ns, Ms, reb, panel, bench, L1map, ind, stale,
                         name, subset=never)
        g3.to_csv(os.path.join(RES, "p3b_%s_grid_nevernswitch.csv" % name), index=False)
        meta[name.lower()]["never_switch_symbols"] = len(never)
        # reversal-year split + fold detail
        for (N, M), df in cells.items():
            if len(df) >= 4:
                df.to_csv(os.path.join(RES, "p3b_%s_cell_N%s_M%s.csv" % (name, N, M)),
                          index=False)
        print("\n=== %s GRID ===" % name)
        d = g.copy()
        for c in ["strong", "mid", "weak", "spread", "strongB", "weakB", "disp",
                  "strong_exbest", "weak_exworst"]:
            d[c] = (d[c] * 100).round(3)
        for c in ["f_strong_pos", "f_weak_neg"]:
            d[c] = (d[c] * 100).round(1)
        for c in ["s_norm", "w_norm"]:
            d[c] = d[c].round(3)
        pd.set_option("display.width", 260)
        print(d.to_string(index=False))
        print("\n[%s] no-infer grid rows=%d   never-switch symbols=%d  grid rows=%d"
              % (name, len(g2), len(never), len(g3)))
        # reversal year breakdown on the widest cell
        big = max(cells, key=lambda k: len(cells[k]))
        df = cells[big]
        if len(df):
            rv = df[df.year.isin(RY)]
            nv = df[~df.year.isin(RY)]
            print("[%s] reversal years %s : strong=%.3f%% weak=%.3f%% (n=%d) | others: strong=%.3f%% weak=%.3f%% (n=%d)"
                  % (name, RY, rv.strongU.mean() * 100 if len(rv) else float('nan'),
                     rv.weakU.mean() * 100 if len(rv) else float('nan'), len(rv),
                     nv.strongU.mean() * 100, nv.weakU.mean() * 100, len(nv)))
    json.dump(meta, open(os.path.join(RES, "p3b_meta.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
