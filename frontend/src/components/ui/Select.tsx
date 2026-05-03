import * as RS from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

export interface SelectOption {
  value: string;
  label: ReactNode;
  disabled?: boolean;
}

interface SelectProps {
  value: string;
  onChange: (v: string) => void;
  options: SelectOption[];
  placeholder?: ReactNode;
  ariaLabel?: string;
  size?: "sm" | "md";
}

export function Select({ value, onChange, options, placeholder, ariaLabel, size = "md" }: SelectProps) {
  return (
    <RS.Root value={value} onValueChange={onChange}>
      <RS.Trigger className={`select select--${size}`} aria-label={ariaLabel}>
        <RS.Value placeholder={placeholder} />
        <RS.Icon>
          <ChevronDown size={14} />
        </RS.Icon>
      </RS.Trigger>
      <RS.Portal>
        <RS.Content className="select__content" position="popper" sideOffset={4}>
          <RS.Viewport className="select__viewport">
            {options.map((opt) => (
              <RS.Item key={opt.value} value={opt.value} disabled={opt.disabled} className="select__item">
                <RS.ItemText>{opt.label}</RS.ItemText>
                <RS.ItemIndicator className="select__indicator">
                  <Check size={14} />
                </RS.ItemIndicator>
              </RS.Item>
            ))}
          </RS.Viewport>
        </RS.Content>
      </RS.Portal>
    </RS.Root>
  );
}
