"""
HoneyClean – Utility functions (validation, zip, dependencies, file finders)
"""

import os
import re
import sys
import subprocess
import zipfile
import importlib.util
from pathlib import Path

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

# ── Logo / Trailer Helper ───────────────────────────────────────
def _find_logo():
    for p in [Path(__file__).parent.parent / "HCC.png",
              Path(__file__).parent.parent / "honeyclean-image" / "HCC.png"]:
        if p.exists():
            return p
    return None

def _find_trailer():
    for p in [Path(__file__).parent.parent / "honeyclean-image" / "Trailer_1.1.mp4",
              Path(__file__).parent.parent / "Trailer_1.1.mp4"]:
        if p.exists():
            return p
    return None
