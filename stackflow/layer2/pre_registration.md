# StackFlow Layer 2 — Pre-Registration (H2 / H2b)

**Written:** 2026-09-21, **before any H2 test result has been seen.**
**Project root:** `stackflow/layer2/` — own cache, own scripts. Layer 1's frozen files are
read-only here. LeadFlow is not touched.

Frozen once the first H2 test executes. Later changes appear only as dated addenda.

---

## 0. Data reality, established before designing the test

### 0.1 Point-in-time index membership is NOT obtainable — this constrains everything

A first attempt appeared to retrieve 19 annual Nifty 500 snapshots (2008–2026). **It was
void.** All 19 files were byte-identical, and year-over-year turnover was 0 added /
0 dropped — impossible for a real index. Cause: the Wayback Machine holds **exactly one
capture** of NSE's constituent CSV (CDX confirms `total captures = 1, month 202007`), and
the `/web/{stamp}/` form silently redirects every request to the nearest capture.
Logged in `RUN_LOG.md`. NSE's own API returns 403/503 and was not evaded; sectoral index
constituent lists are archived once at most.

**Available membership data, in full:**

| snapshot | date | taxonomy |
|---|---|---|
| point-in-time | **2020-07-25** | old NSE (19 classes) |
| current | 2026-09 | new NSE (20 classes) |

That is two points, not a time series. **Genuine point-in-time membership for 2005–2020
is not obtainable with available sources.** It is not estimated or reconstructed.

### 0.2 What this forces — and the design that salvages a clean test

Using today's membership across history would embed both survivorship and inclusion
look-ahead. The single 2020 snapshot is worth more than it looks, because a universe
**fixed at 2020-07-25 and tested only on data after that date is genuinely point-in-time**:
membership was determined before every forward return measured, and companies that later
collapsed or delisted are still in the list.

| test | universe | window | status |
|---|---|---|---|
| **PRIMARY** | Nifty 500 as of **2020-07-25** | **2020-08-31 → 2026-09** | **CLEAN — no survivorship, no look-ahead** |
| SECONDARY | same 2020 list | 2005 → 2020-07 | **CONTAMINATED** — labelled, never used for the verdict |

**The verdict rests on the PRIMARY test only.** The secondary is reported for continuity
and because hiding it would be worse than labelling it, exactly as Layer 1 reported its
own informative-only split.

### 0.3 Power warning, recorded before running

The clean window is **~74 monthly rebalances across 7 calendar-year folds (2020 and 2026
partial)**. The ≥65% fold bar therefore means **≥5 of 7** — a coarse instrument. Each
cross-section holds ~300+ stocks, so per-rebalance estimates are reasonably precise; it is
**fold-level consistency that is underpowered**. A borderline fold result in this test
carries much less information than the same number did in Layer 1's 22 folds, and will not
be treated as though it carries more.

### 0.4 Price data

Stock closes from Yahoo, split/dividend adjusted. Coverage is good for listed names.
**Survivorship in the price source is partial and independent of the membership problem**
— e.g. `RCOM`, `JETAIRWAYS`, `SUZLON`, `IL&FSTRANS`, `YESBANK` are retained, but `DHFL`
and `RELCAPITAL` return nothing. Names in the 2020 list with no retrievable price history
will be **counted and reported**, not silently dropped, since they are exactly the failure
cases H2b is about.

---

## 1. Hypotheses

**H2 (full, selector form):** Among stocks in sectors that pass Layer 1's filter, stocks
with stronger trailing relative strength vs Nifty 500 outperform weaker ones over a
subsequent forward window.

**H2b (narrow, filter form):** Bottom-tercile stocks by trailing RS underperform the
equal-weight mean of the same filtered stock universe, even if the top-tercile selection
claim fails on its own.

Both are specified now, in advance. Layer 1 needed an entire extra phase (H1→H1b) to
discover this split after the fact; that is not repeated here.

## 2. Relative-strength construction — choice and reason

**PRIMARY and only construction tested this phase: plain trailing return minus Nifty 500
return over the lookback window.**

Reason: (a) it is the simplest and most falsifiable form, and testing the simple form
first is the discipline that worked in Layer 1; (b) LeadFlow's drawdown-conditional RS is
a concept this project is required to re-derive rather than import, and adopting it as
primary would import untested complexity into a layer that has no validated result yet;
(c) testing two constructions and reporting the better-looking one is precisely the
selection effect this project keeps guarding against.

