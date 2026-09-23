# AUDIT 09: Independent Transaction Cost and Friction Audit

**Audit Date:** 2026-09-22  
**Baseline Model:** 0.585% Round-Trip (58.5 bps)  
**Sensitivity Tested:** 0.300%, 0.585%, 1.000%  
**Status:** **VERIFIED (Robust Across All Stress Levels)**

---

## 1. Statutory and Market Friction Breakdown

The 0.585% (58.5 bps) round-trip friction model represents realistic institutional/active execution on the National Stock Exchange (NSE) of India for cash equity delivery:

| Friction Component | Regulatory / Market Rate | Buy Side | Sell Side | Round-Trip Total |
|---|---|:---:|:---:|:---:|
| **Securities Transaction Tax (STT)** | 0.100% on delivery turnover | 0.100% | 0.100% | **0.200%** |
| **Brokerage (Institutional / Discount)** | Negotiated / flat rate | 0.025% | 0.025% | **0.050%** |
| **Exchange Transaction Charges (NSE)** | 0.00345% of turnover | 0.003% | 0.003% | **0.007%** |
| **SEBI Turnover Fee** | INR 10 per crore | 0.0001% | 0.0001% | **0.0002%** |
| **State Stamp Duty** | 0.015% on buyer side only | 0.015% | 0.000% | **0.015%** |
| **Goods & Services Tax (GST)** | 18% on (Brokerage + Exchange) | 0.005% | 0.005% | **0.010%** |
| **Bid-Ask Spread & Market Impact** | Half-spread + slippage (INR >10 Cr ADV) | 0.150% | 0.150% | **0.300%** |
| **Total Round-Trip Friction** | | **0.298%** | **0.283%** | **0.585% (58.5 bps)** |

---

## 2. Implementation Audit in the Portfolio Engine

1. **How Cost Was Applied:**
   - In both `src/portfolio_engine.py` and `trade_ledger_pead_v2_audited.csv`, transaction costs are deducted as a flat notional debit:
     $$R_{\text{net}} = R_{\text{gross}} - c = \left(\frac{P_{\text{exit}}^{\text{Close}}}{P_{\text{entry}}^{\text{Open}}} - 1\right) - 0.00585$$
   - In the daily mark-to-market engine, the cost is applied on the exit day $t_{\text{exit}}$:
     $$R_{i, t_{\text{exit}}} = \left(\frac{P_{i, t_{\text{exit}}}}{P_{i, t_{\text{exit}}-1}} - 1\right) - 0.00585$$
2. **Exhaustive Application:**
   - Verified across all 579 executed trades in `trade_ledger_pead_v2_audited.csv`. Zero trades escaped cost deduction.
   - Total friction deducted across all trades:
     $$\text{Total Friction Paid} = 579 \times 0.00585 = 3.38715 \quad (\mathbf{338.7\% \text{ of cumulative sleeve notional}})$$
   - Annual cost drag on the portfolio: approximately **0.67% per annum** (given portfolio turnover of ~115 trades/year across 30 slots $\approx 3.8$ turns/year $\times 58.5$ bps $\times$ 75% active exposure).

---

## 3. Independent Cost Sensitivity Stress Matrix

To ensure the strategy does not hinge on unrealistically low transaction cost assumptions, an independent simulation was performed across three friction regimes:

| Regime | Round-Trip Cost | Strategy CAGR (%) | Nifty 500 CAGR (%) | **Excess CAGR (%)** | MtM Sharpe | Maximum Drawdown (%) | Strategy Survives? |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Low Friction** | 0.300% (30 bps) | **+18.11%** | +11.05% | **+7.06%** | 1.083 | -24.70% | **YES** |
| **Baseline (Frozen V2)** | 0.585% (58.5 bps) | **+16.83%** | +11.05% | **+5.78%** | 1.017 | -25.12% | **YES** |
| **Severe Friction** | 1.000% (100 bps) | **+14.98%** | +11.05% | **+3.93%** | 0.921 | -25.72% | **YES** |
| **Breakeven Cost** | ~1.85% (185 bps) | +11.05% | +11.05% | 0.00% | 0.770 | -27.10% | **BREAKEVEN** |

### Findings:
1. Even under severe friction of **100 bps round-trip** (almost double the baseline), the strategy retains a **+3.93% excess CAGR** over the Nifty 500 and a Sharpe ratio of **0.921**.
2. Breakeven cost is estimated at **~185 bps round-trip**, which is more than 3x the baseline friction.
3. The strategy is robust to execution costs and does not collapse when realistic market impact and taxes are imposed.
