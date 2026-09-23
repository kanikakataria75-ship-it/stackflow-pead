# Layer 3 Data Sourcing — Point-in-Time Leverage / Solvency Data

**Date:** 2026-09-21
**Scope:** sourcing and data-quality diagnostics only. No hypothesis tested, no pipeline
built, no scraper written. Ends in a recommendation.
**Does not modify** `layer3/pre_registration.md` (frozen) or any Layer 1 / Layer 2 file.

---

## VERDICT (up front)

> **No free source clears all three bars as a drop-in dataset.**
> **Exactly one free path does clear them, but it is an extraction project, not a
> download: BSE/NSE XBRL financial-results filings, which carry genuine
> exchange-timestamped filing dates and are as-originally-submitted.**
> Realistic achievable history: **~2017 → 2026, ≈36 quarters / 9 folds** — better than
> Layer 2's 7, short of Layer 1's 22.
>
> Every "easy" source (Screener, Tickertape, yfinance) fails the **same single
> requirement — no filing date** — and more data with the same structural flaw is not
> progress.

---

## 1. The bar, restated

| # | requirement |
|---|---|
| **R1** | Actual **filing/announcement date**, not just period-end. *(This is what killed yfinance.)* |
| **R2** | **As-originally-reported**, or a clearly stated/bounded restatement limitation. |
| **R3** | Enough history × breadth to get fold count nearer Layer 1's 22 than Layer 2's 7. |

---

## 2. Candidates actually probed

Every source below was probed empirically — real tickers, real responses, real field
names — in the same way yfinance was. Nothing here is asserted from reputation.

### 2.1 yfinance — the incumbent baseline (for comparison)

| | |
|---|---|
| **R1 filing date** | ❌ statements carry period-end only |
| **R2 as-reported** | ❌ latest-restated, undisclosed |
| **R3 history** | ❌ **4–5 annual periods** (oldest 2022-03-31) |

*Exception already in use:* `Ticker.earnings_dates` **does** carry real announcement dates
(24 quarters, ~2020-10 → 2026) — which is precisely why EPS growth was the one testable
factor. It has **no balance-sheet items**, so it cannot serve debt/ROE/interest coverage.

### 2.2 Screener.in — best free *values*, no dates

Probed `screener.in/company/RELIANCE/` (no login required for company pages).
13 tables parsed. Line items needed for all three target factors **are present**:

| factor | derivable from | available |
|---|---|---|
| Debt-to-equity | `Borrowings` ÷ (`Equity Capital` + `Reserves`) | ✔ |
| ROE | `Net Profit` ÷ (`Equity Capital` + `Reserves`) | ✔ |
| Interest coverage | `Operating Profit` ÷ `Interest` | ✔ |

| | |
|---|---|
| **R1 filing date** | ❌ **columns are period-end only** (`Mar 2015` … `Mar 2026`) |
| **R2 as-reported** | ❌ not disclosed; presentation implies current values |
| **R3 history** | ✅ **12 years annual (Mar 2015→Mar 2026)**, 13 quarters |

