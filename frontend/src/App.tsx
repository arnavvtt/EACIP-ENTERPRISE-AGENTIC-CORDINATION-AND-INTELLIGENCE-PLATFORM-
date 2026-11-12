import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import TaskList from "./pages/TaskList";
import TaskInput from "./pages/TaskInput";
import TaskDetail from "./pages/TaskDetail";
import ContextWorkspace from "./pages/ContextWorkspace";
import OperationalPackage from "./pages/OperationalPackage";
import WorkflowDashboard from "./pages/WorkflowDashboard";
import AuditLog from "./pages/AuditLog"; // NAYA IMPORT

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          {/* Base Route */}
          <Route path="/" element={<TaskList />} />

          {/* Specific Routes FIRST (Taaki 'new' ko UUID na samjhe) */}
          <Route path="/tasks/new" element={<TaskInput />} />

          {/* Dynamic Routes AFTER */}
          <Route path="/tasks/:id" element={<TaskDetail />} />
          <Route path="/tasks/:id/workspace" element={<ContextWorkspace />} />
          <Route path="/tasks/:id/package" element={<OperationalPackage />} />
          <Route path="/tasks/:id/workflow" element={<WorkflowDashboard />} />
          
          {/* NAYA ROUTE: Audit Logs */}
          <Route path="/tasks/:id/audit" element={<AuditLog />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;