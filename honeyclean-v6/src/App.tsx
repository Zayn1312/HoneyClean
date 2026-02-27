import { useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { useStore } from "./store/useStore";
import { useGPU } from "./hooks/useGPU";
import { useWorker } from "./hooks/useWorker";
import { HoneyBackground } from "./components/HoneyBackground";
import { HoneyCursor } from "./components/HoneyCursor";
import { Layout } from "./components/Layout";
import { ToastContainer } from "./components/Toast";
import { EulaModal } from "./components/EulaModal";
import { FirstRunModal } from "./components/FirstRunModal";
import { GpuSetupModal } from "./components/GpuSetupModal";
import { QueuePage } from "./pages/QueuePage";
import { EditorPage } from "./pages/EditorPage";
import { ModelsPage } from "./pages/ModelsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { DiagnosticsPage } from "./pages/DiagnosticsPage";
import { AboutPage } from "./pages/AboutPage";

export default function App() {
  const page = useStore((s) => s.page);
  const eulaAccepted = useStore((s) => s.eulaAccepted);
  const setEulaAccepted = useStore((s) => s.setEulaAccepted);
  const showFirstRun = useStore((s) => s.showFirstRun);
  const setShowFirstRun = useStore((s) => s.setShowFirstRun);
  const setConfig = useStore((s) => s.setConfig);
  const setLanguage = useStore((s) => s.setLanguage);
  const workerReady = useStore((s) => s.workerReady);
  const setHasGpuWarning = useStore((s) => s.setHasGpuWarning);
  const showGpuSetup = useStore((s) => s.showGpuSetup);
  const setShowGpuSetup = useStore((s) => s.setShowGpuSetup);
  const config = useStore((s) => s.config);
  const { send } = useWorker();

  // Poll GPU info
  useGPU(2000);

  // Load config on worker ready
  useEffect(() => {
    if (!workerReady) return;
    send("get_config").then((res) => {
      if (res.status === "ok" && res.data?.config) {
        const cfg = res.data.config as Record<string, unknown>;
        setConfig(cfg);
        if (cfg.language) setLanguage(cfg.language as "en" | "de" | "fr" | "es" | "zh");
        if (cfg.eula_accepted) setEulaAccepted(true);
      }
    }).catch(() => {});
  }, [workerReady, send, setConfig, setLanguage, setEulaAccepted]);

  // Auto-diagnose GPU on startup — show setup modal if CUDA missing
  useEffect(() => {
    async function gpuSetupCheck() {
      // Skip if user already decided
      const declined = config.gpu_setup_declined as boolean | undefined;
      const done = config.gpu_setup_done as boolean | undefined;
      if (declined || done) return;

      try {
        const diag = await invoke<{
          summary: { all_ok: boolean; critical: number };
          issues: { severity: string; title: string; code: string }[];
        }>("run_gpu_diagnostics");

        const critical = diag.issues.filter((i) => i.severity === "critical");
        setHasGpuWarning(critical.length > 0);

        if (critical.length > 0) {
          // Show the automatic setup modal
          setShowGpuSetup(true);
        }
      } catch (e) {
        console.error("GPU diagnostics failed:", e);
      }
    }

    // Wait for config to load before checking
    if (workerReady && Object.keys(config).length > 0) {
      gpuSetupCheck();
    }
  }, [workerReady, config, setHasGpuWarning, setShowGpuSetup]);

  return (
    <>
      <HoneyBackground />
      <HoneyCursor />

      {!eulaAccepted ? (
        <EulaModal
          onAccept={() => {
            setEulaAccepted(true);
            setShowFirstRun(true);
            send("save_config", {
              config: {
                eula_accepted: true,
                eula_accepted_date: new Date().toISOString(),
              },
            }).catch(() => {});
          }}
        />
      ) : showFirstRun ? (
        <FirstRunModal onClose={() => setShowFirstRun(false)} />
      ) : (
        <Layout>
          {/* All pages rendered simultaneously, hidden via display:none.
              This prevents canvas/WebGL context destruction on navigation. */}
          <div style={{ display: page === "queue" ? "flex" : "none" }} className="h-full flex-col">
            <QueuePage />
          </div>
          <div style={{ display: page === "editor" ? "flex" : "none" }} className="h-full flex-col">
            <EditorPage />
          </div>
          <div style={{ display: page === "models" ? "flex" : "none" }} className="h-full flex-col">
            <ModelsPage />
          </div>
          <div style={{ display: page === "diagnostics" ? "flex" : "none" }} className="h-full flex-col">
            <DiagnosticsPage />
          </div>
          <div style={{ display: page === "settings" ? "flex" : "none" }} className="h-full flex-col">
            <SettingsPage />
          </div>
          <div style={{ display: page === "about" ? "flex" : "none" }} className="h-full flex-col">
            <AboutPage />
          </div>
        </Layout>
      )}

      {showGpuSetup && (
        <GpuSetupModal onClose={() => setShowGpuSetup(false)} />
      )}

      <ToastContainer />
    </>
  );
}
