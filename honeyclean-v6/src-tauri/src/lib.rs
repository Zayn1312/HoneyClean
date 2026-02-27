use serde_json::Value;
use std::io::{BufRead, BufReader, Write};
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, Manager, State};

struct WorkerState {
    child: Option<Child>,
    stdin_writer: Option<std::process::ChildStdin>,
}

impl Default for WorkerState {
    fn default() -> Self {
        Self {
            child: None,
            stdin_writer: None,
        }
    }
}

type WorkerGuard = Mutex<WorkerState>;

fn find_python_312() -> (String, Vec<String>) {
    // Hardcoded Python 3.12 paths — confirmed working with onnxruntime-gpu CUDA
    let paths = vec![
        r"C:\Users\anoua\AppData\Local\Programs\Python\Python312\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Program Files\Python312\python.exe",
    ];

    for path in &paths {
        if std::path::Path::new(path).exists() {
            eprintln!("[HC] Python 3.12 found at: {}", path);
            return (path.to_string(), vec![]);
        }
    }

    // Fallback: try py -3.12
    if Command::new("py")
        .args(["-3.12", "--version"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .creation_flags(0x08000000)
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
    {
        eprintln!("[HC] Using: py -3.12");
        return ("py".to_string(), vec!["-3.12".to_string()]);
    }

    eprintln!("[HC] WARNING: Python 3.12 not found, falling back to python (CPU mode)");
    ("python".to_string(), vec![])
}

fn find_worker_script(app: &AppHandle) -> String {
    // Try multiple locations for the worker script
    let locations = vec![
        // Development: relative to src-tauri
        app.path()
            .resource_dir()
            .ok()
            .map(|p| p.join("python/honeyclean_worker.py")),
        // Alongside the binary
        std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.join("python/honeyclean_worker.py"))),
        // Source directory during development
        Some(
            std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("python/honeyclean_worker.py"),
        ),
    ];

    for loc in locations.into_iter().flatten() {
        if loc.exists() {
            return loc.to_string_lossy().to_string();
        }
    }

    // Fallback
    "python/honeyclean_worker.py".to_string()
}

#[tauri::command]
fn spawn_worker(app: AppHandle, state: State<'_, WorkerGuard>) -> Result<String, String> {
    let mut guard = state.lock().map_err(|e| e.to_string())?;

    // Kill existing worker if any
    if let Some(ref mut child) = guard.child {
        let _ = child.kill();
    }

    let (python_bin, python_prefix) = find_python_312();
    let script = find_worker_script(&app);

    let mut cmd = Command::new(&python_bin);
    for arg in &python_prefix {
        cmd.arg(arg);
    }
    let mut child = cmd
        .arg(&script)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .creation_flags(0x08000000) // CREATE_NO_WINDOW
        .spawn()
        .map_err(|e| format!("Failed to spawn worker: {}", e))?;

    let stdin = child.stdin.take().ok_or("Failed to get stdin")?;
    let stdout = child.stdout.take().ok_or("Failed to get stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to get stderr")?;

    guard.child = Some(child);
    guard.stdin_writer = Some(stdin);

    // Spawn stdout reader thread — emits messages to frontend
    let app_handle = app.clone();
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line) = line {
                if let Ok(msg) = serde_json::from_str::<Value>(&line) {
                    let _ = app_handle.emit("worker-message", msg);
                }
            }
        }
    });

    // Spawn stderr reader thread — log to console
    std::thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line) = line {
                eprintln!("[Worker stderr] {}", line);
            }
        }
    });

    Ok("Worker spawned".to_string())
}

#[tauri::command]
fn send_to_worker(message: String, state: State<'_, WorkerGuard>) -> Result<(), String> {
    let mut guard = state.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut stdin) = guard.stdin_writer {
        writeln!(stdin, "{}", message).map_err(|e| format!("Write failed: {}", e))?;
        stdin.flush().map_err(|e| format!("Flush failed: {}", e))?;
        Ok(())
    } else {
        Err("Worker not running".to_string())
    }
}

const IMAGE_EXTENSIONS: &[&str] = &[
    "png", "jpg", "jpeg", "webp", "bmp", "tiff", "zip",
];
const VIDEO_EXTENSIONS: &[&str] = &["mp4", "mov", "avi", "mkv", "webm", "flv", "m4v"];

#[tauri::command]
fn list_dir_images(path: String) -> Result<Vec<String>, String> {
    let dir = std::path::Path::new(&path);
    if !dir.is_dir() {
        return Err(format!("Not a directory: {}", path));
    }
    let mut files = Vec::new();
    collect_files(dir, &mut files);
    files.sort();
    Ok(files)
}

fn collect_files(dir: &std::path::Path, out: &mut Vec<String>) {
    let entries = match std::fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            collect_files(&path, out);
        } else if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
            let ext_lower = ext.to_lowercase();
            if IMAGE_EXTENSIONS.contains(&ext_lower.as_str())
                || VIDEO_EXTENSIONS.contains(&ext_lower.as_str())
            {
                out.push(path.to_string_lossy().to_string());
            }
        }
    }
}

