# StackFlow — H1b Pre-Registration (Layer 1 as an exclusion filter)

**Project:** StackFlow — independent of LeadFlow (no shared code, cache, or config)
**Written:** 2026-09-21
**Status at time of writing:** Part A is complete (`results/overlap_robustness.md`).
No H1b test has been run. No H1b grid, fold table, or bucket number has been observed.

Frozen once the first H1b test executes. Later changes appear only as dated addenda.

---

## 0. Disclosure: this is a SEMI-CONFIRMATORY test, not a clean one

This must be stated before the hypothesis, because it limits what a pass can mean.

H1b's primary metric — bottom-tercile forward return relative to the equal-weight
sector universe — **has already been partially observed**, in H1 and again in Part A.
Part A reported it across all 16 grid cells on all three panels. That is not a
procedural slip; the brief required Part A to run first precisely so that H1b would be
specified against the corrected panel and the corrected baseline. But the consequence
is real and must not be dressed up: **H1b cannot function as an independent
out-of-sample confirmation of the bottom-tercile effect.**

What is genuinely new in H1b, and therefore not yet observed:

1. **The ranking baseline changes.** H1 and Part A both ranked sectors by trailing RS
   **vs Nifty 500**. H1b ranks by trailing RS **vs the equal-weight sector universe
   mean**. This changes which sectors land in the bottom tercile on any given date, so
   the resulting bucket membership, fold pattern and effect sizes are *not* the Part A
   numbers and are not yet known.
2. **Panel C (23 sectors) is the pre-specified panel from the start**, rather than a
   post-hoc correction.
3. **Formal adjudication against the ≥65% fold bar**, which Part A did not perform.

**Known adverse prior, recorded before running.** Part A observed mean folds-negative of
59.7% on Panel C under Nifty-500-based ranking — **below the 65% bar this test will use**.
So H1b is expected, on current evidence, to **fail** criterion (a). It is being run at
that bar deliberately. Lowering the bar because H1 narrowly missed it would be moving the
goalpost, and the bar is therefore unchanged from H1.

---

## 1. Hypothesis

**H1b:** Sectors in the **bottom tercile of trailing relative strength, measured against
the equal-weight sector universe mean**, underperform the equal-weight sector universe
mean over the subsequent forward window of M trading sessions.

This reframes Layer 1 from a **selector** to an **exclusion filter**. It is the claim the
H1 data actually supported: no mean reversion, no one-year artifact, bottom tercile
negative in nearly every grid cell, and (per Part A) unaffected by sector overlap.

## 2. Why the baseline is the universe, not Nifty 500

H1 demonstrated that measuring against Nifty 500 conflates two distinct effects:

- genuine rank-based underperformance, and
- **equal-weight-vs-cap-weight universe drift**, which was +0.83% at M=90 and inflated
  every H1 bucket.

H1b therefore uses the equal-weight sector universe mean as the baseline on **both**
sides — for the trailing RS that forms the ranking, and for the forward return that is
judged. Correcting this post-hoc a second time is not acceptable.

## 3. Exact procedure (fixed in advance)

1. **Panel:** Panel C, the 23-sector strict non-overlapping panel from Part A
   (`cache/partition_strict.json` / `cache/panels.json`). Fixed by Part A's containment
   and excess-correlation rules, never by H1b results.
2. **Baseline** on each date `t`: `U_trail(t)` = equal-weight mean trailing return across
   all sectors with data; `U_fwd(t)` = equal-weight mean forward return across the same set.
3. On each **month-end** rebalance date `t`:
   - `trailing_RS(s) = sector_return(t−N → t) − U_trail(t)`
   - Rank descending; require **≥9 sectors** present or skip the date.
   - **Bottom tercile = EXCLUDED set.** Everything else = **PASSED THROUGH**.
4. **Forward metric:** `fwd_excess(s) = sector_return(t → t+M) − U_fwd(t)`, from closes
   strictly after `t`. Bucket value = equal-weight mean across bucket members.
5. **Grid:** N ∈ {20,40,60,90} × M ∈ {20,40,60,90} = **16 cells, all reported.** The full
   grid is run even though H1 suggested only long M cleared costs — that pattern is not
   assumed to transfer.
6. **Folds:** calendar years (~22). Every fold reported. Pooled reported alongside, never
   instead of.
7. **Look-ahead control:** ranking at `t` uses only closes ≤ `t`; forward uses only closes
   > `t`. The universe baseline is computed from the same dates as the bucket it offsets.

## 4. Output is BINARY, by design

- **Excluded:** bottom tercile of trailing RS this period.
- **Passed through:** everything else — untouched, unranked, unscored.

No continuous score or rank is built on the passed-through group in this phase. H1 found
`top − middle` near zero and positive in only 11/16 cells: there is no demonstrated
separation within the top two-thirds to rank on. If a later layer wants to rank strong
sectors, that is a separate, separately pre-registered hypothesis — not something folded
in here because the code happens to be open.

## 5. Primary metric

**Mean forward excess of the EXCLUDED (bottom-tercile) bucket vs the equal-weight
universe mean, per grid cell, broken down per calendar-year fold.**

Reported always alongside: passed-through bucket value; raw (vs Nifty 500) figures for
continuity with H1; per-fold counts; number of cells negative.

