# StackFlow PEAD V2 — Timing & Execution Rules

**Specification Date:** 2026-09-22  
**Purpose:** Eliminate all forms of look-ahead, timestamp ambiguity, and announcement-day return leakage.

---

## 1. The Exchange Operating Schedule (NSE)

- **Regular Trading Hours:** 09:15 to 15:30 IST, Monday through Friday (excluding NSE trading holidays).
- **Cutoff Timestamp:** **15:30:00 IST**.

---

## 2. Event Day and Entry Session Resolution

Let an earnings filing occur at timestamp $TS = (\text{Date } D, \text{Time } H:M:S)$.

### Case A: Filing During or Before Trading Hours ($TS \le \text{15:30:00 IST}$) on a Trading Day
- **Event Day ($T$):** Date $D$.
- **Market State:** Market is active or about to open on Date $D$. Prices on Date $D$ absorb the immediate reaction.
- **Entry Session ($T_{\text{entry}}$):** **OPEN of the next trading day ($T+1$)**.
- **Holding Period Start:** Recorded at $T_{\text{entry}}$ Open price ($P_{T+1, \text{Open}}$).
- **Leakage Prevention:** Returns on Date $D$ (close-to-close or open-to-close) are completely excluded from the strategy holding return.

### Case B: Filing After Market Hours ($TS > \text{15:30:00 IST}$) on a Trading Day
- **Event Day ($T$):** **The next trading day ($D+1$)**.
- **Market State:** The first session that can react to the news is Date $D+1$.
- **Entry Session ($T_{\text{entry}}$):** **OPEN of the trading day after the reaction day ($D+2$)**.
- **Holding Period Start:** Recorded at $P_{D+2, \text{Open}}$.
- **Leakage Prevention:** Entry occurs *after* the entire first reaction session ($D+1$) has closed.

### Case C: Filing on Weekends, Market Holidays, or Non-Trading Days
- **Pre-Cutoff Filing ($TS \le \text{15:30:00 IST}$):**
  - **Event Day ($T$):** The first subsequent valid trading session ($D_1$).
  - **Entry Session ($T_{\text{entry}}$):** The OPEN of the second valid trading session ($D_2$).
- **Post-Cutoff / After-Hours Filing ($TS > \text{15:30:00 IST}$):**
  - **As-Coded Behavior:** The code applies the after-hours bump relative to the next trading calendar date ($D_1$), pushing the assigned Event Day to the second session ($D_2$) and the Entry Session to the OPEN of the third session ($D_3$).
  - **Forward Record Standard:** For complete conservatism and zero look-ahead, any weekend/holiday filing broadcast after 15:30 IST assigns $T = D_2$ and enters at $D_3$ Open, ensuring the market has had a full trading session to absorb the filing before entry.

---

## 3. Concrete Timeline Examples

| Example | Filing Timestamp | Event Day ($T$) | Entry Date ($T_{\text{entry}}$) | Entry Price Used | Holding Day 1 Return |
|---|---|---|---|---|---|
| **Ex 1: Mid-day Filing** | Tuesday 2023-10-24 11:42 IST | Tuesday 2023-10-24 | Wednesday 2023-10-25 | Wednesday Open | $\frac{\text{Wed Close}}{\text{Wed Open}} - 1$ |
| **Ex 2: Post-Market Filing** | Tuesday 2023-10-24 18:15 IST | Wednesday 2023-10-25 | Thursday 2023-10-26 | Thursday Open | $\frac{\text{Thu Close}}{\text{Thu Open}} - 1$ |
| **Ex 3: Friday Evening (After-Hours)** | Friday 2023-10-27 19:30 IST | Monday 2023-10-30 | Tuesday 2023-10-31 | Tuesday Open | $\frac{\text{Tue Close}}{\text{Tue Open}} - 1$ |
| **Ex 4: Saturday Evening (After-Hours)** | Saturday 2023-10-28 18:00 IST | Tuesday 2023-10-31 | Wednesday 2023-11-01 | Wednesday Open | $\frac{\text{Wed Close}}{\text{Wed Open}} - 1$ |
| **Ex 5: Diwali / Holiday** | Holiday Evening (>15:30) | Second session after holiday | Third session after holiday | Third session Open | Day 3 Close / Day 3 Open |

---

## 4. Absolute Invariants & Leakage Auditing

1. **Assertion 1 (No Intraday Overlap):**
   $$T_{\text{entry}} > TS$$
   The entry date is strictly greater than the date of filing.
2. **Assertion 2 (No Announcement Price Leakage):**
   The reaction session's closing price is never the entry price. Entry is always the `Open` price of session $T+1$ (or $T+2$ if after-hours).
3. **Assertion 3 (Forward Horizon Alignment):**
   For horizon $h \in \{5, 20, 40, 60, 90, 126\}$, the return is:
   $$R_h = \frac{\text{Close}_{T_{\text{entry}} + h}}{\text{Open}_{T_{\text{entry}}}} - 1$$
   where $T_{\text{entry}} + h$ represents exactly $h$ completed trading sessions in the stock's calendar.
4. **Assertion 4 (Benchmark Date Matching):**
   The benchmark return is computed between the identical session dates:
   $$B_h = \frac{\text{Nifty500}_{T_{\text{entry}} + h}}{\text{Nifty500}_{T_{\text{entry}}}} - 1$$
