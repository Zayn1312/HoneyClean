import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Download, Trash2, RefreshCw, HardDrive } from "lucide-react";
import { useStore } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { useWorker } from "../hooks/useWorker";
import { Button } from "../components/ui/Button";
import { Tooltip } from "../components/ui/Tooltip";
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
    <div className="h-full flex flex-col gap-4 overflow-y-auto" style={{ padding: 20 }}>
      <div className="flex items-center justify-between">
        <h2 className="font-heading font-semibold text-honey-300" style={{ fontSize: 22 }}>
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
        <div className="flex items-center gap-3 p-3 rounded-xl bg-honey-500/10 border border-honey-500/30">
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
      <div className="grid grid-cols-3" style={{ gap: 12 }}>
        {models.map((model) => {
          const info = MODEL_INFO[model.id];
          const isDownloading = downloading.has(model.id);

          return (
            <motion.div
              key={model.id}
              whileHover={{ borderColor: "rgba(217, 163, 60, 0.3)" }}
              className="border border-void-600/40 bg-void-800/40 flex flex-col"
              style={{ borderRadius: 12, padding: 16 }}
            >
              <div className="flex-1 min-w-0 mb-3">
                <h3 className="font-bold text-honey-200 truncate" style={{ fontSize: 15 }}>
                  {info ? t(info.name_key) : model.id}
                </h3>
                <p className="text-honey-600 mt-1 line-clamp-2" style={{ fontSize: 13 }}>
                  {info ? t(info.desc_key) : ""}
                </p>
              </div>

              <div className="flex items-center gap-2 mb-3">
                <span className={`text-[11px] px-2 py-0.5 rounded-md font-medium
                  ${model.cached
                    ? "bg-honey-500/15 text-honey-400"
                    : "bg-void-700 text-honey-700"
                  }`}>
                  {model.cached ? t("model_cached") : t("model_not_cached")}
                </span>
                <span className="text-[11px] text-honey-700 font-mono">
                  {model.size_formatted}
                </span>
              </div>

              <div className="mt-auto">
                {!model.cached ? (
                  <Tooltip content={info ? t(info.name_key) : model.id} detail={`${model.size_formatted} — Klicken zum Herunterladen.`} position="bottom">
                    <button
                      onClick={() => handleDownload(model.id)}
                      disabled={isDownloading}
                      className="w-full flex items-center justify-center gap-2 py-2 rounded-lg
                        bg-honey-500/10 hover:bg-honey-500/20 text-honey-400
                        disabled:opacity-40 transition-colors text-[13px] font-medium"
                    >
                      {isDownloading ? (
                        <><RefreshCw size={14} className="animate-spin" /> Downloading...</>
                      ) : (
                        <><Download size={14} /> Download</>
                      )}
                    </button>
                  </Tooltip>
                ) : (
                  <button
                    onClick={() => handleDelete(model.id)}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg
                      bg-void-700/50 hover:bg-red-500/10 text-honey-700 hover:text-red-400
                      transition-colors text-[13px]"
                  >
                    <Trash2 size={14} /> Delete
                  </button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
