import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { listen } from "@tauri-apps/api/event";
import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { Upload, FolderPlus, Trash2, Play, Pause, Square, Image, Film } from "lucide-react";
import { v4 as uuid } from "uuid";
import { useStore, type QueueItem, type QualityPreset } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { useWorker } from "../hooks/useWorker";
import { Button } from "../components/ui/Button";
import { Select } from "../components/ui/Select";
import { Toggle } from "../components/ui/Toggle";
import { Tooltip } from "../components/ui/Tooltip";
import { isVideoFile, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS } from "../lib/presets";

const QUALITY_OPTIONS: { value: QualityPreset; label: string; tooltip: string; detail: string }[] = [
  { value: "fast", label: "Fast", tooltip: "Schnellstes Modell.", detail: "Gut für einfache Motive mit klarem Kontrast." },
  { value: "balanced", label: "Balanced", tooltip: "Ausgewogene Geschwindigkeit und Qualität.", detail: "Empfohlen für die meisten Bilder." },
  { value: "quality", label: "Quality", tooltip: "BiRefNet — bestes Modell.", detail: "Für Haare, Fell und komplexe Kanten." },
  { value: "anime", label: "Anime", tooltip: "Optimiert für Illustrationen.", detail: "Anime, Manga und Tierfotografie." },
  { value: "portrait", label: "Portrait", tooltip: "Speziell für Personenfotos.", detail: "Erkennt Haare und Haut präzise." },
];

const PLATFORM_OPTIONS = [
  { value: "None", label: "No Platform" },
  { value: "Amazon", label: "Amazon" },
  { value: "Shopify", label: "Shopify" },
  { value: "Etsy", label: "Etsy" },
  { value: "eBay", label: "eBay" },
  { value: "Instagram", label: "Instagram" },
];

const SORT_OPTIONS = [
  { value: "name", label: "Name A–Z" },
  { value: "size", label: "Size" },
  { value: "folder", label: "Folder" },
];

const SUPPORTED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'zip'];
const ALL_VALID_EXTENSIONS = new Set([
  ...IMAGE_EXTENSIONS, ...VIDEO_EXTENSIONS, '.zip',
]);

function isSupportedFile(path: string): boolean {
  const ext = path.slice(path.lastIndexOf('.')).toLowerCase();
  return ALL_VALID_EXTENSIONS.has(ext);
}

function pathsToQueueItems(paths: string[]): QueueItem[] {
  return paths.filter(isSupportedFile).map((path) => {
    const ext = path.slice(path.lastIndexOf('.')).toLowerCase();
    const isImage = !isVideoFile(path) && ext !== '.zip';
    return {
      id: uuid(),
      path,
      name: path.split(/[\\/]/).pop() || path,
      size: 0,
      type: isVideoFile(path) ? "video" as const : "image" as const,
      status: "pending" as const,
      selected: false,
      thumbnail: isImage ? convertFileSrc(path) : undefined,
    };
  });
}

