"""Daily forward scan: NSE filings -> parse -> SUE -> ex-ante quintile -> timing -> filters ->
frozen portfolio decision -> append-only forward record; then fill realised outcomes.

Generates and logs signals only. Nothing here can place an order.
"""
from __future__ import annotations

import json
import threading
import time
import traceback
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import settings
from .book import allocate, latest_state
from .calendar import TradingCalendar, build_calendar, entry_decision_deadline, event_and_entry
from .frozen import FROZEN, verify_frozen_config
from .ledger import FORWARD_COLUMNS, SCAN_COLUMNS, AppendOnlyLedger
from .nse import NSEClient
from .prices import PriceStore, UnitError, turnover20
from .signal import exante_thresholds, load_research_pool, quintile, sue_for_new_quarter
from . import xbrl

_LOCK = threading.Lock()


def now_ist() -> datetime:
    return datetime.now(settings.IST).replace(tzinfo=None)


def forward_ledger() -> AppendOnlyLedger:
    return AppendOnlyLedger(settings.FORWARD_RECORD, FORWARD_COLUMNS,
                            settings.DATA_DIR / "forward_record.chain.json", FROZEN.freeze_date)


def scan_ledger() -> AppendOnlyLedger:
    return AppendOnlyLedger(settings.SCAN_LOG, SCAN_COLUMNS, settings.DATA_DIR / "forward_scan_log.chain.json",
                            FROZEN.freeze_date, key=("signal_id", "decision", "reason"))


def load_state() -> dict:
    if settings.STATE_FILE.exists():
        return json.loads(settings.STATE_FILE.read_text())
    return {}


def save_state(st: dict) -> None:
    tmp = settings.STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1, default=str))
    tmp.replace(settings.STATE_FILE)


# ---------------------------------------------------------------------------- universe / history
def load_history() -> pd.DataFrame:
    e = pd.read_csv(settings.XBRL_EXTRACT, usecols=["symbol", "period", "basis", "taxonomy", "period_end",
                                                    "filing_date", "pat", "industry", "fin"])
    e = e[(e.period == "Quarterly") & e.pat.notna()].copy()
    e["period_end"] = pd.to_datetime(e.period_end, errors="coerce")
    e["source"] = "research"
    if settings.FORWARD_PAT.exists():
        f = pd.read_csv(settings.FORWARD_PAT, parse_dates=["period_end"])
        f["source"] = "forward"
        e = pd.concat([e, f], ignore_index=True)
    return e.dropna(subset=["period_end"])


def universe(history: pd.DataFrame) -> pd.DataFrame:
    u = (history.sort_values("period_end").groupby("symbol")
         .agg(industry=("industry", "last"), fin=("fin", "last"), taxonomy=("taxonomy", "last")).reset_index())
    u["is_fin"] = u.fin.astype(bool) | u.taxonomy.astype(str).str.contains("BANKING|NBFC", regex=True)
    return u


def is_financial(industry: str, taxonomy: str) -> bool:
    """Corrected Non-Financials definition (XBRL D8.1 union rule, used by the corrected research):
    financial if industry == FINANCIAL SERVICES OR taxonomy is BANKING / NBFC."""
    return str(industry).upper() == "FINANCIAL SERVICES" or any(t in str(taxonomy) for t in ("BANKING", "NBFC"))


# ---------------------------------------------------------------------------- filing groups
def _ts(s):
    if not s:
        return None
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M"):
        try:
            return datetime.strptime(str(s).strip().title() if fmt else s, fmt)
        except ValueError:
            continue
    return None


