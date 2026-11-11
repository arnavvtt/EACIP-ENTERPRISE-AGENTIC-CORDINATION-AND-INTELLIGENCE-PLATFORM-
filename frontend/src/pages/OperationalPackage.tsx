import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { tasksApi } from "../api/tasks";

export default function OperationalPackage() {
  const { id } = useParams<{ id: string }>();
  const [pkg, setPkg] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reviewing, setReviewing] = useState(false);

  const fetchPackage = async () => {
    if (!id) return;
    try {
      const data = await tasksApi.getPackage(id);
      setPkg(data);
    } catch (err) {
      console.log("No package found yet");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPackage();
  }, [id]);

  const handleGenerate = async () => {
    if (!id) return;
    setGenerating(true);
    try {
      await tasksApi.generatePackage(id);
      await fetchPackage();
    } catch (err) {
      alert("Failed to generate package");
    } finally {
      setGenerating(false);
    }
  };

  const handleReview = async (decision: "approved" | "rejected") => {
    if (!id) return;
    const comments = decision === "approved" 
      ? "Approved by human reviewer." 
      : "Rejected by human reviewer.";
    
    setReviewing(true);
    try {
      await tasksApi.submitReview(id, decision, comments);
      await fetchPackage(); // Refresh to show new status
    } catch (err) {
      alert("Failed to submit review");
    } finally {
      setReviewing(false);
    }
  };

  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;

  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto", fontFamily: "sans-serif" }}>
      <Link to={`/tasks/${id}`} style={{ color: "#4f46e5", textDecoration: "none" }}>
        ← Back to Task
      </Link>
      
      <h1 style={{ marginTop: "1rem" }}>Operational Package</h1>
      
      {!pkg ? (
        <div style={{ marginTop: "2rem" }}>
          <p>No package generated yet.</p>
          <button 
            onClick={handleGenerate} 
            disabled={generating}
            style={{ padding: "0.5rem 1rem", background: "#4f46e5", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}
          >
            {generating ? "Generating..." : "Generate Package"}
          </button>
        </div>
      ) : (
        <div>
          {/* Header Card */}
          <div style={{ background: pkg.status === 'approved' ? "#d1fae5" : (pkg.status === 'rejected' ? "#fee2e2" : "#e0e7ff"), padding: "1.5rem", borderRadius: "8px", marginBottom: "2rem", borderLeft: `4px solid ${pkg.status === 'approved' ? "#059669" : (pkg.status === 'rejected' ? "#dc2626" : "#4f46e5")}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <p style={{ margin: "0 0 0.5rem 0" }}><strong>Status:</strong> <span style={{ fontWeight: "bold", textTransform: "uppercase" }}>{pkg.status}</span></p>
                <p style={{ margin: "0 0 0.5rem 0" }}><strong>Version:</strong> {pkg.version}</p>
                <p style={{ margin: 0 }}><strong>Summary:</strong> {pkg.summary}</p>
              </div>
              
              {/* Action Buttons */}
              <div style={{ display: "flex", gap: "1rem" }}>
                <button 
                  onClick={handleGenerate} 
                  disabled={generating || reviewing}
                  style={{ padding: "0.6rem 1.2rem", background: "#4f46e5", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
                >
                  {generating ? "Regenerating..." : "Regenerate"}
                </button>

                {/* Human Review Buttons - Only show if status is ready_for_review */}
                {pkg.status === "ready_for_review" && (
                  <>
                    <button 
                      onClick={() => handleReview("approved")} 
                      disabled={reviewing}
                      style={{ padding: "0.6rem 1.2rem", background: "#059669", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
                    >
                      {reviewing ? "Saving..." : "✅ Approve"}
                    </button>
                    <button 
                      onClick={() => handleReview("rejected")} 
                      disabled={reviewing}
                      style={{ padding: "0.6rem 1.2rem", background: "#dc2626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", fontWeight: "bold" }}
                    >
                      {reviewing ? "Saving..." : "❌ Reject"}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Sections List */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {Object.entries(pkg.sections).map(([key, value]: any) => (
              <div key={key} style={{ border: "1px solid #e5e7eb", borderRadius: "8px", padding: "1.5rem", background: "white", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
                <h3 style={{ marginTop: 0, marginBottom: "1rem", textTransform: "capitalize", color: "#1f2937", borderBottom: "2px solid #f3f4f6", paddingBottom: "0.5rem" }}>
                  {key.replace(/_/g, " ").replace("section ", "")}
                </h3>
                
                {typeof value === "object" && value !== null ? (
                  <div style={{ background: "#f9fafb", padding: "1rem", borderRadius: "6px", fontSize: "0.9rem", color: "#374151", overflowX: "auto" }}>
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <p style={{ margin: 0, color: "#4b5563" }}>{String(value)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}