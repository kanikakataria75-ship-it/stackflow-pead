# StackFlow H1b — Results: Sector Exclusion Filter

**Run date:** 2026-09-21
**Panel:** C — 23-sector strict non-overlapping (Part A)
**Verdict written after the data, judged against `pre_registration_h1b.md` as frozen.**

---

## 0. Read this before the numbers: H1b is fully confirmatory

The pre-registration (§0) claimed the change of ranking baseline — from Nifty 500 to the
equal-weight universe mean — was "genuinely new" and would change tercile membership.
**That was wrong.**

On any date `t`, both baselines are **single scalars subtracted from every sector alike**.
Subtracting a per-date constant from a vector cannot change its rank order:

```
rank(trailing − U_trail)  ≡  rank(trailing − nifty500_trailing)
```

The terciles are identical by construction. Confirmed empirically: H1b's `excluded`
column equals Part A Panel C's `bot_vs_uni` in **16/16 cells, max absolute difference
0.000e+00**.

**So H1b contains no new information relative to Part A.** It is a formal adjudication of
numbers already observed, against criteria written after they were observed. The result
below is real, but **nothing in it may be read as independent confirmation.** Genuine
confirmation requires data not used in H1, Part A, or H1b — a held-out period or another
market. This is recorded as an addendum in the pre-registration rather than quietly fixed.

The one substantive correction the brief asked for — measuring *forward* returns against
the universe rather than Nifty 500 — was real, but had already been applied in
`RESULTS_layer1.md` §2 and throughout Part A.

---

## 1. Full grid — all 16 cells

23-sector panel, median 19 sectors live per rebalance, 249–255 rebalances per cell,
22 calendar-year folds. `excluded` and `passed` are vs the equal-weight universe mean.

| N | M | excluded % | passed % | gap % | folds excl<0 | excl ex-worst-fold % | obs hit % |
|---|---|---|---|---|---|---|---|
| 20 | 20 | −0.243 | 0.114 | 0.357 | 54.5% | −0.170 | 56.5 |
| 20 | 40 | −0.467 | 0.220 | 0.687 | 54.5% | −0.303 | 56.3 |
| 20 | 60 | −0.562 | 0.261 | 0.824 | **68.2%** | −0.331 | 56.9 |
| 20 | 90 | −0.974 | 0.443 | 1.417 | **72.7%** | −0.802 | 61.5 |
| 40 | 20 | −0.186 | 0.085 | 0.271 | 54.5% | −0.071 | 54.5 |
| 40 | 40 | −0.407 | 0.181 | 0.588 | **68.2%** | −0.228 | 55.9 |
| 40 | 60 | −0.456 | 0.202 | 0.658 | 50.0% | −0.210 | 56.1 |
| 40 | 90 | −0.609 | 0.266 | 0.876 | 54.5% | −0.397 | 58.7 |
| 60 | 20 | −0.196 | 0.090 | 0.286 | 54.5% | −0.114 | 53.9 |
| 60 | 40 | −0.406 | 0.182 | 0.588 | 59.1% | −0.273 | 56.9 |
| 60 | 60 | −0.418 | 0.184 | 0.602 | 50.0% | −0.256 | 55.2 |
| 60 | 90 | −0.626 | 0.275 | 0.901 | 59.1% | −0.450 | 59.0 |
| 90 | 20 | −0.201 | 0.090 | 0.291 | 54.5% | −0.094 | 54.4 |
| 90 | 40 | −0.311 | 0.137 | 0.448 | 63.6% | −0.169 | 53.0 |
| 90 | 60 | −0.441 | 0.196 | 0.637 | 63.6% | −0.243 | 54.8 |
| 90 | 90 | −0.845 | 0.376 | 1.221 | **72.7%** | −0.620 | 61.0 |

**EXCLUDED bucket vs universe (%)** — negative means the filter works

| N \ M | 20 | 40 | 60 | 90 |
|---|---|---|---|---|
| **20** | −0.243 | −0.467 | −0.562 | −0.974 |
| **40** | −0.186 | −0.407 | −0.456 | −0.609 |
| **60** | −0.196 | −0.406 | −0.418 | −0.626 |
| **90** | −0.201 | −0.311 | −0.441 | −0.845 |

