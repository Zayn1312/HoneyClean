import multiprocessing
multiprocessing.freeze_support()

"""
HoneyClean v2 - AI Background Remover
Glassmorphism Dark UI by HoneyDev

Features: Auto GPU/CPU fallback, Debug console, Manual erase tool,
          Tolerance picker, GPU limit 0-100%, Batch processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, os, io, time, sys, json, subprocess, traceback, queue, math
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFilter

# Suppress onnxruntime CUDA DLL errors as early as possible
os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Hide console window on Windows
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except: pass

# Redirect stderr to suppress CUDA warnings
import io as _io
sys.stderr = _io.StringIO()

VERSION = "2.0"

# ── Config ────────────────────────────────────────────────────────
CFG_PATH = Path(os.environ.get("APPDATA", ".")) / "HoneyClean" / "config.json"

DEFAULT_CFG = {
    "output_dir": str(Path.home() / "Downloads" / "HoneyClean_Output"),
    "gpu_limit": 100,
    "model": "isnet-anime",
    "alpha_fg": 240,
    "alpha_bg": 10,
    "alpha_erode": 10,
    "use_gpu": True,
    "debug": False,
}

def load_cfg():
    try:
        CFG_PATH.parent.mkdir(exist_ok=True)
        if CFG_PATH.exists():
            d = json.loads(CFG_PATH.read_text())
            return {**DEFAULT_CFG, **d}
    except: pass
    return DEFAULT_CFG.copy()

def save_cfg(c):
    try:
        CFG_PATH.parent.mkdir(exist_ok=True)
        CFG_PATH.write_text(json.dumps(c, indent=2))
    except: pass

# ── Enhanced Palette ──────────────────────────────────────────────
BG       = "#08081a"
BG2      = "#0b0b20"
PANEL    = "#0f0f28"
CARD     = "#151535"
CARD2    = "#1b1b40"
BORDER   = "#252550"
ACC      = "#f5a623"
ACC_DIM  = "#c47d00"
BLUE     = "#00d4ff"
BLUE_DIM = "#0099bb"
GREEN    = "#00ff88"
GREEN_DIM= "#00bb66"
RED      = "#e94560"
RED_DIM  = "#bb2244"
AMBER    = "#ffaa00"
FG       = "#e0e0f0"
FG2      = "#7777aa"
FG3      = "#555580"
FONT     = "Segoe UI"

def mix_color(c1_hex, c2_hex, alpha):
    """Mix c1 over c2 at given alpha (0-1)."""
    r1, g1, b1 = int(c1_hex[1:3],16), int(c1_hex[3:5],16), int(c1_hex[5:7],16)
    r2, g2, b2 = int(c2_hex[1:3],16), int(c2_hex[3:5],16), int(c2_hex[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1*alpha + r2*(1-alpha)),
        int(g1*alpha + g2*(1-alpha)),
        int(b1*alpha + b2*(1-alpha)))

def lerp_color(c1_hex, c2_hex, t):
    """Linear interpolate between two colors, t in 0-1."""
    r1, g1, b1 = int(c1_hex[1:3],16), int(c1_hex[3:5],16), int(c1_hex[5:7],16)
    r2, g2, b2 = int(c2_hex[1:3],16), int(c2_hex[3:5],16), int(c2_hex[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1 + (r2-r1)*t), int(g1 + (g2-g1)*t), int(b1 + (b2-b1)*t))

# ── Honey logo (drawn with PIL) ──────────────────────────────────
def make_logo(size=40):
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    d = ImageDraw.Draw(img)
    cx, cy, r = size//2, size//2, size//2-2
    pts = [(cx + r*math.cos(math.radians(a-90)),
            cy + r*math.sin(math.radians(a-90))) for a in range(0,360,60)]
    d.polygon(pts, fill=ACC, outline="#c47d00")
    drop = [(cx, cy-r//2+4), (cx-5, cy+2), (cx, cy+r//3), (cx+5, cy+2)]
    d.polygon(drop, fill="#08081a")
    return img

# ── Custom Widgets ────────────────────────────────────────────────

def _rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draw a rounded rectangle on a canvas using smooth polygon."""
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
           x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
           x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, splinesteps=20, **kw)


class NeonButton(tk.Canvas):
    """Pill-shaped neon glow button with hover animation."""

    def __init__(self, parent, text="", command=None, color=GREEN,
                 width=150, height=44, font_size=11, bold=True):
        try:
            bg = parent.cget("bg")
        except:
            bg = BG
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0, bd=0)
        self._text = text
        self._command = command
        self._color = color
        self._bg = bg
        self._w = width
        self._h = height
        self._r = height // 2
        self._font = (FONT, font_size, "bold" if bold else "")
        self._enabled = True
        self._hover = False
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

    def _draw(self):
        self.delete("all")
        w, h, r = self._w, self._h, self._r
        if self._enabled:
            for pad, alpha in [(0, 0.06), (1, 0.12), (2, 0.20)]:
                gc = mix_color(self._color, self._bg, alpha)
                _rounded_rect(self, pad, pad, w-pad, h-pad, max(1,r-pad),
                              fill=gc, outline="")
            fill = mix_color(self._color, "#ffffff", 0.15) if self._hover else self._color
            fg = "#000000"
        else:
            fill = CARD
            fg = FG3
        _rounded_rect(self, 3, 3, w-3, h-3, max(1,r-3), fill=fill, outline="")
        self.create_text(w//2, h//2, text=self._text, fill=fg, font=self._font)

    def _on_enter(self, e):
        if self._enabled:
            self._hover = True
            self._draw()

    def _on_leave(self, e):
        self._hover = False
        self._draw()

    def _on_click(self, e):
        if self._enabled and self._command:
            self._command()

    def set_state(self, enabled, color=None, text=None):
        self._enabled = enabled
        if color is not None:
            self._color = color
        if text is not None:
            self._text = text
        self.configure(cursor="hand2" if enabled else "")
        self._draw()


class MiniBar(tk.Canvas):
    """Small GPU/VRAM status bar."""

    def __init__(self, parent, width=150, height=10):
        try:
            bg = parent.cget("bg")
        except:
            bg = PANEL
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0, bd=0)
        self._w = width
        self._h = height
        self._value = 0
        self._color = GREEN

    def set(self, value, color=None):
        self._value = min(100, max(0, value))
        if color:
            self._color = color
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self._w, self._h
        self.create_rectangle(0, 1, w, h-1, fill="#0a0a1e", outline=BORDER, width=1)
        fw = int(w * self._value / 100)
        if fw > 0:
            self.create_rectangle(1, 2, fw, h-2, fill=self._color, outline="")


