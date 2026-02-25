import multiprocessing
multiprocessing.freeze_support()

"""
HoneyClean v4.0 - AI Background Remover
Complete Overhaul by Zayn1312
"""

import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

import tkinter as tk
from tkinter import filedialog, colorchooser
import threading, os, io, time, sys, json, subprocess, traceback, queue, math, re, importlib.util
import zipfile, tempfile
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFilter
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

VERSION = "4.0"

# ── Colors ───────────────────────────────────────────────────────
C = {
    "bg": "#0A0A0F", "sidebar": "#111118", "card": "#1A1A25",
    "card_hover": "#252535", "border": "#2A2A3A", "border_bright": "#353550",
    "accent": "#007AFF", "accent_hover": "#0066DD", "accent_dim": "#003D99",
    "text": "#FFFFFF", "text_muted": "#8A8A9A", "text_dim": "#404060",
    "success": "#34C759", "warning": "#FF9500", "error": "#FF3B30",
    "console_bg": "#080810", "console_text": "#00FF88",
}
FONT = "Segoe UI"

# ── i18n ─────────────────────────────────────────────────────────
STRINGS = {"en": {}, "de": {}, "fr": {}, "es": {}, "zh": {}}

def _tr(key, en, de, fr, es, zh):
    for lang, val in [("en",en),("de",de),("fr",fr),("es",es),("zh",zh)]:
        STRINGS[lang][key] = val

