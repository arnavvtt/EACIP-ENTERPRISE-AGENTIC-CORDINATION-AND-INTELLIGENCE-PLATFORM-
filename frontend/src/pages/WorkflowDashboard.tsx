import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Bot, Mail, UserCheck, Database, CheckCircle2, XCircle,
  AlertCircle, Loader2, ArrowLeft, Send, ShieldAlert, Clock
} from "lucide-react";
import { tasksApi } from "../api/tasks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type ProposedAction = {
  action_id: string;
  agent_source: string;
  subtask_id: string;
  action: {
    tool: string;
    reason: string;
    recipient?: string | null;
    subject?: string | null;
    body?: string | null;
    role?: string | null;
    description?: string | null;
    field?: string | null;
    new_value?: string | null;
  };
  created_at: string;
};

export default function WorkflowDashboard() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [workflowState, setWorkflowState] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);

  const { data: currentWorkflow, isLoading } = useQuery({
    queryKey: ["workflow", id],
    queryFn: () => tasksApi.getWorkflow(id!),
    enabled: !!id,
    retry: 0,
  });

  const initiateMutation = useMutation({
    mutationFn: () => tasksApi.initiateWorkflow(id!),
    onSuccess: (data) => {
      setWorkflowState(data);
      qc.invalidateQueries({ queryKey: ["workflow", id] });
      toast.success("Workflow initiated", { description: "Agent is analyzing the package." });
    },
    onError: (e: any) => toast.error("Failed to initiate", { description: e?.response?.data?.detail }),
  });

  const resumeMutation = useMutation({
    mutationFn: (payload: { decision: "approved" | "rejected"; action_id: string }) =>
      tasksApi.resumeWorkflow(id!, workflowState.workflow_id, payload.decision, payload.action_id),
    onSuccess: (data) => {
      const prevAction = workflowState?.proposed_action;
      if (prevAction) {
        setHistory((h) => [...h, { ...prevAction, result: data.execution_result, decision: data.status === "rejected" ? "rejected" : "approved" }]);
      }
      if (data.status === "waiting_for_approval" && data.proposed_action) {
        setWorkflowState(data);
        toast.success("Action approved", { description: "Next action awaiting your review." });
      } else if (data.status === "completed") {
        setWorkflowState(data);
        toast.success("Workflow completed", { description: data.execution_result });
      } else if (data.status === "rejected") {
        setWorkflowState(data);
        toast.error("Workflow rejected");
      } else if (data.status === "failed") {
        setWorkflowState(data);
        toast.error("Workflow failed", { description: data.execution_result });
      }
    },
    onError: (e: any) => toast.error("Failed", { description: e?.response?.data?.detail }),
  });

  const workflow = workflowState || currentWorkflow;
  const status = workflow?.status;
  const proposed: ProposedAction | undefined = workflow?.proposed_action;

  const agentIcon = (source: string) => {
    if (source.toLowerCase().includes("exception")) return ShieldAlert;
    if (source.toLowerCase().includes("information")) return Mail;
    return Bot;
  };

  const toolIcon = (tool: string) => {
    if (tool === "send_email") return Send;
    if (tool === "assign_task") return UserCheck;
    if (tool === "update_database") return Database;
    return Bot;
  };

  if (isLoading) return (
    <div className="flex items-center justify-center h-96">
      <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
    </div>
  );

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <Link to={`/tasks/${id}`} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-4 h-4" /> Back to task
        </Link>
        <h1 className="text-3xl font-semibold tracking-tight mt-2">Agentic Coordination</h1>
        <p className="text-muted-foreground mt-1">Multi-agent workflow with human-in-the-loop approval.</p>
      </div>

      {/* Empty State */}
      {!workflow || (workflow.status === "undefined" && !proposed) ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Bot className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No workflow initiated</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              The multi-agent system will analyze your approved package, decompose it into subtasks, and propose actions for human review.
            </p>
            <Button size="lg" onClick={() => initiateMutation.mutate()} disabled={initiateMutation.isPending}>
              {initiateMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Coordinating agents...</> : <><Bot className="w-4 h-4 mr-2" /> Initiate Workflow</>}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Status Header */}
          <Card className={cn(
            "border-l-4",
            status === "completed" && "border-l-emerald-500",
            status === "rejected" && "border-l-red-500",
            status === "failed" && "border-l-red-500",
            status === "waiting_for_approval" && "border-l-amber-500",
          )}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wider text-muted-foreground font-medium mb-1">Workflow ID</p>
                  <p className="font-mono text-sm">{workflow.workflow_id}</p>
                </div>
                <Badge variant={
                  status === "completed" ? "success" :
                  status === "rejected" || status === "failed" ? "destructive" :
                  status === "waiting_for_approval" ? "warning" : "info"
                } className="text-sm px-3 py-1">
                  {status?.replace(/_/g, " ")}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Pending Approval */}
          {status === "waiting_for_approval" && proposed && (
            <Card className="border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-900/10">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-amber-600" />
                  <CardTitle className="text-base">Human Approval Required</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Agent Attribution */}
                <div className="flex items-center gap-3 flex-wrap">
                  {(() => {
                    const Icon = agentIcon(proposed.agent_source);
                    return (
                      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium">
                        <Icon className="w-4 h-4" />
                        {proposed.agent_source}
                      </div>
                    );
                  })()}
                  <Badge variant="muted" className="text-xs font-mono">{proposed.subtask_id}</Badge>
                  <Badge variant="outline" className="text-xs">
                    Tool: {proposed.action.tool}
                  </Badge>
                </div>

                {/* Reasoning */}
                <div className="bg-background border border-border rounded-md p-4">
                  <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">AI Reasoning</p>
                  <p className="text-sm">{proposed.action.reason}</p>
                </div>

                {/* Email Preview */}
                {proposed.action.tool === "send_email" && (
                  <div className="border border-border rounded-md overflow-hidden">
                    <div className="bg-muted px-4 py-2 border-b border-border flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                        <Mail className="w-3 h-3" /> Email Preview
                      </div>
                      <Badge variant="warning" className="text-[10px]">SIMULATED</Badge>
                    </div>
                    <div className="p-4 space-y-2 bg-background">
                      <div className="text-xs"><span className="text-muted-foreground">To:</span> <span className="font-medium">{proposed.action.recipient}</span></div>
                      <div className="text-xs"><span className="text-muted-foreground">Subject:</span> <span className="font-medium">{proposed.action.subject}</span></div>
                      <div className="border-t border-border pt-3 mt-3 text-sm whitespace-pre-wrap text-foreground">{proposed.action.body}</div>
                    </div>
                  </div>
                )}

                {proposed.action.tool === "assign_task" && (
                  <div className="border border-border rounded-md p-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground"><UserCheck className="w-3 h-3" /> Task Assignment</div>
                    <div className="text-sm"><span className="text-muted-foreground">Role:</span> <span className="font-medium">{proposed.action.role}</span></div>
                    <div className="text-sm"><span className="text-muted-foreground">Task:</span> {proposed.action.description}</div>
                  </div>
                )}

                {proposed.action.tool === "update_database" && (
                  <div className="border border-border rounded-md p-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground"><Database className="w-3 h-3" /> Database Update</div>
                    <div className="text-sm"><span className="text-muted-foreground">Field:</span> <span className="font-mono">{proposed.action.field}</span></div>
                    <div className="text-sm"><span className="text-muted-foreground">New value:</span> <span className="font-mono">{proposed.action.new_value}</span></div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 pt-2">
                  <Button
                    className="flex-1"
                    onClick={() => resumeMutation.mutate({ decision: "approved", action_id: proposed.action_id })}
                    disabled={resumeMutation.isPending}
                  >
                    {resumeMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                    Approve
                  </Button>
                  <Button
                    variant="destructive"
                    className="flex-1"
                    onClick={() => resumeMutation.mutate({ decision: "rejected", action_id: proposed.action_id })}
                    disabled={resumeMutation.isPending}
                  >
                    <XCircle className="w-4 h-4 mr-2" /> Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Completed */}
          {status === "completed" && (
            <Card className="border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-900/10">
              <CardContent className="p-8 text-center">
                <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-600 mb-3" />
                <h3 className="text-lg font-semibold mb-1">Workflow Completed</h3>
                <p className="text-muted-foreground text-sm mb-1">{workflow.execution_result}</p>
              </CardContent>
            </Card>
          )}

          {/* Rejected */}
          {status === "rejected" && (
            <Card className="border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-900/10">
              <CardContent className="p-8 text-center">
                <XCircle className="w-12 h-12 mx-auto text-red-600 mb-3" />
                <h3 className="text-lg font-semibold mb-1">Workflow Rejected</h3>
                <p className="text-muted-foreground text-sm">The proposal was rejected. The workflow has stopped.</p>
              </CardContent>
            </Card>
          )}

          {/* Failed */}
          {status === "failed" && (
            <Card className="border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-900/10">
              <CardContent className="p-8 text-center">
                <AlertCircle className="w-12 h-12 mx-auto text-red-600 mb-3" />
                <h3 className="text-lg font-semibold mb-1">Workflow Failed</h3>
                <p className="text-muted-foreground text-sm">{workflow.execution_result || "One or more agents failed."}</p>
              </CardContent>
            </Card>
          )}

          {/* Execution History */}
          {history.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Execution History</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {history.map((h, i) => {
                  const Icon = toolIcon(h.action?.tool);
                  return (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-md border border-border bg-muted/30">
                      <div className={cn("w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                        h.decision === "rejected" ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"
                      )}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="text-sm font-medium">{h.action?.tool?.replace(/_/g, " ")}</span>
                          <Badge variant={h.decision === "rejected" ? "destructive" : "success"} className="text-[10px]">{h.decision}</Badge>
                          <span className="text-xs text-muted-foreground">by {h.agent_source}</span>
                        </div>
                        <p className="text-xs text-muted-foreground truncate">{h.result || "No execution"}</p>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}