import { ChatBubble } from "../../components/chat/ChatBubble";
import { SiteHeader } from "../../components/layout/SiteHeader";

export default function ChatDefaultPage() {
  return (
    <main className="page-shell">
      <SiteHeader
        backHref="/start"
        backLabel="Back"
        rightAction={{ href: "/start", label: "New Search", variant: "secondary" }}
      />

      <div className="chat-shell">
        <div className="chat-header">
          <div className="chat-title-block">
            <div className="brand-mark">💬</div>
            <div>
              <div style={{ fontSize: 26, fontWeight: 700 }}>
                ShopPilot 3C
              </div>
              <div className="chat-status">
                <span className="status-dot">●</span> Active • Ready to help
              </div>
            </div>
          </div>
        </div>

        <section className="chat-main">
          <ChatBubble
            role="ai"
            message="Hi! I&apos;ll help you find the right accessory."
            description="Tell me your device model and what you&apos;re looking for, and I&apos;ll guide you from there."
            meta="AI Assistant • Just now"
          />
        </section>
      </div>
    </main>
  );
}
