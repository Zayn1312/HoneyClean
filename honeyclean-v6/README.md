<p align="center">
  <img src="public/logo.ico" alt="HoneyClean Logo" width="96" />
</p>

<h1 align="center">HoneyClean v6</h1>

<p align="center">
  <strong>AI Background Removal — Clean as Honey</strong>
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-6.0.0-gold" />
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows-blue" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green" />
  <img alt="Tauri" src="https://img.shields.io/badge/Tauri-v2-blueviolet" />
  <img alt="React" src="https://img.shields.io/badge/React-18-61dafb" />
</p>

---

HoneyClean is a desktop application for AI-powered background removal on images and videos. It runs entirely offline using local AI models, supports batch processing, and includes a built-in editor for manual refinement. Designed for e-commerce sellers, photographers, and content creators who need production-ready cutouts.

## Features

- **16 AI Models** — From lightweight Silueta (43 MB) to BiRefNet Massive (973 MB)
- **Batch Processing** — Drag-and-drop folders, ZIPs, or hundreds of files at once
- **Video Background Removal** — MP4, MOV, AVI, MKV, WebM with temporal smoothing
- **Built-in Editor** — Erase/restore brush, shadow effects, before/after slider, undo/redo
- **5 Quality Presets** — Fast, Balanced, Quality, Anime, Portrait
- **5 Platform Presets** — Amazon, Shopify, Etsy, eBay, Instagram (auto-resize + format)
- **GPU Accelerated** — NVIDIA CUDA, DirectML fallback, or CPU-only
- **GPU Setup Wizard** — Automatic detection and one-click driver/package installation
- **Alpha Matting** — Fine edge refinement for hair, fur, and transparent objects
- **Shadow Effects** — Drop, float, and contact shadows for product photos
- **Edge Feathering & Color Decontamination** — Clean edges without color bleed
- **5 Languages** — English, Deutsch, Français, Español, 中文
- **Dark Theme** — Easy on the eyes during long editing sessions
- **Diagnostics Page** — Real-time GPU stats, VRAM monitoring, system health checks
- **Structured Error Codes** — 25 error codes (HC-001 through HC-045) with clear messages
- **Offline** — All processing runs locally, no data leaves your machine

## Installation

### Requirements

- **Windows 10/11** (64-bit)
- **Python 3.10+** (3.12 recommended)
- **NVIDIA GPU** (optional — CPU and DirectML also supported)
- ~2 GB disk space for the app + models

### Install via Installer

1. Run `HoneyClean_6.0.0_x64-setup.exe`
2. Select language, install location, and check "Create Desktop Shortcut"
3. Launch HoneyClean from your desktop or Start Menu
4. On first run, accept the EULA and complete the GPU setup wizard

### Portable Use

Copy `HoneyClean.exe` anywhere and run it directly. Python and models must be available on PATH.

## Quick Start

1. **Launch** HoneyClean — the first-run wizard will guide you through EULA and GPU setup
2. **Pick a quality preset** — start with "Quality" for best results or "Fast" for speed
3. **Drag and drop** your images (PNG, JPG, WebP, BMP, TIFF) or videos onto the queue
4. **Select a platform preset** (optional) — e.g. "Amazon" auto-configures 2000×2000, white background, JPEG
5. **Click Process** — watch the queue progress in real time with GPU stats in the status bar
6. **Review results** in the built-in editor — use the before/after slider, add shadows, erase/restore edges
7. **Find your files** in `Downloads/HoneyClean_Output` (or your custom output folder)

## Quality Presets

| Preset | Model | Alpha Matting | Best For |
|--------|-------|:---:|----------|
| **Fast** | Silueta | — | Quick previews, bulk low-priority work |
| **Balanced** | ISNet General | ✓ | General purpose, good quality/speed tradeoff |
| **Quality** | BiRefNet General | ✓ | Hair, fur, complex edges — best overall |
| **Anime** | ISNet Anime | — | Anime, manga, illustrated characters |
| **Portrait** | BiRefNet Portrait | ✓ | People, headshots, portrait photography |

## Platform Presets

| Platform | Size | Background | Format | Padding |
|----------|------|------------|--------|:---:|
| **Amazon** | 2000 × 2000 | White | JPEG | 5% |
| **Shopify** | 2048 × 2048 | White | PNG | 8% |
| **Etsy** | 2700 × 2025 | Transparent | PNG | 5% |
| **eBay** | 1600 × 1600 | White | JPEG | 5% |
| **Instagram** | 1080 × 1080 | Transparent | PNG | 10% |

## AI Models

