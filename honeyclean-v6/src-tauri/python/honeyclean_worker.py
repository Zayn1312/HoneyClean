"""
HoneyClean v6.0 — Python Worker Process

JSON-lines protocol over stdin/stdout.
Wraps all rembg, video processing, model management, and config logic.

Actions:
  init_session, process_image, process_video, get_models, download_model,
  check_updates, get_config, save_config, validate_file, extract_zip
"""

import gc
import io
import json
import os
import re
import sys
import time

# Emit Python version as first stdout line (Tauri reads this)
print(json.dumps({"status": "startup", "python": sys.version, "executable": sys.executable}), flush=True)
import shutil
import base64
import logging
import zipfile
import tempfile
import threading
import subprocess
import importlib.util
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging (stderr only — stdout reserved for JSON protocol)
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stderr, level=logging.INFO,
    format="[HoneyClean Worker] %(levelname)s: %(message)s",
)
logger = logging.getLogger("honeyclean_worker")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VERSION = "6.0"
IS_WINDOWS = sys.platform == "win32"

# Force CUDA to use GPU 0
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["ORT_TENSORRT_ENGINE_CACHE_ENABLE"] = "1"

SUBPROCESS_FLAGS = {}
if IS_WINDOWS:
    SUBPROCESS_FLAGS["creationflags"] = subprocess.CREATE_NO_WINDOW

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
    "platform_preset": "None", "skip_processed": False,
    "vram_auto_detected": False,
    "video_format": "webm", "temporal_smoothing": 40, "edge_refinement": 2,
    "video_fps": "original", "hw_encoding": "auto", "max_vram_pct": 75,
    "preserve_audio": True, "temp_dir": "",
    "auto_download_models": True,
    "check_model_updates": True,
    "last_update_check": "",
}

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".m4v"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

# ── Model metadata ──────────────────────────────────────────────
MODEL_PRIORITY = [
    "birefnet-general", "birefnet-massive", "birefnet-portrait",
    "birefnet-general-lite", "isnet-general-use", "u2net",
    "isnet-anime", "u2net_human_seg", "silueta",
]

MODEL_ORDER = [
    "auto", "birefnet-general", "birefnet-massive", "birefnet-portrait",
    "birefnet-general-lite", "birefnet-dis", "birefnet-hrsod", "birefnet-cod",
    "isnet-general-use", "u2net", "u2netp",
    "isnet-anime", "u2net_human_seg", "u2net_cloth_seg",
    "silueta", "bria-rmbg",
]

MODEL_FILENAMES = {
    "u2net": "u2net.onnx",
    "u2netp": "u2netp.onnx",
    "u2net_human_seg": "u2net_human_seg.onnx",
    "u2net_cloth_seg": "u2net_cloth_seg.onnx",
    "silueta": "silueta.onnx",
    "isnet-general-use": "isnet-general-use.onnx",
    "isnet-anime": "isnet-anime.onnx",
    "birefnet-general": "BiRefNet-general-epoch_244.onnx",
    "birefnet-general-lite": "BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx",
    "birefnet-portrait": "BiRefNet-portrait-epoch_150.onnx",
    "birefnet-massive": "BiRefNet-massive-TR_DIS5K_TR_TEs-epoch_420.onnx",
    "birefnet-dis": "BiRefNet-DIS-epoch_590.onnx",
    "birefnet-hrsod": "BiRefNet-HRSOD_DHU-epoch_115.onnx",
    "birefnet-cod": "BiRefNet-COD-epoch_125.onnx",
    "bria-rmbg": "bria-rmbg.onnx",
}

MODEL_SIZES = {
    "u2net": 176_000_000, "u2netp": 4_700_000,
    "u2net_human_seg": 176_000_000, "u2net_cloth_seg": 176_000_000,
    "silueta": 43_000_000, "isnet-general-use": 174_000_000,
    "isnet-anime": 174_000_000, "birefnet-general": 973_000_000,
    "birefnet-general-lite": 410_000_000, "birefnet-portrait": 973_000_000,
    "birefnet-massive": 973_000_000, "birefnet-dis": 973_000_000,
    "birefnet-hrsod": 973_000_000, "birefnet-cod": 973_000_000,
    "bria-rmbg": 176_000_000,
}

