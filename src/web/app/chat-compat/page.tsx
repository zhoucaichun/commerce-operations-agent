import { SiteHeader } from "../../components/layout/SiteHeader";
import { PromptLauncher } from "../../components/chat/PromptLauncher";

const suggestions = [
  "Will this 65W charger charge my MacBook Air M2 and iPhone 15 at the same time?",
  "Does the 20W USB-C charger work for iPhone 15?",
  "Can one USB-C cable work for my MacBook and iPhone 15?",
  "Will a Lightning cable work with iPhone 15?"
];

export default function ChatCompatPage() {
  return (
    <main className="page-shell">
      <SiteHeader
        backHref="/start"
        backLabel="Back"
        rightAction={{ href: "/start", label: "New Search", variant: "secondary" }}
      />

      <div className="state-page">
        <div className="state-header">
          <div className="state-title-wrap">
            <h1>Compatibility Check</h1>
            <p>Structured AI answer for compatibility questions</p>
          </div>
        </div>

        <PromptLauncher
          title="Start a compatibility check"
          description="Ask about devices, ports, power, cables, or travel adapter boundaries."
          suggestions={suggestions}
        />
      </div>
    </main>
  );
}
