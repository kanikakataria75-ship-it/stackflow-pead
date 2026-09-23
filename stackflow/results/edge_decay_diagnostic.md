# Edge Decay Diagnostic — Why Did Layer 1 Weaken?

**Date:** 2026-09-21
**Type:** Explanatory research. Not a tradeable-signal test. No forward-return claim.
**Criteria fixed in advance:** `pre_registration_decay_diagnostic.md`
**The frozen Layer 1 config was not modified, re-tuned, or re-opened by this work.**

---

## 0. CORRECTION FIRST: "a step at ~2015" was over-claimed

Before any of D1/D2/D3, a finding that undercuts the premise of all three — and it
corrects my own Phase 1c write-up, not someone else's.

Phase 1c reported the decay as *"a step, not a drift ... stable across two independent
blocks."* **That claim was an artifact of where the 5-year block boundaries happened to
fall.** Scanning every candidate break year on the constant panel:

| split year | early norm | late norm | gap |
|---|---|---|---|
| 2011 | −0.159 | −0.059 | −0.100 |
| 2012 | −0.156 | −0.053 | −0.104 |
| 2013 | −0.128 | −0.061 | −0.067 |
| 2014 | −0.143 | −0.045 | −0.098 |
| **2015** | −0.142 | −0.037 | **−0.105** |
| 2016 | −0.142 | −0.027 | −0.115 |
| 2017 | −0.136 | −0.023 | −0.113 |
| 2018 | −0.127 | −0.022 | −0.105 |
| **2019** | −0.129 | −0.005 | **−0.124 ← largest** |

The gap is **roughly as large anywhere from 2011 to 2019**, and peaks at **2019**, not
2015. Year-by-year normalised strength is extremely noisy, with strong years on *both*
sides of any cut — 2018 (−0.152), 2022 (−0.130), 2023 (−0.138) are as strong as 2011
(−0.143), 2014 (−0.136), 2015 (−0.145), while 2012 (+0.061) sits in the "strong" era.

**What survives:** the decay itself is real and not just noise. On fold-level units
(calendar years, constant 19-sector panel), early vs late is
**−0.141 vs −0.029 normalised, one-sided permutation p = 0.016** (raw: −1.562% vs
−0.320%, p = 0.024). It is not carried by one or two years either — dropping the early
period's two strongest years still leaves −0.113 vs −0.029.

**What does not survive:** the *dating*. There is a real decline; there is **no
identifiable 2015 event**.

This matters directly, because D1 and D3's pre-registered criteria both hinge on
*timing coincidence with the ~2015 step*. **With the step undated across a 2011–2019
window, those timing tests lose most of their discriminating power.** That is stated here
rather than quietly working around it, and it is why two of the three verdicts below are
inconclusive rather than decided.

---

## 1. D3 — Panel/structural artifact: **RULED OUT**

The only candidate fully answerable from cached data, and it answers cleanly.

**Timing check (pre-registered).** Phase 1c's note is confirmed precise:

| year | 2007–2017 | 2018 | 2019 | 2020 | 2021–2026 |
|---|---|---|---|---|---|
| Panel C live sectors | **19 (unchanged, 11 straight years)** | 20 | 20 | 21 | 23 |

The first new Panel C entrant is **NIFTY HOUSING FINANCE, 2018-04-02**. Entrants after
that: INSURANCE (2019), CONSUMER SERVICES (2020), HOSPITALS (2021). **Every panel change
postdates even the latest candidate break year, and postdates 2015 by three years.**
Per the pre-registered criterion — "less plausible if the step predates any panel change"
— this is **explicit evidence against D3**.

**Decisive test (pre-specified).** Re-run the frozen cell on a **constant 19-sector
panel** that never changes composition:

| panel | early 2005–15 | late 2016–26 | normalised ratio |
|---|---|---|---|
| Panel C (variable, 19→23) | −1.550% (norm −0.142) | −0.380% (norm −0.042) | 3.37× |
| **Constant 19 (no change ever)** | **−1.550% (norm −0.142)** | **−0.300% (norm −0.027)** | **5.28×** |

The decay is **stronger**, not weaker, on a panel whose composition never changed. It
cannot be a composition artifact.

**Identity check.** Bottom-tercile membership is broadly stable across eras — PSU BANK,
TELECOM, REALTY, IT, OIL & GAS and FMCG are frequent exclusions in *both* periods. No
wholesale turnover suggesting an index-methodology shift.

> **D3 verdict: RULED OUT.** The decay survives in full on a fixed panel, and every panel
> change happened years after the decline was already underway.

---

## 2. D1 — Sector-specific capital / arbitrage: **INCONCLUSIVE**