_current_lang = "en"
def t(key, **kw):
    s = STRINGS.get(_current_lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
    if kw:
        try: s = s.format(**kw)
        except Exception: pass
    return s

def set_language(lang):
    global _current_lang
    if lang in STRINGS: _current_lang = lang

_tr("app_title", "HoneyClean", "HoneyClean", "HoneyClean", "HoneyClean", "HoneyClean")
_tr("footer", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312", "Made with <3 by Zayn1312")
_tr("nav_queue", "Queue", "Warteschlange", "File d'attente", "Cola", "\u961f\u5217")
_tr("nav_editor", "Editor", "Editor", "\u00c9diteur", "Editor", "\u7f16\u8f91\u5668")
_tr("nav_settings", "Settings", "Einstellungen", "Param\u00e8tres", "Ajustes", "\u8bbe\u7f6e")
_tr("nav_about", "About", "\u00dcber", "\u00c0 propos", "Acerca de", "\u5173\u4e8e")
_tr("eula_title", "Terms of Use", "Nutzungsbedingungen", "Conditions d'utilisation", "T\u00e9rminos de uso", "\u4f7f\u7528\u6761\u6b3e")
_tr("eula_language", "Language", "Sprache", "Langue", "Idioma", "\u8bed\u8a00")
_tr("eula_checkbox", "I have read and agree to the terms of use", "Ich habe die Nutzungsbedingungen gelesen und stimme zu", "J'ai lu et j'accepte les conditions d'utilisation", "He le\u00eddo y acepto los t\u00e9rminos de uso", "\u6211\u5df2\u9605\u8bfb\u5e76\u540c\u610f\u4f7f\u7528\u6761\u6b3e")
_tr("eula_continue", "Continue", "Weiter", "Continuer", "Continuar", "\u7ee7\u7eed")
_tr("eula_decline", "Decline", "Ablehnen", "Refuser", "Rechazar", "\u62d2\u7edd")
_tr("drop_zone", "Drop files here or click to browse", "Dateien hier ablegen oder klicken", "D\u00e9posez les fichiers ici ou cliquez", "Suelte archivos aqu\u00ed o haga clic", "\u5c06\u6587\u4ef6\u62d6\u653e\u5230\u6b64\u5904\u6216\u70b9\u51fb\u6d4f\u89c8")
_tr("add_folder", "Add Folder", "Ordner hinzuf\u00fcgen", "Ajouter un dossier", "Agregar carpeta", "\u6dfb\u52a0\u6587\u4ef6\u5939")
_tr("queue_label", "Queue", "Warteschlange", "File d'attente", "Cola", "\u961f\u5217")
_tr("clear_queue", "Clear", "Leeren", "Vider", "Limpiar", "\u6e05\u7a7a")
_tr("btn_start", "START", "START", "D\u00c9MARRER", "INICIAR", "\u5f00\u59cb")
_tr("btn_pause", "PAUSE", "PAUSE", "PAUSE", "PAUSA", "\u6682\u505c")
_tr("btn_resume", "RESUME", "WEITER", "REPRENDRE", "REANUDAR", "\u7ee7\u7eed")
_tr("btn_stop", "STOP", "STOPP", "ARR\u00caTER", "DETENER", "\u505c\u6b62")
_tr("open_output", "Open Output", "Ausgabe \u00f6ffnen", "Ouvrir la sortie", "Abrir salida", "\u6253\u5f00\u8f93\u51fa")
_tr("retouch", "Retouch", "Retusche", "Retouche", "Retocar", "\u4fee\u56fe")
_tr("erase", "Erase", "Radieren", "Effacer", "Borrar", "\u64e6\u9664")
_tr("restore", "Restore", "Wiederherstellen", "Restaurer", "Restaurar", "\u6062\u590d")
_tr("brush_size", "Size", "Gr\u00f6\u00dfe", "Taille", "Tama\u00f1o", "\u5927\u5c0f")
_tr("tolerance", "Tolerance", "Toleranz", "Tol\u00e9rance", "Tolerancia", "\u5bb9\u5dee")
_tr("save", "Save", "Speichern", "Enregistrer", "Guardar", "\u4fdd\u5b58")
_tr("reset", "Reset", "Zur\u00fccksetzen", "R\u00e9initialiser", "Restablecer", "\u91cd\u7f6e")
_tr("before_label", "BEFORE", "VORHER", "AVANT", "ANTES", "\u4e4b\u524d")
_tr("after_label", "AFTER", "NACHHER", "APR\u00c8S", "DESPU\u00c9S", "\u4e4b\u540e")
_tr("settings_title", "Settings", "Einstellungen", "Param\u00e8tres", "Ajustes", "\u8bbe\u7f6e")
_tr("output_dir", "Output Folder", "Ausgabeordner", "Dossier de sortie", "Carpeta de salida", "\u8f93\u51fa\u6587\u4ef6\u5939")
_tr("language", "Language", "Sprache", "Langue", "Idioma", "\u8bed\u8a00")
_tr("theme", "Theme", "Design", "Th\u00e8me", "Tema", "\u4e3b\u9898")
_tr("ai_model", "AI Model", "KI-Modell", "Mod\u00e8le IA", "Modelo IA", "AI\u6a21\u578b")
_tr("alpha_fg_label", "Alpha FG", "Alpha VG", "Alpha PP", "Alpha PP", "\u524d\u666fAlpha")
_tr("alpha_bg_label", "Alpha BG", "Alpha HG", "Alpha AP", "Alpha FD", "\u80cc\u666fAlpha")
_tr("alpha_erode_label", "Alpha Erode", "Alpha Erosion", "Alpha \u00c9rosion", "Alpha Erosi\u00f3n", "Alpha\u4fb5\u8680")
_tr("use_gpu_label", "Use GPU", "GPU verwenden", "Utiliser GPU", "Usar GPU", "\u4f7f\u7528GPU")
_tr("gpu_limit_label", "GPU Limit %", "GPU Limit %", "Limite GPU %", "L\u00edmite GPU %", "GPU\u9650\u5236%")
_tr("save_settings", "Save Settings", "Einstellungen speichern", "Enregistrer les param\u00e8tres", "Guardar ajustes", "\u4fdd\u5b58\u8bbe\u7f6e")
_tr("section_general", "General", "Allgemein", "G\u00e9n\u00e9ral", "General", "\u5e38\u89c4")
_tr("section_ai", "AI Engine", "KI-Engine", "Moteur IA", "Motor IA", "AI\u5f15\u64ce")
_tr("section_gpu", "GPU", "GPU", "GPU", "GPU", "GPU")
_tr("about_title", "About", "\u00dcber", "\u00c0 propos", "Acerca de", "\u5173\u4e8e")
_tr("about_desc", "AI-powered background remover", "KI-gest\u00fctzte Hintergrundentfernung", "Suppression d'arri\u00e8re-plan par IA", "Eliminador de fondo con IA", "AI\u9a71\u52a8\u7684\u80cc\u666f\u79fb\u9664\u5de5\u5177")
_tr("about_version", "Version", "Version", "Version", "Versi\u00f3n", "\u7248\u672c")
_tr("about_author", "Author", "Autor", "Auteur", "Autor", "\u4f5c\u8005")
_tr("about_license", "License", "Lizenz", "Licence", "Licencia", "\u8bb8\u53ef\u8bc1")
_tr("about_github", "GitHub", "GitHub", "GitHub", "GitHub", "GitHub")
_tr("status_loading", "Loading AI model...", "Lade KI-Modell...", "Chargement du mod\u00e8le IA...", "Cargando modelo IA...", "\u6b63\u5728\u52a0\u8f7dAI\u6a21\u578b...")
_tr("status_processing", "Processing...", "Verarbeite...", "Traitement en cours...", "Procesando...", "\u5904\u7406\u4e2d...")
_tr("status_done", "Done! {count} images processed", "Fertig! {count} Bilder verarbeitet", "Termin\u00e9 ! {count} images trait\u00e9es", "\u00a1Listo! {count} im\u00e1genes procesadas", "\u5b8c\u6210\uff01\u5df2\u5904\u7406{count}\u5f20\u56fe\u7247")
_tr("status_error", "Error: {error}", "Fehler: {error}", "Erreur : {error}", "Error: {error}", "\u9519\u8bef\uff1a{error}")
_tr("status_paused", "Paused", "Pausiert", "En pause", "En pausa", "\u5df2\u6682\u505c")
_tr("status_empty", "Queue is empty!", "Warteschlange ist leer!", "La file d'attente est vide !", "\u00a1La cola est\u00e1 vac\u00eda!", "\u961f\u5217\u4e3a\u7a7a\uff01")
_tr("status_saved", "Saved: {name}", "Gespeichert: {name}", "Enregistr\u00e9 : {name}", "Guardado: {name}", "\u5df2\u4fdd\u5b58\uff1a{name}")
_tr("status_ready", "Ready", "Bereit", "Pr\u00eat", "Listo", "\u5c31\u7eea")
_tr("status_model_loaded", "Model loaded", "Modell geladen", "Mod\u00e8le charg\u00e9", "Modelo cargado", "\u6a21\u578b\u5df2\u52a0\u8f7d")
_tr("progress_of", "{current} / {total}", "{current} / {total}", "{current} / {total}", "{current} / {total}", "{current} / {total}")
_tr("gpu_label", "GPU", "GPU", "GPU", "GPU", "GPU")
_tr("vram_label", "VRAM", "VRAM", "VRAM", "VRAM", "\u663e\u5b58")
_tr("cpu_mode", "CPU Mode", "CPU Modus", "Mode CPU", "Modo CPU", "CPU\u6a21\u5f0f")
_tr("dep_title", "Missing Dependencies", "Fehlende Abh\u00e4ngigkeiten", "D\u00e9pendances manquantes", "Dependencias faltantes", "\u7f3a\u5c11\u4f9d\u8d56")
_tr("dep_missing", "The following packages are missing:", "Die folgenden Pakete fehlen:", "Les paquets suivants sont manquants :", "Faltan los siguientes paquetes:", "\u7f3a\u5c11\u4ee5\u4e0b\u8f6f\u4ef6\u5305\uff1a")
_tr("dep_install", "Install", "Installieren", "Installer", "Instalar", "\u5b89\u88c5")
_tr("error_title", "Error", "Fehler", "Erreur", "Error", "\u9519\u8bef")
_tr("file_images_filter", "Images", "Bilder", "Images", "Im\u00e1genes", "\u56fe\u7247")
_tr("file_select", "Select Images", "Bilder ausw\u00e4hlen", "S\u00e9lectionner des images", "Seleccionar im\u00e1genes", "\u9009\u62e9\u56fe\u7247")
_tr("dark", "Dark", "Dunkel", "Sombre", "Oscuro", "\u6df1\u8272")
_tr("browse", "Browse", "Durchsuchen", "Parcourir", "Explorar", "\u6d4f\u89c8")
_tr("settings_saved", "Settings saved", "Einstellungen gespeichert", "Param\u00e8tres enregistr\u00e9s", "Ajustes guardados", "\u8bbe\u7f6e\u5df2\u4fdd\u5b58")
_tr("mode_auto", "\u26a1 Auto", "\u26a1 Auto", "\u26a1 Auto", "\u26a1 Auto", "\u26a1 \u81ea\u52a8")
_tr("mode_review", "\U0001f441 Review", "\U0001f441 \u00dcberpr\u00fcfen", "\U0001f441 R\u00e9viser", "\U0001f441 Revisar", "\U0001f441 \u5ba1\u67e5")
_tr("output_format", "Output Format", "Ausgabeformat", "Format de sortie", "Formato de salida", "\u8f93\u51fa\u683c\u5f0f")
_tr("platform_preset", "Platform Preset", "Plattform-Vorlage", "Pr\u00e9r\u00e9glage plateforme", "Preajuste de plataforma", "\u5e73\u53f0\u9884\u8bbe")
_tr("edge_feather", "Feather", "Weichzeichner", "Adoucir", "Difuminar", "\u7fbd\u5316")
_tr("undo", "Undo", "R\u00fcckg\u00e4ngig", "Annuler", "Deshacer", "\u64a4\u9500")
_tr("redo", "Redo", "Wiederholen", "R\u00e9tablir", "Rehacer", "\u91cd\u505a")

# Model display names
_tr("model_auto_name", "Auto (Recommended)", "Auto (Empfohlen)", "Auto (Recommand\u00e9)", "Auto (Recomendado)", "\u81ea\u52a8\uff08\u63a8\u8350\uff09")
_tr("model_auto_desc", "Automatically selects the best model.", "W\u00e4hlt automatisch das beste Modell.", "S\u00e9lectionne automatiquement le meilleur mod\u00e8le.", "Selecciona autom\u00e1ticamente el mejor modelo.", "\u81ea\u52a8\u9009\u62e9\u6700\u4f73\u6a21\u578b\u3002")
_tr("model_birefnet_general_name", "BiRefNet General \u2014 Best Quality", "BiRefNet General \u2014 Beste Qualit\u00e4t", "BiRefNet General \u2014 Meilleure qualit\u00e9", "BiRefNet General \u2014 Mejor calidad", "BiRefNet\u901a\u7528 \u2014 \u6700\u4f73\u8d28\u91cf")
_tr("model_birefnet_general_desc", "Top accuracy for hair, fur and complex edges.", "H\u00f6chste Genauigkeit f\u00fcr Haare, Fell und komplexe Kanten.", "Pr\u00e9cision maximale pour cheveux, fourrure et bords complexes.", "M\u00e1xima precisi\u00f3n para cabello, pelaje y bordes complejos.", "\u6700\u9ad8\u7cbe\u5ea6\uff0c\u9002\u5408\u5934\u53d1\u3001\u6bdb\u53d1\u548c\u590d\u6742\u8fb9\u7f18\u3002")
_tr("model_birefnet_massive_name", "BiRefNet Massive \u2014 Maximum Detail", "BiRefNet Massive \u2014 Maximales Detail", "BiRefNet Massive \u2014 D\u00e9tail maximum", "BiRefNet Massive \u2014 Detalle m\u00e1ximo", "BiRefNet\u5927\u578b \u2014 \u6700\u5927\u7ec6\u8282")
_tr("model_birefnet_massive_desc", "Largest model, slowest but most precise.", "Gr\u00f6\u00dftes Modell, langsamer aber am pr\u00e4zisesten.", "Plus grand mod\u00e8le, plus lent mais plus pr\u00e9cis.", "Modelo m\u00e1s grande, m\u00e1s lento pero m\u00e1s preciso.", "\u6700\u5927\u6a21\u578b\uff0c\u6700\u6162\u4f46\u6700\u7cbe\u786e\u3002")
_tr("model_birefnet_portrait_name", "BiRefNet Portrait \u2014 People Focus", "BiRefNet Portr\u00e4t \u2014 Personenfokus", "BiRefNet Portrait \u2014 Focus personnes", "BiRefNet Retrato \u2014 Enfoque personas", "BiRefNet\u8096\u50cf \u2014 \u4eba\u7269\u805a\u7126")
_tr("model_birefnet_portrait_desc", "Optimized for portraits and people.", "Optimiert f\u00fcr Portr\u00e4ts und Personen.", "Optimis\u00e9 pour portraits et personnes.", "Optimizado para retratos y personas.", "\u9488\u5bf9\u8096\u50cf\u548c\u4eba\u7269\u4f18\u5316\u3002")
_tr("model_birefnet_lite_name", "BiRefNet Lite \u2014 Fast Quality", "BiRefNet Lite \u2014 Schnelle Qualit\u00e4t", "BiRefNet Lite \u2014 Qualit\u00e9 rapide", "BiRefNet Lite \u2014 Calidad r\u00e1pida", "BiRefNet\u8f7b\u91cf \u2014 \u5feb\u901f\u8d28\u91cf")
_tr("model_birefnet_lite_desc", "Good quality with faster processing.", "Gute Qualit\u00e4t mit schnellerer Verarbeitung.", "Bonne qualit\u00e9 avec traitement plus rapide.", "Buena calidad con procesamiento m\u00e1s r\u00e1pido.", "\u826f\u597d\u8d28\u91cf\u4e14\u5904\u7406\u66f4\u5feb\u3002")
_tr("model_isnet_general_name", "ISNet General \u2014 Reliable Classic", "ISNet General \u2014 Zuverl\u00e4ssiger Klassiker", "ISNet General \u2014 Classique fiable", "ISNet General \u2014 Cl\u00e1sico confiable", "ISNet\u901a\u7528 \u2014 \u53ef\u9760\u7ecf\u5178")
_tr("model_isnet_general_desc", "Well-tested all-rounder model.", "Bew\u00e4hrtes Allzweckmodell.", "Mod\u00e8le polyvalent bien test\u00e9.", "Modelo de prop\u00f3sito general bien probado.", "\u7ecf\u8fc7\u5145\u5206\u6d4b\u8bd5\u7684\u901a\u7528\u6a21\u578b\u3002")
_tr("model_u2net_name", "U2Net \u2014 Standard", "U2Net \u2014 Standard", "U2Net \u2014 Standard", "U2Net \u2014 Est\u00e1ndar", "U2Net \u2014 \u6807\u51c6")
_tr("model_u2net_desc", "Classic model. Fast and reliable.", "Klassisches Modell. Schnell und zuverl\u00e4ssig.", "Mod\u00e8le classique. Rapide et fiable.", "Modelo cl\u00e1sico. R\u00e1pido y confiable.", "\u7ecf\u5178\u6a21\u578b\u3002\u5feb\u901f\u53ef\u9760\u3002")
_tr("model_isnet_anime_name", "ISNet Anime \u2014 Anime & Illustration", "ISNet Anime \u2014 Anime & Illustration", "ISNet Anime \u2014 Anime & Illustration", "ISNet Anime \u2014 Anime e ilustraci\u00f3n", "ISNet\u52a8\u6f2b \u2014 \u52a8\u6f2b\u548c\u63d2\u753b")
_tr("model_isnet_anime_desc", "Specialized for anime and manga art.", "Spezialisiert auf Anime- und Manga-Kunst.", "Sp\u00e9cialis\u00e9 pour l'art anime et manga.", "Especializado en arte anime y manga.", "\u4e13\u4e3a\u52a8\u6f2b\u548c\u6f2b\u753b\u827a\u672f\u8bbe\u8ba1\u3002")
_tr("model_u2net_human_name", "U2Net Human \u2014 People Only", "U2Net Human \u2014 Nur Personen", "U2Net Humain \u2014 Personnes uniquement", "U2Net Humano \u2014 Solo personas", "U2Net\u4eba\u50cf \u2014 \u4ec5\u4eba\u7269")
_tr("model_u2net_human_desc", "Optimized for human subjects only.", "Nur f\u00fcr menschliche Motive optimiert.", "Optimis\u00e9 uniquement pour les sujets humains.", "Optimizado solo para sujetos humanos.", "\u4ec5\u9488\u5bf9\u4eba\u7269\u4e3b\u9898\u4f18\u5316\u3002")
_tr("model_silueta_name", "Silueta \u2014 Lightweight", "Silueta \u2014 Leichtgewicht", "Silueta \u2014 L\u00e9ger", "Silueta \u2014 Ligero", "Silueta \u2014 \u8f7b\u91cf\u7ea7")
_tr("model_silueta_desc", "Smallest and fastest. Lower quality.", "Kleinstes und schnellstes. Geringere Qualit\u00e4t.", "Le plus petit et le plus rapide. Qualit\u00e9 inf\u00e9rieure.", "M\u00e1s peque\u00f1o y r\u00e1pido. Menor calidad.", "\u6700\u5c0f\u6700\u5feb\u3002\u8d28\u91cf\u8f83\u4f4e\u3002")

# ── Error Codes ──────────────────────────────────────────────────
ERROR_REGISTRY = {
    "HC-001": "rembg not installed", "HC-002": "Pillow not installed",
    "HC-003": "pymatting not installed", "HC-004": "onnxruntime not installed",
    "HC-005": "numpy not installed",
    "HC-010": "File not found: {path}", "HC-011": "Invalid file type: {path}",
    "HC-012": "Path traversal detected: {path}",
    "HC-013": "ZIP exceeds 500MB", "HC-014": "ZIP bomb detected",
    "HC-015": "ZIP path traversal", "HC-016": "ZIP extraction failed: {error}",
    "HC-017": "Invalid image data: {path}",
    "HC-020": "Model load failed: {error}", "HC-021": "Processing failed: {name}: {error}",
    "HC-022": "GPU unavailable, using CPU", "HC-023": "Model not found: {model}",
    "HC-024": "Cannot create output dir: {path}",
    "HC-030": "Config corrupted", "HC-031": "Config save failed: {error}",
    "HC-040": "UI init failed: {error}", "HC-041": "DnD unavailable: {error}",
    "HC-042": "Shadow generation failed", "HC-043": "Export preset failed",
    "HC-044": "Edge feather failed", "HC-045": "Color decontamination failed",
}
WIKI_BASE = "https://github.com/Zayn1312/HoneyClean/wiki/Error-Codes"

# ── Config ───────────────────────────────────────────────────────
CFG_PATH = Path(os.environ.get("APPDATA", ".")) / "HoneyClean" / "config.json"
DEFAULT_CFG = {
    "output_dir": str(Path.home() / "Downloads" / "HoneyClean_Output"),
    "gpu_limit": 100, "model": "auto", "alpha_fg": 270, "alpha_bg": 20,
    "alpha_erode": 15, "use_gpu": True, "debug": False,
    "language": "en", "theme": "dark",
    "eula_accepted": False, "eula_accepted_date": "",
    "process_mode": "auto", "color_decontaminate": True,
    "output_format": "png", "shadow_type": "none",
    "quality_preset": "quality", "edge_feather": 0,
    "platform_preset": "None",
}

def load_cfg():
    try:
        CFG_PATH.parent.mkdir(exist_ok=True)
        if CFG_PATH.exists():
            return {**DEFAULT_CFG, **json.loads(CFG_PATH.read_text())}
    except Exception:
        pass
    return DEFAULT_CFG.copy()

def save_cfg(c):
    try:
        CFG_PATH.parent.mkdir(exist_ok=True)
        CFG_PATH.write_text(json.dumps(c, indent=2))
    except Exception:
        pass

# ── Security ─────────────────────────────────────────────────────
def _validate_path(path):
    p = str(path)
    if ".." in p:
        return False, "HC-012"
    path = Path(path)
    if not path.exists() or not path.is_file():
        return False, "HC-010"
    return True, None

def _validate_image(path):
    try:
        with open(path, "rb") as f:
            h = f.read(12)
        if h[:4] == b'\x89PNG': return True, "PNG"
        if h[:3] == b'\xff\xd8\xff': return True, "JPEG"
        if h[:4] == b'RIFF' and h[8:12] == b'WEBP': return True, "WEBP"
        if h[:2] == b'BM': return True, "BMP"
        if h[:4] in (b'II\x2a\x00', b'MM\x00\x2a'): return True, "TIFF"
        return False, None
    except Exception:
        return False, None

def _sanitize_filename(name, max_len=200):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).lstrip('.')
    if not name: name = "unnamed"
    if len(name) > max_len:
        stem, ext = os.path.splitext(name)
        name = stem[:max_len - len(ext)] + ext
    return name

# ── ZIP Handling ─────────────────────────────────────────────────
def _extract_zip(zip_path, output_dir):
    zip_path = Path(zip_path)
    tmp_dir = Path(output_dir) / ".honeyclean_tmp" / zip_path.stem
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            total_size = sum(i.file_size for i in zf.infolist())
            if total_size > 500 * 1024 * 1024: return [], "HC-013"
            compressed = sum(i.compress_size for i in zf.infolist() if i.compress_size > 0)
            if compressed > 0 and total_size / compressed > 100: return [], "HC-014"
            extracted = []
            for info in zf.infolist():
                if info.is_dir(): continue
                if ".." in info.filename or info.filename.startswith("/"): return [], "HC-015"
                fname = _sanitize_filename(Path(info.filename).name)
                if Path(fname).suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
                    continue
                target = tmp_dir / fname
                with zf.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                valid, _ = _validate_image(target)
                if valid:
                    extracted.append(target)
                else:
                    target.unlink(missing_ok=True)
            return extracted, None
    except zipfile.BadZipFile:
        return [], "HC-016"
    except Exception:
        return [], "HC-016"

# ── Dependencies ─────────────────────────────────────────────────
def check_dependencies():
    deps = [
        ("rembg", {"critical": True, "pip": "rembg"}),
        ("PIL", {"critical": True, "pip": "Pillow"}),
        ("onnxruntime", {"critical": True, "pip": "onnxruntime"}),
        ("numpy", {"critical": True, "pip": "numpy"}),
        ("pymatting", {"critical": False, "pip": "pymatting"}),
    ]
    missing = []
    for name, info in deps:
        try:
            if importlib.util.find_spec(name) is None:
                missing.append((name, info))
        except (ModuleNotFoundError, ValueError):
            missing.append((name, info))
    return missing

def _auto_install(package):
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception:
        return False

# ── Model System ─────────────────────────────────────────────────
MODEL_PRIORITY = [
    "birefnet-general", "birefnet-massive", "birefnet-portrait",
    "birefnet-general-lite", "isnet-general-use", "u2net",
    "isnet-anime", "u2net_human_seg", "silueta",
]
MODEL_INFO = {
    "auto": {"name_key": "model_auto_name", "desc_key": "model_auto_desc"},
    "birefnet-general": {"name_key": "model_birefnet_general_name", "desc_key": "model_birefnet_general_desc"},
    "birefnet-massive": {"name_key": "model_birefnet_massive_name", "desc_key": "model_birefnet_massive_desc"},
    "birefnet-portrait": {"name_key": "model_birefnet_portrait_name", "desc_key": "model_birefnet_portrait_desc"},
    "birefnet-general-lite": {"name_key": "model_birefnet_lite_name", "desc_key": "model_birefnet_lite_desc"},
    "isnet-general-use": {"name_key": "model_isnet_general_name", "desc_key": "model_isnet_general_desc"},
    "u2net": {"name_key": "model_u2net_name", "desc_key": "model_u2net_desc"},
    "isnet-anime": {"name_key": "model_isnet_anime_name", "desc_key": "model_isnet_anime_desc"},
    "u2net_human_seg": {"name_key": "model_u2net_human_name", "desc_key": "model_u2net_human_desc"},
    "silueta": {"name_key": "model_silueta_name", "desc_key": "model_silueta_desc"},
}
MODEL_ORDER = ["auto", "birefnet-general", "birefnet-massive", "birefnet-portrait",
               "birefnet-general-lite", "isnet-general-use", "u2net",
               "isnet-anime", "u2net_human_seg", "silueta"]

QUALITY_PRESETS = {
    "fast": {"model": "silueta", "alpha_matting": False},
    "balanced": {"model": "isnet-general-use", "alpha_matting": True},
    "quality": {"model": "birefnet-general", "alpha_matting": True},
    "anime": {"model": "isnet-anime", "alpha_matting": False},
    "portrait": {"model": "birefnet-portrait", "alpha_matting": True},
}

PLATFORM_PRESETS = {
    "Amazon": {"bg": (255,255,255), "size": (2000,2000), "padding_pct": 0.05, "format": "jpeg"},
    "Shopify": {"bg": (255,255,255), "size": (2048,2048), "padding_pct": 0.08, "format": "png"},
    "Etsy": {"bg": None, "size": (2700,2025), "padding_pct": 0.05, "format": "png"},
    "eBay": {"bg": (255,255,255), "size": (1600,1600), "padding_pct": 0.05, "format": "jpeg"},
    "Instagram": {"bg": None, "size": (1080,1080), "padding_pct": 0.10, "format": "png"},
}

# ── Image Processing ─────────────────────────────────────────────
def generate_shadow(fg_img, shadow_type="drop", opacity=0.6, blur_radius=20, offset=(8, 12)):
    if shadow_type == "none" or not fg_img:
        return fg_img
    alpha = fg_img.split()[3]
    w, h = fg_img.size
    if shadow_type == "contact":
        offset, blur_radius = (0, h // 8), 15
    elif shadow_type == "float":
        offset, blur_radius = (0, h // 6), 30
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(blur_radius))
    shadow_color = Image.new("RGBA", (w, h), (0, 0, 0, int(255 * opacity)))
    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_layer.paste(shadow_color, mask=shadow_mask)
    pad = max(abs(offset[0]), abs(offset[1])) + blur_radius
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    canvas.paste(shadow_layer, (pad + offset[0], pad + offset[1]), shadow_layer)
    canvas.paste(fg_img, (pad, pad), fg_img)
    return canvas

def decontaminate_edges(img, strength=0.5):
    try:
        import numpy as np
        arr = np.array(img, dtype=np.float32)
        if arr.shape[2] < 4: return img
        rgb, alpha = arr[:, :, :3], arr[:, :, 3:4] / 255.0
        opaque = alpha[:, :, 0] > 0.9
        if opaque.sum() == 0: return img
        avg = rgb[opaque].mean(axis=0)
        semi = (alpha[:, :, 0] > 0.05) & (alpha[:, :, 0] < 0.9)
        blend = (1.0 - alpha[semi]) * strength
        rgb[semi] = rgb[semi] * (1 - blend[:, np.newaxis]) + avg * blend[:, np.newaxis]
        out = np.concatenate([np.clip(rgb, 0, 255), arr[:, :, 3:4]], axis=2).astype(np.uint8)
        return Image.fromarray(out)
    except Exception:
        return img

def apply_edge_feather(img, radius):
    if radius <= 0: return img
    alpha = img.split()[3]
    result = img.copy()
    result.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius)))
    return result

