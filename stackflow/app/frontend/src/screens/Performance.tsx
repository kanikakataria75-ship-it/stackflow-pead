import { Suspense, lazy, useMemo, useState } from "react";
import { scaleLinear, scaleTime } from "d3-scale";
import { area, line } from "d3-shape";
import { extent } from "d3-array";
import { useApi, type Performance as Perf, type PerfPoint } from "../api";
import { Num } from "../components/Num";
import { COLORS, fix, pct, shortDate } from "../lib/format";
import { useStore } from "../store";

const Ribbon3D = lazy(() => import("./Ribbon3D"));

function EquityChart({ s }: { s: PerfPoint[] }) {
  const W = 1100, H = 360, M = { l: 54, r: 70, t: 16, b: 28 }, DDH = 70;
  const x = scaleTime().domain(extent(s, (d) => new Date(d.date)) as [Date, Date]).range([M.l, W - M.r]);
  const lo = Math.min(...s.map((d) => Math.min(d.nav, d.bench))), hi = Math.max(...s.map((d) => Math.max(d.nav, d.bench)));
  const y = scaleLinear().domain([lo - 0.01, hi + 0.01]).range([H - M.b - DDH, M.t]).nice();
  const dd = scaleLinear().domain([Math.min(-0.05, ...s.map((d) => d.drawdown)), 0]).range([H - M.b, H - M.b - DDH + 14]);
  const strat = line<PerfPoint>().x((d) => x(new Date(d.date))).y((d) => y(d.nav))(s)!;
  const bench = line<PerfPoint>().x((d) => x(new Date(d.date))).y((d) => y(d.bench))(s)!;
  const under = area<PerfPoint>().x((d) => x(new Date(d.date))).y0(dd(0)).y1((d) => dd(d.drawdown))(s)!;
  const last = s[s.length - 1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Forward equity curve versus NIFTY 500">
      {y.ticks(5).map((t) => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke={COLORS.bone} opacity={0.07} />
        <text x={M.l - 8} y={y(t) + 3} fontSize={10} textAnchor="end" fill={COLORS.bone3} fontFamily="IBM Plex Mono">{(t * 100).toFixed(0)}</text></g>)}
      {x.ticks(6).map((t) => <text key={+t} x={x(t)} y={H - 8} fontSize={10} textAnchor="middle" fill={COLORS.bone3} fontFamily="IBM Plex Mono">{t.toISOString().slice(0, 10)}</text>)}
      <path d={bench} fill="none" stroke={COLORS.steel} strokeWidth={1.3} />
      <path d={strat} fill="none" stroke={COLORS.amber} strokeWidth={1.8} />
      <text x={W - M.r + 6} y={y(last.nav) + 3} fontSize={11} fill={COLORS.amber} fontFamily="IBM Plex Mono">{(last.nav * 100).toFixed(1)}</text>
      <text x={W - M.r + 6} y={y(last.bench) + 3} fontSize={11} fill={COLORS.steel} fontFamily="IBM Plex Mono">{(last.bench * 100).toFixed(1)}</text>
      <line x1={M.l} x2={W - M.r} y1={dd(0)} y2={dd(0)} stroke={COLORS.bone} opacity={0.2} />
      <path d={under} fill={COLORS.loss} opacity={0.45} />
      <text x={M.l} y={dd(0) - 4} fontSize={10} fill={COLORS.bone3} fontFamily="IBM Plex Sans Condensed" letterSpacing="0.14em">DRAWDOWN</text>
    </svg>
  );
}