class GlowProgress(tk.Canvas):
    """Custom progress bar with gradient fill and leading-edge glow."""

    def __init__(self, parent, height=20):
        try:
            bg = parent.cget("bg")
        except:
            bg = BG
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self._h = height
        self._value = 0
        self._max = 100
        self._grad_tk = None
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, value, maximum=None):
        self._value = value
        if maximum is not None:
            self._max = max(1, maximum)
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self._h
        if w < 10:
            return
        r = h // 2

        # Track
        _rounded_rect(self, 0, 0, w, h, r, fill="#0a0a1e", outline=BORDER)

        pct = self._value / self._max if self._max > 0 else 0
        fw = max(0, int((w - 6) * pct))
        if fw < 2:
            return

        # Gradient fill via PIL
        try:
            grad = Image.new("RGB", (fw, max(1, h - 6)))
            draw = ImageDraw.Draw(grad)
            for x in range(fw):
                t = x / max(1, fw - 1)
                rc = int(0xf5 + (0x00 - 0xf5) * t)
                gc = int(0xa6 + (0xd4 - 0xa6) * t)
                bc = int(0x23 + (0xff - 0x23) * t)
                draw.line([(x, 0), (x, h - 7)], fill=(rc, gc, bc))
            self._grad_tk = ImageTk.PhotoImage(grad)
            self.create_image(3, 3, anchor="nw", image=self._grad_tk)
        except:
            # Fallback: solid fill
            _rounded_rect(self, 3, 3, fw+3, h-3, max(1,r-3), fill=ACC, outline="")

        # Leading edge glow
        if fw > 8:
            cx = fw + 3
            cy = h // 2
            for rad, alpha in [(7, 0.08), (4, 0.18), (2, 0.35)]:
                gc = mix_color(BLUE, "#0a0a1e", alpha)
                self.create_oval(cx-rad, cy-rad, cx+rad, cy+rad, fill=gc, outline="")


