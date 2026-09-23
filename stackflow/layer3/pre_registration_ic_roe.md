# StackFlow Layer 3 / Phase 3b — Pre-Registration: Interest Coverage and ROE

**Written: 2026-09-22, BEFORE any Phase 3b grid result has been generated or seen.**

This is written inside a single continuous run with no external checkpoint before the
test executes. The discipline is unchanged and the reason is unchanged: **the criteria are
committed before the numbers exist, so they cannot be shaded afterwards.**

**This does NOT supersede `pre_registration.md` (the EPS-growth factor).** That remains its
own closed, thin-data result. This phase adds two new factors; it does not redo the first.

---

## 0. Data, and what it does and does not support

Built by `stackflow/data_pipeline/xbrl/` from NSE XBRL filings. Schema: `SCHEMA.md`.
Rules: `LOCKED_DECISIONS.md` (D1–D13), all fixed before this file.

| | Interest Coverage | ROE |
|---|---|---|
| source table | `factor_ic_quarterly.csv` | `factor_roe_annual.csv` |
| frequency | quarterly | annual |
| rows | 10,933 | 2,398 |
| symbols | 373 | 440 |
| obs per symbol | median **30 quarters** | median **6 years** |
| **folds** | **8** | **8** |
| `ctx_inferred` | 46.6% | 65.2% |
| basis-switch rate | 58.7% | 36.6% |

### 0.1 Eight folds — stated plainly, not dressed up

**Both factors have 8 calendar/fiscal folds.** That is better than the EPS factor's 5 and
Layer 2's 7. **It is nowhere near Layer 1's 22.**

At 8 folds the ≥65% bar means **≥6 of 8**, and dropping the single extreme fold removes
12.5% of the evidence. This is a **coarse instrument**, and a borderline result here carries
materially less information than the same number would on 22 folds. **The bar is not
relaxed to compensate** — relaxing a pre-registered bar because the sample makes it harder
is the error this project has refused five times.

Interest coverage has one genuine advantage the fold count hides: **median 30 quarterly
observations per company**, so per-rebalance cross-sections are well populated even though
fold-level consistency is coarse. ROE has only ~6 annual observations per company and is
the weaker of the two by construction.

### 0.2 Known data limitations, stated before results

- **FY2023 is missing from ROE.** Those filings declare `OneD` and `FourD` with the same
  wrong period; recovering it would mean overriding an explicitly declared context.
  ROE folds are FY2017–2022, 2024, 2025.
- **`ctx_inferred` is high** (46.6% IC, 65.2% ROE) — periods inferred, not verified (D11).
  **The D11 sensitivity run is mandatory** (§5).
- **Insurance has no data at all** — 6 universe names (HDFCLIFE, SBILIFE, ICICIPRULI,
  ICICIGI, GICRE, NIACL) are absent from ROE despite D8.3 retaining financials.
- **2% of legacy filings are permanently 404** in NSE's archive.
- **Debt-to-equity does not exist** in this filing type and is not tested.

---

## 1. Universe

**Layer 1's pass-through stocks, applied point-in-time** — which sectors passed Layer 1's
frozen filter as of each historical rebalance date, never today's list applied backwards.
Reuses `layer1_passthrough_pit.csv` and the 2020 point-in-time membership + industry map,
identically to the EPS phase.

- **Interest coverage:** financial sector **EXCLUDED** (D8 union rule — industry is
  `FINANCIAL SERVICES` **or** taxonomy contains `BANKING`/`NBFC_INDAS`). Interest expense
  is cost-of-funds for intermediaries, not a financing burden.
- **ROE:** financial sector **INCLUDED** (D8.3) — ROE is meaningful for lenders.
- **D13:** full series kept; the **single observation immediately after a basis switch is
  dropped**, per company per factor.
- **D4 point-in-time:** a filing's figures are usable only from its `filing_date` forward.
  A signal is stale and dropped if the most recent filing is older than **400 days**
  (annual cadence) for ROE, **200 days** for IC — matching the EPS phase's staleness rule.

## 2. Factors — derived from raw tags only (D3)

```
interest_coverage = (pbt + interest) / interest        # requires interest > 0
roe               = pat / equity                       # requires equity  > 0
```

Filed ratio tags are **banned** — verified wrong by ~100× and rounded to 2 decimals.

## 3. The four hypotheses — separate, never combined

| # | hypothesis |
|---|---|
| **H-IC-excl** | Stocks in the **weak** (bottom) tercile of interest coverage **underperform** the equal-weight filtered-universe mean over the forward window. |
| **H-IC-sel** | Stocks in the **strong** (top) tercile of interest coverage **outperform** that mean. |
| **H-ROE-excl** | Stocks in the **weak** tercile of ROE **underperform** that mean. |
| **H-ROE-sel** | Stocks in the **strong** tercile of ROE **outperform** that mean. |

