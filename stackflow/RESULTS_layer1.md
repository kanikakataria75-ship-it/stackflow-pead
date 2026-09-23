# StackFlow Layer 1 — Results: Sector Momentum Persistence (H1)

**Run date:** 2026-09-21
**Verdict written after the data, judged against `pre_registration.md` as frozen.**

---

## 0. Data actually achieved

| item | value |
|---|---|
| Source | niftyindices.com (NSE Indices Ltd) — **official published index levels** |
| Benchmark | NIFTY 500, 1995-01-01 → 2026-09-18 (7,860 days) |
| Sectors retrieved | 27 of 27 candidates |
| Panel | 7,628 trading days, 1996-01-01 → 2026-09-18 |
| Usable test period | 2005 → 2026 (first date with ≥9 sectors), **22 calendar-year folds** |
| Rebalance dates per cell | 249–255 month-ends |
| Synthetic-constituent fallback | **not needed, not used** |

Sector count is 20–22 from 2005, rising to 27 by 2021. Yahoo Finance was
abandoned as a source: it serves real history for only 3 usable sectors. See
`RUN_LOG.md`, including a corrected wrong diagnosis.

**Sector list came from the provider's live dropdown, not memory,** and differs
from the brief: NIFTY ENERGY and NIFTY INFRA are *Thematic*, not Sectoral, and
11 sectors the brief did not name do exist and are included.

---

## 1. Full N×M grid — all 16 cells (nothing omitted)

Mean forward excess return vs NIFTY 500, %. N = trailing lookback sessions,
M = forward window sessions.

**TOP tercile**

| N \ M | 20 | 40 | 60 | 90 |
|---|---|---|---|---|
| **20** | 0.41 | 0.62 | 0.76 | 1.18 |
| **40** | 0.34 | 0.51 | 0.68 | 1.41 |
| **60** | 0.22 | 0.46 | 0.67 | 1.29 |
| **90** | 0.21 | 0.41 | 0.64 | 1.39 |

**TOP − BOTTOM spread**

| N \ M | 20 | 40 | 60 | 90 |
|---|---|---|---|---|
| **20** | 0.53 | 0.70 | 0.79 | 1.17 |
| **40** | 0.43 | 0.61 | 0.78 | 1.36 |
| **60** | 0.28 | 0.55 | 0.71 | 1.11 |
| **90** | 0.32 | 0.49 | 0.73 | 1.41 |

**BOTTOM tercile — the pre-registered mean-reversion check** (positive means losers bounce)

| N \ M | 20 | 40 | 60 | 90 |
|---|---|---|---|---|
| **20** | −0.11 | −0.08 | −0.03 | 0.01 |
| **40** | −0.09 | −0.10 | −0.10 | 0.05 |
| **60** | −0.07 | −0.09 | −0.03 | 0.18 |
| **90** | −0.11 | −0.08 | −0.09 | −0.02 |

**Mean reversion is not present.** Bottom-tercile forward excess is about zero to
slightly negative in 14 of 16 cells. K3 is not triggered. Trailing losers do not
bounce; they drift mildly further behind.

Per-cell detail (hit rates, monotonicity, cost-net, drop-best-fold) is in
`results/grid_summary.csv`.

---

## 2. The confound that changes the reading

Post-hoc check, declared as post-hoc, reported regardless of outcome
(`results/robustness.csv`).

The equal-weight mean of **all 27 sectors** already beats cap-weighted NIFTY 500.
That drift lifts *every* bucket, so raw top-tercile excess overstates the rank edge.

| forward window M | 20 | 40 | 60 | 90 |
|---|---|---|---|---|
| **universe drift** (all sectors vs Nifty 500, %) | 0.10–0.13 | 0.26–0.31 | 0.40–0.44 | 0.83–0.86 |

At M=90 the top tercile's raw 1.18–1.41% excess is **mostly universe drift**:
roughly 0.83% of it is simply "equal-weighted sectors beat a cap-weighted broad
index" — a size/weighting effect, **not sector rotation**.

**Rank edge with the drift removed (top − universe mean), %:**

