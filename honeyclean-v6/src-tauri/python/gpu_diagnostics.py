"""
HoneyClean v6.0 — GPU Diagnostics Script

Standalone script that checks the full GPU/ONNX pipeline and outputs JSON.
Run: python gpu_diagnostics.py
"""

import json
import os
import sys
import subprocess
import importlib.util

IS_WINDOWS = sys.platform == "win32"
SUBPROCESS_FLAGS = {}
if IS_WINDOWS:
    SUBPROCESS_FLAGS["creationflags"] = 0x08000000  # CREATE_NO_WINDOW


def run_cmd(cmd: list[str], timeout: int = 15) -> tuple[bool, str]:
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout,
            **SUBPROCESS_FLAGS,
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except FileNotFoundError:
        return False, "Command not found"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def check_python() -> dict:
    """Check Python version."""
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return {
        "key": "python",
        "label": "Python",
        "value": ver,
        "ok": sys.version_info >= (3, 10),
    }


def check_nvidia_smi() -> dict:
    """Check NVIDIA GPU via nvidia-smi."""
    ok, output = run_cmd(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                          "--format=csv,noheader,nounits"])
    if ok and output:
        parts = [p.strip() for p in output.split("\n")[0].split(",")]
        gpu_name = parts[0] if len(parts) > 0 else "Unknown"
        driver = parts[1] if len(parts) > 1 else "Unknown"
        vram = parts[2] if len(parts) > 2 else "0"
        return {
            "key": "nvidia_gpu",
            "label": "NVIDIA GPU",
            "value": gpu_name,
            "ok": True,
            "extra": {"driver": driver, "vram_total_mb": int(float(vram))},
        }
    return {
        "key": "nvidia_gpu",
        "label": "NVIDIA GPU",
        "value": "Nicht gefunden",
        "ok": False,
        "extra": {"driver": "", "vram_total_mb": 0},
    }


def check_nvidia_driver() -> dict:
    """Check NVIDIA driver version."""
    ok, output = run_cmd(["nvidia-smi", "--query-gpu=driver_version",
                          "--format=csv,noheader"])
    if ok and output:
        driver = output.strip().split("\n")[0].strip()
        return {
            "key": "nvidia_driver",
            "label": "NVIDIA Treiber",
            "value": driver,
            "ok": True,
        }
    return {
        "key": "nvidia_driver",
        "label": "NVIDIA Treiber",
        "value": "Nicht installiert",
        "ok": False,
    }


def check_cuda_toolkit() -> dict:
    """Check if nvcc (CUDA toolkit) is available."""
    ok, output = run_cmd(["nvcc", "--version"])
    if ok:
        # Extract version from output like "release 12.4"
        import re
        m = re.search(r"release (\d+\.\d+)", output)
        ver = m.group(1) if m else "Unknown"
        return {
            "key": "cuda_toolkit",
            "label": "CUDA Toolkit",
            "value": ver,
            "ok": True,
        }
    return {
        "key": "cuda_toolkit",
        "label": "CUDA Toolkit",
        "value": "Nicht installiert",
        "ok": False,
    }


def check_onnxruntime() -> dict:
    """Check onnxruntime installation and available providers."""
    spec = importlib.util.find_spec("onnxruntime")
    if spec is None:
        return {
            "key": "onnxruntime",
            "label": "ONNX Runtime",
            "value": "Nicht installiert",
            "ok": False,
            "extra": {"version": "", "providers": [], "package": ""},
        }

    import onnxruntime as ort
    providers = ort.get_available_providers()
    version = ort.__version__

    # Detect which package is installed
    package = "onnxruntime"
    try:
        ok_check, pip_output = run_cmd([sys.executable, "-m", "pip", "show", "onnxruntime-gpu"])
        if ok_check and "onnxruntime-gpu" in pip_output:
            package = "onnxruntime-gpu"
        else:
            ok_check2, pip_output2 = run_cmd([sys.executable, "-m", "pip", "show", "onnxruntime-directml"])
            if ok_check2 and "onnxruntime-directml" in pip_output2:
                package = "onnxruntime-directml"
    except Exception:
        pass

    has_cuda = "CUDAExecutionProvider" in providers
    has_dml = "DmlExecutionProvider" in providers
    has_trt = "TensorrtExecutionProvider" in providers
    is_gpu = has_cuda or has_dml or has_trt

    return {
        "key": "onnxruntime",
        "label": "ONNX Runtime",
        "value": f"{version} ({package})",
        "ok": is_gpu,
        "extra": {
            "version": version,
            "providers": providers,
            "package": package,
            "has_cuda": has_cuda,
            "has_dml": has_dml,
            "has_trt": has_trt,
        },
    }


