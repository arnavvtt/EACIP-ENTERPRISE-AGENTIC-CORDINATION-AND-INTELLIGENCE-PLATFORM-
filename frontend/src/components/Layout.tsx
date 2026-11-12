import { Link, useLocation } from "react-router-dom";

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Navigation Bar */}
      <nav style={{ background: "white", borderBottom: "1px solid #e2e8f0", padding: "0 2rem", height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div style={{ width: "32px", height: "32px", background: "#4f46e5", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: "bold", fontSize: "1.2rem" }}>
            E
          </div>
          <span style={{ fontSize: "1.25rem", fontWeight: "700", color: "#111827" }}>EACIP</span>
        </div>
        
        <div style={{ display: "flex", gap: "2rem", alignItems: "center" }}>
          <Link to="/" style={{ fontSize: "0.95rem", fontWeight: "500", color: location.pathname === "/" ? "#4f46e5" : "#64748b" }}>
            Dashboard
          </Link>
          <Link 
            to="/tasks/new" 
            style={{ background: "#4f46e5", color: "white", padding: "0.5rem 1rem", borderRadius: "6px", fontSize: "0.9rem", fontWeight: "600", transition: "background 0.2s" }}
          >
            + New Task
          </Link>
        </div>
      </nav>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: "2rem", maxWidth: "1200px", margin: "0 auto", width: "100%" }}>
        {children}
      </main>
    </div>
  );
}