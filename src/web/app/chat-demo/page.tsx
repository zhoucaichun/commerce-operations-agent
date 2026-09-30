"use client";

import { FormEvent, Fragment, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ChatBubble } from "../../components/chat/ChatBubble";
import { SiteHeader } from "../../components/layout/SiteHeader";
import { QuickReplyChips } from "../../components/recommendation/QuickReplyChips";
import { RecommendationCard } from "../../components/recommendation/RecommendationCard";
import { followupQuestions, recommendationProducts } from "../../lib/mock-data";
import { parseRecommendationAnswer } from "../../lib/recommendation-parser";
import { ProductRecommendation } from "../../lib/types";

type ChatMessage = {
  role: "user" | "ai";
  message: string;
  meta: string;
  description?: string;
  isThinking?: boolean;
  recommendation?: ProductRecommendation | null;
  agentResult?: AgentResponse | null;
};

type DifyResponse = {
  answer?: string;
  message?: string;
  conversation_id?: string;
  detail?: string;
  error?: string;
};

type AgentResponse = {
  status?: string;
  answer?: string;
  request_id?: string;
  thread_id?: string;
  handoff?: { reason?: string; summary?: string } | null;
  tool_result_summary?: Array<{ tool?: string }>;
  detail?: string;
  error?: string;
};

type StoredChatState = {
  messages: ChatMessage[];
  conversationId: string;
  inputText: string;
  liveRecommendation: ProductRecommendation | null;
};

const agentIntentPattern = /\b(order|tracking|shipment|policy|warranty|return|refund|ticket|human|compatib(?:ility|le))\b|订单|物流|包裹|轨迹|政策|保修|退货|退款|工单|人工|客服|兼容|适配/iu;

function isAgentIntent(query: string) {
  return agentIntentPattern.test(query);
}

function buildAgentPayload(query: string, threadId: string) {
  const orderId = query.match(/\bORD-\d{4,}\b/i)?.[0]?.toUpperCase();
  const suffixes = query.match(/(?<!\d)\d{4}(?!\d)/g) || [];
  const slots: Record<string, string> = {};
  if (orderId) slots.order_id = orderId;
  if (suffixes.length) slots.identity_suffix = suffixes[suffixes.length - 1];
  return { thread_id: threadId, message: query, slots };
}

function shouldUseCommerceAgent(query: string, fromStore: boolean) {
  return fromStore || isAgentIntent(query);
}

async function requestAgent(query: string, threadId: string) {
  const response = await fetch("/api/agent/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildAgentPayload(query, threadId))
  });
  const data = (await response.json()) as AgentResponse;
  if (!response.ok) {
    throw new Error(data.detail || data.error || `Commerce Agent request failed: ${response.status}`);
  }
  return data;
}

const starterQuestions = [
  "I use an iPhone 15 and want a charger under $25",
  "Can you recommend a charging bundle for iPhone 15?",
  "I want a travel charger for my MacBook Air M2",
  "Recommend a useful accessory under $15 for iPhone 15",
  "I need a charging cable for my device."
];

function buildChatMessages(query: string): ChatMessage[] {
  return [
    { role: "user", message: query, meta: "You | just now" },
    {
      role: "ai",
      message: "Please wait, I am thinking",
      meta: "ShopPilot 3C | typing...",
      isThinking: true
    }
  ];
}

function buildStorageKey(params: {
  query: string;
  country: string;
  deviceModel: string;
  budget: string;
  usageScenario: string;
}) {
  const search = new URLSearchParams();
  search.set("q", params.query);
  if (params.country) search.set("country", params.country);
  if (params.deviceModel) search.set("device_model", params.deviceModel);
  if (params.budget) search.set("budget", params.budget);
  if (params.usageScenario) search.set("usage_scenario", params.usageScenario);
  return `shoppilot-3c-chat-demo:${search.toString()}`;
}

function readStoredChat(key: string): StoredChatState | null {
  try {
    const raw = window.sessionStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as StoredChatState;
  } catch {
    return null;
  }
}

function writeStoredChat(key: string, state: StoredChatState) {
  try {
    window.sessionStorage.setItem(key, JSON.stringify(state));
  } catch {
    // Ignore storage failures.
  }
}

function inferRecommendation(
  messages: ChatMessage[],
  liveRecommendation: ProductRecommendation | null
) {
  if (liveRecommendation) return liveRecommendation;

  const lastAssistantMessage = [...messages]
    .reverse()
    .find((message) => message.role === "ai" && !message.isThinking);

  if (!lastAssistantMessage) return null;
  return parseRecommendationAnswer(lastAssistantMessage.message);
}

