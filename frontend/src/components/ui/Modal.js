import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as RD from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
/** Visually hidden but reachable to assistive tech. */
const SR_ONLY = {
    position: "absolute",
    width: 1,
    height: 1,
    padding: 0,
    margin: -1,
    overflow: "hidden",
    clip: "rect(0,0,0,0)",
    whiteSpace: "nowrap",
    border: 0,
};
export function Modal({ open, onClose, title, description, children, footer, size = "md" }) {
    const { t } = useTranslation();
    // Radix logs a dev warning unless either ``<Dialog.Description>`` is in
    // the tree or ``aria-describedby={undefined}`` is set on Content. We
    // always render Description: if the caller supplied text, it's visible;
    // otherwise we fall back to an SR-only label derived from the title so
    // screen readers still get a meaningful announcement.
    return (_jsx(RD.Root, { open: open, onOpenChange: (v) => !v && onClose(), children: _jsxs(RD.Portal, { children: [_jsx(RD.Overlay, { className: "modal__overlay" }), _jsxs(RD.Content, { className: `modal modal--${size}`, children: [_jsxs("header", { className: "modal__header", children: [_jsxs("div", { className: "modal__title-block", children: [_jsx(RD.Title, { className: "modal__title", children: title }), description ? (_jsx(RD.Description, { className: "modal__description", children: description })) : (_jsx(RD.Description, { style: SR_ONLY, children: title }))] }), _jsx(RD.Close, { asChild: true, children: _jsx("button", { type: "button", className: "modal__close", "aria-label": t("actions.close"), children: _jsx(X, { size: 18 }) }) })] }), _jsx("div", { className: "modal__body", children: children }), footer && _jsx("footer", { className: "modal__footer", children: footer })] })] }) }));
}