| Model | Description | Size |
|-------|-------------|-----:|
| **Auto** | Automatically selects the best model | — |
| **BiRefNet General** | Top accuracy for hair, fur, complex edges | 973 MB |
| **BiRefNet Massive** | Largest model, maximum detail | 973 MB |
| **BiRefNet Portrait** | Optimized for people and portraits | 973 MB |
| **BiRefNet Lite** | Good quality with faster processing | 410 MB |
| **BiRefNet DIS** | Dichotomous image segmentation | 973 MB |
| **BiRefNet HRSOD** | High-resolution salient object detection | 973 MB |
| **BiRefNet COD** | Camouflaged object detection | 973 MB |
| **ISNet General** | Well-tested all-rounder | 174 MB |
| **ISNet Anime** | Specialized for anime and manga art | 174 MB |
| **U2Net** | Classic model, fast and reliable | 176 MB |
| **U2Net-P** | Lightweight U2Net, very fast | 4.7 MB |
| **U2Net Human** | Optimized for human subjects | 176 MB |
| **U2Net Clothing** | Clothing segmentation | 176 MB |
| **Silueta** | Smallest and fastest | 43 MB |
| **BRIA RMBG 2.0** | Commercial-grade background removal | 176 MB |

Models are downloaded on first use and stored locally. Use the Models page to pre-download or manage them.

## Video Processing

**Supported input formats:** MP4, MOV, AVI, MKV, WebM, FLV, M4V

| Setting | Default | Description |
|---------|---------|-------------|
| Output Format | WebM | Video codec for output |
| Temporal Smoothing | 40 | Frame-to-frame consistency (0–100) |
| Edge Refinement | 2 | Edge detail enhancement (0–10) |
| FPS | Original | Output frame rate (original, 24, 30, 60) |
| HW Encoding | Auto | Hardware encoding (auto, H.264, H.265) |
| Max VRAM | 75% | GPU memory limit during video processing |
| Preserve Audio | Yes | Keep original audio track |

## Settings

All settings are stored in `%APPDATA%/HoneyClean/config.json`.

| Category | Setting | Default | Description |
|----------|---------|---------|-------------|
| **Output** | Output Directory | `Downloads/HoneyClean_Output` | Where processed files are saved |
| **Output** | Output Format | PNG | png, jpeg, or webp |
| **Output** | Platform Preset | None | Auto-configure for a marketplace |
| **Processing** | Quality Preset | Quality | Fast, Balanced, Quality, Anime, Portrait |
| **Processing** | Model | Auto | Which AI model to use |
| **Processing** | Use GPU | Yes | Enable GPU acceleration |
| **Processing** | GPU Limit | 100% | Max GPU utilization |
| **Matting** | Foreground Alpha | 270 | Alpha matting foreground threshold |
| **Matting** | Background Alpha | 20 | Alpha matting background threshold |
| **Matting** | Erosion | 15 | Alpha matting erosion amount |
| **Effects** | Shadow Type | None | none, drop, float, contact |
| **Effects** | Edge Feather | 0 | Feather edges (px) |
| **Effects** | Color Decontamination | Yes | Remove background color bleed |
| **System** | Language | English | en, de, fr, es, zh |
| **System** | Theme | Dark | UI theme |
| **System** | Auto-download Models | Yes | Download models on first use |

## GPU Setup

HoneyClean includes an automatic GPU diagnostics wizard that runs on first launch and is accessible anytime from the Diagnostics page.

**What it checks:**

1. **Python version** — Requires 3.10+
2. **NVIDIA GPU** — Detected via `nvidia-smi`
3. **NVIDIA Driver** — Version verification
4. **CUDA Toolkit** — Optional, enables TensorRT
5. **ONNX Runtime** — Prefers `onnxruntime-gpu` (CUDA), falls back to `onnxruntime-directml`
6. **rembg** — Core background removal library
7. **VRAM** — Current GPU memory utilization

**Automatic fixes:** The wizard can install missing packages with one click — no manual pip commands needed.

**Fallback chain:** NVIDIA CUDA → DirectML → CPU-only

## Error Codes

| Code | Message | Category |
|------|---------|----------|
| HC-001 | rembg not installed | Dependency |
| HC-002 | Pillow not installed | Dependency |
| HC-003 | pymatting not installed | Dependency |
| HC-004 | onnxruntime not installed | Dependency |
| HC-005 | numpy not installed | Dependency |
| HC-010 | File not found | File |
| HC-011 | Invalid file type | File |
| HC-012 | Path traversal detected | File |
| HC-013 | ZIP exceeds 500 MB | File |
| HC-014 | ZIP bomb detected | File |
| HC-015 | ZIP path traversal | File |
| HC-016 | ZIP extraction failed | File |
| HC-017 | Invalid image data | File |
| HC-020 | Model load failed | Model |
| HC-021 | Processing failed | Processing |
| HC-022 | GPU unavailable, using CPU | Model |
| HC-023 | Model not found | Model |
| HC-024 | Cannot create output directory | File |
| HC-030 | Config corrupted | Config |
| HC-031 | Config save failed | Config |
| HC-040 | UI init failed | UI |
| HC-041 | Drag-and-drop unavailable | UI |
| HC-042 | Shadow generation failed | Processing |
| HC-043 | Export preset failed | Processing |
| HC-044 | Edge feather failed | Processing |
| HC-045 | Color decontamination failed | Processing |

## FAQ

