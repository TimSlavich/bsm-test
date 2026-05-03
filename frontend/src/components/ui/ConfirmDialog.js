import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useTranslation } from "react-i18next";
import { Button } from "./Button";
import { Modal } from "./Modal";
export function ConfirmDialog({ open, title, body, confirmLabel, cancelLabel, tone = "danger", busy = false, onConfirm, onClose, }) {
    const { t } = useTranslation();
    return (_jsx(Modal, { open: open, onClose: onClose, title: title, size: "sm", footer: _jsxs(_Fragment, { children: [_jsx(Button, { variant: "ghost", onClick: onClose, disabled: busy, children: cancelLabel ?? t("actions.cancel") }), _jsx(Button, { variant: tone === "danger" ? "danger" : "primary", onClick: onConfirm, loading: busy, children: confirmLabel ?? t("actions.delete") })] }), children: body && _jsx("div", { style: { fontSize: 13, color: "var(--text-muted)", lineHeight: 1.55 }, children: body }) }));
}