def check_rembg() -> dict:
    """Check if rembg is installed."""
    spec = importlib.util.find_spec("rembg")
    if spec is None:
        return {
            "key": "rembg",
            "label": "rembg",
            "value": "Nicht installiert",
            "ok": False,
        }
    try:
        import rembg
        ver = getattr(rembg, "__version__", "installed")
        return {
            "key": "rembg",
            "label": "rembg",
            "value": ver,
            "ok": True,
        }
    except Exception as e:
        return {
            "key": "rembg",
            "label": "rembg",
            "value": f"Import Error: {e}",
            "ok": False,
        }


def check_vram_usage() -> dict:
    """Check current VRAM usage."""
    ok, output = run_cmd(["nvidia-smi", "--query-gpu=memory.used,memory.total",
                          "--format=csv,noheader,nounits"])
    if ok and output:
        parts = [p.strip() for p in output.split("\n")[0].split(",")]
        used = int(float(parts[0])) if len(parts) > 0 else 0
        total = int(float(parts[1])) if len(parts) > 1 else 0
        return {
            "key": "vram",
            "label": "VRAM",
            "value": f"{used}/{total} MB",
            "ok": True,
            "extra": {"used_mb": used, "total_mb": total},
        }
    return {
        "key": "vram",
        "label": "VRAM",
        "value": "Nicht verfuegbar",
        "ok": False,
        "extra": {"used_mb": 0, "total_mb": 0},
    }


