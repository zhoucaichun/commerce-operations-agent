"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

type WidgetResult = { answer?: string; status?: string; handoff?: { reason?: string }; merchant_id?: string };

export default function WidgetPage() {
  const params = useSearchParams();
  const merchantId = params.get("merchant") || "demo-3c-store";
  const [title, setTitle] = useState("Merchant Assistant");
  const [message, setMessage] = useState("Can I check my order status?");
  const [orderId, setOrderId] = useState(merchantId === "orbit-tech-store" ? "ORB-20001" : "ORD-10023");
  const [suffix, setSuffix] = useState(merchantId === "orbit-tech-store" ? "9052" : "4821");
  const [result, setResult] = useState<WidgetResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void fetch(`/api/widget/config/${encodeURIComponent(merchantId)}`)
      .then((response) => response.json())
      .then((data) => setTitle(data.title || "Merchant Assistant"))
      .catch(() => setError("Unable to load the synthetic widget configuration."));
  }, [merchantId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const response = await fetch("/api/widget/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ merchant_id: merchantId, thread_id: `visitor-${crypto.randomUUID()}`, message, slots: { order_id: orderId, identity_suffix: suffix } })
    });
    const data = await response.json();
    if (!response.ok) { setError(data.detail || "Widget request failed."); return; }
    setResult(data);
  }

  return <main className="page-shell"><div className="form-shell">
    <p className="badge badge-warning">Synthetic embedded Widget demo · no real order is queried</p>
    <h1>{title}</h1><p>Consumer-facing entry for a merchant website. The merchant is selected only by the demo URL.</p>
    <div className="chips"><Link className="chip chip-button" href="/widget?merchant=demo-3c-store">NovaGear demo</Link><Link className="chip chip-button" href="/widget?merchant=orbit-tech-store">Orbit demo</Link><Link className="chip chip-button" href="/console">Merchant Console</Link></div>
    <form className="form-card card" onSubmit={submit} style={{ marginTop: 20 }}>
      <div className="field"><label htmlFor="message">Question</label><textarea id="message" className="textarea" value={message} onChange={(e) => setMessage(e.target.value)} /></div>
      <div className="options-grid optional-grid"><div className="field optional-field"><label htmlFor="order">Demo order</label><input id="order" className="input" value={orderId} onChange={(e) => setOrderId(e.target.value)} /></div><div className="field optional-field"><label htmlFor="suffix">Identity last 4</label><input id="suffix" className="input" value={suffix} onChange={(e) => setSuffix(e.target.value)} /></div></div>
      <button className="button button-primary" type="submit">Ask safely</button>
    </form>
    {error ? <p role="alert">{error}</p> : null}
    {result ? <section className="card form-card" style={{ marginTop: 20 }}><strong>{result.status}</strong><p>{result.answer}</p>{result.handoff?.reason ? <p>Human handoff: {result.handoff.reason}</p> : null}</section> : null}
  </div></main>;
}
