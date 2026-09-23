# XBRL Pipeline — LOCKED DECISIONS

**Locked: 2026-09-21, BEFORE any extraction was run.**
**Authority: explicit user decision at the Part 1 checkpoint.**

These rules are fixed in advance so they cannot be re-chosen later on the basis of what
the extracted data looks like. Changing any of them requires a dated addendum stating what
changed and why — not an edit.

---

## D1. Consolidated vs Standalone — LOCKED

**Rule: prefer `Consolidated`. Fall back to `Non-Consolidated` only when no consolidated
filing exists for that company and period.**

Most companies file both, minutes apart (RELIANCE and VOLTAS each did). Without a rule
fixed in advance, the choice could drift toward whichever produces a better-looking factor.

Implementation: for each `(symbol, fromDate, toDate, period)` group, select
`consolidated == "Consolidated"` if present, else `"Non-Consolidated"`. The chosen value is
recorded per row in a `basis` field so any downstream analysis can see which was used and
how often the fallback fired.

## D2. Scope — LOCKED

| factor | status |
|---|---|
| **Interest coverage** | **IN** — quarterly, 2019+ |
| **ROE** | **IN** — annual, ~7 observations/company |
| **Debt-to-equity** | **OUT** — deferred to a separate future PDF/annual-report task |

D/E is not deferred for effort reasons. **The data does not exist in this filing type** —
there is no borrowings or total-debt tag in any probe file. It is recorded as a distinct
future task, not as a gap in this one.

## D3. Ratio tags — BANNED

`DebtEquityRatio`, `InterestServiceCoverageRatio` and `DebtServiceCoverageRatio` **must not
be used**, even where populated.

Verified in Part 1: RELIANCE FY19 derived interest coverage = **4.34x**, reported tag =
**0.04** — scaled ~1/100, rounded to 2 decimals (so one value spans ~3.5–4.5x), and
inconsistently populated. Using them would silently round a factor into noise.

**All ratios are derived from raw tags:**

```
interest_coverage = (ProfitBeforeTax + FinanceCosts) / FinanceCosts
total_equity      = PaidUpValueOfEquityShareCapital + ReserveExcludingRevaluationReserves
ROE               = ProfitLossForPeriod / total_equity
```

## D4. Point-in-time rule — LOCKED

A filing's figures are usable **only from its `filingDate` forward**. The period-end date
(`toDate`) is **never** used as the availability date. This is the failure mode that made
yfinance unusable and it is not repeated.

## D5. Restatement handling — MUST BE MEASURED, NOT ASSUMED

The working assumption is that a correction/refiling appears as a **separate row with a
later `filingDate`** for the same `(symbol, period)`. **This is explicitly unverified.**

Step 2.3 must measure it directly: count duplicate `(symbol, fromDate, toDate, basis)`
groups with differing `filingDate`, and check whether their values differ. Until measured,
no claim about as-reported status may be made.

If duplicates exist, the pre-committed rule is: **use the earliest filing** (what was
actually knowable first), and record the existence of later revisions in a
`n_revisions` field rather than discarding them.

## D6. Universe and history — LOCKED

- History: **2019-01-01 onward** (2017–18 carry a `-` placeholder, not a file).
- Universe: the Layer 1 pass-through stock universe, joined by NSE `symbol`.
- Taxonomies handled: `INDAS`, `NBFC_INDAS`, `BANKING`, `NONINDAS`.

## D7. This task ends in a validated cache, not a result

**No Layer 3 or Layer 4 hypothesis test is run in this task.** No factor is scored,
ranked, combined, or tested against forward returns. The deliverable is data plus a
documented schema.

---

## D8. Financial-sector exclusion from INTEREST COVERAGE — LOCKED

**Added 2026-09-21 by explicit user decision, before Step 2.2.**

**Rule: financial intermediaries are excluded from the interest-coverage factor entirely.
They are RETAINED for ROE, where the metric is valid.**

