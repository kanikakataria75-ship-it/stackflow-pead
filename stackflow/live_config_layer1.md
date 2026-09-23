# StackFlow — Layer 1 FROZEN CONFIGURATION

**Freeze date: 2026-09-21**
**Status: FROZEN. This is what "Layer 1" means from this date forward.**

Written **before** any Phase 1c numbers were generated. Nothing below was re-tuned in
this phase. Every value is carried unchanged from Phases 1 and 1b.

Changes to this file require a new dated phase, a written reason, and a new
pre-registration. Not an edit.

---

## Evidence status of what is being frozen

**DISCOVERY — NOT VALIDATED.**

The bottom-tercile effect has been looked at three times on the same 2005–2026 panel:
the H1 grid, the overlap-robustness re-run across three panels, and H1b (which the logged
addendum established was a re-adjudication of identical numbers, not a fresh test). The
sign held every time. That is encouraging and it is **not** validation — the process has
now seen every fold's outcome, and could have let that knowledge shape panel and cell
choices even without anyone intending it.

**No part of this project has yet produced out-of-sample evidence.** Part C's forward
record is the first thing that will.

---

## A. Frozen parameters

| parameter | frozen value |
|---|---|
| **Panel** | Panel C — 23 sectors (containment + excess-correlation filtered) |
| **Ranking signal** | trailing relative strength, **N = 20** trading sessions |
| **Forward window** | **M = 90** trading sessions |
| **Ranking baseline** | equal-weight sector universe mean |
| **Judgement baseline** | equal-weight sector universe mean |
| **Rebalance** | month-end, monthly |
| **Buckets** | terciles; `k = K // 3` |
| **Minimum sectors** | 9 (else the rebalance date is skipped) |
| **Filter output** | **binary** — bottom tercile excluded, rest passed through untouched |
| **Ranking of pass-through** | **none** — not ranked, not scored, not weighted |

### A1. The 23-sector panel (fixed membership)

NIFTY AUTO · NIFTY BANK · NIFTY CAPITAL GOODS · NIFTY CEMENT · NIFTY CHEMICALS ·
NIFTY COMMERCIAL & TRANSPORT SERVICES · NIFTY CONSTRUCTION · NIFTY CONSUMER DURABLES ·
NIFTY CONSUMER SERVICES · NIFTY FMCG · NIFTY HEALTHCARE · NIFTY HOSPITALS ·
NIFTY HOUSING FINANCE · NIFTY INSURANCE · NIFTY IT · NIFTY MEDIA · NIFTY METAL ·
NIFTY NBFC · NIFTY OIL & GAS · NIFTY POWER · NIFTY PSU BANK · NIFTY REALTY ·
NIFTY TELECOMMUNICATIONS

Excluded from the 27 by Part A's rules, not by results:
PHARMA (80% contained in HEALTHCARE) · PRIVATE BANK (80% in BANK) ·
RETAIL (100% in CONSUMER SERVICES) · FINANCIAL SERVICES (0.90 excess-return correlation
with BANK).

### A2. Ranking baseline — equivalence, stated not re-derived

Ranking by `trailing − U_trail` and by `trailing − nifty500_trailing` produce **identical
terciles**. Both baselines are per-date scalars subtracted from every sector alike, and
subtracting a constant cannot reorder a vector. Confirmed empirically in H1b: identical
in 16/16 cells, max absolute difference 0.000e+00. The universe mean is named as the
frozen baseline because it is the correct one for *judgement*, where the choice does
matter.

### A3. Why N=20 / M=90 — from already-reported evidence only

Selected from cells already reported in `RESULTS_h1b.md` and `overlap_robustness.md`.
**No new grid search was run.** Against the two stated criteria:

**(i) Sign stability across all three panels.** All 16 cells were negative on all three
panels, so this criterion alone does not discriminate. N20/M90 has the largest and most
consistent magnitude of the reported candidates: **−0.842% / −0.951% / −0.974%** on
panels A / B / C.

**(ii) Least fragile fold pattern.** N20/M90 is the discriminating criterion, and it wins
on every measure among the five cells with fold tables on record:

