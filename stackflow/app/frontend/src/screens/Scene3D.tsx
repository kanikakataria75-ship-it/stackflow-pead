/* Lazy-loaded: the only module that pulls in three / R3F / drei for the Observatory. */
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import { Billboard, Line, OrbitControls, Ring } from "@react-three/drei";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitImpl } from "three-stdlib";
import { COLORS, qColor } from "../lib/format";
import { R, holdingProgress, type Node, type SectorInfo } from "../lib/layout";

interface Props {
  nodes: Node[]; sectors: SectorInfo[]; asOf: string | null; reducedMotion: boolean;
  arrivals: string[];                         // symbols whose filing is new since the last refresh
  focus: string | null; onHover: (n: Node | null, x: number, y: number) => void;
}

const tmp = new THREE.Object3D();
const col = new THREE.Color();

const NEON = "#6ec8ff";        // icy steel-cyan: the benchmark hue pushed to luminous
const NEON_CORE = "#d6f1ff";
const ADD = { blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false, transparent: true } as const;

function ringPoints(): THREE.Vector3[][] {
  const out: THREE.Vector3[][] = [];
  for (const lat of [-60, -30, 0, 30, 60]) {
    const pts: THREE.Vector3[] = [];
    const y = Math.sin((lat * Math.PI) / 180) * R * 0.99, r = Math.cos((lat * Math.PI) / 180) * R * 0.99;
    for (let i = 0; i <= 160; i++) { const a = (i / 160) * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(a) * r, y, Math.sin(a) * r)); }
    out.push(pts);
  }
  for (let m = 0; m < 6; m++) {
    const pts: THREE.Vector3[] = [], a0 = (m / 6) * Math.PI;
    for (let i = 0; i <= 160; i++) { const t = (i / 160) * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(t) * Math.cos(a0) * R * 0.99, Math.sin(t) * R * 0.99, Math.cos(t) * Math.sin(a0) * R * 0.99)); }
    out.push(pts);
  }
  return out;
}

/** Soft atmospheric rim: a back-faced fresnel shell, brightest at the silhouette. */
function Atmosphere() {
  const mat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: { c: { value: new THREE.Color(NEON) }, t: { value: 0 } },
    vertexShader: `varying vec3 vN; varying vec3 vV;
      void main(){ vec4 mv = modelViewMatrix*vec4(position,1.0); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }`,
    // back faces: d = 0 at the halo's outer edge, ~0.5 at the globe's silhouette, 1 at the centre.
    // Bright ring at the silhouette, fading outward into space and inward to nothing.
    fragmentShader: `uniform vec3 c; uniform float t; varying vec3 vN; varying vec3 vV;
      void main(){ float d = -dot(vN, vV);
        float k = d > 0.5 ? pow(max(0.0, (1.0 - d) / 0.5), 6.0) : pow(max(0.0, d / 0.5), 1.8);
        float pulse = 0.88 + 0.12*sin(t*0.6);
        gl_FragColor = vec4(c, k * 0.42 * pulse); }`,
    side: THREE.BackSide, ...ADD,
  }), []);
  useFrame((_, dt) => { mat.uniforms.t.value += dt; });
  return <mesh material={mat}><sphereGeometry args={[R * 1.16, 64, 64]} /></mesh>;
}

function Shell({ reducedMotion }: { reducedMotion: boolean }) {
  const lines = useMemo(ringPoints, []);
  const flows = useRef<({ material: { dashOffset: number } } | null)[]>([]);
  useFrame((_, dt) => {
    if (reducedMotion) return;
    flows.current.forEach((l, i) => { if (l) l.material.dashOffset -= dt * (0.9 + (i % 3) * 0.35) * (i % 2 ? -1 : 1); });
  });
  return (
    <group>
      {lines.map((p, i) => {
        const eq = i === 2;
        return (
          <group key={i}>
            <Line points={p} color={NEON} lineWidth={eq ? 8 : 5} opacity={eq ? 0.045 : 0.022} {...ADD} />
            <Line points={p} color={NEON} lineWidth={eq ? 2.6 : 1.8} opacity={eq ? 0.13 : 0.065} {...ADD} />
            <Line points={p} color={NEON_CORE} lineWidth={0.9} opacity={eq ? 0.42 : 0.2} {...ADD} />
          </group>
        );
      })}
      {/* light that drifts around the equator and three meridians */}
      {[2, 5, 7, 9].map((idx, k) => (
        <Line key={`f${idx}`} ref={(el) => { flows.current[k] = el as never; }} points={lines[idx]} color={NEON_CORE}
          lineWidth={2} dashed dashSize={2.6} gapSize={16 + k * 4} dashScale={1} opacity={0.75} {...ADD} />
      ))}
      <Atmosphere />
    </group>
  );
}

