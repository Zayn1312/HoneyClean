import { useRef, useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { listen } from "@tauri-apps/api/event";
import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import { open, save } from "@tauri-apps/plugin-dialog";
import {
  Eraser, Paintbrush, Undo2, Redo2, Save, RotateCcw,
  Upload, Wand2, X, Loader2, Plus, Download, RefreshCw, ChevronDown,
} from "lucide-react";
import { v4 as uuid } from "uuid";
import { useStore, type EditorFile } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { useWorker } from "../hooks/useWorker";
import { Button } from "../components/ui/Button";
import { Slider } from "../components/ui/Slider";
import { Select } from "../components/ui/Select";
import { MODEL_INFO } from "../lib/presets";

interface ModelData {
  id: string;
  filename: string;
  size: number;
  size_formatted: string;
  cached: boolean;
}

const SUPPORTED_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "bmp", "tiff"];

const SHADOW_OPTIONS = [
  { value: "none", label: "None" },
  { value: "drop", label: "Drop" },
  { value: "float", label: "Float" },
  { value: "contact", label: "Contact" },
];

const BG_OPTIONS = [
  { value: "transparent", label: "Transparent" },
  { value: "white", label: "White" },
  { value: "color", label: "Color" },
];

function pathsToEditorFiles(paths: string[]): EditorFile[] {
  return paths
    .filter((p) => {
      const ext = p.slice(p.lastIndexOf(".") + 1).toLowerCase();
      return SUPPORTED_EXTENSIONS.includes(ext);
    })
    .map((path) => ({
      id: uuid(),
      path,
      name: path.split(/[\\/]/).pop() || path,
      beforeSrc: convertFileSrc(path),
      afterSrc: null,
      outputPath: null,
      processing: false,
    }));
}

