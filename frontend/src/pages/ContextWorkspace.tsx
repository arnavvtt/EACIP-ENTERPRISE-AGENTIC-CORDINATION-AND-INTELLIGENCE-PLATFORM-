import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type { ContextWorkspaceResponse } from "../types/task";

export default function ContextWorkspace() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ContextWorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    tasksApi.getContext(id)
      .then(setData)
      .catch((err) => setError(err.message || "Failed to load workspace"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: "3rem", textAlign: "center" }}>Loading workspace...</div>;
  if (error) return <div style={{ padding: "3rem", color: "red", textAlign: "center" }}>Error: {error}</div>;
  if (!data) return null;

  const groupedRecords: Record<string, any[]> = {};
  for (const r of data.retrieved_records) {
    const key = r.retrieval_metadata?.source_key || "unknown";
    (groupedRecords[key] ||= []).push(r);
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto", fontFamily: "sans-serif" }}>
      
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <Link to={`/tasks/${id}`} style={{ color: "#4f46e5", textDecoration: "none", fontWeight: 500 }}>
          ← Back to Task
        </Link>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: "2rem", color: "#111827" }}>Context Workspace</h1>
            <p style={{ margin: "0.5rem 0 0 0", color: "#6b7280" }}>
              Unified operational context assembled by AI.
            </p>
          </div>
          <Link
            to={`/tasks/${id}/package`}
            style={{ padding: "0.8rem 1.5rem", background: "#4f46e5", color: "white", textDecoration: "none", borderRadius: "8px", fontWeight: "bold", boxShadow: "0 4px 6px -1px rgba(79, 70, 229, 0.2)" }}
          >
            View Report Package →
          </Link>
        </div>
      </div>

      {/* Task Info Card */}
      <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1.5rem", marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: "0 0 0.5rem 0", fontSize: "1.2rem" }}>{data.task.title}</h2>
          <p style={{ margin: 0, color: "#4b5563" }}>{data.task.description}</p>
        </div>
        <span style={{ background: "#e0e7ff", color: "#3730a3", padding: "0.4rem 1rem", borderRadius: "20px", fontSize: "0.85rem", fontWeight: "bold" }}>
          {data.task.use_case?.replace(/_/g, " ").toUpperCase() || "GENERIC"}
        </span>
      </div>

      {/* Two Column Layout: Requirements & Records */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "2rem", marginBottom: "2rem" }}>
        
        {/* Left Column: Requirements */}
        <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1.5rem" }}>
          <h3 style={{ marginTop: 0, borderBottom: "2px solid #f3f4f6", paddingBottom: "0.5rem", color: "#374151" }}>
            Required Context ({data.requirements.length})
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1rem" }}>
            {data.requirements.map((req) => (
              <div key={req.id} style={{ background: "#f9fafb", padding: "1rem", borderRadius: "8px", border: "1px solid #e5e7eb" }}>
                <div style={{ fontWeight: "bold", color: "#111827", marginBottom: "0.25rem" }}>{req.requirement_type}</div>
                <div style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "0.5rem" }}>{req.description}</div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {req.is_mandatory ? <span style={{ fontSize: "0.75rem", fontWeight: "bold", color: "#991b1b", background: "#fee2e2", padding: "0.2rem 0.5rem", borderRadius: "4px" }}>Mandatory</span> : <span style={{ fontSize: "0.75rem", fontWeight: "bold", color: "#374151", background: "#e5e7eb", padding: "0.2rem 0.5rem", borderRadius: "4px" }}>Optional</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Retrieved Records */}
        <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1.5rem" }}>
          <h3 style={{ marginTop: 0, borderBottom: "2px solid #f3f4f6", paddingBottom: "0.5rem", color: "#374151" }}>
            Retrieved Evidence ({data.retrieved_records.length})
          </h3>
          <div style={{ marginTop: "1rem" }}>
            {Object.entries(groupedRecords).map(([sourceKey, records]) => (
              <div key={sourceKey} style={{ marginBottom: "1.5rem" }}>
                <h4 style={{ margin: "0 0 0.8rem 0", fontSize: "0.9rem", color: "#1e40af", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  {sourceKey} <span style={{ color: "#9ca3af", fontWeight: "normal" }}>({records.length})</span>
                </h4>
                <div style={{ display: "grid", gap: "0.5rem" }}>
                  {records.map((rec) => (
                    <div key={rec.id} style={{ padding: "0.8rem 1rem", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between" }}>
                      <div>
                        <strong style={{ color: "#111827" }}>{rec.retrieval_metadata?.external_id || "Unknown ID"}</strong>
                        <span style={{ marginLeft: "0.5rem", fontSize: "0.85rem", color: "#6b7280" }}>({rec.retrieval_metadata?.record_type})</span>
                      </div>
                      <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                        for {rec.retrieval_metadata?.requirement_type}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom: Correlations & Validations */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
        <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1.5rem" }}>
          <h3 style={{ marginTop: 0, borderBottom: "2px solid #f3f4f6", paddingBottom: "0.5rem", color: "#374151" }}>Correlations ({data.correlations.length})</h3>
          <ul style={{ paddingLeft: "1.2rem", margin: "1rem 0 0 0", color: "#4b5563" }}>
            {data.correlations.map((c) => (
              <li key={c.id} style={{ marginBottom: "0.5rem" }}>
                <strong>{c.relationship_type.replace(/_/g, " ")}</strong> (Basis: {c.basis})
              </li>
            ))}
          </ul>
        </div>

        <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1.5rem" }}>
          <h3 style={{ marginTop: 0, borderBottom: "2px solid #f3f4f6", paddingBottom: "0.5rem", color: "#374151" }}>Validations ({data.validations.length})</h3>
          <ul style={{ paddingLeft: "1.2rem", margin: "1rem 0 0 0", color: "#4b5563" }}>
            {data.validations.map((v) => (
              <li key={v.id} style={{ marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: "bold", color: v.severity === "high" ? "#991b1b" : "#b45309" }}>[{v.severity.toUpperCase()}]</span> {v.description}
              </li>
            ))}
          </ul>
        </div>
      </div>

    </div>
  );
}