QUALITY_PRESETS = {
    "fast": {"model": "silueta", "alpha_matting": False},
    "balanced": {"model": "isnet-general-use", "alpha_matting": True},
    "quality": {"model": "birefnet-general", "alpha_matting": True},
    "anime": {"model": "isnet-anime", "alpha_matting": False},
    "portrait": {"model": "birefnet-portrait", "alpha_matting": True},
}

PLATFORM_PRESETS = {
    "Amazon": {"bg": [255, 255, 255], "size": [2000, 2000], "padding_pct": 0.05, "format": "jpeg"},
    "Shopify": {"bg": [255, 255, 255], "size": [2048, 2048], "padding_pct": 0.08, "format": "png"},
    "Etsy": {"bg": None, "size": [2700, 2025], "padding_pct": 0.05, "format": "png"},
    "eBay": {"bg": [255, 255, 255], "size": [1600, 1600], "padding_pct": 0.05, "format": "jpeg"},
    "Instagram": {"bg": None, "size": [1080, 1080], "padding_pct": 0.10, "format": "png"},
}

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
    "HC-GPU-001": "No GPU provider available",
}

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_session = None
_session_model = None
_active_provider = "CPUExecutionProvider"
_cfg = None
_model_cache_dir = None


def _get_cache_dir():
    global _model_cache_dir
    if _model_cache_dir is None:
        _model_cache_dir = Path(
            os.environ.get("U2NET_HOME", Path.home() / ".u2net")
        )
        _model_cache_dir.mkdir(parents=True, exist_ok=True)
    return _model_cache_dir


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def load_cfg():
    global _cfg
    try:
        CFG_PATH.parent.mkdir(exist_ok=True)
        if CFG_PATH.exists():
            _cfg = {**DEFAULT_CFG, **json.loads(CFG_PATH.read_text(encoding="utf-8"))}
        else:
            _cfg = DEFAULT_CFG.copy()
    except Exception:
        _cfg = DEFAULT_CFG.copy()
    return _cfg


def save_cfg(c):
    global _cfg
    _cfg = c
    try:
        CFG_PATH.parent.mkdir(exist_ok=True)
        CFG_PATH.write_text(json.dumps(c, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        logger.error("Config save failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_path(path):
    p = str(path)
    if ".." in p:
        return False, "HC-012"
    path = Path(path)
    if not path.exists() or not path.is_file():
        return False, "HC-010"
    return True, None


def validate_image(path):
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


def is_video_file(path):
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def sanitize_filename(name, max_len=200):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).lstrip('.')
    if not name:
        name = "unnamed"
    if len(name) > max_len:
        stem, ext = os.path.splitext(name)
        name = stem[:max_len - len(ext)] + ext
    return name


# ---------------------------------------------------------------------------
# ZIP Handling
# ---------------------------------------------------------------------------
def extract_zip(zip_path, output_dir):
    zip_path = Path(zip_path)
    tmp_dir = Path(output_dir) / ".honeyclean_tmp" / zip_path.stem
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            total_size = sum(i.file_size for i in zf.infolist())
            if total_size > 500 * 1024 * 1024:
                return [], "HC-013"
            compressed = sum(i.compress_size for i in zf.infolist() if i.compress_size > 0)
            if compressed > 0 and total_size / compressed > 100:
                return [], "HC-014"
            extracted = []
            for info in zf.infolist():
                if info.is_dir():
                    continue
                if ".." in info.filename or info.filename.startswith("/"):
                    return [], "HC-015"
                fname = sanitize_filename(Path(info.filename).name)
                if Path(fname).suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                target = tmp_dir / fname
                with zf.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                valid, _ = validate_image(target)
                if valid:
                    extracted.append(str(target))
                else:
                    target.unlink(missing_ok=True)
            return extracted, None
    except zipfile.BadZipFile:
        return [], "HC-016"
    except Exception as e:
        return [], "HC-016"


# ---------------------------------------------------------------------------
# Image Operations
# ---------------------------------------------------------------------------
def decontaminate_edges(img, strength=0.5):
    try:
        import numpy as np
        arr = np.array(img, dtype=np.float32)
        if arr.shape[2] < 4:
            return img
        rgb, alpha = arr[:, :, :3], arr[:, :, 3:4] / 255.0
        opaque = alpha[:, :, 0] > 0.9
        if opaque.sum() == 0:
            return img
        avg = rgb[opaque].mean(axis=0)
        semi = (alpha[:, :, 0] > 0.05) & (alpha[:, :, 0] < 0.9)
        blend = (1.0 - alpha[semi]) * strength
        rgb[semi] = rgb[semi] * (1 - blend[:, np.newaxis]) + avg * blend[:, np.newaxis]
        out = np.concatenate([np.clip(rgb, 0, 255), arr[:, :, 3:4]], axis=2).astype(np.uint8)
        from PIL import Image
        result = Image.fromarray(out)
        del arr, rgb, alpha, out
        return result
    except Exception:
        return img


def apply_edge_feather(img, radius):
    if radius <= 0:
        return img
    from PIL import ImageFilter
    alpha = img.split()[3]
    result = img.copy()
    result.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius)))
    return result


