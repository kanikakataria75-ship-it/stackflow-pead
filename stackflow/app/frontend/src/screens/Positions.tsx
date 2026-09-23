import { useMemo, useState } from "react";
import { useApi, type Position, type Positions as P } from "../api";
import { Num } from "../components/Num";
import { fix, inr, pct, shortDate } from "../lib/format";
import { useStore } from "../store";

type Key = keyof Position;
interface Col { k: Key; label: string; l?: boolean; fmt: (p: Position) => React.ReactNode }

function useSorted(rows: Position[], filter: string, sort: { k: Key; dir: 1 | -1 }) {
  return useMemo(() => {
    const f = filter.trim().toLowerCase();
    const r = rows.filter((p) => !f || p.symbol.toLowerCase().includes(f) || (p.industry ?? "").toLowerCase().includes(f));
    return [...r].sort((a, b) => {
      const x = a[sort.k], y = b[sort.k];
      if (typeof x === "number" && typeof y === "number") return (x - y) * sort.dir;
      return String(x ?? "").localeCompare(String(y ?? "")) * sort.dir;
    });
  }, [rows, filter, sort]);
}

function Table({ rows, cols, caption }: { rows: Position[]; cols: Col[]; caption: string }) {
  const [sort, setSort] = useState<{ k: Key; dir: 1 | -1 }>({ k: cols[0].k, dir: 1 });
  const [filter, setFilter] = useState("");
  const sorted = useSorted(rows, filter, sort);
  return (
    <>
      <div style={{ display: "flex", justifyContent: "flex-end", margin: "-4px 0 6px" }}>
        <input className="filter" placeholder="Filter symbol or sector" value={filter} onChange={(e) => setFilter(e.target.value)} aria-label={`Filter ${caption}`} />
      </div>
      <table className="tab cardify">
        <caption className="label" style={{ textAlign: "left", captionSide: "bottom", paddingTop: 8 }}>{caption}</caption>
        <thead><tr>{cols.map((c) => (
          <th key={String(c.k)} className={c.l ? "l" : ""} aria-sort={sort.k === c.k ? (sort.dir === 1 ? "ascending" : "descending") : undefined}>
            <button onClick={() => setSort((s) => ({ k: c.k, dir: s.k === c.k ? (s.dir === 1 ? -1 : 1) : -1 }))}>
              {c.label}{sort.k === c.k ? (sort.dir === 1 ? " ↑" : " ↓") : ""}
            </button>
          </th>))}</tr></thead>
        <tbody>{sorted.map((p) => (
          <tr key={p.signal_id}>{cols.map((c) => <td key={String(c.k)} data-l={c.label} className={`${c.l ? "l" : ""} ${c.k === "symbol" ? "sym" : ""}`}>{c.fmt(p)}</td>)}</tr>
        ))}</tbody>
      </table>
    </>
  );
}

const signed = (v?: number) => <span className={v == null ? "" : v < 0 ? "loss" : ""}>{pct(v)}</span>;

