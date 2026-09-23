"""Controlled PEAD Exit-Rule Research Study.

Evaluates Hypotheses 0 through 6 strictly on 2021-2023 Discovery data.
Selects the optimal exit rule using predefined risk-adjusted criteria.
Then runs the selected exit rule ONCE on 2024-2026 True OOS data.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, DISCOVERY_END, HOLDOUT_START, COST_BASE
from src.data_loader import load_prices, load_benchmark

def get_atr(df, n=14):
    """Compute 14-day close-to-close volatility proxy."""
    tr = (df['Close'] - df['Close'].shift(1)).abs()
    return tr.rolling(n).mean()

def resolve_candidate_exit(r, px, bench, rule_type, param, next_filing_dict, all_events_by_symbol):
    """Resolve exit index, exit date, exit price, and holding days for a candidate trade."""
    entry_date = r.entry_date
    if entry_date not in px.index:
        return None
    entry_idx = px.index.get_loc(entry_date)
    max_h = 60
    
    # Check baseline 60d validity
    if entry_idx + max_h >= len(px):
        return None
    entry_px = px.Open.iloc[entry_idx]
    if entry_px <= 0:
        return None
        
    exit_idx = entry_idx + max_h # default
    exit_reason = "60D_HOLD_COMPLETE"
    
    # -------------------------------------------------------------
    # HYPOTHESIS 0: Baseline 60-Day Exit
    # -------------------------------------------------------------
    if rule_type == "H0_BASELINE":
        exit_idx = entry_idx + 60
        exit_reason = "60D_HOLD_COMPLETE"

    # -------------------------------------------------------------
    # HYPOTHESIS 1: Time Decay (Fixed Holding Horizon)
    # param: int horizon (10, 20, 30, 40, 60, 90)
    # -------------------------------------------------------------
    elif rule_type == "H1_TIME_DECAY":
        h = int(param)
        if entry_idx + h >= len(px):
            return None
        exit_idx = entry_idx + h
        exit_reason = f"{h}D_HOLD_COMPLETE"

    # -------------------------------------------------------------
    # HYPOTHESIS 2: Signal Decay / SUE Normalization
    # param: 'Q3_OR_LOWER', 'Q2_OR_LOWER', 'SUE_DROP_1SD'
    # -------------------------------------------------------------
    elif rule_type == "H2_SIGNAL_DECAY":
        # Check if stock has a subsequent filing within the 60-day window
        sym_events = all_events_by_symbol.get(r.symbol, [])
        subseq = [ev for ev in sym_events if ev['event_day'] > r.event_day and ev['entry_date'] <= px.index[entry_idx + max_h]]
        if subseq:
            next_ev = subseq[0]
            next_entry = next_ev['entry_date']
            if next_entry in px.index:
                next_idx = px.index.get_loc(next_entry)
                trigger = False
                if param == "Q3_OR_LOWER" and next_ev['q_exante_4q'] <= 3:
                    trigger = True
                elif param == "Q2_OR_LOWER" and next_ev['q_exante_4q'] <= 2:
                    trigger = True
                elif param == "SUE_DROP_1SD" and (r.sue - next_ev['sue']) >= 1.0:
                    trigger = True
                
                if trigger and next_idx < exit_idx and next_idx > entry_idx:
                    exit_idx = next_idx
                    exit_reason = f"SIGNAL_DECAY_{param}"

    # -------------------------------------------------------------
    # HYPOTHESIS 3: Adverse Abnormal-Return Reversal (Stop Loss)
    # param: float threshold (-0.05, -0.075, -0.10, -0.15)
    # -------------------------------------------------------------
    elif rule_type == "H3_ABNORMAL_STOP":
        thresh = float(param)
        b_entry_idx = bench.index.get_loc(entry_date) if entry_date in bench.index else None
        
        for k in range(1, max_h + 1):
            curr_idx = entry_idx + k
            curr_d = px.index[curr_idx]
            stock_ret = (px.Close.iloc[curr_idx] / entry_px) - 1.0
            
            # Benchmark return from entry
            if b_entry_idx is not None and curr_d in bench.index:
                b_curr_idx = bench.index.get_loc(curr_d)
                bench_ret = (bench.iloc[b_curr_idx] / bench.iloc[max(0, b_entry_idx - 1)]) - 1.0
            else:
                bench_ret = 0.0
                
            ar = stock_ret - bench_ret
            if ar <= thresh:
                exit_idx = curr_idx
                exit_reason = f"ABNORMAL_STOP_{thresh}"
                break

    # -------------------------------------------------------------
    # HYPOTHESIS 4: Profit / Drift Exhaustion (Take Profit)
    # param: float threshold (+0.10, +0.15, +0.20, +0.25)
    # -------------------------------------------------------------
    elif rule_type == "H4_ABNORMAL_PROFIT":
        thresh = float(param)
        b_entry_idx = bench.index.get_loc(entry_date) if entry_date in bench.index else None
        
        for k in range(1, max_h + 1):
            curr_idx = entry_idx + k
            curr_d = px.index[curr_idx]
            stock_ret = (px.Close.iloc[curr_idx] / entry_px) - 1.0
            
            if b_entry_idx is not None and curr_d in bench.index:
                b_curr_idx = bench.index.get_loc(curr_d)
                bench_ret = (bench.iloc[b_curr_idx] / bench.iloc[max(0, b_entry_idx - 1)]) - 1.0
            else:
                bench_ret = 0.0
                
            ar = stock_ret - bench_ret
            if ar >= thresh:
                exit_idx = curr_idx
                exit_reason = f"PROFIT_TAKE_{thresh}"
                break

    # -------------------------------------------------------------
    # HYPOTHESIS 5: Next-Earnings Exit
    # param: int days_before (1, 3, 5) or 'ON_ANNOUNCEMENT'
    # -------------------------------------------------------------
    elif rule_type == "H5_NEXT_EARNINGS":
        next_filing = next_filing_dict.get((r.symbol, r.period_end))
        if next_filing is not None and next_filing in px.index:
            nf_idx = px.index.get_loc(next_filing)
            days_before = int(param) if param != "ON_ANNOUNCEMENT" else 0
            target_idx = nf_idx - days_before
            if entry_idx < target_idx < exit_idx:
                exit_idx = target_idx
                exit_reason = f"NEXT_EARNINGS_{param}"

    # -------------------------------------------------------------
    # HYPOTHESIS 6: Volatility / Risk Exit
    # param: 'DAILY_JUMP_2.5SIGMA', 'DAILY_JUMP_3SIGMA', 'VOL_SPIKE_2X', 'CHANDELIER_2.5ATR'
    # -------------------------------------------------------------
    elif rule_type == "H6_VOLATILITY_RISK":
        # Compute entry historical 20-day daily return std
        past_returns = px.Close.iloc[max(0, entry_idx - 20):entry_idx].pct_change().dropna()
        sigma20 = past_returns.std() if len(past_returns) >= 10 else 0.02
        
        if param in ["DAILY_JUMP_2.5SIGMA", "DAILY_JUMP_3SIGMA"]:
            mult = 2.5 if param == "DAILY_JUMP_2.5SIGMA" else 3.0
            for k in range(1, max_h + 1):
                curr_idx = entry_idx + k
                daily_r = (px.Close.iloc[curr_idx] / px.Close.iloc[curr_idx - 1]) - 1.0
                if daily_r < -mult * sigma20:
                    exit_idx = curr_idx
                    exit_reason = param
                    break
        elif param == "VOL_SPIKE_2X":
            for k in range(10, max_h + 1):
                curr_idx = entry_idx + k
                recent_10 = px.Close.iloc[curr_idx - 10:curr_idx].pct_change().dropna()
                if len(recent_10) >= 8 and recent_10.std() > 2.0 * sigma20:
                    exit_idx = curr_idx
                    exit_reason = "VOL_SPIKE_2X"
                    break
        elif param == "CHANDELIER_2.5ATR":
            # ATR drop from peak close
            atr_series = get_atr(px)
            atr_val = atr_series.iloc[entry_idx] if not np.isnan(atr_series.iloc[entry_idx]) else (px.Close.iloc[entry_idx] * 0.02)
            peak_close = entry_px
            for k in range(1, max_h + 1):
                curr_idx = entry_idx + k
                curr_c = px.Close.iloc[curr_idx]
                if curr_c > peak_close:
                    peak_close = curr_c
                if curr_c <= (peak_close - 2.5 * atr_val):
                    exit_idx = curr_idx
                    exit_reason = "CHANDELIER_2.5ATR"
                    break

    exit_date = px.index[exit_idx]
    exit_px = px.Close.iloc[exit_idx]
    if exit_px <= 0:
        return None
    raw_ret = (exit_px / entry_px) - 1.0
    net_ret = raw_ret - COST_BASE
    holding_days = exit_idx - entry_idx
    
    return {
        "symbol": str(r.symbol),
        "entry_date": entry_date,
        "exit_date": exit_date,
        "entry_px": entry_px,
        "exit_px": exit_px,
        "raw_ret": raw_ret,
        "net_ret": net_ret,
        "holding_days": holding_days,
        "exit_reason": exit_reason,
        "sue": float(r.sue)
    }

def simulate_portfolio_from_resolved_candidates(cands_df, prices_dict, bench_series, max_slots=30):
    """Simulate slot allocation and mark-to-market daily returns."""
    if len(cands_df) == 0:
        return None
    cands_df = cands_df.sort_values(["entry_date", "sue"], ascending=[True, False]).copy()
    
    taken_trades = []
    active_positions = []
    
    for entry_d, group in cands_df.groupby("entry_date"):
        active_positions = [pos for pos in active_positions if pos["exit_date"] > entry_d]
        available_slots = max_slots - len(active_positions)
        if available_slots <= 0:
            continue
        order = group.sort_values("sue", ascending=False)
        to_take = order.head(available_slots)
        for _, tr in to_take.iterrows():
            pos_dict = dict(tr)
            active_positions.append(pos_dict)
            taken_trades.append(pos_dict)
            
    taken_df = pd.DataFrame(taken_trades)
    if len(taken_df) == 0:
        return None
        
    sim_start = taken_df["entry_date"].min()
    sim_end = taken_df["exit_date"].max()
    all_dates = bench_series[(bench_series.index >= sim_start) & (bench_series.index <= sim_end)].index
    
    daily_sleeve_returns = pd.Series(0.0, index=all_dates)
    for tr in taken_df.itertuples():
        sym = tr.symbol
        px = prices_dict[sym]
        w = px[(px.index >= tr.entry_date) & (px.index <= tr.exit_date)]
        if len(w) < 1:
            continue
        stock_daily = w["Close"].pct_change()
        stock_daily.iloc[0] = (w["Close"].iloc[0] / tr.entry_px) - 1.0
        stock_daily.iloc[-1] = stock_daily.iloc[-1] - COST_BASE
        aligned_ret = stock_daily.reindex(all_dates, fill_value=0.0)
        daily_sleeve_returns += aligned_ret / float(max_slots)
        
    equity_curve = (1.0 + daily_sleeve_returns).cumprod()
    total_days = (all_dates[-1] - all_dates[0]).days
    years = total_days / 365.25
    cagr = (float(equity_curve.iloc[-1]) ** (1.0 / years)) - 1.0 if years > 0 else 0.0
    daily_std = float(daily_sleeve_returns.std())
    ann_vol = daily_std * np.sqrt(250)
    sharpe = (float(daily_sleeve_returns.mean()) * 250.0 / ann_vol) if ann_vol > 1e-6 else 0.0
    
    roll_max = equity_curve.cummax()
    dd_series = (equity_curve / roll_max) - 1.0
    max_dd = float(dd_series.min())
    
    b_start = bench_series.loc[all_dates[0]]
    b_end = bench_series.loc[all_dates[-1]]
    bench_cagr = ((b_end / b_start) ** (1.0 / years)) - 1.0 if years > 0 else 0.0
    excess_cagr = cagr - bench_cagr
    
    # Monthly returns for worst month
    m_returns = daily_sleeve_returns.resample('ME').apply(lambda s: (1.0 + s).prod() - 1.0)
    worst_month = float(m_returns.min()) * 100.0 if len(m_returns) > 0 else 0.0
    worst_month_date = m_returns.idxmin().strftime('%Y-%m') if len(m_returns) > 0 else ""
    
    # Yearly returns for worst year
    y_returns = daily_sleeve_returns.resample('YE').apply(lambda s: (1.0 + s).prod() - 1.0)
    worst_year = float(y_returns.min()) * 100.0 if len(y_returns) > 0 else 0.0
    worst_year_date = y_returns.idxmin().year if len(y_returns) > 0 else ""

    return {
        "taken_trades": len(taken_df),
        "cagr_pct": cagr * 100.0,
        "bench_cagr_pct": bench_cagr * 100.0,
        "excess_cagr_pct": excess_cagr * 100.0,
        "sharpe": sharpe,
        "ann_vol_pct": ann_vol * 100.0,
        "max_dd_pct": max_dd * 100.0,
        "win_rate_pct": float((taken_df["net_ret"] > 0).mean() * 100.0),
        "avg_trade_pct": float(taken_df["net_ret"].mean() * 100.0),
        "median_trade_pct": float(taken_df["net_ret"].median() * 100.0),
        "avg_holding_days": float(taken_df["holding_days"].mean()),
        "cumulative_ret_pct": (float(equity_curve.iloc[-1]) - 1.0) * 100.0,
        "worst_month": f"{worst_month_date} ({worst_month:+.2f}%)",
        "worst_year": f"{worst_year_date} ({worst_year:+.2f}%)",
        "years": years,
        "equity_curve": equity_curve,
        "daily_returns": daily_sleeve_returns
    }

def main():
    print("=== CONTROLLED PEAD EXIT-RULE RESEARCH STUDY ===")
    events_path = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante", "pead_v2_events.csv")
    ev = pd.read_csv(events_path, parse_dates=["event_day", "entry_date", "period_end"])
    ev = ev[(ev.q_exante_4q == 5) & (ev.is_fin == False)].copy() # Non-Financials Q5
    
    px_dict = load_prices()
    bench = load_benchmark()
    
    # Pre-build lookup for next filings per symbol
    all_events_by_symbol = {}
    for sym, group in ev.sort_values("event_day").groupby("symbol"):
        all_events_by_symbol[sym] = group.to_dict('records')
        
    next_filing_dict = {}
    for sym, group in ev.sort_values("event_day").groupby("symbol"):
        recs = group.to_dict('records')
        for i in range(len(recs) - 1):
            next_filing_dict[(sym, recs[i]['period_end'])] = recs[i+1]['entry_date']
            
    # Strictly partition Discovery (<= 2023-12-31)
    disc_ev = ev[ev.event_day <= DISCOVERY_END].copy()
    hold_ev = ev[ev.event_day >= HOLDOUT_START].copy()
    
    print(f"Discovery Q5 Non-Financial Events: {len(disc_ev)}")
    print(f"Holdout Q5 Non-Financial Events: {len(hold_ev)}")
    
    # Predefined Hypotheses
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
    
    disc_results = []
    for rule_type, param, label in hypotheses:
        # Resolve candidate trades on discovery events
        resolved = []
        for r in disc_ev.itertuples():
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
            disc_results.append({
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
                "worst_month": sim_res["worst_month"],
                "worst_year": sim_res["worst_year"]
            })
            
    df_disc = pd.DataFrame(disc_results)
    out_csv = os.path.join(PEAD_V2_ROOT, "phase_08_backtest", "EXIT_RULE_DISCOVERY_STUDY.csv")
    df_disc.to_csv(out_csv, index=False)
    
    print("\n=== DISCOVERY (2021-2023) EXIT RULE RESULTS (SORTED BY SHARPE) ===")
    print(df_disc[["label", "cagr_pct", "excess_cagr_pct", "sharpe", "max_dd_pct", "win_rate_pct", "avg_trade_pct", "trades", "avg_holding_days"]].sort_values("sharpe", ascending=False).to_string(index=False))

    print("\n=== DISCOVERY (2021-2023) EXIT RULE RESULTS (SORTED BY EXCESS CAGR) ===")
    print(df_disc[["label", "cagr_pct", "excess_cagr_pct", "sharpe", "max_dd_pct", "win_rate_pct", "avg_trade_pct", "trades", "avg_holding_days"]].sort_values("excess_cagr_pct", ascending=False).to_string(index=False))

if __name__ == "__main__":
    main()
