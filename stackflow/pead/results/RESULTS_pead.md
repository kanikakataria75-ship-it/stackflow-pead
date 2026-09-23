# StackFlow PEAD — Results: Earnings Surprise → Post-Announcement Drift

**Run date:** 2026-09-22
**Judged against `pead/pre_registration.md`, saved before any surprise was joined to any return.**

---

## VERDICT

> ## PRIMARY CELL: **CONFIRMED** — all six criteria pass.
>
> **SUE Q5−Q1, 60 trading days, excess vs event universe: +2.50%**
> (discovery +2.89%, holdout +2.16%, 76.2% of quarterly folds positive)
>
> **This is the first signal in StackFlow to clear its pre-registered bar.**
>
> **But the tradeability test fails as specified.** The capped long-only book
> (15 concurrent, 0.585% cost) **underperforms Nifty 500: +8.38% CAGR vs +10.91%** —
> because the cap introduces a selection bias that destroys the edge. The effect is real
> cross-sectionally; the specified implementation does not harvest it.

---

## 1. Coverage

| item | value |
|---|---|
| quarterly filings with PAT | 13,150 across 451 symbols |
| dropped for < 6 prior YoY changes | 4,506 |
| **events with SUE + prices + filters** | **7,973 across 421 symbols** |
| discovery / holdout | 3,516 / 4,457 |
| filing timestamp availability | **100%** |
| `ctx_inferred` | 19.2% · financials 11.2% · basis-switch 23.8% |
| `layer4_seen` flagged | 200 |

| year | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| events | 567 | 1,392 | 1,557 | 1,654 | 1,580 | 1,223 |

Horizon completeness: 5d/10d 100%, 30d 99%, 60d 95%, 126d 90%. Incomplete horizons left blank.

**Note on 2020:** SUE needs ~10 quarters of history, so events begin in 2021. **2020 is
absent from the sample entirely** — criterion 5 is therefore satisfied trivially rather
than by evidence, and is reported that way.

---

## 2. Primary cell against the six criteria

| cut | n (Q5+Q1) | Q5 % | Q1 % | **spread %** | p | folds+ | spread ex-best |
|---|---|---|---|---|---|---|---|
| **ALL** | 3,034 | +1.006 | −1.494 | **+2.500** | 0.0000 | **76.2%** | +2.269 |
| **DISCOVERY** | 1,413 | +1.107 | −1.785 | **+2.893** | 0.0009 | **80.0%** | +2.389 |
| **HOLDOUT** | 1,621 | +0.917 | −1.241 | **+2.157** | 0.0028 | **72.7%** | +1.660 |
| ex-2020 | 3,034 | — | — | +2.500 | 0.0000 | 76.2% | +2.269 |
| **ex-layer4seen** | 2,969 | +0.986 | −1.548 | **+2.534** | 0.0000 | **81.0%** | +2.295 |
| ctx_inferred = False | 2,412 | +1.232 | −1.247 | **+2.479** | 0.0001 | 76.5% | +2.328 |

| # | criterion | result |
|---|---|---|
| 1 | positive on discovery AND holdout | **PASS** (+2.89% / +2.16%) |
| 2 | ≥65% of quarterly folds | **PASS** (76.2% all, 80.0% disc, 72.7% hold) |
| 3 | survives dropping best fold | **PASS** (+2.27% / +2.39% / +1.66%) |
| 4 | roughly monotonic, ≤1 adjacent inversion | **PASS** — see below |
| 5 | not explained by 2020 | **PASS** (2020 not in sample) |
| 6 | survives excluding 203 Layer-4-seen events | **PASS** (+2.53%, folds **improve** to 81.0%) |

**Quintile ladder (xs_univ_60d %):** Q1 −1.494 · Q2 −0.170 · Q3 −0.192 · Q4 +0.854 · Q5 +1.006.
The only inversion is Q2/Q3 (−0.170 vs −0.192, a 0.02pp gap) — within the one-inversion
allowance. Discovery and holdout ladders both rise monotonically at the ends.

**Criterion 6 is the important one.** The whole test was motivated by an already-seen
p = 0.048 on 203 events. Removing those events **strengthens** the result (81.0% fold
positivity vs 76.2%), so the finding does not depend on its own motivation.

---

## 3. Fold detail and stability

