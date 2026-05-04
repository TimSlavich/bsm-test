import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Friendly modal that surfaces scan-form validation problems.
 *
 * The backend returns a list of ``{field, code, message}`` records;
 * we map ``code`` to a localized, human-readable line via i18n templates
 * (``validation.<code>`` keys) and fall back to the backend's English
 * message only if a code is brand new and not yet translated.
 */
import { AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button, Modal } from "../../components/ui";
export function ValidationDialog({ problems, onClose }) {
    const { t } = useTranslation();
    const open = problems.length > 0;
    return (_jsx(Modal, { open: open, onClose: onClose, title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 10 }, children: [_jsx(AlertTriangle, { size: 20, color: "var(--danger, #e5484d)", "aria-hidden": true }), t("validation.title")] }), description: t("validation.subtitle"), size: "sm", footer: _jsx(Button, { onClick: onClose, fullWidth: true, children: t("validation.dismiss") }), children: _jsx("ul", { className: "validation-list", children: problems.map((p, i) => {
                const key = `validation.${p.code}`;
                const localized = t(key, { defaultValue: p.message });
                return (_jsx("li", { className: "validation-list__item", children: localized }, `${p.field}-${i}`));
            }) }) }));
}
