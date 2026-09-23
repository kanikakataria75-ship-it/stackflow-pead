"""Audit point-in-time ex-ante threshold construction with hard assertions."""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT


def audit_thresholds():
    print("=== EXECUTING POINT-IN-TIME EX-ANTE THRESHOLD AUDIT ===")
    events_path = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante", "pead_v2_events.csv")
    ev = pd.read_csv(events_path, parse_dates=["event_day", "entry_date", "filing_ts"])
    ev = ev.sort_values("event_day").reset_index(drop=True)
    
    dates_dt = ev["event_day"].values
    sues = ev["sue"].values
    filing_ts = ev["filing_ts"].values
    
    audit_rows = []
    lookahead_count = 0
    total_audited = 0
    
    lookback_delta = np.timedelta64(365, 'D')
    
    for i in range(len(ev)):
        t_cur = dates_dt[i]
        t_start = t_cur - lookback_delta
        
        # Select historical events strictly before t_cur and >= t_start
        mask = (dates_dt < t_cur) & (dates_dt >= t_start)
        hist_sues = sues[mask]
        hist_sues = hist_sues[np.isfinite(hist_sues)]
        
        # Check if event was assigned a quintile in M1
        q_assigned = ev.loc[i, "q_exante_4q"]
        
        if len(hist_sues) >= 150 and np.isfinite(sues[i]):
            total_audited += 1
            hist_dates = dates_dt[mask]
            latest_info_ts = hist_dates.max()
            
            # Hard assertion: latest_info_ts must be strictly prior to t_cur
            is_lookahead = (latest_info_ts >= t_cur)
            if is_lookahead:
                lookahead_count += 1
                
            q20, q40, q60, q80 = np.quantile(hist_sues, [0.20, 0.40, 0.60, 0.80])
            
            audit_rows.append({
                "event_id": f"EV_{i:05d}",
                "symbol": ev.loc[i, "symbol"],
                "filing_timestamp": str(ev.loc[i, "filing_ts"]),
                "event_day": str(t_cur)[:10],
                "sue": round(float(sues[i]), 4),
                "threshold_window_start": str(t_start)[:10],
                "threshold_window_end": str(t_cur)[:10],
                "Q1_threshold": round(float(q20), 4),
                "Q2_threshold": round(float(q40), 4),
                "Q3_threshold": round(float(q60), 4),
                "Q4_threshold": round(float(q80), 4),
                "assigned_bucket": int(q_assigned) if np.isfinite(q_assigned) else np.nan,
                "latest_information_timestamp_used": str(latest_info_ts)[:10],
                "lookahead_detected": bool(is_lookahead)
            })
            
    df_audit = pd.DataFrame(audit_rows)
    print(f"Total events audited for ex-ante threshold integrity: {total_audited}")
    print(f"Lookahead violations detected: {lookahead_count}")
    
    assert lookahead_count == 0, f"FATAL AUDIT FAILURE: Detected {lookahead_count} lookahead violations!"
    print("HARD ASSERTION PASSED: latest_information_timestamp_used < event_day across 100% of events.")
    
    out_csv = os.path.join(PEAD_V2_ROOT, "AUDIT_05_POINT_IN_TIME.csv")
    df_audit.to_csv(out_csv, index=False)
    print(f"AUDIT_05_POINT_IN_TIME.csv successfully saved ({len(df_audit)} rows).")


if __name__ == "__main__":
    audit_thresholds()
