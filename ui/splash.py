"""
HoneyClean – Splash / EULA mixin
"""

import time
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw

from ui.theme import C, FONT
from core.i18n import t, set_language
from core.config import VERSION, save_cfg
from core.utils import _find_logo, _find_trailer


class SplashMixin:

    # ── EULA ─────────────────────────────────────────────────────
    def _show_eula(self):
        self._eula_frame = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._eula_frame.pack(fill="both", expand=True)
        center = ctk.CTkFrame(self._eula_frame, fg_color=C["card"], corner_radius=12, width=520, height=520)
        center.pack(expand=True)
        center.pack_propagate(False)
        ctk.CTkLabel(center, text="\U0001f36f HoneyClean", font=(FONT, 22, "bold"),
                     text_color=C["accent"]).pack(pady=(24, 4))
        ctk.CTkLabel(center, text=t("eula_title"), font=(FONT, 14), text_color=C["text"]).pack(pady=(0, 12))
        lang_row = ctk.CTkFrame(center, fg_color="transparent")
        lang_row.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(lang_row, text=t("eula_language"), font=(FONT, 11), text_color=C["text_muted"]).pack(side="left")
        ctk.CTkOptionMenu(lang_row, values=["English", "Deutsch", "Fran\u00e7ais", "Espa\u00f1ol", "\u4e2d\u6587"],
                          fg_color=C["card_hover"], button_color=C["accent"], width=140,
                          command=self._eula_lang_change).pack(side="right")
        eula_text = ctk.CTkTextbox(center, fg_color=C["card_hover"], text_color=C["text"],
                                   width=460, height=200, corner_radius=8)
        eula_text.pack(padx=24, pady=8)
        eula_text.insert("1.0", "Terms of Use\n\nHoneyClean is free, open-source software under the MIT License.\n\n"
                         "By using this software, you agree to:\n1. Use it responsibly and ethically\n"
                         "2. Not use it for illegal purposes\n3. Not claim it as your own work\n"
                         "4. Respect the privacy of others\n\nThe software is provided AS-IS without warranty.\n"
                         "Source: github.com/Zayn1312/HoneyClean")
        eula_text.configure(state="disabled")
        self._eula_agree = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(center, text=t("eula_checkbox"), variable=self._eula_agree,
                        checkbox_width=20, checkbox_height=20, border_color=C["border"],
                        fg_color=C["accent"]).pack(padx=24, pady=8)
        btn_row = ctk.CTkFrame(center, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(8, 24))
        ctk.CTkButton(btn_row, text=t("eula_continue"), fg_color=C["accent"],
                      hover_color=C["accent_hover"], cursor="hand2", width=120,
                      command=self._eula_accept).pack(side="right", padx=4)
        ctk.CTkButton(btn_row, text=t("eula_decline"), fg_color=C["card_hover"],
                      cursor="hand2", width=100, command=self.destroy).pack(side="right", padx=4)

    def _eula_lang_change(self, val):
        m = {"English": "en", "Deutsch": "de", "Fran\u00e7ais": "fr", "Espa\u00f1ol": "es", "\u4e2d\u6587": "zh"}
        set_language(m.get(val, "en"))

    def _eula_accept(self):
        if not self._eula_agree.get(): return
        self.cfg["eula_accepted"] = True
        self.cfg["eula_accepted_date"] = time.strftime("%Y-%m-%d")
        save_cfg(self.cfg)
        self._eula_frame.destroy()
        self._start_splash()

    # ── Splash Screen ────────────────────────────────────────────
    def _start_splash(self):
        trailer = _find_trailer()
        show_intro = self.cfg.get("show_intro", True)
        if not show_intro or not trailer:
            self._build_ui()
            return
        try:
            import cv2
        except ImportError:
            self._build_ui()
            return
        self.withdraw()
        self._splash = ctk.CTkToplevel()
        self._splash.overrideredirect(True)
        sw = self._splash.winfo_screenwidth()
        sh = self._splash.winfo_screenheight()
        self._splash.geometry(f"{sw}x{sh}+0+0")
        self._splash.configure(fg_color="#000000")
        self._splash.attributes("-topmost", True)
        self._splash.lift()
        self._splash_canvas = tk.Canvas(self._splash, bg="#000000", highlightthickness=0,
                                         width=sw, height=sh)
        self._splash_canvas.pack(fill="both", expand=True)
        self._splash_skip = False
        self._splash.bind("<Escape>", lambda e: setattr(self, '_splash_skip', True))
        self._splash.bind("<Button-1>", lambda e: setattr(self, '_splash_skip', True))
        self._splash_cap = cv2.VideoCapture(str(trailer))
        if not self._splash_cap.isOpened():
            self._splash.destroy()
            self.deiconify()
            self._build_ui()
            return
        self._splash_fps = self._splash_cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._splash_delay = max(10, int(1000 / self._splash_fps))
        self._splash_frame_count = 0
        self._splash_max_frames = int(self._splash_fps * 8)
        self._splash_sw = sw
        self._splash_sh = sh
        self._splash_photo = None
        self._play_splash_frame()

    def _play_splash_frame(self):
        if self._splash_skip or self._splash_frame_count >= self._splash_max_frames:
            self._end_splash_video()
            return
        try:
            import cv2
            ret, frame = self._splash_cap.read()
            if not ret:
                self._end_splash_video()
                return
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            img_w, img_h = pil_img.size
            scale = max(self._splash_sw / img_w, self._splash_sh / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.BILINEAR)
            left = (new_w - self._splash_sw) // 2
            top = (new_h - self._splash_sh) // 2
            pil_img = pil_img.crop((left, top, left + self._splash_sw, top + self._splash_sh))
            self._splash_photo = ImageTk.PhotoImage(pil_img)
            self._splash_canvas.delete("all")
            self._splash_canvas.create_image(self._splash_sw // 2, self._splash_sh // 2,
                                              image=self._splash_photo)
            self._splash_frame_count += 1
            self._splash.after(self._splash_delay, self._play_splash_frame)
        except Exception:
            self._end_splash_video()

    def _end_splash_video(self):
        try:
            self._splash_cap.release()
        except Exception:
            pass
        self._finish_splash()

    def _show_logo_sequence(self):
        if not self._logo_path:
            self._finish_splash()
            return
        try:
            logo = Image.open(self._logo_path).convert("RGBA")
            logo.thumbnail((200, 200), Image.LANCZOS)
        except Exception:
            self._finish_splash()
            return
        self._splash_logo = logo
        self._splash_canvas.delete("all")
        self._logo_alpha = 0
        self._logo_phase = "in"
        self._logo_hold_count = 0
        self._animate_logo()

    def _animate_logo(self):
        if self._splash_skip:
            self._finish_splash()
            return
        logo = self._splash_logo
        if self._logo_phase == "in":
            self._logo_alpha = min(255, self._logo_alpha + 15)
            if self._logo_alpha >= 255:
                self._logo_phase = "hold"
        elif self._logo_phase == "hold":
            self._logo_hold_count += 1
            if self._logo_hold_count > 40:
                self._logo_phase = "out"
        elif self._logo_phase == "out":
            self._logo_alpha = max(0, self._logo_alpha - 15)
            if self._logo_alpha <= 0:
                self._finish_splash()
                return
        faded = logo.copy()
        alpha_ch = faded.split()[3]
        alpha_ch = alpha_ch.point(lambda p: int(p * self._logo_alpha / 255))
        faded.putalpha(alpha_ch)
        bg = Image.new("RGBA", (self._splash_sw, self._splash_sh), (0, 0, 0, 255))
        ox = (self._splash_sw - faded.size[0]) // 2
        oy = (self._splash_sh - faded.size[1]) // 2
        bg.paste(faded, (ox, oy), faded)
        if self._logo_alpha > 100:
            draw = ImageDraw.Draw(bg)
            tagline = t("about_tagline")
            try:
                from PIL import ImageFont
                font = ImageFont.truetype("segoeui.ttf", 18)
            except Exception:
                font = ImageDraw.Draw(bg).getfont()
            bbox = draw.textbbox((0, 0), tagline, font=font)
            tw = bbox[2] - bbox[0]
            tx = (self._splash_sw - tw) // 2
            ty = oy + faded.size[1] + 24
            draw.text((tx, ty), tagline, fill=(245, 168, 0, int(self._logo_alpha * 0.8)), font=font)
        self._splash_photo = ImageTk.PhotoImage(bg.convert("RGB"))
        self._splash_canvas.delete("all")
        self._splash_canvas.create_image(self._splash_sw // 2, self._splash_sh // 2,
                                          image=self._splash_photo)
        self._splash.after(33, self._animate_logo)

    def _finish_splash(self):
        try:
            self._splash.destroy()
        except Exception:
            pass
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self._build_ui()