**Folds with excluded < 0 (%)** — pre-registered bar is 65%

| N \ M | 20 | 40 | 60 | 90 |
|---|---|---|---|---|
| **20** | 54.5 | 54.5 | **68.2** | **72.7** |
| **40** | 54.5 | **68.2** | 50.0 | 54.5 |
| **60** | 54.5 | 59.1 | 50.0 | 59.1 |
| **90** | 54.5 | 63.6 | 63.6 | **72.7** |

Headline figures: **16/16 cells negative**, mean **−0.459%**, mean folds-negative
**59.7%**, cells clearing the 65% bar **4/16**, cells still negative after dropping the
worst fold **16/16**.

### The asymmetry that matters

`passed` is always the mirror of `excluded` with opposite sign and smaller magnitude —
mechanically so, since the two buckets are complements around the universe mean and the
excluded bucket is the smaller one (≈6 of 19 sectors). Excluding the bottom tercile
lifts the remainder by only **+0.09% to +0.44%**, against the excluded bucket's
**−0.19% to −0.97%** drag. **The filter's benefit to what survives it is roughly a third
of the damage it avoids**, because the pain is concentrated in a third of the universe
while the benefit is spread across the other two-thirds.

## 2. Fold-by-fold, representative cells

**N=20, M=20** — excluded<0 in 12/22 (54.5%)

| year | excluded | passed | | year | excluded | passed |
|---|---|---|---|---|---|---|
| 2005 | −0.17 | 0.07 | | 2016 | −0.50 | 0.23 |
| 2006 | −0.92 | 0.46 | | 2017 | **0.60** | −0.28 |
| 2007 | −1.45 | 0.67 | | 2018 | **0.31** | −0.14 |
| 2008 | **0.41** | −0.19 | | 2019 | **1.15** | −0.51 |
| 2009 | −1.54 | 0.71 | | 2020 | **0.44** | −0.19 |
| 2010 | −1.14 | 0.53 | | 2021 | **0.75** | −0.32 |
| 2011 | **0.23** | −0.11 | | 2022 | **0.08** | −0.03 |
| 2012 | **0.19** | −0.09 | | 2023 | −0.24 | 0.10 |
| 2013 | −0.90 | 0.41 | | 2024 | −0.57 | 0.25 |
| 2014 | −0.78 | 0.36 | | 2025 | −0.90 | 0.39 |
| 2015 | −0.42 | 0.19 | | 2026 | **0.23** | −0.10 |

**N=60, M=60** — excluded<0 in 11/22 (50.0%)

Notable: the effect is very large in 2007 (−3.06), 2008 (−2.93), 2022 (−2.17),
2023 (−2.53) and clearly wrong-signed in 2014 (+1.70), 2009 (+1.01), 2019 (+0.95).

**N=20, M=90** — excluded<0 in 16/22 (72.7%), the strongest cell family.

Full tables: `results/h1b_folds_*.csv`, per-rebalance detail in `results/h1b_cell_*.csv`.

### The pattern in the failures is not random

Wrong-signed folds cluster in **sharp-reversal years: 2009, 2014, 2019, 2020, 2021** —
V-shaped recoveries and violent leadership rotations, where the prior period's laggards
lead the bounce. Right-signed folds cluster in **trending or crisis-continuation years:
2006–2008, 2010, 2013, 2022–2023**. The filter is not merely noisy; it has a
**regime dependency**, and it fails precisely when a portfolio most needs it — at
major turns. That is a materially worse property than a uniformly weak edge.

## 3. Verdict against the frozen criteria

| criterion | result |
|---|---|
| **(a)** excluded<0 in ≥65% of folds | **FAIL** — mean 59.7%; only **4/16** cells clear the bar; two cells sit at exactly 50.0% |
| **(b)** not reversed/collapsed by dropping the single worst fold | **PASS** — negative in **16/16** cells ex-worst-fold (−0.071% to −0.802%); magnitude roughly halves at short M but never flips |
| **(c)** magnitude plausibly survives costs | **PROVISIONAL, not a gate** — see §4 |
| **KB1** not negative in a majority of folds | **not triggered** — negative in a majority in 14/16 cells (2 tied at 50%) |
| **KB2** sign reversal / collapse on worst-fold removal | **not triggered** |
| **KB3** concentration artifact | **not triggered** — Part A showed the effect is identical across 27/24/23-sector panels |

