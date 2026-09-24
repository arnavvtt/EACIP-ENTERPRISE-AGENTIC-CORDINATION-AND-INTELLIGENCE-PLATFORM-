import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type {
  RetrievedRecord,
  TaskRequirement,
  TaskResponse,
} from "../types/task";

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [requirements, setRequirements] = useState<TaskRequirement[]>([]);
  const [retrieved, setRetrieved] = useState<RetrievedRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [understanding, setUnderstanding] = useState(false);
  const [identifying, setIdentifying] = useState(false);
  const [retrieving, setRetrieving] = useState(false);

  const loadRequirements = async (taskId: string) => {
    try {
      const res = await tasksApi.getRequirements(taskId);
      setRequirements(res.requirements);
    } catch {
      /* no requirements yet */
    }
  };

  const loadRetrieved = async (taskId: string) => {
    try {
      const res = await tasksApi.getRetrievedRecords(taskId);
      setRetrieved(res.records);
    } catch {
      /* no retrieved records yet */
    }
  };

  useEffect(() => {
    if (!id) return;
    tasksApi
      .get(id)
      .then(async (t) => {
        setTask(t);
        if (t.use_case) {
          await loadRequirements(id);
          await loadRetrieved(id);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleUnderstand = async () => {
    if (!id) return;
    setUnderstanding(true);
    setError(null);
    try {
      setTask(await tasksApi.understand(id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Understanding failed");
    } finally {
      setUnderstanding(false);
    }
  };

  const handleIdentify = async () => {
    if (!id) return;
    setIdentifying(true);
    setError(null);
    try {
      await tasksApi.identifyRequirements(id);
      await loadRequirements(id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Identification failed");
    } finally {
      setIdentifying(false);
    }
  };

  const handleRetrieve = async () => {
    if (!id) return;
    setRetrieving(true);
    setError(null);
    try {
      await tasksApi.retrieve(id);
      await loadRetrieved(id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Retrieval failed");
    } finally {
      setRetrieving(false);
    }
  };

  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;
  if (error && !task)
    return (
      <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>
    );
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

  // group retrieved by source_key for display
  const grouped: Record<string, RetrievedRecord[]> = {};
  for (const r of retrieved) {
    const key = r.retrieval_metadata.source_key || "unknown";
    (grouped[key] ||= []).push(r);
  }

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

      {/* Description */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Description</h2>
        <p style={{ lineHeight: 1.6, color: "#374151" }}>{task.description}</p>
      </div>

      {/* Understanding */}
      <div style={cardStyle}>
        <div style={flexBetween}>
          <h2 style={h2Style}>Understanding</h2>
          <button
            onClick={handleUnderstand}
            disabled={understanding}
            style={btnStyle(understanding, "#2563eb")}
          >
            {understanding
              ? "Analyzing..."
              : understandingData
              ? "Re-analyze"
              : "Run Task Understanding"}
          </button>
        </div>
        {understandingData ? (
          <div style={{ marginTop: "1rem" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                <Row label="Intent" value={task.intent || "—"} />
                <Row label="Use case" value={task.use_case || "—"} />
                <Row label="Summary" value={understandingData.summary} />
                <Row
                  label="Confidence"
                  value={
                    typeof understandingData.confidence === "number"
                      ? (understandingData.confidence * 100).toFixed(0) + "%"
                      : "—"
                  }
                />
                <Row
                  label="Provider"
                  value={`${understandingData.provider} / ${understandingData.model} / ${Math.round(
                    understandingData.latency_ms,
                  )} ms`}
                  muted
                />
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ marginTop: "1rem", color: "#666" }}>
            Not yet analyzed. Click the button above.
          </p>
        )}
      </div>

      {/* Requirements */}
      <div style={cardStyle}>
        <div style={flexBetween}>
          <h2 style={h2Style}>
            Requirements{" "}
            {requirements.length > 0 && `(${requirements.length})`}
          </h2>
          <button
            onClick={handleIdentify}
            disabled={identifying || !task.use_case}
            style={btnStyle(identifying || !task.use_case, "#7c3aed")}
          >
            {identifying
              ? "Identifying..."
              : requirements.length > 0
              ? "Re-identify"
              : "Identify Requirements"}
          </button>
        </div>

        {!task.use_case ? (
          <p style={{ marginTop: "1rem", color: "#666" }}>
            Run task understanding first.
          </p>
        ) : requirements.length === 0 ? (
          <p style={{ marginTop: "1rem", color: "#666" }}>
            No requirements identified yet.
          </p>
        ) : (
          <div
            style={{
              marginTop: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.6rem",
            }}
          >
            {requirements.map((r) => (
              <div key={r.id} style={reqCardStyle}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "start",
                    gap: "1rem",
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, color: "#111" }}>
                      {r.requirement_type}
                    </div>
                    <div
                      style={{
                        color: "#666",
                        fontSize: "0.9rem",
                        marginTop: "0.25rem",
                      }}
                    >
                      {r.description}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "0.4rem", flexShrink: 0 }}>
                    {r.is_mandatory ? (
                      <span style={badge("#fee2e2", "#991b1b")}>
                        mandatory
                      </span>
                    ) : (
                      <span style={badge("#e5e7eb", "#374151")}>optional</span>
                    )}
                    {r.source_hint && (
                      <span style={badge("#dbeafe", "#1e40af")}>
                        {r.source_hint}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Retrieved Records */}
      <div style={cardStyle}>
        <div style={flexBetween}>
          <h2 style={h2Style}>
            Retrieved Records{" "}
            {retrieved.length > 0 && `(${retrieved.length})`}
          </h2>
          <button
            onClick={handleRetrieve}
            disabled={retrieving || requirements.length === 0}
            style={btnStyle(
              retrieving || requirements.length === 0,
              "#059669",
            )}
          >
            {retrieving
              ? "Retrieving..."
              : retrieved.length > 0
              ? "Re-retrieve"
              : "Run Retrieval"}
          </button>
        </div>

        {requirements.length === 0 ? (
          <p style={{ marginTop: "1rem", color: "#666" }}>
            Identify requirements first.
          </p>
        ) : retrieved.length === 0 ? (
          <p style={{ marginTop: "1rem", color: "#666" }}>
            No records retrieved yet.
          </p>
        ) : (
          <div style={{ marginTop: "1rem" }}>
            {Object.entries(grouped).map(([sourceKey, records]) => (
              <div key={sourceKey} style={{ marginBottom: "1rem" }}>
                <div
                  style={{
                    fontSize: "0.85rem",
                    fontWeight: 600,
                    color: "#1e40af",
                    marginBottom: "0.4rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  {sourceKey} · {records.length}{" "}
                  {records.length === 1 ? "record" : "records"}
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.4rem",
                  }}
                >
                  {records.map((rec) => (
                    <div key={rec.id} style={reqCardStyle}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "start",
                          gap: "1rem",
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, color: "#111" }}>
                            {rec.retrieval_metadata.external_id ||
                              "unknown-id"}
                            <span
                              style={{
                                marginLeft: "0.5rem",
                                fontWeight: 400,
                                color: "#666",
                                fontSize: "0.85rem",
                              }}
                            >
                              ({rec.retrieval_metadata.record_type})
                            </span>
                          </div>
                          <div
                            style={{
                              color: "#666",
                              fontSize: "0.85rem",
                              marginTop: "0.25rem",
                            }}
                          >
                            For requirement:{" "}
                            <strong>
                              {rec.retrieval_metadata.requirement_type}
                            </strong>
                          </div>
                        </div>
                        {rec.relevance_score !== null && (
                          <span
                            style={badge(
                              rec.relevance_score >= 1.0
                                ? "#d1fae5"
                                : "#fef3c7",
                              rec.relevance_score >= 1.0
                                ? "#065f46"
                                : "#92400e",
                            )}
                          >
                            {rec.relevance_score.toFixed(2)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Details */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Details</h2>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <tbody>
            <Row label="Task ID" value={task.id} mono />
            <Row
              label="Created"
              value={new Date(task.created_at).toLocaleString()}
            />
            <Row
              label="Last updated"
              value={new Date(task.updated_at).toLocaleString()}
            />
          </tbody>
        </table>
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
    </div>
  );
}

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------

const cardStyle: React.CSSProperties = {
  marginTop: "1rem",
  padding: "1.5rem",
  background: "white",
  border: "1px solid #e5e7eb",
  borderRadius: "6px",
};

const reqCardStyle: React.CSSProperties = {
  padding: "0.9rem 1rem",
  border: "1px solid #e5e7eb",
  borderRadius: "6px",
  background: "#fafafa",
};

const h2Style: React.CSSProperties = {
  marginTop: 0,
  fontSize: "1.1rem",
};

const flexBetween: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
};

function btnStyle(disabled: boolean, color: string): React.CSSProperties {
  return {
    padding: "0.5rem 1rem",
    background: disabled ? "#999" : color,
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: disabled ? "not-allowed" : "pointer",
    fontSize: "0.85rem",
    fontWeight: 500,
  };
}

function badge(bg: string, color: string): React.CSSProperties {
  return {
    padding: "0.2rem 0.6rem",
    background: bg,
    color: color,
    borderRadius: "10px",
    fontSize: "0.75rem",
    fontWeight: 500,
    whiteSpace: "nowrap",
  };
}

function Row({
  label,
  value,
  mono,
  muted,
}: {
  label: string;
  value: string;
  mono?: boolean;
  muted?: boolean;
}) {
  return (
    <tr>
      <td
        style={{
          padding: "0.5rem 0",
          color: "#666",
          width: "160px",
          verticalAlign: "top",
        }}
      >
        {label}
      </td>
      <td
        style={{
          padding: "0.5rem 0",
          verticalAlign: "top",
          fontFamily: mono ? "monospace" : undefined,
          fontSize: mono ? "0.9rem" : undefined,
          color: muted ? "#999" : undefined,
        }}
      >
        {value}
      </td>
    </tr>
  );
}