def filing_groups(rows_int: list[dict], rows_leg: list[dict], scan_time: datetime) -> list[dict]:
    """Normalise both systems into (symbol, period_end) groups of candidate files."""
    files = []
    for x in rows_int:
        if x.get("type") != "Integrated Filing- Financials":
            continue
        url = x.get("xbrl") or ""
        if not url.endswith(".xml"):
            continue
        pe = pd.to_datetime(x.get("qe_Date"), format="%d-%b-%Y", errors="coerce")
        bts, cts = _ts(x.get("broadcast_Date")), _ts(x.get("creation_Date"))
        rts = _ts(x.get("revised_Date"))
        sub = x.get("type_Sub") or ""
        if bts is not None:
            ts, src = bts, "broadcast"
        elif cts is not None and scan_time - cts > timedelta(days=1):
            # never disseminated a day later: use creation time, forced after-hours (conservative)
            ts, src = cts.replace(hour=23, minute=59, second=0), "creation_forced_after_hours"
        else:
            ts, src = None, "pending_broadcast"
        if sub == "Revision" and rts is not None:     # D12: a revision is dated at its own revision time
            ts = max(ts, rts) if ts else None
        files.append(dict(symbol=x.get("symbol"), company=x.get("cmName") or x.get("smName"), period_end=pe,
                          basis=x.get("consolidated"), ts=ts, ts_source=src, type_sub=sub, xbrl=url,
                          taxonomy=xbrl.taxonomy_of(url), system="integrated"))
    for x in rows_leg:
        url = x.get("xbrl") or ""
        if not url.endswith(".xml") or x.get("period") != "Quarterly":
            continue
        pe = pd.to_datetime(x.get("toDate"), format="%d-%b-%Y", errors="coerce")
        ts = _ts(x.get("broadCastDate")) or _ts(x.get("filingDate"))
        files.append(dict(symbol=x.get("symbol"), company=x.get("companyName"), period_end=pe,
                          basis=x.get("consolidated"), ts=ts, ts_source="broadcast" if ts else "pending_broadcast",
                          type_sub="Original", xbrl=url, taxonomy=xbrl.taxonomy_of(url), system="legacy"))
    groups: dict[tuple, list] = {}
    for f in files:
        if f["symbol"] and pd.notna(f["period_end"]):
            groups.setdefault((f["symbol"], f["period_end"]), []).append(f)
    out = []
    for (sym, pe), fs in groups.items():
        out.append(dict(symbol=sym, period_end=pe, files=fs, company=fs[0]["company"]))
    return out


def choose_file(fs: list[dict]) -> tuple[dict | None, dict | None, str | None]:
    """D1 Consolidated-first among files already disseminated; D12 earliest PARSEABLE file,
    dated at that file's own timestamp. Returns (file, parsed_record, failure)."""
    known = [f for f in fs if f["ts"] is not None]
    if not known:
        return None, None, "PENDING_BROADCAST"
    cons = [f for f in known if str(f["basis"]).startswith("Consolidated")]
    pool = sorted(cons or known, key=lambda f: f["ts"])
    last_err = None
    for f in pool:
        rec, err = xbrl.parse_quarterly(f["xbrl"], f["period_end"])
        if err is None:
            return f, rec, None
        last_err = err
    return None, None, f"PARSE_FAILED:{last_err}"


