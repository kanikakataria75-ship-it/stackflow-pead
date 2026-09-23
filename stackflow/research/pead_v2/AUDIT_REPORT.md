# StackFlow PEAD V2 — Independent Audit Report

**Audit date:** 2026-09-23
**Auditor:** Claude Code (independent of Antigravity; no Antigravity code was imported or executed)
**Subject:** `stackflow/research/pead_v2/` — Antigravity's PEAD V2 research, reports, ledger, live config
**Mode:** Read-only. This file is the only file created or modified. No code, CSV, config, or forward-record file was touched.

---

## 0. Scope note — which version of the report was audited

The audit brief quotes the headline claims **"VALIDATED TRADING STRATEGY", +17.73% CAGR, +6.68% excess, Sharpe 7.47–11.97**. Those figures are **no longer in `FINAL_PEAD_V2_REPORT.md`**. The file was rewritten at 2026-09-22 20:45, after Antigravity's own self-audit (`PEAD_V2_AUDIT_FINAL.md`, 20:52), and now claims:

- +16.83% CAGR, +5.78% excess, Sharpe 1.017, volatility 16.82%, max DD −25.12%
- verdict "Signal confirmed; strategy is a forward-test candidate"

The retracted numbers survive in `AUDIT_01_FROZEN_SPEC.md`, `AUDIT_02/03`, and the unrecomputed prose of `PHASE_09_COST_CAPACITY.md`, which still says "+17.73%", "Sharpe of 7.55" and "−11.5%".

This audit therefore tests **both** sets of numbers: the original claims quoted in the brief, and the revised claims now in the report.

**Method.** I wrote my own code (kept in a session scratchpad, not in the repo) to rebuild everything from the raw inputs:

- `data_pipeline/xbrl/cache/extract_universe.csv`
- `filing_index.csv` and `filing_index_integrated.csv` (raw filing timestamps)
- `pead/cache/px/*.csv` (raw daily OHLCV)
- `cache/sector_close_panel.csv` (NIFTY 500)

This covers the event table, SUE, timing, filters, ex-ante quintiles, forward returns, signal statistics, and a separate share-based, cash-accounted, daily mark-to-market portfolio simulator. Antigravity's pre-computed columns were used **only as comparison targets**, never as inputs.

---

## 1. One-line verdict per audit item

