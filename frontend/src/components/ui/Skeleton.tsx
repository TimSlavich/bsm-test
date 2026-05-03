import type { CSSProperties, HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: number | string;
  height?: number | string;
  rounded?: boolean | "full";
}

export function Skeleton({ width, height, rounded = true, className, style, ...rest }: SkeletonProps) {
  const merged: CSSProperties = {
    ...style,
    width,
    height,
    borderRadius: rounded === "full" ? "999px" : rounded ? "var(--radius-sm)" : 0,
  };
  return <div className={cn("skeleton", className)} style={merged} {...rest} />;
}
