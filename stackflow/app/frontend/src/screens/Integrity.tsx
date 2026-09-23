import { Fragment, useState } from "react";
import { runScan, useApi, type Config, type Health } from "../api";
import { istTime } from "../lib/format";
import { useStore } from "../store";

function Check({ ok, title, detail, value }: { ok: boolean | null; title: string; detail?: React.ReactNode; value?: React.ReactNode }) {
  return (
    <div className="check">
      <span className={`g ${ok === null ? "" : ok ? "ok" : "bad"}`} aria-label={ok === null ? "unknown" : ok ? "passed" : "failed"}>
        {ok === null ? "·" : ok ? "✓" : "✕"}
      </span>
      <div><div>{title}</div>{detail && <div className="d">{detail}</div>}</div>
      <div className="num muted" style={{ fontSize: 12, textAlign: "right" }}>{value}</div>
    </div>
  );
}

const CONST_LABELS: Record<string, string> = {
  version: "Configuration version", freeze_date: "Freeze date (no backfill on/before)", slots: "Concurrent slots",
  holding_sessions: "Holding period (sessions)", round_trip_cost: "Round-trip cost", cutoff_ist: "Filing cut-off (IST)",
  lookback_days: "Ex-ante lookback (days)", min_history_events: "Minimum history events", min_prior_yoy: "Minimum prior YoY changes",
  signal_quintile: "Signal quintile", min_turnover_inr: "20-session turnover floor (INR)", min_price_inr: "Entry open floor (INR)",
  benchmark: "Benchmark", queue_policy: "Queue policy",
};

function fmtConst(k: string, v: unknown): string {
  if (k === "round_trip_cost") return `${(Number(v) * 100).toFixed(3)}% (${(Number(v) * 50).toFixed(4)}% per leg)`;
  if (k === "min_turnover_inr") return `₹${(Number(v) / 1e7).toFixed(0)} crore`;
  if (k === "min_price_inr") return `above ₹${v}`;
  if (k === "cutoff_ist") return `${String(v).slice(0, 5)} IST`;
  return String(v);
}

export default function Integrity() {
  const { demo } = useStore();
  const h = useApi<Health>("/health", false, 60_000);
  const c = useApi<Config>("/config", false, 0);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const d = h.data;
  const last = d?.last_scan;
  const fr = d?.append_only_guard?.forward_record, sl = d?.append_only_guard?.scan_log;
  const tc = d?.total_count_asserts;
  const prices = Object.entries(d?.data_freshness.prices_last_session ?? {});
  return (
    <div className="screen">
      <div className="kicker">
        <h2>Config &amp; Integrity</h2>
        <div className="deck">What the scanner is allowed to do, and proof that it did only that. The frozen configuration is read-only here and in the code; every check below is computed live by the backend.{demo && " Integrity checks always show the real system, never the backtest replay."}</div>
        <button className="btn" disabled={busy} onClick={async () => {
          setBusy(true); setMsg(null);
          try { const r = await runScan(); setMsg(r.ok ? `Scan ${r.scan_id}: ${r.new_events} new events in ${r.duration_s}s.` : `Scan failed: ${(r.errors || []).join("; ")}`); }
          catch (e) { setMsg(String(e)); }
          setBusy(false); h.reload();
        }}>{busy ? "Scanning…" : "Run scan now"}</button>
      </div>
      {msg && <div className="num muted" style={{ marginBottom: 12 }}>{msg}</div>}
      {h.error && <div className="empty">The scanner API is not reachable.<small>{h.error}</small></div>}

      <div className="cols" style={{ gridTemplateColumns: "1.15fr 1fr" }}>
        <section>
          <div className="section-h"><h3>Live integrity</h3><span className="label">{d?.badge}</span></div>
          <Check ok={d ? d.frozen_config.ok : null} title="Frozen config matches the scanner's constants"
            detail={d?.frozen_config.ok ? "Every frozen phrase verified in live_config_pead_v2_corrected.md" : `Missing: ${(d?.frozen_config.missing_phrases ?? []).join(", ")}`}
            value={d?.frozen_config.sha256?.slice(0, 12)} />
          <Check ok={d ? d.calendar.validated : null} title="NSE trading calendar validated"
            detail={d && <>Holidays from NSE ({d.calendar.n_holidays}); weekday rule reproduces {d.calendar.validation_year} index sessions{d.calendar.index_minus_rule?.length ? `; special sessions honoured: ${d.calendar.index_minus_rule.join(", ")}` : ""}. Phantom zero-volume rows rejected.</>}
            value={d?.calendar.historical_end} />
          <Check ok={tc ? tc.checked > 0 && tc.passed === tc.checked : null} title="NSE totalCount asserts passed"
            detail={tc && tc.audits.map((a) => `${a.source} ${a.window}: ${a.rows}/${a.total_count ?? "n/a"}`).join(" · ")}
            value={tc ? `${tc.passed}/${tc.checked}` : undefined} />
          <Check ok={fr ? fr.ok && fr.trailing_unchained_bytes === 0 : null} title="Append-only guard — forward record"
            detail={fr && <>{fr.rows} rows · {fr.file_bytes.toLocaleString()} bytes hash-chained · last append {fr.last_append}</>}
            value={fr ? "active" : undefined} />
          <Check ok={sl ? sl.ok && sl.trailing_unchained_bytes === 0 : null} title="Append-only guard — scan log"
            detail={sl && <>{sl.rows} rows · {sl.file_bytes.toLocaleString()} bytes hash-chained</>} value={sl ? "active" : undefined} />
          <Check ok={last ? !!last.ok : null} title="Last scan"
            detail={last && <>{istTime(last.started)} · {last.filings_seen ?? 0} filings seen · {last.universe_filings ?? 0} in universe · {last.new_events ?? 0} new events{last.errors?.length ? ` · errors: ${last.errors.join("; ")}` : ""}</>}
            value={last?.duration_s != null ? `${last.duration_s.toFixed(2)} s` : undefined} />
          <Check ok={true} title="Safety boundary" detail={d?.safety ?? "signals and logging only"} value="no broker" />

          <div className="section-h"><h3>Data freshness</h3></div>
          <div className="kv">
            <span>Benchmark panel (validated) ends</span><span>{d?.data_freshness.benchmark_panel_end ?? "—"}</span>
            <span>NSE holiday list fetched</span><span>{d?.data_freshness.holidays_fetched_at?.slice(0, 16) ?? "—"}</span>
            <span>Last successful scan</span><span>{d?.last_success ?? "—"}</span>
            {prices.slice(0, 12).map(([k, v]) => <Fragment key={k}><span>{k} last session</span><span>{v}</span></Fragment>)}
          </div>
        </section>

        <section>
          <div className="section-h"><h3>Frozen configuration · read-only</h3><span className="label">v{String(c.data?.constants?.version ?? "")}</span></div>
          <div className="kv">
            {Object.entries(c.data?.constants ?? {}).map(([k, v]) => (
              <Fragment key={k}><span>{CONST_LABELS[k] ?? k}</span><span style={{ whiteSpace: "normal", maxWidth: 260 }}>{fmtConst(k, v)}</span></Fragment>
            ))}
          </div>
          <div className="section-h"><h3>Pre-registration · forward-test protocol</h3></div>
          <pre className="md">{c.data?.pre_registration_markdown || "—"}</pre>
          <details style={{ marginTop: 12 }}>
            <summary className="label" style={{ cursor: "pointer" }}>Full frozen config file</summary>
            <pre className="md">{c.data?.frozen_config_markdown}</pre>
          </details>
        </section>
      </div>
    </div>
  );
}
