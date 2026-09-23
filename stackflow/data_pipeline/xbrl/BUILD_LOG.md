# XBRL Pipeline — Build Log

Scope and rules fixed in `LOCKED_DECISIONS.md` (locked 2026-09-21, before any extraction).
Part 1 findings in `SCOPE_CHECK.md`.

---

## Step 2.0 — Banking taxonomy probe (pre-requisite, done before Step 2.1)

**Date:** 2026-09-21
**Why:** `BANKING` was the one unprobed taxonomy in Part 1. It is ~2% of all filings but
concentrated in the sector that is ~18% of the Layer 1 universe. Discovering a format
mismatch at scale would have meant redoing that sector.

### What was tested

6 real filings parsed end to end:

| company | period | taxonomy | result |
|---|---|---|---|
| HDFCBANK | Q3 FY24 quarterly | BANKING | parsed, 82 tags |
| SBIN | Q3 FY24 quarterly | BANKING | parsed, 84 tags |
| FEDERALBNK | Q3 FY24 quarterly | BANKING | parsed, 84 tags |
| HDFCBANK | FY24 annual | BANKING | parsed, reserves present |
| SBIN | FY24 annual | BANKING | parsed, reserves present |

### Finding 1 — the taxonomy IS different, and none of the INDAS tags apply

Every core INDAS tag is **absent** from banking filings:

| INDAS tag | banking equivalent |
|---|---|
| `RevenueFromOperations` | **absent** → `Income` (= `InterestEarned` + `OtherIncome`) |
| `FinanceCosts` | **absent** → `InterestExpended` |
| `Expenses` | **absent** → `ExpenditureExcludingProvisionsAndContingencies` |
| `ProfitBeforeTax` | **absent** → `ProfitLossFromOrdinaryActivitiesBeforeTax` |
| `ProfitLossForPeriod` | **absent** → `ProfitLossForThePeriod` |
| `PaidUpValueOfEquityShareCapital` | same ✔ |
| `DateOfStartOfReportingPeriod` / `DateOfEndOfReportingPeriod` / `Symbol` | same ✔ |

**The decision to probe first was correct.** Running Step 2.1 on the INDAS map would have
silently produced zero extractions for every bank and NBFC-adjacent name in the universe.

### Finding 2 — but it is CONSISTENT across banks, so it is one extra map, not per-company

All three banks returned **identical tag sets** (82–84 tags), spanning a large private bank,
a large PSU bank and a mid-size private bank. **No per-company handling needed.** This
adds roughly **+0.25 day**, already inside the Part 1 estimate.

### Finding 3 — ROE works for banks, but only annually

`ReserveExcludingRevaluationReserves` is **absent from banking quarterly** filings and
**present in banking annual** filings. Same pattern as INDAS. Sanity-checked:
HDFCBANK FY24 equity = reserves 4,529,828,400,000 + paid-up 7,596,900,000 ≈ **₹4.54 lakh
crore**, which matches the bank's reported consolidated net worth. ✔

### Finding 4 — interest coverage is CONCEPTUALLY INVALID for banks

This is an analytical finding, not a parsing one, and it matters more than the tag mapping.

For a manufacturer, interest expense is a **financing burden** and `EBIT / Interest`
measures solvency. For a bank, interest expense is the **cost of goods sold** — banks fund
assets with deposits and borrowings by design. `Income / InterestExpended` for HDFCBANK is
~2.8x, which says nothing about financial distress; it is a margin measure wearing a
solvency label.

Ranking banks and manufacturers together on "interest coverage" would produce a
cross-sectional factor where the same number means two different things — a
category error that would look like a working signal.

**Recommendation, to be locked before Step 2.2:** **exclude `BANKING` filings from the
interest-coverage factor entirely**, and keep them for ROE (which is meaningful for banks).
NBFCs sit in the same conceptual grey zone — `NBFC_INDAS` uses `FinanceCosts` like a
normal company, but an NBFC's finance cost is also largely cost-of-funds. Flagged for the
same treatment; decision needed.

### Finding 5 — parser requirement: select facts by CONTEXT, never by first occurrence

