type StepCardProps = {
  index: string;
  title: string;
  description: string;
};

export function StepCard({ index, title, description }: StepCardProps) {
  return (
    <article className="step-card">
      <div className="step-badge">{index}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}
