import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { forwardRef } from "react";
import { cn } from "../../lib/cn";
export const Button = forwardRef(function Button({ variant = "primary", size = "md", loading = false, disabled, leftIcon, rightIcon, fullWidth, className, children, ...rest }, ref) {
    return (_jsxs("button", { ref: ref, className: cn("btn", `btn--${variant}`, `btn--${size}`, fullWidth && "btn--full", className), disabled: disabled || loading, "data-loading": loading || undefined, ...rest, children: [loading && _jsx("span", { className: "btn__spinner", "aria-hidden": true }), !loading && leftIcon && _jsx("span", { className: "btn__icon", children: leftIcon }), _jsx("span", { className: "btn__label", children: children }), !loading && rightIcon && _jsx("span", { className: "btn__icon", children: rightIcon })] }));
});
