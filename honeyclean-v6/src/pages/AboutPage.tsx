import { ExternalLink } from "lucide-react";
import { useI18n } from "../hooks/useI18n";

export function AboutPage() {
  const { t } = useI18n();

  return (
    <div className="h-full flex items-center justify-center p-8">
      <div className="text-center space-y-6 max-w-md">
        {/* Logo placeholder */}
        <div className="w-20 h-20 mx-auto rounded-2xl bg-honey-500/20 border border-honey-500/30
          flex items-center justify-center">
          <span className="text-3xl font-heading font-bold text-honey-400">HC</span>
        </div>

        <div>
          <h1 className="text-2xl font-heading font-bold text-honey-300">
            {t("app_title")}
          </h1>
          <p className="text-sm text-honey-500 mt-1">
            {t("about_tagline")}
          </p>
        </div>

        <div className="space-y-2 text-sm">
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
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg
            bg-void-700 hover:bg-void-600 text-honey-400 text-sm
            transition-colors border border-void-500"
        >
          <ExternalLink size={14} />
          {t("about_github")}
        </a>

        <p className="text-xs text-honey-800">
          {t("footer")}
        </p>
      </div>
    </div>
  );
}
