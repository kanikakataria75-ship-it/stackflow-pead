"""Audit-corrected PEAD V2 results: signal, frozen strategy, diagnostics. Single source of truth
for CORRECTED_REPORT.md and PEAD_V2_Tearsheet.xlsx.

Frozen config (live_config_pead_v2_corrected.md): Non-Financials (pipeline `fin` flag), ex-ante
M1 Q5, 30 slots, 60 trading days, FIFO across dates with same-day SUE tie-break, strict slot
release, share/cash accounting, 0.585% round trip (half per leg). Benchmark NIFTY 500 PRICE index.

Periods (primary): trade-attributed books - Discovery = a book holding only trades signalled
<= 2023-12-31; Holdout = a book started fresh holding only trades signalled >= 2024-01-01.
Secondary: calendar split of the one continuous full-period book (flattered in the holdout by
discovery-signalled positions still open in Jan-Feb 2024).
All outputs go to corrected/.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, XBRL_CACHE, DISCOVERY_END
from src.data_loader import load_prices, load_benchmark
from src.portfolio_engine import run_portfolio_backtest
from src.metrics import evaluate_signal_cell, calc_quarterly_folds

OUT = os.path.join(PEAD_V2_ROOT, "corrected")
COST, SLOTS, H, RF = 0.00585, 30, 60, 0.06
HS = pd.Timestamp("2024-01-01")


def nav_metrics(nav, bench, rf=0.0):
    r = nav.pct_change().dropna()
    b = bench.loc[nav.index]
    br = b.pct_change().dropna()
    yrs = (nav.index[-1] - nav.index[0]).days / 365.25
    cagr = (nav.iloc[-1] / nav.iloc[0]) ** (1 / yrs) - 1
    bcagr = (b.iloc[-1] / b.iloc[0]) ** (1 / yrs) - 1
    vol = r.std() * np.sqrt(252)
    dly_rf = (1 + RF) ** (1 / 252) - 1
    sh0 = r.mean() * 252 / vol
    sh6 = (r.mean() - dly_rf) * 252 / vol
    down = r[r < 0]
    sortino = r.mean() * 252 / (np.sqrt((down ** 2).sum() / len(r)) * np.sqrt(252))
    dd = nav / nav.cummax() - 1
    # drawdown episodes
    under = dd < 0
    ep_id = (under != under.shift()).cumsum()[under]
    eps = dd[under].groupby(ep_id)
    ep_depth = eps.min()
    ep_len = eps.size()
    bvol = br.std() * np.sqrt(252)
    return dict(
        start=str(nav.index[0].date()), end=str(nav.index[-1].date()), years=yrs,
        total_return=nav.iloc[-1] / nav.iloc[0] - 1, cagr=cagr, bench_total_return=b.iloc[-1] / b.iloc[0] - 1,
        bench_cagr=bcagr, excess_cagr=cagr - bcagr, vol=vol, bench_vol=bvol,
        sharpe_rf0=sh0, sharpe_rf6=sh6,
        bench_sharpe_rf0=br.mean() * 252 / bvol, bench_sharpe_rf6=(br.mean() - dly_rf) * 252 / bvol,
        sortino_rf0=sortino, max_dd=dd.min(), bench_max_dd=(b / b.cummax() - 1).min(),
        calmar=cagr / abs(dd.min()), avg_dd_episode=ep_depth.mean() if len(ep_depth) else 0.0,
        longest_dd_sessions=int(ep_len.max()) if len(ep_len) else 0,
        var95_daily=-np.percentile(r, 5), cvar95_daily=-r[r <= np.percentile(r, 5)].mean(),
        skew_daily=stats.skew(r), excess_kurt_daily=stats.kurtosis(r),
        beta=np.cov(r, br.reindex(r.index))[0, 1] / br.var())


def trade_metrics(t):
    net = t.net_ret
    w, l = net[net > 0], net[net <= 0]
    return dict(trades=len(t), win_rate=(net > 0).mean(), profit_factor=w.sum() / abs(l.sum()),
                avg_trade_net=net.mean(), avg_win=w.mean(), avg_loss=l.mean(), payoff=w.mean() / abs(l.mean()),
                best_trade=net.max(), worst_trade=net.min(), avg_holding_sessions=float(H),
                mean_trade_xs_univ_60d=t.xs_univ_60d.mean(), mean_trade_xs_nifty=t.xs_nifty.mean())


def main():
    os.makedirs(OUT, exist_ok=True)
    ev = pd.read_csv(os.path.join(OUT, "pead_v2_events_corrected.csv"),
                     parse_dates=["event_day", "entry_date", "period_end", "filing_ts"])
    ev["qtr"] = ev.event_day.dt.to_period("Q")
    exa = ev[ev.q_exante_4q.notna()].copy()
    px = load_prices()
    bench = load_benchmark()
    res = {}

    # ---------------- signal ----------------
    cells = []
    def add(label, d, q="q_exante_4q", r="xs_univ_60d"):
        c = evaluate_signal_cell(d, q, r, label=label)
        if c:
            c = {k: v for k, v in c.items() if k not in ("ladder_q1_to_q5",)} | {
                f"Q{i+1}": v for i, v in enumerate(c["ladder_q1_to_q5"])}
            cells.append(c)
    disc, hold = exa[exa.event_day <= DISCOVERY_END], exa[exa.event_day > DISCOVERY_END]
    add("Primary 60d (all)", exa); add("Discovery 60d", disc); add("Holdout 60d", hold)
    for h in ["5d", "10d", "20d", "30d", "40d", "90d", "126d"]:
        add(f"Horizon {h}", exa, r=f"xs_univ_{h}")
    add("Non-Financials 60d", exa[~exa.is_fin]); add("Financials 60d", exa[exa.is_fin])
    for s in ["Small", "Mid", "Large"]:
        add(f"Size {s} 60d", exa[exa.size_tercile == s])
    add("KT2 ex-2021", exa[exa.event_day.dt.year > 2021])
    add("KT3 Mid+Large only", exa[exa.size_tercile.isin(["Mid", "Large"])])
    add("KT4 ex-Layer-4-seen", exa[~exa.layer4_seen])
    add("KT6 8Q window", ev[ev.q_exante_8q.notna()], q="q_exante_8q")
    add("KT6 expanding window", ev[ev.q_exante_exp.notna()], q="q_exante_exp")
    folds = calc_quarterly_folds(exa, "q_exante_4q", "xs_univ_60d")
    top2 = folds.nlargest(2, "spread")
    ex2 = exa[~exa.qtr.astype(str).isin(top2.qtr)]
    add("KT1 ex top-2 quarters (event level)", ex2)
    sig = pd.DataFrame(cells)
    sig.to_csv(os.path.join(OUT, "signal_cells.csv"), index=False)
    folds["period"] = np.where(folds.qtr < "2024Q1", "Discovery", "Holdout")
    folds.to_csv(os.path.join(OUT, "signal_folds_60d.csv"), index=False)
    res["kt1_top2_quarters"] = list(top2.qtr)
    res["kt1_fold_mean_all"] = float(folds.spread.mean())
    res["kt1_fold_mean_ex_top2"] = float(folds.drop(top2.index).spread.mean())
    res["kt1_fold_pos_ex_top2"] = float((folds.drop(top2.index).spread > 0).mean())

    # ---------------- frozen strategy ----------------
    book = exa[(exa.q_exante_4q == 5) & (~exa.is_fin)]
    runs = {}
    for c in [0.003, COST, 0.01]:
        runs[c] = run_portfolio_backtest(book, px, bench, SLOTS, H, c, "SUE_RANK")
    R = runs[COST]
    nav = R["nav_series"] / R["nav_series"].iloc[0]
    last_disc = nav.index[nav.index < HS][-1]
    periods = {"Full Period": nav, "Discovery": nav[nav.index <= last_disc], "Holdout": nav[nav.index >= last_disc]}

    # trade ledger
    tk = R["taken_df"].copy()
    meta = ev.set_index(["symbol", "entry_date"])
    keys = list(zip(tk.symbol, tk.entry_date))
    for col in ["filing_ts", "event_day", "period_end", "industry", "q_exante_4q", "xs_univ_60d"]:
        tk[col] = [meta.loc[k, col] for k in keys]
    tk["bench_ret"] = [float(bench.asof(x) / bench.asof(e) - 1) for e, x in zip(tk.entry_date, tk.exit_date)]
    tk["xs_nifty"] = tk.raw_ret - tk.bench_ret
    comp = pd.concat([
        pd.read_csv(os.path.join(XBRL_CACHE, "filing_index.csv"), usecols=["symbol", "company"]),
        pd.read_csv(os.path.join(XBRL_CACHE, "filing_index_integrated.csv"), usecols=["symbol", "company"])
    ]).dropna().drop_duplicates("symbol").set_index("symbol").company
    led = pd.DataFrame({
        "trade_id": [f"T{i+1:04d}" for i in range(len(tk))],
        "entry_date": tk.entry_date.dt.date, "symbol": tk.symbol, "company": tk.symbol.map(comp),
        "sector": tk.industry.str.title().str.replace(r"^It$", "IT", regex=True), "filing_timestamp": tk.filing_ts, "event_day": tk.event_day.dt.date,
        "entry_price": tk.entry_px, "exit_date": tk.exit_date.dt.date, "exit_price": tk.exit_px,
        "holding_sessions": H, "sue": tk.sue, "sue_quintile": tk.q_exante_4q.astype(int),
        "gross_return": tk.raw_ret, "cost": COST, "net_return": tk.net_ret,
        "nifty500_return": tk.bench_ret, "excess_vs_nifty500": tk.xs_nifty,
        "excess_vs_event_universe_60d": tk.xs_univ_60d,
        "period": np.where(tk.entry_date < HS, "Discovery", "Holdout"),
        "result": np.where(tk.net_ret > 0, "Win", "Loss")})
    led.to_csv(os.path.join(OUT, "trade_ledger_corrected.csv"), index=False)

    # daily NAV / drawdown / positions
    b = bench.loc[nav.index]
    open_n = pd.Series(0, index=nav.index)
    for e, x in zip(tk.entry_date, tk.exit_date):
        open_n[(open_n.index >= e) & (open_n.index <= x)] += 1
    daily = pd.DataFrame({"strategy_nav": nav * 100, "nifty500": b / b.iloc[0] * 100,
                          "strategy_dd": nav / nav.cummax() - 1, "nifty500_dd": b / b.cummax() - 1,
                          "positions_held": open_n,
                          "period": np.where(nav.index < HS, "Discovery", "Holdout")})
    daily.index.name = "date"
    daily.to_csv(os.path.join(OUT, "nav_daily_corrected.csv"))
    m_s = nav.resample("ME").last(); m_b = b.resample("ME").last()
    m_s = pd.concat([pd.Series([nav.iloc[0]], [nav.index[0] - pd.Timedelta(days=1)]), m_s])
    m_b = pd.concat([pd.Series([b.iloc[0]], [b.index[0] - pd.Timedelta(days=1)]), m_b])
    monthly = pd.DataFrame({"strategy": m_s.pct_change(), "nifty500": m_b.pct_change()}).dropna()
    monthly["excess"] = monthly.strategy - monthly.nifty500
    monthly["year"], monthly["month"] = monthly.index.year, monthly.index.month
    monthly.index.name = "month_end"
    monthly.to_csv(os.path.join(OUT, "monthly_returns_corrected.csv"))
    roll = pd.DataFrame({"strategy_12m": nav / nav.shift(252) - 1, "nifty500_12m": b / b.shift(252) - 1}).dropna()
    roll["excess_12m"] = roll.strategy_12m - roll.nifty500_12m
    roll.to_csv(os.path.join(OUT, "rolling_12m_corrected.csv"))
    yr = pd.DataFrame({"strategy": nav.resample("YE").last(), "nifty500": b.resample("YE").last()})
    yr = pd.concat([pd.DataFrame({"strategy": [nav.iloc[0]], "nifty500": [b.iloc[0]]}, index=[nav.index[0]]), yr]).pct_change().dropna()
    yr["excess"] = yr.strategy - yr.nifty500
    yr["trades_entered"] = [int(((tk.entry_date.dt.year) == d.year).sum()) for d in yr.index]
    yr["window"] = [f"{max(nav.index[0], pd.Timestamp(d.year, 1, 1)).date()} to {min(nav.index[-1], d).date()}" for d in yr.index]
    yr.index = yr.index.year
    yr.to_csv(os.path.join(OUT, "yearly_returns_corrected.csv"))
    # quarterly portfolio excess (trading version of the fold chart)
    q_s = nav.resample("QE").last(); q_b = b.resample("QE").last()
    q_s = pd.concat([pd.Series([nav.iloc[0]], [nav.index[0]]), q_s]); q_b = pd.concat([pd.Series([b.iloc[0]], [b.index[0]]), q_b])
    qx = pd.DataFrame({"strategy": q_s.pct_change(), "nifty500": q_b.pct_change()}).dropna()
    qx["excess"] = qx.strategy - qx.nifty500
    qx.index = qx.index.to_period("Q").astype(str)
    qx.to_csv(os.path.join(OUT, "quarterly_portfolio_excess_corrected.csv"))

    # period metrics.  PRIMARY split = trade-attributed fresh runs (a book started on the first
    # discovery / first holdout signal, holding only trades signalled in that period).  The
    # calendar split of the one continuous book is kept as a secondary view: its "holdout" NAV
    # includes discovery-signalled trades still open in Jan-Feb 2024 (avg net +22%), which
    # flatters the holdout by ~4 pp/yr.
    def enrich(t):
        t = t.copy()
        k = list(zip(t.symbol, t.entry_date))
        t["xs_univ_60d"] = [meta.loc[x, "xs_univ_60d"] for x in k]
        t["xs_nifty"] = [r - float(bench.asof(x) / bench.asof(e) - 1) for r, e, x in zip(t.raw_ret, t.entry_date, t.exit_date)]
        return t
    def turnover(run, t):
        nd = run["nav_series"]
        bv = np.array([nd.asof(e - pd.Timedelta(days=1)) if e > nd.index[0] else nd.iloc[0] for e in t.entry_date]) / SLOTS
        sv = bv * (1 + t.raw_ret.values)
        yrs = (nd.index[-1] - nd.index[0]).days / 365.25
        return (bv.sum() + sv.sum()) / 2 / yrs / nd.mean()
    def adv_of(t):
        out = []
        for s_, e in zip(t.symbol, t.entry_date):
            d = px[s_]; i = d.index.get_loc(e); w = d.iloc[max(0, i - 20):i]
            out.append(float((w.Close * w.Volume).median()))
        return np.array(out)
    fresh = {"Discovery": run_portfolio_backtest(book[book.event_day <= DISCOVERY_END], px, bench, SLOTS, H, COST, "SUE_RANK"),
             "Holdout": run_portfolio_backtest(book[book.event_day > DISCOVERY_END], px, bench, SLOTS, H, COST, "SUE_RANK")}
    pm, navs = {}, {}
    for p_, run in [("Full Period", R), ("Discovery", fresh["Discovery"]), ("Holdout", fresh["Holdout"])]:
        n = run["nav_series"] / run["nav_series"].iloc[0]
        t = enrich(run["taken_df"])
        a = adv_of(t)
        navs[p_] = n
        pm[p_] = nav_metrics(n, bench) | trade_metrics(t) | dict(
            turnover_one_way=turnover(run, t), median_adv20_cr=np.median(a) / 1e7, p10_adv20_cr=np.quantile(a, .1) / 1e7,
            capacity_1pct_90fit_cr=np.quantile(a, .1) * 0.01 * SLOTS / 1e7, capacity_5pct_90fit_cr=np.quantile(a, .1) * 0.05 * SLOTS / 1e7,
            capacity_1pct_50fit_cr=np.quantile(a, .5) * 0.01 * SLOTS / 1e7)
    for p_, n in [("Discovery (calendar split of full book)", nav[nav.index <= last_disc]),
                  ("Holdout (calendar split of full book)", nav[nav.index >= last_disc])]:
        pm[p_] = nav_metrics(n, bench)
    for p_, n in navs.items():
        pd.DataFrame({"strategy_nav": n * 100, "nifty500": bench.loc[n.index] / bench.loc[n.index].iloc[0] * 100,
                      "strategy_dd": n / n.cummax() - 1}).rename_axis("date").to_csv(
            os.path.join(OUT, f"nav_{p_.split()[0].lower()}_corrected.csv"))
    advs = adv_of(tk)
    # capacity
    tk["adv20_median"] = advs
    aum = np.array([0.5, 1, 2, 3, 5, 7.5, 10, 15, 20, 30, 50, 75, 100, 150])
    cap = pd.DataFrame({"aum_cr": aum,
                        "pct_trades_within_1pct_adv": [(aum_i * 1e7 / SLOTS <= 0.01 * advs).mean() for aum_i in aum],
                        "pct_trades_within_5pct_adv": [(aum_i * 1e7 / SLOTS <= 0.05 * advs).mean() for aum_i in aum]})
    cap.to_csv(os.path.join(OUT, "capacity_curve_corrected.csv"), index=False)
    pmdf = pd.DataFrame(pm)
    pmdf.index.name = "metric"
    pmdf.to_csv(os.path.join(OUT, "period_metrics_corrected.csv"))

    # cost sensitivity (full + holdout split)
    cs = []
    for c, rr in runs.items():
        n = rr["nav_series"] / rr["nav_series"].iloc[0]
        hr = run_portfolio_backtest(book[book.event_day > DISCOVERY_END], px, bench, SLOTS, H, c, "SUE_RANK")
        f, h = nav_metrics(n, bench), nav_metrics(hr["nav_series"] / hr["nav_series"].iloc[0], bench)
        cs.append(dict(round_trip_cost=c, full_cagr=f["cagr"], full_excess=f["excess_cagr"], full_sharpe_rf0=f["sharpe_rf0"],
                       full_max_dd=f["max_dd"], holdout_cagr=h["cagr"], holdout_excess=h["excess_cagr"]))
    pd.DataFrame(cs).to_csv(os.path.join(OUT, "cost_sensitivity_corrected.csv"), index=False)

    # placebo: same mechanics, random 20% of all eligible non-fin events, random priority
    elig = exa[~exa.is_fin].copy()
    rng = np.random.default_rng(20260923)
    pl, pl_trades = [], []
    for k in range(40):
        sub = elig.sample(frac=0.2, random_state=int(rng.integers(1e9))).copy()
        sub["sue"] = rng.random(len(sub))
        rr = run_portfolio_backtest(sub, px, bench, SLOTS, H, COST, "SUE_RANK")
        n = rr["nav_series"] / rr["nav_series"].iloc[0]
        f = nav_metrics(n, bench)
        subh = sub[sub.event_day > DISCOVERY_END]
        rh = run_portfolio_backtest(subh, px, bench, SLOTS, H, COST, "SUE_RANK")
        hh = nav_metrics(rh["nav_series"] / rh["nav_series"].iloc[0], bench)
        pl.append(dict(draw=k + 1, trades=rr["taken_trades"], cagr=f["cagr"], excess_cagr=f["excess_cagr"],
                       sharpe_rf0=f["sharpe_rf0"], holdout_excess_cagr=hh["excess_cagr"]))
        pl_trades.append(rr["taken_df"].net_ret.values)
    pd.DataFrame(pl).to_csv(os.path.join(OUT, "placebo_random_books.csv"), index=False)
    pd.DataFrame({"net_return": np.concatenate(pl_trades)}).to_csv(os.path.join(OUT, "placebo_trade_returns.csv"), index=False)

    # kill tests (corrected)
    s = sig.set_index("label")
    kt = [
        ("KT1", "Drop top-2 quarterly folds (" + " & ".join(res["kt1_top2_quarters"]) + ")",
         f"fold-mean {res['kt1_fold_mean_all']*100:+.2f}% -> {res['kt1_fold_mean_ex_top2']*100:+.2f}%, folds+ {res['kt1_fold_pos_ex_top2']*100:.1f}%; event-level spread {s.loc['KT1 ex top-2 quarters (event level)','spread_pct']:+.2f}%",
         res["kt1_fold_mean_ex_top2"] > 0 and res["kt1_fold_pos_ex_top2"] >= 0.65),
        ("KT2", "Drop 2021", f"spread {s.loc['KT2 ex-2021','spread_pct']:+.2f}%, p={s.loc['KT2 ex-2021','p_val']:.1e}",
         s.loc["KT2 ex-2021", "spread_pct"] > 0 and s.loc["KT2 ex-2021", "p_val"] < 0.01),
        ("KT3", "Mid + Large caps only", f"spread {s.loc['KT3 Mid+Large only','spread_pct']:+.2f}%, p={s.loc['KT3 Mid+Large only','p_val']:.4f}",
         s.loc["KT3 Mid+Large only", "spread_pct"] > 0 and s.loc["KT3 Mid+Large only", "p_val"] < 0.05),
        ("KT4", "Exclude Layer-4-seen events", f"spread {s.loc['KT4 ex-Layer-4-seen','spread_pct']:+.2f}%, folds+ {s.loc['KT4 ex-Layer-4-seen','fold_pos_pct']:.1f}%",
         s.loc["KT4 ex-Layer-4-seen", "spread_pct"] > 0 and s.loc["KT4 ex-Layer-4-seen", "fold_pos_pct"] >= 65),
        ("KT5", "1.000% round-trip cost (portfolio)",
         f"full excess {cs[2]['full_excess']*100:+.2f}%, HOLDOUT excess {cs[2]['holdout_excess']*100:+.2f}%",
         cs[2]["full_excess"] > 0 and cs[2]["holdout_excess"] > 0),
        ("KT6", "8Q / expanding threshold windows", f"8Q {s.loc['KT6 8Q window','spread_pct']:+.2f}%, expanding {s.loc['KT6 expanding window','spread_pct']:+.2f}%",
         s.loc["KT6 8Q window", "spread_pct"] > 0 and s.loc["KT6 expanding window", "spread_pct"] > 0),
        ("KT7", "Horizon jitter 40d / 90d", f"40d {s.loc['Horizon 40d','spread_pct']:+.2f}%, 90d {s.loc['Horizon 90d','spread_pct']:+.2f}%",
         s.loc["Horizon 40d", "spread_pct"] > 0 and s.loc["Horizon 90d", "spread_pct"] > 0),
    ]
    pd.DataFrame(kt, columns=["test", "perturbation", "result", "passed"]).to_csv(os.path.join(OUT, "kill_tests_corrected.csv"), index=False)

    # summary print
    pd.set_option("display.width", 250)
    print(sig[["label", "n_q5", "n_q1", "spread_pct", "p_val", "folds_pos", "folds_total", "fold_pos_pct", "spread_ex_best_pct", "inversions"]].round(4).to_string(index=False))
    print(pmdf.loc[["cagr", "bench_cagr", "excess_cagr", "vol", "sharpe_rf0", "sharpe_rf6", "bench_sharpe_rf0", "bench_sharpe_rf6",
                    "max_dd", "bench_max_dd", "trades", "win_rate", "turnover_one_way"]].astype(float).round(4).to_string())
    print(pd.DataFrame(cs).round(4).to_string(index=False))
    print(pd.DataFrame(kt, columns=["test", "perturbation", "result", "passed"]).to_string(index=False))
    pl = pd.DataFrame(pl)
    print("placebo excess full mean %.4f sd %.4f | holdout mean %.4f sd %.4f" % (pl.excess_cagr.mean(), pl.excess_cagr.std(), pl.holdout_excess_cagr.mean(), pl.holdout_excess_cagr.std()))
    print(yr.round(4).to_string())
    print("max positions held:", int(open_n.max()), " largest |daily NAV move|: %.4f" % nav.pct_change().abs().max())


if __name__ == "__main__":
    main()
