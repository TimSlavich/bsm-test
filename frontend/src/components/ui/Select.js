import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as RS from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
export function Select({ value, onChange, options, placeholder, ariaLabel, size = "md" }) {
    return (_jsxs(RS.Root, { value: value, onValueChange: onChange, children: [_jsxs(RS.Trigger, { className: `select select--${size}`, "aria-label": ariaLabel, children: [_jsx(RS.Value, { placeholder: placeholder }), _jsx(RS.Icon, { children: _jsx(ChevronDown, { size: 14 }) })] }), _jsx(RS.Portal, { children: _jsx(RS.Content, { className: "select__content", position: "popper", sideOffset: 4, children: _jsx(RS.Viewport, { className: "select__viewport", children: options.map((opt) => (_jsxs(RS.Item, { value: opt.value, disabled: opt.disabled, className: "select__item", children: [_jsx(RS.ItemText, { children: opt.label }), _jsx(RS.ItemIndicator, { className: "select__indicator", children: _jsx(Check, { size: 14 }) })] }, opt.value))) }) }) })] }));
}