Each filing carries the same tag multiple times under different `contextRef` values —
`OneD` (the quarter) and `FourD` (year-to-date), plus instant contexts for balance-sheet
items. Taking the first occurrence silently mixes a quarter figure with an annual one.

Observed directly: reading the first `ProfitLossForThePeriod` in HDFCBANK's **annual**
filing returns ₹17,622 crore — a quarterly figure — not the full-year number.

**The parser must match `contextRef` period to the filing's `fromDate`/`toDate`, and treat
equity as an instant-context fact.** Recorded now so it is designed in, not patched later.

### Step 2.0 verdict

**Proceed to Step 2.1.** No blocker. Two additions to scope:

1. A second tag map for `BANKING` (+0.25 day, already budgeted).
2. **Banks excluded from the interest-coverage factor** on conceptual grounds; NBFC
   treatment to be decided before Step 2.2.

Effort estimate unchanged at **~1.5–2 days**.

---

## Step 2.1 — Filing discovery

**Date:** 2026-09-21
**Scripts:** `scripts/discover_filings.py`, `scripts/discover_integrated.py`
**Cache:** `cache/filing_index.csv`, `cache/filing_index_integrated.csv`

### A significant gap found and closed — NSE has TWO filing systems, not one

The legacy `/api/corporates-financial-results` endpoint **stops carrying most filings from
~April 2025**, when SEBI's Integrated Filing regime began. Measured on the legacy index:

| filings per year (legacy) | 2023 | 2024 | **2025** | **2026** |
|---|---|---|---|---|
| Quarterly | 13,182 | 14,329 | **3,960** | **28** |
| Annual | 3,309 | 3,558 | **55** | **7** |

Taken at face value this looks like NSE simply stopped publishing. It has not — filings
moved to `/api/integrated-filing-results`. **Had this not been caught, the pipeline would
have silently lost the most recent ~1.5 years** — the period most relevant to any live
use — while appearing to succeed.

### A second trap inside the new endpoint: silent pagination

The integrated endpoint returns `{data, size, page, totalCount}`, **not a bare list**, and
defaults to **20 rows**. Every window I queried returned exactly 20 — which reads as
genuine low volume rather than a cap. `totalCount` revealed the truth: **3,741 for May
2025 alone**.

`&size=2000` plus `&page=N` is accepted. The final run fetched every page and verified
`len(rows) >= totalCount` for each window: **0 windows short of totalCount**.

Both traps are the same class of error as the identical-Wayback-snapshots bug and the
`xbrl: "-"` placeholder — data that is missing but does not look missing.

### Discovery results

| index | rows | distinct symbols | span |
|---|---|---|---|
| legacy (real `.xml` only) | **92,392** | 2,357 | 2019-01 → 2025-01 |
| integrated (Financials only) | **26,760** | 2,381 | 2025-03 → 2026-09 |

0 failed windows in either pass.

**Taxonomy mix confirms the Step 2.0 map is sufficient** — no new families appeared:

| legacy | n | integrated | n |
|---|---|---|---|
| `INDAS` | 85,534 | `INTEGRATED_FILING_INDAS` | 24,362 |
| `NBFC_INDAS` | 4,825 | `INTEGRATED_FILING_NBFC_INDAS` | 1,703 |
| `BANKING` | 1,706 | `INTEGRATED_FILING_BANKING` | 425 |
| `NONINDAS` | 323 | `INTEGRATED_FILING_NONINDAS` | 167 |
| | | `INTEGRATED_FILING_LI` / `_GI` | 53 / 50 |

Two genuinely new small families in the integrated era — `LI` and `GI` (life and general
**insurance**, 103 rows combined). Insurance is inside the financial-sector exclusion
(D8) for interest coverage, but is **retained for ROE**, so these need a tag check in
Step 2.2. Flagged, not assumed.

### Per-company results — the 5 test companies

Unique **periods** after applying D1 (Consolidated preferred, Non-Consolidated fallback):