**Sectoral/thematic fund AUM — clear trend, but far too late.**
Sectoral/thematic AUM reached **₹4.55 lakh crore by March 2025, ~1.5× in one year**, and
**15.45% of total equity AUM**; in FY25, **52 of 70 NFOs** were sectoral/thematic, raising
**₹73,633 crore**, versus **37 of 58** raising **₹25,493 crore** in FY24 ([AMFI Annual
Report FY2025](https://www.amfiindia.com/Themes/Theme1/downloads/AMFI_AnnualMFReport2025.pdf)).
The category roughly doubled from **₹2 trillion (July 2023) to ₹4.21 trillion (July 2024)**
([Business Standard](https://www.business-standard.com/markets/mutual-fund/thematic-funds-emerge-as-largest-mf-category-aum-doubles-in-a-year-124081900778_1.html)).

This is a **2023–2025** phenomenon — roughly **4 to 12 years after** the plausible decay
window. Per the pre-registered criterion ("less plausible if the inflection is clearly
later than the step"), the fund-flow channel is **weakened, not supported**.

**Sector derivatives — timing fits, mechanism does not.**
NSE launched **Bank Nifty weekly options on 27 May 2016**, the first sectoral index to get
them ([Business Standard](https://www.business-standard.com/article/pti-stories/nse-to-launch-weekly-options-contracts-on-bank-nifty-index-116050501487_1.html)),
extending to **Nifty IT weekly options in March 2019**
([Business Standard](https://www.business-standard.com/article/pti-stories/nse-launches-weekly-options-on-nifty-it-index-119031100835_1.html)).
That 2016–2019 ramp sits **squarely inside** the 2011–2019 decay window and is
specifically sector-level.

**But the mechanism link is weak and untested.** Bank Nifty weeklies are overwhelmingly a
short-dated, intraday volatility product. There is no evidence offered — here or in any
source found — that weekly-expiry option volume corrects **20-day-trailing / 90-day-forward
sector relative-strength** mispricing. Treating this as support would be building the
post-hoc story the pre-registration exists to prevent. It is recorded as
**timing-compatible but mechanistically unsupported**.

**FII/DII sector-level flow responsiveness:** **not obtainable** at usable granularity
from free public sources. Sector-attributed institutional flow series are largely
paid/proprietary. It would genuinely help and is noted as a gap, not estimated.

> **D1 verdict: INCONCLUSIVE.** The one well-dated sector-specific capital metric inflects
> far too late to explain the decay. The one timing-compatible development lacks any
> demonstrated mechanism. And the timing test D1 was designed around lost its power once
> the "2015 step" proved undated.

---

## 3. D2 — Broad market efficiency increase: **WEAKENED in its strong form**

**Efficiency proxies are real but late.** A market-microstructure study of NSE
**2020–2024** reports bid-ask spreads **−23.4%**, market depth **+18.1%**, and price
adjustment half-life **−50%** ([Binghamton, *NEJCS* vol.8](https://orb.binghamton.edu/nejcs/vol8/iss1/9/)).
That window is **later than** the decay window.

**Algo participation rose steadily, not stepwise.** NSE cash-market algo share:
**14% (2010) → ~35% (2020) → 53% (2024)**; co-location **3.1% (2010) → 35.7% (2024)** in
cash, **7.3% → 62.1%** in equity derivatives
([Investing.com summarising NSE data](https://in.investing.com/news/colocation-hits-357-algo-trading-surges-to-53-the-techdriven-shift-in-nse-4655643);
[Business Standard](https://www.business-standard.com/markets/news/in-a-first-machines-overtake-humans-in-nse-s-cash-market-trades-125041500893_1.html)).
A *gradual* rise actually fits a *gradual, undated* decay better than a dated step would.
**Intermediate annual values (2013–2019) were not obtainable** from free sources — only
endpoints are published in accessible form, so the inflection shape cannot be tested.

**The discriminating evidence, and it cuts against D2.** If market-wide efficiency had
compressed lag-based signals generally, **stock-level** relative-strength should have
decayed too. It did not. A study of **232 continuously traded Nifty 500 firms over
July 2015 – June 2024** — almost exactly the post-decay period — finds Winner-minus-Loser
portfolios generating **"large and highly significant abnormal profits," with momentum
strength increasing at longer horizons**, and specifically that **"Loser portfolios
persistently underperform"** ([ResearchGate](https://www.researchgate.net/publication/397345499_A_Multi-Factor_and_Portfolio-Based_Approach_of_Momentum_Anomaly_and_Risk_Premium_in_the_Indian_Stock_Market)).

That loser-portfolio finding is the **direct stock-level analogue of Layer 1's
bottom-tercile exclusion** — and over the very window in which the sector-level version
weakened, the stock-level version did not.

**Corroboration of the known weak point.** The same literature notes momentum payoffs
suffer "severe periodic losses ... when markets rebound after enormous losses"
([*Momentum, reversals and liquidity: Indian evidence*, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0927538X23002640)).
This independently matches the regime dependency recorded in `live_config_layer1.md` §B1,
whose failures cluster at V-shaped recoveries. That is a **general property of momentum**,
not a defect unique to this filter.

> **D2 verdict: WEAKENED in its strong form.** Documented efficiency gains postdate the
> decay, and the key prediction of a market-wide explanation — that stock-level lag
> signals should have decayed in step — is contradicted by published evidence covering
> exactly that period. A weak form (gradual efficiency drift contributing something)
> cannot be excluded.

---

## 4. What the evidence supports overall

| explanation | verdict |
|---|---|
| **D3** panel/structural artifact | **RULED OUT** — decay is stronger on a constant panel; all panel changes postdate it |
| **D1** sector-specific arbitrage | **INCONCLUSIVE** — best-dated metric far too late; timing-compatible channel has no demonstrated mechanism |
| **D2** market-wide efficiency | **WEAKENED (strong form)** — proxies postdate the decay, and stock-level momentum did *not* decay over the same window |

**The decay is real** (p ≈ 0.016 on fold-level units, not carried by a couple of years).
**Its cause is not established**, and the data genuinely does not discriminate between a
sector-specific cause and a diffuse one. **This is reported as inconclusive rather than
resolved in favour of a preferred story.**

The one asymmetry worth weight: the single piece of evidence that *does* discriminate —
stock-level momentum persisting strongly through July 2015–June 2024 while sector-level
weakened — points toward the decay being **sector-specific rather than market-wide**.
That is one published study, on one universe, and it is not treated as settled.

**Honest limits.** Timing tests were largely defanged by the undated step. Intermediate
algo-share years and sector-attributed institutional flows are not obtainable from free
sources; both would materially sharpen D1 vs D2 and are noted as gaps, not estimated.
No figure in this document is inferred or reconstructed — every number is cited.

---

## 5. Concrete implication for Layer 2

**Layer 2 should be scoped on the assumption that it does not automatically inherit
Layer 1's decay — but it must budget to measure that, not assume it.**

The most decision-relevant finding is that the one comparable stock-level signal
(loser-portfolio underperformance on Nifty 500) remained **large and highly significant
through July 2015 – June 2024**, the same window in which the sector-level version fell
by two-thirds. That is *mild* evidence Layer 2 operates on a less-arbitraged layer and
may not face the same headwind.

Concretely, Layer 2 should budget for three things from the start:

1. **A pre-registered sub-period stability check, built into its first test rather than
   bolted on.** Layer 1 needed three phases to discover its own decay. Layer 2 should
   report early/late sub-period effect sizes in its *first* results document, with a
   break-point scan rather than fixed blocks — the specific mistake corrected in §0.
2. **A dispersion-normalised metric alongside the raw one.** Raw effect sizes conflated a
   genuine signal decline with a calmer cross-section in Layer 1; normalising separated
   them and changed the reading.
3. **Explicit handling of the reversal-regime weakness.** It is a documented general
   property of momentum in Indian equities, not a quirk of sector data, so Layer 2's
   stock-level relative-strength signal should be **expected** to inherit it. Design for
   it, or measure it early, rather than rediscovering it at integration.

The Phase 1c wrap-up warning stands unchanged: Layer 1 currently delivers ≈ −0.38% per
rebalance and ≈ +0.17% to the pass-through group. **Nothing in this diagnostic improves
that number**, and Layer 2's eventual cost model still has to clear it.

---

*Layer 2 design has not been started. This diagnostic informs that work; it does not
begin it.*

**Sources:**
[AMFI Annual Report FY2025](https://www.amfiindia.com/Themes/Theme1/downloads/AMFI_AnnualMFReport2025.pdf) ·
[Business Standard — thematic funds AUM doubles](https://www.business-standard.com/markets/mutual-fund/thematic-funds-emerge-as-largest-mf-category-aum-doubles-in-a-year-124081900778_1.html) ·
[Business Standard — Bank Nifty weekly options launch](https://www.business-standard.com/article/pti-stories/nse-to-launch-weekly-options-contracts-on-bank-nifty-index-116050501487_1.html) ·
[Business Standard — Nifty IT weekly options](https://www.business-standard.com/article/pti-stories/nse-launches-weekly-options-on-nifty-it-index-119031100835_1.html) ·
[Business Standard — algo overtakes humans in NSE cash trades](https://www.business-standard.com/markets/news/in-a-first-machines-overtake-humans-in-nse-s-cash-market-trades-125041500893_1.html) ·
[Investing.com — colocation 35.7%, algo 53%](https://in.investing.com/news/colocation-hits-357-algo-trading-surges-to-53-the-techdriven-shift-in-nse-4655643) ·
[Binghamton *NEJCS* — NSE microstructure 2020–2024](https://orb.binghamton.edu/nejcs/vol8/iss1/9/) ·
[ResearchGate — momentum & risk premium, Nifty 500, 2015–2024](https://www.researchgate.net/publication/397345499_A_Multi-Factor_and_Portfolio-Based_Approach_of_Momentum_Anomaly_and_Risk_Premium_in_the_Indian_Stock_Market) ·
[ScienceDirect — Momentum, reversals and liquidity: Indian evidence](https://www.sciencedirect.com/science/article/abs/pii/S0927538X23002640)
