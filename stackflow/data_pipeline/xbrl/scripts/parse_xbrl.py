"""Step 2.2 - XBRL parser and extraction.

Applies every rule in LOCKED_DECISIONS.md:
  D1  Consolidated preferred, Non-Consolidated fallback (applied in select_filings)
  D3  ratio tags BANNED - everything derived from raw tags
  D8  financial-sector union exclusion applies to INTEREST COVERAGE only (applied downstream)
  D9  context matching is mandatory and FAILS LOUDLY - never "first match"

Outputs one row per (symbol, period, basis) with the raw inputs, never a ratio that
came from the filing itself.
"""
import os
import re
import time
import json
import warnings
from xml.etree import ElementTree as ET

warnings.filterwarnings("ignore")
import pandas as pd
import requests

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/data_pipeline/xbrl"
CACHE = os.path.join(ROOT, "cache")
XML = os.path.join(CACHE, "xml")
os.makedirs(XML, exist_ok=True)

# --- taxonomy tag maps -------------------------------------------------------
# INDAS and NBFC_INDAS verified identical for these fields (Part 1 / Step 2.0).
INDAS = dict(
    pbt=["ProfitBeforeTax", "ProfitBeforeExceptionalItemsAndTax"],
    interest=["FinanceCosts"],
    pat=["ProfitLossForPeriod"],
    share_capital=["PaidUpValueOfEquityShareCapital"],
    reserves=["ReserveExcludingRevaluationReserves"],
    revenue=["RevenueFromOperations"],
)
BANKING = dict(
    pbt=["ProfitLossFromOrdinaryActivitiesBeforeTax"],
    interest=["InterestExpended"],
    pat=["ProfitLossForThePeriod", "ProfitLossFromOrdinaryActivitiesAfterTax"],
    share_capital=["PaidUpValueOfEquityShareCapital"],
    reserves=["ReserveExcludingRevaluationReserves"],
    revenue=["Income", "InterestEarned"],
)
TAXMAP = {
    "INDAS": INDAS, "INTEGRATED_FILING_INDAS": INDAS,
    "NBFC_INDAS": INDAS, "INTEGRATED_FILING_NBFC_INDAS": INDAS,
    "NONINDAS": INDAS, "INTEGRATED_FILING_NONINDAS": INDAS,
    "BANKING": BANKING, "INTEGRATED_FILING_BANKING": BANKING,
}
# LI / GI (insurance) deliberately UNMAPPED - see BUILD_LOG Step 2.2.
UNMAPPED_KNOWN = {"INTEGRATED_FILING_LI", "INTEGRATED_FILING_GI"}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def sess():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": "https://www.nseindia.com/"})
    return s


def local(url):
    return os.path.join(XML, url.split("/")[-1])


def download(s, url, tries=2):
    fn = local(url)
    if os.path.exists(fn) and os.path.getsize(fn) > 2000:
        return fn
    for t in range(tries):
        try:
            r = s.get(url, timeout=20)
            if r.status_code == 200 and len(r.content) > 2000:
                open(fn, "wb").write(r.content)
                return fn
            if r.status_code == 404:
                return None          # permanent; retrying wastes ~6s per dead URL
        except Exception:
            pass
        time.sleep(2 + 2 * t)
    return None


def contexts(root):
    """ctx_id -> dict(kind='duration'|'instant', start, end)."""
    out = {}
    for c in root.iter():
        if not c.tag.endswith("}context"):
            continue
        cid = c.get("id")
        per = None
        for ch in c:
            if ch.tag.endswith("}period"):
                per = ch
        if per is None:
            continue
        st = en = inst = None
        for ch in per:
            t = ch.tag.split("}")[-1]
            if t == "startDate":
                st = (ch.text or "").strip()
            elif t == "endDate":
                en = (ch.text or "").strip()
            elif t == "instant":
                inst = (ch.text or "").strip()
        if inst:
            out[cid] = dict(kind="instant", start=inst, end=inst)
        elif st and en:
            out[cid] = dict(kind="duration", start=st, end=en)
    return out


def facts(root):
    """tag -> list of (ctx_id, float_value)."""
    out = {}
    for el in root.iter():
        t = el.tag.split("}")[-1]
        cid = el.get("contextRef")
        if not cid or el.text is None:
            continue
        v = el.text.strip().replace(",", "")
        if not re.fullmatch(r"-?\d+(\.\d+)?", v):
            continue
        out.setdefault(t, []).append((cid, float(v)))
    return out


