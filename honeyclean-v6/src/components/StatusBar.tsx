import { useStore } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { Tooltip } from "./ui/Tooltip";

export function StatusBar() {
  const { t } = useI18n();
  const processingState = useStore((s) => s.processingState);
  const currentFile = useStore((s) => s.currentFile);
  const speed = useStore((s) => s.speed);
  const eta = useStore((s) => s.eta);
  const provider = useStore((s) => s.provider);
  const isGpu = useStore((s) => s.isGpu);
  const queue = useStore((s) => s.queue);
  const gpuInfo = useStore((s) => s.gpuInfo);
  const setPage = useStore((s) => s.setPage);

  const dotColor =
    processingState === "processing" ? "#F59E0B" :
    processingState === "stopped" ? "#EF4444" :
    processingState === "paused" ? "#7070A0" :
    "#4ADE80";

  const stateLabel =
    processingState === "processing" ? t("status_processing") :
    processingState === "paused" ? t("status_paused") :
    processingState === "stopped" ? "Stopped" :
    t("status_ready");

  const providerColor =
    provider.includes("CUDA") ? "#4ADE80" :
    provider.includes("DirectML") || provider.includes("DML") ? "#60A5FA" :
    "#EAB308";

  const providerTooltip =
    provider.includes("CUDA") ? "NVIDIA CUDA aktiv. Optimale GPU-Beschleunigung." :
    provider.includes("DirectML") ? "DirectML aktiv. GPU-Beschleunigung über DirectX." :
    "GPU wird nicht verwendet. Verarbeitung läuft auf CPU — deutlich langsamer.";

  const processed = queue.filter((i) => i.status === "done").length;
  const isCpuMode = !isGpu;

  return (
    <>
      {/* GPU warning banner — shown when CPU mode is active */}
      {isCpuMode && provider && (
        <div className="gpu-warning-banner">
          <span>⚠</span>
          <span>GPU nicht aktiv — Verarbeitung läuft auf CPU (10x langsamer).</span>
          <button
            onClick={() => setPage("settings")}
            className="ml-auto text-honey-400 hover:text-honey-300 transition-colors"
            style={{ fontSize: 13 }}
          >
            GPU aktivieren →
          </button>
        </div>
      )}

      <div
        className="flex items-center gap-4 px-4 font-mono shrink-0
          bg-void-900/80 border-t border-void-600/40"
        style={{ height: 28, fontSize: 13 }}
      >
        {/* State indicator */}
        <Tooltip
          content={stateLabel}
          detail={processingState === "processing" ? `${processed}/${queue.length} verarbeitet` : undefined}
          position="top"
        >
          <span className="flex items-center gap-1.5" style={{ color: dotColor }}>
            <span
              className="rounded-full"
              style={{
                width: 6,
                height: 6,
                background: dotColor,
                boxShadow: processingState === "processing" ? `0 0 6px ${dotColor}` : "none",
                animation: processingState === "processing" ? "pulse-amber 1.5s ease-in-out infinite" : "none",
              }}
            />
            {processingState === "processing"
              ? `${t("status_processing").replace("...", "")} ${processed}/${queue.length}`
              : stateLabel
            }
          </span>
        </Tooltip>

        {/* Processing details */}
        {processingState === "processing" && (
          <>
            <span className="text-void-400">—</span>
            {currentFile && (
              <span className="text-honey-600 truncate max-w-48" style={{ fontSize: 13 }}>
                {currentFile}
              </span>
            )}
            {speed > 0 && (
              <>
                <span className="text-void-400">—</span>
                <span className="text-honey-500">
                  {speed.toFixed(1)} Bilder/min
                </span>
              </>
            )}
            {eta && (
              <span className="text-honey-700">
                ETA {eta}
              </span>
            )}
          </>
        )}

        {/* Idle count */}
        {processingState !== "processing" && queue.length > 0 && (
          <span className="text-honey-700" style={{ fontSize: 13 }}>
            {processed}/{queue.length}
          </span>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Provider badge */}
        <Tooltip content={providerTooltip} position="top">
          <span className="flex items-center gap-1.5" style={{ color: providerColor, fontSize: 13 }}>
            <span
              className="rounded-full"
              style={{ width: 5, height: 5, background: providerColor }}
            />
            {provider || "CPU"}
            {isGpu ? " ✓" : " ⚠"}
          </span>
        </Tooltip>

        {/* VRAM */}
        {gpuInfo.vram_total > 0 && (
          <Tooltip content="Aktueller GPU-Speicher: belegt / gesamt." position="top">
            <span className="text-honey-700" style={{ fontSize: 13 }}>
              {gpuInfo.vram_used}/{gpuInfo.vram_total} MB
            </span>
          </Tooltip>
        )}
      </div>
    </>
  );
}
