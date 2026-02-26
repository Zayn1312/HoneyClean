import { useEffect, useRef, useState } from "react";

interface Point {
  x: number;
  y: number;
  alpha: number;
}

export function HoneyCursor() {
  const [pos, setPos] = useState({ x: -100, y: -100 });
  const lerpPos = useRef({ x: -100, y: -100 });
  const trail = useRef<Point[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      setPos({ x: e.clientX, y: e.clientY });
      trail.current.push({ x: e.clientX, y: e.clientY, alpha: 1 });
      if (trail.current.length > 12) trail.current.shift();
    };

    window.addEventListener("mousemove", handleMove, { passive: true });
    document.body.style.cursor = "none";

    return () => {
      window.removeEventListener("mousemove", handleMove);
      document.body.style.cursor = "";
    };
  }, []);

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
    window.addEventListener("resize", resize);

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Lerp cursor position
      lerpPos.current.x += (pos.x - lerpPos.current.x) * 0.15;
      lerpPos.current.y += (pos.y - lerpPos.current.y) * 0.15;
      const { x, y } = lerpPos.current;

      // Draw trail
      for (const point of trail.current) {
        point.alpha *= 0.92;
        if (point.alpha > 0.02) {
          ctx.beginPath();
          ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(217, 163, 60, ${point.alpha * 0.5})`;
          ctx.fill();
        }
      }
      trail.current = trail.current.filter((p) => p.alpha > 0.02);

      // Inner circle
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(217, 163, 60, 0.9)";
      ctx.fill();

      // Outer ring
      ctx.beginPath();
      ctx.arc(x, y, 16, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(217, 163, 60, 0.3)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [pos]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 9999 }}
    />
  );
}
