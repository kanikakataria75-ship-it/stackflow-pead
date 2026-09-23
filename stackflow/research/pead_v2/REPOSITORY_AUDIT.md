# StackFlow — PEAD V2 Repository Audit

**Audit Date:** 2026-09-22  
**Auditor:** Antigravity (Lead Quantitative Researcher & Research-Engineering Agent)  
**Target Repository:** `c:/Users/kanik/Desktop/STACKFLOW ANTIGRAVITY/stackflow`  
**Isolation Guarantee:** Read-only access to existing layers (`pead`, `layer1`, `layer2`, `layer3`, `layer4`, `data_pipeline`). Zero modifications to LeadFlow or existing StackFlow artifacts.

---

## 1. Files Inspected

The following key files across the StackFlow architecture were inspected in detail:

| File Path | Purpose & Content | Status / Role in V2 |
|---|---|---|
| `stackflow/pead/scripts/build_events.py` | Constructs raw event table from XBRL cache and prices. Applies cutoff (15:30 IST), turnover (>= 1 Cr), and price (> 50 INR) filters. | **Reusable Logic** with fixes for hardcoded paths and timestamp handling. |
| `stackflow/pead/scripts/fetch_px.py` | Fetches price series from Layer 4 / cache. | **Reference Only**; prices are already cached locally. |
| `stackflow/pead/scripts/run_pead.py` | Main V1 pipeline: computes SUE (seasonal random walk), calculates returns across horizons (5d to 126d), forms quarterly quintiles, tags `layer4_seen`. | **Partially Reusable**; contains the critical look-ahead in quintile assignment that V2 replaces. |
| `stackflow/pead/scripts/evaluate.py` | Statistical evaluation against 6 pre-registered criteria (BH FDR, fold consistency, drop best fold, monotonicity, 2020 check, `layer4_seen` removal). | **Reusable Logic**; will be formalized into modular metrics module. |
| `stackflow/pead/scripts/backtest.py` | Portfolio simulation of top quintile (Q5), equal-weighted, capped at 15 concurrent positions, 60-day holding. | **Reusable Benchmark**; contains the 15-slot capacity bottleneck analyzed in V2. |
| `stackflow/pead/pre_registration.md` | Original V1 pre-registration specifying SUE, 6 criteria, and 0.585% round-trip cost. | **Baseline Document**; benchmark for baseline reproduction. |
| `stackflow/pead/results/RESULTS_pead.md` | V1 findings: +2.50% cross-sectional spread confirmed, tradeability rejected (+8.38% vs +10.91% Nifty 500). | **Baseline Truth** against which Phase 01 reproduction is verified. |
| `stackflow/data_pipeline/xbrl/cache/` | `extract_universe.csv`, `filing_index.csv`, `filing_index_integrated.csv`. Source of financial statements and exact filing timestamps. | **Primary Data Source** (Read-Only). |
| `stackflow/layer4/cache/px/` & `stackflow/pead/cache/px/` | 434 daily OHLCV price series for universe stocks. | **Primary Price Source** (Read-Only). |
| `stackflow/cache/sector_close_panel.csv` | Daily close prices for NIFTY 500 benchmark and 27 sector indices. | **Primary Benchmark Source** (Read-Only). |

---

## 2. Relevant Functions & Data Flow

### 2.1 Upstream Data Flow
```
[BSE/NSE XBRL XML Filings]
            │
            ▼
[extract_universe.csv] ──> Filter (Quarterly, PAT valid, Consolidated > Standalone)
            │
            ├─ [filing_index.csv + filing_index_integrated.csv] ──> Exact filing timestamps (100% available)
            │
            ▼
[sue_series() calculation] ──> YoY Profit change vs std(prior 8 quarters)
            │
            ├─ [Daily OHLCV Price Cache] ──> Liquidity filters (Turnover >= 1 Cr, Price > 50)
            │
            ▼
[Event Date & Entry Resolution] ──> Next trading session Open (strictly post-filing)
            │
            ├─ [V1: Quarter-level pd.qcut] ──> ⚠️ Look-ahead across calendar quarter
            │
            ▼
[Forward Return Slices: 5d, 10d, 30d, 60d, 126d]
            │
            ▼
[Excess Return vs Event Universe & Nifty 500]
```

### 2.2 Key Algorithms & Formulas
1. **SUE Formula (Locked):**
   $$SUE = \frac{\text{PAT}_q - \text{PAT}_{q-4}}{\sigma(\Delta \text{YoY PAT}_{q-8 \dots q-1})}$$
   Requires $\ge 6$ historical YoY changes. No analyst estimates. Division by historical standard deviation of YoY differences prevents division-by-zero or sign distortion from negative base profits.
2. **Timing Engine:**
   - Filing timestamp $\le$ 15:30 IST: Event day $T = \text{same day}$ (if trading day). Entry = Open of $T+1$.
   - Filing timestamp $>$ 15:30 IST: Event day $T = \text{next trading day}$. Entry = Open of $T+2$.
   - Entry price = `Open` of entry session.
