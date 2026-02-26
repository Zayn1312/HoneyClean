import { useCallback } from "react";
import { useStore } from "../store/useStore";
import { t as translate, setLanguage, type Language } from "../lib/i18n";

export function useI18n() {
  const language = useStore((s) => s.language);
  const storeSetLanguage = useStore((s) => s.setLanguage);

  // Ensure lib is synced with store
  setLanguage(language);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      setLanguage(language);
      return translate(key, params);
    },
    [language]
  );

  const changeLang = useCallback(
    (lang: Language) => {
      setLanguage(lang);
      storeSetLanguage(lang);
    },
    [storeSetLanguage]
  );

  return { t, language, setLanguage: changeLang };
}