def apply_platform_preset(result_img, preset):
    bbox = result_img.split()[3].getbbox()
    if not bbox: return result_img
    subject = result_img.crop(bbox)
    tw, th = preset["size"]
    pad = preset["padding_pct"]
    mw, mh = int(tw * (1 - 2 * pad)), int(th * (1 - 2 * pad))
    subject.thumbnail((mw, mh), Image.LANCZOS)
    if preset["bg"]:
        canvas = Image.new("RGB", (tw, th), preset["bg"])
        canvas.paste(subject, ((tw - subject.width) // 2, (th - subject.height) // 2), subject.split()[3])
    else:
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        canvas.paste(subject, ((tw - subject.width) // 2, (th - subject.height) // 2))
    return canvas

def replace_background(fg_img, bg_type, bg_value=None):
    if bg_type == "transparent": return fg_img
    w, h = fg_img.size
    if bg_type == "white":
        bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    elif bg_type == "color" and bg_value:
        bg = Image.new("RGBA", (w, h), (*bg_value, 255))
    elif bg_type == "image" and bg_value:
        bg = bg_value.resize((w, h), Image.LANCZOS).convert("RGBA")
    else:
        return fg_img
    canvas = Image.new("RGBA", (w, h))
    canvas.paste(bg, (0, 0))
    canvas.paste(fg_img, (0, 0), fg_img.split()[3])
    return canvas

def _make_checker(w, h, sq=12):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            c = (200, 200, 200) if (x // sq + y // sq) % 2 == 0 else (150, 150, 150)
            d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=c)
    return img


# ══════════════════════════════════════════════════════════════════
# MAIN APPLICATION CLASS
# ══════════════════════════════════════════════════════════════════
class HoneyClean(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.cfg = load_cfg()
        set_language(self.cfg.get("language", "en"))

        self.title("HoneyClean")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])

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

        if not self.cfg.get("eula_accepted"):
            self._show_eula()
        else:
            self._build_ui()

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
        self._build_ui()

    # ── Build UI ─────────────────────────────────────────────────
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
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._on_drop)
        except Exception:
            pass

    # ── Sidebar ──────────────────────────────────────────────────
    def _build_sidebar(self):
        logo = ctk.CTkFrame(self._sidebar, fg_color="transparent", height=60)
        logo.pack(fill="x", padx=12, pady=(16, 8))
        ctk.CTkLabel(logo, text="\U0001f36f HoneyClean", font=(FONT, 15, "bold"),
                     text_color=C["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo, text=f"v{VERSION}", font=(FONT, 9), text_color=C["text_muted"]).pack(anchor="w")

        self._nav_btns = {}
        for pid, icon, tkey in [("queue", "\U0001f4c1", "nav_queue"), ("editor", "\u270f\ufe0f", "nav_editor"),
                                 ("settings", "\u2699\ufe0f", "nav_settings"), ("about", "\u2139\ufe0f", "nav_about")]:
            btn = ctk.CTkButton(self._sidebar, text=f"  {icon}  {t(tkey)}", anchor="w", height=40,
                                corner_radius=8, font=(FONT, 12), fg_color="transparent",
                                hover_color=C["card_hover"], text_color=C["text_muted"], cursor="hand2",
                                command=lambda p=pid: self._show_page(p))
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns[pid] = btn

        self._gpu_lbl = ctk.CTkLabel(self._sidebar, text="GPU: --", font=(FONT, 9), text_color=C["text_dim"])
        self._gpu_lbl.pack(side="bottom", padx=12, pady=8, anchor="w")
        self._vram_lbl = ctk.CTkLabel(self._sidebar, text="VRAM: --", font=(FONT, 9), text_color=C["text_dim"])
        self._vram_lbl.pack(side="bottom", padx=12, anchor="w")

    def _show_page(self, pid):
        self._current_page = pid
        for k, f in self._pages.items():
            f.pack(fill="both", expand=True) if k == pid else f.pack_forget()
        for k, b in self._nav_btns.items():
            if k == pid:
                b.configure(fg_color=C["accent_dim"], text_color=C["accent"])
            else:
                b.configure(fg_color="transparent", text_color=C["text_muted"])

    # ── Queue Page ───────────────────────────────────────────────
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
        ctk.CTkLabel(self._empty_frame, text=t("drop_zone"), font=(FONT, 14),
                     text_color=C["text_muted"]).pack(pady=(8, 4))
        ctk.CTkLabel(self._empty_frame, text="PNG, JPG, JPEG, BMP, TIFF, WebP, ZIP",
                     font=(FONT, 10), text_color=C["text_dim"]).pack()

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

    # ── Editor Page ──────────────────────────────────────────────
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

    # ── Settings Page ────────────────────────────────────────────
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

        ctk.CTkButton(page, text=f"\U0001f4be  {t('save_settings')}", width=200, height=40, fg_color=C["accent"],
                      hover_color=C["accent_hover"], corner_radius=8, cursor="hand2", font=(FONT, 12, "bold"),
                      command=self._save_settings).pack(pady=20)

    # ── About Page ───────────────────────────────────────────────
    def _build_about_page(self):
        page = ctk.CTkFrame(self._content, fg_color=C["bg"], corner_radius=0)
        self._pages["about"] = page
        ctr = ctk.CTkFrame(page, fg_color="transparent")
        ctr.pack(expand=True)
        ctk.CTkLabel(ctr, text="\U0001f36f", font=(FONT, 64)).pack(pady=(0, 8))
        ctk.CTkLabel(ctr, text="HoneyClean", font=(FONT, 28, "bold"), text_color=C["accent"]).pack()
        ctk.CTkLabel(ctr, text=t("about_desc"), font=(FONT, 12), text_color=C["text_muted"]).pack(pady=(4, 16))
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

    # ── Status Bar ───────────────────────────────────────────────
    def _build_status_bar(self):
        sb = ctk.CTkFrame(self._content, fg_color=C["card"], height=28, corner_radius=0)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self._sb_processed = ctk.CTkLabel(sb, text="\U0001f5bc 0 processed", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_processed.pack(side="left", padx=12)
        self._sb_speed = ctk.CTkLabel(sb, text="\u26a1 --", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_speed.pack(side="left", padx=12)
        self._sb_queued = ctk.CTkLabel(sb, text="\U0001f4cb 0 queued", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_queued.pack(side="left", padx=12)
        self._sb_gpu = ctk.CTkLabel(sb, text="\U0001f3ae GPU: --", font=(FONT, 9), text_color=C["text_dim"])
        self._sb_gpu.pack(side="left", padx=12)
        self._sb_state = ctk.CTkLabel(sb, text="\u25cf Ready", font=(FONT, 9), text_color=C["success"])
        self._sb_state.pack(side="right", padx=12)

    # ── File Management ──────────────────────────────────────────
    def _browse_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"), ("ZIP", "*.zip"), ("All", "*.*")])
        for f in files:
            self._add_file(Path(f))

    def _browse_folder(self):
        d = filedialog.askdirectory()
        if d:
            for f in Path(d).rglob("*"):
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"):
                    self._add_file(f)

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
        card.bind("<Enter>", lambda e, c=card: c.configure(border_color=C["accent"]))
        card.bind("<Leave>", lambda e, c=card: c.configure(border_color=C["border"]))
        il = ctk.CTkLabel(card, text="", width=120, height=100)
        il.pack(pady=(8, 4))
        name = path.name[:15] + "\u2026" if len(path.name) > 18 else path.name
        ctk.CTkLabel(card, text=name, font=(FONT, 9), text_color=C["text_muted"]).pack()
        sl = ctk.CTkLabel(card, text="\u23f3 Pending", font=(FONT, 8), text_color=C["text_dim"])
        sl.pack()
        self._thumb_cards.append({"card": card, "img_label": il, "status_label": sl, "path": path})
        threading.Thread(target=self._gen_thumb, args=(idx, path, il), daemon=True).start()

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
        self._empty_frame.pack(expand=True, pady=60)
        self._update_queue_header()

    def _update_queue_header(self):
        n = len(self.queue_items)
        self._queue_hdr.configure(text=f"{t('queue_label')} ({n})")
        self._sb_queued.configure(text=f"\U0001f4cb {n} queued")

    # ── Processing ───────────────────────────────────────────────
    def _start_processing(self):
        if not self.queue_items:
            self._show_toast(t("status_empty"), "warning")
            return
        if self.processing: return
        self.processing = True
        self.paused = False
        self.stop_flag = False
        self._results.clear()
        self._process_start_time = time.time()
        self._sb_state.configure(text="\u25cf Processing\u2026", text_color=C["warning"])
        self.title("HoneyClean \u2014 Processing\u2026")
        threading.Thread(target=self._run, daemon=True).start()

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self._btn_pause.configure(text=f"\u25b6  {t('btn_resume')}")
            self._sb_state.configure(text="\u25cf Paused", text_color=C["warning"])
        else:
            self._btn_pause.configure(text=f"\u2016  {t('btn_pause')}")
            self._sb_state.configure(text="\u25cf Processing\u2026", text_color=C["warning"])

    def _stop_processing(self):
        self.stop_flag = True
        self.processing = False
        self._sb_state.configure(text="\u25cf Stopped", text_color=C["error"])
        self.title("HoneyClean")

    def _load_session(self, model):
        if self.session and self.session_model == model:
            return True
        try:
            from rembg import new_session
            providers = []
            if self.cfg.get("use_gpu", True):
                try:
                    import onnxruntime as ort
                    avail = ort.get_available_providers()
                    if "DmlExecutionProvider" in avail: providers.append("DmlExecutionProvider")
                    if "CUDAExecutionProvider" in avail: providers.append("CUDAExecutionProvider")
                except Exception:
                    pass
                providers.append("CPUExecutionProvider")
            if model == "auto":
                for m in MODEL_PRIORITY:
                    try:
                        self.session = new_session(m, providers=providers or None)
                        self.session_model = m
                        self._log_active_provider()
                        return True
                    except Exception:
                        continue
                return False
            self.session = new_session(model, providers=providers or None)
            self.session_model = model
            self._log_active_provider()
            return True
        except Exception as e:
            self.result_queue.put(("log", f"Model load error: {e}"))
            return False

    def _log_active_provider(self):
        try:
            inner = getattr(self.session, 'inner_session', None) or getattr(self.session, 'session', None)
            if inner:
                active = inner.get_providers()
                self.result_queue.put(("log", f"Model: {self.session_model} | Providers: {active}"))
            else:
                self.result_queue.put(("log", f"Model: {self.session_model} | Providers: unknown"))
        except Exception:
            pass

    def _save_single(self, path, result):
        out_dir = Path(self.cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
        out_dir.mkdir(parents=True, exist_ok=True)
        fmt = self.cfg.get("output_format", "png").lower()
        preset_name = self.cfg.get("platform_preset", "None")
        preset = PLATFORM_PRESETS.get(preset_name) if preset_name != "None" else None
        stem = _sanitize_filename(path.stem)
        try:
            img = apply_platform_preset(result, preset) if preset else result
            if preset:
                fmt = preset["format"]
            if fmt == "jpeg":
                op = out_dir / f"{stem}_clean.jpg"
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img)
                bg.save(str(op), "JPEG", quality=95)
            elif fmt == "webp":
                img.save(str(out_dir / f"{stem}_clean.webp"), "WEBP", quality=95)
            else:
                img.save(str(out_dir / f"{stem}_clean.png"), "PNG")
        except Exception:
            pass

    def _run(self):
        import gc
        from rembg import remove
        model = self.cfg.get("model", "auto")
        self.result_queue.put(("log", f"Loading: {model}"))
        if not self._load_session(model):
            self.result_queue.put(("batch_done", 0, len(self.queue_items)))
            self.processing = False
            return
        total = len(self.queue_items)
        auto_mode = self.cfg.get("process_mode") == "auto"
        done_count = 0
        last_path = last_inp = last_result = None
        for i, img_path in enumerate(self.queue_items):
            if self.stop_flag: break
            while self.paused and not self.stop_flag: time.sleep(0.1)
            if self.stop_flag: break
            self.result_queue.put(("progress", i, total))
            self.result_queue.put(("thumb_status", i, "processing"))
            try:
                data = img_path.read_bytes()
                try:
                    out = remove(data, session=self.session, alpha_matting=True,
                                 alpha_matting_foreground_threshold=self.cfg.get("alpha_fg", 270),
                                 alpha_matting_background_threshold=self.cfg.get("alpha_bg", 20),
                                 alpha_matting_erode_size=self.cfg.get("alpha_erode", 15),
                                 post_process_mask=True)
                except TypeError:
                    out = remove(data, session=self.session)
                result = Image.open(io.BytesIO(out)).convert("RGBA")
                del data, out
                if self.cfg.get("color_decontaminate", True):
                    result = decontaminate_edges(result)
                feather = self.cfg.get("edge_feather", 0)
                if feather > 0:
                    result = apply_edge_feather(result, feather)
                if auto_mode:
                    self._save_single(img_path, result)
                    last_path, last_inp, last_result = img_path, None, result
                    del result
                else:
                    inp = Image.open(img_path).convert("RGBA")
                    self._results.append((img_path, inp, result))
                    last_path, last_inp, last_result = img_path, inp, result
                done_count += 1
                self.result_queue.put(("thumb_status", i, "done"))
            except Exception as e:
                self.result_queue.put(("thumb_status", i, "error"))
                self.result_queue.put(("log", f"Error: {img_path.name}: {e}"))
            gc.collect()
        self.result_queue.put(("progress", total, total))
        self.result_queue.put(("batch_done", done_count, total))
        self.processing = False
        if last_path and last_result:
            if not last_inp:
                try: last_inp = Image.open(last_path).convert("RGBA")
                except Exception: last_inp = last_result.copy()
            self._editor_before_img = last_inp
            self._editor_after_img = last_result

    def _poll_results(self):
        try:
            while True:
                msg = self.result_queue.get_nowait()
                kind = msg[0]
                if kind == "progress":
                    i, total = msg[1], msg[2]
                    self._pbar.set(i / max(1, total))
                    self._progress_lbl.configure(text=f"{i} / {total}")
                    self._sb_processed.configure(text=f"\U0001f5bc {i} processed")
                    elapsed = time.time() - self._process_start_time
                    if elapsed > 0 and i > 0:
                        self._sb_speed.configure(text=f"\u26a1 {round(i / (elapsed / 60), 1)}/min")
                elif kind == "thumb_status":
                    idx, status = msg[1], msg[2]
                    if idx < len(self._thumb_cards):
                        clrs = {"processing": C["warning"], "done": C["success"], "error": C["error"]}
                        lbls = {"processing": "\u23f3 Processing", "done": "\u2713 Done", "error": "\u2717 Error"}
                        self._thumb_cards[idx]["status_label"].configure(
                            text=lbls.get(status, status), text_color=clrs.get(status, C["text_dim"]))
                elif kind == "batch_done":
                    done, total = msg[1], msg[2]
                    self._pbar.set(1.0)
                    self._progress_lbl.configure(text=f"{done} / {total}")
                    self._show_toast(t("status_done", count=done), "success")
                    self._sb_state.configure(text="\u25cf Ready", text_color=C["success"])
                    self.title("HoneyClean")
                    out_dir = self.cfg.get("output_dir", "")
                    if out_dir and os.path.isdir(out_dir):
                        self.after(500, lambda: self._open_folder(out_dir))
                elif kind == "log":
                    pass
        except queue.Empty:
            pass
        self.after(100, self._poll_results)

    def _save_batch(self):
        out_dir = Path(self.cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
        out_dir.mkdir(parents=True, exist_ok=True)
        fmt = self.cfg.get("output_format", "png").lower()
        preset_name = self.cfg.get("platform_preset", "None")
        preset = PLATFORM_PRESETS.get(preset_name) if preset_name != "None" else None
        for path, orig, result in self._results:
            stem = _sanitize_filename(path.stem)
            try:
                img = apply_platform_preset(result, preset) if preset else result
                if preset:
                    fmt = preset["format"]
                if fmt == "jpeg":
                    op = out_dir / f"{stem}_clean.jpg"
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        bg.paste(img, mask=img.split()[3])
                    else:
                        bg.paste(img)
                    bg.save(str(op), "JPEG", quality=95)
                elif fmt == "webp":
                    img.save(str(out_dir / f"{stem}_clean.webp"), "WEBP", quality=95)
                else:
                    img.save(str(out_dir / f"{stem}_clean.png"), "PNG")
            except Exception:
                pass

    # ── Editor Methods ───────────────────────────────────────────
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

    # ── Utilities ────────────────────────────────────────────────
    def _show_toast(self, message, toast_type="success"):
        clrs = {"success": C["success"], "warning": C["warning"], "error": C["error"], "info": C["accent"]}
        toast = ctk.CTkLabel(self, text=f"  {message}  ", fg_color=clrs.get(toast_type, C["accent"]),
                              corner_radius=8, font=(FONT, 11), text_color="#FFFFFF", height=36)
        toast.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-50)
        self.after(3000, lambda: toast.destroy())

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
                self._gpu_lbl.configure(text=f"GPU: {parts[0].strip()}%")
                self._vram_lbl.configure(text=f"VRAM: {parts[1].strip()}/{parts[2].strip()} MB")
                self._sb_gpu.configure(text=f"\U0001f3ae {parts[1].strip()}/{parts[2].strip()}MB")
        except Exception:
            self._gpu_lbl.configure(text=t("cpu_mode"))
        self.after(2000, self._update_gpu_info)

    def _open_folder(self, path):
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def _toggle_fullscreen(self):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _on_drop(self, event):
        for f in self.tk.splitlist(event.data):
            self._add_file(Path(f))

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

    def _on_lang_change(self, val):
        m = {"English": "en", "Deutsch": "de", "Fran\u00e7ais": "fr", "Espa\u00f1ol": "es", "\u4e2d\u6587": "zh"}
        self.cfg["language"] = m.get(val, "en")
        set_language(self.cfg["language"])

    def _on_model_change(self, val):
        for mid, info in MODEL_INFO.items():
            if t(info["name_key"]) == val:
                self.cfg["model"] = mid
                self.session = None
                self.session_model = None
                self._update_model_desc()
                break

    def _update_model_desc(self):
        m = self.cfg.get("model", "auto")
        if m in MODEL_INFO:
            self._model_desc_lbl.configure(text=t(MODEL_INFO[m]["desc_key"]))

    def _browse_output(self):
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
        save_cfg(self.cfg)
        self._show_toast(t("settings_saved"), "success")

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


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = HoneyClean()
    app.mainloop()
