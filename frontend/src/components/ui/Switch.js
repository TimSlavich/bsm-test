import { jsx as _jsx } from "react/jsx-runtime";
import { cn } from "../../lib/cn";
export function Switch({ checked, onChange, ariaLabel, size = "md", disabled }) {
    return (_jsx("button", { type: "button", role: "switch", "aria-checked": checked, "aria-label": ariaLabel, disabled: disabled, className: cn("switch", `switch--${size}`, checked && "switch--on"), onClick: () => !disabled && onChange(!checked), children: _jsx("span", { className: "switch__thumb" }) }));
}
