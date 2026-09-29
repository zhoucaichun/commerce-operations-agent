import { FeatureCard } from "../components/home/FeatureCard";
import { StepCard } from "../components/home/StepCard";
import { SiteHeader } from "../components/layout/SiteHeader";
import { Button } from "../components/ui/Button";

const features = [
  {
    href: "/chat-demo",
    icon: "3C",
    title: "Smart Recommendations",
    description:
      "Get personalized product suggestions based on your device and needs."
  },
  {
    href: "/chat-compat",
    icon: "CK",
    title: "Compatibility Check",
    description:
      "Instant verification of accessory compatibility with your devices."
  },
  {
    href: "/chat-policy",
    icon: "P",
    title: "Policy Guidance",
    description:
      "Clear answers about shipping, returns, and warranty information."
  },
  {
    href: "/chat-handoff",
    icon: "!",
    title: "Instant Support",
    description:
      "Connect with human experts when you need additional help."
  }
];

const steps = [
  {
    index: "1",
    title: "Tell us about your device",
    description: "Share your device model and what you're looking for."
  },
  {
    index: "2",
    title: "Get AI recommendations",
    description: "Receive personalized, compatible product suggestions."
  },
  {
    index: "3",
    title: "Shop with confidence",
    description: "Make informed decisions backed by AI insights."
  }
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <SiteHeader
        rightAction={{ href: "/start", label: "Sign In", variant: "secondary" }}
      />

      <div className="container">
        <section className="hero">
          <h1 className="hero-title">ShopPilot 3C</h1>
          <p className="hero-subtitle">
            Cross-border 3C customer service copilot for product recommendations,
            compatibility checks, policy answers, and high-risk handoff.
          </p>

          <div className="hero-actions">
            <Button href="/start">Start Shopping</Button>
          </div>

          <div className="feature-grid">
            {features.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </section>

        <section className="section-panel">
          <h2 className="section-title">How It Works</h2>
          <div className="steps-grid">
            {steps.map((step) => (
              <StepCard key={step.index} {...step} />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