export function QueuePage() {
  const { t } = useI18n();
  const { send } = useWorker();
  const queue = useStore((s) => s.queue);
  const addToQueue = useStore((s) => s.addToQueue);
  const removeFromQueue = useStore((s) => s.removeFromQueue);
  const clearQueue = useStore((s) => s.clearQueue);
  const toggleSelectItem = useStore((s) => s.toggleSelectItem);
  const selectAll = useStore((s) => s.selectAll);
  const deselectAll = useStore((s) => s.deselectAll);
  const sortQueue = useStore((s) => s.sortQueue);
  const updateQueueItem = useStore((s) => s.updateQueueItem);
  const processingState = useStore((s) => s.processingState);
  const setProcessingState = useStore((s) => s.setProcessingState);
  const setProgress = useStore((s) => s.setProgress);
  const setCurrentFile = useStore((s) => s.setCurrentFile);
  const setSpeed = useStore((s) => s.setSpeed);
  const setEta = useStore((s) => s.setEta);
  const qualityPreset = useStore((s) => s.qualityPreset);
  const setQualityPreset = useStore((s) => s.setQualityPreset);
  const platformPreset = useStore((s) => s.platformPreset);
  const setPlatformPreset = useStore((s) => s.setPlatformPreset);
  const skipProcessed = useStore((s) => s.skipProcessed);
  const setSkipProcessed = useStore((s) => s.setSkipProcessed);
  const addToast = useStore((s) => s.addToast);
  const setProvider = useStore((s) => s.setProvider);
  const setIsGpu = useStore((s) => s.setIsGpu);

  const [isDragOver, setIsDragOver] = useState(false);

  const selectedIds = queue.filter((i) => i.selected).map((i) => i.id);
  const hasSelected = selectedIds.length > 0;

  // ── Tauri native drag-drop listener ──
  const addFilesToQueue = useCallback((paths: string[]) => {
    const items = pathsToQueueItems(paths);
    if (items.length === 0) return;
    addToQueue(items);
    addToast(t("added_to_queue", { count: items.length }), "success");
  }, [addToQueue, addToast, t]);

  useEffect(() => {
    const unlistenDrop = listen<{ paths: string[] }>('tauri://drag-drop', (event) => {
      setIsDragOver(false);
      addFilesToQueue(event.payload.paths);
    });
    const unlistenEnter = listen('tauri://drag-enter', () => setIsDragOver(true));
    const unlistenLeave = listen('tauri://drag-leave', () => setIsDragOver(false));

    return () => {
      unlistenDrop.then((f) => f());
      unlistenEnter.then((f) => f());
      unlistenLeave.then((f) => f());
    };
  }, [addFilesToQueue]);

  // ── File picker via Tauri dialog plugin ──
  const handleBrowseFiles = useCallback(async () => {
    try {
      const result = await open({
        multiple: true,
        directory: false,
        filters: [{
          name: 'Images',
          extensions: SUPPORTED_EXTENSIONS,
        }],
      });
      if (!result) return;
      const paths = Array.isArray(result) ? result : [result];
      addFilesToQueue(paths);
    } catch (e) {
      console.error("File pick failed:", e);
    }
  }, [addFilesToQueue]);

  // ── Folder picker: select folder → scan for images recursively ──
  const handleBrowseFolder = useCallback(async () => {
    try {
      const folder = await open({
        multiple: false,
        directory: true,
        recursive: true,
      });
      if (!folder) return;
      const dirPath = typeof folder === "string" ? folder : folder[0];
      console.log("[HoneyClean] Folder selected:", dirPath);
      const files = await invoke<string[]>("list_dir_images", { path: dirPath });
      console.log("[HoneyClean] Found files:", files?.length);
      if (!files?.length) {
        addToast(t("no_images_found") || "No images found in folder", "warning");
        return;
      }
      addFilesToQueue(files);
    } catch (e) {
      console.error("[HoneyClean] Folder pick failed:", e);
      addToast(`Folder error: ${e}`, "error");
    }
  }, [addFilesToQueue, addToast, t]);

  const handleStart = useCallback(async () => {
    if (useStore.getState().processingState === "processing") return;
    setProcessingState("processing");
    const startTime = Date.now();

    // Snapshot the queue at start — read from store, not stale closure
    const items = useStore.getState().queue;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (useStore.getState().processingState === "stopped") break;

      // Wait while paused
      while (useStore.getState().processingState === "paused") {
        await new Promise((r) => setTimeout(r, 100));
      }
      if (useStore.getState().processingState === "stopped") break;

      updateQueueItem(item.id, { status: "processing" });
      setCurrentFile(item.name);
      setProgress(i / items.length);

      try {
        const action = item.type === "video" ? "process_video" : "process_image";
        const res = await send(action, {
          path: item.path,
          skip_existing: useStore.getState().skipProcessed,
        });

        if (res.status === "ok") {
          const elapsed = res.data?.elapsed as number | undefined;
          const skipped = res.data?.skipped as boolean | undefined;
          const outputPath = res.data?.output as string | undefined;
          const providerLabel = res.data?.provider as string | undefined;
          const isGpuResult = res.data?.is_gpu as boolean | undefined;
          if (providerLabel) setProvider(providerLabel);
          if (isGpuResult !== undefined) setIsGpu(isGpuResult);
          updateQueueItem(item.id, {
            status: skipped ? "skipped" : "done",
            elapsed: elapsed ?? 0,
            outputPath: outputPath ?? undefined,
            thumbnail: outputPath ? convertFileSrc(outputPath) : item.thumbnail,
          });
        } else {
          updateQueueItem(item.id, { status: "error" });
        }
      } catch (e) {
        updateQueueItem(item.id, { status: "error" });
      }

      // Update speed/ETA
      const elapsed = (Date.now() - startTime) / 1000;
      const done = i + 1;
      const remaining = items.length - done;
      const avgPer = elapsed / done;
      setSpeed(done / (elapsed / 60));
      const etaSec = remaining * avgPer;
      setEta(etaSec > 60 ? `${Math.floor(etaSec / 60)}m ${Math.floor(etaSec % 60)}s` : `${Math.floor(etaSec)}s`);
    }

    setProgress(1);
    setProcessingState("idle");
    setCurrentFile("");
    setEta("");

    const doneCount = useStore.getState().queue.filter((i) => i.status === "done").length;
    const failedCount = useStore.getState().queue.filter((i) => i.status === "error").length;
    if (doneCount > 0 || failedCount > 0) {
      addToast(t("status_done", { count: doneCount }), doneCount > 0 ? "success" : "warning");
    }
  }, [send, updateQueueItem, setProcessingState, setProgress, setCurrentFile, setSpeed, setEta, addToast, t]);

  const handlePause = useCallback(() => {
    setProcessingState(processingState === "paused" ? "processing" : "paused");
  }, [processingState, setProcessingState]);

  const handleStop = useCallback(() => {
    setProcessingState("stopped");
  }, [setProcessingState]);

  const progress = useStore((s) => s.progress);

  return (
    <div
      className="h-full flex flex-col gap-3"
      style={{ padding: 20 }}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setIsDragOver(false); }}
    >
      {/* Toolbar — ALWAYS visible */}
      <div className="flex items-center gap-2 flex-wrap px-2 rounded-lg shrink-0"
        style={{ height: 48, background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <Button size="sm" icon={<Upload size={14} />} onClick={handleBrowseFiles}>
          {t("file_select")}
        </Button>
        <Button size="sm" icon={<FolderPlus size={14} />} onClick={handleBrowseFolder}>
          {t("add_folder")}
        </Button>
        {queue.length > 0 && (
          <Button size="sm" variant="ghost" onClick={clearQueue}>
            {t("clear_queue")}
          </Button>
        )}

        <div className="w-px h-5 bg-void-600 mx-1" />

        {queue.length > 0 && (
          <>
            <Button size="sm" variant="ghost"
              onClick={() => hasSelected ? deselectAll() : selectAll()}>
              {hasSelected ? t("deselect_all") : t("select_all")}
            </Button>
            {hasSelected && (
              <Button size="sm" variant="ghost" icon={<Trash2 size={14} />}
                onClick={() => removeFromQueue(selectedIds)}>
                {t("remove_selected")}
              </Button>
            )}

            <div className="w-px h-5 bg-void-600 mx-1" />

            <Select
              value="name"
              options={SORT_OPTIONS}
              onChange={(v) => sortQueue(v as "name" | "size" | "folder")}
            />
          </>
        )}

        <Tooltip content="Verarbeitete überspringen" detail="Bilder die bereits verarbeitet wurden werden ignoriert." position="bottom">
          <Toggle
            label={t("skip_existing")}
            checked={skipProcessed}
            onChange={setSkipProcessed}
          />
        </Tooltip>
      </div>

      {/* Quality + Platform presets — ALWAYS visible */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="flex items-center gap-2">
          {QUALITY_OPTIONS.map((opt) => (
            <Tooltip key={opt.value} content={opt.tooltip} detail={opt.detail} position="bottom">
              <button
                onClick={() => setQualityPreset(opt.value)}
                className={`px-3 rounded-md font-medium transition-colors
                  ${qualityPreset === opt.value
                    ? "bg-honey-500/20 text-honey-300 border border-honey-500/40"
                    : "text-honey-600 hover:text-honey-400 border border-transparent"
                  }`}
                style={{ height: 30, fontSize: 13, borderRadius: 6 }}
              >
                {opt.label}
              </button>
            </Tooltip>
          ))}
        </div>
        <Select
          value={platformPreset}
          options={PLATFORM_OPTIONS}
          onChange={setPlatformPreset}
        />
      </div>

      {/* Content area */}
      {queue.length === 0 ? (
        <motion.button
          onClick={handleBrowseFiles}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className={`flex-1 flex flex-col items-center justify-center gap-4
            border-2 border-dashed rounded-xl
            transition-colors cursor-pointer min-h-[200px]
            ${isDragOver
              ? "border-honey-400 bg-honey-500/10 scale-[1.01]"
              : "border-void-500 hover:border-honey-600 hover:bg-void-800/30"
            }`}
        >
          <Upload size={40} className={isDragOver ? "text-honey-400" : "text-honey-600"} />
          <p className="text-honey-400 text-sm">{isDragOver ? t("drop_zone_active") || "Drop files here!" : t("drop_zone")}</p>
          <p className="text-honey-700 text-xs">{t("empty_formats")}</p>
          <p className="text-honey-800 text-[11px] italic">{t("empty_tip")}</p>
        </motion.button>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-5 gap-3">
            <AnimatePresence mode="popLayout">
              {queue.map((item) => (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  onClick={() => toggleSelectItem(item.id)}
                  className={`relative group overflow-hidden cursor-pointer
                    border transition-all
                    ${item.selected
                      ? "border-honey-400 bg-honey-500/10"
                      : "border-[rgba(255,255,255,0.06)] hover:border-[rgba(245,158,11,0.3)] hover:shadow-[0_0_16px_rgba(245,158,11,0.08)]"
                    }`}
                  style={{ width: 160, height: 170, borderRadius: 12, background: "rgba(20,20,32,0.8)", padding: 8 }}
                >
                  {/* Thumbnail */}
                  <div className="w-full h-[110px] flex items-center justify-center"
                    style={item.thumbnail ? {
                      backgroundImage: 'repeating-conic-gradient(#1a1a2e 0% 25%, #252540 0% 50%)',
                      backgroundSize: '16px 16px',
                    } : undefined}
                  >
                    {item.thumbnail ? (
                      <img
                        src={item.thumbnail}
                        alt={item.name}
                        className="w-full h-full object-contain"
                        loading="lazy"
                      />
                    ) : item.type === "video" ? (
                      <Film size={28} className="text-void-500" />
                    ) : (
                      <Image size={28} className="text-void-500" />
                    )}
                  </div>

                  {/* Type badge */}
                  <div className={`absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded text-[9px]
                    font-bold uppercase
                    ${item.type === "video"
                      ? "bg-purple-500/80 text-white"
                      : "bg-honey-500/80 text-void-900"
                    }`}>
                    {item.type === "video" ? "VID" : "IMG"}
                  </div>

                  {/* Info bar */}
                  <div className="pt-1.5">
                    <p className="text-[13px] text-[#A0A0C0] truncate">{item.name}</p>
                    <p className={`text-[11px] mt-0.5 ${
                      item.status === "done" ? "text-green-400" :
                      item.status === "error" ? "text-red-400" :
                      item.status === "processing" ? "text-yellow-400" :
                      item.status === "skipped" ? "text-honey-700" :
                      "text-honey-700"
                    }`}>
                      {item.status === "done" && `✓ Done ${item.elapsed ? `${item.elapsed}s` : ""}`}
                      {item.status === "error" && "✗ Failed"}
                      {item.status === "processing" && "⏳ Processing…"}
                      {item.status === "skipped" && "⏭ Skipped"}
                      {item.status === "pending" && "Pending"}
                      {item.status === "paused" && "⏸ Paused"}
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Progress bar — ALWAYS visible when processing */}
      {processingState !== "idle" && (
        <div className="w-full h-1.5 bg-void-700 rounded-full overflow-hidden shrink-0">
          <motion.div
            className="h-full bg-honey-500 rounded-full"
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      )}

      {/* Action bar — ALWAYS visible */}
      <div className="flex items-center gap-3 shrink-0">
        <Tooltip content="Startet die Verarbeitung" detail="Alle Bilder in der Warteschlange werden verarbeitet." position="top">
          <Button
            variant="primary"
            size="lg"
            icon={<Play size={18} />}
            onClick={handleStart}
            disabled={processingState === "processing" || queue.length === 0}
          >
            {t("btn_start")}
          </Button>
        </Tooltip>
        <Tooltip content="Pausiert nach dem aktuellen Bild." detail="Kann fortgesetzt werden." position="top">
          <Button
            variant="secondary"
            size="lg"
            icon={<Pause size={18} />}
            onClick={handlePause}
            disabled={processingState === "idle" || processingState === "stopped"}
          >
            {processingState === "paused" ? t("btn_resume") : t("btn_pause")}
          </Button>
        </Tooltip>
        <Tooltip content="Stoppt sofort." detail="Bricht die Verarbeitung ab." position="top">
          <Button
            variant="danger"
            size="lg"
            icon={<Square size={18} />}
            onClick={handleStop}
            disabled={processingState === "idle" || processingState === "stopped"}
          >
            {t("btn_stop")}
          </Button>
        </Tooltip>
      </div>
    </div>
  );
}
