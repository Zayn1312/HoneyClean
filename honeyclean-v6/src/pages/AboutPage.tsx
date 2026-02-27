import { ExternalLink } from "lucide-react";
import { useI18n } from "../hooks/useI18n";

export function AboutPage() {
  const { t } = useI18n();

  return (
    <div className="h-full flex items-center justify-center" style={{ padding: 20 }}>
      <div className="text-center space-y-6 max-w-md">
        {/* Amber hexagon logo */}
        <div className="mx-auto flex items-center justify-center" style={{ width: 80, height: 80 }}>
          <svg viewBox="0 0 100 100" width="80" height="80">
            <polygon
              points="50,2 93,25 93,75 50,98 7,75 7,25"
              fill="rgba(245,158,11,0.12)"
              stroke="rgba(245,158,11,0.35)"
              strokeWidth="2"
            />
            <text
              x="50" y="56"
              textAnchor="middle"
              dominantBaseline="middle"
              fill="#F59E0B"
              fontFamily="'Space Grotesk', system-ui, sans-serif"
              fontWeight="700"
              fontSize="28"
            >
              HC
            </text>
          </svg>
        </div>

        <div>
          <h1 className="font-heading font-bold text-honey-300" style={{ fontSize: 26 }}>
            {t("app_title")}
          </h1>
          <p className="text-honey-500 mt-1" style={{ fontSize: 14 }}>
            {t("about_tagline")}
          </p>
        </div>

        <div className="space-y-2" style={{ fontSize: 14 }}>
          <div className="flex items-center justify-center gap-2 text-honey-400">
            <span className="text-honey-600">{t("about_version")}:</span>
            <span className="font-mono">6.0</span>
          </div>
          <div className="flex items-center justify-center gap-2 text-honey-400">
            <span className="text-honey-600">{t("about_author")}:</span>
            <span>Zayn1312</span>
          </div>
          <div className="flex items-center justify-center gap-2 text-honey-400">
            <span className="text-honey-600">{t("about_license")}:</span>
            <span>MIT</span>
          </div>
        </div>

        <a
          href="https://github.com/Zayn1312/HoneyClean"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg
            text-void-900 font-medium transition-all hover:brightness-110"
          style={{
            fontSize: 14,
            background: "linear-gradient(135deg, #F59E0B, #D97706)",
          }}
        >
          <ExternalLink size={15} />
          Star on GitHub
        </a>

        <p className="text-xs text-honey-800">
          {t("footer")}
        </p>
      </div>
    </div>
  );
}