Quarterly Q5−Q1 spread (%): 2021Q3 +5.07 · Q4 +3.91 · **2022Q1 +9.37** · Q2 −1.41 ·
Q3 +4.82 · Q4 −2.47 · 2023Q1 +3.03 · Q2 +1.52 · Q3 +0.83 · Q4 +6.20 · 2024Q1 +6.68 ·
Q2 +2.92 · Q3 −0.04 · Q4 −0.06 · 2025Q1 +2.09 · Q2 +0.90 · Q3 +1.40 · Q4 +3.14 ·
2026Q1 +2.41 · Q2 +2.17. **16 of 21 positive.**

**Break-point scan** (not fixed blocks): split 2022 +4.20% → +2.36%; 2023 +2.87% → +2.37%;
2024 +2.89% → +2.16%; 2025 +2.72% → +2.02%. A mild, monotone decay — the effect is
weakening but positive in every late window. No single break dominates.

---

## 4. Diagnostics

| cut | n | spread % | folds+ | p |
|---|---|---|---|---|
| **non-financials** | 2,644 | **+3.196** | 76% | 0.000 |
| **financials** | 390 | **−4.852** | 31% | 0.004 |
| large (turnover > median) | 1,560 | +1.073 | 71% | 0.165 |
| **small (turnover ≤ median)** | 1,474 | **+3.612** | 81% | 0.000 |

Two findings that matter:

- **Financials reverse the effect, significantly** (−4.85%, only 31% of folds positive).
  Bank/NBFC profit is provision-driven and lumpy, so a seasonal-random-walk SUE is a poor
  surprise proxy for them. Financials should be excluded from any use of this signal —
  the same conceptual split that D8 forced in Layer 3.
- **The effect is concentrated in smaller names** (+3.61% vs +1.07%, and the large-cap
  cut is not significant at p = 0.165). This matches the classic PEAD literature and sits
  squarely in StackFlow's mid/smallcap universe.

**Short side carries it:** Q1 = −1.49% vs Q5 = +1.01%. The same pattern Layers 1 and 2
found — **avoiding bad news is worth more than buying good news.** For a long-only book,
that is a problem, not a detail.

---

## 5. Secondary measures (FDR-corrected)

| measure | horizon | spread % | p | **q (BH)** | folds+ | norm |
|---|---|---|---|---|---|---|
| SUE | 5d | +0.415 | 0.029 | 0.035 | 57% | 0.078 |
| SUE | 10d | +0.789 | 0.001 | 0.001 | 86% | 0.119 |
| SUE | 30d | +1.243 | 0.001 | 0.002 | 81% | 0.118 |
| **SUE** | **60d** | **+2.500** | **0.000** | **0.000** | **76%** | **0.162** |
| SUE | 126d | +4.129 | 0.000 | 0.000 | 76% | 0.163 |
| RevSUE | 5d | +0.445 | 0.021 | 0.026 | 71% | 0.083 |
| RevSUE | 10d | +0.636 | 0.007 | 0.010 | 71% | 0.096 |
| RevSUE | 30d | +0.782 | 0.040 | 0.045 | 62% | 0.074 |
| RevSUE | 60d | +1.042 | 0.059 | 0.062 | 52% | 0.067 |
| RevSUE | 126d | +1.511 | 0.095 | 0.095 | 57% | 0.060 |
| **EAR_clean** | 60d | **+2.847** | 0.000 | 0.000 | 81% | 0.184 |
| EAR_clean | 126d | +3.905 | 0.000 | 0.000 | 67% | 0.154 |

**SUE drift grows monotonically with horizon** (0.41 → 0.79 → 1.24 → 2.50 → 4.13%), which
is the textbook PEAD shape: the market under-reacts and corrects slowly. Revenue SUE is
weaker and fades past 30 days.

### A look-ahead bug caught in a secondary measure

The brief specified EAR as the excess return from **event day −1 to event day +1**. But
entry is the **open of event day +1** — so that window **ends inside the day being
traded** and is not knowable at entry.

The symptom was visible before I found the cause: **100% fold positivity at 5d and 10d**,
far beyond anything else in this project.

Both versions are reported:

| version | 60d spread | folds+ | status |
|---|---|---|---|
| EAR as specified (−1 to +1) | **+5.763%** | 95% | **EXCLUDED — look-ahead** |
| **EAR_clean** (−1 to event-day close) | **+2.847%** | 81% | usable |

