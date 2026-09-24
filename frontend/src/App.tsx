import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import TaskList from "./pages/TaskList";
import TaskInput from "./pages/TaskInput";
import TaskDetail from "./pages/TaskDetail";
import ContextWorkspace from "./pages/ContextWorkspace";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TaskList />} />
        <Route path="/tasks/new" element={<TaskInput />} />
        <Route path="/tasks/:id" element={<TaskDetail />} />
        <Route path="/tasks/:id/workspace" element={<ContextWorkspace />} />
        <Route path="/status" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;