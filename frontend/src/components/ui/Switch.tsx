import { cn } from "../../lib/cn";

interface SwitchProps {
  checked: boolean;
  onChange: (next: boolean) => void;
  ariaLabel?: string;
  size?: "sm" | "md";
  disabled?: boolean;
}

export function Switch({ checked, onChange, ariaLabel, size = "md", disabled }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      className={cn("switch", `switch--${size}`, checked && "switch--on")}
      onClick={() => !disabled && onChange(!checked)}
    >
      <span className="switch__thumb" />
    </button>
  );
}
