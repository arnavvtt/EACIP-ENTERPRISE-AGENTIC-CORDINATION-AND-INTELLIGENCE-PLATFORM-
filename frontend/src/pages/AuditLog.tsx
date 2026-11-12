import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";

export default function AuditLog() {
  const { id } = useParams<{ id: string }>();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    tasksApi.getAuditLogs(id)
      .then((res) => setLogs(res.logs))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: "2rem" }}>Loading logs...</div>;

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      <Link to={`/tasks/${id}`} style={{ color: "#4f46e5", textDecoration: "none" }}>← Back to Task</Link>
      <h1 style={{ marginTop: "1rem" }}>Audit Trail</h1>
      
      <div style={{ marginTop: "2rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
        {logs.length === 0 ? (
          <p>No logs found.</p>
        ) : (
          logs.map((log) => (
            <div key={log.id} style={{ borderLeft: "4px solid #4f46e5", background: "#f9fafb", padding: "1rem", borderRadius: "0 8px 8px 0" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <strong style={{ color: "#111827" }}>{log.event_type.replace(/_/g, " ").toUpperCase()}</strong>
                <span style={{ fontSize: "0.85rem", color: "#6b7280" }}>{new Date(log.timestamp).toLocaleString()}</span>
              </div>
              <div style={{ fontSize: "0.9rem", color: "#4b5563" }}><strong>Actor:</strong> {log.actor}</div>
              {log.details && (
                <pre style={{ marginTop: "0.5rem", background: "#e5e7eb", padding: "0.5rem", borderRadius: "4px", fontSize: "0.8rem" }}>
                  {JSON.stringify(log.details, null, 2)}
                </pre>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}