# ---------------------------------------------------------------------------- the scan
def run_scan(client: NSEClient | None = None, prices: PriceStore | None = None,
             cal: TradingCalendar | None = None, scan_time: datetime | None = None,
             lookback_days: int = 4) -> dict:
    if not _LOCK.acquire(blocking=False):
        return {"ok": False, "error": "a scan is already running"}
    t0 = time.time()
    st = load_state()
    scan_time = scan_time or now_ist()
    scan_id = scan_time.strftime("S%Y%m%d%H%M%S")
    report = {"scan_id": scan_id, "started": scan_time.isoformat(timespec="seconds"), "ok": False,
              "fetch_audits": [], "filings_seen": 0, "new_events": 0, "q5": 0, "decisions": {},
              "fills": {}, "errors": []}
    try:
        fz = verify_frozen_config()
        if not fz["ok"]:
            raise RuntimeError(f"frozen config mismatch, refusing to scan: {fz['missing_phrases']}")
        client = client or NSEClient()
        if cal is None:
            cal, cal_meta = build_calendar(client.holidays)
            st["calendar"] = cal_meta
        prices = prices or PriceStore(cal)
        fwd, log = forward_ledger(), scan_ledger()

        # 1. discovery (both systems, completeness asserted)
        a = max(FROZEN.freeze_date + timedelta(days=1),
                (pd.Timestamp(st.get("last_scan_date", scan_time.date())) - pd.Timedelta(days=lookback_days)).date())
        b = scan_time.date()
        rows_int, rows_leg = [], []
        cur = a
        while cur <= b:
            end = min(b, (pd.Timestamp(cur) + pd.offsets.MonthEnd(0)).date())
            r, aud = client.integrated(cur, end); rows_int += r; report["fetch_audits"].append(aud.__dict__)
            r, aud = client.legacy(cur, end); rows_leg += r; report["fetch_audits"].append(aud.__dict__)
            cur = end + timedelta(days=1)
        report["filings_seen"] = len(rows_int) + len(rows_leg)

        # 2. new (symbol, quarter) events inside the research universe
        hist = load_history()
        uni = universe(hist)
        uni_syms = set(uni.symbol)
        logged = set(log.rows().signal_id) if len(log.rows()) else set()
        groups = [g for g in filing_groups(rows_int, rows_leg, scan_time) if g["symbol"] in uni_syms]
        report["universe_filings"] = len(groups)

        pool = load_research_pool()
        pool_ts = pool.filing_ts.values.astype("datetime64[ns]")
        pool_sue = pool.sue.values.astype(float)
        fl = log.rows()
        if len(fl):          # forward qualifying events join the pool
            q = fl[(fl.sue != "") & (fl.turnover20_inr != "") & (fl.reason != "INSUFFICIENT_HISTORY")]
            q = q.drop_duplicates("signal_id")
            q = q[q.turnover20_inr.astype(float) >= FROZEN.min_turnover_inr]
            pool_ts = np.concatenate([pool_ts, pd.to_datetime(q.filing_timestamp).values.astype("datetime64[ns]")])
            pool_sue = np.concatenate([pool_sue, q.sue.astype(float).values])

        new_rows, pat_rows = [], []
        price_start = FROZEN.freeze_date - timedelta(days=120)
        for g in sorted(groups, key=lambda g: min([f["ts"] for f in g["files"] if f["ts"]] or [datetime.max])):
            sid = f"{g['symbol']}_{g['period_end']:%Y%m%d}"
            prior = hist[(hist.symbol == g["symbol"])]
            if (prior.period_end == g["period_end"]).any() or sid in logged:
                continue                                  # not a new event (already known)
            f, rec, fail = choose_file(g["files"])
            base = dict(scan_id=scan_id, scanned_at=scan_time.isoformat(timespec="seconds"), signal_id=sid,
                        symbol=g["symbol"], company=g["company"], period_end=f"{g['period_end']:%Y-%m-%d}")
            if f is None:
                report["decisions"][fail.split(":")[0]] = report["decisions"].get(fail.split(":")[0], 0) + 1
                continue                                  # retried next scan; nothing appended yet
            if f["ts"].date() <= FROZEN.freeze_date:
                continue                                  # pre-freeze: backtest data, never recorded
            ind = uni.set_index("symbol").industry.get(g["symbol"], "")
            fin = is_financial(ind, f["taxonomy"])
            ev_day, entry = event_and_entry(f["ts"], cal)
            exit_ = cal.add_sessions(entry, FROZEN.holding_sessions)
            sue, pat_ly, n_prior = sue_for_new_quarter(prior[["period_end", "pat"]], g["period_end"], rec["pat"])
            th = exante_thresholds(pool_ts, pool_sue, f["ts"])
            qn = quintile(sue, th)
            px = prices.history(g["symbol"], price_start)
            try:
                t20 = turnover20(px, ev_day, FROZEN.turnover_window_sessions, FROZEN.turnover_min_sessions)
            except UnitError as exc:
                report["errors"].append(str(exc)); t20 = None
            last_close = float(px["Close"].iloc[-1]) if len(px) else None
            prev_basis = prior.sort_values("period_end").basis.iloc[-1] if len(prior) else None
            basis_switch = prev_basis is not None and str(prev_basis)[:4] != str(f["basis"])[:4]

            if not np.isfinite(sue):
                decision, reason = "REJECTED", "INSUFFICIENT_HISTORY"
            elif qn is None:
                decision, reason = "REJECTED", "THRESHOLDS_UNAVAILABLE"
            elif qn != FROZEN.signal_quintile:
                decision, reason = "NO_SIGNAL", f"Q{qn}"
            elif fin:
                decision, reason = "REJECTED", "FINANCIAL_SECTOR"
            elif basis_switch:
                decision, reason = "REJECTED", "BASIS_SWITCH"
            elif t20 is None or t20 < FROZEN.min_turnover_inr:
                decision, reason = "REJECTED", "LIQUIDITY_FILTER"
            else:
                decision, reason = "CANDIDATE", ""
            row = base | dict(industry=ind, is_fin=fin, taxonomy=f["taxonomy"], basis=f["basis"],
                              filing_timestamp=f["ts"].isoformat(sep=" "), ts_source=f["ts_source"],
                              event_day=ev_day.isoformat(), planned_entry=entry.isoformat(), planned_exit=exit_.isoformat(),
                              pat=rec["pat"], pat_prior_year=pat_ly, sue=sue if np.isfinite(sue) else "",
                              n_prior_yoy=n_prior, hist_events=th.n, q20=th.q20, q40=th.q40, q60=th.q60, q80=th.q80,
                              quintile=qn or "", turnover20_inr=t20 if t20 else "", last_close_inr=last_close or "",
                              decision=decision, reason=reason, xbrl=f["xbrl"])
            new_rows.append(row)
            if t20 is not None and t20 >= FROZEN.min_turnover_inr and np.isfinite(sue):
                pool_ts = np.append(pool_ts, np.datetime64(f["ts"], "ns"))   # visible only to LATER filings
                pool_sue = np.append(pool_sue, sue)
            pat_rows.append(dict(symbol=g["symbol"], period="Quarterly", basis=f["basis"], taxonomy=f["taxonomy"],
                                 period_end=f"{g['period_end']:%Y-%m-%d}", filing_date=f"{f['ts']:%Y-%m-%d}",
                                 pat=rec["pat"], industry=ind, fin=fin))
        report["new_events"] = len(new_rows)

        # 3. frozen portfolio decisions for Q5 candidates (per planned entry date)
        state = latest_state(fwd.rows())
        queued = state[state.status == "QUEUED"] if len(state) else state
        fwd_rows = []
        pending: dict[date, list] = {}
        for r in new_rows:
            if r["decision"] == "CANDIDATE":
                pending.setdefault(date.fromisoformat(r["planned_entry"]), []).append(r)
        for q in queued.itertuples() if len(queued) else []:
            pending.setdefault(pd.Timestamp(q.entry_date).date(), []).append(
                {"signal_id": q.signal_id, "sue": float(q.sue_value), "_queued": q})
        final_rows = {}
        for entry, cands in pending.items():
            deadline = entry_decision_deadline(entry, cal)
            entry_open = datetime.combine(entry, datetime.min.time()).replace(hour=9, minute=15)
            if scan_time >= entry_open:
                for c in cands:
                    final_rows[c["signal_id"]] = ("REJECTED", "ENTRY_MISSED")
            elif scan_time < deadline:
                for c in cands:
                    final_rows[c["signal_id"]] = ("QUEUED", "AWAITING_SAME_DAY_PEERS")
            else:
                for al in allocate(entry, [(c["signal_id"], float(c["sue"])) for c in cands], state):
                    final_rows[al.signal_id] = (al.decision, al.reason)
        for r in new_rows:
            if r["decision"] == "CANDIDATE":
                r["decision"], r["reason"] = final_rows[r["signal_id"]]
            report["decisions"][r["decision"]] = report["decisions"].get(r["decision"], 0) + 1
        log.append(new_rows)
        if pat_rows:        # only after the scan log accepted the events (else they would look "known")
            pd.DataFrame(pat_rows).to_csv(settings.FORWARD_PAT, mode="a", index=False,
                                          header=not settings.FORWARD_PAT.exists())

        def fwd_row(sid, symbol, period_end, fts, ev, sue, q80, status, reason, entry, exit_, **kw):
            base = dict(signal_id=sid, symbol=symbol, period_end=period_end, filing_timestamp=fts, event_day=ev,
                        sue_value=sue, rolling_q80_threshold=q80,
                        is_taken={"ENTER": "True", "OPEN": "True", "CLOSED": "True", "QUEUED": "pending"}.get(status, "False"),
                        skip_reason=reason, entry_date=entry, exit_date=exit_, holding_sessions="", status=status)
            base.update(kw)
            return base

        for r in new_rows:                       # every Q5 filing (incl. financial / illiquid skips)
            if r["quintile"] == FROZEN.signal_quintile:
                report["q5"] += 1
                fwd_rows.append(fwd_row(r["signal_id"], r["symbol"], r["period_end"], r["filing_timestamp"],
                                        r["event_day"], r["sue"], r["q80"], r["decision"], r["reason"],
                                        r["planned_entry"], r["planned_exit"]))
        for q in queued.itertuples() if len(queued) else []:
            dec, why = final_rows.get(q.signal_id, ("QUEUED", ""))
            if dec != "QUEUED":
                fwd_rows.append(fwd_row(q.signal_id, q.symbol, q.period_end, q.filing_timestamp, q.event_day,
                                        q.sue_value, q.rolling_q80_threshold, dec, why, q.entry_date, q.exit_date))
        fwd.append(fwd_rows)

        # 4. realised outcomes — only when the prices actually exist
        report["fills"] = fill_outcomes(fwd, prices, cal, scan_time)
        report["ok"] = True
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        report["traceback"] = traceback.format_exc(limit=6)
    finally:
        report["duration_s"] = round(time.time() - t0, 2)
        st["last_scan"] = report
        if report["ok"]:
            st["last_scan_date"] = scan_time.date().isoformat()
            st["last_success"] = scan_time.isoformat(timespec="seconds")
        st["price_freshness"] = (prices.freshness if prices else {})
        save_state(st)
        _LOCK.release()
    return report


