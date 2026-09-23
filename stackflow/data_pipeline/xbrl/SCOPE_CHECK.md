# XBRL Pipeline — Part 1 Scope Check

**Date:** 2026-09-21
**Scope:** 3-company probe only. No pipeline built. No hypothesis tested.
**Probe companies:** RELIANCE (large), VOLTAS (mid), CANFINHOME (small/mid, NBFC —
deliberately chosen to test a different taxonomy).

---

## GO / NO-GO (up front)

> **GO — but on a reduced scope, and the reasons cut both ways.**
>
> **Effort is LOWER than the 3–6 day estimate: revised to ~1.5–2 days.** Access turned out
> far better than assumed — NSE has a genuine **bulk discovery API** with filing dates and
> direct XBRL URLs, and the core tags are **identical across taxonomies**.
>
> **But scope is SMALLER and history SHORTER than the diagnostic claimed:**
> - **Debt-to-equity is NOT derivable at any effort** from these filings — there is no
>   borrowings/total-debt tag. This is a hard blocker, not a cost.
> - **History starts 2019, not 2017** — the 2017–18 records carry a placeholder, not a file.
>   **~7 folds, not the ~9 I estimated.**
>
> Net: **2 of 3 target factors, ~7 years, ~1.5–2 days.**

---

## 1. Access — much better than assumed

### 1.1 There IS a bulk discovery endpoint

`GET https://www.nseindia.com/api/corporates-financial-results?index=equities&from_date=DD-MM-YYYY&to_date=DD-MM-YYYY&period=Quarterly|Annual`

One call returns **every equity filing in the window** (~3,000 per quarter, 703 KB–2.6 MB).
No per-company URL curation is needed. Each record carries:

| field | example | use |
|---|---|---|
| `symbol` | `RELIANCE` | **joins directly to the Layer 1/2 universe** |
| `filingDate` | `19-Jan-2024 19:17` | **the point-in-time date** |
| `broadCastDate` / `exchdisstime` | `19-Jan-2024 19:21:xx` | exchange dissemination |
| `fromDate` / `toDate` | `01-Oct-2023` / `31-Dec-2023` | period covered |
| `period`, `relatingTo` | `Quarterly`, `Third Quarter` | period type |
| `consolidated` | `Consolidated` / `Non-Consolidated` | **both are filed; must pick one** |
| `audited`, `indAs` | `Un-Audited`, `Ind-AS New` | quality/taxonomy flags |
| `xbrl` | direct `.xml` URL | the data file |

### 1.2 Fully programmatic — no browser needed

NSE blocks a cold API call, but a standard cookie handshake works from plain `requests`:

```
GET https://www.nseindia.com/                    -> 403  (sets 1 cookie)
GET .../corporate-filings-financial-results      -> 200  (now 5 cookies)
GET /api/corporates-financial-results?...        -> 200  (703 KB JSON)
```

XBRL files themselves are on `nsearchives.nseindia.com` and download with **no auth and no
handshake** — all 4 probe files fetched first try (40–59 KB each).

**No anti-scraping blocker.** This was the main risk flagged in the diagnostic; it is not
present.

---

## 2. History — a correction to my own estimate

The sourcing diagnostic estimated ~9 folds from the **April 2017** XBRL mandate. **That was
wrong.** The mandate date is not the availability date. Measured directly — and note the
first measurement was itself wrong:

> **Measurement error caught:** counting records where `xbrl` was non-empty gave "100%
> coverage in every year back to 2017". False — 2017–18 records contain the literal string
> `.../xbrl/-`, a placeholder. Re-counting only URLs ending `.xml` gives the real picture.
> Same class of silent error as the identical-Wayback-snapshots bug in Layer 2; caught here
> before any build.

