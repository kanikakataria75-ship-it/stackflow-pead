import { Suspense, lazy, useEffect, useState } from "react";
import { useApi, type UniversePoint } from "./api";
import { CommandPalette } from "./components/CommandPalette";
import { Masthead } from "./components/Masthead";
import { SCREENS, useStore } from "./store";

const Observatory = lazy(() => import("./screens/Observatory"));
const SignalTape = lazy(() => import("./screens/SignalTape"));
const Positions = lazy(() => import("./screens/Positions"));
const Performance = lazy(() => import("./screens/Performance"));
const Integrity = lazy(() => import("./screens/Integrity"));
const Backtest = lazy(() => import("./screens/Backtest"));
const Intro = lazy(() => import("./components/Intro"));

function shouldPlayIntro(reducedMotion: boolean) {
  if (reducedMotion || new URLSearchParams(window.location.search).get("intro") === "0") return false;
  if (new URLSearchParams(window.location.search).get("intro") === "1") return true;
  try { return sessionStorage.getItem("drift-intro-seen") !== "1"; } catch { return true; }
}

export default function App() {
  const { screen, setScreen, demo, reducedMotion } = useStore();
  const [palette, setPalette] = useState(false);
  const [intro, setIntro] = useState(() => shouldPlayIntro(reducedMotion));
  const endIntro = () => { try { sessionStorage.setItem("drift-intro-seen", "1"); } catch { /* private mode */ } setIntro(false); };
  const uni = useApi<{ symbols: UniversePoint[] }>("/universe/map", demo, 0);

  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette((p) => !p); return; }
      const tag = (e.target as HTMLElement)?.tagName;
      if (palette || tag === "INPUT" || tag === "TEXTAREA" || e.ctrlKey || e.metaKey || e.altKey) return;
      const i = Number(e.key) - 1;
      if (i >= 0 && i < SCREENS.length) setScreen(SCREENS[i].id);
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [palette, setScreen]);

  useEffect(() => { document.title = `DRIFT — ${SCREENS.find((s) => s.id === screen)?.label}${demo ? " · BACKTEST REPLAY" : ""}`; }, [screen, demo]);

  return (
    <div className="app">
      <div>
        <Masthead onPalette={() => setPalette(true)} />
      </div>
      <main id="main">
        <Suspense fallback={<div className="screen label">Loading…</div>}>
          {screen === "observatory" && <Observatory />}
          {screen === "tape" && <SignalTape />}
          {screen === "positions" && <Positions />}
          {screen === "performance" && <Performance />}
          {screen === "backtest" && <Backtest />}
          {screen === "integrity" && <Integrity />}
        </Suspense>
      </main>
      <CommandPalette open={palette} onClose={() => setPalette(false)}
        symbols={(uni.data?.symbols ?? []).map((s) => ({ symbol: s.symbol, sector: s.sector }))} />
      <div className="grain" aria-hidden />
      {intro && <Suspense fallback={<div className="intro" />}><Intro onDone={endIntro} /></Suspense>}
    </div>
  );
}
