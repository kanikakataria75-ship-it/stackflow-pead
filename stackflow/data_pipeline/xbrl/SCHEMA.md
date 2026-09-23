# XBRL Pipeline — Cache Schema and Handoff Reference

**Version:** 1.0 · **Date:** 2026-09-22
**Purpose:** so a future pre-registration can cite exact field names and coverage without
re-deriving them. Rules that produced this data are in `LOCKED_DECISIONS.md`.

---

## Files in `stackflow/data_pipeline/xbrl/cache/`

| file | what it is |
|---|---|
| `filing_index.csv` | **legacy** NSE financial-results filings, 2019-01 → 2025-01 |
| `filing_index_integrated.csv` | **integrated** filings, 2025-03 → 2026-09 |
| `extract_universe.csv` | **the handoff table** — parsed fundamentals, one row per company-period |
| `extract_test.csv` | same schema, 5-company validation set (Step 2.2) |
| `revision_check.csv` | Step 2.3 Original-vs-Revision comparison |
| `xml/` | raw XBRL instances, cached by filename |

**Both filing systems must be used.** The legacy endpoint stops carrying most filings from
~April 2025; the integrated endpoint starts ~March 2025. Either alone loses data silently.

---

## `extract_universe.csv` — field reference

### Identity and period

| field | type | meaning |
|---|---|---|
| `symbol` | str | NSE symbol. **Join key** to the Layer 1/2 universe. |
| `period` | str | `Quarterly` or `Annual` |
| `period_start` | date `YYYY-MM-DD` | start of the period the figures cover |
| `period_end` | date `YYYY-MM-DD` | end of the period the figures cover |
| **`filing_date`** | date `YYYY-MM-DD` | **the point-in-time date. Figures are usable ONLY from this date forward (D4).** Never use `period_end` for availability. |

### Provenance and audit

| field | type | meaning |
|---|---|---|
| `src` | str | `legacy` or `integrated` |
| `taxonomy` | str | `INDAS`, `NBFC_INDAS`, `BANKING`, `NONINDAS`, or `INTEGRATED_FILING_*` |
| `basis` | str | `Consolidated`, `Non-Consolidated` (legacy) or `Standalone` (integrated). **The latter two mean the same thing — labels are not normalised upstream.** D1: Consolidated preferred, others are fallback. |
| `audited` | str | `Audited` / `Un-Audited` |
| `type_sub` | str | `Original` or `Revision` (D12) |
| **`ctx_inferred`** | bool | **D11 audit flag. `True` means the XBRL referenced a context it never defined, and the period was INFERRED from the filing's declared dates rather than verified from the file.** Must be reported as a % alongside any result built on this data. |
| `reasons` | json str | per-field failure reasons where a field could not be resolved |

### Financial values — all in **absolute INR** (not lakhs, not crores)

| field | meaning | taxonomy source |
|---|---|---|
| `pbt` | profit before tax | `ProfitBeforeTax` / `ProfitLossFromOrdinaryActivitiesBeforeTax` (banking) |
| `interest` | interest / finance cost | `FinanceCosts` / `InterestExpended` (banking) |
| `pat` | profit after tax | `ProfitLossForPeriod` / `ProfitLossForThePeriod` (banking) |
| `revenue` | revenue | `RevenueFromOperations` / `Income` (banking) |
| `share_capital` | paid-up equity share capital | `PaidUpValueOfEquityShareCapital` |
| `reserves` | reserves excl. revaluation | `ReserveExcludingRevaluationReserves` |
| `equity` | `share_capital + reserves` | derived |

### Usability flags

| field | meaning |
|---|---|
| `ok_ic` | `pbt` and `interest` both present → row usable for interest coverage |
| `ok_roe` | `pat` and `equity` both present → row usable for ROE |

---

## Derived factors — compute these downstream, never read them from the filing

**Ratio tags in the filings are BANNED (D3)** — verified wrong by ~100× and rounded to 2
decimals. Always derive:

```python
interest_coverage = (pbt + interest) / interest      # requires ok_ic and interest > 0
roe               = pat / equity                     # requires ok_roe and equity > 0
```

---

## Mandatory usage rules for any downstream test

1. **Point-in-time (D4).** A row is available only from `filing_date` forward. Rank on a
   date `t` using rows where `filing_date <= t`.
2. **Financial-sector exclusion for interest coverage only (D8).** Exclude a stock from
   the interest-coverage factor if **either** its NSE industry is `FINANCIAL SERVICES`
   **or** its `taxonomy` contains `BANKING` or `NBFC_INDAS`. **ROE keeps them.**
3. **`ctx_inferred` sensitivity is mandatory (D11 condition 2).** Every grid runs twice —
   with and without `ctx_inferred` rows. Same verdict → inference was safe. Different
   verdict → report as **"PROVISIONAL — unverified-context-dependent"**.
4. **Report the `ctx_inferred` %** in every results table (D11 condition 3).
5. **ROE is annual.** `reserves` is filed almost only in annual contexts, so quarterly rows
   rarely carry equity. This is the data's behaviour, not a bug.
6. **Never combine interest coverage and ROE into one score.** Founding-brief rule;
   combination is a separate, separately pre-registered question.

---

## Known coverage gaps — state these in any pre-registration

| gap | detail |
|---|---|
| **History starts 2019** | 2017–18 filings exist but carry a `-` placeholder, not a file. |
| **Insurance has no data** | LI/GI taxonomies are unmapped *and* have **zero legacy filings** — all 11 insurance names exist only from 2025. Affects 6 universe names (HDFCLIFE, SBILIFE, ICICIPRULI, ICICIGI, GICRE, NIACL). |
| **Debt-to-equity impossible** | No borrowings/total-debt tag exists in results filings (D2). Deferred to a future annual-report/PDF task. |
| **Basis can switch within a company** | D1 applied per period can give consolidated quarters and standalone annuals (e.g. RELIANCE FY2022). `basis` is on every row; a pre-registration may require consistency. |
| **`ctx_inferred` is substantial** | ~50% of legacy rows. Integrated rows: 0%. |
