import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { useApi, type Signal } from "../api";
import { COLORS, REASONS, fix, num, qColor, shortDate } from "../lib/format";
import { useStore } from "../store";

const BAR = 7, GAP = 2, DAYGAP = 18, H = 300, BASE = 190;

function ThresholdLadder({ s }: { s: Signal }) {
  const cuts = [s.q20, s.q40, s.q60, s.q80].map((v) => num(v));
  const sue = num(s.sue);
  if (cuts.some((c) => c == null) || sue == null) return <div className="dim">Thresholds unavailable.</div>;
  const lo = Math.min(cuts[0]! - 1, sue - 0.3), hi = Math.max(cuts[3]! + 1, sue + 0.3);
  const x = (v: number) => ((v - lo) / (hi - lo)) * 380;
  return (
    <svg width="100%" viewBox="0 0 390 64" role="img" aria-label="SUE against ex-ante quintile thresholds">
      {[0, 1, 2, 3, 4].map((i) => {
        const edges = [lo, ...(cuts as number[]), hi];
        return <rect key={i} x={x(edges[i])} y={22} width={x(edges[i + 1]) - x(edges[i])} height={10} fill={qColor(i + 1)} opacity={0.55} />;
      })}
      {cuts.map((c, i) => <g key={i}><line x1={x(c!)} x2={x(c!)} y1={18} y2={36} stroke={COLORS.bone3} /><text x={x(c!)} y={50} fontSize={9} fill={COLORS.bone3} textAnchor="middle" fontFamily="IBM Plex Mono">{c!.toFixed(2)}</text></g>)}
      <line x1={x(sue)} x2={x(sue)} y1={8} y2={40} stroke={COLORS.bone} strokeWidth={1.5} />
      <text x={x(sue)} y={8} fontSize={10} fill={COLORS.bone} textAnchor="middle" fontFamily="IBM Plex Mono">SUE {sue.toFixed(2)}</text>
    </svg>
  );
}

