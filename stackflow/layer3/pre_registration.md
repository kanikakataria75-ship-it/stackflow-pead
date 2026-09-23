# StackFlow Layer 3 — Pre-Registration (H3: Fundamentals as an Exclusion Filter)

**Written:** 2026-09-21, **before any H3 test result has been seen.**
**Root:** `stackflow/layer3/` — own cache, own scripts. Layer 1's frozen files and Layer 2's
paused files are read-only here. LeadFlow is not touched.

Frozen once the first H3 test executes. Later changes appear only as dated addenda.

---

## 0. DATA SOURCE AND POINT-IN-TIME STATUS — the gate, answered first

The brief requires a clear, honest answer before proceeding. Here it is.

**Source: Yahoo Finance via `yfinance`.** Two distinct fundamental series exist, with very
different point-in-time properties. They were probed empirically (12–18 stocks) before any
design work.

### 0.1 Financial statements — LATEST-RESTATED ONLY, and far too short

| series | periods available | oldest | announcement dates? |
|---|---|---|---|
| `income_stmt` (annual) | **4–5** | 2022-03-31 | **No** |
| `balance_sheet` (annual) | **4–5** | 2022-03-31 | **No** |
| `quarterly_income_stmt` | 3–7, **gappy** | 2024-12-31 (typ.) | **No** |
| `quarterly_balance_sheet` | **3** | 2025-03-31 (typ.) | **No** |

**These are latest-restated figures.** There is no as-reported flag, no original-filing
value, and no filing/announcement date attached. Both failure modes the brief warns about
are present:

- **Reporting lag** — with no announcement date, any use of a period-end figure at
  period-end is look-ahead. It could only be handled by *assuming* a lag.
- **Restatement** — a FY2023 figure retrieved today is whatever it was last revised to,
  not what was knowable in 2023.

