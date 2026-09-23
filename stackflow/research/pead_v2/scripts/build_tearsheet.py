"""Build PEAD_V2_Tearsheet.xlsx from the corrected outputs (corrected/*.csv, CORRECTED_REPORT.md rev 2).

No figure is estimated here: every number is either copied from a corrected/*.csv file into the
hidden Data sheet, or derived in-workbook by an Excel formula over those copied tables. Per-trade
price paths (sparklines) are read from the same calendar-filtered price files the engine used.
"""
import os
import sys
import zipfile
import shutil
import datetime as dt
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import NamedStyle, Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.chart import LineChart, AreaChart, BarChart, ScatterChart, Reference, Series
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.axis import DateAxis
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
from openpyxl.comments import Comment

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import PEAD_V2_ROOT
from src.data_loader import load_prices

C = os.path.join(PEAD_V2_ROOT, "corrected")
OUT = os.path.join(PEAD_V2_ROOT, "PEAD_V2_Tearsheet.xlsx")
GEN = dt.date.today().isoformat()

# ---------------- palette & styles (one palette, used everywhere) ----------------
NAVY, ACCENT, GREY, GREEN, RED = "1F2A44", "2E86AB", "8C8C8C", "2E7D32", "C62828"
LIGHT, AMBER, BAND_D, BAND_H = "F2F4F7", "F4A261", "DCE3EE", "FBE9D0"
FONT = "Arial"
thin = Side(style="thin", color="C9CED6")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()
STY = {}
def style(name, **kw):
    s = NamedStyle(name=name)
    s.font = Font(name=FONT, **kw.pop("font", {}))
    if "fill" in kw:
        s.fill = PatternFill("solid", fgColor=kw.pop("fill"))
    s.alignment = kw.pop("align", Alignment(vertical="center"))
    if kw.pop("border", False):
        s.border = BOX
    wb.add_named_style(s)
    STY[name] = name
style("sf_title", font=dict(size=20, bold=True, color=NAVY))
style("sf_subtitle", font=dict(size=11, italic=True, color="555555"), align=Alignment(vertical="center", wrap_text=True))
style("sf_h1", font=dict(size=14, bold=True, color=NAVY))
style("sf_h2", font=dict(size=10, bold=True, color="FFFFFF"), fill=NAVY, align=Alignment(horizontal="center", vertical="center", wrap_text=True), border=True)
style("sf_section", font=dict(size=10, bold=True, color=NAVY), fill=LIGHT, border=True)
style("sf_body", font=dict(size=10), border=True)
style("sf_text", font=dict(size=10), align=Alignment(vertical="top", wrap_text=True))
style("sf_num", font=dict(size=10), align=Alignment(horizontal="right", vertical="center"), border=True)
style("sf_note", font=dict(size=9, italic=True, color="555555"), align=Alignment(vertical="top", wrap_text=True))
style("sf_footer", font=dict(size=8, italic=True, color="7F7F7F"))
style("sf_kpi_value", font=dict(size=20, bold=True, color=ACCENT), align=Alignment(horizontal="center", vertical="center"))
style("sf_kpi_label", font=dict(size=9, color="555555"), align=Alignment(horizontal="center", vertical="top", wrap_text=True))
style("sf_badge", font=dict(size=11, bold=True, color="FFFFFF"), fill="B23A48", align=Alignment(horizontal="center", vertical="center", wrap_text=True), border=True)

PCT, PCT1, NUM2, INT = "0.00%", "0.0%", "0.00", "#,##0"

def put(ws, ref, value, st="sf_body", fmt=None):
    c = ws[ref]
    c.value = value
    c.style = st
    if fmt:
        c.number_format = fmt
    return c

def footer(ws, row, sources):
    put(ws, f"A{row}", f"Source: {sources}  ·  Built from CORRECTED_REPORT.md (revision 2) outputs  ·  Workbook generated {GEN}", "sf_footer")

def name(nm, ref):
    wb.defined_names[nm] = DefinedName(nm, attr_text=ref)

def color_scale(ws, rng, lo=-0.10, hi=0.10):
    ws.conditional_formatting.add(rng, ColorScaleRule(start_type="num", start_value=lo, start_color="F4B6B6",
                                                      mid_type="num", mid_value=0, mid_color="FFFFFF",
                                                      end_type="num", end_value=hi, end_color="A9D8B0"))

# ---------------- load corrected outputs ----------------
pm = pd.read_csv(os.path.join(C, "period_metrics_corrected.csv"), index_col=0)
daily = pd.read_csv(os.path.join(C, "nav_daily_corrected.csv"), parse_dates=["date"])
monthly = pd.read_csv(os.path.join(C, "monthly_returns_corrected.csv"), parse_dates=["month_end"])
yearly = pd.read_csv(os.path.join(C, "yearly_returns_corrected.csv"), index_col=0)
roll = pd.read_csv(os.path.join(C, "rolling_12m_corrected.csv"), index_col=0, parse_dates=True)
folds = pd.read_csv(os.path.join(C, "signal_folds_60d.csv"))
qx = pd.read_csv(os.path.join(C, "quarterly_portfolio_excess_corrected.csv"), index_col=0)
plb = pd.read_csv(os.path.join(C, "placebo_random_books.csv"))
plt_ = pd.read_csv(os.path.join(C, "placebo_trade_returns.csv"))
cap = pd.read_csv(os.path.join(C, "capacity_curve_corrected.csv"))
cost = pd.read_csv(os.path.join(C, "cost_sensitivity_corrected.csv"))
sig = pd.read_csv(os.path.join(C, "signal_cells.csv"))
kt = pd.read_csv(os.path.join(C, "kill_tests_corrected.csv"))
led = pd.read_csv(os.path.join(C, "trade_ledger_corrected.csv"),
                  parse_dates=["entry_date", "event_day", "exit_date", "filing_timestamp"])

# ================= Data sheet (hidden, grey) =================
cover = wb.active; cover.title = "Cover"
ex = wb.create_sheet("Executive Summary")
pc = wb.create_sheet("Performance Charts")
tl = wb.create_sheet("Trade Log")
rk = wb.create_sheet("Risk Diagnostics")
me = wb.create_sheet("Methodology")
D = wb.create_sheet("Data")
cover.sheet_properties.tabColor = ACCENT
for w in (ex, pc, tl, rk, me):
    w.sheet_properties.tabColor = NAVY
D.sheet_properties.tabColor = "A6A6A6"

BLK = {}
def block(key, df, col, title, fmts=None, row=3):
    """Write df at (row, col) on Data with a title row above; return {colname: letter}."""
    D.cell(row=row - 2, column=col, value=title).style = "sf_section"
    for j, cn in enumerate(df.columns):
        D.cell(row=row, column=col + j, value=cn).style = "sf_h2"
    vals = df.values
    for i in range(len(df)):
        for j in range(df.shape[1]):
            v = vals[i, j]
            if isinstance(v, (np.floating, float)) and not np.isfinite(v):
                v = None
            elif isinstance(v, np.generic):
                v = v.item()
            elif isinstance(v, pd.Timestamp):
                v = v.to_pydatetime()
            cell = D.cell(row=row + 1 + i, column=col + j, value=v)
            if fmts and df.columns[j] in fmts:
                cell.number_format = fmts[df.columns[j]]
    letters = {cn: L(col + j) for j, cn in enumerate(df.columns)}
    BLK[key] = dict(first=row + 1, last=row + len(df), col=col, letters=letters, n=len(df))
    return letters