**Drawdown-conditional RS is NOT tested in this phase.** If it is ever tested it gets its
own pre-registration. This is stated so that no later run can be presented as though the
choice had been open.

## 3. Universe construction (fixed in advance)

1. Start from the **2020-07-25 Nifty 500 list** (501 stocks).
2. Map each stock's **2020-vintage NSE industry** to Panel C sector(s) by the table below.
3. At each month-end `t`, compute Layer 1's frozen filter **point-in-time** (Panel C
   sector indices, N=20 trailing RS vs equal-weight sector-universe mean, bottom tercile
   excluded, ≥9 sectors required). This part is genuinely point-in-time — sector index
   levels are real historical data — so **no contamination enters through Layer 1**.
4. A stock is **passed through** if its industry passed (rule in §3.2).
5. Stocks whose industry maps to no Panel C sector are **excluded from the universe**.

### 3.1 Industry → Panel C sector map (2020 taxonomy)

| 2020 industry | n | Panel C sector(s) |
|---|---|---|
| FINANCIAL SERVICES | 87 | BANK, PSU BANK, NBFC, HOUSING FINANCE, INSURANCE |
| CONSUMER GOODS | 73 | FMCG, CONSUMER DURABLES |
| INDUSTRIAL MANUFACTURING | 49 | CAPITAL GOODS |
| PHARMA | 38 | HEALTHCARE |
| AUTOMOBILE | 30 | AUTO |
| CONSTRUCTION | 30 | CONSTRUCTION, REALTY |
| SERVICES | 28 | COMMERCIAL & TRANSPORT SERVICES, CONSUMER SERVICES |
| IT | 27 | IT |
| METALS | 22 | METAL |
| CHEMICALS | 21 | CHEMICALS |
| OIL & GAS | 18 | OIL & GAS |
| CEMENT & CEMENT PRODUCTS | 15 | CEMENT |
| POWER | 15 | POWER |
| FERTILISERS & PESTICIDES | 12 | CHEMICALS |
| MEDIA & ENTERTAINMENT | 10 | MEDIA |
| HEALTHCARE SERVICES | 7 | HOSPITALS |
| TELECOM | 7 | TELECOMMUNICATIONS |
| **TEXTILES** | 10 | **none — dropped** |
| **PAPER** | 2 | **none — dropped** |

12 stocks (TEXTILES + PAPER) are dropped as unmappable.

### 3.2 Multi-mapped industries — majority rule, fixed now

NSE's macro industries do not map one-to-one onto Panel C. Five Panel C sectors sit under
`FINANCIAL SERVICES`; `CONSUMER GOODS`, `CONSTRUCTION` and `SERVICES` each map to two.

