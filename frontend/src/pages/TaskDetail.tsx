import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type { TaskResponse } from "../types/task";

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    tasksApi
      .get(id)
      .then(setTask)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;
  if (error)
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
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Details</h2>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <tbody>
            <tr>
              <td
                style={{
                  padding: "0.5rem 0",
                  color: "#666",
                  width: "180px",
                }}
              >
                Task ID
              </td>
              <td
                style={{
                  padding: "0.5rem 0",
                  fontFamily: "monospace",
                  fontSize: "0.9rem",
                }}
              >
                {task.id}
              </td>
            </tr>
            <tr>
              <td style={{ padding: "0.5rem 0", color: "#666" }}>Use case</td>
              <td style={{ padding: "0.5rem 0" }}>
                {task.use_case || "— (auto-detect)"}
              </td>
            </tr>
            <tr>
              <td style={{ padding: "0.5rem 0", color: "#666" }}>Intent</td>
              <td style={{ padding: "0.5rem 0" }}>
                {task.intent || "— (not yet determined)"}
              </td>
            </tr>
            <tr>
              <td style={{ padding: "0.5rem 0", color: "#666" }}>Created</td>
              <td style={{ padding: "0.5rem 0" }}>
                {new Date(task.created_at).toLocaleString()}
              </td>
            </tr>
            <tr>
              <td style={{ padding: "0.5rem 0", color: "#666" }}>
                Last updated
              </td>
              <td style={{ padding: "0.5rem 0" }}>
                {new Date(task.updated_at).toLocaleString()}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}