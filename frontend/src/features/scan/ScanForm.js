import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { Play } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import { Button, Field, Input, Tooltip } from "../../components/ui";
export function ScanForm({ values, onChange, onSubmit, isRunning }) {
    const { t } = useTranslation();
    const ids = {
        brand: useId(),
        keyword: useId(),
        geo: useId(),
        top_n: useId(),
    };
    const set = (k, v) => onChange({ ...values, [k]: v });
    return (_jsxs("form", { className: "scan-form", onSubmit: (e) => {
            e.preventDefault();
            onSubmit();
        }, children: [_jsx(Field, { label: _jsxs(_Fragment, { children: [t("scan_form.brand"), _jsx(Tooltip, { content: t("scan_form.tooltip_brand"), side: "right", children: _jsx("span", { className: "field__why", "aria-hidden": true, children: "?" }) })] }), htmlFor: ids.brand, children: _jsx(Input, { id: ids.brand, value: values.brand_slug, onChange: (e) => set("brand_slug", e.target.value), autoComplete: "off", spellCheck: false }) }), _jsx(Field, { label: _jsxs(_Fragment, { children: [t("scan_form.keyword"), _jsx(Tooltip, { content: t("scan_form.tooltip_keyword"), side: "right", children: _jsx("span", { className: "field__why", "aria-hidden": true, children: "?" }) })] }), htmlFor: ids.keyword, children: _jsx(Input, { id: ids.keyword, value: values.keyword, onChange: (e) => set("keyword", e.target.value), autoComplete: "off" }) }), _jsxs("div", { className: "scan-form__row", children: [_jsx(Field, { label: _jsxs(_Fragment, { children: [t("scan_form.geo"), _jsx(Tooltip, { content: t("scan_form.tooltip_geo"), side: "right", children: _jsx("span", { className: "field__why", "aria-hidden": true, children: "?" }) })] }), htmlFor: ids.geo, children: _jsx(Input, { id: ids.geo, value: values.geo, onChange: (e) => set("geo", e.target.value.toUpperCase().slice(0, 4)), maxLength: 4, autoComplete: "off" }) }), _jsx(Field, { label: _jsxs(_Fragment, { children: [t("scan_form.top_n"), _jsx(Tooltip, { content: t("scan_form.tooltip_top_n"), side: "right", children: _jsx("span", { className: "field__why", "aria-hidden": true, children: "?" }) })] }), htmlFor: ids.top_n, children: _jsx(Input, { id: ids.top_n, type: "number", min: 1, max: 20, value: values.top_n, onChange: (e) => set("top_n", Math.max(1, Math.min(20, Number(e.target.value) || 10))) }) })] }), _jsx(Button, { type: "submit", loading: isRunning, fullWidth: true, leftIcon: _jsx(Play, { size: 14 }), size: "lg", children: isRunning ? t("actions.scanning") : t("actions.run_scan") })] }));
}
