import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type { TaskResponse } from "../types/task";

export default function TaskList() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    tasksApi
      .list()
      .then((data) => {
        setTasks(data.tasks);
        setTotal(data.total);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;
  if (error)
    return <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>;

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1>Tasks ({total})</h1>
        <Link
          to="/tasks/new"
          style={{
            padding: "0.5rem 1rem",
            background: "#2563eb",
            color: "white",
            textDecoration: "none",
            borderRadius: "4px",
            fontWeight: 500,
          }}
        >
          + New Task
        </Link>
      </div>

      {tasks.length === 0 ? (
        <p style={{ marginTop: "2rem", color: "#666" }}>
          No tasks yet. Create one to get started.
        </p>
      ) : (
        <div
          style={{
            marginTop: "2rem",
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
          }}
        >
          {tasks.map((task) => (
            <Link
              key={task.id}
              to={`/tasks/${task.id}`}
              style={{
                display: "block",
                padding: "1rem",
                border: "1px solid #e5e7eb",
                borderRadius: "6px",
                textDecoration: "none",
                color: "inherit",
                background: "white",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "start",
                  gap: "1rem",
                }}
              >
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: 0 }}>{task.title}</h3>
                  <p
                    style={{
                      margin: "0.5rem 0 0",
                      color: "#666",
                      fontSize: "0.9rem",
                    }}
                  >
                    {task.description.slice(0, 120)}
                    {task.description.length > 120 ? "..." : ""}
                  </p>
                </div>
                <span
                  style={{
                    padding: "0.25rem 0.75rem",
                    background:
                      task.status === "pending" ? "#fef3c7" : "#d1fae5",
                    color: task.status === "pending" ? "#92400e" : "#065f46",
                    borderRadius: "12px",
                    fontSize: "0.8rem",
                    fontWeight: 500,
                    whiteSpace: "nowrap",
                  }}
                >
                  {task.status}
                </span>
              </div>
              <p
                style={{
                  margin: "0.5rem 0 0",
                  color: "#999",
                  fontSize: "0.75rem",
                }}
              >
                {task.use_case || "No use case"} ·{" "}
                {new Date(task.created_at).toLocaleString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}