import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef } from "react";
import { cn } from "../../lib/cn";
export const IconButton = forwardRef(function IconButton({ size = "md", tone = "neutral", className, ...rest }, ref) {
    return _jsx("button", { ref: ref, className: cn("icon-btn", `icon-btn--${size}`, `icon-btn--${tone}`, className), ...rest });
});
