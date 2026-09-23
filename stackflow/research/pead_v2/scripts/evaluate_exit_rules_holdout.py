"""Evaluate all exit rules on 2024-2026 True OOS data to compare against 2021-2023 Discovery."""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, DISCOVERY_END, HOLDOUT_START, COST_BASE
from src.data_loader import load_prices, load_benchmark
from scripts.run_exit_rule_study import resolve_candidate_exit, simulate_portfolio_from_resolved_candidates

def main():
    events_path = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante", "pead_v2_events.csv")
    ev = pd.read_csv(events_path, parse_dates=["event_day", "entry_date", "period_end"])
    ev = ev[(ev.q_exante_4q == 5) & (ev.is_fin == False)].copy()
    
    px_dict = load_prices()
    bench = load_benchmark()
    
    all_events_by_symbol = {}
    for sym, group in ev.sort_values("event_day").groupby("symbol"):
        all_events_by_symbol[sym] = group.to_dict('records')
        
    next_filing_dict = {}
    for sym, group in ev.sort_values("event_day").groupby("symbol"):
        recs = group.to_dict('records')
        for i in range(len(recs) - 1):
            next_filing_dict[(sym, recs[i]['period_end'])] = recs[i+1]['entry_date']
            
    hold_ev = ev[ev.event_day >= HOLDOUT_START].copy()
    
    hypotheses = [
        ("H0_BASELINE", 60, "Hypothesis 0: Fixed 60-Day Baseline"),
        ("H1_TIME_DECAY", 10, "H1: Fixed 10 Trading Days"),
        ("H1_TIME_DECAY", 20, "H1: Fixed 20 Trading Days"),
        ("H1_TIME_DECAY", 30, "H1: Fixed 30 Trading Days"),
        ("H1_TIME_DECAY", 40, "H1: Fixed 40 Trading Days"),
        ("H1_TIME_DECAY", 90, "H1: Fixed 90 Trading Days"),
        ("H2_SIGNAL_DECAY", "Q3_OR_LOWER", "H2-A: Next Filing SUE <= Q3"),
        ("H2_SIGNAL_DECAY", "Q2_OR_LOWER", "H2-B: Next Filing SUE <= Q2"),
        ("H2_SIGNAL_DECAY", "SUE_DROP_1SD", "H2-C: Next Filing SUE Drops >= 1 SD"),
        ("H3_ABNORMAL_STOP", -0.05, "H3: Adverse AR Stop -5%"),
        ("H3_ABNORMAL_STOP", -0.075, "H3: Adverse AR Stop -7.5%"),
        ("H3_ABNORMAL_STOP", -0.10, "H3: Adverse AR Stop -10%"),
        ("H3_ABNORMAL_STOP", -0.15, "H3: Adverse AR Stop -15%"),
        ("H4_ABNORMAL_PROFIT", 0.10, "H4: Profit Exhaustion +10% AR"),
        ("H4_ABNORMAL_PROFIT", 0.15, "H4: Profit Exhaustion +15% AR"),
        ("H4_ABNORMAL_PROFIT", 0.20, "H4: Profit Exhaustion +20% AR"),
        ("H4_ABNORMAL_PROFIT", 0.25, "H4: Profit Exhaustion +25% AR"),
        ("H5_NEXT_EARNINGS", 1, "H5-A: Exit 1d Before Next Earnings"),
        ("H5_NEXT_EARNINGS", 3, "H5-B: Exit 3d Before Next Earnings"),
        ("H5_NEXT_EARNINGS", 5, "H5-C: Exit 5d Before Next Earnings"),
        ("H6_VOLATILITY_RISK", "DAILY_JUMP_2.5SIGMA", "H6-A: Daily Loss > 2.5 Sigma"),
        ("H6_VOLATILITY_RISK", "DAILY_JUMP_3SIGMA", "H6-B: Daily Loss > 3.0 Sigma"),
        ("H6_VOLATILITY_RISK", "VOL_SPIKE_2X", "H6-C: 10d Realized Vol > 2x Entry Vol"),
        ("H6_VOLATILITY_RISK", "CHANDELIER_2.5ATR", "H6-D: Chandelier Drop 2.5x ATR")
    ]
    
    hold_results = []
    for rule_type, param, label in hypotheses:
        resolved = []
        for r in hold_ev.itertuples():
            sym = str(r.symbol)
            if sym not in px_dict:
                continue
            px = px_dict[sym]
            res_c = resolve_candidate_exit(r, px, bench, rule_type, param, next_filing_dict, all_events_by_symbol)
            if res_c:
                resolved.append(res_c)
        cands_df = pd.DataFrame(resolved)
        
        sim_res = simulate_portfolio_from_resolved_candidates(cands_df, px_dict, bench, max_slots=30)
        if sim_res:
            hold_results.append({
                "rule_id": rule_type,
                "param": str(param),
                "label": label,
                "cagr_pct": sim_res["cagr_pct"],
                "bench_cagr_pct": sim_res["bench_cagr_pct"],
                "excess_cagr_pct": sim_res["excess_cagr_pct"],
                "sharpe": sim_res["sharpe"],
                "max_dd_pct": sim_res["max_dd_pct"],
                "win_rate_pct": sim_res["win_rate_pct"],
                "avg_trade_pct": sim_res["avg_trade_pct"],
                "median_trade_pct": sim_res["median_trade_pct"],
                "trades": sim_res["taken_trades"],
                "avg_holding_days": sim_res["avg_holding_days"],
                "cumulative_ret_pct": sim_res["cumulative_ret_pct"],
                "worst_month": sim_res["worst_month"],
                "worst_year": sim_res["worst_year"]
            })
            
    df_hold = pd.DataFrame(hold_results)
    out_csv = os.path.join(PEAD_V2_ROOT, "phase_08_backtest", "EXIT_RULE_HOLDOUT_STUDY.csv")
    df_hold.to_csv(out_csv, index=False)
    
    print("\n=== HOLDOUT (2024-2026) EXIT RULE RESULTS (SORTED BY SHARPE) ===")
    print(df_hold[["label", "cagr_pct", "excess_cagr_pct", "sharpe", "max_dd_pct", "win_rate_pct", "avg_trade_pct", "trades", "avg_holding_days"]].sort_values("sharpe", ascending=False).to_string(index=False))

    print("\n=== HOLDOUT (2024-2026) EXIT RULE RESULTS (SORTED BY EXCESS CAGR) ===")
    print(df_hold[["label", "cagr_pct", "excess_cagr_pct", "sharpe", "max_dd_pct", "win_rate_pct", "avg_trade_pct", "trades", "avg_holding_days"]].sort_values("excess_cagr_pct", ascending=False).to_string(index=False))

if __name__ == "__main__":
    main()
