import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { applyTheme, getInitialTheme, type Theme } from "../../lib/theme";
import { IconButton, Tooltip } from "../ui";

export function ThemeToggle() {
  const { t } = useTranslation();
  const [theme, setTheme] = useState<Theme>(() => getInitialTheme());

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggle = () => setTheme((prev) => (prev === "dark" ? "light" : "dark"));

  return (
    <Tooltip content={t("theme.toggle")}>
      <IconButton onClick={toggle} aria-label={t("theme.toggle")}>
        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      </IconButton>
    </Tooltip>
  );
}
