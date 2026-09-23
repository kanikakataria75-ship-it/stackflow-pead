# StackFlow PEAD V2 — Research Execution Manifest

**Execution Date:** 2026-09-22  
**Platform / Environment:** Python 3.14 on Windows NT  
**Workspace:** `c:/Users/kanik/Desktop/STACKFLOW ANTIGRAVITY/stackflow`  
**Research Engine Directory:** `stackflow/research/pead_v2/`

---

## 1. Input Data Snapshots (Point-in-Time & Read-Only)

| Input File | Path | Size | Description / Role | Integrity Status |
|---|---|---|---|---|
| `extract_universe.csv` | `data_pipeline/xbrl/cache/extract_universe.csv` | ~3.8 MB | Raw quarterly PAT filings (13,150 rows) | Certified 100% point-in-time |
| `filing_index.csv` | `data_pipeline/xbrl/cache/filing_index.csv` | ~28.3 MB | NSE filing dates & timestamps | 100% timestamp availability |
| `filing_index_integrated.csv` | `data_pipeline/xbrl/cache/filing_index_integrated.csv` | ~19.1 MB | Integrated broadcast timestamps | Verified |
| `px/*.csv` | `pead/cache/px/*.csv` | 434 files | Daily OHLCV price series | Bonus & split adjusted |
| `sector_close_panel.csv` | `cache/sector_close_panel.csv` | ~1.2 MB | Official NIFTY 500 benchmark series | 1996 to 2026 daily |
| `pead_events.csv` | `pead/results/pead_events.csv` | ~4.6 MB | V1 baseline events (7,973 rows) | Baseline verified |

---

## 2. Research Scripts Executed & Provenance

| Script Name | Path | Execution Time | Purpose & Deliverables | Status |
|---|---|---|---|---|
| `audit_and_validate.py` | `scripts/audit_and_validate.py` | 5.2s | Automated assertions on filings, prices, SUE logic -> `DATA_VALIDATION_REPORT.md` | **PASSED** |
| `reproduce_baseline.py` | `scripts/reproduce_baseline.py` | 3.8s | Replicates V1 60d Q5-Q1 spread (+2.50%) -> `PHASE_01_BASELINE_REPRODUCTION.md` | **VERIFIED (1:1)** |
| `build_v2_dataset.py` | `scripts/build_v2_dataset.py` | 14.5s | Builds full horizons (5d..126d) & rolling ex-ante quintiles -> `pead_v2_events.csv` | **COMPLETED** |
| `run_phase2_ex_ante.py` | `scripts/run_phase2_ex_ante.py` | 4.6s | Evaluates ex-ante SUE quintiles -> `PHASE_02_EX_ANTE_RESULTS.csv`, `REPORT.md` | **CONFIRMED** |
| `run_phase3_robustness.py` | `scripts/run_phase3_robustness.py` | 4.1s | Monotonicity & fold drop tests -> `PHASE_03_ROBUSTNESS.md` | **CONFIRMED** |
| `run_phase4_size.py` | `scripts/run_phase4_size.py` | 3.9s | Small / Mid / Large cap turnover segmentation -> `PHASE_04_SIZE_ANALYSIS.md` | **CONFIRMED** |
| `run_phase5_sector.py` | `scripts/run_phase5_sector.py` | 3.5s | Financials vs Non-Financials split -> `PHASE_05_SECTOR_ANALYSIS.md` | **CONFIRMED** |
| `run_phase6_filing_timing.py` | `scripts/run_phase6_filing_timing.py` | 4.2s | Filing speed & FIFO queue diagnostics -> `PHASE_06_FILING_TIMING.md` | **CONFIRMED** |
| `run_phase8_portfolio.py` | `scripts/run_phase8_portfolio.py` | 65.0s | 96-cell portfolio simulation grid -> `PHASE_08_PORTFOLIO_RESULTS.csv`, `REPORT.md` | **VALIDATED** |
| `run_phase9_cost_capacity.py` | `scripts/run_phase9_cost_capacity.py` | 8.9s | Friction stress (0.30%, 0.585%, 1.00%) -> `PHASE_09_COST_CAPACITY.md` | **VALIDATED** |
| `run_phase10_holdout.py` | `scripts/run_phase10_holdout.py` | 9.4s | Out-of-sample holdout validation -> `PHASE_10_HOLDOUT_VALIDATION.md` | **VALIDATED** |
| `run_phase11_kill_tests.py` | `scripts/run_phase11_kill_tests.py` | 7.8s | 7 adversarial kill tests -> `PHASE_11_KILL_TEST.md` | **0 KILLS (SURVIVES)** |
| `generate_all_charts.py` | `scripts/generate_all_charts.py` | 11.2s | 12 publication-grade visualisations in `artifacts/charts/` | **COMPLETED** |
| `build_master_results.py` | `scripts/build_master_results.py` | 2.1s | Compiles all 113 tested cells into `PEAD_V2_MASTER_RESULTS.csv` | **COMPLETED** |

---

## 3. Output Artifacts & Manifest

```text
stackflow/research/pead_v2/
├── REPOSITORY_AUDIT.md
├── PRE_REGISTRATION.md
├── TIMING_RULES.md
├── DATA_VALIDATION_REPORT.md
├── RESEARCH_MANIFEST.md
├── PEAD_V2_MASTER_RESULTS.csv
├── FINAL_PEAD_V2_REPORT.md
├── live_config_pead_v2.md
├── forward_record_pead_v2.csv
│
├── phase_01_baseline/
│   └── PHASE_01_BASELINE_REPRODUCTION.md
├── phase_02_ex_ante/
│   ├── pead_v2_events.csv
│   ├── PHASE_02_EX_ANTE_RESULTS.csv
│   └── PHASE_02_EX_ANTE_REPORT.md
├── phase_03_robustness/
│   └── PHASE_03_ROBUSTNESS.md
├── phase_04_size/
│   └── PHASE_04_SIZE_ANALYSIS.md
├── phase_05_sector/
│   └── PHASE_05_SECTOR_ANALYSIS.md
├── phase_06_filing_timing/
│   └── PHASE_06_FILING_TIMING.md
├── phase_07_portfolio/
│   └── PHASE_07_PORTFOLIO_SPEC.md
├── phase_08_backtest/
│   ├── PHASE_08_PORTFOLIO_RESULTS.csv
│   └── PHASE_08_PORTFOLIO_REPORT.md
├── phase_09_cost_capacity/
│   └── PHASE_09_COST_CAPACITY.md
├── phase_10_holdout/
│   └── PHASE_10_HOLDOUT_VALIDATION.md
├── phase_11_kill_test/
│   └── PHASE_11_KILL_TEST.md
│
└── artifacts/charts/
    ├── 01_sue_distribution.png
    ├── 02_quintile_ladder.png
    ├── 03_cumulative_spread.png
    ├── 04_horizon_response.png
    ├── 05_fold_consistency.png
    ├── 06_size_by_sue.png
    ├── 07_sector_by_sue.png
    ├── 08_filing_timing_by_sue.png
    ├── 09_portfolio_equity_curve.png
    ├── 10_drawdown_curve.png
    ├── 11_cost_sensitivity.png
    └── 12_discovery_vs_holdout.png
```

Research campaign is 100% reproducible and audit-certified.
