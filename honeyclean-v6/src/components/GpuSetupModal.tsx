import { useCallback, useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { motion } from "framer-motion";
import { Zap, RefreshCw, CheckCircle, XCircle } from "lucide-react";
import { Button } from "./ui/Button";
import { useStore } from "../store/useStore";
import { useWorker } from "../hooks/useWorker";

type ModalState = "prompt" | "installing" | "success" | "failed";

export function GpuSetupModal({ onClose }: { onClose: () => void }) {
  const { send } = useWorker();
  const workerReady = useStore((s) => s.workerReady);
  const gpuInfo = useStore((s) => s.gpuInfo);

  const [state, setState] = useState<ModalState>("prompt");
  const [currentStep, setCurrentStep] = useState("");
  const [installLog, setInstallLog] = useState("");
  const [restartCountdown, setRestartCountdown] = useState(3);
  const [errorId, setErrorId] = useState("");
  const logRef = useRef<HTMLPreElement>(null);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [installLog]);

  const handleInstall = useCallback(async () => {
    setState("installing");
    setCurrentStep("Verbinde mit PyPI...");
    setInstallLog("");

    const unlisten = await listen<{ step: string }>("install-progress", (event) => {
      setCurrentStep(event.payload.step);
      setInstallLog((prev) => prev + "\n" + event.payload.step);
    });

    try {
      const log = await invoke<string>("install_gpu_packages");
      unlisten();

      setInstallLog(log);
      setState("success");

      // Save preference via worker
      if (workerReady) {
        send("save_config", { config: { gpu_setup_done: true } }).catch(() => {});
      }

      // Auto restart countdown
      let count = 3;
      setRestartCountdown(count);
      const timer = setInterval(() => {
        count--;
        setRestartCountdown(count);
        if (count <= 0) {
          clearInterval(timer);
          invoke("restart_app").catch(() => {});
        }
      }, 1000);
    } catch (error) {
      unlisten();

      const eid = `HC-GPU-${Date.now().toString(36).toUpperCase()}`;
      setErrorId(eid);

      // Send crash email automatically
      invoke("send_crash_email", {
        errorId: eid,
        errorType: "HC-INSTALL-002",
        message: String(error),
        context: "GPU package installation during setup wizard",
      }).catch(() => {});

      setState("failed");
    }
  }, [send, workerReady]);

  const handleSkip = useCallback(() => {
    if (workerReady) {
      send("save_config", { config: { gpu_setup_declined: true } }).catch(() => {});
    }
    onClose();
  }, [onClose, send, workerReady]);

  const handleUseCPU = useCallback(() => {
    if (workerReady) {
      send("save_config", { config: { gpu_setup_declined: true } }).catch(() => {});
    }
    onClose();
  }, [onClose, send, workerReady]);

  const gpuName = gpuInfo.gpu_name || "NVIDIA GPU";

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(6px)" }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-md bg-void-800 border border-void-600 rounded-2xl shadow-2xl overflow-hidden"
      >
        {/* ── PROMPT ── */}
        {state === "prompt" && (
          <div style={{ padding: 28 }}>
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.2)" }}>
                <Zap size={32} className="text-amber-400" />
              </div>
            </div>

            <h2 className="text-center font-heading font-bold text-honey-200 mb-2" style={{ fontSize: 20 }}>
              10x schnellere Verarbeitung
            </h2>
            <p className="text-center text-sm text-honey-500 mb-5">
              HoneyClean kann deine <strong className="text-honey-300">{gpuName}</strong> nutzen.
              Dafuer wird <strong className="text-honey-300">onnxruntime-gpu</strong> installiert (~200 MB).
            </p>

            <div className="space-y-2 mb-6">
              {[
                "GPU statt CPU — 10x schneller",
                "RAM bleibt frei",
                "Batch-Verarbeitung in Sekunden",
              ].map((text) => (
                <div key={text} className="flex items-center gap-2.5 text-sm text-honey-400">
                  <CheckCircle size={14} className="text-green-400 shrink-0" />
                  <span>{text}</span>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <Button variant="primary" className="w-full justify-center" onClick={handleInstall}>
                <Zap size={15} /> Ja, GPU einrichten (empfohlen)
              </Button>
              <Button variant="ghost" className="w-full justify-center" onClick={handleSkip}>
                Nein, CPU verwenden
              </Button>
            </div>

            <p className="text-center text-[11px] text-honey-700 mt-3">
              Diese Frage erscheint nicht erneut.
            </p>
          </div>
        )}

        {/* ── INSTALLING ── */}
        {state === "installing" && (
          <div style={{ padding: 28 }}>
            <div className="flex justify-center mb-4">
              <RefreshCw size={40} className="text-amber-400 animate-spin" />
            </div>

            <h2 className="text-center font-heading font-bold text-honey-200 mb-1" style={{ fontSize: 18 }}>
              GPU wird eingerichtet...
            </h2>
            <p className="text-center text-sm text-amber-400 mb-4">
              {currentStep}
            </p>

            <pre ref={logRef}
              className="text-[11px] font-mono text-honey-500 bg-void-900 border border-void-600 rounded-lg p-3 max-h-[160px] overflow-y-auto whitespace-pre-wrap mb-4">
              {installLog || "Warte auf Ausgabe..."}
            </pre>

            {/* Indeterminate progress bar */}
            <div className="w-full h-1.5 bg-void-700 rounded-full overflow-hidden">
              <div className="h-full bg-amber-400 rounded-full animate-pulse" style={{ width: "60%" }} />
            </div>

            <p className="text-center text-[11px] text-honey-700 mt-3">
              Bitte nicht schliessen — Installation laeuft...
            </p>
          </div>
        )}

        {/* ── SUCCESS ── */}
        {state === "success" && (
          <div style={{ padding: 28 }}>
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.2)" }}>
                <CheckCircle size={32} className="text-green-400" />
              </div>
            </div>

            <h2 className="text-center font-heading font-bold text-green-400 mb-2" style={{ fontSize: 20 }}>
              GPU eingerichtet
            </h2>
            <p className="text-center text-sm text-honey-400 mb-4">
              CUDA erfolgreich aktiviert! HoneyClean wird neu gestartet...
            </p>

            {/* Countdown bar */}
            <div className="w-full h-2 bg-void-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-green-400 rounded-full"
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{ duration: 3, ease: "linear" }}
              />
            </div>

            <p className="text-center text-sm text-honey-500 mt-3">
              Neustart in {restartCountdown}...
            </p>
          </div>
        )}

        {/* ── FAILED ── */}
        {state === "failed" && (
          <div style={{ padding: 28 }}>
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)" }}>
                <XCircle size={32} className="text-red-400" />
              </div>
            </div>

            <h2 className="text-center font-heading font-bold text-red-400 mb-2" style={{ fontSize: 20 }}>
              Installation fehlgeschlagen
            </h2>
            <p className="text-center text-sm text-honey-500 mb-1">
              Ein Fehlerbericht wurde an den Entwickler gesendet.
            </p>
            <p className="text-center text-xs text-honey-600 mb-5">
              Fehler-ID: <strong className="text-honey-400 font-mono">{errorId}</strong>
            </p>

            <div className="space-y-2">
              <Button variant="primary" className="w-full justify-center" onClick={handleUseCPU}>
                CPU verwenden
              </Button>
              <Button variant="ghost" className="w-full justify-center" onClick={() => {
                setState("prompt");
                setInstallLog("");
                setCurrentStep("");
              }}>
                Erneut versuchen
              </Button>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
