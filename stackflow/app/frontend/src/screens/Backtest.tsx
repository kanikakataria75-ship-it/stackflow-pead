import { useMemo, useState } from "react";
import { scaleBand, scaleLinear, scaleTime } from "d3-scale";
import { area, line } from "d3-shape";
import { useApi } from "../api";
import { Num } from "../components/Num";
import { COLORS, fix, pct } from "../lib/format";

type M = Record<string, number | string | null>;
interface BT {
  label: string; source: string;
  periods: Record<string, M>;
  nav: { date: string; strategy_nav: number; nifty500: number; strategy_dd: number; positions_held: number; period: string }[];
  yearly: { year: number; strategy: number; nifty500: number; excess: number; trades_entered: number; window: string }[];
  cost: { round_trip_cost: number; full_cagr: number; full_excess: number; full_sharpe_rf0: number; full_max_dd: number; holdout_cagr: number; holdout_excess: number }[];
  kill_tests: { test: string; perturbation: string; result: string; passed: boolean | string }[];
  signal: { label: string; n_q5: number; n_q1: number; spread_pct: number; p_val: number; folds_pos: number; folds_total: number }[];
  folds: { qtr: string; spread: number; period: string }[];
  placebo: { n: number; full_excess_mean: number; full_excess_sd: number; holdout_excess_mean: number; holdout_excess_sd: number };
}
const n = (v: unknown) => (typeof v === "number" ? v : null);

function Equity({ nav, logScale }: { nav: BT["nav"]; logScale: boolean }) {
  const W = 1200, H = 420, M = { l: 50, r: 64, t: 18, b: 26 }, DD = 80;
  const pts = nav.map((d) => ({ ...d, t: new Date(d.date) }));
  const x = scaleTime().domain([pts[0].t, pts[pts.length - 1].t]).range([M.l, W - M.r]);
  const hi = Math.max(...pts.map((d) => Math.max(d.strategy_nav, d.nifty500)));
  const lo = Math.min(...pts.map((d) => Math.min(d.strategy_nav, d.nifty500)));
  const tr = (v: number) => (logScale ? Math.log(v) : v);
  const y = scaleLinear().domain([tr(lo * 0.97), tr(hi * 1.03)]).range([H - M.b - DD, M.t]);
  const dd = scaleLinear().domain([Math.min(...pts.map((d) => d.strategy_dd)) * 1.1, 0]).range([H - M.b, H - M.b - DD + 16]);
  const split = pts.find((d) => d.period === "Holdout")?.t;
  const sl = line<(typeof pts)[0]>().x((d) => x(d.t)).y((d) => y(tr(d.strategy_nav)))(pts)!;
  const bl = line<(typeof pts)[0]>().x((d) => x(d.t)).y((d) => y(tr(d.nifty500)))(pts)!;
  const fill = area<(typeof pts)[0]>().x((d) => x(d.t)).y0(y(tr(lo * 0.97))).y1((d) => y(tr(d.strategy_nav)))(pts)!;
  const uw = area<(typeof pts)[0]>().x((d) => x(d.t)).y0(dd(0)).y1((d) => dd(d.strategy_dd))(pts)!;
  const last = pts[pts.length - 1];
  const ticks = logScale ? [100, 125, 150, 175, 200, 225].filter((v) => v >= lo * 0.97 && v <= hi * 1.03) : y.ticks(6);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Backtest equity curve versus NIFTY 500">
      <defs>
        <linearGradient id="btfill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor={COLORS.amber} stopOpacity="0.22" /><stop offset="1" stopColor={COLORS.amber} stopOpacity="0" /></linearGradient>
      </defs>
      {split && <rect x={x(split)} y={M.t} width={W - M.r - x(split)} height={H - M.b - M.t} fill={COLORS.bone} opacity={0.035} />}
      {split && <text x={x(split) + 8} y={M.t + 12} fontSize={10} fill={COLORS.bone3} fontFamily="IBM Plex Sans Condensed" letterSpacing="0.16em">HOLDOUT →</text>}
      <text x={M.l + 6} y={M.t + 12} fontSize={10} fill={COLORS.bone3} fontFamily="IBM Plex Sans Condensed" letterSpacing="0.16em">DISCOVERY</text>
      {ticks.map((t) => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(tr(t))} y2={y(tr(t))} stroke={COLORS.bone} opacity={0.07} />
        <text x={M.l - 8} y={y(tr(t)) + 3} fontSize={10} textAnchor="end" fill={COLORS.bone3} fontFamily="IBM Plex Mono">{Math.round(t)}</text></g>)}
      {x.ticks(6).map((t) => <text key={+t} x={x(t)} y={H - 6} fontSize={10} textAnchor="middle" fill={COLORS.bone3} fontFamily="IBM Plex Mono">{t.getFullYear()}</text>)}
      <path d={fill} fill="url(#btfill)" />
      <path d={bl} fill="none" stroke={COLORS.steel} strokeWidth={1.3} />
      <path d={sl} fill="none" stroke={COLORS.amber} strokeWidth={2} />
      <text x={W - M.r + 6} y={y(tr(last.strategy_nav)) + 4} fontSize={12} fill={COLORS.amber} fontFamily="IBM Plex Mono">{last.strategy_nav.toFixed(0)}</text>
      <text x={W - M.r + 6} y={y(tr(last.nifty500)) + 4} fontSize={12} fill={COLORS.steel} fontFamily="IBM Plex Mono">{last.nifty500.toFixed(0)}</text>
      <line x1={M.l} x2={W - M.r} y1={dd(0)} y2={dd(0)} stroke={COLORS.bone} opacity={0.2} />
      <path d={uw} fill={COLORS.loss} opacity={0.5} />
      <text x={M.l} y={dd(0) - 4} fontSize={10} fill={COLORS.bone3} fontFamily="IBM Plex Sans Condensed" letterSpacing="0.14em">DRAWDOWN</text>
    </svg>
  );
}

