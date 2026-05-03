import { useQuery } from "@tanstack/react-query";
import { Bot, Calendar, CalendarClock } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Card, CardBody, CardHeader, Skeleton } from "../../components/ui";
import { fetchSchedulerJobs } from "../../lib/api";
import { formatRelativeTime } from "../../lib/format";
import type { BrandSnapshotSummary } from "../../lib/api";

interface HealthCardProps {
  latestSnapshot: BrandSnapshotSummary | null;
}

export function HealthCard({ latestSnapshot }: HealthCardProps) {
  const { t, i18n } = useTranslation();
  const scheduler = useQuery({
    queryKey: ["scheduler-jobs"],
    queryFn: fetchSchedulerJobs,
    staleTime: 30_000,
  });

  return (
    <Card>
      <CardHeader title={t("health.title")} />
      <CardBody className="health">
        <div className="health__row">
          <span className="health__label">
            <Calendar size={12} /> {t("health.last_scan")}
          </span>
          <span className="health__value">
            {latestSnapshot
              ? formatRelativeTime(latestSnapshot.captured_at, i18n.resolvedLanguage ?? "en")
              : t("health.never")}
          </span>
        </div>
        <div className="health__row">
          <span className="health__label">
            <CalendarClock size={12} /> {t("health.scheduler")}
          </span>
          <span className="health__value">
            {scheduler.isLoading ? (
              <Skeleton width={80} height={12} />
            ) : scheduler.data?.enabled ? (
              <>
                <span className="health__dot health__dot--ok" />
                {t("health.scheduler_running", { n: scheduler.data.jobs.length })}
              </>
            ) : (
              <>
                <span className="health__dot health__dot--off" />
                {t("health.scheduler_off")}
              </>
            )}
          </span>
        </div>
        <div className="health__row">
          <span className="health__label">
            <Bot size={12} /> {t("health.llm")}
          </span>
          <span className="health__value">
            <span className="health__dot health__dot--ok" />
            {t("health.llm_ready")}
          </span>
        </div>
      </CardBody>
    </Card>
  );
}
