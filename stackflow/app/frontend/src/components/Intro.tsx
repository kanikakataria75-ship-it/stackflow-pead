/* DRIFT intro — "from one filing to the whole market".
   0.0s  darkness; a single amber point ignites (an earnings filing)
   0.6s  thousands of particles spiral out of it: a galaxy, drifting with differential rotation
   2.4s  the galaxy collapses onto a sphere — the Observatory's shell — and neon rings draw in
   3.3s  the wordmark assembles from blur and wide tracking; an amber rule sweeps beneath it
   5.2s  the camera dives through the globe; the overlay dissolves into the home screen
   Skippable (click / any key). Plays once per session. Never shown under prefers-reduced-motion. */
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import { motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

const N = 3200;
const TOTAL = 6.6;
const R = 10;
const AMBER = new THREE.Color("#e8963c"), BONE = new THREE.Color("#ece5d8"), NEON = new THREE.Color("#6ec8ff");
const ease = (k: number) => (k <= 0 ? 0 : k >= 1 ? 1 : k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
const seg = (t: number, a: number, b: number) => clamp01((t - a) / (b - a));

function dotTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d")!;
  const grd = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grd.addColorStop(0, "rgba(255,255,255,1)");
  grd.addColorStop(0.25, "rgba(255,255,255,0.8)");
  grd.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grd;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

function Field({ t }: { t: React.RefObject<number> }) {
  const pts = useRef<THREE.Points>(null!);
  const core = useRef<THREE.Mesh>(null!);
  const { camera } = useThree();
  const data = useMemo(() => {
    const galaxy = new Float32Array(N * 3), sphere = new Float32Array(N * 3), col = new Float32Array(N * 3);
    const arm = new Float32Array(N), rad = new Float32Array(N), jit = new Float32Array(N);
    const c = new THREE.Color();
    for (let i = 0; i < N; i++) {
      // galaxy: 3 logarithmic arms plus a bulge
      const r = Math.pow(Math.random(), 0.7) * 16 + 0.3;
      const a = (i % 3) * ((Math.PI * 2) / 3) + r * 0.42 + (Math.random() - 0.5) * 0.55;
      rad[i] = r; arm[i] = a; jit[i] = (Math.random() - 0.5) * (1.4 - r / 20);
      galaxy.set([Math.cos(a) * r, jit[i], Math.sin(a) * r], i * 3);
      // sphere: fibonacci shell (the Observatory)
      const y = 1 - (2 * (i + 0.5)) / N, rr = Math.sqrt(1 - y * y), th = Math.PI * (3 - Math.sqrt(5)) * i;
      sphere.set([Math.cos(th) * rr * R, y * R, Math.sin(th) * rr * R], i * 3);
      const amberish = Math.random() < 0.09;
      c.copy(amberish ? AMBER : BONE).lerp(NEON, amberish ? 0 : Math.random() * 0.45);
      col.set([c.r, c.g, c.b], i * 3);
    }
    return { galaxy, sphere, col, arm, rad, jit };
  }, []);
  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
    g.setAttribute("color", new THREE.BufferAttribute(data.col, 3));
    return g;
  }, [data]);
  const tex = useMemo(dotTexture, []);

  useFrame(() => {
    const T = t.current;
    const spawn = ease(seg(T, 0.5, 2.2));          // galaxy unfurls from the ignition point
    const morph = ease(seg(T, 2.3, 3.8));          // galaxy -> sphere
    const spin = T * 0.35;
    const p = geo.attributes.position.array as Float32Array;
    for (let i = 0; i < N; i++) {
      const r = data.rad[i] * spawn;
      const a = data.arm[i] + spin * (1.6 - data.rad[i] / 16);   // differential rotation = drift
      const gx = Math.cos(a) * r, gz = Math.sin(a) * r, gy = data.jit[i] * spawn;
      // the sphere turns slowly as it forms
      const sx = data.sphere[i * 3], sy = data.sphere[i * 3 + 1], sz = data.sphere[i * 3 + 2];
      const ca = Math.cos(spin * 0.5), sa = Math.sin(spin * 0.5);
      const rx = sx * ca - sz * sa, rz = sx * sa + sz * ca;
      const lag = clamp01(morph * 1.25 - (data.rad[i] / 16) * 0.25);            // inner stars arrive first
      p[i * 3] = gx + (rx - gx) * lag;
      p[i * 3 + 1] = gy + (sy - gy) * lag;
      p[i * 3 + 2] = gz + (rz - gz) * lag;
    }
    geo.attributes.position.needsUpdate = true;
    const m = pts.current.material as THREE.PointsMaterial;
    m.opacity = seg(T, 0.45, 1.0) * (1 - seg(T, 5.6, 6.4));
    m.size = 0.3 - 0.08 * morph;
    // ignition core
    const ig = seg(T, 0.05, 0.45) * (1 - seg(T, 1.1, 2.0));
    core.current.scale.setScalar(0.05 + ig * (0.5 + 0.12 * Math.sin(T * 18)));
    (core.current.material as THREE.MeshBasicMaterial).opacity = ig;
    // camera: tilted galaxy view -> level view of the globe -> dive through it
    const tilt = 1 - morph;
    const dive = ease(seg(T, 5.0, 6.5));
    const dist = 38 - 6 * morph - 30 * dive;
    camera.position.set(Math.sin(T * 0.12) * 4, 3 + 22 * tilt - 3 * dive, dist);
    camera.lookAt(0, 0, 0);
  });

  return (
    <>
      <points ref={pts} geometry={geo}>
        <pointsMaterial vertexColors map={tex} transparent depthWrite={false} blending={THREE.AdditiveBlending} sizeAttenuation toneMapped={false} />
      </points>
      <mesh ref={core}>
        <sphereGeometry args={[1, 24, 24]} />
        <meshBasicMaterial color={AMBER} transparent blending={THREE.AdditiveBlending} toneMapped={false} />
      </mesh>
    </>
  );
}

