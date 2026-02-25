"""
HoneyClean – Settings page mixin
"""

import customtkinter as ctk

from ui.theme import C, FONT
from core.i18n import t, set_language
from core.config import MODEL_INFO, MODEL_ORDER, save_cfg


class SettingsPageMixin:

    def _build_settings_page(self):
        page = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self._pages["settings"] = page
        ctk.CTkLabel(page, text=t("settings_title"), font=(FONT, 20, "bold"), text_color=C["text"]).pack(anchor="w", padx=20, pady=(20, 16))

        # General
        gc = ctk.CTkFrame(page, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
        gc.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(gc, text=t("section_general"), font=(FONT, 13, "bold"), text_color=C["accent"]).pack(anchor="w", padx=16, pady=(12, 8))
        r1 = ctk.CTkFrame(gc, fg_color="transparent"); r1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(r1, text=t("output_dir"), font=(FONT, 11), text_color=C["text_muted"], width=120, anchor="w").pack(side="left")
        self._out_entry = ctk.CTkEntry(r1, fg_color=C["card_hover"], border_color=C["border"], text_color=C["text"], width=300)
        self._out_entry.pack(side="left", padx=4)
        self._out_entry.insert(0, self.cfg.get("output_dir", ""))
        ctk.CTkButton(r1, text=t("browse"), width=70, height=28, corner_radius=6, fg_color=C["card_hover"],
                      cursor="hand2", command=self._browse_output).pack(side="left", padx=4)
        r2 = ctk.CTkFrame(gc, fg_color="transparent"); r2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(r2, text=t("language"), font=(FONT, 11), text_color=C["text_muted"], width=120, anchor="w").pack(side="left")
        self._lang_menu = ctk.CTkOptionMenu(r2, values=["English", "Deutsch", "Fran\u00e7ais", "Espa\u00f1ol", "\u4e2d\u6587"],
                                             fg_color=C["card_hover"], button_color=C["accent"], width=160,
                                             command=self._on_lang_change)
        lm = {"en": "English", "de": "Deutsch", "fr": "Fran\u00e7ais", "es": "Espa\u00f1ol", "zh": "\u4e2d\u6587"}
        self._lang_menu.set(lm.get(self.cfg.get("language", "en"), "English"))
        self._lang_menu.pack(side="left", padx=4)
        r3 = ctk.CTkFrame(gc, fg_color="transparent"); r3.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(r3, text=t("output_format"), font=(FONT, 11), text_color=C["text_muted"], width=120, anchor="w").pack(side="left")
        self._fmt_seg = ctk.CTkSegmentedButton(r3, values=["PNG", "JPEG", "WebP"], height=28, width=200)
        self._fmt_seg.set(self.cfg.get("output_format", "png").upper())
        self._fmt_seg.pack(side="left", padx=4)
        r4 = ctk.CTkFrame(gc, fg_color="transparent"); r4.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(r4, text=t("platform_preset"), font=(FONT, 11), text_color=C["text_muted"], width=120, anchor="w").pack(side="left")
        self._platform_menu = ctk.CTkOptionMenu(r4, values=["None", "Amazon", "Shopify", "Etsy", "eBay", "Instagram"],
                                                  fg_color=C["card_hover"], button_color=C["accent"], width=160,
                                                  command=self._on_platform_change)
        self._platform_menu.set(self.cfg.get("platform_preset", "None"))
        self._platform_menu.pack(side="left", padx=4)

        # AI Engine
        ac = ctk.CTkFrame(page, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
        ac.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(ac, text=t("section_ai"), font=(FONT, 13, "bold"), text_color=C["accent"]).pack(anchor="w", padx=16, pady=(12, 8))
        mr = ctk.CTkFrame(ac, fg_color="transparent"); mr.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(mr, text=t("ai_model"), font=(FONT, 11), text_color=C["text_muted"], width=120, anchor="w").pack(side="left")
        model_names = [t(MODEL_INFO[m]["name_key"]) for m in MODEL_ORDER]
        self._model_menu = ctk.CTkOptionMenu(mr, values=model_names, fg_color=C["card_hover"],
                                              button_color=C["accent"], width=280, command=self._on_model_change)
        cm = self.cfg.get("model", "auto")
        if cm in MODEL_INFO: self._model_menu.set(t(MODEL_INFO[cm]["name_key"]))
        self._model_menu.pack(side="left", padx=4)
        self._model_desc_lbl = ctk.CTkLabel(ac, text="", font=(FONT, 10), text_color=C["text_dim"], anchor="w")
        self._model_desc_lbl.pack(fill="x", padx=36, pady=(0, 8))
        self._update_model_desc()

        self._alpha_vars = {}
        for key, lkey, default, mx in [("alpha_fg", "alpha_fg_label", 270, 300),
                                        ("alpha_bg", "alpha_bg_label", 20, 100),
                                        ("alpha_erode", "alpha_erode_label", 15, 50)]:
            row = ctk.CTkFrame(ac, fg_color="transparent"); row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text=t(lkey), font=(FONT, 11), text_color=C["text_muted"], width=120, anchor="w").pack(side="left")
            var = ctk.IntVar(value=self.cfg.get(key, default))
            ctk.CTkSlider(row, from_=0, to=mx, variable=var, width=180, button_color=C["accent"]).pack(side="left", padx=4)
            vl = ctk.CTkLabel(row, text=str(var.get()), font=(FONT, 10), text_color=C["text_muted"], width=40)
            vl.pack(side="left")
            var.trace_add("write", lambda *_, v=var, l=vl: l.configure(text=str(v.get())))
            self._alpha_vars[key] = var

        self._decontam_var = ctk.BooleanVar(value=self.cfg.get("color_decontaminate", True))
        ctk.CTkSwitch(ac, text="Color Decontamination", variable=self._decontam_var,
                      button_color=C["accent"]).pack(anchor="w", padx=16, pady=(4, 12))

        # GPU
        gpc = ctk.CTkFrame(page, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
        gpc.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(gpc, text=t("section_gpu"), font=(FONT, 13, "bold"), text_color=C["accent"]).pack(anchor="w", padx=16, pady=(12, 8))
        self._gpu_var = ctk.BooleanVar(value=self.cfg.get("use_gpu", True))
        ctk.CTkSwitch(gpc, text=t("use_gpu_label"), variable=self._gpu_var,
                      button_color=C["accent"]).pack(anchor="w", padx=16, pady=4)
        gr = ctk.CTkFrame(gpc, fg_color="transparent"); gr.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(gr, text=t("gpu_limit_label"), font=(FONT, 11), text_color=C["text_muted"], width=120, anchor="w").pack(side="left")
        self._gpu_limit_var = ctk.IntVar(value=self.cfg.get("gpu_limit", 100))
        ctk.CTkSlider(gr, from_=0, to=100, variable=self._gpu_limit_var, width=180,
                      button_color=C["accent"]).pack(side="left", padx=4)
        self._gpu_limit_lbl = ctk.CTkLabel(gr, text=f"{self._gpu_limit_var.get()}%", font=(FONT, 10),
                                            text_color=C["text_muted"], width=40)
        self._gpu_limit_lbl.pack(side="left")
        self._gpu_limit_var.trace_add("write", lambda *_: self._gpu_limit_lbl.configure(text=f"{self._gpu_limit_var.get()}%"))

        # Video
        vc = ctk.CTkFrame(page, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
        vc.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(vc, text=t("section_video"), font=(FONT, 13, "bold"), text_color=C["accent"]).pack(anchor="w", padx=16, pady=(12, 8))
        vr1 = ctk.CTkFrame(vc, fg_color="transparent"); vr1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(vr1, text=t("video_format"), font=(FONT, 11), text_color=C["text_muted"], width=140, anchor="w").pack(side="left")
        self._vid_fmt_seg = ctk.CTkSegmentedButton(vr1, values=["WebM", "MOV", "PNG Seq", "MP4 Green"],
                                                     height=28, width=280)
        vfm = {"webm": "WebM", "mov": "MOV", "png_sequence": "PNG Seq", "mp4_greenscreen": "MP4 Green"}
        self._vid_fmt_seg.set(vfm.get(self.cfg.get("video_format", "webm"), "WebM"))
        self._vid_fmt_seg.pack(side="left", padx=4)
        vr2 = ctk.CTkFrame(vc, fg_color="transparent"); vr2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(vr2, text=t("temporal_smooth"), font=(FONT, 11), text_color=C["text_muted"], width=140, anchor="w").pack(side="left")
        self._temporal_var = ctk.IntVar(value=self.cfg.get("temporal_smoothing", 40))
        ctk.CTkSlider(vr2, from_=0, to=100, variable=self._temporal_var, width=180,
                      button_color=C["accent"]).pack(side="left", padx=4)
        self._temporal_lbl = ctk.CTkLabel(vr2, text=f"{self._temporal_var.get()}%", font=(FONT, 10),
                                           text_color=C["text_muted"], width=40)
        self._temporal_lbl.pack(side="left")
        self._temporal_var.trace_add("write", lambda *_: self._temporal_lbl.configure(text=f"{self._temporal_var.get()}%"))
        vr3 = ctk.CTkFrame(vc, fg_color="transparent"); vr3.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(vr3, text=t("edge_refine"), font=(FONT, 11), text_color=C["text_muted"], width=140, anchor="w").pack(side="left")
        self._edge_ref_var = ctk.IntVar(value=self.cfg.get("edge_refinement", 2))
        ctk.CTkSlider(vr3, from_=0, to=10, variable=self._edge_ref_var, width=180,
                      button_color=C["accent"]).pack(side="left", padx=4)
        self._edge_ref_lbl = ctk.CTkLabel(vr3, text=str(self._edge_ref_var.get()), font=(FONT, 10),
                                           text_color=C["text_muted"], width=40)
        self._edge_ref_lbl.pack(side="left")
        self._edge_ref_var.trace_add("write", lambda *_: self._edge_ref_lbl.configure(text=str(self._edge_ref_var.get())))
        self._preserve_audio_var = ctk.BooleanVar(value=self.cfg.get("preserve_audio", True))
        ctk.CTkSwitch(vc, text=t("preserve_audio"), variable=self._preserve_audio_var,
                      button_color=C["accent"]).pack(anchor="w", padx=16, pady=(4, 12))

        # Visual Effects
        vxc = ctk.CTkFrame(page, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
        vxc.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(vxc, text=t("section_visual"), font=(FONT, 13, "bold"), text_color=C["accent"]).pack(anchor="w", padx=16, pady=(12, 8))
        self._hex_bg_var = ctk.BooleanVar(value=self.cfg.get("show_hex_bg", True))
        ctk.CTkSwitch(vxc, text=t("hex_bg_label"), variable=self._hex_bg_var,
                      button_color=C["accent"]).pack(anchor="w", padx=16, pady=3)
        self._smoke_var = ctk.BooleanVar(value=self.cfg.get("show_smoke", True))
        ctk.CTkSwitch(vxc, text=t("smoke_label"), variable=self._smoke_var,
                      button_color=C["accent"]).pack(anchor="w", padx=16, pady=3)
        self._drips_var = ctk.BooleanVar(value=self.cfg.get("show_drips", True))
        ctk.CTkSwitch(vxc, text=t("drip_label"), variable=self._drips_var,
                      button_color=C["accent"]).pack(anchor="w", padx=16, pady=3)
        efr = ctk.CTkFrame(vxc, fg_color="transparent"); efr.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(efr, text=t("effects_fps_label"), font=(FONT, 11), text_color=C["text_muted"], width=140, anchor="w").pack(side="left")
        self._efx_fps_var = ctk.IntVar(value=self.cfg.get("effects_fps", 30))
        ctk.CTkSlider(efr, from_=10, to=60, variable=self._efx_fps_var, width=140,
                      button_color=C["accent"]).pack(side="left", padx=4)
        self._efx_fps_lbl = ctk.CTkLabel(efr, text=f"{self._efx_fps_var.get()} FPS", font=(FONT, 10),
                                          text_color=C["text_muted"], width=50)
        self._efx_fps_lbl.pack(side="left")
        self._efx_fps_var.trace_add("write", lambda *_: self._efx_fps_lbl.configure(text=f"{self._efx_fps_var.get()} FPS"))
        self._intro_var = ctk.BooleanVar(value=self.cfg.get("show_intro", True))
        ctk.CTkSwitch(vxc, text=t("intro_video_label"), variable=self._intro_var,
                      button_color=C["accent"]).pack(anchor="w", padx=16, pady=(3, 12))

        ctk.CTkButton(page, text=f"\U0001f4be  {t('save_settings')}", width=200, height=40, fg_color=C["accent"],
                      hover_color=C["accent_hover"], corner_radius=8, cursor="hand2", font=(FONT, 12, "bold"),
                      command=self._save_settings).pack(pady=20)

    def _on_lang_change(self, val):
        m = {"English": "en", "Deutsch": "de", "Fran\u00e7ais": "fr", "Espa\u00f1ol": "es", "\u4e2d\u6587": "zh"}
        self.cfg["language"] = m.get(val, "en")
        set_language(self.cfg["language"])

    def _on_model_change(self, val):
        for mid, info in MODEL_INFO.items():
            if t(info["name_key"]) == val:
                old = self.cfg.get("model")
                self.cfg["model"] = mid
                self.session = None
                self.session_model = None
                self._update_model_desc()
                if old != mid:
                    self._show_toast(t("model_reload"), "info")
                break

    def _update_model_desc(self):
        m = self.cfg.get("model", "auto")
        if m in MODEL_INFO:
            self._model_desc_lbl.configure(text=t(MODEL_INFO[m]["desc_key"]))

    def _browse_output(self):
        from tkinter import filedialog
        d = filedialog.askdirectory()
        if d:
            self._out_entry.delete(0, "end")
            self._out_entry.insert(0, d)

    def _save_settings(self):
        self.cfg["output_dir"] = self._out_entry.get()
        for k, v in self._alpha_vars.items():
            self.cfg[k] = v.get()
        self.cfg["use_gpu"] = self._gpu_var.get()
        self.cfg["gpu_limit"] = self._gpu_limit_var.get()
        self.cfg["color_decontaminate"] = self._decontam_var.get()
        self.cfg["output_format"] = self._fmt_seg.get().lower()
        self.cfg["platform_preset"] = self._platform_menu.get()
        self.cfg["skip_processed"] = self._skip_var.get()
        # Video settings
        vfm_rev = {"WebM": "webm", "MOV": "mov", "PNG Seq": "png_sequence", "MP4 Green": "mp4_greenscreen"}
        self.cfg["video_format"] = vfm_rev.get(self._vid_fmt_seg.get(), "webm")
        self.cfg["temporal_smoothing"] = self._temporal_var.get()
        self.cfg["edge_refinement"] = self._edge_ref_var.get()
        self.cfg["preserve_audio"] = self._preserve_audio_var.get()
        # Visual settings
        self.cfg["show_hex_bg"] = self._hex_bg_var.get()
        self.cfg["show_smoke"] = self._smoke_var.get()
        self.cfg["show_drips"] = self._drips_var.get()
        self.cfg["effects_fps"] = self._efx_fps_var.get()
        self.cfg["show_intro"] = self._intro_var.get()
        save_cfg(self.cfg)
        self._show_toast(t("settings_saved"), "success")
