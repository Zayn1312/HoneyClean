import multiprocessing
multiprocessing.freeze_support()

"""
HoneyClean v3.0 - AI Background Remover
Enterprise Release by Zayn1312
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, os, io, time, sys, json, subprocess, traceback, queue, math, re
import zipfile, tempfile
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFilter

os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except: pass

import io as _io
sys.stderr = _io.StringIO()

VERSION = "3.0"

# ── i18n System ──────────────────────────────────────────────────
STRINGS = {"en": {}, "de": {}, "fr": {}, "es": {}, "zh": {}}

def _tr(key, en, de, fr, es, zh):
    for lang, val in [("en",en),("de",de),("fr",fr),("es",es),("zh",zh)]:
        STRINGS[lang][key] = val

_current_lang = "en"

def t(key, **kwargs):
    s = STRINGS.get(_current_lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
    if kwargs:
        try: s = s.format(**kwargs)
        except: pass
    return s

def set_language(lang):
    global _current_lang
    if lang in STRINGS:
        _current_lang = lang

# App
_tr("app_title", "HoneyClean", "HoneyClean", "HoneyClean", "HoneyClean", "HoneyClean")
_tr("footer", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312")

# Navigation
_tr("nav_queue", "Queue", "Warteschlange", "File d'attente", "Cola", "\u961f\u5217")
_tr("nav_editor", "Editor", "Editor", "\u00c9diteur", "Editor", "\u7f16\u8f91\u5668")
_tr("nav_settings", "Settings", "Einstellungen", "Param\u00e8tres", "Ajustes", "\u8bbe\u7f6e")
_tr("nav_about", "About", "\u00dcber", "\u00c0 propos", "Acerca de", "\u5173\u4e8e")

# EULA
_tr("eula_title", "Terms of Use", "Nutzungsbedingungen", "Conditions d'utilisation", "T\u00e9rminos de uso", "\u4f7f\u7528\u6761\u6b3e")
_tr("eula_language", "Language", "Sprache", "Langue", "Idioma", "\u8bed\u8a00")
_tr("eula_checkbox", "I have read and agree to the terms of use", "Ich habe die Nutzungsbedingungen gelesen und stimme zu", "J'ai lu et j'accepte les conditions d'utilisation", "He le\u00eddo y acepto los t\u00e9rminos de uso", "\u6211\u5df2\u9605\u8bfb\u5e76\u540c\u610f\u4f7f\u7528\u6761\u6b3e")
_tr("eula_continue", "Continue", "Weiter", "Continuer", "Continuar", "\u7ee7\u7eed")
_tr("eula_decline", "Decline", "Ablehnen", "Refuser", "Rechazar", "\u62d2\u7edd")

# Queue
_tr("drop_zone", "Drop files here or click to browse", "Dateien hier ablegen oder klicken", "D\u00e9posez les fichiers ici ou cliquez", "Suelte archivos aqu\u00ed o haga clic", "\u5c06\u6587\u4ef6\u62d6\u653e\u5230\u6b64\u5904\u6216\u70b9\u51fb\u6d4f\u89c8")
_tr("add_folder", "Add Folder", "Ordner hinzuf\u00fcgen", "Ajouter un dossier", "Agregar carpeta", "\u6dfb\u52a0\u6587\u4ef6\u5939")
_tr("queue_label", "Queue", "Warteschlange", "File d'attente", "Cola", "\u961f\u5217")
_tr("clear_queue", "Clear", "Leeren", "Vider", "Limpiar", "\u6e05\u7a7a")
_tr("btn_start", "START", "START", "D\u00c9MARRER", "INICIAR", "\u5f00\u59cb")
_tr("btn_pause", "PAUSE", "PAUSE", "PAUSE", "PAUSA", "\u6682\u505c")
_tr("btn_resume", "RESUME", "WEITER", "REPRENDRE", "REANUDAR", "\u7ee7\u7eed")
_tr("btn_stop", "STOP", "STOPP", "ARR\u00caTER", "DETENER", "\u505c\u6b62")
_tr("open_output", "Open Output", "Ausgabe \u00f6ffnen", "Ouvrir la sortie", "Abrir salida", "\u6253\u5f00\u8f93\u51fa")

# Editor
_tr("retouch", "Retouch", "Retusche", "Retouche", "Retocar", "\u4fee\u56fe")
_tr("erase", "Erase", "Radieren", "Effacer", "Borrar", "\u64e6\u9664")
_tr("restore", "Restore", "Wiederherstellen", "Restaurer", "Restaurar", "\u6062\u590d")
_tr("brush_size", "Size", "Gr\u00f6\u00dfe", "Taille", "Tama\u00f1o", "\u5927\u5c0f")
_tr("tolerance", "Tolerance", "Toleranz", "Tol\u00e9rance", "Tolerancia", "\u5bb9\u5dee")
_tr("save", "Save", "Speichern", "Enregistrer", "Guardar", "\u4fdd\u5b58")
_tr("reset", "Reset", "Zur\u00fccksetzen", "R\u00e9initialiser", "Restablecer", "\u91cd\u7f6e")
_tr("before_label", "BEFORE", "VORHER", "AVANT", "ANTES", "\u4e4b\u524d")
_tr("after_label", "AFTER", "NACHHER", "APR\u00c8S", "DESPU\u00c9S", "\u4e4b\u540e")
_tr("checkerboard", "Checkerboard", "Schachbrett", "\u00c9chiquier", "Tablero", "\u68cb\u76d8")

# Settings
_tr("settings_title", "Settings", "Einstellungen", "Param\u00e8tres", "Ajustes", "\u8bbe\u7f6e")
_tr("output_dir", "Output Folder", "Ausgabeordner", "Dossier de sortie", "Carpeta de salida", "\u8f93\u51fa\u6587\u4ef6\u5939")
_tr("language", "Language", "Sprache", "Langue", "Idioma", "\u8bed\u8a00")
_tr("theme", "Theme", "Design", "Th\u00e8me", "Tema", "\u4e3b\u9898")
_tr("ai_model", "AI Model", "KI-Modell", "Mod\u00e8le IA", "Modelo IA", "AI\u6a21\u578b")
_tr("auto_model", "Auto (recommended)", "Auto (empfohlen)", "Auto (recommand\u00e9)", "Auto (recomendado)", "\u81ea\u52a8\uff08\u63a8\u8350\uff09")
_tr("alpha_fg_label", "Alpha FG", "Alpha VG", "Alpha PP", "Alpha PP", "\u524d\u666fAlpha")
_tr("alpha_bg_label", "Alpha BG", "Alpha HG", "Alpha AP", "Alpha FD", "\u80cc\u666fAlpha")
_tr("alpha_erode_label", "Alpha Erode", "Alpha Erosion", "Alpha \u00c9rosion", "Alpha Erosi\u00f3n", "Alpha\u4fb5\u8680")
_tr("use_gpu_label", "Use GPU", "GPU verwenden", "Utiliser GPU", "Usar GPU", "\u4f7f\u7528GPU")
_tr("gpu_limit_label", "GPU Limit %", "GPU Limit %", "Limite GPU %", "L\u00edmite GPU %", "GPU\u9650\u5236%")
_tr("save_settings", "Save Settings", "Einstellungen speichern", "Enregistrer les param\u00e8tres", "Guardar ajustes", "\u4fdd\u5b58\u8bbe\u7f6e")
_tr("section_general", "General", "Allgemein", "G\u00e9n\u00e9ral", "General", "\u5e38\u89c4")
_tr("section_ai", "AI Model", "KI-Modell", "Mod\u00e8le IA", "Modelo IA", "AI\u6a21\u578b")
_tr("section_gpu", "GPU", "GPU", "GPU", "GPU", "GPU")

# About
_tr("about_title", "About", "\u00dcber", "\u00c0 propos", "Acerca de", "\u5173\u4e8e")
_tr("about_desc", "AI-powered background remover", "KI-gest\u00fctzte Hintergrundentfernung", "Suppression d'arri\u00e8re-plan par IA", "Eliminador de fondo con IA", "AI\u9a71\u52a8\u7684\u80cc\u666f\u79fb\u9664\u5de5\u5177")
_tr("about_version", "Version", "Version", "Version", "Versi\u00f3n", "\u7248\u672c")
_tr("about_author", "Author", "Autor", "Auteur", "Autor", "\u4f5c\u8005")
_tr("about_license", "License", "Lizenz", "Licence", "Licencia", "\u8bb8\u53ef\u8bc1")
_tr("about_github", "GitHub", "GitHub", "GitHub", "GitHub", "GitHub")

# Status
_tr("status_loading", "Loading AI model...", "Lade KI-Modell...", "Chargement du mod\u00e8le IA...", "Cargando modelo IA...", "\u6b63\u5728\u52a0\u8f7dAI\u6a21\u578b...")
_tr("status_processing", "Processing...", "Verarbeite...", "Traitement en cours...", "Procesando...", "\u5904\u7406\u4e2d...")
_tr("status_done", "Done! {count} images processed", "Fertig! {count} Bilder verarbeitet", "Termin\u00e9 ! {count} images trait\u00e9es", "\u00a1Listo! {count} im\u00e1genes procesadas", "\u5b8c\u6210\uff01\u5df2\u5904\u7406{count}\u5f20\u56fe\u7247")
_tr("status_error", "Error: {error}", "Fehler: {error}", "Erreur : {error}", "Error: {error}", "\u9519\u8bef\uff1a{error}")
_tr("status_paused", "Paused", "Pausiert", "En pause", "En pausa", "\u5df2\u6682\u505c")
_tr("status_empty", "Queue is empty!", "Warteschlange ist leer!", "La file d'attente est vide !", "\u00a1La cola est\u00e1 vac\u00eda!", "\u961f\u5217\u4e3a\u7a7a\uff01")
_tr("status_no_image", "No image to save", "Kein Bild zum Speichern", "Aucune image \u00e0 enregistrer", "No hay imagen para guardar", "\u6ca1\u6709\u53ef\u4fdd\u5b58\u7684\u56fe\u7247")
_tr("status_saved", "Saved: {name}", "Gespeichert: {name}", "Enregistr\u00e9 : {name}", "Guardado: {name}", "\u5df2\u4fdd\u5b58\uff1a{name}")
_tr("status_reset_done", "Reset done", "Zur\u00fcckgesetzt", "R\u00e9initialisation effectu\u00e9e", "Restablecido", "\u5df2\u91cd\u7f6e")
_tr("status_ready", "Ready - starting processing", "Bereit - starte Verarbeitung", "Pr\u00eat - d\u00e9marrage du traitement", "Listo - iniciando procesamiento", "\u5c31\u7eea - \u5f00\u59cb\u5904\u7406")
_tr("status_model_loaded", "Model loaded", "Modell geladen", "Mod\u00e8le charg\u00e9", "Modelo cargado", "\u6a21\u578b\u5df2\u52a0\u8f7d")
_tr("status_output_missing", "Output folder does not exist yet", "Ausgabeordner existiert noch nicht", "Le dossier de sortie n'existe pas encore", "La carpeta de salida a\u00fan no existe", "\u8f93\u51fa\u6587\u4ef6\u5939\u5c1a\u4e0d\u5b58\u5728")

# Progress
_tr("progress_eta", "ETA {m}m {s:02d}s", "ETA {m}m {s:02d}s", "ETA {m}m {s:02d}s", "ETA {m}m {s:02d}s", "\u9884\u8ba1{m}\u5206{s:02d}\u79d2")
_tr("progress_elapsed", "Elapsed", "Vergangen", "\u00c9coul\u00e9", "Transcurrido", "\u5df2\u7528\u65f6")
_tr("progress_speed", "{speed} img/min", "{speed} Bild/min", "{speed} img/min", "{speed} img/min", "{speed}\u5f20/\u5206")
_tr("progress_of", "{current} / {total}", "{current} / {total}", "{current} / {total}", "{current} / {total}", "{current} / {total}")

# GPU
_tr("gpu_label", "GPU", "GPU", "GPU", "GPU", "GPU")
_tr("vram_label", "VRAM", "VRAM", "VRAM", "VRAM", "\u663e\u5b58")
_tr("cpu_mode", "CPU Mode", "CPU Modus", "Mode CPU", "Modo CPU", "CPU\u6a21\u5f0f")
_tr("gpu_not_found", "nvidia-smi not found (CPU Mode)", "nvidia-smi nicht gefunden (CPU Modus)", "nvidia-smi introuvable (Mode CPU)", "nvidia-smi no encontrado (Modo CPU)", "\u672a\u627e\u5230nvidia-smi (CPU\u6a21\u5f0f)")

# Dependencies
_tr("dep_title", "Missing Dependencies", "Fehlende Abh\u00e4ngigkeiten", "D\u00e9pendances manquantes", "Dependencias faltantes", "\u7f3a\u5c11\u4f9d\u8d56")
_tr("dep_missing", "The following packages are missing:", "Die folgenden Pakete fehlen:", "Les paquets suivants sont manquants :", "Faltan los siguientes paquetes:", "\u7f3a\u5c11\u4ee5\u4e0b\u8f6f\u4ef6\u5305\uff1a")
_tr("dep_install", "Install", "Installieren", "Installer", "Instalar", "\u5b89\u88c5")
_tr("dep_critical", "Critical dependency missing - cannot continue", "Kritische Abh\u00e4ngigkeit fehlt - kann nicht fortfahren", "D\u00e9pendance critique manquante - impossible de continuer", "Dependencia cr\u00edtica faltante - no se puede continuar", "\u7f3a\u5c11\u5173\u952e\u4f9d\u8d56 - \u65e0\u6cd5\u7ee7\u7eed")

# Errors
_tr("error_title", "Error", "Fehler", "Erreur", "Error", "\u9519\u8bef")
_tr("error_visit_wiki", "Visit Wiki", "Wiki besuchen", "Visiter le Wiki", "Visitar Wiki", "\u8bbf\u95eeWiki")
_tr("error_close", "Close", "Schlie\u00dfen", "Fermer", "Cerrar", "\u5173\u95ed")

# Files
_tr("file_added", "Added: {name}", "Hinzugef\u00fcgt: {name}", "Ajout\u00e9 : {name}", "Agregado: {name}", "\u5df2\u6dfb\u52a0\uff1a{name}")
_tr("file_processing", "Processing {name} ({current} of {total})", "Verarbeite {name} ({current} von {total})", "Traitement de {name} ({current} sur {total})", "Procesando {name} ({current} de {total})", "\u6b63\u5728\u5904\u7406{name}({current}/{total})")
_tr("file_add_images", "Add images to start", "Bilder hinzuf\u00fcgen zum Starten", "Ajoutez des images pour commencer", "Agregue im\u00e1genes para comenzar", "\u6dfb\u52a0\u56fe\u7247\u4ee5\u5f00\u59cb")
_tr("file_select", "Select Images", "Bilder ausw\u00e4hlen", "S\u00e9lectionner des images", "Seleccionar im\u00e1genes", "\u9009\u62e9\u56fe\u7247")
_tr("file_select_folder", "Select Folder", "Ordner ausw\u00e4hlen", "S\u00e9lectionner un dossier", "Seleccionar carpeta", "\u9009\u62e9\u6587\u4ef6\u5939")
_tr("file_images_filter", "Images", "Bilder", "Images", "Im\u00e1genes", "\u56fe\u7247")

# Misc
_tr("dark", "Dark", "Dunkel", "Sombre", "Oscuro", "\u6df1\u8272")
_tr("browse", "Browse", "Durchsuchen", "Parcourir", "Explorar", "\u6d4f\u89c8")
_tr("settings_saved", "Settings saved", "Einstellungen gespeichert", "Param\u00e8tres enregistr\u00e9s", "Ajustes guardados", "\u8bbe\u7f6e\u5df2\u4fdd\u5b58")
_tr("images_processed", "images processed", "Bilder verarbeitet", "images trait\u00e9es", "im\u00e1genes procesadas", "\u5f20\u56fe\u7247\u5df2\u5904\u7406")

# ── Color Palette - Apple Dark Mode ──────────────────────────────
BG = "#1c1c1e"
SURFACE = "#2c2c2e"
SURFACE_VAR = "#3a3a3c"
SIDEBAR_BG = "#252528"
ACCENT = "#007AFF"
SUCCESS = "#30D158"
WARNING = "#FFD60A"
ERROR_CLR = "#FF453A"
TEXT = "#FFFFFF"
TEXT_SEC = "#98989D"
TEXT_TER = "#636366"
BORDER = "#3d3d40"
FONT = "Segoe UI"

# ── Error Code Registry ─────────────────────────────────────────
ERROR_REGISTRY = {
    "HC-001": "rembg not installed", "HC-002": "Pillow not installed",
    "HC-003": "pymatting not installed", "HC-004": "onnxruntime not installed",
    "HC-005": "numpy not installed",
    "HC-010": "File not found: {path}", "HC-011": "Invalid file type: {path}",
    "HC-012": "Path traversal detected: {path}",
    "HC-013": "ZIP exceeds 500MB uncompressed", "HC-014": "ZIP bomb detected",
    "HC-015": "ZIP path traversal", "HC-016": "ZIP extraction failed: {error}",
    "HC-017": "Invalid image data: {path}",
    "HC-020": "Model load failed: {error}", "HC-021": "Processing failed: {name}: {error}",
    "HC-022": "GPU unavailable, using CPU", "HC-023": "Model not found: {model}",
    "HC-024": "Cannot create output dir: {path}",
    "HC-030": "Config corrupted", "HC-031": "Config save failed: {error}",
    "HC-032": "Invalid config: {key}={value}",
    "HC-040": "UI init failed: {error}", "HC-041": "DnD unavailable: {error}",
}
WIKI_BASE = "https://github.com/Zayn1312/HoneyClean/wiki/Error-Codes"

# ── Config ───────────────────────────────────────────────────────
CFG_PATH = Path(os.environ.get("APPDATA", ".")) / "HoneyClean" / "config.json"
DEFAULT_CFG = {
    "output_dir": str(Path.home() / "Downloads" / "HoneyClean_Output"),
    "gpu_limit": 100, "model": "auto", "alpha_fg": 240, "alpha_bg": 10,
    "alpha_erode": 10, "use_gpu": True, "debug": False,
    "language": "en", "theme": "dark",
    "eula_accepted": False, "eula_accepted_date": "",
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

# ── Honey logo (drawn with PIL) ─────────────────────────────────
def make_logo(size=40):
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    d = ImageDraw.Draw(img)
    cx, cy, r = size//2, size//2, size//2-2
    pts = [(cx + r*math.cos(math.radians(a-90)),
            cy + r*math.sin(math.radians(a-90))) for a in range(0,360,60)]
    d.polygon(pts, fill=ACCENT, outline="#005ec4")
    drop = [(cx, cy-r//2+4), (cx-5, cy+2), (cx, cy+r//3), (cx+5, cy+2)]
    d.polygon(drop, fill="#1c1c1e")
    return img

# ── Security Functions ───────────────────────────────────────────
def _validate_path(path):
    """Reject path traversal, non-existent, non-file. Returns (bool, error_code_or_None)."""
    p = str(path)
    if ".." in p:
        return False, "HC-012"
    path = Path(path)
    if not path.exists():
        return False, "HC-010"
    if not path.is_file():
        return False, "HC-010"
    return True, None

def _validate_image(path):
    """Check magic bytes for image formats. Returns (bool, format_or_None)."""
    try:
        with open(path, "rb") as f:
            header = f.read(12)
        if header[:4] == b'\x89PNG':
            return True, "PNG"
        if header[:3] == b'\xff\xd8\xff':
            return True, "JPEG"
        if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
            return True, "WEBP"
        if header[:2] == b'BM':
            return True, "BMP"
        return False, None
    except:
        return False, None

def _sanitize_filename(name, max_len=200):
    """Strip dangerous chars, limit length, prevent hidden files."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = name.lstrip('.')
    if not name:
        name = "unnamed"
    if len(name) > max_len:
        stem, ext = os.path.splitext(name)
        name = stem[:max_len - len(ext)] + ext
    return name

