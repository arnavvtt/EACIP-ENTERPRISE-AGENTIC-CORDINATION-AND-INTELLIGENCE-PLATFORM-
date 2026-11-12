import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";

export default function WorkflowDashboard() {
  const { id } = useParams<{ id: string }>();
  const [workflow, setWorkflow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [initiating, setInitiating] = useState(false);
  const [reviewing, setReviewing] = useState(false);

  const fetchWorkflow = async () => {
    if (!id) return;
    try {
      const data = await tasksApi.getWorkflow(id);
      setWorkflow(data);
    } catch (err: any) {
      if (err?.response?.status === 404) {
        setWorkflow(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflow();
  }, [id]);

  const handleInitiate = async () => {
    if (!id) return;
    setInitiating(true);
    try {
      const res = await tasksApi.initiateWorkflow(id);
      setWorkflow(res); // Set response (which contains proposed_action if paused)
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to initiate workflow");
    } finally {
      setInitiating(false);
    }
  };

  const handleDecision = async (decision: "approved" | "rejected") => {
    if (!id || !workflow) return;
    setReviewing(true);
    try {
      const actionId = workflow.proposed_action?.action_id;
      const res = await tasksApi.resumeWorkflow(id, workflow.workflow_id, decision, actionId);
      alert(`Workflow ${res.status}: ${res.execution_result || "Action processed."}`);
      await fetchWorkflow(); // Reload to show completed/rejected status
    } catch (err: any) {
      alert("Failed to submit decision: " + (err?.response?.data?.detail || err.message));
    } finally {
      setReviewing(false);
    }
  };

  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;

  // Helper to render dynamic AI action
  const renderActionDetails = (actionData: any) => {
    if (!actionData) return null;
    const { tool, reason, ...params } = actionData;

    return (
      <div style={{ background: "#f9fafb", padding: "1rem", borderRadius: "6px", border: "1px solid #e5e7eb", marginTop: "1rem" }}>
        <p><strong>AI Reasoning:</strong> {reason}</p>
        <p><strong>Selected Tool:</strong> <span style={{ background: "#dbeafe", color: "#1e40af", padding: "0.2rem 0.5rem", borderRadius: "4px" }}>{tool}</span></p>
        
        <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
          {Object.entries(params).filter(([_, v]) => v !== null).map(([key, value]) => (
            <div key={key} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.3rem" }}>
              <span style={{ fontWeight: "bold", minWidth: "80px" }}>{key}:</span>
              <span style={{ color: "#4b5563", whiteSpace: "pre-wrap" }}>{String(value)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto", fontFamily: "sans-serif" }}>
      <Link to={`/tasks/${id}`} style={{ color: "#4f46e5", textDecoration: "none" }}>
        ← Back to Task
      </Link>
      
      <h1 style={{ marginTop: "1rem" }}>Agentic Coordination Dashboard</h1>
      <p style={{ color: "#666", marginBottom: "2rem" }}>
        Phase 2: Governed Operational Coordination (LangGraph + HITL)
      </p>

      {!workflow ? (
        <div style={{ background: "#f9fafb", padding: "2rem", textAlign: "center", borderRadius: "8px", border: "1px dashed #ccc" }}>
          <h3>No Workflow Initiated</h3>
          <p style={{ color: "#666", marginBottom: "1.5rem" }}>
            The LangGraph Agent will analyze the approved package and propose an action.
          </p>
          <button 
            onClick={handleInitiate} 
            disabled={initiating}
            style={{ padding: "0.8rem 1.5rem", background: "#4f46e5", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}
          >
            {initiating ? "Agent is thinking..." : "🤖 Initiate LangGraph Workflow"}
          </button>
        </div>
      ) : (
        <div>
          {/* Status Header */}
          <div style={{ 
            background: workflow.status === "completed" ? "#d1fae5" : (workflow.status === "rejected" ? "#fee2e2" : "#e0e7ff"), 
            padding: "1rem", 
            borderRadius: "8px", 
            marginBottom: "2rem", 
            borderLeft: `4px solid ${workflow.status === "completed" ? "#059669" : (workflow.status === "rejected" ? "#dc2626" : "#4f46e5")}` 
          }}>
            <p style={{ margin: 0 }}><strong>Workflow ID:</strong> {workflow.workflow_id}</p>
            <p style={{ margin: "0.5rem 0 0 0" }}><strong>Status:</strong> <span style={{ textTransform: "uppercase", fontWeight: "bold" }}>{workflow.status}</span></p>
          </div>

          {/* Agent Interrupt / Action Card */}
          {workflow.status === "waiting_for_approval" && workflow.proposed_action && (
            <div style={{ background: "#fffbeb", border: "1px solid #fcd34d", padding: "1.5rem", borderRadius: "8px" }}>
              <h3 style={{ marginTop: 0, color: "#b45309" }}>🤖 Human Approval Required</h3>
              <p>The LangGraph Agent is paused and waiting for your decision.</p>
              
              {renderActionDetails(workflow.proposed_action.action)}

              <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
                <button 
                  onClick={() => handleDecision("approved")}
                  disabled={reviewing}
                  style={{ padding: "0.6rem 1.2rem", background: "#059669", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}
                >
                  {reviewing ? "Processing..." : "✅ Approve Action"}
                </button>
                <button 
                  onClick={() => handleDecision("rejected")}
                  disabled={reviewing}
                  style={{ padding: "0.6rem 1.2rem", background: "#dc2626", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}
                >
                  {reviewing ? "Processing..." : "❌ Reject Action"}
                </button>
              </div>
            </div>
          )}

          {/* Completed View */}
          {workflow.status === "completed" && (
            <div style={{ background: "#f0fdf4", padding: "1.5rem", borderRadius: "8px", border: "1px solid #bbf7d0" }}>
              <h3 style={{ marginTop: 0, color: "#166534" }}>✅ Workflow Completed</h3>
              <p>The agent executed the approved action successfully.</p>
            </div>
          )}

          {/* Rejected View */}
          {workflow.status === "rejected" && (
            <div style={{ background: "#fee2e2", padding: "1.5rem", borderRadius: "8px", border: "1px solid #fca5a5" }}>
              <h3 style={{ marginTop: 0, color: "#991b1b" }}>❌ Workflow Rejected</h3>
              <p>The proposed action was rejected by the human. The agent has been stopped.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}