function Points({ nodes, onHover }: { nodes: Node[]; onHover: Props["onHover"] }) {
  const solid = useMemo(() => nodes.map((n, i) => ({ n, i })).filter((x) => !x.n.p.is_fin), [nodes]);
  const hollow = useMemo(() => nodes.map((n, i) => ({ n, i })).filter((x) => x.n.p.is_fin), [nodes]);
  const sRef = useRef<THREE.InstancedMesh>(null!);
  const hRef = useRef<THREE.InstancedMesh>(null!);

  useLayoutEffect(() => {
    solid.forEach(({ n }, k) => {
      const s = n.forward ? 0.16 + Math.min(Math.abs(n.sue ?? 0), 4) * 0.025 : 0.085;
      tmp.position.set(...n.pos); tmp.scale.setScalar(s); tmp.updateMatrix();
      sRef.current.setMatrixAt(k, tmp.matrix);
      sRef.current.setColorAt(k, col.set(n.forward ? qColor(n.q) : "#6f695f"));
    });
    sRef.current.instanceMatrix.needsUpdate = true;
    if (sRef.current.instanceColor) sRef.current.instanceColor.needsUpdate = true;
    hollow.forEach(({ n }, k) => {
      tmp.position.set(...n.pos);
      tmp.lookAt(n.pos[0] * 2, n.pos[1] * 2, n.pos[2] * 2);        // ring faces outward: visibly hollow
      tmp.scale.setScalar(n.forward ? 1.5 : 1); tmp.updateMatrix();
      hRef.current.setMatrixAt(k, tmp.matrix);
      hRef.current.setColorAt(k, col.set(n.forward ? qColor(n.q) : "#8d867a"));
    });
    hRef.current.instanceMatrix.needsUpdate = true;
    if (hRef.current.instanceColor) hRef.current.instanceColor.needsUpdate = true;
  }, [solid, hollow]);

  const hover = (list: { n: Node }[]) => (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    if (e.instanceId != null) onHover(list[e.instanceId].n, e.nativeEvent.clientX, e.nativeEvent.clientY);
  };
  return (
    <>
      <instancedMesh ref={sRef} args={[undefined, undefined, solid.length]} onPointerMove={hover(solid)} onPointerOut={() => onHover(null, 0, 0)}>
        <sphereGeometry args={[1, 12, 12]} />
        <meshBasicMaterial toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={hRef} args={[undefined, undefined, hollow.length]} onPointerMove={hover(hollow)} onPointerOut={() => onHover(null, 0, 0)}>
        <ringGeometry args={[0.075, 0.11, 24]} />
        <meshBasicMaterial toneMapped={false} side={THREE.DoubleSide} />
      </instancedMesh>
    </>
  );
}

