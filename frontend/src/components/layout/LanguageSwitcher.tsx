import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Select, type SelectOption } from "../ui";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  const options: SelectOption[] = [
    { value: "en", label: t("language.en") },
    { value: "uk", label: t("language.uk") },
  ];

  const lang = i18n.resolvedLanguage?.startsWith("uk") ? "uk" : "en";

  return (
    <span className="lang-switcher" aria-label={t("language.label")}>
      <Languages size={14} className="lang-switcher__icon" aria-hidden />
      <Select
        value={lang}
        onChange={(v) => void i18n.changeLanguage(v)}
        options={options}
        size="sm"
        ariaLabel={t("language.label")}
      />
    </span>
  );
}