function Drawer({ s, onClose }: { s: Signal; onClose: () => void }) {
  const ref = useRef<HTMLButtonElement>(null);
  useEffect(() => { ref.current?.focus(); const k = (e: KeyboardEvent) => e.key === "Escape" && onClose(); window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, [onClose]);
  const q = num(s.quintile);
  return (
    <motion.aside className="drawer" role="dialog" aria-label={`${s.symbol} filing detail`}
      initial={{ x: 40, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 40, opacity: 0 }} transition={{ duration: 0.18 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span className="label">Filing · {s.industry}</span>
        <button ref={ref} className="btn" onClick={onClose} aria-label="Close">Close</button>
      </div>
      <h3>{s.symbol}</h3>
      <div className="muted" style={{ marginBottom: 18 }}>{s.company}</div>
      <div className="section-h"><h3>Surprise vs thresholds in force at filing</h3></div>
      <ThresholdLadder s={s} />
      <div className="kv" style={{ marginTop: 14 }}>
        <span>Quintile</span><span style={{ color: qColor(q) }}>{q ? `Q${q}` : "—"}</span>
        <span>SUE</span><span>{fix(num(s.sue), 3)}</span>
        <span>History used</span><span>{s.hist_events ?? "—"} filings, trailing 365d</span>
        <span>Filed</span><span>{s.filing_timestamp.slice(0, 19)}{s.ts_source && s.ts_source !== "broadcast" ? ` (${s.ts_source})` : ""}</span>
        <span>Event day</span><span>{shortDate(s.event_day)}</span>
        <span>Planned entry (open)</span><span>{shortDate(s.planned_entry)}</span>
        <span>Planned exit (close)</span><span>{shortDate(s.planned_exit)}</span>
        <span>Decision</span><span style={{ color: s.decision === "ENTER" ? "var(--amber)" : undefined }}>{s.decision}</span>
        <span>Reason</span><span style={{ whiteSpace: "normal", maxWidth: 220 }}>{REASONS[s.reason] ?? s.reason ?? "—"}</span>
        <span>Scanned</span><span>{s.scanned_at.replace("T", " ")}</span>
      </div>
    </motion.aside>
  );
}

export default function SignalTape() {
  const { demo, asOf, setAsOf } = useStore();
  const { data, error } = useApi<{ signals: Signal[] }>("/signals/history", demo, 120_000);
  const [open, setOpen] = useState<Signal | null>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const drag = useRef(false);

  const { bars, days, width, maxAbs } = useMemo(() => {
    const sig = [...(data?.signals ?? [])].filter((s) => num(s.sue) != null)
      .sort((a, b) => a.filing_timestamp.localeCompare(b.filing_timestamp));
    let x = 24, prev = "";
    const bars: { s: Signal; x: number }[] = [], days: { d: string; x: number }[] = [];
    for (const s of sig) {
      const d = s.filing_timestamp.slice(0, 10);
      if (d !== prev) { if (prev) x += DAYGAP; days.push({ d, x }); prev = d; }
      bars.push({ s, x }); x += BAR + GAP;
    }
    const maxAbs = Math.max(2, ...sig.map((s) => Math.abs(num(s.sue)!)));
    return { bars, days, width: Math.max(x + 40, 600), maxAbs };
  }, [data]);

  useEffect(() => { if (wrap.current) wrap.current.scrollLeft = wrap.current.scrollWidth; }, [width]);  // newest on the right

  const scale = (v: number) => (Math.max(-maxAbs, Math.min(maxAbs, v)) / maxAbs) * 150;
  const dateAt = (clientX: number) => {
    const el = wrap.current!; const x = clientX - el.getBoundingClientRect().left + el.scrollLeft;
    let d = days[0]?.d ?? null;
    for (const k of days) if (k.x <= x) d = k.d;
    return d;
  };
  const cursorX = asOf ? (days.filter((d) => d.d <= asOf).pop()?.x ?? 0) : null;

  return (
    <div className="screen" style={{ maxWidth: "none" }}>
      <div className="kicker">
        <h2>Signal Tape</h2>
        <div className="deck">Every forward filing processed, oldest left, newest right. Bar height is SUE — above the rule for beats, below for misses; colour is the ex-ante quintile. Drag across the tape to scrub the Observatory to that day; click a bar for the full record.</div>
        <span className="label num">{bars.length} filings</span>
      </div>
      {error && <div className="empty">The scanner API is not reachable.<small>{error}</small></div>}
      {!error && data && bars.length === 0 && (
        <div className="empty">No forward filings yet.<small>The tape starts on 23 Sep 2026, the first session after the freeze. Results season for the September quarter opens in October; the scanner runs daily at 18:30 IST.</small></div>
      )}
      {bars.length > 0 && (
        <div className="tape-wrap" ref={wrap}
          onPointerDown={(e) => { drag.current = true; setAsOf(dateAt(e.clientX)); }}
          onPointerMove={(e) => { if (drag.current) setAsOf(dateAt(e.clientX)); }}
          onPointerUp={() => { drag.current = false; }} onPointerLeave={() => { drag.current = false; }}>
          <svg width={width} height={H} role="img" aria-label="Filing tape">
            <line x1={0} x2={width} y1={BASE} y2={BASE} stroke={COLORS.bone3} strokeWidth={1} opacity={0.6} />
            {days.map((d, i) => (
              <g key={d.d}>
                <line x1={d.x - DAYGAP / 2} x2={d.x - DAYGAP / 2} y1={20} y2={H - 30} stroke={COLORS.bone} opacity={0.07} />
                {(i % 3 === 0 || i === days.length - 1) && <text x={d.x} y={H - 12} fontSize={10} fill={COLORS.bone3} fontFamily="IBM Plex Mono">{d.d.slice(5)}</text>}
              </g>
            ))}
            {bars.map(({ s, x }) => {
              const v = num(s.sue)!, h = scale(v), q = num(s.quintile);
              const future = asOf != null && s.filing_timestamp.slice(0, 10) > asOf;
              return (
                <rect key={s.signal_id} x={x} y={h >= 0 ? BASE - h : BASE} width={BAR} height={Math.max(1, Math.abs(h))}
                  fill={qColor(q)} opacity={future ? 0.18 : q === 5 ? 1 : 0.85}
                  stroke={s.decision === "ENTER" ? COLORS.bone : "none"} strokeWidth={s.decision === "ENTER" ? 1 : 0}
                  tabIndex={0} role="button" aria-label={`${s.symbol} SUE ${v.toFixed(2)} Q${q ?? "?"}`}
                  onClick={(e) => { e.stopPropagation(); setOpen(s); }}
                  onKeyDown={(e) => { if (e.key === "Enter") setOpen(s); }}
                  onPointerDown={(e) => e.stopPropagation()} style={{ cursor: "pointer" }}>
                  <title>{`${s.symbol}  SUE ${v.toFixed(2)}  Q${q ?? "?"}  ${s.decision}`}</title>
                </rect>
              );
            })}
            {cursorX != null && <g><line x1={cursorX - 4} x2={cursorX - 4} y1={10} y2={H - 26} stroke={COLORS.amber} strokeWidth={1} />
              <text x={cursorX} y={16} fontSize={10} fill={COLORS.amber} fontFamily="IBM Plex Mono">as of {asOf}</text></g>}
          </svg>
        </div>
      )}
      <div style={{ display: "flex", gap: 22, marginTop: 12, flexWrap: "wrap" }} className="dim">
        <span><span className="accent">▮</span> Q5</span><span style={{ color: "#a39b8e" }}>▮ Q4</span><span style={{ color: "#7a7368" }}>▮ Q3</span>
        <span style={{ color: "#5f5a51" }}>▮ Q2</span><span style={{ color: "#8a4a3f" }}>▮ Q1</span>
        <span>outlined = slot allocated</span>
        {asOf && <button className="btn" onClick={() => setAsOf(null)}>Clear scrub</button>}
      </div>
      <AnimatePresence>{open && <Drawer s={open} onClose={() => setOpen(null)} />}</AnimatePresence>
    </div>
  );
}
