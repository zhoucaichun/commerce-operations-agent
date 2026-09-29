"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "../ui/Card";
import { QuickReplyChips } from "../recommendation/QuickReplyChips";

type PromptLauncherProps = {
  title: string;
  description: string;
  suggestions: string[];
};

export function PromptLauncher({
  title,
  description,
  suggestions
}: PromptLauncherProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function openChat(nextQuery: string) {
    const trimmed = nextQuery.trim();
    if (!trimmed) return;
    router.push(`/chat-demo?q=${encodeURIComponent(trimmed)}`);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    openChat(query);
  }

  return (
    <Card className="prompt-launcher">
      <div className="prompt-launcher-copy">
        <h2>{title}</h2>
        <p>{description}</p>
      </div>

      <div>
        <div className="followup-label">You can ask like this:</div>
        <QuickReplyChips questions={suggestions} onSelect={openChat} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Type your own question..."
        />
        <button className="button button-primary" type="submit" disabled={!query.trim()}>
          Ask AI
        </button>
      </form>
    </Card>
  );
}
