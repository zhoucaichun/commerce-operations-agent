import Link from "next/link";
import { Card } from "../ui/Card";

type FeatureCardProps = {
  href: string;
  icon: string;
  title: string;
  description: string;
};

export function FeatureCard({
  href,
  icon,
  title,
  description
}: FeatureCardProps) {
  return (
    <Link href={href} className="feature-card-link" aria-label={title}>
      <Card className="feature-card">
        <div className="feature-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{description}</p>
      </Card>
    </Link>
  );
}