function attachRecommendationToLastAssistant(
  messages: ChatMessage[],
  recommendation: ProductRecommendation | null
) {
  if (!recommendation || messages.some((message) => message.recommendation)) {
    return messages;
  }

  const lastAssistantIndex = [...messages]
    .map((message, index) => ({ message, index }))
    .reverse()
    .find(({ message }) => message.role === "ai" && !message.isThinking)?.index;

  if (lastAssistantIndex === undefined) return messages;

  return messages.map((message, index) =>
    index === lastAssistantIndex ? { ...message, recommendation } : message
  );
}

function buildErrorCopy(error: unknown) {
  const detail = error instanceof Error ? error.message : "Unknown connection error.";
  const isTimeout = detail.toLowerCase().includes("timed out");

  return {
    message: isTimeout
      ? "The live AI answer is taking longer than expected."
      : "I could not connect to Dify successfully.",
    description: isTimeout
      ? "This usually means the live Dify workflow or model call is slow. You can try again, clear the chat, or use another example question."
      : detail
  };
}

function buildAgentErrorCopy(error: unknown) {
  const detail = error instanceof Error ? error.message : "Unknown connection error.";
  return {
    message: "The operations agent could not complete this request.",
    description: `${detail} No real order, inventory, refund, cancellation, or address action was performed.`
  };
}

function buildDifyInputs(params: {
  query: string;
  country: string;
  deviceModel: string;
  budget: string;
  usageScenario: string;
}) {
  const inferredDeviceModel = inferDeviceModel(params.query);
  const inferredBudget = inferBudget(params.query);
  const inferredUsageScenario = inferUsageScenario(params.query);

  return {
    country: params.country || "US",
    device_model: params.deviceModel || inferredDeviceModel,
    budget: params.budget || inferredBudget,
    usage_scenario: params.usageScenario || inferredUsageScenario
  };
}

function inferDeviceModel(query: string) {
  const normalized = query.toLowerCase();
  if (normalized.includes("iphone 15 pro")) return "iPhone 15 Pro";
  if (normalized.includes("iphone 15")) return "iPhone 15";
  if (normalized.includes("macbook air m2")) return "MacBook Air M2";
  if (normalized.includes("macbook air")) return "MacBook Air";
  if (normalized.includes("macbook pro 14")) return "MacBook Pro 14";
  if (normalized.includes("samsung s24") || normalized.includes("galaxy s24")) {
    return "Samsung S24";
  }
  return "";
}

function inferBudget(query: string) {
  const budgetMatch = query.match(/(?:under|below|within|less than)\s*\$?\s*(\d+)/i);
  if (budgetMatch?.[1]) return `under $${budgetMatch[1]}`;

  const dollarMatch = query.match(/\$\s*(\d+)/);
  if (dollarMatch?.[1]) return `$${dollarMatch[1]}`;

  return "";
}

function inferUsageScenario(query: string) {
  const normalized = query.toLowerCase();
  if (normalized.includes("travel")) return "travel";
  if (normalized.includes("desk")) return "desk setup";
  if (normalized.includes("daily") || normalized.includes("everyday")) return "daily charging";
  if (normalized.includes("bundle") || normalized.includes("setup")) return "daily charging";
  return "";
}

function buildRecommendationIntro(recommendation: ProductRecommendation) {
  const hasBundleItems =
    recommendation.bundleItems && recommendation.bundleItems.length > 1;

  if (hasBundleItems) {
    return "Sure. I put together a complete charging setup based on your request.";
  }

  return `Sure. My best match is ${recommendation.name}.`;
}

function AgentResultCard({ result }: { result: AgentResponse }) {
  const tools = (result.tool_result_summary || []).map((item) => item.tool).filter(Boolean);
  return (
    <section className="agent-result-card" aria-label="Commerce Agent result">
      <div className="agent-result-heading">
        <strong>Commerce Operations Agent</strong>
        <span className="agent-status">{result.status || "completed"}</span>
      </div>
      {tools.length ? <p>Verified tools: {tools.join(", ")}</p> : null}
      {result.handoff?.reason ? <p>Human handoff: {result.handoff.reason}</p> : null}
      {result.handoff?.summary ? <p>{result.handoff.summary}</p> : null}
      <p className="agent-safety-note">Synthetic-only result. No real merchant operation was performed.</p>
    </section>
  );
}

