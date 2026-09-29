"use client";

type QuickReplyChipsProps = {
  questions: string[];
  onSelect?: (question: string) => void;
  disabled?: boolean;
};

export function QuickReplyChips({
  questions,
  onSelect,
  disabled = false
}: QuickReplyChipsProps) {
  return (
    <div className="followup-chips">
      {questions.map((question) => (
        <button
          key={question}
          type="button"
          className="chip chip-soft chip-button quick-reply-button"
          onClick={() => onSelect?.(question)}
          disabled={disabled}
        >
          {question}
        </button>
      ))}
    </div>
  );
}
