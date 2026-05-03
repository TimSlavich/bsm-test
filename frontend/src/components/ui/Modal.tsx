import * as RD from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
}

/** Visually hidden but reachable to assistive tech. */
const SR_ONLY: React.CSSProperties = {
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0,0,0,0)",
  whiteSpace: "nowrap",
  border: 0,
};

export function Modal({ open, onClose, title, description, children, footer, size = "md" }: ModalProps) {
  const { t } = useTranslation();
  // Radix logs a dev warning unless either ``<Dialog.Description>`` is in
  // the tree or ``aria-describedby={undefined}`` is set on Content. We
  // always render Description: if the caller supplied text, it's visible;
  // otherwise we fall back to an SR-only label derived from the title so
  // screen readers still get a meaningful announcement.
  return (
    <RD.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <RD.Portal>
        <RD.Overlay className="modal__overlay" />
        <RD.Content className={`modal modal--${size}`}>
          <header className="modal__header">
            <div className="modal__title-block">
              <RD.Title className="modal__title">{title}</RD.Title>
              {description ? (
                <RD.Description className="modal__description">{description}</RD.Description>
              ) : (
                <RD.Description style={SR_ONLY}>{title}</RD.Description>
              )}
            </div>
            <RD.Close asChild>
              <button type="button" className="modal__close" aria-label={t("actions.close")}>
                <X size={18} />
              </button>
            </RD.Close>
          </header>
          <div className="modal__body">{children}</div>
          {footer && <footer className="modal__footer">{footer}</footer>}
        </RD.Content>
      </RD.Portal>
    </RD.Root>
  );
}