def infer_contexts(ctxs, refs, from_date, to_date):
    """D11: ONLY for context ids referenced but never defined in the instance.

    NSE convention, applied precisely so an annual filing can never pick up a Q4 figure:
      OneD  = the QUARTER ending at to_date
      FourD = the FISCAL YEAR-TO-DATE period ending at to_date (FY starts 1 April)
    Inferring both to the same range would let OneD (Q4) satisfy an annual filing's
    target period - exactly the error D9 exists to prevent.
    """
    inferred = set()
    out = dict(ctxs)
    if not (from_date and to_date):
        return out, inferred
    try:
        end = pd.Timestamp(to_date)
    except Exception:
        return out, inferred
    qstart = (end - pd.offsets.QuarterBegin(startingMonth=1)).normalize()
    fy_year = end.year if end.month >= 4 else end.year - 1
    fystart = pd.Timestamp(fy_year, 4, 1)
    for cid in refs:
        if cid in out:
            continue
        if cid == "OneD":
            out[cid] = dict(kind="duration", start=qstart.strftime("%Y-%m-%d"),
                            end=to_date, inferred=True)
            inferred.add(cid)
        elif cid == "FourD":
            out[cid] = dict(kind="duration", start=fystart.strftime("%Y-%m-%d"),
                            end=to_date, inferred=True)
            inferred.add(cid)
    return out, inferred


def pick(fx, ctxs, names, want_start, want_end, kind):
    """Resolve a fact by matching its context period. Returns (value, reason, used_inferred).

    kind='duration' -> context start AND end must match the target period (D9).
    kind='as_at'    -> D10: context END must equal the target period end. An instant
                       context at that date is preferred; a duration context ending on
                       that date is accepted. Used for equity.
    """
    tried = False
    fallback = None
    for nm in names:
        if nm not in fx:
            continue
        tried = True
        for cid, val in fx[nm]:
            c = ctxs.get(cid)
            if not c:
                continue
            inf = bool(c.get("inferred"))
            if kind == "as_at":
                if c["end"] != want_end:
                    continue
                if c["kind"] == "instant":
                    return val, None, inf            # D10 preference
                if fallback is None:
                    fallback = (val, inf)
            else:
                if c["kind"] == "duration" and c["start"] == want_start and c["end"] == want_end:
                    return val, None, inf
    if fallback is not None:
        return fallback[0], None, fallback[1]
    return None, ("no_context_match" if tried else "missing_tag"), False


def parse_one(fn, taxonomy, from_date, to_date):
    """Returns (record, failure_reason)."""
    tm = TAXMAP.get(taxonomy)
    if tm is None:
        return None, ("unmapped_taxonomy_known" if taxonomy in UNMAPPED_KNOWN
                      else "unmapped_taxonomy_new:%s" % taxonomy)
    try:
        root = ET.parse(fn).getroot()
    except Exception as e:
        return None, "malformed_xml:%s" % type(e).__name__
    ctxs = contexts(root)
    fx = facts(root)
    if not fx:
        return None, "no_numeric_facts"

    refs = {cid for lst in fx.values() for cid, _ in lst}
    ctxs, inferred_ids = infer_contexts(ctxs, refs, from_date, to_date)
    if not ctxs:
        return None, "no_contexts"

    rec, reasons = {}, {}
    used_inf = False
    for field in ("pbt", "interest", "pat", "revenue"):
        v, why, inf = pick(fx, ctxs, tm[field], from_date, to_date, "duration")
        rec[field] = v
        used_inf = used_inf or inf
        if why:
            reasons[field] = why
    for field in ("share_capital", "reserves"):
        v, why, inf = pick(fx, ctxs, tm[field], from_date, to_date, "as_at")
        rec[field] = v
        used_inf = used_inf or inf
        if why:
            reasons[field] = why
    rec["ctx_inferred"] = used_inf

    rec["equity"] = (rec["share_capital"] + rec["reserves"]
                     if rec["share_capital"] is not None and rec["reserves"] is not None
                     else None)
    rec["reasons"] = json.dumps(reasons) if reasons else ""
    # a row is usable for IC if pbt+interest present; for ROE if pat+equity present
    rec["ok_ic"] = rec["pbt"] is not None and rec["interest"] is not None
    rec["ok_roe"] = rec["pat"] is not None and rec["equity"] is not None
    if not rec["ok_ic"] and not rec["ok_roe"]:
        main = reasons.get("pbt") or reasons.get("interest") or reasons.get("pat") or "unknown"
        return rec, main
    return rec, None


def iso(d):
    """'01-Oct-2023' -> '2023-10-01'; '31-MAR-2025' -> '2025-03-31'."""
    if not isinstance(d, str) or not d.strip():
        return None
    try:
        return pd.to_datetime(d.strip(), format="%d-%b-%Y").strftime("%Y-%m-%d")
    except Exception:
        try:
            return pd.to_datetime(d.strip()).strftime("%Y-%m-%d")
        except Exception:
            return None
