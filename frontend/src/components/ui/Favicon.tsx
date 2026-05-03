import { cn } from "../../lib/cn";
import { faviconFor } from "../../lib/format";

interface FaviconProps {
  domain: string;
  size?: number;
  className?: string;
}

/**
 * Favicon. Backend proxy at ``/api/favicons/:domain`` always returns 200 OK
 * (resolved icon or deterministic SVG tile), so no DevTools 404 noise.
 */
export function Favicon({ domain, size = 16, className }: FaviconProps) {
  if (!domain) return null;
  return (
    <img
      src={faviconFor(domain, Math.max(32, size * 2))}
      alt=""
      width={size}
      height={size}
      className={cn("favicon", className)}
      loading="lazy"
      referrerPolicy="no-referrer"
    />
  );
}
