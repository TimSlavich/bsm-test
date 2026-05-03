import * as RT from "@radix-ui/react-tooltip";
import type { ReactNode } from "react";

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  side?: "top" | "right" | "bottom" | "left";
  align?: "start" | "center" | "end";
  delayDuration?: number;
}

export function Tooltip({ content, children, side = "top", align = "center", delayDuration = 250 }: TooltipProps) {
  return (
    <RT.Provider delayDuration={delayDuration}>
      <RT.Root>
        <RT.Trigger asChild>{children}</RT.Trigger>
        <RT.Portal>
          <RT.Content className="tooltip" side={side} align={align} sideOffset={6}>
            {content}
            <RT.Arrow className="tooltip__arrow" />
          </RT.Content>
        </RT.Portal>
      </RT.Root>
    </RT.Provider>
  );
}
