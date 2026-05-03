import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useTranslation } from "react-i18next";
import { Modal } from "../../components/ui";
export function MethodologyModal({ open, onClose }) {
    const { t } = useTranslation();
    return (_jsx(Modal, { open: open, onClose: onClose, size: "lg", title: t("methodology.title"), description: t("methodology.intro"), children: _jsxs("div", { className: "methodology", children: [_jsx("h3", { children: t("methodology.stage1_title") }), _jsx("p", { children: t("methodology.stage1_body") }), _jsx("h3", { children: t("methodology.stage2_title") }), _jsx("p", { children: t("methodology.stage2_body") }), _jsx("h3", { children: t("methodology.stage3_title") }), _jsx("p", { children: t("methodology.stage3_body") }), _jsx("h3", { children: t("methodology.signals_title") }), _jsx("p", { children: t("methodology.signals_body") }), _jsx("h3", { children: t("methodology.taxonomy_title") }), _jsx("p", { children: t("methodology.taxonomy_body") })] }) }));
}