A web check confirmed point-in-time / as-reported Indian fundamentals are an
**enterprise-grade product** (Bloomberg, FactSet and similar), not available from free
sources. That is noted as genuinely helpful and moved past, not blocked on
([search evidence](https://www.quora.com/What-are-some-fundamental-data-API-providers-for-listed-Indian-stocks)).

### 0.2 Earnings history — announcement-dated, and usable

`Ticker.earnings_dates` is materially better and is the exception:

| property | value |
|---|---|
| rows per stock | **25 (hard cap imposed by the source)** |
| rows with reported EPS | **24** |
| span | **~2020-10 → 2026** (~24 quarters) |
| **actual announcement date** | **YES — this is the key property** |
| figure | reported EPS, from the earnings-surprise history |

Because each row carries the **real announcement date**, a signal built from it can be used
from that date forward with **no reporting-lag look-ahead**. This is a genuine point-in-time
property, and it is the only one available in this phase.

**Restatement status: believed as-reported but NOT VERIFIABLE.** A surprise history records
what was reported against estimate at the time, so it should be the original figure. I
cannot confirm this from the source, and it is therefore recorded as an unverified
assumption, not a fact.

### 0.3 Consequence — what is and is not testable

| # | factor | verdict |
|---|---|---|
| 1 | **Earnings growth (YoY EPS)** | **TESTABLE** — announcement-dated, ~24 quarters |
| 2 | Debt-to-equity | **NOT TESTABLE** |
| 3 | ROE | **NOT TESTABLE** |
| 4 | Interest coverage | **NOT TESTABLE** |

Factors 2–4 all require balance-sheet items, which exist only as **4–5 annual
latest-restated periods with no announcement dates**. That yields ~4 annual signal dates
— four folds — while simultaneously carrying restatement look-ahead and an assumed
reporting lag. That is not a test; it is noise with a known bias.

**Per the brief's instruction to report "not obtainable" plainly rather than produce a
plausible-looking number, factors 2–4 are declared NOT TESTABLE.** They will be run only
as an explicitly labelled **CONTAMINATED PILOT — NOT EVIDENCE**, to document what the data
can and cannot support, and no verdict will be drawn from them.

**Every result in this phase is flagged with its point-in-time status.** No finding from
factors 2–4 may be described as clean under any outcome.

---

## 1. Universe — stated unambiguously

**Layer 1's pass-through universe directly. NOT any Layer 2 output.**

Layer 2 is paused with no validated output (H2 and H2b both rejected on available data),
so there is nothing to hand down. This phase does **not** assume any stock-level
relative-strength filter exists.

Construction, identical to Layer 2's and reused read-only:
1. Universe = **Nifty 500 as of 2020-07-25** (the only point-in-time membership capture
   that exists — established in Layer 2).
2. Mapped to Panel C sectors by 2020-vintage NSE industry, majority rule, ties→pass.
3. At each rebalance date, Layer 1's frozen filter is applied **point-in-time**; stocks in
   passing industries form the universe.

**A fortunate alignment worth stating:** Layer 3's usable window (from ~2021-11, see §3)
lies **entirely after** the 2020-07-25 membership snapshot. The universe is therefore
**genuinely point-in-time for this whole test** — no survivorship, no inclusion look-ahead.
Unlike Layer 2, there is no contaminated secondary window here, because there is no
fundamental data old enough to build one.

## 2. Hypotheses

**H3 (primary, exclusion form):** Among stocks in Layer 1's pass-through universe, stocks
with **weak** fundamental quality on a given factor underperform the universe mean over a
subsequent forward window.

**H3-inv (reported alongside, not assumed away):** stocks with **strong** fundamental
quality on that factor outperform the universe mean.

Exclusion is the default expectation because Layer 1 found "drop the worst" survived while
"pick the best" did not, and Layer 2's weak evidence leaned the same way. Both forms are
tested and both reported — the priority is an expectation, not an assumption.

## 3. Factor definition and test procedure (factor 1, the testable one)

- **Signal:** `YoY EPS growth = (reported_eps[q] / reported_eps[q-4]) − 1`, using the
  **announcement date of quarter q** as the date the signal becomes usable. Requires 5
  quarters of history, so signals begin ~**2021-11**.
- **Sign handling, fixed in advance:** YoY growth is undefined or meaningless when the
  base quarter's EPS is ≤ 0. Those observations are **dropped**, not imputed, and the
  count is reported. Ratios are winsorised at the **1st/99th percentile cross-sectionally
  per date** to limit split/bonus-share artefacts (see §7).
- **Rebalance: QUARTERLY (calendar quarter-end), not monthly.** Reasoning fixed before
  testing: fundamentals update at most quarterly, staggered by actual announcement date,
  so a monthly cadence would re-rank on mostly unchanged information, inflate turnover and
  manufacture false precision. Layer 1's monthly cadence is **not** inherited by default.
  At each quarter-end, each stock's signal is its **most recent announcement on or before
  that date**, and only if that announcement is **within the prior 200 calendar days**
  (stale data is dropped, count reported).
- **Forward-window grid, appropriate to a slow signal:**
  **M ∈ {60, 90, 120, 180} trading days — all four reported, no cell selection.**
- **Buckets:** terciles by signal within the passed-through universe. Require **≥30 stocks**
  on a date or the date is skipped.
- **Baselines, both reported in every table:**
  1. **equal-weight mean of the same filtered universe** — the primary, confound-free measure;
  2. vs Nifty 500 — continuity only. Layer 2 showed this is inflated for *all* buckets by
     the dividend/price-index mismatch plus equal-weight drift, so it is **never** used for
     a verdict.
- **Dispersion-normalised metric** (effect ÷ cross-sectional dispersion of forward excess)
  reported **alongside the raw figure in every table**, from the first run.
- **Stability:** any sub-period claim uses a **full break-point scan** across candidate
  split points, never fixed blocks (the corrected method from Layer 1's diagnostic).
- **Reversal years:** the pre-registered rule from Layer 2 is reused unchanged (Nifty 500
  peak-to-trough ≥15% within the year or prior 6 months **and** year return ≥+10%). It
  yields 2009 and 2020 among others; in this phase's window only **2020** could qualify and
  it falls before the signal start, so the reversal breakdown is expected to be
  **structurally empty**. That is reported as a limitation, not quietly omitted.
- **Look-ahead control:** signal uses only announcements dated ≤ the rebalance date;
  forward returns use only closes strictly after it.

## 4. What would CONFIRM H3 (per factor)

- **(a)** Weak-tercile forward return is **negative vs the equal-weight filtered-universe
  mean** in a majority of the 4 grid cells.
- **(b)** Negative in **≥65% of folds**. **Bar unchanged from every prior StackFlow phase.**
- **(c)** Survives dropping the single most extreme fold.
- **(d)** Not explained by the universe-composition confound — i.e. it persists when
  measured against the filtered-universe mean, not merely against Nifty 500.

H3-inv is judged by the mirror-image criteria and reported whatever it shows.

## 5. What would KILL it (any one sufficient)

- **KF1** — No separation between strong and weak tercile forward returns.
- **KF2** — Effect carried by 1–2 folds and reverses on dropping the extreme fold.
- **KF3** — Effect appears only in isolated cells of an otherwise flat grid.
- **KF4** — Effect explained by the mechanical universe-composition / weighting confound.

## 6. Pre-committed interpretation rule

- (a)–(d) all hold → **H3 SUPPORTED** for that factor (exclusion filter).
- Mirror criteria hold for the strong tercile → **H3-inv SUPPORTED** (selector), reported as such.
- Any of KF1–KF4 → **REJECTED**, reported as rejected, no re-cutting to rescue.
- Neither → **INCONCLUSIVE**, failing criterion named.
- Factors 2–4 → **NOT TESTABLE**, regardless of what their pilot numbers look like.

**No factor combination, weighting, or scoring occurs in this phase under any outcome.**
Per StackFlow's founding brief this layer is a filter, not a score. If more than one factor
were to show a real independent effect, combining them is a separate, later, separately
pre-registered question — explicitly not folded in here because the code is open. That
combination-before-validation error is the one LeadFlow's 4-factor weighting made.

## 7. Known limitations acknowledged in advance

- **~5 folds (2021 partial → 2026).** The 25-row source cap is a **hard ceiling** — more
  downloading cannot fix it. Fold-level consistency is underpowered, and the drop-extreme-
  fold criterion is correspondingly harsh, exactly as it was in Layer 2 at 7 folds. The bar
  is **not** relaxed for this.
- **Restatement status of reported EPS is unverified** (§0.2).
- **EPS is share-count sensitive.** Splits and bonus issues can corrupt YoY EPS growth if
  the source is inconsistently adjusted. Winsorisation limits but does not eliminate this;
  it is a known residual risk, not a solved one.
- **Single-factor coverage only.** Three of four pre-specified factors are not testable, so
  this phase cannot deliver the breadth the founding brief envisaged for Layer 3.
- **EPS growth is a profitability-momentum measure, not a solvency or quality measure.**
  The factors that would capture balance-sheet fragility — leverage, interest coverage —
  are precisely the untestable ones. Any conclusion here says nothing about them.
- **No cost model**, consistent with Layers 1 and 2.
- **Overlapping forward windows** at M ≥ 60. No t-statistic will be quoted as evidence;
  fold-unit permutation tests are used instead.

---

*(Addenda, if any, appear below this line with dates.)*
