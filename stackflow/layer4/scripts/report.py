"""Layer 4 Parts D/E + deliverables.
Runs analyse.main() for returns, then holdout/FDR/surprise analysis and the 3 CSVs.
"""
import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexicon import THEMES
import analyse

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer4"
CACHE = os.path.join(ROOT, "cache")
RES = os.path.join(ROOT, "results")
HOR = ["5d", "10d", "30d", "6m"]
COST = 0.585
DISC_END = pd.Timestamp("2023-12-31")


def bh_fdr(p):
    p = np.asarray(p, float)
    ok = np.isfinite(p)
    q = np.full(len(p), np.nan)
    idx = np.where(ok)[0]
    if not len(idx):
        return q
    pv = p[idx]
    o = np.argsort(pv)
    n = len(pv)
    adj = pv[o] * n / (np.arange(n) + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.clip(adj, 0, 1)
    q[idx] = out
    return q


def tstat_p(x):
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    if len(x) < 8:
        return np.nan, np.nan, len(x)
    m = x.mean()
    se = x.std(ddof=1) / np.sqrt(len(x))
    if se == 0:
        return m, np.nan, len(x)
    from scipy import stats
    t = m / se
    return m, 2 * (1 - stats.t.cdf(abs(t), len(x) - 1)), len(x)


def main():
    ev = analyse.main()
    ev["event_date"] = pd.to_datetime(ev.event_date)
    ev["period"] = np.where(ev.event_date <= DISC_END, "discovery", "holdout")
    ev["q"] = ev.event_date.dt.to_period("Q")

    # ---------- mood buckets ----------
    lines = []
    def bucket_table(col, label, sub=None):
        d = ev if sub is None else sub
        d = d[d[col].notna()].copy()
        if len(d) < 30:
            return None
        d["b"] = pd.qcut(d[col], 3, labels=["low", "mid", "high"], duplicates="drop")
        rows = []
        for b, g in d.groupby("b", observed=True):
            r = dict(bucket=b, n=len(g))
            for h in HOR:
                r["xs_univ_" + h] = 100 * g["xs_univ_" + h].mean()
            rows.append(r)
        return pd.DataFrame(rows)

    out = {}
    for col, lab in [("mood_remarks", "FinBERT mood - remarks"),
                     ("mood_qna", "FinBERT mood - Q&A"),
                     ("mood_all", "FinBERT mood - all")]:
        out[lab] = bucket_table(col, lab)

    # ---------- theme scores ----------
    theme_cols = []
    for th in THEMES:
        a, b = "rem_th_%s_p1k" % th, "qa_th_%s_p1k" % th
        ev["theme_%s" % th] = ev[[c for c in (a, b) if c in ev.columns]].sum(axis=1, min_count=1)
        theme_cols.append("theme_%s" % th)
    for c in [x for x in ev.columns if x.startswith("rem_lm_") and x.endswith("_p1k")]:
        nm = c.replace("rem_lm_", "lm_").replace("_p1k", "")
        qa = c.replace("rem_", "qa_")
        ev[nm] = ev[[x for x in (c, qa) if x in ev.columns]].sum(axis=1, min_count=1)
        theme_cols.append(nm)

    # ---------- per-feature discovery/holdout ----------
    rows = []
    H = "30d"
    for f in theme_cols:
        d = ev[ev[f].notna() & ev["xs_univ_" + H].notna()]
        if len(d) < 40:
            continue
        disc = d[d.period == "discovery"]
        hold = d[d.period == "holdout"]
        if len(disc) < 30:
            continue
        hi = disc[disc[f] > disc[f].median()]["xs_univ_" + H]
        lo = disc[disc[f] <= disc[f].median()]["xs_univ_" + H]
        m_d, p_d, n_d = tstat_p(np.concatenate([hi.values, -lo.values]))
        rec = dict(feature=f, n_disc=len(disc), n_hold=len(hold),
                   disc_effect=100 * m_d if np.isfinite(m_d) else np.nan, disc_p=p_d)
        if len(hold) >= 30:
            hh = hold[hold[f] > disc[f].median()]["xs_univ_" + H]
            hl = hold[hold[f] <= disc[f].median()]["xs_univ_" + H]
            m_h, p_h, n_h = tstat_p(np.concatenate([hh.values, -hl.values]))
            rec["hold_effect"] = 100 * m_h if np.isfinite(m_h) else np.nan
            rec["hold_p"] = p_h
            fo = []
            for qq, g in hold.groupby("q"):
                if len(g) < 8:
                    continue
                a = g[g[f] > disc[f].median()]["xs_univ_" + H].mean()
                b2 = g[g[f] <= disc[f].median()]["xs_univ_" + H].mean()
                if np.isfinite(a) and np.isfinite(b2):
                    fo.append(a - b2)
            rec["hold_folds"] = len(fo)
            rec["hold_fold_pos"] = float(np.mean([x > 0 for x in fo])) if fo else np.nan
        rows.append(rec)
    summ = pd.DataFrame(rows)
    if len(summ):
        summ["disc_q"] = bh_fdr(summ.disc_p.values)
        def status(r):
            if not np.isfinite(r.get("disc_q", np.nan)) or r["disc_q"] > 0.10:
                return "not established"
            if not np.isfinite(r.get("hold_effect", np.nan)):
                return "not established"
            if np.sign(r["hold_effect"]) != np.sign(r["disc_effect"]):
                return "reversed on holdout"
            fp = r.get("hold_fold_pos", np.nan)
            if np.isfinite(fp) and fp >= 0.65:
                return "finding"
            return "not established"
        summ["status"] = summ.apply(status, axis=1)
    summ.to_csv(os.path.join(RES, "trigger_word_summary.csv"), index=False)

    # ---------- trigger_word_events.csv ----------
    hp = os.path.join(CACHE, "phrase_hits.csv")
    if os.path.exists(hp):
        ph = pd.read_csv(hp)
        ph = ph.drop_duplicates(subset=["url", "trigger_word", "section"])
        keep = ["symbol", "event_date", "filing_date", "company", "industry", "period",
                "surprise", "mood_remarks", "mood_qna"] + \
               ["ret_" + h for h in HOR] + ["xs_nifty_" + h for h in HOR] + \
               ["xs_univ_" + h for h in HOR]
        keep = [c for c in keep if c in ev.columns]
        m = ph.merge(ev[keep + ["url"]] if "url" in ev.columns else ev[keep],
                     on=["symbol"], how="inner", suffixes=("", "_e"))
        m = m.rename(columns={"company": "company_name", "industry": "sector",
                              "event_date": "call_date_used",
                              "mood_remarks": "finbert_mood_remarks",
                              "mood_qna": "finbert_mood_qna",
                              "surprise": "earnings_surprise"})
        m.to_csv(os.path.join(RES, "trigger_word_events.csv"), index=False)
        print("trigger_word_events.csv: %d rows" % len(m))

    json.dump({k: (v.to_dict("records") if v is not None else None)
               for k, v in out.items()},
              open(os.path.join(RES, "mood_buckets.json"), "w"), indent=1, default=str)

    # ---------- console summary ----------
    print("\n=== EVENTS ===")
    print("total=%d  discovery=%d  holdout=%d  symbols=%d"
          % (len(ev), (ev.period == "discovery").sum(), (ev.period == "holdout").sum(),
             ev.symbol.nunique()))
    print("event_src:", ev.event_src.value_counts().to_dict())
    for h in HOR:
        print("  %-4s complete: %d (%.0f%%)" % (h, ev["ret_" + h].notna().sum(),
                                                100 * ev["ret_" + h].notna().mean()))
    print("\n=== MOOD BUCKETS (xs_univ %, by tercile) ===")
    for lab, t in out.items():
        if t is None:
            print("  %s: insufficient n" % lab)
            continue
        print("\n" + lab)
        print(t.round(3).to_string(index=False))
    print("\n=== FEATURE SUMMARY (30d, xs_univ) ===")
    if len(summ):
        s2 = summ.sort_values("disc_p")
        print(s2.round(4).to_string(index=False))
        print("\nsurvived FDR q<=0.10 on discovery: %d / %d"
              % ((summ.disc_q <= 0.10).sum(), len(summ)))
        print("status counts:", summ.status.value_counts().to_dict())
    # surprise control
    print("\n=== SURPRISE CONTROL ===")
    d = ev[ev.surprise.notna() & ev.mood_all.notna() & ev["xs_univ_30d"].notna()]
    print("events with surprise: %d (%.0f%%)" % (len(d), 100 * len(d) / max(len(ev), 1)))
    if len(d) >= 40:
        import statsmodels.api as sm
        X = sm.add_constant(d[["mood_all"]])
        r1 = sm.OLS(d["xs_univ_30d"], X).fit()
        X2 = sm.add_constant(d[["mood_all", "surprise"]])
        r2 = sm.OLS(d["xs_univ_30d"], X2).fit()
        print("  mood alone     : beta=%.4f p=%.3f" % (r1.params["mood_all"], r1.pvalues["mood_all"]))
        print("  mood + surprise: beta=%.4f p=%.3f  (surprise beta=%.4f p=%.3f)"
              % (r2.params["mood_all"], r2.pvalues["mood_all"],
                 r2.params["surprise"], r2.pvalues["surprise"]))
    else:
        print("  insufficient overlap for the regression")


if __name__ == "__main__":
    main()
