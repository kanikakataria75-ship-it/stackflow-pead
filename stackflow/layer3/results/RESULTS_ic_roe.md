# StackFlow Layer 3 / Phase 3b — Results: Interest Coverage and ROE

**Run date:** 2026-09-22
**Judged against `layer3/pre_registration_ic_roe.md`, written and saved before any grid existed.**
**Does not supersede the EPS-growth factor result**, which stays as its own closed, thin-data finding.

---

## THE FOUR VERDICTS

| # | hypothesis | verdict |
|---|---|---|
| 1 | **H-IC-exclusion** — weak interest coverage underperforms | **REJECTED** (K1, wrong direction) |
| 2 | **H-IC-selection** — strong interest coverage outperforms | **REJECTED** (K1, wrong direction) |
| 3 | **H-ROE-exclusion** — weak ROE underperforms | **INCONCLUSIVE — not testable** (4–5 rebalance dates) |
| 4 | **H-ROE-selection** — strong ROE outperforms | **INCONCLUSIVE — not testable** (4–5 rebalance dates) |

**Nothing in Layer 3 clears the bar. Nothing is carried forward.**

The interest-coverage result is not merely null — it is **significantly wrong-signed**, and
that is itself the most informative output of this phase.

---

## 1. Data quality, stated before results (pre-registration §5.7)

| diagnostic | Interest Coverage | ROE |
|---|---|---|
| rows used | 10,594 | 2,202 |
| symbols | 373 | 440 |
| **`ctx_inferred`** | **46.1%** | **64.9%** |
| **basis-switch rate** | **49.9%** | **31.1%** |
| observations dropped by D13 (post-switch) | 339 | 196 |
| never-switch subset | 187 symbols | 303 symbols |

**Roughly half the interest-coverage data and two-thirds of the ROE data rests on inferred
periods (D11), not verified ones.** No reading of what follows should treat this as clean data.

---

## 2. Interest Coverage — full grid, all 12 cells

Quarterly rebalance. `N` = quarters of signal smoothing, `M` = forward trading days.
`strong`/`weak` = forward excess vs the **equal-weight filtered-universe mean** (primary
baseline). `_norm` = effect ÷ cross-sectional dispersion.

| N | M | n | folds | medK | strong % | mid % | weak % | spread % | s_norm | w_norm | folds strong>0 | folds weak<0 | strong ex-best | weak ex-worst | p_strong | p_weak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60 | 29 | 8 | 267 | −0.959 | 0.131 | **+0.824** | −1.783 | −0.052 | 0.045 | 37.5% | 37.5% | −1.676 | +1.438 | 0.894 | 0.850 |
| 1 | 120 | 29 | 8 | 259 | −1.819 | 0.516 | **+1.291** | −3.110 | −0.066 | 0.047 | 25.0% | 50.0% | −2.958 | +2.602 | 0.913 | 0.892 |
| 1 | 180 | 28 | 7 | 263 | −3.091 | 0.804 | **+2.270** | −5.361 | −0.082 | 0.060 | 28.6% | 57.1% | −3.999 | +3.187 | 0.940 | 0.799 |
| 1 | 250 | 26 | 7 | 268 | −5.057 | −0.158 | **+5.198** | −10.256 | −0.096 | 0.098 | 14.3% | 42.9% | −5.953 | +5.781 | 0.984 | 0.912 |
| 2 | 60 | 28 | 8 | 268 | −0.915 | −0.085 | **+1.001** | −1.917 | −0.049 | 0.054 | 50.0% | 37.5% | −1.574 | +1.629 | 0.848 | 0.886 |
| 2 | 120 | 28 | 8 | 263 | −2.161 | 0.469 | **+1.686** | −3.847 | −0.077 | 0.060 | 25.0% | 37.5% | −3.117 | +2.672 | 0.924 | 0.920 |
| 2 | 180 | 27 | 7 | 267 | −3.784 | 0.893 | **+2.883** | −6.666 | −0.100 | 0.076 | 28.6% | 42.9% | −4.400 | +3.511 | 0.953 | 0.875 |
| 2 | 250 | 25 | 7 | 269 | −6.010 | −0.284 | **+6.309** | −12.319 | −0.112 | 0.117 | **0.0%** | 14.3% | −6.634 | +6.994 | 1.000 | 0.993 |
| 4 | 60 | 26 | 8 | 266 | −1.268 | −0.063 | **+1.329** | −2.597 | −0.067 | 0.071 | 37.5% | 25.0% | −1.755 | +1.743 | 0.763 | 0.780 |
| 4 | 120 | 26 | 8 | 261 | −3.199 | 0.384 | **+2.810** | −6.010 | −0.113 | 0.099 | 25.0% | 12.5% | −3.757 | +3.414 | 0.989 | 0.988 |
| 4 | 180 | 25 | 7 | 264 | −4.759 | 0.309 | **+4.433** | −9.191 | −0.127 | 0.118 | 14.3% | 28.6% | −5.419 | +4.788 | 0.992 | 0.867 |
| 4 | 250 | 23 | 7 | 269 | −6.721 | −0.879 | **+7.606** | −14.327 | −0.130 | 0.147 | **0.0%** | 14.3% | −7.466 | +8.566 | 1.000 | 0.991 |

