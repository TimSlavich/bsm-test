import { jsx as _jsx } from "react/jsx-runtime";
import { cn } from "../../lib/cn";
export function Skeleton({ width, height, rounded = true, className, style, ...rest }) {
    const merged = {
        ...style,
        width,
        height,
        borderRadius: rounded === "full" ? "999px" : rounded ? "var(--radius-sm)" : 0,
    };
    return _jsx("div", { className: cn("skeleton", className), style: merged, ...rest });
}
