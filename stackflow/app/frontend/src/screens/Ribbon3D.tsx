/* 3D ribbon of the forward equity curve: x = time, y = NAV, ribbon width = positions held,
   colour = drawdown depth. A chart that carries two more variables than the 2D line. */
import { Canvas } from "@react-three/fiber";
import { Line, OrbitControls } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import type { PerfPoint } from "../api";
import { COLORS } from "../lib/format";

export default function Ribbon3D({ series }: { series: PerfPoint[] }) {
  const { geo, bench } = useMemo(() => {
    const n = series.length;
    const lo = Math.min(...series.map((d) => Math.min(d.nav, d.bench))), hi = Math.max(...series.map((d) => Math.max(d.nav, d.bench)));
    const X = (i: number) => (i / Math.max(1, n - 1)) * 20 - 10;
    const Y = (v: number) => ((v - lo) / Math.max(1e-9, hi - lo)) * 6 - 3;
    const pos = new Float32Array(n * 6), col = new Float32Array(n * 6), idx: number[] = [];
    const bone = new THREE.Color(COLORS.bone), red = new THREE.Color(COLORS.loss), c = new THREE.Color();
    const maxDD = Math.max(0.05, ...series.map((d) => -d.drawdown));
    series.forEach((d, i) => {
      const w = 0.08 + (d.positions / 30) * 1.6;
      pos.set([X(i), Y(d.nav), -w, X(i), Y(d.nav), w], i * 6);
      c.copy(bone).lerp(red, Math.min(1, -d.drawdown / maxDD));
      col.set([c.r, c.g, c.b, c.r, c.g, c.b], i * 6);
      if (i < n - 1) { const a = i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    g.setIndex(idx);
    return { geo: g, bench: series.map((d, i) => new THREE.Vector3(X(i), Y(d.bench), 0)) };
  }, [series]);
  return (
    <Canvas camera={{ position: [0, 5, 17], fov: 40 }} dpr={[1, 1.75]}>
      <color attach="background" args={[COLORS.ink]} />
      <mesh geometry={geo}><meshBasicMaterial vertexColors side={THREE.DoubleSide} toneMapped={false} /></mesh>
      <Line points={bench} color={COLORS.steel} lineWidth={1.5} />
      <gridHelper args={[22, 22, "#2a261f", "#221f1a"]} position={[0, -3.2, 0]} />
      <OrbitControls enableDamping enablePan={false} minDistance={8} maxDistance={30} />
    </Canvas>
  );
}