def build_issues(checks: list[dict]) -> list[dict]:
    """Analyze check results and build issue list."""
    issues = []
    check_map = {c["key"]: c for c in checks}

    # --- NVIDIA GPU not found ---
    gpu = check_map.get("nvidia_gpu", {})
    if not gpu.get("ok"):
        issues.append({
            "code": "no_nvidia_gpu",
            "severity": "critical",
            "title": "Keine NVIDIA GPU gefunden",
            "description": "nvidia-smi konnte keine GPU erkennen. HoneyClean benoetigt eine NVIDIA GPU mit CUDA-Unterstuetzung fuer GPU-Beschleunigung.",
            "fix_type": "open_url",
            "fix_command": "https://www.nvidia.com/Download/index.aspx",
        })

    # --- NVIDIA driver missing/outdated ---
    driver = check_map.get("nvidia_driver", {})
    if gpu.get("ok") and not driver.get("ok"):
        issues.append({
            "code": "no_nvidia_driver",
            "severity": "critical",
            "title": "NVIDIA Treiber fehlt",
            "description": "Der NVIDIA Treiber ist nicht installiert oder veraltet.",
            "fix_type": "open_url",
            "fix_command": "https://www.nvidia.com/Download/index.aspx",
        })

    # --- ONNX Runtime not installed ---
    ort = check_map.get("onnxruntime", {})
    ort_extra = ort.get("extra", {})
    if not ort_extra.get("version"):
        issues.append({
            "code": "no_onnxruntime",
            "severity": "critical",
            "title": "ONNX Runtime nicht installiert",
            "description": "onnxruntime-gpu wird fuer die KI-Verarbeitung benoetigt.",
            "fix_type": "pip_install",
            "fix_command": "python -m pip install onnxruntime-gpu",
        })

    # --- Wrong onnxruntime package (directml instead of gpu) ---
    elif ort_extra.get("package") == "onnxruntime-directml" and gpu.get("ok"):
        issues.append({
            "code": "wrong_onnxruntime_package",
            "severity": "critical",
            "title": "Falsches ONNX Runtime Paket installiert",
            "description": f"onnxruntime-directml ist installiert, aber fuer NVIDIA GPUs wird onnxruntime-gpu benoetigt. Aktuell: {ort_extra.get('version', '?')}. Provider: {', '.join(ort_extra.get('providers', []))}.",
            "fix_type": "pip_install",
            "fix_command": "python -m pip install --force-reinstall onnxruntime-gpu",
        })

    # --- onnxruntime-gpu installed but no CUDA provider ---
    elif ort_extra.get("package") == "onnxruntime-gpu" and not ort_extra.get("has_cuda"):
        issues.append({
            "code": "ort_gpu_no_cuda",
            "severity": "warning",
            "title": "ONNX Runtime GPU installiert, aber CUDA nicht verfuegbar",
            "description": f"onnxruntime-gpu {ort_extra.get('version', '?')} ist installiert, aber CUDAExecutionProvider fehlt. Moeglicherweise stimmt die CUDA-Version nicht ueberein. Verfuegbare Provider: {', '.join(ort_extra.get('providers', []))}.",
            "fix_type": "pip_install",
            "fix_command": "python -m pip install --force-reinstall onnxruntime-gpu",
        })

    # --- Plain onnxruntime (no gpu, no dml) ---
    elif ort_extra.get("package") == "onnxruntime" and gpu.get("ok"):
        issues.append({
            "code": "ort_cpu_only",
            "severity": "critical",
            "title": "Nur CPU-Version von ONNX Runtime installiert",
            "description": "Das Paket 'onnxruntime' (CPU-only) ist installiert. Fuer GPU-Beschleunigung wird 'onnxruntime-gpu' benoetigt.",
            "fix_type": "pip_install",
            "fix_command": "python -m pip install onnxruntime-gpu",
        })

    # --- CUDA toolkit not found (warning, not critical) ---
    cuda = check_map.get("cuda_toolkit", {})
    if gpu.get("ok") and not cuda.get("ok"):
        issues.append({
            "code": "no_cuda_toolkit",
            "severity": "info",
            "title": "CUDA Toolkit nicht im PATH",
            "description": "nvcc wurde nicht gefunden. Das ist fuer die meisten Nutzer kein Problem — der NVIDIA Treiber reicht fuer ONNX Runtime. Nur fuer TensorRT-Optimierung wird das CUDA Toolkit benoetigt.",
            "fix_type": "none",
            "fix_command": "",
        })

    # --- rembg missing ---
    rembg = check_map.get("rembg", {})
    if not rembg.get("ok"):
        issues.append({
            "code": "no_rembg",
            "severity": "critical",
            "title": "rembg nicht installiert",
            "description": "Das rembg-Paket wird fuer die Hintergrundentfernung benoetigt.",
            "fix_type": "pip_install",
            "fix_command": "python -m pip install rembg[gpu]",
        })

    # --- Everything OK ---
    if ort_extra.get("has_cuda") and gpu.get("ok"):
        issues.append({
            "code": "gpu_ok",
            "severity": "ok",
            "title": "GPU bereit",
            "description": f"CUDA aktiv mit {gpu.get('value', 'GPU')}. Alles korrekt konfiguriert.",
            "fix_type": "none",
            "fix_command": "",
        })
    elif ort_extra.get("has_dml") and not ort_extra.get("has_cuda"):
        issues.append({
            "code": "dml_fallback",
            "severity": "warning",
            "title": "DirectML Fallback aktiv",
            "description": "Verarbeitung laeuft ueber DirectML statt CUDA. CUDA ist schneller. Installiere onnxruntime-gpu fuer beste Leistung.",
            "fix_type": "pip_install",
            "fix_command": "python -m pip install --force-reinstall onnxruntime-gpu",
        })

    return issues


def main():
    checks = [
        check_python(),
        check_nvidia_smi(),
        check_nvidia_driver(),
        check_cuda_toolkit(),
        check_onnxruntime(),
        check_rembg(),
        check_vram_usage(),
    ]

    issues = build_issues(checks)

    result = {
        "checks": checks,
        "issues": issues,
        "summary": {
            "total_issues": len([i for i in issues if i["severity"] in ("critical", "warning")]),
            "critical": len([i for i in issues if i["severity"] == "critical"]),
            "warnings": len([i for i in issues if i["severity"] == "warning"]),
            "all_ok": all(i["severity"] in ("ok", "info") for i in issues),
        },
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