**Reason (user's, recorded so the rule is not re-argued later):** an NBFC's business model
is fundamentally the same as a bank's — borrow wholesale, lend retail. Its "interest
expense" is **cost of funds**, not a financing burden. The difference between a bank and an
NBFC is a regulatory label, not business economics. Ranking a manufacturer and an NBFC on
the same interest-coverage scale produces a number that looks identical but means two
different things.

### D8.1 Exclusion is a UNION of two tests — not taxonomy alone

Verified empirically on 3,482 filings from Q3 FY24 joined to the Layer 1 universe:

| financial-industry stocks | XBRL taxonomy filed under |
|---|---|
| 34 | `NBFC_INDAS` |
| 30 | `BANKING` |
| **12** | **plain `INDAS`** |

**A taxonomy-only filter would have let ~8 financial-industry names through** (BSE,
CARERATING, CDSL, CGCL, CRISIL, ICRA, IEX, NAM-INDIA). The reverse leak also exists:
2 non-financial-industry names (MAHSCOOTER, WESTLIFE) file under `BANKING`/`NBFC_INDAS`.

**Therefore a stock is excluded from interest coverage if EITHER holds:**

1. its NSE macro industry is **`FINANCIAL SERVICES`** (the combined industry — this catches
   NBFC, Housing Finance, Insurance, PSU Bank and Private Bank, which are *not* separable
   by name at the industry level), **OR**
2. its filing taxonomy is **`BANKING`** or **`NBFC_INDAS`**.

Belt and braces, deliberately. Under-exclusion causes a silent category error;
over-exclusion costs a handful of names.

### D8.2 Known over-exclusion, accepted — flagged for reversal if wanted

The union rule also removes ~7 **fee-based** financial names that are **not**
balance-sheet intermediaries: exchanges (BSE, IEX), a depository (CDSL), rating agencies
(CRISIL, ICRA, CARERATING) and an asset manager (NAM-INDIA). For these, interest coverage
*is* meaningful in the ordinary sense — they carry little debt and their interest expense
is a genuine financing cost, not cost of funds. Only CGCL among the eight is a true lender.

This over-exclusion is **accepted as the conservative direction** and is recorded here
rather than silently applied. It costs ~7 names out of ~400. If a later phase wants them
back, that is a documented, reversible carve-out — not a rediscovery.

### D8.3 ROE is unaffected

Financial intermediaries stay in the ROE factor. Banking **annual** filings carry
`ReserveExcludingRevaluationReserves`, verified against HDFCBANK FY24 (equity ≈ ₹4.54 lakh
crore, matching reported net worth).

---

## D9. Context matching — LOCKED

**Added 2026-09-21 by explicit user decision, before Step 2.2.**

Every filing repeats the same tag under multiple `contextRef` values. Taking the first
occurrence silently mixes periods — observed directly: the first `ProfitLossForThePeriod`
in HDFCBANK's **annual** filing returns a **quarterly** figure (₹17,622 crore), not the
full-year number.

**Rules:**

1. **Quarterly figures** — match the `OneD`-type context whose period equals the filing's
   `fromDate`/`toDate` quarter.
2. **Annual figures** — match the `FourD`/full-year context, i.e. the duration context
   spanning the filing's full `fromDate` → `toDate`.
3. **Equity is ALWAYS taken from an instant context.** Balance-sheet items are
   point-in-time stocks, not period flows, and must never be read from a duration context.

**Implementation requirement:** the parser resolves each fact by explicitly matching the
context's period to the target period, and **fails loudly** (records the filing as a parse
failure with a reason) rather than falling back to "first match" when no context matches.
A silent fallback here is exactly the class of error this rule exists to prevent.

---

## D10. Equity context resolution — LOCKED (supersedes D9 clause 3)

**Locked 2026-09-22 by explicit user decision. This is a REINTERPRETATION, not a relaxation.**

D9 clause 3 said equity must come from an *instant* context. The intent — "equity must be
a number as at a fixed date, not a period flow" — was correct. The **assumption** that NSE
would label it `instant` was wrong. Measured across 80 files, equity tags resolve to
`OneD`/`FourD` **duration** contexts in 100% of cases; instant contexts exist in the files
but are never used for equity.

**Rule:** equity is read from the context whose **period END equals the filing's period
end**. If an instant context exists at that date, prefer it. Otherwise accept the duration
context ending on that date. **Fail loudly if no context ends at the period end.**

Same principle, correct implementation. No audit flag is required, because the value
retrieved is still the as-at-period-end balance.

## D11. Undefined-context inference — CONDITIONALLY APPROVED

**Locked 2026-09-22 by explicit user decision. This IS a genuine relaxation of D9 and is
recorded as such.**

49% of files (73/149 measured; 70 of those 73 are `_WEB.xml` variants) reference `OneD`/
`FourD` without defining them. The period cannot be verified from the file. Strict
verification discards ~half the corpus, including **100% of legacy Annual filings** — the
data ROE entirely depends on.

