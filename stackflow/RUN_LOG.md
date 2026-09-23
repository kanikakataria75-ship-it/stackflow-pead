# StackFlow — Run Log

Every run is recorded here, including runs later found void, and including
diagnoses later found wrong. Void runs are annotated, never deleted.

| # | Date | Script | Status | Note |
|---|------|--------|--------|------|
| 1 | 2026-09-21 | `probe_data_source.py` | **VOID** | Bulk yfinance probe. 17 of 21 NSE sectoral tickers returned exactly 1 row dated 2026-09-18; 4 returned full multi-year history. |
| 2 | 2026-09-21 | `probe_retry.py` | **VOID** | Paced re-probe of the 19 failures, one ticker at a time with sleeps. All 19 returned 0 usable rows. |
| 3 | 2026-09-21 | control test | valid | `^NSEBANK` returned 4678 rows *immediately* under the identical code path that gave `^CNXAUTO` exactly 1 row, repeatably. |

## Correction to the run-1 diagnosis (recorded, not overwritten)

When run 1 produced its 1-row stubs I wrote in this log that the cause was
**Yahoo throttling**. That diagnosis was **wrong**, and run 3 is what disproved
it: under throttling a known-good ticker would also degrade, and `^NSEBANK` did
not — it returned full history in the same loop, repeatably.

The true cause: Yahoo has **retired historical data for most NSE sectoral
indices**. The symbols are correct and still resolve (a Yahoo symbol-search
confirmed `^CNXAUTO` → "NIFTY AUTO", `^CNXFMCG` → "NIFTY FMCG", etc.), but only
a current-day stub is served. Yahoo retains real history for only Nifty 500,
Nifty 50, Bank, IT and Pharma.

Why this correction matters rather than being a footnote: the throttling
diagnosis implied "retry harder and it will work". The correct diagnosis implies
"this source cannot support this test at all" — 3 usable sectors, where terciles
need at least 9. Acting on the wrong diagnosis would have burned time on retries
and then, plausibly, led to quietly running the test on 3–4 sectors, which would
have produced a meaningless grid that still *looked* like a result.

## Source change

| # | Date | Script | Status | Note |
|---|------|--------|--------|------|
| 4 | 2026-09-21 | `build_dataset.py` (v2) | valid | Source switched from Yahoo to **niftyindices.com (NSE Indices Ltd)** — the official index provider. All 27 sectoral indices + Nifty 500 retrieved with full published history. |

Notes on the switch:
- NSE's own `nseindia.com` API returned 403/503 to programmatic requests. No
  attempt was made to evade that bot protection.
- The provider's *current* endpoint is `/BackPage/getHistoricaldatatabletoString`.
  The widely-documented `/Backpage.aspx/getHistoricaldatatabletoString` is
  retired and now redirects to an HTML page — an earlier attempt failed for that
  reason alone, not because of blocking. Found by observing the live page's own
  network calls.
- The sector list was read live from the provider's "Sectoral Indices" dropdown
  rather than from memory. It **differs from the phase brief's assumed list**:
  NIFTY ENERGY and NIFTY INFRA are classified *Thematic*, not Sectoral, and
  several sectors the brief did not list exist (CAPITAL GOODS, CEMENT,
  CHEMICALS, HOSPITALS, NBFC, RETAIL, TELECOMMUNICATIONS, CONSTRUCTION,
  CONSUMER SERVICES, HOUSING FINANCE, INSURANCE, COMMERCIAL & TRANSPORT SERVICES).
- **The synthetic-constituent fallback was NOT needed and was NOT used.** Real
  published index levels embed point-in-time constituents, so the
  reclassification/survivorship look-ahead that a fallback would have introduced
  does not arise.

## Layer 1 test runs

| # | Date | Script | Status | Note |
|---|------|--------|--------|------|
| 5 | 2026-09-21 | `run_h1_grid.py` | valid | Full 4x4 N x M grid, 22 calendar-year folds, 249-255 rebalances per cell. All 16 cells reported. |
| 6 | 2026-09-21 | `run_robustness.py` | valid, **POST-HOC** | Universe-drift confound + top-vs-middle separation + 2006+ subsample. Run *after* seeing run 5, and labelled post-hoc in the results report rather than folded in silently. It materially weakened the headline result and is reported for that reason. |

Result: **H1 INCONCLUSIVE** - fails pre-registered criteria (b) fold positivity
and (c) monotonicity; no kill criterion cleanly triggered. See `RESULTS_layer1.md`.

## Phase 1b runs

| # | Date | Script | Status | Note |
|---|------|--------|--------|------|
| 7 | 2026-09-21 | `build_containment.py` | valid | Containment map from ACTUAL constituent CSVs for all 27 sectors. Found the assumed nesting (BANK inside FINANCIAL SERVICES, HOSPITALS inside HEALTHCARE) is FALSE: only 36% and 23% respectively. These are capped select indices, not exhaustive buckets. Only 4 real containment edges exist. |
| 8 | 2026-09-21 | excess-corr breadth | valid | Effective breadth on excess returns: 13.78 (27 sectors), 14.38 (24), 15.22 (23). Breadth concern CONFIRMED and understated; but overlap removal barely helps, because redundancy is correlation-driven not membership-driven. |
| 9 | 2026-09-21 | `run_overlap_rerun.py` | valid | H1 grid re-run on panels A/B/C. Bottom-tercile effect SURVIVES: 16/16 cells negative on all three panels, means -0.465 / -0.464 / -0.459%. Not a concentration artifact. |
| 10 | 2026-09-21 | `run_h1b.py` | valid, **FULLY CONFIRMATORY** | H1b grid. Output identical to run 9 Panel C in 16/16 cells (max diff 0.000e+00). |

