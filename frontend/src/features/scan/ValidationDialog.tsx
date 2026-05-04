/**
 * Friendly modal that surfaces scan-form validation problems.
 *
 * The backend returns a list of ``{field, code, message}`` records;
 * we map ``code`` to a localized, human-readable line via i18n templates
 * (``validation.<code>`` keys) and fall back to the backend's English
 * message only if a code is brand new and not yet translated.
 */
import { AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button, Modal } from "../../components/ui";
import type { ValidationProblem } from "../../lib/api";

interface ValidationDialogProps {
  problems: ValidationProblem[];
  onClose: () => void;
}

export function ValidationDialog({ problems, onClose }: ValidationDialogProps) {
  const { t } = useTranslation();
  const open = problems.length > 0;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={
        <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
          <AlertTriangle
            size={20}
            color="var(--danger, #e5484d)"
            aria-hidden
          />
          {t("validation.title")}
        </span>
      }
      description={t("validation.subtitle")}
      size="sm"
      footer={
        <Button onClick={onClose} fullWidth>
          {t("validation.dismiss")}
        </Button>
      }
    >
      <ul className="validation-list">
        {problems.map((p, i) => {
          const key = `validation.${p.code}`;
          const localized = t(key, { defaultValue: p.message });
          return (
            <li key={`${p.field}-${i}`} className="validation-list__item">
              {localized}
            </li>
          );
        })}
      </ul>
    </Modal>
  );
}
