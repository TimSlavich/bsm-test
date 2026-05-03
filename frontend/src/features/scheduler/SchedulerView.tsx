import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  ConfirmDialog,
  EmptyState,
  IconButton,
  Skeleton,
  Switch,
} from "../../components/ui";
import {
  createBrandKeyword,
  deleteBrandKeyword,
  fetchBrandKeywords,
  fetchSchedulerJobs,
  patchBrandKeyword,
  type BrandKeyword,
  type KeywordCreate,
} from "../../lib/api";
import { formatDate, formatRelativeTime } from "../../lib/format";
import { KeywordDialog } from "./KeywordDialog";

interface SchedulerViewProps {
  brandSlug: string;
}

export function SchedulerView({ brandSlug }: SchedulerViewProps) {
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

  const [editing, setEditing] = useState<BrandKeyword | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<BrandKeyword | null>(null);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["keywords", brandSlug] });
    qc.invalidateQueries({ queryKey: ["scheduler-jobs"] });
  };

  const createMut = useMutation({
    mutationFn: (body: KeywordCreate) => createBrandKeyword(brandSlug, body),
    onSuccess: () => {
      toast.success(t("scheduler_view.saved"));
      invalidate();
      setCreating(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<KeywordCreate> }) =>
      patchBrandKeyword(id, body),
    onSuccess: () => {
      toast.success(t("scheduler_view.saved"));
      invalidate();
      setEditing(null);
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteBrandKeyword(id),
    onSuccess: () => {
      toast.success(t("scheduler_view.deleted"));
      invalidate();
      setDeleting(null);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const schedulerOff = schedulerQ.data?.enabled === false;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <Card>
        <CardHeader
          title={t("scheduler_view.title")}
          description={t("scheduler_view.intro")}
          action={
            <Button leftIcon={<Plus size={14} />} onClick={() => setCreating(true)}>
              {t("actions.add")}
            </Button>
          }
        />
        <CardBody>
          {schedulerOff && (
            <div className="callout callout--warning" style={{ marginBottom: 16 }}>
              <AlertTriangle size={14} />
              <span>{t("scheduler_view.scheduler_off_warning")}</span>
            </div>
          )}
          {keywordsQ.isLoading ? (
            <Skeleton width="100%" height={200} />
          ) : (keywordsQ.data ?? []).length === 0 ? (
            <EmptyState
              title={t("scheduler_view.empty_title")}
              description={t("scheduler_view.empty_body")}
              action={
                <Button leftIcon={<Plus size={14} />} onClick={() => setCreating(true)}>
                  {t("actions.add")}
                </Button>
              }
            />
          ) : (
            <table className="domain-table" style={{ marginTop: 4 }}>
              <thead>
                <tr>
                  <th>{t("scheduler_view.headers.keyword")}</th>
                  <th>{t("scheduler_view.headers.geo")}</th>
                  <th>{t("scheduler_view.headers.frequency")}</th>
                  <th>{t("scheduler_view.headers.last_scan")}</th>
                  <th>{t("scheduler_view.headers.next_run")}</th>
                  <th>{t("scheduler_view.headers.active")}</th>
                  <th style={{ textAlign: "right" }}>{t("scheduler_view.headers.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {(keywordsQ.data ?? []).map((kw) => (
                  <tr key={kw.id}>
                    <td>
                      <div style={{ fontWeight: 500 }}>{kw.keyword}</div>
                    </td>
                    <td>
                      <Badge tone="muted">{kw.geo}</Badge>
                    </td>
                    <td className="domain-table__conf">
                      {t("scheduler_view.every_hours", { n: kw.frequency_hours })}
                    </td>
                    <td className="domain-table__conf">
                      {kw.last_scan_at ? (
                        <span title={formatDate(kw.last_scan_at, lang)}>
                          {formatRelativeTime(kw.last_scan_at, lang)}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-subtle)" }}>{t("common.n_a")}</span>
                      )}
                    </td>
                    <td className="domain-table__conf">
                      {kw.next_run_at ? (
                        <span title={formatDate(kw.next_run_at, lang)}>
                          {formatRelativeTime(kw.next_run_at, lang)}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-subtle)" }}>{t("common.n_a")}</span>
                      )}
                    </td>
                    <td>
                      <Switch
                        checked={kw.active}
                        onChange={(v) => updateMut.mutate({ id: kw.id, body: { active: v } })}
                        ariaLabel={t("scheduler_view.headers.active")}
                        size="sm"
                      />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <span style={{ display: "inline-flex", gap: 4 }}>
                        <IconButton
                          size="sm"
                          aria-label={t("actions.edit")}
                          onClick={() => setEditing(kw)}
                        >
                          <Pencil size={14} />
                        </IconButton>
                        <IconButton
                          size="sm"
                          tone="danger"
                          aria-label={t("actions.delete")}
                          onClick={() => setDeleting(kw)}
                        >
                          <Trash2 size={14} />
                        </IconButton>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
      {/* (single card now contains both the heading and the keyword table) */}

      <KeywordDialog
        open={creating}
        onClose={() => setCreating(false)}
        onSubmit={(values) => createMut.mutate(values)}
        busy={createMut.isPending}
      />
      <KeywordDialog
        open={Boolean(editing)}
        initial={editing}
        onClose={() => setEditing(null)}
        onSubmit={(values) => {
          if (editing) updateMut.mutate({ id: editing.id, body: values });
        }}
        busy={updateMut.isPending}
      />
      <ConfirmDialog
        open={Boolean(deleting)}
        title={t("scheduler_view.delete_confirm_title")}
        body={
          deleting
            ? t("scheduler_view.delete_confirm_body", {
                keyword: deleting.keyword,
                geo: deleting.geo,
              })
            : null
        }
        busy={deleteMut.isPending}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMut.mutate(deleting.id)}
      />
    </div>
  );
}