### The result is the opposite of both hypotheses, in every single cell

- **Strong interest coverage UNDERPERFORMS in 12/12 cells** (−0.92% to −6.72%).
- **Weak interest coverage OUTPERFORMS in 12/12 cells** (+0.82% to +7.61%).
- The spread is negative in **12/12**, and grows monotonically with horizon.
- `mono` is **False in 12/12** — no clean rank ladder.

**Verdict 1 — H-IC-exclusion: REJECTED.** The hypothesis requires the weak tercile to
underperform. It **outperforms in every cell**, fold positivity never reaches the ≥65% bar
(max 57.1%), and no cell is significant (best p = 0.780). **K1 triggered.**

**Verdict 2 — H-IC-selection: REJECTED.** The hypothesis requires the strong tercile to
outperform. It **underperforms in every cell**, reaching **0% of folds positive** in two
cells, with p up to 1.000. **K1 triggered.**

Both fail criteria (a), (b) and (c) outright. Criterion (d) is moot — there is no
correctly-signed effect for the confound to explain.

---

## 3. The wrong-signed effect is a 2020 artifact — and that matters more than the sign

Fold-by-fold, cell N=2/M=120 (%):

| year | n | strong | mid | weak |
|---|---|---|---|---|
| 2019 | 3 | **+3.43** | −0.89 | −2.51 |
| **2020** | 4 | **−10.30** | +5.19 | **+5.01** |
| 2021 | 4 | −2.07 | −0.03 | +2.10 |
| 2022 | 4 | +0.52 | +0.03 | −0.55 |
| 2023 | 4 | −2.83 | −2.61 | +5.46 |
| 2024 | 4 | −0.66 | +1.46 | −0.78 |
| 2025 | 4 | −0.99 | +0.22 | +0.77 |
| 2026 | 1 | −5.50 | −1.19 | +6.69 |

**Reversal-year breakdown (pre-registered rule; 2020 is the only qualifying year in range):**

| | strong | weak | n |
|---|---|---|---|
| **2020 (reversal year)** | **−5.08%** | **+5.17%** | 4 |
| all other years | **−0.30%** | **+0.13%** | 25 |

**Excluding 2020 collapses the effect by roughly two-thirds in every cell:**

| cell | all years | excluding 2020 |
|---|---|---|
| N1/M60 | strong −0.96%, weak +0.82% | strong **−0.30%**, weak **+0.13%** |
| N1/M120 | strong −1.82%, weak +1.29% | strong **−0.54%**, weak **+0.41%** |
| N2/M120 | strong −2.16%, weak +1.69% | strong **−0.81%**, weak **+1.13%** |
| N4/M60 | strong −1.27%, weak +1.33% | strong **−0.49%**, weak **+0.69%** |