3. **Horizon Returns:**
   $$R_h = \frac{P_{\text{entry} + h}}{P_{\text{entry},\text{Open}}} - 1$$
   $$R_{\text{excess, univ}, h} = R_h - \bar{R}_{\text{month}, h}$$

---

## 3. Reusable vs. Dangerous Components

### 3.1 Reusable Components (Safe)
- **Data Loaders:** Parsing of `extract_universe.csv`, `filing_index.csv`, and price CSVs is sound and handles edge cases (e.g. date formats, NaNs, missing bars).
- **SUE Mathematical Definition:** The seasonal random walk specification is mathematically robust to sign-flips and does not suffer from small-denominator explosions.
- **Timing Gate:** The 15:30 IST cutoff logic ensures that trades never enter at the close of an already-announcing day, but strictly at the open of the subsequent session.
- **Statistical Evaluation Suite:** Two-sample t-tests, fold positivity calculations, Benjamini-Hochberg FDR correction, and best-fold drop routines are verified.

### 3.2 Dangerous Components & Flaws in V1
1. **Critical Look-Ahead in Bucket Assignment (Ex-Post Quintiles):**
   In `run_pead.py`:
   ```python
   ev["quintile"] = ev.groupby("qtr", group_keys=False).apply(lambda g: qcut(g, "sue"))
   ```
   *The Hazard:* Grouping by `qtr` uses all events occurring in that calendar quarter. A company filing on October 15th has its quintile cutoff determined by companies filing in November and December. This is an ex-post bucket construction and cannot be executed in live trading.
2. **Hardcoded Machine Paths:**
   Scripts in `pead/scripts/` contain static paths like `C:/Users/kanik/Desktop/stackflow claude/stackflow/...`. These break portability and must be replaced with workspace-relative path resolution.
3. **EAR Look-Ahead Window:**
   In `run_pead.py`, EAR as initially defined in the brief ($[-1, +1]$) overlaps with the entry date ($+1$ Open), creating an intra-day look-ahead. While flagged as `ear_lookahead` in V1, V2 must ban this completely from any decision path.
4. **Calendar Day vs Trading Day Holding in Portfolio Sim:**
   In `backtest.py`, holding period was approximated using 88 calendar days and linear daily interpolation. V2 requires exact trading-day bars matching the underlying price series.
5. **FIFO Queue Capacity Bottleneck:**
   A static 15-position cap without ranking or queue management selects only early-filing large-cap names, creating an unrepresentative sub-sample.

---

## 4. Known Look-Ahead Risks & Mitigations

| Risk | Source | V2 Mitigation Strategy |
|---|---|---|
| **Future SUE Thresholds** | Computing quintile cuts using contemporaneous quarter events. | **Strict Rolling Historical Thresholds:** An event at date $T$ is classified using SUE percentiles computed *exclusively* from qualifying events that occurred prior to date $T$. |
| **Intraday Announcement Leakage** | Buying at close on announcement day or before market digest. | **Next-Session Open Entry:** Hard assertion verifying entry timestamp $>$ announcement timestamp + market close. |
| **Restatement / Revision Leakage** | Using restated financials filed months later. | **Earliest Filing Lock:** Locked decision D12 enforced; only the earliest parseable filing timestamp per company-period is utilized. |
| **Benchmark Alignment** | Mismatched return indexing across holidays/sessions. | Exact date-aligned indexing against Nifty 500 closing series. |
| **Look-Ahead in Portfolio Queue** | Prioritizing trades based on forward performance or ex-post SUE. | Strictly ex-ante queue policies: either pure time priority, or priority based on SUE known at the time of entry. |

---

## 5. Proposed V2 System Architecture

```text
stackflow/research/pead_v2/
├── PRE_REGISTRATION.md           # Master protocol (Locked)
├── REPOSITORY_AUDIT.md           # This document
├── TIMING_RULES.md               # Explicit timing specifications
├── DATA_VALIDATION_REPORT.md     # Data integrity audit & automated assertions
├── RESEARCH_MANIFEST.md          # Complete execution provenance
├── PEAD_V2_MASTER_RESULTS.csv    # Every single tested cell logged
├── FINAL_PEAD_V2_REPORT.md       # Final synthesis & conclusion
│
├── src/                          # Modular Python library
│   ├── __init__.py
│   ├── config.py                 # Paths, constants, locked parameters
│   ├── data_loader.py            # Unified XBRL & OHLCV loader
│   ├── sue_engine.py             # SUE math & rolling ex-ante percentile engine
│   ├── timing.py                 # Exchange session calendar & entry alignment
│   ├── metrics.py                # Folds, BH FDR, drop-best, t-tests
│   ├── portfolio_engine.py       # True trading-day portfolio simulation
│   └── visualizer.py             # Matplotlib charts for artifacts/charts/
│
├── scripts/                      # Phase runners (Phases 01 through 12)
├── artifacts/charts/             # 12 required publication-grade visualisations
└── phase_outputs/                # Intermediate and final CSV/MD results
```

This architecture guarantees complete reproducibility, strict point-in-time correctness, and zero contamination of other repository assets.
