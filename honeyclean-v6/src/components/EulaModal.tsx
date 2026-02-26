import { useState } from "react";
import { motion } from "framer-motion";
import { useI18n } from "../hooks/useI18n";
import { Select } from "./ui/Select";
import { Button } from "./ui/Button";
import { LANGUAGES } from "../lib/i18n";

interface EulaModalProps {
  onAccept: () => void;
}

export function EulaModal({ onAccept }: EulaModalProps) {
  const { t, language, setLanguage } = useI18n();
  const [agreed, setAgreed] = useState(false);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-void-900/90 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-lg mx-4 bg-void-800 border border-void-600 rounded-2xl
          shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="p-6 pb-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-heading font-bold text-honey-300">
              {t("eula_title")}
            </h2>
            <Select
              value={language}
              options={LANGUAGES}
              onChange={(v) => setLanguage(v as typeof language)}
              className="w-32"
            />
          </div>

          {/* Terms content */}
          <div className="h-48 overflow-y-auto bg-void-900 rounded-lg p-4 text-xs text-honey-500
            border border-void-600 space-y-2 leading-relaxed">
            <p className="font-semibold text-honey-300">HoneyClean v6.0 — Terms of Use</p>
            <p>
              This software is provided "as is" without warranty of any kind. HoneyClean uses AI
              models for background removal processing. By using this software, you agree that:
            </p>
            <ul className="list-disc ml-4 space-y-1">
              <li>You have the rights to process the images you upload.</li>
              <li>AI processing results may vary in quality and accuracy.</li>
              <li>The software downloads AI models from external sources (PyPI, GitHub).</li>
              <li>GPU processing requires compatible hardware and drivers.</li>
              <li>No data is collected or transmitted beyond model downloads.</li>
              <li>The software is licensed under the MIT License.</li>
            </ul>
            <p>
              For full documentation and source code, visit the GitHub repository.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 space-y-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="w-4 h-4 rounded border-void-500 bg-void-700 accent-honey-500"
            />
            <span className="text-sm text-honey-300">
              {t("eula_checkbox")}
            </span>
          </label>

          <div className="flex gap-3">
            <Button
              variant="primary"
              size="lg"
              className="flex-1"
              disabled={!agreed}
              onClick={onAccept}
            >
              {t("eula_continue")}
            </Button>
            <Button
              variant="ghost"
              size="lg"
              onClick={() => window.close?.()}
            >
              {t("eula_decline")}
            </Button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
