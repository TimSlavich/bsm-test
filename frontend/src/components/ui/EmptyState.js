import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { cn } from "../../lib/cn";
export function EmptyState({ icon, title, description, action, className }) {
    return (_jsxs("div", { className: cn("empty-state", className), children: [icon && _jsx("div", { className: "empty-state__icon", children: icon }), _jsx("h3", { className: "empty-state__title", children: title }), description && _jsx("p", { className: "empty-state__description", children: description }), action && _jsx("div", { className: "empty-state__action", children: action })] }));
}
