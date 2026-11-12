import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";

const SCOPES = [
  { id: "supplier_qualification", label: "Supplier Qualification & Onboarding" },
  { id: "employee_onboarding", label: "Employee Onboarding" },
  { id: "purchase_delay", label: "Critical Purchase Delay Resolution" },
];

export default function TaskInput() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [useCase, setUseCase] = useState("supplier_qualification");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title || !description || !useCase) {
      setError("Please fill all fields.");
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const newTask = await tasksApi.create({ 
        title, 
        description, 
        use_case: useCase 
      });
      navigate(`/tasks/${newTask.id}`); 
    } catch (err: any) {
      console.error("Full Error Object:", err);
      console.error("Response Data:", err.response?.data);
      
      let errorMsg = "Failed to create task.";
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Extract exact field and message from FastAPI 422 error
          errorMsg = err.response.data.detail.map((e: any) => `${e.loc.join('.')}: ${e.msg}`).join(', ');
        } else {
          errorMsg = err.response.data.detail;
        }
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "700px", margin: "0 auto", fontFamily: "sans-serif" }}>
      <Link to="/" style={{ color: "#4f46e5", textDecoration: "none", fontSize: "0.9rem", fontWeight: 500 }}>
        ← Back to Tasks
      </Link>

      <div style={{ marginTop: "1.5rem", background: "white", padding: "2rem", borderRadius: "12px", border: "1px solid #e5e7eb", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.05)" }}>
        <h1 style={{ marginTop: 0, fontSize: "1.8rem", color: "#111827" }}>Create New Operational Task</h1>
        
        {error && (
          <div style={{ background: "#fee2e2", color: "#991b1b", padding: "0.8rem", borderRadius: "6px", marginBottom: "1.5rem", fontSize: "0.9rem", fontWeight: "bold" }}>
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          
          <div>
            <label style={{ display: "block", fontWeight: "bold", color: "#374151", marginBottom: "0.5rem" }}>Operational Scope</label>
            <select 
              value={useCase} 
              onChange={(e) => setUseCase(e.target.value)}
              style={{ width: "100%", padding: "0.8rem", borderRadius: "6px", border: "1px solid #d1d5db", fontSize: "1rem", background: "#f9fafb", cursor: "pointer" }}
            >
              {SCOPES.map((scope) => (
                <option key={scope.id} value={scope.id}>{scope.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: "bold", color: "#374151", marginBottom: "0.5rem" }}>Task Title</label>
            <input 
              type="text" 
              value={title} 
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Qualify ABC Components as supplier"
              style={{ width: "100%", padding: "0.8rem", borderRadius: "6px", border: "1px solid #d1d5db", fontSize: "1rem" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontWeight: "bold", color: "#374151", marginBottom: "0.5rem" }}>Task Description / Details</label>
            <textarea 
              value={description} 
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what you want to achieve..."
              rows={4}
              style={{ width: "100%", padding: "0.8rem", borderRadius: "6px", border: "1px solid #d1d5db", fontSize: "1rem", resize: "vertical" }}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            style={{ padding: "1rem", background: loading ? "#9ca3af" : "#4f46e5", color: "white", border: "none", borderRadius: "6px", fontSize: "1.1rem", fontWeight: "bold", cursor: loading ? "not-allowed" : "pointer", marginTop: "1rem" }}
          >
            {loading ? "Creating Task..." : "Create Task & Start Pipeline →"}
          </button>
        </form>
      </div>
    </div>
  );
}