"""Audit-corrected PEAD V2 event dataset, rebuilt from raw inputs (not inherited from V1).

Applies the audit fixes that live in the data layer:
  Fix 4  - Non-Financials by the XBRL pipeline's own `fin` flag (taxonomy BANKING/NBFC OR
           industry == FINANCIAL SERVICES): excludes NBFCs, AMCs, exchanges, rating agencies,
           insurers that file under the plain INDAS taxonomy.
  Fix 5  - SUE with fiscal-quarter-matched YoY (compute_sue_series_datematched).
  Fix 6  - Prices filtered to the NSE (NIFTY 500) session calendar BEFORE event day, entry,
           liquidity filter and forward returns are computed (phantom zero-volume rows removed).
Timing (TIMING_RULES.md, as coded): filing <= 15:30 IST -> event day = first session >= filing
date; after 15:30 -> one session later; entry = OPEN of the session after the event day.
Ex-ante quintiles: model M1 (event_day in [T-365, T), >= 150 prior events), unchanged.

Output: corrected/pead_v2_events_corrected.csv
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, STACKFLOW_ROOT, XBRL_CACHE, CUTOFF, MIN_TURNOVER, MIN_PRICE, DISCOVERY_END
from src.data_loader import load_timestamps, load_prices, load_benchmark
from src.sue_engine import (compute_sue_series_datematched, assign_ex_ante_quintiles_rolling,
                            assign_ex_ante_quintiles_expanding)

HORIZONS = {"5d": 5, "10d": 10, "20d": 20, "30d": 30, "40d": 40, "60d": 60, "90d": 90, "126d": 126}
OUT_DIR = os.path.join(PEAD_V2_ROOT, "corrected")


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    e = pd.read_csv(os.path.join(XBRL_CACHE, "extract_universe.csv"))
    e = e[(e.period == "Quarterly") & e.pat.notna()].copy()
    e["period_end"] = pd.to_datetime(e.period_end, errors="coerce")
    e = e[e.period_end.notna()].copy()
    ts = load_timestamps()[["symbol", "to_date", "ts"]].rename(columns={"to_date": "period_end"})
    e = e.merge(ts, on=["symbol", "period_end"], how="left")

    parts = []
    for sym, g in e.groupby("symbol"):
        g = g.sort_values("period_end").copy()
        g["sue"], g["yoy_pat"] = compute_sue_series_datematched(g.period_end.values, g.pat.values.astype(float))
        parts.append(g)
    e = pd.concat(parts, ignore_index=True)
    n_rows, n_nosue = len(e), int(e.sue.isna().sum())
    e = e[e.sue.notna() & e.ts.notna()].copy()

    px = load_prices()            # Fix 6: calendar-filtered
    bench = load_benchmark()
    rows, drops = [], dict(no_px=0, no_session=0, short_hist=0, liquidity=0, price=0)
    for r in e.itertuples():
        s = str(r.symbol)
        if s not in px:
            drops["no_px"] += 1
            continue
        d = px[s]
        ix = d.index
        t = pd.Timestamp(r.ts)
        day = t.normalize()
        k = ix.searchsorted(day)
        if (t - day) > CUTOFF:
            k += 1
        if k + 1 >= len(ix):
            drops["no_session"] += 1
            continue
        evi, ei = k, k + 1
        w = d.iloc[max(0, evi - 20):evi]
        if len(w) < 10:
            drops["short_hist"] += 1
            continue
        turn = float((w.Close * w.Volume).mean())
        if not (turn >= MIN_TURNOVER):
            drops["liquidity"] += 1
            continue
        p0 = float(d.Open.iloc[ei])
        if not (p0 > MIN_PRICE):
            drops["price"] += 1
            continue
        rec = dict(symbol=s, industry=r.industry, period_end=r.period_end, filing_ts=t,
                   event_day=ix[evi], entry_date=ix[ei], entry_open=p0, turnover20=turn,
                   pat=r.pat, sue=r.sue, basis=r.basis, taxonomy=r.taxonomy,
                   is_fin=bool(r.fin), is_fin_taxonomy_only=bool(pd.Series([r.taxonomy]).str.contains("BANKING|NBFC_INDAS").iloc[0]),
                   ctx_inferred=bool(r.ctx_inferred))
        for h, n in HORIZONS.items():
            j = ei + n
            if j < len(ix):
                rr = float(d.Close.iloc[j]) / p0 - 1.0
                br = float(bench.asof(ix[j]) / bench.asof(ix[ei]) - 1.0)
                rec[f"ret_{h}"], rec[f"xs_nifty_{h}"] = rr, rr - br
            else:
                rec[f"ret_{h}"], rec[f"xs_nifty_{h}"] = np.nan, np.nan
        rows.append(rec)
    ev = pd.DataFrame(rows)
    ev["ym"] = ev.entry_date.dt.to_period("M")
    for h in HORIZONS:
        ev[f"xs_univ_{h}"] = ev[f"ret_{h}"] - ev.groupby("ym")[f"ret_{h}"].transform("mean")
    ev = ev.sort_values("event_day").reset_index(drop=True)
    ev["q_exante_4q"] = assign_ex_ante_quintiles_rolling(ev, "event_day", "sue", lookback_days=365, min_events=150)
    ev["q_exante_8q"] = assign_ex_ante_quintiles_rolling(ev, "event_day", "sue", lookback_days=730, min_events=250)
    ev["q_exante_exp"] = assign_ex_ante_quintiles_expanding(ev, "event_day", "sue", min_events=150)
    ev["qtr"] = ev.event_day.dt.to_period("Q").astype(str)
    ev["period"] = np.where(ev.event_day <= DISCOVERY_END, "discovery", "holdout")
    ev["days_from_qe"] = (ev.event_day - ev.period_end).dt.days
    ev["filing_cohort"] = np.where(ev.days_from_qe <= 25, "Early", np.where(ev.days_from_qe <= 45, "Mid", "Late"))
    q33 = ev.groupby("ym")["turnover20"].transform(lambda s: s.quantile(0.333))
    q66 = ev.groupby("ym")["turnover20"].transform(lambda s: s.quantile(0.666))
    ev["size_tercile"] = np.where(ev.turnover20 <= q33, "Small", np.where(ev.turnover20 <= q66, "Mid", "Large"))
    # Layer-4-seen flag (same rule as V1: symbol + calendar quarter of the concall event)
    seen = set()
    p4 = os.path.join(STACKFLOW_ROOT, "layer4", "results", "call_events.csv")
    if os.path.exists(p4):
        c4 = pd.read_csv(p4)
        if "surprise" in c4.columns:
            c4 = c4[c4.surprise.notna()]
            for s, dte in zip(c4.symbol, pd.to_datetime(c4.event_date, errors="coerce")):
                if pd.notna(dte):
                    seen.add((str(s), str(dte.to_period("Q"))))
    ev["layer4_seen"] = [(s, q) in seen for s, q in zip(ev.symbol, ev.qtr)]
    ev = ev.drop(columns=["ym"])
    out = os.path.join(OUT_DIR, "pead_v2_events_corrected.csv")
    ev.to_csv(out, index=False)
    print(f"quarterly PAT rows {n_rows}; no date-matched SUE {n_nosue}; drops {drops}")
    print(f"events {len(ev)} symbols {ev.symbol.nunique()} | with 4Q quintile {ev.q_exante_4q.notna().sum()} | "
          f"financial {ev.is_fin.sum()} | layer4_seen {ev.layer4_seen.sum()} -> {out}")
    return ev


if __name__ == "__main__":
    build()
