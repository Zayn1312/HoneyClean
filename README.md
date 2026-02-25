<p align="center">
  <img src="https://img.shields.io/badge/HoneyClean-v3.0-007AFF?style=for-the-badge" alt="HoneyClean v3.0"/>
  <br/>
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"/>
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows" alt="Windows"/>
  <img src="https://img.shields.io/badge/GPU-CUDA%20%7C%20DirectML-76B900?style=flat-square&logo=nvidia" alt="GPU Accelerated"/>
</p>

<h1 align="center">HoneyClean</h1>
<h3 align="center">AI Background Remover &mdash; by Zayn1312</h3>

<p align="center">
  <strong>Remove backgrounds from images instantly with AI. Free, GPU-accelerated, batch processing with a modern Apple-style dark UI.</strong>
</p>

---

## Features

- **AI Background Removal** &mdash; Powered by [rembg](https://github.com/danielgatis/rembg) with multiple AI models (ISNet, U2Net, Silueta) and auto model selection
- **GPU Accelerated** &mdash; CUDA & DirectML support with automatic CPU fallback
- **Batch Processing** &mdash; Process hundreds of images at once with visual queue and thumbnail grid
- **ZIP File Support** &mdash; Drop ZIP archives containing images for batch processing with built-in security (zipbomb detection, path traversal protection)
- **Manual Retouch Tools** &mdash; Erase & restore brush for fine-tuning results with adjustable size and tolerance
- **Transparent PNG Output** &mdash; Clean transparent backgrounds, ready for use
- **GPU Monitoring** &mdash; Real-time GPU/VRAM usage display with configurable GPU limit (0-100%)
- **Drag & Drop** &mdash; Drop files, folders, or ZIP archives directly into the app
- **Before/After Preview** &mdash; Side-by-side comparison with checkerboard transparency view
- **Multi-Language** &mdash; Full UI translation in English, German, French, Spanish, and Chinese
- **Modern UI** &mdash; Apple-style dark mode with sidebar navigation, clean typography, and smooth interactions
- **First-Run EULA** &mdash; Ethical usage agreement on first launch
- **Error Code System** &mdash; Structured error codes (HC-001 through HC-041) with [wiki documentation](https://github.com/Zayn1312/HoneyClean/wiki/Error-Codes)
- **Security Hardened** &mdash; Path traversal protection, image magic byte validation, filename sanitization
- **Dependency Checker** &mdash; Auto-detects missing packages with one-click install
- **Fullscreen Mode** &mdash; Press F11 to toggle fullscreen
- **Portable EXE** &mdash; Build as standalone Windows executable with PyInstaller

## Installation

### Option 1: Run from Source

```bash
# Clone the repository
git clone https://github.com/Zayn1312/HoneyClean.git
cd HoneyClean

# Install dependencies
pip install rembg[gpu] pillow onnxruntime-directml pymatting

# Optional: Drag & drop support
pip install tkinterdnd2

# Run
python HoneyClean.py
```

### Option 2: Download EXE

Download the latest release from [Releases](https://github.com/Zayn1312/HoneyClean/releases).

> **Windows SmartScreen:** On first run, Windows may show a SmartScreen warning. Click "More info" then "Run anyway". This happens because the EXE is not code-signed. The app is open source and safe to use.

### Option 3: Build EXE from Source

```bash
# Run the build script
build_HoneyClean_exe.bat
```

The executable will be created in `dist/HoneyClean/HoneyClean.exe`.

## Requirements

- **Python** 3.10+
- **rembg** &mdash; AI background removal engine
- **Pillow** &mdash; Image processing
- **onnxruntime** or **onnxruntime-directml** &mdash; AI inference (GPU optional)
- **pymatting** &mdash; Alpha matting for clean edges
- **tkinterdnd2** &mdash; Drag & drop support (optional)

### GPU Support

| Provider | Package | GPU |
|----------|---------|-----|
| DirectML | `onnxruntime-directml` | AMD / Intel / NVIDIA |
| CUDA | `onnxruntime-gpu` | NVIDIA only |
| CPU | `onnxruntime` | No GPU needed |

## AI Models

| Model | Best For |
|-------|----------|
| `auto` | **Recommended** &mdash; automatically selects the best available model |
| `isnet-general-use` | General objects |
| `u2net` | General purpose |
| `isnet-anime` | Anime, illustrations, clean edges |
| `u2net_human_seg` | Human portraits |
| `silueta` | Fast, lightweight |

## Error Codes

HoneyClean uses structured error codes for troubleshooting. See the [Error Codes Wiki](https://github.com/Zayn1312/HoneyClean/wiki/Error-Codes) for detailed solutions.

| Code | Description |
|------|-------------|
| HC-001 | rembg not installed |
| HC-002 | Pillow not installed |
| HC-003 | pymatting not installed |
| HC-004 | onnxruntime not installed |
| HC-005 | numpy not installed |
| HC-010–017 | File and ZIP errors |
| HC-020–024 | Processing and model errors |
| HC-030–032 | Configuration errors |
| HC-040–041 | UI errors |

## Usage

1. **First Run** &mdash; Accept the Terms of Use and select your language
2. **Add Images** &mdash; Click the drop zone, use "Add Folder", drag & drop files, or drop a ZIP archive
3. **Configure** &mdash; Go to Settings page to choose AI model, output folder, language, GPU options
4. **Process** &mdash; Click START to begin batch processing. Watch per-image progress in the thumbnail grid
5. **Retouch** &mdash; Switch to Editor page to use erase/restore brush tools for manual touch-ups
6. **Output** &mdash; Click "Open Output" to view the results folder

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F11 | Toggle fullscreen |
| Drag title bar | Move window |
| Double-click title bar | Maximize / restore |

## Configuration

Settings are saved to `%APPDATA%/HoneyClean/config.json`:

```json
{
  "output_dir": "~/Downloads/HoneyClean_Output",
  "gpu_limit": 100,
  "model": "auto",
  "alpha_fg": 240,
  "alpha_bg": 10,
  "alpha_erode": 10,
  "use_gpu": true,
  "language": "en",
  "theme": "dark",
  "eula_accepted": true
}
```

## Tech Stack

- **Python** + **tkinter** &mdash; Native desktop GUI
- **rembg** &mdash; AI background removal (ISNet/U2Net)
- **ONNX Runtime** &mdash; GPU-accelerated AI inference
- **Pillow** &mdash; Image processing & display
- **pymatting** &mdash; Alpha matting for clean edge detection
- **PyInstaller** &mdash; Standalone EXE packaging

## License

[MIT License](LICENSE) &mdash; free for personal and commercial use.

## Credits

Built by **[Zayn1312](https://github.com/Zayn1312)** with AI-powered background removal by [rembg](https://github.com/danielgatis/rembg).

---

<p align="center">
  <sub>Keywords: background remover, AI background removal, remove background, free background remover, rembg GUI, batch background removal, GPU accelerated, transparent PNG, image background eraser, remove bg, photo background eraser, AI image editor, background removal tool, Windows background remover</sub>
</p>
