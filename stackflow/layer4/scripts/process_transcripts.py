"""Layer 4 Part B/C - download transcripts, extract text, compute features.

Executes what pre_registration.md fixed. Resumable with checkpoints.
No returns are touched here - this produces text features only.
"""
import io
import os
import re
import sys
import json
import time
import random
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexicon import LM, THEMES

ROOT = r"C:/Users/kanik/Desktop/stackflow claude/stackflow/layer4"
CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(CACHE, "transcript_features.csv")
TARGET = 2200
MAX_SENT = 50
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

QA_MARK = re.compile(r"(question[- ]and[- ]answer|question and answer session|"
                     r"we will now begin the question|first question comes|"
                     r"Q\s*&\s*A session)", re.I)
TRANSCRIPT_MARK = re.compile(r"(moderator|ladies and gentlemen|question[- ]and[- ]answer|"
                             r"analyst|thank you.{0,40}question)", re.I)
CALLDATE = re.compile(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*"
                      r"(January|February|March|April|May|June|July|August|September|"
                      r"October|November|December)[,\s]+(20\d{2})", re.I)


def sess():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": "https://www.nseindia.com/"})
    return s


def extract_text(content):
    """PyMuPDF first (~0.2s), pdfplumber fallback (~3.8s). Returns (text, engine)."""
    t = ""
    try:
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        t = "\n".join(p.get_text() for p in doc)
        if len(t.split()) >= 400:
            return t, "pymupdf"
    except Exception:
        t = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            t2 = "\n".join((p.extract_text() or "") for p in pdf.pages)
        if len(t2.split()) > len(t.split()):
            return t2, "pdfplumber"
    except Exception:
        pass
    return t, "pymupdf"


def split_sections(t):
    m = QA_MARK.search(t)
    if m and 0.05 * len(t) < m.start() < 0.95 * len(t):
        return t[:m.start()], t[m.start():], "split"
    return t, "", "whole"


def sentences(t, cap):
    s = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", t))
    s = [x.strip() for x in s if 25 <= len(x.strip()) <= 400]
    if len(s) > cap:
        idx = np.linspace(0, len(s) - 1, cap).astype(int)
        s = [s[i] for i in idx]
    return s


def lex_counts(text):
    words = re.findall(r"[a-z']+", text.lower())
    n = len(words)
    setw = {}
    for w in words:
        setw[w] = setw.get(w, 0) + 1
    out = {}
    for cat, lst in LM.items():
        c = sum(setw.get(w, 0) for w in lst)
        out["lm_%s" % cat] = c
        out["lm_%s_p1k" % cat] = 1000.0 * c / n if n else np.nan
    low = text.lower()
    for th, phrases in THEMES.items():
        c = sum(low.count(p) for p in phrases)
        out["th_%s" % th] = c
        out["th_%s_p1k" % th] = 1000.0 * c / n if n else np.nan
    out["n_words"] = n
    return out


def phrase_hits(text, section):
    """Every individual trigger phrase occurrence, with a <=25 word context snippet."""
    low = text.lower()
    words = len(re.findall(r"[a-z']+", low)) or 1
    rows = []
    for th, phrases in THEMES.items():
        for p in phrases:
            c = low.count(p)
            if not c:
                continue
            i = low.find(p)
            lo, hi = max(0, i - 90), min(len(text), i + len(p) + 90)
            snip = " ".join(text[lo:hi].split())[:180]
            rows.append(dict(trigger_word=p, theme=th, source_lexicon="custom",
                             section=section, count=c,
                             per_1000_words=1000.0 * c / words, context_snippet=snip))
    return rows