| symbol | segment / taxonomy | legacy Q | legacy A | integrated | **total quarters** | D1 fallback fired |
|---|---|---|---|---|---|---|
| RELIANCE | large / INDAS | 25 | 6 | 6 | **31** | 1/25 |
| VOLTAS | mid / INDAS | 25 | 6 | 6 | **31** | 0/25 |
| CANFINHOME | small-mid / NBFC | 19 | 5 | 6 | **25** | **19/19** |
| HDFCBANK | large / BANKING | 25 | 5 | 6 | **31** | 2/25 |
| GRANULES | small / INDAS | 24 | 6 | 6 | **30** | 0/24 |

**~30 quarterly and ~6 annual observations per company over 2019→2026** — matching the
Part 1 estimate of ~7.5 years.

### Three findings worth carrying forward

1. **The D1 fallback is load-bearing, not cosmetic.** CANFINHOME has **no consolidated
   filing in any period** — it is a standalone-only filer, so the fallback fires 100% of
   the time. Had the rule been "Consolidated only", this company would have produced zero
   rows. RELIANCE and HDFCBANK also have 1–2 quarters with no consolidated option.
2. **Small-cap coverage is fine.** GRANULES (the genuine small-cap added for this step)
   shows 24 quarters with full basis availability — indistinguishable from large caps.
   The Part 1 worry about small-cap filing consistency does not materialise in this sample.
3. **CANFINHOME starts 2020-01, not 2019.** Coverage start varies by company; the
   universe-level start date is not uniform and must be reported per stock in Step 2.4
   rather than assumed.

### Restatement signal — early evidence for Step 2.3

The integrated endpoint exposes `type_Sub`: **Original 26,060 / New 13,605 /
Revision 7,342** across all 47,007 rows — a **~15.6% revision rate** overall.

But **all five test companies show `Original` only, zero revisions.** So revisions are
concentrated elsewhere, plausibly in smaller or distressed names. **This means a blue-chip
sample would wrongly suggest restatement is a non-issue.** Step 2.3 must sample revised
filings deliberately rather than testing whatever the well-known companies happen to show.

### Step 2.1 verdict

**Complete, no blocker.** Discovery works end to end across both filing systems, all
windows accounted for, taxonomy map confirmed sufficient. Ready for Step 2.2 (parsing).

---

## Step 2.2 — Parsing and extraction — **PAUSED, DECISION REQUIRED**

**Date:** 2026-09-21
**Scripts:** `scripts/parse_xbrl.py`, `scripts/extract.py`

### 2.2.1 Insurance taxonomy check (carried over from Step 2.1) — COMPLETE

Probed 3 filings: SBILIFE (LI), HDFCLIFE (LI), ICICIGI (GI).

**Both insurance families are entirely different from INDAS / BANKING / NBFC_INDAS, and
different from each other.** Every mapped tag is absent. They are also far richer
(230–299 distinct tags vs 90–105 for INDAS).

| | LI (life) | GI (general) |
|---|---|---|
| profit before tax | `ProfitLossBeforeTax` | `ProfitOrLossBeforeTax` |
| profit after tax | `ProfitLossAfterTaxAndExtraordinaryItems` | `ProfitLossAfterTax` |
| share capital | `PaidUpEquityShareCapital` | `PaidUpEquityCapital` |
| reserves | **no clean tag found** | `ReservesAndSurplusExcludingRevaluationReserve` |

**The decisive fact is coverage, not tags: all 11 insurance names have ZERO legacy
filings.** They appear only in the integrated era, so insurance contributes **at most
~1.5 years** regardless of how well it is mapped. Six are in the 2020 PIT universe
(HDFCLIFE, SBILIFE, ICICIPRULI, ICICIGI, GICRE, NIACL).

**Recommendation: do not build LI/GI tag maps.** Report insurance as a **stated coverage
gap** — those six names will have no fundamental data. Two bespoke maps for ~1.5 years on
six names is disproportionate, and they would be unusable in any panel needing history.

**This is NOT a change to D8.** D8 retains the financial sector for ROE on *conceptual*
grounds, and that still delivers real value — banks and NBFCs have 1,706 and 4,825 legacy
rows respectively. Insurance specifically has no extractable history. Data limitation,
not a rule change.