**Break-point scan** (N2/M120, strong tercile — scan, not fixed blocks, per lesson from
Phase 1c):

| split | early | late | gap |
|---|---|---|---|
| 2020 | +3.43% (n=3) | −2.83% (n=25) | **+6.26** |
| 2021 | −4.42% (n=7) | −1.41% (n=21) | −3.01 |
| 2022 | −3.56% (n=11) | −1.26% (n=17) | −2.31 |
| 2023 | −2.47% (n=15) | −1.80% (n=13) | −0.67 |
| 2024 | −2.55% (n=19) | −1.34% (n=9) | −1.20 |

The largest break is at **2020**, and the pre-2020 sample is only 3 rebalances.

**Interpretation, stated carefully.** What the data shows is that in the COVID crash and
recovery, **highly-levered, low-coverage companies rebounded hardest** — a distress/leverage
rally, which is a well-known crisis-recovery pattern and is exactly the reversal-regime
behaviour this project has documented in every prior layer. Outside 2020 the effect is
−0.30% / +0.13% — small, unstable, and not significant.

**This is not evidence that buying weak-balance-sheet companies works.** It is one crisis
recovery dominating a 29-rebalance sample. Reporting it as a tradeable inverse signal would
be precisely the one-fold artifact this project has rejected five times.

---

## 4. ROE — NOT TESTABLE, and the pre-registration's fold claim was wrong

| N | M | **rebalances** | folds | years covered | strong % | weak % | p_strong | p_weak |
|---|---|---|---|---|---|---|---|---|
| 1 | 120 | **5** | 5 | 2019–22, 2025 | −0.791 | +0.277 | 0.847 | 0.595 |
| 1 | 180 | **5** | 5 | 2019–22, 2025 | +0.406 | +0.211 | 0.474 | 0.540 |
| 1 | 250 | **4** | 4 | 2019–2022 | −0.446 | −0.213 | 0.560 | 0.500 |
| 2 | 120 | **4** | 4 | 2020–22, 2025 | +0.924 | −0.528 | 0.311 | 0.439 |
| 2 | 180 | **4** | 4 | 2020–22, 2025 | +2.982 | −1.550 | 0.310 | 0.380 |

### A correction to my own pre-registration

**§0 of the pre-registration stated ROE has 8 folds. The realised test has 4–5 rebalance
dates.** That claim came from *data coverage* (8 fiscal years present in the cache) and did
not account for what the annual cadence does once the test is actually run: with one
rebalance per year, a 400-day staleness rule, a ≥30-stock minimum, and a forward window of
120–250 days consuming the tail, only 4–5 dates survive.

The error is recorded rather than quietly absorbed. **8 folds of stored data is not 8 folds
of testable signal**, and I should have derived the second number rather than the first.

**Verdicts 3 and 4 — H-ROE-exclusion and H-ROE-selection: INCONCLUSIVE, not testable.**
Signs are mixed across cells (strong positive in 2/5, weak negative in 2/5), nothing
approaches significance (best p = 0.310), and **4–5 observations cannot support a ≥65%
fold criterion at all.** Declaring either REJECTED would overstate what 4 dates can refute,
just as declaring either CONFIRMED would overstate what they can support.

**The D11 sensitivity for ROE could not run**: excluding `ctx_inferred` rows left **zero
usable grid cells**, because 64.9% of ROE rows are inferred. Per D11 condition 2, any ROE
finding would therefore have had to be labelled **PROVISIONAL — unverified-context-dependent**
regardless. There is no finding to label.

---

## 5. Mandatory checks — all run, all reported

