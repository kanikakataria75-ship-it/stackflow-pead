"""Layer 4 Parts C/D/E - returns, holdout evaluation, surprise control, deliverables.

Executes what pre_registration.md fixed. Produces the three CSVs and the numbers
that RESULTS_layer4.md reports.
"""
import os
import sys
import glob
import json
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer4"
CACHE = os.path.join(ROOT, "cache")
RES = os.path.join(ROOT, "results")
XB = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl/cache"
L1 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
os.makedirs(RES, exist_ok=True)

HOR = {"5d": 5, "10d": 10, "30d": 30, "6m": 126}
COST = 0.585          # % round trip, LeadFlow NSE cost model
DISC_END = pd.Timestamp("2023-12-31")
MIN_TURNOVER = 1e7    # INR 1 crore
MIN_PRICE = 50.0      # INR


def load_px():
    px = {}
    for f in glob.glob(os.path.join(CACHE, "px", "*.csv")):
        s = os.path.basename(f)[:-4]
        try:
            d = pd.read_csv(f, index_col=0, parse_dates=True)
            if len(d) > 200 and {"Open", "Close", "Volume"} <= set(d.columns):
                px[s] = d.sort_index()
        except Exception:
            pass
    return px


def bench():
    b = pd.read_csv(os.path.join(L1, "sector_close_panel.csv"), index_col=0,
                    parse_dates=True)["NIFTY 500"].dropna()
    return b


def surprise_table():
    """Earnings surprise from the XBRL cache: YoY PAT change / sd(past YoY changes)."""
    f = os.path.join(XB, "extract_universe.csv")
    if not os.path.exists(f):
        return pd.DataFrame(columns=["symbol", "filing_date", "surprise"])
    d = pd.read_csv(f)
    d = d[(d.period == "Quarterly") & d.pat.notna()].copy()
    d["filing_date"] = pd.to_datetime(d.filing_date, errors="coerce")
    d["pe"] = pd.to_datetime(d.period_end, errors="coerce")
    d = d[d.filing_date.notna() & d.pe.notna()].sort_values(["symbol", "pe"])
    out = []
    for sym, g in d.groupby("symbol"):
        g = g.drop_duplicates("pe").sort_values("pe")
        pat = g.pat.values
        yoy = np.full(len(g), np.nan)
        for i in range(4, len(g)):
            base = abs(pat[i - 4])
            if base > 0:
                yoy[i] = (pat[i] - pat[i - 4]) / base
        g = g.assign(yoy=yoy)
        sd = pd.Series(yoy).expanding(min_periods=4).std().shift(1).values
        g = g.assign(surprise=np.where((sd is not None) & np.isfinite(sd) & (sd > 0),
                                       yoy / sd, np.nan))
        out.append(g[["symbol", "filing_date", "surprise"]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main():
    feat = pd.read_csv(os.path.join(CACHE, "transcript_features.csv"))
    feat["filing_date"] = pd.to_datetime(feat.filing_date, errors="coerce")
    feat["call_date"] = pd.to_datetime(feat.call_date, errors="coerce")
    # event date: call date where parsed and sane, else filing date
    cd = feat.call_date
    ok = cd.notna() & (cd <= feat.filing_date) & (cd >= feat.filing_date - pd.Timedelta(days=45))
    feat["event_date"] = np.where(ok, cd, feat.filing_date)
    feat["event_date"] = pd.to_datetime(feat.event_date)
    feat["event_src"] = np.where(ok, "call_date", "filing_date")
    px = load_px()
    b = bench()
    print("features=%d  symbols=%d  with prices=%d" %
          (len(feat), feat.symbol.nunique(),
           sum(1 for s in feat.symbol.unique() if str(s) in px)))

    rows = []
    for r in feat.itertuples():
        s = str(r.symbol)
        if s not in px:
            continue
        d = px[s]
        after = d.index[d.index > r.event_date]
        if len(after) == 0:
            continue
        e = d.index.get_loc(after[0])
        # point-in-time liquidity filter over the 20 sessions BEFORE entry
        w = d.iloc[max(0, e - 20):e]
        if len(w) < 10:
            continue
        turn = (w.Close * w.Volume).mean()
        if not np.isfinite(turn) or turn < MIN_TURNOVER:
            continue
        p0 = d.Open.iloc[e]
        if not np.isfinite(p0) or p0 <= MIN_PRICE:
            continue
        rec = dict(symbol=s, event_date=r.event_date, entry_date=d.index[e],
                   entry_open=p0, event_src=r.event_src)
        for k, h in HOR.items():
            j = e + h
            if j < len(d):
                px_ret = d.Close.iloc[j] / p0 - 1.0
                bi = b.index.searchsorted(d.index[e])
                bj = b.index.searchsorted(d.index[j])
                bret = (b.iloc[bj] / b.iloc[bi] - 1.0) if bj < len(b) and bi < len(b) else np.nan
                rec["ret_" + k] = px_ret
                rec["xs_nifty_" + k] = px_ret - bret
            else:
                rec["ret_" + k] = np.nan          # never partially filled
                rec["xs_nifty_" + k] = np.nan
        rows.append(rec)
    ev = pd.DataFrame(rows)
    print("events with returns: %d" % len(ev))

    # xs_univ: excess vs equal-weight mean of all event stocks entering the same month
    ev["ym"] = ev.entry_date.dt.to_period("M")
    for k in HOR:
        m = ev.groupby("ym")["ret_" + k].transform("mean")
        ev["xs_univ_" + k] = ev["ret_" + k] - m

    ev["period"] = np.where(ev.event_date <= DISC_END, "discovery", "holdout")
    f2 = feat.copy()
    f2["event_date"] = pd.to_datetime(f2.event_date)
    key = ["symbol", "event_date"]
    ev = ev.merge(f2.drop(columns=["event_src"]), on=key, how="left",
                  suffixes=("", "_f"))

    sup = surprise_table()
    if len(sup):
        sup = sup.sort_values("filing_date")
        ev = ev.sort_values("event_date")
        ev = pd.merge_asof(ev, sup.rename(columns={"filing_date": "sdate"}),
                           left_on="event_date", right_on="sdate", by="symbol",
                           direction="backward",
                           tolerance=pd.Timedelta(days=150))
    else:
        ev["surprise"] = np.nan
    ev.to_csv(os.path.join(RES, "call_events.csv"), index=False)
    print("call_events.csv written: %d rows  surprise coverage %.0f%%"
          % (len(ev), 100 * ev.surprise.notna().mean()))
    return ev


if __name__ == "__main__":
    main()
