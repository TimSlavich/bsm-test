import { jsx as _jsx } from "react/jsx-runtime";
import { cn } from "../../lib/cn";
export function Spinner({ size = 16, className }) {
    return (_jsx("span", { className: cn("spinner", className), style: { width: size, height: size }, role: "status", "aria-live": "polite" }));
}
