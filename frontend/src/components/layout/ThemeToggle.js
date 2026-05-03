import { jsx as _jsx } from "react/jsx-runtime";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { applyTheme, getInitialTheme } from "../../lib/theme";
import { IconButton, Tooltip } from "../ui";
export function ThemeToggle() {
    const { t } = useTranslation();
    const [theme, setTheme] = useState(() => getInitialTheme());
    useEffect(() => {
        applyTheme(theme);
    }, [theme]);
    const toggle = () => setTheme((prev) => (prev === "dark" ? "light" : "dark"));
    return (_jsx(Tooltip, { content: t("theme.toggle"), children: _jsx(IconButton, { onClick: toggle, "aria-label": t("theme.toggle"), children: theme === "dark" ? _jsx(Sun, { size: 16 }) : _jsx(Moon, { size: 16 }) }) }));
}
