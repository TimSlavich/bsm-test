import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { forwardRef } from "react";
import { cn } from "../../lib/cn";
export const Card = forwardRef(function Card({ className, children, ...rest }, ref) {
    return (_jsx("div", { ref: ref, className: cn("card", className), ...rest, children: children }));
});
export function CardHeader({ title, description, action, className, ...rest }) {
    return (_jsxs("div", { className: cn("card__header", className), ...rest, children: [_jsxs("div", { className: "card__header-text", children: [_jsx("h2", { className: "card__title", children: title }), description && _jsx("p", { className: "card__description", children: description })] }), action && _jsx("div", { className: "card__header-action", children: action })] }));
}
export function CardBody({ className, children, ...rest }) {
    return (_jsx("div", { className: cn("card__body", className), ...rest, children: children }));
}