| year | filings | **real `.xml`** | % |
|---|---|---|---|
| 2017 | 2,946 | **0** | **0%** |
| 2018 | 3,151 | **0** | **0%** |
| 2019 | 2,328 | 2,218 | 95.3% |
| 2020 | 3,007 | 2,882 | 95.8% |
| 2021 | 2,906 | 2,906 | 100% |
| 2022 | 3,071 | 2,942 | 95.8% |
| 2023 | 3,164 | 3,164 | 100% |
| 2024 | 3,482 | 3,482 | 100% |
| 2025 | 3,865 | 3,865 | 100% |

**Usable history: 2019 → 2026 ≈ 7.5 years** — ~30 quarterly and ~7 annual observations per
company. Better than Layer 3's current 5 folds, better than Layer 2's 7, still short of
Layer 1's 22.

---

## 3. Taxonomy consistency — the good surprise

Four taxonomy families, from the filename prefix:

| taxonomy | share (2024) | probe coverage |
|---|---|---|
| `INDAS` | ~92% | RELIANCE, VOLTAS |
| `NBFC_INDAS` | ~6% | CANFINHOME |
| `BANKING` | ~2% | not probed |
| `NONINDAS` | <1% | not probed |

**The core P&L tags are identical across INDAS and NBFC_INDAS.** Verified present in all
four probe files, large-cap through small-cap NBFC:

`RevenueFromOperations` · `Expenses` · `FinanceCosts` · `ProfitBeforeTax` ·
`ProfitBeforeExceptionalItemsAndTax` · `ProfitLossForPeriod` ·
`PaidUpValueOfEquityShareCapital` · `DateOfStartOfReportingPeriod` ·
`DateOfEndOfReportingPeriod` · `Symbol` · `NatureOfReportStandaloneConsolidated`

**No per-company handling is needed.** This was the diagnostic's main effort risk and it
does not materialise. `BANKING` remains unprobed and is the one real unknown.

---

## 4. Content — the blocker

**These are *results* filings. They contain a P&L, not a balance sheet.**

| field required | status | source |
|---|---|---|
| **Interest expense** | ✅ **available, every file, every taxonomy** | `FinanceCosts` |
| **EBIT / operating profit** | ✅ **derivable** | `ProfitBeforeTax + FinanceCosts` |
| **Total equity** | ⚠️ **annual filings only** | `PaidUpValueOfEquityShareCapital + ReserveExcludingRevaluationReserves` |
| **Total debt / borrowings** | ❌ **NOT PRESENT — no tag, any file** | — |

`ReserveExcludingRevaluationReserves` is present in the **annual** filing and in the
**NBFC quarterly**, but **absent from the INDAS quarterly** filings for both RELIANCE and
VOLTAS. So equity is an annual-frequency field for most companies.

Balance-sheet content is limited to **segment** tags (`SegmentAssets`,
`SegmentLiabilities`, `UnAllocableAssets`, `UnAllocableLiabilities`) — segment-level, not a
consolidated balance sheet, and not a substitute for borrowings.

### Consequence per factor

| factor | verdict |
|---|---|
| **Interest coverage** | ✅ **fully derivable, quarterly, 2019+, all taxonomies** |
| **ROE** | ✅ **derivable annually** (~7 observations/company) |
| **Debt-to-equity** | ❌ **BLOCKED — no debt figure exists in this filing type** |

D/E would require the **annual-report balance sheet**, which is filed as a **PDF**, not
XBRL. That is the weeks-of-work PDF path the sourcing diagnostic already recommended
against.

---

## 5. A trap found and verified — do not use the ready-made ratio tags

The filings contain `DebtEquityRatio`, `InterestServiceCoverageRatio` and
`DebtServiceCoverageRatio`. **They look like exactly what this project needs. They are
unusable, and I verified this numerically rather than assuming.**

For RELIANCE FY19:

```
Derived from raw tags: (PBT + FinanceCosts) / FinanceCosts = 4.34x
Reported InterestServiceCoverageRatio tag                  = 0.04
```

Three independent problems:

