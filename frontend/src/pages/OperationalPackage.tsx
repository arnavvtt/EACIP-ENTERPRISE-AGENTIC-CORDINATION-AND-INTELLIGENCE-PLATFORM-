import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";

// ------------------------------------------------------------------
// Helper Components
// ------------------------------------------------------------------
const SeverityBadge = ({ severity }: { severity: string }) => {
  const colors: Record<string, { bg: string; text: string }> = {
    high: { bg: "#fee2e2", text: "#991b1b" },
    medium: { bg: "#fef3c7", text: "#92400e" },
    low: { bg: "#d1fae5", text: "#065f46" },
  };
  const color = colors[severity?.toLowerCase()] || { bg: "#f3f4f6", text: "#374151" };
  return (
    <span style={{ padding: "0.2rem 0.6rem", borderRadius: "10px", fontSize: "0.75rem", fontWeight: "bold", textTransform: "uppercase", background: color.bg, color: color.text }}>
      {severity || "unknown"}
    </span>
  );
};

const Accordion = ({ title, children, defaultOpen = false }: { title: string, children: React.ReactNode, defaultOpen?: boolean }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: "8px", marginBottom: "1rem", background: "white", overflow: "hidden" }}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        style={{ width: "100%", padding: "1rem 1.5rem", background: "#f9fafb", border: "none", textAlign: "left", display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer", fontWeight: "bold", color: "#374151", fontSize: "1rem" }}
      >
        {title}
        <span>{isOpen ? "▲" : "▼"}</span>
      </button>
      {isOpen && <div style={{ padding: "1.5rem", borderTop: "1px solid #e5e7eb" }}>{children}</div>}
    </div>
  );
};