| N \ M | 20 | 40 | 60 | 90 |
|---|---|---|---|---|
| **20** | 0.28 | 0.31 | 0.31 | 0.33 |
| **40** | 0.21 | 0.22 | 0.25 | **0.56** |
| **60** | 0.09 | 0.18 | 0.26 | **0.46** |
| **90** | 0.11 | 0.16 | 0.24 | **0.57** |

Positive in 16/16 cells — real, but roughly **one third the size** of the naive number.
Mean across the grid: **+0.28%**. Assumed round-trip cost is **0.40%**.
**Only 3 of 16 cells clear costs** (bold).

**Where the separation actually lives.** Decomposing against the universe mean:

| bucket | typical vs universe |
|---|---|
| top | +0.09% to +0.57% |
| middle | −0.03% to +0.48% (about zero at short horizons) |
| **bottom** | **−0.19% to −0.85% (consistently, every cell)** |

The signal is driven by the **bottom tercile underperforming**, not the top
outperforming. `top − middle` is positive in only 11/16 cells and is
near-zero in magnitude (often 0.00–0.03%). This is an *avoid-the-laggards*
effect far more than a *chase-the-leaders* effect.

---

## 3. Fold-by-fold (22 calendar years)

Cell **N=90, M=90** (strongest cell), forward excess %:

| year | top | mid | bot | spread |
|---|---|---|---|---|
| 2005 | 8.66 | −4.64 | 0.10 | 8.56 |
| 2006 | 2.09 | −0.43 | −0.02 | 2.11 |
| 2007 | 6.02 | 3.16 | −2.76 | 8.78 |
| 2008 | −2.02 | −1.90 | 0.32 | −2.34 |
| 2009 | 2.15 | 5.17 | 9.08 | −6.92 |
| 2010 | 2.39 | 1.49 | −1.20 | 3.59 |
| 2011 | 1.71 | 0.86 | −1.03 | 2.73 |
| 2012 | 0.74 | 1.08 | −0.81 | 1.55 |
| 2013 | 1.59 | 0.64 | −4.76 | 6.35 |
| 2014 | −0.36 | 4.66 | 2.30 | −2.66 |
| 2015 | 1.31 | −1.52 | −1.35 | 2.66 |
| 2016 | 2.59 | 1.25 | 0.62 | 1.97 |
| 2017 | −0.28 | 0.28 | 0.43 | −0.71 |
| 2018 | −2.10 | −1.87 | −3.25 | 1.15 |
| 2019 | −1.23 | −1.29 | −4.81 | 3.58 |
| 2020 | −0.69 | 5.40 | 3.58 | −4.27 |
| 2021 | 1.88 | 1.54 | 2.30 | −0.42 |
| 2022 | 1.51 | 0.24 | −1.93 | 3.45 |
| 2023 | 7.23 | 3.30 | 1.55 | 5.68 |
| 2024 | 0.41 | 0.52 | −0.32 | 0.72 |
| 2025 | 0.30 | 0.21 | 0.61 | −0.31 |
| 2026 | 0.12 | 5.92 | 3.07 | −2.95 |

folds top>0: **16/22 (72.7%)** · folds spread>0: **14/22 (63.6%)**

Fold tables for N=20/M=20, N=60/M=60, N=20/M=90, N=90/M=20 are in
`results/folds_*.csv`. Fold positivity across those cells: 63.6%, 59.1%, 77.3%, 50.0%.

**Fold-concentration test (K2):** dropping the single best fold does **not**
flip the sign in any of the 16 cells. Magnitude does fall — e.g. N=20/M=20 top
0.41→0.29 (−29%), spread 0.53→0.35 (−34%); N=90/M=90 top 1.39→1.21. So the
effect is *not* a one-year artifact, but short-horizon cells lean on the best year.
On the drift-corrected edge, fold positivity is 45.5%–68.2%, with **only 2 of 16
cells reaching the pre-registered 65% bar**.

---

## 4. Verdict against the frozen criteria