## Correction to the H1b pre-registration (recorded, not overwritten)

Section 0 of `pre_registration_h1b.md` claimed that changing the ranking baseline from
Nifty 500 to the equal-weight universe mean would change tercile membership, making H1b
partly novel. **That was wrong and was provable by inspection beforehand:** both
baselines are per-date scalars subtracted from every sector alike, and subtracting a
constant cannot change a rank order. The terciles are identical by construction.

Why it matters: the error inflated how much evidential weight H1b could carry. H1b is
not semi-confirmatory but FULLY confirmatory - a re-adjudication of already-observed
numbers against criteria written afterwards. Recorded as a dated addendum in the
pre-registration.

Results: **Part A SURVIVES** (`results/overlap_robustness.md`).
**H1b INCONCLUSIVE** - fails criterion (a) fold consistency at 59.7% vs the 65% bar;
criterion (b) passes; no kill criterion triggered (`results/RESULTS_h1b.md`).

## Phase 1c runs

| # | Date | Script | Status | Note |
|---|------|--------|--------|------|
| 11 | 2026-09-21 | (config freeze) | valid | `live_config_layer1.md` written and LOCKED before any Phase 1c number was generated. Frozen cell N=20/M=90 on Panel C, selected from already-reported cells only - no new grid search. |
| 12 | 2026-09-21 | temporal split | valid, **INFORMATIVE ONLY** | Retroactive split at 2016-01-01 (near-even fold count, reason fixed in advance). NOT out-of-sample: both halves were already seen in prior reports. Sign holds both halves; magnitude does NOT - late half 4x weaker (-1.550% vs -0.380%), fold consistency 81.8% -> 63.6%. |
| 13 | 2026-09-21 | dispersion diagnostic | valid | Tested whether the decay is just a calmer cross-section. It is not: dispersion fell 1.20x while the effect fell 4.08x. Dispersion-normalised effect still fell 3.37x, stepping down ~two-thirds after 2015 and staying flat across two 5-year blocks. |
| 14 | 2026-09-21 | `update_forward_record.py` | valid | Forward record initialised, correctly EMPTY (0 rows). First rebalance 2026-09-30; first completed 90-session window ~2027-02. Hard code guard refuses any pre-freeze date. |

## Phase 1c outcome

Layer 1 is **FROZEN** as bottom-tercile binary exclusion, N=20/M=90, Panel C.
Evidence status: **DISCOVERY - NOT VALIDATED**. No out-of-sample evidence exists yet.

Material finding this phase: the effect has **decayed by roughly two-thirds since ~2015**
on a dispersion-normalised basis and stayed weak across two independent 5-year blocks.
The full-period headline (-0.974%) overstates the last decade (-0.380%). The forward
record must be judged against the late-half figure, not the full-sample one.

The frozen config was NOT re-tuned in response to the decay - it was locked beforehand,
and re-selecting on late-half performance would be the exact seen-data selection this
phase exists to avoid. The decay is recorded as a known property of what was frozen.

## Edge-decay diagnostic (exploratory, 2026-09-21)

| # | Date | Script | Status | Note |
|---|------|--------|--------|------|
| 15 | 2026-09-21 | `diag_d3_panel.py` | valid | D3 decisive test. Constant 19-sector panel (zero composition change) shows the decay STRONGER (5.28x normalised) than the variable panel (3.37x). Panel C held exactly 19 sectors 2007-2017; first entrant 2018-04-02. D3 RULED OUT. |
| 16 | 2026-09-21 | break-point scan | valid | **Corrects Phase 1c.** The "step at ~2015" is NOT well-identified: early/late gap is comparable anywhere from 2011 to 2019 and PEAKS at 2019 (-0.124), not 2015. Phase 1c's "a step, not a drift" was an artifact of 5-year block boundaries. |
| 17 | 2026-09-21 | permutation test | valid | Decay is statistically real on fold-level units: early -0.141 vs late -0.029 normalised, one-sided permutation p=0.016 (raw p=0.024). Not carried by 1-2 years (early ex-top2 still -0.113). |
| 18 | 2026-09-21 | web evidence D1/D2 | valid | Sourced external evidence gathered. See `results/edge_decay_diagnostic.md` for citations. |

## Correction to the Phase 1c decay framing (recorded, not overwritten)

Phase 1c described the decay as "a step, not a drift ... stable across two independent
blocks." That rested on 5-year blocks whose boundaries happened to fall at 2014/2015.
A full break-point scan shows no identifiable 2015 event - the gap is similar across
2011-2019 and largest at 2019. The DECLINE is real (p=0.016); the DATING is not.

Why it matters: D1 and D3 pre-registered criteria both hinged on timing coincidence with
the "~2015 step". With the step undated, those tests lost most of their power - which is
why D1 is reported INCONCLUSIVE rather than decided.

## Diagnostic outcome

D3 panel artifact  : **RULED OUT** (decay stronger on constant panel; changes postdate it)
D1 sector-specific : **INCONCLUSIVE** (fund AUM inflects 2023-25, far too late; sector
                     derivatives ramp 2016-19 fits timing but mechanism unsupported)
D2 market-wide     : **WEAKENED (strong form)** - efficiency proxies postdate the decay,
                     and stock-level momentum on Nifty 500 did NOT decay over Jul2015-Jun2024

Layer 2 implication: does not automatically inherit the decay, but must budget to measure
it - sub-period check in its FIRST results doc, dispersion-normalised metric alongside raw,
and explicit handling of the reversal-regime weakness (a general momentum property).
