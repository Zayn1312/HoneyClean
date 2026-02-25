"""
HoneyClean – Editor page mixin
"""

import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from PIL import Image, ImageTk

from ui.theme import C, FONT
from core.i18n import t
from core.config import PLATFORM_PRESETS
from core.image_ops import _make_checker


class EditorPageMixin:

    def _build_editor_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self._pages["editor"] = page

        tb = ctk.CTkFrame(page, fg_color=C["card"], height=48, corner_radius=0)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        self._tool_seg = ctk.CTkSegmentedButton(tb, values=[f"\U0001f58a {t('erase')}", f"\u2726 {t('restore')}"],
                                                  command=self._on_tool_change, height=30, width=180)
        self._tool_seg.pack(side="left", padx=(12, 8), pady=8)
        self._tool_seg.set(f"\U0001f58a {t('erase')}")
        ctk.CTkLabel(tb, text=t("brush_size"), font=(FONT, 10), text_color=C["text_muted"]).pack(side="left", padx=(8, 4))
        self._size_var = ctk.IntVar(value=15)
        ctk.CTkSlider(tb, from_=1, to=100, variable=self._size_var, width=100, height=16,
                      button_color=C["accent"]).pack(side="left")
        self._size_lbl = ctk.CTkLabel(tb, text="15px", font=(FONT, 10), text_color=C["text_muted"], width=40)
        self._size_lbl.pack(side="left")
        self._size_var.trace_add("write", lambda *_: self._size_lbl.configure(text=f"{self._size_var.get()}px"))
        ctk.CTkLabel(tb, text=t("edge_feather"), font=(FONT, 10), text_color=C["text_muted"]).pack(side="left", padx=(12, 4))
        self._feather_var = ctk.IntVar(value=0)
        ctk.CTkSlider(tb, from_=0, to=20, variable=self._feather_var, width=80, height=16,
                      button_color=C["accent"]).pack(side="left")
        ctk.CTkButton(tb, text="\u21a9", width=32, height=32, corner_radius=8, fg_color=C["card_hover"],
                      cursor="hand2", command=self._undo).pack(side="left", padx=(12, 2))
        ctk.CTkButton(tb, text="\u21aa", width=32, height=32, corner_radius=8, fg_color=C["card_hover"],
                      cursor="hand2", command=self._redo).pack(side="left", padx=2)
        ctk.CTkButton(tb, text=f"\U0001f4be  {t('save')}", width=90, height=32, fg_color=C["success"],
                      hover_color="#2aa84a", cursor="hand2", corner_radius=8,
                      command=self._save_current).pack(side="right", padx=(4, 12))
        ctk.CTkButton(tb, text=t("reset"), width=70, height=32, fg_color=C["card_hover"],
                      cursor="hand2", corner_radius=8, command=self._reset_editor).pack(side="right", padx=4)

        self._editor_canvas = tk.Canvas(page, bg=C["bg"], highlightthickness=0, cursor="sb_h_double_arrow")
        self._editor_canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self._editor_canvas.bind("<ButtonPress-1>", self._editor_press)
        self._editor_canvas.bind("<B1-Motion>", self._editor_drag)
        self._editor_canvas.bind("<ButtonRelease-1>", self._editor_release)
        self._editor_canvas.bind("<Configure>", lambda e: self._render_editor())

        ps = ctk.CTkFrame(page, fg_color=C["card"], height=44, corner_radius=0)
        ps.pack(fill="x")
        ps.pack_propagate(False)
        ctk.CTkLabel(ps, text="Shadow:", font=(FONT, 10), text_color=C["text_muted"]).pack(side="left", padx=(12, 4), pady=6)
        self._shadow_seg = ctk.CTkSegmentedButton(ps, values=["None", "Drop", "Float", "Contact"],
                                                    command=self._on_shadow_change, height=28, width=240)
        self._shadow_seg.set("None")
        self._shadow_seg.pack(side="left", padx=4, pady=6)
        ctk.CTkLabel(ps, text="Background:", font=(FONT, 10), text_color=C["text_muted"]).pack(side="left", padx=(16, 4), pady=6)
        self._bg_seg = ctk.CTkSegmentedButton(ps, values=["Transparent", "White", "Color\u2026"],
                                                command=self._on_bg_change, height=28, width=220)
        self._bg_seg.set("Transparent")
        self._bg_seg.pack(side="left", padx=4, pady=6)

    def _editor_press(self, e):
        self._dragging_divider = True

    def _editor_drag(self, e):
        if self._dragging_divider:
            w = self._editor_canvas.winfo_width()
            if w > 0:
                self._divider_pos = max(0.02, min(0.98, e.x / w))
                self._render_editor()

    def _editor_release(self, e):
        self._dragging_divider = False

    def _render_editor(self):
        if not self._editor_before_img or not self._editor_after_img: return
        w, h = self._editor_canvas.winfo_width(), self._editor_canvas.winfo_height()
        if w < 10 or h < 10: return
        div = int(w * self._divider_pos)
        before_r = self._editor_before_img.resize((w, h), Image.LANCZOS)
        after_r = self._editor_after_img.resize((w, h), Image.LANCZOS)
        checker = _make_checker(w, h).convert("RGBA")
        checker.paste(after_r, mask=after_r.split()[3])
        after_comp = checker
        combined = Image.new("RGBA", (w, h))
        combined.paste(before_r.crop((0, 0, div, h)), (0, 0))
        combined.paste(after_comp.crop((div, 0, w, h)), (div, 0))
        self._editor_tk_img = ImageTk.PhotoImage(combined)
        self._editor_canvas.delete("all")
        self._editor_canvas.create_image(0, 0, anchor="nw", image=self._editor_tk_img)
        self._editor_canvas.create_line(div, 0, div, h, fill="#FFFFFF", width=2, dash=(4, 4))
        self._editor_canvas.create_oval(div - 14, h // 2 - 14, div + 14, h // 2 + 14,
                                         fill=C["accent"], outline="#FFF", width=2)
        self._editor_canvas.create_text(max(8, div - 8), 18, text="BEFORE", fill="white", anchor="e", font=(FONT, 9, "bold"))
        self._editor_canvas.create_text(min(w - 8, div + 8), 18, text="AFTER", fill="white", anchor="w", font=(FONT, 9, "bold"))

    def _on_tool_change(self, val): pass
    def _on_shadow_change(self, val): self.cfg["shadow_type"] = val.lower()

    def _on_bg_change(self, val):
        if "Color" in val:
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Choose background color")
            if color[0]:
                self._bg_color = tuple(int(c) for c in color[0])

    def _on_platform_change(self, val):
        self.cfg["platform_preset"] = val

    def _save_current(self):
        if self._results:
            out_dir = Path(self.cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
            out_dir.mkdir(parents=True, exist_ok=True)
            path, _, result = self._results[-1]
            result.save(str(out_dir / f"{path.stem}_clean.png"), "PNG")
            self._show_toast(t("status_saved", name=path.stem), "success")

    def _reset_editor(self):
        if self._results:
            self._editor_after_img = self._results[-1][2].copy()
            self._render_editor()

    def _undo(self):
        if self._history:
            self._redo_stack.append(self._editor_after_img.copy() if self._editor_after_img else None)
            self._editor_after_img = self._history.pop()
            self._render_editor()

    def _redo(self):
        if self._redo_stack:
            if self._editor_after_img: self._history.append(self._editor_after_img.copy())
            self._editor_after_img = self._redo_stack.pop()
            self._render_editor()
