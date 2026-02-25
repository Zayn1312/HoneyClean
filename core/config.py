"""
HoneyClean – Configuration, presets, and model definitions
"""

import json
import os
from pathlib import Path

VERSION = "5.0"

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
    "skip_processed": False,
    "vram_auto_detected": False,
    "show_hex_bg": True, "show_smoke": True, "show_drips": True,
    "effects_fps": 30, "show_intro": True,
    "video_format": "webm", "temporal_smoothing": 40, "edge_refinement": 2,
    "video_fps": "original", "hw_encoding": "auto", "max_vram_pct": 75,
    "preserve_audio": True, "temp_dir": "",
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

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".m4v"}

def is_video_file(path):
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS
