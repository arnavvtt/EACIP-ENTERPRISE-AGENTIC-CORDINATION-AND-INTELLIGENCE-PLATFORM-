import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type { TaskResponse } from "../types/task";

export default function TaskList() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    tasksApi.list()
      .then((res) => setTasks(res.tasks))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getStatusBadge = (status: string) => {
    const colors: Record<string, any> = {
      pending: { bg: "#fef3c7", text: "#92400e" },
      approved: { bg: "#d1fae5", text: "#065f46" },
      rejected: { bg: "#fee2e2", text: "#991b1b" },
      completed: { bg: "#dbeafe", text: "#1e40af" },
    };
    const c = colors[status.toLowerCase()] || { bg: "#f1f5f9", text: "#475569" };
    return <span style={{ padding: "0.25rem 0.75rem", borderRadius: "999px", fontSize: "0.75rem", fontWeight: "bold", background: c.bg, color: c.text, textTransform: "uppercase" }}>{status}</span>;
  };

  if (loading) return <div style={{ textAlign: "center", padding: "3rem" }}>Loading dashboard...</div>;

  return (
    <div>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.8rem", fontWeight: "bold", color: "#0f172a", margin: 0 }}>Welcome to EACIP</h1>
        <p style={{ color: "#64748b", marginTop: "0.5rem" }}>Manage your operational tasks and AI-driven workflows.</p>
      </div>

      <div style={{ background: "white", borderRadius: "12px", border: "1px solid #e2e8f0", overflow: "hidden", boxShadow: "0 1px 3px 0 rgba(0,0,0,0.1)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
              <th style={{ padding: "1rem 1.5rem", color: "#475569", fontSize: "0.85rem", fontWeight: "600", textTransform: "uppercase" }}>Task Title</th>
              <th style={{ padding: "1rem 1.5rem", color: "#475569", fontSize: "0.85rem", fontWeight: "600", textTransform: "uppercase" }}>Scope</th>
              <th style={{ padding: "1rem 1.5rem", color: "#475569", fontSize: "0.85rem", fontWeight: "600", textTransform: "uppercase" }}>Status</th>
              <th style={{ padding: "1rem 1.5rem", color: "#475569", fontSize: "0.85rem", fontWeight: "600", textTransform: "uppercase" }}>Created At</th>
              <th style={{ padding: "1rem 1.5rem" }}></th>
            </tr>
          </thead>
          <tbody>
            {tasks.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: "3rem", textAlign: "center", color: "#64748b" }}>
                  No tasks found. Click "+ New Task" to create one.
                </td>
              </tr>
            ) : (
              tasks.map((task) => (
                <tr key={task.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "1rem 1.5rem" }}>
                    <div style={{ fontWeight: "600", color: "#0f172a" }}>{task.title}</div>
                    <div style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "0.2rem", display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{task.description}</div>
                  </td>
                  <td style={{ padding: "1rem 1.5rem" }}>
                    <span style={{ background: "#f1f5f9", color: "#334155", padding: "0.25rem 0.5rem", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "500" }}>
                      {task.use_case || "Generic"}
                    </span>
                  </td>
                  <td style={{ padding: "1rem 1.5rem" }}>{getStatusBadge(task.status)}</td>
                  <td style={{ padding: "1rem 1.5rem", fontSize: "0.9rem", color: "#64748b" }}>
                    {new Date(task.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: "1rem 1.5rem", textAlign: "right" }}>
                    <Link to={`/tasks/${task.id}`} style={{ color: "#4f46e5", fontWeight: "600", fontSize: "0.9rem" }}>
                      View →
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}