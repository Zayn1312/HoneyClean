import { useEffect, useCallback, type ReactNode } from "react";
import { Save, FolderOpen, AlertTriangle, Zap } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import { useStore } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { useWorker } from "../hooks/useWorker";
import { Button } from "../components/ui/Button";
import { Slider } from "../components/ui/Slider";
import { Toggle } from "../components/ui/Toggle";
import { Select } from "../components/ui/Select";
import { Tooltip } from "../components/ui/Tooltip";
import { MODEL_ORDER, MODEL_INFO } from "../lib/presets";
import { LANGUAGES } from "../lib/i18n";

// ── SettingsCard ──
function SettingsCard({ icon, title, subtitle, children }: {
  icon: string;
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="settings-card">
      <div className="settings-card-header">
        <span className="settings-card-icon">{icon}</span>
        <span className="settings-card-title">{title}</span>
        {subtitle && <span className="settings-card-subtitle">{subtitle}</span>}
      </div>
      <div className="settings-card-body">
        {children}
      </div>
    </div>
  );
}

// ── SettingRow ──
function SettingRow({ label, tooltip, tooltipDetail, children }: {
  label: string;
  tooltip?: string;
  tooltipDetail?: string;
  children: ReactNode;
}) {
  const inner = (
    <div className="setting-row">
      <span className="setting-label">{label}</span>
      <div>{children}</div>
    </div>
  );

  if (tooltip) {
    return (
      <Tooltip content={tooltip} detail={tooltipDetail} position="right">
        {inner}
      </Tooltip>
    );
  }

  return inner;
}