function Yearly({ rows }: { rows: BT["yearly"] }) {
  const W = 600, H = 250, M = { l: 40, r: 10, t: 14, b: 40 };
  const x = scaleBand<string>().domain(rows.map((r) => String(r.year))).range([M.l, W - M.r]).padding(0.28);
  const vals = rows.flatMap((r) => [r.strategy, r.nifty500]);
  const y = scaleLinear().domain([Math.min(0, ...vals) * 1.15, Math.max(...vals) * 1.15]).range([H - M.b, M.t]).nice();
  const bw = x.bandwidth() / 2;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Calendar-year returns">
      {y.ticks(5).map((t) => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke={COLORS.bone} opacity={t === 0 ? 0.3 : 0.07} />
        <text x={M.l - 6} y={y(t) + 3} fontSize={9} textAnchor="end" fill={COLORS.bone3} fontFamily="IBM Plex Mono">{Math.round(t * 100)}%</text></g>)}
      {rows.map((r) => (
        <g key={r.year}>
          <rect x={x(String(r.year))!} y={y(Math.max(0, r.strategy))} width={bw - 2} height={Math.abs(y(r.strategy) - y(0))} fill={r.strategy >= 0 ? COLORS.amber : COLORS.loss} />
          <rect x={x(String(r.year))! + bw} y={y(Math.max(0, r.nifty500))} width={bw - 2} height={Math.abs(y(r.nifty500) - y(0))} fill={COLORS.steel} opacity={0.7} />
          <text x={x(String(r.year))! + bw} y={H - 24} fontSize={10} textAnchor="middle" fill={COLORS.bone2} fontFamily="IBM Plex Mono">{r.year}</text>
          <text x={x(String(r.year))! + bw} y={H - 10} fontSize={10} textAnchor="middle" fill={r.excess >= 0 ? COLORS.bone : COLORS.loss} fontFamily="IBM Plex Mono">{pct(r.excess, 1)}</text>
        </g>
      ))}
    </svg>
  );
}

function Folds({ rows }: { rows: BT["folds"] }) {
  const W = 600, H = 230, M = { l: 36, r: 8, t: 12, b: 34 };
  const x = scaleBand<string>().domain(rows.map((r) => r.qtr)).range([M.l, W - M.r]).padding(0.25);
  const y = scaleLinear().domain([Math.min(0, ...rows.map((r) => r.spread)) * 1.2, Math.max(...rows.map((r) => r.spread)) * 1.1]).range([H - M.b, M.t]).nice();
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Quarterly Q5 minus Q1 spread">
      {y.ticks(4).map((t) => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke={COLORS.bone} opacity={t === 0 ? 0.3 : 0.07} />
        <text x={M.l - 5} y={y(t) + 3} fontSize={9} textAnchor="end" fill={COLORS.bone3} fontFamily="IBM Plex Mono">{Math.round(t * 100)}%</text></g>)}
      {rows.map((r, i) => (
        <g key={r.qtr}>
          <rect x={x(r.qtr)!} y={y(Math.max(0, r.spread))} width={x.bandwidth()} height={Math.abs(y(r.spread) - y(0))}
            fill={r.spread >= 0 ? (r.period === "Holdout" ? COLORS.amber : COLORS.bone2) : COLORS.loss} />
          {i % 2 === 0 && <text x={x(r.qtr)! + x.bandwidth() / 2} y={H - 18} fontSize={8.5} textAnchor="middle" fill={COLORS.bone3} fontFamily="IBM Plex Mono">{r.qtr.replace("20", "")}</text>}
        </g>
      ))}
    </svg>
  );
}

