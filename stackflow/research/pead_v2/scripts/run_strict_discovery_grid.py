"""Run the 96-cell parameter grid strictly on 2021-2023 Discovery data.
Then select the optimal configuration based exclusively on Discovery performance.
Finally, evaluate that exact selected configuration on 2024-2026 OOS data.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, DISCOVERY_END, HOLDOUT_START, COST_BASE
from src.data_loader import load_prices, load_benchmark
from src.portfolio_engine import run_portfolio_backtest

def main():
    print("=== EXECUTING STRICT DISCOVERY GRID (2021-2023) ===")
    events_path = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante", "pead_v2_events.csv")
    ev = pd.read_csv(events_path, parse_dates=["event_day", "entry_date", "period_end"])
    ev = ev[ev["q_exante_4q"].notna()].copy()
    
    # Filter strictly for Discovery (events occurring on or before 2023-12-31)
    disc_ev = ev[ev.event_day <= DISCOVERY_END].copy()
    hold_ev = ev[ev.event_day >= HOLDOUT_START].copy()
    
    print(f"Total Discovery events: {len(disc_ev)}")
    print(f"Total Holdout events: {len(hold_ev)}")
    
    px_dict = load_prices()
    bench = load_benchmark()
    
    signals = [
        ("Q5_only", disc_ev[disc_ev.q_exante_4q == 5]),
        ("Q4_Q5", disc_ev[disc_ev.q_exante_4q >= 4])
    ]
    slots_list = [10, 20, 30]
    horizons = [20, 40, 60, 90]
    queue_policies = ["FIFO", "SUE_RANK"]
    universe_variants = [
        ("All_Sectors", False),
        ("Non_Financials", True)
    ]
    
    results = []
    for u_name, ex_fin in universe_variants:
        for sig_name, sig_df in signals:
            current_df = sig_df[sig_df["is_fin"] == False] if ex_fin else sig_df
            for slots in slots_list:
                for h in horizons:
                    for qp in queue_policies:
                        res = run_portfolio_backtest(
                            trades_df=current_df,
                            prices_dict=px_dict,
                            benchmark_series=bench,
                            max_slots=slots,
                            holding_period=h,
                            cost=COST_BASE,
                            queue_policy=qp
                        )
                        if res:
                            results.append({
                                "universe": u_name,
                                "signal": sig_name,
                                "slots": slots,
                                "holding_days": h,
                                "queue_policy": qp,
                                "eligible_trades": res["eligible_trades"],
                                "taken_trades": res["taken_trades"],
                                "cagr_pct": round(res["cagr_pct"], 2),
                                "bench_cagr_pct": round(res["bench_cagr_pct"], 2),
                                "excess_cagr_pct": round(res["excess_cagr_pct"], 2),
                                "sharpe": round(res["sharpe"], 3),
                                "max_dd_pct": round(res["max_dd_pct"], 2),
                                "win_rate_pct": round(res["win_rate_pct"], 1),
                                "profit_factor": round(res["profit_factor"], 2) if not np.isnan(res["profit_factor"]) else np.nan
                            })
                            
    res_df = pd.DataFrame(results)
    print(f"Total Discovery grid backtests completed: {len(res_df)}")
    
    # Save discovery grid results
    disc_csv = os.path.join(PEAD_V2_ROOT, "phase_08_backtest", "DISCOVERY_GRID_2021_2023.csv")
    res_df.to_csv(disc_csv, index=False)
    
    # Sort by excess CAGR
    top_by_excess = res_df.sort_values("excess_cagr_pct", ascending=False)
    print("\n--- TOP 10 CONFIGURATIONS IN DISCOVERY (2021-2023) BY EXCESS CAGR ---")
    print(top_by_excess[["universe", "signal", "slots", "holding_days", "queue_policy", "cagr_pct", "excess_cagr_pct", "sharpe", "max_dd_pct", "taken_trades"]].head(10).to_string(index=False))

    top_by_sharpe = res_df.sort_values("sharpe", ascending=False)
    print("\n--- TOP 10 CONFIGURATIONS IN DISCOVERY (2021-2023) BY SHARPE ---")
    print(top_by_sharpe[["universe", "signal", "slots", "holding_days", "queue_policy", "cagr_pct", "excess_cagr_pct", "sharpe", "max_dd_pct", "taken_trades"]].head(10).to_string(index=False))

    # Also check the specific frozen V2 config in discovery:
    v2_frozen_disc = res_df[(res_df.universe == "Non_Financials") & 
                            (res_df.signal == "Q5_only") & 
                            (res_df.slots == 30) & 
                            (res_df.holding_days == 60) & 
                            (res_df.queue_policy == "SUE_RANK")]
    print("\n--- FROZEN V2 CONFIG (Non-Fin, Q5, 30 slots, 60d, SUE_RANK) IN DISCOVERY ---")
    print(v2_frozen_disc.to_string(index=False))

if __name__ == "__main__":
    main()
