import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { tasksApi } from "../api/tasks";
import type { TaskCreate } from "../types/task";

const USE_CASES = [
  { value: "supplier_qualification", label: "Supplier Qualification & Onboarding" },
  { value: "purchase_delay", label: "Critical Purchase Delay Resolution" },
  { value: "incident_investigation", label: "Incident Investigation + Remediation" },
  { value: "employee_onboarding", label: "Employee Onboarding" },
  { value: "customer_issue", label: "Customer Issue Resolution" },
];

export default function TaskInput() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [useCase, setUseCase] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const payload: TaskCreate = {
        title,
        description,
        use_case: useCase || null,
      };
      const task = await tasksApi.create(payload);
      navigate(`/tasks/${task.id}`);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to create task";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "700px", margin: "0 auto" }}>
      <h1>New Task</h1>
      <p style={{ color: "#666" }}>
        Describe the operational task. EACIP will prepare the context.
      </p>

      <form onSubmit={handleSubmit} style={{ marginTop: "2rem" }}>
        <div style={{ marginBottom: "1rem" }}>
          <label
            htmlFor="title"
            style={{ display: "block", marginBottom: "0.25rem", fontWeight: 500 }}
          >
            Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            maxLength={500}
            placeholder="Qualify ABC Components as supplier"
            style={{
              width: "100%",
              padding: "0.5rem",
              border: "1px solid #ccc",
              borderRadius: "4px",
            }}
          />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label
            htmlFor="description"
            style={{ display: "block", marginBottom: "0.25rem", fontWeight: 500 }}
          >
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            rows={5}
            placeholder="Prepare the complete operational context required to qualify ABC Components as a supplier."
            style={{
              width: "100%",
              padding: "0.5rem",
              border: "1px solid #ccc",
              borderRadius: "4px",
              resize: "vertical",
            }}
          />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label
            htmlFor="useCase"
            style={{ display: "block", marginBottom: "0.25rem", fontWeight: 500 }}
          >
            Use Case (optional)
          </label>
          <select
            id="useCase"
            value={useCase}
            onChange={(e) => setUseCase(e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem",
              border: "1px solid #ccc",
              borderRadius: "4px",
            }}
          >
            <option value="">— Auto-detect —</option>
            {USE_CASES.map((uc) => (
              <option key={uc.value} value={uc.value}>
                {uc.label}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div
            style={{
              padding: "0.75rem",
              background: "#fee",
              color: "#900",
              borderRadius: "4px",
              marginBottom: "1rem",
            }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          style={{
            padding: "0.75rem 1.5rem",
            background: submitting ? "#999" : "#2563eb",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: submitting ? "not-allowed" : "pointer",
            fontWeight: 500,
          }}
        >
          {submitting ? "Submitting..." : "Submit Task"}
        </button>
      </form>
    </div>
  );
}