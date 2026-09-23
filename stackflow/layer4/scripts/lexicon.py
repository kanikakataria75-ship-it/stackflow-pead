"""Layer 4 lexicon - FIXED in pre_registration.md before any return was joined."""

# Loughran-McDonald finance categories (compact free subsets of the published lists)
LM = {
    "negative": """abandon abandoned abandoning adverse adversely against aggravate alleged
        anomalies anomaly bad breach breaches burden burdened cancel cancellation challenge
        challenged challenges challenging closed closing concern concerned concerns
        constrain constrained correction crisis critical damage damages decline declined
        declines declining default deficiency deficit delay delayed delays deteriorate
        deteriorated deterioration difficult difficulties difficulty diminish diminished
        disappointing disruption disruptions downgrade downturn drag erosion failure
        failures fell forced hurt impair impaired impairment inability inadequate
        ineffective inefficiency insufficient lack lag lagging litigation loss losses
        negative negatively omitted penalties penalty poor pressure pressures problem
        problems recession reduce reduced reduction refuse resign restructuring setback
        severe shortage shortfall shrink slow slowdown slower sluggish stagnant struggle
        suffer suffered suspension termination threat troubled unable uncertain
        underperform unfavorable unfavourable volatile weak weaken weakened weakening
        weakness worse worsen worsening writedown writeoff""".split(),
    "positive": """able accomplish achieve achieved achievement achievements advance
        advantage advantages attain attractive beneficial benefit benefited benefits best
        better boost breakthrough brilliant courageous creative delight delighted despite
        dream durable efficiency efficient empower enable enabled encouraged encouraging
        enhance enhanced enhancement enjoy enjoyed excellence excellent exceptional
        excited exciting exclusive favorable favourable gain gained gains good great
        greater growth healthy highest impressive improve improved improvement
        improvements incredible innovate innovation leadership leading loyal opportunities
        opportunity optimistic outperform outstanding pleased positive positively premier
        profitable progress prospered prosperity record rebound recover recovered recovery
        resilient revolutionize reward rewarding robust satisfaction satisfactory smooth
        solid stability stable strength strengthen strengthened strong stronger strongest
        succeed success successful successfully superior surge sustainable transform
        tremendous upgrade upside valuable win winner winning""".split(),
    "uncertainty": """almost ambiguity ambiguous anticipate anticipated apparently
        appear appeared appears approximate approximately assume assumed assumption
        assumptions believe believed cautious clarification confusion contingency
        contingent could depend depended depending depends doubt doubtful exposure
        fluctuate fluctuation fluctuations hidden imprecise indefinite indeterminate
        likely may maybe might nearly occasionally pending perhaps possible possibly
        precaution predict predicted prediction preliminary probable probably random
        recalculate reassess revise risk risks risky roughly rumors seems seldom
        sometimes somewhat speculate speculation sporadic sudden suggest suggests
        tending tentative turbulence uncertain uncertainly uncertainties uncertainty
        unclear unconfirmed undecided undefined unexpected unforeseen unknown unplanned
        unpredictable unproven unsettled unusual vagaries vague variability variable
        variant variation varied varies vary volatile volatility""".split(),
    "litigious": """adjudication allegation allegations appeal appellate arbitration
        attorney claim claimant claims contract contractual convict conviction court
        courts defendant dispute disputed disputes judicial jurisdiction law lawsuit
        lawsuits legal legally liabilities liability litigation plaintiff prosecute
        prosecution regulation regulations regulatory settlement statute statutory sue
        sued suit testimony tribunal verdict""".split(),
    "constraining": """abide bound bounded commit commitment commitments committed compel
        compelled comply compulsory confine confined constrain constrained constraint
        constraints depend dependence dependent forbid forbidden imposed imposing
        limit limitation limitations limited limiting mandate mandated mandatory
        obligated obligation obligations obliged preclude precluded prohibit prohibited
        prohibition require required requirement requirements restrict restricted
        restriction restrictions restrictive stipulate stipulated""".split(),
    "strong_modal": """always best clearly definitely definitively highest lowest must
        never strongly undoubtedly unequivocally will without doubt certainly""".split(),
    "weak_modal": """almost apparently appears conceivably could depending may maybe
        might occasionally perhaps possible possibly seldom sometimes suggests
        uncertain""".split(),
}

# Hand-written Indian-concall phrases, by theme
THEMES = {
    "positive_guidance": ["strong demand", "order book", "capacity expansion",
                          "margin expansion", "upgrade guidance", "record quarter",
                          "market share gain", "robust demand", "healthy demand",
                          "strong pipeline", "operating leverage", "demand is strong",
                          "all time high", "best ever"],
    "negative_caution": ["headwinds", "margin pressure", "subdued demand",
                         "inventory destocking", "slowdown", "one-off",
                         "challenging environment", "demand weakness", "cost pressure",
                         "de-growth", "muted", "soft demand", "under pressure",
                         "lower than expected"],
    "hedging_evasion": ["difficult to say", "too early to comment", "we will come back",
                        "not in a position", "let us see", "cannot comment",
                        "hard to predict", "wait and watch", "difficult to predict",
                        "too early to say", "come back to you"],
    "capital_actions": ["capex", "fund raise", "qip", "debt reduction", "buyback",
                        "deleveraging", "preferential allotment", "capital expenditure",
                        "debt repayment", "fund raising"],
}