# ── ZIP Handling ─────────────────────────────────────────────────
def _extract_zip(zip_path, output_dir):
    """Extract images from ZIP to temp dir with security checks.
    Returns (list_of_paths, error_code_or_None)."""
    zip_path = Path(zip_path)
    tmp_dir = Path(output_dir) / ".honeyclean_tmp" / zip_path.stem
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check total uncompressed size
            total_size = sum(info.file_size for info in zf.infolist())
            if total_size > 500 * 1024 * 1024:
                return [], "HC-013"

            # Check compression ratio
            compressed_size = sum(info.compress_size for info in zf.infolist() if info.compress_size > 0)
            if compressed_size > 0 and total_size / compressed_size > 100:
                return [], "HC-014"

            extracted = []
            for info in zf.infolist():
                if info.is_dir():
                    continue
                # Reject path traversal
                if ".." in info.filename or info.filename.startswith("/"):
                    return [], "HC-015"

                fname = _sanitize_filename(Path(info.filename).name)
                ext = Path(fname).suffix.lower()
                if ext not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
                    continue

                target = tmp_dir / fname
                with zf.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())

                # Validate magic bytes
                valid, _ = _validate_image(target)
                if valid:
                    extracted.append(target)
                else:
                    target.unlink(missing_ok=True)

            return extracted, None
    except zipfile.BadZipFile as e:
        return [], "HC-016"
    except Exception as e:
        return [], "HC-016"

# ── Dependency Checker ───────────────────────────────────────────
def check_dependencies():
    """Try importing required packages. Returns list of (name, info) for missing deps."""
    deps = [
        ("rembg", {"critical": True, "pip": "rembg"}),
        ("PIL", {"critical": True, "pip": "Pillow"}),
        ("onnxruntime", {"critical": True, "pip": "onnxruntime"}),
        ("numpy", {"critical": True, "pip": "numpy"}),
        ("pymatting", {"critical": False, "pip": "pymatting"}),
        ("tkinterdnd2", {"critical": False, "pip": "tkinterdnd2"}),
    ]
    missing = []
    for name, info in deps:
        try:
            __import__(name)
        except ImportError:
            missing.append((name, info))
    return missing

