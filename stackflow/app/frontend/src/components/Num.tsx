import { useEffect, useRef, useState } from "react";
import { useStore } from "../store";

/** A number that rolls to its new value with an eased count. Tabular digits keep width fixed,
 *  so a changing value never jitters the layout. The roll only happens on change. */
export function Num({ value, format, className = "" }: { value: number | null | undefined; format: (v: number) => string; className?: string }) {
  const { reducedMotion } = useStore();
  const [shown, setShown] = useState<number | null>(value ?? null);
  const from = useRef<number | null>(value ?? null);
  useEffect(() => {
    if (value == null || !Number.isFinite(value)) { setShown(null); return; }
    const start = from.current;
    from.current = value;
    if (reducedMotion || start == null || start === value) { setShown(value); return; }
    const t0 = performance.now(), dur = 650;
    let raf = 0;
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / dur);
      const e = 1 - Math.pow(1 - k, 3);
      setShown(start + (value - start) * e);
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value, reducedMotion]);
  return <span className={`num ${className}`}>{shown == null ? "—" : format(shown)}</span>;
}
