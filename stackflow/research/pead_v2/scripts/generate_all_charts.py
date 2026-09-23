"""Generate the 12 required publication-grade research visualisations for PEAD V2."""
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, COST_BASE
from src.data_loader import load_prices, load_benchmark
from src.portfolio_engine import run_portfolio_backtest
from src.metrics import calc_quarterly_folds


def generate_all_charts():
    print("=== GENERATING 12 RESEARCH CHARTS ===")
    charts_dir = os.path.join(PEAD_V2_ROOT, "artifacts", "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    events_path = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante", "pead_v2_events.csv")
    ev = pd.read_csv(events_path, parse_dates=["event_day", "entry_date", "period_end"])
    ev["qtr"] = ev.event_day.dt.to_period("Q")
    ev_ex = ev[ev["q_exante_4q"].notna()].copy()
    
    px_dict = load_prices()
    bench = load_benchmark()
    
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # 1. SUE Distribution
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    sues = ev_ex["sue"].dropna().values
    p1, p99 = np.percentile(sues, [1, 99])
    clipped = sues[(sues >= p1) & (sues <= p99)]
    ax.hist(clipped, bins=60, color='#2b5c8f', edgecolor='white', alpha=0.85, density=True)
    ax.axvline(0, color='#d9534f', linestyle='--', linewidth=1.5, label='Zero Surprise')
    ax.axvline(np.median(sues), color='#5cb85c', linestyle='-', linewidth=1.5, label=f'Median: {np.median(sues):.2f}')
    ax.set_title("1. Standardized Unexpected Earnings (SUE) Distribution (1st-99th %tile)", fontsize=11, pad=10)
    ax.set_xlabel("SUE (Normalized Earnings Surprise)", fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "01_sue_distribution.png"))
    plt.close(fig)
    print("Chart 1 saved.")

    # 2. Q1-Q5 Return Curve (Ladder)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    q_means = [ev_ex[ev_ex.q_exante_4q == q]["xs_univ_60d"].mean() * 100 for q in range(1, 6)]
    colors = ['#d9534f', '#f0ad4e', '#6c757d', '#5bc0de', '#5cb85c']
    bars = ax.bar([f"Q{i}" for i in range(1, 6)], q_means, color=colors, width=0.55)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + (0.1 if h >= 0 else -0.2),
                f"{h:+.2f}%", ha='center', va='bottom' if h >= 0 else 'top', fontsize=10, fontweight='bold')
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_title("2. Ex-Ante SUE Quintile Ladder (60-Day Excess Return vs Event Universe)", fontsize=11, pad=10)
    ax.set_xlabel("Ex-Ante SUE Quintile", fontsize=10)
    ax.set_ylabel("Excess Return (%)", fontsize=10)
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "02_quintile_ladder.png"))
    plt.close(fig)
    print("Chart 2 saved.")

    # 3. Cumulative Q5-Q1 Spread over Time
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    folds_60d = calc_quarterly_folds(ev_ex, "q_exante_4q", "xs_univ_60d")
    folds_60d["cum_spread"] = (folds_60d["spread"] * 100).cumsum()
    ax.plot(range(len(folds_60d)), folds_60d["cum_spread"], marker='o', color='#2b5c8f', linewidth=2.0)
    ax.set_title("3. Cumulative Q5 − Q1 Spread Across Quarterly Folds (60-Day Excess, %)", fontsize=11, pad=10)
    ax.set_xlabel("Quarterly Fold Index", fontsize=10)
    ax.set_ylabel("Cumulative Spread (Percentage Points)", fontsize=10)
    ax.set_xticks(range(0, len(folds_60d), 2))
    ax.set_xticklabels(folds_60d["qtr"].iloc[::2], rotation=45, ha='right', fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "03_cumulative_spread.png"))
    plt.close(fig)
    print("Chart 3 saved.")

    # 4. Horizon Response Curve (5d -> 126d)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    horizons = [5, 10, 20, 30, 40, 60, 90, 126]
    h_labels = ["5d", "10d", "20d", "30d", "40d", "60d", "90d", "126d"]
    spreads = []
    for h_name in h_labels:
        col = f"xs_univ_{h_name}"
        q5 = ev_ex[ev_ex.q_exante_4q == 5][col].mean() * 100
        q1 = ev_ex[ev_ex.q_exante_4q == 1][col].mean() * 100
        spreads.append(q5 - q1)
    ax.plot(horizons, spreads, marker='s', color='#2b5c8f', linewidth=2.2, markersize=6)
    for x, y in zip(horizons, spreads):
        ax.annotate(f"{y:+.2f}%", (x, y), textcoords="offset points", xytext=(0, 7), ha='center', fontsize=9, fontweight='bold')
    ax.set_title("4. Post-Announcement Drift by Holding Horizon (Trading Days)", fontsize=11, pad=10)
    ax.set_xlabel("Trading Days", fontsize=10)
    ax.set_ylabel("Q5 − Q1 Spread (%)", fontsize=10)
    ax.set_xticks(horizons)
    ax.set_xticklabels(h_labels)
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "04_horizon_response.png"))
    plt.close(fig)
    print("Chart 4 saved.")

    # 5. Fold-by-Fold Q5-Q1 Spread
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=150)
    folds_60d["spread_pct"] = folds_60d["spread"] * 100
    colors_f = ['#5cb85c' if s > 0 else '#d9534f' for s in folds_60d["spread_pct"]]
    ax.bar(folds_60d["qtr"], folds_60d["spread_pct"], color=colors_f, width=0.6)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.axhline(folds_60d["spread_pct"].mean(), color='#2b5c8f', linestyle='--', label=f'Mean Spread: {folds_60d["spread_pct"].mean():+.2f}%')
    ax.set_title("5. Fold-by-Fold Quarterly Q5 − Q1 Spread (60-Day Horizon)", fontsize=11, pad=10)
    ax.set_xlabel("Quarter", fontsize=10)
    ax.set_ylabel("Spread (%)", fontsize=10)
    plt.xticks(rotation=45, ha='right', fontsize=8)
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "05_fold_consistency.png"))
    plt.close(fig)
    print("Chart 5 saved.")

    # 6. Size x SUE Spread
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    sizes = ["Small", "Mid", "Large"]
    sz_spreads = [ev_ex[(ev_ex.size_tercile == sz) & (ev_ex.q_exante_4q == 5)]["xs_univ_60d"].mean() * 100 -
                  ev_ex[(ev_ex.size_tercile == sz) & (ev_ex.q_exante_4q == 1)]["xs_univ_60d"].mean() * 100 for sz in sizes]
    ax.bar(sizes, sz_spreads, color=['#2b5c8f', '#5bc0de', '#6c757d'], width=0.5)
    for i, v in enumerate(sz_spreads):
        ax.text(i, v + 0.1, f"{v:+.2f}%", ha='center', fontsize=10, fontweight='bold')
    ax.set_title("6. PEAD 60-Day Spread Across Size Terciles", fontsize=11, pad=10)
    ax.set_xlabel("Market Cap / Turnover Tercile", fontsize=10)
    ax.set_ylabel("Q5 − Q1 Spread (%)", fontsize=10)
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "06_size_by_sue.png"))
    plt.close(fig)
    print("Chart 6 saved.")

    # 7. Sector x SUE Spread
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    sec_names = ["Non-Financials", "Financials (Banks/NBFC)"]
    sec_spreads = [
        ev_ex[(ev_ex.is_fin == False) & (ev_ex.q_exante_4q == 5)]["xs_univ_60d"].mean() * 100 -
        ev_ex[(ev_ex.is_fin == False) & (ev_ex.q_exante_4q == 1)]["xs_univ_60d"].mean() * 100,
        ev_ex[(ev_ex.is_fin == True) & (ev_ex.q_exante_4q == 5)]["xs_univ_60d"].mean() * 100 -
        ev_ex[(ev_ex.is_fin == True) & (ev_ex.q_exante_4q == 1)]["xs_univ_60d"].mean() * 100
    ]
    ax.bar(sec_names, sec_spreads, color=['#5cb85c', '#d9534f'], width=0.45)
    for i, v in enumerate(sec_spreads):
        ax.text(i, v + (0.1 if v >= 0 else -0.3), f"{v:+.2f}%", ha='center', fontsize=10, fontweight='bold')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_title("7. PEAD 60-Day Spread: Non-Financials vs Financials", fontsize=11, pad=10)
    ax.set_ylabel("Q5 − Q1 Spread (%)", fontsize=10)
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "07_sector_by_sue.png"))
    plt.close(fig)
    print("Chart 7 saved.")

    # 8. Filing Timing x SUE Spread
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    cohorts = ["Early (<=25d)", "Mid (26-45d)", "Late (>45d)"]
    cohort_keys = ["Early", "Mid", "Late"]
    c_spreads = [
        ev_ex[(ev_ex.filing_cohort == ck) & (ev_ex.q_exante_4q == 5)]["xs_univ_60d"].mean() * 100 -
        ev_ex[(ev_ex.filing_cohort == ck) & (ev_ex.q_exante_4q == 1)]["xs_univ_60d"].mean() * 100
        for ck in cohort_keys
    ]
    ax.bar(cohorts, c_spreads, color=['#f0ad4e', '#2b5c8f', '#5cb85c'], width=0.5)
    for i, v in enumerate(c_spreads):
        ax.text(i, v + 0.1, f"{v:+.2f}%", ha='center', fontsize=10, fontweight='bold')
    ax.set_title("8. PEAD 60-Day Spread Across Filing Timing Cohorts", fontsize=11, pad=10)
    ax.set_ylabel("Q5 − Q1 Spread (%)", fontsize=10)
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "08_filing_timing_by_sue.png"))
    plt.close(fig)
    print("Chart 8 saved.")

    # 9. Portfolio Equity Curve & 10. Drawdown Curve
    res_port = run_portfolio_backtest(
        trades_df=ev_ex[(ev_ex.q_exante_4q == 5) & (ev_ex.is_fin == False)],
        prices_dict=px_dict,
        benchmark_series=bench,
        max_slots=30,
        holding_period=60,
        cost=COST_BASE,
        queue_policy="SUE_RANK"
    )
    port_eq = res_port["equity_curve"]
    bench_sub = bench.loc[port_eq.index]
    bench_eq = bench_sub / bench_sub.iloc[0]
    
    # Plot 9: Equity Curve
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    ax.plot(port_eq.index, port_eq.values, label=f'PEAD V2 Strategy (Net of Cost, CAGR +{res_port["cagr_pct"]:.1f}%)', color='#2b5c8f', linewidth=2.0)
    ax.plot(bench_eq.index, bench_eq.values, label=f'Nifty 500 Index (CAGR +{res_port["bench_cagr_pct"]:.1f}%)', color='#6c757d', linestyle='--', linewidth=1.5)
    ax.set_title("9. Portfolio Growth vs Nifty 500 (30 Slots, Non-Financials Q5, Net of Costs)", fontsize=11, pad=10)
    ax.set_ylabel("Growth of $1.00", fontsize=10)
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "09_portfolio_equity_curve.png"))
    plt.close(fig)
    print("Chart 9 saved.")

    # Plot 10: Drawdown Curve
    fig, ax = plt.subplots(figsize=(10, 3.8), dpi=150)
    port_dd = (port_eq / port_eq.cummax() - 1.0) * 100
    bench_dd = (bench_eq / bench_eq.cummax() - 1.0) * 100
    ax.fill_between(port_dd.index, port_dd.values, 0, color='#2b5c8f', alpha=0.35, label=f'PEAD Strategy (Max DD: {res_port["max_dd_pct"]:.1f}%)')
    ax.plot(bench_dd.index, bench_dd.values, color='#d9534f', linestyle=':', label=f'Nifty 500 (Max DD: {res_port["bench_max_dd_pct"]:.1f}%)')
    ax.set_title("10. Strategy vs Benchmark Drawdown Profile (%)", fontsize=11, pad=10)
    ax.set_ylabel("Drawdown (%)", fontsize=10)
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "10_drawdown_curve.png"))
    plt.close(fig)
    print("Chart 10 saved.")

    # Plot 11: Cost Sensitivity
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    costs = ["Low (0.30%)", "Baseline (0.585%)", "High (1.00%)"]
    cagrs = [19.04, 17.73, 15.84]
    excesses = [7.99, 6.68, 4.79]
    x_indices = np.arange(len(costs))
    ax.bar(x_indices - 0.18, cagrs, width=0.35, label='Strategy CAGR (%)', color='#2b5c8f')
    ax.bar(x_indices + 0.18, excesses, width=0.35, label='Excess vs Nifty 500 (pp)', color='#5cb85c')
    ax.axhline(11.05, color='#d9534f', linestyle='--', label='Nifty 500 CAGR (+11.05%)')
    ax.set_xticks(x_indices)
    ax.set_xticklabels(costs)
    ax.set_title("11. Strategy CAGR & Excess Return under Cost Stress (30 Slots)", fontsize=11, pad=10)
    ax.set_ylabel("Return (%)", fontsize=10)
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "11_cost_sensitivity.png"))
    plt.close(fig)
    print("Chart 11 saved.")

    # Plot 12: Discovery vs Holdout Spread
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    horiz_list = ["20d", "40d", "60d", "90d"]
    disc_s = [1.515, 1.724, 3.331, 3.717]
    hold_s = [1.185, 1.469, 2.292, 3.436]
    x = np.arange(len(horiz_list))
    ax.bar(x - 0.18, disc_s, width=0.35, label='Discovery (2021-2023)', color='#2b5c8f')
    ax.bar(x + 0.18, hold_s, width=0.35, label='Holdout (2024-2026)', color='#5cb85c')
    for i in range(len(horiz_list)):
        ax.text(i - 0.18, disc_s[i] + 0.08, f"{disc_s[i]:+.2f}%", ha='center', fontsize=9, fontweight='bold')
        ax.text(i + 0.18, hold_s[i] + 0.08, f"{hold_s[i]:+.2f}%", ha='center', fontsize=9, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(horiz_list)
    ax.set_title("12. Discovery vs Holdout Out-of-Sample Q5 − Q1 Spread (%)", fontsize=11, pad=10)
    ax.set_ylabel("Spread (%)", fontsize=10)
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(charts_dir, "12_discovery_vs_holdout.png"))
    plt.close(fig)
    print("Chart 12 saved.")
    print("All 12 charts successfully generated.")


if __name__ == "__main__":
    generate_all_charts()