export default function Positions() {
  const { demo } = useStore();
  const { data, error } = useApi<P>("/positions/open", demo, 60_000);
  const openCols: Col[] = [
    { k: "symbol", label: "Symbol", l: true, fmt: (p) => p.symbol },
    { k: "industry", label: "Sector", l: true, fmt: (p) => <span className="muted" style={{ fontFamily: "var(--f-label)" }}>{p.industry}</span> },
    { k: "sue", label: "SUE", fmt: (p) => fix(p.sue, 2) },
    { k: "entry_date", label: "Entered", fmt: (p) => shortDate(p.entry_date) },
    { k: "sessions_held", label: "Held / 60", fmt: (p) => (
      <span style={{ display: "inline-flex", gap: 10, alignItems: "center" }}>
        <span className="bar live" aria-hidden><b style={{ width: `${Math.min(100, ((p.sessions_held ?? 0) / p.holding_sessions) * 100)}%` }} /></span>
        <span>{String(p.sessions_held ?? 0).padStart(2, " ")}</span>
      </span>) },
    { k: "exit_date", label: "Exit", fmt: (p) => shortDate(p.exit_date) },
    { k: "entry_price", label: "Entry", fmt: (p) => inr(p.entry_price) },
    { k: "current_price", label: "Last", fmt: (p) => inr(p.current_price) },
    { k: "unrealised_return", label: "Unrealised", fmt: (p) => signed(p.unrealised_return) },
    { k: "excess_vs_nifty500", label: "vs NIFTY 500", fmt: (p) => signed(p.excess_vs_nifty500) },
  ];
  const closedCols: Col[] = [
    { k: "symbol", label: "Symbol", l: true, fmt: (p) => p.symbol },
    { k: "industry", label: "Sector", l: true, fmt: (p) => <span className="muted" style={{ fontFamily: "var(--f-label)" }}>{p.industry}</span> },
    { k: "entry_date", label: "Entered", fmt: (p) => shortDate(p.entry_date) },
    { k: "exit_date", label: "Exited", fmt: (p) => shortDate(p.exit_date) },
    { k: "entry_price", label: "Entry", fmt: (p) => inr(p.entry_price) },
    { k: "exit_price", label: "Exit", fmt: (p) => inr(p.exit_price ?? p.current_price) },
    { k: "net_return", label: "Net (after 0.585%)", fmt: (p) => signed(p.net_return ?? p.unrealised_return) },
    { k: "excess_vs_nifty500", label: "vs NIFTY 500", fmt: (p) => signed(p.excess_vs_nifty500) },
  ];
  const plannedCols: Col[] = [
    { k: "symbol", label: "Symbol", l: true, fmt: (p) => p.symbol },
    { k: "industry", label: "Sector", l: true, fmt: (p) => <span className="muted" style={{ fontFamily: "var(--f-label)" }}>{p.industry}</span> },
    { k: "sue", label: "SUE", fmt: (p) => fix(p.sue, 2) },
    { k: "entry_date", label: "Entry open", fmt: (p) => shortDate(p.entry_date) },
    { k: "exit_date", label: "Planned exit", fmt: (p) => shortDate(p.exit_date) },
  ];
  const d = data;
  return (
    <div className="screen">
      <div className="kicker">
        <h2>Positions</h2>
        <div className="deck">The frozen 30-slot book, marked to the last NSE close. Prices are raw exchange prices; a slot is released only after its exit close. Entries and exits are logged — this tool never sends orders.</div>
        <span />
      </div>
      <div className="cols" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 10 }}>
        <div className="stat"><div className="v"><Num value={d?.slots_used ?? null} format={(v) => Math.round(v).toString()} /><span className="dim"> / {d?.slots ?? 30}</span></div><div className="label l">Slots in use</div></div>
        <div className="stat"><div className="v"><Num value={d?.open.length ?? null} format={(v) => Math.round(v).toString()} /></div><div className="label l">Open</div></div>
        <div className="stat"><div className="v"><Num value={d?.planned?.length ?? 0} format={(v) => Math.round(v).toString()} /></div><div className="label l">Awaiting entry open</div></div>
        <div className="stat"><div className="v"><Num value={d?.closed.length ?? null} format={(v) => Math.round(v).toString()} /></div><div className="label l">Closed</div></div>
      </div>
      {error && <div className="empty">The scanner API is not reachable.<small>{error}</small></div>}

      <div className="section-h"><h3>Open</h3><span className="label">sorted by column · click a header</span></div>
      {d && d.open.length === 0
        ? <div className="empty">No open positions.<small>Positions open at the NSE open after a Q5 filing is allocated a slot.</small></div>
        : d && <Table rows={d.open} cols={openCols} caption="Unrealised return deducts the entry leg of the cost (0.2925%)." />}

      {d?.planned && d.planned.length > 0 && <>
        <div className="section-h"><h3>Allocated — awaiting entry open</h3></div>
        <Table rows={d.planned} cols={plannedCols} caption="Price filter (open above ₹50) is checked at the actual open." />
      </>}

      <div className="section-h"><h3>Closed</h3></div>
      {d && d.closed.length === 0
        ? <div className="empty">No closed positions yet.<small>A position closes at the NSE close of its 60th session.</small></div>
        : d && <Table rows={d.closed} cols={closedCols} caption="Net return deducts the full 0.585% round trip." />}
    </div>
  );
}
