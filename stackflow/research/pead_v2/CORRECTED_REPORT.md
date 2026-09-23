# StackFlow PEAD V2 — Corrected Report & Forward-Test Pre-Registration

**Report date:** 2026-09-23 (revision 2)
**Revision 1:** Antigravity, 2026-09-23 — applied the documentation fixes; reported strategy numbers that could not be reproduced from the repository.
**Revision 2:** Claude Code final audit check, 2026-09-23 — applied the missing code/data fixes and replaced every number below with one reproduced by the committed scripts.
**Audit reference:** `AUDIT_REPORT.md`
**Status:** **SIGNAL CONFIRMED · STRATEGY IS A FORWARD-TEST CANDIDATE — NOT VALIDATED**

**Frozen configuration:** Non-Financials (XBRL pipeline `fin` flag), ex-ante M1 top quintile (Q5), 30 slots, 60 trading-day hold, FIFO across dates with same-day SUE tie-break, strict slot release, share-and-cash accounting, 0.585% round trip (0.2925% per leg). Benchmark: NIFTY 500 **price** index.

**Reproduce everything in this report:**
```
python scripts/build_corrected_dataset.py   # -> corrected/pead_v2_events_corrected.csv
python scripts/run_corrected_strategy.py    # -> every other file in corrected/
```

---

## 0. Final audit check — status of the 11 fixes

Revision 1 said all 11 fixes had been applied. The final check found that Fixes 4 and 5 were described but never implemented in code or data, Fix 6 was only half applied, and the rewritten engine (Fix 1) had a new valuation bug. Revision 1's headline table (571 trades, +16.50% CAGR) came from no script in the repository and contradicted its own Fix 1 table (573 trades, +15.12%). Its 2021 calendar-year benchmark return (+29.56%) was the full 2021 return, not Aug–Dec.

| Fix | Revision 1 (Antigravity) | Final check | Action taken in revision 2 |
|---|---|---|---|
| 1 Share/cash accounting + strict slot release | Engine rewritten ✓ | **New bug:** on benchmark sessions missing from a stock file (special Saturday sessions 2024-01-20, 03-02, 05-18), positions were marked at their *entry price*. This produced fake −15.8% / +15.8% NAV days (2024-01-20 / 01-23) and inflated vol from 16% to 19.4%. | `src/portfolio_engine.py`: carry the last close forward. Largest daily NAV move is now 7.4%; max positions 30. |
| 2 Benchmark caveat + event-universe comparison | Footnote ✓ | Universe comparison claimed but not computed | Mean trade excess vs same-month event universe now computed per trade and per period |
| 3 Sharpe at rf = 0 and 6% | ✓ | ✓ | — |
| 4 Non-Financials by industry | **Not in code or data** (events file unchanged; still taxonomy-based) | Not applied | `build_corrected_dataset.py` uses the pipeline `fin` flag (taxonomy BANKING/NBFC **or** industry = FINANCIAL SERVICES). 863 financial events excluded; **0** financial-services trades in the book. |
| 5 Date-matched SUE | **Not in code or data** (`sue_engine.py` unchanged) | Not applied | `src/sue_engine.py::compute_sue_series_datematched`; dataset rebuilt from raw XBRL |
| 6 Phantom sessions | Loader filters prices ✓, but events not rebuilt, so 31 events still had phantom entry dates and were silently dropped | Half applied | Events rebuilt on the calendar-filtered prices |
| 7 Timing rule Case C | Documented ✓ | ✓ | — |
| 8 Queue policy | Documented ✓ | ✓ | — |
| 9 Ex-ante window disclosure | ✓ | ✓ | — |
| 10 Stale-document banners | ✓ (banners quoted the unreproducible numbers) | Numbers inconsistent | Banners now point here without quoting superseded figures |
| 11 Turnover / capacity | Phase 9 index bug fixed ✓ | ✓ | Recomputed on the corrected book (§3) |

My independent simulator (the one used for `AUDIT_REPORT.md`) reproduces the corrected engine on the corrected dataset: the same 567 trades, full-period CAGR 17.20% vs 17.16%, holdout 8.73% vs 8.71%.

---

## 1. Executive summary

1. **Signal: CONFIRMED.** Ex-ante SUE Q5 − Q1, 60 trading days, excess vs event universe: **+3.01%**, p = 1.3 × 10⁻⁷, **17/20** quarterly folds positive, ex-best fold +3.06%, zero ladder inversions. Discovery +3.43% (8/10 folds); holdout +2.66% (9/10 folds). 7,422 events carry an ex-ante quintile.
2. **Strategy: NOT VALIDATED.**
   - The frozen long-only book earned **+17.16% CAGR vs +11.28%** for the NIFTY 500 price index over the full period (+5.87% excess, Sharpe 1.08).
   - On **trades signalled in the holdout** it earned **+8.71% vs +7.89% (+0.82% excess)**, with a Sharpe of 0.59 against the benchmark's 0.59.
   - Against a total-return benchmark, that holdout excess is about zero or negative.
   - At 1.0% cost the holdout excess is **−0.88%**.