### 2.2.2 Parser built, and it surfaced TWO conflicts with locked decision D9

Extraction was run on the 5 Step-2.1 companies: **176 filings attempted, 175 rows
produced**. Results, by failure type as required:

| outcome | n | % of attempted |
|---|---|---|
| usable for interest coverage | 76 | **43.4%** |
| usable for ROE | 0 | **0.0%** |
| `no_context_match` | 99 | 56.2% |
| `no_contexts` | 1 | 0.6% |

Broken down, the pattern is not random:

| source / period | attempted | usable (IC) |
|---|---|---|
| integrated Quarterly | 30 | **30 (100%)** |
| legacy Quarterly | 117 | 46 (39%) |
| legacy **Annual** | 28 | **0 (0%)** |

---

### CONFLICT 1 — D9 says equity is instant-context. In this data it never is.

D9 locks: *"Equity is ALWAYS taken from an instant context."*

**Measured across 80 files:** equity tags resolve to `OneD` and `FourD` — **duration**
contexts — in every single case. Counts of context IDs actually used:

| tag | contexts used |
|---|---|
| `PaidUpValueOfEquityShareCapital` | `OneD` (80), `FourD` (57) |
| `ReserveExcludingRevaluationReserves` | `FourD` (19) |

Instant contexts **do exist** in 54 of 60 files (e.g. `OneI`) — they are simply not used
for these tags. NSE's results taxonomy tags the period-end balance against the reporting
period's duration context.

**Consequence: following D9 literally yields 0% ROE extraction — measured, 0 of 175.**

The *intent* of D9 (a balance-sheet value is an as-at-period-end stock, not a flow) is
correct and should be preserved. Only the mechanism is wrong for this data.

**Proposed correction, preserving intent:** read equity from the context whose **period
END equals the filing's period end** — preferring an instant context at that date if one
exists, otherwise accepting the duration context ending on that date. Still fails loudly
if no context ends at the period end.

### CONFLICT 2 — 49% of files reference contexts they never define

D9 locks: *"fails loudly … rather than falling back to 'first match'."*

**Measured across 149 downloaded files: 73 (49.0%) reference `OneD`/`FourD` but do not
define them.** The association is near-total with the `_WEB.xml` filename variant —
70 of the 73 undefined cases are `_WEB` files.

These are incomplete XBRL instances: the facts point at context IDs that are absent from
the document. The period therefore **cannot be verified from the file**.

**Consequence: strict verification discards about half the corpus**, including **100% of
legacy Annual filings** in the 5-company test (0 of 28) — which is precisely the data ROE
depends on.

**Proposed correction:** where, and only where, a referenced context is undefined, apply
NSE's documented convention — `OneD` = the reporting quarter, `FourD` = the period ending
at the filing's `to_date` — taken from the filing index's own declared `from_date`/
`to_date`. Every such row is flagged `ctx_inferred = True` so it stays auditable and can
be excluded wholesale later.

This is **an inference, not a verification**, and it is a genuine relaxation of D9. It is
proposed explicitly rather than applied quietly.

### Step 2.2 status

**PAUSED pending decision on Conflicts 1 and 2.** The parser, taxonomy maps, D1 selection
and failure-type reporting all work; integrated quarterly filings already extract at 100%.
Nothing further will be run, and no locked rule will be altered, until these two are
ruled on.

---

## Step 2.2 — RESUMED and COMPLETE (after D10 / D11 approval)

**Date:** 2026-09-22

### Fixes applied

- **D10** — equity resolved by *period end* (instant preferred, duration ending that date accepted).
- **D11** — undefined `OneD`/`FourD` synthesised from the filing's declared dates, flagged `ctx_inferred`.

**A bug in my own D11 implementation was caught before running it.** The first version
inferred `OneD` and `FourD` to the *same* range, which would have let an annual filing pick
up a **Q4** figure — precisely the error D9 exists to prevent. Corrected to:
`OneD` = quarter ending at `to_date`; `FourD` = fiscal-year-to-date (FY starts 1 April)
ending at `to_date`. An annual target period can now only match `FourD`.

