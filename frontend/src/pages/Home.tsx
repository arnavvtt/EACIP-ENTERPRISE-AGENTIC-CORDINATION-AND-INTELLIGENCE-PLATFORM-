import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

type HealthResponse = {
  status: string;
  database: string;
  version: string;
  service: string;
};

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<HealthResponse>("/health")
      .then((res) => setHealth(res.data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1>EACIP</h1>
      <p>Enterprise Agentic Coordination &amp; Intelligence Platform</p>

      <div style={{ marginTop: "2rem", padding: "1rem", background: "white", borderRadius: "8px" }}>
        <h2>System Status</h2>
        {error && <p style={{ color: "red" }}>Error: {error}</p>}
        {health ? (
          <ul>
            <li>Service: {health.service}</li>
            <li>Version: {health.version}</li>
            <li>API: {health.status}</li>
            <li>Database: {health.database}</li>
          </ul>
        ) : (
          !error && <p>Loading...</p>
        )}
      </div>
    </div>
  );
}