# --- period metrics
PERIODS = ["Full Period", "Discovery", "Holdout"]
LABELS = {
    "start": "Window start", "end": "Window end", "years": "Years",
    "total_return": "Total return", "cagr": "CAGR", "bench_total_return": "NIFTY 500 (PR) total return",
    "bench_cagr": "NIFTY 500 (PR) CAGR", "excess_cagr": "Excess CAGR vs NIFTY 500 (PR)",
    "mean_trade_xs_univ_60d": "Mean trade excess vs same-month event universe (60d)",
    "mean_trade_xs_nifty": "Mean trade excess vs NIFTY 500 (per trade)",
    "vol": "Annualised volatility", "bench_vol": "NIFTY 500 volatility",
    "sharpe_rf0": "Sharpe (rf = 0%)", "sharpe_rf6": "Sharpe (rf = 6%)",
    "bench_sharpe_rf0": "NIFTY 500 Sharpe (rf = 0%)", "bench_sharpe_rf6": "NIFTY 500 Sharpe (rf = 6%)",
    "sortino_rf0": "Sortino (rf = 0%)", "calmar": "Calmar (CAGR / |max DD|)", "max_dd": "Maximum drawdown",
    "bench_max_dd": "NIFTY 500 maximum drawdown", "avg_dd_episode": "Average drawdown (mean episode trough)",
    "longest_dd_sessions": "Longest drawdown (trading sessions)", "beta": "Beta to NIFTY 500 (daily)",
    "var95_daily": "VaR 95% (1-day)", "cvar95_daily": "CVaR 95% (1-day)", "skew_daily": "Skewness (daily)",
    "excess_kurt_daily": "Excess kurtosis (daily)",
    "trades": "Total trades", "win_rate": "Win rate", "profit_factor": "Profit factor",
    "avg_trade_net": "Average net trade", "avg_win": "Average win", "avg_loss": "Average loss",
    "payoff": "Payoff ratio (avg win / |avg loss|)", "best_trade": "Best trade", "worst_trade": "Worst trade",
    "avg_holding_sessions": "Average holding period (sessions)",
    "turnover_one_way": "Annual one-way turnover", "median_adv20_cr": "Median 20-day ADV of traded names (INR Cr)",
    "p10_adv20_cr": "10th-pct 20-day ADV (INR Cr)", "capacity_1pct_90fit_cr": "Capacity @1% ADV, 90% of trades fit (INR Cr)",
    "capacity_5pct_90fit_cr": "Capacity @5% ADV, 90% of trades fit (INR Cr)",
    "capacity_1pct_50fit_cr": "Capacity @1% ADV, only 50% of trades fit (INR Cr)",
}
FMT = {k: PCT for k in LABELS}
FMT.update({k: NUM2 for k in ["years", "sharpe_rf0", "sharpe_rf6", "bench_sharpe_rf0", "bench_sharpe_rf6", "sortino_rf0",
                              "calmar", "beta", "skew_daily", "excess_kurt_daily", "profit_factor", "payoff"]})
FMT.update({k: INT for k in ["trades", "longest_dd_sessions", "avg_holding_sessions"]})
FMT.update({k: '"INR "0.0" Cr"' for k in ["median_adv20_cr", "p10_adv20_cr", "capacity_1pct_90fit_cr", "capacity_5pct_90fit_cr", "capacity_1pct_50fit_cr"]})
FMT.update({"turnover_one_way": "0%", "start": "@", "end": "@"})
cols = PERIODS + ["Discovery (calendar split of full book)", "Holdout (calendar split of full book)"]
D["A1"].value = "Period metrics (corrected/period_metrics_corrected.csv)"; D["A1"].style = "sf_section"
for j, h in enumerate(["key", "metric"] + cols):
    D.cell(row=3, column=1 + j, value=h).style = "sf_h2"
MROW = {}
for i, k in enumerate(LABELS):
    r = 4 + i
    MROW[k] = r
    D.cell(row=r, column=1, value=k); D.cell(row=r, column=2, value=LABELS[k])
    for j, p in enumerate(cols):
        v = pm.loc[k, p] if k in pm.index else None
        if isinstance(v, str):
            try:
                v = float(v) if k not in ("start", "end") else v
            except ValueError:
                pass
        if isinstance(v, float) and not np.isfinite(v):
            v = None
        c = D.cell(row=r, column=3 + j, value=v); c.number_format = FMT[k]
    name(f"m_{k}", f"Data!$C${r}:$E${r}")
name("PeriodHeaders", "Data!$C$3:$E$3")
last_metric_row = 4 + len(LABELS) - 1

# --- daily NAV (col I)
dd = daily[["date", "strategy_nav", "nifty500", "strategy_dd", "nifty500_dd", "positions_held", "period"]].copy()
dcols = block("daily", dd, 9, "Daily NAV, rebased to 100 (corrected/nav_daily_corrected.csv)",
              {"date": "yyyy-mm-dd", "strategy_nav": "0.0", "nifty500": "0.0", "strategy_dd": PCT1, "nifty500_dd": PCT1})
bd = BLK["daily"]
band_col_d, band_col_h = bd["col"] + 7, bd["col"] + 8
D.cell(row=3, column=band_col_d, value="band_discovery").style = "sf_h2"
D.cell(row=3, column=band_col_h, value="band_holdout").style = "sf_h2"
navmax = float(max(dd.strategy_nav.max(), dd.nifty500.max()))
D.cell(row=2, column=band_col_d, value="band height =").style = "sf_note"
D.cell(row=2, column=band_col_h, value=float(np.ceil(navmax / 25) * 25))
for r in range(bd["first"], bd["last"] + 1):
    D.cell(row=r, column=band_col_d, value=f'=IF({dcols["period"]}{r}="Discovery",${L(band_col_h)}$2,0)')
    D.cell(row=r, column=band_col_h, value=f'=IF({dcols["period"]}{r}="Holdout",${L(band_col_h)}$2,0)')
ddmin = float(min(dd.strategy_dd.min(), dd.nifty500_dd.min()))

# --- monthly (col T)
mo = monthly[["month_end", "year", "month", "strategy", "nifty500", "excess"]]
mcols = block("monthly", mo, 20, "Monthly returns (corrected/monthly_returns_corrected.csv)",
              {"month_end": "yyyy-mm-dd", "strategy": PCT, "nifty500": PCT, "excess": PCT})
# --- yearly (col AA)
yr = yearly.reset_index().rename(columns={"index": "year"})
yr.columns = ["year"] + list(yearly.columns)
yr = yr[["year", "window", "strategy", "nifty500", "excess", "trades_entered"]]
ycols = block("yearly", yr, 27, "Calendar-year returns (corrected/yearly_returns_corrected.csv)",
              {"strategy": PCT, "nifty500": PCT, "excess": PCT})
# --- rolling 12m (col AH)
ro = roll.reset_index().rename(columns={"index": "date"})
ro.columns = ["date"] + list(roll.columns)
rcols = block("roll", ro, 34, "Rolling 12-month (252-session) returns (corrected/rolling_12m_corrected.csv)",
              {"date": "yyyy-mm-dd", "strategy_12m": PCT1, "nifty500_12m": PCT1, "excess_12m": PCT1})
# --- signal folds (col AM)
fo = folds[["qtr", "period", "n_hi", "n_lo", "spread"]].copy()
fcols = block("folds", fo, 39, "Signal: quarterly Q5-Q1 spread, 60d, xs event universe (corrected/signal_folds_60d.csv)",
              {"spread": PCT})
bf = BLK["folds"]
pcol, ncol = bf["col"] + 5, bf["col"] + 6
D.cell(row=3, column=pcol, value="positive").style = "sf_h2"; D.cell(row=3, column=ncol, value="negative").style = "sf_h2"
for r in range(bf["first"], bf["last"] + 1):
    D.cell(row=r, column=pcol, value=f"=MAX({fcols['spread']}{r},0)").number_format = PCT
    D.cell(row=r, column=ncol, value=f"=MIN({fcols['spread']}{r},0)").number_format = PCT
# --- quarterly portfolio excess (col AU)
q = qx.reset_index().rename(columns={"index": "quarter"})
q.columns = ["quarter"] + list(qx.columns)
qcols = block("qx", q, 47, "Portfolio: quarterly return vs NIFTY 500 (corrected/quarterly_portfolio_excess_corrected.csv)",
              {"strategy": PCT, "nifty500": PCT, "excess": PCT})
bq = BLK["qx"]
qp, qn = bq["col"] + 4, bq["col"] + 5
D.cell(row=3, column=qp, value="positive").style = "sf_h2"; D.cell(row=3, column=qn, value="negative").style = "sf_h2"
for r in range(bq["first"], bq["last"] + 1):
    D.cell(row=r, column=qp, value=f"=MAX({qcols['excess']}{r},0)").number_format = PCT
    D.cell(row=r, column=qn, value=f"=MIN({qcols['excess']}{r},0)").number_format = PCT
# --- placebo books (col BB), placebo trades (col BI)
pbcols = block("plb", plb, 54, "Placebo: 40 random books, same mechanics (corrected/placebo_random_books.csv)",
               {"cagr": PCT, "excess_cagr": PCT, "sharpe_rf0": NUM2, "holdout_excess_cagr": PCT})