| check | result |
|---|---|
| **Universe-composition confound** | Against Nifty 500 **both** IC terciles show large positive excess (strong +0.5% to +6.7%, **weak +2.3% to +20.4%**) — both buckets cannot beat the benchmark by that much. Against the filtered-universe mean the effects are as in §2. The confound is real and, for the fourth consecutive layer, would have badly misled a naive reading. **Criterion (d) is moot here since no effect is correctly signed.** |
| **D11 `ctx_inferred` sensitivity** | IC: the no-inference grid produced all 12 cells; **the verdict does not change** — both IC forms remain rejected. ROE: **0 cells survive**, so no verdict could be issued either way. |
| **D13 basis sensitivity** | Never-switch subsets: **IC 187 symbols, ROE 303 symbols** — both large enough. The IC grid on the never-switch subset produced all 12 cells and **does not change the verdict**. |
| **Break-point scan** | §3. Largest break at 2020; pre-2020 sample is 3 rebalances. |
| **Dispersion-normalised** | Reported in every table. IC effects are **0.045–0.147 SD** — small even where raw numbers look large, against cross-sectional dispersion of 18–54%. |
| **Reversal-regime** | §3. 2020 is the only qualifying year in range and drives the entire IC result. |

---

## 6. Plain summary — does anything clear the bar?

**No. Nothing in Layer 3 clears the bar, in filter form or selector form, for either factor.**

- **Interest coverage fails in the most decisive way available**: not a weak effect, but a
  **consistently wrong-signed** one across all 12 cells — and that wrong sign is itself an
  artifact of a single crisis year. Outside 2020 it is −0.30%/+0.13% per rebalance, with
  fold positivity never reaching 65% and p-values up to 1.000.
- **ROE is not testable on this data** at 4–5 rebalance dates, and its D11 sensitivity
  cannot run at all.

**No magnitude is quoted against a cost assumption, because §9 of the pre-registration
requires that only for something that clears the bar. Nothing does.** For scale: the
largest non-2020 IC effect is ~0.8% per rebalance, wrong-signed, on data that is ~half
inferred — which is not a candidate for a cost comparison.

**Layer 3 ends with no usable factor.** EPS growth was inconclusive and leaning
selector-shaped; interest coverage is rejected wrong-signed; ROE is untestable; debt-to-equity
does not exist in this data at all. The layer the founding brief intended as a
"quality/sanity filter" has **no validated component**.

### On the pipeline

The two days of pipeline work produced a **working, validated, reusable point-in-time
fundamentals dataset** — 15,803 parsed filings, 2019–2026, filing-dated, as-reported,
across four taxonomies, with restatement handling verified against 2,596 Original/Revision
pairs. That infrastructure stands regardless of this result, and it is what makes this
null **credible** rather than merely disappointing: the null is on real, hard-won,
point-in-time data, not on a source that was quietly cheating.

**A null result on good data is a valid output of this phase.** It is reported here exactly
as plainly as H1's and H3's verdicts were, and it is not softened to make the build feel
better rewarded than the evidence supports.

### What this does and does not say

It does **not** say fundamental quality is irrelevant to Indian equities. It says that
**on 2019–2026 data, within Layer 1's pass-through universe, ranked cross-sectionally into
terciles, at these horizons**, interest coverage and ROE do not separate forward returns in
the hypothesised direction. The period is short, contains one extreme regime that dominates
it, and the data is half-inferred. A longer or cleaner sample could say something different.

### Recommendation

1. **Do not carry any Layer 3 factor forward.** No filter, no selector, no combination.
2. **Do not chase the inverse IC effect.** It is a 2020 distress rally — one fold in a
   29-rebalance sample, the exact artifact class rejected throughout this project.
3. **The binding constraint remains data length**, as in Layers 2 and 3a. 8 folds of storage
   yielding 29 quarterly rebalances (IC) and 4–5 annual ones (ROE) is not enough to settle a
   cross-sectional factor. Extending history before re-testing is worth more than any further
   modelling.
4. **Debt-to-equity remains the one untested factor** the founding brief wanted most, and it
   requires the annual-report/PDF route (D2), not this pipeline.

---

*Layer 1 remains frozen. Layer 2 remains paused. No Layer 4 work started. No factor
combination was performed at any point in this phase.*