def main():
    cand = pd.read_csv(os.path.join(CACHE, "transcript_candidates.csv"))
    cand["fdate"] = pd.to_datetime(cand.an_dt.str.slice(0, 11), format="%d-%b-%Y",
                                   errors="coerce")
    cand = cand[cand.fdate.notna()].reset_index(drop=True)
    order = list(range(len(cand)))
    random.Random(42).shuffle(order)            # pre-registered seed-42 order

    done = set()
    prev = []
    if os.path.exists(OUT):
        try:
            p0 = pd.read_csv(OUT)
            prev = p0.to_dict("records")
            done = set(p0.url)
            print("resuming: %d already processed" % len(prev), flush=True)
        except Exception:
            prev, done = [], set()

    # FinBERT
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    tok = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    mdl = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    mdl.eval()
    lab = mdl.config.id2label

    def mood(sents):
        if not sents:
            return np.nan, 0
        pos = neg = 0
        with torch.no_grad():
            for i in range(0, len(sents), 32):
                b = tok(sents[i:i + 32], return_tensors="pt", truncation=True,
                        max_length=64, padding=True)
                pr = mdl(**b).logits.argmax(-1).tolist()
                for p in pr:
                    l = lab[p].lower()
                    pos += l == "positive"
                    neg += l == "negative"
        return (pos - neg) / len(sents), len(sents)

    s = sess()
    rows = list(prev)
    hits_rows = []
    hp = os.path.join(CACHE, "phrase_hits.csv")
    stats = dict(scanned=0, download_fail=0, not_transcript=0, ok=0)
    since = 0
    for oi in order:
        if len(rows) >= TARGET:
            break
        r = cand.iloc[oi]
        if r.url in done:
            continue
        try:
            resp = s.get(r.url, timeout=45)
        except Exception:
            stats["download_fail"] += 1
            continue
        if resp.status_code != 200 or len(resp.content) < 3000:
            stats["download_fail"] += 1
            continue
        text, engine = extract_text(resp.content)
        nw = len(text.split())
        if nw < 400:
            stats["scanned"] += 1
            continue
        if not TRANSCRIPT_MARK.search(text):
            stats["not_transcript"] += 1
            continue
        rem, qa, how = split_sections(text)
        cd = None
        m = CALLDATE.search(text[:4000])
        if m:
            try:
                cd = pd.to_datetime("%s %s %s" % (m.group(1), m.group(2), m.group(3))).date()
            except Exception:
                cd = None
        f_rem = lex_counts(rem)
        f_qa = lex_counts(qa) if qa else {}
        m_rem, n_rem = mood(sentences(rem, MAX_SENT // 2))
        m_qa, n_qa = mood(sentences(qa, MAX_SENT // 2)) if qa else (np.nan, 0)
        rec = dict(symbol=r.symbol, company=r.company, industry=r.industry,
                   filing_date=str(r.fdate.date()), call_date=str(cd) if cd else "",
                   url=r.url, engine=engine, split=how, n_words=nw,
                   mood_remarks=m_rem, mood_qna=m_qa, mood_all=(np.nansum([ (m_rem or 0)*n_rem, (m_qa or 0)*n_qa ])/max(n_rem+n_qa,1)),
                   n_sent_rem=n_rem, n_sent_qa=n_qa)
        for k, v in f_rem.items():
            rec["rem_" + k] = v
        for k, v in f_qa.items():
            rec["qa_" + k] = v
        rows.append(rec)
        stats["ok"] += 1
        for h in phrase_hits(rem, "remarks") + (phrase_hits(qa, "QnA") if qa else []):
            h.update(symbol=r.symbol, filing_date=str(r.fdate.date()),
                     call_date=str(cd) if cd else "", url=r.url)
            hits_rows.append(h)
        since += 1
        if since >= 25:
            pd.DataFrame(rows).to_csv(OUT, index=False)
            pd.DataFrame(hits_rows).to_csv(hp, mode="a", index=False,
                                           header=not os.path.exists(hp))
            hits_rows = []
            since = 0
            print("  ...%d processed  %s" % (len(rows), stats), flush=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    if hits_rows:
        pd.DataFrame(hits_rows).to_csv(hp, mode="a", index=False,
                                       header=not os.path.exists(hp))
    print("\nprocessed=%d  %s" % (len(rows), stats))
    print("written:", OUT)


if __name__ == "__main__":
    main()
