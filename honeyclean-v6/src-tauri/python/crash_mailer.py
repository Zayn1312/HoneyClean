"""
HoneyClean Crash Mailer
Sends classified error reports to zaynhonig@gmail.com
Called by Rust via subprocess — never by user.
"""
import sys
import json
import datetime
import platform
import subprocess
import os
import smtplib
from email.mime.text import MIMEText

ERROR_CLASSES = {
    "HC-INSTALL-001": ("CRITICAL", "Python subprocess spawn failed"),
    "HC-INSTALL-002": ("CRITICAL", "pip install failed"),
    "HC-INSTALL-003": ("CRITICAL", "Post-install CUDA check failed"),
    "HC-GPU-001":     ("ERROR",    "No GPU provider available"),
    "HC-GPU-002":     ("ERROR",    "Session creation failed"),
    "HC-WORKER-001":  ("ERROR",    "Worker process died unexpectedly"),
    "HC-WORKER-002":  ("WARNING",  "Worker communication timeout"),
    "HC-PROC-001":    ("ERROR",    "Image processing failed"),
    "HC-PROC-002":    ("WARNING",  "Output save failed"),
    "HC-MEM-001":     ("WARNING",  "RAM threshold exceeded"),
    "HC-CRASH-001":   ("CRITICAL", "Unhandled worker exception"),
}


def send_report(data: dict):
    error_id   = data.get("error_id", "HC-UNKNOWN-001")
    error_type = data.get("error_type", "UNKNOWN")
    message    = data.get("message", "")
    context    = data.get("context", "")
    traceback_str = data.get("traceback", "")

    cls = ERROR_CLASSES.get(error_type, ("UNKNOWN", "Unclassified error"))
    severity, description = cls

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        gpu = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3
        ).stdout.strip()
    except Exception:
        gpu = "unavailable"

    body = f"""
HONEYCLEAN v6.0 — AUTOMATED ERROR REPORT

ERROR ID:     {error_id}
SEVERITY:     {severity}
DESCRIPTION:  {description}
TIMESTAMP:    {timestamp}

ERROR DETAILS
Type:     {error_type}
Message:  {message}
Context:  {context}

TRACEBACK
{traceback_str or "No traceback available"}

SYSTEM INFO
OS:       {platform.platform()}
Python:   {sys.version}
GPU:      {gpu}
""".strip()

    config_path = os.path.join(
        os.environ.get("APPDATA", ""), "HoneyClean", "mailer.json"
    )

    try:
        if os.path.exists(config_path):
            with open(config_path) as f:
                cfg = json.load(f)
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = f"[HC v6.0] {severity}: {error_id} — {description}"
            msg["From"]    = cfg["from"]
            msg["To"]      = "zaynhonig@gmail.com"

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(cfg["from"], cfg["password"])
                s.send_message(msg)
        else:
            # Fallback: save to local file
            log_dir = os.path.join(os.environ.get("APPDATA", ""), "HoneyClean", "errors")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, f"{error_id}.txt"), "w") as f:
                f.write(body)
    except Exception:
        # Never crash the mailer
        pass


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    send_report(data)
