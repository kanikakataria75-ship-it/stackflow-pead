# Part A — Sector Overlap Correction and H1 Robustness Re-run

**Date:** 2026-09-21
**Status:** robustness re-run of the closed H1 hypothesis. No new pre-registration.
Judged against the confirm/kill criteria already on record in `pre_registration.md`.

---

## VERDICT (up front)

> **The bottom-tercile-underperforms finding SURVIVES the overlap correction, essentially unchanged.**
> Bottom tercile vs equal-weight universe mean is negative in **16/16 cells on all three
> panels**, with mean −0.465% (27 sectors), −0.464% (24), −0.459% (23). It was **not** a
> single-theme concentration artifact.

Two secondary findings, both of which cut against assumptions carried into this phase:

1. **The assumed containment structure is largely false.** The nesting asserted in the
   Phase 1b brief — and in my own Phase 1 limitations section — does not hold in the
   actual constituent data. I state this plainly below because I am the one who
   originally asserted it.
2. **Effective breadth really is low (13.8), but overlap correction barely fixes it**,
   because the redundancy is driven by return correlation, not shared membership.

---

## A1. Containment map — built from actual constituents

Source: `niftyindices.com/IndexConstituent/*.csv`, all 27 panel sectors retrieved
(cached in `cache/constituents/`, symbol sets in `cache/constituents.json`).
Metric: `containment(A in B) = |A ∩ B| / |A|`, i.e. share of A's members also in B.
Full matrices: `cache/containment_matrix.csv`, `cache/jaccard_matrix.csv`.

### Containment edges at ≥80% — there are only four

| A (size) | inside | B (size) | containment |
|---|---|---|---|
| NIFTY RETAIL (26) | → | NIFTY CONSUMER SERVICES (46) | **100%** |
| NIFTY HEALTHCARE (20) | ↔ | NIFTY PHARMA (20) | **80%** (mutual) |
| NIFTY PHARMA (20) | ↔ | NIFTY HEALTHCARE (20) | **80%** (mutual) |
| NIFTY PRIVATE BANK (10) | → | NIFTY BANK (14) | **80%** |

### The assumed nesting is NOT in the data

The brief (following my own Phase 1 limitations note) stated that BANK, NBFC, HOUSING
FINANCE, INSURANCE, PRIVATE BANK and PSU BANK all sit inside FINANCIAL SERVICES, and
HOSPITALS inside HEALTHCARE. Measured against real constituents:

**Share of each financial sub-index actually inside NIFTY FINANCIAL SERVICES:**

| sub-index | size | % of its members inside FIN SERVICES |
|---|---|---|
| NIFTY BANK | 14 | **36%** |
| NIFTY PRIVATE BANK | 10 | 40% |
| NIFTY INSURANCE | 12 | 33% |
| NIFTY NBFC | 19 | 26% |
| NIFTY HOUSING FINANCE | 10 | 10% |
| NIFTY PSU BANK | 12 | **8%** |
| NIFTY HOSPITALS *(vs HEALTHCARE)* | 13 | **23%** |

Nine of NIFTY BANK's fourteen members are **not** in FINANCIAL SERVICES
(AUBANK, BANKBARODA, CANBK, FEDERALBNK, IDFCFIRSTB, INDUSINDBK, PNB, UNIONBANK, YESBANK).
Ten of HOSPITALS' thirteen are **not** in HEALTHCARE.

**Why:** these are **capped select indices with fixed member counts**, not exhaustive
sector buckets. NIFTY FINANCIAL SERVICES holds only 20 names — the largest financials —
so it cannot contain the mid-cap banks that populate NIFTY BANK, let alone PSU BANK.
The names imply a hierarchy that the membership rules do not create.