def apply_platform_preset(result_img, preset):
    from PIL import Image
    bbox = result_img.split()[3].getbbox()
    if not bbox:
        return result_img
    subject = result_img.crop(bbox)
    tw, th = preset["size"]
    pad = preset["padding_pct"]
    mw, mh = int(tw * (1 - 2 * pad)), int(th * (1 - 2 * pad))
    subject.thumbnail((mw, mh), Image.LANCZOS)
    if preset["bg"]:
        canvas = Image.new("RGB", (tw, th), tuple(preset["bg"]))
        canvas.paste(subject, ((tw - subject.width) // 2, (th - subject.height) // 2), subject.split()[3])
    else:
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        canvas.paste(subject, ((tw - subject.width) // 2, (th - subject.height) // 2))
    return canvas


def generate_shadow(fg_img, shadow_type="drop", opacity=0.6, blur_radius=20, offset=(8, 12)):
    from PIL import Image, ImageFilter
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


def replace_background(fg_img, bg_type, bg_value=None):
    from PIL import Image
    if bg_type == "transparent":
        return fg_img
    w, h = fg_img.size
    if bg_type == "white":
        bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    elif bg_type == "color" and bg_value:
        bg = Image.new("RGBA", (w, h), (*bg_value, 255))
    else:
        return fg_img
    canvas = Image.new("RGBA", (w, h))
    canvas.paste(bg, (0, 0))
    canvas.paste(fg_img, (0, 0), fg_img.split()[3])
    return canvas


# ---------------------------------------------------------------------------
# Session Management — GPU PRIORITY
# ---------------------------------------------------------------------------
def create_session(model_name):
    """Create or reuse a rembg session. Priority: CUDA > DML > CPU."""
    global _session, _session_model, _active_provider

    if _session is not None and _session_model == model_name:
        return _session

    import onnxruntime as ort
    from rembg import new_session

    available = ort.get_available_providers()
    logger.info("Available providers: %s", available)

    # Priority order — CUDA wins if available
    priority = ["CUDAExecutionProvider", "DmlExecutionProvider", "CPUExecutionProvider"]

    for provider in priority:
        if provider not in available:
            continue
        try:
            sess_options = ort.SessionOptions()
            sess_options.enable_mem_pattern = False
            sess_options.enable_cpu_mem_arena = False
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

            # Build provider list — always include CPU as fallback for unsupported ops
            providers = [provider]
            if provider != "CPUExecutionProvider":
                providers.append("CPUExecutionProvider")

            session = new_session(
                model_name,
                providers=providers,
                sess_options=sess_options,
            )

            # Verify which provider is actually active
            actual = []
            inner = getattr(session, 'inner_session', None) or getattr(session, 'session', None)
            if inner:
                actual = list(inner.get_providers())

            _active_provider = actual[0] if actual else provider
            _session = session
            _session_model = model_name

            logger.info("SUCCESS — Provider: %s (requested: %s)", _active_provider, provider)
            return session

        except Exception as e:
            logger.warning("Provider %s failed: %s", provider, e)
            continue

    raise RuntimeError("HC-GPU-001: No provider available")


def _get_active_providers():
    try:
        inner = getattr(_session, 'inner_session', None) or getattr(_session, 'session', None)
        if inner:
            return list(inner.get_providers())
    except Exception:
        pass
    return [_active_provider]


def _provider_label():
    """Return a human-readable label for the current provider."""
    if "CUDA" in _active_provider:
        return "CUDA"
    if "Dml" in _active_provider or "DirectML" in _active_provider:
        return "DirectML"
    return "CPU"


def _is_gpu_provider():
    return _active_provider in ("CUDAExecutionProvider", "DmlExecutionProvider")


# ---------------------------------------------------------------------------
# Image Processing — GPU ONLY, ONE IMAGE AT A TIME
# ---------------------------------------------------------------------------
def process_single_image(file_path, cfg):
    """Process single image. Load → GPU → Save → FREE MEMORY."""
    from PIL import Image
    from rembg import remove

    img = None
    result = None

    try:
        # Create/reuse session
        model_name = cfg.get("model", "auto")
        if model_name == "auto":
            # Pick best available model
            for m in MODEL_PRIORITY:
                if is_model_cached(m):
                    model_name = m
                    break
            else:
                model_name = "birefnet-general"

        create_session(model_name)

        # Load image — smallest possible footprint
        img = Image.open(file_path)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        # Process on GPU
        try:
            result = remove(
                img, session=_session,
                alpha_matting=False,
                post_process_mask=True,
            )
        except (TypeError, ValueError):
            result = remove(img, session=_session)

        # IMMEDIATELY free source image
        img.close()
        del img
        img = None

        if result.mode != "RGBA":
            old = result
            result = result.convert("RGBA")
            old.close()
            del old

        # Apply post-processing in-place (no extra copies)
        if cfg.get("color_decontaminate", True):
            old = result
            result = decontaminate_edges(result, cfg.get("decontaminate_strength", 0.5))
            if old is not result:
                old.close()
                del old

        feather = cfg.get("edge_feather", 0)
        if feather > 0:
            old = result
            result = apply_edge_feather(result, feather)
            if old is not result:
                old.close()
                del old

        return result, None

    except Exception as e:
        logger.error("process_single_image failed: %s", e)
        return None, "HC-021"

    finally:
        # MANDATORY — free every byte immediately
        if img is not None:
            try:
                img.close()
            except Exception:
                pass
            del img
        gc.collect()


def save_result(result_img, original_path, cfg):
    out_dir = Path(cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = cfg.get("output_format", "png").lower()
    preset_name = cfg.get("platform_preset", "None")
    preset = PLATFORM_PRESETS.get(preset_name) if preset_name != "None" else None
    stem = sanitize_filename(Path(original_path).stem)

    try:
        img = apply_platform_preset(result_img, preset) if preset else result_img
        if preset:
            fmt = preset["format"]

        if fmt == "jpeg":
            from PIL import Image
            op = out_dir / f"{stem}_clean.jpg"
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)
            bg.save(str(op), "JPEG", quality=95)
            bg.close()
            del bg
            return str(op)
        elif fmt == "webp":
            op = out_dir / f"{stem}_clean.webp"
            img.save(str(op), "WEBP", quality=95)
            return str(op)
        else:
            op = out_dir / f"{stem}_clean.png"
            img.save(str(op), "PNG")
            return str(op)
    except Exception as e:
        logger.error("save_result failed: %s", e)
        return None


def output_exists(file_path, cfg):
    out_dir = Path(cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
    stem = sanitize_filename(Path(file_path).stem)
    if is_video_file(file_path):
        vid_fmt = cfg.get("video_format", "webm")
        ext_map = {"webm": "webm", "mov": "mov", "mp4_greenscreen": "mp4", "png_sequence": ""}
        ext = ext_map.get(vid_fmt, "webm")
        if vid_fmt == "png_sequence":
            return (out_dir / f"{stem}_clean").is_dir()
        return (out_dir / f"{stem}_clean.{ext}").exists()
    fmt = cfg.get("output_format", "png").lower()
    ext_map = {"jpeg": "jpg", "webp": "webp", "png": "png"}
    ext = ext_map.get(fmt, "png")
    return (out_dir / f"{stem}_clean.{ext}").exists()


# ---------------------------------------------------------------------------
# Model Management
# ---------------------------------------------------------------------------
def get_cached_models():
    cache_dir = _get_cache_dir()
    cached = []
    for model, fname in MODEL_FILENAMES.items():
        if (cache_dir / fname).exists():
            cached.append(model)
    return cached


def is_model_cached(model_name):
    fname = MODEL_FILENAMES.get(model_name)
    if not fname:
        return False
    return (_get_cache_dir() / fname).exists()


def download_model(model_name, request_id):
    if model_name not in MODEL_FILENAMES:
        return False
    if is_model_cached(model_name):
        return True

    expected_size = MODEL_SIZES.get(model_name, 0)
    fname = MODEL_FILENAMES[model_name]
    target = _get_cache_dir() / fname
    stop_monitor = threading.Event()

    def _monitor_progress():
        while not stop_monitor.is_set():
            current = 0
            if target.exists() and expected_size > 0:
                current = target.stat().st_size
            else:
                for f in _get_cache_dir().iterdir():
                    if f.name.startswith("tmp") and expected_size > 0:
                        try:
                            current = f.stat().st_size
                        except OSError:
                            pass
                        break
            if expected_size > 0 and current > 0:
                pct = min(99, int(current / expected_size * 100))
                emit_event(request_id, "download_progress", {
                    "model": model_name, "pct": pct
                })
            stop_monitor.wait(0.5)

    monitor = threading.Thread(target=_monitor_progress, daemon=True)
    monitor.start()

    try:
        from rembg import new_session
        new_session(model_name)
        stop_monitor.set()
        monitor.join(timeout=2)
        return True
    except Exception as e:
        stop_monitor.set()
        monitor.join(timeout=2)
        logger.error("download_model failed: %s", e)
        return False


def delete_model(model_name):
    fname = MODEL_FILENAMES.get(model_name)
    if not fname:
        return False
    p = _get_cache_dir() / fname
    if p.exists():
        try:
            p.unlink()
            return True
        except OSError:
            return False
    return False


def cleanup_temp_files():
    count = 0
    try:
        for f in _get_cache_dir().iterdir():
            if f.name.startswith("tmp") or f.suffix == ".tmp":
                try:
                    f.unlink()
                    count += 1
                except OSError:
                    pass
    except OSError:
        pass
    return count


def check_for_updates():
    result = {"update_available": False, "installed": "", "latest": "", "error": None}
    try:
        import importlib.metadata
        result["installed"] = importlib.metadata.version("rembg")
    except Exception:
        result["installed"] = "unknown"

    try:
        import urllib.request
        req = urllib.request.Request(
            "https://pypi.org/pypi/rembg/json",
            headers={"User-Agent": "HoneyClean/6.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            result["latest"] = data.get("info", {}).get("version", "")
    except Exception as e:
        result["error"] = str(e)
        return result

    if result["installed"] != "unknown" and result["latest"]:
        result["update_available"] = result["installed"] != result["latest"]
    return result


def format_size(size_bytes):
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.0f} MB"
    return f"{size_bytes / 1_000:.0f} KB"


# ---------------------------------------------------------------------------
# Video Processing (delegates to VideoProcessor pipeline)
# ---------------------------------------------------------------------------
def process_video_file(video_path, cfg, request_id, cancel_flag):
    try:
        import cv2
    except ImportError:
        return False, "OpenCV not installed"

    out_dir = Path(cfg.get("output_dir", str(Path.home() / "Downloads" / "HoneyClean_Output")))
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = sanitize_filename(Path(video_path).stem)
    vid_fmt = cfg.get("video_format", "webm")
    ext_map = {"webm": "webm", "mov": "mov", "mp4_greenscreen": "mp4"}
    if vid_fmt == "png_sequence":
        output_path = str(out_dir / f"{stem}_clean")
    else:
        ext = ext_map.get(vid_fmt, "webm")
        output_path = str(out_dir / f"{stem}_clean.{ext}")

    settings = {
        "variant": "mobilenetv3",
        "batch_size": "auto",
        "smoothing": cfg.get("temporal_smoothing", 40) / 100.0,
        "edge_refinement": cfg.get("edge_refinement", 2),
        "output_format": vid_fmt,
        "preserve_audio": cfg.get("preserve_audio", True),
        "max_vram_pct": cfg.get("max_vram_pct", 75),
    }

    vp = _create_video_processor()
    if vp is None:
        return False, "VideoProcessor not available"

    done_flag = threading.Event()
    error_flag = threading.Event()

    def progress_cb(stage, current, total, fps, eta):
        if cancel_flag.is_set():
            return
        emit_event(request_id, "video_progress", {
            "stage": stage, "current": current, "total": total,
            "fps": round(fps, 1), "eta": round(eta, 1),
        })
        if stage == "done":
            done_flag.set()
        elif stage == "error":
            error_flag.set()

    try:
        vp.process_video(str(video_path), output_path, settings, progress_cb, cancel_flag)
    except Exception as e:
        logger.error("Video processing error: %s", e)
        return False, str(e)

    return done_flag.is_set() and not error_flag.is_set(), None


def _create_video_processor():
    """Create a VideoProcessor instance. Try local import first, then bundled."""
    try:
        v5_dir = Path(__file__).resolve().parent.parent.parent.parent
        vp_path = v5_dir / "video_processor.py"
        if vp_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("video_processor", str(vp_path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.VideoProcessor()
    except Exception as e:
        logger.warning("Could not load VideoProcessor from v5: %s", e)

    try:
        from video_processor import VideoProcessor
        return VideoProcessor()
    except ImportError:
        pass

    return None


# ---------------------------------------------------------------------------
# GPU Info
# ---------------------------------------------------------------------------
def get_gpu_info():
    info = {"gpu_name": "", "vram_total": 0, "vram_used": 0, "gpu_util": 0, "driver": ""}
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version",
             "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
            **SUBPROCESS_FLAGS,
        )
        if proc.returncode == 0:
            parts = proc.stdout.decode().strip().split(",")
            if len(parts) >= 5:
                info["gpu_name"] = parts[0].strip()
                info["vram_total"] = int(float(parts[1].strip()))
                info["vram_used"] = int(float(parts[2].strip()))
                info["gpu_util"] = int(float(parts[3].strip()))
                info["driver"] = parts[4].strip()
    except Exception:
        pass
    return info


# ---------------------------------------------------------------------------
# Crash Reporter
# ---------------------------------------------------------------------------
def capture_crash(error, context=None):
    """Capture crash, save locally. Returns crash_id."""
    import traceback
    import platform
    from datetime import datetime

    crash_id = f"HC-CRASH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    report = {
        "crash_id": crash_id,
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context or {},
        "system": {
            "platform": platform.platform(),
            "python": sys.version,
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "gpu_info": _get_gpu_info_safe(),
        "memory_info": _get_memory_info_safe(),
        "worker_state": {
            "active_model": _session_model,
            "active_provider": _active_provider,
            "current_file": (context or {}).get("current_file", "unknown"),
        }
    }

    # Save locally
    crash_dir = Path(os.environ.get("APPDATA", ".")) / "HoneyClean" / "crashes"
    crash_dir.mkdir(parents=True, exist_ok=True)
    crash_path = crash_dir / f"{crash_id}.json"
    try:
        with open(crash_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # Send email (non-blocking, fire and forget)
    threading.Thread(
        target=_send_crash_email, args=(report, str(crash_path)), daemon=True
    ).start()

    logger.error("Crash captured: %s — %s", crash_id, str(error))
    return crash_id


def _send_crash_email(report, crash_path):
    """Send crash report email. Silent fail — never crash the crash reporter."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        subject = f"[HoneyClean v{VERSION}] Crash: {report['error_type']} — {report['crash_id']}"

        body = f"""
HoneyClean Crash Report
{'=' * 55}
ID:        {report['crash_id']}
Time:      {report['timestamp']}
Version:   {report['version']}

ERROR
{'-' * 55}
Type:      {report['error_type']}
Message:   {report['error_message']}

TRACEBACK
{'-' * 55}
{report['traceback']}

CONTEXT
{'-' * 55}
Model:     {report['worker_state']['active_model']}
Provider:  {report['worker_state']['active_provider']}
File:      {report['worker_state']['current_file']}

SYSTEM
{'-' * 55}
Platform:  {report['system']['platform']}
Python:    {report['system']['python']}
GPU:       {report.get('gpu_info', 'unknown')}
Memory:    {report.get('memory_info', 'unknown')}

Local file: {crash_path}
{'=' * 55}
        """.strip()

        # Read credentials from %APPDATA%/HoneyClean/smtp_config.json
        smtp_config_path = Path(
            os.environ.get("APPDATA", ".")
        ) / "HoneyClean" / "smtp_config.json"

        if smtp_config_path.exists():
            with open(smtp_config_path) as f:
                smtp_cfg = json.load(f)

            msg = MIMEMultipart()
            msg["From"] = smtp_cfg.get("user", "")
            msg["To"] = "zaynhonig@gmail.com"
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(smtp_cfg.get("host", "smtp.gmail.com"), smtp_cfg.get("port", 587)) as server:
                server.starttls()
                server.login(smtp_cfg["user"], smtp_cfg["password"])
                server.sendmail(smtp_cfg["user"], "zaynhonig@gmail.com", msg.as_string())

    except Exception:
        pass  # Never crash the crash reporter


def _get_gpu_info_safe():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3,
            **SUBPROCESS_FLAGS,
        )
        return result.stdout.strip()
    except Exception:
        return "unavailable"


def _get_memory_info_safe():
    try:
        import psutil
        m = psutil.virtual_memory()
        return f"{m.used // 1024**2} MB used / {m.total // 1024**2} MB total ({m.percent}%)"
    except Exception:
        return "unavailable"


# ---------------------------------------------------------------------------
# Protocol: JSON-lines over stdin/stdout
# ---------------------------------------------------------------------------
def send_response(request_id, status, data=None, error=None):
    msg = {"id": request_id, "status": status}
    if data is not None:
        msg["data"] = data
    if error is not None:
        msg["error"] = error
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def emit_event(request_id, event_type, data):
    msg = {"id": request_id, "event": event_type, "data": data}
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Action Handlers
# ---------------------------------------------------------------------------
_cancel_flags = {}


def handle_action(msg):
    action = msg.get("action")
    request_id = msg.get("id", "unknown")
    params = msg.get("params", {})

    try:
        if action == "get_config":
            cfg = load_cfg()
            send_response(request_id, "ok", {
                "config": cfg,
                "version": VERSION,
                "defaults": DEFAULT_CFG,
            })

        elif action == "save_config":
            new_cfg = params.get("config", {})
            current = load_cfg()
            current.update(new_cfg)
            ok = save_cfg(current)
            send_response(request_id, "ok" if ok else "error",
                          error=None if ok else "HC-031")

        elif action == "init_session":
            model = params.get("model", "auto")
            try:
                # Resolve auto model
                actual_model = model
                if actual_model == "auto":
                    for m in MODEL_PRIORITY:
                        if is_model_cached(m):
                            actual_model = m
                            break
                    else:
                        actual_model = "birefnet-general"

                create_session(actual_model)
                providers = _get_active_providers()
                send_response(request_id, "ok", {
                    "model": actual_model,
                    "providers": providers,
                    "primary": _active_provider,
                    "is_gpu": _is_gpu_provider(),
                    "label": _provider_label(),
                })
            except Exception as e:
                send_response(request_id, "error", error=str(e))

        elif action == "process_image":
            file_path = params.get("path")
            cfg = load_cfg()
            cfg.update(params.get("config_overrides", {}))
            skip = params.get("skip_existing", False)

            if skip and output_exists(file_path, cfg):
                send_response(request_id, "ok", {"skipped": True, "path": file_path})
                return

            t0 = time.time()
            result = None
            try:
                result, error_code = process_single_image(file_path, cfg)
                elapsed = round(time.time() - t0, 2)

                if result:
                    output_path = save_result(result, file_path, cfg)
                    # FREE result immediately after saving
                    result.close()
                    del result
                    result = None
                    gc.collect()

                    send_response(request_id, "ok", {
                        "path": file_path,
                        "output": output_path,
                        "elapsed": elapsed,
                        "skipped": False,
                        "provider": _provider_label(),
                        "is_gpu": _is_gpu_provider(),
                    })
                else:
                    gc.collect()
                    send_response(request_id, "error", error=error_code)
            except Exception as e:
                if result is not None:
                    try:
                        result.close()
                    except Exception:
                        pass
                    del result
                gc.collect()
                crash_id = capture_crash(e, context={"current_file": file_path})
                send_response(request_id, "error",
                              error=f"{crash_id}: {e}")

        elif action == "process_video":
            file_path = params.get("path")
            cfg = load_cfg()
            cfg.update(params.get("config_overrides", {}))

            cancel_flag = threading.Event()
            _cancel_flags[request_id] = cancel_flag

            def _run_video():
                try:
                    ok, err = process_video_file(file_path, cfg, request_id, cancel_flag)
                    _cancel_flags.pop(request_id, None)
                    if ok:
                        send_response(request_id, "ok", {"path": file_path})
                    else:
                        send_response(request_id, "error", error=err or "Video processing failed")
                except Exception as e:
                    crash_id = capture_crash(e, context={"current_file": file_path})
                    send_response(request_id, "error", error=f"{crash_id}: {e}")

            threading.Thread(target=_run_video, daemon=True).start()

        elif action == "cancel":
            target_id = params.get("target_id", request_id)
            flag = _cancel_flags.get(target_id)
            if flag:
                flag.set()
            send_response(request_id, "ok")

        elif action == "get_models":
            cached = get_cached_models()
            models = []
            for m in MODEL_ORDER:
                if m == "auto":
                    continue
                models.append({
                    "id": m,
                    "filename": MODEL_FILENAMES.get(m, ""),
                    "size": MODEL_SIZES.get(m, 0),
                    "size_formatted": format_size(MODEL_SIZES.get(m, 0)),
                    "cached": m in cached,
                })
            send_response(request_id, "ok", {
                "models": models,
                "cached": cached,
                "model_order": MODEL_ORDER,
                "priority": MODEL_PRIORITY,
            })

        elif action == "download_model":
            model = params.get("model")

            def _do_download():
                ok = download_model(model, request_id)
                if ok:
                    send_response(request_id, "ok", {"model": model})
                else:
                    send_response(request_id, "error",
                                  error=f"Download failed: {model}")

            threading.Thread(target=_do_download, daemon=True).start()

        elif action == "delete_model":
            model = params.get("model")
            ok = delete_model(model)
            send_response(request_id, "ok" if ok else "error",
                          data={"model": model} if ok else None,
                          error=None if ok else f"Delete failed: {model}")

        elif action == "cleanup_temp":
            count = cleanup_temp_files()
            send_response(request_id, "ok", {"cleaned": count})

        elif action == "check_updates":
            result = check_for_updates()
            send_response(request_id, "ok", result)

        elif action == "validate_file":
            file_path = params.get("path")
            ok, code = validate_path(file_path)
            if not ok:
                send_response(request_id, "error", error=code)
                return
            if is_video_file(file_path):
                send_response(request_id, "ok", {"type": "video", "path": file_path})
            else:
                valid, fmt = validate_image(file_path)
                if valid:
                    send_response(request_id, "ok", {
                        "type": "image", "format": fmt, "path": file_path
                    })
                else:
                    send_response(request_id, "error", error="HC-011")

        elif action == "extract_zip":
            zip_path = params.get("path")
            output_dir = params.get("output_dir", str(Path.home() / "Downloads"))
            files, error = extract_zip(zip_path, output_dir)
            if error:
                send_response(request_id, "error", error=error)
            else:
                send_response(request_id, "ok", {"files": files, "count": len(files)})

        elif action == "get_gpu_info":
            info = get_gpu_info()
            send_response(request_id, "ok", info)

        elif action == "ping":
            send_response(request_id, "ok", {"version": VERSION, "pid": os.getpid()})

        elif action == "shutdown":
            send_response(request_id, "ok")
            sys.exit(0)

        else:
            send_response(request_id, "error", error=f"Unknown action: {action}")

    except Exception as e:
        logger.exception("Action %s failed", action)
        crash_id = capture_crash(e, context={"action": action})
        send_response(request_id, "error", error=f"{crash_id}: {e}")


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------
def main():
    logger.info("HoneyClean Worker v%s started (PID %d)", VERSION, os.getpid())
    load_cfg()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            send_response("parse_error", "error", error=f"Invalid JSON: {e}")
            continue

        try:
            handle_action(msg)
        except Exception as e:
            crash_id = capture_crash(e, context={"raw_line": line[:200]})
            send_response(
                msg.get("id", "unknown"), "error",
                error=f"{crash_id}: {e}"
            )


if __name__ == "__main__":
    main()