#[tauri::command]
fn get_gpu_info() -> Result<Value, String> {
    let output = Command::new("nvidia-smi")
        .args([
            "--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version",
            "--format=csv,noheader,nounits",
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .creation_flags(0x08000000)
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let text = String::from_utf8_lossy(&out.stdout);
            let parts: Vec<&str> = text.trim().split(',').collect();
            if parts.len() >= 5 {
                Ok(serde_json::json!({
                    "gpu_name": parts[0].trim(),
                    "vram_total": parts[1].trim().parse::<f64>().unwrap_or(0.0) as i64,
                    "vram_used": parts[2].trim().parse::<f64>().unwrap_or(0.0) as i64,
                    "gpu_util": parts[3].trim().parse::<f64>().unwrap_or(0.0) as i64,
                    "driver": parts[4].trim(),
                }))
            } else {
                Ok(serde_json::json!({}))
            }
        }
        _ => Ok(serde_json::json!({})),
    }
}

#[tauri::command]
fn copy_file(src: String, dst: String) -> Result<(), String> {
    std::fs::copy(&src, &dst).map_err(|e| format!("Copy failed: {}", e))?;
    Ok(())
}

#[tauri::command]
fn run_gpu_diagnostics(app: AppHandle) -> Result<Value, String> {
    let (python_bin, python_prefix) = find_python_312();

    // Find gpu_diagnostics.py using same logic as worker script
    let locations = vec![
        app.path()
            .resource_dir()
            .ok()
            .map(|p| p.join("python/gpu_diagnostics.py")),
        std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.join("python/gpu_diagnostics.py"))),
        Some(
            std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("python/gpu_diagnostics.py"),
        ),
    ];

    let script = locations
        .into_iter()
        .flatten()
        .find(|p| p.exists())
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| "python/gpu_diagnostics.py".to_string());

    let mut cmd = Command::new(&python_bin);
    for arg in &python_prefix {
        cmd.arg(arg);
    }
    let output = cmd
        .arg(&script)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .creation_flags(0x08000000)
        .output()
        .map_err(|e| format!("Failed to run diagnostics: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);

    serde_json::from_str::<Value>(stdout.trim())
        .map_err(|e| format!("Invalid diagnostics JSON: {} — output: {}", e, stdout))
}

#[tauri::command]
fn run_pip_install(package: String) -> Result<String, String> {
    let (python_bin, python_prefix) = find_python_312();

    let mut cmd = Command::new(&python_bin);
    for arg in &python_prefix {
        cmd.arg(arg);
    }
    let output = cmd
        .args(["-m", "pip", "install", "--force-reinstall", &package])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .creation_flags(0x08000000)
        .output()
        .map_err(|e| format!("pip install failed: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    let combined = format!("{}\n{}", stdout, stderr);

    if output.status.success() {
        Ok(combined)
    } else {
        Err(format!("pip install failed:\n{}", combined))
    }
}

fn find_python_312_exe() -> String {
    let paths = vec![
        r"C:\Users\anoua\AppData\Local\Programs\Python\Python312\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Program Files\Python312\python.exe",
    ];
    for path in &paths {
        if std::path::Path::new(path).exists() {
            return path.to_string();
        }
    }
    "py".to_string()
}

fn find_script(app: &AppHandle, name: &str) -> String {
    let locations = vec![
        app.path()
            .resource_dir()
            .ok()
            .map(|p| p.join(format!("python/{}", name))),
        std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.join(format!("python/{}", name)))),
        Some(
            std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join(format!("python/{}", name)),
        ),
    ];
    for loc in locations.into_iter().flatten() {
        if loc.exists() {
            return loc.to_string_lossy().to_string();
        }
    }
    format!("python/{}", name)
}

#[tauri::command]
async fn install_gpu_packages(
    _app: AppHandle,
    window: tauri::Window,
) -> Result<String, String> {
    let python = find_python_312_exe();
    let packages = vec!["onnxruntime-gpu", "rembg[gpu]"];
    let mut full_log = String::new();

    for package in &packages {
        let _ = window.emit(
            "install-progress",
            serde_json::json!({
                "step": format!("Installiere {}...", package),
                "package": package,
            }),
        );

        let output = Command::new(&python)
            .args(["-m", "pip", "install", "--upgrade", package])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .creation_flags(0x08000000)
            .output()
            .map_err(|e| format!("HC-INSTALL-001: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        full_log.push_str(&format!("\n=== {} ===\n{}\n{}", package, stdout, stderr));

        if !output.status.success() {
            return Err(format!("HC-INSTALL-002: pip install {} failed:\n{}", package, full_log));
        }
    }

    Ok(full_log)
}

#[tauri::command]
fn restart_app(app: AppHandle) {
    tauri::process::restart(&app.env());
}

#[tauri::command]
fn send_crash_email(
    app: AppHandle,
    error_id: String,
    error_type: String,
    message: String,
    context: String,
) -> Result<(), String> {
    let python = find_python_312_exe();
    let script = find_script(&app, "crash_mailer.py");

    let payload = serde_json::json!({
        "error_id": error_id,
        "error_type": error_type,
        "message": message,
        "context": context,
    });

    std::thread::spawn(move || {
        let _ = Command::new(&python)
            .args([&script, &payload.to_string()])
            .creation_flags(0x08000000)
            .output();
    });

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(Mutex::new(WorkerState::default()))
        .invoke_handler(tauri::generate_handler![
            spawn_worker,
            send_to_worker,
            get_gpu_info,
            list_dir_images,
            copy_file,
            run_gpu_diagnostics,
            run_pip_install,
            install_gpu_packages,
            restart_app,
            send_crash_email,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
