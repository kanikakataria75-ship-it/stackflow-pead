import { useEffect, useRef, useState } from "react";

export interface Signal {
  signal_id: string; symbol: string; company?: string; industry?: string; is_fin?: boolean | string;
  filing_timestamp: string; event_day: string; planned_entry: string; planned_exit: string;
  sue: number | string | null; quintile: number | string | null;
  q20?: number | null; q40?: number | null; q60?: number | null; q80?: number | null; hist_events?: number | null;
  decision: string; reason: string; scanned_at: string; ts_source?: string; turnover20_inr?: number | string | null;
  demo?: boolean;
}
export interface UniversePoint {
  symbol: string; sector: string; is_fin: boolean;
  forward: Signal | null;
  research_last: { filing_ts: string; sue: number | null; quintile: number | null; source: string } | null;
  position: { entry_date: string; exit_date: string; status?: string; sessions_held?: number } | null;
}
export interface Status {
  badge: string; demo: boolean; now_ist: string; next_scan_ist: string;
  last_scan: { scan_id?: string; started?: string; ok?: boolean; duration_s?: number; errors?: string[] };
  filings_processed_today: number; q5_today: number; slots_used: number; slots: number; forward_signals_total: number;
}
export interface Position {
  signal_id: string; symbol: string; industry: string; sue: number; entry_date: string; exit_date: string;
  entry_price?: number; current_price?: number; exit_price?: number; sessions_held?: number; holding_sessions: number;
  unrealised_return?: number; net_return?: number; excess_vs_nifty500?: number; price_date?: string;
}
export interface Positions { open: Position[]; planned?: Position[]; closed: Position[]; slots_used: number; slots: number; demo: boolean }
export interface PerfPoint { date: string; nav: number; bench: number; positions: number; drawdown: number }
export interface Performance {
  demo: boolean; series: PerfPoint[]; starts?: string; trades_filled?: number; note?: string;
  seasons: { seasons: { quarter_end: string; deadline: string; complete: boolean }[]; completed: number; required_min: number; required_max: number };
  kill_criteria: string[];
  research_reference: { label: string; source: string; periods: Record<string, Record<string, number | null>> };
}
export interface Health {
  badge: string;
  frozen_config: { ok: boolean; path: string; sha256?: string; missing_phrases?: string[]; constants?: Record<string, unknown> };
  calendar: { validated: boolean; source?: string; fetched_at?: string; n_holidays?: number; historical_end?: string; validation_year?: number; rule_minus_index?: string[]; index_minus_rule?: string[] };
  append_only_guard: Record<string, { ok: boolean; file_bytes: number; chained_bytes: number; rows: number; trailing_unchained_bytes: number; last_append: string; path: string }>;
  total_count_asserts: { checked: number; passed: number; audits: { source: string; window: string; pages: number; rows: number; total_count: number | null; asserted: boolean; at: string }[] };
  last_scan: { scan_id?: string; started?: string; ok?: boolean; duration_s?: number; errors?: string[]; filings_seen?: number; universe_filings?: number; new_events?: number; q5?: number; decisions?: Record<string, number>; fills?: Record<string, number> };
  last_success?: string;
  data_freshness: { prices_last_session: Record<string, string>; benchmark_panel_end?: string; holidays_fetched_at?: string };
  safety: string;
}
export interface Config { read_only: boolean; frozen_config_markdown: string; pre_registration_markdown: string; verification: Health["frozen_config"]; constants: Record<string, unknown> }

const BASE = "/api";

export async function getJSON<T>(path: string, demo: boolean): Promise<T> {
  const sep = path.includes("?") ? "&" : "?";
  const r = await fetch(`${BASE}${path}${demo ? `${sep}demo=true` : ""}`);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export async function runScan() {
  const r = await fetch(`${BASE}/scan/run`, { method: "POST" });
  return r.json();
}

/** Poll an endpoint. Returns data, error and the time of the last successful refresh. */
export function useApi<T>(path: string, demo: boolean, everyMs = 60_000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [at, setAt] = useState<Date | null>(null);
  const [nonce, setNonce] = useState(0);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    let t: number | undefined;
    const tick = () => {
      getJSON<T>(path, demo)
        .then((d) => { if (alive.current) { setData(d); setError(null); setAt(new Date()); } })
        .catch((e) => { if (alive.current) setError(String(e.message || e)); })
        .finally(() => { if (alive.current && everyMs > 0) t = window.setTimeout(tick, everyMs); });
    };
    tick();
    return () => { alive.current = false; if (t) clearTimeout(t); };
  }, [path, demo, everyMs, nonce]);
  return { data, error, at, reload: () => setNonce((n) => n + 1) };
}
