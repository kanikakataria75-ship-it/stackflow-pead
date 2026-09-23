"""PEAD Parts B-E. Executes exactly what pre_registration.md fixed."""
import os
import glob
import json
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/pead"
XB = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl/cache"
PX = os.path.join(ROOT, "cache", "px")
L1 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
L4 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer4/results"
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)

HOR = {"5d": 5, "10d": 10, "30d": 30, "60d": 60, "126d": 126}
MIN_TURNOVER, MIN_PRICE = 1e7, 50.0
CUTOFF = pd.Timedelta(hours=15, minutes=30)
DISC_END = pd.Timestamp("2023-12-31")
COST = 0.585
MIN_PRIOR = 6


def load_px():
    px = {}
    for f in glob.glob(os.path.join(PX, "*.csv")):
        s = os.path.basename(f)[:-4]
        try:
            d = pd.read_csv(f, index_col=0, parse_dates=True)
            if len(d) > 300 and {"Open", "Close", "Volume"} <= set(d.columns):
                px[s] = d.sort_index()
        except Exception:
            pass
    return px


def timestamps():
    rows = []
    L = pd.read_csv(os.path.join(XB, "filing_index.csv"))
    L = L[L.has_xml == True]
    rows.append(pd.DataFrame(dict(
        symbol=L.symbol,
        to_date=pd.to_datetime(L.to_date, format="%d-%b-%Y", errors="coerce"),
        ts=pd.to_datetime(L.filing_date, format="%d-%b-%Y %H:%M", errors="coerce"))))
    I = pd.read_csv(os.path.join(XB, "filing_index_integrated.csv"))
    I = I[(I.filing_type == "Integrated Filing- Financials") & (I.has_xml == True)]
    rows.append(pd.DataFrame(dict(
        symbol=I.symbol,
        to_date=pd.to_datetime(I.qe_date, format="%d-%b-%Y", errors="coerce"),
        ts=pd.to_datetime(I.broadcast, format="%d-%b-%Y %H:%M:%S", errors="coerce"))))
    d = pd.concat(rows, ignore_index=True).dropna(subset=["symbol", "to_date"])
    return d.sort_values("ts").groupby(["symbol", "to_date"], as_index=False).first()


def sue_series(vals):
    """SUE with >=MIN_PRIOR prior YoY changes; returns array aligned to vals."""
    n = len(vals)
    yoy = np.full(n, np.nan)
    for i in range(4, n):
        yoy[i] = vals[i] - vals[i - 4]
    out = np.full(n, np.nan)
    for i in range(n):
        hist = yoy[max(0, i - 8):i]
        hist = hist[np.isfinite(hist)]
        if len(hist) >= MIN_PRIOR and np.isfinite(yoy[i]):
            sd = hist.std(ddof=1)
            if sd > 0:
                out[i] = yoy[i] / sd
    return out, yoy


