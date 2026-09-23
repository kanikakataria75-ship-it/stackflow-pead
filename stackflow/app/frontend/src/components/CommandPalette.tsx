import { useEffect, useMemo, useRef, useState } from "react";
import { SCREENS, useStore } from "../store";

interface Item { key: string; label: string; kind: string; run: () => void }

export function CommandPalette({ open, onClose, symbols }: { open: boolean; onClose: () => void; symbols: { symbol: string; sector: string }[] }) {
  const { setScreen, setFocus, setDemo, demo } = useStore();
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const input = useRef<HTMLInputElement>(null);

  const items = useMemo<Item[]>(() => {
    const base: Item[] = SCREENS.map((s, i) => ({ key: s.id, label: `${String(i + 1).padStart(2, "0")}  ${s.label}`, kind: "Screen", run: () => setScreen(s.id) }));
    base.push({ key: "demo", label: demo ? "Back to live forward data" : "Backtest replay (real data, 30 Jun 2026)", kind: "Mode", run: () => setDemo(!demo) });
    const syms: Item[] = symbols.map((s) => ({
      key: `sym-${s.symbol}`, label: s.symbol, kind: s.sector,
      run: () => { setScreen("observatory"); setFocus(s.symbol); },
    }));
    const all = [...base, ...syms];
    const t = q.trim().toLowerCase();
    if (!t) return base;
    return all.filter((i) => i.label.toLowerCase().includes(t) || i.kind.toLowerCase().includes(t)).slice(0, 40);
  }, [q, symbols, demo, setScreen, setFocus, setDemo]);

  useEffect(() => { if (open) { setQ(""); setSel(0); setTimeout(() => input.current?.focus(), 0); } }, [open]);
  useEffect(() => setSel(0), [q]);
  if (!open) return null;

  const pick = (i: Item | undefined) => { if (i) { i.run(); onClose(); } };
  return (
    <div className="palette-bg" onMouseDown={onClose}>
      <div className="palette" role="dialog" aria-label="Command palette" onMouseDown={(e) => e.stopPropagation()}>
        <input ref={input} value={q} placeholder="Jump to a symbol or screen…" aria-label="Search"
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") onClose();
            else if (e.key === "ArrowDown") { e.preventDefault(); setSel((s) => Math.min(s + 1, items.length - 1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setSel((s) => Math.max(s - 1, 0)); }
            else if (e.key === "Enter") pick(items[sel]);
          }} />
        <ul role="listbox">
          {items.map((i, k) => (
            <li key={i.key} role="option" aria-selected={k === sel} onMouseEnter={() => setSel(k)} onClick={() => pick(i)}>
              <span className="mono">{i.label}</span><span>{i.kind}</span>
            </li>
          ))}
          {!items.length && <li><span className="dim">No match.</span><span /></li>}
        </ul>
      </div>
    </div>
  );
}
