"""Frozen portfolio rules for the forward book.

* 30 slots. A position exiting at the CLOSE of day d still occupies its slot at the OPEN of d:
  a slot is free for entry date D only if the position's exit date is strictly before D.
* FIFO across entry dates; among candidates for the SAME entry date, highest SUE first.
  No cross-day displacement.
* Sizing at fill: min(available cash, NAV at previous close / 30); 0.2925% charged on the buy
  and 0.2925% on the sell. Cash earns 0%. No leverage.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from .frozen import FROZEN

LIVE_STATES = {"ENTER", "OPEN"}          # states that hold (or will hold) a slot


def latest_state(record: pd.DataFrame) -> pd.DataFrame:
    """Event-sourced record -> one row per signal_id (its most recent appended row)."""
    if record.empty:
        return record
    r = record.reset_index(drop=True).copy()
    r["_order"] = np.arange(len(r))
    return r.sort_values("_order").groupby("signal_id", as_index=False).last().drop(columns="_order")


def occupied_slots(state: pd.DataFrame, entry: date) -> int:
    """Slots held at the OPEN of `entry` by positions entered (or planned) before/at it."""
    if state.empty:
        return 0
    live = state[state.status.isin(LIVE_STATES)]
    n = 0
    for r in live.itertuples():
        e, x = pd.Timestamp(r.entry_date).date(), pd.Timestamp(r.exit_date).date()
        if e <= entry <= x:            # exit on `entry` day still occupies at its open
            n += 1
    return n


@dataclass
class Allocation:
    signal_id: str
    decision: str          # ENTER / REJECTED
    reason: str            # "" / FULL_QUEUE / LOWER_SUE_RANK


def allocate(entry: date, candidates: list[tuple[str, float]], state: pd.DataFrame,
             slots: int = FROZEN.slots) -> list[Allocation]:
    """Final allocation for one entry date. candidates: (signal_id, sue) not yet decided."""
    free = slots - occupied_slots(state, entry)
    out = []
    ranked = sorted(candidates, key=lambda c: (-c[1], c[0]))     # SUE desc, deterministic tie-break
    for i, (sid, _) in enumerate(ranked):
        if i < max(free, 0):
            out.append(Allocation(sid, "ENTER", ""))
        else:
            out.append(Allocation(sid, "REJECTED", "FULL_QUEUE" if free <= 0 else "LOWER_SUE_RANK"))
    return out


def forward_nav(state: pd.DataFrame, prices: dict[str, pd.DataFrame], bench: pd.Series,
                sessions: list[date]) -> pd.DataFrame:
    """Daily mark-to-market NAV of the forward book from the first post-freeze session.
    Only filled positions (status OPEN / CLOSED with an entry_price) participate."""
    cols = ["nav", "bench", "positions", "drawdown", "cash"]
    if not sessions:
        return pd.DataFrame(columns=cols)
    filled = state[state.status.isin({"OPEN", "CLOSED"}) & (state.entry_price.astype(str) != "")] if len(state) else state
    by_entry: dict[date, list] = {}
    for r in filled.itertuples():
        by_entry.setdefault(pd.Timestamp(r.entry_date).date(), []).append(r)
    hc = FROZEN.half_cost
    cash, nav_prev, pos, rows = 1.0, 1.0, [], []
    b0 = None
    for d in sessions:
        ts = pd.Timestamp(d)
        for r in sorted(by_entry.get(d, []), key=lambda x: -float(x.sue_value)):
            alloc = min(cash, nav_prev / FROZEN.slots)
            if alloc <= 0:
                continue
            p0 = float(r.entry_price)
            sh = alloc / (1 + hc) / p0
            cash -= sh * p0 * (1 + hc)
            pos.append(dict(sym=r.symbol, sh=sh, p0=p0,
                            exit=pd.Timestamp(r.exit_date).date() if r.status == "CLOSED" else None,
                            px_exit=float(r.exit_price) if r.status == "CLOSED" else None))
        val, keep = 0.0, []
        for p in pos:
            px = prices.get(p["sym"])
            last = px["Close"][px.index <= ts] if px is not None and len(px) else pd.Series(dtype=float)
            close = float(last.iloc[-1]) if len(last) else p["p0"]
            if p["exit"] == d:
                cash += p["sh"] * (p["px_exit"] or close) * (1 - hc)
            else:
                val += p["sh"] * close
                keep.append(p)
        pos = keep
        nav = cash + val
        bl = bench[bench.index <= ts]
        bv = float(bl.iloc[-1]) if len(bl) else np.nan
        b0 = bv if b0 is None else b0
        rows.append(dict(date=d, nav=nav, bench=bv / b0 if b0 else np.nan, positions=len(pos), cash=cash))
        nav_prev = nav
    df = pd.DataFrame(rows).set_index("date")
    df["drawdown"] = df.nav / df.nav.cummax() - 1
    return df[cols]
