"""
HoneyClean – Sidebar mixin
"""

import random
import subprocess
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from ui.theme import C, FONT, _FX_MAX_PARTICLES, _blend_hex, _make_smoke, _make_drip
from core.i18n import t
from core.config import VERSION


class SidebarMixin:

    def _build_sidebar(self):
        logo_row = ctk.CTkFrame(self._sidebar, fg_color="transparent", height=60)
        logo_row.pack(fill="x", padx=12, pady=(16, 8))
        self._sidebar_logo_img = None
        if self._logo_path:
            try:
                li = Image.open(self._logo_path).convert("RGBA")
                li.thumbnail((44, 44), Image.LANCZOS)
                self._sidebar_logo_img = ctk.CTkImage(light_image=li, dark_image=li, size=(44, 44))
                ctk.CTkLabel(logo_row, image=self._sidebar_logo_img, text="").pack(side="left", padx=(0, 8))
            except Exception:
                pass
        title_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        title_col.pack(side="left", fill="y")
        ctk.CTkLabel(title_col, text="HoneyClean", font=(FONT, 15, "bold"),
                     text_color=C["accent"]).pack(anchor="w")
        ctk.CTkLabel(title_col, text=f"v{VERSION}", font=(FONT, 9), text_color=C["text_muted"]).pack(anchor="w")

        self._nav_btns = {}
        for pid, icon, tkey in [("queue", "\U0001f4c1", "nav_queue"), ("editor", "\u270f\ufe0f", "nav_editor"),
                                 ("settings", "\u2699\ufe0f", "nav_settings"), ("about", "\u2139\ufe0f", "nav_about")]:
            btn = ctk.CTkButton(self._sidebar, text=f"  {icon}  {t(tkey)}", anchor="w", height=40,
                                corner_radius=8, font=(FONT, 12), fg_color="transparent",
                                hover_color=C["card_hover"], text_color=C["text_muted"], cursor="hand2",
                                command=lambda p=pid: self._show_page(p))
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns[pid] = btn

        self._provider_lbl = ctk.CTkLabel(self._sidebar, text=t("cpu_mode"), font=(FONT, 9), text_color=C["warning"])
        self._provider_lbl.pack(side="bottom", padx=12, pady=(0, 8), anchor="w")
        self._gpu_lbl = ctk.CTkLabel(self._sidebar, text="GPU: --", font=(FONT, 9), text_color=C["text_dim"])
        self._gpu_lbl.pack(side="bottom", padx=12, pady=0, anchor="w")
        self._vram_lbl = ctk.CTkLabel(self._sidebar, text="VRAM: --", font=(FONT, 9), text_color=C["text_dim"])
        self._vram_lbl.pack(side="bottom", padx=12, anchor="w")

        self._fx_sidebar_canvas = tk.Canvas(
            self._sidebar, bg=C["sidebar"], highlightthickness=0, width=180, height=200)
        self._fx_sidebar_canvas.pack(side="bottom", fill="x", pady=(0, 8))

    def _show_page(self, pid):
        self._current_page = pid
        for k, f in self._pages.items():
            f.pack(fill="both", expand=True) if k == pid else f.pack_forget()
        for k, b in self._nav_btns.items():
            if k == pid:
                b.configure(fg_color=C["accent_dim"], text_color=C["accent"])
            else:
                b.configure(fg_color="transparent", text_color=C["text_muted"])

    def _fx_start(self):
        """Initialize particle list and kick off the FX loop."""
        self._fx_particles = []
        self._fx_tick = 0
        self._fx_loop()

    def _fx_loop(self):
        """Main particle tick — spawn, update, cull, render."""
        try:
            if not hasattr(self, '_fx_sidebar_canvas'):
                self.after(500, self._fx_loop)
                return

            smoke_on = getattr(self, '_smoke_var', None) and self._smoke_var.get()
            drips_on = getattr(self, '_drips_var', None) and self._drips_var.get()
            fps = getattr(self, '_efx_fps_var', None)
            fps = fps.get() if fps else 30
            fps = max(10, min(60, fps))

            if not smoke_on and not drips_on:
                if self._fx_particles:
                    self._fx_particles.clear()
                    self._fx_sidebar_canvas.delete("fx")
                self.after(500, self._fx_loop)
                return

            w = 180
            h = 200
            self._fx_tick += 1

            # Spawn
            if smoke_on and len(self._fx_particles) < _FX_MAX_PARTICLES:
                if self._fx_tick % 4 == 0:
                    self._fx_particles.append(_make_smoke(w, h))
            if drips_on and len(self._fx_particles) < _FX_MAX_PARTICLES:
                if self._fx_tick % 10 == 0:
                    self._fx_particles.append(_make_drip(w, h))

            # Update & Cull
            alive = []
            for p in self._fx_particles:
                p["age"] += 1
                if p["age"] > p["life"]:
                    continue
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                if p["type"] == "smoke":
                    p["vx"] += random.uniform(-0.04, 0.04)
                    p["vx"] *= 0.98
                    p["vy"] *= 0.995
                    if p["r0"] == 0:
                        p["r0"] = p["r"]
                    progress = p["age"] / p["life"]
                    p["r"] = p["r0"] * (1.0 + progress * 0.6)
                else:
                    p["vy"] += 0.025
                    p["vx"] *= 0.99
                if p["y"] < -60 or p["y"] > h + 60 or p["x"] < -60 or p["x"] > w + 60:
                    continue
                alive.append(p)
            self._fx_particles = alive

            # Render
            canvas = self._fx_sidebar_canvas
            canvas.delete("fx")

            for p in self._fx_particles:
                frac = p["age"] / p["life"]
                if p["type"] == "smoke":
                    if frac < 0.2:
                        alpha = frac / 0.2 * 0.30
                    else:
                        alpha = 0.30 * (1.0 - (frac - 0.2) / 0.8)
                    alpha = max(0.0, alpha)
                    r = p["r"]
                    x, y = p["x"], p["y"]
                    halo_c = _blend_hex("#222222", alpha * 0.5)
                    canvas.create_oval(x - r, y - r, x + r, y + r,
                                       fill=halo_c, outline="", tags="fx")
                    ri = r * 0.55
                    core_c = _blend_hex("#2D2D2D", alpha * 0.8)
                    canvas.create_oval(x - ri, y - ri, x + ri, y + ri,
                                       fill=core_c, outline="", tags="fx")
                else:
                    if frac < 0.85:
                        alpha = 1.0
                    else:
                        alpha = 1.0 - (frac - 0.85) / 0.15
                    alpha = max(0.0, alpha)
                    r = p["r"]
                    x, y = p["x"], p["y"]
                    trail_len = min(r * 5, 20)
                    trail_c = _blend_hex("#F5A800", alpha * 0.4)
                    canvas.create_line(x, y - trail_len, x, y - r,
                                       fill=trail_c, width=max(1, r * 0.4), tags="fx")
                    body_c = _blend_hex("#F5A800", alpha * 0.85)
                    canvas.create_oval(x - r, y - r * 1.4, x + r, y + r * 0.8,
                                       fill=body_c, outline="", tags="fx")
                    rc = r * 0.45
                    core_c = _blend_hex("#FFD000", alpha)
                    canvas.create_oval(x - rc, y - rc, x + rc, y + rc,
                                       fill=core_c, outline="", tags="fx")

        except Exception:
            pass

        delay = max(16, int(1000 / fps)) if (smoke_on or drips_on) else 500
        self.after(delay, self._fx_loop)

    def _update_gpu_info(self):
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                                "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=2,
                               startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            if r.returncode == 0:
                parts = r.stdout.strip().split(",")
                self._gpu_lbl.configure(text=f"GPU: {parts[0].strip()}% (DirectX)")
                self._vram_lbl.configure(text=f"VRAM: {parts[1].strip()}/{parts[2].strip()} MB")
                self._sb_gpu.configure(text=f"\U0001f3ae {parts[1].strip()}/{parts[2].strip()}MB")
        except Exception:
            self._gpu_lbl.configure(text=t("cpu_mode"))
        self.after(2000, self._update_gpu_info)

    def _redraw_honeycomb(self, event=None):
        pass