**Rule: an industry passes if a strict majority of its mapped Panel C sectors passed that
month. Ties resolve to PASS** (the less restrictive direction, chosen so the filter is not
silently made more aggressive than Layer 1's own one-third exclusion).

This is an approximation and is recorded as such: it means a financial stock is judged by
"are financials as a group weak", not by its own sub-sector. **Sensitivity check
(reported regardless of outcome):** re-run assigning stocks by actual current Panel C
sectoral-index membership where available. That version is contaminated but definitionally
faithful; if the two disagree materially, the mapping is load-bearing and that will be said.

## 4. Test procedure

- **Rebalance:** month-end, monthly. Matches the cadence of the Layer 1 output it consumes
  and avoids the turnover and noise of daily re-ranking.
- **Grid, re-derived for stocks — NOT inherited from Layer 1:**
  **N ∈ {20, 60, 120, 250} × M ∈ {20, 60, 120} = 12 cells, all reported.**
  Rationale: Jegadeesh–Titman-style stock momentum conventionally uses 3–12 month
  formation and 1–6 month holding. Layer 1's 20/90 was derived for sectors and is not
  assumed to transfer. **No skip month** is used (keeps the design minimal and comparable
  to Layer 1); short-term reversal is therefore a known confound specific to N=20, and
  will be flagged rather than tuned away.
- **Buckets:** terciles by trailing RS *within the passed-through universe* on each date.
  Require ≥30 stocks or the date is skipped.
- **Baselines, both reported in every table:**
  1. vs **Nifty 500** (continuity with Layer 1), and
  2. vs the **equal-weight mean of the same filtered stock universe** — the
     universe-composition confound check. This is a **first-class part of the initial
     run**, not a follow-up. Layer 1 found ~two-thirds of its headline was equal-weight
     drift discovered post-hoc; that is not repeated.
- **Dispersion-normalised metric** (`effect / cross-sectional sd of forward excess`)
  reported **alongside the raw figure in every table**, not as an afterthought.
- **Stability:** any sub-period claim uses a **break-point scan across all candidate split
  points**, never fixed blocks. Phase 1c's "step at 2015" was an artifact of fixed
  5-year boundaries; that error is not repeated.
- **Look-ahead control:** ranking at `t` uses only closes ≤ `t`; forward uses only closes
  > `t`.

## 5. Reversal-regime reporting — built in from the start

Published evidence (cited in Layer 1's decay diagnostic) finds "severe periodic losses…
when markets rebound after enormous losses" is a **general property of momentum in Indian
equities**, not a sector-data quirk. This layer therefore reports reversal-year behaviour
in its **first** results document.

**Objective rule, fixed now (the rule is pre-registered, not the resulting list):** a
calendar year is a REVERSAL year if the Nifty 500 suffered a peak-to-trough drawdown of
**≥15%** within that year or the preceding 6 months, **and** the year's return is **≥+10%**.
The computed list will be reported. 2009 and 2020 are expected to qualify; the rule may
identify others and they will be reported as found.

Every results table reports the effect **excluding reversal years** alongside the
all-years figure.

## 6. What would CONFIRM H2 (full selector form)

All four required, on the **clean primary test**:
- **(a)** Top-tercile forward excess vs Nifty 500 positive on average across a majority of the 12 cells.
- **(b)** Holds in **≥65% of folds** (≥5 of 7). **Bar unchanged from Layer 1** — not relaxed.
- **(c)** Survives dropping the single best fold.
- **(d)** Separates **monotonically**: top > middle > bottom. A top-vs-rest jump with no
  middle ordering is not accepted — Layer 1's top-vs-middle turned out to be noise.

## 7. What would CONFIRM H2b (narrow filter form)

- Bottom-tercile forward return is **negative vs the equal-weight filtered-universe mean**
  in a majority of cells, **negative in ≥65% of folds**, and not reversed by dropping the
  single most extreme fold.

If H2 fails but H2b holds, it is reported explicitly **as the Layer 1 analogue it is** —
a filter, not a selector — not as a full rejection.

## 8. What would KILL both

- **KL1** — No separation between top and bottom tercile forward returns, in either form.
- **KL2** — Effect appears only in isolated cells of an otherwise flat 12-cell grid.
- **KL3** — Effect carried by 1–2 folds and reverses when the best fold is dropped.
- **KL4** — Effect is **nominal, not real**: fully explained by the universe-composition /
  weighting confound, i.e. it vanishes when measured against the equal-weight filtered
  universe mean rather than Nifty 500.

## 9. Pre-committed interpretation rule

- H2 (a)–(d) all hold → **H2 SUPPORTED** (selector).
- H2 fails but §7 holds → **H2b SUPPORTED** (filter only), reported as such.
- Any of KL1–KL4 → **REJECTED**, reported as rejected, no re-cutting to rescue.
- Neither clean confirm nor clean kill → **INCONCLUSIVE**, with the failing criterion named.

## 10. Effect-size prior — budget for less than the headline

The supporting result Layer 1's diagnostic found (232 Nifty 500 firms, Jul 2015–Jun 2024,
"loser portfolios persistently underperform") is **one published study, one universe, one
period**. Its magnitude is treated as an **upper bound**, not an expected result. A
finding materially *larger* than that prior is grounds for suspecting a bug or a confound,
not for celebration.

## 11. Known limitations acknowledged in advance

- **Clean window is only ~6 years / 7 folds** (§0.3) — fold consistency is underpowered.
- **Industry→sector mapping is approximate** for four multi-mapped industries (§3.2).
- **12 stocks unmappable** and dropped; count reported.
- **Price-source survivorship is partial** (§0.4); missing names counted and reported.
- **No cost model.** Layer 2 turnover is measured and reported, but no cost-based verdict
  is issued — consistent with Layer 1's frozen-config caveat.
- **Overlapping forward windows** at M > 20 make observations autocorrelated. No t-stat
  will be quoted as evidence; fold counts and permutation tests are used instead.
- **No Layer 3 / fundamentals work** follows in this phase under any outcome.

---

*(Addenda, if any, appear below this line with dates.)*
