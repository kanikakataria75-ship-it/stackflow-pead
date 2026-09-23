"""PEAD evaluation - primary cell against the 6 pre-registered criteria, plus
secondary measures (FDR-corrected) and all Part E diagnostics."""
import os
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/pead"
RES = os.path.join(ROOT, "results")
HOR = ["5d", "10d", "30d", "60d", "126d"]
COST = 0.585


def bh(p):
    p = np.asarray(p, float)
    ok = np.isfinite(p)
    q = np.full(len(p), np.nan)
    i = np.where(ok)[0]
    if not len(i):
        return q
    pv = p[i]
    o = np.argsort(pv)
    n = len(pv)
    a = pv[o] * n / (np.arange(n) + 1)
    a = np.minimum.accumulate(a[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.clip(a, 0, 1)
    q[i] = out
    return q


def spread_folds(d, qcol, rcol):
    """per-quarter Q5-Q1 spread."""
    out = []
    for q, g in d.groupby("qtr"):
        hi = g[g[qcol] == 5][rcol]
        lo = g[g[qcol] == 1][rcol]
        if len(hi) >= 3 and len(lo) >= 3:
            out.append((str(q), hi.mean() - lo.mean()))
    return pd.DataFrame(out, columns=["qtr", "spread"])


def summarise(d, qcol, rcol, label):
    hi = d[d[qcol] == 5][rcol].dropna()
    lo = d[d[qcol] == 1][rcol].dropna()
    if len(hi) < 20 or len(lo) < 20:
        return None
    from scipy import stats
    sp = hi.mean() - lo.mean()
    t, p = stats.ttest_ind(hi, lo, equal_var=False)
    fo = spread_folds(d, qcol, rcol)
    return dict(label=label, n_hi=len(hi), n_lo=len(lo),
                q5=100 * hi.mean(), q1=100 * lo.mean(), spread=100 * sp,
                p=p, folds=len(fo),
                fold_pos=float((fo.spread > 0).mean()) if len(fo) else np.nan,
                spread_exbest=100 * float(fo.spread.drop(fo.spread.idxmax()).mean())
                if len(fo) > 2 else np.nan,
                disp=100 * d[rcol].std(),
                norm=sp / d[rcol].std() if d[rcol].std() else np.nan)


def main():
    ev = pd.read_csv(os.path.join(RES, "pead_events.csv"), parse_dates=["event_day", "entry_date"])
    ev["qtr"] = ev.event_day.dt.to_period("Q")
    R = "xs_univ_60d"
    Q = "quintile"
    print("=== COVERAGE ===")
    print("events=%d symbols=%d  discovery=%d holdout=%d"
          % (len(ev), ev.symbol.nunique(), (ev.period == "discovery").sum(),
             (ev.period == "holdout").sum()))
    print("by year:")
    print(ev.groupby(ev.event_day.dt.year).agg(n=("symbol", "size"),
                                               syms=("symbol", "nunique")).to_string())
    for h in HOR:
        print("  %-5s complete %d (%.0f%%)" % (h, ev["ret_" + h].notna().sum(),
                                               100 * ev["ret_" + h].notna().mean()))
    print("\nctx_inferred %.1f%%  financials %.1f%%  layer4_seen %d"
          % (100 * ev.ctx_inferred.mean(), 100 * ev.is_fin.mean(), ev.layer4_seen.sum()))
    bs = ev.groupby("symbol").basis.nunique()
    print("basis-switch rate (symbols with >1 basis): %.1f%%" % (100 * (bs > 1).mean()))

    print("\n=== PRIMARY CELL: SUE Q5-Q1, 60d, excess vs event universe ===")
    rows = []
    for lab, sub in [("ALL", ev), ("DISCOVERY", ev[ev.period == "discovery"]),
                     ("HOLDOUT", ev[ev.period == "holdout"]),
                     ("ex-2020", ev[ev.event_day.dt.year != 2020]),
                     ("ex-layer4seen", ev[~ev.layer4_seen]),
                     ("ctx_inferred=False", ev[~ev.ctx_inferred])]:
        r = summarise(sub, Q, R, lab)
        if r:
            rows.append(r)
    prim = pd.DataFrame(rows)
    pd.set_option("display.width", 240)
    print(prim.round(4).to_string(index=False))

    print("\n--- quintile ladder (monotonicity), xs_univ_60d %% ---")
    lad = ev.groupby(Q)[R].agg(["size", "mean"])
    lad["mean"] = (100 * lad["mean"]).round(3)
    print(lad.to_string())
    for lab, sub in [("discovery", ev[ev.period == "discovery"]),
                     ("holdout", ev[ev.period == "holdout"])]:
        l2 = sub.groupby(Q)[R].mean() * 100
        print("  %-10s %s" % (lab, "  ".join("Q%d=%+.2f" % (int(k), v) for k, v in l2.items())))

    print("\n--- long vs short side (vs universe mean = 0 by construction) ---")
    for lab, sub in [("ALL", ev), ("HOLDOUT", ev[ev.period == "holdout"])]:
        hi = sub[sub[Q] == 5][R].mean() * 100
        lo = sub[sub[Q] == 1][R].mean() * 100
        print("  %-9s Q5=%+.3f%%  Q1=%+.3f%%  -> %s side carries it"
              % (lab, hi, lo, "LONG" if abs(hi) > abs(lo) else "SHORT"))

    print("\n--- fold detail (quarterly Q5-Q1 spread, %) ---")
    fo = spread_folds(ev, Q, R)
    fo["spread"] = (100 * fo.spread).round(2)
    print(fo.to_string(index=False))
    print("  folds positive: %d/%d (%.1f%%)" % ((fo.spread > 0).sum(), len(fo),
                                                100 * (fo.spread > 0).mean()))

    print("\n--- break-point scan (spread before vs after each year) ---")
    ev["y"] = ev.event_day.dt.year
    for b in range(2021, 2026):
        a = summarise(ev[ev.y < b], Q, R, "e")
        c = summarise(ev[ev.y >= b], Q, R, "l")
        if a and c:
            print("  split %d: early %+.3f%% (n=%d)  late %+.3f%% (n=%d)"
                  % (b, a["spread"], a["n_hi"] + a["n_lo"], c["spread"], c["n_hi"] + c["n_lo"]))

    print("\n=== DIAGNOSTICS ===")
    med = ev.turnover20.median()
    for lab, sub in [("financials", ev[ev.is_fin]), ("non-financials", ev[~ev.is_fin]),
                     ("large (turnover>med)", ev[ev.turnover20 > med]),
                     ("small (turnover<=med)", ev[ev.turnover20 <= med])]:
        r = summarise(sub, Q, R, lab)
        if r:
            print("  %-22s n=%-5d spread=%+.3f%%  folds+=%.0f%%  p=%.3f"
                  % (lab, r["n_hi"] + r["n_lo"], r["spread"], 100 * r["fold_pos"], r["p"]))

    print("\n=== SECONDARY (FDR-corrected) ===")
    sec = []
    for meas, qc in [("SUE", "quintile"), ("RevSUE", "quintile_rev"),
                     ("EAR_clean", "quintile_ear"),
                     ("EAR_LOOKAHEAD(excluded)", "quintile_earla")]:
        for h in HOR:
            r = summarise(ev, qc, "xs_univ_" + h, "%s_%s" % (meas, h))
            if r:
                r["measure"] = meas
                r["horizon"] = h
                sec.append(r)
    S = pd.DataFrame(sec)
    if len(S):
        S["q_fdr"] = bh(S.p.values)
        print(S[["measure", "horizon", "n_hi", "n_lo", "q5", "q1", "spread", "p",
                 "q_fdr", "fold_pos", "norm"]].round(4).to_string(index=False))
        S.to_csv(os.path.join(RES, "pead_summary.csv"), index=False)
    prim.to_csv(os.path.join(RES, "pead_primary.csv"), index=False)
    fo.to_csv(os.path.join(RES, "pead_folds.csv"), index=False)


if __name__ == "__main__":
    main()
