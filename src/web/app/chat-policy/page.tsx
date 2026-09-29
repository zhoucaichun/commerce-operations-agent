import { SiteHeader } from "../../components/layout/SiteHeader";
import { PromptLauncher } from "../../components/chat/PromptLauncher";

const suggestions = [
  "How long does shipping to the US take?",
  "What is the return window?",
  "Do you have student discount?",
  "What about warranty support?"
];

export default function ChatPolicyPage() {
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
            <h1>Policy Answer</h1>
            <p>Policy Q&A rendered as a structured support-style response</p>
          </div>
        </div>

        <PromptLauncher
          title="Start a policy question"
          description="Ask about shipping, returns, warranty, discounts, or other store policy details."
          suggestions={suggestions}
        />
      </div>
    </main>
  );
}
