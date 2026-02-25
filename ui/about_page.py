"""
HoneyClean – About page mixin
"""

import customtkinter as ctk
from PIL import Image

from ui.theme import C, FONT
from core.i18n import t
from core.config import VERSION


class AboutPageMixin:

    def _build_about_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self._pages["about"] = page
        ctr = ctk.CTkFrame(page, fg_color="transparent")
        ctr.pack(expand=True)
        self._about_logo_img = None
        if self._logo_path:
            try:
                al = Image.open(self._logo_path).convert("RGBA")
                al.thumbnail((96, 96), Image.LANCZOS)
                self._about_logo_img = ctk.CTkImage(light_image=al, dark_image=al, size=(96, 96))
                ctk.CTkLabel(ctr, image=self._about_logo_img, text="").pack(pady=(0, 8))
            except Exception:
                ctk.CTkLabel(ctr, text="\U0001f36f", font=(FONT, 64)).pack(pady=(0, 8))
        else:
            ctk.CTkLabel(ctr, text="\U0001f36f", font=(FONT, 64)).pack(pady=(0, 8))
        ctk.CTkLabel(ctr, text="HoneyClean", font=(FONT, 28, "bold"), text_color=C["accent"]).pack()
        ctk.CTkLabel(ctr, text=t("about_tagline"), font=(FONT, 12), text_color=C["text_muted"]).pack(pady=(4, 4))
        vb = ctk.CTkFrame(ctr, fg_color=C["accent_dim"], corner_radius=12, height=28)
        vb.pack(pady=(4, 16))
        ctk.CTkLabel(vb, text=f"  v{VERSION}  ", font=(FONT, 11, "bold"), text_color=C["accent"]).pack(padx=8, pady=2)
        ic = ctk.CTkFrame(ctr, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
        ic.pack(padx=40, pady=8)
        for lbl, val in [(t("about_version"), VERSION), (t("about_author"), "Zayn1312"),
                          (t("about_license"), "MIT"), (t("about_github"), "github.com/Zayn1312/HoneyClean")]:
            row = ctk.CTkFrame(ic, fg_color="transparent"); row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row, text=lbl, font=(FONT, 11), text_color=C["text_muted"], width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=(FONT, 11), text_color=C["text"]).pack(side="left", padx=8)
        ctk.CTkButton(ctr, text="\u2b50  Star on GitHub", width=160, height=36, fg_color=C["accent"],
                      hover_color=C["accent_hover"], corner_radius=8, cursor="hand2",
                      command=lambda: self._open_url("https://github.com/Zayn1312/HoneyClean")).pack(pady=16)