/** Neon latitude rings that draw themselves in as the sphere forms. */
function Rings({ t }: { t: React.RefObject<number> }) {
  const lines = useMemo(() => [-60, -30, 0, 30, 60].map((lat) => {
    const y = Math.sin((lat * Math.PI) / 180) * R, r = Math.cos((lat * Math.PI) / 180) * R;
    return Array.from({ length: 161 }, (_, i) => new THREE.Vector3(Math.cos((i / 160) * Math.PI * 2) * r, y, Math.sin((i / 160) * Math.PI * 2) * r));
  }), []);
  const refs = useRef<({ material: THREE.Material & { opacity: number; dashOffset: number } } | null)[]>([]);
  useFrame(() => {
    const T = t.current;
    refs.current.forEach((l, i) => {
      if (!l) return;
      const k = ease(seg(T, 2.9 + i * 0.12, 4.0 + i * 0.12));
      l.material.opacity = k * (1 - seg(T, 5.4, 6.2)) * (i % 2 === 0 ? 0.9 : 0.5);
      l.material.dashOffset = 70 * (1 - k);       // visible arc = first 70k units: the ring "draws" itself
    });
  });
  return (
    <group>
      {lines.map((p, i) => (
        <Line key={i} ref={(el) => { refs.current[i] = el as never; }} points={p} color={i === 2 ? "#d6f1ff" : "#6ec8ff"}
          lineWidth={i === 2 ? 2.2 : 1.3} dashed dashSize={70} gapSize={70} transparent opacity={0}
          blending={THREE.AdditiveBlending} depthWrite={false} toneMapped={false} />
      ))}
    </group>
  );
}

// dev aid: ?introAt=3.4 freezes the intro at that second (used to review each act)
const FREEZE = Number(new URLSearchParams(window.location.search).get("introAt") ?? NaN);

function Clock({ t, onEnd }: { t: React.RefObject<number>; onEnd: () => void }) {
  const done = useRef(false);
  useFrame((_, dt) => {
    if (Number.isFinite(FREEZE)) { t.current = FREEZE; return; }
    t.current += Math.min(dt, 1 / 20);
    if (!done.current && t.current >= TOTAL) { done.current = true; onEnd(); }
  });
  return null;
}

export default function Intro({ onDone }: { onDone: () => void }) {
  const t = useRef(0);
  const [leaving, setLeaving] = useState(false);
  const [phase, setPhase] = useState(0);
  const finish = useRef(() => {});
  finish.current = () => { if (!leaving) { setLeaving(true); setTimeout(onDone, 650); } };

  useEffect(() => {
    const k = () => finish.current();
    window.addEventListener("keydown", k);
    if (Number.isFinite(FREEZE)) { setPhase(FREEZE >= 4.3 ? 2 : FREEZE >= 3.3 ? 1 : 0); return () => window.removeEventListener("keydown", k); }
    const timers = [setTimeout(() => setPhase(1), 3300), setTimeout(() => setPhase(2), 4300)];
    return () => { window.removeEventListener("keydown", k); timers.forEach(clearTimeout); };
  }, []);

  const letters = "DRIFT".split("");
  return (
    <motion.div className="intro" onClick={() => finish.current()} role="presentation"
      initial={{ opacity: 1 }} animate={{ opacity: leaving ? 0 : 1 }} transition={{ duration: 0.6, ease: "easeInOut" }}>
      <Canvas dpr={[1, 1.75]} camera={{ position: [0, 25, 38], fov: 42 }} gl={{ antialias: true }}>
        <color attach="background" args={["#0d0c0a"]} />
        <Clock t={t} onEnd={() => finish.current()} />
        <Field t={t} />
        <Rings t={t} />
      </Canvas>
      <div className="intro__mark" aria-label="DRIFT">
        <div className="intro__word">
          {letters.map((ch, i) => (
            <motion.span key={i}
              initial={{ opacity: 0, filter: "blur(14px)", y: 18, letterSpacing: "0.9em" }}
              animate={phase >= 1 ? { opacity: 1, filter: "blur(0px)", y: 0, letterSpacing: "0.06em" } : {}}
              transition={{ duration: 1.1, delay: i * 0.09, ease: [0.16, 1, 0.3, 1] }}>{ch}</motion.span>
          ))}
        </div>
        <motion.div className="intro__rule" initial={{ scaleX: 0 }} animate={phase >= 1 ? { scaleX: 1 } : {}}
          transition={{ duration: 1.2, delay: 0.5, ease: [0.65, 0, 0.35, 1] }} />
        <motion.div className="intro__sub" initial={{ opacity: 0, y: 8 }} animate={phase >= 2 ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}>
          StackFlow Forward Scanner · PEAD V2
        </motion.div>
        <motion.div className="intro__badge" initial={{ opacity: 0 }} animate={phase >= 2 ? { opacity: 1 } : {}} transition={{ duration: 0.8, delay: 0.3 }}>
          Forward-test candidate
        </motion.div>
      </div>
      <button className="intro__skip" onClick={(e) => { e.stopPropagation(); finish.current(); }}>Skip intro ↵</button>
    </motion.div>
  );
}
