import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { Badge, Button, Card, CardBody, CardHeader, ConfirmDialog, EmptyState, IconButton, Skeleton, Switch, } from "../../components/ui";
import { createBrandKeyword, deleteBrandKeyword, fetchBrandKeywords, fetchSchedulerJobs, patchBrandKeyword, } from "../../lib/api";
import { formatDate, formatRelativeTime } from "../../lib/format";
import { KeywordDialog } from "./KeywordDialog";
export function SchedulerView({ brandSlug }) {
    const { t, i18n } = useTranslation();
    const lang = i18n.resolvedLanguage ?? "en";
    const qc = useQueryClient();
    const keywordsQ = useQuery({
        queryKey: ["keywords", brandSlug],
        queryFn: () => fetchBrandKeywords(brandSlug),
        enabled: Boolean(brandSlug),
        staleTime: 10_000,
    });
    const schedulerQ = useQuery({
        queryKey: ["scheduler-jobs"],
        queryFn: fetchSchedulerJobs,
        staleTime: 30_000,
    });
    const [editing, setEditing] = useState(null);
    const [creating, setCreating] = useState(false);
    const [deleting, setDeleting] = useState(null);
    const invalidate = () => {
        qc.invalidateQueries({ queryKey: ["keywords", brandSlug] });
        qc.invalidateQueries({ queryKey: ["scheduler-jobs"] });
    };
    const createMut = useMutation({
        mutationFn: (body) => createBrandKeyword(brandSlug, body),
        onSuccess: () => {
            toast.success(t("scheduler_view.saved"));
            invalidate();
            setCreating(false);
        },
        onError: (e) => toast.error(e.message),
    });
    const updateMut = useMutation({
        mutationFn: ({ id, body }) => patchBrandKeyword(id, body),
        onSuccess: () => {
            toast.success(t("scheduler_view.saved"));
            invalidate();
            setEditing(null);
        },
        onError: (e) => toast.error(e.message),
    });
    const deleteMut = useMutation({
        mutationFn: (id) => deleteBrandKeyword(id),
        onSuccess: () => {
            toast.success(t("scheduler_view.deleted"));
            invalidate();
            setDeleting(null);
        },
        onError: (e) => toast.error(e.message),
    });
    const schedulerOff = schedulerQ.data?.enabled === false;
    return (_jsxs("div", { style: { display: "flex", flexDirection: "column", gap: 20 }, children: [_jsxs(Card, { children: [_jsx(CardHeader, { title: t("scheduler_view.title"), description: t("scheduler_view.intro"), action: _jsx(Button, { leftIcon: _jsx(Plus, { size: 14 }), onClick: () => setCreating(true), children: t("actions.add") }) }), _jsxs(CardBody, { children: [schedulerOff && (_jsxs("div", { className: "callout callout--warning", style: { marginBottom: 16 }, children: [_jsx(AlertTriangle, { size: 14 }), _jsx("span", { children: t("scheduler_view.scheduler_off_warning") })] })), keywordsQ.isLoading ? (_jsx(Skeleton, { width: "100%", height: 200 })) : (keywordsQ.data ?? []).length === 0 ? (_jsx(EmptyState, { title: t("scheduler_view.empty_title"), description: t("scheduler_view.empty_body"), action: _jsx(Button, { leftIcon: _jsx(Plus, { size: 14 }), onClick: () => setCreating(true), children: t("actions.add") }) })) : (_jsxs("table", { className: "domain-table", style: { marginTop: 4 }, children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: t("scheduler_view.headers.keyword") }), _jsx("th", { children: t("scheduler_view.headers.geo") }), _jsx("th", { children: t("scheduler_view.headers.frequency") }), _jsx("th", { children: t("scheduler_view.headers.last_scan") }), _jsx("th", { children: t("scheduler_view.headers.next_run") }), _jsx("th", { children: t("scheduler_view.headers.active") }), _jsx("th", { style: { textAlign: "right" }, children: t("scheduler_view.headers.actions") })] }) }), _jsx("tbody", { children: (keywordsQ.data ?? []).map((kw) => (_jsxs("tr", { children: [_jsx("td", { children: _jsx("div", { style: { fontWeight: 500 }, children: kw.keyword }) }), _jsx("td", { children: _jsx(Badge, { tone: "muted", children: kw.geo }) }), _jsx("td", { className: "domain-table__conf", children: t("scheduler_view.every_hours", { n: kw.frequency_hours }) }), _jsx("td", { className: "domain-table__conf", children: kw.last_scan_at ? (_jsx("span", { title: formatDate(kw.last_scan_at, lang), children: formatRelativeTime(kw.last_scan_at, lang) })) : (_jsx("span", { style: { color: "var(--text-subtle)" }, children: t("common.n_a") })) }), _jsx("td", { className: "domain-table__conf", children: kw.next_run_at ? (_jsx("span", { title: formatDate(kw.next_run_at, lang), children: formatRelativeTime(kw.next_run_at, lang) })) : (_jsx("span", { style: { color: "var(--text-subtle)" }, children: t("common.n_a") })) }), _jsx("td", { children: _jsx(Switch, { checked: kw.active, onChange: (v) => updateMut.mutate({ id: kw.id, body: { active: v } }), ariaLabel: t("scheduler_view.headers.active"), size: "sm" }) }), _jsx("td", { style: { textAlign: "right" }, children: _jsxs("span", { style: { display: "inline-flex", gap: 4 }, children: [_jsx(IconButton, { size: "sm", "aria-label": t("actions.edit"), onClick: () => setEditing(kw), children: _jsx(Pencil, { size: 14 }) }), _jsx(IconButton, { size: "sm", tone: "danger", "aria-label": t("actions.delete"), onClick: () => setDeleting(kw), children: _jsx(Trash2, { size: 14 }) })] }) })] }, kw.id))) })] }))] })] }), _jsx(KeywordDialog, { open: creating, onClose: () => setCreating(false), onSubmit: (values) => createMut.mutate(values), busy: createMut.isPending }), _jsx(KeywordDialog, { open: Boolean(editing), initial: editing, onClose: () => setEditing(null), onSubmit: (values) => {
                    if (editing)
                        updateMut.mutate({ id: editing.id, body: values });
                }, busy: updateMut.isPending }), _jsx(ConfirmDialog, { open: Boolean(deleting), title: t("scheduler_view.delete_confirm_title"), body: deleting
                    ? t("scheduler_view.delete_confirm_body", {
                        keyword: deleting.keyword,
                        geo: deleting.geo,
                    })
                    : null, busy: deleteMut.isPending, onClose: () => setDeleting(null), onConfirm: () => deleting && deleteMut.mutate(deleting.id) })] }));
}