ptcols = block("plt", plt_, 61, "Placebo trade-level net returns (corrected/placebo_trade_returns.csv)", {"net_return": PCT})
# --- capacity (col BK), cost (col BO), signal cells (col BW), kill tests (col CN)
ccols = block("cap", cap, 63, "Capacity curve (corrected/capacity_curve_corrected.csv)",
              {"pct_trades_within_1pct_adv": PCT1, "pct_trades_within_5pct_adv": PCT1})
cscols = block("cost", cost, 67, "Cost sensitivity (corrected/cost_sensitivity_corrected.csv)",
               {c: PCT for c in cost.columns if c != "full_sharpe_rf0"} | {"full_sharpe_rf0": NUM2, "round_trip_cost": "0.000%"})
sg = sig[["label", "n_q5", "n_q1", "q5_pct", "q1_pct", "spread_pct", "p_val", "folds_pos", "folds_total", "spread_ex_best_pct", "inversions"]].copy()
for c_ in ["q5_pct", "q1_pct", "spread_pct", "spread_ex_best_pct"]:
    sg[c_] = sg[c_] / 100.0   # stored as fractions for % formatting
sgcols = block("sig", sg, 76, "Signal cells, 60d unless stated (corrected/signal_cells.csv)",
               {"q5_pct": PCT, "q1_pct": PCT, "spread_pct": PCT, "spread_ex_best_pct": PCT, "p_val": "0.0E+00"})
ktcols = block("kt", kt, 88, "Kill tests (corrected/kill_tests_corrected.csv)")

# --- per-trade price paths for sparklines (col CT): Close/entry open, entry day .. exit day (61 sessions)
px = load_prices()
paths = []
for s_, e_, x_, p0 in zip(led.symbol, led.entry_date, led.exit_date, led.entry_price):
    w = px[s_].Close.loc[e_:x_].values / p0
    paths.append(list(w) + [None] * (61 - len(w)))
pp = pd.DataFrame(paths, columns=[f"s{i}" for i in range(61)])
pp.insert(0, "trade_id", led.trade_id.values)
ppcols = block("paths", pp, 94, "Per-trade price path: Close / entry Open, entry day to exit day (calendar-filtered pead/cache/px)")
D.freeze_panes = "A4"
footer(D, last_metric_row + 3, "corrected/*.csv (see block titles)")
D.sheet_state = "hidden"

def dref(key, colname):
    b = BLK[key]
    return f"Data!${b['letters'][colname]}${b['first']}:${b['letters'][colname]}${b['last']}"
def mref(k, period):
    return f"=Data!{L(3 + cols.index(period))}{MROW[k]}"

# ================= chart helpers =================
def style_axis(ch, yfmt=None, xfmt=None, skip=None):
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    if yfmt:
        ch.y_axis.number_format = yfmt
    if xfmt:
        ch.x_axis.number_format = xfmt
    if skip:
        ch.x_axis.tickLblSkip = skip
        ch.x_axis.tickMarkSkip = skip
    ch.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill="E5E7EB"))

def date_axis(ch, low=False):
    ax = DateAxis(crossAx=100)
    ax.number_format = "mmm-yy"
    ax.majorTimeUnit = "months"
    ax.majorUnit = 6
    ax.delete = False
    if low:
        ax.tickLblPos = "low"
    ch.x_axis = ax
    ch.y_axis.crossAx = 500

def finish(ch, title):
    ch.title = title
    ch.title.overlay = False

def line_series(ch, ref, title, color, width=19050, dash=None):
    s = Series(Reference(D, range_string=ref), title=title)
    s.graphicalProperties.line.solidFill = color
    s.graphicalProperties.line.width = width
    if dash:
        s.graphicalProperties.line.dashStyle = dash
    s.smooth = False
    s.marker.symbol = "none"
    ch.series.append(s)
    return s

def equity_chart(title, w, h):
    band = AreaChart()
    for colidx, nm, colr in [(band_col_d, "Discovery period (2021-08 to 2023-12)", BAND_D), (band_col_h, "Holdout period (2024-01 onward)", BAND_H)]:
        s = Series(Reference(D, min_col=colidx, min_row=bd["first"], max_row=bd["last"]), title=nm)
        s.graphicalProperties.solidFill = colr
        s.graphicalProperties.line.noFill = True
        band.series.append(s)
    band.set_categories(Reference(D, range_string=dref("daily", "date")))
    band.y_axis.scaling.min = 0
    band.y_axis.scaling.max = float(D.cell(row=2, column=band_col_h).value)
    band.y_axis.delete = True
    date_axis(band)
    ln = LineChart()
    date_axis(ln)
    line_series(ln, dref("daily", "strategy_nav"), "Strategy (NAV, rebased 100)", ACCENT, 22225)
    line_series(ln, dref("daily", "nifty500"), "NIFTY 500 price index (rebased 100)", GREY, 15875)
    ln.y_axis.axId = 200
    ln.y_axis.delete = False
    ln.y_axis.crosses = "min"
    ln.y_axis.scaling.min = 0
    ln.y_axis.scaling.max = band.y_axis.scaling.max
    ln.y_axis.number_format = "0"
    ln.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill="E5E7EB"))
    ln.y_axis.crossAx = 500
    band += ln
    finish(band, title)
    band.legend.position = "t"
    band.width, band.height = w, h
    return band

def underwater_chart(title, w, h):
    ar = AreaChart()
    s = Series(Reference(D, range_string=dref("daily", "strategy_dd")), title="Strategy drawdown")
    s.graphicalProperties.solidFill = ACCENT
    s.graphicalProperties.line.noFill = True
    ar.series.append(s)
    ar.set_categories(Reference(D, range_string=dref("daily", "date")))
    ln = LineChart()
    date_axis(ln, low=True)
    line_series(ln, dref("daily", "nifty500_dd"), "NIFTY 500 drawdown", GREY, 15875)
    ln.y_axis.axId = 200
    ln.y_axis.delete = True
    for ax in (ar.y_axis, ln.y_axis):
        ax.scaling.min = float(np.floor(ddmin * 20) / 20)
        ax.scaling.max = 0
    style_axis(ar, "0%")
    date_axis(ar, low=True)
    ln.y_axis.crossAx = 500
    ar += ln
    finish(ar, title)
    ar.legend.position = "t"
    ar.width, ar.height = w, h
    return ar

# ================= Cover =================
ws = cover
ws.sheet_view.showGridLines = False
for c_ in range(1, 20):
    ws.column_dimensions[L(c_)].width = 11.5
ws.merge_cells("A1:R1"); put(ws, "A1", "StackFlow PEAD V2 — Post-Earnings-Announcement Drift, NSE", "sf_title")
ws.row_dimensions[1].height = 34
ws.merge_cells("A2:R2")
put(ws, "A2", "Thesis: Indian stocks with the largest point-in-time earnings surprise (ex-ante SUE, top quintile) keep drifting "
              "up for ~60 trading days after the filing; a 30-slot long-only non-financial book tries to harvest it.", "sf_subtitle")
ws.row_dimensions[2].height = 30
ws.merge_cells("A3:E3"); put(ws, "A3", "FORWARD-TEST CANDIDATE — NOT VALIDATED", "sf_badge")
ws.merge_cells("F3:I3"); put(ws, "F3", f"Generated {GEN}", "sf_note")
ws["F3"].alignment = Alignment(vertical="center")
put(ws, "K3", "View period ▸", "sf_h1"); ws["K3"].font = Font(name=FONT, size=10, bold=True, color=NAVY)
ws["K3"].alignment = Alignment(horizontal="right", vertical="center")
ws.merge_cells("L3:M3"); put(ws, "L3", "Full Period", "sf_section")
ws["L3"].alignment = Alignment(horizontal="center", vertical="center")
dv = DataValidation(type="list", formula1='"Full Period,Discovery,Holdout"', allow_blank=False)
dv.prompt, dv.promptTitle = "Choose Full Period / Discovery / Holdout. KPI cards update.", "Period"
ws.add_data_validation(dv); dv.add("L3")
name("SelPeriod", "Cover!$L$3")
ws.merge_cells("N3:R3")
put(ws, "N3", '="Window: "&INDEX(m_start,1,MATCH(SelPeriod,PeriodHeaders,0))&" to "&INDEX(m_end,1,MATCH(SelPeriod,PeriodHeaders,0))', "sf_note")
ws["N3"].alignment = Alignment(vertical="center")
ws.row_dimensions[3].height = 26

