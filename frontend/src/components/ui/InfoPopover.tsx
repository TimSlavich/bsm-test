import * as RP from "@radix-ui/react-popover";
import { Info } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

interface InfoPopoverProps {
  title?: ReactNode;
  children: ReactNode;
}

/**
 * The discreet ``(?)`` icon that opens an explanation popover. Used next to
 * chart titles so users can learn what each visual means without leaving
 * the page.
 */
export function InfoPopover({ title, children }: InfoPopoverProps) {
  const { t } = useTranslation();
  return (
    <RP.Root>
      <RP.Trigger asChild>
        <button type="button" className="info-trigger" aria-label={t("common.info")}>
          <Info size={14} />
        </button>
      </RP.Trigger>
      <RP.Portal>
        <RP.Content className="popover" sideOffset={8} align="start">
          {title && <div className="popover__title">{title}</div>}
          <div className="popover__body">{children}</div>
          <RP.Arrow className="popover__arrow" />
        </RP.Content>
      </RP.Portal>
    </RP.Root>
  );
}
