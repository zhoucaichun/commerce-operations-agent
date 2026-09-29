import { ReactNode } from "react";

type ChatBubbleProps = {
  role: "user" | "ai";
  message: string | ReactNode;
  meta: string;
  description?: string;
  isThinking?: boolean;
};

export function ChatBubble({
  role,
  message,
  meta,
  description,
  isThinking = false
}: ChatBubbleProps) {
  const content =
    typeof message === "string" && role === "ai"
      ? renderAssistantMessage(message)
      : message;

  return (
    <div className={`bubble-row ${role}`}>
      <div>
        <div className={`bubble ${role}`}>
          <div className={isThinking ? "thinking-message" : undefined}>{content}</div>
          {description ? (
            <div className="bubble-description">{description}</div>
          ) : null}
        </div>
        <div className="bubble-meta">{meta}</div>
      </div>
    </div>
  );
}

type AssistantSection =
  | {
      kind: "text";
      text: string;
    }
  | {
      kind: "section";
      title: string;
      items: string[];
    }
  | {
      kind: "card";
      tone: "conclusion" | "product" | "reason" | "note" | "policy" | "default";
      label: string;
      text: string;
    };

function renderAssistantMessage(message: string) {
  const sections = parseAssistantMessage(message);

  if (!sections.length) {
    return <div style={{ whiteSpace: "pre-wrap" }}>{message}</div>;
  }

  return (
    <div className="assistant-message">
      {sections.map((section, index) => {
        if (section.kind === "text") {
          const isConclusion = isConclusionText(section.text);

          return (
            <div
              key={`${section.kind}-${index}`}
              className={
                isConclusion
                  ? "assistant-conclusion"
                  : "assistant-paragraph"
              }
            >
              {isConclusion ? <span>Conclusion</span> : null}
              <p>{renderInlineText(section.text)}</p>
            </div>
          );
        }

        if (section.kind === "card") {
          return (
            <div
              key={`${section.kind}-${index}`}
              className={`assistant-answer-card assistant-answer-card-${section.tone}`}
            >
              <div className="assistant-answer-label">{section.label}</div>
              <p>{renderInlineText(section.text)}</p>
            </div>
          );
        }

        return (
          <div
            key={`${section.kind}-${index}`}
            className={`assistant-section assistant-section-${getSectionTone(section.title)}`}
          >
            <div className="assistant-section-title">{section.title}</div>
            <div className="assistant-section-body">
              {section.items.map((item) => (
                <p key={item}>{renderInlineText(item)}</p>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function parseAssistantMessage(message: string): AssistantSection[] {
  const normalized = message.replace(/\r\n/g, "\n").trim();
  const headings = [
    "Best pick",
    "Best picks",
    "Matching product",
    "Why it fits",
    "Why they fit",
    "Why",
    "Note",
    "Notes",
    "Also consider",
    "For charging multiple devices"
  ];
  const headingPattern = headings.map(escapeRegExp).join("|");
  const parts = normalized.split(new RegExp(`(${headingPattern}):`, "gi"));
  const sections: AssistantSection[] = [];
  let currentTitle = "";

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    if (headings.some((heading) => heading.toLowerCase() === trimmed.toLowerCase())) {
      currentTitle = normalizeHeading(trimmed);
      continue;
    }

    if (!currentTitle) {
      sections.push({ kind: "text", text: trimmed });
      continue;
    }

    const body = trimmed.replace(/\s+-\s+/g, "\n- ");
    const hasBulletLines = body.split("\n").some((line) => /^\s*[-*]/.test(line));
    const items = (hasBulletLines ? body.split("\n") : [body])
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => line.replace(/^[-*]\s*/, "").trim())
      .filter(Boolean);

    if (items.length > 0) {
      sections.push({
        kind: "section",
        title: currentTitle,
        items
      });
    } else {
      sections.push({
        kind: "text",
        text: `${currentTitle} ${trimmed}`.trim()
      });
    }

    currentTitle = "";
  }

  if (sections.some((section) => section.kind === "section")) {
    return sections;
  }

  return buildStructuredCards(normalized);
}

function buildStructuredCards(message: string): AssistantSection[] {
  const blocks = message
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  const sourceBlocks = blocks.length ? blocks : [message.trim()].filter(Boolean);
  const cards: AssistantSection[] = [];

  sourceBlocks.forEach((block, blockIndex) => {
    const splitBlocks = shouldSplitIntoSentenceCards(block)
      ? splitSentences(block)
      : [block];

    splitBlocks.forEach((text, splitIndex) => {
      cards.push(createCardSection(text, blockIndex, splitIndex));
    });
  });

  return cards.length ? cards : [{ kind: "text", text: message }];
}

function shouldSplitIntoSentenceCards(text: string) {
  return (
    isPolicyText(text) &&
    splitSentences(text).length > 1 &&
    text.length <= 420
  );
}

function splitSentences(text: string) {
  const matches = text.match(/[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$/g);
  return (matches || [text]).map((part) => part.trim()).filter(Boolean);
}

function createCardSection(
  text: string,
  blockIndex: number,
  splitIndex: number
): AssistantSection {
  const lower = text.toLowerCase();
  const isFirst = blockIndex === 0 && splitIndex === 0;

  if (isConclusionText(text) || (isFirst && /^(yes|no)\b/i.test(text))) {
    return {
      kind: "card",
      tone: /^(no)\b/i.test(text) ? "note" : "conclusion",
      label: /^(no)\b/i.test(text) ? "Answer" : "Answer",
      text
    };
  }

  if (/\bsku\d{3}\b/i.test(text) || lower.includes("matching product")) {
    return {
      kind: "card",
      tone: "product",
      label: "Product",
      text
    };
  }

  if (isPolicyText(text)) {
    return {
      kind: "card",
      tone: "policy",
      label: getPolicyLabel(text),
      text
    };
  }

  if (
    lower.includes("please note") ||
    lower.startsWith("note") ||
    lower.includes("may affect") ||
    lower.includes("may be") ||
    lower.includes("sold separately") ||
    lower.includes("when both ports")
  ) {
    return {
      kind: "card",
      tone: "note",
      label: "Note",
      text
    };
  }

  if (
    lower.includes("compatible") ||
    lower.includes("key features") ||
    lower.includes("listed as") ||
    lower.includes("supports") ||
    lower.includes("based on") ||
    lower.includes("works with") ||
    lower.includes("because")
  ) {
    return {
      kind: "card",
      tone: "reason",
      label: "Why",
      text
    };
  }

  return {
    kind: "card",
    tone: "default",
    label: isFirst ? "Response" : "Detail",
    text
  };
}

function isPolicyText(text: string) {
  return /\b(shipping|business days|order|processed|return|refund|warranty|discount|student|delivery|express|standard|policy|support)\b/i.test(
    text
  );
}

function getPolicyLabel(text: string) {
  const lower = text.toLowerCase();
  if (lower.includes("express")) return "Express Shipping";
  if (lower.includes("standard")) return "Standard Shipping";
  if (lower.includes("return") || lower.includes("refund")) return "Returns";
  if (lower.includes("warranty")) return "Warranty";
  if (lower.includes("discount") || lower.includes("student")) return "Discount";
  return "Policy";
}

function isConclusionText(text: string) {
  return /^(yes|no|not sure|unclear)\.?$/i.test(text.trim());
}

function renderInlineText(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }

    return part;
  });
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeHeading(value: string) {
  const lower = value.toLowerCase();
  if (lower === "why") return "Why this works";
  if (lower === "note" || lower === "notes") return "Before you buy";
  return value.replace(/\b\w/g, (char) => char.toUpperCase());
}

function getSectionTone(title: string) {
  const lower = title.toLowerCase();
  if (lower.includes("matching") || lower.includes("best")) return "product";
  if (lower.includes("why")) return "why";
  if (lower.includes("note") || lower.includes("before")) return "note";
  return "default";
}
