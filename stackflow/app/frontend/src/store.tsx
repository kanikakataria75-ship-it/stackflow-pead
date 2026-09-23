import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Screen = "observatory" | "tape" | "positions" | "performance" | "backtest" | "integrity";
export const SCREENS: { id: Screen; label: string }[] = [
  { id: "observatory", label: "Observatory" },
  { id: "tape", label: "Signal Tape" },
  { id: "positions", label: "Positions" },
  { id: "performance", label: "Forward Performance" },
  { id: "backtest", label: "Backtest" },
  { id: "integrity", label: "Config & Integrity" },
];

interface Ctx {
  screen: Screen; setScreen: (s: Screen) => void;
  demo: boolean; setDemo: (b: boolean) => void;
  asOf: string | null; setAsOf: (d: string | null) => void;          // tape scrub -> observatory
  focus: string | null; setFocus: (s: string | null) => void;        // symbol to fly to
  reducedMotion: boolean;
}

const C = createContext<Ctx | null>(null);

function fromHash(): Screen {
  const h = window.location.hash.replace("#/", "") as Screen;
  return SCREENS.some((s) => s.id === h) ? h : "observatory";
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [screen, setScreenState] = useState<Screen>(fromHash);
  const [demo, setDemoState] = useState<boolean>(() => new URLSearchParams(window.location.search).get("demo") === "1");
  const [asOf, setAsOf] = useState<string | null>(null);
  const [focus, setFocus] = useState<string | null>(null);
  const [reducedMotion, setRM] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setRM(mq.matches);
    mq.addEventListener("change", on);
    const hc = () => setScreenState(fromHash());
    window.addEventListener("hashchange", hc);
    return () => { mq.removeEventListener("change", on); window.removeEventListener("hashchange", hc); };
  }, []);

  const value = useMemo<Ctx>(() => ({
    screen,
    setScreen: (s) => { window.location.hash = `/${s}`; setScreenState(s); },
    demo,
    setDemo: (b) => {
      const u = new URL(window.location.href);
      if (b) u.searchParams.set("demo", "1"); else u.searchParams.delete("demo");
      window.history.replaceState(null, "", u.toString());
      setAsOf(null);
      setDemoState(b);
    },
    asOf, setAsOf, focus, setFocus, reducedMotion,
  }), [screen, demo, asOf, focus, reducedMotion]);
  return <C.Provider value={value}>{children}</C.Provider>;
}

export function useStore() {
  const c = useContext(C);
  if (!c) throw new Error("StoreProvider missing");
  return c;
}
