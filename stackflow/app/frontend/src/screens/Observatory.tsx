import { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";
import { useApi, type Status, type UniversePoint } from "../api";
import { Num } from "../components/Num";
import { Tooltip } from "../components/Tooltip";
import { istTime, qColor, shortDate } from "../lib/format";
import { layout, type Node } from "../lib/layout";
import { useStore } from "../store";

const Scene3D = lazy(() => import("./Scene3D"));

function canRender3D(): { ok: boolean; why: string } {
  if (window.innerWidth < 760) return { ok: false, why: "narrow screen — sector map" };
  const nav = navigator as Navigator & { deviceMemory?: number };
  if ((nav.hardwareConcurrency ?? 8) <= 2 || (nav.deviceMemory ?? 8) <= 2) return { ok: false, why: "low-power device — 2D fallback" };
  try {
    const c = document.createElement("canvas");
    const gl = c.getContext("webgl2") || c.getContext("webgl");
    if (!gl) return { ok: false, why: "WebGL unavailable — 2D fallback" };
  } catch { return { ok: false, why: "WebGL unavailable — 2D fallback" }; }
  return { ok: true, why: "" };
}

/** 2D sector map: the same information as the 3D field, as small multiples. */
function SectorMap({ nodes, onHover }: { nodes: Node[]; onHover: (n: Node | null, x: number, y: number) => void }) {
  const groups = useMemo(() => {
    const m = new Map<string, Node[]>();
    nodes.forEach((n) => { const k = n.p.sector; if (!m.has(k)) m.set(k, []); m.get(k)!.push(n); });
    return [...m.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [nodes]);
  return (
    <div className="sector-map" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))", gap: 0, padding: "210px 28px 90px" }}>
      {groups.map(([name, ns]) => (
        <section key={name} style={{ borderTop: "1px solid var(--rule)", padding: "10px 12px 16px 0" }}>
          <div className="label" style={{ marginBottom: 8 }}>{name} <span className="num">{ns.length}</span></div>
          <svg width="100%" viewBox={`0 0 220 ${Math.ceil(ns.length / 18) * 12 + 4}`} role="img" aria-label={`${name} stocks`}>
            {ns.map((n, i) => {
              const x = 6 + (i % 18) * 12, y = 6 + Math.floor(i / 18) * 12;
              const c = n.forward ? qColor(n.q) : "#6f695f";
              return n.p.is_fin
                ? <circle key={n.p.symbol} cx={x} cy={y} r={3.2} fill="none" stroke={c} strokeWidth={1}
                    onMouseMove={(e) => onHover(n, e.clientX, e.clientY)} onMouseLeave={() => onHover(null, 0, 0)} />
                : <circle key={n.p.symbol} cx={x} cy={y} r={n.forward ? 3.8 : 2.6} fill={c}
                    stroke={n.p.position ? "var(--amber)" : "none"} strokeWidth={1.4}
                    onMouseMove={(e) => onHover(n, e.clientX, e.clientY)} onMouseLeave={() => onHover(null, 0, 0)} />;
            })}
          </svg>
        </section>
      ))}
    </div>
  );
}

export default function Observatory() {
  const { demo, asOf, setAsOf, focus, reducedMotion } = useStore();
  const uni = useApi<{ symbols: UniversePoint[] }>("/universe/map", demo, 120_000);
  const st = useApi<Status>("/status", demo, 30_000);
  const [hover, setHover] = useState<{ n: Node; x: number; y: number } | null>(null);
  const [mode] = useState(canRender3D);
  const seen = useRef<Set<string> | null>(null);
  const [arrivals, setArrivals] = useState<string[]>([]);

  const { nodes, sectors } = useMemo(() => layout(uni.data?.symbols ?? [], asOf), [uni.data, asOf]);

  // motion encodes change: a filing not present in the previous refresh arrives as a particle.
  useEffect(() => {
    if (!uni.data) return;
    const withFwd = uni.data.symbols.filter((s) => s.forward);
    const ids = new Set(withFwd.map((s) => s.forward!.signal_id));
    if (seen.current === null) {
      // first load: only the most recent scan's filings are "arriving"
      const last = withFwd.map((s) => s.forward!.scanned_at.slice(0, 10)).sort().pop();
      setArrivals(withFwd.filter((s) => s.forward!.scanned_at.slice(0, 10) === last).map((s) => s.symbol).slice(0, 40));
    } else {
      setArrivals(withFwd.filter((s) => !seen.current!.has(s.forward!.signal_id)).map((s) => s.symbol));
    }
    seen.current = ids;
  }, [uni.data]);

  const s = st.data;
  const nFwd = nodes.filter((n) => n.forward).length;
  return (
    <div className="obs" onMouseLeave={() => setHover(null)}>
      <div className="legend" aria-label="Legend">
        <div><i style={{ background: "var(--amber)" }} /> Q5 — top ex-ante SUE quintile (signal)</div>
        <div><i style={{ background: "#a39b8e" }} /><i style={{ background: "#7a7368" }} /><i style={{ background: "#5f5a51" }} /> Q4 · Q3 · Q2</div>
        <div><i style={{ background: "#8a4a3f" }} /> Q1 — largest misses</div>
        <div><i className="hollow" /> Financial sector — excluded, shown hollow</div>
        <div><i style={{ background: "#6f695f", width: 6, height: 6 }} /> No forward filing yet</div>
      </div>
      <div className="obs-caption">
        {nodes.length} NSE stocks in the research universe, grouped by sector. Radial height of a point is its SUE; a ring fills clockwise
        as an open position ages toward its 60-session exit.
        {asOf && <div style={{ marginTop: 8 }}><span className="label">As of</span> <span className="num">{shortDate(asOf)}</span> <button className="btn" style={{ marginLeft: 8, padding: "2px 8px" }} onClick={() => setAsOf(null)}>Today</button></div>}
        {!mode.ok && <div className="label" style={{ marginTop: 8 }}>{mode.why}</div>}
      </div>

      {uni.error && <div className="empty" style={{ position: "absolute", top: 120, left: 28, right: 28 }}>The scanner API is not reachable.<small>{uni.error} — start the backend (see README) and this view fills in.</small></div>}

      {mode.ok ? (
        <Suspense fallback={<div className="label" style={{ position: "absolute", top: "45%", width: "100%", textAlign: "center" }}>Loading observatory…</div>}>
          <Scene3D nodes={nodes} sectors={sectors} asOf={asOf} reducedMotion={reducedMotion} arrivals={arrivals}
            focus={focus} onHover={(n, x, y) => setHover(n ? { n, x, y } : null)} />
        </Suspense>
      ) : (
        <SectorMap nodes={nodes} onHover={(n, x, y) => setHover(n ? { n, x, y } : null)} />
      )}

      {hover && <Tooltip node={hover.n} x={hover.x} y={hover.y} />}

      <div className="hud" aria-label="Scan status">
        <div><div className="v">{s?.last_scan?.ok === false ? <span className="loss">FAILED</span> : s?.last_scan?.started ? "OK" : "—"}</div><div className="label l">Last scan</div></div>
        <div><div className="v"><Num value={s?.filings_processed_today ?? null} format={(v) => Math.round(v).toString()} /></div><div className="label l">Filings today</div></div>
        <div><div className="v accent"><Num value={s?.q5_today ?? null} format={(v) => Math.round(v).toString()} /></div><div className="label l">Q5 today</div></div>
        <div><div className="v"><Num value={s?.slots_used ?? null} format={(v) => Math.round(v).toString().padStart(2, " ")} /><span className="dim"> / {s?.slots ?? 30}</span></div><div className="label l">Slots used</div></div>
        <div><div className="v"><Num value={nFwd} format={(v) => Math.round(v).toString()} /></div><div className="label l">Forward filings shown</div></div>
        <div><div className="v" style={{ fontSize: 13 }}>{s ? istTime(s.last_scan?.started ?? null) : "—"}</div><div className="label l">Last refresh · next {s ? s.next_scan_ist.slice(11, 16) : "—"} IST</div></div>
        <div style={{ textAlign: "right", border: 0 }} className="dim">
          {s && s.filings_processed_today === 0 && !demo ? <>No filings today. Next scan {s.next_scan_ist.slice(11, 16)} IST.</> : null}
        </div>
      </div>
    </div>
  );
}
