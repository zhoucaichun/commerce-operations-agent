import { ReactNode } from "react";

type BadgeTone = "default" | "success" | "warning" | "info";

type BadgeProps = {
  children: ReactNode;
  tone?: BadgeTone;
};

export function Badge({ children, tone = "default" }: BadgeProps) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
