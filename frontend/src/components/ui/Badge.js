import { jsx as _jsx } from "react/jsx-runtime";
import { CATEGORY_BG, CATEGORY_FG } from "../../lib/categories";
import { cn } from "../../lib/cn";
export function Badge({ category, tone = "neutral", className, children, style, ...rest }) {
    const categoryStyle = category
        ? { background: CATEGORY_BG[category], color: CATEGORY_FG[category] }
        : undefined;
    return (_jsx("span", { className: cn("badge", `badge--${tone}`, category && `badge--cat-${category}`, className), style: { ...categoryStyle, ...style }, ...rest, children: children }));
}
