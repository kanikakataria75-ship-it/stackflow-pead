"""Step 2.4b - build the ANNUAL (ROE) table properly.

WHY THIS EXISTS
The first pass under-counted ROE badly:
  - legacy annual filings for FY2023/FY2024 carry `reserves` but PAT failed to resolve,
    because their defined contexts do not start at the index's declared from_date;
  - integrated filings are all labelled `Quarterly`, so March-quarter filings - which
    carry FULL-YEAR figures in their fiscal-year-to-date context AND year-end equity -
    were never considered for ROE at all.
Result was 4 annual observations per company spanning FY2017-FY2022 only.

THE FIX
Treat every filing whose period_end is 31 March as an annual observation, and resolve:
  - PAT from the FISCAL-YEAR duration context (1 Apr -> 31 Mar), not the quarter;
  - equity as-at 31 March (D10).
This is a re-read of XML already cached - no new downloads.

It does NOT relax any locked rule: D10 (as-at equity), D11 (ctx_inferred flag),
D12 (earliest parseable filing) and D4 (filing_date availability) all still apply.
"""
import os
import sys
import json
import warnings
from xml.etree import ElementTree as ET

warnings.filterwarnings("ignore")
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_xbrl import contexts, facts, infer_contexts, pick, TAXMAP, local, CACHE
from extract import load_index, select_filings

L2 = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer2/cache"


def annual_record(fn, taxonomy, fy_start, fy_end):
    tm = TAXMAP.get(taxonomy)
    if tm is None:
        return None, "unmapped_taxonomy"
    try:
        root = ET.parse(fn).getroot()
    except Exception as e:
        return None, "malformed_xml:%s" % type(e).__name__
    ctxs = contexts(root)
    fx = facts(root)
    if not fx:
        return None, "no_numeric_facts"
    refs = {cid for lst in fx.values() for cid, _ in lst}
    # D11: for an annual target, FourD is the FY duration ending at fy_end
    ctxs, _ = infer_contexts(ctxs, refs, fy_start, fy_end)
    inf = False
    pat, why_pat, i1 = pick(fx, ctxs, tm["pat"], fy_start, fy_end, "duration")
    pbt, _, i2 = pick(fx, ctxs, tm["pbt"], fy_start, fy_end, "duration")
    interest, _, i3 = pick(fx, ctxs, tm["interest"], fy_start, fy_end, "duration")
    sc, _, i4 = pick(fx, ctxs, tm["share_capital"], fy_start, fy_end, "as_at")
    rs, why_rs, i5 = pick(fx, ctxs, tm["reserves"], fy_start, fy_end, "as_at")
    inf = any([i1, i2, i3, i4, i5])
    eq = sc + rs if (sc is not None and rs is not None) else None
    rec = dict(pat=pat, pbt=pbt, interest=interest, share_capital=sc, reserves=rs,
               equity=eq, ctx_inferred=inf)
    if pat is None or eq is None:
        return rec, (why_pat or why_rs or "incomplete")
    return rec, None


def main():
    idx = load_index()
    u = pd.read_csv(os.path.join(L2, "pit_universe_2020.csv"))
    u["Industry"] = u.Industry.str.strip().str.upper()
    ind = dict(zip(u.Symbol, u.Industry))
    sel = select_filings(idx, sorted(set(u.Symbol.astype(str))))
    sel = sel[sel.from_iso.notna() & sel.to_iso.notna()].copy()
    sel["pe"] = pd.to_datetime(sel.to_iso, errors="coerce")
    ann = sel[sel.pe.dt.month == 3].copy()          # every 31-March filing
    print("31-March filings considered: %d  (symbols=%d)" % (len(ann), ann.symbol.nunique()),
          flush=True)

    rows, fails = [], {}
    for r in ann.itertuples():
        fn = local(r.xbrl)
        if not os.path.exists(fn):
            fails["not_cached"] = fails.get("not_cached", 0) + 1
            continue
        fy_end = r.pe.strftime("%Y-%m-%d")
        fy_start = "%d-04-01" % (r.pe.year - 1)
        rec, why = annual_record(fn, r.taxonomy, fy_start, fy_end)
        if rec is None:
            fails[why.split(":")[0]] = fails.get(why.split(":")[0], 0) + 1
            continue
        if why:
            fails[why.split(":")[0]] = fails.get(why.split(":")[0], 0) + 1
        rows.append(dict(symbol=r.symbol, industry=ind.get(r.symbol),
                         fy_start=fy_start, fy_end=fy_end,
                         fy=r.pe.year - 1,
                         filing_date=r.filed.strftime("%Y-%m-%d") if pd.notna(r.filed) else "",
                         basis=r.basis, taxonomy=r.taxonomy, src=r.src,
                         pat=rec["pat"], pbt=rec["pbt"], interest=rec["interest"],
                         share_capital=rec["share_capital"], reserves=rec["reserves"],
                         equity=rec["equity"], ctx_inferred=rec["ctx_inferred"],
                         ok_roe=(rec["pat"] is not None and rec["equity"] is not None)))

    d = pd.DataFrame(rows)
    # D12: earliest parseable filing per (symbol, fy)
    d = d[d.ok_roe].sort_values("filing_date").groupby(["symbol", "fy"], as_index=False).first()
    path = os.path.join(CACHE, "annual_roe.csv")
    d.to_csv(path, index=False)
    print("\nusable annual ROE rows: %d  symbols: %d" % (len(d), d.symbol.nunique()))
    print("fiscal years: %s" % sorted(d.fy.unique()))
    print("obs per symbol: median=%d" % d.groupby("symbol").size().median())
    print("ctx_inferred: %.1f%%" % (100 * d.ctx_inferred.mean()))
    print("\nfailures:", fails)
    print("written:", path)


if __name__ == "__main__":
    main()
