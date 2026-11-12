"""
Agentic Workflow Service (Multi-Agent Foundation).
"""
from typing import Any
from uuid import UUID
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.types import Command

from app.models.workflow import Workflow
from app.models.audit_log import AuditLog
from app.repositories import PackageRepository, TaskRepository
from app.services.langgraph_engine import build_agent_graph
from app.services.checkpointer import get_langgraph_checkpointer

class AgenticWorkflowError(Exception):
    pass

class AgenticWorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pkg_repo = PackageRepository(session)
        self.task_repo = TaskRepository(session)

    def _log_audit(self, task_id: UUID, event_type: str, details: dict):
        audit = AuditLog(
            task_id=task_id,
            event_type=event_type,
            entity_type="workflow",
            actor="Human/System",
            details=details
        )
        self.session.add(audit)

    async def _log_specialist_failures(self, task_id: UUID, graph_state) -> None:
        """Log any failed specialist subtasks to audit trail."""
        outputs = (graph_state.values or {}).get("agent_outputs", [])
        for out in outputs:
            if out.get("status") == "failed":
                subtask = out.get("subtask", {}) or {}
                self._log_audit(task_id, "workflow.specialist_failed", {
                    "agent_source": out.get("agent", "Unknown"),
                    "subtask_id": subtask.get("id", "unknown"),
                    "subtask_description": subtask.get("description", ""),
                    "error": str(out.get("error", "Unknown error"))[:500]
                })

    async def initiate_workflow(self, task_id: UUID) -> dict[str, Any]:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise AgenticWorkflowError("Task not found.")

        pkg = await self.pkg_repo.get_latest_for_task(task_id)
        if not pkg or pkg.status != "approved":
            raise AgenticWorkflowError("Package must be approved.")

        workflow = Workflow(
            task_id=task_id,
            package_id=pkg.id,
            template_name="multi_agent_orchestration",
            status="active",
            description="Multi-Agent Workflow"
        )
        self.session.add(workflow)
        self._log_audit(task_id, "workflow.initiated", {"package_version": pkg.version})
        await self.session.commit()
        await self.session.refresh(workflow)

        checkpointer = await get_langgraph_checkpointer()
        graph = build_agent_graph(checkpointer)
        
        initial_state = {
            "task_id": str(task_id),
            "gaps": pkg.sections.get("section_7_information_gaps", []),
            "inconsistencies": pkg.sections.get("section_8_potential_inconsistencies", []),
            "modified_data": None,
            "subtasks": [],
            "current_subtask_index": 0,
            "agent_outputs": [],
            "pending_actions": [],
            "approved_action_id": None,
            "last_executed_action": None,
            "workflow_failed": False,
            "human_decision": "",
            "execution_result": ""
        }

        config = {"configurable": {"thread_id": str(workflow.id)}}
        result = await graph.ainvoke(initial_state, config)

        # Fetch actual state (result dict is incomplete on interrupt)
        graph_state = await graph.aget_state(config)
        current_values = graph_state.values or {}

        # Log any specialist failures
        await self._log_specialist_failures(task_id, graph_state)

        if "__interrupt__" in result:
            workflow.status = "active"
            await self.session.commit()
            interrupt_data = result["__interrupt__"][0].value
            return {
                "workflow_id": str(workflow.id),
                "status": "waiting_for_approval",
                "message": "Agent is waiting for human approval.",
                "proposed_action": interrupt_data.get("action_data")
            }
        else:
            # NEW: Distinguish failed vs completed
            if current_values.get("workflow_failed"):
                workflow.status = "failed"
            else:
                workflow.status = "completed"
            
            exec_result = current_values.get("execution_result") or result.get("execution_result", "Workflow finished.")
            event_type = "workflow.failed" if current_values.get("workflow_failed") else "workflow.completed_automatically"
            self._log_audit(task_id, event_type, {"result": exec_result})
            await self.session.commit()
            return {
                "workflow_id": str(workflow.id),
                "status": workflow.status,
                "message": exec_result,
                "proposed_action": None
            }

    async def resume_workflow(
        self, 
        task_id: UUID, 
        workflow_id: UUID, 
        decision: str, 
        action_id: str,
        modified_action: dict | None = None
    ) -> dict[str, Any]:
        
        stmt = select(Workflow).where(Workflow.id == workflow_id, Workflow.task_id == task_id)
        workflow = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if not workflow:
            raise AgenticWorkflowError("Workflow not found.")
            
        if workflow.status != "active":
            raise AgenticWorkflowError(f"Workflow is already {workflow.status}. Cannot resume.")

        checkpointer = await get_langgraph_checkpointer()
        graph = build_agent_graph(checkpointer)
        
        config = {"configurable": {"thread_id": str(workflow.id)}}
        
        resume_payload = decision
        if decision == "modified" and modified_action:
            resume_payload = {"decision": "modified", "modified_data": modified_action}

        # Fetch state before resume for audit
        state_before = await graph.aget_state(config)
        values_before = state_before.values or {}
        pending_before = values_before.get("pending_actions", [])
        current_action = next((a for a in pending_before if a.get("action_id") == action_id), None)
        
        agent_source = current_action.get("agent_source", "Unknown") if current_action else "Unknown"
        subtask_id = current_action.get("subtask_id", "Unknown") if current_action else "Unknown"

        # Log human decision
        self._log_audit(task_id, f"workflow.human_{decision}", {
            "action_id": action_id,
            "agent_source": agent_source,
            "subtask_id": subtask_id
        })
        await self.session.commit()

        result = await graph.ainvoke(Command(resume=resume_payload), config)

        # Fetch actual state
        graph_state = await graph.aget_state(config)
        current_values = graph_state.values or {}

        # Log specialist failures (only if modified - re-planning may have new failures)
        if decision == "modified":
            await self._log_specialist_failures(task_id, graph_state)

        # Log tool execution for approved actions
        if decision == "approved":
            executed_action = current_values.get("last_executed_action", {}) or {}
            self._log_audit(task_id, "workflow.tool_executed", {
                "result": current_values.get("execution_result"),
                "agent_source": executed_action.get("agent_source", "Unknown"),
                "subtask_id": executed_action.get("subtask_id", "Unknown")
            })
            await self.session.commit()

        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            
            if decision == "modified":
                msg = "Action modified. Agent re-planned and is waiting for new approval."
            else:
                msg = "Action approved. Next pending action is waiting for approval."
                
            return {
                "workflow_id": str(workflow.id),
                "status": "waiting_for_approval",
                "message": msg,
                "proposed_action": interrupt_data.get("action_data"),
                "execution_result": current_values.get("execution_result", "")
            }
        
        # No interrupt - workflow finished
        if current_values.get("workflow_failed"):
            workflow.status = "failed"
        elif decision == "rejected":
            workflow.status = "rejected"
        else:
            workflow.status = "completed"

        await self.session.commit()

        exec_result = current_values.get("execution_result", "")
        if not exec_result:
            if decision == "rejected":
                exec_result = "Action was rejected by human."
            elif decision == "modified":
                exec_result = "Action was modified. Agent is re-planning."
            else:
                exec_result = "No result."

        return {
            "workflow_id": str(workflow.id),
            "status": workflow.status,
            "execution_result": exec_result,
            "action_id_approved": action_id
        }