### H1b is INCONCLUSIVE.

Per the pre-committed rule: criterion (a) fails, (b) passes, no kill criterion triggers.
That is the "negative but fragile" case, and the rule requires reporting it as
inconclusive with the failing criterion named. The failing criterion is
**(a), fold consistency**.

The adverse prior recorded in the pre-registration before running (59.7% observed in
Part A, below the 65% bar) was **exactly correct** — necessarily so, given §0.

**The honest reading:** the effect is real in sign and remarkably stable in *magnitude*
across every specification tried — 16/16 cells negative on three different panels, and
16/16 still negative after removing the worst year. What it is not is **reliable
year-to-year**: it works in about 6 years out of 10, and it fails in a recognisable and
unfortunate pattern (sharp reversals).

## 4. Costs — why no pass/fail is declared

The **0.40% round-trip figure from H1 is a placeholder** for eventual stock-level costs.
It is **not** the cost of trading a sector index: NSE sectoral indices are not directly
tradeable, and sector ETFs carry tracking error, spreads and liquidity limits this
project has not modelled.

An exclusion filter's real cost depends on how often a sector crosses the tercile
boundary **and** how many stock-level entries and exits that forces downstream — neither
is known until Layer 2 exists. Effect sizes are therefore reported raw and
universe-relative, and **no cost-based verdict is issued.**

For scale only, not as a verdict: the excluded bucket's drag is −0.19% to −0.97%, and the
benefit conferred on the passed-through group is only **+0.09% to +0.44%**. It is that
smaller number a cost model would eventually have to beat.

## 5. Limitations

- **Fully confirmatory** (§0). No independent evidential value beyond Part A.
- **Effective breadth ≈15, not 23** (Part A §A3). 22 folds × ~19 sectors is much less
  independent evidence than the counts suggest.
- **Overlapping forward windows** — monthly rebalance with M up to 90 sessions makes
  observations autocorrelated. No t-stat is quoted anywhere; fold counts are the evidence.
- **Price, not total-return, indices** — dividend-yield differences bias excess returns
  slightly against high-yield sectors. Not corrected.
- **Panel C uses present-day constituent and correlation structure** applied to the full
  history. Hindsight in universe construction, not look-ahead in return computation, but
  hindsight nonetheless.
- **Widening cross-section** — 20→23 sectors over the period; tercile width varies by fold.
- **Regime dependency is a characterisation, not a tested hypothesis.** The clustering of
  failures in reversal years was observed after the fact and is not pre-registered. It
  should be treated as a lead to test, not a finding.

## 6. Recommendation

**Do not adopt H1b as a gating filter in Layer 2 on this evidence.** It fails its own
pre-registered consistency bar at 59.7% against 65%, and that bar was deliberately not
relaxed after H1 missed it.

**Do not discard it either.** The sign stability is genuinely unusual: 16/16 cells across
three panels, surviving worst-fold removal in all of them. Something real is being
measured — it is just not dependable enough, year to year, to gate a portfolio on.

Three things worth doing, in order, none of them in this session:

1. **Get genuinely independent evidence.** Everything so far is one dataset, adjudicated
   three times. A held-out period (e.g. pre-2010 vs post-2010) or another market would
   for the first time actually test the effect rather than re-measure it.
2. **Test the regime dependency properly.** Pre-register the reversal-year pattern from
   §2 as its own hypothesis. If the filter's failures are predictable from market state,
   that is more useful than the filter itself; if they are not, the pattern was noise.
3. **Treat it as a soft input, not a gate.** If it enters Layer 2 at all, it should carry
   information rather than veto power — a ~60% year-to-year hit rate does not justify
   hard-excluding a third of the universe.

**Layer 1 is not settled, and Layers 2–4 remain unbuilt.** No layer combination,
weighting, or scoring has been attempted, and no Layer 2 design work follows in this
session.