// ── GPU Status Card ──
function GpuStatusCard({ provider, isGpu, gpuEnabled }: {
  provider: string;
  isGpu: boolean;
  gpuEnabled: boolean;
}) {
  const setShowGpuSetup = useStore((s) => s.setShowGpuSetup);

  // GPU is active and working
  if (isGpu) {
    return (
      <div className="mx-4 mb-3 p-3 rounded-lg border"
        style={{ background: "rgba(34,197,94,0.06)", borderColor: "rgba(34,197,94,0.2)" }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400" />
          <span className="text-sm font-medium text-green-400">GPU aktiv</span>
          <span className="text-xs text-green-500/70 ml-auto font-mono">{provider}</span>
        </div>
        <p className="text-xs text-green-500/60 mt-1">
          Verarbeitung laeuft auf der Grafikkarte — maximale Geschwindigkeit.
        </p>
      </div>
    );
  }

  // GPU toggle is ON but provider is CPU — offer automatic fix
  if (gpuEnabled && !isGpu) {
    return (
      <div className="mx-4 mb-3 p-3 rounded-lg border"
        style={{ background: "rgba(245,158,11,0.06)", borderColor: "rgba(245,158,11,0.25)" }}>
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle size={14} className="text-amber-400" />
          <span className="text-sm font-medium text-amber-400">GPU aktiviert, aber CPU wird verwendet</span>
        </div>
        <p className="text-xs text-honey-500 mb-3">
          GPU-Beschleunigung ist nicht korrekt eingerichtet. HoneyClean kann das automatisch beheben.
        </p>
        <button
          onClick={() => setShowGpuSetup(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{
            background: "rgba(245,158,11,0.12)",
            color: "#F59E0B",
            border: "1px solid rgba(245,158,11,0.3)",
          }}
        >
          <Zap size={14} /> GPU jetzt einrichten
        </button>
      </div>
    );
  }

  // GPU toggle is OFF
  return (
    <div className="mx-4 mb-3 p-3 rounded-lg border"
      style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.06)" }}>
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-honey-700" />
        <span className="text-sm text-honey-600">GPU deaktiviert</span>
      </div>
      <p className="text-xs text-honey-700 mt-1">
        Verarbeitung laeuft auf der CPU. Aktiviere GPU fuer ~10x schnellere Verarbeitung.
      </p>
    </div>
  );
}

export function SettingsPage() {
  const { t, language, setLanguage } = useI18n();
  const { send } = useWorker();
  const config = useStore((s) => s.config);
  const setConfig = useStore((s) => s.setConfig);
  const updateConfig = useStore((s) => s.updateConfig);
  const workerReady = useStore((s) => s.workerReady);
  const addToast = useStore((s) => s.addToast);
  const provider = useStore((s) => s.provider);
  const isGpu = useStore((s) => s.isGpu);

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
    <div className="h-full overflow-y-auto" style={{ padding: 20 }}>
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-heading font-semibold text-honey-300" style={{ fontSize: 22 }}>
            {t("settings_title")}
          </h2>
          <Button variant="primary" size="sm" icon={<Save size={14} />} onClick={handleSave}>
            {t("save_settings")}
          </Button>
        </div>

        {/* 1. General */}
        <SettingsCard icon="📁" title={t("section_general")}>
          <SettingRow label={t("output_dir")} tooltip="Zielordner für verarbeitete Bilder." tooltipDetail="Alle Ergebnisse werden hier gespeichert.">
            <div className="flex items-end gap-2">
              <input
                type="text"
                value={(config.output_dir as string) ?? ""}
                onChange={(e) => updateConfig({ output_dir: e.target.value })}
                className="flex-1 bg-void-700 border border-void-500 text-honey-100
                  rounded-lg px-3 py-2 text-sm focus:border-honey-500 focus:outline-none"
              />
              <Button size="sm" variant="ghost" icon={<FolderOpen size={14} />}
                onClick={handleBrowseOutput}>
                {t("browse")}
              </Button>
            </div>
          </SettingRow>

          <SettingRow label={t("language")} tooltip="Sprache der Benutzeroberfläche.">
            <Select
              value={language}
              options={LANGUAGES}
              onChange={(v) => {
                setLanguage(v as typeof language);
                updateConfig({ language: v });
              }}
            />
          </SettingRow>

          <SettingRow label={t("output_format")} tooltip="Ausgabeformat der Bilder." tooltipDetail="PNG = verlustfrei mit Transparenz. JPEG = kleiner, kein Alpha. WebP = komprimiert mit Alpha.">
            <Select
              value={(config.output_format as string) ?? "png"}
              options={formatOptions}
              onChange={(v) => updateConfig({ output_format: v })}
            />
          </SettingRow>
        </SettingsCard>

        {/* 2. AI Engine */}
        <SettingsCard icon="🤖" title={t("section_ai")}>
          <SettingRow label={t("ai_model")} tooltip="KI-Modell für die Hintergrundentfernung." tooltipDetail="BiRefNet General = beste Qualität. Silueta = schnellstes.">
            <Select
              value={(config.model as string) ?? "auto"}
              options={modelOptions}
              onChange={(v) => updateConfig({ model: v })}
            />
          </SettingRow>

          <SettingRow label={t("color_decontaminate")} tooltip="Farbentfernung an semi-transparenten Kanten." tooltipDetail="Entfernt Hintergrundfarbe die in die Ränder blutet.">
            <Toggle
              label=""
              checked={(config.color_decontaminate as boolean) ?? true}
              onChange={(v) => updateConfig({ color_decontaminate: v })}
            />
          </SettingRow>

          <SettingRow label={t("edge_feather")} tooltip="Weiche Kanten." tooltipDetail="0 = scharf. 5-10 = natürlichere Übergänge.">
            <Slider
              label=""
              value={(config.edge_feather as number) ?? 0}
              min={0} max={20}
              onChange={(v) => updateConfig({ edge_feather: v })}
              suffix="px"
            />
          </SettingRow>

          <SettingRow label={t("alpha_fg_label")} tooltip="Vordergrundstärke." tooltipDetail="Höhere Werte = härtere Kanten beim Ausschneiden.">
            <Slider
              label=""
              value={(config.alpha_fg as number) ?? 270}
              min={0} max={300}
              onChange={(v) => updateConfig({ alpha_fg: v })}
            />
          </SettingRow>

          <SettingRow label={t("alpha_bg_label")} tooltip="Hintergrundtoleranz." tooltipDetail="Höhere Werte = mehr Hintergrund wird entfernt.">
            <Slider
              label=""
              value={(config.alpha_bg as number) ?? 20}
              min={0} max={100}
              onChange={(v) => updateConfig({ alpha_bg: v })}
            />
          </SettingRow>

          <SettingRow label={t("alpha_erode_label")} tooltip="Kantenreduzierung." tooltipDetail="Verhindert Hintergrundfarbe an den Rändern.">
            <Slider
              label=""
              value={(config.alpha_erode as number) ?? 15}
              min={0} max={50}
              onChange={(v) => updateConfig({ alpha_erode: v })}
            />
          </SettingRow>
        </SettingsCard>

        {/* 3. GPU */}
        <SettingsCard icon="⚡" title={t("section_gpu")} subtitle={`${provider} ${isGpu ? "✓" : "⚠"}`}>
          <SettingRow label={t("use_gpu_label")} tooltip="GPU-Beschleunigung aktivieren." tooltipDetail="Deaktivieren nur wenn GPU Probleme verursacht.">
            <Toggle
              label=""
              checked={(config.use_gpu as boolean) ?? true}
              onChange={(v) => updateConfig({ use_gpu: v })}
            />
          </SettingRow>

          {/* GPU status explanation */}
          <GpuStatusCard provider={provider} isGpu={isGpu} gpuEnabled={(config.use_gpu as boolean) ?? true} />

          <SettingRow label={t("gpu_limit_label")} tooltip="Begrenzt die GPU-Auslastung." tooltipDetail="100% = maximale Geschwindigkeit.">
            <Slider
              label=""
              value={(config.gpu_limit as number) ?? 100}
              min={10} max={100}
              onChange={(v) => updateConfig({ gpu_limit: v })}
              suffix="%"
            />
          </SettingRow>
        </SettingsCard>

        {/* 4. Video */}
        <SettingsCard icon="🎬" title={t("section_video")}>
          <SettingRow label={t("video_format")} tooltip="Ausgabeformat für Videos." tooltipDetail="WebM = klein mit Alpha. MOV = ProRes für Profis.">
            <Select
              value={(config.video_format as string) ?? "webm"}
              options={videoFormatOptions}
              onChange={(v) => updateConfig({ video_format: v })}
            />
          </SettingRow>

          <SettingRow label={t("temporal_smooth")} tooltip="Zeitglättung zwischen Frames." tooltipDetail="Verhindert Flackern in Videos. Höher = glatter.">
            <Slider
              label=""
              value={(config.temporal_smoothing as number) ?? 40}
              min={0} max={100}
              onChange={(v) => updateConfig({ temporal_smoothing: v })}
              suffix="%"
            />
          </SettingRow>

          <SettingRow label={t("edge_refine")} tooltip="Kantenverfeinerung für Videoframes." tooltipDetail="Höher = präzisere Kanten, aber langsamer.">
            <Slider
              label=""
              value={(config.edge_refinement as number) ?? 2}
              min={0} max={10}
              onChange={(v) => updateConfig({ edge_refinement: v })}
            />
          </SettingRow>

          <SettingRow label={t("max_vram")} tooltip="Maximaler VRAM für Videoframes." tooltipDetail="Reduzieren wenn andere Programme VRAM brauchen.">
            <Slider
              label=""
              value={(config.max_vram_pct as number) ?? 75}
              min={25} max={100}
              onChange={(v) => updateConfig({ max_vram_pct: v })}
              suffix="%"
            />
          </SettingRow>

          <SettingRow label={t("preserve_audio")} tooltip="Audio aus dem Originalvideo beibehalten.">
            <Toggle
              label=""
              checked={(config.preserve_audio as boolean) ?? true}
              onChange={(v) => updateConfig({ preserve_audio: v })}
            />
          </SettingRow>
        </SettingsCard>
      </div>
    </div>
  );
}
