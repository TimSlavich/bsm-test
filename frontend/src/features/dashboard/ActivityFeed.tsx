import { CheckCircle2, Search } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Card, CardBody, CardHeader, EmptyState } from "../../components/ui";
import { formatRelativeTime } from "../../lib/format";
import type { BrandSnapshotSummary } from "../../lib/api";

interface ActivityFeedProps {
  snapshots: BrandSnapshotSummary[];
}

export function ActivityFeed({ snapshots }: ActivityFeedProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "en";

  return (
    <Card>
      <CardHeader title={t("activity.title")} />
      <CardBody>
        {snapshots.length === 0 ? (
          <EmptyState icon={<Search size={20} />} title={t("activity.empty")} />
        ) : (
          <ul className="activity">
            {snapshots.slice(0, 8).map((s) => (
              <li key={s.snapshot_id} className="activity__item">
                <span className="activity__icon" aria-hidden>
                  <CheckCircle2 size={12} />
                </span>
                <div className="activity__title">
                  {t("activity.scan_completed", { id: s.snapshot_id, keyword: s.keyword })}
                </div>
                <div className="activity__meta">
                  {formatRelativeTime(s.captured_at, lang)} · {s.geo} ·{" "}
                  {t("snapshot.n_hits", { n: s.n_results })}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
