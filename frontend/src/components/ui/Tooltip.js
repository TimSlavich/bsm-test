import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as RT from "@radix-ui/react-tooltip";
export function Tooltip({ content, children, side = "top", align = "center", delayDuration = 250 }) {
    return (_jsx(RT.Provider, { delayDuration: delayDuration, children: _jsxs(RT.Root, { children: [_jsx(RT.Trigger, { asChild: true, children: children }), _jsx(RT.Portal, { children: _jsxs(RT.Content, { className: "tooltip", side: side, align: align, sideOffset: 6, children: [content, _jsx(RT.Arrow, { className: "tooltip__arrow" })] }) })] }) }));
}
