
# StackFlow Layer 2 — Run Log

| # | Date | Item | Status | Note |
|---|------|------|--------|------|
| L2-1 | 2026-09-21 | Wayback CDX probe (http) | **VOID** | Repeated ReadTimeouts on port 80. Concluded nothing; superseded. |
| L2-2 | 2026-09-21 | `fetch_pit_membership.py` | **VOID — IMPORTANT** | Fetched 19 "annual" Nifty 500 snapshots 2008-2026. **All 19 files are byte-identical** (single md5), and consecutive years showed 0 added / 0 dropped — impossible for a real index over 18 years. Cause: Wayback holds **exactly ONE capture** of this URL (2020-07-25, on host `www1.nseindia.com`); the `/web/{stamp}/` form silently redirects every request to the nearest capture, so all 19 requests returned the same 2020 file. |

## Correction to an earlier claim (recorded, not overwritten)

I told the user "point-in-time membership is obtainable" after a single successful fetch
of `/web/2015/...` that returned an old-taxonomy constituent list. The old taxonomy made
it look period-correct for 2015. It was not: it was the **2020-07-25** capture, which
legitimately carries the old NSE taxonomy (NSE changed taxonomy ~2021-22).

The error was generalising a time series from one fetch without verifying the returned
capture timestamp. The fix that caught it was a cheap invariant - checking year-over-year
membership turnover - which should have been run before the claim, not after.

Detection: 0 added / 0 dropped between every consecutive pair of annual snapshots.
Any real index turns over. That check is now standard for any archived-data pull here.

| L2-3 | 2026-09-21 | `fetch_pit_stocks.py` | valid (2 resumes) | 2020 PIT universe prices. 433/489 mappable names (88.5%). 56 missing - dominated by mergers/renames (HDFC, LTI, MINDTREE, MOTHERSUMI, MCDOWELL-N), not failures. First run hit the 590s timeout (exit 143); fetcher is idempotent so it was resumed, not restarted. |
| L2-4 | 2026-09-21 | `layer1_passthrough.py` | valid | Layer 1 frozen filter reproduced point-in-time: 257 month-end decisions 2005-2026, median 19 sectors live / 6 excluded. Genuinely PIT - sector index levels are real historical data. |
| L2-5 | 2026-09-21 | `run_h2.py` | valid | 12-cell grid, CLEAN (7 folds) + CONTAM (16 folds) windows, dual baselines, dispersion-normalised, fold permutation tests, reversal-year split. |
| L2-6 | 2026-09-21 | `run_h2_sensitivity.py` | valid | Pre-registered mapping sensitivity. Membership-based assignment: 0/12 cells survive fold-robustness vs 2-4/12 on the industry map. Mapping is load-bearing. |

## Phase 2a outcome

**H2 (selector) REJECTED** - KL3 triggered: 10/12 cells flip sign when the single best
fold is dropped; only 2/12 cells reach the >=65% fold bar (mean 54.8%).

**H2b (filter) NOT SUPPORTED** - bottom tercile negative in 10/12 cells (the one genuine
positive), but fails the fold bar (58.3%) and robustness (4/12), and halves to 5/12 under
the sensitivity check.

**No cell reaches significance** (best permutation p = 0.102). Normalised effects are
0.01-0.07 SD against cross-sectional dispersion of 9.6-27.5%.

KL4 confounded check CONFIRMED the confound exists: vs Nifty 500, BOTH buckets show
+2.8% to +6.2% at M=120 (impossible) - dividend/price-index mismatch plus equal-weight
drift. Building this into the first run is what separated this verdict from a false
positive. Layer 1 found the same class of confound only post-hoc.

Power caveat (pre-recorded): 7 folds makes the drop-best-fold criterion harsher than it
was for Layer 1 at 22 folds. Verdict is "not established", NOT "proven absent". The bar
was not relaxed.

Highest-value next step is DATA, not method: a point-in-time constituent source would
take the clean window from 7 folds to ~20.
