"""Append-only ledgers with a tamper guard.

The forward record is event-sourced: a signal's life (QUEUED -> ENTER -> OPEN -> CLOSED, or
REJECTED) is a sequence of appended rows sharing one signal_id; the latest row is the current
state. There is deliberately NO update or delete method anywhere in this module.

Guards (all raise, none warn):
  * TamperError   - the bytes already on disk differ from the hash recorded after the last
                    append (someone edited / truncated / reordered a past row).
  * BackfillError - a row whose filing timestamp is on or before the freeze date.
  * DuplicateError- the same (signal_id, status) appended twice.
  * SchemaError   - columns differ from the file's frozen header.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

# frozen schema from live_config_pead_v2_corrected.md §4 — header of forward_record_pead_v2.csv
FORWARD_COLUMNS = [
    "signal_id", "symbol", "period_end", "filing_timestamp", "event_day", "sue_value",
    "rolling_q80_threshold", "is_taken", "skip_reason", "entry_date", "entry_price", "exit_date",
    "exit_price", "holding_sessions", "gross_return", "net_return", "cost_deducted",
    "nifty500_excess_return", "univ_excess_return", "status",
]

SCAN_COLUMNS = [
    "scan_id", "scanned_at", "signal_id", "symbol", "company", "industry", "is_fin", "taxonomy",
    "basis", "period_end", "filing_timestamp", "ts_source", "event_day", "planned_entry",
    "planned_exit", "pat", "pat_prior_year", "sue", "n_prior_yoy", "hist_events", "q20", "q40",
    "q60", "q80", "quintile", "turnover20_inr", "last_close_inr", "decision", "reason", "xbrl",
]


class TamperError(RuntimeError): ...
class BackfillError(ValueError): ...
class DuplicateError(ValueError): ...
class SchemaError(ValueError): ...


class AppendOnlyLedger:
    def __init__(self, path: Path, columns: list[str], chain_path: Path, freeze_date: date,
                 ts_column: str = "filing_timestamp", key: tuple[str, ...] = ("signal_id", "status")):
        self.path, self.columns, self.chain_path = Path(path), list(columns), Path(chain_path)
        self.freeze_date, self.ts_column, self.key = freeze_date, ts_column, key
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "x", newline="", encoding="utf-8") as fh:   # 'x': never clobbers
                csv.writer(fh).writerow(self.columns)
        header = self._header()
        if header != self.columns:
            raise SchemaError(f"{self.path.name}: header {header} != frozen schema {self.columns}")
        if not self.chain_path.exists():
            self._write_chain(self._bytes())

    # ------------------------------------------------------------------ integrity
    def _bytes(self) -> bytes:
        with open(self.path, "rb") as fh:
            return fh.read()

    def _header(self) -> list[str]:
        with open(self.path, "r", newline="", encoding="utf-8") as fh:
            return next(csv.reader(fh), [])

    def _write_chain(self, blob: bytes) -> None:
        tmp = self.chain_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                                   "rows": max(blob.count(b"\n") - 1, 0),
                                   "updated": datetime.now().isoformat(timespec="seconds")}))
        os.replace(tmp, self.chain_path)

    def verify(self) -> dict:
        blob = self._bytes()
        chain = json.loads(self.chain_path.read_text())
        n = chain["bytes"]
        ok = len(blob) >= n and hashlib.sha256(blob[:n]).hexdigest() == chain["sha256"]
        return {"ok": ok, "file_bytes": len(blob), "chained_bytes": n, "rows": chain.get("rows"),
                "trailing_unchained_bytes": max(len(blob) - n, 0), "last_append": chain.get("updated")}

    # ------------------------------------------------------------------ read
    def rows(self) -> pd.DataFrame:
        return pd.read_csv(self.path, dtype=str, keep_default_na=False)

    # ------------------------------------------------------------------ the only write path
    def append(self, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        v = self.verify()
        if not v["ok"] or v["trailing_unchained_bytes"]:
            raise TamperError(f"{self.path.name}: on-disk bytes no longer match the append chain {v}")
        existing = self.rows()
        seen = set(map(tuple, existing[list(self.key)].values.tolist())) if len(existing) else set()
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=self.columns, lineterminator="\n", extrasaction="raise")
        for r in rows:
            if set(r) - set(self.columns):
                raise SchemaError(f"unknown columns {sorted(set(r) - set(self.columns))}")
            ts = pd.Timestamp(r.get(self.ts_column))
            if pd.isna(ts) or ts.date() <= self.freeze_date:
                raise BackfillError(f"refused: {self.ts_column}={r.get(self.ts_column)} is on/before "
                                    f"freeze date {self.freeze_date} (no backfill)")
            k = tuple(str(r.get(c, "")) for c in self.key)
            if k in seen:
                raise DuplicateError(f"refused: {self.key}={k} already recorded")
            seen.add(k)
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in self.columns})
        blob = self._bytes()
        prefix_newline = b"" if blob.endswith(b"\n") else b"\n"
        with open(self.path, "ab") as fh:                     # append mode only
            fh.write(prefix_newline + buf.getvalue().encode("utf-8"))
            fh.flush()
            os.fsync(fh.fileno())
        self._write_chain(self._bytes())
        return len(rows)