cards = [("cagr", "CAGR", PCT), ("excess_cagr", "Excess CAGR vs NIFTY 500 (price index)*", PCT),
         ("sharpe_rf0", "Sharpe (rf = 0%)", NUM2), ("max_dd", "Maximum drawdown", PCT),
         ("win_rate", "Win rate (net of costs)", PCT1), ("trades", "Total trades", INT)]
for i, (k, lab, fmt) in enumerate(cards):
    r0 = 5 if i < 3 else 9
    c0 = 1 + (i % 3) * 2
    a, b = L(c0), L(c0 + 1)
    ws.merge_cells(f"{a}{r0}:{b}{r0 + 1}")
    put(ws, f"{a}{r0}", f"=INDEX(m_{k},1,MATCH(SelPeriod,PeriodHeaders,0))", "sf_kpi_value", fmt)
    ws.merge_cells(f"{a}{r0 + 2}:{b}{r0 + 2}")
    put(ws, f"{a}{r0 + 2}", lab, "sf_kpi_label")
    for rr in range(r0, r0 + 3):
        for cc in (c0, c0 + 1):
            cell = ws.cell(row=rr, column=cc)
            cell.border = Border(left=thin if cc == c0 else None, right=thin if cc == c0 + 1 else None,
                                 top=thin if rr == r0 else None, bottom=thin if rr == r0 + 2 else None)
            cell.fill = PatternFill("solid", fgColor=LIGHT)
for r_ in (5, 6, 9, 10):
    ws.row_dimensions[r_].height = 20
ws.row_dimensions[7].height = 26; ws.row_dimensions[11].height = 26
put(ws, "A12", "KPI cards follow the period selector in L3 (Full Period / Discovery / Holdout). Charts show the full-period book with "
               "the two periods shaded.", "sf_note")
ws.merge_cells("A12:F13")

# discovery vs holdout mini-table
put(ws, "A15", "Discovery vs Holdout — the honesty check", "sf_h1")
hdr = ["Metric", "", "Full Period", "Discovery", "Holdout", "Holdout, calendar split"]
for j, h in enumerate(hdr):
    put(ws, f"{L(1 + j)}16", h, "sf_h2")
ws.merge_cells("A16:B16")
mini = [("cagr", "CAGR", PCT), ("bench_cagr", "NIFTY 500 (PR) CAGR", PCT), ("excess_cagr", "Excess CAGR vs NIFTY 500*", PCT),
        ("sharpe_rf0", "Sharpe (rf = 0%)", NUM2), ("bench_sharpe_rf0", "NIFTY 500 Sharpe (rf = 0%)", NUM2),
        ("sharpe_rf6", "Sharpe (rf = 6%)", NUM2), ("max_dd", "Maximum drawdown", PCT), ("trades", "Trades", INT)]
for i, (k, lab, fmt) in enumerate(mini):
    r = 17 + i
    ws.merge_cells(f"A{r}:B{r}"); put(ws, f"A{r}", lab, "sf_body")
    for j, p in enumerate(PERIODS + ["Holdout (calendar split of full book)"]):
        v = mref(k, p)
        if k == "trades" and p.startswith("Holdout (cal"):
            v = "n/a"
        put(ws, f"{L(3 + j)}{r}", v, "sf_num", fmt)
color_scale(ws, "C19:F19")
ws.merge_cells("A25:F28")
put(ws, "A25", "Holdout = a book holding ONLY trades signalled on/after 2024-01-01, started empty. The calendar split of the continuous "
               "book (last column) looks better only because Q4-2023 discovery trades still open in Jan–Feb 2024 averaged +22% net; it is "
               "shown for transparency, not as holdout evidence. Holdout Sharpe equals the index's. The 2024–26 window was already seen "
               "by V1, the V2 grid and the exit-rule study, so it cannot validate the strategy.", "sf_note")
for r_ in range(25, 29):
    ws.row_dimensions[r_].height = 16

ws.add_chart(equity_chart("Equity curve — strategy vs NIFTY 500 (rebased to 100)", 17.5, 8.2), "H5")
ws.add_chart(underwater_chart("Underwater — drawdown from peak", 17.5, 6.2), "H22")
ws.merge_cells("A31:F36")
put(ws, "A31", "*Benchmark is the NIFTY 500 PRICE index; strategy prices are dividend-adjusted (yfinance auto_adjust). No NIFTY 500 TRI "
               "series is available in the repository, so every excess figure is overstated by roughly the index dividend yield "
               "(~1.0–1.5 pp/yr); holdout excess vs a TRI is ≈ 0% or below.  Costs: 0.585% round trip on every trade (0.2925% per leg, "
               "LeadFlow NSE cost model).  Status: forward-test candidate — NOT a validated live strategy. The only remaining clean test "
               "is the forward record (forward_record_pead_v2.csv).", "sf_note")
footer(ws, 38, "corrected/period_metrics_corrected.csv, corrected/nav_daily_corrected.csv")
ws.print_area = "A1:R38"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 1
ws.sheet_properties.pageSetUpPr.fitToPage = True

# ================= Executive Summary =================
ws = ex
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 52
for c_ in "BCDEF":
    ws.column_dimensions[c_].width = 18
put(ws, "A1", "Executive Summary — full KPI table (as at last completed trade, 2026-08-11)", "sf_title")
ws["A1"].font = Font(name=FONT, size=16, bold=True, color=NAVY)
put(ws, "A2", "Status: FORWARD-TEST CANDIDATE — NOT VALIDATED. Discovery and Holdout are trade-attributed books (each holds only the "
              "trades signalled in its own period). Excess figures are vs the NIFTY 500 PRICE index (see Methodology).", "sf_note")
ws.merge_cells("A2:E2"); ws.row_dimensions[2].height = 30
hdr = ["Metric", "Full Period", "Discovery", "Holdout", "Holdout, calendar split (flattered)"]
for j, h in enumerate(hdr):
    put(ws, f"{L(1 + j)}4", h, "sf_h2")
ws.row_dimensions[4].height = 30
sections = [
    ("Window", ["start", "end", "years"]),
    ("Return", ["total_return", "cagr", "bench_cagr", "excess_cagr", "mean_trade_xs_univ_60d", "mean_trade_xs_nifty"]),
    ("Risk", ["vol", "bench_vol", "sharpe_rf0", "sharpe_rf6", "bench_sharpe_rf0", "bench_sharpe_rf6", "sortino_rf0", "calmar",
              "max_dd", "bench_max_dd", "avg_dd_episode", "longest_dd_sessions", "beta"]),
    ("Trades", ["trades", "win_rate", "profit_factor", "avg_trade_net", "avg_win", "avg_loss", "payoff", "best_trade",
                "worst_trade", "avg_holding_sessions"]),
    ("Capacity & turnover", ["turnover_one_way", "median_adv20_cr", "p10_adv20_cr", "capacity_1pct_90fit_cr",
                             "capacity_5pct_90fit_cr", "capacity_1pct_50fit_cr"]),
]
r = 5
EXC_ROWS = []
for sec, keys in sections:
    ws.merge_cells(f"A{r}:E{r}"); put(ws, f"A{r}", sec, "sf_section"); r += 1
    for k in keys:
        put(ws, f"A{r}", LABELS[k], "sf_body")
        for j, p in enumerate(PERIODS + ["Holdout (calendar split of full book)"]):
            has = not (p.startswith("Holdout (cal") and pd.isna(pm.loc[k, p]) if k in pm.index else True)
            put(ws, f"{L(2 + j)}{r}", mref(k, p) if has else "n/a", "sf_num", FMT[k])
        if k in ("excess_cagr", "mean_trade_xs_univ_60d", "mean_trade_xs_nifty"):
            EXC_ROWS.append(r)
        r += 1
for er in EXC_ROWS:
    color_scale(ws, f"B{er}:E{er}", -0.08, 0.08)
