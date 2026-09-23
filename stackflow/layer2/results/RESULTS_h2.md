# StackFlow Layer 2 — Results: H2 / H2b (Stock Selection Within Passed Sectors)

**Run date:** 2026-09-21
**Judged against `layer2/pre_registration.md` as frozen.**
**Verdict written after the data.**

---

## VERDICT (up front)

> **H2 (selector) is REJECTED — kill criterion KL3 triggered.**
> **H2b (filter) is NOT SUPPORTED.**
> On the clean point-in-time window, **no cell of the 12-cell grid is statistically
> distinguishable from zero** (best permutation p = 0.102), and the apparent effects
> **collapse when the single best fold is dropped** — 10 of 12 cells flip sign for the
> top tercile, and under the pre-registered sensitivity check **0 of 12** survive.

This is "not established," not "proven absent" — see the power caveat in §6, which is
real and was recorded before the run.

---

## 1. What was actually testable

| item | value |
|---|---|
| Point-in-time universe | Nifty 500 as of **2020-07-25** (the only capture that exists) |
| Mappable to Panel C sectors | 489 of 501 (TEXTILES + PAPER dropped, 12 names) |
| With retrievable prices | **433 (88.5%)** — 56 missing, listed in §7 |
| **PRIMARY clean window** | **2020-08-31 → 2026-09, 73 rebalances, 7 folds** |
| SECONDARY contaminated window | 2005 → 2020-07, 178 rebalances, 16 folds — labelled, not used for verdict |
| Median stocks per cross-section | **340** (clean) |
| Layer 1 filter | applied **genuinely point-in-time** — no contamination enters through Layer 1 |
| Reversal years (pre-registered rule) | 1999, 2002, 2003, 2004, 2006, 2007, **2009**, 2012, **2020** — only **2020** falls in the clean window |

The rule flagged 2009 and 2020 as anticipated, which is a check on the rule rather than a
result.

---

## 2. Full grid — CLEAN window, all 12 cells (nothing omitted)

`topU` / `botU` = forward excess vs the **equal-weight filtered-universe mean** (primary
baseline). `_norm` = effect ÷ cross-sectional dispersion. `p` = one-sided sign-flip
permutation on fold units.

| N | M | topU % | midU % | botU % | spread % | topU_norm | botU_norm | folds top>0 | folds bot<0 | topU ex-best | botU ex-worst | mono | p_top | p_bot |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 20 | −0.119 | −0.051 | 0.171 | −0.290 | −0.012 | 0.018 | 42.9% | 28.6% | −0.332 | 0.325 | ✗ | 0.845 | 0.919 |
| 20 | 60 | 0.063 | 0.069 | −0.132 | 0.195 | 0.004 | −0.007 | 42.9% | 57.1% | −0.199 | 0.142 | ✗ | 0.463 | 0.458 |
| 20 | 120 | 0.458 | −0.057 | −0.400 | 0.859 | 0.017 | −0.015 | 42.9% | 71.4% | −0.043 | 0.018 | ✓ | 0.290 | 0.332 |
| 60 | 20 | 0.060 | −0.130 | 0.070 | −0.010 | 0.006 | 0.007 | 57.1% | 28.6% | −0.133 | 0.238 | ✗ | 0.560 | 0.849 |
| 60 | 60 | 0.408 | −0.181 | −0.225 | 0.634 | 0.023 | −0.013 | 71.4% | 57.1% | −0.061 | 0.137 | ✓ | 0.380 | 0.396 |
| 60 | 120 | 1.016 | −0.152 | −0.863 | 1.879 | 0.037 | −0.031 | 71.4% | 71.4% | **0.173** | **−0.468** | ✓ | 0.199 | **0.102** |
| 120 | 20 | 0.075 | 0.074 | −0.150 | 0.225 | 0.008 | −0.016 | 57.1% | 57.1% | −0.160 | 0.126 | ✓ | 0.571 | 0.482 |
| 120 | 60 | 0.346 | 0.158 | −0.505 | 0.851 | 0.019 | −0.028 | 57.1% | 57.1% | −0.175 | 0.020 | ✓ | 0.441 | 0.312 |
| 120 | 120 | 1.316 | −0.026 | −1.290 | 2.606 | 0.048 | −0.047 | 57.1% | 57.1% | **0.068** | **−0.432** | ✓ | 0.244 | 0.126 |
| 250 | 20 | 0.262 | 0.039 | −0.302 | 0.564 | 0.027 | −0.031 | 57.1% | 71.4% | −0.115 | 0.051 | ✓ | 0.372 | 0.398 |
| 250 | 60 | 0.829 | 0.254 | −1.086 | 1.915 | 0.046 | −0.061 | 42.9% | 71.4% | −0.260 | **−0.093** | ✓ | 0.354 | 0.284 |
| 250 | 120 | 1.593 | 0.221 | −1.815 | 3.408 | 0.058 | −0.066 | 57.1% | 71.4% | −0.846 | **−0.045** | ✓ | 0.419 | 0.303 |