// ------------------------------------------------------------------
// Main Component
// ------------------------------------------------------------------
export default function OperationalPackage() {
  const { id } = useParams<{ id: string }>();
  const [pkg, setPkg] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reviewing, setReviewing] = useState(false);

  const fetchPackage = async () => {
    if (!id) return;
    try {
      const data = await tasksApi.getPackage(id);
      setPkg(data);
    } catch (err) {
      console.log("No package found");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPackage(); }, [id]);

  const handleGenerate = async () => {
    if (!id) return;
    setGenerating(true);
    try {
      await tasksApi.generatePackage(id);
      await fetchPackage();
    } catch (err) {
      alert("Failed to generate package");
    } finally {
      setGenerating(false);
    }
  };

  const handleReview = async (decision: "approved" | "rejected") => {
    if (!id) return;
    const comments = decision === "approved" ? "Approved by human reviewer." : "Rejected by human reviewer.";
    setReviewing(true);
    try {
      await tasksApi.submitReview(id, decision, comments);
      await fetchPackage();
    } catch (err) {
      alert("Failed to submit review");
    } finally {
      setReviewing(false);
    }
  };

  if (loading) return <div style={{ padding: "3rem", textAlign: "center", color: "#6b7280" }}>Loading package...</div>;

  // Extract specific sections for better UX
  const sections = pkg?.sections || {};
  const insights = sections["section_11_ai_insights_and_next_steps"] || {};
  const gaps = sections["section_7_information_gaps"] || [];
  const inconsistencies = sections["section_8_potential_inconsistencies"] || [];
  const requirements = sections["section_3_required_context"] || [];
  const entities = sections["section_2_relevant_entities"] || [];

  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto", fontFamily: "sans-serif" }}>
      <Link to={`/tasks/${id}`} style={{ color: "#4f46e5", textDecoration: "none", fontWeight: 500 }}>
        ← Back to Task
      </Link>
      
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginTop: "1rem", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "2rem", color: "#111827" }}>Operational Report</h1>
          <p style={{ margin: "0.5rem 0 0 0", color: "#6b7280" }}>AI-generated context and recommendations.</p>
        </div>
      </div>

      {!pkg ? (
        <div style={{ background: "#f9fafb", padding: "3rem", textAlign: "center", borderRadius: "12px", border: "1px dashed #ccc" }}>
          <h3 style={{ marginTop: 0 }}>No Report Generated</h3>
          <button onClick={handleGenerate} disabled={generating} style={{ padding: "0.8rem 1.5rem", background: "#4f46e5", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold", marginTop: "1rem" }}>
            {generating ? "Generating..." : "Generate Report"}
          </button>
        </div>
      ) : (
        <div>
          {/* HEADER CONTROLS */}
          <div style={{ background: pkg.status === 'approved' ? "#d1fae5" : (pkg.status === 'rejected' ? "#fee2e2" : "#e0e7ff"), padding: "1.5rem", borderRadius: "12px", marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", borderLeft: `6px solid ${pkg.status === 'approved' ? "#059669" : (pkg.status === 'rejected' ? "#dc2626" : "#4f46e5")}` }}>
            <div>
              <h2 style={{ margin: "0 0 0.5rem 0", fontSize: "1.2rem", textTransform: "capitalize" }}>Status: {pkg.status.replace(/_/g, " ")}</h2>
              <p style={{ margin: 0, fontSize: "0.9rem", color: "#4b5563" }}>Version {pkg.version} | {pkg.summary}</p>
            </div>
            
            <div style={{ display: "flex", gap: "1rem" }}>
              <button onClick={handleGenerate} disabled={generating || reviewing} style={{ padding: "0.6rem 1.2rem", background: "#4f46e5", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}>
                {generating ? "Regenerating..." : "Regenerate"}
              </button>
              {pkg.status === "ready_for_review" && (
                <>
                  <button onClick={() => handleReview("approved")} disabled={reviewing} style={{ padding: "0.6rem 1.2rem", background: "#059669", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}>
                    {reviewing ? "Saving..." : "✅ Approve"}
                  </button>
                  <button onClick={() => handleReview("rejected")} disabled={reviewing} style={{ padding: "0.6rem 1.2rem", background: "#dc2626", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}>
                    {reviewing ? "Saving..." : "❌ Reject"}
                  </button>
                </>
              )}
            </div>
          </div>

          {/* SECTION 1: AI SUMMARY & NEXT STEPS (Prioritized) */}
          <div style={{ marginBottom: "2rem" }}>
            <h2 style={{ fontSize: "1.4rem", color: "#111827", marginBottom: "1rem" }}>🤖 AI Executive Summary</h2>
            {insights.insights && insights.insights.length > 0 && (
              <div style={{ display: "grid", gap: "1rem", marginBottom: "1.5rem" }}>
                {insights.insights.map((insight: any, i: number) => (
                  <div key={i} style={{ background: "white", border: "1px solid #e5e7eb", padding: "1.5rem", borderRadius: "8px", borderLeft: "4px solid #8b5cf6" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                      <strong style={{ fontSize: "1.1rem" }}>{insight.title}</strong>
                      <SeverityBadge severity={insight.severity} />
                    </div>
                    <p style={{ margin: 0, color: "#4b5563" }}>{insight.detail}</p>
                  </div>
                ))}
              </div>
            )}
            
            {insights.next_steps && insights.next_steps.length > 0 && (
              <div style={{ background: "#f8fafc", padding: "1.5rem", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ marginTop: 0, fontSize: "1.1rem", color: "#1e293b" }}>🎯 Recommended Actions</h3>
                <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "#334155", lineHeight: 1.6 }}>
                  {insights.next_steps.map((step: any, i: number) => (
                    <li key={i} style={{ marginBottom: "0.5rem" }}>
                      <strong>{step.step}</strong> — {step.rationale}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* SECTION 2: ISSUES (Gaps & Inconsistencies) */}
          <div style={{ marginBottom: "2rem" }}>
            <h2 style={{ fontSize: "1.4rem", color: "#111827", marginBottom: "1rem" }}>⚠️ Detected Issues</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
              
              {/* Gaps */}
              <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "1.5rem" }}>
                <h3 style={{ marginTop: 0, fontSize: "1.1rem", color: "#374151", borderBottom: "1px solid #e5e7eb", paddingBottom: "0.5rem" }}>Information Gaps</h3>
                {gaps.length === 0 ? <p style={{ color: "#6b7280" }}>No gaps found.</p> : (
                  <ul style={{ paddingLeft: "1.2rem", margin: 0 }}>
                    {gaps.map((gap: any, i: number) => (
                      <li key={i} style={{ marginBottom: "0.8rem" }}>
                        <div style={{ fontWeight: "bold", color: "#111827" }}>{gap.details?.requirement_type || gap.description}</div>
                        <div style={{ marginTop: "0.2rem", display: "flex", gap: "0.5rem", alignItems: "center" }}>
                          <SeverityBadge severity={gap.severity} />
                          <span style={{ fontSize: "0.85rem", color: "#6b7280" }}>{gap.description}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Inconsistencies */}
              <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "1.5rem" }}>
                <h3 style={{ marginTop: 0, fontSize: "1.1rem", color: "#374151", borderBottom: "1px solid #e5e7eb", paddingBottom: "0.5rem" }}>Conflicts Detected</h3>
                {inconsistencies.length === 0 ? <p style={{ color: "#6b7280" }}>No conflicts found.</p> : (
                  <ul style={{ paddingLeft: "1.2rem", margin: 0 }}>
                    {inconsistencies.map((inc: any, i: number) => (
                      <li key={i} style={{ marginBottom: "0.8rem" }}>
                        <div style={{ fontWeight: "bold", color: "#111827" }}>{inc.details?.conflicts?.[0]?.field || "Data Conflict"}</div>
                        <div style={{ marginTop: "0.2rem", display: "flex", gap: "0.5rem", alignItems: "center" }}>
                          <SeverityBadge severity={inc.severity} />
                          <span style={{ fontSize: "0.85rem", color: "#6b7280" }}>{inc.description}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

            </div>
          </div>

          {/* SECTION 3: TECHNICAL DETAILS (Hidden in Accordion) */}
          <div style={{ marginBottom: "2rem" }}>
            <h2 style={{ fontSize: "1.4rem", color: "#111827", marginBottom: "1rem" }}>📁 Supporting Data</h2>
            
            <Accordion title={`Identified Requirements (${requirements.length})`}>
              <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
                {requirements.map((req: any) => (
                  <li key={req.id} style={{ marginBottom: "0.5rem" }}>
                    <strong>{req.type}</strong> {req.mandatory ? "(Mandatory)" : "(Optional)"}
                  </li>
                ))}
              </ul>
            </Accordion>

            <Accordion title={`Extracted Entities (${entities.length})`}>
              <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
                {entities.map((ent: any, i: number) => (
                  <li key={i}><strong>{ent.type}:</strong> {ent.value}</li>
                ))}
              </ul>
            </Accordion>

            <Accordion title="System Traceability & Metadata">
              <pre style={{ background: "#1f2937", color: "#f3f4f6", padding: "1rem", borderRadius: "6px", overflowX: "auto", fontSize: "0.8rem" }}>
                {JSON.stringify({ 
                  task_id: pkg.task_id, 
                  generated_at: pkg.created_at, 
                  version: pkg.version,
                  source_traceability: sections["section_10_source_traceability"]
                }, null, 2)}
              </pre>
            </Accordion>
          </div>

        </div>
      )}
    </div>
  );
}