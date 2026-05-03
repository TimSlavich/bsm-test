import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function AppShell({ topbar, sidebar, main, rightRail }) {
    return (_jsxs("div", { className: "shell", "data-has-rail": rightRail ? "true" : undefined, children: [_jsx("div", { className: "shell__topbar", children: topbar }), _jsx("aside", { className: "shell__sidebar", children: sidebar }), _jsx("main", { className: "shell__main", children: main }), rightRail && _jsx("aside", { className: "shell__rail", children: rightRail })] }));
}
