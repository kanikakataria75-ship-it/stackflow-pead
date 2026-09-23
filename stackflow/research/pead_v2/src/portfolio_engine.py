"""Event-driven, point-in-time portfolio backtesting engine."""
import numpy as np
import pandas as pd


def run_portfolio_backtest(trades_df, prices_dict, benchmark_series,
                           max_slots=20, holding_period=60, cost=0.00585,
                           queue_policy="FIFO", capital=1_000_000.0):
    """Simulate a multi-slot, event-driven portfolio.
    
    Parameters:
    - trades_df: DataFrame of qualifying events sorted by entry_date.
    - prices_dict: Dict of {symbol: DataFrame(OHLCV)}.
    - benchmark_series: Series of daily Nifty 500 closes.
    - max_slots: Maximum concurrent positions (e.g. 10, 20, 30).
    - holding_period: Holding period in trading days (e.g. 20, 40, 60, 90).
    - cost: Round-trip cost per trade (0.00585 = 0.585%).
    - queue_policy: 'FIFO' (first-come) or 'SUE_RANK' (priority by SUE magnitude).
    """
    if len(trades_df) == 0:
        return None
        
    trades_df = trades_df.sort_values(["entry_date", "sue"], ascending=[True, False]).copy()
    
    # 1. Resolve exact exit dates and returns per candidate trade
    valid_candidates = []
    for r in trades_df.itertuples():
        sym = str(r.symbol)
        if sym not in prices_dict:
            continue
        px = prices_dict[sym]
        if r.entry_date not in px.index:
            continue
            
        entry_idx = px.index.get_loc(r.entry_date)
        exit_idx = entry_idx + holding_period
        if exit_idx >= len(px):
            # Incomplete holding window
            continue
            
        exit_date = px.index[exit_idx]
        entry_px = px.Open.iloc[entry_idx]
        exit_px = px.Close.iloc[exit_idx]
        if entry_px <= 0 or exit_px <= 0:
            continue
            
        raw_ret = (exit_px / entry_px) - 1.0
        net_ret = raw_ret - cost
        
        valid_candidates.append({
            "symbol": sym,
            "entry_date": r.entry_date,
            "exit_date": exit_date,
            "entry_px": entry_px,
            "exit_px": exit_px,
            "raw_ret": raw_ret,
            "net_ret": net_ret,
            "sue": float(r.sue),
            "turnover20": float(getattr(r, "turnover20", np.nan))
        })
        
    cands_df = pd.DataFrame(valid_candidates)
    if len(cands_df) == 0:
        return None
        
    # 2. Simulate slot allocation with strict slot release
    # A slot exiting on day d at Close must NOT fund an entry at day d Open.
    # It only frees up for new entries from the next session's Open onward.
    taken_trades = []
    active_positions = []
    
    # Group candidates by entry date
    for entry_d, group in cands_df.groupby("entry_date"):
        # Positions exiting on or after entry_d are still active during entry_d Open
        active_positions = [pos for pos in active_positions if pos["exit_date"] >= entry_d]
        available_slots = max_slots - len(active_positions)
        
        if available_slots <= 0:
            continue
            
        if queue_policy == "SUE_RANK":
            order = group.sort_values("sue", ascending=False)
        else: # FIFO
            order = group
            
        to_take = order.head(available_slots)
        for _, tr in to_take.iterrows():
            pos_dict = dict(tr)
            active_positions.append(pos_dict)
            taken_trades.append(pos_dict)
            
    taken_df = pd.DataFrame(taken_trades)
    if len(taken_df) == 0:
        return None
        
    # 3. Construct daily NAV series using share-and-cash accounting
    sim_start = taken_df["entry_date"].min()
    sim_end = taken_df["exit_date"].max()
    all_dates = benchmark_series[(benchmark_series.index >= sim_start) &
                                 (benchmark_series.index <= sim_end)].index
                                 
    half_cost = cost / 2.0
    cash = capital
    open_positions = []
    nav_history = []
    trades_by_entry = taken_df.groupby("entry_date")
    
    for t in all_dates:
        # Prior close NAV (capital on day 1)
        prior_nav = nav_history[-1] if len(nav_history) > 0 else capital
        target_pos_val = prior_nav / float(max_slots)
        
        # Morning Open: execute new entries
        if t in trades_by_entry.groups:
            todays_entries = trades_by_entry.get_group(t)
            for _, tr in todays_entries.iterrows():
                invest_cash = min(cash, target_pos_val)
                if invest_cash > 0 and tr["entry_px"] > 0:
                    # Buy shares, deducting half round-trip cost on entry
                    shares = (invest_cash / (1.0 + half_cost)) / tr["entry_px"]
                    cost_paid = shares * tr["entry_px"] * (1.0 + half_cost)
                    cash -= cost_paid
                    open_positions.append({
                        "symbol": tr["symbol"],
                        "shares": shares,
                        "entry_px": tr["entry_px"],
                        "entry_date": tr["entry_date"],
                        "exit_date": tr["exit_date"]
                    })
                    
        # Evening Close: mark-to-market and execute exits
        surviving = []
        stock_val = 0.0
        for pos in open_positions:
            px = prices_dict.get(pos["symbol"])
            # Audit fix: on benchmark sessions the stock file lacks (e.g. the 2024 special
            # Saturday sessions), carry the last available close forward. Falling back to the
            # entry price created spurious +/-15.8% NAV days (2024-01-20/23) and inflated vol.
            if px is not None and t in px.index:
                close_px = float(px.Close.loc[t])
            elif px is not None:
                last = px.Close.loc[:t]
                close_px = float(last.iloc[-1]) if len(last) else pos["entry_px"]
            else:
                close_px = pos["entry_px"]
            
            if pos["exit_date"] == t:
                # Sell shares, deducting second half of round-trip cost on exit
                proceeds = pos["shares"] * close_px * (1.0 - half_cost)
                cash += proceeds
            else:
                stock_val += pos["shares"] * close_px
                surviving.append(pos)
                
        open_positions = surviving
        nav = cash + stock_val
        nav_history.append(nav)
        
    nav_series = pd.Series(nav_history, index=all_dates)
    equity_curve = nav_series / capital
    daily_returns = nav_series.pct_change().fillna(0.0)
    
    # 4. Performance metrics (Honest Discrete Share/Cash Mark-to-Market)
    total_days = (all_dates[-1] - all_dates[0]).days
    years = total_days / 365.25
    if years <= 0:
        return None
        
    final_nav = float(nav_series.iloc[-1])
    cagr = ((final_nav / capital) ** (1.0 / years)) - 1.0
    daily_std = float(daily_returns.std())
    ann_vol = daily_std * np.sqrt(252)
    daily_mean = float(daily_returns.mean())
    sharpe0 = (daily_mean * 252.0 / ann_vol) if ann_vol > 1e-6 else 0.0
    sharpe6 = ((daily_mean * 252.0 - 0.06) / ann_vol) if ann_vol > 1e-6 else 0.0
    
    roll_max = nav_series.cummax()
    dd_series = (nav_series / roll_max) - 1.0
    max_dd = float(dd_series.min())
    
    # Benchmark performance over same dates
    b_start = benchmark_series.loc[all_dates[0]]
    b_end = benchmark_series.loc[all_dates[-1]]
    bench_cagr = ((b_end / b_start) ** (1.0 / years)) - 1.0
    bench_daily = benchmark_series.loc[all_dates].pct_change().dropna()
    bench_std = float(bench_daily.std())
    bench_vol = bench_std * np.sqrt(252)
    bench_mean = float(bench_daily.mean())
    bench_sharpe0 = (bench_mean * 252.0 / bench_vol) if bench_vol > 1e-6 else 0.0
    bench_sharpe6 = ((bench_mean * 252.0 - 0.06) / bench_vol) if bench_vol > 1e-6 else 0.0
    bench_roll_max = (benchmark_series.loc[all_dates] / benchmark_series.loc[all_dates].cummax()) - 1.0
    bench_max_dd = float(bench_roll_max.min())
    
    # Trade-level statistics
    n_trades = len(taken_df)
    win_rate = float((taken_df["net_ret"] > 0).mean())
    avg_net_ret = float(taken_df["net_ret"].mean())
    avg_gross_ret = float(taken_df["raw_ret"].mean())
    wins = taken_df[taken_df["net_ret"] > 0]["net_ret"]
    losses = taken_df[taken_df["net_ret"] <= 0]["net_ret"]
    avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
    avg_loss = float(losses.mean()) if len(losses) > 0 else 0.0
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) > 0 and abs(losses.sum()) > 0 else np.nan
    
    return {
        "max_slots": max_slots,
        "holding_period": holding_period,
        "queue_policy": queue_policy,
        "cost": cost,
        "eligible_trades": len(cands_df),
        "taken_trades": n_trades,
        "capacity_utilization_pct": float(n_trades / len(cands_df) * 100),
        "years": round(years, 2),
        "cagr_pct": float(cagr * 100),
        "ann_vol_pct": float(ann_vol * 100),
        "sharpe": round(sharpe0, 3),
        "sharpe_rf6": round(sharpe6, 3),
        "max_dd_pct": float(max_dd * 100),
        "bench_cagr_pct": float(bench_cagr * 100),
        "bench_vol_pct": float(bench_vol * 100),
        "bench_sharpe": round(bench_sharpe0, 3),
        "bench_sharpe_rf6": round(bench_sharpe6, 3),
        "bench_max_dd_pct": float(bench_max_dd * 100),
        "excess_cagr_pct": float((cagr - bench_cagr) * 100),
        "win_rate_pct": float(win_rate * 100),
        "avg_gross_trade_pct": float(avg_gross_ret * 100),
        "avg_net_trade_pct": float(avg_net_ret * 100),
        "avg_win_pct": float(avg_win * 100),
        "avg_loss_pct": float(avg_loss * 100),
        "profit_factor": round(profit_factor, 2) if np.isfinite(profit_factor) else np.nan,
        "taken_df": taken_df,
        "equity_curve": equity_curve,
        "nav_series": nav_series,
        "daily_returns": daily_returns
    }
