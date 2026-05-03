import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "sm" | "md";
  tone?: "neutral" | "primary" | "danger";
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { size = "md", tone = "neutral", className, ...rest },
  ref,
) {
  return <button ref={ref} className={cn("icon-btn", `icon-btn--${size}`, `icon-btn--${tone}`, className)} {...rest} />;
});