## 6. What would CONFIRM H1b

- **(a)** Excluded-bucket forward excess is negative in a **clear majority of folds** —
  **≥65%**, the same bar H1 used and missed. Unchanged deliberately.
- **(b)** The effect is **not reversed or collapsed to near-zero** by dropping the single
  most extreme (most negative) fold.
- **(c)** Magnitude is large enough to plausibly survive realistic costs once Layer 2's
  turnover is known. **Provisional and flagged, NOT a hard pass/fail gate** — see §8.

## 7. What would KILL H1b (any one sufficient)

- **KB1** — Excluded-bucket underperformance vs the universe mean is **not negative in a
  majority of folds** on Panel C.
- **KB2** — The effect **reverses sign or collapses to near-zero** when the single most
  extreme fold is dropped.
- **KB3** — The effect proves to be a **concentration artifact** on the non-overlapping
  panel. *(Part A already tested this and it did not collapse; if it had, H1b would not
  have been run at all. Retained for completeness.)*

## 8. Cost-model caveat, carried forward explicitly

The **0.40% round-trip figure used in H1 is a placeholder** standing in for eventual
stock-level trading costs. It is **not** the cost of trading a sector index: NSE sectoral
indices are not directly tradeable, and sector ETFs carry their own tracking error,
spreads and liquidity limits that this project has not modelled.

Therefore **the cost-clearance question is provisional until Layer 2 defines actual
turnover** driven by sector-exclusion-induced stock entries and exits. An exclusion
filter's true cost depends on how often a sector crosses the tercile boundary *and* on
how many stock-level trades that forces downstream — neither is known yet.

**H1b will report raw and universe-relative effect sizes regardless** of whether a cost
comparison is meaningful, and will not declare a pass or fail on cost grounds.

## 9. Pre-committed interpretation rule

- **(a) and (b)** both hold → H1b **SUPPORTED**; Layer 1 is usable as an exclusion filter,
  with (c) noted as provisional.
- **Any of KB1–KB3** → H1b **REJECTED**. Reported as rejected. No re-cutting to rescue it.
- Negative but fragile, meeting neither → **INCONCLUSIVE**, with the failing criterion named.

Given the adverse prior in §0, the most likely outcome is failure of (a). If that happens
it will be reported as a failure, not reframed.

No layer combination, weighting, or scoring occurs in this phase under any outcome.
Layers 2–4 are not built in this phase, and no Layer 2 design work follows in this
session regardless of result.

## 10. Known limitations acknowledged in advance

- **Effective breadth ~15, not 23** (Part A §A3). 22 folds × ~19 live sectors is less
  independent evidence than the raw counts imply.
- **Overlapping forward windows** (monthly rebalance, M up to 90) make observations
  autocorrelated; no t-stat will be quoted. Fold counts are the evidence.
- **Price, not total-return, indices** — dividend-yield differences bias excess returns
  slightly against high-yield sectors. Not corrected.
- **Widening cross-section** — 20→23 sectors over the period; tercile width varies by fold.
- **Panel C membership uses present-day constituent and correlation structure** applied to
  the full history. This is a universe-construction choice made with hindsight, not a
  look-ahead in the return computation, but it is hindsight and is recorded as such.

---

*(Addenda, if any, appear below this line with dates.)*

---

## ADDENDUM — 2026-09-21, appended after running H1b

Section 0 of this pre-registration claimed the ranking-baseline change was "genuinely
new" and that it would "change which sectors land in the bottom tercile on any given
date, so the resulting bucket membership, fold pattern and effect sizes are *not* the
Part A numbers and are not yet known."

**That claim is false, and it is false for a reason that could have been established by
inspection before the run rather than after it.**

On any rebalance date `t`, both candidate baselines — the equal-weight universe trailing
mean `U_trail(t)` and the Nifty 500 trailing return — are **single scalars applied
identically to every sector**. Subtracting a per-date constant from every element of a
vector cannot change that vector's rank order. Therefore:

    rank(sector_trailing - U_trail)  ==  rank(sector_trailing - nifty500_trailing)

The two rankings are identical by construction, and so are the resulting terciles.

Empirically confirmed: H1b's `excluded` column equals Part A Panel C's `bot_vs_uni`
in **16 of 16 cells, to a maximum absolute difference of 0.000e+00**.

### Consequence for how H1b may be read

H1b is **not semi-confirmatory as §0 asserted — it is fully confirmatory.** It contains
no new information whatsoever relative to Part A. It is a re-adjudication of numbers
already observed, against criteria written after those numbers were observed.

The forward-measurement baseline (excess vs universe rather than vs Nifty 500) was the
only substantive correction, and that had already been applied in `RESULTS_layer1.md` §2
and again throughout Part A.

This does not invalidate the H1b result. It does mean **no part of the H1b verdict may be
presented as independent confirmation of the bottom-tercile effect.** It is the same
evidence, formally adjudicated. Any genuine confirmation requires data not used in H1,
Part A, or H1b — e.g. a held-out period or a different market.

The §0 disclosure was directionally right that H1b was contaminated; it understated the
degree, and the understatement is recorded here rather than quietly corrected.
