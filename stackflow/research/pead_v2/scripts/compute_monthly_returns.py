import os
import sys
import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.data_loader import load_prices, load_benchmark

def main():
    ledger_path = os.path.join(os.path.dirname(__file__), "..", "trade_ledger_pead_v2_audited.csv")
    ledger = pd.read_csv(ledger_path, parse_dates=["entry_date", "exit_date"])
    px_dict = load_prices()
    bench500 = load_benchmark()

    # Download Nifty 50
    nifty50_df = yf.download("^NSEI", start="2021-01-01", end="2026-09-20", auto_adjust=False, progress=False)
    if isinstance(nifty50_df.columns, pd.MultiIndex):
        nifty50_df.columns = nifty50_df.columns.get_level_values(0)
    nifty50 = nifty50_df["Close"].dropna()

    # All trading days from Aug 2021 through Aug 2026
    all_trading_dates = bench500[(bench500.index >= "2021-08-01") & (bench500.index <= "2026-08-31")].index

    # Daily portfolio returns
    daily_pead = pd.Series(0.0, index=all_trading_dates)
    for tr in ledger.itertuples():
        sym = tr.symbol
        if sym not in px_dict:
            continue
        px = px_dict[sym]
        w = px[(px.index >= tr.entry_date) & (px.index <= tr.exit_date)]
        if len(w) < 1:
            continue
        stock_daily = w["Close"].pct_change()
        stock_daily.iloc[0] = (w["Close"].iloc[0] / tr.entry_price) - 1.0
        stock_daily.iloc[-1] = stock_daily.iloc[-1] - tr.transaction_cost
        aligned_ret = stock_daily.reindex(all_trading_dates, fill_value=0.0)
        daily_pead += aligned_ret / 30.0

    # Monthly breakdown
    months = pd.date_range("2021-08-01", "2026-08-31", freq="MS").strftime("%Y-%m")

    rows = []
    for ym in months:
        m_dates = all_trading_dates[all_trading_dates.strftime("%Y-%m") == ym]
        if len(m_dates) == 0:
            continue
        
        # PEAD compounded daily return for this month
        pead_m = (1.0 + daily_pead.loc[m_dates]).prod() - 1.0
        
        # Benchmark: end-of-month / end-of-previous-month
        prev_dates = bench500[bench500.index < m_dates[0]].index
        p_date = prev_dates[-1]
        n500_m = (bench500.loc[m_dates[-1]] / bench500.loc[p_date]) - 1.0
        n50_m = (nifty50.loc[m_dates[-1]] / nifty50.loc[p_date]) - 1.0
        
        rows.append({
            "month": ym,
            "pead": pead_m,
            "nifty50": n50_m,
            "nifty500": n500_m,
            "xs_nifty50": pead_m - n50_m,
            "xs_nifty500": pead_m - n500_m
        })

    df = pd.DataFrame(rows)
    
    print("MONTHLY_TABLE_START")
    for idx, r in df.iterrows():
        p_str = f"{r['pead']*100:+.2f}%"
        n50_str = f"{r['nifty50']*100:+.2f}%"
        n500_str = f"{r['nifty500']*100:+.2f}%"
        xs50_str = f"{r['xs_nifty50']*100:+.2f}%"
        xs500_str = f"{r['xs_nifty500']*100:+.2f}%"
        print(f"{r['month']} | {p_str} | {n50_str} | {n500_str} | {xs50_str} | {xs500_str}")
    print("MONTHLY_TABLE_END")

    print("\n--- STATS ---")
    for col, name in [("pead", "PEAD V2"), ("nifty50", "Nifty 50"), ("nifty500", "Nifty 500")]:
        s = df[col]
        pos = int((s > 0).sum())
        neg = int((s < 0).sum())
        zero = int((s == 0).sum())
        avg = s.mean() * 100
        med = s.median() * 100
        best_idx = s.idxmax()
        worst_idx = s.idxmin()
        best_val = s.loc[best_idx] * 100
        best_m = df.loc[best_idx, "month"]
        worst_val = s.loc[worst_idx] * 100
        worst_m = df.loc[worst_idx, "month"]
        cum = ((1.0 + s).prod() - 1.0) * 100
        years = len(df) / 12.0
        cagr = (((1.0 + s).prod()) ** (1.0 / years) - 1.0) * 100
        print(f"[{name}]")
        print(f"  Positive Months: {pos}")
        print(f"  Negative Months: {neg}")
        print(f"  Zero Months: {zero}")
        print(f"  Average Monthly Return: {avg:+.2f}%")
        print(f"  Median Monthly Return:  {med:+.2f}%")
        print(f"  Best Month:  {best_m} ({best_val:+.2f}%)")
        print(f"  Worst Month: {worst_m} ({worst_val:+.2f}%)")
        print(f"  Cumulative Return: {cum:+.2f}%")
        print(f"  CAGR (over {len(df)} months / {years:.2f} yrs): {cagr:+.2f}%")

    # Spreads summary
    for col, name in [("xs_nifty50", "PEAD minus Nifty 50"), ("xs_nifty500", "PEAD minus Nifty 500")]:
        s = df[col]
        pos = int((s > 0).sum())
        neg = int((s < 0).sum())
        avg = s.mean() * 100
        med = s.median() * 100
        best_idx = s.idxmax()
        worst_idx = s.idxmin()
        best_val = s.loc[best_idx] * 100
        best_m = df.loc[best_idx, "month"]
        worst_val = s.loc[worst_idx] * 100
        worst_m = df.loc[worst_idx, "month"]
        print(f"[{name}]")
        print(f"  Outperforming Months: {pos}")
        print(f"  Underperforming Months: {neg}")
        print(f"  Average Monthly Alpha: {avg:+.2f}%")
        print(f"  Median Monthly Alpha:  {med:+.2f}%")
        print(f"  Best Alpha Month:  {best_m} ({best_val:+.2f}%)")
        print(f"  Worst Alpha Month: {worst_m} ({worst_val:+.2f}%)")

if __name__ == "__main__":
    main()
