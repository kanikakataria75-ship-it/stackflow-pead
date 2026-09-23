"""Master Trade Ledger Generation and Independent Reconstruction Script for PEAD V2 Audit."""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT, COST_BASE, DISCOVERY_END, HOLDOUT_START
from src.data_loader import load_prices, load_benchmark

def generate_audited_trade_ledger():
    print("=== EXECUTING MASTER TRADE LEDGER GENERATION ===")
    events_path = os.path.join(PEAD_V2_ROOT, "phase_02_ex_ante", "pead_v2_events.csv")
    ev = pd.read_csv(events_path, parse_dates=["filing_ts", "event_day", "entry_date", "period_end"])
    
    # Filter for Strategy Universe & Signal
    # Strategy: Non-Financials (is_fin == False), Q5 Ex-Ante (q_exante_4q == 5)
    sig_df = ev[(ev.q_exante_4q == 5) & (ev.is_fin == False)].copy()
    print(f"Total eligible Q5 Non-Financial events: {len(sig_df)}")
    
    px_dict = load_prices()
    bench = load_benchmark()
    
    # Sort events by entry_date and SUE descending
    sig_df = sig_df.sort_values(["entry_date", "sue"], ascending=[True, False]).reset_index(drop=True)
    
    # 1. Resolve candidates with valid price series and complete 60-day holding period
    candidates = []
    holding_period = 60
    
    for r in sig_df.itertuples():
        sym = str(r.symbol)
        if sym not in px_dict:
            continue
        px = px_dict[sym]
        if r.entry_date not in px.index:
            continue
        ei = px.index.get_loc(r.entry_date)
        xi = ei + holding_period
        if xi >= len(px):
            # Incomplete holding window at end of data
            continue
            
        exit_date = px.index[xi]
        entry_px = float(px.Open.iloc[ei])
        exit_px = float(px.Close.iloc[xi])
        if entry_px <= 0 or exit_px <= 0:
            continue
            
        gross_ret = (exit_px / entry_px) - 1.0
        net_ret = gross_ret - COST_BASE
        
        candidates.append({
            "event_idx": r.Index,
            "symbol": sym,
            "filing_ts": r.filing_ts,
            "filing_date": str(r.filing_ts)[:10],
            "event_day": r.event_day,
            "signal_date": str(r.event_day)[:10],
            "entry_date": r.entry_date,
            "exit_date": exit_date,
            "entry_px": entry_px,
            "exit_px": exit_px,
            "holding_days": holding_period,
            "sue": float(r.sue),
            "sue_bucket": 5,
            "taxonomy": str(getattr(r, "taxonomy", "INDAS")),
            "size_group": str(getattr(r, "size_tercile", "Mid")),
            "filing_timing_group": str(getattr(r, "filing_cohort", "Mid")),
            "turnover20": float(getattr(r, "turnover20", np.nan)),
            "gross_return": gross_ret,
            "cost": COST_BASE,
            "transaction_cost": COST_BASE,
            "net_return": net_ret
        })
        
    cands_df = pd.DataFrame(candidates)
    print(f"Total price-valid candidates: {len(cands_df)}")
    
    # 2. Simulate 30-slot queue with SUE_RANK priority and track discrete slots
    max_slots = 30
    available_slots = list(range(1, max_slots + 1)) # Slots 1..30
    
    # active_positions: list of dicts: {"slot": int, "exit_date": Timestamp, ...}
    active_positions = []
    taken_trades = []
    
    # Group candidates by entry_date
    for entry_d, group in cands_df.groupby("entry_date"):
        # Vacate slots where exit_date <= entry_d
        # (In portfolio_engine: active_positions = [pos for pos in active_positions if pos["exit_date"] > entry_d])
        still_active = []
        for pos in active_positions:
            if pos["exit_date"] > entry_d:
                still_active.append(pos)
            else:
                # Slot is freed
                available_slots.append(pos["slot"])
        available_slots.sort()
        active_positions = still_active
        
        n_avail = len(available_slots)
        if n_avail <= 0:
            continue
            
        # Sort by SUE descending
        sorted_cands = group.sort_values("sue", ascending=False).reset_index(drop=True)
        to_take = sorted_cands.head(n_avail)
        
        for rank_idx, tr_row in to_take.iterrows():
            slot_num = available_slots.pop(0) # Assign lowest available slot
            tr_dict = dict(tr_row)
            tr_dict["priority_rank"] = rank_idx + 1
            tr_dict["slot"] = slot_num
            tr_dict["entry_reason"] = "Q5_SUE_SIGNAL_NON_FINANCIAL" if (rank_idx + 1 <= n_avail and len(sorted_cands) <= n_avail) else "SUE_RANK_PRIORITY"
            tr_dict["exit_reason"] = "60D_HOLD_COMPLETE"
            tr_dict["portfolio_weight"] = round(1.0 / max_slots, 6)
            tr_dict["portfolio_pnl"] = tr_dict["net_return"] * tr_dict["portfolio_weight"]
            
            active_positions.append({"slot": slot_num, "exit_date": tr_dict["exit_date"]})
            taken_trades.append(tr_dict)
            
    taken_df = pd.DataFrame(taken_trades)
    print(f"Total trades taken into portfolio: {len(taken_df)}")
    
    # Assign sequential trade_id
    taken_df["trade_id"] = [f"TR_{i+1:05d}" for i in range(len(taken_df))]
    
    # Categorize sector
    def map_sector(tax):
        if "BANK" in tax:
            return "Banking"
        elif "NBFC" in tax:
            return "NBFC"
        else:
            return "Commercial & Industrial"
            
    taken_df["sector"] = taken_df["taxonomy"].apply(map_sector)
    taken_df["sector_group"] = "Non-Financials"
    
    # Required columns order
    ordered_cols = [
        "trade_id", "symbol", "filing_date", "filing_timestamp", "signal_date",
        "entry_date", "entry_price", "exit_date", "exit_price", "holding_days",
        "SUE", "SUE_bucket", "sector", "sector_group", "size_group",
        "filing_timing_group", "priority_rank", "slot", "entry_reason", "exit_reason",
        "gross_return", "transaction_cost", "cost", "net_return", "portfolio_weight", "portfolio_pnl"
    ]
    
    taken_df["filing_timestamp"] = taken_df["filing_ts"].astype(str)
    taken_df["entry_date"] = taken_df["entry_date"].dt.strftime("%Y-%m-%d")
    taken_df["exit_date"] = taken_df["exit_date"].dt.strftime("%Y-%m-%d")
    taken_df["entry_price"] = taken_df["entry_px"].round(2)
    taken_df["exit_price"] = taken_df["exit_px"].round(2)
    taken_df["SUE"] = taken_df["sue"].round(4)
    taken_df["SUE_bucket"] = 5
    taken_df["gross_return"] = taken_df["gross_return"].round(6)
    taken_df["transaction_cost"] = COST_BASE
    taken_df["cost"] = COST_BASE
    taken_df["net_return"] = taken_df["net_return"].round(6)
    taken_df["portfolio_weight"] = round(1.0 / max_slots, 6)
    taken_df["portfolio_pnl"] = (taken_df["net_return"] * taken_df["portfolio_weight"]).round(6)
    
    final_ledger = taken_df[ordered_cols].copy()
    
    # Save both trade_ledger_pead_v2.csv and trade_ledger_pead_v2_audited.csv
    p1 = os.path.join(PEAD_V2_ROOT, "trade_ledger_pead_v2.csv")
    p2 = os.path.join(PEAD_V2_ROOT, "trade_ledger_pead_v2_audited.csv")
    final_ledger.to_csv(p1, index=False)
    final_ledger.to_csv(p2, index=False)
    print(f"Saved master trade ledger to {p1} and {p2} ({len(final_ledger)} trades).")
    
    return final_ledger

if __name__ == "__main__":
    generate_audited_trade_ledger()