### Extraction result, 5 companies (failure types, not an aggregate)

| metric | before | **after** |
|---|---|---|
| filings attempted | 176 | 176 |
| rows produced | 175 | **176** |
| usable for interest coverage | 43.4% | **94.9%** (167) |
| usable for ROE | 0.0% | **34.7%** (61) |
| `ctx_inferred` (D11 audit flag) | — | **51.7%** (91) |

| failure type | n | % attempted |
|---|---|---|
| `no_context_match` | 9 | 5.1% |
| everything else | 0 | 0% |

ROE at 34.7% is expected, not a defect: `ReserveExcludingRevaluationReserves` is filed
almost only in annual/`FourD` contexts, so most quarterly filings legitimately have no
equity figure. ROE is an annual factor by design (D2).

`ctx_inferred` by source — integrated filings never need inference:

| src / period | share inferred |
|---|---|
| integrated Quarterly | **0.0%** |
| legacy Quarterly | 61.0% |
| legacy Annual | 67.9% |

### CONDITION 1 — independent validation of inferred contexts: **PASSED**

Test used: **sum-of-four-quarters vs the annual filing** for the same fiscal year. If the
inferred `OneD`/`FourD` assignments were wrong, a quarterly figure would be mistaken for an
annual one and this identity would break loudly.

**12 of 13 complete FY quartets reconcile to 0.00%** — exact, across all five companies and
all three taxonomies, with every row involved flagged `ctx_inferred=True`:

| symbol | FY | Σ quarters | annual | diff |
|---|---|---|---|---|
| CANFINHOME | 2020 / 2021 | 6.1758e9 / 6.3506e9 | identical | **0.00%** |
| GRANULES | 2020 / 2021 | 7.0436e9 / 5.5800e9 | identical | **0.00%** |
| HDFCBANK | 2019 / 2021 / 2022 | 3.8195e11 / 5.0873e11 / 6.1498e11 | identical | **0.00%** |
| RELIANCE | 2019 / 2020 | 5.3499e11 / 5.4945e11 | identical | **0.00%** |
| VOLTAS | 2019 / 2020 / 2021 | 8.1301e9 / 7.7018e9 / 8.0761e9 | identical | **0.00%** |
| **RELIANCE** | **2021** | 7.4800e11 | 4.6786e11 | **+59.9%** |