| cell | folds neg (A / B / C) | mean % | ex-worst % | retention | turn-year mean % |
|---|---|---|---|---|---|
| **N20/M90** | **77.3 / 81.8 / 72.7** | **−0.95** | **−0.80** | **84.6%** | **−0.08** |
| N90/M90 | 68.2 / 77.3 / 72.7 | −0.82 | −0.62 | 75.6% | +0.14 |
| N90/M20 | 63.6 / 54.5 / 54.5 | −0.19 | −0.09 | 50.7% | +0.18 |
| N20/M20 | 54.5 / 54.5 / 54.5 | −0.23 | −0.17 | 73.2% | +0.01 |
| N60/M60 | 54.5 / 54.5 / 50.0 | −0.38 | −0.26 | 66.8% | +0.83 |

N20/M90 is the **only** candidate clearing the 65% fold bar on all three panels, has the
best worst-fold retention (84.6%), and is the **only** one whose mean across the flagged
turn years (2009, 2014, 2019, 2020, 2021) remains negative rather than flipping positive.

**One cell is frozen, not several.** Logging multiple cells forward would multiply the
comparisons and dilute the only genuinely out-of-sample evidence this project will have.

---

## B. Known limitations inherited by this freeze

These are **not fixed** by freezing. They are what is being frozen, weaknesses included.

### B1. Regime dependency — the material weak point

The filter's wrong-signed years cluster at **sharp market turns** (2009, 2014, 2019,
2020, 2021) and its right-signed years cluster in **trending / crisis-continuation**
periods (2006–2008, 2010, 2013, 2022–2023). It fails when prior laggards lead a V-shaped
recovery — that is, it is least reliable at exactly the moments a portfolio most needs a
defensive filter.

N20/M90 was chosen partly because it degrades least at turns (turn-year mean −0.08% vs
+0.83% for N60/M60), but **−0.08% is barely negative — the edge still substantially
disappears at turns.** This is an inherited weakness, not a solved problem, and it is
frozen in knowingly.

### B2. Failed its own consistency bar

H1b's verdict was **INCONCLUSIVE**: 59.7% mean fold-negativity against a pre-registered
65% bar (criterion (a) failed; criterion (b) passed). The frozen cell is the best cell,
at 72.7% on Panel C — but the grid *as a whole* did not clear the bar, and selecting the
best cell from a grid that failed overall is itself a selection effect operating on seen
data.

### B3. Effective breadth ≈15, not 23

Per `overlap_robustness.md` §A3. 22 folds × ~19 live sectors is materially less
independent evidence than the raw counts imply.

### B4. Small benefit to the survivors

Excluding the bottom third lifts the passed-through two-thirds by only **+0.09% to
+0.44%**, against the excluded bucket's −0.19% to −0.97% drag — the pain is concentrated
in a third, the benefit diluted across two-thirds. That smaller number is what Layer 2's
eventual cost model must beat.

### B5. No cost model exists

The 0.40% round-trip used in Phase 1 is a **placeholder** for stock-level costs. NSE
sectoral indices are not directly tradeable. Real cost depends on tercile-boundary
crossing frequency **and** the stock-level churn that forces downstream — unknown until
Layer 2 exists. **No cost-based claim is made about this configuration.**

### B6. Structural caveats

Price (not total-return) indices — mild bias against high-yield sectors, uncorrected.
Overlapping forward windows — monthly rebalance with M=90 makes observations
autocorrelated; no t-stats are quoted anywhere in this project. Panel C membership uses
present-day constituent and correlation structure applied to full history — hindsight in
universe construction, though not look-ahead in return computation. Cross-section widens
from 20 to 23 sectors over the period.

---

## C. Layer 1's contract with Layer 2

```
INPUT   23-sector Panel C, month-end
SIGNAL  trailing RS over N=20 sessions vs equal-weight universe mean
OUTPUT  EXCLUDED       = bottom tercile (~6 of 19 live sectors)
        PASSED THROUGH = the rest, UNTOUCHED — unranked, unscored, unweighted
```

Layer 2 receives a **set**, not a ranking. Any ranking of the pass-through group is a
separate hypothesis requiring its own pre-registration. Given H1's finding that
`top − middle` was near zero and positive in only 11/16 cells, there is **no evidence a
ranking within the pass-through group would carry information.**

**Layer 2 begins a fresh research phase.** It is not a continuation of this one.
