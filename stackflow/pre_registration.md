# StackFlow — Phase 1 Pre-Registration

**Project:** StackFlow (new, independent of LeadFlow — no shared code, cache, or config)
**Layer:** 1 of 4 — Sector rotation detection
**Written:** 2026-09-21
**Status at time of writing:** No H1 test has been run. Data-source availability
probe has been run (that is a coverage check, not a hypothesis test). No grid
result, no fold result, and no bucket return has been observed.

This file is frozen once the first test executes. Any later change appears only
as a dated addendum at the bottom, stating what changed and why.

---

## 1. Hypothesis

**H1:** A sector index that has outperformed the broad market (Nifty 500) over a
trailing lookback window of N trading sessions continues to outperform the broad
market over the subsequent forward window of M trading sessions, more often and
by more than a bottom-ranked sector does.

This is a **persistence / continuation** claim, tested **backward-looking and
mechanically**. It is explicitly **not** a claim that we can predict which sector
will *begin* outperforming before it does. That stronger claim is out of scope
for this phase and will not be tested or implied by any result here.

## 2. Exact test procedure (fixed in advance)

1. Universe: NSE sectoral indices, restricted to those with verified clean daily
   history from the data source. The exact accepted list and each index's true
   start date are written to `cache/coverage_report.csv` by `build_dataset.py`
   **before** the test runs, and are determined by data availability alone —
   never by which sectors produce a better result.
2. Benchmark: Nifty 500 (`^CRSLDX`).
3. On each **month-end** rebalance date `t` (month-end, not daily — daily
   rebalancing overfits noise and implies unrealistic turnover):
   - For each sector with at least N+1 closes on or before `t`, compute
     `trailing_RS = sector_return(t-N → t) − nifty500_return(t-N → t)`.
   - Rank sectors by `trailing_RS`, descending.
   - Split into **terciles**: top / middle / bottom. Require at least
     **9 sectors** present on date `t`, else skip that date.
4. Forward measurement: for each sector, `forward_excess =
   sector_return(t → t+M) − nifty500_return(t → t+M)`, using only closes
   strictly after `t`. Bucket forward excess = equal-weighted mean across the
   sectors in that bucket.
5. Grid: **N ∈ {20, 40, 60, 90} × M ∈ {20, 40, 60, 90} = 16 cells.**
   **All 16 cells are reported.** No cell is selected post hoc as "the result".
6. Folds: **calendar years.** Every fold reported individually. Pooled numbers
   are reported alongside, never instead of, the fold breakdown.
7. Costs: 0.20% one-way applied per rebalance to the long-bucket excess return.
   This layer trades in dimensionless return space; there are **no
   currency-denominated thresholds anywhere in Layer 1** (no price floor, no
   turnover floor). `sanity_check_units()` prints every numeric constant for
   manual inspection before each run. This is a deliberate guard against the
   unconverted-INR-floor bug that silently voided the earlier US-market test.

## 3. Primary metric to be judged

**Mean forward excess return of the TOP tercile vs the BOTTOM tercile
(`top − bottom` spread), per grid cell, broken down per calendar-year fold.**

Secondary, reported always: top-tercile mean forward excess vs zero; middle
tercile; the full rank-bucket ordering; hit rate (fraction of rebalance dates
with positive top-tercile forward excess); fraction of folds positive.

## 4. What would CONFIRM H1

All three required:

- **(a)** Top-tercile forward excess return is positive on average, and the
  `top − bottom` spread is positive, across the *majority of the 16 grid cells* —
  not in one or two isolated cells.
- **(b)** The effect is positive in a **clear majority of calendar-year folds**
  (operationally: ≥ 65% of folds positive for the representative cells), and
  removing the single best fold does not flip the pooled sign.
- **(c)** The rank-bucket relationship is **monotonic or near-monotonic**:
  top > middle > bottom. A top-vs-rest jump with no middle-bucket ordering is
  not accepted as confirmation.

## 5. What would KILL H1 (any one of these is sufficient)

- **K1 — No separation.** Top-tercile forward excess is not distinguishable from
  bottom-tercile forward excess (spread ≈ 0, or spread sign unstable across the
  grid).
- **K2 — Fold concentration.** The pooled effect is carried by one or two
  calendar years and is flat or negative in the rest. Operationally: dropping
  the single best fold flips the pooled sign or removes most of the magnitude.
  (This is precisely the failure mode LeadFlow had to confront; it is assumed
  present here until disproved.)
- **K3 — Wrong-direction monotonicity.** Bottom-tercile trailing RS predicts
  *higher* forward excess than top-tercile — i.e. mean reversion, not momentum.
  This alternative is a real, documented equity pattern and is tested and
  reported explicitly, not assumed away.
- **K4 — Cherry-picked window.** The effect appears only in isolated grid cells
  with no coherent region of the N×M surface supporting it. A single good cell
  inside an otherwise flat grid is noise, and will be reported as noise.

## 6. Pre-committed interpretation rule

- If **(a) and (b) and (c)** all hold → H1 **SUPPORTED**, proceed to consider Layer 2.
- If **any of K1–K4** holds → H1 **REJECTED** for that formulation. Report it as
  rejected. Do not re-cut the data to rescue it.
- If the grid shows a positive but statistically fragile pattern that satisfies
  neither the full confirm set nor a clean kill → **INCONCLUSIVE**, reported as
  inconclusive, with the specific criterion that failed named.

No layer combination, weighting, or scoring occurs in this phase under any
outcome. Layers 2–4 are not built in this phase.

## 7. Known limitations acknowledged in advance

- yfinance NSE sectoral indices are **price** indices; dividend yield differs
  across sectors (e.g. FMCG/IT vs Realty), so forward excess is very slightly
  biased against high-yield sectors. Magnitude is small relative to the effect
  sizes being tested but is not zero, and is not corrected for here.
- Index constituent reconstitution is handled by the index provider. We use
  published index levels, so historical levels reflect the constituents as they
  were — this avoids the survivorship/reclassification look-ahead that would
  arise from applying today's sector membership to historical stocks.
- Sectors with later inception dates enter the panel only from their true start
  date, which changes the cross-section width over time. The 9-sector minimum
  guards against degenerate early terciles.

---

*(Addenda, if any, appear below this line with dates.)*
