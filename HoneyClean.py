import multiprocessing
multiprocessing.freeze_support()

"""
HoneyClean v5.0 - AI Background Remover
Complete Overhaul by Zayn1312
"""

import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

import tkinter as tk
import os, sys, time, queue
from pathlib import Path
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor

os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

from core.config import VERSION, load_cfg, save_cfg
from core.i18n import t, set_language
from core.utils import check_dependencies, _find_logo
from ui.theme import C, FONT

from core.processing import ProcessingMixin
from ui.sidebar import SidebarMixin
from ui.queue_page import QueuePageMixin
from ui.editor_page import EditorPageMixin
from ui.settings_page import SettingsPageMixin
from ui.about_page import AboutPageMixin
from ui.widgets import WidgetsMixin
from ui.splash import SplashMixin


class HoneyClean(ProcessingMixin, SidebarMixin, QueuePageMixin, EditorPageMixin,
                 SettingsPageMixin, AboutPageMixin, WidgetsMixin, SplashMixin, ctk.CTk):

    def __init__(self):
        super().__init__()
        self.cfg = load_cfg()
        set_language(self.cfg.get("language", "en"))

        self.title(f"HoneyClean v{VERSION} \u2014 AI Background Removal")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])

        self._logo_path = _find_logo()
        if self._logo_path:
            try:
                ico = Image.open(self._logo_path)
                ico.thumbnail((64, 64), Image.LANCZOS)
                self._ico_photo = ImageTk.PhotoImage(ico)
                self.iconphoto(False, self._ico_photo)
            except Exception:
                pass

        # State
        self.session = None
        self.session_model = None
        self.queue_items = []
        self.processing = False
        self.paused = False
        self.stop_flag = False
        self._results = []
        self._current_page = "queue"
        self._history = []
        self._redo_stack = []
        self._processed_today = 0
        self._process_start_time = 0
        self.result_queue = queue.Queue()
        self._thumb_images = []
        self._thumb_cards = []
        self._editor_before_img = None
        self._editor_after_img = None
        self._editor_tk_img = None
        self._divider_pos = 0.5
        self._dragging_divider = False
        self._bg_color = (255, 255, 255)
        self._selected_cards = set()
        self._all_selected = False
        self._failed_items = []
        self._per_image_times = {}
        self._thumb_executor = ThreadPoolExecutor(max_workers=4)
        self._undo_queue_stack = []
        self._skip_processed = self.cfg.get("skip_processed", False)
        self._batch_fail_count = 0
        self._fx_particles = []
        self._fx_processing_indices = set()
        self._fx_tick = 0
        self._glow_phase = 0
        self._video_processor = None
        self._log_lines = []

        try:
            from crash_reporter import install_hooks
            install_hooks(self)
        except Exception:
            pass

        if not self.cfg.get("eula_accepted"):
            self._show_eula()
        else:
            self._start_splash()

    def _build_ui(self):
        missing = check_dependencies()
        if any(info["critical"] for _, info in missing):
            self._show_dep_dialog(missing)
            return

        self._sidebar = ctk.CTkFrame(self, width=180, fg_color=C["sidebar"], corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        self._content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._pages = {}
        self._build_queue_page()
        self._build_editor_page()
        self._build_settings_page()
        self._build_about_page()
        self._build_status_bar()
        self._show_page("queue")
        self._poll_results()
        self._update_gpu_info()

        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.bind("<Control-z>", lambda e: self._undo_queue_add() if self._current_page == "queue" else self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
        self.bind("<Control-a>", lambda e: (self._toggle_select_all(), "break")[-1] if self._current_page == "queue" else None)
        self.bind("<Delete>", lambda e: self._remove_selected() if self._current_page == "queue" else None)
        self.bind("<Escape>", lambda e: self._stop_processing() if self.processing else None)
        self.bind("<space>", lambda e: self._space_toggle(e))
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.dnd_bind('<<DragLeave>>', self._on_drag_leave)
            self.dnd_bind('<<Drop>>', self._on_drop)
        except Exception:
            pass
        self.after(1500, self._auto_detect_vram)
        self.after(1800, self._fx_start)


if __name__ == "__main__":
    app = HoneyClean()
    app.mainloop()
