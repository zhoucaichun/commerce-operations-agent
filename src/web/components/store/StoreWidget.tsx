"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

type Turn = { role: "user" | "assistant"; text: string; agentResult?: AgentResponse };
type Attachment = { kind: "image" | "audio"; name: string; mime_type: string; size_bytes: number; demo_scenario: string };
type AgentResponse = { answer?: string; detail?: string; error?: string; tool_result_summary?: Array<{ citations?: Array<{ document_id: string; chunk_id: string; version: string }> }> };

function createThreadId() { return `store-widget-${crypto.randomUUID()}`; }

export function StoreWidget({ onClose }: { onClose: () => void }) {
  const [threadId] = useState(createThreadId);
  const [turns, setTurns] = useState<Turn[]>([{ role: "assistant", text: "Hi! Ask me about a product, compatibility, a policy, or a demo order." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    try {
      window.sessionStorage.setItem(`shoppilot-agent-thread:${threadId}`, JSON.stringify({
        messages: turns.map((turn) => ({ role: turn.role === "user" ? "user" : "ai", message: turn.text,
          meta: turn.role === "user" ? "You | just now" : "ShopPilot AI Assistant", agentResult: turn.agentResult })),
        threadId, conversationId: "", inputText: "", liveRecommendation: null
      }));
    } catch { /* The conversation remains usable without browser storage. */ }
  }, [threadId, turns]);
  async function send(text: string, attachments: Attachment[] = []) {
    const message = text.trim(); if (!message || loading) return;
    setTurns((current) => [...current, { role: "user", text: message }]); setInput(""); setLoading(true);
    try {
      const response = await fetch("/api/agent/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ thread_id: threadId, message, slots: {}, attachments }) });
      const data = await response.json() as AgentResponse;
      setTurns((current) => [...current, { role: "assistant", agentResult: response.ok ? data : undefined, text: response.ok ? data.answer || "No answer was returned." : data.detail || data.error || "The assistant is unavailable. Please try again." }]);
    } catch { setTurns((current) => [...current, { role: "assistant", text: "The assistant is unavailable. Please try again." }]); } finally { setLoading(false); }
  }
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); void send(input); }
  const fullChatHref = `/chat-demo?from=store&thread=${encodeURIComponent(threadId)}`;
  return <aside className="store-widget" aria-label="ShopPilot AI Assistant"><header><div><i>✦</i><strong>ShopPilot AI Assistant</strong><span>Online · demo data</span></div><button aria-label="Close assistant" onClick={onClose}>×</button></header><div className="store-widget-body"><div className="widget-chat-log" aria-live="polite">{turns.map((turn, index) => <p key={`${turn.role}-${index}`} className={turn.role === "assistant" ? "widget-bubble" : "widget-user-bubble"}>{turn.text}{turn.agentResult?.tool_result_summary?.flatMap((item) => item.citations || []).map((citation, citationIndex) => <small key={citationIndex} style={{ display: "block" }}>证据：{citation.document_id} / {citation.chunk_id} @ {citation.version}</small>)}</p>)}{loading ? <p className="widget-bubble">Thinking…</p> : null}</div>{turns.length === 1 ? <div className="widget-prompts"><button onClick={() => void send("Recommend a charging bundle for iPhone 15")}>Recommend a charging bundle</button><button onClick={() => void send("Is AC-65W compatible with MacBook Pro 14")}>Check compatibility</button><button onClick={() => void send("order ORD-10023 tracking 4821")}>Track my demo order</button></div> : null}<form className="widget-chat-form" onSubmit={submit}><input aria-label="Ask ShopPilot AI" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask a question…" /><button disabled={loading || !input.trim()} aria-label="Send message">↑</button></form><div className="widget-input-actions"><button type="button" onClick={() => void send("Please help with this voice request for a MacBook charger", [{ kind: "audio", name: "voice-macbook-demo.webm", mime_type: "audio/webm", size_bytes: 24000, demo_scenario: "voice_macbook" }])}>🎙 Voice demo</button><button type="button" onClick={() => void send("What accessory fits the product in this photo?", [{ kind: "image", name: "macbook-charger-demo.jpg", mime_type: "image/jpeg", size_bytes: 48000, demo_scenario: "macbook_charger" }])}>▣ Photo demo</button></div><small>Demo only: no media bytes are uploaded or retained.</small></div><footer><Link href={fullChatHref}>Open full conversation <span>→</span></Link></footer></aside>;
}
