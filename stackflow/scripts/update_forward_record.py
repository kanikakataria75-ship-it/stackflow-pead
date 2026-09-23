"""
StackFlow Layer 1 - FORWARD RECORD updater.

Appends ONLY post-freeze rebalance dates. This is the single piece of genuinely
out-of-sample evidence in the project; its entire value is that each entry was
not visible when it was generated.

HARD GUARD: any rebalance date < FREEZE_DATE is refused. Backfilling pre-freeze
history into this log would destroy the only thing the log is for.

Run this periodically (monthly is enough). It is idempotent.
"""
import os, sys, json, time, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

sys.path.insert(0, r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import CACHE_DIR, MIN_SECTORS_PER_DATE

# ---- FROZEN CONFIG (live_config_layer1.md, 2026-09-21). Do not edit here. ----
FREEZE_DATE = pd.Timestamp("2026-09-21")
N, M        = 20, 90
ROOT   = r"C:/Users/kanik/Desktop/stackflow claude/stackflow"
LOG    = os.path.join(ROOT, "forward_record_layer1.csv")
PANELC = json.load(open(os.path.join(CACHE_DIR, "panels.json")))["C"]

COLS = ["rebalance_date","status","n_live_sectors","excluded_sectors",
        "forward_window_ends","excluded_vs_universe_pct","passed_vs_universe_pct",
        "universe_fwd_vs_nifty500_pct","logged_at"]


def refresh_panel():
    """Re-download the frozen panel's indices + benchmark. Falls back to cache."""
    try:
        import build_dataset  # noqa
    except Exception:
        pass
    p = pd.read_csv(os.path.join(CACHE_DIR, "sector_close_panel.csv"),
                    index_col=0, parse_dates=True).sort_index()
    return p


def main(panel=None):
    panel = refresh_panel() if panel is None else panel
    SEC = [s for s in PANELC if s in panel.columns]
    idx = panel.index
    mats = {s: panel[s].to_numpy(float) for s in SEC}
    bench = panel["NIFTY 500"].to_numpy(float) if "NIFTY 500" in panel.columns else None
    pos = pd.Series(np.arange(len(idx)), index=idx).groupby([idx.year, idx.month]).last().values

    def ret(a, i, j):
        x, y = a[i], a[j]
        return np.nan if not (np.isfinite(x) and np.isfinite(y) and x > 0) else y/x - 1.0

    rows = []
    for i in pos:
        t = idx[i]
        if t < FREEZE_DATE:          # <<< HARD GUARD: no pre-freeze backfill, ever
            continue
        if i - N < 0:
            continue
        live = [(s, ret(mats[s], i-N, i)) for s in SEC]
        live = [(s, v) for s, v in live if np.isfinite(v)]
        K = len(live)
        if K < MIN_SECTORS_PER_DATE:
            continue
        tr = np.array([v for _, v in live])
        rs = tr - tr.mean()
        order = np.argsort(-rs); k = K // 3
        excl = [live[j][0] for j in order[-k:]]
        pssd = [live[j][0] for j in order[:K-k]]

        rec = dict(rebalance_date=str(t.date()), n_live_sectors=K,
                   excluded_sectors="|".join(sorted(excl)),
                   logged_at=pd.Timestamp.utcnow().strftime("%Y-%m-%d"))
        if i + M < len(idx):
            fe = {s: ret(mats[s], i, i+M) for s, _ in live}
            fv = np.array([fe[s] for s, _ in live], dtype=float)
            if np.isfinite(fv).all():
                U = fv.mean()
                rec.update(status="complete",
                    forward_window_ends=str(idx[i+M].date()),
                    excluded_vs_universe_pct=round(float(np.mean([fe[s] for s in excl])-U)*100, 4),
                    passed_vs_universe_pct=round(float(np.mean([fe[s] for s in pssd])-U)*100, 4),
                    universe_fwd_vs_nifty500_pct=(
                        round(float(U - ret(bench, i, i+M))*100, 4) if bench is not None else ""))
            else:
                rec.update(status="pending", forward_window_ends="",
                           excluded_vs_universe_pct="", passed_vs_universe_pct="",
                           universe_fwd_vs_nifty500_pct="")
        else:
            rec.update(status="pending", forward_window_ends="",
                       excluded_vs_universe_pct="", passed_vs_universe_pct="",
                       universe_fwd_vs_nifty500_pct="")
        rows.append(rec)

    new = pd.DataFrame(rows, columns=COLS) if rows else pd.DataFrame(columns=COLS)
    if os.path.exists(LOG):
        old = pd.read_csv(LOG, dtype=str)
        keep = old[~old.rebalance_date.isin(new.rebalance_date)] if len(new) else old
        out = pd.concat([keep, new], ignore_index=True)
    else:
        out = new
    if len(out):
        out = out.sort_values("rebalance_date")
    out.to_csv(LOG, index=False)

    done = (out.status == "complete").sum() if len(out) else 0
    pend = (out.status == "pending").sum() if len(out) else 0
    print(f"Forward record updated: {LOG}")
    print(f"  freeze date        : {FREEZE_DATE.date()}")
    print(f"  panel last close   : {idx[-1].date()}")
    print(f"  rebalances logged  : {len(out)}  (complete {done}, pending {pend})")
    if done == 0:
        print("  NO COMPLETED FORWARD WINDOWS YET. Nothing here is interpretable.")
    if len(out):
        print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    main()
