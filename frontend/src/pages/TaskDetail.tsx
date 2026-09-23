import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type { TaskResponse } from "../types/task";

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [understanding, setUnderstanding] = useState(false);

  useEffect(() => {
    if (!id) return;
    tasksApi
      .get(id)
      .then(setTask)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleUnderstand = async () => {
    if (!id) return;
    setUnderstanding(true);
    setError(null);
    try {
      const updated = await tasksApi.understand(id);
      setTask(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Understanding failed";
      setError(message);
    } finally {
      setUnderstanding(false);
    }
  };

  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;
  if (error && !task)
    return <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>;
  if (!task) return null;

  const statusColor = (status: string) => {
    switch (status) {
      case "pending":
        return { bg: "#fef3c7", color: "#92400e" };
      case "processing":
        return { bg: "#dbeafe", color: "#1e40af" };
      case "ready":
      case "approved":
        return { bg: "#d1fae5", color: "#065f46" };
      case "rejected":
        return { bg: "#fee2e2", color: "#991b1b" };
      default:
        return { bg: "#e5e7eb", color: "#374151" };
    }
  };

  const colors = statusColor(task.status);
  const understandingData = (task.task_metadata?.understanding as any) || null;

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      <Link to="/" style={{ color: "#2563eb", textDecoration: "none" }}>
        ← Back to tasks
      </Link>

      <div
        style={{
          marginTop: "1.5rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "start",
          gap: "1rem",
        }}
      >
        <h1 style={{ margin: 0 }}>{task.title}</h1>
        <span
          style={{
            padding: "0.4rem 1rem",
            background: colors.bg,
            color: colors.color,
            borderRadius: "12px",
            fontSize: "0.85rem",
            fontWeight: 500,
            whiteSpace: "nowrap",
          }}
        >
          {task.status}
        </span>
      </div>

      <div
        style={{
          marginTop: "1.5rem",
          padding: "1.5rem",
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: "6px",
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Description</h2>
        <p style={{ lineHeight: 1.6, color: "#374151" }}>{task.description}</p>
      </div>

      <div
        style={{
          marginTop: "1rem",
          padding: "1.5rem",
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: "6px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Understanding</h2>
          <button
            onClick={handleUnderstand}
            disabled={understanding}
            style={{
              padding: "0.5rem 1rem",
              background: understanding ? "#999" : "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: understanding ? "not-allowed" : "pointer",
              fontSize: "0.85rem",
              fontWeight: 500,
            }}
          >
            {understanding
              ? "Analyzing..."
              : understandingData
              ? "Re-analyze"
              : "Run Task Understanding"}
          </button>
        </div>

        {error && (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.75rem",
              background: "#fee",
              color: "#900",
              borderRadius: "4px",
            }}
          >
            {error}
          </div>
        )}

        {understandingData ? (
          <div style={{ marginTop: "1rem" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                <tr>
                  <td style={cellLabel}>Intent</td>
                  <td style={cellValue}>{task.intent || "—"}</td>
                </tr>
                <tr>
                  <td style={cellLabel}>Use case</td>
                  <td style={cellValue}>{task.use_case || "—"}</td>
                </tr>
                <tr>
                  <td style={cellLabel}>Summary</td>
                  <td style={cellValue}>{understandingData.summary || "—"}</td>
                </tr>
                <tr>
                  <td style={cellLabel}>Confidence</td>
                  <td style={cellValue}>
                    {typeof understandingData.confidence === "number"
                      ? (understandingData.confidence * 100).toFixed(0) + "%"
                      : "—"}
                  </td>
                </tr>
                <tr>
                  <td style={cellLabel}>Entities</td>
                  <td style={cellValue}>
                    {understandingData.entities?.length ? (
                      <ul style={{ margin: 0, paddingLeft: "1rem" }}>
                        {understandingData.entities.map(
                          (e: any, i: number) => (
                            <li key={i}>
                              <strong>{e.type}</strong>: {e.value}
                            </li>
                          ),
                        )}
                      </ul>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
                <tr>
                  <td style={cellLabel}>Rationale</td>
                  <td style={{ ...cellValue, color: "#666" }}>
                    {understandingData.rationale || "—"}
                  </td>
                </tr>
                <tr>
                  <td style={cellLabel}>Provider</td>
                  <td
                    style={{
                      ...cellValue,
                      color: "#999",
                      fontSize: "0.85rem",
                    }}
                  >
                    {understandingData.provider} / {understandingData.model} /{" "}
                    {Math.round(understandingData.latency_ms)} ms
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ marginTop: "1rem", color: "#666" }}>
            Not yet analyzed. Click the button above to run task understanding.
          </p>
        )}
      </div>

      <div
        style={{
          marginTop: "1rem",
          padding: "1.5rem",
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: "6px",
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Details</h2>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <tbody>
            <tr>
              <td style={cellLabel}>Task ID</td>
              <td
                style={{
                  ...cellValue,
                  fontFamily: "monospace",
                  fontSize: "0.9rem",
                }}
              >
                {task.id}
              </td>
            </tr>
            <tr>
              <td style={cellLabel}>Use case (raw)</td>
              <td style={cellValue}>{task.use_case || "—"}</td>
            </tr>
            <tr>
              <td style={cellLabel}>Created</td>
              <td style={cellValue}>
                {new Date(task.created_at).toLocaleString()}
              </td>
            </tr>
            <tr>
              <td style={cellLabel}>Last updated</td>
              <td style={cellValue}>
                {new Date(task.updated_at).toLocaleString()}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

const cellLabel: React.CSSProperties = {
  padding: "0.5rem 0",
  color: "#666",
  width: "160px",
  verticalAlign: "top",
};

const cellValue: React.CSSProperties = {
  padding: "0.5rem 0",
  verticalAlign: "top",
};