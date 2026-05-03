import { cn } from "../../lib/cn";

interface SpinnerProps {
  size?: number;
  className?: string;
}

export function Spinner({ size = 16, className }: SpinnerProps) {
  return (
    <span
      className={cn("spinner", className)}
      style={{ width: size, height: size }}
      role="status"
      aria-live="polite"
    />
  );
}
