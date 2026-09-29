import { SiteHeader } from "../../components/layout/SiteHeader";
import { Card } from "../../components/ui/Card";

const metrics = [
  { label: "Recommendation Accuracy", value: "87%", trend: "+6.2% vs last round", tone: "positive" },
  { label: "Correct Handoff Rate", value: "92%", trend: "+4.1% vs last round", tone: "positive" },
  { label: "Hallucination Rate", value: "5.8%", trend: "-2.3% vs last round", tone: "positive" },
  { label: "Badcase Open Count", value: "11", trend: "Needs review this week", tone: "warning" }
];

const recentBadcases = [
  ["E011", "Recommendation", "Repeated follow-up after user already gave enough info", "Fixed"],
  ["E027", "Compatibility", "Safety warning too weak before handoff", "Fixed"],
  ["E091", "Compatibility", "Conditional answer missing for simultaneous charging", "Needs follow-up"],
  ["E099", "Recommendation", "Example-led follow-up still too generic", "Observed"]
];

const distribution = [
  ["Recommendation Memory Loss", 42],
  ["Unnecessary Follow-up", 28],
  ["Safety / Handoff Wording", 18],
  ["Policy Grounding", 12]
];

export default function DashboardPage() {
  return (
    <main className="page-shell">
      <SiteHeader
        backHref="/"
        backLabel="Back"
        rightAction={{ href: "/chat-demo", label: "Open Chat", variant: "secondary" }}
      />

      <div className="state-page">
        <div className="state-header">
          <div className="state-title-wrap">
            <h1>Evaluation & Badcase Dashboard</h1>
            <p>Measure recommendation quality, handoff quality, and badcase iteration status</p>
          </div>
        </div>

        <div className="dashboard-grid">
          {metrics.map((metric) => (
            <Card key={metric.label} className="metric-card">
              <div className="metric-label">{metric.label}</div>
              <div className="metric-value">{metric.value}</div>
              <div className={`metric-trend ${metric.tone}`}>{metric.trend}</div>
            </Card>
          ))}
        </div>

        <div className="dashboard-panels">
          <Card className="table-card">
            <h2 className="panel-title">Recent Badcases</h2>
            <table className="simple-table">
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Type</th>
                  <th>Issue</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentBadcases.map((row) => (
                  <tr key={row[0]}>
                    <td>{row[0]}</td>
                    <td>{row[1]}</td>
                    <td>{row[2]}</td>
                    <td>{row[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card className="chart-card">
            <h2 className="panel-title">Issue Distribution</h2>
            <div className="chart-bars">
              {distribution.map(([label, value]) => (
                <div key={label} className="chart-row">
                  <div>{label}</div>
                  <div className="chart-track">
                    <div className="chart-fill" style={{ width: `${value}%` }} />
                  </div>
                  <div>{value}%</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </main>
  );
}
