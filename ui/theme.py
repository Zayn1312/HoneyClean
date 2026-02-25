"""
HoneyClean – Theme constants and FX helpers
"""

import math
import random

# ── Colors ───────────────────────────────────────────────────────
C = {
    "bg": "#000000", "sidebar": "#0A0A0A", "card": "#0F0F0F",
    "card_hover": "#161616", "border": "#1A1400", "border_bright": "#4A3500",
    "accent": "#F5A800", "accent_hover": "#FFD000", "accent_dim": "#8A5E00",
    "accent_glow": "#FF8C00", "text": "#FFFFFF", "text_muted": "#A07820",
    "text_dim": "#3A2800", "success": "#4ADE80", "warning": "#F5A800",
    "error": "#EF4444", "console_bg": "#000000", "console_text": "#F5A800",
    "smoke": "#1A1A1A", "honey_drip": "#F5A800", "hex_pattern": "#0D0D00",
}
FONT = "Segoe UI"

# ── Honeycomb Drawing ────────────────────────────────────────────
def draw_honeycomb(canvas, width, height, radius=30, color="#0D0D00"):
    dx = radius * 1.5
    dy = radius * math.sqrt(3)
    row = 0
    y = 0
    while y < height + dy:
        x = dx if row % 2 else 0
        while x < width + dx:
            pts = []
            for a in range(6):
                ang = math.radians(60 * a + 30)
                pts.extend([x + radius * math.cos(ang), y + radius * math.sin(ang)])
            canvas.create_polygon(pts, outline=color, fill="", width=1, tags="hex")
            x += dx * 2
        y += dy / 2
        row += 1

# ── Particle Effect Helpers ──────────────────────────────────────
_FX_MAX_PARTICLES = 120

def _blend_hex(color, alpha, bg="#000000"):
    """Blend *color* toward *bg* by *alpha* (0=invisible, 1=full color)."""
    cr, cg, cb = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    br, bg_, bb = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
    a = max(0.0, min(1.0, alpha))
    r = int(br + (cr - br) * a)
    g = int(bg_ + (cg - bg_) * a)
    b = int(bb + (cb - bb) * a)
    return f"#{r:02x}{g:02x}{b:02x}"

def _make_smoke(w, h):
    """Create a smoke particle dict spawning near the bottom."""
    return {
        "type": "smoke",
        "x": random.uniform(0, w),
        "y": random.uniform(h * 0.85, h + 20),
        "vx": random.uniform(-0.3, 0.3),
        "vy": random.uniform(-0.6, -0.25),
        "r": random.uniform(10, 22),
        "r0": 0,
        "age": 0,
        "life": random.randint(80, 160),
    }

def _make_drip(w, h):
    """Create a honey drip particle dict spawning near the top."""
    return {
        "type": "drip",
        "x": random.uniform(w * 0.05, w * 0.95),
        "y": random.uniform(-10, h * 0.08),
        "vx": random.uniform(-0.15, 0.15),
        "vy": random.uniform(0.3, 0.7),
        "r": random.uniform(3, 6),
        "age": 0,
        "life": random.randint(120, 220),
    }
