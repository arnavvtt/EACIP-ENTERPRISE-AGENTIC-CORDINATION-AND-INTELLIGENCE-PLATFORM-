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
            "human_decision": "",
            "execution_result": ""
        }

        config = {"configurable": {"thread_id": str(workflow.id)}}
        result = await graph.ainvoke(initial_state, config)

        # Handle interrupt (waiting for human)
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            return {
                "workflow_id": str(workflow.id),
                "status": "waiting_for_approval",
                "message": "Agent is waiting for human approval.",
                "proposed_action": interrupt_data.get("action_data")
            }
        else:
            # Handle empty plans or completion
            workflow.status = "completed"
            exec_result = result.get("execution_result", "Workflow completed without human approval.")
            self._log_audit(task_id, "workflow.completed_automatically", {"result": exec_result})
            await self.session.commit()
            return {
                "workflow_id": str(workflow.id),
                "status": "completed",
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

        self._log_audit(task_id, f"workflow.human_{decision}", {"action_id": action_id})
        await self.session.commit()

        # CORRECTED: Removed extra indentation
        result = await graph.ainvoke(Command(resume=resume_payload), config)

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
                "proposed_action": interrupt_data.get("action_data")
            }
        elif decision in ["approved", "modified"] and not result.get("pending_actions"):
            # Only mark completed if there are no more actions left in the queue
            workflow.status = "completed"
            self._log_audit(task_id, "workflow.tool_executed", {
                "result": result.get("execution_result"),
                "pending": len(result.get("pending_actions", []))
            })
        elif decision == "rejected":
            workflow.status = "rejected"

        await self.session.commit()

        return {
            "workflow_id": str(workflow.id),
            "status": workflow.status,
            "execution_result": result.get("execution_result", "No result."),
            "action_id_approved": action_id
        }