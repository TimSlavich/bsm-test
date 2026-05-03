import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as RP from "@radix-ui/react-popover";
import { Info } from "lucide-react";
import { useTranslation } from "react-i18next";
/**
 * The discreet ``(?)`` icon that opens an explanation popover. Used next to
 * chart titles so users can learn what each visual means without leaving
 * the page.
 */
export function InfoPopover({ title, children }) {
    const { t } = useTranslation();
    return (_jsxs(RP.Root, { children: [_jsx(RP.Trigger, { asChild: true, children: _jsx("button", { type: "button", className: "info-trigger", "aria-label": t("common.info"), children: _jsx(Info, { size: 14 }) }) }), _jsx(RP.Portal, { children: _jsxs(RP.Content, { className: "popover", sideOffset: 8, align: "start", children: [title && _jsx("div", { className: "popover__title", children: title }), _jsx("div", { className: "popover__body", children: children }), _jsx(RP.Arrow, { className: "popover__arrow" })] }) })] }));
}
