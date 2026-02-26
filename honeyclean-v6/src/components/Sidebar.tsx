import { Layers, PenTool, Settings, Info, Box } from "lucide-react";
import { useStore, type Page } from "../store/useStore";
import { useI18n } from "../hooks/useI18n";
import { motion } from "framer-motion";

const NAV_ITEMS: { page: Page; icon: typeof Layers; labelKey: string }[] = [
  { page: "queue", icon: Layers, labelKey: "nav_queue" },
  { page: "editor", icon: PenTool, labelKey: "nav_editor" },
  { page: "models", icon: Box, labelKey: "nav_models" },
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

  return (
    <aside className="w-48 h-full flex flex-col shrink-0
      bg-void-800/60 backdrop-blur-xl border-r border-void-600/40">
      {/* Logo */}
      <div className="p-4 pb-2">
        <h1 className="text-lg font-heading font-bold text-honey-400 tracking-tight">
          HoneyClean
        </h1>
        <p className="text-[10px] text-honey-700 mt-0.5">v6.0</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-2 space-y-0.5">
        {NAV_ITEMS.map(({ page: p, icon: Icon, labelKey }) => {
          const active = page === p;
          return (
            <motion.button
              key={p}
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setPage(p)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm
                transition-colors cursor-pointer
                ${active
                  ? "bg-honey-500/15 text-honey-300 font-medium"
                  : "text-honey-600 hover:text-honey-400 hover:bg-void-700/50"
                }`}
            >
              <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
              <span>{t(labelKey)}</span>
              {active && (
                <motion.div
                  layoutId="sidebar-indicator"
                  className="absolute left-0 w-0.5 h-5 bg-honey-400 rounded-r"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* GPU Info */}
      <div className="px-3 py-3 border-t border-void-600/40 space-y-1">
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${isGpu ? "bg-green-400" : "bg-yellow-500"}`} />
          <span className="text-[11px] text-honey-400 font-mono">
            {provider}
          </span>
        </div>
        {gpuInfo.gpu_name && (
          <>
            <p className="text-[10px] text-honey-700 truncate">{gpuInfo.gpu_name}</p>
            <p className="text-[10px] text-honey-700 font-mono">
              {gpuInfo.vram_used}/{gpuInfo.vram_total} MB · {gpuInfo.gpu_util}%
            </p>
          </>
        )}
      </div>
    </aside>
  );
}
