
## Data-sourcing diagnostic (2026-09-21)

| # | Item | Status | Note |
|---|------|--------|------|
| DS-1 | Screener.in probe | valid | 12y annual + 13 quarters, all three target factors derivable (Borrowings, Equity Capital+Reserves, Operating Profit, Interest). **Period-end columns only - NO filing date.** No public API; export is login-gated. Its Documents section links out to BSE filings. |
| DS-2 | Tickertape probe | valid | Free JSON, no login, FY2017-FY2026 + quarterlies. Payload searched explicitly for filingDate/announcementDate/resultDate/reportDate - **all absent**. Only displayPeriod/endDate. |
| DS-3 | Trendlyne | valid (shallow) | No public API, retail subscription only. Dead end, recorded. |
| DS-4 | BSE/NSE filings probe | valid | **Exchange Received Time / Exchange Disseminated Time to the second**, plus a Result category filter and Announcement-xbrl submission type. Clears R1 and R2. XBRL mandatory from 1 Apr 2017 -> ~9 folds. Numbers are inside XBRL/PDF attachments, so this is an extraction project. |
| DS-5 | BSE API params | **UNRESOLVED** | `AnnGetData/w` is live (returns "No Record Found!" not an error) but the parameter format was not cracked in the timebox, and the site date picker rejected programmatic input. **Archive depth therefore NOT verified** - the 2017 figure rests on the documented XBRL mandate, not an observed query. |

## Outcome

No free source is a drop-in. Every easy source (Screener, Tickertape, yfinance) fails the
SAME requirement: no filing date. More data with the same structural flaw is not progress.

Recommended: **BSE/NSE XBRL extraction** (~9 folds, 2017-2026; est. 3-6 focused days,
with taxonomy mapping and bank/NBFC schedules as the overrun risk).
Second: hybrid Tickertape/Screener values + BSE dates - fixes reporting-lag look-ahead,
does NOT fix restatement; usable only if labelled permanently.
Not worth pursuing: Trendlyne, pre-2017 PDF parsing, Screener as a backend.

Opportunistic: the same BSE announcements infrastructure also yields date-stamped concall
transcripts - i.e. Layer 4 input. Makes option 1 a two-layer investment, not one-layer.

## H3 factor-1 run (2026-09-21)

| # | Item | Status | Note |
|---|------|--------|------|
| L3-1 | `fetch_earnings.py` | valid (1 resume) | 400/434 stocks with usable reported-EPS history. First run hit the 590s timeout (exit 143); fetcher idempotent, resumed not restarted. |
| L3-2 | `run_h3.py` | valid | 4-cell forward grid, quarterly rebalance, dual baselines, dispersion-normalised, fold permutation tests. |
| L3-3 | cross-section audit | **caught a sample-composition problem BEFORE reporting** | Folds appeared from 2017 though signals were expected from ~2021-11. Cause: a minority of stocks have deeper Yahoo EPS history, clearing the 30-stock floor on a biased subset. Cross-section steps 4-5x at end-2021 (~40-60 stocks 2017-21 vs ~227-247 from 2022). Both samples reported; primary = 2022+, restricted on a representativeness criterion independent of results. |

## H3 outcome

**H3 (exclusion) REJECTED** - KF2 triggered. Weak-tercile effect flips POSITIVE when the
single extreme fold is dropped, in 4/4 cells on BOTH samples. Fold bar failed 0/4 cells.
Best p_weak = 0.296. On the representative sample the weak tercile is positive outright
at M=60 and M=90.

**H3-inv (selection) INCONCLUSIVE, leaning supportive at long horizons only** - 4/4 cells
positive, 3/4 clear the fold bar, 4/4 survive drop-best-fold, and the effect scales
coherently with horizon (0.52 -> 1.19 -> 1.95 -> 2.92%), so KF3 not triggered. But no cell
is significant (best p=0.060), it rests on 2 of 5 folds (2023 and a single-rebalance 2026),
and it is NON-MONOTONIC: middle tercile is the worst bucket in every cell.

**Notable reversal of the StackFlow pattern.** Layers 1 and 2 both leaned filter-shaped.
Here the exclusion form fails outright and the selection form is the one with any life.
The prior was wrong - which is why both forms were tested rather than assumed.

Confound check bit again: vs Nifty 500 the WEAK tercile also beats the benchmark by
+1.4% to +4.2%; implied universe drift +1.3% to +4.4%. Naive measurement would have made
H3-inv look 2-3x larger and the weak tercile look like a winner. Third consecutive layer
where this mattered.

Reversal-regime breakdown STRUCTURALLY EMPTY - no reversal year falls in the
representative window, so the signal is untested against the regime that has broken every
prior StackFlow signal.

Factors 2-4 NOT TESTABLE - no run attempted, per pre-registration section 0.