**The contamination inflated it roughly 2×.** The primary cell is unaffected — SUE uses
only accounting data known at the filing timestamp.

---

## 6. Part F — Tradeability. The effect is real; this book does not capture it.

Long-only, top-quintile SUE, next-day open entry, 60 trading days, equal weight,
**max 15 concurrent**, 0.585% round trip.

| | value |
|---|---|
| top-quintile events with completed 60d | 1,516 |
| **trades actually taken under the cap** | **300 (20%)** |
| gross mean per trade | +2.641% |
| cost | −0.585% |
| **net mean per trade** | **+2.056%** |
| median net | +0.249% |
| win rate | 51.7% |
| **vs Nifty 500** | **−0.392%** |
| **vs event universe** | **−0.799%** |
| **CAGR / max DD** | **+8.38% / −14.55%** |
| **Nifty 500 CAGR / max DD** | **+10.91% / −18.84%** |

### Why it fails, diagnosed

| | uncapped Q5 | capped (15) |
|---|---|---|
| n | 1,516 | 300 |
| xs vs universe | **+1.006%** | **−0.799%** |
| xs vs Nifty 500 | +2.080% | −0.392% |

**The cap fills first-come, so it systematically buys the earliest filers** — median 23
days into the quarter for taken trades vs 39 for skipped ones. Because a 60-day hold blocks
a sleeve for essentially a whole quarter, the book captures roughly one cohort per quarter,
and that cohort is *not* a random sample of the quintile. Taken trades also skew to larger
names (median turnover ₹1.27bn vs ₹0.61bn) — **precisely the segment where §4 showed the
effect is weakest and insignificant.**

So the cap does not merely reduce the edge; it **inverts it**, by selecting on exactly the
two dimensions the effect depends on.

**Per-trade net (+2.06%) does clear the 0.585% cost by a wide margin in gross terms** — the
cost is not what kills this. **Capacity and selection are.**

---

## 7. Verdict, stated plainly

**The cross-sectional PEAD effect is CONFIRMED** on 7,973 point-in-time, as-reported,
filing-timestamped events: **+2.50% Q5−Q1 at 60 days**, holding on discovery and holdout,
in 76% of quarterly folds, surviving best-fold removal, monotonic, and **stronger** when
the events that motivated the test are removed.

**The specified long-only implementation is REJECTED on tradeability**: +8.38% CAGR vs
Nifty 500's +10.91%, with negative excess return, because a 15-position cap selects the
earliest-filing, largest-cap subset where the effect is weakest.

**Size against cost:** the honest per-event number is **+1.01% (Q5 vs event universe) or
+2.50% (Q5−Q1) over 60 days**, against **0.585% round trip**. The long-short spread clears
cost ~4×; the long-only leg alone clears it ~1.7×. Neither is captured by the book as
specified.

### What would plausibly work, and is NOT claimed here

The diagnostics point at a different implementation — more concurrent positions, a
small-cap tilt, financials excluded, and the short side included (which carries most of
the effect). **None of that has been tested, and none of it is a finding.** Testing it
requires its own pre-registration, because choosing an implementation after seeing which
diagnostics looked good is exactly the selection this project has refused throughout.

---

## 8. Limitations

- **No analyst estimates** — SUE uses a seasonal random walk. Weaker than consensus, and it
  misclassifies trending or lumpy-seasonality businesses. This is the single largest
  methodological compromise.
- **2021+ only.** SUE needs ~10 quarters of history, so 2019–20 events are unusable and
  **no extreme regime is in the sample**. The signal is untested against a crisis.
- **19.2% of events carry `ctx_inferred` periods** (D11). The primary cell survives their
  exclusion (+2.48%), so this is not load-bearing.
- **23.8% of symbols switch reporting basis** at some point; D13's post-switch exclusion is
  applied upstream.
- **421 of 451 universe symbols** have usable prices.
- **Mild decay over time** (+4.20% → +2.02% across break-point splits). Positive in every
  window, but the trend is downward and worth watching.
- **Backtest uses a calendar-day approximation** (88 days ≈ 60 trading days) for the
  concurrency cap and distributes each trade's return linearly across its holding window.
  That is adequate for the capacity conclusion, not for precise path statistics.

---

*Layer 1 remains frozen. No combination with Layer 1, Layer 4 or LeadFlow signals was
performed — that is a separate, separately pre-registered question.*