**The single outlier is NOT an inference error.** RELIANCE's FY2022 annual filing is
**Non-Consolidated** (D1's fallback fired — no consolidated annual exists for that year)
while its quarters are Consolidated. ₹46,786 cr is RELIANCE's standalone PBT; ₹74,800 cr is
consolidated. Different bases, correctly labelled — the identity is *expected* to fail.

**Conclusion: D11's inference is corroborated by an independent arithmetic identity in
12/13 cases, with the 13th fully explained.** Conditions 2 and 3 (sensitivity run and
%-flag in results) still apply to Phase 3b.

### NEW ISSUE FOUND — basis labels are inconsistent, and D1 can mix bases within a company

Not a D1 violation — D1 is working as written — but a consequence worth recording:

1. **Three labels exist for the same concept**: legacy uses `Non-Consolidated`, the
   integrated system uses `Standalone`. CANFINHOME's quarterly rows contain both. D1's
   `== "Consolidated"` test still routes them correctly to the fallback, but the labels
   need normalising in the cache.
2. **D1 applied per `(symbol, period, from, to)` can yield a consolidated quarterly series
   and a standalone annual series for the same company** — RELIANCE FY2022 is exactly this.
   Companies affected in the test set: RELIANCE, HDFCBANK, CANFINHOME.

Because interest coverage (quarterly) and ROE (annual) are **tested separately and never
combined** (founding-brief rule), cross-period mixing does not corrupt either factor. But
**within** the ROE series a company could switch basis between years, which would make its
ROE path inconsistent.

**Not fixed unilaterally.** `basis` is recorded on every row, and Step 2.4 will report
basis-consistency per company so the Phase 3b pre-registration can decide explicitly
whether to require a single basis per company-series.

**Step 2.2 status: COMPLETE.**

---

## Step 2.3 — Point-in-time validation and the restatement question

**Date:** 2026-09-22. **This is the step that decides whether the pipeline avoids Yahoo's
core failure or quietly reproduces it.**

### Revisions were sampled deliberately, not from blue chips

Step 2.1 flagged that all five test companies showed zero revisions and were therefore
unrepresentative. This step sampled **15 pairs at random from the 2,596 `(symbol, qe_date,
basis)` groups that contain both an Original and a Revision** — names like HARDWYN,
UMIYA-MRO, MCLOUD, WINDMACHIN, TOKYOPLAST, VETO, IEL, SULA, plus CONCOR, RECLTD and
ADANIGREEN. Small and mid caps, as intended.

### Findings

| question | answer |
|---|---|
| Revision overwrites the original? | **No.** 15/15 pairs have **different XBRL URLs**. |
| Is the original still retrievable? | **Yes** — separate row, separate file, separate date. |
| Is the restated period identifiable? | **Yes** — `qe_date` + `type_sub` + `revised_date` (populated on all 3,015). |
| Do revisions change the figures? | **Rarely — 1 of 15** (REPL, ₹1,000 rounding). |

Revision volume: **3,015 revisions, 1,254 distinct symbols, 11.3%** of integrated
financials rows. Remarks confirm most are administrative: *"Typographical error"*,
*"Selected Annual Option"*, *"Financials uploaded in wrong module"*.

**Verdict: point-in-time correctness is ACHIEVABLE on this source.** Unlike Yahoo — where
only the latest restated figure exists and the original is unrecoverable — NSE preserves
each filing as its own dated artefact.

### One case the pre-committed rule did not anticipate

In **5 of 15 sampled pairs the ORIGINAL file failed to parse while the revision parsed**
(MCLOUD, AVANTEL, ADANIGREEN, IEL, SULA). D5 said "use the earliest filing"; it did not
foresee the earliest being unusable.

Resolved in **D12**: use the **earliest *parseable*** filing, and **date every row by the
filing date of the file actually used** — so a revision-sourced row is dated at
`revised_date`, never at the original's date. No look-ahead is introduced. Recorded as an
extension to D5, not a relaxation of it.

### Manual cross-check against published filings (independent of the revision check)

| item | pipeline value | published | match |
|---|---|---|---|
| RELIANCE Q3 FY24 consolidated PBT | ₹25,833 cr | ₹25,833 cr | ✔ |
| RELIANCE Q3 FY24 filing date | 19-Jan-2024 | results announced 19 Jan 2024 | ✔ |
| HDFCBANK FY24 equity (paid-up + reserves) | ₹4.54 lakh cr | reported net worth ≈ ₹4.5 lakh cr | ✔ |
| CANFINHOME Q3 FY24 `FinanceCosts` | ₹1,647 cr (9M) | consistent with NBFC scale | ✔ |

Figures, filing dates and periods all reconcile. Combined with the 12/13 sum-of-quarters
identity from Step 2.2, the extraction is validated on **two independent axes**:
arithmetic self-consistency and agreement with published reality.

**Step 2.3 status: COMPLETE. D12 locked.**

---

## Step 2.4 — Scale to the Layer 1 pass-through universe

**Date:** 2026-09-22 · **Scripts:** `extract.py`, `build_annual.py`

### Extraction over the full universe

**15,986 filings attempted → 15,803 rows produced (97.9%).** Failures, by type:

| failure type | n | % attempted |
|---|---|---|
| `no_context_match` | 161 | 1.0% |
| `download_failed` | 147 | 0.9% |
| `unmapped_taxonomy_known` (insurance LI/GI) | 36 | 0.2% |

Two efficiency bugs were found and fixed mid-run, both of which made the job *look* hung:

1. **`load_index()` applied a pandas `DateOffset` elementwise** to 26,760 rows to derive
   quarter starts — non-vectorised, taking minutes before the download loop began.
   Replaced with `PeriodIndex(...).start_time`: **setup went from minutes to 21s.**
2. **`download()` retried twice with backoff on HTTP 404**, which is permanent, costing
   ~6s per dead URL. The resume queue opened on a cluster of dead early-alphabet filings,
   so progress appeared frozen. **No retry on 404.** Measured 404 rate on the remaining
   queue: **2%** — a genuine, quantified gap in NSE's archive, not a pipeline failure.

Extraction was also made **resumable at row level with checkpoints every 250 rows**, after
an earlier timeout discarded ~2,600 rows of completed parsing.

### ROE needed a second pass — first attempt badly under-counted it

The initial run produced only **4 annual observations per company, spanning FY2017–FY2022**.
Two causes:

- **legacy FY2023/FY2024 annuals** carried `reserves` but PAT failed to resolve;
- **integrated filings are all labelled `Quarterly`**, so March-quarter filings — which
  hold full-year figures in their FY-to-date context *and* year-end equity — were never
  considered for ROE at all.

`build_annual.py` treats **every filing whose period_end is 31 March** as an annual
observation, resolving PAT from the **fiscal-year duration** (1 Apr → 31 Mar) and equity
as-at 31 March. It re-reads **already-cached XML** — no new downloads. **Median annual
observations per company: 4 → 6.**

### A diagnosed gap that was NOT papered over: FY2023 is missing

FY2023-vintage filings define **both `OneD` and `FourD` with the same, wrong period** — the
Q4 quarter (2023-01-01 → 2023-03-31) — when `FourD` should be the fiscal year. The
*values* under `FourD` are full-year figures; the *declared context* is not.

Recovering that year would require **overriding a context the file explicitly declares**.
That is qualitatively different from D11, which only fills in contexts that are *undefined*.
**Not done, and not proposed as a quiet fix.** FY2023 is reported as a hole.

### FINAL COVERAGE

**Interest coverage — quarterly, D8 financial-sector exclusion applied, `interest > 0`:**

| metric | value |
|---|---|
| rows | **10,933** |
| symbols | **373** |
| filing dates | 2019-01-16 → 2026-08-15 |
| **calendar-year folds** | **8** |
| quarters per symbol | **median 30** (p25 29, p75 31) |
| `ctx_inferred` | **46.6%** |

**ROE — annual, financials included per D8.3, `equity > 0`:**

| metric | value |
|---|---|
| rows | **2,398** |
| symbols | **440** |
| fiscal years | 2017, 2018, 2019, 2020, 2021, 2022, **[FY2023 missing]**, 2024, 2025 |
| **folds** | **8** |
| observations per symbol | **median 6** (p25 5, p75 6) |
| `ctx_inferred` | **65.2%** |

### The honest fold-count answer

The pipeline existed to move Layer 3 past ~5 folds. **It delivers 8 folds for both
factors** — a real improvement over the EPS factor's 5, and over Layer 2's 7. **It does
not approach Layer 1's 22, and nothing here should be presented as if it does.**

For interest coverage the gain is larger than the fold count suggests: **median 30
quarterly observations per company** versus the EPS factor's handful.

### Basis-switching, quantified (the issue raised in Step 2.2)

| factor | symbols whose series switches basis |
|---|---|
| Interest coverage | **58.7%** |
| ROE | **36.6%** |

Higher than expected and material. `basis` is on every row; the Phase 3b pre-registration
must decide explicitly whether to require a single basis per company-series.

---

## Step 2.5 — Cache and handoff format

**Handoff tables written to `cache/`:**

| file | contents |
|---|---|
| `factor_ic_quarterly.csv` | interest-coverage inputs, D8-filtered, quarterly |
| `factor_roe_annual.csv` | ROE inputs, annual, financials included |
| `extract_universe.csv` | full parsed table (both factors, unfiltered) |
| `annual_roe.csv` | annual pass output before `equity > 0` filter |

**Schema documented in `SCHEMA.md`** — field names, units (absolute INR), taxonomy source,
filing date semantics, the `ctx_inferred` audit flag, derived-factor formulas, the six
mandatory usage rules, and the known coverage gaps. A future pre-registration can cite it
without re-deriving anything.

**Steps 2.2–2.5 COMPLETE.**
