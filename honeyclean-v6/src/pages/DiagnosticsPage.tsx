import { useCallback, useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { motion, AnimatePresence } from "framer-motion";
import {
  RefreshCw, AlertTriangle, CheckCircle, Info, XCircle,
  Download, ExternalLink, Terminal,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { Button } from "../components/ui/Button";
import { Tooltip } from "../components/ui/Tooltip";

// ── Types ──
interface DiagCheck {
  key: string;
  label: string;
  value: string;
  ok: boolean;
  extra?: Record<string, unknown>;
}

interface DiagIssue {
  code: string;
  severity: "critical" | "warning" | "info" | "ok";
  title: string;
  description: string;
  fix_type: "pip_install" | "external_command" | "open_url" | "none";
  fix_command: string;
}

interface DiagResult {
  checks: DiagCheck[];
  issues: DiagIssue[];
  summary: {
    total_issues: number;
    critical: number;
    warnings: number;
    all_ok: boolean;
  };
}

// ── Severity config ──
const SEVERITY = {
  critical: { icon: XCircle, color: "#ef4444", bg: "rgba(239,68,68,0.08)", border: "rgba(239,68,68,0.25)", label: "Kritisch" },
  warning: { icon: AlertTriangle, color: "#f59e0b", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.25)", label: "Warnung" },
  info: { icon: Info, color: "#6b7280", bg: "rgba(107,114,128,0.08)", border: "rgba(107,114,128,0.2)", label: "Info" },
  ok: { icon: CheckCircle, color: "#22c55e", bg: "rgba(34,197,94,0.08)", border: "rgba(34,197,94,0.25)", label: "OK" },
};

// ── Main page ──
export function DiagnosticsPage() {
  const addToast = useStore((s) => s.addToast);
  const setHasGpuWarning = useStore((s) => s.setHasGpuWarning);

  const [result, setResult] = useState<DiagResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [installing, setInstalling] = useState<string | null>(null);
  const [installLog, setInstallLog] = useState("");
  const logRef = useRef<HTMLPreElement>(null);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [installLog]);

  const runDiagnostics = useCallback(async () => {
    setLoading(true);
    setInstallLog("");
    try {
      const diag = await invoke<DiagResult>("run_gpu_diagnostics");
      setResult(diag);

      const critical = diag.issues.filter((i) => i.severity === "critical");
      setHasGpuWarning(critical.length > 0);

      if (diag.summary.all_ok) {
        addToast("GPU-Diagnose: Alles OK", "success");
      } else if (critical.length > 0) {
        addToast(`${critical.length} kritische(s) Problem(e) gefunden`, "warning");
      }
    } catch (e) {
      addToast(`Diagnose fehlgeschlagen: ${e}`, "error");
    }
    setLoading(false);
  }, [addToast, setHasGpuWarning]);

  const handleFix = useCallback(async (issue: DiagIssue) => {
    if (issue.fix_type === "pip_install") {
      // Use automatic installer — no terminal needed
      setInstalling(issue.code);
      setInstallLog("");

      const unlisten = await listen<{ step: string }>("install-progress", (event) => {
        setInstallLog((prev) => prev + "\n" + event.payload.step);
      });

      try {
        const log = await invoke<string>("install_gpu_packages");
        unlisten();
        setInstallLog(log);
        addToast("Installation abgeschlossen — starte HoneyClean neu", "success");

        // Auto restart after 3 seconds
        setTimeout(() => {
          invoke("restart_app").catch(() => {});
        }, 3000);
      } catch (e) {
        unlisten();
        setInstallLog(String(e));
        addToast("Installation fehlgeschlagen", "error");

        // Send crash report
        invoke("send_crash_email", {
          errorId: `HC-DIAG-${Date.now().toString(36).toUpperCase()}`,
          errorType: "HC-INSTALL-002",
          message: String(e),
          context: "GPU fix from diagnostics page",
        }).catch(() => {});
      }
      setInstalling(null);
      await runDiagnostics();
    }

    if (issue.fix_type === "open_url") {
      window.open(issue.fix_command, "_blank");
    }
  }, [addToast, runDiagnostics]);

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto" style={{ padding: 20 }}>
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="font-heading font-semibold text-honey-300" style={{ fontSize: 22 }}>
            GPU-Diagnose
          </h2>
          <p className="text-sm text-honey-600 mt-0.5">
            Prueft GPU, Treiber, ONNX Runtime und alle Abhaengigkeiten
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          icon={loading ? <RefreshCw size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          onClick={runDiagnostics}
          disabled={loading}
        >
          {loading ? "Diagnose laeuft..." : result ? "Erneut pruefen" : "Diagnose starten"}
        </Button>
      </div>

      {/* No result yet */}
      {!result && !loading && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <Terminal size={48} className="text-honey-700" />
          <p className="text-honey-500 text-sm">Klicke "Diagnose starten" um dein System zu pruefen</p>
        </div>
      )}

      {/* Loading */}
      {loading && !result && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <RefreshCw size={48} className="text-honey-500 animate-spin" />
          <p className="text-honey-400 text-sm">System wird geprueft...</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Summary banner */}
          <div className="shrink-0 p-4 rounded-xl border"
            style={{
              background: result.summary.all_ok ? "rgba(34,197,94,0.06)" : "rgba(245,158,11,0.06)",
              borderColor: result.summary.all_ok ? "rgba(34,197,94,0.2)" : "rgba(245,158,11,0.2)",
            }}>
            <div className="flex items-center gap-3">
              {result.summary.all_ok ? (
                <CheckCircle size={20} className="text-green-400" />
              ) : (
                <AlertTriangle size={20} className="text-amber-400" />
              )}
              <span className="text-sm font-medium" style={{
                color: result.summary.all_ok ? "#22c55e" : "#f59e0b",
              }}>
                {result.summary.all_ok
                  ? "Alle Checks bestanden — GPU ist bereit"
                  : `${result.summary.critical} kritisch, ${result.summary.warnings} Warnungen`
                }
              </span>
            </div>
          </div>

          {/* System checks grid */}
          <div className="shrink-0">
            <h3 className="text-xs uppercase tracking-wider text-honey-600 font-semibold mb-2 px-1">
              System-Checks
            </h3>
            <div className="grid grid-cols-4 gap-2">
              {result.checks.map((check) => (
                <div key={check.key}
                  className="p-3 rounded-lg border"
                  style={{
                    background: check.ok ? "rgba(34,197,94,0.04)" : "rgba(239,68,68,0.04)",
                    borderColor: check.ok ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)",
                  }}>
                  <div className="flex items-center gap-2 mb-1">
                    {check.ok ? (
                      <CheckCircle size={12} className="text-green-400" />
                    ) : (
                      <XCircle size={12} className="text-red-400" />
                    )}
                    <span className="text-xs text-honey-500">{check.label}</span>
                  </div>
                  <p className="text-sm font-mono text-honey-300 truncate">{check.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Issues */}
          <div className="flex-1">
            <h3 className="text-xs uppercase tracking-wider text-honey-600 font-semibold mb-2 px-1">
              Ergebnisse
            </h3>
            <div className="space-y-3">
              <AnimatePresence mode="popLayout">
                {result.issues.map((issue) => {
                  const sev = SEVERITY[issue.severity];
                  const Icon = sev.icon;
                  const isInstalling = installing === issue.code;

                  return (
                    <motion.div
                      key={issue.code}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="p-4 rounded-xl border"
                      style={{ background: sev.bg, borderColor: sev.border }}
                    >
                      <div className="flex items-start gap-3">
                        <Icon size={18} style={{ color: sev.color, marginTop: 2 }} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-semibold" style={{ color: sev.color }}>
                              {issue.title}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                              style={{ background: sev.border, color: sev.color }}>
                              {sev.label}
                            </span>
                          </div>
                          <p className="text-xs text-honey-500 leading-relaxed">
                            {issue.description}
                          </p>
                        </div>

                        {/* Fix button */}
                        {issue.fix_type !== "none" && (
                          <Tooltip
                            content={
                              issue.fix_type === "pip_install" ? "Automatisch installieren" :
                              issue.fix_type === "open_url" ? "Link oeffnen" :
                              "Automatisch beheben"
                            }
                            position="left"
                          >
                            <button
                              onClick={() => handleFix(issue)}
                              disabled={isInstalling}
                              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors shrink-0"
                              style={{
                                background: "rgba(245,158,11,0.12)",
                                color: "#F59E0B",
                                border: "1px solid rgba(245,158,11,0.3)",
                              }}
                            >
                              {isInstalling ? (
                                <><RefreshCw size={12} className="animate-spin" /> Installiert...</>
                              ) : issue.fix_type === "pip_install" ? (
                                <><Download size={12} /> Automatisch beheben</>
                              ) : issue.fix_type === "open_url" ? (
                                <><ExternalLink size={12} /> Oeffnen</>
                              ) : (
                                <><Download size={12} /> Beheben</>
                              )}
                            </button>
                          </Tooltip>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </div>

          {/* Install log */}
          {installLog && (
            <div className="shrink-0">
              <h3 className="text-xs uppercase tracking-wider text-honey-600 font-semibold mb-2 px-1">
                Installations-Log
              </h3>
              <pre ref={logRef}
                className="text-xs font-mono text-honey-400 bg-void-900 border border-void-600 rounded-xl p-4 max-h-[200px] overflow-y-auto whitespace-pre-wrap">
                {installLog}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
