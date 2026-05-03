import type { HTMLAttributes, ReactNode } from "react";
import { CATEGORY_BG, CATEGORY_FG, type CategoryKey } from "../../lib/categories";
import { cn } from "../../lib/cn";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  category?: CategoryKey;
  tone?: "neutral" | "success" | "warning" | "danger" | "muted";
  children: ReactNode;
}

export function Badge({ category, tone = "neutral", className, children, style, ...rest }: BadgeProps) {
  const categoryStyle = category
    ? { background: CATEGORY_BG[category], color: CATEGORY_FG[category] }
    : undefined;
  return (
    <span
      className={cn("badge", `badge--${tone}`, category && `badge--cat-${category}`, className)}
      style={{ ...categoryStyle, ...style }}
      {...rest}
    >
      {children}
    </span>
  );
}