function Hero({ v, label, sub, accent }: { v: number | null; label: string; sub?: string; accent?: boolean }) {
  return (
    <div className="stat">
      <div className={`v ${accent ? "accent" : ""}`} style={{ fontSize: 40 }}><Num value={v} format={(x) => label.includes("Sharpe") ? x.toFixed(2) : label.includes("Trades") ? Math.round(x).toString() : pct(x)} /></div>
      <div className="label l">{label}</div>
      {sub && <div className="dim num" style={{ fontSize: 12, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export default function Backtest() {
  const { data, error } = useApi<BT>("/research/backtest", false, 0);
  const [logScale, setLog] = useState(false);
  const full = data?.periods["Full Period"], disc = data?.periods["Discovery"], hold = data?.periods["Holdout"];
  const nav = useMemo(() => data?.nav ?? [], [data]);
  const primary = data?.signal.find((s) => s.label.startsWith("Primary"));
  const rows: [string, string, (m?: M) => string][] = [
    ["CAGR", "cagr", (m) => pct(n(m?.cagr))], ["NIFTY 500 CAGR", "bench_cagr", (m) => pct(n(m?.bench_cagr))],
    ["Excess CAGR", "excess_cagr", (m) => pct(n(m?.excess_cagr))], ["Sharpe (rf 0)", "sharpe_rf0", (m) => fix(n(m?.sharpe_rf0))],
    ["NIFTY 500 Sharpe", "bench_sharpe_rf0", (m) => fix(n(m?.bench_sharpe_rf0))], ["Max drawdown", "max_dd", (m) => pct(n(m?.max_dd))],
    ["Win rate", "win_rate", (m) => pct(n(m?.win_rate), 1, false)], ["Profit factor", "profit_factor", (m) => fix(n(m?.profit_factor))],
    ["Trades", "trades", (m) => String(n(m?.trades) ?? "—")],
  ];
  return (
    <div className="screen">
      <div className="kicker">
        <h2>Backtest</h2>
        <div className="deck">The corrected PEAD V2 backtest, Aug 2021 – Aug 2026: 30 slots, non-financials, top ex-ante SUE quintile, 60-session hold, share-and-cash accounting, 0.585% round trip. <span className="accent">This is research on data already seen — not forward evidence.</span></div>
        <a className="btn dl" href="/api/research/tearsheet.xlsx" download="PEAD_V2_Tearsheet.xlsx"
          title="Institutional tear sheet: cover, KPI table, charts, all 567 trades, risk diagnostics, methodology">
          ↓ Download Excel tear sheet
        </a>
      </div>
      {error && <div className="empty">The scanner API is not reachable.<small>{error}</small></div>}

      <div className="cols bt-hero" style={{ gridTemplateColumns: "repeat(6, 1fr)" }}>
        <Hero v={n(full?.cagr)} label="CAGR" sub={`NIFTY 500 ${pct(n(full?.bench_cagr))}`} accent />
        <Hero v={n(full?.excess_cagr)} label="Excess vs NIFTY 500" sub="price index" accent />
        <Hero v={n(full?.sharpe_rf0)} label="Sharpe (rf 0)" sub={`index ${fix(n(full?.bench_sharpe_rf0))}`} />
        <Hero v={n(full?.max_dd)} label="Max drawdown" sub={`index ${pct(n(full?.bench_max_dd))}`} />
        <Hero v={n(full?.total_return)} label="Total return" sub={`${full?.start ?? ""} → ${full?.end ?? ""}`} />
        <Hero v={n(full?.trades)} label="Trades" sub={`win rate ${pct(n(full?.win_rate), 1, false)}`} />
      </div>

      <div className="section-h"><h3>Equity curve · rebased to 100</h3>
        <button className="btn" aria-pressed={logScale} onClick={() => setLog(!logScale)}>{logScale ? "Linear" : "Log scale"}</button></div>
      {nav.length > 0 && <Equity nav={nav} logScale={logScale} />}
      <div style={{ display: "flex", gap: 22, fontSize: 12 }} className="dim"><span><span className="accent">━</span> strategy</span><span><span className="steel">━</span> NIFTY 500 price index</span><span>shaded = holdout (2024 →)</span></div>

      <div className="cols" style={{ gridTemplateColumns: "1.25fr 1fr", marginTop: 26 }}>
        <section>
          <div className="section-h"><h3>Discovery vs holdout — the honesty check</h3></div>
          <table className="tab">
            <thead><tr><th className="l">Metric</th><th>Full period</th><th>Discovery</th><th>Holdout</th></tr></thead>
            <tbody>{rows.map(([lab, , f]) => (
              <tr key={lab}><td className="l" style={{ fontFamily: "var(--f-label)" }}>{lab}</td><td>{f(full)}</td><td>{f(disc)}</td>
                <td className={lab === "Excess CAGR" ? "accent" : ""}>{f(hold)}</td></tr>))}</tbody>
          </table>
          <div className="dim" style={{ fontSize: 12, marginTop: 8 }}>
            Holdout = trades signalled 2024 onward, in a book started empty. Its excess is thin (+0.82%) and its Sharpe equals the index — which is why the strategy is a forward-test candidate, not validated.
          </div>
        </section>
        <section>
          <div className="section-h"><h3>The signal underneath</h3></div>
          <div className="cols" style={{ gridTemplateColumns: "1fr 1fr 1fr", marginBottom: 10 }}>
            <div className="stat"><div className="v accent">{pct((primary?.spread_pct ?? 0) / 100)}</div><div className="label l">Q5 − Q1, 60 sessions</div></div>
            <div className="stat"><div className="v">{primary ? `${primary.folds_pos}/${primary.folds_total}` : "—"}</div><div className="label l">Quarters positive</div></div>
            <div className="stat"><div className="v">{primary ? primary.p_val.toExponential(1) : "—"}</div><div className="label l">p-value</div></div>
          </div>
          {data && <Folds rows={data.folds} />}
          <div className="dim" style={{ fontSize: 12 }}>Quarterly spread; amber = holdout quarters.</div>
        </section>
      </div>

      <div className="cols" style={{ gridTemplateColumns: "1fr 1fr", marginTop: 26 }}>
        <section>
          <div className="section-h"><h3>Calendar years · strategy vs index</h3></div>
          {data && <Yearly rows={data.yearly} />}
          <div className="dim" style={{ fontSize: 12 }}>Amber = strategy, steel = NIFTY 500. Bottom row = excess. 2021 from 11 Aug; 2026 to 11 Aug.</div>
        </section>
        <section>
          <div className="section-h"><h3>Cost sensitivity</h3></div>
          <table className="tab">
            <thead><tr><th className="l">Round trip</th><th>CAGR</th><th>Excess</th><th>Sharpe</th><th>Holdout excess</th></tr></thead>
            <tbody>{(data?.cost ?? []).map((c) => (
              <tr key={c.round_trip_cost}><td className="l">{(c.round_trip_cost * 100).toFixed(3)}%</td><td>{pct(c.full_cagr)}</td><td>{pct(c.full_excess)}</td>
                <td>{fix(c.full_sharpe_rf0)}</td><td className={c.holdout_excess < 0 ? "loss" : ""}>{pct(c.holdout_excess)}</td></tr>))}</tbody>
          </table>
          {data && <div className="dim" style={{ fontSize: 12, marginTop: 10 }}>
            Placebo ({data.placebo.n} random books, same mechanics): full-period excess {pct(data.placebo.full_excess_mean)} ± {pct(data.placebo.full_excess_sd, 2, false)}; holdout {pct(data.placebo.holdout_excess_mean)} ± {pct(data.placebo.holdout_excess_sd, 2, false)}. The SUE ordering beats random selection.</div>}
          <div className="section-h"><h3>Kill tests</h3></div>
          {(data?.kill_tests ?? []).map((k) => {
            const ok = k.passed === true || k.passed === "True";
            return (
              <div className="check" key={k.test}>
                <span className={`g ${ok ? "ok" : "bad"}`}>{ok ? "✓" : "✕"}</span>
                <div><div>{k.test} · {k.perturbation}</div><div className="d">{k.result}</div></div>
                <div className={`num ${ok ? "muted" : "loss"}`} style={{ fontSize: 12 }}>{ok ? "PASS" : "FAIL"}</div>
              </div>
            );
          })}
        </section>
      </div>
      <div className="grey-panel" style={{ marginTop: 26, fontSize: 12 }}>
        Source: {data?.source}. Excess is versus the NIFTY 500 price index while strategy prices include dividends — excess versus a total-return index is roughly 1–1.5 pp a year lower. Discovery and holdout have both been examined repeatedly; the forward record is the only remaining clean test.
      </div>
    </div>
  );
}
