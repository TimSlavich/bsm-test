import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { forwardRef } from "react";
import { cn } from "../../lib/cn";
export const Input = forwardRef(function Input({ leftIcon, rightSlot, className, ...rest }, ref) {
    return (_jsxs("span", { className: cn("input", className), children: [leftIcon && _jsx("span", { className: "input__icon", children: leftIcon }), _jsx("input", { ref: ref, className: "input__el", ...rest }), rightSlot && _jsx("span", { className: "input__right", children: rightSlot })] }));
});
export function Field({ label, hint, htmlFor, children }) {
    return (_jsxs("label", { className: "field", htmlFor: htmlFor, children: [_jsxs("span", { className: "field__label", children: [label, hint && _jsx("span", { className: "field__hint", children: hint })] }), children] }));
}