**Rule:** where, and ONLY where, a referenced context is undefined, apply NSE's convention
— `OneD` = the reporting quarter, `FourD` = the period ending at the filing's `to_date` —
using the filing index's own declared `from_date`/`to_date`. Every such row is flagged
`ctx_inferred = True`.

**This is an inference, not a verification.** Approved because the risk is stated and
auditable, not because it is safe.

### Three binding conditions (all mandatory, none optional)

1. **Sample validation before use.** Take 10–15 `ctx_inferred = True` rows and cross-check
   the inferred period against an independent source — principally the same
   company-period appearing in the integrated system, where the period is verified.
   Reported before the data is used in any test.
2. **Mandatory sensitivity check in Phase 3b.** Every grid is run **twice** — once
   including `ctx_inferred` rows, once excluding them. If both runs give the **same
   verdict**, the inference was safe. If the verdict **changes**, the ROE result rests on
   inferred data and must be reported as **"PROVISIONAL — unverified-context-dependent"**,
   never as a confident finding.
3. **The flag appears in every final results table.** The **% of rows that were
   `ctx_inferred`** is shown alongside results, so any reader can see how much of the
   finding stands on assumption.

---

## D12. Revision handling — LOCKED after Step 2.3 measurement

**Locked 2026-09-22, after measuring rather than assuming (D5 required this).**

### What was measured

- **3,015 revisions** across **1,254 distinct symbols** — 11.3% of integrated financials rows.
- **2,596 `(symbol, qe_date, basis)` groups contain BOTH an `Original` AND a `Revision`.**
  Only **1** group has a Revision with no Original.
- **Original and Revision have DIFFERENT XBRL URLs in 15 of 15 sampled pairs.**
  The original file is preserved at its own URL and is **never overwritten**.
- Parsing both files in 15 sampled pairs: **figures changed in only 1 of 15** (REPL, a
  ₹1,000 rounding difference). Remarks confirm most revisions are metadata fixes
  ("Typographical error", "Selected Annual Option", "uploaded in wrong module").

### Answers to the three Step 2.3 questions

1. **Does querying "as of original filing date" return the original figure?** **Yes.**
   The original row and its file persist independently, so filtering on filing date
   returns as-reported data.
2. **Separate row, or overwrite?** **Separate row, separate URL, separate date.**
   Point-in-time correctness is therefore **achievable**, not merely desirable.
3. **Is the restated period identifiable?** **Yes** — `qe_date` identifies the period and
   `type_sub` marks Original vs Revision, with `revised_date` populated on all 3,015.

### The rule

**Use the EARLIEST PARSEABLE filing per `(symbol, period, basis)`, and date every row by
the filing date of the file actually used.**

- Normal case: the `Original` is used, dated at its own broadcast date.
- **Exception found in measurement:** in **5 of 15** sampled pairs the *original* file was
  unparseable while the revision parsed. D5 anticipated "use the earliest"; it did not
  anticipate the earliest being unusable. In that case the revision is used **and dated at
  `revised_date`, never at the original's date.**
- This introduces **no look-ahead**: the figure is only made available from the date the
  file that supplied it became public, exactly as D4 requires.
- Every row records `type_sub` and `n_revisions` so the choice is auditable.

This is an **extension** of D5 to a case D5 did not foresee, not a relaxation of it — the
point-in-time guarantee is preserved intact.

---

## D13. Basis-switching handling — LOCKED

**Locked 2026-09-22 by explicit user ruling, BEFORE any Phase 3b grid was generated.**

Measured: **58.7%** of interest-coverage series and **36.6%** of ROE series switch between
Consolidated and Standalone/Non-Consolidated at some point.

**Rule:**

1. **Do NOT enforce a single basis per company-series.** The full series is kept.
2. **Exclude only the ONE observation immediately following a basis switch**, for that
   company and that factor. Not the company, not the series — only the single period where
   a mechanical basis-change artefact is most likely to look like a real move.
3. **Report basis-switch rate as a diagnostic in every results table**, exactly as
   `ctx_inferred %` is reported (D11 condition 3).
4. **One sensitivity check:** repeat the primary grid restricted to companies that never
   switch basis. **State the subset size found.** If it is too small for fold-level
   analysis, say so plainly and skip it — do not force a result from too few names.
