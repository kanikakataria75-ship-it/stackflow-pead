# StackFlow Layer 3 — Results: H3 / H3-inv (Fundamentals as a Filter)

**Run date:** 2026-09-21
**Judged against `layer3/pre_registration.md` as frozen.** Verdict written after the data.

---

## VERDICT (up front)

> **H3 (exclusion — "drop weak fundamentals") is REJECTED.** Kill criterion KF2 triggered:
> the weak-tercile effect reverses sign when the single most extreme fold is dropped, in
> **4 of 4 cells**, on both samples. Nothing approaches significance (best p = 0.296).
>
> **H3-inv (selection — "strong EPS growth outperforms") is INCONCLUSIVE, leaning
> supportive at long horizons only.** Positive in 4/4 cells, surviving the drop-best-fold
> test in 4/4, clearing the fold bar in 3/4 — but **no cell reaches significance**
> (best p = 0.060), the sample is 4–5 folds, and it rests heavily on 2 of them.
>
> **Factors 2–4 (debt/equity, ROE, interest coverage) remain NOT TESTABLE** — no run was
> attempted, per §0 of the pre-registration.

**This is a reversal of the pattern in Layers 1 and 2.** Both landed filter-shaped
("drop the worst" survived, "pick the best" did not). Here the **exclusion form fails
outright and the selection form is the one with any life in it.** That is why the
pre-registration required testing both rather than assuming the filter framing.

---

## 1. What was actually testable

| item | value |
|---|---|
| Factor tested | **1 of 4** — YoY EPS growth, announcement-dated |
| Universe with prices **and** EPS history | **400** of 434 |
| YoY observations | 7,004 usable; **364 dropped** (base EPS ≤ 0, as pre-registered) |
| Stale-signal drops (>200 days old) | **7,656 / 28,716 = 26.7%** |
| Rebalance | quarterly, as pre-registered |
| Reversal years in the representative sample | **NONE** — 2020 predates the usable window |

## 2. A data-quality problem found before reporting, not after

The pre-registration expected signals to begin ~2021-11 (median first announcement
2021-10-19). The run instead produced folds from **2017**. Cause: a minority of stocks have
unusually deep Yahoo EPS history, so early dates cleared the 30-stock minimum on a small,
non-representative subset.

**Cross-section size by year:**

| year | 2017 | 2018 | 2019 | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| median stocks | 41 | 47 | 59 | 53 | 59 | **227** | 227 | 247 | 227 | 228 |

A **4–5× step change at end-2021.** Folds before 2022 rest on ~40–60 stocks — roughly 12%
of the universe, and almost certainly biased toward larger, longer-listed, better-covered
companies.

**Both samples are reported. The primary is 2022+.** That restriction is post-hoc in
timing, but it is made on a **data-representativeness criterion that is independent of any
result** (cross-section size), and it moves the test *closer* to the pre-registered window,
not further from it. It is labelled rather than silently applied.

---

## 3. Full grid — all 4 cells, both samples

`strong`/`weak` = forward excess vs the **equal-weight filtered universe** (primary
baseline). `_norm` = effect ÷ cross-sectional dispersion.

| M | sample | folds | medK | strong % | mid % | weak % | spread % | s_norm | w_norm | folds strong>0 | folds weak<0 | strong ex-best | weak ex-worst | p_strong | p_weak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 60 | FULL 2017+ | 10 | 191 | 0.748 | −0.542 | −0.205 | 0.953 | 0.044 | −0.012 | 70% | 40% | 0.526 | **+0.640** | 0.083 | 0.513 |
| 60 | **2022+** | 5 | 233 | 0.518 | −0.573 | **+0.062** | 0.455 | 0.034 | 0.004 | 80% | 40% | **0.007** | **+0.423** | 0.248 | 0.716 |
| 90 | FULL 2017+ | 10 | 191 | 1.146 | −0.552 | −0.635 | 1.781 | 0.052 | −0.029 | 70% | 60% | 0.626 | **+0.100** | 0.057 | 0.296 |
| 90 | **2022+** | 5 | 233 | 1.190 | −1.345 | **+0.175** | 1.015 | 0.060 | 0.009 | 60% | 60% | **0.066** | **+0.236** | 0.190 | 0.562 |
| 120 | FULL 2017+ | 10 | 132 | 1.300 | −0.894 | −0.446 | 1.745 | 0.052 | −0.018 | 70% | 60% | 1.187 | **+0.410** | 0.044 | 0.386 |
| 120 | **2022+** | 5 | 233 | 1.947 | −1.870 | −0.047 | 1.994 | 0.086 | −0.002 | 80% | 60% | 1.557 | **+0.106** | 0.060 | 0.341 |
| 180 | FULL 2017+ | 9 | 99 | 2.153 | −1.466 | −0.687 | 2.841 | 0.066 | −0.021 | 78% | 44% | 1.721 | **+0.367** | 0.028 | 0.368 |
| 180 | **2022+** | 4 | 231 | 2.917 | −2.616 | −0.220 | 3.137 | 0.100 | −0.008 | 75% | 50% | 1.862 | **+0.337** | 0.123 | 0.433 |