def fill_outcomes(fwd: AppendOnlyLedger, prices: PriceStore, cal: TradingCalendar, scan_time: datetime) -> dict:
    state = latest_state(fwd.rows())
    out = {"opened": 0, "closed": 0, "price_rejects": 0, "waiting": 0}
    if state.empty:
        return out
    rows = []
    bench = prices.benchmark(FROZEN.freeze_date)
    start = FROZEN.freeze_date - timedelta(days=120)
    for r in state.itertuples():
        if r.status not in ("ENTER", "OPEN"):
            continue
        px = prices.history(r.symbol, start)
        e, x = pd.Timestamp(r.entry_date), pd.Timestamp(r.exit_date)
        common = {c: getattr(r, c) for c in FORWARD_COLUMNS if c not in ("status",)}
        if r.status == "ENTER":
            if e not in px.index:
                out["waiting"] += 1
                continue
            p0 = float(px.loc[e, "Open"])
            if not p0 > FROZEN.min_price_inr:
                rows.append(common | dict(status="REJECTED", is_taken="False", skip_reason="PRICE_FILTER", entry_price=p0))
                out["price_rejects"] += 1
                continue
            rows.append(common | dict(status="OPEN", entry_price=p0))
            out["opened"] += 1
            r_entry = p0
        else:
            r_entry = float(r.entry_price)
        if x in px.index and x in bench.index:
            p1 = float(px.loc[x, "Close"])
            gross = p1 / r_entry - 1
            bret = float(bench.loc[x] / bench.asof(e) - 1)
            rows.append(common | dict(status="CLOSED", entry_price=r_entry, exit_price=p1,
                                      holding_sessions=len(cal.sessions_between(e.date(), x.date())),
                                      gross_return=gross, net_return=gross - FROZEN.round_trip_cost,
                                      cost_deducted=FROZEN.round_trip_cost, nifty500_excess_return=gross - bret))
            out["closed"] += 1
    fwd.append(rows)
    return out
