"""
StackFlow Layer 1 - Data source probe.
Purpose: determine, EMPIRICALLY, which NSE sectoral index tickers are
retrievable and how much clean daily history each actually has.
Nothing is assumed from prior knowledge - the candidate list below is a
superset to be tested, and only what verifiably returns data is used.
Writes nothing except into stackflow/cache/.
"""
import warnings, json, sys
warnings.filterwarnings("ignore")
import yfinance as yf
import pandas as pd

CANDIDATES = {
    # broad market benchmark candidates
    "NIFTY_500":        ["^CRSLDX"],
    "NIFTY_50":         ["^NSEI"],
    # sectoral candidates - multiple ticker spellings tried per sector
    "NIFTY_AUTO":       ["^CNXAUTO"],
    "NIFTY_BANK":       ["^NSEBANK"],
    "NIFTY_FIN_SERVICE":["NIFTY_FIN_SERVICE.NS", "^CNXFIN"],
    "NIFTY_FMCG":       ["^CNXFMCG"],
    "NIFTY_IT":         ["^CNXIT"],
    "NIFTY_MEDIA":      ["^CNXMEDIA"],
    "NIFTY_METAL":      ["^CNXMETAL"],
    "NIFTY_PHARMA":     ["^CNXPHARMA"],
    "NIFTY_PSU_BANK":   ["^CNXPSUBANK"],
    "NIFTY_PVT_BANK":   ["NIFTY_PVT_BANK.NS", "^NIFTYPVTBANK"],
    "NIFTY_REALTY":     ["^CNXREALTY"],
    "NIFTY_ENERGY":     ["^CNXENERGY"],
    "NIFTY_INFRA":      ["^CNXINFRA"],
    "NIFTY_HEALTHCARE": ["NIFTY_HEALTHCARE.NS", "^CNXHEALTHCARE"],
    "NIFTY_CONSR_DURBL":["NIFTY_CONSR_DURBL.NS"],
    "NIFTY_OIL_AND_GAS":["NIFTY_OIL_AND_GAS.NS"],
    "NIFTY_COMMODITIES":["^CNXCMDT"],
    "NIFTY_CONSUMPTION":["^CNXCONSUM"],
    "NIFTY_PSE":        ["^CNXPSE"],
    "NIFTY_SERV_SECTOR":["^CNXSERVICE"],
    "NIFTY_MNC":        ["^CNXMNC"],
}

rows = []
for name, tickers in CANDIDATES.items():
    best = None
    for t in tickers:
        try:
            df = yf.download(t, start="1990-01-01", interval="1d",
                             auto_adjust=False, progress=False, threads=False)
        except Exception as e:
            rows.append(dict(sector=name, ticker=t, status=f"ERROR {type(e).__name__}",
                             n=0, start="", end="", nan_close=0))
            continue
        if df is None or len(df) == 0:
            rows.append(dict(sector=name, ticker=t, status="EMPTY", n=0,
                             start="", end="", nan_close=0))
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        close = df["Close"].dropna()
        rec = dict(sector=name, ticker=t, status="OK", n=int(len(close)),
                   start=str(close.index[0].date()), end=str(close.index[-1].date()),
                   nan_close=int(df["Close"].isna().sum()))
        rows.append(rec)
        if best is None or rec["n"] > best["n"]:
            best = rec

res = pd.DataFrame(rows)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
print(res.to_string(index=False))
res.to_csv(r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache/_probe_results.csv", index=False)
print("\nOK count:", (res.status == "OK").sum(), "of", len(res))
