import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useQuery } from "@tanstack/react-query";
import { Bot, Calendar, CalendarClock } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Card, CardBody, CardHeader, Skeleton } from "../../components/ui";
import { fetchSchedulerJobs } from "../../lib/api";
import { formatRelativeTime } from "../../lib/format";
export function HealthCard({ latestSnapshot }) {
    const { t, i18n } = useTranslation();
    const scheduler = useQuery({
        queryKey: ["scheduler-jobs"],
        queryFn: fetchSchedulerJobs,
        staleTime: 30_000,
    });
    return (_jsxs(Card, { children: [_jsx(CardHeader, { title: t("health.title") }), _jsxs(CardBody, { className: "health", children: [_jsxs("div", { className: "health__row", children: [_jsxs("span", { className: "health__label", children: [_jsx(Calendar, { size: 12 }), " ", t("health.last_scan")] }), _jsx("span", { className: "health__value", children: latestSnapshot
                                    ? formatRelativeTime(latestSnapshot.captured_at, i18n.resolvedLanguage ?? "en")
                                    : t("health.never") })] }), _jsxs("div", { className: "health__row", children: [_jsxs("span", { className: "health__label", children: [_jsx(CalendarClock, { size: 12 }), " ", t("health.scheduler")] }), _jsx("span", { className: "health__value", children: scheduler.isLoading ? (_jsx(Skeleton, { width: 80, height: 12 })) : scheduler.data?.enabled ? (_jsxs(_Fragment, { children: [_jsx("span", { className: "health__dot health__dot--ok" }), t("health.scheduler_running", { n: scheduler.data.jobs.length })] })) : (_jsxs(_Fragment, { children: [_jsx("span", { className: "health__dot health__dot--off" }), t("health.scheduler_off")] })) })] }), _jsxs("div", { className: "health__row", children: [_jsxs("span", { className: "health__label", children: [_jsx(Bot, { size: 12 }), " ", t("health.llm")] }), _jsxs("span", { className: "health__value", children: [_jsx("span", { className: "health__dot health__dot--ok" }), t("health.llm_ready")] })] })] })] }));
}
