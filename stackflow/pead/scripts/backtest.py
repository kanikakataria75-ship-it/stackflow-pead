"""PEAD Part F - tradeability. Runs ONLY because the primary cell was CONFIRMED.

Long-only: buy every top-quintile SUE event at the next-day open, hold 60 trading days,
equal weight, max 15 concurrent positions, 0.585% round-trip cost.
"""
import os
import glob
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/pead"
RES = os.path.join(ROOT, "results")
PX = os.path.join(ROOT, "cache", "px")
L1 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
COST = 0.00585
HOLD = 60
MAXPOS = 15


def main():
    ev = pd.read_csv(os.path.join(RES, "pead_events.csv"),
                     parse_dates=["event_day", "entry_date"])
    ev = ev[(ev.quintile == 5) & ev.ret_60d.notna()].sort_values("entry_date")
    print("top-quintile events with completed 60d: %d" % len(ev))

    # sequential book with a concurrency cap
    open_until = []
    taken = []
    for r in ev.itertuples():
        open_until = [d for d in open_until if d > r.entry_date]
        if len(open_until) >= MAXPOS:
            continue
        taken.append(r)
        # approximate exit date by 60 trading days ~ 88 calendar days
        open_until.append(r.entry_date + pd.Timedelta(days=88))
    t = pd.DataFrame([dict(symbol=x.symbol, entry=x.entry_date, ret=x.ret_60d,
                           xs_nifty=x.xs_nifty_60d, xs_univ=x.xs_univ_60d)
                      for x in taken])
    t["net"] = t.ret - COST
    print("trades taken (cap %d concurrent): %d of %d" % (MAXPOS, len(t), len(ev)))

    n = len(t)
    gross = t.ret.mean()
    net = t.net.mean()
    print("\n--- per-trade (60 trading days) ---")
    print("  gross mean        %+.3f%%" % (100 * gross))
    print("  cost              -%.3f%%" % (100 * COST))
    print("  NET mean          %+.3f%%" % (100 * net))
    print("  median net        %+.3f%%" % (100 * (t.ret.median() - COST)))
    print("  win rate (net>0)  %.1f%%" % (100 * (t.net > 0).mean()))
    print("  vs Nifty 500      %+.3f%%" % (100 * t.xs_nifty.mean()))
    print("  vs event universe %+.3f%%" % (100 * t.xs_univ.mean()))

    # equity curve: equal-weight sleeve, each trade 1/MAXPOS of book
    t = t.sort_values("entry")
    t["exit"] = t.entry + pd.Timedelta(days=88)
    days = pd.date_range(t.entry.min(), t.exit.max(), freq="B")
    eq = pd.Series(1.0, index=days)
    # simple approximation: distribute each trade's net return linearly over its holding window
    daily = pd.Series(0.0, index=days)
    for r in t.itertuples():
        w = days[(days >= r.entry) & (days <= r.exit)]
        if len(w) == 0:
            continue
        daily.loc[w] += (r.net / MAXPOS) / len(w)
    eq = (1 + daily).cumprod()
    yrs = (days[-1] - days[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else np.nan
    dd = (eq / eq.cummax() - 1).min()
    print("\n--- book (equal weight, %d sleeves, %.1f years) ---" % (MAXPOS, yrs))
    print("  CAGR              %+.2f%%" % (100 * cagr))
    print("  max drawdown      %.2f%%" % (100 * dd))
    print("  final equity      %.3fx" % eq.iloc[-1])

    b = pd.read_csv(os.path.join(L1, "sector_close_panel.csv"), index_col=0,
                    parse_dates=True)["NIFTY 500"].dropna()
    b = b[(b.index >= days[0]) & (b.index <= days[-1])]
    if len(b) > 2:
        bc = (b.iloc[-1] / b.iloc[0]) ** (1 / yrs) - 1
        bdd = (b / b.cummax() - 1).min()
        print("  Nifty 500 CAGR    %+.2f%%   maxDD %.2f%%" % (100 * bc, 100 * bdd))
    t.to_csv(os.path.join(RES, "pead_trades.csv"), index=False)
    eq.to_frame("equity").to_csv(os.path.join(RES, "pead_equity.csv"))


if __name__ == "__main__":
    main()
