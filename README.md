<p align="center">
  <img src="https://img.shields.io/badge/HoneyClean-v2.0-f5a623?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJsOS41IDE2LjVIMi41eiIgZmlsbD0iI2Y1YTYyMyIvPjwvc3ZnPg==" alt="HoneyClean v2.0"/>
  <br/>
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"/>
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows" alt="Windows"/>
  <img src="https://img.shields.io/badge/GPU-CUDA%20%7C%20DirectML-76B900?style=flat-square&logo=nvidia" alt="GPU Accelerated"/>
</p>

<h1 align="center">HoneyClean v2</h1>
<h3 align="center">AI Background Remover &mdash; by HoneyDev</h3>

<p align="center">
  <strong>Remove backgrounds from images instantly with AI. Free, GPU-accelerated, batch processing. Beautiful glassmorphism dark UI.</strong>
</p>

---

## Features

- **AI Background Removal** &mdash; Powered by [rembg](https://github.com/danielgatis/rembg) with multiple AI models (ISNet, U2Net, Silueta)
- **GPU Accelerated** &mdash; CUDA & DirectML support with automatic CPU fallback
- **Batch Processing** &mdash; Process hundreds of images at once with queue management
- **Manual Retouch Tools** &mdash; Erase & restore brush for fine-tuning results
- **Transparent PNG Output** &mdash; Clean transparent backgrounds, ready for use
- **GPU Monitoring** &mdash; Real-time GPU/VRAM usage display with configurable GPU limit (0-100%)
- **Drag & Drop** &mdash; Drop files or folders directly into the app
- **Before/After Preview** &mdash; Side-by-side comparison with checkerboard transparency view
- **Glassmorphism Dark UI** &mdash; Premium frameless window with neon glow effects, animated controls
- **Portable EXE** &mdash; Build as standalone Windows executable with PyInstaller

## Screenshots

> *Add screenshots of HoneyClean in action here*

| Before | After |
|--------|-------|
| Original image with background | Clean transparent PNG |

## Installation

### Option 1: Run from Source

```bash
# Clone the repository
git clone https://github.com/HoneyDevTM/HoneyClean.git
cd HoneyClean

# Install dependencies
pip install rembg[gpu] pillow onnxruntime-directml

# Optional: Drag & drop support
pip install tkinterdnd2

# Run
python HoneyClean.py
```

### Option 2: Build Standalone EXE

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
| `isnet-anime` | Anime, illustrations, clean edges |
| `u2net` | General purpose |
| `u2net_human_seg` | Human portraits |
| `silueta` | Fast, lightweight |
| `isnet-general-use` | General objects |

## Usage

1. **Add images** &mdash; Click the drop zone, use the folder button, or drag & drop files
2. **Configure** &mdash; Open Settings to choose AI model, output folder, GPU options
3. **Process** &mdash; Click START to begin batch processing
4. **Retouch** &mdash; Use the erase/restore brush tools for manual touch-ups
5. **Output** &mdash; Click "Output offnen" to open the results folder

## Keyboard & Controls

- **Drag title bar** to move the window
- **Double-click title bar** to maximize/restore
- **Resize** from window edges and corner
- **GPU Limit** slider to throttle GPU usage

## Configuration

Settings are saved to `%APPDATA%/HoneyClean/config.json`:

```json
{
  "output_dir": "~/Downloads/HoneyClean_Output",
  "gpu_limit": 100,
  "model": "isnet-anime",
  "alpha_fg": 240,
  "alpha_bg": 10,
  "alpha_erode": 10,
  "use_gpu": true
}
```

## Tech Stack

- **Python** + **tkinter** &mdash; Native desktop GUI
- **rembg** &mdash; AI background removal (ISNet/U2Net)
- **ONNX Runtime** &mdash; GPU-accelerated AI inference
- **Pillow** &mdash; Image processing & display
- **PyInstaller** &mdash; Standalone EXE packaging

## License

[MIT License](LICENSE) &mdash; free for personal and commercial use.

## Credits

Built by **[HoneyDev](https://github.com/HoneyDevTM)** with AI-powered background removal by [rembg](https://github.com/danielgatis/rembg).

---

<p align="center">
  <sub>Keywords: background remover, AI background removal, remove background from image, free background remover, rembg GUI, image background eraser, batch background removal, GPU accelerated background removal, transparent background maker, PNG background remover, Windows background remover app, remove bg, photo background eraser, AI image editor</sub>
</p>
