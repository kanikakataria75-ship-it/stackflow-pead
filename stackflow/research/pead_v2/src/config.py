"""PEAD V2 configuration and constants."""
import os
import pandas as pd

# Dynamic workspace path resolution
PEAD_V2_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STACKFLOW_ROOT = os.path.abspath(os.path.join(PEAD_V2_ROOT, "..", ".."))

# Data input paths
XBRL_CACHE = os.path.join(STACKFLOW_ROOT, "data_pipeline", "xbrl", "cache")
PX_CACHE = os.path.join(STACKFLOW_ROOT, "pead", "cache", "px")
if not os.path.exists(PX_CACHE):
    PX_CACHE = os.path.join(STACKFLOW_ROOT, "layer4", "cache", "px")
BENCHMARK_FILE = os.path.join(STACKFLOW_ROOT, "cache", "sector_close_panel.csv")
LAYER4_CALLS = os.path.join(STACKFLOW_ROOT, "layer4", "results", "call_events.csv")
V1_EVENTS = os.path.join(STACKFLOW_ROOT, "pead", "results", "pead_events.csv")

# Constants
MIN_TURNOVER = 1e7      # INR 1 Crore (20-day trailing mean turnover)
MIN_PRICE = 50.0        # INR 50 minimum entry open price
CUTOFF = pd.Timedelta(hours=15, minutes=30)
DISCOVERY_END = pd.Timestamp("2023-12-31")
HOLDOUT_START = pd.Timestamp("2024-01-01")
MIN_PRIOR_YOY = 6       # Minimum prior YoY changes for SUE denominator

# Horizons (trading days)
HORIZONS = {"5d": 5, "20d": 20, "40d": 40, "60d": 60, "90d": 90, "126d": 126}

# Cost assumptions
COST_LOW = 0.00300      # 0.300%
COST_BASE = 0.00585     # 0.585% (round-trip)
COST_HIGH = 0.01000     # 1.000%
