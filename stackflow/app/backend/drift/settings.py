"""Filesystem locations. Everything the app writes lives under DATA_DIR, except the forward
record, which is the research program's own append-only file (research/pead_v2/)."""
from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

BACKEND_DIR = Path(__file__).resolve().parents[1]
STACKFLOW = BACKEND_DIR.parents[1]                      # .../stackflow
PEAD_V2 = STACKFLOW / "research" / "pead_v2"
XBRL_DIR = STACKFLOW / "data_pipeline" / "xbrl"

DATA_DIR = Path(os.environ.get("DRIFT_DATA_DIR", BACKEND_DIR / "data"))

# ---- read-only research inputs -------------------------------------------------------------
FROZEN_CONFIG_PATH = PEAD_V2 / "live_config_pead_v2_corrected.md"
PREREG_PATH = PEAD_V2 / "CORRECTED_REPORT.md"
CORRECTED_EVENTS = PEAD_V2 / "corrected" / "pead_v2_events_corrected.csv"   # ex-ante pool seed
PERIOD_METRICS = PEAD_V2 / "corrected" / "period_metrics_corrected.csv"     # research reference only
XBRL_EXTRACT = XBRL_DIR / "cache" / "extract_universe.csv"                  # historical PAT series
XBRL_PARSER = XBRL_DIR / "scripts" / "parse_xbrl.py"                        # existing locked parser
BENCH_PANEL = STACKFLOW / "cache" / "sector_close_panel.csv"                # validated NSE sessions

# ---- append-only forward ledgers -----------------------------------------------------------
FORWARD_RECORD = Path(os.environ.get("DRIFT_FORWARD_RECORD", PEAD_V2 / "forward_record_pead_v2.csv"))
SCAN_LOG = DATA_DIR / "forward_scan_log.csv"

# ---- app caches (safe to delete) -----------------------------------------------------------
PX_DIR = DATA_DIR / "px"
XML_DIR = DATA_DIR / "xml"
STATE_FILE = DATA_DIR / "state.json"
HOLIDAYS_FILE = DATA_DIR / "nse_holidays.json"
FORWARD_PAT = DATA_DIR / "forward_pat.csv"             # PAT parsed from post-freeze filings

SCAN_HOUR_IST = 18
SCAN_MINUTE_IST = 30

for d in (DATA_DIR, PX_DIR, XML_DIR):
    d.mkdir(parents=True, exist_ok=True)
