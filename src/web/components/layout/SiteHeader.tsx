import Link from "next/link";
import { Button } from "../ui/Button";

type SiteHeaderProps = {
  backHref?: string;
  backLabel?: string;
  rightAction?: {
    href: string;
    label: string;
    variant?: "primary" | "secondary";
  };
};

export function SiteHeader({
  backHref,
  backLabel = "Back",
  rightAction
}: SiteHeaderProps) {
  return (
    <header className="topbar">
      <div className="container topbar-inner">
        <div className="topbar-left">
          {backHref ? (
            <Link href={backHref} className="back-link" aria-label={backLabel}>
              <span className="back-link-icon" aria-hidden="true">
                {"<"}
              </span>
              <span>{backLabel}</span>
            </Link>
          ) : null}

          <Link href="/" className="brand brand-home" aria-label="Home">
            <span className="brand-mark">3C</span>
            <span className="brand-home-text">
              <span className="brand-home-label">Home</span>
              <span className="brand-home-name">ShopPilot 3C</span>
            </span>
          </Link>
        </div>

        {rightAction ? (
          <Button href={rightAction.href} variant={rightAction.variant}>
            {rightAction.label}
          </Button>
        ) : null}
      </div>
    </header>
  );
}