ws.freeze_panes = "B5"
r += 1
notes = [
    "Excess vs equal-weight event universe is reported at trade level (mean 60-day excess of the traded names over the same-month "
    "mean of all qualifying events), because no daily equal-weight universe NAV exists in the corrected outputs.",
    "Capacity = AUM at which 90% of trades stay within 1% (or 5%) of the stock's 20-session median traded value before entry; "
    "the 50%-fit row shows how far the headline would have to stretch to reach the old 'INR 15–30 Cr' claim.",
    "Holdout Sharpe (0.59) equals NIFTY 500's (0.59). At 1.0% round-trip cost the holdout excess is -0.88% (Risk Diagnostics, KT5).",
]
for n_ in notes:
    ws.merge_cells(f"A{r}:E{r}"); put(ws, f"A{r}", "• " + n_, "sf_note"); ws.row_dimensions[r].height = 28; r += 1
footer(ws, r + 1, "corrected/period_metrics_corrected.csv")
ws.print_area = f"A1:E{r + 1}"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
ws.sheet_properties.pageSetUpPr.fitToPage = True

# ================= Performance Charts =================
ws = pc
ws.sheet_view.showGridLines = False
for c_ in range(1, 26):
    ws.column_dimensions[L(c_)].width = 9.5
put(ws, "A1", "Performance Charts", "sf_title")
put(ws, "A2", "Forward-test candidate — not validated. Shaded bands: Discovery (2021-08 → 2023-12) and Holdout (2024-01 →).", "sf_note")
ws.merge_cells("A2:P2")
ws.column_dimensions["A"].width = 16
put(ws, "A4", "1 · Equity curve (full history, rebased to 100) with Discovery / Holdout bands", "sf_h1")
ws.add_chart(equity_chart("Strategy vs NIFTY 500 price index", 32, 9), "A5")
put(ws, "A24", "2 · Underwater curve (same period, same x-axis)", "sf_h1")
ws.add_chart(underwater_chart("Drawdown from running peak", 32, 7), "A25")
put(ws, "A40", "3 · Rolling 12-month excess return vs NIFTY 500", "sf_h1")
rc = LineChart()
line_series(rc, dref("roll", "excess_12m"), "Strategy minus NIFTY 500, trailing 252 sessions", ACCENT, 19050)
rc.set_categories(Reference(D, range_string=dref("roll", "date")))
style_axis(rc, "0%")
date_axis(rc, low=True)
rc.varyColors = False
rc.y_axis.scaling.min = float(np.floor(ro.excess_12m.min() * 10) / 10)
rc.y_axis.scaling.max = float(np.ceil(ro.excess_12m.max() * 10) / 10)
finish(rc, "Rolling 12-month excess return"); rc.legend.position = "t"; rc.width, rc.height = 32, 7
ws.add_chart(rc, "A41")

# 4 · monthly heatmap
put(ws, "A56", "4 · Monthly returns heatmap — strategy (full-period book)", "sf_h1")
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
heads = ["Year"] + months + ["YTD / Annual", "NIFTY 500", "Excess"]
years = sorted(monthly.year.unique())
def heat(r0, value_col, title):
    put(ws, f"A{r0}", title, "sf_section"); ws.merge_cells(f"A{r0}:P{r0}")
    for j, h in enumerate(heads):
        put(ws, f"{L(1 + j)}{r0 + 1}", h, "sf_h2")
    yc, mc, vc = BLK["monthly"]["letters"]["year"], BLK["monthly"]["letters"]["month"], BLK["monthly"]["letters"][value_col]
    f, l_ = BLK["monthly"]["first"], BLK["monthly"]["last"]
    yf, yl = BLK["yearly"]["first"], BLK["yearly"]["last"]
    ycl = BLK["yearly"]["letters"]
    for i, y in enumerate(years):
        r = r0 + 2 + i
        put(ws, f"A{r}", str(y), "sf_body")
        for m in range(1, 13):
            put(ws, f"{L(1 + m)}{r}",
                f'=IF(COUNTIFS(Data!${yc}${f}:${yc}${l_},{y},Data!${mc}${f}:${mc}${l_},{m})=0,"",'
                f'SUMIFS(Data!${vc}${f}:${vc}${l_},Data!${yc}${f}:${yc}${l_},{y},Data!${mc}${f}:${mc}${l_},{m}))',
                "sf_num", PCT1)
        key = "strategy" if value_col == "strategy" else "excess"
        put(ws, f"N{r}", f"=INDEX(Data!${ycl[key]}${yf}:${ycl[key]}${yl},MATCH({y},Data!${ycl['year']}${yf}:${ycl['year']}${yl},0))", "sf_num", PCT1)
        put(ws, f"O{r}", f"=INDEX(Data!${ycl['nifty500']}${yf}:${ycl['nifty500']}${yl},MATCH({y},Data!${ycl['year']}${yf}:${ycl['year']}${yl},0))", "sf_num", PCT1)
        put(ws, f"P{r}", f"=INDEX(Data!${ycl['excess']}${yf}:${ycl['excess']}${yl},MATCH({y},Data!${ycl['year']}${yf}:${ycl['year']}${yl},0))", "sf_num", PCT1)
    r = r0 + 2 + len(years)
    put(ws, f"A{r}", "Month avg", "sf_section")
    for m in range(1, 13):
        cl = L(1 + m)
        put(ws, f"{cl}{r}", f'=IFERROR(AVERAGE({cl}{r0 + 2}:{cl}{r - 1}),"")', "sf_num", PCT1)
    put(ws, f"A{r + 1}", "% positive", "sf_section")
    for m in range(1, 13):
        cl = L(1 + m)
        put(ws, f"{cl}{r + 1}", f'=IFERROR(COUNTIF({cl}{r0 + 2}:{cl}{r - 1},">0")/COUNT({cl}{r0 + 2}:{cl}{r - 1}),"")', "sf_num", "0%")
    color_scale(ws, f"B{r0 + 2}:M{r}", -0.08, 0.08)
    color_scale(ws, f"N{r0 + 2}:N{r - 1}", -0.25, 0.25)
    color_scale(ws, f"P{r0 + 2}:P{r - 1}", -0.15, 0.15)
    return r + 1
end = heat(57, "strategy", "Strategy monthly return (YTD / Annual = calendar-year return; 2021 from 11-Aug, 2026 to 11-Aug)")
end = heat(end + 2, "excess", "Monthly excess vs NIFTY 500 price index (YTD / Annual column = calendar-year excess)")

# 5 · histogram
r0 = end + 3
put(ws, f"A{r0}", "5 · Trade-level net return distribution — strategy vs placebo (random books, same mechanics)", "sf_h1")
edges = list(np.round(np.arange(-0.40, 0.601, 0.05), 2))
put(ws, f"A{r0 + 1}", "Bin (net return)", "sf_h2"); put(ws, f"B{r0 + 1}", "Lower", "sf_h2"); put(ws, f"C{r0 + 1}", "Upper", "sf_h2")
put(ws, f"D{r0 + 1}", "Strategy (% of trades)", "sf_h2"); put(ws, f"E{r0 + 1}", "Placebo (% of trades)", "sf_h2")
nf = "'Trade Log'!$O$5:$O$" + str(4 + len(led))
plr = dref("plt", "net_return")
bins = [(-9.99, edges[0])] + [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)] + [(edges[-1], 9.99)]
for i, (lo, hi) in enumerate(bins):
    r = r0 + 2 + i
    fz = lambda v: f"{(v + 0.0):.0%}".replace("-0%", "0%")
    lab = f"< {fz(edges[0])}" if lo < -9 else (f"≥ {fz(lo)}" if hi > 9 else f"{fz(lo)} to {fz(hi)}")
    put(ws, f"A{r}", lab, "sf_body"); put(ws, f"B{r}", lo, "sf_num", "0%"); put(ws, f"C{r}", hi, "sf_num", "0%")
    put(ws, f"D{r}", f'=COUNTIFS({nf},">="&B{r},{nf},"<"&C{r})/COUNT({nf})', "sf_num", PCT1)
    put(ws, f"E{r}", f'=COUNTIFS({plr},">="&B{r},{plr},"<"&C{r})/COUNT({plr})', "sf_num", PCT1)
hb = BarChart(); hb.type = "col"; hb.grouping = "clustered"
for colL, nm, colr in [("D", "Strategy trades", ACCENT), ("E", "Placebo trades (40 random books)", GREY)]:
    s = Series(Reference(ws, range_string=f"'Performance Charts'!${colL}${r0 + 2}:${colL}${r0 + 1 + len(bins)}"), title=nm)
    s.graphicalProperties.solidFill = colr; s.graphicalProperties.line.noFill = True
    hb.series.append(s)