def main():
    e = pd.read_csv(os.path.join(XB, "extract_universe.csv"))
    e = e[(e.period == "Quarterly") & e.pat.notna()].copy()
    e["period_end"] = pd.to_datetime(e.period_end, errors="coerce")
    e["fdate"] = pd.to_datetime(e.filing_date, errors="coerce")
    e = e[e.period_end.notna() & e.fdate.notna()]
    e = e.merge(timestamps(), left_on=["symbol", "period_end"],
                right_on=["symbol", "to_date"], how="left")

    # --- SUE per company, in period order (no look-ahead: history only) ---
    parts = []
    dropped = 0
    for sym, g in e.groupby("symbol"):
        g = g.drop_duplicates("period_end").sort_values("period_end").copy()
        s, y = sue_series(g.pat.values)
        g["sue"] = s
        g["yoy_pat"] = y
        g["pat_prev"] = g.pat.shift(4)
        if "revenue" in g.columns and g.revenue.notna().sum() > 8:
            rs, _ = sue_series(g.revenue.values)
            g["sue_rev"] = rs
        else:
            g["sue_rev"] = np.nan
        dropped += int(g.sue.isna().sum())
        parts.append(g)
    e = pd.concat(parts, ignore_index=True)
    print("events before SUE: %d   dropped for <%d prior YoY: %d"
          % (len(e), MIN_PRIOR, dropped))
    e = e[e.sue.notna()].copy()

    px = load_px()
    b = pd.read_csv(os.path.join(L1, "sector_close_panel.csv"), index_col=0,
                    parse_dates=True)["NIFTY 500"].dropna()
    rows = []
    for r in e.itertuples():
        s = str(r.symbol)
        if s not in px:
            continue
        d = px[s]
        if pd.notna(r.ts):
            base = pd.Timestamp(r.ts).normalize()
            after = (pd.Timestamp(r.ts) - base) > CUTOFF
        else:
            base = pd.Timestamp(r.fdate).normalize()
            after = True
        c = d.index[d.index >= base]
        if len(c) == 0:
            continue
        ev = c[0]
        if after or ev < base:
            nx = d.index[d.index > ev]
            if len(nx) == 0:
                continue
            ev = nx[0]
        nx = d.index[d.index > ev]
        if len(nx) == 0:
            continue
        entry = nx[0]
        ei, evi = d.index.get_loc(entry), d.index.get_loc(ev)
        w = d.iloc[max(0, evi - 20):evi]
        if len(w) < 10:
            continue
        turn = float((w.Close * w.Volume).mean())
        if not np.isfinite(turn) or turn < MIN_TURNOVER:
            continue
        p0 = d.Open.iloc[ei]
        if not np.isfinite(p0) or p0 <= MIN_PRICE:
            continue
        rec = dict(symbol=s, period_end=r.period_end, filing_ts=r.ts,
                   event_day=ev, entry_date=entry, entry_open=float(p0),
                   turnover20=turn, pat=r.pat, pat_prev=r.pat_prev,
                   sue=r.sue, sue_rev=r.sue_rev, basis=r.basis,
                   taxonomy=r.taxonomy, ctx_inferred=bool(r.ctx_inferred))
        # EAR as specified in the brief: event day -1 to +1. NOTE: entry is the OPEN of
        # ev+1, so this window ENDS inside the day being traded -> it is NOT knowable at
        # entry. Kept for reference and clearly flagged as contaminated.
        if evi >= 1 and evi + 1 < len(d):
            sr = d.Close.iloc[evi + 1] / d.Close.iloc[evi - 1] - 1
            i0 = b.index.searchsorted(d.index[evi - 1])
            i1 = b.index.searchsorted(d.index[evi + 1])
            br = (b.iloc[i1] / b.iloc[i0] - 1) if i1 < len(b) else np.nan
            rec["ear_lookahead"] = sr - br
        else:
            rec["ear_lookahead"] = np.nan
        # EAR_clean: event day -1 to event day CLOSE. Fully knowable before the ev+1 open
        # entry. This is the version any verdict may use.
        if evi >= 1:
            sr = d.Close.iloc[evi] / d.Close.iloc[evi - 1] - 1
            i0 = b.index.searchsorted(d.index[evi - 1])
            i1 = b.index.searchsorted(d.index[evi])
            br = (b.iloc[i1] / b.iloc[i0] - 1) if i1 < len(b) else np.nan
            rec["ear"] = sr - br
        else:
            rec["ear"] = np.nan
        for k, h in HOR.items():
            j = ei + h
            if j < len(d):
                rr = d.Close.iloc[j] / p0 - 1.0
                i0 = b.index.searchsorted(d.index[ei])
                i1 = b.index.searchsorted(d.index[j])
                br = (b.iloc[i1] / b.iloc[i0] - 1) if i1 < len(b) and i0 < len(b) else np.nan
                rec["ret_" + k] = rr
                rec["xs_nifty_" + k] = rr - br
            else:
                rec["ret_" + k] = np.nan
                rec["xs_nifty_" + k] = np.nan
        rows.append(rec)
    ev = pd.DataFrame(rows)
    print("EVENTS with SUE + prices + filters: %d  symbols: %d" % (len(ev), ev.symbol.nunique()))

    ev["ym"] = ev.entry_date.dt.to_period("M")
    for k in HOR:
        ev["xs_univ_" + k] = ev["ret_" + k] - ev.groupby("ym")["ret_" + k].transform("mean")
    ev["qtr"] = ev.event_day.dt.to_period("Q")
    ev["period"] = np.where(ev.event_day <= DISC_END, "discovery", "holdout")
    ev["is_fin"] = ev.taxonomy.str.contains("BANKING|NBFC_INDAS", na=False)
    # quintiles within each calendar quarter
    def qcut(g, col, n=5):
        try:
            return pd.qcut(g[col].rank(method="first"), n, labels=[1, 2, 3, 4, 5])
        except Exception:
            return pd.Series(np.nan, index=g.index)
    ev["quintile"] = ev.groupby("qtr", group_keys=False).apply(lambda g: qcut(g, "sue"))
    ev["quintile_rev"] = ev.groupby("qtr", group_keys=False).apply(lambda g: qcut(g, "sue_rev"))
    ev["quintile_ear"] = ev.groupby("qtr", group_keys=False).apply(lambda g: qcut(g, "ear"))
    ev["quintile_earla"] = ev.groupby("qtr", group_keys=False).apply(lambda g: qcut(g, "ear_lookahead"))

    # layer4_seen flag
    seen = set()
    p4 = os.path.join(L4, "call_events.csv")
    if os.path.exists(p4):
        c4 = pd.read_csv(p4)
        if "surprise" in c4.columns:
            c4 = c4[c4.surprise.notna()]
            c4["ed"] = pd.to_datetime(c4.event_date, errors="coerce")
            for r in c4.itertuples():
                seen.add((str(r.symbol), pd.Timestamp(r.ed).to_period("Q")))
    ev["layer4_seen"] = [(s, q) in seen for s, q in zip(ev.symbol, ev.qtr)]
    print("layer4_seen events flagged: %d" % ev.layer4_seen.sum())
    ev.to_csv(os.path.join(RES, "pead_events.csv"), index=False)
    return ev


if __name__ == "__main__":
    main()
