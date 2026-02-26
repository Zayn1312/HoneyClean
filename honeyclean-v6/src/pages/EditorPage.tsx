import { useRef, useCallback } from "react";
import { Eraser, Paintbrush, Undo2, Redo2, Save, RotateCcw } from "lucide-react";
import { useStore } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { Button } from "../components/ui/Button";
import { Slider } from "../components/ui/Slider";
import { Select } from "../components/ui/Select";

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

export function EditorPage() {
  const { t } = useI18n();
  const editor = useStore((s) => s.editor);
  const setEditor = useStore((s) => s.setEditor);
  const dividerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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

  const hasBefore = !!editor.beforeSrc;
  const hasAfter = !!editor.afterSrc;

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Tool selection */}
        <div className="flex items-center gap-1 bg-void-800 rounded-lg p-0.5">
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

        <div className="flex-1" />

        <Button size="sm" variant="ghost" icon={<RotateCcw size={14} />}>
          {t("reset")}
        </Button>
        <Button size="sm" variant="primary" icon={<Save size={14} />}>
          {t("save")}
        </Button>
      </div>

      {/* Canvas area */}
      <div
        ref={containerRef}
        className="flex-1 relative rounded-xl overflow-hidden border border-void-600
          bg-void-900"
        style={{
          backgroundImage:
            "repeating-conic-gradient(#1a1a1a 0% 25%, #222 0% 50%)",
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
                src={editor.beforeSrc!}
                alt="Before"
                className="w-full h-full object-contain"
              />
              <span className="absolute top-3 left-3 px-2 py-1 text-[10px] font-bold
                bg-void-900/70 text-honey-400 rounded">
                {t("before_label")}
              </span>
            </div>

            {/* After image */}
            <div
              className="absolute inset-0"
              style={{ clipPath: `inset(0 0 0 ${editor.dividerPos}%)` }}
            >
              <img
                src={editor.afterSrc!}
                alt="After"
                className="w-full h-full object-contain"
              />
              <span className="absolute top-3 right-3 px-2 py-1 text-[10px] font-bold
                bg-void-900/70 text-honey-400 rounded">
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
        ) : (
          <div className="flex items-center justify-center h-full text-honey-700 text-sm">
            Process an image first to use the editor
          </div>
        )}
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
