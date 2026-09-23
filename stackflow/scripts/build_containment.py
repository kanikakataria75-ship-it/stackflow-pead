"""
StackFlow Part A - sector containment map from ACTUAL constituent lists.
Overlap is measured from real symbols pulled from niftyindices.com constituent
CSVs, never inferred from index naming.

containment(A in B) = |A & B| / |A|   (fraction of A's members also in B)
jaccard(A,B)        = |A & B| / |A | B|
"""
import os, sys, time, json, io
import requests, pandas as pd, numpy as np

sys.path.insert(0, r"C:/Users/kanik/Desktop/stackflow claude/stackflow/config")
from sectors import SECTORS, CACHE_DIR

CSVMAP = {
 "NIFTY AUTO":"ind_niftyautolist.csv",
 "NIFTY BANK":"ind_niftybanklist.csv",
 "NIFTY CAPITAL GOODS":"ind_niftyCapitalGoods_list.csv",
 "NIFTY CEMENT":"ind_NiftyCement_list.csv",
 "NIFTY CHEMICALS":"ind_niftyChemicals_list.csv",
 "NIFTY COMMERCIAL & TRANSPORT SERVICES":"ind_niftyCommercialTransportServices_list.csv",
 "NIFTY CONSTRUCTION":"ind_niftyConstruction_list.csv",
 "NIFTY CONSUMER DURABLES":"ind_niftyconsumerdurableslist.csv",
 "NIFTY CONSUMER SERVICES":"ind_niftyConsumerServices_list.csv",
 "NIFTY FINANCIAL SERVICES":"ind_niftyfinancelist.csv",
 "NIFTY FMCG":"ind_niftyfmcglist.csv",
 "NIFTY HEALTHCARE":"ind_niftyhealthcarelist.csv",
 "NIFTY HOSPITALS":"ind_niftyHospitals_list.csv",
 "NIFTY HOUSING FINANCE":"ind_niftyHousingFinance_list.csv",
 "NIFTY INSURANCE":"ind_niftyInsurance_list.csv",
 "NIFTY IT":"ind_niftyitlist.csv",
 "NIFTY MEDIA":"ind_niftymedialist.csv",
 "NIFTY METAL":"ind_niftymetallist.csv",
 "NIFTY NBFC":"ind_niftyNBFC_list.csv",
 "NIFTY OIL & GAS":"ind_niftyoilgaslist.csv",
 "NIFTY PHARMA":"ind_niftypharmalist.csv",
 "NIFTY POWER":"ind_niftyPower_list.csv",
 "NIFTY PRIVATE BANK":"ind_nifty_privatebanklist.csv",
 "NIFTY PSU BANK":"ind_niftypsubanklist.csv",
 "NIFTY REALTY":"ind_niftyrealtylist.csv",
 "NIFTY RETAIL":"ind_niftyRetail_list.csv",
 "NIFTY TELECOMMUNICATIONS":"ind_niftyTelecommunications_list.csv",
}
BASE = "https://niftyindices.com/IndexConstituent/"
OUT = os.path.join(CACHE_DIR, "constituents")
os.makedirs(OUT, exist_ok=True)

s = requests.Session()
s.headers.update({"User-Agent":("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
  "Referer":"https://niftyindices.com/indices/equity/sectoral-indices"})

members = {}
for name, fn in CSVMAP.items():
    lp = os.path.join(OUT, fn)
    txt = None
    if os.path.exists(lp):
        txt = open(lp, encoding="utf-8", errors="replace").read()
    if not txt or "Symbol" not in txt:
        for a in range(3):
            try:
                r = s.get(BASE + fn, timeout=40)
                if r.status_code == 200 and "Symbol" in r.text:
                    txt = r.text; open(lp,"w",encoding="utf-8").write(txt); break
            except Exception: pass
            time.sleep(3)
    if not txt or "Symbol" not in txt:
        print(f"  !! {name}: constituent list UNAVAILABLE"); continue
    df = pd.read_csv(io.StringIO(txt))
    syms = set(df["Symbol"].astype(str).str.strip())
    members[name] = syms
    time.sleep(0.5)

names = [n for n in SECTORS if n in members]
print(f"Constituent lists retrieved: {len(names)}/{len(SECTORS)}")
print("\nSector sizes:")
for n in sorted(names, key=lambda x:-len(members[x])):
    print(f"  {n:40s} {len(members[n]):3d}")

C = pd.DataFrame(index=names, columns=names, dtype=float)
J = pd.DataFrame(index=names, columns=names, dtype=float)
for a in names:
    for b in names:
        A, B = members[a], members[b]
        C.loc[a,b] = len(A & B)/len(A) if A else np.nan
        J.loc[a,b] = len(A & B)/len(A | B) if (A|B) else np.nan
C.to_csv(os.path.join(CACHE_DIR,"containment_matrix.csv"))
J.to_csv(os.path.join(CACHE_DIR,"jaccard_matrix.csv"))
json.dump({k:sorted(v) for k,v in members.items()},
          open(os.path.join(CACHE_DIR,"constituents.json"),"w"), indent=1)

THRESH = 0.80
print(f"\nCONTAINMENT EDGES  (>= {THRESH:.0%} of A's members also in B, A != B):")
edges=[]
for a in names:
    for b in names:
        if a!=b and C.loc[a,b] >= THRESH:
            edges.append((a,b,C.loc[a,b],len(members[a]),len(members[b])))
for a,b,v,na,nb in sorted(edges, key=lambda e:-e[2]):
    print(f"  {a:40s} ({na:2d}) -> inside -> {b:32s} ({nb:2d})   {v:.0%}")

# greedy partition: keep larger parents, drop anything nesting inside a kept one
order = sorted(names, key=lambda n: -len(members[n]))
kept, dropped = [], {}
for n in order:
    par = [k for k in kept if C.loc[n,k] >= THRESH]
    if par: dropped[n] = par[0]
    else: kept.append(n)
print(f"\nNON-OVERLAPPING PANEL: {len(kept)} sectors")
for n in sorted(kept): print("  KEEP ", n)
print(f"\nDROPPED: {len(dropped)}")
for n,p in sorted(dropped.items()): print(f"  DROP  {n:40s} (nests in {p})")

# residual overlap among kept
print("\nResidual pairwise Jaccard among KEPT sectors > 0.10:")
res=[(a,b,J.loc[a,b]) for i,a in enumerate(kept) for b in kept[i+1:] if J.loc[a,b]>0.10]
for a,b,v in sorted(res,key=lambda e:-e[2]): print(f"  {a:38s} <-> {b:38s} {v:.0%}")
if not res: print("  (none)")
json.dump({"kept":sorted(kept),"dropped":dropped,"threshold":THRESH},
          open(os.path.join(CACHE_DIR,"partition.json"),"w"), indent=1)
