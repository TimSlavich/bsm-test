/**
 * i18n bootstrap. Default language is English; the auto-detector promotes
 * Ukrainian when ``navigator.language`` resolves to ``uk-*``. Persisted in
 * localStorage so the user's choice survives reloads.
 */
import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import uk from "./uk.json";
export const SUPPORTED_LANGS = ["en", "uk"];
i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
    resources: {
        en: { translation: en },
        uk: { translation: uk },
    },
    fallbackLng: "en",
    supportedLngs: [...SUPPORTED_LANGS],
    interpolation: { escapeValue: false },
    detection: {
        order: ["localStorage", "navigator"],
        caches: ["localStorage"],
        lookupLocalStorage: "brand-monitor.lang",
    },
});
export default i18n;
