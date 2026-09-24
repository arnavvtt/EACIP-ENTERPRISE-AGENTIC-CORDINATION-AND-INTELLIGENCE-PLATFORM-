import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type {
  ContextWorkspaceResponse,
  Correlation,
  RetrievedRecord,
  TaskRequirement,
} from "../types/task";

export default function ContextWorkspace() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ContextWorkspaceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [correlating, setCorrelating] = useState(false);

  const loadContext = async (taskId: string) => {
    try {
      const res = await tasksApi.getContext(taskId);
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load workspace");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!id) return;
    loadContext(id);
  }, [id]);

  const handleCorrelate = async () => {
    if (!id) return;
    setCorrelating(true);
    setError(null);
    try {
      await tasksApi.correlate(id);
      await loadContext(id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Correlation failed");
    } finally {
      setCorrelating(false);
    }
  };

  if (loading)
    return (
      <div style={{ padding: "2rem", color: "#666" }}>
        Loading workspace...
      </div>
    );
  if (error && !data)
    return (
      <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>
    );
  if (!data) return null;

  const { task, requirements, retrieved_records, correlations } = data;
  const understandingData = (task.task_metadata?.understanding as any) || null;

  // Group retrieved records by source_key
  const grouped: Record<string, RetrievedRecord[]> = {};
  for (const r of retrieved_records) {
    const key = r.retrieval_metadata.source_key || "unknown";
    (grouped[key] ||= []).push(r);
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      {/* Top nav */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <Link to="/" style={{ color: "#2563eb", textDecoration: "none" }}>
          ← Back to tasks
        </Link>
        <Link
          to={`/tasks/${task.id}`}
          style={{
            color: "#2563eb",
            textDecoration: "none",
            fontSize: "0.9rem",
          }}
        >
          View task detail →
        </Link>
      </div>

      {/* Header */}
      <div style={{ marginTop: "1rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.6rem" }}>{task.title}</h1>
        <div
          style={{
            marginTop: "0.5rem",
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
            color: "#666",
            fontSize: "0.9rem",
          }}
        >
          <span>
            <strong>Intent:</strong> {task.intent || "—"}
          </span>
          <span>
            <strong>Use case:</strong> {task.use_case || "—"}
          </span>
          {understandingData && (
            <>
              <span>
                <strong>Confidence:</strong>{" "}
                {(understandingData.confidence * 100).toFixed(0)}%
              </span>
              <span>
                <strong>Provider:</strong> {understandingData.provider} /{" "}
                {understandingData.model}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Main grid */}
      <div
        style={{
          marginTop: "1.5rem",
          display: "grid",
          gridTemplateColumns: "minmax(280px, 1fr) minmax(400px, 2fr)",
          gap: "1rem",
        }}
      >
        {/* Left: Requirements */}
        <Section
          title={`Requirements (${requirements.length})`}
          accent="#7c3aed"
        >
          {requirements.length === 0 ? (
            <EmptyState message="No requirements identified yet." />
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
              }}
            >
              {requirements.map((r) => (
                <RequirementRow key={r.id} requirement={r} />
              ))}
            </div>
          )}
        </Section>

        {/* Right: Retrieved records */}
        <Section
          title={`Retrieved Records (${retrieved_records.length})`}
          accent="#059669"
        >
          {retrieved_records.length === 0 ? (
            <EmptyState message="No records retrieved yet." />
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              {Object.entries(grouped).map(([sourceKey, records]) => (
                <SourceGroup
                  key={sourceKey}
                  sourceKey={sourceKey}
                  records={records}
                />
              ))}
            </div>
          )}
        </Section>
      </div>

      {/* Correlations */}
      <div style={{ marginTop: "1rem" }}>
        <Section
          title={`Correlations (${correlations.length})`}
          accent="#d97706"
          action={
            <button
              onClick={handleCorrelate}
              disabled={correlating || retrieved_records.length === 0}
              style={btnStyle(
                correlating || retrieved_records.length === 0,
                "#d97706",
              )}
            >
              {correlating
                ? "Correlating..."
                : correlations.length > 0
                ? "Re-correlate"
                : "Run Correlation"}
            </button>
          }
        >
          {retrieved_records.length === 0 ? (
            <EmptyState message="Run retrieval first." />
          ) : correlations.length === 0 ? (
            <EmptyState message="No correlations yet. Click the button above." />
          ) : (
            <CorrelationGroups correlations={correlations} />
          )}
        </Section>
      </div>

      {/* Gaps & Inconsistencies (placeholder) */}
      <div style={{ marginTop: "1rem" }}>
        <Section title="Gaps & Inconsistencies" accent="#dc2626">
          <EmptyState message="Validation will run in Stage 9." />
        </Section>
      </div>

      {/* AI Insights (placeholder) */}
      <div style={{ marginTop: "1rem" }}>
        <Section title="AI-Assisted Insights" accent="#0891b2">
          <EmptyState message="Insights will be generated in Stage 11." />
        </Section>
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
// Sub-components
// ---------------------------------------------------------------------

function CorrelationGroups({ correlations }: { correlations: Correlation[] }) {
  const anchorPairs: Correlation[] = [];
  const secondaryPairs: Correlation[] = [];

  for (const c of correlations) {
    if (c.correlation_metadata.pair_kind === "secondary") {
      secondaryPairs.push(c);
    } else {
      anchorPairs.push(c);
    }
  }

  // Group anchor pairs by anchor_external_id
  const byAnchor: Record<string, Correlation[]> = {};
  for (const c of anchorPairs) {
    const key = c.correlation_metadata.anchor_external_id || "unknown";
    (byAnchor[key] ||= []).push(c);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {Object.entries(byAnchor).map(([anchorId, items]) => (
        <div key={anchorId}>
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              color: "#d97706",
              letterSpacing: "0.5px",
              textTransform: "uppercase",
              marginBottom: "0.35rem",
            }}
          >
            {anchorId} · {items.length}{" "}
            {items.length === 1 ? "correlation" : "correlations"}
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.35rem",
            }}
          >
            {items.map((c) => {
              const otherExternalId =
                c.correlation_metadata.record_a_external_id === anchorId
                  ? c.correlation_metadata.record_b_external_id
                  : c.correlation_metadata.record_a_external_id;
              return (
                <CorrelationRow
                  key={c.id}
                  otherExternalId={otherExternalId || "?"}
                  relationshipType={c.relationship_type}
                  basis={c.basis}
                  confidence={c.confidence}
                  matchedFields={c.correlation_metadata.matched_fields}
                />
              );
            })}
          </div>
        </div>
      ))}

      {secondaryPairs.length > 0 && (
        <div>
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              color: "#9ca3af",
              letterSpacing: "0.5px",
              textTransform: "uppercase",
              marginBottom: "0.35rem",
            }}
          >
            Secondary relationships · {secondaryPairs.length}
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.35rem",
            }}
          >
            {secondaryPairs.map((c) => (
              <CorrelationRow
                key={c.id}
                otherExternalId={`${c.correlation_metadata.record_a_external_id} ↔ ${c.correlation_metadata.record_b_external_id}`}
                relationshipType={c.relationship_type}
                basis={c.basis}
                confidence={c.confidence}
                matchedFields={c.correlation_metadata.matched_fields}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function CorrelationRow({
  otherExternalId,
  relationshipType,
  basis,
  confidence,
  matchedFields,
}: {
  otherExternalId: string;
  relationshipType: string;
  basis: string;
  confidence: number;
  matchedFields?: string[];
}) {
  return (
    <div
      style={{
        padding: "0.5rem 0.75rem",
        border: "1px solid #e5e7eb",
        borderRadius: "6px",
        background: "#fffbeb",
        fontSize: "0.85rem",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <span style={{ fontWeight: 600, color: "#111" }}>
          {otherExternalId}
        </span>
        <span
          style={{
            fontSize: "0.7rem",
            color: "#92400e",
            background: "#fef3c7",
            padding: "0.1rem 0.4rem",
            borderRadius: "6px",
            fontWeight: 500,
          }}
        >
          {confidence.toFixed(2)}
        </span>
      </div>
      <div
        style={{
          marginTop: "0.25rem",
          color: "#666",
          fontSize: "0.75rem",
        }}
      >
        {relationshipType} · <em>{basis}</em>
        {matchedFields && matchedFields.length > 0 && (
          <> · matched: {matchedFields.join(", ")}</>
        )}
      </div>
    </div>
  );
}

function Section({
  title,
  accent,
  action,
  children,
}: {
  title: string;
  accent: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        background: "white",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "1.25rem",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.75rem",
          gap: "1rem",
        }}
      >
        <div
          style={{
            fontSize: "0.85rem",
            fontWeight: 700,
            color: accent,
            letterSpacing: "0.5px",
            textTransform: "uppercase",
          }}
        >
          {title}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

function RequirementRow({ requirement }: { requirement: TaskRequirement }) {
  const mandatory = requirement.is_mandatory;
  return (
    <div
      style={{
        padding: "0.6rem 0.75rem",
        border: "1px solid #e5e7eb",
        borderRadius: "6px",
        background: mandatory ? "#fef3c7" : "#f9fafb",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <span style={{ fontWeight: 600, color: "#111", fontSize: "0.9rem" }}>
          {requirement.requirement_type}
        </span>
        {mandatory && (
          <span
            style={{
              fontSize: "0.7rem",
              color: "#92400e",
              background: "#fee2e2",
              padding: "0.1rem 0.4rem",
              borderRadius: "6px",
              fontWeight: 500,
            }}
          >
            mandatory
          </span>
        )}
      </div>
      {requirement.source_hint && (
        <div
          style={{
            fontSize: "0.75rem",
            color: "#1e40af",
            marginTop: "0.25rem",
          }}
        >
          {requirement.source_hint}
        </div>
      )}
    </div>
  );
}

function SourceGroup({
  sourceKey,
  records,
}: {
  sourceKey: string;
  records: RetrievedRecord[];
}) {
  return (
    <div>
      <div
        style={{
          fontSize: "0.75rem",
          fontWeight: 700,
          color: "#059669",
          letterSpacing: "0.5px",
          textTransform: "uppercase",
          marginBottom: "0.35rem",
        }}
      >
        {sourceKey} · {records.length}{" "}
        {records.length === 1 ? "record" : "records"}
      </div>
      <div
        style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}
      >
        {records.map((r) => (
          <div
            key={r.id}
            style={{
              padding: "0.5rem 0.75rem",
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
              background: "#f9fafb",
              fontSize: "0.85rem",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <span style={{ fontWeight: 600, color: "#111" }}>
                {r.retrieval_metadata.external_id || "unknown"}
                <span
                  style={{
                    marginLeft: "0.5rem",
                    color: "#666",
                    fontWeight: 400,
                  }}
                >
                  ({r.retrieval_metadata.record_type})
                </span>
              </span>
              {r.relevance_score !== null && (
                <span
                  style={{
                    fontSize: "0.7rem",
                    color: "#92400e",
                    background: "#fef3c7",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "6px",
                    fontWeight: 500,
                  }}
                >
                  {r.relevance_score.toFixed(2)}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div
      style={{
        padding: "1rem",
        color: "#999",
        fontStyle: "italic",
        fontSize: "0.9rem",
        textAlign: "center",
      }}
    >
      {message}
    </div>
  );
}

const btnStyle = (disabled: boolean, color: string): React.CSSProperties => ({
  padding: "0.4rem 0.9rem",
  background: disabled ? "#999" : color,
  color: "white",
  border: "none",
  borderRadius: "4px",
  cursor: disabled ? "not-allowed" : "pointer",
  fontSize: "0.8rem",
  fontWeight: 500,
});