"""Build the master PEAD V2 event dataset with complete horizons and ex-ante quintiles."""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, V1_EVENTS, HORIZONS, BENCHMARK_FILE
from src.data_loader import load_prices, load_benchmark
from src.sue_engine import assign_ex_ante_quintiles_rolling, assign_ex_ante_quintiles_expanding


def build_v2_events():
    print("=== BUILDING PEAD V2 MASTER DATASET ===")
    assert os.path.exists(V1_EVENTS), f"V1 events missing at {V1_EVENTS}"
    ev = pd.read_csv(V1_EVENTS, parse_dates=["period_end", "filing_ts", "event_day", "entry_date"])
    print(f"Loaded {len(ev)} base events.")
    
    px_dict = load_prices()
    bench = load_benchmark()
    print(f"Loaded {len(px_dict)} price series and benchmark.")
    
    # Add all required horizons: 5d, 10d, 20d, 30d, 40d, 60d, 90d, 126d
    all_horizons = {"5d": 5, "10d": 10, "20d": 20, "30d": 30, "40d": 40, "60d": 60, "90d": 90, "126d": 126}
    
    # Check which horizons need calculation
    for h_name, h_bars in all_horizons.items():
        ret_col = f"ret_{h_name}"
        xs_nifty_col = f"xs_nifty_{h_name}"
        if ret_col not in ev.columns:
            print(f"Computing forward returns for horizon: {h_name} ({h_bars} trading days)...")
            ret_vals = []
            xs_nifty_vals = []
            for r in ev.itertuples():
                sym = str(r.symbol)
                if sym not in px_dict:
                    ret_vals.append(np.nan)
                    xs_nifty_vals.append(np.nan)
                    continue
                px = px_dict[sym]
                if r.entry_date not in px.index:
                    ret_vals.append(np.nan)
                    xs_nifty_vals.append(np.nan)
                    continue
                ei = px.index.get_loc(r.entry_date)
                target_i = ei + h_bars
                if target_i < len(px):
                    p0 = float(r.entry_open)
                    p_target = float(px.Close.iloc[target_i])
                    stock_ret = (p_target / p0) - 1.0 if p0 > 0 else np.nan
                    
                    # Benchmark return
                    i0 = bench.index.searchsorted(px.index[ei])
                    i1 = bench.index.searchsorted(px.index[target_i])
                    if i0 < len(bench) and i1 < len(bench):
                        bench_ret = float(bench.iloc[i1] / bench.iloc[i0] - 1.0)
                    else:
                        bench_ret = np.nan
                    xs_nifty = stock_ret - bench_ret if np.isfinite(stock_ret) and np.isfinite(bench_ret) else np.nan
                    ret_vals.append(stock_ret)
                    xs_nifty_vals.append(xs_nifty)
                else:
                    ret_vals.append(np.nan)
                    xs_nifty_vals.append(np.nan)
            ev[ret_col] = ret_vals
            ev[xs_nifty_col] = xs_nifty_vals
            
    # Compute excess returns vs monthly contemporaneous event universe
    ev["ym"] = ev.entry_date.dt.to_period("M")
    for h_name in all_horizons:
        ret_col = f"ret_{h_name}"
        xs_univ_col = f"xs_univ_{h_name}"
        month_means = ev.groupby("ym")[ret_col].transform("mean")
        ev[xs_univ_col] = ev[ret_col] - month_means
        
    # SUE Ex-Ante Quintile Assignments
    print("Computing Ex-Ante SUE Quintiles...")
    ev = ev.sort_values("event_day").reset_index(drop=True)
    
    # Model M1: Rolling 365 calendar days (~4 quarters)
    ev["q_exante_4q"] = assign_ex_ante_quintiles_rolling(ev, "event_day", "sue", lookback_days=365, min_events=150)
    
    # Model M2: Rolling 730 calendar days (~8 quarters)
    ev["q_exante_8q"] = assign_ex_ante_quintiles_rolling(ev, "event_day", "sue", lookback_days=730, min_events=250)
    
    # Model M3: Expanding historical window
    ev["q_exante_exp"] = assign_ex_ante_quintiles_expanding(ev, "event_day", "sue", min_events=150)
    
    # Preserve V1 look-ahead quintile
    ev["q_v1"] = ev["quintile"]
    
    # Filing Timing Diagnostics
    ev["days_from_qe"] = (ev.event_day - ev.period_end).dt.days
    ev["filing_cohort"] = np.where(ev.days_from_qe <= 25, "Early",
                          np.where(ev.days_from_qe <= 45, "Mid", "Late"))
                          
    # Size Terciles based on turnover20 (Small, Mid, Large)
    # Rolling or expanding turnover tercile
    t_q33 = ev.groupby("ym")["turnover20"].transform(lambda s: s.quantile(0.333))
    t_q66 = ev.groupby("ym")["turnover20"].transform(lambda s: s.quantile(0.666))
    ev["size_tercile"] = np.where(ev["turnover20"] <= t_q33, "Small",
                         np.where(ev["turnover20"] <= t_q66, "Mid", "Large"))
                         
    out_dir = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante")
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, "pead_v2_events.csv")
    ev.to_csv(out_csv, index=False)
    print(f"Master V2 events saved to {out_csv} ({len(ev)} rows).")
    
    print("\nEx-Ante Coverage Summary:")
    print(f"q_exante_4q valid: {ev.q_exante_4q.notna().sum()} / {len(ev)} ({ev.q_exante_4q.notna().mean()*100:.1f}%)")
    print(f"q_exante_8q valid: {ev.q_exante_8q.notna().sum()} / {len(ev)} ({ev.q_exante_8q.notna().mean()*100:.1f}%)")
    print(f"q_exante_exp valid: {ev.q_exante_exp.notna().sum()} / {len(ev)} ({ev.q_exante_exp.notna().mean()*100:.1f}%)")
    return ev


if __name__ == "__main__":
    build_v2_events()
