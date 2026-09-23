# DRIFT backend — forward scanner (FastAPI)

Runs the frozen PEAD V2 configuration (`research/pead_v2/live_config_pead_v2_corrected.md`,
v2.1.0-AUDIT-CORRECTED) on new NSE result filings and appends to the forward record.
**Signals and logging only: no broker connection, no orders, no credentials.**

## Run

```bash
pip install -r requirements.txt
```

```bash
python -m uvicorn drift.api:app --app-dir stackflow/app/backend --port 8765
```

- The daily scan runs at **18:30 IST** from a built-in scheduler thread. Set `DRIFT_SCHEDULER=0` to disable it, for example during development.
- `POST /scan/run` runs a scan immediately.

### Environment

| var | default | purpose |
|---|---|---|
| `DRIFT_SCHEDULER` | `1` | daily 18:30 IST scan thread |
| `DRIFT_DATA_DIR` | `backend/data` | caches, scan log, append chains, state |
| `DRIFT_FORWARD_RECORD` | `research/pead_v2/forward_record_pead_v2.csv` | the forward record (tests point this at a temp file) |

## Tests

```bash
cd stackflow/app/backend && python -m pytest -q
```

There are 64 tests. None of them touch the real forward record or network.

| file | covers |
|---|---|
| `test_thresholds.py` | a filing can never see a filing made at or after its own timestamp (same-day later, exactly-equal, 20 random future-noise draws); 365-day window edges; the 150-event minimum; research quintile boundary convention |
| `test_timing.py` | 15:30 cut-off (including exactly 15:30:00), Friday evening, Saturday before and after 15:30, Sunday night, NSE holidays, after-hours before a holiday; a fortnight sweep proving entry is always the session after the event day; phantom zero-volume rows rejected; index-validated special sessions honoured |
| `test_ledger.py` | append-only guard: edited, deleted or unchained past rows raise `TamperError`; rows on or before the freeze raise `BackfillError`; duplicates and unknown columns are refused; no mutation API exists; opening never rewrites |
| `test_nse_and_book.py` | the **silent-cap** case (20 rows vs totalCount 84) raises; paging to completion; missing totalCount raises; legacy round-number cap detection; strict slot release; same-day SUE ranking; FULL_QUEUE; the frozen constants match the frozen markdown |
| `test_scan_e2e.py` | the full lifecycle on a simulated feed: pending-broadcast is held back, financials excluded, QUEUED until same-day peers close, ENTER, OPEN at the real open, CLOSED after 60 sessions (net = gross − 0.585%); nothing is recorded before the freeze |

## Pipeline (`drift/scanner.py`)

1. **Discovery.** Pulls from the integrated system (`/api/integrated-filing-results`, `&size=2000`, paged) and the legacy system.
   - `nse.assert_complete` hard-fails when rows < `totalCount`, so a short fetch aborts the scan.
   - The window is the last scan date minus 4 days, through today, and never before the freeze.
2. **Parse.** Uses the **existing** locked parser, `data_pipeline/xbrl/scripts/parse_xbrl.py`, loaded from its own file.
   - Earliest *parseable* filing; Consolidated first (D1, D12).
   - A revision is dated at its own revision time.
   - Rows with no `broadcast_Date` wait. After a day, they fall back to creation time forced to after-hours (conservative).
3. **SUE.** Uses `compute_sue_series_datematched`, imported from the corrected research (`research/pead_v2/src/sue_engine.py`): YoY matched by fiscal quarter.
4. **Ex-ante quintile.** Thresholds come from qualifying events with filing timestamp in `[T − 365 d, T)`, with at least 150 of them.
   - The pool is seeded with the corrected research events, then grows with forward events in timestamp order.
   - A filing never sees a later one, including within the same scan.
5. **Timing.** Frozen Cases A–C against a validated calendar: NSE holiday master plus NIFTY 500 index sessions, with weekend special sessions honoured. Price rows on non-sessions or with zero volume are dropped.
6. **Filters.**
   - Universe filters: 20-session mean `Close × Volume` ≥ ₹1 crore before the event day, and entry **open** > ₹50, checked at the real open.
   - Units are asserted, not assumed: the Yahoo currency must be `INR`, and turnover must fall in a plausible INR range.
   - Financial exclusion (D8.1 union): industry `FINANCIAL SERVICES` **or** taxonomy BANKING/NBFC.
   - D13 basis switch: the first quarter after a Consolidated/Standalone switch is rejected.
7. **Decision.** 30 slots, strict slot release (a position exiting at day *d*'s close holds its slot at *d*'s open), FIFO across dates, same-day ties to the highest SUE.
   - A candidate stays `QUEUED` until 15:30 IST on the session before its entry, after which no same-day peer can arrive. It is then `ENTER` or `REJECTED` (`FULL_QUEUE` / `LOWER_SUE_RANK`).
   - Discovered after its entry open → `ENTRY_MISSED`.
8. **Record.** Every Q5 filing is appended to `forward_record_pead_v2.csv`, whose frozen 20-column schema is unchanged. Every filing, with scan time, all four thresholds, the history count, the quintile, planned entry and exit, and the reason code, goes to `data/forward_scan_log.csv`.
9. **Fill.** An `OPEN` row is appended only when the entry session's open exists, and a `CLOSED` row (gross, net after 0.585%, excess vs NIFTY 500) only when the exit close exists. Prices are raw exchange prices (`auto_adjust=False`).

### Append-only guarantee (`drift/ledger.py`)

- The ledger has one write method, `append`, and no update or delete method.
- After every append, the file's byte length and SHA-256 are recorded in a chain file (`data/*.chain.json`).
- Before the next append, the on-disk prefix is re-hashed. Any edit, deletion, reorder, or bytes written outside the guard raises `TamperError`, and the scan stops.
- Rows dated on or before 2026-09-22 raise `BackfillError`.
- A signal's lifecycle is recorded as new rows, never as edits.

### Deliberate divergences from the research backtest (documented, not hidden)

- **Thresholds** use the filing *timestamp* (`< T`), which is stricter than the research's `event_day < T`.
- **D13 basis-switch** rejection is applied, as the brief requires. The corrected backtest did not apply it.
- **Fills** use raw exchange prices. The backtest used dividend-adjusted prices, so forward and backtest returns are not directly comparable. Forward excess is therefore price-vs-price against the NIFTY 500 price index.
- **Universe** is restricted to the 451 research-universe symbols, which are the ones with the ≥ 6 prior YoY quarters that SUE needs.

## Endpoints

- All endpoints are read-only except `POST /scan/run`.
- `?demo=true` on read endpoints returns **synthetic** data stamped `"demo": true, "stamp": "DEMO DATA"`. It is dated in a simulated post-freeze window and never written anywhere.

| endpoint | returns |
|---|---|
| `GET /status` | badge, last and next scan, filings and Q5 today, slots used |
| `POST /scan/run` | runs the pipeline now; returns the scan report |
| `GET /signals/today`, `/signals/history` | scan-log rows |
| `GET /positions/open` | open (marked to last close), planned, closed |
| `GET /forward/performance` | forward-only NAV vs NIFTY 500, seasons completed, kill criteria, research reference (separate) |
| `GET /universe/map` | 451 symbols, sector, financial flag, latest forward filing, research-period last filing (labelled), position |
| `GET /config` | frozen config markdown, verification hash, pre-registration §5 — read-only |
| `GET /health` | frozen-config check, calendar validation, totalCount audits, append-chain status, last scan, data freshness |