hb.set_categories(Reference(ws, range_string=f"'Performance Charts'!$A${r0 + 2}:$A${r0 + 1 + len(bins)}"))
style_axis(hb, "0%"); hb.gapWidth = 40
finish(hb, "Net return per trade (60 sessions, after 0.585% cost)"); hb.legend.position = "t"; hb.width, hb.height = 22, 8
ws.add_chart(hb, f"G{r0 + 1}")
r0 = r0 + 3 + len(bins) + 2

# 6 · fold charts
put(ws, f"A{r0}", "6 · Fold-by-fold robustness — quarterly bars, green = positive, red = negative", "sf_h1")
def fold_chart(key, pos_col, neg_col, title, cat):
    b = BarChart(); b.type = "col"; b.grouping = "stacked"; b.overlap = 100
    bb = BLK[key]
    for colidx, nm, colr in [(pos_col, "Positive", GREEN), (neg_col, "Negative", RED)]:
        s = Series(Reference(D, min_col=colidx, min_row=bb["first"], max_row=bb["last"]), title=nm)
        s.graphicalProperties.solidFill = colr; s.graphicalProperties.line.noFill = True
        s.invertIfNegative = False
        b.series.append(s)
    b.set_categories(Reference(D, range_string=dref(key, cat)))
    style_axis(b, "0%"); b.gapWidth = 60
    b.x_axis.tickLblPos = "low"
    finish(b, title); b.legend = None; b.width, b.height = 16, 7.5
    return b
ws.add_chart(fold_chart("folds", pcol, ncol, "Signal: Q5−Q1 spread per quarter (60d, xs event universe) — 17/20 positive", "qtr"), f"A{r0 + 1}")
ws.add_chart(fold_chart("qx", qp, qn, "Trading version: strategy minus NIFTY 500 per calendar quarter", "quarter"), f"L{r0 + 1}")
footer(ws, r0 + 17, "corrected/nav_daily_corrected.csv, rolling_12m, monthly_returns, yearly_returns, trade_ledger, "
                    "placebo_trade_returns, signal_folds_60d, quarterly_portfolio_excess")

# ================= Trade Log =================
ws = tl
ws.sheet_view.showGridLines = False
put(ws, "A1", "Trade Log — every trade of the frozen configuration, A to Z (chronological)", "sf_title")
ws["A1"].font = Font(name=FONT, size=16, bold=True, color=NAVY)
put(ws, "A2", "Forward-test candidate — not validated. Net return = gross − 0.585% round trip. Excess vs benchmark = gross return − NIFTY 500 "
              "price-index return between entry and exit dates. Price path = daily Close ÷ entry Open, entry to exit.", "sf_note")
ws.merge_cells("A2:S2"); ws.row_dimensions[2].height = 28
tcols = [("Entry date", "entry_date", "yyyy-mm-dd", 11), ("Symbol", "symbol", None, 13), ("Company", "company", None, 34),
         ("Sector", "sector", None, 22), ("Filing timestamp (IST)", "filing_timestamp", "yyyy-mm-dd hh:mm", 17),
         ("Event day", "event_day", "yyyy-mm-dd", 11), ("Entry price (Open)", "entry_price", "#,##0.00", 11),
         ("Exit date", "exit_date", "yyyy-mm-dd", 11), ("Exit price (Close)", "exit_price", "#,##0.00", 11),
         ("Holding days (sessions)", "holding_sessions", "0", 9), ("SUE", "sue", "0.00", 8), ("SUE quintile", "sue_quintile", "0", 8),
         ("Gross return", "gross_return", PCT, 10), ("Cost", "cost", "0.000%", 8), ("Net return", "net_return", PCT, 10),
         ("Excess vs NIFTY 500", "excess_vs_nifty500", PCT, 11), ("Period", "period", None, 10), ("Result", "result", None, 8),
         ("Price path", None, None, 16)]
HR = 4
for j, (h, _, _, wdt) in enumerate(tcols):
    put(ws, f"{L(1 + j)}{HR}", h, "sf_h2")
    ws.column_dimensions[L(1 + j)].width = wdt
ws.row_dimensions[HR].height = 44
for i, row in enumerate(led.itertuples(index=False)):
    r = HR + 1 + i
    rd = row._asdict()
    for j, (h, k, fmt, _) in enumerate(tcols):
        if k is None:
            continue
        v = rd[k]
        if isinstance(v, pd.Timestamp):
            v = v.to_pydatetime()
        elif isinstance(v, np.generic):
            v = v.item()
        c = ws.cell(row=r, column=1 + j, value=v)
        c.font = Font(name=FONT, size=9)
        if fmt:
            c.number_format = fmt
