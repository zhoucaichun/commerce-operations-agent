import Link from "next/link";
import { PreChatForm } from "../../components/form/PreChatForm";
import { SiteHeader } from "../../components/layout/SiteHeader";

const deviceChips = [
  "iPhone 15 Pro",
  "iPhone 14",
  "Samsung Galaxy S24",
  "Google Pixel 8",
  "MacBook Pro M3"
];

const promptChips = [
  "Can you recommend a charging bundle for iPhone 15?",
  "Will this charger work with my MacBook Air M2?",
  "Do you have student discount?",
  "How long does shipping to the US take?"
];

export default function StartPage() {
  return (
    <main className="page-shell">
      <SiteHeader
        backHref="/"
        backLabel="Back"
        rightAction={{
          href: "/chat-demo",
          label: "Open Chat",
          variant: "secondary"
        }}
      />

      <div className="form-shell">
        <div className="form-heading">
          <h1>Ask ShopPilot 3C</h1>
          <p>
            Enter your question first. Device, country, budget, and scenario are
            optional helpers.
          </p>
        </div>

        <PreChatForm deviceChips={deviceChips} promptChips={promptChips} />

        <div className="form-footer-note">
          You can ask a question directly, or add optional context to help
          ShopPilot 3C answer more precisely.
          <div>
            <Link href="/chat-demo" className="form-footer-link">
              Open chat without extra context
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