| criterion | result |
|---|---|
| **(a)** positive top and spread across majority of grid | **PASS** — 16/16 cells |
| **(b)** ≥65% of folds positive, sign survives dropping best fold | **FAIL** on fold positivity (representative cells: 63.6, 59.1, 72.7, 77.3, 50.0 — 2 of 5 clear the bar; 2/16 on the drift-corrected edge). Sign-survival sub-clause PASSES. |
| **(c)** monotonic top > middle > bottom | **FAIL** — monotonic in only 10/16 cells; `top − middle` is about zero and positive in only 11/16. Separation is top+middle vs bottom, not a rank ladder. |
| **K1** no separation | not triggered — spread positive in 16/16 |
| **K2** fold concentration | not triggered — no sign flip on dropping best fold |
| **K3** mean reversion | not triggered — bottom tercile about zero or negative in 14/16 |
| **K4** cherry-picked cells | not triggered — grid is coherent, rises monotonically in M across every row |

### H1 is INCONCLUSIVE.

Per the pre-committed interpretation rule: the full confirm set is not met
((b) and (c) both fail) and no kill criterion is cleanly triggered. That is
explicitly the "positive but fragile" case, and the rule says report it as
inconclusive and name the failing criteria. Those are **(b) fold positivity**
and **(c) monotonicity**.

**Practically, the honest reading leans negative for using this as a standalone
signal.** The effect that survives the universe-drift correction is about 0.28% per
rebalance, against an assumed 0.40% round trip. It clears costs in 3 of 16 cells,
all at M=90. A signal that is only profitable at one edge of the tested grid is
exactly the pattern the brief's REJECTED #11 warns about.

### What did hold up, and is worth carrying forward

1. **No mean reversion.** Cleanly answered, in 16/16 cells. Trailing sector
   losers do not bounce.
2. **The bottom tercile is the reliable part.** Bottom-vs-universe is negative in
   **every single cell**, and it is the largest, most consistent component. The
   defensible claim is *"sectors with weak trailing RS keep lagging"* — a
   **screen-out**, not a rank-and-buy.
3. **Longer forward windows are where anything survives costs.** M=20 is
   destroyed by costs in every cell (net −0.19% to +0.01%).

---

## 5. Limitations, stated plainly

- **Overlapping forward windows.** Monthly rebalance with M up to 90 sessions
  means observations are autocorrelated; a naive t-stat would be overstated. No
  t-stat is quoted anywhere above — fold counts and hit rates are the evidence.
- **Price, not total-return, indices.** Sector dividend-yield differences bias
  forward excess slightly against high-yield sectors. Not corrected.
- **Overlapping sector definitions.** BANK is inside FINANCIAL SERVICES; NBFC,
  HOUSING FINANCE, INSURANCE, PRIVATE BANK and PSU BANK all overlap FINANCIAL
  SERVICES; HOSPITALS sits inside HEALTHCARE. Buckets are therefore less
  independent than "27 sectors" suggests, which reduces effective breadth and can
  concentrate a tercile in one macro theme.
- **Widening cross-section.** 20–22 sectors in 2005 rising to 27 by 2021. Tercile
  width is not constant across folds.
- **The universe-drift check was post-hoc.** It was not in the pre-registration
  and was run after seeing the main grid. It is reported because it materially
  changes the reading, and it is labelled post-hoc rather than folded in silently.

---

## 6. Recommendation for next step

**Do not proceed to Layer 2 on the assumption that Layer 1 delivers a
rank-and-buy sector signal.** It does not, at the strength required.

Before any Layer 2 work, the cheap and honest move is to re-pose Layer 1 as the
claim the data actually supports and re-pre-register it:

> **H1b:** sectors in the bottom tercile of trailing RS underperform the
> equal-weight sector universe over the forward window — i.e. Layer 1 is an
> *exclusion filter*, not a selector.

That is testable with the data already cached, it matches where the separation
demonstrably lives, and it changes Layer 1's role in the stack from "pick the
strong sector" to "drop the weak ones, pass the rest down." Layers 2–4 remain
unbuilt, and no layer combination has been attempted.