**No public API.** Confirmed: Screener offers CSV/Excel *export* behind login, not an API
([support docs](https://support.screener.in/article/28-export-screen-results),
[premium](https://www.screener.in/premium/)). `/company/RELIANCE/export/` returns 404 when
logged out.

**Notable:** Screener's "Documents" section does not contain dates itself — it **links out
to BSE corporate announcements and annual-report PDFs**. Screener is a presentation layer
over BSE filings. That is the tell pointing to §2.5.

### 2.3 Tickertape — free JSON, 10 years, still no dates

Probed `api.tickertape.in/search` (200 OK, returns `sid`) and the stock page's
`__NEXT_DATA__` payload (437 KB parsed).

| | |
|---|---|
| **R1 filing date** | ❌ payload contains `displayPeriod` and `endDate`; searched explicitly for `filingDate`, `announcementDate`, `resultDate`, `reportDate` — **all absent** |
| **R2 as-reported** | ❌ not disclosed |
| **R3 history** | ✅ **FY2017 → FY2026 annual + quarterlies**, free, no login |

The only date-bearing keys in the entire payload are `dateOfPublish`, `exDate`,
`forecastDate`, `updatedAt` — news, corporate actions and cache metadata, **not statement
filing dates**.

**Verdict: structurally identical to Screener** — good values, no filing dates. Cheap
programmatic access (no login) makes it the better *values* source of the two if a hybrid
is ever built.

### 2.4 Trendlyne — not promising, not pursued far

Homepage reachable. **No public API**; access is a retail subscription
(~₹2,090/year reported). Nothing indicates statement-level filing dates or bulk export.
**Dead end for this requirement**, and recorded as such rather than omitted.

### 2.5 BSE / NSE corporate filings — THE ONLY FREE PATH THAT CLEARS THE BAR

Probed `bseindia.com/corporates/ann.html` in a browser. The announcements listing exposes,
**visibly and per filing**:

```
Exchange Received Time 21-09-2026 16:18:20
Exchange Disseminated Time 21-09-2026 16:18:20   Time Taken 00:00:00
```

| | |
|---|---|
| **R1 filing date** | ✅ **exchange-stamped, to the second** — the definitional source of "announcement date"; a **`Result` category filter** isolates earnings filings |
| **R2 as-reported** | ✅ each filing is the original submission; restatements appear as later filings rather than overwriting earlier ones |
| **R3 history** | ⚠️ **XBRL mandatory from 1 April 2017** (BSE circular DCS/COMP/28/2016-17) → **~36 quarters / 9 folds**. Pre-2017 is PDF only. |

An **`Announcement-xbrl` submission type** exists, and BSE hosts a centralised
`bseindia.com/corporates/xbrldetails` page. NSE has the parallel
`corporate-filings-financial-results` and, from Q4 FY2024-25, `corporate-integrated-filing`.

**The catch, stated plainly:** the announcement listing gives **dates and PDF/XBRL
attachments**, not parsed numbers. Getting `Borrowings`, `Equity`, `EBIT` and `Interest`
means **parsing XBRL**. This is an extraction project, not a download.

**Honest limits of what I verified:** BSE's API responds
(`api.bseindia.com/BseIndiaAPI/api/AnnGetData/w` returns `"No Record Found!"` rather than
an error, so the endpoint is live) but I did **not** crack its parameter format within the
timebox, and the site's date picker did not accept programmatic input. **I therefore could
not verify how far the announcement archive itself extends** — the 2017 figure rests on the
documented XBRL mandate date, not on an observed query. That uncertainty is real and is
not smoothed over.

### 2.6 Paid enterprise — reference only, no access attempted

| source | access model | cost signal |
|---|---|---|
| **Capitaline**, **Ace Equity** | Indian institutional standard; per-seat subscription | **Pricing is quote-based and not publicly listed.** No figure is asserted here. |
| **Bloomberg Terminal** | per-seat annual licence | widely reported ~US$25–30k/seat/yr — **not verified in this task** |
| **FactSet** | enterprise subscription | comparable order of magnitude; quote-based |

These are the only sources that would deliver **long-history, as-reported, filing-dated
Indian fundamentals as a product** rather than a build. Recorded as a cost/benefit
reference point, nothing more.

---

## 3. Summary table

| source | R1 filing date | R2 as-reported | R3 history | usable? |
|---|---|---|---|---|
| yfinance statements | ❌ | ❌ | ❌ 4–5 annual | **No** |
| yfinance `earnings_dates` | ✅ | ~ believed | ~6y, **EPS only** | EPS factor only |
| Screener.in | ❌ | ❌ undisclosed | ✅ 12y | **No** |
| Tickertape | ❌ | ❌ undisclosed | ✅ 10y | **No** |
| Trendlyne | ❌ | ❌ | — | **No** |
| **BSE/NSE XBRL filings** | ✅ | ✅ | ⚠️ ~9y (2017+) | **Yes, with build effort** |
| Paid enterprise | ✅ | ✅ | ✅ | Yes, at cost |

---

## 4. Ranked recommendation

### 1st — BSE/NSE XBRL extraction (recommended if Layer 3 is worth pursuing)

The only free option that clears R1 and R2 honestly.

- **Achievable fold count: ~9 (2017–2026)** — a real improvement on Layer 2's 7, still
  short of Layer 1's 22. Reported as-is, not rounded up.
- **Effort estimate: roughly 3–6 focused days** to a working pipeline over ~400 stocks:
  (a) enumerate `Result`-category announcements per company per quarter with their
  exchange timestamps; (b) fetch the XBRL/XML attachment; (c) map taxonomy tags to
  Borrowings / Equity / EBIT / Interest; (d) handle standalone vs consolidated; (e) handle
  banks and NBFCs, whose schedules differ materially and which are **18% of the universe**.
- **Main risk is (c) and (e), not (a) or (b).** Taxonomy mapping and financial-sector
  schedule differences are where this kind of project usually overruns. Treat 3–6 days as
  optimistic if banks must be handled properly.

### 2nd — Hybrid: Tickertape/Screener values + BSE filing dates

Join 10–12 years of statement values to BSE announcement dates on period.

- **Fixes R1** (reporting-lag look-ahead) — the flaw that killed yfinance.
- **Does NOT fix R2** — values remain latest-restated.
- Per the brief's own standard, this converts an **unstated** flaw into a **stated,
  bounded** one, which is genuinely more usable. But it must be labelled that way in any
  result, permanently.
- Cheaper than option 1 and buys ~10–12 years instead of ~9. Worth it **only** if
  restatement risk is explicitly carried in every downstream verdict.

### Not worth pursuing

- **Trendlyne** — no API, no filing dates, subscription for retail UI. Nothing to gain.
- **Pre-2017 PDF parsing** to extend history — variable layouts across thousands of
  filings, some scanned. **Weeks of work, low and unmeasurable reliability**, to add years
  that would still need per-company validation. The marginal folds are not worth it.
- **Screener as a data backend** — no API, login-gated export, and it is a presentation
  layer over the BSE filings you would be better off reading directly.

### If none of this is acceptable

Then the honest conclusion is that **Layer 3's leverage/solvency factors require paid
data**, and the decision is a commercial one rather than a technical one. That is a
legitimate outcome and is stated rather than worked around. **What is not acceptable is
quietly reverting to yfinance and calling 4 restated annual periods a fundamentals test** —
that would repeat the exact class of silent structural error that produced the rupee/dollar
currency bug and Layer 2's dividend-adjustment confound.

---

## 5. Opportunistic finding — relevant to Layer 4, not chased here

**The BSE announcements infrastructure is also the natural source for Layer 4
(earnings-call tone / FinBERT).**

While probing, the live announcement feed showed entries such as *"Announcement under
Regulation 30 (LODR)-Analyst / Investor Meeting"* with attached PDFs, alongside annual
reports back to 2018. Screener's Documents section aggregates the same BSE filings,
including concall transcripts and investor presentations.

So the **same extraction work** that would serve Layer 3's balance-sheet needs —
enumerating BSE announcements with exchange timestamps and pulling attachments — also
yields **date-stamped concall transcripts**, which is exactly Layer 4's input and exactly
the thing that is otherwise hard to obtain point-in-time.

That materially improves the cost/benefit of option 1: it is not a single-layer
investment. **Flagged for the Layer 4 decision, deliberately not pursued in this task.**

---

## 6. What I could not establish

- **BSE announcement archive depth** — the API parameter format was not cracked and the
  date picker rejected programmatic input within the timebox. The ~2017 figure comes from
  the documented XBRL mandate, not an observed historical query. **Verifying this is the
  first thing to do** if option 1 is approved, because it sets the real fold count.
- **Whether Screener/Tickertape restate** — neither discloses a policy. Treated as
  restated (the conservative assumption), not asserted as fact.
- **Capitaline / Ace Equity pricing** — quote-based and not public. No figure invented.

**Sources:**
[BSE corporate announcements](https://www.bseindia.com/corporates/ann.html) ·
[BSE XBRL details](https://www.bseindia.com/corporates/xbrldetails.aspx) ·
[NSE XBRL information](https://www.nseindia.com/static/companies-listing/xbrl-information) ·
[BSE XBRL mandate, Apr 2017](https://datatracks.com/in/blog/bombay-stock-exchange-mandates-financial-results-xbrl-format/) ·
[India XBRL filings overview](https://www.tigzig.com/vigil/india-xbrl-filings) ·
[Screener export docs](https://support.screener.in/article/28-export-screen-results) ·
[Screener premium](https://www.screener.in/premium/) ·
[Tickertape JSON endpoints](https://dev.to/datadaemon/indian-stock-fundamentals-as-json-the-tickertape-endpoints-that-work-without-a-login-5ag8)
