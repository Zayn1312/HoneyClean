import { useEffect, useRef } from "react";

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

interface TrailPoint {
  x: number;
  y: number;
  time: number;
}

export function HoneyCursor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouse = useRef({ x: -100, y: -100 });
  const ringPos = useRef({ x: -100, y: -100 });
  const trail = useRef<TrailPoint[]>([]);
  const hovering = useRef(false);
  const clicking = useRef(false);
  const clickScale = useRef(1);
  const rafRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();

    const onMove = (e: MouseEvent) => {
      mouse.current = { x: e.clientX, y: e.clientY };
      trail.current.push({ x: e.clientX, y: e.clientY, time: Date.now() });
      if (trail.current.length > 8) trail.current.shift();
    };

    const onDown = () => {
      clicking.current = true;
      clickScale.current = 0.7;
    };

    const onUp = () => {
      clicking.current = false;
    };

    const checkHover = (e: MouseEvent) => {
      const el = document.elementFromPoint(e.clientX, e.clientY);
      if (!el) { hovering.current = false; return; }
      const tag = el.tagName.toLowerCase();
      hovering.current = tag === "button" || tag === "a" ||
        el.closest("button") !== null || el.closest("a") !== null ||
        el.getAttribute("role") === "button" ||
        getComputedStyle(el).cursor === "pointer";
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("mousemove", checkHover, { passive: true });
    window.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("resize", resize);

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const { x: mx, y: my } = mouse.current;

      // Ring lerps to mouse with lag
      ringPos.current.x = lerp(ringPos.current.x, mx, 0.12);
      ringPos.current.y = lerp(ringPos.current.y, my, 0.12);
      const rx = ringPos.current.x;
      const ry = ringPos.current.y;

      // Click scale spring back
      clickScale.current = lerp(clickScale.current, 1, 0.15);

      const now = Date.now();

      // Draw trail — last 8 positions, fading over 400ms
      for (const point of trail.current) {
        const age = now - point.time;
        if (age > 400) continue;
        const alpha = (1 - age / 400) * 0.3;
        ctx.beginPath();
        ctx.arc(point.x, point.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(217, 163, 60, ${alpha})`;
        ctx.fill();
      }
      trail.current = trail.current.filter((p) => now - p.time < 400);

      // Inner dot — follows mouse exactly, 6px diameter
      ctx.beginPath();
      ctx.arc(mx, my, 3, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(217, 163, 60, 0.9)";
      ctx.fill();

      // Outer ring — 24px diameter, lerped, with hover/click effects
      const hoverScale = hovering.current ? 1.8 : 1;
      const scale = hoverScale * clickScale.current;
      const ringRadius = 12 * scale;

      ctx.beginPath();
      ctx.arc(rx, ry, ringRadius, 0, Math.PI * 2);

      if (hovering.current) {
        // Fill with 30% amber on hover
        ctx.fillStyle = "rgba(217, 163, 60, 0.15)";
        ctx.fill();
      }

      ctx.strokeStyle = "rgba(217, 163, 60, 0.4)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mousemove", checkHover);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 99999 }}
    />
  );
}
