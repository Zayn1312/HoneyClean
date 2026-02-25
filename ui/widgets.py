"""
HoneyClean – Shared widgets mixin (toast, status bar, dialogs, system integration)
"""

import os
import sys
import subprocess
import webbrowser
import json
from pathlib import Path

import customtkinter as ctk

from ui.theme import C, FONT
from core.i18n import t
from core.utils import _auto_install


class WidgetsMixin:

    def _build_status_bar(self):
        sb = ctk.CTkFrame(self._content, fg_color=C["card"], height=28, corner_radius=0)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self._sb_processed = ctk.CTkLabel(sb, text="\U0001f5bc 0 processed", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_processed.pack(side="left", padx=12)
        self._sb_speed = ctk.CTkLabel(sb, text="\u26a1 --", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_speed.pack(side="left", padx=8)
        self._sb_eta = ctk.CTkLabel(sb, text="", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_eta.pack(side="left", padx=8)
        self._sb_file = ctk.CTkLabel(sb, text="", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_file.pack(side="left", padx=8)
        self._sb_queued = ctk.CTkLabel(sb, text="\U0001f4cb 0 queued", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_queued.pack(side="left", padx=8)
        self._sb_gpu = ctk.CTkLabel(sb, text="\U0001f3ae GPU: --", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_gpu.pack(side="left", padx=8)
        self._sb_state = ctk.CTkLabel(sb, text="\u25cf Ready", font=(FONT, 9), text_color=C["success"])
        self._sb_state.pack(side="right", padx=12)
        self._sb_shortcuts = ctk.CTkLabel(sb, text=t("shortcut_hint"), font=(FONT, 8), text_color=C["text_dim"])
        self._sb_shortcuts.pack(side="right", padx=8)

    def _show_toast(self, message, toast_type="success"):
        clrs = {"success": C["success"], "warning": C["warning"], "error": C["error"], "info": C["accent"]}
        toast = ctk.CTkLabel(self, text=f"  {message}  ", fg_color=clrs.get(toast_type, C["accent"]),
                              corner_radius=8, font=(FONT, 11), text_color="#FFFFFF", height=36)
        toast.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-50)
        self.after(3000, lambda: toast.destroy())

    def _open_folder(self, path):
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _open_url(self, url):
        webbrowser.open(url)

    def _toggle_fullscreen(self):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _show_dep_dialog(self, missing):
        dlg = ctk.CTkToplevel(self)
        dlg.title(t("dep_title"))
        dlg.geometry("400x300")
        dlg.configure(fg_color=C["bg"])
        ctk.CTkLabel(dlg, text=t("dep_missing"), font=(FONT, 13), text_color=C["text"]).pack(pady=16)
        for name, info in missing:
            ctk.CTkLabel(dlg, text=f"  \u2022 {name} ({info['pip']})", font=(FONT, 11),
                         text_color=C["text_muted"]).pack(anchor="w", padx=20)
        def install():
            for _, info in missing: _auto_install(info["pip"])
            dlg.destroy()
            self._build_ui()
        ctk.CTkButton(dlg, text=t("dep_install"), fg_color=C["accent"], cursor="hand2",
                      command=install).pack(pady=16)

    def _show_crash_dialog(self, report):
        try:
            dlg = ctk.CTkToplevel(self)
            dlg.title(t("crash_title"))
            dlg.geometry("500x400")
            dlg.configure(fg_color=C["bg"])
            dlg.transient(self)
            dlg.grab_set()
            dlg.resizable(False, False)
            ctk.CTkLabel(dlg, text="\u26a0", font=(FONT, 48), text_color=C["error"]).pack(pady=(20, 8))
            ctk.CTkLabel(dlg, text=t("crash_title"), font=(FONT, 16, "bold"), text_color=C["text"]).pack(pady=4)
            err_type = report.get("error", {}).get("type", "Unknown")
            err_msg = report.get("error", {}).get("message", "Unknown error")
            ctk.CTkLabel(dlg, text=f"{err_type}: {err_msg[:120]}", font=(FONT, 11),
                         text_color=C["text_muted"], wraplength=440).pack(padx=20, pady=4)
            suggestion = report.get("recovery_suggestion", "Try restarting HoneyClean")
            ctk.CTkLabel(dlg, text=f"Suggestion: {suggestion}", font=(FONT, 11),
                         text_color=C["accent"], wraplength=440).pack(padx=20, pady=(4, 12))
            bf = ctk.CTkFrame(dlg, fg_color="transparent")
            bf.pack(pady=12)
            def copy_report():
                try:
                    self.clipboard_clear()
                    self.clipboard_append(json.dumps(report, indent=2))
                    self._show_toast("Crash report copied!", "info")
                except Exception:
                    pass
            ctk.CTkButton(bf, text=t("crash_copy"), width=140, height=36, fg_color=C["accent"],
                          hover_color=C["accent_hover"], cursor="hand2", command=copy_report).pack(side="left", padx=4)
            crash_dir = str(Path(os.environ.get("APPDATA", ".")) / "HoneyClean" / "crashes")
            ctk.CTkButton(bf, text=t("crash_open_folder"), width=140, height=36, fg_color=C["card_hover"],
                          hover_color=C["border"], cursor="hand2",
                          command=lambda: self._open_folder(crash_dir)).pack(side="left", padx=4)
            ctk.CTkButton(bf, text=t("dismiss"), width=90, height=36, fg_color=C["card_hover"],
                          hover_color=C["border"], cursor="hand2", command=dlg.destroy).pack(side="left", padx=4)
        except Exception:
            pass