1. **Scaled by ~1/100** — 4.34x is reported as 0.04.
2. **Rounded to 2 decimals** — `0.04` covers anything from ~3.5x to ~4.5x. For a
   cross-sectional tercile ranking this is **catastrophic precision loss**, and it would
   be invisible in the output.
3. **Not universally populated** — VOLTAS reports none of the three; RELIANCE's
   `DebtEquityRatio` reads `0.00`, which is simply wrong (actual ≈ 0.4).

**Anything built must derive ratios from `FinanceCosts` / `ProfitBeforeTax` / equity
components and ignore the ratio tags entirely.** Using them would have produced a
plausible-looking factor that was silently rounded into noise — the same failure class as
the unconverted currency floor and the dividend-adjustment confound.

---

## 6. Revised effort estimate

| task | original | revised | why |
|---|---|---|---|
| Filing discovery | ~1–2 d | **~0.25 d** | bulk API exists; no per-company crawling |
| Fetch + cache XBRL | ~1 d | **~0.25 d** | plain HTTP, no auth on archive host |
| Parse — interest coverage (quarterly) | ~1–2 d | **~0.5 d** | tags identical across taxonomies |
| Parse — ROE (annual) | — | **+0.5 d** | equity = paid-up + reserves, annual only |
| Point-in-time validation | ~0.5 d | **~0.25 d** | filing date is an explicit API field |
| Bank/NBFC handling | ~1 d | **~0.25 d** | NBFC verified identical; `BANKING` unprobed |
| **Debt-to-equity** | included | **∞ — blocked** | no debt tag exists |
| **TOTAL** | **3–6 days** | **≈1.5–2 days** | **for 2 of 3 factors** |

**Effort revised down ~60%. Scope revised down to 2 of 3 factors. History revised down
from ~9 folds to ~7.**

---

## 7. Recommendation

**GO, as a reduced v1.** Build:

- **Interest coverage** — quarterly, 2019+, all taxonomies. The strongest result of this
  probe, and the single most relevant factor for a leverage-prone mid/smallcap universe.
- **ROE** — annual, 2019+, ~7 observations per company. Thin, but real and point-in-time.
- **Drop debt-to-equity.** It is not a budget question; the data does not exist in this
  source. Revisit only if a balance-sheet source is found.

**Two decisions needed before Step 2.1:**

1. **Consolidated vs standalone.** Both are filed for most companies (RELIANCE and VOLTAS
   each filed both, minutes apart). A rule must be fixed **in advance** — recommend
   *prefer Consolidated, fall back to Non-Consolidated* — and recorded before any
   extraction, so it cannot be chosen later on the basis of results.
2. **`BANKING` taxonomy is unprobed.** ~2% of filings but concentrated in exactly the
   sector that is 18% of the Layer 1 universe. Worth one probe at the start of Step 2.2
   rather than discovering it at scale.

**Layer 4 note:** NSE exposes a parallel corporate-announcements API on the same host and
handshake. The discovery pattern proven here very likely transfers to concall transcripts,
which would make this a two-layer investment as the sourcing diagnostic suggested.
**Not verified in this probe** — stated as a plausible extension, not a finding.

---

## 8. What I did not verify

- **`BANKING` taxonomy tags** (§7).
- **Whether `FinanceCosts` is consistently defined** across all companies, or whether some
  report it net of capitalised interest. Spot-checking belongs in Step 2.3.
- **Whether a filing is ever revised/refiled** for the same period — the API returns one
  row per filing, so a later correction presumably appears as a separate row with a later
  `filingDate`. **This is exactly the restatement question** and must be settled in
  Step 2.3, not assumed.
- **Coverage for small caps specifically.** All three probe companies filed cleanly, but
  CANFINHOME is the smallest tested and is still a well-covered NBFC. True small-cap
  filing consistency is unproven.

---

*Part 2 not started. Awaiting review, per the checkpoint this task requires.*
