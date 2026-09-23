export const COLORS = {
  ink: "#15130f", bone: "#ece5d8", bone2: "#b9b1a3", bone3: "#847d71",
  amber: "#e8963c", steel: "#86a0b8", loss: "#c0594a", rule: "rgba(236,229,216,0.13)",
};

/** Quintile colour: Q5 accent, Q1 dim red, the middle three muted greys. */
export function qColor(q: number | null | undefined): string {
  if (q === 5) return COLORS.amber;
  if (q === 1) return "#8a4a3f";
  if (q === 4) return "#a39b8e";
  if (q === 3) return "#7a7368";
  if (q === 2) return "#5f5a51";
  return "#4a463f";
}

export const num = (v: unknown): number | null => {
  const n = typeof v === "string" ? (v === "" ? NaN : Number(v)) : (v as number);
  return typeof n === "number" && Number.isFinite(n) ? n : null;
};

export const pct = (v: number | null | undefined, d = 2, signed = true) =>
  v == null || !Number.isFinite(v) ? "—" : `${signed && v > 0 ? "+" : ""}${(v * 100).toFixed(d)}%`;

export const fix = (v: number | null | undefined, d = 2) => (v == null || !Number.isFinite(v) ? "—" : v.toFixed(d));

export const inr = (v: number | null | undefined) =>
  v == null ? "—" : `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })}`;

export const crore = (v: number | null | undefined) => (v == null ? "—" : `₹${(v / 1e7).toFixed(1)} Cr`);

export function shortDate(iso: string | null | undefined) {
  if (!iso) return "—";
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso.replace(" ", "T"));
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

export function istTime(iso: string | null | undefined) {
  if (!iso) return "—";
  return iso.replace("T", " ").slice(0, 16) + " IST";
}

export const REASONS: Record<string, string> = {
  "": "Allocated a slot",
  FULL_QUEUE: "All 30 slots occupied at the entry open",
  LOWER_SUE_RANK: "Lost same-day tie-break to a higher SUE",
  FINANCIAL_SECTOR: "Financial sector — excluded by frozen rule",
  LIQUIDITY_FILTER: "20-session traded value below ₹1 Cr",
  PRICE_FILTER: "Entry open not above ₹50",
  BASIS_SWITCH: "First quarter after a Consolidated/Standalone switch (D13)",
  INSUFFICIENT_HISTORY: "Fewer than 6 prior year-on-year changes",
  THRESHOLDS_UNAVAILABLE: "Fewer than 150 qualifying filings in the trailing 365 days",
  AWAITING_SAME_DAY_PEERS: "Same-day candidates can still arrive; allocation pending",
  ENTRY_MISSED: "Discovered after its entry open — not taken",
};