### The middle tercile is the worst bucket — the relationship is U-shaped, not monotonic

On the representative sample the ordering is **strong > weak > mid** in every cell
(monotonic in 0/4). Middle-tercile EPS growers underperform *both* extremes by
−0.57% to −2.62%.

A clean fundamental factor should not behave this way. A U-shape is more consistent with
noise, or with a non-linear artefact of ranking a ratio, than with "EPS growth is
priced". **This materially weakens any story built on H3-inv**, and is reported for that
reason rather than left in a footnote.

---

## 4. Adjudication against the frozen criteria

### H3 — exclusion form (the primary hypothesis): **REJECTED**

| criterion | representative 2022+ | full 2017+ |
|---|---|---|
| (a) weak < 0 in majority of cells | **FAIL** 2/4 | PASS 4/4 |
| (b) negative in ≥65% of folds | **FAIL 0/4 cells** (40–60%) | **FAIL** (40–60%) |
| (c) survives dropping extreme fold | **FAIL 0/4** — flips positive in all | **FAIL 0/4** — flips positive in all |
| (d) not a composition confound | n/a — nothing to explain | n/a |

**KF2 triggered** ("effect carried by 1–2 folds and reverses on dropping the extreme
fold"). The weak tercile's apparent underperformance is entirely one fold per cell:
remove it and the bucket turns **positive in 4/4 cells on both samples**. On the
representative sample the weak tercile is **positive outright** at M=60 and M=90.

Per the pre-committed rule: **H3 REJECTED.**

### H3-inv — selection form: **INCONCLUSIVE, leaning supportive at long horizons**

| criterion | representative 2022+ |
|---|---|
| (a) strong > 0 in majority of cells | **PASS** 4/4 |
| (b) positive in ≥65% of folds | **PASS in 3/4** (80%, 60%, 80%, 75%) |
| (c) survives dropping best fold | **PASS 4/4** — but see below |
| (d) not a composition confound | **PASS** — see §5 |

**Why this is not called supported:**

- **No cell reaches significance.** Best p = 0.060 (M=120). Full sample reaches p = 0.028
  at M=180, but that sample is half-composed of the biased thin folds.
- **(c) passes only nominally at short horizons.** Dropping the best fold leaves
  **0.007%** at M=60 and **0.066%** at M=90 — i.e. the entire effect at short horizons *is*
  one fold. Only M=120 (1.557%) and M=180 (1.862%) retain real magnitude.
- **It rests on 2 of 5 folds.** At M=120: 2022 −0.60, **2023 +5.48**, 2024 +0.74,
  2025 +1.51, **2026 +4.58** — and the 2026 fold contains **a single rebalance** (K=132).
- **Non-monotonic** (§3).
- **Effect sizes are small once normalised:** 0.034–0.100 SD against cross-sectional
  dispersion of 17–33%.

The one genuinely encouraging feature: the effect **strengthens coherently with horizon**
(0.52 → 1.19 → 1.95 → 2.92%) rather than appearing in isolated cells, so **KF3 is not
triggered**. That is the pattern a slow fundamental signal should show.

---

## 5. Universe-composition confound — checked first-class, and it bites again

| M | strong vs universe | strong vs Nifty 500 | weak vs universe | weak vs Nifty 500 | **implied universe drift** |
|---|---|---|---|---|---|
| 60 | +0.518 | +1.856 | +0.062 | **+1.401** | **+1.338** |
| 90 | +1.190 | +3.904 | +0.175 | **+2.890** | **+2.714** |
| 120 | +1.947 | +5.205 | −0.047 | **+3.211** | **+3.258** |
| 180 | +2.917 | +7.347 | −0.220 | **+4.210** | **+4.431** |

**Measured against Nifty 500, even the *weak* tercile beats the benchmark by +1.4% to
+4.2%.** Both buckets cannot outperform like that. The implied universe drift is
**+1.3% to +4.4%** — dividend-adjusted stock prices against a price-only index, compounded
by equal-weight vs cap-weight, plus Layer 1's own filter tilt.

Had this been measured naively against Nifty 500, H3-inv would have looked **2–3× larger
than it is**, and the weak tercile would have looked like a *winner*. Measured against the
filtered-universe mean, as pre-registered, the honest effect is what §3 shows.

**This is the third consecutive layer where this confound was material** — Layer 1 caught
it post-hoc, Layer 2 and Layer 3 caught it in the first run. **KF4 not triggered**,
because the effect survives the correct baseline; but it is much smaller than the naive
number.

---

## 6. Reversal-regime breakdown — structurally empty, as predicted

The pre-registration anticipated this. The pre-registered rule flags 2020 (and 2009), both
of which **predate the representative window**. The representative sample contains **no
reversal year at all**.

So this layer's signal is **untested against the regime that has broken every prior
StackFlow signal.** That is a gap, not a clean bill of health, and it cannot be closed with
the available data.

---

## 7. Limitations

- **1 of 4 factors tested.** The three that are not testable — leverage, ROE, interest
  coverage — are exactly the **solvency/fragility** measures a quality filter for a
  leverage-prone universe would most want. EPS growth is profitability *momentum*.
  **Nothing here says anything about balance-sheet quality.** See
  `data_sourcing/RESULTS_sourcing.md` for the route to fixing that.
- **4–5 representative folds** — thinner than Layer 2's 7, far below Layer 1's 22. The
  ≥65% bar means ≥4/5 and is coarse. **It was not relaxed.**
- **26.7% of signals dropped as stale** (>200 days since last announcement). That is a
  large fraction of the cross-section silently excluded each quarter.
- **Restatement status unverified** (pre-registration §0.2). Reported EPS is *believed*
  as-originally-reported; this could not be confirmed.
- **EPS is share-count sensitive.** Winsorisation at 1/99 limits split/bonus artefacts but
  does not eliminate them.
- **2026 fold contains one rebalance** and carries disproportionate weight in H3-inv.
- **No cost model**, consistent with Layers 1 and 2.
- **Overlapping forward windows** at all M. No t-statistic quoted; fold-unit permutation
  tests used throughout.

---

## 8. Recommendation

**Do not adopt an EPS-growth filter or selector into the stack on this evidence.**

- **The exclusion form is rejected outright** — and that is the form StackFlow's own
  history predicted would work. Worth registering that the prior was wrong here.
- **The selection form is not established.** It is the most promising single result in the
  layer — coherent horizon scaling, 4/4 cells positive, surviving drop-best-fold — but it
  is not significant, rests on 2 of 5 folds, is non-monotonic, and has never been tested
  against a reversal regime.

Two things, in order, neither in this session:

1. **The binding constraint is again data, not method** — same conclusion as Layer 2, for
   a different reason. Layer 3 is testing **one** factor because three are unobtainable,
   on **5** folds because the source caps at 25 rows. The BSE/NSE XBRL route
   (`data_sourcing/RESULTS_sourcing.md`, ~9 folds, 3–6 days, and it also unlocks Layer 4's
   concall transcripts) would make Layer 3 a real test rather than a single-factor probe.
2. **If H3-inv is ever revisited, it needs its own pre-registration at long horizons only
   (M=120/180)** and must not inherit this phase's borderline result as a prior. Re-running
   the same thin data and reporting it again would be re-adjudication, not evidence — the
   exact error caught and logged in H1b.

**No factor combination or scoring was performed**, per the founding brief and the
pre-registration. With one factor testable and that factor rejected in its primary form,
combination is not on the table.

---

*Layer 1 remains frozen. Layer 2 remains paused. No Layer 4 work started.*
