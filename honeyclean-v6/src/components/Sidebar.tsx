import { Layers, PenTool, Settings, Info, Box, Cpu } from "lucide-react";
import { useStore, type Page } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { Tooltip } from "./ui/Tooltip";

const NAV_ITEMS: { page: Page; icon: typeof Layers; labelKey: string }[] = [
  { page: "queue", icon: Layers, labelKey: "nav_queue" },
  { page: "editor", icon: PenTool, labelKey: "nav_editor" },
  { page: "models", icon: Box, labelKey: "nav_models" },
  { page: "diagnostics", icon: Cpu, labelKey: "nav_diagnostics" },
  { page: "settings", icon: Settings, labelKey: "nav_settings" },
  { page: "about", icon: Info, labelKey: "nav_about" },
];

export function Sidebar() {
  const { t } = useI18n();
  const page = useStore((s) => s.page);
  const setPage = useStore((s) => s.setPage);
  const gpuInfo = useStore((s) => s.gpuInfo);
  const provider = useStore((s) => s.provider);
  const isGpu = useStore((s) => s.isGpu);
  const hasGpuWarning = useStore((s) => s.hasGpuWarning);

  return (
    <aside className="h-full flex flex-col shrink-0
      bg-void-800/60 backdrop-blur-xl border-r border-void-600/40"
      style={{ width: 180 }}>
      {/* Logo */}
      <div className="px-4 pt-5 pb-4" style={{ borderBottom: "1px solid rgba(245,158,11,0.08)" }}>
        <h1 className="font-heading text-[18px] font-bold text-[#F0F0FF] tracking-tight">
          HoneyClean
        </h1>
        <p className="text-[11px] text-[#7070A0] mt-0.5">v6.0</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV_ITEMS.map(({ page: p, icon: Icon, labelKey }) => {
          const active = page === p;
          return (
            <button
              key={p}
              onClick={() => setPage(p)}
              className="w-full flex items-center gap-2.5 px-4 rounded-lg transition-all duration-150"
              style={{
                height: 44,
                fontSize: 14,
                color: active ? "#F59E0B" : "#7070A0",
                background: active ? "rgba(245,158,11,0.06)" : "transparent",
                borderLeft: active ? "2px solid #F59E0B" : "2px solid transparent",
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  e.currentTarget.style.color = "#C0C0E0";
                  e.currentTarget.style.background = "rgba(255,255,255,0.03)";
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  e.currentTarget.style.color = "#7070A0";
                  e.currentTarget.style.background = "transparent";
                }
              }}
            >
              <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
              <span className={active ? "font-medium" : ""}>{t(labelKey)}</span>
              {p === "diagnostics" && hasGpuWarning && (
                <span className="nav-badge ml-auto">!</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* GPU Info */}
      <div className="px-4 py-3 space-y-1" style={{ borderTop: "1px solid rgba(245,158,11,0.08)" }}>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isGpu ? "bg-green-400" : "bg-yellow-500"}`} />
          <span className="text-[12px] font-mono" style={{ color: isGpu ? "#4ade80" : "#eab308" }}>
            {provider} {isGpu ? "✓" : "⚠"}
          </span>
        </div>
        {gpuInfo.gpu_name && (
          <>
            <Tooltip content="Deine Grafikkarte." detail="RTX 4070 Ti Super = optimal für HoneyClean." position="right">
              <p className="text-[12px] text-[#505070] truncate">{gpuInfo.gpu_name}</p>
            </Tooltip>
            <Tooltip content="GPU-Speicher Auslastung." detail="Während der Verarbeitung steigt der VRAM-Verbrauch." position="right">
              <p className="text-[12px] text-[#505070] font-mono">
                {gpuInfo.vram_used}/{gpuInfo.vram_total} MB
              </p>
            </Tooltip>
          </>
        )}
      </div>
    </aside>
  );
}