function Seasons({ p }: { p: Perf["seasons"] }) {
  const n = p.required_max;
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${n}, 1fr)`, gap: 6, marginTop: 6 }}>
        {Array.from({ length: n }).map((_, i) => {
          const s = p.seasons[i];
          const done = s?.complete;
          return (
            <div key={i} style={{ borderTop: `3px solid ${done ? "var(--bone)" : i < p.required_min ? "var(--rule-strong)" : "var(--rule)"}`, paddingTop: 6 }}>
              <div className="label" style={{ color: done ? "var(--bone)" : undefined }}>Season {i + 1}{i === p.required_min - 1 ? " · minimum" : ""}</div>
              <div className="num dim" style={{ fontSize: 11 }}>{s ? `Q/E ${s.quarter_end}` : "—"}</div>
            </div>
          );
        })}
      </div>
      <div className="stat" style={{ marginTop: 14 }}><div className="v"><Num value={p.completed} format={(v) => Math.round(v).toString()} /><span className="dim"> of {p.required_min} seasons</span></div>
        <div className="label l">Pre-registered minimum before any verdict (4–6 seasons)</div></div>
    </div>
  );
}

export default function Performance() {
  const { demo } = useStore();
  const { data, error } = useApi<Perf>("/forward/performance", demo, 120_000);
  const [three, setThree] = useState(false);
  const s = data?.series ?? [];
  const summary = useMemo(() => {
    if (s.length < 2) return null;
    const a = s[0], b = s[s.length - 1];
    return { ret: b.nav / a.nav - 1, bench: b.bench / a.bench - 1, dd: Math.min(...s.map((d) => d.drawdown)), pos: b.positions };
  }, [s]);
  const ref = data?.research_reference;
  return (
    <div className="screen">
      <div className="kicker">
        <h2>Forward Performance</h2>
        <div className="deck">The only honest test left. This curve begins at the freeze and contains nothing but the forward record — no backtest history is mixed in. Backtest figures appear only in the greyed reference panel below.</div>
        <button className="btn" aria-pressed={three} onClick={() => setThree(!three)}>{three ? "2D view" : "3D ribbon"}</button>
      </div>
      {error && <div className="empty">The scanner API is not reachable.<small>{error}</small></div>}
      {demo && data?.note && <div className="num" style={{ color: "var(--amber)", fontSize: 12, marginBottom: 10 }}>{data.note}</div>}

      <div className="cols" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 8 }}>
        <div className="stat"><div className="v accent"><Num value={summary?.ret ?? null} format={(v) => pct(v)} /></div><div className="label l">{demo ? "Backtest book, 6 months to 30 Jun 2026" : "Forward book, since freeze"}</div></div>
        <div className="stat"><div className="v steel"><Num value={summary?.bench ?? null} format={(v) => pct(v)} /></div><div className="label l">NIFTY 500 (price), same days</div></div>
        <div className="stat"><div className="v"><Num value={summary?.dd ?? null} format={(v) => pct(v)} /></div><div className="label l">Worst drawdown · kill at −25.0%</div></div>
        <div className="stat"><div className="v"><Num value={summary?.pos ?? null} format={(v) => Math.round(v).toString()} /></div><div className="label l">Positions held today</div></div>
      </div>

      {data && s.length < 2 && (
        <div className="empty">The forward record has no filled positions yet.<small>
          The curve starts {data.starts ? shortDate(data.starts) : "at the first session after 22 Sep 2026"}. It will draw once a Q5 signal is allocated and filled at an NSE open.</small></div>
      )}
      {s.length >= 2 && (three
        ? <Suspense fallback={<div className="label">Loading ribbon…</div>}><div style={{ height: 420, borderTop: "1px solid var(--rule)", borderBottom: "1px solid var(--rule)" }}><Ribbon3D series={s} /></div>
            <div className="dim" style={{ fontSize: 12, marginTop: 6 }}>Ribbon: height = NAV, width = positions held that day, colour = drawdown depth (bone → red). Drag to orbit.</div></Suspense>
        : <EquityChart s={s} />)}
      {s.length >= 2 && <div style={{ display: "flex", gap: 22, fontSize: 12 }} className="dim"><span><span className="accent">━</span> forward book (share &amp; cash, 0.585% cost)</span><span><span className="steel">━</span> NIFTY 500 price index</span></div>}

      <div className="cols" style={{ gridTemplateColumns: "1.3fr 1fr", marginTop: 26 }}>
        <div>
          <div className="section-h"><h3>Seasons completed</h3></div>
          {data && <Seasons p={data.seasons} />}
        </div>
        <div>
          <div className="section-h"><h3>Pre-registered kill criteria</h3></div>
          <ol style={{ margin: 0, paddingLeft: 18, color: "var(--bone-2)", display: "grid", gap: 8, fontSize: 13 }}>
            {(data?.kill_criteria ?? []).map((k) => <li key={k}>{k}</li>)}
          </ol>
          <div className="dim" style={{ fontSize: 12, marginTop: 10 }}>Any one triggers permanent retirement. Evaluated only on forward data.</div>
        </div>
      </div>

      {ref && (
        <div className="grey-panel" style={{ marginTop: 30 }} aria-label="Research reference, not forward evidence">
          <div className="label" style={{ marginBottom: 10 }}>{ref.label} · {ref.source}</div>
          <table className="tab" style={{ opacity: 0.8 }}>
            <thead><tr><th className="l">Backtest (seen data)</th><th>CAGR</th><th>NIFTY 500</th><th>Excess</th><th>Sharpe</th><th>NIFTY Sharpe</th><th>Max DD</th><th>Trades</th></tr></thead>
            <tbody>{Object.entries(ref.periods).map(([p, m]) => (
              <tr key={p}><td className="l" style={{ fontFamily: "var(--f-label)" }}>{p}</td>
                <td>{pct(m.cagr)}</td><td>{pct(m.bench_cagr)}</td><td>{pct(m.excess_cagr)}</td><td>{fix(m.sharpe_rf0)}</td>
                <td>{fix(m.bench_sharpe_rf0)}</td><td>{pct(m.max_dd)}</td><td>{m.trades ?? "—"}</td></tr>))}</tbody>
          </table>
          <div style={{ fontSize: 12, marginTop: 10 }}>Discovery and holdout have both been examined repeatedly; they cannot serve as further evidence. Excess is versus the NIFTY 500 price index and overstates excess versus a total-return index by roughly 1–1.5 pp a year.</div>
        </div>
      )}
    </div>
  );
}