def _auto_install(package):
    """Attempt pip install. Returns bool."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

# ── Auto Model Selection ────────────────────────────────────────
MODEL_PRIORITY = ["isnet-general-use", "u2net", "isnet-anime", "u2net_human_seg", "silueta"]

def _auto_select_model():
    """Try models in priority order. Returns (model_name, session) or (None, None)."""
    from rembg import new_session
    for model in MODEL_PRIORITY:
        try:
            session = new_session(model)
            return model, session
        except:
            continue
    return None, None


# ======================================================================
# SECTION 2: Widget Classes
# ======================================================================

class AppleButton(tk.Canvas):
    """Clean rounded rectangle button with Apple design style."""

    def __init__(self, parent, text="", command=None, style="primary",
                 width=150, height=40, font_size=11, bold=True, **kw):
        try:
            bg = parent.cget("bg")
        except:
            bg = BG
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0, bd=0)
        self._text = text
        self._command = command
        self._style = style
        self._bg = bg
        self._cw = width
        self._ch = height
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
        w, h = self._cw, self._ch
        r = 8

        if not self._enabled:
            fill = SURFACE_VAR
            fg = TEXT_TER
            outline = ""
        elif self._style == "primary":
            fill = "#005ec4" if self._hover else ACCENT
            fg = "#FFFFFF"
            outline = ""
        elif self._style == "secondary":
            fill = SURFACE_VAR if self._hover else ""
            fg = TEXT_SEC
            outline = BORDER
        elif self._style == "destructive":
            fill = "#cc362e" if self._hover else ERROR_CLR
            fg = "#FFFFFF"
            outline = ""
        elif self._style == "plain":
            fill = SURFACE_VAR if self._hover else ""
            fg = ACCENT
            outline = ""
        else:
            fill = ACCENT
            fg = "#FFFFFF"
            outline = ""

        if fill:
            self.create_rectangle(r, 0, w-r, h, fill=fill, outline="")
            self.create_rectangle(0, r, w, h-r, fill=fill, outline="")
            self.create_oval(0, 0, r*2, r*2, fill=fill, outline="")
            self.create_oval(w-r*2, 0, w, r*2, fill=fill, outline="")
            self.create_oval(0, h-r*2, r*2, h, fill=fill, outline="")
            self.create_oval(w-r*2, h-r*2, w, h, fill=fill, outline="")
        if outline:
            self.create_rectangle(1, 1, w-1, h-1, outline=outline, width=1)

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

    def set_state(self, enabled, text=None, style=None):
        self._enabled = enabled
        if text is not None:
            self._text = text
        if style is not None:
            self._style = style
        self.configure(cursor="hand2" if enabled else "")
        self._draw()


class AppleProgress(tk.Canvas):
    """Thin 4px progress bar with Apple styling."""

    def __init__(self, parent, height=4):
        try:
            bg = parent.cget("bg")
        except:
            bg = BG
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self._ch = height
        self._value = 0
        self._max = 100
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, value, maximum=None):
        self._value = value
        if maximum is not None:
            self._max = max(1, maximum)
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self._ch
        if w < 4:
            return
        self.create_rectangle(0, 0, w, h, fill=SURFACE_VAR, outline="")
        pct = self._value / self._max if self._max > 0 else 0
        fw = max(0, int(w * pct))
        if fw > 0:
            self.create_rectangle(0, 0, fw, h, fill=ACCENT, outline="")


class SidebarItem(tk.Frame):
    """Sidebar navigation item with icon and text."""

    def __init__(self, parent, icon="", text="", command=None):
        super().__init__(parent, bg=SIDEBAR_BG, cursor="hand2")
        self._command = command
        self._selected = False
        self._icon = icon
        self._text_str = text

        self._icon_lbl = tk.Label(self, text=icon, font=(FONT, 13),
                                   fg=TEXT_SEC, bg=SIDEBAR_BG, width=2)
        self._icon_lbl.pack(side="left", padx=(12, 4), pady=8)

        self._text_lbl = tk.Label(self, text=text, font=(FONT, 10),
                                   fg=TEXT_SEC, bg=SIDEBAR_BG, anchor="w")
        self._text_lbl.pack(side="left", fill="x", expand=True, padx=(0, 12))

        for w in [self, self._icon_lbl, self._text_lbl]:
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_click(self, e):
        if self._command:
            self._command()

    def _on_enter(self, e):
        if not self._selected:
            for w in [self, self._icon_lbl, self._text_lbl]:
                w.config(bg=SURFACE)

    def _on_leave(self, e):
        if not self._selected:
            for w in [self, self._icon_lbl, self._text_lbl]:
                w.config(bg=SIDEBAR_BG)

    def set_selected(self, selected):
        self._selected = selected
        if selected:
            bg = ACCENT
            fg = "#FFFFFF"
        else:
            bg = SIDEBAR_BG
            fg = TEXT_SEC
        for w in [self, self._icon_lbl, self._text_lbl]:
            w.config(bg=bg)
        self._icon_lbl.config(fg=fg)
        self._text_lbl.config(fg=fg)

    def set_text(self, text):
        self._text_str = text
        self._text_lbl.config(text=text)


class ThumbnailGrid(tk.Frame):
    """Scrollable grid of image thumbnails with status dots."""

    THUMB_SIZE = 64
    STATUS_COLORS = {
        "pending": TEXT_TER,
        "processing": ACCENT,
        "done": SUCCESS,
        "error": ERROR_CLR,
    }

    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._canvas = tk.Canvas(self, bg=SURFACE, highlightthickness=0, bd=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical",
                                         command=self._canvas.yview,
                                         style="Dark.Vertical.TScrollbar")
        self._inner = tk.Frame(self._canvas, bg=SURFACE)
        self._inner.bind("<Configure>",
                         lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._items = []
        self._thumb_refs = []
        self._cols = 4
        self._canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, e):
        new_cols = max(1, e.width // (self.THUMB_SIZE + 8))
        if new_cols != self._cols:
            self._cols = new_cols
            self._relayout()

    def _relayout(self):
        for widget in self._inner.winfo_children():
            widget.grid_forget()
        for idx, item in enumerate(self._items):
            row = idx // self._cols
            col = idx % self._cols
            item["frame"].grid(row=row, column=col, padx=2, pady=2)

    def add_item(self, path, status="pending"):
        idx = len(self._items)
        frame = tk.Frame(self._inner, bg=SURFACE_VAR, width=self.THUMB_SIZE+4,
                         height=self.THUMB_SIZE+4)
        frame.grid_propagate(False)

        canvas = tk.Canvas(frame, width=self.THUMB_SIZE, height=self.THUMB_SIZE,
                           bg=SURFACE_VAR, highlightthickness=0, bd=0)
        canvas.pack(padx=2, pady=2)

        dot_color = self.STATUS_COLORS.get(status, TEXT_TER)
        dot = canvas.create_oval(self.THUMB_SIZE-10, 2, self.THUMB_SIZE-2, 10,
                                 fill=dot_color, outline="")

        item = {"frame": frame, "canvas": canvas, "dot": dot,
                "path": path, "status": status, "thumb_ref": None}
        self._items.append(item)

        row = idx // self._cols
        col = idx % self._cols
        frame.grid(row=row, column=col, padx=2, pady=2)

        threading.Thread(target=self._gen_thumb, args=(idx, path), daemon=True).start()

    def _gen_thumb(self, idx, path):
        try:
            img = Image.open(path)
            img.thumbnail((self.THUMB_SIZE, self.THUMB_SIZE), Image.LANCZOS)
            bg = Image.new("RGB", (self.THUMB_SIZE, self.THUMB_SIZE), (44, 44, 46))
            ox = (self.THUMB_SIZE - img.size[0]) // 2
            oy = (self.THUMB_SIZE - img.size[1]) // 2
            if img.mode == "RGBA":
                bg.paste(img, (ox, oy), mask=img.split()[3])
            else:
                bg.paste(img, (ox, oy))
            tk_img = ImageTk.PhotoImage(bg)
            self._items[idx]["thumb_ref"] = tk_img
            canvas = self._items[idx]["canvas"]
            canvas.after(0, lambda: canvas.create_image(
                self.THUMB_SIZE//2, self.THUMB_SIZE//2, anchor="center", image=tk_img))
            dot_color = self.STATUS_COLORS.get(self._items[idx]["status"], TEXT_TER)
            canvas.after(0, lambda: canvas.create_oval(
                self.THUMB_SIZE-10, 2, self.THUMB_SIZE-2, 10,
                fill=dot_color, outline=""))
        except:
            pass

    def update_status(self, idx, status):
        if 0 <= idx < len(self._items):
            self._items[idx]["status"] = status
            dot_color = self.STATUS_COLORS.get(status, TEXT_TER)
            canvas = self._items[idx]["canvas"]
            canvas.delete(self._items[idx]["dot"])
            self._items[idx]["dot"] = canvas.create_oval(
                self.THUMB_SIZE-10, 2, self.THUMB_SIZE-2, 10,
                fill=dot_color, outline="")

    def clear(self):
        for item in self._items:
            item["frame"].destroy()
        self._items.clear()
        self._thumb_refs.clear()


# ======================================================================
# SECTION 3: HoneyClean Class - Init, EULA, Build UI
# ======================================================================

class HoneyClean:
    def __init__(self, root):
        self.root = root
        self.cfg = load_cfg()

        # Set language from config
        lang = self.cfg.get("language", "en")
        set_language(lang)

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
        self._fullscreen = False
        self._restore_geo = ""
        self._pre_fs_geo = ""
        self._current_page = "queue"

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

        # 1px border around entire window
        self.root.configure(bg=BORDER)
        self._main_frame = tk.Frame(self.root, bg=BG)
        self._main_frame.pack(fill="both", expand=True, padx=1, pady=1)

        self._set_icon()

        # Check EULA
        if not self.cfg.get("eula_accepted", False):
            self.root.attributes("-alpha", 1.0)
            self._show_eula()
        else:
            self._build_ui()
            self._setup_resize()
            self._setup_dnd()
            self._start_gpu_monitor()
            self._debug_pump()
            self._fade_in()

        self.root.bind("<F11>", self._toggle_fullscreen)

    # ── EULA Dialog ──────────────────────────────────────────────
    def _show_eula(self):
        self._eula_win = tk.Toplevel(self.root)
        w = self._eula_win
        w.title(t("eula_title"))
        w.geometry("600x500")
        w.configure(bg=BG)
        w.resizable(False, False)
        w.grab_set()
        w.protocol("WM_DELETE_WINDOW", self._eula_decline)

        # Center on screen
        w.update_idletasks()
        sx = (w.winfo_screenwidth() - 600) // 2
        sy = (w.winfo_screenheight() - 500) // 2
        w.geometry(f"600x500+{sx}+{sy}")

        # Title
        tk.Label(w, text=t("eula_title"), font=(FONT, 16, "bold"),
                 fg=TEXT, bg=BG).pack(pady=(20, 10))

        # Language selector
        lang_frame = tk.Frame(w, bg=BG)
        lang_frame.pack(pady=(0, 10))
        tk.Label(lang_frame, text=t("eula_language") + ":", font=(FONT, 10),
                 fg=TEXT_SEC, bg=BG).pack(side="left", padx=(0, 8))
        self._eula_lang_var = tk.StringVar(value=self.cfg.get("language", "en"))
        lang_cb = ttk.Combobox(lang_frame, textvariable=self._eula_lang_var,
                               values=["en", "de", "fr", "es", "zh"],
                               state="readonly", width=8)
        lang_cb.pack(side="left")
        lang_cb.bind("<<ComboboxSelected>>", self._eula_lang_change)

        # Scrollable EULA text
        text_frame = tk.Frame(w, bg=SURFACE)
        text_frame.pack(fill="both", expand=True, padx=30, pady=10)
        self._eula_text = tk.Text(text_frame, bg=SURFACE, fg=TEXT, font=(FONT, 9),
                                   wrap="word", relief="flat", state="disabled",
                                   insertbackground=TEXT, padx=12, pady=12)
        eula_sb = ttk.Scrollbar(text_frame, command=self._eula_text.yview)
        eula_sb.pack(side="right", fill="y")
        self._eula_text.pack(fill="both", expand=True)
        self._eula_text.config(yscrollcommand=eula_sb.set)
        self._fill_eula_text()

        # Checkbox
        self._eula_agree = tk.BooleanVar(value=False)
        self._eula_cb = tk.Checkbutton(w, text=t("eula_checkbox"),
                                        variable=self._eula_agree,
                                        bg=BG, fg=TEXT, selectcolor=SURFACE,
                                        activebackground=BG, activeforeground=TEXT,
                                        font=(FONT, 9), command=self._eula_check_toggle)
        self._eula_cb.pack(pady=(5, 10))

        # Buttons
        btn_frame = tk.Frame(w, bg=BG)
        btn_frame.pack(pady=(0, 20))

        self._eula_continue_btn = tk.Button(btn_frame, text=t("eula_continue"),
                                             font=(FONT, 11, "bold"),
                                             bg=SURFACE_VAR, fg=TEXT_TER,
                                             relief="flat", padx=30, pady=8,
                                             state="disabled",
                                             command=self._eula_accept)
        self._eula_continue_btn.pack(side="left", padx=10)

        tk.Button(btn_frame, text=t("eula_decline"), font=(FONT, 11),
                  bg=SURFACE, fg=TEXT_SEC, relief="flat", padx=30, pady=8,
                  command=self._eula_decline).pack(side="left", padx=10)

    def _fill_eula_text(self):
        eula_content = """HONEYCLEAN - TERMS OF USE

