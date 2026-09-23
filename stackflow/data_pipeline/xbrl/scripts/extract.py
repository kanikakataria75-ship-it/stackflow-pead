"""Step 2.2/2.4 - run extraction over a chosen symbol set.

Usage: python extract.py <mode> [symbols...]
  mode = 'test'      -> the 5 Step-2.1 companies
  mode = 'universe'  -> Layer 1 pass-through universe (Step 2.4)
"""
import os
import sys
import json
import time
import collections
import warnings

warnings.filterwarnings("ignore")
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_xbrl import sess, download, parse_one, local, iso, CACHE, TAXMAP

L2 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2/cache"


def load_index():
    L = pd.read_csv(os.path.join(CACHE, "filing_index.csv"))
    L = L[L.has_xml == True].copy()
    L["src"] = "legacy"
    L["from_iso"] = L.from_date.map(iso)
    L["to_iso"] = L.to_date.map(iso)
    L["filed"] = pd.to_datetime(L.filing_date.str.slice(0, 11), format="%d-%b-%Y", errors="coerce")
    L["type_sub"] = "Original"
    L = L[["symbol", "period", "basis", "taxonomy", "from_iso", "to_iso", "filed",
           "xbrl", "src", "type_sub", "audited"]]

    I = pd.read_csv(os.path.join(CACHE, "filing_index_integrated.csv"))
    I = I[(I.filing_type == "Integrated Filing- Financials") & (I.has_xml == True)].copy()
    I["src"] = "integrated"
    I["to_iso"] = I.qe_date.map(iso)
    # integrated filings are quarterly results; Q-end minus one quarter start
    _te = pd.to_datetime(I.to_iso, errors="coerce")
    # vectorised quarter-start; elementwise DateOffset on 26k rows takes minutes
    I["from_iso"] = pd.PeriodIndex(_te, freq="Q").start_time.strftime("%Y-%m-%d")
    I["filed"] = pd.to_datetime(I.broadcast.str.slice(0, 11), format="%d-%b-%Y", errors="coerce")
    I["period"] = "Quarterly"
    I = I[["symbol", "period", "basis", "taxonomy", "from_iso", "to_iso", "filed",
           "xbrl", "src", "type_sub", "audited"]]
    return pd.concat([L, I], ignore_index=True)


def select_filings(idx, symbols):
    """D1: Consolidated preferred, Non-Consolidated fallback.
    D5 (interim): keep the EARLIEST filing per (symbol, period, from, to, basis)."""
    d = idx[idx.symbol.isin(symbols)].copy()
    d = d.sort_values("filed")
    d["basis_rank"] = (d.basis != "Consolidated").astype(int)  # 0 = Consolidated
    d = (d.sort_values(["symbol", "period", "from_iso", "to_iso", "basis_rank", "filed"])
           .groupby(["symbol", "period", "from_iso", "to_iso"], as_index=False)
           .first())
    return d


def run(symbols, out_name):
    idx = load_index()
    sel = select_filings(idx, symbols)
    sel = sel[sel.from_iso.notna() & sel.to_iso.notna()]
    print("filings selected: %d  (symbols=%d)" % (len(sel), sel.symbol.nunique()), flush=True)

    # RESUMABLE: skip rows already extracted in a previous pass
    path = os.path.join(CACHE, out_name)
    done = set()
    prev = []
    if os.path.exists(path):
        try:
            p0 = pd.read_csv(path)
            prev = p0.to_dict("records")
            done = set(zip(p0.symbol, p0.period, p0.period_start, p0.period_end))
            print("resuming: %d rows already extracted" % len(prev), flush=True)
        except Exception:
            prev, done = [], set()

    s = sess()
    rows, fails = list(prev), collections.Counter()
    since_flush = 0
    for i, r in enumerate(sel.itertuples(), 1):
        if (r.symbol, r.period, r.from_iso, r.to_iso) in done:
            continue
        fn = download(s, r.xbrl)
        if fn is None:
            fails["download_failed"] += 1
            continue
        rec, why = parse_one(fn, r.taxonomy, r.from_iso, r.to_iso)
        if rec is None:
            fails[why.split(":")[0]] += 1
            continue
        if why:
            fails[why.split(":")[0]] += 1
        rows.append(dict(symbol=r.symbol, period=r.period, basis=r.basis,
                         taxonomy=r.taxonomy, src=r.src, type_sub=r.type_sub,
                         audited=r.audited,
                         period_start=r.from_iso, period_end=r.to_iso,
                         filing_date=r.filed.strftime("%Y-%m-%d") if pd.notna(r.filed) else "",
                         pbt=rec["pbt"], interest=rec["interest"], pat=rec["pat"],
                         revenue=rec["revenue"], share_capital=rec["share_capital"],
                         reserves=rec["reserves"], equity=rec["equity"],
                         ok_ic=rec["ok_ic"], ok_roe=rec["ok_roe"],
                         ctx_inferred=rec.get("ctx_inferred", False),
                         reasons=rec["reasons"]))
        since_flush += 1
        if since_flush >= 250:
            pd.DataFrame(rows).to_csv(path, index=False)   # checkpoint
            since_flush = 0
            print("  ...%d/%d  rows=%d  [checkpointed]" % (i, len(sel), len(rows)), flush=True)
        time.sleep(0.05)

    d = pd.DataFrame(rows)
    d.to_csv(path, index=False)
    print("\n=== EXTRACTION SUMMARY ===")
    print("filings attempted : %d" % len(sel))
    print("rows produced     : %d" % len(d))
    if len(d):
        print("usable for IC     : %d (%.1f%%)" % (d.ok_ic.sum(), 100 * d.ok_ic.mean()))
        print("usable for ROE    : %d (%.1f%%)" % (d.ok_roe.sum(), 100 * d.ok_roe.mean()))
        print("ctx_inferred rows : %d (%.1f%%)  [D11 audit flag]" % (d.ctx_inferred.sum(), 100 * d.ctx_inferred.mean()))
    print("\nFAILURES BY TYPE (not an aggregate %):")
    for k, v in fails.most_common():
        print("   %-28s %5d  (%.1f%% of attempted)" % (k, v, 100 * v / max(len(sel), 1)))
    print("\nwritten:", path)
    return d


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    if mode == "test":
        run(["RELIANCE", "VOLTAS", "CANFINHOME", "HDFCBANK", "GRANULES"],
            "extract_test.csv")
    else:
        u = pd.read_csv(os.path.join(L2, "pit_universe_2020.csv"))
        run(sorted(set(u.Symbol.astype(str))), "extract_universe.csv")
