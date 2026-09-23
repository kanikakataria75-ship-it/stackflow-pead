"""PEAD Part A - build the event table with correct timing.

Reads the XBRL cache READ-ONLY. All LOCKED_DECISIONS rules already applied upstream
(earliest parseable filing per company-period, Consolidated-first, context rules,
ratio tags banned).

Timing is the look-ahead-critical part:
  - filing timestamp <= 15:30 IST  -> event day = that trading day
  - filing timestamp >  15:30 IST  -> event day = next trading day
  - no usable timestamp            -> next trading day (conservative)
  - ENTRY = OPEN of the trading day AFTER the event day. Never same-day close.
"""
import os
import glob
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/pead"
XB = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl/cache"
PX = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer4/cache/px"
L1 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)

MIN_TURNOVER = 1e7     # INR 1 crore
MIN_PRICE = 50.0       # INR
CUTOFF = pd.Timedelta(hours=15, minutes=30)


def timestamps():
    """symbol+period_end+basis -> full filing timestamp, from both filing systems."""
    rows = []
    L = pd.read_csv(os.path.join(XB, "filing_index.csv"))
    L = L[L.has_xml == True]
    ts = pd.to_datetime(L.filing_date, format="%d-%b-%Y %H:%M", errors="coerce")
    rows.append(pd.DataFrame(dict(symbol=L.symbol, basis=L.basis,
                                  to_date=pd.to_datetime(L.to_date, format="%d-%b-%Y",
                                                         errors="coerce"),
                                  ts=ts)))
    I = pd.read_csv(os.path.join(XB, "filing_index_integrated.csv"))
    I = I[(I.filing_type == "Integrated Filing- Financials") & (I.has_xml == True)]
    ts2 = pd.to_datetime(I.broadcast, format="%d-%b-%Y %H:%M:%S", errors="coerce")
    rows.append(pd.DataFrame(dict(symbol=I.symbol, basis=I.basis,
                                  to_date=pd.to_datetime(I.qe_date, format="%d-%b-%Y",
                                                         errors="coerce"),
                                  ts=ts2)))
    d = pd.concat(rows, ignore_index=True).dropna(subset=["symbol", "to_date"])
    d = d.sort_values("ts").groupby(["symbol", "to_date"], as_index=False).first()
    return d


def load_px():
    px = {}
    for f in glob.glob(os.path.join(PX, "*.csv")):
        s = os.path.basename(f)[:-4]
        try:
            d = pd.read_csv(f, index_col=0, parse_dates=True)
            if len(d) > 200 and {"Open", "Close", "Volume"} <= set(d.columns):
                px[s] = d.sort_index()
        except Exception:
            pass
    return px


def main():
    e = pd.read_csv(os.path.join(XB, "extract_universe.csv"))
    e = e[(e.period == "Quarterly") & e.pat.notna()].copy()
    e["period_end"] = pd.to_datetime(e.period_end, errors="coerce")
    e["fdate"] = pd.to_datetime(e.filing_date, errors="coerce")
    e = e[e.period_end.notna() & e.fdate.notna()]
    print("quarterly rows with PAT: %d  symbols: %d" % (len(e), e.symbol.nunique()))

    ts = timestamps()
    e = e.merge(ts.rename(columns={"to_date": "period_end", "basis": "basis_idx"}),
                on=["symbol", "period_end"], how="left")
    e["has_time"] = e.ts.notna()
    print("events with a usable filing TIMESTAMP: %d / %d (%.1f%%)"
          % (e.has_time.sum(), len(e), 100 * e.has_time.mean()))

    px = load_px()
    print("price series available: %d symbols" % len(px))

    rows = []
    for r in e.itertuples():
        s = str(r.symbol)
        if s not in px:
            continue
        d = px[s]
        # --- event day ---
        if pd.notna(r.ts):
            base = pd.Timestamp(r.ts).normalize()
            after_hours = (pd.Timestamp(r.ts) - base) > CUTOFF
        else:
            base = pd.Timestamp(r.fdate).normalize()
            after_hours = True                      # conservative
        cand = d.index[d.index >= base]
        if len(cand) == 0:
            continue
        ev = cand[0]
        if after_hours or ev < base:
            nxt = d.index[d.index > ev]
            if len(nxt) == 0:
                continue
            ev = nxt[0]
        # --- entry = OPEN of the day AFTER the event day ---
        nxt = d.index[d.index > ev]
        if len(nxt) == 0:
            continue
        entry = nxt[0]
        ei = d.index.get_loc(entry)
        evi = d.index.get_loc(ev)
        # --- liquidity filter as of the EVENT day ---
        w = d.iloc[max(0, evi - 20):evi]
        if len(w) < 10:
            continue
        turn = float((w.Close * w.Volume).mean())
        if not np.isfinite(turn) or turn < MIN_TURNOVER:
            continue
        p0 = d.Open.iloc[ei]
        if not np.isfinite(p0) or p0 <= MIN_PRICE:
            continue
        rows.append(dict(symbol=s, company=getattr(r, "company", ""),
                         period_end=r.period_end, filing_ts=r.ts,
                         filing_date=r.fdate, has_time=bool(pd.notna(r.ts)),
                         event_day=ev, entry_date=entry, entry_open=float(p0),
                         turnover20=turn,
                         pat=r.pat, revenue=getattr(r, "revenue", np.nan),
                         basis=r.basis, taxonomy=r.taxonomy,
                         ctx_inferred=bool(r.ctx_inferred), src=r.src))
    ev = pd.DataFrame(rows)
    ev.to_csv(os.path.join(CACHE, "events_raw.csv"), index=False)
    print("\nEVENTS after timing + liquidity filters: %d  symbols: %d"
          % (len(ev), ev.symbol.nunique()))
    ev["y"] = ev.event_day.dt.year
    ev["q"] = ev.event_day.dt.to_period("Q").astype(str)
    print("\nby year:")
    print(ev.groupby("y").agg(events=("symbol", "size"), symbols=("symbol", "nunique")).to_string())
    print("\nby quarter (first 8 / last 8):")
    g = ev.groupby("q").size()
    print(pd.concat([g.head(8), g.tail(8)]).to_string())
    print("\nfiling-time availability among used events: %.1f%%" % (100 * ev.has_time.mean()))
    print("ctx_inferred: %.1f%%" % (100 * ev.ctx_inferred.mean()))


if __name__ == "__main__":
    main()
