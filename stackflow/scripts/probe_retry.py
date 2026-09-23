import warnings, time, sys
warnings.filterwarnings("ignore")
import yfinance as yf
import pandas as pd

T = ["^CNXAUTO","^CNXFIN","^CNXFMCG","^CNXMEDIA","^CNXMETAL","^CNXPSUBANK",
     "^CNXREALTY","^CNXENERGY","^CNXINFRA","^CNXCMDT","^CNXCONSUM","^CNXPSE",
     "^CNXSERVICE","^CNXMNC","NIFTY_PVT_BANK.NS","NIFTY_HEALTHCARE.NS",
     "NIFTY_CONSR_DURBL.NS","NIFTY_OIL_AND_GAS.NS","NIFTY_FIN_SERVICE.NS"]
out=[]
for t in T:
    n=0; s=e=""
    for attempt in range(3):
        try:
            h = yf.Ticker(t).history(period="max", interval="1d", auto_adjust=False)
        except Exception as ex:
            h = None
        if h is not None and len(h) > 5:
            c = h["Close"].dropna(); n=len(c); s=str(c.index[0].date()); e=str(c.index[-1].date())
            break
        time.sleep(4)
    out.append(dict(ticker=t, n=n, start=s, end=e))
    print(f"{t:24s} n={n:6d} {s} -> {e}", flush=True)
    time.sleep(2)
pd.DataFrame(out).to_csv(r"C:/Users/kanik/Desktop/stackflow claude/stackflow/cache/_probe_retry.csv", index=False)
