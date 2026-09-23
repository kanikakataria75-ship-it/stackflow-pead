"""Publication-grade visualisations for PEAD V2 research."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def setup_style():
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['axes.edgecolor'] = '#cccccc'
    plt.rcParams['axes.linewidth'] = 0.8


def plot_sue_distribution(sue_series, out_path):
    setup_style()
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    vals = sue_series.dropna().values
    p1, p99 = np.percentile(vals, [1, 99])
    clipped = vals[(vals >= p1) & (vals <= p99)]
    ax.hist(clipped, bins=60, color='#2b5c8f', edgecolor='white', alpha=0.85, density=True)
    ax.axvline(0, color='#d9534f', linestyle='--', linewidth=1.5, label='Zero Surprise')
    ax.axvline(np.median(vals), color='#5cb85c', linestyle='-', linewidth=1.5, label=f'Median: {np.median(vals):.2f}')
    ax.set_title("Standardized Unexpected Earnings (SUE) Distribution (1st-99th %tile)", fontsize=12, pad=10)
    ax.set_xlabel("SUE (Normalized Earnings Surprise)", fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_quintile_ladder(ladder_df, out_path, title="Ex-Ante SUE Quintile Ladder (60d Excess Return)"):
    setup_style()
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    quintiles = [f"Q{i}" for i in range(1, 6)]
    colors = ['#d9534f', '#f0ad4e', '#6c757d', '#5bc0de', '#5cb85c']
    bars = ax.bar(quintiles, ladder_df['mean_pct'], color=colors, edgecolor='white', width=0.55)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + (0.1 if h >= 0 else -0.2),
                f"{h:+.2f}%", ha='center', va='bottom' if h >= 0 else 'top', fontsize=10, fontweight='bold')
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_title(title, fontsize=12, pad=10)
    ax.set_xlabel("Ex-Ante SUE Quintile", fontsize=10)
    ax.set_ylabel("Excess Return vs Event Universe Mean (%)", fontsize=10)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_horizon_response(horizons_df, out_path):
    setup_style()
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(horizons_df['horizon_days'], horizons_df['spread_pct'], marker='o', color='#2b5c8f',
            linewidth=2.2, markersize=7, label='Q5 - Q1 Spread (%)')
    for _, r in horizons_df.iterrows():
        ax.annotate(f"{r['spread_pct']:+.2f}%", (r['horizon_days'], r['spread_pct']),
                    textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, fontweight='bold')
    ax.axhline(0, color='#d9534f', linestyle='--', linewidth=1.0)
    ax.set_title("Post-Announcement Drift by Holding Horizon (Ex-Ante)", fontsize=12, pad=10)
    ax.set_xlabel("Holding Period (Trading Days)", fontsize=10)
    ax.set_ylabel("Q5 - Q1 Spread vs Event Universe (%)", fontsize=10)
    ax.set_xticks(horizons_df['horizon_days'])
    ax.set_xticklabels(horizons_df['horizon_label'])
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_fold_consistency(folds_df, out_path):
    setup_style()
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    colors = ['#5cb85c' if s > 0 else '#d9534f' for s in folds_df['spread_pct']]
    bars = ax.bar(folds_df['qtr'], folds_df['spread_pct'], color=colors, edgecolor='white', width=0.65)
    ax.axhline(0, color='black', linewidth=0.8)
    pos_pct = (folds_df['spread_pct'] > 0).mean() * 100
    mean_spread = folds_df['spread_pct'].mean()
    ax.axhline(mean_spread, color='#2b5c8f', linestyle='--', linewidth=1.2,
               label=f'Mean Spread: {mean_spread:+.2f}% (Positivity: {pos_pct:.1f}%)')
    ax.set_title("Quarterly Fold-by-Fold Q5 - Q1 Spread (60d Excess)", fontsize=12, pad=10)
    ax.set_xlabel("Calendar Quarter", fontsize=10)
    ax.set_ylabel("Spread (%)", fontsize=10)
    plt.xticks(rotation=45, ha='right', fontsize=8)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_portfolio_equity(equity_df, out_path, title="Portfolio Equity Curve vs Nifty 500"):
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.plot(equity_df.index, equity_df['portfolio'], label='PEAD V2 Strategy (Net of Cost)', color='#2b5c8f', linewidth=2.0)
    ax.plot(equity_df.index, equity_df['benchmark'], label='Nifty 500 Index', color='#6c757d', linestyle='--', linewidth=1.5)
    ax.set_title(title, fontsize=12, pad=10)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Normalized Wealth ($1 Initial)", fontsize=10)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_drawdown(equity_df, out_path):
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    port_dd = (equity_df['portfolio'] / equity_df['portfolio'].cummax() - 1.0) * 100
    bench_dd = (equity_df['benchmark'] / equity_df['benchmark'].cummax() - 1.0) * 100
    ax.fill_between(port_dd.index, port_dd, 0, color='#2b5c8f', alpha=0.3, label='Strategy Drawdown')
    ax.plot(bench_dd.index, bench_dd, color='#d9534f', linestyle=':', linewidth=1.2, label='Nifty 500 Drawdown')
    ax.set_title("Portfolio Underwater Drawdown (%)", fontsize=12, pad=10)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Drawdown (%)", fontsize=10)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