export function EditorPage() {
  const { t } = useI18n();
  const { send } = useWorker();
  const editor = useStore((s) => s.editor);
  const setEditor = useStore((s) => s.setEditor);
  const addEditorFiles = useStore((s) => s.addEditorFiles);
  const removeEditorFile = useStore((s) => s.removeEditorFile);
  const setActiveEditorIndex = useStore((s) => s.setActiveEditorIndex);
  const updateEditorFile = useStore((s) => s.updateEditorFile);
  const addToast = useStore((s) => s.addToast);

  const dividerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const stripRef = useRef<HTMLDivElement>(null);

  const [isDragOver, setIsDragOver] = useState(false);
  const [showModels, setShowModels] = useState(false);
  const [models, setModels] = useState<ModelData[]>([]);
  const [downloading, setDownloading] = useState<Set<string>>(new Set());
  const workerReady = useStore((s) => s.workerReady);

  const { files, activeIndex } = editor;
  const activeFile = files[activeIndex] ?? null;
  const hasFiles = files.length > 0;
  const cachedCount = models.filter((m) => m.cached).length;

  // ── Drag-drop via Tauri native events ──
  const addFiles = useCallback((paths: string[]) => {
    const items = pathsToEditorFiles(paths);
    if (items.length === 0) return;
    addEditorFiles(items);
  }, [addEditorFiles]);

  useEffect(() => {
    const unlistenDrop = listen<{ paths: string[] }>("tauri://drag-drop", (event) => {
      setIsDragOver(false);
      addFiles(event.payload.paths);
    });
    const unlistenEnter = listen("tauri://drag-enter", () => setIsDragOver(true));
    const unlistenLeave = listen("tauri://drag-leave", () => setIsDragOver(false));

    return () => {
      unlistenDrop.then((f) => f());
      unlistenEnter.then((f) => f());
      unlistenLeave.then((f) => f());
    };
  }, [addFiles]);

  // ── Model management ──
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

  const handleDownloadModel = useCallback(async (model: string) => {
    setDownloading((s) => new Set(s).add(model));
    try {
      const res = await send("download_model", { model });
      if (res.status === "ok") {
        addToast(`Downloaded: ${model}`, "success");
      } else {
        addToast(`Download failed: ${model}`, "error");
      }
    } catch {
      addToast(`Download failed: ${model}`, "error");
    }
    setDownloading((s) => { const n = new Set(s); n.delete(model); return n; });
    loadModels();
  }, [send, addToast, loadModels]);

  const handleDownloadAllModels = useCallback(async () => {
    const uncached = models.filter((m) => !m.cached);
    for (const m of uncached) {
      await handleDownloadModel(m.id);
    }
  }, [models, handleDownloadModel]);

  // ── File picker ──
  const handleBrowseFiles = useCallback(async () => {
    try {
      const result = await open({
        multiple: true,
        directory: false,
        filters: [{ name: "Images", extensions: SUPPORTED_EXTENSIONS }],
      });
      if (!result) return;
      const paths = Array.isArray(result) ? result : [result];
      addFiles(paths);
    } catch (e) {
      console.error("File pick failed:", e);
    }
  }, [addFiles]);

  // ── Divider drag ──
  const handleDrag = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      const container = containerRef.current;
      if (!container) return;

      const onMove = (ev: MouseEvent) => {
        const rect = container.getBoundingClientRect();
        const pct = ((ev.clientX - rect.left) / rect.width) * 100;
        setEditor({ dividerPos: Math.max(5, Math.min(95, pct)) });
      };

      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      };

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    },
    [setEditor]
  );

  // ── Remove BG for active file ──
  const handleRemoveBg = useCallback(async () => {
    if (!activeFile || activeFile.processing) return;
    updateEditorFile(activeFile.id, { processing: true });
    try {
      const res = await send("process_image", { path: activeFile.path });
      if (res.status === "ok") {
        const outputPath = res.data?.output as string | undefined;
        updateEditorFile(activeFile.id, {
          processing: false,
          outputPath: outputPath ?? null,
          afterSrc: outputPath ? convertFileSrc(outputPath) : null,
        });
      } else {
        updateEditorFile(activeFile.id, { processing: false });
        addToast(res.error ?? "Processing failed", "error");
      }
    } catch (e) {
      updateEditorFile(activeFile.id, { processing: false });
      addToast(`Error: ${e}`, "error");
    }
  }, [activeFile, send, updateEditorFile, addToast]);

  // ── Remove BG All ──
  const handleRemoveBgAll = useCallback(async () => {
    const currentFiles = useStore.getState().editor.files;
    for (const file of currentFiles) {
      if (file.afterSrc || file.processing) continue;
      updateEditorFile(file.id, { processing: true });
      try {
        const res = await send("process_image", { path: file.path });
        if (res.status === "ok") {
          const outputPath = res.data?.output as string | undefined;
          updateEditorFile(file.id, {
            processing: false,
            outputPath: outputPath ?? null,
            afterSrc: outputPath ? convertFileSrc(outputPath) : null,
          });
        } else {
          updateEditorFile(file.id, { processing: false });
        }
      } catch {
        updateEditorFile(file.id, { processing: false });
      }
    }
    addToast(t("status_done", { count: currentFiles.length }), "success");
  }, [send, updateEditorFile, addToast, t]);

  // ── Save ──
  const handleSave = useCallback(async () => {
    if (!activeFile) return;
    const srcPath = activeFile.outputPath ?? activeFile.path;
    const ext = srcPath.slice(srcPath.lastIndexOf(".") + 1).toLowerCase();
    try {
      const dst = await save({
        defaultPath: activeFile.name,
        filters: [{ name: "Image", extensions: [ext] }],
      });
      if (!dst) return;
      await invoke("copy_file", { src: srcPath, dst });
      addToast(t("editor_save_success"), "success");
    } catch (e) {
      addToast(`Save failed: ${e}`, "error");
    }
  }, [activeFile, addToast, t]);

  // ── Reset active file ──
  const handleReset = useCallback(() => {
    if (!activeFile) return;
    updateEditorFile(activeFile.id, { afterSrc: null, outputPath: null });
  }, [activeFile, updateEditorFile]);

  // ── Render ──

  // Empty state — drop zone
  if (!hasFiles) {
    return (
      <div
        className="h-full flex flex-col" style={{ padding: 20 }}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragOver(false); }}
      >
        <motion.button
          onClick={handleBrowseFiles}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className={`flex-1 flex flex-col items-center justify-center gap-4
            border-2 border-dashed rounded-xl transition-colors cursor-pointer min-h-[200px]
            ${isDragOver
              ? "border-honey-400 bg-honey-500/10"
              : "border-void-500 hover:border-honey-600 hover:bg-void-800/30"
            }`}
        >
          <Upload size={40} className={isDragOver ? "text-honey-400" : "text-honey-600"} />
          <p className="text-honey-400 text-sm">{t("editor_drop_zone")}</p>
          <p className="text-honey-700 text-xs">PNG, JPG, JPEG, WEBP, BMP, TIFF</p>
        </motion.button>
      </div>
    );
  }

  const hasBefore = !!activeFile?.beforeSrc;
  const hasAfter = !!activeFile?.afterSrc;

  return (
    <div
      className="h-full flex flex-col gap-3"
      style={{ padding: 20 }}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setIsDragOver(false); }}
    >
      {/* Toolbar — glassmorphism */}
      <div
        className="flex items-center gap-3 flex-wrap rounded-xl px-4 border border-void-600/40"
        style={{
          height: 52,
          background: "rgba(20, 20, 32, 0.6)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
        }}
      >
        {/* Tool selection */}
        <div className="flex items-center gap-1 bg-void-800/60 rounded-lg p-0.5">
          <button
            onClick={() => setEditor({ tool: "erase" })}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors
              ${editor.tool === "erase"
                ? "bg-honey-500/20 text-honey-300"
                : "text-honey-600 hover:text-honey-400"}`}
          >
            <Eraser size={14} />
            {t("erase")}
          </button>
          <button
            onClick={() => setEditor({ tool: "restore" })}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors
              ${editor.tool === "restore"
                ? "bg-honey-500/20 text-honey-300"
                : "text-honey-600 hover:text-honey-400"}`}
          >
            <Paintbrush size={14} />
            {t("restore")}
          </button>
        </div>

        <div className="w-40">
          <Slider
            label={t("brush_size")}
            value={editor.brushSize}
            min={1}
            max={100}
            onChange={(v) => setEditor({ brushSize: v })}
            suffix="px"
          />
        </div>

        <div className="w-40">
          <Slider
            label={t("edge_feather")}
            value={editor.feather}
            min={0}
            max={20}
            onChange={(v) => setEditor({ feather: v })}
            suffix="px"
          />
        </div>

        <div className="w-px h-6 bg-void-600" />

        <Button size="sm" variant="ghost" icon={<Undo2 size={14} />}
          disabled={editor.undoStack.length === 0}>
          {t("undo")}
        </Button>
        <Button size="sm" variant="ghost" icon={<Redo2 size={14} />}
          disabled={editor.redoStack.length === 0}>
          {t("redo")}
        </Button>

        <div className="w-px h-6 bg-void-600" />

        {/* Remove BG */}
        <Button
          size="sm"
          variant="primary"
          icon={activeFile?.processing ? <Loader2 size={14} className="animate-spin" /> : <Wand2 size={14} />}
          onClick={handleRemoveBg}
          disabled={!activeFile || activeFile.processing}
        >
          {activeFile?.processing ? t("editor_processing") : t("editor_remove_bg")}
        </Button>

        <Button
          size="sm"
          variant="secondary"
          icon={<Wand2 size={14} />}
          onClick={handleRemoveBgAll}
        >
          {t("editor_remove_bg_all")}
        </Button>

        <div className="flex-1" />

        <Button size="sm" variant="ghost" icon={<Plus size={14} />} onClick={handleBrowseFiles}>
          {t("editor_add_files")}
        </Button>
        <button
          onClick={() => setShowModels(!showModels)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors
            ${showModels
              ? "bg-honey-500/20 text-honey-300"
              : "text-honey-600 hover:text-honey-400"}`}
        >
          <Download size={14} />
          {t("editor_models")}
          <span className="text-[10px] text-honey-700">({cachedCount}/{models.length})</span>
          <ChevronDown size={10} className={`transition-transform ${showModels ? "rotate-180" : ""}`} />
        </button>
        <Button size="sm" variant="ghost" icon={<RotateCcw size={14} />} onClick={handleReset}
          disabled={!activeFile?.afterSrc}>
          {t("reset")}
        </Button>
        <Button size="sm" variant="primary" icon={<Save size={14} />} onClick={handleSave}
          disabled={!activeFile}>
          {t("save")}
        </Button>
      </div>

      {/* Model download panel */}
      <AnimatePresence>
        {showModels && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-lg border border-void-600 bg-void-800/50 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-honey-300 font-medium">
                  {t("editor_models_ready", { count: cachedCount })}
                </span>
                <Button
                  size="sm"
                  icon={<Download size={12} />}
                  onClick={handleDownloadAllModels}
                  disabled={downloading.size > 0 || cachedCount === models.length}
                >
                  {t("editor_download_all")}
                </Button>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {models.map((model) => {
                  const info = MODEL_INFO[model.id];
                  const isDown = downloading.has(model.id);
                  return (
                    <div key={model.id}
                      className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-void-900/50 border border-void-700">
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] text-honey-200 truncate">
                          {info ? t(info.name_key) : model.id}
                        </p>
                        <p className="text-[9px] text-honey-700">{model.size_formatted}</p>
                      </div>
                      {model.cached ? (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-500/15 text-green-400 font-medium shrink-0">
                          ✓
                        </span>
                      ) : (
                        <button
                          onClick={() => handleDownloadModel(model.id)}
                          disabled={isDown}
                          className="p-1 rounded hover:bg-honey-500/15 text-honey-500
                            disabled:opacity-40 transition-colors shrink-0"
                        >
                          {isDown ? <RefreshCw size={12} className="animate-spin" /> : <Download size={12} />}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Canvas area */}
      <div
        ref={containerRef}
        className="flex-1 relative rounded-xl overflow-hidden border border-void-600 bg-void-900"
        style={{
          backgroundImage: "repeating-conic-gradient(#1a1a1a 0% 25%, #222 0% 50%)",
          backgroundSize: "24px 24px",
        }}
      >
        {hasBefore && hasAfter ? (
          <>
            {/* Before image */}
            <div
              className="absolute inset-0"
              style={{ clipPath: `inset(0 ${100 - editor.dividerPos}% 0 0)` }}
            >
              <img
                src={activeFile!.beforeSrc}
                alt="Before"
                className="w-full h-full object-contain"
              />
              <span className="absolute top-3 left-3 px-2 py-1 text-[10px] font-bold bg-void-900/70 text-honey-400 rounded">
                {t("before_label")}
              </span>
            </div>

            {/* After image */}
            <div
              className="absolute inset-0"
              style={{ clipPath: `inset(0 0 0 ${editor.dividerPos}%)` }}
            >
              <img
                src={activeFile!.afterSrc!}
                alt="After"
                className="w-full h-full object-contain"
              />
              <span className="absolute top-3 right-3 px-2 py-1 text-[10px] font-bold bg-void-900/70 text-honey-400 rounded">
                {t("after_label")}
              </span>
            </div>

            {/* Divider */}
            <div
              ref={dividerRef}
              onMouseDown={handleDrag}
              className="absolute top-0 bottom-0 w-0.5 bg-honey-400 cursor-col-resize z-10"
              style={{ left: `${editor.dividerPos}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2
                w-6 h-6 rounded-full bg-honey-500 border-2 border-void-900
                flex items-center justify-center cursor-col-resize">
                <span className="text-void-900 text-[10px] font-bold">⟷</span>
              </div>
            </div>
          </>
        ) : hasBefore ? (
          <>
            <img
              src={activeFile!.beforeSrc}
              alt={activeFile!.name}
              className="w-full h-full object-contain"
            />
            {activeFile?.processing && (
              <div className="absolute inset-0 flex items-center justify-center bg-void-900/50">
                <Loader2 size={32} className="text-honey-400 animate-spin" />
              </div>
            )}
            {!activeFile?.processing && !hasAfter && (
              <span className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1.5
                text-xs text-honey-600 bg-void-900/70 rounded">
                {t("editor_no_output")}
              </span>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-honey-700 text-sm">
            {t("editor_drop_zone")}
          </div>
        )}
      </div>

      {/* File navigation strip */}
      <div
        ref={stripRef}
        className="flex items-center gap-2 overflow-x-auto py-1 px-0.5
          scrollbar-thin scrollbar-thumb-void-600 scrollbar-track-transparent"
      >
        <AnimatePresence mode="popLayout">
          {files.map((file, i) => (
            <motion.div
              key={file.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              onClick={() => setActiveEditorIndex(i)}
              className={`relative group flex-shrink-0 rounded-lg overflow-hidden cursor-pointer
                border-2 transition-colors
                ${i === activeIndex
                  ? "border-honey-400"
                  : "border-void-600 hover:border-void-500"
                }`}
              style={{ width: 72, height: 72 }}
            >
              <img
                src={file.afterSrc ?? file.beforeSrc}
                alt={file.name}
                className="w-full h-full object-cover"
                loading="lazy"
              />

              {/* Processing spinner */}
              {file.processing && (
                <div className="absolute inset-0 flex items-center justify-center bg-void-900/60">
                  <Loader2 size={16} className="text-honey-400 animate-spin" />
                </div>
              )}

              {/* Processed check */}
              {file.afterSrc && !file.processing && (
                <div className="absolute top-0.5 right-0.5 w-4 h-4 rounded-full
                  bg-green-500/80 flex items-center justify-center">
                  <span className="text-[8px] text-white font-bold">✓</span>
                </div>
              )}

              {/* Remove button */}
              <button
                onClick={(e) => { e.stopPropagation(); removeEditorFile(file.id); }}
                className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full
                  bg-void-900/70 text-honey-600 hover:text-red-400
                  flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X size={10} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Bottom controls */}
      <div className="flex items-center gap-4">
        <Select
          label="Shadow"
          value={editor.shadowType}
          options={SHADOW_OPTIONS}
          onChange={(v) => setEditor({ shadowType: v as typeof editor.shadowType })}
        />
        <Select
          label="Background"
          value={editor.bgType}
          options={BG_OPTIONS}
          onChange={(v) => setEditor({ bgType: v as typeof editor.bgType })}
        />
        {editor.bgType === "color" && (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-honey-300">Color</label>
            <input
              type="color"
              value={editor.bgColor}
              onChange={(e) => setEditor({ bgColor: e.target.value })}
              className="w-10 h-9 rounded border border-void-500 cursor-pointer bg-transparent"
            />
          </div>
        )}
      </div>
    </div>
  );
}