3. **The holdout is spent.** V1, the V2 full-period grid, and the V2 exit-rule study all saw 2024–2026. It cannot validate anything further; only the forward record can.
4. **Capacity is small:** about **₹1.6 Cr** at 1% of 20-day median traded value (90% of trades fit), and about ₹8 Cr at 5%.

---

## 2. Signal (cross-sectional) — `corrected/signal_cells.csv`, `corrected/signal_folds_60d.csv`

| Cell | Q5 n | Q1 n | Q5 | Q1 | **Spread** | p | Folds + | Ex-best |
|---|---|---|---|---|---|---|---|---|
| **Primary 60d** | 1,427 | 1,503 | +1.41% | −1.60% | **+3.01%** | 1.3e-7 | 17/20 | +3.06% |
| Discovery 60d | 635 | 709 | +1.70% | −1.73% | +3.43% | 1.3e-4 | 8/10 | +3.50% |
| Holdout 60d | 792 | 794 | +1.19% | −1.48% | +2.66% | 3.0e-4 | 9/10 | +2.20% |
| Non-Financials 60d | 1,114 | 1,403 | +1.48% | −1.96% | +3.44% | 3.7e-8 | 17/20 | +3.51% |
| Financials 60d (excluded) | 313 | 100 | +1.17% | +3.51% | −2.34% | 0.19 | 9/17 | −2.44% |
| Size: Small | 358 | 595 | +1.38% | −2.87% | +4.25% | 2.7e-5 | 19/20 | |
| Size: Mid | 483 | 504 | +1.71% | −0.51% | +2.22% | 0.038 | 13/20 | |
| Size: Large | 586 | 404 | +1.19% | −1.07% | +2.26% | 0.012 | 14/19 | |

- **Quintile ladder (60d):** Q1 −1.60 · Q2 −0.25 · Q3 −0.14 · Q4 +0.85 · Q5 +1.41 (%) — fully monotonic.
- **Horizon profile (spread):** 5d +0.61% · 10d +1.02% · 20d +1.66% · 30d +1.46% · 40d +1.82% · 60d +3.01% · 90d +3.92% · 126d +3.86%.

**Kill tests** (`corrected/kill_tests_corrected.csv`):

| Test | Perturbation | Result | Pass |
|---|---|---|---|
| KT1 | Drop top-2 folds (2021Q3 & 2022Q1) | fold-mean +3.45% → +2.75%, folds+ 83.3%; event-level spread +2.62% | ✓ |
| KT2 | Drop 2021 | +2.88%, p = 7.9e-7 | ✓ |
| KT3 | Mid + Large caps only | +2.19%, p = 0.0017 | ✓ |
| KT4 | Exclude Layer-4-seen events | +3.05%, folds+ 85.0% | ✓ |
| **KT5** | **1.000% round-trip cost (portfolio)** | **full excess +4.06%; holdout excess −0.88%** | **✗** |
| KT6 | 8Q / expanding thresholds | +2.91% / +2.83% | ✓ |
| KT7 | 40d / 90d horizon | +1.82% / +3.92% | ✓ |

All signal-level kill tests pass. The only portfolio-level kill test fails on the holdout.

---

## 3. Strategy — `corrected/period_metrics_corrected.csv`

**Period split.** Discovery and Holdout are **trade-attributed books**: each holds only trades signalled in its own period, and the holdout book starts empty on the first 2024 signal.

A calendar split of the single continuous book is shown on the last two rows for completeness. Its "holdout" slice includes discovery-signalled trades still open in Jan–Feb 2024, which averaged **+22% net** during the small/mid-cap rally. That flatters the holdout by about 4 pp/yr, so it is **not** the holdout figure.

