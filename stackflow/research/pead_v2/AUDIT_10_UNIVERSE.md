# AUDIT 10: Point-in-Time Universe Eligibility Audit

**Audit Date:** 2026-09-22  
**Universe Scope:** 421 NSE-Listed Equities  
**Active Portfolio Breadth:** 246 Unique Symbols Executed  
**Status:** **PASSED WITH NOTED METHODOLOGICAL CAVEATS**

---

## 1. Trade Eligibility Verification

For each of the 579 executed trades in `trade_ledger_pead_v2_audited.csv`, the following point-in-time conditions were tested:

| Eligibility Rule | Pre-Registered Standard | Audit Result Across 579 Trades | Status |
|---|---|---|:---:|
| **Minimum Entry Price** | $P_{\text{entry}}^{\text{Open}} \ge \text{INR } 50.00$ | Min observed: **INR 52.51** (0 violations) | **PASSED** |
| **Minimum Trailing Liquidity** | Trailing 20d ADV $\ge \text{INR } 1.0\text{ Cr}$ | All trades satisfied liquidity filter at entry | **PASSED** |
| **Sector Exclusion** | Exclude Banks & NBFCs | 100% Non-Financial taxonomy (0 violations) | **PASSED** |
| **Ex-Ante SUE Signal** | $Q_{\text{ex-ante}} = 5$ (Top 20% by prior 365d cuts) | 100% assigned to Q5 ex-ante (0 violations) | **PASSED** |
| **Historical Data Depth** | $\ge 6$ prior YoY changes ($\ge 10$ historical Qs) | Validated across 100% of event SUEs | **PASSED** |

---

## 2. Universe Composition & Symbol Concentration

- **Candidate Universe:** 421 symbols with structured XBRL filings.
- **Executed Universe:** 246 unique symbols were selected into the 30-slot book across the 5-year backtest.
- **Symbol Concentration:**
  - Most frequent symbol: 7 trades (e.g. quarterly recurring beats).
  - Top 10 most frequent symbols account for only **52 of 579 trades (9.0%)**.
  - 85% of symbols appeared 1 to 3 times.
  - The strategy is diversified across the broad Indian corporate landscape, not concentrated in a small handful of repeated names.

---

## 3. Critical Methodological Caveat: Static Universe Construction

> [!CAUTION]
> **Universe Backfill vs. Strict Point-in-Time Index Membership:**  
> The 421-stock universe used in StackFlow was extracted from a consolidated XBRL filing cache created in 2024–2026. While each individual event enforces point-in-time thresholds and prices, the *master list of 421 symbols* represents companies that were actively tracked and filing during the 2024–2026 research period.
>
> **Implications:**
> 1. Companies that underwent liquidation, total insolvency, or hostile regulatory delisting prior to 2023 (and therefore had incomplete or missing XBRL archives) were not in the 421-stock candidate pool.
> 2. This creates a mild **survivorship / listing selection bias** common to post-hoc universe extraction.
> 3. However, because the strategy requires a minimum INR 1 Cr daily liquidity and $\ge 10$ quarters of consistent quarterly filings, the eligible universe was structurally restricted to established mid- and large-cap businesses where outright catastrophic failure rates are historically low.

**Conclusion:** Trade-level eligibility rules (price, liquidity, sector, history) were strictly enforced at every event date. The universe selection methodology, however, carries a known survivorship artifact that must be documented as a research caveat.
