import type { Signal, UniversePoint } from "../api";
import { num } from "./format";

export const R = 10;                       // shell radius
type V3 = [number, number, number];

export interface Node {
  p: UniversePoint;
  dir: V3;                                 // unit direction on the shell
  pos: V3;                                 // rendered position (radius encodes SUE for forward filings)
  sue: number | null;
  q: number | null;
  forward: Signal | null;                  // forward filing visible at the current as-of date
}
export interface SectorInfo { name: string; dir: V3; count: number; nodes: number[] }

const norm = (v: V3): V3 => { const l = Math.hypot(...v) || 1; return [v[0] / l, v[1] / l, v[2] / l]; };
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

function fib(i: number, n: number): V3 {
  const y = 1 - (2 * (i + 0.5)) / n;
  const r = Math.sqrt(1 - y * y);
  const th = Math.PI * (3 - Math.sqrt(5)) * i;
  return [Math.cos(th) * r, y * 0.74, Math.sin(th) * r];
}

/** Radial offset for a SUE value: outward for beats, inward for misses, clamped. */
export const sueHeight = (sue: number) => Math.max(-3, Math.min(6, sue)) * 0.42;

export function layout(points: UniversePoint[], asOf: string | null): { nodes: Node[]; sectors: SectorInfo[] } {
  const bySector = new Map<string, UniversePoint[]>();
  for (const p of [...points].sort((a, b) => a.symbol.localeCompare(b.symbol))) {
    const k = p.sector || "Unclassified";
    if (!bySector.has(k)) bySector.set(k, []);
    bySector.get(k)!.push(p);
  }
  const names = [...bySector.keys()].sort((a, b) => bySector.get(b)!.length - bySector.get(a)!.length);
  const nodes: Node[] = [];
  const sectors: SectorInfo[] = [];
  names.forEach((name, si) => {
    const c = norm(fib(si, names.length));
    const up: V3 = Math.abs(c[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0];
    const u = norm(cross(c, up));
    const v = norm(cross(c, u));
    const members = bySector.get(name)!;
    const spread = 0.07 + 0.028 * Math.sqrt(members.length);
    const idx: number[] = [];
    members.forEach((p, k) => {
      const a = k * 2.39996, rr = spread * Math.sqrt((k + 0.5) / members.length);
      const d = norm([c[0] + (u[0] * Math.cos(a) + v[0] * Math.sin(a)) * rr,
                      c[1] + (u[1] * Math.cos(a) + v[1] * Math.sin(a)) * rr,
                      c[2] + (u[2] * Math.cos(a) + v[2] * Math.sin(a)) * rr]);
      const f = p.forward && (!asOf || p.forward.filing_timestamp.slice(0, 10) <= asOf) ? p.forward : null;
      const sue = f ? num(f.sue) : null;
      const q = f ? num(f.quintile) : null;
      const rad = R + (sue != null ? sueHeight(sue) : 0);
      idx.push(nodes.length);
      nodes.push({ p, dir: d, pos: [d[0] * rad, d[1] * rad, d[2] * rad], sue, q, forward: f });
    });
    sectors.push({ name, dir: c, count: members.length, nodes: idx });
  });
  return { nodes, sectors };
}

export function holdingProgress(entry: string, exit: string, asOf: string | null): number {
  const a = new Date(entry).getTime(), b = new Date(exit).getTime();
  const t = asOf ? new Date(asOf).getTime() : Date.now();
  if (!(b > a)) return 0;
  return Math.max(0, Math.min(1, (t - a) / (b - a)));
}
