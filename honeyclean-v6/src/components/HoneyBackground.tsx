import { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

const vertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = `
  uniform float uTime;
  uniform vec2 uMouse;
  uniform vec2 uResolution;
  varying vec2 vUv;

  // Simplex noise helper
  vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

  float snoise(vec2 v) {
    const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                       -0.577350269189626, 0.024390243902439);
    vec2 i = floor(v + dot(v, C.yy));
    vec2 x0 = v - i + dot(i, C.xx);
    vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod289(i);
    vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
    vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
    m = m * m; m = m * m;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
    vec3 g;
    g.x = a0.x * x0.x + h.x * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
  }

  void main() {
    vec2 uv = vUv;
    float aspect = uResolution.x / uResolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    // Mouse influence
    vec2 mouse = (uMouse - 0.5) * vec2(aspect, 1.0);
    float mouseDist = length(p - mouse);
    float mouseInfluence = smoothstep(0.5, 0.0, mouseDist) * 0.15;

    // Layered noise for fluid effect
    float t = uTime * 0.08;
    float n1 = snoise(p * 2.0 + t) * 0.5;
    float n2 = snoise(p * 4.0 - t * 0.7) * 0.25;
    float n3 = snoise(p * 8.0 + t * 0.3) * 0.125;
    float noise = n1 + n2 + n3 + mouseInfluence;

    // Dark amber palette
    vec3 dark = vec3(0.04, 0.03, 0.02);       // Near black
    vec3 amber = vec3(0.15, 0.08, 0.02);       // Deep amber
    vec3 highlight = vec3(0.25, 0.15, 0.04);   // Warm highlight

    vec3 color = mix(dark, amber, noise * 0.5 + 0.5);
    color = mix(color, highlight, max(0.0, noise - 0.3) * 0.5);

    // Vignette
    float vignette = 1.0 - length(uv - 0.5) * 0.8;
    color *= vignette;

    gl_FragColor = vec4(color, 1.0);
  }
`;

function FluidPlane() {
  const meshRef = useRef<THREE.Mesh>(null);
  const mouseRef = useRef(new THREE.Vector2(0.5, 0.5));
  const { viewport } = useThree();

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(0.5, 0.5) },
      uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
    }),
    []
  );

  useFrame(({ clock }) => {
    uniforms.uTime.value = clock.getElapsedTime();
    uniforms.uMouse.value.lerp(mouseRef.current, 0.05);
  });

  // Track mouse
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      mouseRef.current.set(e.clientX / window.innerWidth, 1 - e.clientY / window.innerHeight);
    };
    window.addEventListener("mousemove", handler, { passive: true });
    return () => window.removeEventListener("mousemove", handler);
  }, []);

  return (
    <mesh ref={meshRef} position={[0, 0, 0]}>
      <planeGeometry args={[viewport.width, viewport.height]} />
      <shaderMaterial
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
      />
    </mesh>
  );
}

export function HoneyBackground() {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas
        gl={{ antialias: false, powerPreference: "low-power" }}
        camera={{ position: [0, 0, 1] }}
        frameloop="always"
        dpr={[1, 1.5]}
      >
        <FluidPlane />
      </Canvas>
    </div>
  );
}
