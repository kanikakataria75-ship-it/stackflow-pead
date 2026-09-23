import { useEffect, useState } from "react";
import { SCREENS, useStore } from "../store";

function useISTClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(t); }, []);
  return now.toLocaleString("en-GB", { timeZone: "Asia/Kolkata", hour12: false, day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function Masthead({ onPalette }: { onPalette: () => void }) {
  const { screen, setScreen, demo, setDemo } = useStore();
  const clock = useISTClock();
  return (
    <>
      {demo && <div className="demo-bar" role="status">BACKTEST REPLAY — REAL HISTORICAL DATA AS OF 30 JUN 2026 — SEEN DATA, NOT FORWARD EVIDENCE</div>}
      <header className="mast">
        <div className="mast__title">
          <span className="mast__wordmark">DRIFT</span>
          <span className="mast__sub">StackFlow Forward Scanner · PEAD V2</span>
        </div>
        <div />
        <div className="mast__meta">
          <span className="clock num" aria-label="Indian Standard Time">{clock} IST</span>
          <button className="toggle" role="switch" aria-checked={demo} onClick={() => setDemo(!demo)} title="Replay the forward screens on the real corrected backtest, as it stood on 30 Jun 2026">
            <i /> Backtest replay
          </button>
          <span className="badge" title="Status fixed by the pre-registration. Never 'live' or 'validated'.">Forward-test candidate</span>
        </div>
        <nav className="nav" aria-label="Screens">
          {SCREENS.map((s, i) => (
            <button key={s.id} aria-current={screen === s.id ? "page" : undefined} onClick={() => setScreen(s.id)}>
              <span className="k">{String(i + 1).padStart(2, "0")}</span>{s.label}
            </button>
          ))}
          <span className="spacer" />
          <button className="kbd" onClick={onPalette} aria-label="Open command palette">Ctrl K</button>
        </nav>
      </header>
    </>
  );
}