LR = HR + len(led)
tab = Table(displayName="TradeLog", ref=f"A{HR}:{L(len(tcols))}{LR}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
ws.add_table(tab)
ws.conditional_formatting.add(f"O{HR + 1}:O{LR}", CellIsRule(operator="greaterThan", formula=["0"], fill=PatternFill("solid", fgColor="D7EFD9"), font=Font(color=GREEN)))
ws.conditional_formatting.add(f"O{HR + 1}:O{LR}", CellIsRule(operator="lessThan", formula=["0"], fill=PatternFill("solid", fgColor="F8D7D7"), font=Font(color=RED)))
ws.conditional_formatting.add(f"P{HR + 1}:P{LR}", CellIsRule(operator="greaterThan", formula=["0"], font=Font(color=GREEN)))
ws.conditional_formatting.add(f"P{HR + 1}:P{LR}", CellIsRule(operator="lessThan", formula=["0"], font=Font(color=RED)))
T = LR + 1
put(ws, f"A{T}", "TOTALS", "sf_section")
put(ws, f"B{T}", f"=COUNTA(B{HR + 1}:B{LR})", "sf_num", '0" trades"')
put(ws, f"M{T}", f"=AVERAGE(M{HR + 1}:M{LR})", "sf_num", PCT)
put(ws, f"N{T}", "avg net →", "sf_note")
put(ws, f"O{T}", f"=AVERAGE(O{HR + 1}:O{LR})", "sf_num", PCT)
put(ws, f"P{T}", f"=AVERAGE(P{HR + 1}:P{LR})", "sf_num", PCT)
put(ws, f"Q{T}", "win rate →", "sf_note")
put(ws, f"R{T}", f'=COUNTIF(R{HR + 1}:R{LR},"Win")/COUNTA(R{HR + 1}:R{LR})', "sf_num", PCT1)
ws.freeze_panes = f"C{HR + 1}"
footer(ws, T + 2, "corrected/trade_ledger_corrected.csv; price paths from pead/cache/px (NSE-calendar filtered)")
SPARK = dict(first=HR + 1, last=LR, col=L(len(tcols)))

# ================= Risk Diagnostics =================
ws = rk
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 40
for c_ in "BCDEFGHIJK":
    ws.column_dimensions[c_].width = 14
put(ws, "A1", "Risk & Robustness Diagnostics", "sf_title")
put(ws, "A2", "Forward-test candidate — not validated. Signal tests use the cross-sectional event sample; KT5 is the only portfolio-level kill test.", "sf_note")
ws.merge_cells("A2:H2")
r = 4
put(ws, f"A{r}", "Tail risk (daily NAV returns)", "sf_h1"); r += 1
for j, h in enumerate(["Metric"] + PERIODS):
    put(ws, f"{L(1 + j)}{r}", h, "sf_h2")
r += 1
for k in ["var95_daily", "cvar95_daily", "skew_daily", "excess_kurt_daily", "vol", "max_dd"]:
    put(ws, f"A{r}", LABELS[k], "sf_body")
    for j, p in enumerate(PERIODS):
        put(ws, f"{L(2 + j)}{r}", mref(k, p), "sf_num", FMT[k])
    r += 1
r += 1
put(ws, f"A{r}", "Signal breakdown — Q5 minus Q1, 60 trading days, excess vs event universe", "sf_h1"); r += 1
sh = ["Cut", "Q5 n", "Q1 n", "Q5", "Q1", "Spread", "p-value", "Folds +", "Folds", "Ex-best fold"]
for j, h in enumerate(sh):
    put(ws, f"{L(1 + j)}{r}", h, "sf_h2")
r += 1
sgb = BLK["sig"]
lab_rows = {lab: sgb["first"] + i for i, lab in enumerate(sg.label)}
sel = [("Primary 60d (all)", "All events"), ("Discovery 60d", "Discovery (≤ 2023)"), ("Holdout 60d", "Holdout (≥ 2024)"),
       ("Size Small 60d", "Size: Small (turnover tercile)"), ("Size Mid 60d", "Size: Mid"), ("Size Large 60d", "Size: Large"),
       ("Non-Financials 60d", "Non-Financials (traded universe)"), ("Financials 60d", "Financials (EXCLUDED)")]
spread_rows = []
for lab, disp in sel:
    rr = lab_rows[lab]
    put(ws, f"A{r}", disp, "sf_body")
    for j, (cn, fmt) in enumerate([("n_q5", INT), ("n_q1", INT), ("q5_pct", PCT), ("q1_pct", PCT), ("spread_pct", PCT),
                                   ("p_val", "0.0E+00"), ("folds_pos", INT), ("folds_total", INT), ("spread_ex_best_pct", PCT)]):
        put(ws, f"{L(2 + j)}{r}", f"=Data!{sgb['letters'][cn]}{rr}", "sf_num", fmt)
    spread_rows.append(r)
    r += 1
color_scale(ws, f"F{spread_rows[0]}:F{spread_rows[-1]}", -0.05, 0.05)
ws.merge_cells(f"A{r}:J{r + 1}")
put(ws, f"A{r}", "Financials excluded: banks, NBFCs, housing finance, insurers, AMCs, exchanges/market infrastructure and rating agencies, "
                 "identified by the XBRL pipeline 'fin' flag (taxonomy BANKING/NBFC or industry = FINANCIAL SERVICES). Provision-driven "
                 "profits make a seasonal-random-walk SUE a poor surprise proxy; the financials spread is negative and not significant.", "sf_note")
ws.row_dimensions[r].height = 18; ws.row_dimensions[r + 1].height = 18
r += 3
put(ws, f"A{r}", "Kill tests (corrected)", "sf_h1"); r += 1
for j, h in enumerate(["Test", "Perturbation", "", "", "Result", "", "", "", "", "Pass?"]):
    put(ws, f"{L(1 + j)}{r}", h, "sf_h2")
ws.merge_cells(f"B{r}:D{r}"); ws.merge_cells(f"E{r}:I{r}")
r += 1
ktb = BLK["kt"]
kt_first = r
for i in range(len(kt)):
    rr = ktb["first"] + i
    put(ws, f"A{r}", f"=Data!{ktb['letters']['test']}{rr}", "sf_body")
    ws.merge_cells(f"B{r}:D{r}"); put(ws, f"B{r}", f"=Data!{ktb['letters']['perturbation']}{rr}", "sf_body")
    ws.merge_cells(f"E{r}:I{r}"); put(ws, f"E{r}", f"=Data!{ktb['letters']['result']}{rr}", "sf_body")
    put(ws, f"J{r}", f'=IF(Data!{ktb["letters"]["passed"]}{rr},"PASS","FAIL")', "sf_num")
    r += 1
ws.conditional_formatting.add(f"J{kt_first}:J{r - 1}", CellIsRule(operator="equal", formula=['"PASS"'], fill=PatternFill("solid", fgColor="D7EFD9"), font=Font(color=GREEN, bold=True)))
ws.conditional_formatting.add(f"J{kt_first}:J{r - 1}", CellIsRule(operator="equal", formula=['"FAIL"'], fill=PatternFill("solid", fgColor="F8D7D7"), font=Font(color=RED, bold=True)))
ws.merge_cells(f"A{r}:J{r + 1}")
put(ws, f"A{r}", "Reading: every signal-level test passes; the portfolio-level cost test (KT5) fails because at 1.0% round-trip cost the "
                 "holdout book trails NIFTY 500. KT1 compares the mean of quarterly fold spreads with and without the two best quarters "
                 "(2021Q3, 2022Q1).", "sf_note")
r += 3
put(ws, f"A{r}", "Cost sensitivity", "sf_h1"); r += 1
chead = ["Round-trip cost", "Full CAGR", "Full excess*", "Full Sharpe (rf 0)", "Full max DD", "Holdout CAGR", "Holdout excess*"]
for j, h in enumerate(chead):
    put(ws, f"{L(1 + j)}{r}", h, "sf_h2")
r += 1
cb = BLK["cost"]
c_first = r
for i in range(len(cost)):
    rr = cb["first"] + i
    for j, (cn, fmt) in enumerate([("round_trip_cost", "0.000%"), ("full_cagr", PCT), ("full_excess", PCT), ("full_sharpe_rf0", NUM2),
                                   ("full_max_dd", PCT), ("holdout_cagr", PCT), ("holdout_excess", PCT)]):
        put(ws, f"{L(1 + j)}{r}", f"=Data!{cb['letters'][cn]}{rr}", "sf_num", fmt)
    r += 1
color_scale(ws, f"C{c_first}:C{r - 1}", -0.08, 0.08); color_scale(ws, f"G{c_first}:G{r - 1}", -0.08, 0.08)
r += 1
put(ws, f"A{r}", "Capacity — share of trades that fit within 1% / 5% of 20-day median traded value", "sf_h1"); r += 1
sc = ScatterChart()
capb = BLK["cap"]
xr = Reference(D, range_string=dref("cap", "aum_cr"))
for cn, nm, dash in [("pct_trades_within_1pct_adv", "Within 1% of ADV", None), ("pct_trades_within_5pct_adv", "Within 5% of ADV", "dash")]:
    s = Series(Reference(D, range_string=dref("cap", cn)), xr, title=nm)
    s.graphicalProperties.line.solidFill = ACCENT; s.graphicalProperties.line.width = 22225
    if dash:
        s.graphicalProperties.line.dashStyle = dash
    s.marker.symbol = "circle"; s.marker.size = 5
    s.marker.graphicalProperties = GraphicalProperties(solidFill=ACCENT)
    s.smooth = False
    sc.series.append(s)
sc.x_axis.title = "Strategy AUM (INR Crore, log scale)"; sc.y_axis.title = "% of trades that fit"
sc.x_axis.scaling.logBase = 10; sc.x_axis.scaling.min = 0.5; sc.x_axis.scaling.max = 150
sc.y_axis.scaling.min = 0; sc.y_axis.scaling.max = 1
style_axis(sc, "0%"); sc.x_axis.number_format = "0.0"
finish(sc, "Capacity: 90% of trades fit at ~INR 1.6 Cr (1%) / ~INR 8 Cr (5%)"); sc.legend.position = "t"; sc.width, sc.height = 18, 8
ws.add_chart(sc, f"A{r}")
footer(ws, r + 17, "corrected/period_metrics_corrected.csv, signal_cells.csv, kill_tests_corrected.csv, cost_sensitivity_corrected.csv, capacity_curve_corrected.csv")

# ================= Methodology =================
ws = me
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 120
put(ws, "A1", "Methodology & Disclaimers", "sf_title")
TXT = [
    ("h", "Status"),
    ("t", "DISCOVERY — NOT VALIDATED. StackFlow PEAD V2 is a FORWARD-TEST CANDIDATE. The cross-sectional signal is confirmed; the "
          "long-only trading strategy is not validated. Nothing in this workbook is investment advice or a live-trading recommendation."),
    ("h", "Signal — Standardised Unexpected Earnings (SUE)"),
    ("t", "SUE_q = (PAT_q − PAT of the same fiscal quarter one year earlier) ÷ standard deviation of the YoY PAT changes of the 8 prior "
          "quarters (at least 6 required). Seasonal random walk: NO analyst estimates are used. YoY is matched by fiscal quarter-end date "
          "(audit fix 5), so gaps in the XBRL series never compare the wrong quarters."),
    ("t", "Ex-ante buckets (model M1): for an event on day T, quintile cut-offs are the 20/40/60/80th percentiles of SUE across all "
          "qualifying events with event day in [T−365, T), minimum 150 prior events (pre-registration said 200; disclosed deviation; "
          "with 200 the spread is unchanged). Events 2021-08-10 → 2022-02-09 use truncated windows because data begins 2021-02-10. "
          "The strategy buys Q5 only."),
    ("h", "Universe and filters"),
    ("t", "NSE equities with quarterly XBRL PAT (earliest parseable filing per company-quarter, Consolidated first, Standalone fallback). "
          "20-session average traded value before the event day ≥ INR 1 crore; entry Open > INR 50. Prices restricted to NSE sessions "
          "(phantom zero-volume holiday rows removed, audit fix 6). Financial sector excluded by the XBRL pipeline 'fin' flag: taxonomy "
          "BANKING/NBFC or industry FINANCIAL SERVICES — banks, NBFCs, housing finance, insurers, AMCs, exchanges, rating agencies "
          "(audit fix 4). Universe = 421 symbols with a price history today: survivorship bias is not removed."),
    ("h", "Entry / exit timing (reconciled rule, TIMING_RULES.md)"),
    ("t", "Case A — filing ≤ 15:30 IST on a session day D: event day = D; entry = OPEN of the next session."),
    ("t", "Case B — filing > 15:30 IST on a session day D: event day = next session; entry = OPEN of the session after that."),
    ("t", "Case C — filing on a weekend/holiday: ≤ 15:30 IST → event day = first session D1, entry = OPEN of D2; > 15:30 IST → event day "
          "= D2, entry = OPEN of D3 (as coded; conservative)."),
    ("t", "Exit = CLOSE of the 60th session after entry. 30 slots; a slot freed at an exit CLOSE is reusable only from the next session's "
          "OPEN. Queue: FIFO across dates, same-day ties to the highest SUE. Sizing: min(cash, NAV of prior close ÷ 30) at entry; shares "
          "held and marked at every close; cash earns 0%; no leverage."),
    ("h", "Costs"),
    ("t", "0.585% round trip on every trade — the LeadFlow NSE cost model — charged 0.2925% on the entry and 0.2925% on the exit. "
          "Sensitivity at 0.300% and 1.000% is on Risk Diagnostics."),
    ("h", "Benchmark and its caveat"),
    ("t", "NIFTY 500 PRICE index (cache/sector_close_panel.csv). Strategy prices are dividend-adjusted (yfinance auto_adjust=True), the "
          "index is not, and no NIFTY 500 Total Return Index series exists in the repository. Every excess figure is therefore overstated "
          "by roughly the index dividend yield, ~1.0–1.5 pp/yr. Sharpe is shown at rf = 0% and rf = 6% (≈ 91-day T-bill, 2021–26)."),
    ("h", "Periods"),
    ("t", "Discovery = trades signalled on/before 2023-12-31; Holdout = trades signalled on/after 2024-01-01, in a book started empty. "
          "The calendar split of the continuous book is shown only for transparency: its holdout slice contains discovery trades still "
          "open in Jan–Feb 2024 and flatters the holdout by ~4 pp/yr."),
    ("h", "What This Is Not"),
    ("t", "• Not a validated live strategy. On trades signalled in 2024–26 the book returned +8.71% CAGR vs +7.89% for the NIFTY 500 "
          "price index (+0.82% excess; ≈ 0% or below vs a total-return index), with the same Sharpe as the index; at 1% cost the "
          "holdout excess is negative."),
    ("t", "• The discovery AND holdout windows have both been seen multiple times (V1 results, the V2 full-period grid, the V2 exit-rule "
          "study, this audit). Neither can serve as further out-of-sample evidence. The configuration (30 slots, non-financials, Q5, 60d) "
          "was chosen with 2024–26 in view."),
    ("t", "• The forward record (forward_record_pead_v2.csv, no backfill of events filed on/before 2026-09-22) is the only remaining clean test."),
    ("t", "• The short-side edge is real in the data (Q1 lags the event universe by −1.60% over 60 days, larger than Q5's +1.41% lead) "
          "but is NOT captured by this long-only book."),
    ("t", "• Capacity is small: ~INR 1.6 Cr at 1% of ADV (90% of trades fit); ~INR 8 Cr at 5%."),
    ("h", "Pre-registered forward-test evaluation plan (verbatim from CORRECTED_REPORT.md §5 / live_config_pead_v2_corrected.md §3)"),
    ("t", "Evaluation standard: realised daily mark-to-market NAV, discrete share-and-cash accounting, evaluated against NIFTY 500 and the "
          "equal-weight event-universe mean."),
    ("t", "Minimum forward horizon: at least 4 to 6 earnings seasons (12–18 calendar months of live forward records)."),
    ("t", "Kill criteria — the strategy is permanently killed if: (1) Cumulative strategy return trails NIFTY 500 over 4 consecutive "
          "earnings seasons (excess ≤ 0%); (2) Average Q5 net trade return trails the cross-sectional event-universe average (excess vs "
          "event universe ≤ 0%); (3) Realised portfolio drawdown exceeds −25.0%."),
    ("t", "No backfill: only events filed after 2026-09-22 may enter forward_record_pead_v2.csv."),
    ("h", "Data not available (left out rather than estimated)"),
    ("t", "Intraday prices/fills, NIFTY 500 Total Return Index, a daily equal-weight event-universe NAV, and point-in-time (delisted) "
          "constituents are not in the corrected outputs. Metrics that would need them are omitted and require a data source first."),
]
r = 3
for kind, txt in TXT:
    if kind == "h":
        r += 1
        put(ws, f"A{r}", txt, "sf_h1")
        ws.row_dimensions[r].height = 22
    else:
        put(ws, f"A{r}", txt, "sf_text")
        ws.row_dimensions[r].height = 14 * (len(txt) // 105 + 1) + 4
    r += 1
footer(ws, r + 1, "CORRECTED_REPORT.md (rev 2), live_config_pead_v2_corrected.md, TIMING_RULES.md, AUDIT_REPORT.md")

for w_ in (cover, pc, rk):
    for ch_ in w_._charts:
        if ch_.legend is not None:
            ch_.legend.overlay = False
for w_ in (pc, tl, rk, me):
    w_.page_setup.orientation = "landscape"
    w_.page_setup.fitToWidth, w_.page_setup.fitToHeight = 1, 0
    w_.sheet_properties.pageSetUpPr.fitToPage = True
tl.print_title_rows = f"{HR}:{HR}"
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)

# ---------------- sparklines (x14 extension; openpyxl has no native API) ----------------
def add_sparklines(path):
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin:
        wbxml = zin.read("xl/workbook.xml").decode()
        rels = zin.read("xl/_rels/workbook.xml.rels").decode()
        import re
        rid = re.search(r'<sheet[^>]*name="Trade Log"[^>]*r:id="(rId\d+)"', wbxml).group(1)
        target = re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"|Target="([^"]+)"[^>]*Id="{rid}"', rels)
        target = target.group(1) or target.group(2)
        sheet_path = "xl/" + target.lstrip("/").replace("xl/", "")
        pb = BLK["paths"]
        first_col, last_col = L(pb["col"] + 1), L(pb["col"] + 61)
        sp = "".join(f"<x14:sparkline><xm:f>Data!{first_col}{pb['first'] + i}:{last_col}{pb['first'] + i}</xm:f>"
                     f"<xm:sqref>{SPARK['col']}{SPARK['first'] + i}</xm:sqref></x14:sparkline>" for i in range(pb["n"]))
        ext = ('<extLst><ext uri="{05C60535-1F16-4fd2-B633-F4F36F0B64E0}" '
               'xmlns:x14="http://schemas.microsoft.com/office/spreadsheetml/2009/9/main">'
               '<x14:sparklineGroups xmlns:xm="http://schemas.microsoft.com/office/excel/2006/main">'
               '<x14:sparklineGroup displayEmptyCellsAs="gap" displayHidden="1" first="1" last="1">'
               f'<x14:colorSeries rgb="FF{ACCENT}"/><x14:colorNegative rgb="FF{RED}"/><x14:colorAxis rgb="FF000000"/>'
               f'<x14:colorMarkers rgb="FF{ACCENT}"/><x14:colorFirst rgb="FF{GREY}"/><x14:colorLast rgb="FF{NAVY}"/>'
               f'<x14:colorHigh rgb="FF{GREEN}"/><x14:colorLow rgb="FF{RED}"/>'
               f'<x14:sparklines>{sp}</x14:sparklines></x14:sparklineGroup></x14:sparklineGroups></ext></extLst>')
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == sheet_path:
                    x = data.decode()
                    assert "<extLst>" not in x
                    x = x.replace("</worksheet>", ext + "</worksheet>")
                    data = x.encode()
                zout.writestr(item, data)
    shutil.move(tmp, path)
add_sparklines(OUT)
print("saved", OUT)