/** Radial stalks from the shell to each forward filing: the height IS the SUE. */
function Stalks({ nodes }: { nodes: Node[] }) {
  const geo = useMemo(() => {
    const f = nodes.filter((n) => n.forward && n.sue != null);
    const pos = new Float32Array(f.length * 6), c = new Float32Array(f.length * 6);
    f.forEach((n, i) => {
      pos.set([n.dir[0] * R, n.dir[1] * R, n.dir[2] * R, ...n.pos], i * 6);
      col.set(qColor(n.q)); c.set([col.r, col.g, col.b, col.r, col.g, col.b], i * 6);
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(c, 3));
    return g;
  }, [nodes]);
  return <lineSegments geometry={geo}><lineBasicMaterial vertexColors transparent opacity={0.55} toneMapped={false} /></lineSegments>;
}

/** Open positions: a soft halo and a watch-complication ring that fills clockwise over 60 sessions. */
function Holdings({ nodes, asOf }: { nodes: Node[]; asOf: string | null }) {
  const held = nodes.filter((n) => n.p.position);
  return (
    <>
      {held.map((n) => {
        const pos = n.p.position!;
        // sessions held (from the backend) is exact; the calendar fraction is used only when scrubbing
        const k = !asOf && pos.sessions_held != null ? pos.sessions_held / 60 : holdingProgress(pos.entry_date, pos.exit_date, asOf);
        return (
          <group key={n.p.symbol} position={n.pos}>
            <mesh><sphereGeometry args={[0.34, 16, 16]} /><meshBasicMaterial color={COLORS.amber} transparent opacity={0.13} toneMapped={false} depthWrite={false} /></mesh>
            <Billboard>
              <Ring args={[0.42, 0.455, 64]}><meshBasicMaterial color={COLORS.bone} transparent opacity={0.16} toneMapped={false} /></Ring>
              {/* thetaStart at 12 o'clock, negative length -> fills clockwise */}
              <Ring args={[0.42, 0.455, 64, 1, Math.PI / 2, -Math.max(0.001, k) * Math.PI * 2]}>
                <meshBasicMaterial color={COLORS.amber} toneMapped={false} side={THREE.DoubleSide} />
              </Ring>
            </Billboard>
          </group>
        );
      })}
    </>
  );
}

/** A new filing travels in from the edge of the field and settles onto its stock. */
function Arrivals({ nodes, symbols }: { nodes: Node[]; symbols: string[] }) {
  const targets = useMemo(() => symbols.map((s) => nodes.find((n) => n.p.symbol === s)).filter(Boolean) as Node[], [nodes, symbols]);
  const refs = useRef<(THREE.Mesh | null)[]>([]);
  const t0 = useRef(performance.now());
  useEffect(() => { t0.current = performance.now(); }, [symbols]);
  useFrame(() => {
    const now = performance.now();
    targets.forEach((n, i) => {
      const m = refs.current[i];
      if (!m) return;
      const k = Math.min(1, Math.max(0, (now - t0.current - i * 140) / 1700));
      const e = 1 - Math.pow(1 - k, 3);
      const from = new THREE.Vector3(...n.dir).multiplyScalar(R * 2.8).add(new THREE.Vector3(0, 6 * (1 - e), 0));
      m.position.copy(from.lerp(new THREE.Vector3(...n.pos), e));
      m.visible = k > 0 && k < 1;
      (m.material as THREE.MeshBasicMaterial).opacity = 0.35 + 0.65 * e;
    });
  });
  return (
    <>
      {targets.map((n, i) => (
        <mesh key={n.p.symbol} ref={(el) => { refs.current[i] = el; }} visible={false}>
          <sphereGeometry args={[0.13, 10, 10]} />
          <meshBasicMaterial color={qColor(n.q)} transparent toneMapped={false} />
        </mesh>
      ))}
    </>
  );
}

/** Leader lines live in 3D; the label text lives in a plain DOM overlay (no extra React roots).
 *  Each frame the anchor is projected to screen space and labels on the far hemisphere fade out. */
function LabelProjector({ sectors, labels }: { sectors: SectorInfo[]; labels: React.RefObject<(HTMLButtonElement | null)[]> }) {
  const lines = useRef<(THREE.Group | null)[]>([]);
  const cam = useMemo(() => new THREE.Vector3(), []);
  const v = useMemo(() => new THREE.Vector3(), []);
  const geo = useMemo(() => sectors.map((s) => ({
    dir: new THREE.Vector3(...s.dir),
    a: [s.dir[0] * R * 1.03, s.dir[1] * R * 1.03, s.dir[2] * R * 1.03] as [number, number, number],
    b: new THREE.Vector3(s.dir[0] * R * 1.3, s.dir[1] * R * 1.3 + 0.4, s.dir[2] * R * 1.3),
  })), [sectors]);
  useFrame(({ camera, size }) => {
    cam.copy(camera.position).normalize();
    geo.forEach((g, i) => {
      const o = THREE.MathUtils.clamp((cam.dot(g.dir) + 0.15) / 0.35, 0, 1);
      const el = labels.current?.[i];
      if (el) {
        v.copy(g.b).project(camera);
        el.style.transform = `translate(${((v.x + 1) / 2) * size.width + 4}px, ${((1 - v.y) / 2) * size.height}px) translateY(-50%)`;
        el.style.opacity = String(o);
        el.style.pointerEvents = o > 0.3 ? "auto" : "none";
      }
      const ln = lines.current[i];
      if (ln) ln.visible = o > 0.05;
    });
  });
  return (
    <>
      {geo.map((g, i) => (
        <group key={sectors[i].name} ref={(el) => { lines.current[i] = el; }}>
          <Line points={[g.a, [g.b.x, g.b.y, g.b.z]]} color={COLORS.bone} transparent opacity={0.22} lineWidth={1} />
        </group>
      ))}
    </>
  );
}

function Rig({ fly, idleRotate, controls }: { fly: THREE.Vector3 | null; idleRotate: boolean; controls: React.RefObject<OrbitImpl | null> }) {
  const { camera } = useThree();
  const dest = useRef<THREE.Vector3 | null>(null);
  useEffect(() => { dest.current = fly ? fly.clone() : null; }, [fly]);
  useFrame((_, dt) => {
    const c = controls.current;
    if (c) c.autoRotate = idleRotate && !dest.current;
    if (dest.current) {
      camera.position.lerp(dest.current, 1 - Math.pow(0.02, dt));
      if (camera.position.distanceTo(dest.current) < 0.05) dest.current = null;
    }
    c?.update();
  });
  return null;
}

export default function Scene3D({ nodes, sectors, asOf, reducedMotion, arrivals, focus, onHover }: Props) {
  const controls = useRef<OrbitImpl | null>(null);
  const [fly, setFly] = useState<THREE.Vector3 | null>(null);
  const [idle, setIdle] = useState(true);
  const idleTimer = useRef<number | undefined>(undefined);
  const dist = 33;
  const labelRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const [on, setOn] = useState<string | null>(null);

  useEffect(() => {
    if (!focus) return;
    const n = nodes.find((x) => x.p.symbol === focus);
    if (n) setFly(new THREE.Vector3(...n.dir).multiplyScalar(dist * 0.62));
  }, [focus, nodes]);

  const wake = () => {
    setIdle(false);
    window.clearTimeout(idleTimer.current);
    idleTimer.current = window.setTimeout(() => setIdle(true), 9000);
  };

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Canvas dpr={[1, 1.75]} camera={{ position: [0, 6, dist], fov: 40, near: 0.1, far: 200 }}
        gl={{ antialias: true, powerPreference: "high-performance" }} frameloop={reducedMotion ? "demand" : "always"}
        onPointerDown={wake} onWheel={wake}>
        <color attach="background" args={[COLORS.ink]} />
        <Shell reducedMotion={reducedMotion} />
        <Stalks nodes={nodes} />
        <Points nodes={nodes} onHover={onHover} />
        <Holdings nodes={nodes} asOf={asOf} />
        {!reducedMotion && arrivals.length > 0 && <Arrivals nodes={nodes} symbols={arrivals} />}
        <LabelProjector sectors={sectors} labels={labelRefs} />
        <OrbitControls ref={controls as never} enableDamping dampingFactor={0.06} enablePan={false}
          minDistance={13} maxDistance={52} autoRotateSpeed={0.28} makeDefault />
        <Rig fly={fly} idleRotate={idle && !reducedMotion} controls={controls} />
      </Canvas>
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "hidden" }}>
        {sectors.map((s, i) => (
          <button key={s.name} ref={(el) => { labelRefs.current[i] = el; }}
            className={`sector-label ${on === s.name ? "on" : ""}`}
            style={{ position: "absolute", left: 0, top: 0, opacity: 0, willChange: "transform" }}
            onClick={() => { setOn(s.name); wake(); setFly(new THREE.Vector3(...s.dir).multiplyScalar(dist * 0.7)); }}>
            {s.name} <span className="num">{s.count}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
