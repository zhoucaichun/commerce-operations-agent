import { SiteHeader } from "../../components/layout/SiteHeader";
import { PromptLauncher } from "../../components/chat/PromptLauncher";

const suggestions = [
  "Can I use this travel adapter with my hair dryer in Japan?",
  "My charger started smoking. What should I do?",
  "Can I use a travel adapter for hospital equipment?",
  "My package says delivered but I did not receive it."
];

export default function ChatHandoffPage() {
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
            <h1>High-Risk Handoff</h1>
            <p>AI stops short and routes the case to human support</p>
          </div>
        </div>

        <PromptLauncher
          title="Start a support or safety question"
          description="Ask about risky usage, product issues, delivery problems, or cases that may need human support."
          suggestions={suggestions}
        />
      </div>
    </main>
  );
}
