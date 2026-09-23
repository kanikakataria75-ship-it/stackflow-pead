"""Statistical evaluation metrics, fold consistency, and hypothesis verification."""
import numpy as np
import pandas as pd
from scipy import stats


def bh_fdr(p_values):
    """Benjamini-Hochberg False Discovery Rate adjustment."""
    p = np.asarray(p_values, float)
    ok = np.isfinite(p)
    q = np.full(len(p), np.nan)
    i = np.where(ok)[0]
    if len(i) == 0:
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


def calc_quarterly_folds(df, qcol, rcol, qtr_col="qtr", min_obs_per_bucket=3):
    """Compute per-quarter Q5 - Q1 spread."""
    out = []
    for q, g in df.groupby(qtr_col):
        hi = g[g[qcol] == 5][rcol].dropna()
        lo = g[g[qcol] == 1][rcol].dropna()
        if len(hi) >= min_obs_per_bucket and len(lo) >= min_obs_per_bucket:
            spread = hi.mean() - lo.mean()
            out.append({"qtr": str(q), "n_hi": len(hi), "n_lo": len(lo),
                        "q5_mean": hi.mean(), "q1_mean": lo.mean(), "spread": spread})
    return pd.DataFrame(out)


def evaluate_signal_cell(df, qcol, rcol, qtr_col="qtr", label="Cell"):
    """Evaluate a Q5 - Q1 signal cell against statistical and fold robustness standards."""
    hi = df[df[qcol] == 5][rcol].dropna()
    lo = df[df[qcol] == 1][rcol].dropna()
    
    if len(hi) < 10 or len(lo) < 10:
        return None
        
    t_stat, p_val = stats.ttest_ind(hi, lo, equal_var=False)
    spread = hi.mean() - lo.mean()
    
    # Quarterly folds
    folds_df = calc_quarterly_folds(df, qcol, rcol, qtr_col=qtr_col)
    folds_total = len(folds_df)
    folds_pos = int((folds_df["spread"] > 0).sum()) if folds_total > 0 else 0
    fold_pos_pct = (folds_pos / folds_total) if folds_total > 0 else 0.0
    
    # Drop best fold
    if folds_total > 2:
        best_idx = folds_df["spread"].idxmax()
        worst_idx = folds_df["spread"].idxmin()
        best_fold = folds_df.loc[best_idx, "qtr"]
        best_val = folds_df.loc[best_idx, "spread"]
        worst_fold = folds_df.loc[worst_idx, "qtr"]
        worst_val = folds_df.loc[worst_idx, "spread"]
        ex_best_df = folds_df.drop(best_idx)
        spread_ex_best = float(ex_best_df["spread"].mean())
    else:
        best_fold, best_val, worst_fold, worst_val, spread_ex_best = None, np.nan, None, np.nan, np.nan
        
    # Monotonicity check across Q1..Q5
    means = []
    for b in [1, 2, 3, 4, 5]:
        vals = df[df[qcol] == b][rcol].dropna()
        means.append(vals.mean() if len(vals) > 0 else np.nan)
        
    inversions = 0
    for j in range(len(means) - 1):
        if np.isfinite(means[j]) and np.isfinite(means[j + 1]):
            if means[j] > means[j + 1]:
                inversions += 1
                
    return {
        "label": label,
        "n_q5": len(hi),
        "n_q1": len(lo),
        "q5_pct": float(hi.mean() * 100),
        "q1_pct": float(lo.mean() * 100),
        "spread_pct": float(spread * 100),
        "t_stat": float(t_stat),
        "p_val": float(p_val),
        "folds_total": folds_total,
        "folds_pos": folds_pos,
        "fold_pos_pct": float(fold_pos_pct * 100),
        "best_fold": f"{best_fold} ({best_val*100:+.2f}%)" if best_fold else "N/A",
        "worst_fold": f"{worst_fold} ({worst_val*100:+.2f}%)" if worst_fold else "N/A",
        "spread_ex_best_pct": float(spread_ex_best * 100) if np.isfinite(spread_ex_best) else np.nan,
        "ladder_q1_to_q5": [round(float(m * 100), 3) if np.isfinite(m) else np.nan for m in means],
        "inversions": inversions,
        "monotonic_ok": (inversions <= 1),
        "dispersion_pct": float(df[rcol].std() * 100)
    }