# ══════════════════════════════════════════════════════════════════
class HoneyClean:
    def __init__(self, root):
        self.root = root
        self.cfg = load_cfg()
        self.session = None
        self.session_model = None
        self.queue_items = []
        self.processing = False
        self.paused = False
        self.stop_flag = False
        self.debug_q = queue.Queue()
        self.erase_mode = False
        self.erase_radius = 15
        self.last_result_img = None
        self.last_result_path = None
        self.tool_mode = "none"
        self._maximized = False
        self._restore_geo = ""

        # Frameless window setup
        self.root.overrideredirect(True)
        self.root.geometry("1200x820")
        self.root.minsize(960, 640)
        self.root.attributes("-alpha", 0.0)

        # Center on screen
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 1200) // 2
        y = (sh - 820) // 2
        self.root.geometry(f"1200x820+{x}+{y}")

        # 1px accent border around entire window
        self.root.configure(bg=ACC_DIM)
        self._main_frame = tk.Frame(self.root, bg=BG)
        self._main_frame.pack(fill="both", expand=True, padx=1, pady=1)

        self._set_icon()
        self._build_ui()
        self._setup_resize()
        self._setup_dnd()
        self._start_gpu_monitor()
        self._debug_pump()
        self._fade_in()

    # ── Fade-in animation ─────────────────────────────────────────
    def _fade_in(self):
        self._alpha = 0.0
        def step():
            self._alpha = min(self._alpha + 0.06, 1.0)
            self.root.attributes("-alpha", self._alpha)
            if self._alpha < 1.0:
                self.root.after(18, step)
        self.root.after(30, step)

    # ── Window icon ───────────────────────────────────────────────
    def _set_icon(self):
        try:
            logo = make_logo(32)
            self._icon = ImageTk.PhotoImage(logo)
            self.root.iconphoto(True, self._icon)
        except: pass

    # ── Resize handles ────────────────────────────────────────────
    def _setup_resize(self):
        grip_r = tk.Frame(self.root, width=5, bg=ACC_DIM, cursor="sb_h_double_arrow")
        grip_r.place(relx=1.0, y=0, relheight=1.0, anchor="ne")
        grip_r.bind("<B1-Motion>", self._resize_r)

        grip_b = tk.Frame(self.root, height=5, bg=ACC_DIM, cursor="sb_v_double_arrow")
        grip_b.place(x=0, rely=1.0, relwidth=1.0, anchor="sw")
        grip_b.bind("<B1-Motion>", self._resize_b)

        grip_br = tk.Frame(self.root, width=14, height=14, bg=ACC_DIM, cursor="size_nw_se")
        grip_br.place(relx=1.0, rely=1.0, anchor="se")
        grip_br.bind("<B1-Motion>", self._resize_br)

    def _resize_r(self, e):
        w = max(960, self.root.winfo_pointerx() - self.root.winfo_rootx())
        self.root.geometry(f"{w}x{self.root.winfo_height()}")

    def _resize_b(self, e):
        h = max(640, self.root.winfo_pointery() - self.root.winfo_rooty())
        self.root.geometry(f"{self.root.winfo_width()}x{h}")

    def _resize_br(self, e):
        w = max(960, self.root.winfo_pointerx() - self.root.winfo_rootx())
        h = max(640, self.root.winfo_pointery() - self.root.winfo_rooty())
        self.root.geometry(f"{w}x{h}")

    # ── Title bar helpers ─────────────────────────────────────────
    def _start_drag(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _do_drag(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = max(0, self.root.winfo_y() + e.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def _toggle_maximize(self, e=None):
        if self._maximized:
            self.root.geometry(self._restore_geo)
            self._maximized = False
        else:
            self._restore_geo = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
            self._maximized = True

    def _minimize(self):
        self.root.withdraw()
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<Map>", self._on_map)

    def _on_map(self, e):
        if self.root.state() != "iconic":
            self.root.after(10, lambda: self.root.overrideredirect(True))
            self.root.unbind("<Map>")

    def _close(self):
        self.root.destroy()

    # ── Glow card helper ──────────────────────────────────────────
    def _make_card(self, parent, border_color=BORDER):
        glow = tk.Frame(parent, bg=mix_color(border_color, BG, 0.15))
        border_f = tk.Frame(glow, bg=border_color)
        border_f.pack(fill="both", expand=True, padx=1, pady=1)
        content = tk.Frame(border_f, bg=CARD)
        content.pack(fill="both", expand=True, padx=1, pady=1)
        return glow, content

    # ── Build UI ──────────────────────────────────────────────────
    def _build_ui(self):
        mf = self._main_frame

        # ── Custom Title Bar ──────────────────────────────────────
        title_bar = tk.Frame(mf, bg=BG2, height=38)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        # Drag bindings
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._do_drag)
        title_bar.bind("<Double-Button-1>", self._toggle_maximize)

        # Logo
        try:
            logo_img = make_logo(28)
            self._logo_tk = ImageTk.PhotoImage(logo_img)
            logo_lbl = tk.Label(title_bar, image=self._logo_tk, bg=BG2)
            logo_lbl.pack(side="left", padx=(12, 6))
            logo_lbl.bind("<Button-1>", self._start_drag)
            logo_lbl.bind("<B1-Motion>", self._do_drag)
        except: pass

        title_lbl = tk.Label(title_bar, text="HoneyClean", font=(FONT, 13, "bold"),
                             fg=ACC, bg=BG2)
        title_lbl.pack(side="left")
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._do_drag)

        sub_lbl = tk.Label(title_bar, text="by HoneyDev", font=(FONT, 8),
                           fg=FG2, bg=BG2)
        sub_lbl.pack(side="left", padx=(6, 0), pady=(2, 0))
        sub_lbl.bind("<Button-1>", self._start_drag)
        sub_lbl.bind("<B1-Motion>", self._do_drag)

        # Version badge
        ver_f = tk.Frame(title_bar, bg=ACC_DIM, padx=6, pady=1)
        ver_f.pack(side="left", padx=(10, 0), pady=10)
        tk.Label(ver_f, text=f"v{VERSION}", font=(FONT, 7, "bold"),
                 fg="#000000", bg=ACC_DIM).pack()

        # Close button
        close_btn = tk.Label(title_bar, text=" \u2715 ", font=(FONT, 12),
                             fg=FG3, bg=BG2, cursor="hand2")
        close_btn.pack(side="right", padx=(0, 4))
        close_btn.bind("<Button-1>", lambda e: self._close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=RED, bg="#1a0a10"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=FG3, bg=BG2))

        # Minimize button
        min_btn = tk.Label(title_bar, text=" \u2500 ", font=(FONT, 12),
                           fg=FG3, bg=BG2, cursor="hand2")
        min_btn.pack(side="right", padx=2)
        min_btn.bind("<Button-1>", lambda e: self._minimize())
        min_btn.bind("<Enter>", lambda e: min_btn.config(fg=FG, bg=CARD))
        min_btn.bind("<Leave>", lambda e: min_btn.config(fg=FG3, bg=BG2))

        # Settings button
        gear_btn = tk.Label(title_bar, text=" \u2699 ", font=(FONT, 14),
                            fg=FG3, bg=BG2, cursor="hand2")
        gear_btn.pack(side="right", padx=2)
        gear_btn.bind("<Button-1>", lambda e: self._open_settings())
        gear_btn.bind("<Enter>", lambda e: gear_btn.config(fg=ACC))
        gear_btn.bind("<Leave>", lambda e: gear_btn.config(fg=FG3))

        # Debug button
        self.debug_btn = tk.Label(title_bar, text=" Debug ", font=(FONT, 8),
                                  fg=FG3, bg=CARD, cursor="hand2", padx=6, pady=2)
        self.debug_btn.pack(side="right", padx=4, pady=8)
        self.debug_btn.bind("<Button-1>", lambda e: self._toggle_debug())

        # ── GPU Monitor Row ───────────────────────────────────────
        gpu_card, gpu_inner = self._make_card(mf, border_color=BORDER)
        gpu_card.pack(fill="x", padx=12, pady=(6, 0))

        gpu_row = tk.Frame(gpu_inner, bg=CARD, pady=4)
        gpu_row.pack(fill="x")

        tk.Label(gpu_row, text="GPU", font=(FONT, 8, "bold"),
                 fg=FG2, bg=CARD).pack(side="left", padx=(8, 4))
        self.gpu_bar = MiniBar(gpu_row, width=140, height=10)
        self.gpu_bar.pack(side="left")
        self.gpu_lbl = tk.Label(gpu_row, text="\u2013", font=(FONT, 8, "bold"),
                                fg=BLUE, bg=CARD, width=6)
        self.gpu_lbl.pack(side="left", padx=4)

        tk.Label(gpu_row, text="VRAM", font=(FONT, 8, "bold"),
                 fg=FG2, bg=CARD).pack(side="left", padx=(8, 4))
        self.vram_bar = MiniBar(gpu_row, width=130, height=10)
        self.vram_bar.pack(side="left")
        self.vram_lbl = tk.Label(gpu_row, text="\u2013", font=(FONT, 8, "bold"),
                                 fg=BLUE, bg=CARD, width=10)
        self.vram_lbl.pack(side="left", padx=4)

        self.gpu_name_lbl = tk.Label(gpu_row, text="", font=(FONT, 8),
                                     fg=FG2, bg=CARD)
        self.gpu_name_lbl.pack(side="left", padx=6)

        self.fallback_lbl = tk.Label(gpu_row, text="", font=(FONT, 8, "italic"),
                                     fg=ACC, bg=CARD)
        self.fallback_lbl.pack(side="left", padx=4)

        # GPU Limit (right side)
        tk.Label(gpu_row, text="%", font=(FONT, 8), fg=FG2, bg=CARD
                 ).pack(side="right", padx=(0, 8))
        self.throttle_var = tk.IntVar(value=self.cfg["gpu_limit"])
        tk.Spinbox(gpu_row, from_=0, to=100, width=4,
                   textvariable=self.throttle_var, font=(FONT, 8),
                   bg=CARD2, fg=FG, relief="flat", buttonbackground=CARD2,
                   command=self._save_throttle).pack(side="right")
        tk.Label(gpu_row, text="GPU Limit:", font=(FONT, 8), fg=FG2, bg=CARD
                 ).pack(side="right", padx=(0, 4))

        # ── Main Content ──────────────────────────────────────────
        main = tk.Frame(mf, bg=BG)
        main.pack(fill="both", expand=True, padx=12, pady=6)

        # ── Left Panel (Queue) ────────────────────────────────────
        left = tk.Frame(main, bg=BG, width=260)
        left.pack(side="left", fill="y", padx=(0, 6))
        left.pack_propagate(False)

        # Animated drop zone
        dz_card, dz_inner = self._make_card(left, border_color=ACC_DIM)
        dz_card.pack(fill="x")
        self.drop_canvas = tk.Canvas(dz_inner, bg=CARD, highlightthickness=0,
                                     height=80, cursor="hand2")
        self.drop_canvas.pack(fill="x")
        self.drop_canvas.bind("<Button-1>", lambda e: self._browse_files())
        self.drop_canvas.bind("<Configure>", lambda e: self._draw_drop())
        self._dash_offset = 0
        self._animate_drop()

        # Folder button
        NeonButton(left, text="\U0001F4C1  Ordner hinzufugen",
                   command=self._browse_folder, color=PANEL,
                   width=256, height=32, font_size=9, bold=False
                   ).pack(fill="x", pady=(4, 2))

        # Queue label
        tk.Label(left, text="Warteschlange", font=(FONT, 8, "bold"),
                 fg=FG2, bg=BG).pack(anchor="w", pady=(4, 2))

        # Queue list in glow card
        q_card, q_inner = self._make_card(left, border_color=BORDER)
        q_card.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(q_inner, style="Dark.Vertical.TScrollbar")
        sb.pack(side="right", fill="y")
        self.q_list = tk.Listbox(q_inner, bg=CARD, fg=FG, font=(FONT, 8),
                                  selectbackground=ACC, selectforeground="black",
                                  relief="flat", bd=0, yscrollcommand=sb.set,
                                  activestyle="none", highlightthickness=0)
        self.q_list.pack(fill="both", expand=True)
        sb.config(command=self.q_list.yview)

        # Clear button
        NeonButton(left, text="\U0001F5D1  Leeren", command=self._clear_queue,
                   color=RED_DIM, width=256, height=30, font_size=9, bold=False
                   ).pack(fill="x", pady=(3, 0))

        # ── Right Panel ───────────────────────────────────────────
        right = tk.Frame(main, bg=BG)
        right.pack(side="right", fill="both", expand=True)

        # ── Retouch Toolbar ───────────────────────────────────────
        tb_card, tb_inner = self._make_card(right, border_color=BORDER)
        tb_card.pack(fill="x")

        etb = tk.Frame(tb_inner, bg=CARD, pady=4)
        etb.pack(fill="x")

        tk.Label(etb, text="Retusche:", font=(FONT, 8, "bold"),
                 fg=FG2, bg=CARD).pack(side="left", padx=(8, 4))

        self.erase_btn = tk.Button(etb, text="✏ Radieren", font=(FONT, 8),
                  bg=CARD2, fg=FG2, relief="flat", padx=8, pady=3, cursor="hand2",
                  activebackground=RED_DIM, activeforeground="white",
                  command=self._toggle_erase)
        self.erase_btn.pack(side="left", padx=2)

        self.restore_btn = tk.Button(etb, text="\U0001F504 Wiederherstellen", font=(FONT, 8),
                  bg=CARD2, fg=FG2, relief="flat", padx=8, pady=3, cursor="hand2",
                  activebackground=GREEN_DIM, activeforeground="white",
                  command=self._toggle_restore)
        self.restore_btn.pack(side="left", padx=2)

        tk.Label(etb, text="Gr\u00f6\u00dfe:", font=(FONT, 8), fg=FG2, bg=CARD
                 ).pack(side="left", padx=(12, 2))
        self.brush_var = tk.IntVar(value=15)
        tk.Scale(etb, from_=3, to=60, orient="horizontal", variable=self.brush_var,
                 bg=CARD, fg=FG2, troughcolor=PANEL, highlightthickness=0,
                 length=90, showvalue=False, sliderrelief="flat",
                 activebackground=ACC).pack(side="left")

        tk.Label(etb, text="Toleranz:", font=(FONT, 8), fg=FG2, bg=CARD
                 ).pack(side="left", padx=(12, 2))
        self.tolerance_var = tk.IntVar(value=30)
        tk.Scale(etb, from_=0, to=100, orient="horizontal", variable=self.tolerance_var,
                 bg=CARD, fg=FG2, troughcolor=PANEL, highlightthickness=0,
                 length=90, showvalue=False, sliderrelief="flat",
                 activebackground=ACC).pack(side="left")

        tk.Button(etb, text="\U0001F4BE Speichern", font=(FONT, 8),
                  bg=GREEN_DIM, fg="white", relief="flat", padx=8, pady=3,
                  cursor="hand2", activebackground=GREEN, activeforeground="black",
                  command=self._save_edit).pack(side="right", padx=8)

        tk.Button(etb, text="\u21A9 Zur\u00fccksetzen", font=(FONT, 8),
                  bg=CARD2, fg=FG2, relief="flat", padx=8, pady=3,
                  cursor="hand2", activebackground=PANEL,
                  command=self._reset_edit).pack(side="right", padx=2)

        # ── Before / After Panels ─────────────────────────────────
        pf = tk.Frame(right, bg=BG)
        pf.pack(fill="both", expand=True, pady=(4, 0))

        # VORHER
        bc_card, bc_inner = self._make_card(pf, border_color=mix_color(RED, BG, 0.4))
        bc_card.pack(side="left", fill="both", expand=True, padx=(0, 3))
        tk.Label(bc_inner, text="VORHER", font=(FONT, 8, "bold"),
                 fg=RED, bg=CARD).pack(pady=3)
        self.before_cv = tk.Canvas(bc_inner, bg="#0a0a1a", highlightthickness=0)
        self.before_cv.pack(fill="both", expand=True, padx=2, pady=(0, 2))

        # NACHHER
        ac_card, ac_inner = self._make_card(pf, border_color=mix_color(BLUE, BG, 0.4))
        ac_card.pack(side="right", fill="both", expand=True, padx=(3, 0))
        ah = tk.Frame(ac_inner, bg=CARD)
        ah.pack(fill="x")
        tk.Label(ah, text="NACHHER", font=(FONT, 8, "bold"),
                 fg=BLUE, bg=CARD).pack(side="left", pady=3, padx=4)
        self.checker_var = tk.BooleanVar(value=True)
        tk.Checkbutton(ah, text="Schachbrett", variable=self.checker_var,
                       bg=CARD, fg=FG2, selectcolor=CARD2, font=(FONT, 8),
                       activebackground=CARD, activeforeground=FG,
                       command=self._refresh_after).pack(side="right", padx=6)
        self.after_cv = tk.Canvas(ac_inner, bg="#0a0a1a", highlightthickness=0,
                                  cursor="crosshair")
        self.after_cv.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        self.after_cv.bind("<B1-Motion>", self._on_canvas_draw)
        self.after_cv.bind("<Button-1>", self._on_canvas_draw)

        # ── File info label ───────────────────────────────────────
        self.file_lbl = tk.Label(right, text="F\u00fcge Bilder hinzu um zu starten",
                                  font=(FONT, 8), fg=FG2, bg=BG)
        self.file_lbl.pack()

        # ── Progress Bar ──────────────────────────────────────────
        pr = tk.Frame(mf, bg=BG)
        pr.pack(fill="x", padx=12, pady=(2, 0))
        self.prog = GlowProgress(pr, height=18)
        self.prog.pack(side="left", fill="x", expand=True)
        self.prog_lbl = tk.Label(pr, text="0 / 0", font=(FONT, 8, "bold"),
                                  fg=FG, bg=BG, width=10)
        self.prog_lbl.pack(side="left", padx=6)
        self.eta_lbl = tk.Label(pr, text="", font=(FONT, 8), fg=FG2, bg=BG, width=14)
        self.eta_lbl.pack(side="left")

        # ── Control Buttons ───────────────────────────────────────
        br = tk.Frame(mf, bg=BG)
        br.pack(pady=6)

        self.start_btn = NeonButton(br, text="\u25B6  START", command=self._start,
                                    color=GREEN, width=160, height=44, font_size=11)
        self.start_btn.pack(side="left", padx=5)

        self.pause_btn = NeonButton(br, text="\u23F8  PAUSE", command=self._toggle_pause,
                                    color=AMBER, width=160, height=44, font_size=11)
        self.pause_btn.set_state(False)
        self.pause_btn.pack(side="left", padx=5)

        self.stop_btn = NeonButton(br, text="\u23F9  STOP", command=self._stop,
                                   color=RED, width=160, height=44, font_size=11)
        self.stop_btn.set_state(False)
        self.stop_btn.pack(side="left", padx=5)

        self.open_btn = NeonButton(br, text="\U0001F4C2  Output \u00f6ffnen",
                                   command=self._open_output,
                                   color=PANEL, width=160, height=44, font_size=9)
        self.open_btn.pack(side="left", padx=5)

        # ── Status Label ──────────────────────────────────────────
        self.status_lbl = tk.Label(mf, text="", font=(FONT, 9, "italic"),
                                   fg=FG2, bg=BG)
        self.status_lbl.pack()

        # ── Footer Branding ───────────────────────────────────────
        footer = tk.Frame(mf, bg=BG2, height=24)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        tk.Label(footer, text="Made with \u2764 by HoneyDev", font=(FONT, 8),
                 fg=FG3, bg=BG2).pack(expand=True)

        # ── Debug Console (hidden by default) ─────────────────────
        self.debug_frame = tk.Frame(mf, bg="#060612")
        self.debug_text = tk.Text(self.debug_frame, bg="#060612", fg=GREEN,
                                   font=("Consolas", 8), height=6, relief="flat",
                                   state="disabled", insertbackground=GREEN,
                                   selectbackground=ACC_DIM)
        self.debug_text.pack(fill="both", expand=True, padx=4, pady=2)
        dbsb = ttk.Scrollbar(self.debug_frame, command=self.debug_text.yview)
        dbsb.pack(side="right", fill="y")
        self.debug_text.config(yscrollcommand=dbsb.set)
        if self.cfg.get("debug"):
            self.debug_frame.pack(fill="x", padx=12, pady=(0, 4), before=footer)

    # ── Animated drop zone ────────────────────────────────────────
    def _draw_drop(self):
        c = self.drop_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10:
            return
        c.create_rectangle(8, 8, w-8, h-8, dash=(10, 5),
                           dashoffset=self._dash_offset,
                           outline=ACC, width=2)
        c.create_text(w//2, h//2 - 8, text="\U0001F4C2", font=(FONT, 16), fill=ACC)
        c.create_text(w//2, h//2 + 14,
                      text="Dateien hier ablegen oder klicken",
                      font=(FONT, 8), fill=FG2)

    def _animate_drop(self):
        self._dash_offset = (self._dash_offset + 1) % 15
        self._draw_drop()
        self.root.after(100, self._animate_drop)

    # ── Settings Dialog ───────────────────────────────────────────
    def _open_settings(self):
        w = tk.Toplevel(self.root)
        w.title("HoneyClean \u2013 Settings")
        w.geometry("520x380")
        w.configure(bg=BG)
        w.resizable(False, False)
        w.grab_set()
        # Center on parent
        w.update_idletasks()
        px = self.root.winfo_x() + (self.root.winfo_width() - 520) // 2
        py = self.root.winfo_y() + (self.root.winfo_height() - 380) // 2
        w.geometry(f"+{px}+{py}")

        tk.Label(w, text="\u2699  Settings", font=(FONT, 13, "bold"),
                 fg=ACC, bg=BG).grid(row=0, column=0, columnspan=3, pady=12)

        fields = [
            ("Output-Ordner", "output_dir", "folder"),
            ("KI-Modell",     "model",      ["isnet-anime","u2net","u2net_human_seg","silueta","isnet-general-use"]),
            ("GPU Limit %",   "gpu_limit",  "int_0_100"),
            ("Alpha FG",      "alpha_fg",   "int_0_255"),
            ("Alpha BG",      "alpha_bg",   "int_0_255"),
            ("Alpha Erode",   "alpha_erode","int_0_30"),
        ]
        vars_ = {}
        for i, (label, key, kind) in enumerate(fields, 1):
            tk.Label(w, text=label, font=(FONT, 9), fg=FG2, bg=BG,
                     width=14, anchor="e").grid(row=i, column=0, padx=10, pady=5, sticky="e")
            v = tk.StringVar(value=str(self.cfg.get(key, "")))
            vars_[key] = v
            if isinstance(kind, list):
                cb = ttk.Combobox(w, textvariable=v, values=kind, state="readonly", width=28)
                cb.grid(row=i, column=1, padx=6, sticky="ew")
            elif kind == "folder":
                fr = tk.Frame(w, bg=BG)
                fr.grid(row=i, column=1, padx=6, sticky="ew")
                tk.Entry(fr, textvariable=v, font=(FONT, 9), bg=CARD, fg=FG,
                         relief="flat", width=22, insertbackground=FG).pack(side="left")
                tk.Button(fr, text="\u2026", bg=PANEL, fg=FG2, relief="flat",
                          command=lambda vr=v: vr.set(filedialog.askdirectory() or vr.get())
                          ).pack(side="left", padx=3)
            else:
                tk.Entry(w, textvariable=v, font=(FONT, 9), bg=CARD, fg=FG,
                         relief="flat", width=8, insertbackground=FG
                         ).grid(row=i, column=1, padx=6, sticky="w")

        use_gpu = tk.BooleanVar(value=self.cfg.get("use_gpu", True))
        tk.Checkbutton(w, text="GPU verwenden (f\u00e4llt auf CPU zur\u00fcck wenn nicht verf\u00fcgbar)",
                       variable=use_gpu, bg=BG, fg=FG, selectcolor=CARD,
                       activebackground=BG, activeforeground=FG,
                       font=(FONT, 9)).grid(row=len(fields)+1, column=0, columnspan=3, pady=4)

        def save():
            for key, v in vars_.items():
                val = v.get()
                try: val = int(val)
                except: pass
                self.cfg[key] = val
            self.cfg["use_gpu"] = use_gpu.get()
            self.throttle_var.set(self.cfg["gpu_limit"])
            self.session = None
            save_cfg(self.cfg)
            w.destroy()
            self._log("Settings gespeichert")

        tk.Button(w, text="\U0001F4BE  Speichern", font=(FONT, 10, "bold"),
                  bg=ACC, fg="black", relief="flat", padx=20, pady=6,
                  cursor="hand2", activebackground=ACC_DIM, command=save
                  ).grid(row=len(fields)+2, column=0, columnspan=3, pady=12)

    def _save_throttle(self):
        self.cfg["gpu_limit"] = self.throttle_var.get()
        save_cfg(self.cfg)

    def _toggle_debug(self):
        self.cfg["debug"] = not self.cfg.get("debug", False)
        save_cfg(self.cfg)
        # Get footer reference
        footer = self._main_frame.winfo_children()[-1]
        if self.cfg["debug"]:
            self.debug_frame.pack(fill="x", padx=12, pady=(0, 4), before=footer)
            self.debug_btn.config(bg=ACC, fg="black")
        else:
            self.debug_frame.pack_forget()
            self.debug_btn.config(bg=CARD, fg=FG3)

    def _log(self, msg):
        self.debug_q.put(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def _debug_pump(self):
        try:
            while True:
                msg = self.debug_q.get_nowait()
                self.debug_text.config(state="normal")
                self.debug_text.insert("end", msg + "\n")
                self.debug_text.see("end")
                self.debug_text.config(state="disabled")
        except: pass
        self.root.after(300, self._debug_pump)

    # ── File browsing & queue ─────────────────────────────────────
    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Bilder ausw\u00e4hlen",
            filetypes=[("Bilder", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Alle", "*.*")])
        for f in files:
            self._add(Path(f))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Ordner ausw\u00e4hlen")
        if folder:
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"]:
                for f in sorted(Path(folder).rglob(ext)):
                    self._add(f)

    def _add(self, path: Path):
        if path not in self.queue_items:
            self.queue_items.append(path)
            self.q_list.insert("end", f"  {path.name}")
            self.prog.set(0, maximum=len(self.queue_items))
            self.prog_lbl.config(text=f"0 / {len(self.queue_items)}")
            self._log(f"Hinzugef\u00fcgt: {path.name}")

    def _clear_queue(self):
        if not self.processing:
            self.queue_items.clear()
            self.q_list.delete(0, "end")
            self.prog_lbl.config(text="0 / 0")

    def _setup_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
            self._log("Drag & Drop aktiviert")
        except Exception as e:
            self._log(f"tkinterdnd2 nicht verf\u00fcgbar: {e}")

    def _on_drop(self, event):
        import re
        for m in re.finditer(r'\{([^}]+)\}|(\S+)', event.data):
            p = Path(m.group(1) or m.group(2))
            if p.is_dir():
                for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                    for f in sorted(p.rglob(ext)):
                        self._add(f)
            elif p.exists():
                self._add(p)

    # ── GPU Monitoring ────────────────────────────────────────────
    def _start_gpu_monitor(self):
        threading.Thread(target=self._gpu_loop, daemon=True).start()

    def _gpu_loop(self):
        while True:
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,name",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=3,
                    startupinfo=si, creationflags=0x08000000)
                if r.returncode == 0:
                    p = [x.strip() for x in r.stdout.strip().split(",")]
                    if len(p) >= 4:
                        gpu = int(p[0]); mu = int(p[1]); mt = int(p[2])
                        mp = int(mu/mt*100) if mt else 0
                        self.root.after(0, self._upd_gpu, gpu, mp, mu, mt, p[3])
                        limit = self.throttle_var.get()
                        if limit < 100 and self.processing and not self.paused and gpu > limit:
                            self._log(f"GPU {gpu}% > Limit {limit}% \u2013 warte...")
                            time.sleep(1.5)
            except FileNotFoundError:
                self.root.after(0, lambda: self.gpu_name_lbl.config(
                    text="nvidia-smi nicht gefunden (CPU Modus)"))
                time.sleep(10)
                continue
            except Exception as e:
                self._log(f"GPU Monitor Fehler: {e}")
            time.sleep(1)

    def _upd_gpu(self, gpu, mp, mu, mt, name):
        c = GREEN if gpu < 60 else ACC if gpu < 85 else RED
        self.gpu_bar.set(gpu, color=c)
        self.gpu_lbl.config(text=f"{gpu}%", fg=c)
        vc = GREEN if mp < 60 else ACC if mp < 85 else RED
        self.vram_bar.set(mp, color=vc)
        self.vram_lbl.config(text=f"{mu}M / {mt}M")
        self.gpu_name_lbl.config(text=name)

    # ── Processing ────────────────────────────────────────────────
    def _start(self):
        if not self.queue_items:
            self.status_lbl.config(text="\u26A0 Warteschlange ist leer!", fg=ACC)
            return
        if self.processing:
            return
        self.processing = True
        self.paused = False
        self.stop_flag = False
        self.start_btn.set_state(False, color=PANEL)
        self.pause_btn.set_state(True, color=AMBER, text="\u23F8  PAUSE")
        self.stop_btn.set_state(True, color=RED)
        threading.Thread(target=self._run, daemon=True).start()

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.set_state(True, color=GREEN, text="\u25B6  WEITER")
            self.status_lbl.config(text="\u23F8 Pausiert", fg=ACC)
        else:
            self.pause_btn.set_state(True, color=AMBER, text="\u23F8  PAUSE")
            self.status_lbl.config(text="\u25B6 Verarbeite...", fg=BLUE)

    def _stop(self):
        self.stop_flag = True
        self.paused = False

    def _open_output(self):
        out = self.cfg.get("output_dir", "")
        if out and os.path.exists(out):
            os.startfile(out)
        else:
            self.status_lbl.config(text="\u26A0 Output-Ordner existiert noch nicht", fg=ACC)

    def _load_session(self):
        from rembg import new_session
        model = self.cfg.get("model", "isnet-anime")
        use_gpu = self.cfg.get("use_gpu", True)

        if self.session and self.session_model == model:
            return True

        self._log(f"Lade Modell: {model} (GPU={'ja' if use_gpu else 'nein'})")

        providers = []
        if use_gpu:
            try:
                import onnxruntime as ort
                available = ort.get_available_providers()
                self._log(f"ORT Provider verf\u00fcgbar: {available}")
                if "DmlExecutionProvider" in available:
                    providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
                    self._log("GPU (DirectML) wird verwendet")
                    self.root.after(0, lambda: self.fallback_lbl.config(
                        text="\u25B6 GPU (DirectML)", fg=GREEN))
                elif "CUDAExecutionProvider" in available:
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    self._log("GPU (CUDA) wird verwendet")
                    self.root.after(0, lambda: self.fallback_lbl.config(
                        text="\u25B6 GPU (CUDA)", fg=GREEN))
                else:
                    raise RuntimeError("Kein GPU Provider verf\u00fcgbar")
            except Exception as e:
                self._log(f"GPU nicht verf\u00fcgbar ({e}) \u2192 CPU Fallback")
                self.root.after(0, lambda: self.fallback_lbl.config(
                    text="\u25B6 CPU Modus", fg=ACC))
                providers = ["CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]
            self.root.after(0, lambda: self.fallback_lbl.config(
                text="\u25B6 CPU Modus", fg=FG2))

        os.environ["ORT_LOGGING_LEVEL"] = "3"

        try:
            self.session = new_session(model, providers=providers)
        except TypeError:
            self.session = new_session(model)

        self.session_model = model
        self._log(f"Modell geladen: {model}")
        return True

    def _run(self):
        self.root.after(0, lambda: self.status_lbl.config(
            text="\U0001F504 Lade KI-Modell...", fg=ACC))
        try:
            from rembg import remove
            self._load_session()
        except Exception as e:
            self._log(f"FEHLER beim Laden: {traceback.format_exc()}")
            self.root.after(0, lambda: self.status_lbl.config(
                text=f"\u2717 Fehler: {e}", fg=RED))
            self._finish()
            return

        self.root.after(0, lambda: self.status_lbl.config(
            text="\u2713 Bereit \u2013 starte Verarbeitung", fg=GREEN))

        out_base = Path(self.cfg.get("output_dir",
                        str(Path.home() / "Downloads" / "HoneyClean_Output")))
        out_base.mkdir(parents=True, exist_ok=True)

        total = len(self.queue_items)
        done = 0
        t0 = time.time()

        for i, img_path in enumerate(self.queue_items):
            if self.stop_flag:
                break
            while self.paused:
                time.sleep(0.3)

            self.root.after(0, lambda idx=i: [
                self.q_list.selection_clear(0, "end"),
                self.q_list.selection_set(idx),
                self.q_list.see(idx)
            ])

            out_file = out_base / (img_path.stem + "_clean.png")
            self.root.after(0, self._show_before, img_path)
            self.root.after(0, lambda n=img_path.name: self.file_lbl.config(
                text=f"\u25B6 {n}", fg=FG2))
            self._log(f"Verarbeite [{i+1}/{total}]: {img_path.name}")

            if out_file.exists():
                img = Image.open(out_file).convert("RGBA")
                self.root.after(0, self._show_after, img, img_path, out_file)
                done += 1
                self.root.after(0, self._upd_prog, done, total, t0)
                self.root.after(0, lambda idx=i: self.q_list.itemconfig(idx, fg="#555577"))
                continue

            try:
                with open(img_path, "rb") as f:
                    data = f.read()

                from rembg import remove
                out_data = remove(
                    data,
                    session=self.session,
                    alpha_matting=True,
                    alpha_matting_foreground_threshold=self.cfg.get("alpha_fg", 240),
                    alpha_matting_background_threshold=self.cfg.get("alpha_bg", 10),
                    alpha_matting_erode_size=self.cfg.get("alpha_erode", 10),
                )
                result = Image.open(io.BytesIO(out_data)).convert("RGBA")
                result.save(out_file, "PNG")

                self.root.after(0, self._show_after, result, img_path, out_file)
                self.root.after(0, lambda idx=i: self.q_list.itemconfig(idx, fg=GREEN))
                self._log(f"\u2713 Gespeichert: {out_file.name}")
                done += 1
                self.root.after(0, self._upd_prog, done, total, t0)
                time.sleep(0.1)

            except Exception as e:
                self._log(f"\u2717 Fehler bei {img_path.name}: {traceback.format_exc()}")
                self.root.after(0, lambda idx=i, err=str(e): [
                    self.q_list.itemconfig(idx, fg=RED),
                    self.status_lbl.config(text=f"\u2717 {err}", fg=RED)
                ])
                done += 1
                self.root.after(0, self._upd_prog, done, total, t0)

        self.root.after(0, lambda d=done: [
            self.status_lbl.config(
                text=f"\U0001F389 Fertig! {d} Bilder \u2192 {out_base}", fg=GREEN),
            self.file_lbl.config(text=f"\u2713 {d} Bilder verarbeitet")
        ])
        self._finish()

    def _finish(self):
        self.processing = False
        self.root.after(0, lambda: [
            self.start_btn.set_state(True, color=GREEN, text="\u25B6  START"),
            self.pause_btn.set_state(False, text="\u23F8  PAUSE"),
            self.stop_btn.set_state(False),
        ])

    def _upd_prog(self, done, total, t0):
        pct = int(done / total * 100) if total else 0
        self.prog.set(pct)
        self.prog_lbl.config(text=f"{done} / {total}")
        if done > 0:
            per = (time.time() - t0) / done
            rem = per * (total - done)
            m, s = divmod(int(rem), 60)
            self.eta_lbl.config(text=f"ETA {m}m {s:02d}s")

    # ── Image display ─────────────────────────────────────────────
    def _fit(self, img, canvas):
        canvas.update_idletasks()
        cw = canvas.winfo_width() or 400
        ch = canvas.winfo_height() or 300
        iw, ih = img.size
        s = min(cw / iw, ch / ih, 1.0)
        nw, nh = max(1, int(iw * s)), max(1, int(ih * s))
        self._scale = s
        self._offset = ((cw - nw) // 2, (ch - nh) // 2)
        return img.resize((nw, nh), Image.LANCZOS)

    def _show_before(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            self._orig_before = img
            disp = self._fit(img, self.before_cv)
            bg = Image.new("RGB", disp.size, (10, 10, 26))
            bg.paste(disp, mask=disp.split()[3])
            self._tk_before = ImageTk.PhotoImage(bg)
            self.before_cv.delete("all")
            cw = self.before_cv.winfo_width() or 400
            ch = self.before_cv.winfo_height() or 300
            self.before_cv.create_image(cw // 2, ch // 2, anchor="center",
                                        image=self._tk_before)
        except: pass

    def _show_after(self, img, src_path=None, out_path=None):
        self._orig_after = img.copy()
        self._edit_after = img.copy()
        self._src_path = src_path
        self._out_path = out_path
        self.last_result_img = img
        self.last_result_path = out_path
        self._refresh_after()

    def _refresh_after(self):
        if not hasattr(self, "_edit_after"):
            return
        disp = self._fit(self._edit_after, self.after_cv)
        if self.checker_var.get():
            bg = self._checker(disp.size)
        else:
            bg = Image.new("RGB", disp.size, (10, 10, 26))
        bg.paste(disp, mask=disp.split()[3])
        self._tk_after = ImageTk.PhotoImage(bg)
        self.after_cv.delete("all")
        cw = self.after_cv.winfo_width() or 400
        ch = self.after_cv.winfo_height() or 300
        self.after_cv.create_image(cw // 2, ch // 2, anchor="center",
                                   image=self._tk_after)

    def _checker(self, size, sq=14):
        img = Image.new("RGB", size)
        d = ImageDraw.Draw(img)
        for y in range(0, size[1], sq):
            for x in range(0, size[0], sq):
                c = (170, 170, 170) if (x // sq + y // sq) % 2 == 0 else (100, 100, 100)
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=c)
        return img

    # ── Erase / Restore tools ─────────────────────────────────────
    def _toggle_erase(self):
        if self.tool_mode == "erase":
            self.tool_mode = "none"
            self.erase_btn.config(bg=CARD2, fg=FG2)
        else:
            self.tool_mode = "erase"
            self.erase_btn.config(bg=RED, fg="white")
            self.restore_btn.config(bg=CARD2, fg=FG2)

    def _toggle_restore(self):
        if self.tool_mode == "restore":
            self.tool_mode = "none"
            self.restore_btn.config(bg=CARD2, fg=FG2)
        else:
            self.tool_mode = "restore"
            self.restore_btn.config(bg=GREEN_DIM, fg="white")
            self.erase_btn.config(bg=CARD2, fg=FG2)

    def _on_canvas_draw(self, event):
        if self.tool_mode == "none" or not hasattr(self, "_edit_after"):
            return
        if not hasattr(self, "_scale"):
            return

        ox, oy = self._offset
        ix = int((event.x - ox) / self._scale)
        iy = int((event.y - oy) / self._scale)
        r = max(1, int(self.brush_var.get() / self._scale))

        img = self._edit_after
        orig = self._orig_before if hasattr(self, "_orig_before") else None

        if self.tool_mode == "erase":
            mask = Image.new("L", img.size, 0)
            d = ImageDraw.Draw(mask)
            d.ellipse([ix - r, iy - r, ix + r, iy + r], fill=255)
            r_ch, g_ch, b_ch, a_ch = img.split()
            new_a = self._subtract_alpha(a_ch, mask)
            self._edit_after = Image.merge("RGBA", (r_ch, g_ch, b_ch, new_a))

        elif self.tool_mode == "restore" and orig is not None:
            orig_rgba = orig.convert("RGBA")
            mask = Image.new("L", img.size, 0)
            d = ImageDraw.Draw(mask)
            d.ellipse([ix - r, iy - r, ix + r, iy + r], fill=255)
            result = self._edit_after.copy()
            result.paste(orig_rgba, mask=mask)
            self._edit_after = result

        self._refresh_after()

    def _subtract_alpha(self, alpha_ch, mask):
        import numpy as np
        a = np.array(alpha_ch, dtype=np.int16)
        m = np.array(mask, dtype=np.int16)
        result = np.clip(a - m, 0, 255).astype(np.uint8)
        return Image.fromarray(result, mode="L")

    def _save_edit(self):
        if not hasattr(self, "_edit_after") or self._out_path is None:
            self.status_lbl.config(text="\u26A0 Kein Bild zum Speichern", fg=ACC)
            return
        self._edit_after.save(self._out_path, "PNG")
        self.status_lbl.config(text=f"\u2713 Gespeichert: {self._out_path.name}", fg=GREEN)
        self._log(f"Edit gespeichert: {self._out_path}")

    def _reset_edit(self):
        if hasattr(self, "_orig_after"):
            self._edit_after = self._orig_after.copy()
            self._refresh_after()
            self.status_lbl.config(text="\u21A9 Zur\u00fcckgesetzt", fg=FG2)


# ── Entry ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except Exception:
        root = tk.Tk()

    # Style ttk widgets
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TProgressbar", troughcolor="#0a0a18",
                    background=ACC, thickness=11)
    style.configure("Dark.Vertical.TScrollbar",
                    background=CARD2, troughcolor=PANEL,
                    borderwidth=0, arrowsize=8, relief="flat")
    style.map("Dark.Vertical.TScrollbar",
              background=[("active", ACC_DIM), ("pressed", ACC)])
    style.configure("TCombobox", fieldbackground=CARD, background=CARD2,
                    foreground=FG, selectbackground=ACC)

    app = HoneyClean(root)
    root.mainloop()