**Do I need an NVIDIA GPU?**
No. HoneyClean works on CPU and DirectML (AMD/Intel GPUs). An NVIDIA GPU with CUDA makes processing significantly faster, but it is not required.

**Which model should I use?**
Start with "Auto" — it picks the best model for each image. For manual selection: BiRefNet General gives the best quality, Silueta is the fastest, and ISNet Anime is best for illustrated content.

**Can I process videos?**
Yes. Drag and drop MP4, MOV, AVI, MKV, or WebM files. HoneyClean removes the background frame-by-frame with temporal smoothing for consistent results.

**Where do processed files go?**
By default, `Downloads/HoneyClean_Output`. Change this in Settings → Output Directory.

**How do I install GPU support?**
Launch HoneyClean and go to the Diagnostics page. The GPU wizard detects your hardware and offers one-click fixes for missing drivers and packages.

**What languages are supported?**
English, German (Deutsch), French (Français), Spanish (Español), and Chinese (中文). Change in Settings → Language.

**Where are models stored?**
In your user home directory under `.u2net/`. Models are downloaded on first use and shared across sessions.

**How many files can I process at once?**
There is no hard limit. HoneyClean processes files sequentially through the queue — drag and drop hundreds of files or entire folders.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "rembg not installed" on launch | Open Diagnostics → click "Fix" next to rembg. Or manually: `pip install rembg[gpu]` |
| Processing is slow (CPU-only) | Install CUDA: Diagnostics → GPU Setup wizard will guide you |
| Black output / corrupted images | Try a different model (BiRefNet General recommended). Check that input images are not corrupted |
| "Model not found" error | Go to Models page → download the required model |
| App won't start | Ensure Python 3.10+ is on PATH. Run `python --version` in a terminal |
| ZIP upload fails | ZIPs must be under 500 MB. Ensure no path traversal in archive |
| Video processing freezes | Lower Max VRAM percentage in Settings. Try disabling HW Encoding |
| GPU not detected | Update NVIDIA drivers. Restart after driver installation |

## Building from Source

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Rust](https://rustup.rs/) (latest stable)
- [Python](https://python.org/) 3.10+ with pip
- [Tauri CLI](https://v2.tauri.app/) v2

### Steps

```bash
# Clone the repository
git clone https://github.com/Zayn1312/honeyclean-v6.git
cd honeyclean-v6

# Install frontend dependencies
npm install

# Install Python dependencies
pip install rembg[gpu] pillow pymatting onnxruntime-gpu

# Development mode
npm run tauri dev

# Production build
npm run tauri build
```

The installer will be at `src-tauri/target/release/bundle/nsis/HoneyClean_6.0.0_x64-setup.exe`.

## Architecture

```
honeyclean-v6/
├── src/                          # Frontend (React + TypeScript)
│   ├── App.tsx                   # Main application component
│   ├── main.tsx                  # React entry point
│   ├── components/               # UI components
│   │   ├── EulaModal.tsx         # EULA acceptance dialog
│   │   ├── FirstRunModal.tsx     # First-run setup wizard
│   │   ├── GpuSetupModal.tsx     # GPU configuration wizard
│   │   ├── Layout.tsx            # Main layout wrapper
│   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   ├── StatusBar.tsx         # Status bar with GPU stats
│   │   └── ui/                   # Base UI primitives
│   ├── pages/                    # Page components
│   │   ├── QueuePage.tsx         # Batch processing queue
│   │   ├── EditorPage.tsx        # Image editor with brush tools
│   │   ├── ModelsPage.tsx        # Model management
│   │   ├── SettingsPage.tsx      # Configuration
│   │   └── DiagnosticsPage.tsx   # GPU diagnostics & health
│   ├── hooks/                    # React hooks
│   │   ├── useWorker.ts          # Python worker communication
│   │   ├── useGPU.ts             # GPU polling (2s interval)
│   │   └── useI18n.ts            # Internationalization
│   ├── store/
│   │   └── useStore.ts           # Zustand global state
│   └── lib/
│       ├── presets.ts            # Quality/platform presets, model sizes
│       ├── errorCodes.ts         # HC-001 through HC-045
│       └── i18n.ts               # 5-language translation strings
│
├── src-tauri/                    # Backend (Rust + Tauri v2)
│   ├── tauri.conf.json           # App config, NSIS installer settings
│   ├── src/
│   │   ├── main.rs               # Entry point
│   │   └── lib.rs                # Tauri commands & IPC
│   └── python/                   # Python processing backend
│       ├── honeyclean_worker.py  # Image/video processing pipeline
│       ├── gpu_diagnostics.py    # GPU detection & auto-fix
│       └── crash_mailer.py       # Error reporting
│
└── public/                       # Static assets
    └── logo.ico                  # Application icon
```

**Stack:** Tauri v2 (Rust) + React 18 + TypeScript + Zustand + Vite + Python (rembg, ONNX Runtime)

## License

MIT — [Zayn1312](https://github.com/Zayn1312)
