"""DRIFT API. Read-only except POST /scan/run. No broker, no orders, no credentials."""
from __future__ import annotations

import functools
import threading
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from . import demo, settings
from .book import forward_nav, latest_state, occupied_slots
from .calendar import build_calendar
from .frozen import FROZEN, frozen_config_text, verify_frozen_config
from .prices import PriceStore
from .scanner import forward_ledger, load_history, load_state, now_ist, run_scan, scan_ledger, universe


# ------------------------------------------------------------------ cached read-only inputs
@functools.lru_cache(maxsize=1)
def _history():
    return load_history()


@functools.lru_cache(maxsize=1)
def _universe():
    return universe(_history())


@functools.lru_cache(maxsize=1)
def _research_last():
    ev = pd.read_csv(settings.CORRECTED_EVENTS, usecols=["symbol", "filing_ts", "sue", "q_exante_4q", "event_day"],
                     parse_dates=["filing_ts"])
    return ev.sort_values("filing_ts").groupby("symbol").last()


_CAL = {"cal": None, "meta": None, "at": 0.0}


def calendar():
    if _CAL["cal"] is None or time.time() - _CAL["at"] > 6 * 3600:
        from .nse import NSEClient
        cal, meta = build_calendar(NSEClient().holidays)
        _CAL.update(cal=cal, meta=meta, at=time.time())
    return _CAL["cal"], _CAL["meta"]


def _clean(v):
    if isinstance(v, (np.floating, float)):
        return None if not np.isfinite(v) else float(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (pd.Timestamp, datetime, date)):
        return v.isoformat()
    return v


def records(df: pd.DataFrame) -> list[dict]:
    return [{k: _clean(v) for k, v in r.items()} for r in df.to_dict("records")]


def next_scan_time(now: datetime) -> datetime:
    t = now.replace(hour=settings.SCAN_HOUR_IST, minute=settings.SCAN_MINUTE_IST, second=0, microsecond=0)
    return t if now < t else t + timedelta(days=1)


def seasons_completed(today: date) -> dict:
    """An earnings season = the results window for one fiscal quarter-end after the freeze.
    It is complete once the SEBI filing deadline has passed (45 days; 60 for March quarters)."""
    qs, q = [], pd.Timestamp(FROZEN.freeze_date).to_period("Q")
    while True:
        qe = q.end_time.normalize().date()
        deadline = qe + timedelta(days=60 if qe.month == 3 else 45)
        if qe <= FROZEN.freeze_date:
            q += 1
            continue
        if qe > today:
            break
        qs.append({"quarter_end": qe.isoformat(), "deadline": deadline.isoformat(), "complete": today > deadline})
        q += 1
    return {"seasons": qs, "completed": sum(s["complete"] for s in qs), "required_min": 4, "required_max": 6}


# ------------------------------------------------------------------ scheduler
class DailyScheduler(threading.Thread):
    daemon = True

    def __init__(self):
        super().__init__(name="drift-scheduler")
        self.stop = threading.Event()

    def run(self):
        while not self.stop.wait(30):
            now = now_ist()
            st = load_state()
            due = (now.hour, now.minute) >= (settings.SCAN_HOUR_IST, settings.SCAN_MINUTE_IST)
            if due and st.get("last_scheduled") != now.date().isoformat():     # once per day, after 18:30 IST
                st["last_scheduled"] = now.date().isoformat()
                from .scanner import save_state
                save_state(st)
                run_scan()


_SCHED: DailyScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    global _SCHED
    if os.environ.get("DRIFT_SCHEDULER", "1") == "1":
        _SCHED = DailyScheduler()
        _SCHED.start()
    yield
    if _SCHED:
        _SCHED.stop.set()


