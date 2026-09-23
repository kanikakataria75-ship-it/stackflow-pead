"""Append-only guard: past rows can't be edited, pre-freeze rows can't be written."""
from datetime import date

import pytest

from drift.ledger import (FORWARD_COLUMNS, AppendOnlyLedger, BackfillError, DuplicateError, SchemaError,
                          TamperError)

FREEZE = date(2026, 9, 22)


def row(sid="ABC_20260930", status="ENTER", ts="2026-10-20 16:10:00", **kw):
    r = {c: "" for c in FORWARD_COLUMNS}
    r.update(signal_id=sid, symbol="ABC", filing_timestamp=ts, status=status, sue_value="2.1")
    r.update(kw)
    return r


@pytest.fixture
def led(tmp_path):
    return AppendOnlyLedger(tmp_path / "fr.csv", FORWARD_COLUMNS, tmp_path / "fr.chain.json", FREEZE)


def test_append_grows_file_and_verifies(led):
    assert led.append([row()]) == 1
    size = led.path.stat().st_size
    led.append([row(status="OPEN", entry_price="101.5")])
    assert led.path.stat().st_size > size
    assert led.verify()["ok"] and len(led.rows()) == 2


def test_editing_a_past_row_is_detected_and_blocks_appends(led):
    led.append([row()])
    txt = led.path.read_text().replace("2.1", "9.9")          # silently "improve" a past SUE
    led.path.write_text(txt)
    assert not led.verify()["ok"]
    with pytest.raises(TamperError):
        led.append([row(status="OPEN")])


def test_deleting_a_past_row_is_detected(led):
    led.append([row(), row(sid="XYZ_20260930")])
    lines = led.path.read_text().splitlines(True)
    led.path.write_text("".join(lines[:-1]))
    with pytest.raises(TamperError):
        led.append([row(sid="NEW_20260930")])


def test_unchained_bytes_appended_outside_the_guard_are_refused(led):
    led.append([row()])
    with open(led.path, "a") as fh:
        fh.write("FAKE,,,,,,,,,,,,,,,,,,,CLOSED\n")
    with pytest.raises(TamperError):
        led.append([row(status="OPEN")])


@pytest.mark.parametrize("ts", ["2026-09-22 10:00:00", "2026-09-22 23:59:59", "2025-01-01 10:00:00", ""])
def test_rows_on_or_before_freeze_date_are_refused(led, ts):
    with pytest.raises(BackfillError):
        led.append([row(ts=ts)])
    assert len(led.rows()) == 0


def test_duplicate_state_refused(led):
    led.append([row()])
    with pytest.raises(DuplicateError):
        led.append([row()])


def test_unknown_column_refused(led):
    r = row(); r["sneaky"] = 1
    with pytest.raises(SchemaError):
        led.append([r])


def test_existing_file_with_wrong_header_refused(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b,c\n")
    with pytest.raises(SchemaError):
        AppendOnlyLedger(p, FORWARD_COLUMNS, tmp_path / "c.json", FREEZE)


def test_no_mutation_api_exists(led):
    for name in ("update", "delete", "remove", "edit", "overwrite", "write", "truncate", "set"):
        assert not hasattr(led, name)


def test_opening_never_rewrites_existing_content(tmp_path):
    p = tmp_path / "fr.csv"
    AppendOnlyLedger(p, FORWARD_COLUMNS, tmp_path / "c.json", FREEZE).append([row()])
    before = p.read_bytes()
    AppendOnlyLedger(p, FORWARD_COLUMNS, tmp_path / "c.json", FREEZE)
    assert p.read_bytes() == before
