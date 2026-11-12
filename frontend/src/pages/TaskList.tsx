import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Inbox } from "lucide-react";
import { tasksApi } from "../api/tasks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

function statusVariant(status: string): "success" | "warning" | "destructive" | "info" | "muted" {
  switch (status) {
    case "approved": return "success";
    case "rejected": return "destructive";
    case "processing": return "info";
    case "pending": return "warning";
    case "ready": return "info";
    default: return "muted";
  }
}

export default function TaskList() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.list(),
  });

  const tasks = data?.tasks ?? [];
  const total = data?.total ?? 0;
  const pending = tasks.filter((t) => t.status === "pending" || t.status === "processing").length;
  const approved = tasks.filter((t) => t.status === "approved").length;
  const rejected = tasks.filter((t) => t.status === "rejected").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Tasks</h1>
          <p className="text-muted-foreground mt-1">Manage operational tasks and AI-driven workflows.</p>
        </div>
        <Button onClick={() => navigate("/tasks/new")}>
          <Plus className="w-4 h-4 mr-2" /> New Task
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-semibold">{total}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Processing</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-semibold">{pending}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Approved</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-semibold text-emerald-600">{approved}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Rejected</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-semibold text-red-600">{rejected}</div></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Tasks</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading tasks...</div>
          ) : isError ? (
            <div className="p-8 text-center text-destructive">
              Error: {(error as Error).message}
            </div>
          ) : tasks.length === 0 ? (
            <div className="p-12 text-center">
              <Inbox className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">No tasks yet.</p>
              <Button onClick={() => navigate("/tasks/new")}>Create your first task</Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Task</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Scope</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Created</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {tasks.map((task) => (
                    <tr key={task.id} className="hover:bg-muted/50 transition-colors">
                      <td className="px-6 py-4 max-w-md">
                        <div className="font-medium text-foreground truncate">{task.title}</div>
                        <div className="text-sm text-muted-foreground truncate">{task.description}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm capitalize">{task.use_case?.replace(/_/g, " ") ?? "—"}</span>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={statusVariant(task.status)}>{task.status}</Badge>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {new Date(task.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button variant="ghost" size="sm" onClick={() => navigate(`/tasks/${task.id}`)}>
                          View →
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}