1. LAWFUL USE ONLY
This software is provided for lawful purposes only. You agree not to use HoneyClean for any illegal activities, including but not limited to fraud, identity theft, or any activity that violates applicable laws.

2. NO DEEPFAKES / NON-CONSENSUAL IMAGE MANIPULATION
You agree not to use HoneyClean to create deepfakes or to manipulate images of individuals without their explicit consent. Creating misleading or harmful content using this software is strictly prohibited.

3. USER RESPONSIBILITY
You are solely responsible for all content processed through HoneyClean and for ensuring that your use of the software complies with all applicable laws and regulations. The developer assumes no liability for misuse.

4. NO WARRANTY
HoneyClean is provided "AS IS" without warranty of any kind, express or implied. The developer makes no guarantees regarding the software's fitness for any particular purpose.

5. MIT LICENSE
This software is released under the MIT License. You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, subject to the conditions of the MIT License.

6. ETHICAL USAGE COMMITMENT
By using HoneyClean, you commit to using this tool ethically and responsibly. You agree to respect the rights, privacy, and dignity of all individuals.

By clicking "Continue", you acknowledge that you have read, understood, and agree to these terms.
"""
        self._eula_text.config(state="normal")
        self._eula_text.delete("1.0", "end")
        self._eula_text.insert("1.0", eula_content)
        self._eula_text.config(state="disabled")

    def _eula_lang_change(self, event=None):
        lang = self._eula_lang_var.get()
        set_language(lang)
        self.cfg["language"] = lang
        self._eula_win.title(t("eula_title"))
        self._eula_cb.config(text=t("eula_checkbox"))
        self._eula_continue_btn.config(text=t("eula_continue"))

    def _eula_check_toggle(self):
        if self._eula_agree.get():
            self._eula_continue_btn.config(state="normal", bg=ACCENT, fg="#FFFFFF")
        else:
            self._eula_continue_btn.config(state="disabled", bg=SURFACE_VAR, fg=TEXT_TER)

    def _eula_accept(self):
        self.cfg["eula_accepted"] = True
        self.cfg["eula_accepted_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.cfg["language"] = self._eula_lang_var.get()
        set_language(self.cfg["language"])
        save_cfg(self.cfg)
        self._eula_win.destroy()

        self._build_ui()
        self._setup_resize()
        self._setup_dnd()
        self._start_gpu_monitor()
        self._debug_pump()
        self._fade_in()

    def _eula_decline(self):
        self.root.destroy()
        sys.exit()

    # ── Fade-in animation ────────────────────────────────────────
    def _fade_in(self):
        self._alpha = 0.0
        def step():
            self._alpha = min(self._alpha + 0.06, 1.0)
            self.root.attributes("-alpha", self._alpha)
            if self._alpha < 1.0:
                self.root.after(18, step)
        self.root.after(30, step)

    # ── Window icon ──────────────────────────────────────────────
    def _set_icon(self):
        try:
            logo = make_logo(32)
            self._icon = ImageTk.PhotoImage(logo)
            self.root.iconphoto(True, self._icon)
        except: pass

    # ── Resize handles ───────────────────────────────────────────
    def _setup_resize(self):
        grip_r = tk.Frame(self.root, width=5, bg=BORDER, cursor="sb_h_double_arrow")
        grip_r.place(relx=1.0, y=0, relheight=1.0, anchor="ne")
        grip_r.bind("<B1-Motion>", self._resize_r)

        grip_b = tk.Frame(self.root, height=5, bg=BORDER, cursor="sb_v_double_arrow")
        grip_b.place(x=0, rely=1.0, relwidth=1.0, anchor="sw")
        grip_b.bind("<B1-Motion>", self._resize_b)

        grip_br = tk.Frame(self.root, width=14, height=14, bg=BORDER, cursor="size_nw_se")
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

    # ── Title bar helpers ────────────────────────────────────────
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

    def _toggle_fullscreen(self, event=None):
        if self._fullscreen:
            self.root.overrideredirect(True)
            self.root.geometry(self._pre_fs_geo)
            self._fullscreen = False
        else:
            self._pre_fs_geo = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.overrideredirect(True)
            self.root.geometry(f"{sw}x{sh}+0+0")
            self._fullscreen = True

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

    # ── Build Title Bar ──────────────────────────────────────────
    def _build_title_bar(self, parent):
        title_bar = tk.Frame(parent, bg=SURFACE, height=38)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        # Drag bindings
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._do_drag)
        title_bar.bind("<Double-Button-1>", self._toggle_maximize)

        # Logo
        try:
            logo_img = make_logo(24)
            self._logo_tk = ImageTk.PhotoImage(logo_img)
            logo_lbl = tk.Label(title_bar, image=self._logo_tk, bg=SURFACE)
            logo_lbl.pack(side="left", padx=(12, 6))
            logo_lbl.bind("<Button-1>", self._start_drag)
            logo_lbl.bind("<B1-Motion>", self._do_drag)
        except: pass

        self._title_lbl = tk.Label(title_bar, text=t("app_title"), font=(FONT, 13, "bold"),
                             fg=TEXT, bg=SURFACE)
        self._title_lbl.pack(side="left")
        self._title_lbl.bind("<Button-1>", self._start_drag)
        self._title_lbl.bind("<B1-Motion>", self._do_drag)

        # Close button
        close_btn = tk.Label(title_bar, text=" \u2715 ", font=(FONT, 12),
                             fg=TEXT_TER, bg=SURFACE, cursor="hand2")
        close_btn.pack(side="right", padx=(0, 4))
        close_btn.bind("<Button-1>", lambda e: self._close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#FFFFFF", bg=ERROR_CLR))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_TER, bg=SURFACE))

        # Maximize button
        max_btn = tk.Label(title_bar, text=" \u25A1 ", font=(FONT, 12),
                           fg=TEXT_TER, bg=SURFACE, cursor="hand2")
        max_btn.pack(side="right", padx=2)
        max_btn.bind("<Button-1>", self._toggle_maximize)
        max_btn.bind("<Enter>", lambda e: max_btn.config(fg=TEXT, bg=SURFACE_VAR))
        max_btn.bind("<Leave>", lambda e: max_btn.config(fg=TEXT_TER, bg=SURFACE))

        # Minimize button
        min_btn = tk.Label(title_bar, text=" \u2500 ", font=(FONT, 12),
                           fg=TEXT_TER, bg=SURFACE, cursor="hand2")
        min_btn.pack(side="right", padx=2)
        min_btn.bind("<Button-1>", lambda e: self._minimize())
        min_btn.bind("<Enter>", lambda e: min_btn.config(fg=TEXT, bg=SURFACE_VAR))
        min_btn.bind("<Leave>", lambda e: min_btn.config(fg=TEXT_TER, bg=SURFACE))

        return title_bar

    # ── Build UI ─────────────────────────────────────────────────
    def _build_ui(self):
        mf = self._main_frame

        # Title bar
        self._build_title_bar(mf)

        # Main body: sidebar + content
        body = tk.Frame(mf, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────
        self._sidebar = tk.Frame(body, bg=SIDEBAR_BG, width=180)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Sidebar items
        self._nav_items = {}
        nav_data = [
            ("queue", "\U0001F4CB", t("nav_queue")),
            ("editor", "\u270F", t("nav_editor")),
            ("settings", "\u2699", t("nav_settings")),
            ("about", "\u2139", t("nav_about")),
        ]
        for page_name, icon, label in nav_data:
            item = SidebarItem(self._sidebar, icon=icon, text=label,
                               command=lambda p=page_name: self._show_page(p))
            item.pack(fill="x")
            self._nav_items[page_name] = item

        # GPU status at bottom of sidebar
        gpu_status_frame = tk.Frame(self._sidebar, bg=SIDEBAR_BG)
        gpu_status_frame.pack(side="bottom", fill="x", padx=8, pady=8)

        self._gpu_sidebar_lbl = tk.Label(gpu_status_frame, text=t("gpu_label") + ": --",
                                          font=(FONT, 8), fg=TEXT_SEC, bg=SIDEBAR_BG)
        self._gpu_sidebar_lbl.pack(anchor="w")

        self._vram_sidebar_lbl = tk.Label(gpu_status_frame, text=t("vram_label") + ": --",
                                           font=(FONT, 8), fg=TEXT_SEC, bg=SIDEBAR_BG)
        self._vram_sidebar_lbl.pack(anchor="w")

        self._gpu_name_sidebar_lbl = tk.Label(gpu_status_frame, text="",
                                               font=(FONT, 7), fg=TEXT_TER, bg=SIDEBAR_BG)
        self._gpu_name_sidebar_lbl.pack(anchor="w")

        self._fallback_lbl = tk.Label(gpu_status_frame, text="",
                                       font=(FONT, 7, "italic"), fg=ACCENT, bg=SIDEBAR_BG)
        self._fallback_lbl.pack(anchor="w")

        # ── Content Area ─────────────────────────────────────────
        self._content = tk.Frame(body, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        # Create all pages
        self._pages = {}
        self._pages["queue"] = tk.Frame(self._content, bg=BG)
        self._pages["editor"] = tk.Frame(self._content, bg=BG)
        self._pages["settings"] = tk.Frame(self._content, bg=BG)
        self._pages["about"] = tk.Frame(self._content, bg=BG)

        self._build_queue_page(self._pages["queue"])
        self._build_editor_page(self._pages["editor"])
        self._build_settings_page(self._pages["settings"])
        self._build_about_page(self._pages["about"])

        # Status label
        self.status_lbl = tk.Label(mf, text="", font=(FONT, 9, "italic"),
                                   fg=TEXT_SEC, bg=BG)
        self.status_lbl.pack(pady=(0, 2))

        # Footer
        self._footer = tk.Frame(mf, bg=SURFACE, height=24)
        self._footer.pack(fill="x", side="bottom")
        self._footer.pack_propagate(False)
        self._footer_lbl = tk.Label(self._footer, text=t("footer"),
                                     font=(FONT, 8), fg=TEXT_TER, bg=SURFACE)
        self._footer_lbl.pack(expand=True)

        # Debug Console (hidden by default)
        self.debug_frame = tk.Frame(mf, bg="#111113")
        self.debug_text = tk.Text(self.debug_frame, bg="#111113", fg=SUCCESS,
                                   font=("Consolas", 8), height=6, relief="flat",
                                   state="disabled", insertbackground=SUCCESS,
                                   selectbackground=ACCENT)
        self.debug_text.pack(fill="both", expand=True, padx=4, pady=2)
        dbsb = ttk.Scrollbar(self.debug_frame, command=self.debug_text.yview)
        dbsb.pack(side="right", fill="y")
        self.debug_text.config(yscrollcommand=dbsb.set)
        if self.cfg.get("debug"):
            self.debug_frame.pack(fill="x", padx=12, pady=(0, 4), before=self._footer)

        # Show default page
        self._show_page("queue")

    # ── Show Page ────────────────────────────────────────────────
    def _show_page(self, page_name):
        for name, page in self._pages.items():
            page.pack_forget()
        if page_name in self._pages:
            self._pages[page_name].pack(fill="both", expand=True, padx=12, pady=6)
        for name, item in self._nav_items.items():
            item.set_selected(name == page_name)
        self._current_page = page_name

    # ── Build Queue Page ─────────────────────────────────────────
    def _build_queue_page(self, parent):
        # Drop zone
        dz_frame = tk.Frame(parent, bg=SURFACE, padx=2, pady=2)
        dz_frame.pack(fill="x")
        self.drop_canvas = tk.Canvas(dz_frame, bg=SURFACE, highlightthickness=0,
                                     height=80, cursor="hand2")
        self.drop_canvas.pack(fill="x")
        self.drop_canvas.bind("<Button-1>", lambda e: self._browse_files())
        self.drop_canvas.bind("<Configure>", lambda e: self._draw_drop())
        self._dash_offset = 0
        self._animate_drop()

        # Add folder button
        folder_row = tk.Frame(parent, bg=BG)
        folder_row.pack(fill="x", pady=(4, 2))
        self._add_folder_btn = AppleButton(folder_row, text="\U0001F4C1  " + t("add_folder"),
                   style="secondary", width=200, height=32, font_size=9, bold=False,
                   command=self._browse_folder)
        self._add_folder_btn.pack(side="left")

        # Queue label
        self._queue_label = tk.Label(parent, text=t("queue_label"), font=(FONT, 8, "bold"),
                 fg=TEXT_SEC, bg=BG)
        self._queue_label.pack(anchor="w", pady=(4, 2))

        # Thumbnail grid
        self.thumb_grid = ThumbnailGrid(parent)
        self.thumb_grid.pack(fill="both", expand=True)

        # Hidden listbox for queue tracking
        self._q_list_frame = tk.Frame(parent)
        self.q_list = tk.Listbox(self._q_list_frame, bg=SURFACE, fg=TEXT, font=(FONT, 8),
                                  selectbackground=ACCENT, selectforeground="white",
                                  relief="flat", bd=0, activestyle="none",
                                  highlightthickness=0)
        self.q_list.pack(fill="both", expand=True)

        # Control buttons row
        btn_row = tk.Frame(parent, bg=BG)
        btn_row.pack(fill="x", pady=(6, 2))

        self.start_btn = AppleButton(btn_row, text="\u25B6  " + t("btn_start"),
                                     command=self._start, style="primary",
                                     width=140, height=40, font_size=11)
        self.start_btn.pack(side="left", padx=4)

        self.pause_btn = AppleButton(btn_row, text="\u23F8  " + t("btn_pause"),
                                     command=self._toggle_pause, style="secondary",
                                     width=140, height=40, font_size=11)
        self.pause_btn.set_state(False)
        self.pause_btn.pack(side="left", padx=4)

        self.stop_btn = AppleButton(btn_row, text="\u23F9  " + t("btn_stop"),
                                    command=self._stop, style="destructive",
                                    width=140, height=40, font_size=11)
        self.stop_btn.set_state(False)
        self.stop_btn.pack(side="left", padx=4)

        self._open_btn = AppleButton(btn_row, text="\U0001F4C2  " + t("open_output"),
                                     command=self._open_output, style="plain",
                                     width=160, height=40, font_size=9, bold=False)
        self._open_btn.pack(side="left", padx=4)

        self._clear_btn = AppleButton(btn_row, text="\U0001F5D1  " + t("clear_queue"),
                                      command=self._clear_queue, style="secondary",
                                      width=100, height=40, font_size=9, bold=False)
        self._clear_btn.pack(side="right", padx=4)

        # Progress section
        prog_row = tk.Frame(parent, bg=BG)
        prog_row.pack(fill="x", pady=(4, 0))

        self.prog = AppleProgress(prog_row, height=4)
        self.prog.pack(fill="x", pady=(0, 4))

        info_row = tk.Frame(parent, bg=BG)
        info_row.pack(fill="x")
        self.prog_lbl = tk.Label(info_row, text="0 / 0", font=(FONT, 8, "bold"),
                                  fg=TEXT, bg=BG, width=10, anchor="w")
        self.prog_lbl.pack(side="left")
        self.eta_lbl = tk.Label(info_row, text="", font=(FONT, 8), fg=TEXT_SEC,
                                 bg=BG, width=20, anchor="w")
        self.eta_lbl.pack(side="left")
        self._speed_lbl = tk.Label(info_row, text="", font=(FONT, 8), fg=TEXT_SEC,
                                    bg=BG, anchor="e")
        self._speed_lbl.pack(side="right")

        # File info label
        self.file_lbl = tk.Label(parent, text=t("file_add_images"),
                                  font=(FONT, 8), fg=TEXT_SEC, bg=BG)
        self.file_lbl.pack(pady=(2, 0))

    # ── Build Editor Page ────────────────────────────────────────
    def _build_editor_page(self, parent):
        # Retouch Toolbar
        tb_frame = tk.Frame(parent, bg=SURFACE, padx=8, pady=6)
        tb_frame.pack(fill="x")

        self._retouch_lbl = tk.Label(tb_frame, text=t("retouch") + ":", font=(FONT, 9, "bold"),
                 fg=TEXT_SEC, bg=SURFACE)
        self._retouch_lbl.pack(side="left", padx=(4, 8))

        self.erase_btn = tk.Button(tb_frame, text="\u270F " + t("erase"), font=(FONT, 9),
                  bg=SURFACE_VAR, fg=TEXT_SEC, relief="flat", padx=10, pady=4, cursor="hand2",
                  activebackground=ERROR_CLR, activeforeground="white",
                  command=self._toggle_erase)
        self.erase_btn.pack(side="left", padx=2)

        self.restore_btn = tk.Button(tb_frame, text="\U0001F504 " + t("restore"), font=(FONT, 9),
                  bg=SURFACE_VAR, fg=TEXT_SEC, relief="flat", padx=10, pady=4, cursor="hand2",
                  activebackground=SUCCESS, activeforeground="white",
                  command=self._toggle_restore)
        self.restore_btn.pack(side="left", padx=2)

        self._size_lbl = tk.Label(tb_frame, text=t("brush_size") + ":", font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE)
        self._size_lbl.pack(side="left", padx=(16, 4))
        self.brush_var = tk.IntVar(value=15)
        tk.Scale(tb_frame, from_=3, to=60, orient="horizontal", variable=self.brush_var,
                 bg=SURFACE, fg=TEXT_SEC, troughcolor=SURFACE_VAR, highlightthickness=0,
                 length=90, showvalue=False, sliderrelief="flat",
                 activebackground=ACCENT).pack(side="left")

        self._tol_lbl = tk.Label(tb_frame, text=t("tolerance") + ":", font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE)
        self._tol_lbl.pack(side="left", padx=(16, 4))
        self.tolerance_var = tk.IntVar(value=30)
        tk.Scale(tb_frame, from_=0, to=100, orient="horizontal", variable=self.tolerance_var,
                 bg=SURFACE, fg=TEXT_SEC, troughcolor=SURFACE_VAR, highlightthickness=0,
                 length=90, showvalue=False, sliderrelief="flat",
                 activebackground=ACCENT).pack(side="left")

        self._save_btn = tk.Button(tb_frame, text="\U0001F4BE " + t("save"), font=(FONT, 9),
                  bg=SUCCESS, fg="white", relief="flat", padx=10, pady=4,
                  cursor="hand2", activebackground="#28b84c", activeforeground="white",
                  command=self._save_edit)
        self._save_btn.pack(side="right", padx=8)

        self._reset_btn = tk.Button(tb_frame, text="\u21A9 " + t("reset"), font=(FONT, 9),
                  bg=SURFACE_VAR, fg=TEXT_SEC, relief="flat", padx=10, pady=4,
                  cursor="hand2", activebackground=SURFACE,
                  command=self._reset_edit)
        self._reset_btn.pack(side="right", padx=2)

        # Before / After panels
        pf = tk.Frame(parent, bg=BG)
        pf.pack(fill="both", expand=True, pady=(6, 0))

        # BEFORE
        before_frame = tk.Frame(pf, bg=SURFACE_VAR, padx=1, pady=1)
        before_frame.pack(side="left", fill="both", expand=True, padx=(0, 3))
        before_inner = tk.Frame(before_frame, bg=SURFACE)
        before_inner.pack(fill="both", expand=True)
        self._before_lbl = tk.Label(before_inner, text=t("before_label"), font=(FONT, 8, "bold"),
                 fg=ERROR_CLR, bg=SURFACE)
        self._before_lbl.pack(pady=3)
        self.before_cv = tk.Canvas(before_inner, bg="#1c1c1e", highlightthickness=0)
        self.before_cv.pack(fill="both", expand=True, padx=2, pady=(0, 2))

        # AFTER
        after_frame = tk.Frame(pf, bg=SURFACE_VAR, padx=1, pady=1)
        after_frame.pack(side="right", fill="both", expand=True, padx=(3, 0))
        after_inner = tk.Frame(after_frame, bg=SURFACE)
        after_inner.pack(fill="both", expand=True)

        after_header = tk.Frame(after_inner, bg=SURFACE)
        after_header.pack(fill="x")
        self._after_lbl = tk.Label(after_header, text=t("after_label"), font=(FONT, 8, "bold"),
                 fg=ACCENT, bg=SURFACE)
        self._after_lbl.pack(side="left", pady=3, padx=4)
        self.checker_var = tk.BooleanVar(value=True)
        self._checker_cb = tk.Checkbutton(after_header, text=t("checkerboard"),
                       variable=self.checker_var,
                       bg=SURFACE, fg=TEXT_SEC, selectcolor=SURFACE_VAR, font=(FONT, 8),
                       activebackground=SURFACE, activeforeground=TEXT,
                       command=self._refresh_after)
        self._checker_cb.pack(side="right", padx=6)

        self.after_cv = tk.Canvas(after_inner, bg="#1c1c1e", highlightthickness=0,
                                  cursor="crosshair")
        self.after_cv.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        self.after_cv.bind("<B1-Motion>", self._on_canvas_draw)
        self.after_cv.bind("<Button-1>", self._on_canvas_draw)

    # ── Build Settings Page ──────────────────────────────────────
    def _build_settings_page(self, parent):
        # Scrollable settings
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                                   style="Dark.Vertical.TScrollbar")
        settings_inner = tk.Frame(canvas, bg=BG)
        settings_inner.bind("<Configure>",
                            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=settings_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._settings_title_lbl = tk.Label(settings_inner, text=t("settings_title"),
                 font=(FONT, 16, "bold"), fg=TEXT, bg=BG)
        self._settings_title_lbl.pack(pady=(20, 16), anchor="w", padx=20)

        # ── General Section ──────────────────────────────────────
        self._section_general_lbl = tk.Label(settings_inner, text=t("section_general"),
                 font=(FONT, 11, "bold"), fg=ACCENT, bg=BG)
        self._section_general_lbl.pack(anchor="w", padx=20, pady=(10, 6))

        gen_frame = tk.Frame(settings_inner, bg=SURFACE, padx=16, pady=12)
        gen_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Output folder
        of_row = tk.Frame(gen_frame, bg=SURFACE)
        of_row.pack(fill="x", pady=4)
        self._output_dir_lbl = tk.Label(of_row, text=t("output_dir"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._output_dir_lbl.pack(side="left", padx=(0, 8))
        self._out_var = tk.StringVar(value=self.cfg.get("output_dir", ""))
        tk.Entry(of_row, textvariable=self._out_var, font=(FONT, 9), bg=SURFACE_VAR, fg=TEXT,
                 relief="flat", width=35, insertbackground=TEXT).pack(side="left", fill="x", expand=True)
        self._browse_settings_btn = tk.Button(of_row, text=t("browse"), bg=SURFACE_VAR, fg=TEXT_SEC,
                  relief="flat", padx=8, font=(FONT, 8),
                  command=lambda: self._out_var.set(filedialog.askdirectory() or self._out_var.get()))
        self._browse_settings_btn.pack(side="left", padx=(4, 0))

        # Language
        lang_row = tk.Frame(gen_frame, bg=SURFACE)
        lang_row.pack(fill="x", pady=4)
        self._language_lbl = tk.Label(lang_row, text=t("language"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._language_lbl.pack(side="left", padx=(0, 8))
        self._lang_var = tk.StringVar(value=self.cfg.get("language", "en"))
        ttk.Combobox(lang_row, textvariable=self._lang_var,
                     values=["en", "de", "fr", "es", "zh"],
                     state="readonly", width=12).pack(side="left")

        # Theme
        theme_row = tk.Frame(gen_frame, bg=SURFACE)
        theme_row.pack(fill="x", pady=4)
        self._theme_lbl = tk.Label(theme_row, text=t("theme"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._theme_lbl.pack(side="left", padx=(0, 8))
        self._theme_var = tk.StringVar(value=t("dark"))
        ttk.Combobox(theme_row, textvariable=self._theme_var,
                     values=[t("dark")], state="readonly", width=12).pack(side="left")

        # ── AI Model Section ─────────────────────────────────────
        self._section_ai_lbl = tk.Label(settings_inner, text=t("section_ai"),
                 font=(FONT, 11, "bold"), fg=ACCENT, bg=BG)
        self._section_ai_lbl.pack(anchor="w", padx=20, pady=(10, 6))

        ai_frame = tk.Frame(settings_inner, bg=SURFACE, padx=16, pady=12)
        ai_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Model
        model_row = tk.Frame(ai_frame, bg=SURFACE)
        model_row.pack(fill="x", pady=4)
        self._model_lbl = tk.Label(model_row, text=t("ai_model"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._model_lbl.pack(side="left", padx=(0, 8))
        self._model_var = tk.StringVar(value=self.cfg.get("model", "auto"))
        ttk.Combobox(model_row, textvariable=self._model_var,
                     values=["auto", "isnet-anime", "u2net", "u2net_human_seg",
                             "silueta", "isnet-general-use"],
                     state="readonly", width=20).pack(side="left")

        # Alpha FG
        afg_row = tk.Frame(ai_frame, bg=SURFACE)
        afg_row.pack(fill="x", pady=4)
        self._afg_lbl = tk.Label(afg_row, text=t("alpha_fg_label"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._afg_lbl.pack(side="left", padx=(0, 8))
        self._afg_var = tk.StringVar(value=str(self.cfg.get("alpha_fg", 240)))
        tk.Entry(afg_row, textvariable=self._afg_var, font=(FONT, 9), bg=SURFACE_VAR, fg=TEXT,
                 relief="flat", width=8, insertbackground=TEXT).pack(side="left")

        # Alpha BG
        abg_row = tk.Frame(ai_frame, bg=SURFACE)
        abg_row.pack(fill="x", pady=4)
        self._abg_lbl = tk.Label(abg_row, text=t("alpha_bg_label"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._abg_lbl.pack(side="left", padx=(0, 8))
        self._abg_var = tk.StringVar(value=str(self.cfg.get("alpha_bg", 10)))
        tk.Entry(abg_row, textvariable=self._abg_var, font=(FONT, 9), bg=SURFACE_VAR, fg=TEXT,
                 relief="flat", width=8, insertbackground=TEXT).pack(side="left")

        # Alpha Erode
        aer_row = tk.Frame(ai_frame, bg=SURFACE)
        aer_row.pack(fill="x", pady=4)
        self._aer_lbl = tk.Label(aer_row, text=t("alpha_erode_label"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._aer_lbl.pack(side="left", padx=(0, 8))
        self._aer_var = tk.StringVar(value=str(self.cfg.get("alpha_erode", 10)))
        tk.Entry(aer_row, textvariable=self._aer_var, font=(FONT, 9), bg=SURFACE_VAR, fg=TEXT,
                 relief="flat", width=8, insertbackground=TEXT).pack(side="left")

        # ── GPU Section ──────────────────────────────────────────
        self._section_gpu_lbl = tk.Label(settings_inner, text=t("section_gpu"),
                 font=(FONT, 11, "bold"), fg=ACCENT, bg=BG)
        self._section_gpu_lbl.pack(anchor="w", padx=20, pady=(10, 6))

        gpu_frame = tk.Frame(settings_inner, bg=SURFACE, padx=16, pady=12)
        gpu_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Use GPU
        gpu_check_row = tk.Frame(gpu_frame, bg=SURFACE)
        gpu_check_row.pack(fill="x", pady=4)
        self._use_gpu_var = tk.BooleanVar(value=self.cfg.get("use_gpu", True))
        self._use_gpu_cb = tk.Checkbutton(gpu_check_row, text=t("use_gpu_label"),
                       variable=self._use_gpu_var, bg=SURFACE, fg=TEXT,
                       selectcolor=SURFACE_VAR, activebackground=SURFACE,
                       activeforeground=TEXT, font=(FONT, 9))
        self._use_gpu_cb.pack(side="left")

        # GPU Limit
        gpu_limit_row = tk.Frame(gpu_frame, bg=SURFACE)
        gpu_limit_row.pack(fill="x", pady=4)
        self._gpu_limit_lbl = tk.Label(gpu_limit_row, text=t("gpu_limit_label"), font=(FONT, 9),
                 fg=TEXT_SEC, bg=SURFACE, width=14, anchor="e")
        self._gpu_limit_lbl.pack(side="left", padx=(0, 8))
        self.throttle_var = tk.IntVar(value=self.cfg["gpu_limit"])
        tk.Spinbox(gpu_limit_row, from_=0, to=100, width=6,
                   textvariable=self.throttle_var, font=(FONT, 9),
                   bg=SURFACE_VAR, fg=TEXT, relief="flat", buttonbackground=SURFACE_VAR
                   ).pack(side="left")

        # Save button
        self._save_settings_btn = AppleButton(settings_inner,
                                              text="\U0001F4BE  " + t("save_settings"),
                                              command=self._save_settings, style="primary",
                                              width=200, height=40, font_size=10)
        self._save_settings_btn.pack(pady=(16, 20), padx=20, anchor="w")

    # ── Build About Page ─────────────────────────────────────────
    def _build_about_page(self, parent):
        center = tk.Frame(parent, bg=BG)
        center.pack(expand=True)

        # Logo
        try:
            about_logo = make_logo(64)
            self._about_logo_tk = ImageTk.PhotoImage(about_logo)
            tk.Label(center, image=self._about_logo_tk, bg=BG).pack(pady=(0, 12))
        except: pass

        tk.Label(center, text=t("app_title"), font=(FONT, 24, "bold"),
                 fg=TEXT, bg=BG).pack()
        self._about_desc_lbl = tk.Label(center, text=t("about_desc"), font=(FONT, 11),
                 fg=TEXT_SEC, bg=BG)
        self._about_desc_lbl.pack(pady=(4, 16))

        info_frame = tk.Frame(center, bg=SURFACE, padx=30, pady=20)
        info_frame.pack()

        info_items = [
            (t("about_version"), VERSION),
            (t("about_author"), "Zayn1312"),
            (t("about_license"), "MIT"),
            (t("about_github"), "github.com/Zayn1312/HoneyClean"),
        ]
        self._about_info_labels = []
        for label, value in info_items:
            row = tk.Frame(info_frame, bg=SURFACE)
            row.pack(fill="x", pady=3)
            lbl = tk.Label(row, text=label + ":", font=(FONT, 10, "bold"),
                     fg=TEXT_SEC, bg=SURFACE, width=10, anchor="e")
            lbl.pack(side="left", padx=(0, 12))
            val = tk.Label(row, text=value, font=(FONT, 10),
                     fg=TEXT, bg=SURFACE, anchor="w")
            val.pack(side="left")
            self._about_info_labels.append((lbl, val))


    # ── Save Settings ────────────────────────────────────────────
    def _save_settings(self):
        old_model = self.cfg.get("model")
        old_lang = self.cfg.get("language")

        self.cfg["output_dir"] = self._out_var.get()
        self.cfg["language"] = self._lang_var.get()
        self.cfg["model"] = self._model_var.get()
        self.cfg["use_gpu"] = self._use_gpu_var.get()
        self.cfg["gpu_limit"] = self.throttle_var.get()

        try: self.cfg["alpha_fg"] = int(self._afg_var.get())
        except: pass
        try: self.cfg["alpha_bg"] = int(self._abg_var.get())
        except: pass
        try: self.cfg["alpha_erode"] = int(self._aer_var.get())
        except: pass

        save_cfg(self.cfg)

        # Reset session if model changed
        if self.cfg.get("model") != old_model:
            self.session = None
            self.session_model = None

        # Retranslate if language changed
        if self.cfg.get("language") != old_lang:
            set_language(self.cfg["language"])
            self._retranslate()

        self.status_lbl.config(text=t("settings_saved"), fg=SUCCESS)
        self._log(t("settings_saved"))

    def _save_throttle(self):
        self.cfg["gpu_limit"] = self.throttle_var.get()
        save_cfg(self.cfg)

    # ── Animated drop zone ───────────────────────────────────────
    def _draw_drop(self):
        c = self.drop_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10:
            return
        c.create_rectangle(8, 8, w-8, h-8, dash=(10, 5),
                           dashoffset=self._dash_offset,
                           outline=ACCENT, width=2)
        c.create_text(w//2, h//2 - 8, text="\U0001F4C2", font=(FONT, 16), fill=ACCENT)
        c.create_text(w//2, h//2 + 14,
                      text=t("drop_zone"),
                      font=(FONT, 8), fill=TEXT_SEC)

    def _animate_drop(self):
        self._dash_offset = (self._dash_offset + 1) % 15
        self._draw_drop()
        self.root.after(100, self._animate_drop)

    # ── Debug ────────────────────────────────────────────────────
    def _toggle_debug(self):
        self.cfg["debug"] = not self.cfg.get("debug", False)
        save_cfg(self.cfg)
        if self.cfg["debug"]:
            self.debug_frame.pack(fill="x", padx=12, pady=(0, 4), before=self._footer)
        else:
            self.debug_frame.pack_forget()

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

    # ── File browsing & queue ────────────────────────────────────
    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title=t("file_select"),
            filetypes=[(t("file_images_filter"), "*.png *.jpg *.jpeg *.webp *.bmp *.zip"),
                       ("All", "*.*")])
        for f in files:
            p = Path(f)
            if p.suffix.lower() == ".zip":
                extracted, err = _extract_zip(p, self.cfg.get("output_dir", "."))
                if err:
                    self._show_error(err)
                else:
                    for ep in extracted:
                        self._add(ep)
            else:
                valid, code = _validate_path(p)
                if valid:
                    img_valid, fmt = _validate_image(p)
                    if img_valid:
                        self._add(p)
                    else:
                        self._show_error("HC-011", path=str(p))
                else:
                    self._show_error(code, path=str(p))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title=t("file_select_folder"))
        if folder:
            valid, code = _validate_path(folder)
            # Folders won't pass _validate_path is_file check, handle directly
            fp = Path(folder)
            if fp.is_dir():
                for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"]:
                    for f in sorted(fp.rglob(ext)):
                        v, c = _validate_path(f)
                        if v:
                            iv, fmt = _validate_image(f)
                            if iv:
                                self._add(f)

    def _add(self, path):
        path = Path(path)
        if path not in self.queue_items:
            self.queue_items.append(path)
            self.q_list.insert("end", f"  {path.name}")
            self.thumb_grid.add_item(path, status="pending")
            self.prog.set(0, maximum=len(self.queue_items))
            self.prog_lbl.config(text=t("progress_of", current=0, total=len(self.queue_items)))
            self._log(t("file_added", name=path.name))

    def _clear_queue(self):
        if not self.processing:
            self.queue_items.clear()
            self.q_list.delete(0, "end")
            self.thumb_grid.clear()
            self.prog_lbl.config(text="0 / 0")
            self.prog.set(0)

    def _setup_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
            self._log("Drag & Drop enabled")
        except Exception as e:
            self._show_error("HC-041", error=str(e))

    def _on_drop(self, event):
        for m in re.finditer(r'\{([^}]+)\}|(\S+)', event.data):
            p = Path(m.group(1) or m.group(2))
            if p.suffix.lower() == ".zip":
                extracted, err = _extract_zip(p, self.cfg.get("output_dir", "."))
                if err:
                    self._show_error(err)
                else:
                    for ep in extracted:
                        self._add(ep)
            elif p.is_dir():
                for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"]:
                    for f in sorted(p.rglob(ext)):
                        v, c = _validate_path(f)
                        if v:
                            iv, fmt = _validate_image(f)
                            if iv:
                                self._add(f)
            elif p.exists():
                v, c = _validate_path(p)
                if v:
                    iv, fmt = _validate_image(p)
                    if iv:
                        self._add(p)

    def _open_output(self):
        out = self.cfg.get("output_dir", "")
        if out and os.path.exists(out):
            os.startfile(out)
        else:
            self.status_lbl.config(text=t("status_output_missing"), fg=WARNING)

    # ══════════════════════════════════════════════════════════════
    # SECTION 5: GPU + Processing + Display + Tools
    # ══════════════════════════════════════════════════════════════

    # ── GPU Monitoring ───────────────────────────────────────────
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
                            self._log(f"GPU {gpu}% > Limit {limit}% - throttling...")
                            time.sleep(1.5)
            except FileNotFoundError:
                self.root.after(0, lambda: self._gpu_name_sidebar_lbl.config(
                    text=t("gpu_not_found")))
                time.sleep(10)
                continue
            except Exception as e:
                self._log(f"GPU Monitor error: {e}")
            time.sleep(1)

    def _upd_gpu(self, gpu, mp, mu, mt, name):
        c = SUCCESS if gpu < 60 else WARNING if gpu < 85 else ERROR_CLR
        self._gpu_sidebar_lbl.config(text=f"{t('gpu_label')}: {gpu}%", fg=c)
        vc = SUCCESS if mp < 60 else WARNING if mp < 85 else ERROR_CLR
        self._vram_sidebar_lbl.config(text=f"{t('vram_label')}: {mu}M / {mt}M", fg=vc)
        self._gpu_name_sidebar_lbl.config(text=name)

    # ── Processing ───────────────────────────────────────────────
    def _start(self):
        if not self.queue_items:
            self.status_lbl.config(text=t("status_empty"), fg=WARNING)
            return
        if self.processing:
            return
        self.processing = True
        self.paused = False
        self.stop_flag = False
        self.start_btn.set_state(False)
        self.pause_btn.set_state(True, text="\u23F8  " + t("btn_pause"))
        self.stop_btn.set_state(True)
        threading.Thread(target=self._run, daemon=True).start()

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.set_state(True, text="\u25B6  " + t("btn_resume"))
            self.status_lbl.config(text=t("status_paused"), fg=WARNING)
        else:
            self.pause_btn.set_state(True, text="\u23F8  " + t("btn_pause"))
            self.status_lbl.config(text=t("status_processing"), fg=ACCENT)

    def _stop(self):
        self.stop_flag = True
        self.paused = False

    def _load_session(self):
        from rembg import new_session
        model = self.cfg.get("model", "auto")
        use_gpu = self.cfg.get("use_gpu", True)

        # Auto model selection
        if model == "auto":
            if self.session and self.session_model:
                return True
            self._log("Auto-selecting best model...")
            auto_model, auto_session = _auto_select_model()
            if auto_model:
                self.session = auto_session
                self.session_model = auto_model
                self._log(f"Auto-selected model: {auto_model}")
                self.root.after(0, lambda: self.status_lbl.config(
                    text=t("status_model_loaded") + f" ({auto_model})", fg=SUCCESS))
                return True
            else:
                self._show_error("HC-020", error="No model available")
                return False

        if self.session and self.session_model == model:
            return True

        self._log(f"Loading model: {model} (GPU={'yes' if use_gpu else 'no'})")

        providers = []
        if use_gpu:
            try:
                import onnxruntime as ort
                available = ort.get_available_providers()
                self._log(f"ORT providers: {available}")
                if "DmlExecutionProvider" in available:
                    providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
                    self._log("Using GPU (DirectML)")
                    self.root.after(0, lambda: self._fallback_lbl.config(
                        text="GPU (DirectML)", fg=SUCCESS))
                elif "CUDAExecutionProvider" in available:
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    self._log("Using GPU (CUDA)")
                    self.root.after(0, lambda: self._fallback_lbl.config(
                        text="GPU (CUDA)", fg=SUCCESS))
                else:
                    raise RuntimeError("No GPU provider available")
            except Exception as e:
                self._log(f"GPU unavailable ({e}) - CPU fallback")
                self._show_error("HC-022")
                self.root.after(0, lambda: self._fallback_lbl.config(
                    text=t("cpu_mode"), fg=WARNING))
                providers = ["CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]
            self.root.after(0, lambda: self._fallback_lbl.config(
                text=t("cpu_mode"), fg=TEXT_SEC))

        os.environ["ORT_LOGGING_LEVEL"] = "3"

        try:
            self.session = new_session(model, providers=providers)
        except TypeError:
            self.session = new_session(model)

        self.session_model = model
        self._log(f"Model loaded: {model}")
        return True

    def _run(self):
        self.root.after(0, lambda: self.status_lbl.config(
            text=t("status_loading"), fg=ACCENT))
        try:
            from rembg import remove
            if not self._load_session():
                self._finish()
                return
        except ImportError:
            self._show_error("HC-001")
            self._finish()
            return
        except Exception as e:
            self._log(f"Load error: {traceback.format_exc()}")
            self._show_error("HC-020", error=str(e))
            self._finish()
            return

        self.root.after(0, lambda: self.status_lbl.config(
            text=t("status_ready"), fg=SUCCESS))

        out_base = Path(self.cfg.get("output_dir",
                        str(Path.home() / "Downloads" / "HoneyClean_Output")))
        try:
            out_base.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._show_error("HC-024", path=str(out_base))
            self._finish()
            return

        total = len(self.queue_items)
        done = 0
        t0 = time.time()

        for i, img_path in enumerate(self.queue_items):
            if self.stop_flag:
                break
            while self.paused:
                time.sleep(0.3)

            # Update thumbnail status
            self.root.after(0, lambda idx=i: self.thumb_grid.update_status(idx, "processing"))

            self.root.after(0, lambda idx=i: [
                self.q_list.selection_clear(0, "end"),
                self.q_list.selection_set(idx),
                self.q_list.see(idx)
            ])

            out_file = out_base / (img_path.stem + "_clean.png")
            self.root.after(0, self._show_before, img_path)
            self.root.after(0, lambda n=img_path.name, c=i+1, tot=total:
                self.file_lbl.config(
                    text=t("file_processing", name=n, current=c, total=tot), fg=TEXT_SEC))
            self._log(t("file_processing", name=img_path.name, current=i+1, total=total))

            if out_file.exists():
                img = Image.open(out_file).convert("RGBA")
                self.root.after(0, self._show_after, img, img_path, out_file)
                done += 1
                self.root.after(0, self._upd_prog, done, total, t0)
                self.root.after(0, lambda idx=i: self.thumb_grid.update_status(idx, "done"))
                continue

            try:
                with open(img_path, "rb") as f:
                    data = f.read()

                from rembg import remove
                try:
                    out_data = remove(
                        data,
                        session=self.session,
                        alpha_matting=True,
                        alpha_matting_foreground_threshold=self.cfg.get("alpha_fg", 240),
                        alpha_matting_background_threshold=self.cfg.get("alpha_bg", 10),
                        alpha_matting_erode_size=self.cfg.get("alpha_erode", 10),
                    )
                except ImportError:
                    # pymatting not available, process without alpha matting
                    self._log("pymatting not available, processing without alpha matting")
                    self._show_error("HC-003")
                    out_data = remove(data, session=self.session)

                result = Image.open(io.BytesIO(out_data)).convert("RGBA")
                result.save(out_file, "PNG")

                self.root.after(0, self._show_after, result, img_path, out_file)
                self.root.after(0, lambda idx=i: self.thumb_grid.update_status(idx, "done"))
                self._log(f"Saved: {out_file.name}")
                done += 1
                self.root.after(0, self._upd_prog, done, total, t0)
                time.sleep(0.1)

            except Exception as e:
                self._log(f"Error {img_path.name}: {traceback.format_exc()}")
                self._show_error("HC-021", name=img_path.name, error=str(e))
                self.root.after(0, lambda idx=i: self.thumb_grid.update_status(idx, "error"))
                done += 1
                self.root.after(0, self._upd_prog, done, total, t0)

        self.root.after(0, lambda d=done: [
            self.status_lbl.config(
                text=t("status_done", count=d), fg=SUCCESS),
            self.file_lbl.config(text=f"{d} {t('images_processed')}")
        ])
        self._finish()

    def _finish(self):
        self.processing = False
        self.root.after(0, lambda: [
            self.start_btn.set_state(True, text="\u25B6  " + t("btn_start")),
            self.pause_btn.set_state(False, text="\u23F8  " + t("btn_pause")),
            self.stop_btn.set_state(False),
        ])

    def _upd_prog(self, done, total, t0):
        pct = int(done / total * 100) if total else 0
        self.prog.set(pct)
        self.prog_lbl.config(text=t("progress_of", current=done, total=total))
        if done > 0:
            elapsed = time.time() - t0
            per = elapsed / done
            rem = per * (total - done)
            m, s = divmod(int(rem), 60)
            self.eta_lbl.config(text=t("progress_eta", m=m, s=s))
            speed = round(60 / per, 1) if per > 0 else 0
            self._speed_lbl.config(text=t("progress_speed", speed=speed))

    # ── Image display ────────────────────────────────────────────
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
            bg = Image.new("RGB", disp.size, (28, 28, 30))
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
            bg = Image.new("RGB", disp.size, (28, 28, 30))
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

    # ── Erase / Restore tools ────────────────────────────────────
    def _toggle_erase(self):
        if self.tool_mode == "erase":
            self.tool_mode = "none"
            self.erase_btn.config(bg=SURFACE_VAR, fg=TEXT_SEC)
        else:
            self.tool_mode = "erase"
            self.erase_btn.config(bg=ERROR_CLR, fg="white")
            self.restore_btn.config(bg=SURFACE_VAR, fg=TEXT_SEC)

    def _toggle_restore(self):
        if self.tool_mode == "restore":
            self.tool_mode = "none"
            self.restore_btn.config(bg=SURFACE_VAR, fg=TEXT_SEC)
        else:
            self.tool_mode = "restore"
            self.restore_btn.config(bg=SUCCESS, fg="white")
            self.erase_btn.config(bg=SURFACE_VAR, fg=TEXT_SEC)

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
        if not hasattr(self, "_edit_after") or not hasattr(self, "_out_path") or self._out_path is None:
            self.status_lbl.config(text=t("status_no_image"), fg=WARNING)
            return
        self._edit_after.save(self._out_path, "PNG")
        self.status_lbl.config(text=t("status_saved", name=self._out_path.name), fg=SUCCESS)
        self._log(f"Edit saved: {self._out_path}")

    def _reset_edit(self):
        if hasattr(self, "_orig_after"):
            self._edit_after = self._orig_after.copy()
            self._refresh_after()
            self.status_lbl.config(text=t("status_reset_done"), fg=TEXT_SEC)

    # ── Error Handling ───────────────────────────────────────────
    def _show_error(self, code, **kwargs):
        msg_template = ERROR_REGISTRY.get(code, "Unknown error")
        try:
            msg = msg_template.format(**kwargs)
        except:
            msg = msg_template
        full_msg = f"[{code}] {msg}"
        self._log(full_msg)
        self.root.after(0, lambda: self.status_lbl.config(
            text=t("status_error", error=full_msg), fg=ERROR_CLR))
        # Show dialog for critical errors
        if code in ("HC-001", "HC-002", "HC-004", "HC-005", "HC-020"):
            self.root.after(0, lambda: self._error_dialog(code, msg))

    def _error_dialog(self, code, message):
        w = tk.Toplevel(self.root)
        w.title(t("error_title") + f" [{code}]")
        w.geometry("450x220")
        w.configure(bg=BG)
        w.resizable(False, False)
        w.grab_set()
        w.update_idletasks()
        px = self.root.winfo_x() + (self.root.winfo_width() - 450) // 2
        py = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
        w.geometry(f"+{px}+{py}")

        tk.Label(w, text=t("error_title"), font=(FONT, 14, "bold"),
                 fg=ERROR_CLR, bg=BG).pack(pady=(16, 8))
        tk.Label(w, text=f"[{code}]", font=(FONT, 11, "bold"),
                 fg=TEXT, bg=BG).pack()
        tk.Label(w, text=message, font=(FONT, 9),
                 fg=TEXT_SEC, bg=BG, wraplength=400).pack(pady=(4, 12))

        btn_frame = tk.Frame(w, bg=BG)
        btn_frame.pack(pady=(0, 16))

        import webbrowser
        tk.Button(btn_frame, text=t("error_visit_wiki"), font=(FONT, 9),
                  bg=ACCENT, fg="white", relief="flat", padx=16, pady=6,
                  command=lambda: webbrowser.open(f"{WIKI_BASE}#{code}")
                  ).pack(side="left", padx=6)
        tk.Button(btn_frame, text=t("error_close"), font=(FONT, 9),
                  bg=SURFACE_VAR, fg=TEXT_SEC, relief="flat", padx=16, pady=6,
                  command=w.destroy).pack(side="left", padx=6)

    # ── Retranslate UI ───────────────────────────────────────────
    def _retranslate(self):
        """Update all UI text when language changes."""
        # Sidebar items
        nav_labels = {
            "queue": t("nav_queue"),
            "editor": t("nav_editor"),
            "settings": t("nav_settings"),
            "about": t("nav_about"),
        }
        for name, item in self._nav_items.items():
            item.set_text(nav_labels.get(name, name))

        # Title bar
        if hasattr(self, "_title_lbl"):
            self._title_lbl.config(text=t("app_title"))

        # Footer
        if hasattr(self, "_footer_lbl"):
            self._footer_lbl.config(text=t("footer"))

        # GPU sidebar labels
        self._gpu_sidebar_lbl.config(text=t("gpu_label") + ": --")
        self._vram_sidebar_lbl.config(text=t("vram_label") + ": --")

        # Queue page
        if hasattr(self, "_queue_label"):
            self._queue_label.config(text=t("queue_label"))
        if hasattr(self, "file_lbl"):
            self.file_lbl.config(text=t("file_add_images"))

        # Editor page
        if hasattr(self, "_retouch_lbl"):
            self._retouch_lbl.config(text=t("retouch") + ":")
        if hasattr(self, "_size_lbl"):
            self._size_lbl.config(text=t("brush_size") + ":")
        if hasattr(self, "_tol_lbl"):
            self._tol_lbl.config(text=t("tolerance") + ":")
        if hasattr(self, "_before_lbl"):
            self._before_lbl.config(text=t("before_label"))
        if hasattr(self, "_after_lbl"):
            self._after_lbl.config(text=t("after_label"))
        if hasattr(self, "_checker_cb"):
            self._checker_cb.config(text=t("checkerboard"))

        # Settings page
        if hasattr(self, "_settings_title_lbl"):
            self._settings_title_lbl.config(text=t("settings_title"))
        if hasattr(self, "_section_general_lbl"):
            self._section_general_lbl.config(text=t("section_general"))
        if hasattr(self, "_section_ai_lbl"):
            self._section_ai_lbl.config(text=t("section_ai"))
        if hasattr(self, "_section_gpu_lbl"):
            self._section_gpu_lbl.config(text=t("section_gpu"))
        if hasattr(self, "_output_dir_lbl"):
            self._output_dir_lbl.config(text=t("output_dir"))
        if hasattr(self, "_language_lbl"):
            self._language_lbl.config(text=t("language"))
        if hasattr(self, "_theme_lbl"):
            self._theme_lbl.config(text=t("theme"))
        if hasattr(self, "_model_lbl"):
            self._model_lbl.config(text=t("ai_model"))
        if hasattr(self, "_afg_lbl"):
            self._afg_lbl.config(text=t("alpha_fg_label"))
        if hasattr(self, "_abg_lbl"):
            self._abg_lbl.config(text=t("alpha_bg_label"))
        if hasattr(self, "_aer_lbl"):
            self._aer_lbl.config(text=t("alpha_erode_label"))
        if hasattr(self, "_gpu_limit_lbl"):
            self._gpu_limit_lbl.config(text=t("gpu_limit_label"))

        # About page
        if hasattr(self, "_about_desc_lbl"):
            self._about_desc_lbl.config(text=t("about_desc"))

        # Status
        self.status_lbl.config(text="")


# ── Entry Point ──────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except Exception:
        root = tk.Tk()

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TProgressbar", troughcolor=SURFACE_VAR, background=ACCENT, thickness=4)
    style.configure("Dark.Vertical.TScrollbar",
                    background=SURFACE, troughcolor=BG,
                    borderwidth=0, arrowsize=8, relief="flat")
    style.map("Dark.Vertical.TScrollbar",
              background=[("active", ACCENT), ("pressed", ACCENT)])
    style.configure("TCombobox", fieldbackground=SURFACE, background=SURFACE_VAR,
                    foreground=TEXT, selectbackground=ACCENT)

    app = HoneyClean(root)
    root.mainloop()
