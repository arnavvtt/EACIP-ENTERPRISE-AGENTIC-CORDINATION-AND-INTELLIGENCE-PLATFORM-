import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import TaskList from "./pages/TaskList";
import TaskInput from "./pages/TaskInput";
import TaskDetail from "./pages/TaskDetail";
import ContextWorkspace from "./pages/ContextWorkspace";
import OperationalPackage from "./pages/OperationalPackage";
import WorkflowDashboard from "./pages/WorkflowDashboard";
import AuditLog from "./pages/AuditLog";

function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<TaskList />} />
          <Route path="/tasks/new" element={<TaskInput />} />
          <Route path="/tasks/:id" element={<TaskDetail />} />
          <Route path="/tasks/:id/workspace" element={<ContextWorkspace />} />
          <Route path="/tasks/:id/package" element={<OperationalPackage />} />
          <Route path="/tasks/:id/workflow" element={<WorkflowDashboard />} />
          <Route path="/tasks/:id/audit" element={<AuditLog />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}

export default App;