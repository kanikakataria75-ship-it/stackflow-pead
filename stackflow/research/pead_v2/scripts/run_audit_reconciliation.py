"""Comprehensive Audit Reconciliation Engine for StackFlow PEAD V2.

Computes exact numbers and generates data for AUDIT 06 through 18, and PEAD_V2_AUDIT_FINAL.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, COST_BASE, DISCOVERY_END, HOLDOUT_START, BENCHMARK_FILE
from src.data_loader import load_prices, load_benchmark

def run_reconciliation():
    print("=== RUNNING AUDIT RECONCILIATION SUITE ===")
    
    # 1. Load Master Trade Ledger
    ledger_path = os.path.join(PEAD_V2_ROOT, "trade_ledger_pead_v2_audited.csv")
    ledger = pd.read_csv(ledger_path, parse_dates=["entry_date", "exit_date", "filing_timestamp"])
    print(f"Loaded Audited Ledger: {len(ledger)} trades.")
    
    # Check no duplicate trade IDs
    assert ledger["trade_id"].nunique() == len(ledger), "Duplicate trade IDs detected!"
    
    # Ensure return columns are numeric if formatted with %
    for col in ["net_return", "gross_return"]:
        if col in ledger.columns and not pd.api.types.is_numeric_dtype(ledger[col]):
            ledger[col] = ledger[col].astype(str).str.rstrip('%').astype(float) / 100.0
    
    px_dict = load_prices()
    bench = load_benchmark()
    
    # Rebuild daily MtM equity curve directly from trade ledger
    sim_start = ledger["entry_date"].min()
    sim_end = ledger["exit_date"].max()
    all_dates = bench[(bench.index >= sim_start) & (bench.index <= sim_end)].index
    
    max_slots = 30
    daily_sleeve_returns = pd.Series(0.0, index=all_dates)
    
    # Active slot tracking matrix: dates x 30 slots
    slot_occupancy = pd.DataFrame(0, index=all_dates, columns=range(1, max_slots + 1))
    
    for tr in ledger.itertuples():
        sym = tr.symbol
        px = px_dict[sym]
        w = px[(px.index >= tr.entry_date) & (px.index <= tr.exit_date)]
        if len(w) < 1:
            continue
            
        stock_daily = w["Close"].pct_change()
        stock_daily.iloc[0] = (w["Close"].iloc[0] / tr.entry_price) - 1.0
        stock_daily.iloc[-1] = stock_daily.iloc[-1] - tr.transaction_cost
        
        aligned_ret = stock_daily.reindex(all_dates, fill_value=0.0)
        daily_sleeve_returns += aligned_ret / float(max_slots)
        
        # Track slot occupancy
        slot_dates = all_dates[(all_dates >= tr.entry_date) & (all_dates <= tr.exit_date)]
        slot_occupancy.loc[slot_dates, tr.slot] += 1
        
    # Check overlapping slot violations: max occupancy per slot should be <= 1 (except possibly handover on exit_date)
    # Actually if exit_date was free for new entry on same day, let's check max occupancy
    max_slot_concurrency = slot_occupancy.values.max()
    print(f"Maximum slot concurrency observed across any single day: {max_slot_concurrency}")
    
    equity_curve = (1.0 + daily_sleeve_returns).cumprod()
    
    total_days = (all_dates[-1] - all_dates[0]).days
    years = total_days / 365.25
    cagr = (float(equity_curve.iloc[-1]) ** (1.0 / years)) - 1.0
    daily_std = float(daily_sleeve_returns.std())
    ann_vol = daily_std * np.sqrt(250)
    sharpe = float(daily_sleeve_returns.mean() * 250.0 / ann_vol)
    
    roll_max = equity_curve.cummax()
    dd_series = (equity_curve / roll_max) - 1.0
    max_dd = float(dd_series.min())
    
    # Benchmark
    b_series = bench.loc[all_dates]
    bench_cagr = ((b_series.iloc[-1] / b_series.iloc[0]) ** (1.0 / years)) - 1.0
    bench_dd = (b_series / b_series.cummax()) - 1.0
    bench_max_dd = float(bench_dd.min())
    
    print("\n--- RECONSTRUCTED METRICS ---")
    print(f"Total Trades: {len(ledger)}")
    print(f"CAGR: {cagr*100:.2f}% (Reported: 16.83%)")
    print(f"Benchmark CAGR: {bench_cagr*100:.2f}% (Reported: 10.26%)")
    print(f"Excess CAGR: {(cagr - bench_cagr)*100:.2f}% (Reported: +5.78% to +6.57%)")
    print(f"Max DD: {max_dd*100:.2f}% (Reported: -25.12%)")
    print(f"Sharpe: {sharpe:.3f} (Reported: 1.017)")
    print(f"Annualized Volatility: {ann_vol*100:.2f}% (Reported: 16.82%)")
    
    # 2. Trade PnL vs Portfolio PnL reconciliation
    sum_trade_pnl = ledger["portfolio_pnl"].sum()
    sum_net_ret = ledger["net_return"].sum()
    arithmetic_avg_net_ret = ledger["net_return"].mean()
    win_rate = (ledger["net_return"] > 0).mean()
    
    print("\n--- P&L RECONCILIATION ---")
    print(f"Sum of Trade Net Returns: {sum_net_ret*100:.2f}%")
    print(f"Sum of Portfolio PnL (1/30 sleeve sum): {sum_trade_pnl*100:.2f}%")
    print(f"Arithmetic Mean Net Trade Return: {arithmetic_avg_net_ret*100:.2f}%")
    print(f"Win Rate: {win_rate*100:.1f}%")
    
    # 3. Year-by-Year Performance
    yearly_rows = []
    ledger["entry_year"] = ledger["entry_date"].dt.year
    for yr in range(2021, 2027):
        sub_dates = all_dates[all_dates.year == yr]
        if len(sub_dates) < 5:
            continue
        sub_ret = daily_sleeve_returns.loc[sub_dates]
        yr_eq = (1.0 + sub_ret).cumprod()
        strat_yr_ret = (yr_eq.iloc[-1] - 1.0) * 100.0
        
        bench_sub = bench.loc[sub_dates]
        bench_yr_ret = ((bench_sub.iloc[-1] / bench_sub.iloc[0]) - 1.0) * 100.0
        
        yr_max_dd = ((yr_eq / yr_eq.cummax()) - 1.0).min() * 100.0
        n_yr_trades = (ledger["entry_year"] == yr).sum()
        
        yearly_rows.append({
            "year": yr,
            "strategy_return_pct": round(strat_yr_ret, 2),
            "benchmark_return_pct": round(bench_yr_ret, 2),
            "excess_return_pct": round(strat_yr_ret - bench_yr_ret, 2),
            "trade_count": int(n_yr_trades),
            "max_drawdown_pct": round(yr_max_dd, 2)
        })
    df_yearly = pd.DataFrame(yearly_rows)
    print("\n--- YEAR-BY-YEAR PERFORMANCE ---")
    print(df_yearly.to_string(index=False))
    
    # 4. Discovery vs Holdout Performance
    disc_dates = all_dates[all_dates <= DISCOVERY_END]
    hold_dates = all_dates[all_dates >= HOLDOUT_START]
    
    # Discovery
    d_ret = daily_sleeve_returns.loc[disc_dates]
    d_eq = (1.0 + d_ret).cumprod()
    d_yrs = (disc_dates[-1] - disc_dates[0]).days / 365.25
    d_cagr = ((d_eq.iloc[-1] ** (1.0 / d_yrs)) - 1.0) * 100.0
    d_bench = bench.loc[disc_dates]
    d_bench_cagr = (((d_bench.iloc[-1] / d_bench.iloc[0]) ** (1.0 / d_yrs)) - 1.0) * 100.0
    d_sharpe = float(d_ret.mean() * 250.0 / (d_ret.std() * np.sqrt(250)))
    d_dd = ((d_eq / d_eq.cummax()) - 1.0).min() * 100.0
    d_trades = (ledger["entry_date"] <= DISCOVERY_END).sum()
    d_win = (ledger[ledger["entry_date"] <= DISCOVERY_END]["net_return"] > 0).mean() * 100.0
    
    # Holdout
    h_ret = daily_sleeve_returns.loc[hold_dates]
    h_eq = (1.0 + h_ret).cumprod()
    h_yrs = (hold_dates[-1] - hold_dates[0]).days / 365.25
    h_cagr = ((h_eq.iloc[-1] ** (1.0 / h_yrs)) - 1.0) * 100.0
    h_bench = bench.loc[hold_dates]
    h_bench_cagr = (((h_bench.iloc[-1] / h_bench.iloc[0]) ** (1.0 / h_yrs)) - 1.0) * 100.0
    h_sharpe = float(h_ret.mean() * 250.0 / (h_ret.std() * np.sqrt(250)))
    h_dd = ((h_eq / h_eq.cummax()) - 1.0).min() * 100.0
    h_trades = (ledger["entry_date"] >= HOLDOUT_START).sum()
    h_win = (ledger[ledger["entry_date"] >= HOLDOUT_START]["net_return"] > 0).mean() * 100.0
    
    print("\n--- DISCOVERY VS HOLDOUT BREAKDOWN ---")
    print(f"Discovery (2021-2023): CAGR = {d_cagr:+.2f}%, Nifty = {d_bench_cagr:+.2f}%, Excess = {d_cagr-d_bench_cagr:+.2f}%, Sharpe = {d_sharpe:.2f}, Max DD = {d_dd:.2f}%, Trades = {d_trades}, Win = {d_win:.1f}%")
    print(f"Holdout (2024-2026):   CAGR = {h_cagr:+.2f}%, Nifty = {h_bench_cagr:+.2f}%, Excess = {h_cagr-h_bench_cagr:+.2f}%, Sharpe = {h_sharpe:.2f}, Max DD = {h_dd:.2f}%, Trades = {h_trades}, Win = {h_win:.1f}%")
    
    # 5. Extreme Trades Sensitivity
    sorted_trades = ledger.sort_values("net_return", ascending=False).reset_index(drop=True)
    top20 = sorted_trades.head(20)
    bot20 = sorted_trades.tail(20)
    
    def simulate_dropped_trades(drop_indices):
        d_ret = pd.Series(0.0, index=all_dates)
        for i, tr in enumerate(ledger.itertuples()):
            if i in drop_indices:
                continue
            sym = tr.symbol
            px = px_dict[sym]
            w = px[(px.index >= tr.entry_date) & (px.index <= tr.exit_date)]
            if len(w) < 1:
                continue
            s_ret = w["Close"].pct_change()
            s_ret.iloc[0] = (w["Close"].iloc[0] / tr.entry_price) - 1.0
            s_ret.iloc[-1] = s_ret.iloc[-1] - tr.transaction_cost
            aligned = s_ret.reindex(all_dates, fill_value=0.0)
            d_ret += aligned / float(max_slots)
        eq = (1.0 + d_ret).cumprod()
        drop_cagr = (float(eq.iloc[-1]) ** (1.0 / years)) - 1.0
        return drop_cagr * 100.0
        
    top1_idx = set(sorted_trades.head(1).index)
    top5_idx = set(sorted_trades.head(5).index)
    top10_idx = set(sorted_trades.head(10).index)
    
    cagr_all = cagr * 100.0
    cagr_drop1 = simulate_dropped_trades(top1_idx)
    cagr_drop5 = simulate_dropped_trades(top5_idx)
    cagr_drop10 = simulate_dropped_trades(top10_idx)
    
    print("\n--- EXTREME TRADES SENSITIVITY ---")
    print(f"All 579 Trades CAGR:            {cagr_all:.2f}%")
    print(f"Drop Top 1 Trade CAGR:          {cagr_drop1:.2f}% (delta: {cagr_drop1 - cagr_all:+.2f}pp)")
    print(f"Drop Top 5 Trades CAGR:         {cagr_drop5:.2f}% (delta: {cagr_drop5 - cagr_all:+.2f}pp)")
    print(f"Drop Top 10 Trades CAGR:        {cagr_drop10:.2f}% (delta: {cagr_drop10 - cagr_all:+.2f}pp)")
    
    # 6. Cost Sensitivity
    def simulate_cost(cost_val):
        d_ret = pd.Series(0.0, index=all_dates)
        for tr in ledger.itertuples():
            sym = tr.symbol
            px = px_dict[sym]
            w = px[(px.index >= tr.entry_date) & (px.index <= tr.exit_date)]
            if len(w) < 1:
                continue
            s_ret = w["Close"].pct_change()
            s_ret.iloc[0] = (w["Close"].iloc[0] / tr.entry_price) - 1.0
            s_ret.iloc[-1] = s_ret.iloc[-1] - cost_val
            aligned = s_ret.reindex(all_dates, fill_value=0.0)
            d_ret += aligned / float(max_slots)
        eq = (1.0 + d_ret).cumprod()
        c = (float(eq.iloc[-1]) ** (1.0 / years)) - 1.0
        sh = float(d_ret.mean() * 250.0 / (d_ret.std() * np.sqrt(250)))
        dd = ((eq / eq.cummax()) - 1.0).min() * 100.0
        return c * 100.0, sh, dd
        
    c_low, sh_low, dd_low = simulate_cost(0.0030)
    c_base, sh_base, dd_base = simulate_cost(0.00585)
    c_high, sh_high, dd_high = simulate_cost(0.0100)
    
    print("\n--- COST SENSITIVITY ---")
    print(f"Low Friction (0.30%):  CAGR = {c_low:.2f}%, Sharpe = {sh_low:.3f}, Max DD = {dd_low:.2f}%")
    print(f"Base Friction (0.585%): CAGR = {c_base:.2f}%, Sharpe = {sh_base:.3f}, Max DD = {dd_base:.2f}%")
    print(f"High Friction (1.00%): CAGR = {c_high:.2f}%, Sharpe = {sh_high:.3f}, Max DD = {dd_high:.2f}%")
    
    # 7. Generate Random 50 Trades Audit Sample
    np.random.seed(42)
    sample_indices = np.random.choice(len(ledger), size=50, replace=False)
    sample_trades = ledger.iloc[sample_indices].copy().sort_values("entry_date").reset_index(drop=True)
    sample_trades["sample_id"] = [f"SMP_{i+1:02d}" for i in range(len(sample_trades))]
    sample_path = os.path.join(PEAD_V2_ROOT, "AUDIT_14_RANDOM_TRADES.csv")
    sample_trades.to_csv(sample_path, index=False)
    print(f"\nSaved 50 random audited trades to {sample_path}")
    
    return {
        "cagr": cagr * 100.0,
        "bench_cagr": bench_cagr * 100.0,
        "excess_cagr": (cagr - bench_cagr) * 100.0,
        "sharpe": sharpe,
        "ann_vol": ann_vol * 100.0,
        "max_dd": max_dd * 100.0,
        "bench_max_dd": bench_max_dd * 100.0,
        "n_trades": len(ledger),
        "df_yearly": df_yearly,
        "disc": {"cagr": d_cagr, "bench_cagr": d_bench_cagr, "excess": d_cagr-d_bench_cagr, "sharpe": d_sharpe, "max_dd": d_dd, "n": d_trades, "win": d_win},
        "hold": {"cagr": h_cagr, "bench_cagr": h_bench_cagr, "excess": h_cagr-h_bench_cagr, "sharpe": h_sharpe, "max_dd": h_dd, "n": h_trades, "win": h_win},
        "top20": top20,
        "bot20": bot20,
        "drops": {"drop1": cagr_drop1, "drop5": cagr_drop5, "drop10": cagr_drop10},
        "costs": {"low": (c_low, sh_low, dd_low), "base": (c_base, sh_base, dd_base), "high": (c_high, sh_high, dd_high)}
    }

if __name__ == "__main__":
    run_reconciliation()