This is exactly the failure the brief warned against ("by constituent overlap, not by
name resemblance"), and the warning was justified — the name-based assumption, which I
had put in writing in Phase 1, was wrong.

## A2. The non-overlapping partitions

**Panel B — containment partition (24 sectors).** Greedy: order by size descending, drop
any sector ≥80% contained in one already kept.

Dropped, and nothing else: **NIFTY PHARMA** (in HEALTHCARE), **NIFTY PRIVATE BANK**
(in BANK), **NIFTY RETAIL** (in CONSUMER SERVICES). → **24 sectors**

**Panel C — strict (23 sectors).** Panel B, then collapse any remaining pair whose
*excess-return* correlation ≥0.75, keeping the longer-history member. Constituent
overlap misses weight-driven redundancy — two capped indices can share few names but be
dominated by the same mega-caps — so this catches what A1 cannot.

Additional drop: **NIFTY FINANCIAL SERVICES** (excess-return corr **0.90** with NIFTY BANK).
→ **23 sectors**

## A3. Effective independent breadth

Eigenvalue participation ratio on **excess returns** vs Nifty 500 (market factor removed —
on raw returns every equity sector shares the market factor and the measure is
uninformative). 2006+, pairwise-complete.

| panel | nominal sectors | **effective breadth** |
|---|---|---|
| A — original | 27 | **13.78** |
| B — containment | 24 | **14.38** |
| C — strict | 23 | **15.22** |

**The breadth concern is confirmed and was if anything understated** — effective breadth
is ~13.8, below the 15–18 the brief anticipated. But note that **dropping three
overlapping sectors barely moves it (13.78 → 14.38)**. Redundancy lives in correlated
*returns*, not shared *membership*:

| pair | excess-return correlation |
|---|---|
| HEALTHCARE ↔ PHARMA | 0.978 |
| BANK ↔ FINANCIAL SERVICES | 0.898 |
| BANK ↔ PRIVATE BANK | 0.875 |
| CONSUMER SERVICES ↔ RETAIL | 0.836 |
| FINANCIAL SERVICES ↔ PRIVATE BANK | 0.819 |
| CONSTRUCTION ↔ REALTY | 0.742 |

BANK and FINANCIAL SERVICES correlate at 0.90 on excess returns while sharing only 36%
of members — precisely the weight-driven redundancy that constituent counting misses.

## A4. H1 grid re-run — side by side

Same N×M grid, same terciles, same month-end rebalance, same 22 calendar-year folds.
Full grids: `results/overlap_grid_{A_orig_27,B_containment,C_strict}.csv`.

### The H1 survivor: BOTTOM tercile vs equal-weight universe mean (%)

| N \ M | | 20 | 40 | 60 | 90 |
|---|---|---|---|---|---|
| **20** | A / B / C | −0.244 / −0.265 / −0.243 | −0.388 / −0.481 / −0.467 | −0.479 / −0.594 / −0.562 | −0.842 / −0.951 / −0.974 |
| **40** | A / B / C | −0.221 / −0.172 / −0.186 | −0.399 / −0.362 / −0.407 | −0.527 / −0.443 / −0.456 | −0.796 / −0.593 / −0.609 |
| **60** | A / B / C | −0.194 / −0.204 / −0.196 | −0.375 / −0.396 / −0.406 | −0.446 / −0.409 / −0.418 | −0.656 / −0.633 / −0.626 |
| **90** | A / B / C | −0.206 / −0.177 / −0.201 | −0.338 / −0.339 / −0.311 | −0.489 / −0.509 / −0.441 | −0.845 / −0.887 / −0.845 |

| panel | mean | min | max | cells negative | mean folds-negative |
|---|---|---|---|---|---|
| A — 27 | **−0.465%** | −0.845% | −0.194% | **16/16** | 63.6% |
| B — 24 | **−0.464%** | −0.951% | −0.172% | **16/16** | 62.8% |
| C — 23 | **−0.459%** | −0.974% | −0.186% | **16/16** | 59.7% |

**Unchanged to three decimal places in the mean.** The effect does not depend on the
duplicated sectors.

### Drift-corrected TOP edge (top − universe mean)

| panel | mean | min | max | cells positive |
|---|---|---|---|---|
| A — 27 | 0.284% | 0.090% | 0.566% | 16/16 |
| B — 24 | 0.363% | 0.141% | 0.632% | 16/16 |
| C — 23 | **0.385%** | 0.167% | 0.648% | 16/16 |

The top edge **improves** on the cleaner panels (+0.10pp), which is the opposite of the
concentration-artifact worry. It remains below the 0.40% placeholder round-trip on
average, so H1's cost conclusion is unchanged.

### Fold positivity, TOP tercile vs Nifty 500 (the `RESULTS_layer1.md` §3 metric)

| cell | A (27) | B (24) | C (23) |
|---|---|---|---|
| N20/M20 | 14/22 (63.6%) | 15/22 (68.2%) | 16/22 (72.7%) |
| N60/M60 | 13/22 (59.1%) | 14/22 (63.6%) | 14/22 (63.6%) |
| N20/M90 | 17/22 (77.3%) | 16/22 (72.7%) | 17/22 (77.3%) |
| N90/M20 | 11/22 (50.0%) | 11/22 (50.0%) | 11/22 (50.0%) |
| N90/M90 | 16/22 (72.7%) | 14/22 (63.6%) | 15/22 (68.2%) |

Marginally better at short lookbacks, unchanged at N90/M20. **H1's criterion (b) still
fails** — most cells remain under the 65% bar. The overlap fix does not rescue H1.

### Drop-worst-fold check on the bottom tercile

Removing each panel's single most-negative fold, `bot_vs_uni` stays negative in
**16/16 cells on all three panels** (A: −0.102% to −0.646%; B: −0.063% to −0.753%;
C: −0.071% to −0.802%). Magnitude roughly halves at short horizons. No sign reversal
anywhere.

## A5. Plain verdict

**SURVIVES.** The bottom-tercile-underperforms finding is not a concentration artifact.
It is identical in mean across all three panels, negative in 16/16 cells on every panel,
and survives dropping the worst fold on every panel.

Two honest qualifications:

- **Fold consistency is the weak point, and it got slightly worse, not better.** Mean
  folds-negative falls 63.6% → 62.8% → 59.7% as the panel is cleaned. All three are
  **below the 65% bar**. The effect is persistent in *sign across cells* but only
  moderately consistent *across years* — which is what H1b must be judged on.
- **Effective breadth is ~14–15, not 27.** Fold counts should be read with that in mind:
  22 folds × ~19 sectors is far less independent evidence than the raw numbers suggest.

**Consequence for Part B:** H1b proceeds, pre-registered against **Panel C (23 sectors)**
with the equal-weight universe baseline. On the pre-registered ≥65% fold bar, Panel C's
observed 59.7% mean folds-negative means **H1b starts out likely to fail its own
confirm criterion**, and it is being run at that bar deliberately rather than at a
relaxed one.
