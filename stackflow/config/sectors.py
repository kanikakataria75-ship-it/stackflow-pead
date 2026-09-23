"""
StackFlow Layer 1 - universe + config.
SELF-CONTAINED. Imports nothing from LeadFlow. Writes only into stackflow/cache/.

DATA SOURCE: niftyindices.com (NSE Indices Ltd), the official index provider.
These are the REAL published index levels, so historical levels already reflect
the constituents as they actually were on each date. This avoids the
reclassification / survivorship look-ahead that a synthetic index rebuilt from
TODAY's constituent list would introduce. No synthetic fallback is needed.

SECTOR LIST PROVENANCE: read live from the provider's own "Sectoral Indices"
dropdown on 2026-09-21, not from memory. The live list differs from the list
assumed in the phase brief - e.g. NIFTY ENERGY and NIFTY INFRA are classified
THEMATIC, not sectoral, and several sectors (CAPITAL GOODS, CEMENT, CHEMICALS,
HOSPITALS, NBFC, RETAIL, TELECOMMUNICATIONS...) exist that the brief did not list.

NOTE ON ABSOLUTE THRESHOLDS (the LeadFlow US-test currency-bug class):
This layer operates ONLY on index-level RATIOS of returns (dimensionless).
There are NO price floors, NO turnover floors, NO currency-denominated
thresholds anywhere in Layer 1. sanity_check_units() prints every numeric
constant for manual inspection before any run.
"""

BENCHMARK = "NIFTY 500"

# Live "Sectoral Indices" list, minus cap-segment / weight-cap VARIANTS of an
# index already present. Exclusion rule is pre-committed and structural - it is
# about double-counting the same sector in a tercile, never about results:
#   excluded: NIFTY FINANCIAL SERVICES 25/50      (weight-cap variant of FIN SERVICES)
#             NIFTY FINANCIAL SERVICES EX-BANK    (subset variant of FIN SERVICES)
#             NIFTY MIDSMALL FINANCIAL SERVICES   (cap-segment variant)
#             NIFTY MIDSMALL HEALTHCARE           (cap-segment variant)
#             NIFTY MIDSMALL IT & TELECOM         (cap-segment variant)
#             NIFTY500 HEALTHCARE                 (universe variant of HEALTHCARE)
#             NIFTY REITS & REALTY                (near-duplicate of REALTY)
SECTORS = [
    "NIFTY AUTO",
    "NIFTY BANK",
    "NIFTY CAPITAL GOODS",
    "NIFTY CEMENT",
    "NIFTY CHEMICALS",
    "NIFTY COMMERCIAL & TRANSPORT SERVICES",
    "NIFTY CONSTRUCTION",
    "NIFTY CONSUMER DURABLES",
    "NIFTY CONSUMER SERVICES",
    "NIFTY FINANCIAL SERVICES",
    "NIFTY FMCG",
    "NIFTY HEALTHCARE",
    "NIFTY HOSPITALS",
    "NIFTY HOUSING FINANCE",
    "NIFTY INSURANCE",
    "NIFTY IT",
    "NIFTY MEDIA",
    "NIFTY METAL",
    "NIFTY NBFC",
    "NIFTY OIL & GAS",
    "NIFTY PHARMA",
    "NIFTY POWER",
    "NIFTY PRIVATE BANK",
    "NIFTY PSU BANK",
    "NIFTY REALTY",
    "NIFTY RETAIL",
    "NIFTY TELECOMMUNICATIONS",
]

# --- pre-registered test grid (see pre_registration.md) ---
LOOKBACKS = [20, 40, 60, 90]     # trading sessions
FORWARDS  = [20, 40, 60, 90]     # trading sessions
REBALANCE = "M"                  # month-end; NOT daily (noise / unrealistic turnover)
MIN_SECTORS_PER_DATE = 9         # need >=9 for three non-degenerate terciles
N_BUCKETS = 3

# One-way cost assumption for net figures. Dimensionless fraction.
COST_ONE_WAY = 0.0020

CACHE_DIR = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache"
RESULTS_DIR = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/results"


def sanity_check_units():
    print("=" * 74)
    print("UNIT / THRESHOLD SANITY CHECK (manual inspection required)")
    print("=" * 74)
    print(f"  LOOKBACKS (trading sessions)  : {LOOKBACKS}")
    print(f"  FORWARDS  (trading sessions)  : {FORWARDS}")
    print(f"  REBALANCE                     : {REBALANCE} (month-end)")
    print(f"  N_BUCKETS                     : {N_BUCKETS}")
    print(f"  MIN_SECTORS_PER_DATE          : {MIN_SECTORS_PER_DATE}")
    print(f"  COST_ONE_WAY                  : {COST_ONE_WAY} "
          f"(= {COST_ONE_WAY*100:.2f}%, DIMENSIONLESS fraction, not INR/USD)")
    print(f"  BENCHMARK                     : {BENCHMARK}")
    print(f"  SECTOR CANDIDATES             : {len(SECTORS)}")
    print("  Currency-denominated thresholds present: NONE (by design).")
    print("  All signal maths is (sector_return - benchmark_return): dimensionless.")
    print("=" * 74)