| Metric | Full period | Discovery (≤ 2023 signals) | **Holdout (≥ 2024 signals)** |
|---|---|---|---|
| Window | 2021-08-11 → 2026-08-11 | 2021-08-11 → 2024-02-13 | 2024-01-17 → 2026-08-11 |
| Trades | 567 | 277 | 296 |
| Total return | +120.7% | +68.6% | +23.9% |
| **CAGR** | **+17.16%** | **+23.16%** | **+8.71%** |
| NIFTY 500 (PR) CAGR | +11.28% | +15.19% | +7.89% |
| **Excess CAGR vs NIFTY 500 PR**\* | **+5.87%** | **+7.97%** | **+0.82%** |
| Mean trade excess vs event universe (60d) | +1.06% | +0.34% | +1.08% |
| Annualised volatility | 16.07% | 14.85% | 16.70% |
| Sharpe, rf = 0 (NIFTY 500) | 1.08 (0.82) | 1.50 (1.09) | 0.59 (0.59) |
| Sharpe, rf = 6% (NIFTY 500) | 0.72 (0.42) | 1.11 (0.68) | 0.24 (0.20) |
| Sortino (rf = 0) | 1.48 | 2.05 | 0.80 |
| Max drawdown (NIFTY 500) | −23.68% (−18.84%) | −19.28% (−18.48%) | −24.95% (−18.84%) |
| Calmar | 0.72 | 1.20 | 0.35 |
| Longest drawdown (sessions) | 423 | 184 | 431 |
| Win rate | 58.4% | 59.2% | 56.4% |
| Profit factor | 2.09 | 2.67 | 1.51 |
| Avg win / avg loss | +15.1% / −10.1% | +16.9% / −9.2% | +12.6% / −10.8% |
| One-way turnover / yr | 381% | 371% | 386% |
| Capacity, 1% ADV (90% of trades fit) | ₹1.6 Cr | ₹1.2 Cr | ₹2.4 Cr |
| Capacity, 5% ADV (90% of trades fit) | ₹8.1 Cr | ₹6.2 Cr | ₹12.2 Cr |
| *Calendar split of the full book: CAGR / excess* | — | *+21.84% / +6.67%* | *+13.05% / +5.19% (flattered, see above)* |

\* NIFTY 500 is a **price-return** index, while strategy prices are dividend-adjusted. Excess over a Total Return Index would be roughly 1.0–1.5 pp/yr lower. On the holdout that puts excess at about **≤ 0%**. No TRI series is available in the repository.

**Cost sensitivity** (`corrected/cost_sensitivity_corrected.csv`):

| Round-trip cost | Full CAGR / excess | Full Sharpe (rf = 0) | Holdout CAGR / excess |
|---|---|---|---|
| 0.300% | +18.42% / +7.13% | 1.15 | +9.89% / +2.00% |
| 0.585% | +17.16% / +5.87% | 1.08 | +8.71% / +0.82% |
| 1.000% | +15.34% / +4.06% | 0.98 | +7.01% / **−0.88%** |

**Placebo** (`corrected/placebo_random_books.csv`: 40 books of random 20% draws of eligible non-financial events, random priority, same mechanics):

- Full-period excess **−1.41% ± 2.37%**; the frozen book (+5.87%) sits about 3 sd above.
- Holdout excess **−4.22% ± 2.85%**; the frozen book (+0.82%) sits about 1.8 sd above.

The SUE ordering adds value relative to random selection. The long-only book does not reliably beat the market.

**Calendar years** (`corrected/yearly_returns_corrected.csv`; same window for strategy and benchmark):

| Year | Window | Strategy | NIFTY 500 PR | Excess | Trades entered |
|---|---|---|---|---|---|
| 2021 | Aug 11 – Dec 31 | +7.17% | +8.07% | −0.90% | 37 |
| 2022 | full | +6.17% | +3.02% | +3.15% | 120 |
| 2023 | full | +40.71% | +25.76% | +14.94% | 120 |
| 2024 | full | +28.30% | +15.16% | +13.13% | 110 |
| 2025 | full | −3.02% | +6.69% | −9.70% | 120 |
| 2026 | Jan 1 – Aug 11 | +10.78% | −0.80% | +11.58% | 60 |

---

## 4. Final classification

- **Signal: CONFIRMED.**
- **Tradeable strategy: INCONCLUSIVE — forward-test candidate, not validated.** The "VALIDATED TRADING STRATEGY" label remains **REJECTED**.
  - Full-period outperformance is concentrated in the discovery-signalled trades and in 2023–24.
  - Trades signalled in the (already-seen) holdout matched the price index, with equal risk-adjusted return.
  - The configuration was chosen with the holdout in view.

---

## 5. Forward-test protocol (pre-registered; identical to `live_config_pead_v2_corrected.md` §3)

- **Evaluation standard:** realised daily mark-to-market NAV, discrete share-and-cash accounting, evaluated against NIFTY 500 and the equal-weight event-universe mean.
- **Minimum forward horizon:** at least 4 to 6 earnings seasons (12–18 calendar months of live forward records).
- **Kill criteria.** The strategy is permanently killed if any one of these holds:
  1. Cumulative strategy return trails NIFTY 500 over 4 consecutive earnings seasons (excess ≤ 0%).
  2. Average Q5 net trade return trails the cross-sectional event-universe average (excess vs event universe ≤ 0%).
  3. Realised portfolio drawdown exceeds −25.0%.
- **No backfill:** only events filed after 2026-09-22 may enter `forward_record_pead_v2.csv`.
