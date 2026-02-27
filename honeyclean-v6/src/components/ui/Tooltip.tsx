import { useState, useRef, useCallback, useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface TooltipProps {
  content: string;
  detail?: string;
  delay?: number;
  position?: "top" | "bottom" | "left" | "right";
  children: ReactNode;
}

export function Tooltip({
  content,
  detail,
  delay = 600,
  position = "top",
  children,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const show = useCallback(() => {
    timerRef.current = setTimeout(() => {
      if (!triggerRef.current) return;
      const rect = triggerRef.current.getBoundingClientRect();
      const maxW = 260;
      let x = 0;
      let y = 0;

      if (position === "top") {
        x = rect.left + rect.width / 2;
        y = rect.top - 8;
      } else if (position === "bottom") {
        x = rect.left + rect.width / 2;
        y = rect.bottom + 8;
      } else if (position === "left") {
        x = rect.left - 8;
        y = rect.top + rect.height / 2;
      } else {
        x = rect.right + 8;
        y = rect.top + rect.height / 2;
      }

      // Viewport edge detection
      if (position === "top" || position === "bottom") {
        x = Math.max(maxW / 2 + 8, Math.min(window.innerWidth - maxW / 2 - 8, x));
      }
      if (position === "top" && y < 60) {
        y = rect.bottom + 8;
      }
      if (position === "bottom" && y > window.innerHeight - 60) {
        y = rect.top - 8;
      }

      setCoords({ x, y });
      setVisible(true);
    }, delay);
  }, [delay, position]);

  const hide = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setVisible(false);
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const isVertical = position === "top" || position === "bottom";
  const transformOrigin =
    position === "top" ? "center bottom" :
    position === "bottom" ? "center top" :
    position === "left" ? "right center" :
    "left center";

  const transform =
    isVertical
      ? "translate(-50%, 0)"
      : position === "left"
        ? "translate(-100%, -50%)"
        : "translate(0, -50%)";

  return (
    <div
      ref={triggerRef}
      onMouseEnter={show}
      onMouseLeave={hide}
      style={{ display: "contents" }}
    >
      {children}
      {visible && createPortal(
        <div
          style={{
            position: "fixed",
            left: coords.x,
            top: coords.y,
            transform,
            transformOrigin,
            zIndex: 100000,
            background: "rgba(10, 10, 20, 0.95)",
            border: "1px solid rgba(245, 158, 11, 0.2)",
            borderRadius: 8,
            padding: "8px 12px",
            maxWidth: 260,
            pointerEvents: "none",
            backdropFilter: "blur(8px)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            animation: "tooltip-fade-in 150ms ease",
          }}
        >
          <div style={{ fontSize: 13, color: "#F0F0FF", fontWeight: 500, marginBottom: detail ? 2 : 0 }}>
            {content}
          </div>
          {detail && (
            <div style={{ fontSize: 12, color: "#6060A0", lineHeight: 1.4 }}>
              {detail}
            </div>
          )}
        </div>,
        document.body
      )}
    </div>
  );
}