export default function ChatDemoPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const fromStore = searchParams.get("from") === "store";
  const assistantName = fromStore ? "ShopPilot AI Assistant" : "ShopPilot 3C";

  const initialQuery = searchParams.get("q")?.trim() || "";
  const initialConversationId = searchParams.get("conversation_id")?.trim() || "";
  const country = searchParams.get("country")?.trim() || "";
  const deviceModel = searchParams.get("device_model")?.trim() || "";
  const budget = searchParams.get("budget")?.trim() || "";
  const usageScenario = searchParams.get("usage_scenario")?.trim() || "";
  const storageKey = useMemo(
    () =>
      buildStorageKey({
        query: initialQuery,
        country,
        deviceModel,
        budget,
        usageScenario
      }),
    [budget, country, deviceModel, initialQuery, usageScenario]
  );

  const [messages, setMessages] = useState<ChatMessage[]>(
    initialQuery ? buildChatMessages(initialQuery) : []
  );
  const [inputText, setInputText] = useState("");
  const [conversationId, setConversationId] = useState(initialConversationId);
  const [isSubmitting, setIsSubmitting] = useState(Boolean(initialQuery));
  const [useMock, setUseMock] = useState(true);
  const [liveRecommendation, setLiveRecommendation] =
    useState<ProductRecommendation | null>(null);
  const [isReady, setIsReady] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const mockEnabled = process.env.NEXT_PUBLIC_USE_MOCK === "true";
    setUseMock(mockEnabled);
    setIsReady(false);
    setIsSubmitting(Boolean(initialQuery));

    if (!initialQuery) {
      setMessages([]);
      setInputText("");
      setConversationId("");
      setLiveRecommendation(null);
      setIsSubmitting(false);
      setIsReady(true);
      return;
    }

    const stored = readStoredChat(storageKey);
    if (stored) {
      const restoredMessages = stored.messages?.length
        ? stored.messages
        : buildChatMessages(initialQuery);
      const restoredConversationId = stored.conversationId || initialConversationId;
      const restoredRecommendation =
        inferRecommendation(restoredMessages, stored.liveRecommendation) || null;

      setMessages(attachRecommendationToLastAssistant(restoredMessages, restoredRecommendation));
      setInputText(stored.inputText || "");
      setConversationId(restoredConversationId);
      setLiveRecommendation(restoredRecommendation);
      setIsSubmitting(false);
      setIsReady(true);

      if (restoredConversationId && searchParams.get("conversation_id") !== restoredConversationId) {
        const params = new URLSearchParams(searchParams.toString());
        params.set("conversation_id", restoredConversationId);
        router.replace(
          params.toString() ? `${pathname}?${params.toString()}` : pathname,
          { scroll: false }
        );
      }

      return;
    }

    async function runInitialQuery() {
      if (mockEnabled && !shouldUseCommerceAgent(initialQuery, fromStore)) {
        setMessages([
          { role: "user", message: initialQuery, meta: "You | just now" },
          {
            role: "ai",
            message:
              "Great! I analyzed a few product options and can help you compare them by device, budget, and everyday use.",
            meta: "ShopPilot 3C | just now"
          }
        ]);
        setLiveRecommendation(null);
        setIsSubmitting(false);
        setIsReady(true);
        return;
      }

      try {
        if (shouldUseCommerceAgent(initialQuery, fromStore)) {
          const agentResult = await requestAgent(initialQuery, `web-agent-${crypto.randomUUID()}`);
          setLiveRecommendation(null);
          setMessages([
            { role: "user", message: initialQuery, meta: "You | just now" },
            {
              role: "ai",
              message: agentResult.answer || "Commerce Agent returned successfully, but no answer text was found.",
              meta: "Commerce Agent | just now",
              agentResult
            }
          ]);
          return;
        }
        const response = await fetch("/api/dify/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: initialQuery,
            user: "demo-user",
            response_mode: "blocking",
            conversation_id: initialConversationId || undefined,
            inputs: buildDifyInputs({
              query: initialQuery,
              country,
              deviceModel,
              budget,
              usageScenario
            })
          })
        });

        const data = (await response.json()) as DifyResponse;
        if (!response.ok) {
          throw new Error(data?.detail || data?.error || `Dify request failed: ${response.status}`);
        }

        const answer =
          typeof data?.answer === "string" && data.answer.trim()
            ? data.answer.trim()
            : typeof data?.message === "string" && data.message.trim()
              ? data.message.trim()
              : "Dify returned successfully, but no answer text was found.";
        const recommendation = parseRecommendationAnswer(answer);
        const nextConversationId =
          typeof data?.conversation_id === "string" && data.conversation_id.trim()
            ? data.conversation_id.trim()
            : initialConversationId;

        setConversationId(nextConversationId);
        setLiveRecommendation(recommendation);
        setMessages([
          { role: "user", message: initialQuery, meta: "You | just now" },
          {
            role: "ai",
            message: recommendation
              ? buildRecommendationIntro(recommendation)
              : answer,
            meta: "ShopPilot 3C | just now",
            recommendation
          }
        ]);
      } catch (error) {
        const errorCopy = shouldUseCommerceAgent(initialQuery, fromStore) ? buildAgentErrorCopy(error) : buildErrorCopy(error);
        setLiveRecommendation(null);
        setMessages([
          { role: "user", message: initialQuery, meta: "You | just now" },
          {
            role: "ai",
            message: errorCopy.message,
            description: errorCopy.description,
            meta: "ShopPilot 3C | just now"
          }
        ]);
      } finally {
        setIsSubmitting(false);
        setIsReady(true);
      }
    }

    void runInitialQuery();
  }, [
    budget,
    country,
    deviceModel,
    initialConversationId,
    initialQuery,
    pathname,
    router,
    searchParams,
    storageKey,
    usageScenario
    , fromStore
  ]);

  useEffect(() => {
    if (!isReady) return;
    writeStoredChat(storageKey, {
      messages,
      conversationId,
      inputText,
      liveRecommendation
    });
  }, [conversationId, inputText, isReady, liveRecommendation, messages, storageKey]);

  async function submitQuery(queryText: string) {
    const trimmed = queryText.trim();
    if (!trimmed || isSubmitting) return;

    setInputText("");
    setLiveRecommendation(null);
    setMessages((current) => [
      ...current,
      { role: "user", message: trimmed, meta: "You | just now" },
      {
        role: "ai",
        message: "Please wait, I am thinking",
        meta: "ShopPilot 3C | typing...",
        isThinking: true
      }
    ]);
    setIsSubmitting(true);

    if (shouldUseCommerceAgent(trimmed, fromStore)) {
      try {
        const agentResult = await requestAgent(trimmed, `web-agent-${crypto.randomUUID()}`);
        setMessages((current) => {
          const next = [...current];
          next.pop();
          next.push({
            role: "ai",
            message: agentResult.answer || "Commerce Agent returned successfully, but no answer text was found.",
            meta: "Commerce Agent | just now",
            agentResult
          });
          return next;
        });
      } catch (error) {
        const errorCopy = buildAgentErrorCopy(error);
        setMessages((current) => {
          const next = [...current];
          next.pop();
          next.push({ role: "ai", message: errorCopy.message, description: errorCopy.description, meta: "Commerce Agent | just now" });
          return next;
        });
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    if (useMock) {
      setTimeout(() => {
        setMessages((current) =>
          current.map((message, index) =>
            index === current.length - 1 && message.isThinking
              ? {
                  role: "ai",
                  message:
                    "Great follow-up. I can keep refining the recommendation based on your next question.",
                  meta: "ShopPilot 3C | just now"
                }
              : message
          )
        );
        setIsSubmitting(false);
      }, 800);
      return;
    }

    try {
      const response = await fetch("/api/dify/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: trimmed,
          user: "demo-user",
          response_mode: "blocking",
          conversation_id: conversationId || undefined,
          inputs: buildDifyInputs({
            query: trimmed,
            country,
            deviceModel,
            budget,
            usageScenario
          })
        })
      });

      const data = (await response.json()) as DifyResponse;
      if (!response.ok) {
        throw new Error(data?.detail || data?.error || `Dify request failed: ${response.status}`);
      }

      const answer =
        typeof data?.answer === "string" && data.answer.trim()
          ? data.answer.trim()
          : typeof data?.message === "string" && data.message.trim()
            ? data.message.trim()
            : "Dify returned successfully, but no answer text was found.";
      const recommendation = parseRecommendationAnswer(answer);
      const nextConversationId =
        typeof data?.conversation_id === "string" && data.conversation_id.trim()
          ? data.conversation_id.trim()
          : conversationId;

      setConversationId(nextConversationId);
      setLiveRecommendation(recommendation);

      if (
        initialQuery &&
        nextConversationId &&
        searchParams.get("conversation_id") !== nextConversationId
      ) {
        const params = new URLSearchParams(searchParams.toString());
        params.set("conversation_id", nextConversationId);
        router.replace(
          params.toString() ? `${pathname}?${params.toString()}` : pathname,
          { scroll: false }
        );
      }

      setMessages((current) => {
        const next = [...current];
        next.pop();
        next.push({
          role: "ai",
          message: recommendation
            ? buildRecommendationIntro(recommendation)
            : answer,
          meta: "ShopPilot 3C | just now",
          recommendation
        });
        return next;
      });
    } catch (error) {
      const errorCopy = buildErrorCopy(error);
      setLiveRecommendation(null);
      setMessages((current) => {
        const next = [...current];
        next.pop();
        next.push({
          role: "ai",
          message: errorCopy.message,
          description: errorCopy.description,
          meta: "ShopPilot 3C | just now"
        });
        return next;
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuery(inputText);
  }

  function handleClearChat() {
    try {
      window.sessionStorage.removeItem(storageKey);
    } catch {
      // Ignore storage failures.
    }

    setMessages([]);
    setInputText("");
    setConversationId("");
    setLiveRecommendation(null);
    setIsSubmitting(false);
    window.history.replaceState(null, "", pathname);
  }

  function handleAskFollowup() {
    inputRef.current?.focus();
  }

  return (
    <main className={fromStore ? "page-shell storefront-chat" : "page-shell"}>
      <SiteHeader
        backHref={fromStore ? "/store" : "/start"}
        backLabel={fromStore ? "Back to store" : "Back"}
        homeHref={fromStore ? "/store" : "/"}
        homeLabel={fromStore ? "ShopPilot 3C Store" : "Home"}
        rightAction={{ href: fromStore ? "/store" : "/start", label: fromStore ? "Continue shopping" : "New Search", variant: "secondary" }}
      />

      <div className="chat-shell">
        <div className="chat-header">
          <div className="chat-title-block">
            <div className="brand-mark">3C</div>
            <div>
              <div style={{ fontSize: 26, fontWeight: 700 }}>
                {assistantName}
              </div>
              <div className="chat-status">
                <span className="status-dot">o</span>{" "}
                {fromStore ? "ShopPilot 3C Store · online" : useMock ? "Mock mode" : "Live Dify mode"}
                {conversationId ? ` | Conversation ${conversationId}` : ""}
              </div>
            </div>
          </div>

          <div className="chat-header-actions">
            <button
              type="button"
              className="button button-secondary"
              onClick={handleClearChat}
              disabled={isSubmitting || messages.length === 0}
            >
              Clear Chat
            </button>
          </div>
        </div>

        <section className="chat-main">
          {messages.map((message, index) => (
            <Fragment key={`${message.role}-${index}-${message.meta}`}>
              <ChatBubble
                role={message.role}
                message={message.message}
                description={message.description}
                meta={message.meta}
                isThinking={message.isThinking}
              />
              {message.agentResult ? <AgentResultCard result={message.agentResult} /> : null}
              {message.recommendation && !useMock ? (
                <RecommendationCard
                  product={message.recommendation}
                  onViewProduct={handleAskFollowup}
                  onAskFollowup={handleAskFollowup}
                />
              ) : null}
            </Fragment>
          ))}

          {messages.length === 0 ? (
            <section className="empty-chat-card">
              <div className="brand-mark">3C</div>
              <div>
                <h2>Ask {assistantName}</h2>
                <p>
                  {fromStore
                    ? "Ask about products, compatibility, delivery policy, or a simulated order."
                    : "Start with a product need, budget, device model, or usage scenario, and I will recommend matching 3C accessories."}
                </p>
              </div>
              <div>
                <div className="followup-label">You can ask like this:</div>
                <QuickReplyChips
                  questions={starterQuestions}
                  onSelect={(question) => void submitQuery(question)}
                  disabled={isSubmitting}
                />
              </div>
            </section>
          ) : null}

          {useMock && messages.length > 0 && !isSubmitting ? (
            <section className="reco-section">
              <div className="reco-heading">
                <div className="brand-mark">AI</div>
                <div>
                  <h2>Top 3 Recommendations</h2>
                  <p>Recommendation preview</p>
                </div>
              </div>

              {recommendationProducts.map((product) => (
                <RecommendationCard key={product.name} product={product} />
              ))}
            </section>
          ) : null}
        </section>
      </div>

      <div className="followup-bar">
        <div className="chat-shell">
          {messages.length > 0 ? (
            <>
              <div className="followup-label">Continue the conversation:</div>
              <QuickReplyChips
                questions={followupQuestions}
                onSelect={(question) => void submitQuery(question)}
                disabled={isSubmitting}
              />
            </>
          ) : null}

          <form className="chat-input-form" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              id="chat-input"
              className="chat-input"
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              placeholder="Ask a follow-up question..."
              disabled={isSubmitting}
            />
            <button
              className="button button-primary"
              type="submit"
              disabled={isSubmitting || !inputText.trim()}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