app = FastAPI(title="DRIFT — StackFlow Forward Scanner", version=FROZEN.version, lifespan=lifespan,
              description="Forward-test candidate. Generates and logs signals only. No broker, no orders.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])

BADGE = "FORWARD-TEST CANDIDATE"


def _scan_rows() -> pd.DataFrame:
    return scan_ledger().rows()


def _fwd_state() -> pd.DataFrame:
    return latest_state(forward_ledger().rows())


# ------------------------------------------------------------------ endpoints
@app.get("/health")
def health():
    cal, meta = calendar()
    st = load_state()
    fwd_v, log_v = forward_ledger().verify(), scan_ledger().verify()
    last = st.get("last_scan") or {}
    audits = last.get("fetch_audits", [])
    return {
        "badge": BADGE,
        "frozen_config": verify_frozen_config(),
        "calendar": {k: meta.get(k) for k in ("validated", "source", "fetched_at", "n_holidays", "historical_end",
                                               "validation_year", "rule_minus_index", "index_minus_rule")},
        "append_only_guard": {"forward_record": fwd_v | {"path": str(settings.FORWARD_RECORD)},
                              "scan_log": log_v | {"path": str(settings.SCAN_LOG)}},
        "total_count_asserts": {"checked": len(audits), "passed": sum(1 for a in audits if a.get("asserted")),
                                "audits": audits},
        "last_scan": {k: last.get(k) for k in ("scan_id", "started", "ok", "duration_s", "errors", "filings_seen",
                                               "universe_filings", "new_events", "q5", "decisions", "fills")},
        "last_success": st.get("last_success"),
        "data_freshness": {"prices_last_session": st.get("price_freshness", {}),
                           "benchmark_panel_end": meta.get("historical_end"),
                           "holidays_fetched_at": meta.get("fetched_at")},
        "safety": "signals and logging only; no broker connection, no order placement, no credentials",
    }


@app.get("/status")
def status(demo_mode: bool = Query(False, alias="demo")):
    now = now_ist()
    if demo_mode:
        sig = demo.demo_signals(None, demo.DEMO_TODAY)
        pos = demo.demo_positions(sig, demo.DEMO_TODAY)
        last_day = max(s["scanned_at"][:10] for s in sig)
        today = [s for s in sig if s["scanned_at"][:10] == last_day]
        return {"badge": BADGE, **demo.STAMP, "now_ist": now.isoformat(timespec="seconds"),
                "next_scan_ist": next_scan_time(now).isoformat(timespec="minutes"),
                "last_scan": {"started": f"{last_day}T18:30:00", "ok": True, "duration_s": None},
                "filings_processed_today": len(today), "q5_today": sum(1 for s in today if s["quintile"] == 5),
                "slots_used": pos["slots_used"], "slots": FROZEN.slots, "forward_signals_total": len(sig)}
    st = load_state()
    rows = _scan_rows()
    today = rows[rows.scanned_at.str[:10] == now.date().isoformat()] if len(rows) else rows
    state = _fwd_state()
    used = occupied_slots(state, now.date()) if len(state) else 0
    return {"badge": BADGE, "demo": False, "now_ist": now.isoformat(timespec="seconds"),
            "next_scan_ist": next_scan_time(now).isoformat(timespec="minutes"),
            "last_scan": {k: (st.get("last_scan") or {}).get(k) for k in ("scan_id", "started", "ok", "duration_s", "errors")},
            "filings_processed_today": int(len(today)),
            "q5_today": int((today.quintile == "5").sum()) if len(today) else 0,
            "slots_used": int(used), "slots": FROZEN.slots, "forward_signals_total": int(len(rows)),
            "freeze_date": FROZEN.freeze_date.isoformat()}


@app.post("/scan/run")
def scan_run():
    rep = run_scan()
    _history.cache_clear(); _universe.cache_clear()
    return rep


def _signals(demo_mode: bool) -> list[dict]:
    if demo_mode:
        return demo.demo_signals(None, demo.DEMO_TODAY)
    rows = _scan_rows()
    return [{**r, "demo": False} for r in records(rows)]


@app.get("/signals/today")
def signals_today(demo_mode: bool = Query(False, alias="demo")):
    sig = _signals(demo_mode)
    ref = max((s["scanned_at"][:10] for s in sig), default="") if demo_mode else now_ist().date().isoformat()
    return {"date": ref, "signals": [s for s in sig if str(s.get("scanned_at", ""))[:10] == ref], "demo": demo_mode}


@app.get("/signals/history")
def signals_history(demo_mode: bool = Query(False, alias="demo")):
    return {"signals": _signals(demo_mode), "demo": demo_mode}


@app.get("/positions/open")
def positions(demo_mode: bool = Query(False, alias="demo")):
    today = now_ist().date()
    if demo_mode:
        return demo.demo_positions(demo.demo_signals(None, demo.DEMO_TODAY), demo.DEMO_TODAY)
    state = _fwd_state()
    if state.empty:
        return {"open": [], "planned": [], "closed": [], "slots_used": 0, "slots": FROZEN.slots, "demo": False}
    cal, _ = calendar()
    store = PriceStore(cal)
    bench = store.benchmark(FROZEN.freeze_date)
    ind = _universe().set_index("symbol").industry
    open_, planned, closed = [], [], []
    for r in state.itertuples():
        base = dict(signal_id=r.signal_id, symbol=r.symbol, industry=ind.get(r.symbol, ""), sue=float(r.sue_value),
                    entry_date=r.entry_date, exit_date=r.exit_date, holding_sessions=FROZEN.holding_sessions)
        if r.status == "ENTER":
            planned.append(base)
        elif r.status == "OPEN":
            px = store.history(r.symbol, FROZEN.freeze_date - timedelta(days=120))
            e = pd.Timestamp(r.entry_date)
            p0, p1 = float(r.entry_price), float(px.Close.iloc[-1]) if len(px) else float(r.entry_price)
            held = len(cal.sessions_between(e.date(), min(today, px.index.max().date() if len(px) else today)))
            bret = float(bench.iloc[-1] / bench.asof(e) - 1) if len(bench) else 0.0
            open_.append(base | dict(entry_price=p0, current_price=p1, sessions_held=held,
                                     unrealised_return=p1 / p0 - 1 - FROZEN.half_cost,
                                     excess_vs_nifty500=p1 / p0 - 1 - bret, price_date=str(px.index.max().date()) if len(px) else None))
        elif r.status == "CLOSED":
            closed.append(base | dict(entry_price=float(r.entry_price), exit_price=float(r.exit_price),
                                      net_return=float(r.net_return), excess_vs_nifty500=float(r.nifty500_excess_return)))
    return {"open": open_, "planned": planned, "closed": closed,
            "slots_used": occupied_slots(state, today), "slots": FROZEN.slots, "demo": False}


@app.get("/forward/performance")
def performance(demo_mode: bool = Query(False, alias="demo")):
    today = now_ist().date()
    ref = pd.read_csv(settings.PERIOD_METRICS, index_col=0)
    keep = ["cagr", "bench_cagr", "excess_cagr", "sharpe_rf0", "bench_sharpe_rf0", "max_dd", "trades", "win_rate"]
    research = {"label": "Research reference (not forward evidence)", "source": str(settings.PERIOD_METRICS.name),
                "periods": {p: {k: _clean(pd.to_numeric(ref.loc[k, p], errors="coerce")) for k in keep}
                            for p in ["Full Period", "Discovery", "Holdout"]}}
    kill = ["Cumulative strategy return trails NIFTY 500 over 4 consecutive earnings seasons (excess <= 0%)",
            "Average Q5 net trade return trails the event-universe average (excess vs event universe <= 0%)",
            "Realised portfolio drawdown exceeds -25.0%"]
    if demo_mode:
        return demo.demo_performance(demo.DEMO_TODAY) | {"research_reference": research, "kill_criteria": kill,
                                                         "seasons": seasons_completed(demo.DEMO_TODAY),
                                                         "starts": (FROZEN.freeze_date + timedelta(days=1)).isoformat()}
    cal, _ = calendar()
    state = _fwd_state()
    start = cal.next_session(FROZEN.freeze_date)
    sessions = cal.sessions_between(FROZEN.freeze_date, today) if today >= start else []
    store = PriceStore(cal)
    bench = store.benchmark(FROZEN.freeze_date)
    sessions = [d for d in sessions if pd.Timestamp(d) <= bench.index.max()]
    filled = state[state.status.isin({"OPEN", "CLOSED"})] if len(state) else state
    pxs = {s: store.history(s, FROZEN.freeze_date - timedelta(days=120)) for s in set(filled.symbol)} if len(filled) else {}
    nav = forward_nav(state, pxs, bench, sessions)
    series = [dict(date=str(d), nav=_clean(r.nav), bench=_clean(r.bench), positions=int(r.positions),
                   drawdown=_clean(r.drawdown)) for d, r in nav.iterrows()]
    return {"demo": False, "starts": start.isoformat(), "series": series, "trades_filled": int(len(filled)),
            "seasons": seasons_completed(today), "kill_criteria": kill, "research_reference": research,
            "note": "Forward record only. No backtest history is mixed into this curve."}


@app.get("/universe/map")
def universe_map(demo_mode: bool = Query(False, alias="demo")):
    u = _universe().copy()
    last = _research_last()
    rows = []
    fwd = {}
    for s in _signals(demo_mode):
        fwd[s["symbol"]] = s
    state = pd.DataFrame() if demo_mode else _fwd_state()
    live = {}
    if demo_mode:
        for p in demo.demo_positions(list(fwd.values()), demo.DEMO_TODAY)["open"]:
            live[p["symbol"]] = p
    elif len(state):
        for r in state[state.status.isin({"OPEN", "ENTER"})].itertuples():
            live[r.symbol] = {"entry_date": r.entry_date, "exit_date": r.exit_date, "status": r.status}
    for r in u.itertuples():
        f = fwd.get(r.symbol)
        rl = last.loc[r.symbol] if r.symbol in last.index else None
        rows.append({
            "symbol": r.symbol, "sector": str(r.industry).title() if isinstance(r.industry, str) else "Unclassified",
            "is_fin": bool(r.is_fin),
            "forward": f,
            "research_last": None if rl is None else {"filing_ts": _clean(rl.filing_ts), "sue": _clean(rl.sue),
                                                      "quintile": _clean(rl.q_exante_4q), "source": "research (pre-freeze)"},
            "position": live.get(r.symbol),
        })
    return {"symbols": rows, "n": len(rows), "demo": demo_mode}


@functools.lru_cache(maxsize=1)
def _backtest():
    C = settings.PEAD_V2 / "corrected"
    pm = pd.read_csv(C / "period_metrics_corrected.csv", index_col=0)
    periods = {}
    for p in ["Full Period", "Discovery", "Holdout"]:
        periods[p] = {k: (_clean(pd.to_numeric(v, errors="coerce")) if k not in ("start", "end") else v)
                      for k, v in pm[p].items()}
    for p, col in [("Holdout (calendar split)", "Holdout (calendar split of full book)")]:
        periods[p] = {k: (_clean(pd.to_numeric(v, errors="coerce")) if k not in ("start", "end") else v)
                      for k, v in pm[col].items() if pd.notna(v)}
    nav = pd.read_csv(C / "nav_daily_corrected.csv")
    yr = pd.read_csv(C / "yearly_returns_corrected.csv").rename(columns={"Unnamed: 0": "year"})
    sig = pd.read_csv(C / "signal_cells.csv")
    pl = pd.read_csv(C / "placebo_random_books.csv")
    return {
        "label": "Backtest — research data already seen; not forward evidence",
        "source": "research/pead_v2/corrected/ (CORRECTED_REPORT.md revision 2)",
        "periods": periods,
        "nav": records(nav[["date", "strategy_nav", "nifty500", "strategy_dd", "positions_held", "period"]]),
        "yearly": records(yr),
        "cost": records(pd.read_csv(C / "cost_sensitivity_corrected.csv")),
        "kill_tests": records(pd.read_csv(C / "kill_tests_corrected.csv")),
        "signal": records(sig[["label", "n_q5", "n_q1", "spread_pct", "p_val", "folds_pos", "folds_total"]]),
        "folds": records(pd.read_csv(C / "signal_folds_60d.csv")[["qtr", "spread", "period"]]),
        "placebo": {"n": int(len(pl)), "full_excess_mean": float(pl.excess_cagr.mean()), "full_excess_sd": float(pl.excess_cagr.std()),
                    "holdout_excess_mean": float(pl.holdout_excess_cagr.mean()), "holdout_excess_sd": float(pl.holdout_excess_cagr.std())},
    }


@app.get("/research/tearsheet.xlsx")
def tearsheet():
    from fastapi.responses import FileResponse
    f = settings.PEAD_V2 / "PEAD_V2_Tearsheet.xlsx"
    return FileResponse(f, filename="PEAD_V2_Tearsheet.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/research/backtest")
def backtest():
    return _backtest()


@app.get("/config")
def config():
    v = verify_frozen_config()
    prereg = settings.PREREG_PATH.read_text(encoding="utf-8")
    sec5 = prereg[prereg.find("## 5. Forward-test protocol"):] if "## 5. Forward-test protocol" in prereg else ""
    return {"read_only": True, "frozen_config_markdown": frozen_config_text(), "verification": v,
            "pre_registration_markdown": sec5, "constants": v.get("constants")}
