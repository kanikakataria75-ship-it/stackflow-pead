import type { Node } from "../lib/layout";
import { REASONS, fix, qColor, shortDate } from "../lib/format";

export function Tooltip({ node, x, y }: { node: Node; x: number; y: number }) {
  const f = node.forward;
  const r = node.p.research_last;
  const left = Math.min(x + 18, window.innerWidth - 290);
  const top = Math.min(y + 14, window.innerHeight - 260);
  return (
    <div className="tip" style={{ left, top }} role="tooltip">
      <h4>{node.p.symbol} {node.p.is_fin && <span className="label" style={{ marginLeft: 6 }}>excluded · financial</span>}</h4>
      <div className="label">{node.p.sector}</div>
      {f ? (
        <dl>
          <dt>Filed</dt><dd>{f.filing_timestamp.slice(0, 16)}</dd>
          <dt>SUE</dt><dd style={{ color: qColor(node.q) }}>{fix(node.sue, 3)}</dd>
          <dt>Quintile</dt><dd style={{ color: qColor(node.q) }}>{node.q ? `Q${node.q}` : "—"}</dd>
          <dt>Thresholds</dt><dd>{[f.q20, f.q40, f.q60, f.q80].map((v) => fix(v as number, 2)).join(" · ")}</dd>
          <dt>History n</dt><dd>{f.hist_events ?? "—"}</dd>
          <dt>Decision</dt><dd style={{ color: f.decision === "ENTER" ? "var(--amber)" : undefined }}>{f.decision}</dd>
          {f.reason && <><dt>Reason</dt><dd style={{ whiteSpace: "normal", maxWidth: 190 }}>{REASONS[f.reason] ?? f.reason}</dd></>}
          {f.planned_entry && <><dt>Entry / exit</dt><dd>{shortDate(f.planned_entry)} → {shortDate(f.planned_exit)}</dd></>}
        </dl>
      ) : (
        <dl>
          <dt>Forward filings</dt><dd>none yet</dd>
          {r && <><dt>Last research filing</dt><dd>{shortDate(r.filing_ts)}</dd>
            <dt>Its SUE (pre-freeze)</dt><dd>{fix(r.sue, 2)}{r.quintile ? ` · Q${r.quintile}` : ""}</dd></>}
        </dl>
      )}
      {node.p.position && <div className="label accent" style={{ marginTop: 8 }}>Open position</div>}
    </div>
  );
}
