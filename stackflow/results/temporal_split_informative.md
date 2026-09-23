# Temporal Split — INFORMATIVE ONLY, NOT OUT-OF-SAMPLE

**Run date:** 2026-09-21
**Configuration:** the frozen Layer 1 config (`live_config_layer1.md`), locked before any
number in this document was generated.

---

## ⚠️ What this is, and what it is not

**This is NOT a held-out test. It carries no validation weight.**

Fold-by-fold results for the **entire** 2005–2026 period were already reported and read
in `RESULTS_layer1.md` §3 and `RESULTS_h1b.md` §2. Both halves of this split — including
every year of the "late" half — have already been seen. Splitting already-seen data at a
chronological point does not make the later portion out-of-sample; it only rearranges
evidence that has already influenced the choices made in Phases 1 and 1b.

Concretely, the panel and the N/M cell frozen in Part A were chosen using knowledge of
outcomes across the whole period, this later half included. Sign agreement between halves
therefore **cannot** be read as confirmation, and will not be read that way below.

**The only genuinely unseen evidence this project will ever have starts with Part C's
forward record, from 2026-09-21 onward.**

Why run this at all: a *disagreement* between halves would be a real and useful warning,
even though agreement would prove nothing. This is an asymmetric diagnostic — it can
raise a concern, it cannot retire one.

---

## 1. Split point, fixed before any numbers were seen

**Split at 2016-01-01.** Reason, stated in advance and independent of results: it divides
the 22 calendar-year folds almost exactly in half — **2005–2015 = 11 folds**,
**2016–2026 = 11 folds** — with near-equal rebalance counts (128 vs 124). Purely
arithmetic and structural. No regime-boundary judgement, no alignment to any known good
or bad period for the strategy.

*Boundary note:* rebalances are assigned by rebalance date. With M=90, a late-2015
rebalance's forward window extends into early 2016. This affects at most 3–4 observations
and is not material to figures of this size.

---

## 2. Result — frozen cell N=20 / M=90, Panel C

Bottom-tercile forward excess vs equal-weight universe mean. Negative = filter worked.

| | rebalances | folds | **mean** | median fold | folds negative | obs negative |
|---|---|---|---|---|---|---|
| **FULL 2005–2026** | 252 | 22 | **−0.974%** | −0.985% | 16/22 (72.7%) | 61.5% |
| **EARLY 2005–2015** | 128 | 11 | **−1.550%** | −1.645% | 9/11 (**81.8%**) | 61.7% |
| **LATE 2016–2026** | 124 | 11 | **−0.380%** | −0.382% | 7/11 (**63.6%**) | 61.3% |

Passed-through bucket: early **+0.711%**, late **+0.166%**.

**Sign holds in both halves. Magnitude does not — the late half is roughly 4× weaker,
and fold consistency falls from 81.8% to 63.6%, dropping back below the 65% bar.**

### Fold detail

| year | half | excluded % | | year | half | excluded % |
|---|---|---|---|---|---|---|
| 2005 | EARLY | −1.94 | | 2016 | LATE | −0.80 |
| 2006 | EARLY | −0.19 | | 2017 | LATE | −0.15 |
| 2007 | EARLY | −4.02 | | 2018 | LATE | −1.04 |
| 2008 | EARLY | −2.80 | | 2019 | LATE | **+1.34** |
| 2009 | EARLY | −1.64 | | 2020 | LATE | **+0.18** |
| 2010 | EARLY | −2.15 | | 2021 | LATE | −0.38 |
| 2011 | EARLY | −1.10 | | 2022 | LATE | −1.45 |
| 2012 | EARLY | **+0.67** | | 2023 | LATE | −1.78 |
| 2013 | EARLY | −3.16 | | 2024 | LATE | **+1.04** |
| 2014 | EARLY | **+0.10** | | 2025 | LATE | −1.02 |
| 2015 | EARLY | −0.95 | | 2026 | LATE | **+0.38** |

Wrong-signed folds: 2 of 11 early, **4 of 11 late**.

Dropping each half's most-positive fold: early −1.550% → **−1.785%**;
late −0.380% → **−0.502%**. Neither half reverses.

---

## 3. Is the decay just a calmer market?

A smaller effect would be unremarkable if sector returns had simply become less dispersed
— the same signal strength in a tighter cross-section produces smaller absolute numbers.
Tested directly:

| | mean cross-sectional dispersion of forward excess | raw effect |
|---|---|---|
| early 2005–2015 | 12.06% | −1.550% |
| late 2016–2026 | 10.07% | −0.380% |
| **ratio early/late** | **1.20×** | **4.08×** |

**Dispersion fell 1.20×. The effect fell 4.08×.** Normalising the effect by
cross-sectional dispersion:

| | effect / cross-sectional sd |
|---|---|
| early | **−0.142** |
| late | **−0.042** |
| ratio | **3.37×** |

**The decay is not explained by a calmer cross-section.** After normalising for
dispersion the effect is still roughly **one third** of its early-period strength.

### Five-year blocks — the decay is a step, not a drift

| block | n | median live sectors | effect % | dispersion % | **normalised** |
|---|---|---|---|---|---|
| 2005–09 | 56 | 19 | −2.133 | 15.09 | **−0.134** |
| 2010–14 | 60 | 19 | −1.125 | 10.07 | **−0.150** |
| 2015–19 | 60 | 19 | −0.320 | 9.13 | **−0.050** |
| 2020–26 | 76 | 23 | −0.519 | 10.47 | **−0.052** |

Normalised strength is flat and strong across 2005–2014 (−0.134, −0.150), then **steps
down by roughly two-thirds and stays there** (−0.050, −0.052). It is not a gradual fade
and it is not a single bad block — the post-2015 level is stable at about a third of the
pre-2015 level, across two independent blocks and 136 rebalances.

The median live sector count rises from 19 to 23 only in the final block, after the
step-down had already occurred, so panel widening does not explain it.

---

## 4. Conclusion — informative only, not validation

**The sign agrees across both halves; the strength does not.**

What this does **not** establish: nothing about whether the effect is real out-of-sample.
Both halves were already seen. Sign agreement here is not evidence, and is not counted
as evidence.

What this **does** raise, as a genuine warning:

1. **The effect has weakened by roughly two-thirds since ~2015 and stayed weak**, on a
   dispersion-normalised basis, across two 5-year blocks and 136 rebalances. That is a
   large and persistent change, not a noisy dip.
2. **The frozen configuration's headline number is carried substantially by the
   2005–2014 period.** The −0.974% full-period mean overstates what the same
   configuration has delivered for the last decade, which is **−0.380%**.
3. **Late-half fold consistency is 63.6% — back below the 65% bar** that H1b failed and
   that Part A's cell selection cleared only on full-period data.

**The honest reading of the recent decade is weaker than the honest reading of the full
sample**, and the full-sample figure should not be quoted as the expectation going
forward. The forward record in Part C should be judged against something closer to the
late-half figure (≈ −0.4%, ~64% fold consistency) than the full-period one.

This does not falsify the effect and is not treated as a falsification — the same
seen-data limitation that blocks validation also blocks clean refutation.

**The frozen configuration is not changed in response to this.** It was locked before
these numbers were generated, and re-tuning it now — for instance, re-selecting the cell
on late-half performance — would be precisely the seen-data selection this phase exists
to avoid. The decay is recorded as a known property of what was frozen, alongside the
regime dependency in `live_config_layer1.md` §B1.
