import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Select } from "../ui";
export function LanguageSwitcher() {
    const { i18n, t } = useTranslation();
    const options = [
        { value: "en", label: t("language.en") },
        { value: "uk", label: t("language.uk") },
    ];
    const lang = i18n.resolvedLanguage?.startsWith("uk") ? "uk" : "en";
    return (_jsxs("span", { className: "lang-switcher", "aria-label": t("language.label"), children: [_jsx(Languages, { size: 14, className: "lang-switcher__icon", "aria-hidden": true }), _jsx(Select, { value: lang, onChange: (v) => void i18n.changeLanguage(v), options: options, size: "sm", ariaLabel: t("language.label") })] }));
}
