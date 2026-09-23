"""totalCount assert (the silent-cap bug), frozen slot allocation, frozen-config verification."""
from datetime import date

import pandas as pd
import pytest

from drift.book import allocate, occupied_slots
from drift.frozen import verify_frozen_config
from drift.nse import PAGE_SIZE, IncompleteFetchError, NSEClient, assert_complete

A, B = date(2026, 10, 1), date(2026, 10, 31)


def fake(pages, total):
    calls = []

    def getter(url, params):
        calls.append(params)
        assert params["size"] == PAGE_SIZE           # &size=2000 always requested
        i = params["page"] - 1
        return {"data": pages[i] if i < len(pages) else [], "totalCount": total}
    return getter, calls


def test_silent_cap_raises():
    # NSE returns 20 rows but says there are 84 — the historical silent-cap bug
    g, _ = fake([[{"symbol": f"S{i}"} for i in range(20)]], 84)
    with pytest.raises(IncompleteFetchError, match="20 rows < totalCount 84"):
        NSEClient(getter=g, pause=0).integrated(A, B)


def test_pages_until_complete():
    p1 = [{"symbol": f"S{i}"} for i in range(PAGE_SIZE)]
    p2 = [{"symbol": f"T{i}"} for i in range(345)]
    g, calls = fake([p1, p2], PAGE_SIZE + 345)
    rows, audit = NSEClient(getter=g, pause=0).integrated(A, B)
    assert len(rows) == PAGE_SIZE + 345 and audit.pages == 2 and audit.asserted
    assert [c["page"] for c in calls] == [1, 2]


def test_missing_total_count_raises():
    with pytest.raises(IncompleteFetchError):
        NSEClient(getter=lambda u, p: {"data": []}, pause=0).integrated(A, B)


def test_assert_complete_direct():
    assert_complete(84, 84, "x")
    assert_complete(85, 84, "x")
    with pytest.raises(IncompleteFetchError):
        assert_complete(83, 84, "x")


def test_legacy_round_number_treated_as_cap():
    with pytest.raises(IncompleteFetchError):
        NSEClient(getter=lambda u, p: [{}] * 20, pause=0).legacy(A, B)
    rows, audit = NSEClient(getter=lambda u, p: [{}] * 7, pause=0).legacy(A, B)
    assert len(rows) == 7 and audit.asserted


def _state(rows):
    return pd.DataFrame(rows, columns=["signal_id", "status", "entry_date", "exit_date"])


def test_strict_slot_release():
    # a position exiting at the close of 2026-12-01 still occupies its slot at that day's open
    st = _state([["X", "OPEN", "2026-09-01", "2026-12-01"]])
    assert occupied_slots(st, date(2026, 12, 1)) == 1
    assert occupied_slots(st, date(2026, 12, 2)) == 0


def test_allocation_ranks_same_day_by_sue_and_respects_capacity():
    st = _state([[f"P{i}", "OPEN", "2026-10-01", "2026-12-30"] for i in range(28)])
    al = allocate(date(2026, 11, 3), [("a", 1.6), ("b", 3.2), ("c", 2.4)], st)
    got = {x.signal_id: (x.decision, x.reason) for x in al}
    assert got == {"b": ("ENTER", ""), "c": ("ENTER", ""), "a": ("REJECTED", "LOWER_SUE_RANK")}


def test_full_book_rejects_with_full_queue():
    st = _state([[f"P{i}", "ENTER", "2026-10-01", "2026-12-30"] for i in range(30)])
    al = allocate(date(2026, 11, 3), [("a", 9.0)], st)
    assert (al[0].decision, al[0].reason) == ("REJECTED", "FULL_QUEUE")


def test_rejected_and_closed_do_not_hold_slots():
    st = _state([["R", "REJECTED", "2026-10-01", "2026-12-30"], ["C", "CLOSED", "2026-10-01", "2026-12-30"]])
    assert occupied_slots(st, date(2026, 11, 3)) == 0


def test_constants_match_frozen_config_file():
    v = verify_frozen_config()
    assert v["ok"], v["missing_phrases"]
