import { useTranslation } from "react-i18next";

import { Modal } from "../../components/ui";

interface MethodologyModalProps {
  open: boolean;
  onClose: () => void;
}

export function MethodologyModal({ open, onClose }: MethodologyModalProps) {
  const { t } = useTranslation();
  return (
    <Modal
      open={open}
      onClose={onClose}
      size="lg"
      title={t("methodology.title")}
      description={t("methodology.intro")}
    >
      <div className="methodology">
        <h3>{t("methodology.stage1_title")}</h3>
        <p>{t("methodology.stage1_body")}</p>
        <h3>{t("methodology.stage2_title")}</h3>
        <p>{t("methodology.stage2_body")}</p>
        <h3>{t("methodology.stage3_title")}</h3>
        <p>{t("methodology.stage3_body")}</p>
        <h3>{t("methodology.signals_title")}</h3>
        <p>{t("methodology.signals_body")}</p>
        <h3>{t("methodology.taxonomy_title")}</h3>
        <p>{t("methodology.taxonomy_body")}</p>
      </div>
    </Modal>
  );
}
