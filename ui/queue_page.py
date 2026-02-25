"""
HoneyClean – Queue page mixin
"""

import subprocess
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from PIL import Image

from ui.theme import C, FONT
from core.i18n import t
from core.config import QUALITY_PRESETS, MODEL_INFO, save_cfg
from core.utils import _validate_path, _validate_image, _extract_zip


class QueuePageMixin:

    def _build_queue_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self._pages["queue"] = page

        # Drop zone
        self._drop_frame = ctk.CTkFrame(page, height=100, fg_color=C["card"], border_width=2,
                                         border_color=C["border"], corner_radius=12, cursor="hand2")
        self._drop_frame.pack(fill="x", padx=16, pady=(16, 8))
        self._drop_frame.pack_propagate(False)
        self._drop_lbl = ctk.CTkLabel(self._drop_frame, text=f"\U0001f4c2  {t('drop_zone')}",
                                       font=(FONT, 13), text_color=C["text_muted"])
        self._drop_lbl.pack(expand=True)
        for w in (self._drop_frame, self._drop_lbl):
            w.bind("<Button-1>", lambda e: self._browse_files())
        self._drop_frame.bind("<Enter>", lambda e: self._drop_frame.configure(border_color=C["accent"]))
        self._drop_frame.bind("<Leave>", lambda e: self._drop_frame.configure(border_color=C["border"]))

        # Toolbar
        tb = ctk.CTkFrame(page, fg_color="transparent", height=40)
        tb.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(tb, text=f"\U0001f4c1 {t('add_folder')}", width=110, height=32, corner_radius=8,
                      fg_color=C["card"], hover_color=C["card_hover"], cursor="hand2",
                      command=self._browse_folder).pack(side="left", padx=(0, 4))
        ctk.CTkButton(tb, text=f"\U0001f5d1 {t('clear_queue')}", width=80, height=32, corner_radius=8,
                      fg_color=C["card"], hover_color=C["card_hover"], cursor="hand2",
                      command=self._clear_queue).pack(side="left", padx=4)
        self._preset_seg = ctk.CTkSegmentedButton(tb, values=["\u26a1Fast", "\u2696\ufe0fBalanced", "\u2728Quality", "\U0001f3a8Anime", "\U0001f464Portrait"],
                                                   command=self._on_preset_change, height=30)
        self._preset_seg.pack(side="right")
        self._preset_seg.set("\u2728Quality")

        # Queue management row
        mgmt = ctk.CTkFrame(page, fg_color="transparent", height=32)
        mgmt.pack(fill="x", padx=16, pady=2)
        self._sel_btn = ctk.CTkButton(mgmt, text=t("select_all"), width=100, height=28, corner_radius=6,
                                       fg_color=C["card"], hover_color=C["card_hover"], font=(FONT, 10),
                                       cursor="hand2", command=self._toggle_select_all)
        self._sel_btn.pack(side="left", padx=(0, 4))
        self._rem_btn = ctk.CTkButton(mgmt, text=f"\U0001f5d1 {t('remove_selected')}", width=130, height=28,
                                       corner_radius=6, fg_color=C["card"], hover_color=C["card_hover"],
                                       font=(FONT, 10), cursor="hand2", command=self._remove_selected)
        self._rem_btn.pack(side="left", padx=4)
        self._skip_var = ctk.BooleanVar(value=self._skip_processed)
        self._skip_sw = ctk.CTkSwitch(mgmt, text=t("skip_existing"), variable=self._skip_var,
                                       button_color=C["accent"], height=24, font=(FONT, 10),
                                       command=lambda: setattr(self, '_skip_processed', self._skip_var.get()))
        self._skip_sw.pack(side="left", padx=12)
        self._sort_menu = ctk.CTkOptionMenu(mgmt, values=[t("sort_name"), t("sort_size"), t("sort_folder")],
                                              fg_color=C["card"], button_color=C["accent"], width=100, height=28,
                                              command=self._on_sort_change)
        self._sort_menu.pack(side="right")
        ctk.CTkLabel(mgmt, text="Sort:", font=(FONT, 10), text_color=C["text_muted"]).pack(side="right", padx=(0, 4))

        # Queue header
        self._queue_hdr = ctk.CTkLabel(page, text=f"{t('queue_label')} (0)", font=(FONT, 12, "bold"),
                                        text_color=C["text"], anchor="w")
        self._queue_hdr.pack(fill="x", padx=20, pady=(8, 4))

        # Thumbnail scroll area
        self._thumb_scroll = ctk.CTkScrollableFrame(page, fg_color=C["bg"], corner_radius=0)
        self._thumb_scroll.pack(fill="both", expand=True, padx=12, pady=4)
        self._empty_frame = ctk.CTkFrame(self._thumb_scroll, fg_color="transparent")
        self._empty_frame.pack(expand=True, pady=60)
        ctk.CTkLabel(self._empty_frame, text="\u2726", font=(FONT, 48), text_color=C["text_dim"]).pack()
        ctk.CTkLabel(self._empty_frame, text=t("empty_title"), font=(FONT, 14),
                     text_color=C["text_muted"]).pack(pady=(8, 4))
        ctk.CTkLabel(self._empty_frame, text=t("empty_formats"),
                     font=(FONT, 10), text_color=C["text_dim"]).pack()
        ctk.CTkLabel(self._empty_frame, text=t("empty_tip"),
                     font=(FONT, 10), text_color=C["accent"]).pack(pady=(8, 0))

        # Progress bar
        self._pbar = ctk.CTkProgressBar(page, fg_color=C["card"], progress_color=C["accent"], height=4)
        self._pbar.pack(fill="x", padx=16, pady=0)
        self._pbar.set(0)

        # Action bar
        ab = ctk.CTkFrame(page, fg_color=C["card"], height=56, corner_radius=0)
        ab.pack(fill="x", side="bottom")
        ab.pack_propagate(False)
        left = ctk.CTkFrame(ab, fg_color="transparent")
        left.pack(side="left", padx=16, pady=8)
        self._mode_seg = ctk.CTkSegmentedButton(left, values=[t("mode_auto"), t("mode_review")],
                                                 command=self._on_mode_change, height=32, width=200)
        self._mode_seg.set(t("mode_auto") if self.cfg.get("process_mode") == "auto" else t("mode_review"))
        self._mode_seg.pack(side="left", padx=(0, 12))
        self._progress_lbl = ctk.CTkLabel(left, text="0 / 0", font=(FONT, 11), text_color=C["text_muted"])
        self._progress_lbl.pack(side="left")
        right = ctk.CTkFrame(ab, fg_color="transparent")
        right.pack(side="right", padx=16, pady=8)
        self._btn_start = ctk.CTkButton(right, text=f"\u25b6  {t('btn_start')}", width=120, height=36,
                                          fg_color=C["accent"], hover_color=C["accent_hover"],
                                          corner_radius=8, cursor="hand2", font=(FONT, 12, "bold"),
                                          command=self._start_processing)
        self._btn_start.pack(side="left", padx=4)
        self._btn_pause = ctk.CTkButton(right, text=f"\u2016  {t('btn_pause')}", width=90, height=36,
                                          fg_color=C["card_hover"], hover_color=C["border"],
                                          corner_radius=8, cursor="hand2", command=self._toggle_pause)
        self._btn_pause.pack(side="left", padx=4)
        self._btn_stop = ctk.CTkButton(right, text=f"\u25a0  {t('btn_stop')}", width=80, height=36,
                                         fg_color=C["card_hover"], hover_color=C["border"],
                                         corner_radius=8, cursor="hand2", command=self._stop_processing)
        self._btn_stop.pack(side="left", padx=4)

    # ── File Management ──────────────────────────────────────────
    def _browse_files(self):
        from tkinter import filedialog
        files = filedialog.askopenfilenames(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"), ("ZIP", "*.zip"), ("All", "*.*")])
        before = len(self.queue_items)
        for f in files:
            self._add_file(Path(f))
        added = len(self.queue_items) - before
        if added > 0:
            self._undo_queue_stack.append((before, len(self.queue_items)))
            self._show_toast(t("added_to_queue", count=added), "info")

    def _browse_folder(self):
        from tkinter import filedialog
        d = filedialog.askdirectory()
        if d:
            before = len(self.queue_items)
            for f in Path(d).rglob("*"):
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"):
                    self._add_file(f)
            added = len(self.queue_items) - before
            if added > 0:
                self._undo_queue_stack.append((before, len(self.queue_items)))
                self._show_toast(t("added_to_queue", count=added), "info")

    def _add_file(self, path):
        if path.suffix.lower() == ".zip":
            extracted, err = _extract_zip(path, self.cfg.get("output_dir", "."))
            if err:
                self._show_toast(f"ZIP Error: {err}", "error")
                return
            for p in extracted: self._add_file(p)
            return
        ok, _ = _validate_path(path)
        if not ok: return
        ok2, _ = _validate_image(path)
        if not ok2: return
        self.queue_items.append(path)
        self._add_thumbnail(path)
        self._update_queue_header()

    def _add_thumbnail(self, path):
        self._empty_frame.pack_forget()
        idx = len(self._thumb_cards)
        card = ctk.CTkFrame(self._thumb_scroll, width=140, height=160, fg_color=C["card"],
                             corner_radius=8, border_width=1, border_color=C["border"])
        cols = max(1, 5)
        card.grid(row=idx // cols, column=idx % cols, padx=4, pady=4)
        card.grid_propagate(False)
        card.bind("<Enter>", lambda e, c=card, i=idx: c.configure(
            border_color=C["accent"] if i in self._selected_cards else C["border_bright"]))
        card.bind("<Leave>", lambda e, c=card, i=idx: c.configure(
            border_color=C["accent"] if i in self._selected_cards else C["border"]))
        card.bind("<Button-1>", lambda e, i=idx: self._toggle_select_card(i))
        il = ctk.CTkLabel(card, text="", width=120, height=100)
        il.pack(pady=(8, 4))
        il.bind("<Button-1>", lambda e, i=idx: self._toggle_select_card(i))
        name = path.name[:15] + "\u2026" if len(path.name) > 18 else path.name
        ctk.CTkLabel(card, text=name, font=(FONT, 9), text_color=C["text_muted"]).pack()
        sl = ctk.CTkLabel(card, text="\u23f3 Pending", font=(FONT, 8), text_color=C["text_dim"])
        sl.pack()
        self._thumb_cards.append({"card": card, "img_label": il, "status_label": sl, "path": path})
        self._thumb_executor.submit(self._gen_thumb, idx, path, il)

    def _gen_thumb(self, idx, path, label):
        try:
            img = Image.open(path)
            img.thumbnail((120, 100), Image.LANCZOS)
            bg = Image.new("RGBA", (120, 100), (26, 26, 37, 255))
            ox, oy = (120 - img.size[0]) // 2, (100 - img.size[1]) // 2
            paste_img = img.convert("RGBA")
            bg.paste(paste_img, (ox, oy), paste_img.split()[3])
            ctk_img = ctk.CTkImage(light_image=bg, dark_image=bg, size=(120, 100))
            self._thumb_images.append(ctk_img)
            label.after(0, lambda: label.configure(image=ctk_img))
        except Exception:
            pass

    def _clear_queue(self):
        self.queue_items.clear()
        for item in self._thumb_cards: item["card"].destroy()
        self._thumb_cards.clear()
        self._thumb_images.clear()
        self._results.clear()
        self._selected_cards.clear()
        self._all_selected = False
        self._failed_items.clear()
        self._per_image_times.clear()
        self._undo_queue_stack.clear()
        self._empty_frame.pack(expand=True, pady=60)
        self._update_queue_header()

    def _update_queue_header(self):
        n = len(self.queue_items)
        self._queue_hdr.configure(text=f"{t('queue_label')} ({n})")
        self._sb_queued.configure(text=f"\U0001f4cb {n} queued")

    # ── Queue Management ─────────────────────────────────────────
    def _toggle_select_card(self, idx):
        if idx in self._selected_cards:
            self._selected_cards.discard(idx)
            if idx < len(self._thumb_cards):
                self._thumb_cards[idx]["card"].configure(border_color=C["border"])
        else:
            self._selected_cards.add(idx)
            if idx < len(self._thumb_cards):
                self._thumb_cards[idx]["card"].configure(border_color=C["accent"])

    def _toggle_select_all(self):
        if self._all_selected:
            self._selected_cards.clear()
            for item in self._thumb_cards:
                item["card"].configure(border_color=C["border"])
            self._all_selected = False
            self._sel_btn.configure(text=t("select_all"))
        else:
            self._selected_cards = set(range(len(self._thumb_cards)))
            for item in self._thumb_cards:
                item["card"].configure(border_color=C["accent"])
            self._all_selected = True
            self._sel_btn.configure(text=t("deselect_all"))

    def _remove_selected(self):
        if not self._selected_cards or self.processing:
            return
        for idx in sorted(self._selected_cards, reverse=True):
            if idx < len(self.queue_items):
                self.queue_items.pop(idx)
            if idx < len(self._thumb_cards):
                self._thumb_cards[idx]["card"].destroy()
                self._thumb_cards.pop(idx)
        self._selected_cards.clear()
        self._all_selected = False
        self._sel_btn.configure(text=t("select_all"))
        for i, item in enumerate(self._thumb_cards):
            item["card"].grid(row=i // 5, column=i % 5, padx=4, pady=4)
        self._update_queue_header()
        if not self.queue_items:
            self._empty_frame.pack(expand=True, pady=60)

    def _on_sort_change(self, val):
        m = {t("sort_name"): "name", t("sort_size"): "size", t("sort_folder"): "folder"}
        self._sort_queue(m.get(val, "name"))

    def _sort_queue(self, method):
        if not self.queue_items or self.processing:
            return
        if method == "name":
            self.queue_items.sort(key=lambda p: p.name.lower())
        elif method == "size":
            self.queue_items.sort(key=lambda p: p.stat().st_size, reverse=True)
        elif method == "folder":
            self.queue_items.sort(key=lambda p: str(p.parent).lower())
        for item in self._thumb_cards:
            item["card"].destroy()
        self._thumb_cards.clear()
        self._thumb_images.clear()
        self._selected_cards.clear()
        for path in self.queue_items:
            self._add_thumbnail(path)

    def _undo_queue_add(self):
        if not self._undo_queue_stack or self.processing:
            return
        before, after = self._undo_queue_stack.pop()
        count = min(after, len(self.queue_items)) - before
        if count <= 0:
            return
        for idx in range(min(after, len(self.queue_items)) - 1, before - 1, -1):
            if idx < len(self.queue_items):
                self.queue_items.pop(idx)
            if idx < len(self._thumb_cards):
                self._thumb_cards[idx]["card"].destroy()
                self._thumb_cards.pop(idx)
        self._selected_cards.clear()
        for i, item in enumerate(self._thumb_cards):
            item["card"].grid(row=i // 5, column=i % 5, padx=4, pady=4)
        self._update_queue_header()
        if not self.queue_items:
            self._empty_frame.pack(expand=True, pady=60)

    def _space_toggle(self, event=None):
        if self._current_page != "queue":
            return
        focused = self.focus_get()
        if isinstance(focused, (tk.Entry, ctk.CTkEntry)):
            return
        if self.processing:
            self._toggle_pause()
        elif self.queue_items:
            self._start_processing()

    def _on_preset_change(self, val):
        m = {"\u26a1Fast": "fast", "\u2696\ufe0fBalanced": "balanced", "\u2728Quality": "quality",
             "\U0001f3a8Anime": "anime", "\U0001f464Portrait": "portrait"}
        key = m.get(val, "quality")
        if key in QUALITY_PRESETS:
            self.cfg["model"] = QUALITY_PRESETS[key]["model"]
            self.cfg["quality_preset"] = key
            self.session = None
            self.session_model = None

    def _on_mode_change(self, val):
        self.cfg["process_mode"] = "auto" if t("mode_auto") in val else "review"

    def _on_drag_enter(self, event):
        self._drop_frame.configure(border_color=C["accent"], border_width=3)
        self._drop_lbl.configure(text="\U0001f4c2  Drop images here!", text_color=C["accent"])

    def _on_drag_leave(self, event):
        self._drop_frame.configure(border_color=C["border"], border_width=2)
        self._drop_lbl.configure(text=f"\U0001f4c2  {t('drop_zone')}", text_color=C["text_muted"])

    def _on_drop(self, event):
        self._drop_frame.configure(border_color=C["border"], border_width=2)
        self._drop_lbl.configure(text=f"\U0001f4c2  {t('drop_zone')}", text_color=C["text_muted"])
        before = len(self.queue_items)
        for f in self.tk.splitlist(event.data):
            self._add_file(Path(f))
        added = len(self.queue_items) - before
        if added > 0:
            self._undo_queue_stack.append((before, len(self.queue_items)))
            self._show_toast(t("added_to_queue", count=added), "info")

    def _show_batch_summary(self, done, failed, elapsed):
        dlg = ctk.CTkToplevel(self)
        dlg.title(t("batch_complete"))
        dlg.geometry("420x300")
        dlg.configure(fg_color=C["bg"])
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
        avg = round(elapsed / max(1, done + failed), 1)
        icon = "\u2713" if failed == 0 else "\u26a0"
        icon_color = C["success"] if failed == 0 else C["warning"]
        ctk.CTkLabel(dlg, text=icon, font=(FONT, 48), text_color=icon_color).pack(pady=(24, 8))
        ctk.CTkLabel(dlg, text=t("batch_stats", done=done, failed=failed, time=time_str),
                     font=(FONT, 14, "bold"), text_color=C["text"]).pack(pady=4)
        ctk.CTkLabel(dlg, text=t("batch_avg", avg=avg),
                     font=(FONT, 11), text_color=C["text_muted"]).pack(pady=2)
        bf = ctk.CTkFrame(dlg, fg_color="transparent")
        bf.pack(pady=24)
        out_dir = self.cfg.get("output_dir", "")
        ctk.CTkButton(bf, text=f"\U0001f4c1 {t('open_output')}", width=130, height=36,
                      fg_color=C["accent"], hover_color=C["accent_hover"], cursor="hand2",
                      command=lambda: (self._open_folder(out_dir), dlg.destroy())).pack(side="left", padx=4)
        if failed > 0 and self._failed_items:
            ctk.CTkButton(bf, text=f"\u21a9 {t('retry_failed')}", width=120, height=36,
                          fg_color=C["warning"], hover_color="#CC7A00", cursor="hand2",
                          command=lambda: (self._retry_failed(), dlg.destroy())).pack(side="left", padx=4)
        ctk.CTkButton(bf, text=t("dismiss"), width=90, height=36,
                      fg_color=C["card_hover"], hover_color=C["border"], cursor="hand2",
                      command=dlg.destroy).pack(side="left", padx=4)

    def _retry_failed(self):
        items = list(self._failed_items)
        self._clear_queue()
        for path in items:
            self._add_file(path)

    def _auto_detect_vram(self):
        if self.cfg.get("vram_auto_detected"):
            return
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            r = subprocess.run(["nvidia-smi", "--query-gpu=memory.total,name",
                                "--format=csv,noheader,nounits"], capture_output=True, text=True,
                               timeout=3, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            if r.returncode == 0:
                parts = r.stdout.strip().split(",")
                vram_mb = int(parts[0].strip())
                gpu_name = parts[1].strip()
                vram_gb = vram_mb / 1024
                if vram_gb > 8:
                    preset, seg_val = "Quality", "\u2728Quality"
                elif vram_gb >= 4:
                    preset, seg_val = "Balanced", "\u2696\ufe0fBalanced"
                else:
                    preset, seg_val = "Fast", "\u26a1Fast"
                self._preset_seg.set(seg_val)
                self._on_preset_change(seg_val)
                self._show_toast(t("auto_preset_toast", preset=preset, gpu=f"{gpu_name} ({int(vram_gb)}GB)"), "info")
                self.cfg["vram_auto_detected"] = True
                save_cfg(self.cfg)
        except Exception:
            pass
