"""Run the exact frozen configuration selected from 2021-2023 on 2024-2026 True OOS."""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, DISCOVERY_END, HOLDOUT_START, COST_BASE
from src.data_loader import load_prices, load_benchmark
from src.portfolio_engine import run_portfolio_backtest

def main():
    events_path = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante", "pead_v2_events.csv")
    ev = pd.read_csv(events_path, parse_dates=["event_day", "entry_date", "period_end"])
    ev = ev[ev["q_exante_4q"].notna()].copy()
    
    disc_ev = ev[ev.event_day <= DISCOVERY_END].copy()
    hold_ev = ev[ev.event_day >= HOLDOUT_START].copy()
    
    px_dict = load_prices()
    bench = load_benchmark()
    
    # 1. 30 Slots, Non-Financials, Q5_only, 60d, SUE_RANK (#1 Sharpe configuration in Discovery)
    disc_df = disc_ev[(disc_ev.q_exante_4q == 5) & (disc_ev.is_fin == False)]
    hold_df = hold_ev[(hold_ev.q_exante_4q == 5) & (hold_ev.is_fin == False)]
    
    res_disc_30 = run_portfolio_backtest(
        trades_df=disc_df,
        prices_dict=px_dict,
        benchmark_series=bench,
        max_slots=30,
        holding_period=60,
        cost=COST_BASE,
        queue_policy="SUE_RANK"
    )
    
    res_hold_30 = run_portfolio_backtest(
        trades_df=hold_df,
        prices_dict=px_dict,
        benchmark_series=bench,
        max_slots=30,
        holding_period=60,
        cost=COST_BASE,
        queue_policy="SUE_RANK"
    )
    
    # Also evaluate FIFO on holdout for comparison since they tied on discovery
    res_hold_30_fifo = run_portfolio_backtest(
        trades_df=hold_df,
        prices_dict=px_dict,
        benchmark_series=bench,
        max_slots=30,
        holding_period=60,
        cost=COST_BASE,
        queue_policy="FIFO"
    )
    
    # Also evaluate 10 slots on holdout for complete transparency
    res_disc_10 = run_portfolio_backtest(
        trades_df=disc_df,
        prices_dict=px_dict,
        benchmark_series=bench,
        max_slots=10,
        holding_period=60,
        cost=COST_BASE,
        queue_policy="SUE_RANK"
    )
    res_hold_10 = run_portfolio_backtest(
        trades_df=hold_df,
        prices_dict=px_dict,
        benchmark_series=bench,
        max_slots=10,
        holding_period=60,
        cost=COST_BASE,
        queue_policy="SUE_RANK"
    )

    cum_disc = (res_disc_30['equity_curve'].iloc[-1] - 1.0) * 100.0
    cum_hold = (res_hold_30['equity_curve'].iloc[-1] - 1.0) * 100.0

    print("=== SELECTION 1: 30 SLOTS, NON-FINANCIALS, Q5, 60D, SUE_RANK (#1 SHARPE IN DISCOVERY) ===")
    print("\n--- 2021-2023 DISCOVERY PERFORMANCE ---")
    print(f"CAGR: {res_disc_30['cagr_pct']:.2f}%")
    print(f"Nifty 500 CAGR: {res_disc_30['bench_cagr_pct']:.2f}%")
    print(f"Excess CAGR: {res_disc_30['excess_cagr_pct']:.2f}%")
    print(f"Sharpe: {res_disc_30['sharpe']:.3f}")
    print(f"Max Drawdown: {res_disc_30['max_dd_pct']:.2f}%")
    print(f"Trades Taken: {res_disc_30['taken_trades']} (Eligible: {res_disc_30['eligible_trades']})")
    print(f"Win Rate: {res_disc_30['win_rate_pct']:.1f}%")
    print(f"Cumulative Return: {cum_disc:.2f}%")
    print(f"Span Years: {res_disc_30['years']:.3f}")

    print("\n--- 2024-2026 TRUE OOS PERFORMANCE (SUE_RANK) ---")
    print(f"CAGR: {res_hold_30['cagr_pct']:.2f}%")
    print(f"Nifty 500 CAGR: {res_hold_30['bench_cagr_pct']:.2f}%")
    print(f"Excess CAGR: {res_hold_30['excess_cagr_pct']:.2f}%")
    print(f"Sharpe: {res_hold_30['sharpe']:.3f}")
    print(f"Max Drawdown: {res_hold_30['max_dd_pct']:.2f}%")
    print(f"Trades Taken: {res_hold_30['taken_trades']} (Eligible: {res_hold_30['eligible_trades']})")
    print(f"Win Rate: {res_hold_30['win_rate_pct']:.1f}%")
    print(f"Cumulative Return: {cum_hold:.2f}%")
    print(f"Span Years: {res_hold_30['years']:.3f}")

    print("\n--- 2024-2026 TRUE OOS PERFORMANCE (FIFO) ---")
    print(f"CAGR: {res_hold_30_fifo['cagr_pct']:.2f}%")
    print(f"Nifty 500 CAGR: {res_hold_30_fifo['bench_cagr_pct']:.2f}%")
    print(f"Excess CAGR: {res_hold_30_fifo['excess_cagr_pct']:.2f}%")
    print(f"Sharpe: {res_hold_30_fifo['sharpe']:.3f}")
    print(f"Trades: {res_hold_30_fifo['taken_trades']}")

    print("\n=== ALTERNATIVE 10 SLOTS (HIGHEST DISCOVERY CAGR) ===")
    print(f"Discovery: CAGR={res_disc_10['cagr_pct']:.2f}%, Excess={res_disc_10['excess_cagr_pct']:.2f}%, Sharpe={res_disc_10['sharpe']:.3f}, Trades={res_disc_10['taken_trades']}")
    print(f"Holdout:   CAGR={res_hold_10['cagr_pct']:.2f}%, Excess={res_hold_10['excess_cagr_pct']:.2f}%, Sharpe={res_hold_10['sharpe']:.3f}, Trades={res_hold_10['taken_trades']}")

if __name__ == "__main__":
    main()
