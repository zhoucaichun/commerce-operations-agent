import { SiteHeader } from "../../components/layout/SiteHeader";
import { Card } from "../../components/ui/Card";

export default function BadcaseDetailPage() {
  return (
    <main className="page-shell">
      <SiteHeader
        backHref="/dashboard"
        backLabel="Back"
        rightAction={{ href: "/dashboard", label: "Back to Dashboard", variant: "secondary" }}
      />

      <div className="state-page">
        <div className="state-header">
          <div className="state-title-wrap">
            <h1>Badcase Detail</h1>
            <p>Root cause review and fix recommendation for one evaluation case</p>
          </div>
        </div>

        <div className="badcase-layout">
          <Card className="case-card">
            <h2 className="panel-title">Conversation Snapshot</h2>

            <div className="transcript-box">
              <div className="transcript-label">Original Question</div>
              <div className="transcript-text">
                Can I charge MacBook Pro 14 and iPhone at the same time with a 65W charger?
              </div>
            </div>

            <div className="transcript-box" style={{ marginTop: 14 }}>
              <div className="transcript-label">Original Answer</div>
              <div className="transcript-text">
                We cannot determine if the 65W charger can charge both your MacBook Pro 14 and iPhone at the same time based on the provided information.
              </div>
            </div>

            <div className="transcript-box" style={{ marginTop: 14 }}>
              <div className="transcript-label">Expected Better Answer</div>
              <div className="transcript-text">
                Explain that the answer depends on the charger’s number of ports and how power is shared between them, instead of stopping at a generic refusal.
              </div>
            </div>
          </Card>

          <Card className="case-card">
            <h2 className="panel-title">Analysis & Fix</h2>

            <div className="detail-stack">
              <div className="detail-box">
                <h3>Root Cause</h3>
                <p>
                  The compatibility branch chose a conservative fallback instead of
                  producing a conditional explanation when retrieval did not fully
                  confirm simultaneous charging behavior.
                </p>
              </div>

              <div className="detail-box">
                <h3>Optimization Suggestion</h3>
                <ul className="detail-list">
                  <li>Prefer conditional answers over flat refusal when possible.</li>
                  <li>Explicitly mention port count dependency.</li>
                  <li>Explain shared power behavior in concise user language.</li>
                </ul>
              </div>

              <div className="detail-box">
                <h3>Status After Fix</h3>
                <p>
                  The workflow now keeps the conservative boundary, but it can
                  explain the key condition instead of only saying the answer is unknown.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </main>
  );
}
