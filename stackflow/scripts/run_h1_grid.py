"""
StackFlow Layer 1 - H1 grid test (sector momentum persistence).
Executes exactly the procedure fixed in pre_registration.md. Reports the FULL
N x M grid and fold-by-fold breakdowns - never only the best cell.

Look-ahead control: trailing RS at rebalance index i uses closes[i-N..i];
forward excess uses closes[i..i+M]. The two never share a future bar, and the
rank decision at i is made only from data at or before i.
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

sys.path.insert(0, r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import (LOOKBACKS, FORWARDS, MIN_SECTORS_PER_DATE, COST_ONE_WAY,
                     BENCHMARK, CACHE_DIR, RESULTS_DIR, sanity_check_units)

BNAME = BENCHMARK
ROUND_TRIP = 2 * COST_ONE_WAY


def load_panel():
    p = pd.read_csv(os.path.join(CACHE_DIR, "sector_close_panel.csv"),
                    index_col=0, parse_dates=True).sort_index()
    p = p[~p.index.duplicated(keep="last")]
    return p


def rebalance_positions(idx):
    """Integer positions of the last trading day of each calendar month."""
    s = pd.Series(np.arange(len(idx)), index=idx)
    return s.groupby([idx.year, idx.month]).last().values


def ret(a, i0, i1):
    """Simple return of array a from position i0 to i1; NaN-safe."""
    x0, x1 = a[i0], a[i1]
    if not np.isfinite(x0) or not np.isfinite(x1) or x0 <= 0:
        return np.nan
    return x1 / x0 - 1.0


def run_cell(panel, sectors, N, M):
    """One (N, M) grid cell. Returns per-rebalance-date bucket records."""
    idx = panel.index
    bench = panel[BNAME].to_numpy(dtype=float)
    mats = {s: panel[s].to_numpy(dtype=float) for s in sectors}
    recs = []
    for i in rebalance_positions(idx):
        if i - N < 0 or i + M >= len(idx):
            continue
        br_t = ret(bench, i - N, i)
        br_f = ret(bench, i, i + M)
        if not np.isfinite(br_t) or not np.isfinite(br_f):
            continue
        rows = []
        for s in sectors:
            a = mats[s]
            trail = ret(a, i - N, i)
            fwd = ret(a, i, i + M)
            if np.isfinite(trail) and np.isfinite(fwd):
                rows.append((s, trail - br_t, fwd - br_f))
        K = len(rows)
        if K < MIN_SECTORS_PER_DATE:
            continue
        rows.sort(key=lambda r: -r[1])              # descending trailing RS
        k = K // 3
        buckets = {"top": rows[:k], "bottom": rows[-k:], "middle": rows[k:K - k]}
        rec = dict(date=idx[i], year=idx[i].year, n_sectors=K)
        for b, rws in buckets.items():
            rec[b] = float(np.mean([r[2] for r in rws])) if rws else np.nan
        rec["spread"] = rec["top"] - rec["bottom"]
        recs.append(rec)
    return pd.DataFrame(recs)


def summarize(df):
    if len(df) == 0:
        return {}
    return dict(
        n_dates=len(df),
        top=df["top"].mean(), middle=df["middle"].mean(), bottom=df["bottom"].mean(),
        spread=df["spread"].mean(),
        top_net=df["top"].mean() - ROUND_TRIP,
        top_hit=(df["top"] > 0).mean(),
        spread_hit=(df["spread"] > 0).mean(),
        monotonic=bool(df["top"].mean() > df["middle"].mean() > df["bottom"].mean()),
    )


def main():
    sanity_check_units()
    panel = load_panel()
    sectors = [c for c in panel.columns if c != BNAME]
    print(f"\nPanel: {panel.shape[0]} trading days, "
          f"{panel.index[0].date()} -> {panel.index[-1].date()}")
    print(f"Sectors in panel: {len(sectors)}")
    print(f"Round-trip cost charged to net figures: {ROUND_TRIP*100:.2f}%\n")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    grid_rows, all_cells = [], {}
    for N in LOOKBACKS:
        for M in FORWARDS:
            df = run_cell(panel, sectors, N, M)
            all_cells[(N, M)] = df
            s = summarize(df)
            if not s:
                continue
            fold = df.groupby("year")[["top", "middle", "bottom", "spread"]].mean()
            s.update(N=N, M=M,
                     n_folds=len(fold),
                     folds_top_pos=float((fold["top"] > 0).mean()),
                     folds_spread_pos=float((fold["spread"] > 0).mean()))
            # fold-concentration check (K2): drop the single best fold by spread
            if len(fold) > 2:
                drop = fold.drop(fold["spread"].idxmax())
                s["spread_ex_best_fold"] = float(drop["spread"].mean())
                s["top_ex_best_fold"] = float(
                    fold.drop(fold["top"].idxmax())["top"].mean())
            grid_rows.append(s)
            df.to_csv(os.path.join(RESULTS_DIR, f"cell_N{N}_M{M}.csv"), index=False)

    g = pd.DataFrame(grid_rows)
    cols = ["N", "M", "n_dates", "top", "middle", "bottom", "spread", "top_net",
            "top_hit", "spread_hit", "monotonic", "n_folds", "folds_top_pos",
            "folds_spread_pos", "top_ex_best_fold", "spread_ex_best_fold"]
    g = g[[c for c in cols if c in g.columns]]
    g.to_csv(os.path.join(RESULTS_DIR, "grid_summary.csv"), index=False)

    pd.set_option("display.width", 250)
    pct = ["top", "middle", "bottom", "spread", "top_net",
           "top_ex_best_fold", "spread_ex_best_fold"]
    disp = g.copy()
    for c in pct:
        if c in disp: disp[c] = (disp[c] * 100).round(2)
    for c in ["top_hit", "spread_hit", "folds_top_pos", "folds_spread_pos"]:
        if c in disp: disp[c] = (disp[c] * 100).round(1)
    print("=" * 130)
    print("FULL N x M GRID  (all 16 cells; returns in %, forward excess vs Nifty 500)")
    print("=" * 130)
    print(disp.to_string(index=False))

    print("\n" + "=" * 130)
    print("GRID SHAPE - mean TOP-tercile forward excess % (rows=lookback N, cols=forward M)")
    print("=" * 130)
    print((g.pivot(index="N", columns="M", values="top") * 100).round(2).to_string())
    print("\nmean TOP-BOTTOM spread %")
    print((g.pivot(index="N", columns="M", values="spread") * 100).round(2).to_string())
    print("\nmean BOTTOM-tercile forward excess % (MEAN-REVERSION CHECK: "
          "positive => losers bounce)")
    print((g.pivot(index="N", columns="M", values="bottom") * 100).round(2).to_string())

    # fold-by-fold for representative cells
    reps = [(20, 20), (60, 60), (90, 90), (20, 90), (90, 20)]
    for cell in reps:
        if cell not in all_cells or len(all_cells[cell]) == 0:
            continue
        df = all_cells[cell]
        fold = df.groupby("year").agg(
            n=("top", "size"), top=("top", "mean"), middle=("middle", "mean"),
            bottom=("bottom", "mean"), spread=("spread", "mean"))
        f = fold.copy()
        for c in ["top", "middle", "bottom", "spread"]:
            f[c] = (f[c] * 100).round(2)
        print("\n" + "=" * 90)
        print(f"FOLD-BY-FOLD (calendar year) - cell N={cell[0]}, M={cell[1]}  [%]")
        print("=" * 90)
        print(f.to_string())
        print(f"  folds with top>0   : {(fold['top']>0).sum()}/{len(fold)}")
        print(f"  folds with spread>0: {(fold['spread']>0).sum()}/{len(fold)}")
        fold.to_csv(os.path.join(RESULTS_DIR, f"folds_N{cell[0]}_M{cell[1]}.csv"))

    print("\nNOTE: monthly rebalance with M up to 90 sessions creates OVERLAPPING "
          "forward windows.\nObservations are autocorrelated; any naive t-stat "
          "would be overstated. Fold counts and\nhit rates are therefore the "
          "primary evidence, not pooled significance.")


if __name__ == "__main__":
    main()