### Why the raw numbers are misleading, and normalisation matters

The largest cell (N=250, M=120) shows top +1.59%, bottom −1.82%, a 3.41% spread — which
looks substantial. **Dispersion-normalised it is 0.058 and −0.066 SD.** Cross-sectional
dispersion of forward excess runs **9.6% at M=20 to 27.5% at M=120**. The effects are a
few percent of one standard deviation of the thing being measured.

Carrying the dispersion-normalised column from day one (Layer 1 lesson 2) is what makes
this visible immediately rather than after a phase of over-interpretation.

---

## 3. Adjudication against the frozen criteria

### H2 — full selector form

| criterion | result |
|---|---|
| **(a)** top positive across majority of cells | **PASS** — 11/12 cells positive |
| **(b)** holds in ≥65% of folds (≥5 of 7) | **FAIL** — only **2/12** cells reach it; mean **54.8%** |
| **(c)** survives dropping single best fold | **FAIL** — only **2/12** cells remain positive; 10 flip negative |
| **(d)** monotonic top > middle > bottom | partial — 9/12 cells |

**KL3 is triggered** ("effect carried by 1–2 folds and reverses when the best fold is
dropped"). Per the pre-committed rule: **H2 REJECTED.**

### H2b — narrow filter form

| criterion | result |
|---|---|
| bottom negative in majority of cells | **PASS** — 10/12 |
| negative in ≥65% of folds | **FAIL** — 5/12 cells; mean **58.3%** |
| not reversed by dropping most extreme fold | **FAIL** — only **4/12** remain negative |

**H2b NOT SUPPORTED.** It is closer than H2 — the bottom tercile is negative in 10 of 12
cells and holds the best fold-consistency (71.4% in five cells) — but it fails both the
fold bar and the robustness check, and no cell is significant.

### KL4 — the universe-composition confound

**Confirmed present, and it would have been badly misleading if measured naively.**
Against Nifty 500 directly, *both* buckets show large positive excess: at M=120, top
+5.0% to +6.2% **and bottom +2.8% to +4.2%**. Both buckets cannot beat the benchmark by
that much. Two mechanical causes: stock prices are dividend-adjusted while the Nifty 500
series is a price index, and the filtered universe is equal-weighted against a cap-weighted
benchmark — the same drift that inflated two-thirds of Layer 1's original headline.

Measured against the equal-weight filtered-universe mean, as pre-registered, the effect is
what §2 shows: near zero. **Building this check into the first run (Layer 1 lesson) is the
difference between this verdict and a false positive.**

---

## 4. Pre-registered sensitivity: does the sector mapping carry the result?

Re-assigning stocks by **actual Panel C sectoral-index membership** instead of the
industry→sector majority rule (249 stocks, median 177 per cross-section):

| metric | primary (industry map) | sensitivity (membership) |
|---|---|---|
| cells top > 0 | 11/12 | 9/12 |
| cells bottom < 0 | **10/12** | **5/12** |
| cells top > 0 after dropping best fold | 2/12 | **0/12** |
| cells bottom < 0 after dropping worst fold | 4/12 | **0/12** |
| best permutation p | 0.102 | 0.566 |

**The mapping is load-bearing, and this is reported as the pre-registration required.**
H2b's one relative strength — bottom negative in 10/12 cells — **drops to 5/12** under the
faithful-membership assignment, and nothing at all survives fold-robustness. A result
that depends this much on an admittedly approximate mapping is not a result.

Note the sensitivity universe is contaminated by present-day membership, so neither
version is clean on every axis. They agree on the conclusion: nothing established.

---

## 5. Reversal-regime behaviour (built in, not discovered late)

Excluding the single reversal year in the window (2020):

| | all folds | excluding 2020 |
|---|---|---|
| mean topU across cells | 0.526% | **0.654%** |
| mean botU across cells | −0.544% | **−0.673%** |

Both sides improve by roughly 25% when the reversal year is removed — **directionally
exactly what the published evidence predicts** ("severe periodic losses when markets
rebound after enormous losses"), and consistent with Layer 1's own regime dependency.

This is suggestive, not established: removing one of seven folds is a large intervention,
and it was flagged in advance precisely so it could not be presented as a discovery.

---

## 6. The power caveat — recorded before the run, and it binds

The clean window has **7 folds**. Dropping the single best fold removes ~14% of the
evidence — a far harsher test than the same criterion applied to Layer 1's 22 folds.
Criterion (c) is therefore **more punishing here than it was for Layer 1**, and a genuine
but modest effect could plausibly fail it.

The bar was **not relaxed**, because relaxing a pre-registered criterion after seeing it
fail is the exact error this project has avoided four times now.

But the honest reading of a rejection at n=7 folds is **"not established on the clean data
available,"** not "shown to be absent." The two findings that do *not* depend on fold
count point the same way, though:

- **No cell reaches significance** (best p = 0.102) — that is a statement about the
  73 rebalances, not the 7 folds.
- **Normalised effects are 0.01–0.07 SD** — small on any sample size.

---

## 7. Limitations

- **7 folds / ~6 years** (§6). The binding constraint, and a consequence of only one
  point-in-time membership capture existing.
- **56 of 489 names (11.5%) have no retrievable price history.** Critically, these are
  dominated by **mergers and renames**, not failures — `HDFC`, `LTI`, `MINDTREE`,
  `MOTHERSUMI`, `MCDOWELL-N`, `SRTRANSFIN`, `CADILAHC`, `INFRATEL`, `PEL`, `GMRINFRA` —
  so the gap is *not* primarily survivorship of distressed names. Some genuine distress
  cases are present (`SPICEJET`, `IBREALEST`, `IBULHSGFIN`). Names listed in
  `cache/pit_stock_coverage.csv`.
- **Industry→sector mapping is approximate and load-bearing** (§4). The majority rule
  also under-excludes large industries: SERVICES passes 94.7% of months and FINANCIAL
  SERVICES (87 stocks, 18% of the universe) 84.0%, versus 65–75% for single-mapped
  industries. Overall 12.4 of 17 industries pass per month (73%), close to Layer 1's
  two-thirds, so aggregate strength is about right but applied unevenly.
- **Dividend/price-index mismatch** inflates all vs-Nifty-500 figures (§3, KL4). Those
  columns are reported for continuity only and are not used for any verdict.
- **No skip month**, as pre-registered — short-term reversal is a live confound at N=20
  specifically, and N=20 is indeed the weakest row (topU negative at M=20).
- **Overlapping forward windows** at M=60/120. No t-statistic is quoted anywhere;
  fold-unit permutation tests are used instead.
- **No cost model**, consistent with Layer 1's frozen-config caveat. Costs would only
  worsen a result that is already not distinguishable from zero.

### Secondary contaminated window — reported, not used

2005 → 2020-07, 16 folds: top positive in 10/12 cells, **9/12 surviving the best-fold
drop**, mean fold-positivity 65.6%, and one cell reaching **p = 0.009**. It looks
**materially better than the clean window**.

That is exactly what contamination predicts — the universe is 2020's Nifty 500 members
applied backwards, so the sample is pre-selected for stocks that grew into the index. It
is recorded here because suppressing a favourable-looking result would be as dishonest as
promoting it, and it **does not change the verdict**.

---

## 8. Recommendation

**Do not carry a stock-level relative-strength selector into Layer 3 on this evidence, and
do not treat H2b as a validated filter either.**

What the data supports is narrow: the bottom tercile is negative in 10 of 12 cells on the
primary mapping, with the best fold-consistency in the grid — a *hint* in the same
direction Layer 1 landed (filter, not selector). It fails robustness, fails the fold bar,
is not significant, and halves under the sensitivity check.

Three things, in order, none of them in this session:

1. **The binding constraint is data, not method.** Everything here is limited by one
   point-in-time membership capture. A paid point-in-time constituent source (or NSE index
   change circulars reconstructed systematically) would extend the clean window from 7
   folds to ~20 and is worth more than any further modelling. **This is the single highest
   -value next step.**
2. **Do not test drawdown-conditional RS as a rescue.** It was deliberately excluded from
   this phase's pre-registration. Running it now, after a null, and reporting it if it
   looks better would be the exact selection effect this project has guarded against
   throughout. If it is tested, it gets its own pre-registration and its own clean window.
3. **Revisit the sector mapping before re-testing.** §4 shows it is load-bearing. Resolving
   financials properly — rather than by majority rule over five sub-sectors — is a
   prerequisite for any re-run being informative.

**Against the §10 upper-bound prior:** the published study's "loser portfolios persistently
underperform" was treated as an upper bound, not an expectation. The clean-window result
came in **well below** it. That is the outcome the prior was written to make legible, and
it is being reported as such rather than explained away.

---

*Layer 3 (fundamentals) has not been started. Layer 1 remains frozen and untouched.*
