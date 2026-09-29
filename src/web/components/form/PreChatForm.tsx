"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "../ui/Card";

type PreChatFormProps = {
  deviceChips: string[];
  promptChips: string[];
};

export function PreChatForm({ deviceChips, promptChips }: PreChatFormProps) {
  const router = useRouter();
  const [queryText, setQueryText] = useState("");
  const [country, setCountry] = useState("");
  const [deviceModel, setDeviceModel] = useState("");
  const [budget, setBudget] = useState("");
  const [usageScenario, setUsageScenario] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!queryText.trim()) return;

    const query = new URLSearchParams();
    query.set("q", queryText.trim());
    if (country.trim()) query.set("country", country.trim());
    if (deviceModel.trim()) query.set("device_model", deviceModel.trim());
    if (budget.trim()) query.set("budget", budget.trim());
    if (usageScenario.trim()) query.set("usage_scenario", usageScenario.trim());

    const target = `/chat-demo?${query.toString()}`;
    router.push(target);
    window.location.href = target;
  }

  return (
    <Card className="form-card">
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="query">Ask AI directly</label>
          <textarea
            id="query"
            className="textarea"
            placeholder="e.g., Can you recommend a charging bundle for iPhone 15?"
            value={queryText}
            onChange={(event) => setQueryText(event.target.value)}
          />
          <div className="chips">
            {promptChips.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className={`chip chip-button${queryText === prompt ? " chip-active" : ""}`}
                onClick={() => setQueryText(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label htmlFor="device-model">Device model (Optional)</label>
          <input
            id="device-model"
            className="input"
            placeholder="e.g., iPhone 15 Pro, MacBook Air M2"
            value={deviceModel}
            onChange={(event) => setDeviceModel(event.target.value)}
          />
          <div className="chips">
            {deviceChips.map((chip) => (
              <button
                key={chip}
                type="button"
                className={`chip chip-button${deviceModel === chip ? " chip-active" : ""}`}
                onClick={() => setDeviceModel(chip)}
              >
                {chip}
              </button>
            ))}
          </div>
        </div>

        <div className="options-grid optional-grid">
          <div className="field optional-field">
            <label htmlFor="country">Country / Region (Optional)</label>
            <input
              id="country"
              className="input"
              placeholder="e.g., US, UK, China"
              value={country}
              onChange={(event) => setCountry(event.target.value)}
            />
          </div>

          <div className="field optional-field">
            <label htmlFor="budget">Budget (Optional)</label>
            <input
              id="budget"
              className="input"
              placeholder="e.g., 25, under $50"
              value={budget}
              onChange={(event) => setBudget(event.target.value)}
            />
          </div>

          <div className="field optional-field optional-field-wide">
            <label htmlFor="usage-scenario">Usage scenario (Optional)</label>
            <input
              id="usage-scenario"
              className="input"
              placeholder="e.g., travel, office, car, work from home"
              value={usageScenario}
              onChange={(event) => setUsageScenario(event.target.value)}
            />
          </div>
        </div>

        <button
          type="submit"
          className="button button-primary button-full"
          disabled={!queryText.trim()}
        >
          Ask AI
        </button>
      </form>
    </Card>
  );
}
