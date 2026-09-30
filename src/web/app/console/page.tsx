"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Ticket = { ticket_id: string; status: string; summary?: string };
type Overview = { merchant: { name: string; merchant_id: string }; tickets: Ticket[]; metrics: Record<string, number>; recent_handoffs: string[]; widget_snippet: string; connector_status: string; role: string };

export default function ConsolePage() {
  const [merchantId, setMerchantId] = useState("demo-3c-store");
  const [role, setRole] = useState("support");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  async function load() {
    setError("");
    const response = await fetch("/api/merchant/overview", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ merchant_id: merchantId, role }) });
    const data = await response.json();
    if (!response.ok) { setError(data.detail || "Could not load merchant view."); return; }
    setOverview(data);
  }
  useEffect(() => { void load(); }, [merchantId, role]);
  async function resolve(ticketId: string) {
    const response = await fetch(`/api/merchant/tickets/${encodeURIComponent(ticketId)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ merchant_id: merchantId, role, status: "simulated_resolved" }) });
    if (!response.ok) { const data = await response.json(); setError(data.detail || "Unable to update simulated ticket."); return; }
    void load();
  }
  return <main className="page-shell"><div className="state-page">
    <p className="badge badge-warning">Synthetic Merchant Console demo · role selector is not real authentication</p>
    <div className="state-header"><div className="state-title-wrap"><h1>{overview?.merchant.name || "Merchant Console"}</h1><p>Merchant staff entry. All records are isolated synthetic demo data.</p></div><Link className="button button-secondary" href={`/widget?merchant=${merchantId}`}>Open consumer Widget</Link></div>
    <section className="card form-card"><div className="options-grid optional-grid"><div className="field optional-field"><label>Demo merchant</label><select className="input" value={merchantId} onChange={(e) => setMerchantId(e.target.value)}><option value="demo-3c-store">NovaGear 3C</option><option value="orbit-tech-store">Orbit Tech Store</option></select></div><div className="field optional-field"><label>Demo role</label><select className="input" value={role} onChange={(e) => setRole(e.target.value)}><option value="support">Support</option><option value="operator">Operations</option><option value="merchant_admin">Merchant admin</option></select></div></div></section>
    {error ? <p role="alert">{error}</p> : null}
    {overview ? <><section className="dashboard-grid" style={{ marginTop: 18 }}>{Object.entries(overview.metrics).filter(([key]) => ["chat_requests", "handoffs", "completed", "tool_calls"].includes(key)).map(([key, value]) => <div className="card metric-card" key={key}><div className="metric-label">{key}</div><div className="metric-value">{value}</div></div>)}</section>
      <section className="dashboard-panels"><div className="card table-card"><h2 className="panel-title">Simulated support tickets</h2>{overview.tickets.length ? <table className="simple-table"><thead><tr><th>ID</th><th>Status</th><th>Action</th></tr></thead><tbody>{overview.tickets.map((ticket) => <tr key={ticket.ticket_id}><td>{ticket.ticket_id}</td><td>{ticket.status}</td><td>{role !== "operator" && ticket.status !== "simulated_resolved" ? <button className="button button-secondary" onClick={() => void resolve(ticket.ticket_id)}>Resolve demo ticket</button> : "Read only"}</td></tr>)}</tbody></table> : <p>No synthetic tickets yet. Use the Widget and request human support with an idempotency key in a later test.</p>}</div><div className="card chart-card"><h2 className="panel-title">Operations & installation</h2><p>Recent handoff reasons: {overview.recent_handoffs.join(", ") || "none"}</p><p>Connector: {overview.connector_status}</p><code>{overview.widget_snippet}</code></div></section></> : null}
  </div></main>;
}
