import { useEffect, useCallback } from "react";
import { Save, FolderOpen } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import { useStore } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { useWorker } from "../hooks/useWorker";
import { Button } from "../components/ui/Button";
import { Slider } from "../components/ui/Slider";
import { Toggle } from "../components/ui/Toggle";
import { Select } from "../components/ui/Select";
import { MODEL_ORDER, MODEL_INFO } from "../lib/presets";
import { LANGUAGES } from "../lib/i18n";

export function SettingsPage() {
  const { t, language, setLanguage } = useI18n();
  const { send } = useWorker();
  const config = useStore((s) => s.config);
  const setConfig = useStore((s) => s.setConfig);
  const updateConfig = useStore((s) => s.updateConfig);
  const workerReady = useStore((s) => s.workerReady);
  const addToast = useStore((s) => s.addToast);

  useEffect(() => {
    if (!workerReady) return;
    send("get_config").then((res) => {
      if (res.status === "ok" && res.data?.config) {
        setConfig(res.data.config as Record<string, unknown>);
        const lang = (res.data.config as Record<string, unknown>).language as string;
        if (lang) setLanguage(lang as typeof language);
      }
    }).catch(() => {});
  }, [workerReady, send, setConfig, setLanguage]);

  const handleSave = useCallback(async () => {
    try {
      const res = await send("save_config", { config });
      if (res.status === "ok") {
        addToast(t("settings_saved"), "success");
      }
    } catch (e) {
      addToast("Failed to save settings", "error");
    }
  }, [config, send, addToast, t]);

  const handleBrowseOutput = useCallback(async () => {
    try {
      const folder = await invoke<string | null>("pick_output_folder");
      if (folder) updateConfig({ output_dir: folder });
    } catch {}
  }, [updateConfig]);

  const modelOptions = MODEL_ORDER.map((id) => ({
    value: id,
    label: MODEL_INFO[id] ? t(MODEL_INFO[id].name_key) : id,
  }));

  const formatOptions = [
    { value: "png", label: "PNG" },
    { value: "jpeg", label: "JPEG" },
    { value: "webp", label: "WebP" },
  ];

  const videoFormatOptions = [
    { value: "webm", label: "WebM (VP8)" },
    { value: "mov", label: "MOV (ProRes)" },
    { value: "mp4_greenscreen", label: "MP4 Green" },
    { value: "png_sequence", label: "PNG Sequence" },
  ];

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-heading font-bold text-honey-300">
            {t("settings_title")}
          </h2>
          <Button variant="primary" size="sm" icon={<Save size={14} />} onClick={handleSave}>
            {t("save_settings")}
          </Button>
        </div>

        {/* General */}
        <section className="space-y-3">
          <h3 className="text-sm font-semibold text-honey-400 uppercase tracking-wider">
            {t("section_general")}
          </h3>
          <div className="space-y-3 bg-void-800/40 rounded-xl p-4 border border-void-600/40">
            {/* Output directory */}
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <label className="text-xs text-honey-300 block mb-1">{t("output_dir")}</label>
                <input
                  type="text"
                  value={(config.output_dir as string) ?? ""}
                  onChange={(e) => updateConfig({ output_dir: e.target.value })}
                  className="w-full bg-void-700 border border-void-500 text-honey-100
                    rounded-lg px-3 py-2 text-sm focus:border-honey-500 focus:outline-none"
                />
              </div>
              <Button size="md" variant="ghost" icon={<FolderOpen size={14} />}
                onClick={handleBrowseOutput}>
                {t("browse")}
              </Button>
            </div>

            <Select
              label={t("language")}
              value={language}
              options={LANGUAGES}
              onChange={(v) => {
                setLanguage(v as typeof language);
                updateConfig({ language: v });
              }}
            />

            <Select
              label={t("output_format")}
              value={(config.output_format as string) ?? "png"}
              options={formatOptions}
              onChange={(v) => updateConfig({ output_format: v })}
            />
          </div>
        </section>

        {/* AI Engine */}
        <section className="space-y-3">
          <h3 className="text-sm font-semibold text-honey-400 uppercase tracking-wider">
            {t("section_ai")}
          </h3>
          <div className="space-y-3 bg-void-800/40 rounded-xl p-4 border border-void-600/40">
            <Select
              label={t("ai_model")}
              value={(config.model as string) ?? "auto"}
              options={modelOptions}
              onChange={(v) => updateConfig({ model: v })}
            />

            <Toggle
              label={t("color_decontaminate")}
              checked={(config.color_decontaminate as boolean) ?? true}
              onChange={(v) => updateConfig({ color_decontaminate: v })}
            />

            <Slider
              label={t("edge_feather")}
              value={(config.edge_feather as number) ?? 0}
              min={0} max={20}
              onChange={(v) => updateConfig({ edge_feather: v })}
              suffix="px"
            />

            <Slider
              label={t("alpha_fg_label")}
              value={(config.alpha_fg as number) ?? 270}
              min={0} max={300}
              onChange={(v) => updateConfig({ alpha_fg: v })}
            />

            <Slider
              label={t("alpha_bg_label")}
              value={(config.alpha_bg as number) ?? 20}
              min={0} max={100}
              onChange={(v) => updateConfig({ alpha_bg: v })}
            />

            <Slider
              label={t("alpha_erode_label")}
              value={(config.alpha_erode as number) ?? 15}
              min={0} max={50}
              onChange={(v) => updateConfig({ alpha_erode: v })}
            />
          </div>
        </section>

        {/* GPU */}
        <section className="space-y-3">
          <h3 className="text-sm font-semibold text-honey-400 uppercase tracking-wider">
            {t("section_gpu")}
          </h3>
          <div className="space-y-3 bg-void-800/40 rounded-xl p-4 border border-void-600/40">
            <Toggle
              label={t("use_gpu_label")}
              checked={(config.use_gpu as boolean) ?? true}
              onChange={(v) => updateConfig({ use_gpu: v })}
            />

            <Slider
              label={t("gpu_limit_label")}
              value={(config.gpu_limit as number) ?? 100}
              min={10} max={100}
              onChange={(v) => updateConfig({ gpu_limit: v })}
              suffix="%"
            />
          </div>
        </section>

        {/* Video */}
        <section className="space-y-3">
          <h3 className="text-sm font-semibold text-honey-400 uppercase tracking-wider">
            {t("section_video")}
          </h3>
          <div className="space-y-3 bg-void-800/40 rounded-xl p-4 border border-void-600/40">
            <Select
              label={t("video_format")}
              value={(config.video_format as string) ?? "webm"}
              options={videoFormatOptions}
              onChange={(v) => updateConfig({ video_format: v })}
            />

            <Slider
              label={t("temporal_smooth")}
              value={(config.temporal_smoothing as number) ?? 40}
              min={0} max={100}
              onChange={(v) => updateConfig({ temporal_smoothing: v })}
              suffix="%"
            />

            <Slider
              label={t("edge_refine")}
              value={(config.edge_refinement as number) ?? 2}
              min={0} max={10}
              onChange={(v) => updateConfig({ edge_refinement: v })}
            />

            <Slider
              label={t("max_vram")}
              value={(config.max_vram_pct as number) ?? 75}
              min={25} max={100}
              onChange={(v) => updateConfig({ max_vram_pct: v })}
              suffix="%"
            />

            <Toggle
              label={t("preserve_audio")}
              checked={(config.preserve_audio as boolean) ?? true}
              onChange={(v) => updateConfig({ preserve_audio: v })}
            />
          </div>
        </section>
      </div>
    </div>
  );
}
