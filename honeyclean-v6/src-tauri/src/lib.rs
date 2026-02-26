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

fn find_python() -> String {
    // Try common Python paths on Windows
    for cmd in &["python", "python3", "py"] {
        if let Ok(output) = Command::new(cmd)
            .arg("--version")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .creation_flags(0x08000000) // CREATE_NO_WINDOW
            .output()
        {
            if output.status.success() {
                return cmd.to_string();
            }
        }
    }
    "python".to_string()
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

    let python = find_python();
    let script = find_worker_script(&app);

    let mut child = Command::new(&python)
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
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
