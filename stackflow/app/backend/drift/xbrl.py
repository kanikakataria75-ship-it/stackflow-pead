"""Thin adapter over the EXISTING locked XBRL parser (data_pipeline/xbrl/scripts/parse_xbrl.py).

The parser is loaded from its own file (not copied) so every locked decision it encodes — D3
banned ratio tags, D9/D10 context matching that fails loudly, D11 inferred-context flagging —
applies unchanged. Only the download location differs (app cache instead of the research cache).
"""
from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path

import pandas as pd
import requests

from . import settings

_parser = None


def parser():
    global _parser
    if _parser is None:
        spec = importlib.util.spec_from_file_location("stackflow_parse_xbrl", settings.XBRL_PARSER)
        mod = importlib.util.module_from_spec(spec)
        real_makedirs = os.makedirs
        os.makedirs = lambda *a, **k: None        # the module mkdirs a legacy path at import; suppress
        try:
            spec.loader.exec_module(mod)
        finally:
            os.makedirs = real_makedirs
        _parser = mod
    return _parser


def taxonomy_of(url: str) -> str:
    if not url or not url.endswith(".xml"):
        return ""
    m = re.match(r"^([A-Z_]+?)_\d", url.split("/")[-1])
    return m.group(1) if m else "?"


def download(url: str, session: requests.Session | None = None) -> Path | None:
    fn = settings.XML_DIR / url.split("/")[-1]
    if fn.exists() and fn.stat().st_size > 2000:
        return fn
    s = session or requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/"})
    for _ in range(2):
        try:
            r = s.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 2000:
                fn.write_bytes(r.content)
                return fn
            if r.status_code == 404:
                return None
        except Exception:
            pass
    return None


def parse_quarterly(url: str, period_end: pd.Timestamp) -> tuple[dict | None, str | None]:
    """Returns (record, failure_reason). Quarterly: from = quarter start, to = quarter end."""
    fn = download(url)
    if fn is None:
        return None, "download_failed"
    to = pd.Timestamp(period_end)
    frm = to.to_period("Q").start_time
    rec, why = parser().parse_one(str(fn), taxonomy_of(url), frm.strftime("%Y-%m-%d"), to.strftime("%Y-%m-%d"))
    if rec is None or rec.get("pat") is None:
        return rec, why or "no_pat"
    return rec, None
