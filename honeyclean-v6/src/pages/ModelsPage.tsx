import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Download, Trash2, RefreshCw, HardDrive } from "lucide-react";
import { useStore } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { useWorker } from "../hooks/useWorker";
import { Button } from "../components/ui/Button";
import { MODEL_INFO } from "../lib/presets";

interface ModelData {
  id: string;
  filename: string;
  size: number;
  size_formatted: string;
  cached: boolean;
}

export function ModelsPage() {
  const { t } = useI18n();
  const { send } = useWorker();
  const workerReady = useStore((s) => s.workerReady);
  const addToast = useStore((s) => s.addToast);

  const [models, setModels] = useState<ModelData[]>([]);
  const [downloading, setDownloading] = useState<Set<string>>(new Set());
  const [updateInfo, setUpdateInfo] = useState<{
    available: boolean;
    installed: string;
    latest: string;
  } | null>(null);

  const loadModels = useCallback(async () => {
    if (!workerReady) return;
    try {
      const res = await send("get_models");
      if (res.status === "ok" && res.data?.models) {
        setModels(res.data.models as ModelData[]);
      }
    } catch (e) {
      console.error("Failed to load models:", e);
    }
  }, [workerReady, send]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  useEffect(() => {
    if (!workerReady) return;
    send("check_updates").then((res) => {
      if (res.status === "ok" && res.data) {
        setUpdateInfo({
          available: res.data.update_available as boolean,
          installed: res.data.installed as string,
          latest: res.data.latest as string,
        });
      }
    }).catch(() => {});
  }, [workerReady, send]);

  const handleDownload = useCallback(async (model: string) => {
    setDownloading((s) => new Set(s).add(model));
    try {
      const res = await send("download_model", { model });
      if (res.status === "ok") {
        addToast(`Downloaded: ${model}`, "success");
      } else {
        addToast(t("model_download_error", { model }), "error");
      }
    } catch {
      addToast(t("model_download_error", { model }), "error");
    }
    setDownloading((s) => {
      const next = new Set(s);
      next.delete(model);
      return next;
    });
    loadModels();
  }, [send, addToast, loadModels, t]);

  const handleDelete = useCallback(async (model: string) => {
    const res = await send("delete_model", { model });
    if (res.status === "ok") {
      addToast(`Deleted: ${model}`, "info");
    }
    loadModels();
  }, [send, addToast, loadModels]);

  const handleCleanup = useCallback(async () => {
    const res = await send("cleanup_temp");
    if (res.status === "ok") {
      const count = res.data?.cleaned as number ?? 0;
      addToast(t("model_cleanup_done", { count }), "info");
    }
  }, [send, addToast, t]);

  const handleDownloadPriority = useCallback(async () => {
    const priority = models.filter(
      (m) => !m.cached && ["birefnet-general", "isnet-general-use", "silueta", "isnet-anime"].includes(m.id)
    );
    for (const m of priority) {
      await handleDownload(m.id);
    }
  }, [models, handleDownload]);

  return (
    <div className="h-full flex flex-col p-4 gap-4 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-heading font-bold text-honey-300">
          {t("model_page_title")}
        </h2>
        <div className="flex gap-2">
          <Button size="sm" icon={<Download size={14} />} onClick={handleDownloadPriority}>
            {t("model_download_all")}
          </Button>
          <Button size="sm" variant="ghost" icon={<HardDrive size={14} />}
            onClick={handleCleanup}>
            {t("model_cleanup")}
          </Button>
        </div>
      </div>

      {/* Update banner */}
      {updateInfo?.available && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-honey-500/10 border border-honey-500/30">
          <RefreshCw size={16} className="text-honey-400" />
          <span className="text-sm text-honey-300">
            {t("model_update_available", { latest: updateInfo.latest })}
          </span>
          <span className="text-xs text-honey-600">
            Installed: {updateInfo.installed}
          </span>
        </div>
      )}

      {/* Model cards grid */}
      <div className="grid grid-cols-3 gap-3">
        {models.map((model) => {
          const info = MODEL_INFO[model.id];
          const isDownloading = downloading.has(model.id);

          return (
            <motion.div
              key={model.id}
              whileHover={{ borderColor: "rgba(217, 163, 60, 0.3)" }}
              className="rounded-lg border border-void-600 bg-void-800/50 p-3 flex flex-col gap-2"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-honey-200 truncate">
                    {info ? t(info.name_key) : model.id}
                  </h3>
                  <p className="text-[11px] text-honey-600 mt-0.5 line-clamp-2">
                    {info ? t(info.desc_key) : ""}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between mt-auto">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium
                    ${model.cached
                      ? "bg-green-500/15 text-green-400"
                      : "bg-void-700 text-honey-700"
                    }`}>
                    {model.cached ? t("model_cached") : t("model_not_cached")}
                  </span>
                  <span className="text-[10px] text-honey-700">
                    {model.size_formatted}
                  </span>
                </div>

                <div className="flex gap-1">
                  {!model.cached ? (
                    <button
                      onClick={() => handleDownload(model.id)}
                      disabled={isDownloading}
                      className="p-1.5 rounded-md hover:bg-honey-500/15 text-honey-500
                        disabled:opacity-40 transition-colors"
                    >
                      {isDownloading ? (
                        <RefreshCw size={14} className="animate-spin" />
                      ) : (
                        <Download size={14} />
                      )}
                    </button>
                  ) : (
                    <button
                      onClick={() => handleDelete(model.id)}
                      className="p-1.5 rounded-md hover:bg-red-500/15 text-red-400
                        transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