| # | Item | Verdict | Key numbers compared (claimed → recomputed) |
|---|---|---|---|
| 1 | Sharpe / vol / drawdown | **DISCREPANCY FOUND** | **Original:** Sharpe 7.5–12 and DD −11% are an artefact of linear smoothing. Reproduced exactly: CAGR 17.73%, vol 2.12%, Sharpe 7.86, DD −11.02%. **Revised:** 16.83% / 16.82% / 1.017 / −25.12% reproduces under Antigravity's own method (16.85 / 16.89 / 1.022 / −25.12), but that method is biased upward. **Share/cash MtM:** CAGR **14.74%**, vol **16.02%**, Sharpe **0.95** (rf=0) / **0.59** (rf=6%), max DD **−23.68%**, excess **+3.69%**. |
| 2 | Look-ahead in ex-ante quintiles and entry timing | **CONFIRMED** (minor caveats) | 7,818/7,818 quintiles reproduced exactly. In a 34-event raw-data sample: 34/34 match on raw timestamp, event day, entry session, entry Open and quintile. 0 events use information filed after their own entry open. Caveats: min history 150 vs 200 pre-registered; first-year windows truncated but described as full 365-day windows; 5 zero-volume "phantom" sessions in 2026 price data. |
| 3 | Holdout independence | **DISCREPANCY FOUND** (holdout contaminated) | Split = event_day ≤ 2023-12-31 / ≥ 2024-01-01, **identical to V1's**, which had already evaluated this window. Config chosen from a full-period grid: chosen cell is #1 of 48 distinct cells on both excess and Sharpe. **Holdout:** +7.55% / +0.14% claimed → +7.57% / +0.16% (Antigravity method); **+6.65% / −0.76%** under share accounting. Headline is carried by discovery (+26.8% CAGR / +11.3% excess). |
| 4 | Reconciliation with V1 | **DISCREPANCY FOUND** (in V2's explanation) | V1's 76.2% = 16/21 because a **NaN fold (2026Q3, incomplete returns) was counted as non-positive**. Correct V1 figure = 16/20 = **80.0%**. V2's explanation (a 2021Q2 fold with one event per side at −20.50%) is wrong: V1's code never included 2021Q2. 2019 vs 2021 start is reconciled: the first usable event is 2021-02-10 because SUE needs ≥6 prior YoY changes. |
| 5 | Mid = Large = +2.11% coincidence | **CONFIRMED** (genuine coincidence) | Mid +2.1127% vs Large +2.1101%. Disjoint samples (0 shared events; Mid n=522/537, Large n=615/438). Different Q5/Q1 legs and different names; tercile labels independently reproduced 100%. |
| 6 | Cost model, turnover, capacity | **DISCREPANCY FOUND** | Cost: **CONFIRMED** per-trade in the code path (0.585% on every trade). Turnover: claimed ~280–330% → **362%** one-way (my NAV-based) / **389%** (Antigravity's own formula; its Phase 9 table prints 392.1%). Capacity: claimed ₹15–30 Cr at 1% participation → **₹2.0 Cr** for 90% of trades to fit within 1% of 20-day median traded value. Antigravity's own Phase 9 table computes ₹2.2 Cr. At ₹15 Cr, **43%** of trades exceed 1% of ADV. |
| 7 | Kill tests KT1, KT4, KT5 | **CONFIRMED numerically; DISCREPANCY in labelling/interpretation** | KT1 +2.54% / 83.3% ✓, but the dropped folds are **2021Q3 & 2022Q1**, not "2022Q1 & 2024Q1", and the statistic is a fold-mean (baseline 3.30%, not 2.77%). KT4 +2.82% / 85.0% ✓. KT5 +14.98% / +3.93% claimed → +15.00% / +3.95% ✓ (Antigravity method); **+13.05% / +2.00%** under share accounting; **holdout excess at 1% cost = −1.55%**. |
| 8 | Universe / filter consistency | **CONFIRMED** (filters applied identically) **with definition issues** | 7,973 events rebuilt bit-for-bit. Spread test and portfolio draw on the same table with the same filters. All 579 trades satisfy ₹1 Cr / ₹50. Consolidated-first: 0 violations. Issues: "Non-Financials" is defined by XBRL taxonomy, which lets **31 portfolio trades** in NBFCs, AMCs and exchanges through (Bajaj Finance, Spandana, CGCL, Motilal Oswal …). 683 events (8.6%) have a SUE whose "t−4" row is not the same quarter last year. |

---

## 2. Detail per item

### Item 1 — Sharpe ratio and volatility sanity check

**What I recomputed.** I independently rebuilt the 30-slot, Non-Financials, Q5, 60-day, 0.585% book. My selection reproduces Antigravity's `trade_ledger_pead_v2_audited.csv` exactly: **579/579 trades**, identical exit dates, gross returns within 0.005 pp. I then built the equity curve five ways:

| Method | Period | CAGR | Ann. vol | Sharpe (rf=0) | Max DD | Nifty 500 CAGR | Excess |
|---|---|---|---|---|---|---|---|
| **D. Linear smoothing** (each trade's net return spread evenly over its holding days) | 2021-08-11 → 2026-07-30 | **17.73%** | **2.12%** | **7.86** | **−11.02%** | 11.05% | **+6.68%** |
| E. Realized-at-exit only | same | 17.40% | 7.85% | 2.12 | −14.38% | 11.05% | +6.35% |
| A. Antigravity's current "sleeve" MtM (my re-implementation) | same | 16.85% | 16.89% | 1.022 | −25.12% | 11.05% | +5.80% |
| **B. Share-based, cash-accounted daily MtM** (as-coded trade selection) | same | **14.74%** | **16.02%** | **0.954** | **−23.68%** | 11.05% | **+3.69%** |
| C. Share-based, strict slot release (573 trades) | 2021-08-11 → 2026-08-07 | 15.18% | 16.47% | 0.955 | −22.24% | 11.34% | +3.84% |
| *Nifty 500 (price index), same span as A/B* | | 11.05% | 14.51% | 0.808 | −18.84% | | |

**Methodology (B, C).** On each entry day, at the Open, buy `NAV(previous close)/30` of the stock, capped by available cash; charge half the cost on the buy and half on the sell. Hold the shares and mark them at every Close. Sell at the exit-day Close. Cash earns 0%. The daily NAV is cash plus Σ shares × Close. Metrics:

- CAGR over calendar years (days / 365.25)
- Vol = std(daily return) × √252
- Sharpe = mean(daily excess over rf) × 252 / vol
- Max DD from the daily NAV

**Risk-free rate.** Antigravity's Sharpe is **excess-of-zero**; the report does not state this. With a 6% rf (roughly the average Indian 91-day T-bill rate over 2021–26), Sharpe is **0.59 (B) / 0.60 (C)**, against **0.41** for the Nifty 500.

**Original numbers (Sharpe 7.47–11.97, DD −5% to −22%, CAGR 17.73%).** Method D reproduces the retracted headline cell *to the second decimal*: 17.73% CAGR, +6.68% excess, −11.0% DD. Across the grid it also reproduces the other cells Antigravity quoted in `AUDIT_03`: 10 slots +17.02%, 20 slots +15.15%. Across the 12 Q5/Non-Fin cells, D gives Sharpe 3.5–11.3 and DD −5.5% to −20.5%.

Linear smoothing removes all within-trade price volatility, leaving volatility near 2%. That is why Sharpe was 7–12 while drawdowns (which still appear at trade boundaries) stayed double-digit. **The original triple was computed on a non-daily-MtM basis and is wrong.** Antigravity has since retracted it, correctly.

**Revised numbers (16.83% / 16.82% / 1.017 / −25.12%).** These reproduce under Antigravity's current method A, but A overstates return by about **2.1 pp/yr** relative to honest cash accounting (B). Decomposition:

| Step | CAGR | Δ |
|---|---|---|
| A. Sleeve (daily-rebalanced constant 1/30 weight per open trade, as coded) | 16.85% | |
| → buy-and-hold shares, leverage allowed | 15.86% | −0.99 pp (daily-rebalancing effect of the sleeve formula) |
| → cash-constrained (no leverage) | 14.74% | −1.12 pp (removes the leverage below) |

**Same-day slot recycling creates leverage.** `portfolio_engine.py` frees a slot for a new entry at the **Open** of day *d* when the old position exits at the **Close** of the same day *d* (`pos["exit_date"] > entry_d`). In the sleeve formula, both positions earn a full 1/30 weight that day. The book holds **more than 30 positions on 193 days (maximum 34, i.e. about 113% gross exposure)**. The live config says "1/N of initial sleeve equity", which matches neither the engine (1/30 of *current* NAV, rebalanced daily) nor a real account.

**Corrected triple (B):** Sharpe **0.95** (rf=0) / **0.59** (rf=6%), vol **16.0%**, max DD **−23.7%**, CAGR **14.7%**, excess **+3.7%** vs the Nifty 500 price index.

- **Original numbers: WRONG.**
- **Revised numbers: arithmetically reproducible but overstated by ~2 pp/yr of CAGR**, driven by the engine's sizing and slot-recycling rules.

A further upward bias that I could **not** quantify from local data: `fetch_px.py` downloads prices with `auto_adjust=True`, so stock returns **include dividends**. The benchmark is the NIFTY 500 **price** index. Every "excess" number in V2 (and V1) is therefore overstated by roughly the index dividend yield, **~1–1.5 pp/yr** (my estimate, not computed; no TRI series exists in the repo).

### Item 2 — Look-ahead re-verification

**Full-population check (not just a sample).** I independently implemented the rolling ex-ante quintile: history = qualifying events with `event_day ∈ [T−365, T)`, at least 150 events, cut-offs = empirical 20/40/60/80th percentiles of SUE. It reproduces `q_exante_4q` for **7,818/7,818 events (100%)**. The 730-day (min 250) and expanding (min 150) variants also match 100%.

**Timestamp-strict test.** For every event I found the latest *filing timestamp* among the events in its history set:

- History filed **after the event's own entry open (09:15 on the entry day): 0 events.** No information unavailable at trade time is ever used.
- History containing a filing timestamp **later than the event's own filing timestamp: 324 events.** Cause: the window is keyed on `event_day` rather than on the filing timestamp. Also, weekend/holiday after-hours filings are pushed two sessions forward, so a Saturday-evening filing gets event day Tuesday and its history includes Monday's filings. This is not tradeable look-ahead, since everything is known before the entry open. But the claim in `PEAD_V2_AUDIT_FINAL.md` §4.2 and `AUDIT_05_POINT_IN_TIME.csv` of "max(historical timestamp) < event timestamp, 0 violations" is **not true at timestamp granularity**. `AUDIT_05` compares *dates* (`latest_information_timestamp_used` is a date), which makes its test true by construction.
- Rebuilding quintiles with the stricter rule "history = filings strictly before own filing timestamp" changes **30 of 7,818** assignments (99.6% agreement).

**20-event sample (34 events drawn).** The sample is stratified by year 2021–2026, intraday vs after-hours, weekend filings, the first valid dates, low-history windows and Q5 events. It is saved in the session scratchpad as `sample_events.csv` and was recomputed from **raw strings** in the two filing-index files and **raw rows** in `pead/cache/px/<SYMBOL>.csv`:

- 34/34 match on earliest raw filing timestamp, event day, entry session, and entry **Open** (to 1e-6).
- 34/34 have a quintile equal to V2's.
- Examples:
  - WIPRO, filed 2021-10-13 16:33: event day 10-14; entry 10-18, across the Dussehra holiday and the weekend.
  - CUB, filed Fri 2022-11-04 18:40: event day Mon 11-07; entry 11-09, across the Guru Nanak Jayanti holiday.
  - HDFCBANK, filed Sat 2025-04-19 22:42: event day Tue 04-22; entry 04-23.

**Timing rule vs code.** For after-hours filings on non-trading days, the code (inherited from V1) sets event day = the **second** session after the filing, not the first as `TIMING_RULES.md` Case C states. Entry is therefore one session later than documented. This is conservative, not a leak, but the live forward record must follow one rule consistently.

**Boundary (first ~365 days).** The event sample starts 2021-02-10. The first event with a quintile is **2021-08-10**; the **155 events** before it are excluded (fewer than 150 prior events). **653 events** between 2021-08-10 and 2022-02-09 use **truncated windows**: history begins 2021-02-10 and holds as few as 155 events, which is effectively an expanding window. Reporting problems:

- The report (§4.3) describes every threshold as coming from "the window [T−365, T)".
- `AUDIT_05_POINT_IN_TIME.csv` lists window starts such as 2020-08-10, when no data exists before 2021-02-10.
- The code's `min_events=150` deviates from the pre-registered **≥ 200** (`PRE_REGISTRATION.md` §3.3). With 200, 7,751 events qualify instead of 7,818, and the 60-day spread is +2.75% (85% folds): **immaterial to the result, but an undisclosed deviation.**

**Data defect affecting timing (2026 only).** Five dates in the price files are zero-volume holiday rows that are not NSE sessions: 2026-01-15, 05-01, 05-28, 06-26 and 09-14. On these, 373–434 stocks show Volume = 0. Effects:

- 35 events have their event day and **31 events their entry** on such a phantom session.
- **5 portfolio trades enter on a phantom session**, and **74** holding windows span one, so they are one real session shorter than 60.

This does not change the signal result. It **must** be fixed before the forward record uses these files for entry dates.

### Item 3 — Holdout independence

- **Split used:** discovery = `event_day ≤ 2023-12-31`; holdout = `event_day ≥ 2024-01-01` (`config.py`). This is **the same split V1 used** (`pead/scripts/run_pead.py`, `DISC_END`).
- **Was the holdout seen before V2 was designed?** Yes, several times over:
  1. V1 (`RESULTS_pead.md`, file time 16:09) evaluated this signal on this exact holdout (+2.16%).
  2. V1 also produced the **full-sample** diagnostics that motivated V2's design choices: Financials invert (−4.85%), small caps stronger, the FIFO cap selects early filers. V2's `PRE_REGISTRATION.md` (18:42) was written after those results.
  3. The Phase 8 grid ran on the **full 2021–2026 period**, and the live config was frozen minutes later (Antigravity's own `AUDIT_02` timeline: 18:49 → 18:51). **Holdout contaminated.** "Successful replication" does not hold in the normal sense.
- **Selection evidence.** In `PHASE_08_PORTFOLIO_RESULTS.csv` the chosen cell (Non-Fin, Q5, 30 slots, 60 days) ranks **#1 of 48 distinct cells by excess CAGR and #1 by Sharpe**. There are 48 distinct cells, not 96, because every FIFO row equals its SUE_RANK row (see §3.1).
- **Mitigating but retrospective.** The discovery-only grid (`DISCOVERY_GRID_2021_2023.csv`) also ranks this cell #1 by Sharpe (#3 by excess). But that file was generated **2026-09-23 04:29, after** the config freeze, so it is a post-hoc consistency check, not a pre-commitment. No selection criterion (Sharpe vs excess) was pre-registered.
- **Further holdout reuse.** `EXIT_RULE_HOLDOUT_STUDY.csv` (04:42) evaluated 24 alternative exit rules directly on the holdout.
- The holdout window has therefore been evaluated **at least three times**: by V1, by the V2 full-period grid, and by the V2 exit-rule study.

**Holdout-only results for the 30-slot strategy** (fresh run on holdout events, as in Phase 10):

| | CAGR | Nifty 500 | Excess | Sharpe rf=0 (Nifty) | Sharpe rf=6% (Nifty) | Max DD |
|---|---|---|---|---|---|---|
| Antigravity claim (§11.1) | +7.55% | +7.41% | +0.14% | 0.51 | — | −25.12% |
| My re-impl. of Antigravity method | +7.57% | +7.41% | +0.16% | 0.51 (0.56) | 0.18 (0.17) | −25.12% |
| **Share-based MtM, fresh run** | **+6.65%** | +7.41% | **−0.76%** | **0.48 (0.56)** | **0.13 (0.17)** | −23.61% |
| Share-based MtM, continuous run split at 2024-01-01 | +8.36% | +7.38% | +0.98% | 0.57 (0.56) | 0.22 (0.17) | −23.68% |
| Discovery, Antigravity method (fresh run) | +26.85% | +15.50% | +11.35% | 1.61 | | −20.32% |

**Answer.** The headline (+16.8% CAGR / +5.8% excess, or +14.7% / +3.7% under honest accounting) is **carried by the discovery period**: +26.8% CAGR, +11.3% excess, including 2023's +43.6% vs +25.8%. On the holdout, the strategy roughly matched the Nifty 500 price index: excess between −0.8 and +1.0 pp depending on accounting. Its Sharpe was **equal to or below** the index's, and 2025 was −4.9% vs +6.7%.

It still beat same-mechanics random portfolios on the holdout (random 20% draws: mean excess −4.05%, sd 3.13%, 40 draws). **The signal adds value relative to the event universe, but the long-only book did not beat the market out of sample.**

### Item 4 — Reconciliation with V1

- **76.2% vs 80.0%.** V1's `pead_folds.csv` has **21 rows**. The last, `2026Q3`, has an **empty spread**: its 60-day returns are incomplete, but at least 3 events exist per bucket, so the fold is not filtered. `evaluate.py` computes `(fo.spread > 0).mean()`, which counts the NaN as not-positive, giving **16/21 = 76.2%**.
  - The correct V1 figure is **16/20 = 80.0%**. I reproduced this from the V1 quarter-grouped quintiles with ≥3 events per bucket.
  - The same bug makes V1's **holdout** fold figure 8/11 = 72.7%; the correct figure is **8/10 = 80.0%**.
  - V2's explanation (a 2021Q2 fold with one Q5 and one Q1 event at −20.50%, dropped by a ≥3 filter) is **incorrect as an account of V1's number**. V1's code already required ≥3 per bucket, so 2021Q2 was never among its 21 folds. That fold exists only if the minimum is relaxed to 1 (I get 16/21 = 76.2% that way too, with 2021Q2 at −20.50%). This is **a numerical coincidence that V2 presented as the reconciliation**.
- **2019 vs 2021 start.**
  - V1's pre-registration said "Discovery: filings 2019 → 2023"; the actual sample starts 2021.
  - Recomputed from raw data: 13,150 quarterly PAT rows; **4,506 dropped for fewer than 6 prior YoY changes**; the first surviving event is **2021-02-10**.
  - V1's `RESULTS_pead.md` already disclosed "events begin in 2021", and V2's reason (SUE needs about 10 quarters of XBRL history) is correct.
  - **Both reports agree on the sample actually used; only V1's pre-registration projection differs.**
  - V2's ex-ante discovery effectively starts **2021-08-10** (first valid quintile), not at the 2021-02-10 sample start.
- **Spread sizes.**
  - V1 +2.50% (look-ahead quarter quintiles, 3,034 Q5+Q1 events) is reproduced from V1's quintile column.
  - V2 +2.77% is recomputed exactly: Q5 +1.196%, Q1 −1.578%, Welch **p = 3.88 × 10⁻⁷**, 17/20 folds, ex-best +2.90%.
  - The difference comes from bucket assignment (quarter-grouped vs trailing-365-day thresholds) on an **identical** event set: my rebuild gives 7,973 events and 421 symbols, bit-for-bit equal to V1's `pead_events.csv`.
  - V2 did not change the universe, filters, or SUE. It inherits V1's event file directly (`build_v2_dataset.py` reads `pead/results/pead_events.csv`).

### Item 5 — Size tercile coincidence

- **Samples are disjoint:** Mid 2,582 events, Large 2,613 events, **0 shared** (symbol, period_end) keys.
- **Tercile labels:** independently recomputed with the same rule (per entry-month 33.3% / 66.6% quantiles of `turnover20`), matching V2's labels 100%.

| Tercile | Q5 n | Q5 mean | Q1 n | Q1 mean | Spread | 95% bootstrap CI | Q5 sample symbols | Q1 sample symbols |
|---|---|---|---|---|---|---|---|---|
| Mid | 522 | +1.5850% | 537 | −0.5277% | **+2.1127%** | +0.15 … +4.09% | REDINGTON, JKPAPER, BERGEPAINT, BALMLAWRIE, POLYMED, CCL | BALRAMCHIN, TORNTPHARM, HINDZINC, TORNTPOWER, CYIENT, EMAMILTD |
| Large | 615 | +0.8452% | 438 | −1.2650% | **+2.1101%** | +0.38 … +3.83% | SHREECEM, EICHERMOT, MPHASIS, CIPLA, WIPRO, AUBANK | JINDALSTEL, JSWSTEEL, LAURUSLABS, NHPC, INDUSINDBK, INDIGO |
| Small | 373 | +1.2289% | 619 | −2.7118% | +3.9407% | | | |

**Genuine coincidence, not a bug.** The sets, legs, medians and names all differ; the two spreads match to 0.003 pp by chance. Antigravity's §7.1 figures are all reproduced.

Two caveats:

- Both confidence intervals are wide and nearly touch zero; Mid is significant only at p = 0.036.
- Terciles use same-month peers' `turnover20`, so the label depends on events filed later in the month. That is harmless for a diagnostic but should not be used as a live filter.

### Item 6 — Cost model and turnover

**Cost application: CONFIRMED per-trade.** Two code paths apply it:

- `src/portfolio_engine.py`: `net_ret = raw_ret - cost` for each candidate, and in the MtM path `stock_daily.iloc[-1] = stock_daily.iloc[-1] - cost` on each trade's exit day.
- `run_audit_reconciliation.py`: uses the ledger's per-trade `transaction_cost`.

There is no flat annual haircut. Each of the 579 trades bears 0.585%, a total of about 11.3% of initial NAV. My independent share simulator charges 0.2925% on each leg and reproduces the cost sensitivity:

| Round-trip cost | Antigravity method: CAGR / excess / Sharpe | Share MtM: CAGR / excess / Sharpe | Holdout excess (Antigravity method, fresh run) |
|---|---|---|---|
| 0.300% | 18.13% / +7.08% / 1.088 (claimed 18.11 / 7.06 / 1.083) | 15.92% / +4.87% / 1.019 | +1.36% |
| 0.585% | 16.85% / +5.80% / 1.022 (claimed 16.83 / 5.78 / 1.017) | 14.74% / +3.69% / 0.954 | +0.16% |
| 1.000% | 15.00% / +3.95% / 0.926 (claimed 14.98 / 3.93 / 0.921) | 13.05% / +2.00% / 0.859 | **−1.55%** |

**Turnover.** The report (§10) claims "~280% to 330%".

- **Mine:** average annual buys and sells ÷ average NAV = **357% buys / 368% sells, 362% one-way**.
- **Antigravity's own formula** (trades per year ÷ slots): **389%**. Its own `PHASE_09` table prints **392.1%**.
- **The 280–330% figure is not supported by any computation in the repository.** Correct figure: about **360–390% per year one-way**, roughly 7× the capital traded per year round-trip.

**Capacity.** The report claims ₹15–30 Cr at 1% participation (₹80–150 Cr at 5%). From real `Close × Volume` for each of the 579 trades, using the median of the 20 sessions before entry:

- Median ADV **₹68.9 Cr**, p10 **₹6.7 Cr**, p25 ₹19.0 Cr, minimum ₹0.98 Cr.
- Position size = AUM/30. AUM at which a given share of trades stays within the participation cap:

| Participation cap | 50% of trades fit | 90% of trades fit | 100% fit |
|---|---|---|---|
| 1% of ADV | ₹20.7 Cr | **₹2.0 Cr** | ₹0.29 Cr |
| 5% of ADV | ₹103 Cr | **₹10.0 Cr** | ₹1.5 Cr |

- At ₹15 Cr AUM, **43%** of trades exceed 1% of ADV and 15% exceed 5%. At ₹30 Cr, **60%** exceed 1% and 26% exceed 5%.
- The "₹15–30 Cr" figure is only reachable by sizing to the *median* stock and ignoring the less-liquid half of the book.
- Antigravity's own Phase 9 code (p10 turnover × 1% × slots) prints **₹2.2 Cr**. That table has a further bug: all three rows ("10-/20-/30-slot") are `records[1]`, `records[4]` and `records[7]`, which are **the 20-slot book at three cost levels**. The prose ("15–40 Cr") is hard-coded text that contradicts the table printed above it.

**Honest capacity at 1% participation: ~₹2–3 Cr; about ₹10 Cr at 5%.**

### Item 7 — Kill tests (executed, not just inspected)

- **KT1 — drop top-2 folds.**
  - My fold list (4Q quintiles, 60 days, ≥3 per bucket) has top-2 folds **2021Q3 (+10.90%)** and **2022Q1 (+9.40%)**. The label "2022Q1 & 2024Q1" in the report and script is wrong; 2024Q1 (+6.88%) ranks 5th.
  - Mean of the remaining 18 fold spreads = **+2.54%**, with 15/18 = **83.3%** positive. This matches the claim numerically.
  - But the statistic is the mean of fold spreads, whose **full-sample value is +3.30%**, not the pooled +2.77%. KT1 therefore shows a 0.76 pp drop, not the 0.23 pp the report implies.
  - Event-level version (drop all events in those two quarters and re-pool): **+2.38%**, 83.3% folds.
  - The Phase 11 prose also says "+2.45%", contradicting its own table. **Passes, but mislabelled and overstated.**
- **KT4 — exclude Layer-4-seen events.** 200 events flagged. Spread **+2.82%** (Q5 n=1,475 / Q1 n=1,567), 17/20 = **85.0%** folds. **Matches the claim.**
- **KT5 — 1.0% cost.** Antigravity method: **+15.00% CAGR / +3.95% excess** (claimed +14.98% / +3.93%; the Phase 11 prose says +15.84% / +4.79%, which is inconsistent). Share accounting: **+13.05% / +2.00%**.
  - The test's pass criterion (full-period excess > 0) is dominated by discovery.
  - **On the holdout at 1% cost the excess is −1.55%** (Antigravity method, fresh run) or −0.68% (share method, split run). **Under a holdout criterion, KT5 would trigger.**
- Also re-run: KT2 (ex-2021) +2.60% ✓; KT3 (Mid+Large) +2.04%, p = 0.0021 ✓ (the prose says +2.12%, inconsistent); KT6 8Q +2.91% / expanding +2.89% ✓; KT7 40d +1.59% / 90d +3.58% ✓.
- **All seven kill tests except KT5 are signal-level tests.** The only portfolio-level kill test fails on the holdout.

### Item 8 — Universe and filter consistency

- **Event table.**
  - My independent build applies the stated rules: earliest filing timestamp across both filing systems, the 15:30 cut-off, entry at next-session Open, 20-session mean turnover ≥ ₹1 Cr before the event day, entry Open > ₹50, SUE with ≥6 prior YoY changes.
  - It gives 7,973 events and 421 symbols, and reproduces V2's `pead_v2_events.csv` field-for-field: filing_ts, event_day, entry_date, entry_open, turnover20, SUE, every forward return and `xs_univ` at every horizon, `is_fin` — max difference ≤ 4e-12.
  - Drop counts: 4,506 without SUE, 201 without price file, 90 liquidity, 380 price ≤ ₹50.
- **Same filters in both period splits and in both analyses.**
  - The cross-sectional spread and every portfolio run (full, discovery, holdout, grid, kill tests, ledger) read the **same** `pead_v2_events.csv` with `q_exante_4q` non-null. Filters are applied once, upstream.
  - Both require a complete forward window: NaN returns in the signal test; `exit_idx < len(px)` in the portfolio.
  - All 579 ledger trades satisfy turnover ≥ ₹1 Cr, Open > ₹50, Q5 and non-financial.
  - **No signal/portfolio filter mismatch was found.**
- **Consolidated-first / Standalone-fallback:** 888 events use a standalone-basis PAT, and **none** of those quarters has a consolidated XBRL filing in either index. 0 violations.
- **Earliest-filing rule:** reproduced. In 16 of 7,085 consolidated-basis events, the earliest timestamp (from a standalone XBRL filing) precedes the first *consolidated* XBRL filing by more than a day. Results PDFs normally publish both bases together, so this is probably harmless, but it is a residual point-in-time risk.
- **Definition issue — "Non-Financials".**
  - `is_fin` means the taxonomy contains `BANKING` or `NBFC_INDAS`. NBFCs and other financial companies that file under the plain `INDAS` taxonomy slip through: **161 events and 31 portfolio trades**. These include BAJFINANCE, SPANDANA, CGCL and MOTILALOFS (NBFC / broker-lender), HDFCAMC and NAM-INDIA (AMCs), BSE, CDSL and IEX (market infrastructure), and CRISIL, ICRA and CARERATING (rating agencies).
  - `live_config_pead_v2.md` says "Banks, NBFCs, and insurance excluded", but the code does not implement that.
  - Signal impact is small: industry-based Non-Fin gives a 60-day spread of +3.35% vs +3.48%.
- **Definition issue — SUE lag.** `compute_sue_series` takes `vals[i-4]` by row index. In 683 of 7,973 events (8.6%), row i−4 is **not** the same fiscal quarter a year earlier because of gaps in the XBRL series, which conflicts with the pre-registered definition. With date-matched SUE, the 60-day spread is **+2.98%** (18/20 folds). The signal is not hurt; the implementation simply differs from its specification.
- **Survivorship.** The universe is the 421 symbols that yfinance returns *today*. Delisted or renamed names are absent. Antigravity estimates the bias at 0.4–0.8%/yr; I did not verify that figure.

---

## 3. Additional findings not covered by items 1–8

### 3.1 The "SUE-rank priority" queue policy is a no-op

In both grids (`PHASE_08_PORTFOLIO_RESULTS.csv` and `DISCOVERY_GRID_2021_2023.csv`), **every FIFO row is identical to its SUE_RANK row** (taken trades, CAGR, Sharpe; max difference 0).

The cause: `run_portfolio_backtest` pre-sorts candidates by `[entry_date, sue desc]`, so "FIFO" already ranks same-day candidates by SUE. Neither policy ranks across days, and the pre-registered "higher SUE displaces lowest SUE" variant was never implemented.

Consequences:

- The "96-cell grid" is **48 distinct cells**.
- `AUDIT_03`'s statement that SUE-rank "outperformed FIFO in Phase 8 (+17.73% vs +12.38%)" is **false**. The +12.38% must be a different cell.
- The live config's `LOWER_SUE_RANK` rejection code describes a rule that in practice only breaks same-day ties.

### 3.2 Portfolio-level placebo (same mechanics, other quintiles)

Non-Fin, 30 slots, 60 days, full period, Antigravity method:

| Book | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| CAGR | 3.1% | 9.3% | 8.5% | 17.0% | 16.8% |
| Excess | −8.2% | −1.9% | −2.7% | +5.7% | +5.8% |

Random-selection books (40 draws of 20% of events, random priority) give mean excess **−0.52% (sd 2.36%)** over the full period and **−4.05% (sd 3.13%)** on the holdout.

The SUE ordering therefore carries real information at the portfolio level (Q5 − random ≈ +6 pp full, ≈ +4 pp holdout). Q4 is as good as Q5. Much of the "excess vs Nifty" in any single book, however, is regime and universe noise of ±2–3 pp.

### 3.3 Internal inconsistencies

These documents are still in the repository with stale or contradictory numbers:

- **`FINAL_PEAD_V2_REPORT.md`**
  - §9 win rate 53.8% (grid and my recomputation: **57.9%**).
  - §9 labels V2-quintile, 10/20-slot runs as "V1 Replicated". V1 was a 15-slot book on look-ahead quintiles and returned +8.38%.
  - §10's turnover and capacity figures are unsupported (item 6).
- **`PHASE_08_PORTFOLIO_REPORT.md`:** its prose says the V1 spec "achieves +8.4% to +9.1% CAGR, trailing Nifty (+11.6%)", while its own table shows +14.07% and +12.14%.
- **`PHASE_09_COST_CAPACITY.md`:** prose still says +17.73%, Sharpe 7.55, DD −11.5%, and ₹15–40 Cr.
- **`PHASE_10_HOLDOUT_VALIDATION.md`:** still says "untouched Holdout data" and "tradeability survive[s] out-of-sample scrutiny".
- **`PHASE_11_KILL_TEST.md`:** prose numbers (KT1 +2.45%, KT3 +2.12%, KT5 +15.84% / +4.79%) differ from its own table.
- **`AUDIT_01_FROZEN_SPEC.md`:** still lists +17.73% / +6.68% as the strategy's figures.
- **`AUDIT_05_POINT_IN_TIME.csv`:** window starts earlier than the data (item 2).

---

## 4. Revised overall classification

**Signal (cross-sectional PEAD, ex-ante SUE Q5 − Q1, 60 days, excess vs event universe): CONFIRMED.**
Every signal number was independently reproduced from raw data:

- +2.77%, p = 3.9 × 10⁻⁷, 85% of 20 quarterly folds positive, ex-best +2.90%, one inversion.
- Discovery +3.33% (8/10 folds); holdout +2.29% (9/10 folds).
- Survives the 8Q/expanding windows, ex-Layer-4, ex-2021, Mid+Large only, date-matched SUE and industry-based Non-Fin.

The holdout window had already been examined by V1, so the V2 signal holdout is a **re-confirmation of an already-observed window**, not a fresh out-of-sample test. The bucketing change (ex-ante thresholds) was methodological rather than tuned to results, so the signal verdict stands.

**Tradeable strategy (30-slot, Non-Fin, Q5, 60-day long-only book): INCONCLUSIVE — not validated.** The label "VALIDATED TRADING STRATEGY" is **REJECTED**.

- Full-period performance is +14.7% CAGR / +3.7% excess vs a price index, Sharpe 0.95 (0.59 at rf = 6%, vs 0.41 for the Nifty 500), under honest accounting. It is largely a discovery-period result from a configuration selected with the holdout in view.
- On the (contaminated) holdout the book matched the Nifty 500 price index: excess −0.8 to +1.0 pp; Sharpe ≤ benchmark; negative excess at 1% cost.
- It was not compared against a total-return benchmark, which would lower every excess figure further.
- Realistic capacity is about ₹2–3 Cr at 1% participation.

V2's own pre-registered bar for "VALIDATED TRADING STRATEGY" (§8: positive excess on holdout) is **failed under share-based accounting** (−0.76%). It is met only marginally (+0.14%) under the engine's leveraged, daily-rebalanced sleeve formula. Even that pass would not count, given the contamination and 48-way selection.

**Antigravity's current label ("Signal confirmed; strategy is a forward-test candidate") is directionally right.** Its supporting strategy numbers are still overstated (item 1), and its turnover and capacity figures are wrong (item 6). A forward test is the appropriate next step, but only after the fixes in §5.

---

## 5. What should NOT be trusted as-is, and what must be fixed first

Fixes are described, not applied.

**Do not trust:**

1. **Any Sharpe of 7–12, DD of −11%, CAGR of +17.73% or excess of +6.68%.** These are linear-smoothing artefacts, still present in `AUDIT_01`, `AUDIT_02`, `AUDIT_03` and `PHASE_09` prose.
2. **The revised +16.83% CAGR / +5.78% excess / Sharpe 1.017.** They are overstated by about 2 pp/yr (sleeve formula plus same-day slot-recycling leverage). Use about **+14.7–15.2% / +3.7–3.8% / 0.95** (rf=0), and treat even these as **upper bounds** because of the dividend-adjusted-vs-price-index benchmark mismatch.
3. **Any claim that the strategy "survived out-of-sample" or "replicated on holdout".** The holdout was used three times and shows about zero excess.
4. **Capacity ₹15–30 Cr at 1% (₹80–150 Cr at 5%)** → about ₹2 Cr / ₹10 Cr. **Turnover 280–330%** → about 360–390%.
5. **The "SUE-rank priority" dimension:** identical to FIFO in the code.
6. **KT1's fold labels and its implied size of drop; KT5 as evidence of cost robustness.** KT5 fails on the holdout.
7. **V2's reconciliation of V1's 76.2%.** The real cause is a NaN-fold counting bug; the correct figure is 80.0%.
8. **`AUDIT_05`'s "0 look-ahead violations"** as a timestamp-level statement. It compares dates. The substantive conclusion (no information after entry is used) is nonetheless correct.

**Fix before relying on `live_config_pead_v2.md` or `forward_record_pead_v2.csv`.** The forward record is currently header-only, so nothing needs unwinding.

1. **Portfolio accounting.** Replace the sleeve formula with share/cash accounting. Forbid entering at the Open of a day on which a slot is only freed at that day's Close, or explicitly model the cash. State position sizing precisely: the live config says "1/N of initial sleeve equity", the engine uses 1/30 of current NAV rebalanced daily, and neither is what a broker account does.
2. **Benchmark.** Use NIFTY 500 **TRI**, or unadjusted prices plus explicit dividends, since stock prices are `auto_adjust=True`. Also report an equal-weight event-universe benchmark, which the pre-registration promised and the report omitted.
3. **Sharpe convention.** State the risk-free rate; report rf = 0 and rf ≈ 91-day T-bill.
4. **"Non-Financials".** Define by industry or an explicit NBFC/AMC/insurer/exchange list so the code matches the live-config text, or change the text.
5. **SUE lag.** Match YoY by fiscal quarter date, not row index, as pre-registered (683 events affected).
6. **Price calendar.** Drop the five zero-volume phantom sessions in 2026 and validate every price file against the NSE trading calendar. Otherwise forward-record event days and entries will be wrong.
7. **Timing rule.** Reconcile `TIMING_RULES.md` Case C with the code's two-session bump for weekend/holiday after-hours filings, and freeze one rule for the forward record.
8. **Queue policy.** Specify it as implemented (same-day SUE tie-break only) or implement true cross-day ranking/displacement. The latter would be a new, untested configuration.
9. **Ex-ante thresholds.** Disclose the `min_events` = 150 deviation from the pre-registered 200, and the truncated windows for 2021-08-10 → 2022-02-09.
10. **Stale documents.** Correct or retire the stale numbers listed in §3.3 so no reader picks up the retracted figures.
11. **Forward-test evaluation.** Pre-register now, before any forward data exists:
    - the evaluation metric (excess vs NIFTY 500 TRI, share-based MtM)
    - the minimum horizon (at least 4–6 earnings seasons)
    - a kill criterion (e.g. excess ≤ 0 after N seasons)

    Also pre-register what counts as "validated". The current configuration was chosen with all data up to 2026-08 in view, so the forward period is the **only** clean test it can get.

---

*Reproducibility:* all recomputations used independent scripts and saved outputs (events, quintiles, the 34-event sample, NAV series, the placebo draws). These live in this session's scratchpad directory, per the read-only constraint. Key parameters:

- Cut-off 15:30 IST; entry at next-session Open; 60-session hold; 0.585% round-trip, 0.2925% per leg.
- 30 slots; slot release as coded (exit_date > entry_date) and strict (exit_date < entry_date).
- NIFTY 500 price index from `cache/sector_close_panel.csv`.
- Vol annualised with √252; Sharpe shown at rf = 0 and rf = 6%.
