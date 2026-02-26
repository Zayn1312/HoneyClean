import { useStore } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";

export function StatusBar() {
  const { t } = useI18n();
  const processingState = useStore((s) => s.processingState);
  const progress = useStore((s) => s.progress);
  const currentFile = useStore((s) => s.currentFile);
  const speed = useStore((s) => s.speed);
  const eta = useStore((s) => s.eta);
  const provider = useStore((s) => s.provider);
  const isGpu = useStore((s) => s.isGpu);
  const queue = useStore((s) => s.queue);

  const stateColors: Record<string, string> = {
    idle: "text-green-400",
    processing: "text-yellow-400",
    paused: "text-yellow-400",
    stopped: "text-red-400",
  };

  const stateLabels: Record<string, string> = {
    idle: t("status_ready"),
    processing: t("status_processing"),
    paused: t("status_paused"),
    stopped: "Stopped",
  };

  const processed = queue.filter((i) => i.status === "done").length;

  return (
    <div className="h-7 flex items-center gap-4 px-4 text-[11px]
      bg-void-900/80 border-t border-void-600/40 font-mono shrink-0">
      {/* State indicator */}
      <span className={`flex items-center gap-1.5 ${stateColors[processingState]}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current" />
        {stateLabels[processingState]}
      </span>

      {/* Progress */}
      {processingState === "processing" && (
        <>
          <span className="text-honey-400">
            {Math.round(progress * 100)}%
          </span>
          {currentFile && (
            <span className="text-honey-600 truncate max-w-48">
              {currentFile}
            </span>
          )}
          {speed > 0 && (
            <span className="text-honey-500">
              {speed.toFixed(1)}/min
            </span>
          )}
          {eta && (
            <span className="text-honey-600">
              ETA: {eta}
            </span>
          )}
        </>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Processed count */}
      <span className="text-honey-600">
        {processed}/{queue.length}
      </span>

      {/* Provider */}
      <span className={`flex items-center gap-1 ${isGpu ? "text-green-400" : "text-yellow-500"}`}>
        {provider} {isGpu ? "✓" : "⚠"}
      </span>
    </div>
  );
}