**No factor combination or scoring anywhere in this phase**, per the founding brief. If
both were to work, combining them is a separate, separately pre-registered question.

**No directional prior is assumed.** Layers 1 and 2 leaned filter-shaped; the EPS factor
reversed that and leaned selector-shaped. All four are judged on their own evidence.

## 4. Grids — deliberately different per factor, because update frequency differs

**Interest coverage (quarterly, ~30 obs/company)** — quarterly rebalance:

> **N ∈ {1, 2, 4} quarters of signal lookback × M ∈ {60, 120, 180, 250} trading days**
> = **12 cells, all reported.**

`N` is how many quarters of the ratio are averaged to form the signal (1 = latest filing
only; 4 = trailing-twelve-month smoothing, which damps single-quarter noise in a ratio
with a small denominator).

**ROE (annual, ~6 obs/company)** — annual rebalance:

> **N ∈ {1, 2} years of signal lookback × M ∈ {120, 180, 250} trading days**
> = **6 cells, all reported.**

Justification for the difference, fixed in advance: a factor updating once a year cannot
support a 20–60 day forward window without the same stale signal being re-tested four
times, and cannot support a 4-period lookback when companies have only ~6 periods total.
**Reusing one grid for both factors would be a default, not a choice.**

Buckets: **terciles** within the passed-through universe on each rebalance date.
Require **≥30 stocks** on a date or the date is skipped.

## 5. Mandatory checks — first-class, not follow-ups

1. **Universe-composition confound.** Primary baseline is the **equal-weight mean of the
   same Layer-1-pass-through, financial-sector-adjusted universe**. Figures vs Nifty 500
   are reported for continuity only and **never used for a verdict**. This exact confound
   has now appeared in Layers 1, 2 and the EPS factor; it is built in from the first run.
2. **D11 `ctx_inferred` sensitivity — mandatory.** Every grid runs **twice**, with and
   without inferred-context rows. Same verdict → inference was safe. Verdict changes →
   that factor is reported **"PROVISIONAL — unverified-context-dependent"**.
3. **D13 basis sensitivity.** Repeat the primary grid on companies that never switch
   basis. **State the subset size.** If too small for fold-level analysis, say so and skip.
4. **Break-point scan** for any stability claim — never fixed blocks.
5. **Dispersion-normalised metric** (effect ÷ cross-sectional dispersion) alongside the raw
   figure **in every table, from the first run**.
6. **Reversal-regime breakdown.** Using the rule already fixed in the EPS pre-registration
   (Nifty 500 drawdown ≥15% within the year or prior 6 months **and** year return ≥+10%).
   In the 2019+ range **2020 qualifies**; the computed list is reported as found.
7. **Data-quality diagnostics in every results table:** `ctx_inferred %` and basis-switch
   rate, per factor.

## 6. Confirm criteria — identical for all four hypotheses

A hypothesis is **CONFIRMED** only if **all four** hold:

- **(a)** Effect is correctly signed in a **majority of that factor's grid cells**.
- **(b)** Correctly signed in **≥65% of folds** — i.e. **≥6 of 8**. **Unchanged.**
- **(c)** **Survives dropping the single most extreme fold** (best for selection forms,
  worst for exclusion forms).
- **(d)** **Not explained by the universe-composition confound** — it persists when
  measured against the filtered-universe mean, not merely against Nifty 500.

## 7. Kill criteria — any one is sufficient

- **K1** — No separation between strong and weak tercile forward returns.
- **K2** — Effect carried by 1–2 folds and reverses when the extreme fold is dropped.
- **K3** — Effect appears only in isolated cells of an otherwise flat grid.
- **K4** — Effect vanishes against the filtered-universe mean (i.e. it was composition).

## 8. Pre-committed interpretation rule

- All of (a)–(d) → **CONFIRMED**.
- Any of K1–K4 → **REJECTED**, reported as rejected, no re-cutting to rescue.
- Neither → **INCONCLUSIVE**, with the failing criterion named.
- D11 sensitivity flips a verdict → that verdict becomes **PROVISIONAL**.

**Four verdicts will be reported, each judged only against its own criteria.** None is
inferred from another.

## 9. Effect-size reporting requirement

For anything that clears the bar, the report must state its **real per-rebalance magnitude
in %**, and its magnitude relative to a realistic cost assumption — the way Layer 1's
frozen config was reported (≈−0.38% per rebalance, ≈+0.17% to survivors). **A sign and a
p-value are not a result.**

## 10. Pre-commitment on a null

If nothing clears the bar, it is reported as plainly as H1's and H3's verdicts were. **An
honest null on real, hard-won data is a valid output.** The pipeline stands as reusable
infrastructure regardless of what this specific test finds, and the report will not be
softened to make the build feel better rewarded than the evidence supports.

---

*(Addenda, if any, appear below this line with dates.)*
