import { useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { Download, Check, X, Loader2 } from "lucide-react";
import { useI18n } from "../hooks/useI18n";
import { useWorker } from "../hooks/useWorker";
import { useStore } from "../store/useStore";
import { Button } from "./ui/Button";
import { MODEL_PRIORITY } from "../lib/presets";
import { formatSize, MODEL_SIZES } from "../lib/presets";

interface ModelStatus {
  id: string;
  status: "pending" | "downloading" | "done" | "error";
  pct: number;
}

interface FirstRunModalProps {
  onClose: () => void;
}

export function FirstRunModal({ onClose }: FirstRunModalProps) {
  const { t } = useI18n();
  const { send } = useWorker();
  const workerReady = useStore((s) => s.workerReady);

  const [models, setModels] = useState<ModelStatus[]>(
    MODEL_PRIORITY.map((id) => ({ id, status: "pending", pct: 0 }))
  );
  const [isDownloading, setIsDownloading] = useState(false);
  const [allDone, setAllDone] = useState(false);

  // Check which models are already cached
  useEffect(() => {
    if (!workerReady) return;
    send("get_models").then((res) => {
      if (res.status === "ok" && res.data?.cached) {
        const cached = res.data.cached as string[];
        setModels((prev) =>
          prev.map((m) => cached.includes(m.id) ? { ...m, status: "done", pct: 100 } : m)
        );
      }
    }).catch(() => {});
  }, [workerReady, send]);

  const handleDownloadAll = useCallback(async () => {
    setIsDownloading(true);
    const toDownload = models.filter((m) => m.status !== "done");

    for (const model of toDownload) {
      setModels((prev) =>
        prev.map((m) => m.id === model.id ? { ...m, status: "downloading", pct: 0 } : m)
      );

      try {
        const res = await send("download_model", { model: model.id });
        setModels((prev) =>
          prev.map((m) =>
            m.id === model.id
              ? { ...m, status: res.status === "ok" ? "done" : "error", pct: 100 }
              : m
          )
        );
      } catch {
        setModels((prev) =>
          prev.map((m) => m.id === model.id ? { ...m, status: "error", pct: 0 } : m)
        );
      }
    }

    setIsDownloading(false);
    setAllDone(true);
  }, [models, send]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-void-900/90 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-lg mx-4 bg-void-800 border border-void-600 rounded-2xl
          shadow-2xl overflow-hidden"
      >
        <div className="p-6">
          <h2 className="text-xl font-heading font-bold text-honey-300 mb-2">
            {t("model_first_run_title")}
          </h2>
          <p className="text-sm text-honey-500 mb-4">
            {t("model_first_run_desc")}
          </p>

          {/* Model list */}
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {models.map((model) => (
              <div
                key={model.id}
                className="flex items-center gap-3 p-2.5 rounded-lg bg-void-900/50 border border-void-700"
              >
                {/* Status icon */}
                <div className="w-5 h-5 flex items-center justify-center">
                  {model.status === "done" && <Check size={14} className="text-green-400" />}
                  {model.status === "error" && <X size={14} className="text-red-400" />}
                  {model.status === "downloading" && (
                    <Loader2 size={14} className="text-honey-400 animate-spin" />
                  )}
                  {model.status === "pending" && (
                    <Download size={14} className="text-honey-700" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-xs text-honey-200 truncate">{model.id}</p>
                </div>

                <span className="text-[10px] text-honey-700 font-mono">
                  {formatSize(MODEL_SIZES[model.id] ?? 0)}
                </span>

                {model.status === "downloading" && (
                  <span className="text-[10px] text-honey-400 font-mono w-8 text-right">
                    {model.pct}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="px-6 pb-6 flex gap-3">
          <Button
            variant="primary"
            size="lg"
            className="flex-1"
            icon={isDownloading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            disabled={isDownloading}
            onClick={allDone ? onClose : handleDownloadAll}
          >
            {allDone ? t("eula_continue") : t("model_download_now")}
          </Button>
          <Button variant="ghost" size="lg" onClick={onClose} disabled={isDownloading}>
            {t("model_skip")}
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
