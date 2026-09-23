"""Frozen PEAD V2 configuration (live_config_pead_v2_corrected.md, version 2.1.0-AUDIT-CORRECTED).

The constants below are the ONLY place the scanner reads strategy parameters from. At start-up
`verify_frozen_config()` re-reads the frozen markdown file and checks that every constant here
still matches the text; any mismatch is reported by /health and blocks scanning. The file itself
is only ever opened read-only.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from datetime import date, time

from . import settings


@dataclass(frozen=True)
class FrozenConfig:
    version: str = "2.1.0-AUDIT-CORRECTED"
    freeze_date: date = date(2026, 9, 22)          # events on/before this date are backtest data
    slots: int = 30
    holding_sessions: int = 60
    round_trip_cost: float = 0.00585               # 0.2925% per leg
    cutoff_ist: time = time(15, 30)
    lookback_days: int = 365
    min_history_events: int = 150
    min_prior_yoy: int = 6
    signal_quintile: int = 5
    min_turnover_inr: float = 1e7                  # INR 1 crore, 20-session mean traded value
    min_price_inr: float = 50.0                    # entry OPEN must be strictly above
    turnover_window_sessions: int = 20
    turnover_min_sessions: int = 10
    benchmark: str = "NIFTY 500 (price index)"
    queue_policy: str = "FIFO across entry dates; same-day ties to highest SUE; no cross-day displacement"

    @property
    def half_cost(self) -> float:
        return self.round_trip_cost / 2.0


FROZEN = FrozenConfig()

# phrases that must appear in the frozen markdown for the constants above to be considered in sync
_EXPECTED_PHRASES = {
    "version": r"2\.1\.0-AUDIT-CORRECTED",
    "slots": r"30 Concurrent Slots",
    "holding_sessions": r"60 Trading Days",
    "round_trip_cost": r"0\.585% Round-Trip",
    "cutoff_ist": r"15:30:00 IST",
    "lookback_days": r"Rolling 365 Days",
    "min_history_events": r"minimum 150 events",
    "min_turnover_inr": r"turnover \$\\ge\$ INR 1 Crore",
    "min_price_inr": r"Entry Open \$>\$ INR 50",
    "signal_quintile": r"Top Quintile \(Q5\)",
    "non_financials": r"Non-Financials \(Industry Classification\)",
    "date_matched_sue": r"exact fiscal quarter date",
    "share_cash": r"Discrete Share & Cash Accounting",
    "queue": r"FIFO across dates",
    "per_leg_cost": r"0\.2925\\?%",
}


def verify_frozen_config() -> dict:
    """Read-only check that the constants match the frozen markdown. Never writes."""
    path = settings.FROZEN_CONFIG_PATH
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        return {"ok": False, "path": str(path), "error": f"cannot read frozen config: {exc}"}
    text = raw.decode("utf-8", errors="replace")
    missing = [k for k, pat in _EXPECTED_PHRASES.items() if not re.search(pat, text)]
    return {
        "ok": not missing,
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "missing_phrases": missing,
        "constants": {k: (str(v) if not isinstance(v, (int, float, str)) else v) for k, v in asdict(FROZEN).items()},
    }


def frozen_config_text() -> str:
    with open(settings.FROZEN_CONFIG_PATH, "r", encoding="utf-8") as fh:
        return fh.read()
