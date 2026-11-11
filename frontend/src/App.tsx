import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import TaskList from "./pages/TaskList";
import TaskInput from "./pages/TaskInput";
import TaskDetail from "./pages/TaskDetail";
import ContextWorkspace from "./pages/ContextWorkspace";
import OperationalPackage from "./pages/OperationalPackage";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ... purane routes ... */}
        <Route path="/tasks/:id" element={<TaskDetail />} />
        <Route path="/tasks/:id/workspace" element={<ContextWorkspace />} />
        
        {/* NAYA ROUTE */}
        <Route path="/tasks/:id/package" element={<OperationalPackage />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;