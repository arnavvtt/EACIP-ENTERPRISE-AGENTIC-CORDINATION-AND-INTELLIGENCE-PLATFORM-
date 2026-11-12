"""
Agentic Workflow Service (Stage 13.3).
Integrates LangGraph with database and API.
"""

from typing import Any
from uuid import UUID
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.types import Command

from app.models.workflow import Workflow
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

    async def initiate_workflow(self, task_id: UUID) -> dict[str, Any]:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise AgenticWorkflowError("Task not found.")

        pkg = await self.pkg_repo.get_latest_for_task(task_id)
        if not pkg or pkg.status != "approved":
            raise AgenticWorkflowError("Package must be approved to start Phase 2.")

        workflow = Workflow(
            task_id=task_id,
            package_id=pkg.id,
            template_name="langgraph_multi_tool",
            status="active",
            description="Agentic Workflow"
        )
        self.session.add(workflow)
        await self.session.commit()
        await self.session.refresh(workflow)

        checkpointer = await get_langgraph_checkpointer()
        graph = build_agent_graph(checkpointer)
        
        initial_state = {
            "task_id": str(task_id),
            "gaps": pkg.sections.get("section_7_information_gaps", []),
            "inconsistencies": pkg.sections.get("section_8_potential_inconsistencies", []),
            "proposed_action": {},
            "human_decision": "",
            "execution_result": ""
        }

        config = {"configurable": {"thread_id": str(workflow.id)}}
        result = await graph.ainvoke(initial_state, config)

        # LangGraph interrupt structure
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            return {
                "workflow_id": str(workflow.id),
                "status": "waiting_for_approval",
                "message": "Agent is waiting for human approval.",
                "proposed_action": interrupt_data.get("action_data")
            }
        else:
            workflow.status = "completed"
            await self.session.commit()
            return {
                "workflow_id": str(workflow.id),
                "status": "completed",
                "message": result.get("execution_result", "Workflow completed."),
                "proposed_action": None
            }

    async def resume_workflow(
        self, 
        task_id: UUID, 
        workflow_id: UUID, 
        decision: str, 
        action_id: str
    ) -> dict[str, Any]:
        
        stmt = select(Workflow).where(Workflow.id == workflow_id, Workflow.task_id == task_id)
        workflow = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if not workflow:
            raise AgenticWorkflowError("Workflow not found.")
            
        if workflow.status != "active":
            raise AgenticWorkflowError(f"Workflow is already {workflow.status}.")

        checkpointer = await get_langgraph_checkpointer()
        graph = build_agent_graph(checkpointer)
        
        config = {"configurable": {"thread_id": str(workflow.id)}}
        
        result = await graph.ainvoke(Command(resume=decision), config)

        workflow.status = "completed" if decision == "approved" else "rejected"
        await self.session.commit()

        return {
            "workflow_id": str(workflow.id),
            "status": workflow.status,
            "execution_result": result.get("execution_result", "No result."),
            "action_id_approved": action_id
        }