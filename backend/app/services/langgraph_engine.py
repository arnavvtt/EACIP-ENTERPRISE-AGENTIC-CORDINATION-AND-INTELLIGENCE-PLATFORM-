"""
LangGraph Multi-Agent Orchestration Engine (Fixed).
"""
from typing import TypedDict, List, Dict, Any
import uuid
import json
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.llm import get_llm_provider
from app.services.agent_models import (
    LLMDecisionOutput, 
    ProposedAction, 
    CoordinatorPlan
)

class AgentState(TypedDict):
    task_id: str
    gaps: List[dict]
    inconsistencies: List[dict]
    modified_data: dict | None
    
    subtasks: List[dict]
    current_subtask_index: int
    agent_outputs: List[dict]
    
    pending_actions: List[dict]
    approved_action_id: str | None  # NEW
    human_decision: str
    execution_result: str

# ------------------------------------------------------------------
# Nodes
# ------------------------------------------------------------------
async def coordinator_node(state: AgentState):
    print("--- COORDINATOR AGENT THINKING ---")
    gaps = state.get("gaps", [])
    inconsistencies = state.get("inconsistencies", [])
    modified_data = state.get("modified_data")

    if not gaps and not inconsistencies:
        return {"subtasks": [], "execution_result": "No gaps found."}

    context = f"Gaps: {json.dumps(gaps)}\nInconsistencies: {json.dumps(inconsistencies)}"
    if modified_data:
        context += f"\nHuman requested modifications: {json.dumps(modified_data)}"

    system_prompt = """
    You are the Coordinator Agent for EACIP. Analyze the gaps and inconsistencies.
    Decompose them into a list of subtasks.
    Valid subtask types:
    - 'info_request' (for missing documents, missing data)
    - 'exception_handling' (for data conflicts, inconsistencies)
    Return a valid JSON matching the schema. If no work is needed, return an empty list.
    """
    
    llm = get_llm_provider()
    try:
        response, meta = await llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=context,
            response_schema=CoordinatorPlan
        )
        
        if not response.subtasks:
            return {"subtasks": [], "execution_result": "Coordinator found no actionable subtasks."}
            
        return {
            "subtasks": [t.model_dump() for t in response.subtasks],
            "current_subtask_index": 0,
            "agent_outputs": [],
            "pending_actions": [],
            "modified_data": None
        }
    except Exception as e:
        print(f"Coordinator Planning Failed: {e}")
        return {"subtasks": [], "execution_result": f"Coordinator failed: {str(e)}"}

def route_subtasks(state: AgentState):
    subtasks = state.get("subtasks", [])
    idx = state.get("current_subtask_index", 0)
    
    if not subtasks:
        return "end"
    if idx >= len(subtasks):
        return "consolidate"
    
    current_task = subtasks[idx]
    if current_task["type"] == "info_request":
        return "info_agent"
    elif current_task["type"] == "exception_handling":
        return "exception_agent"
    return "consolidate"

async def info_agent_node(state: AgentState):
    print("--- INFO REQUEST AGENT ---")
    idx = state.get("current_subtask_index", 0)
    subtask = state["subtasks"][idx]
    
    llm = get_llm_provider()
    system_prompt = "You are the Information Request Agent. Propose an action (send_email or assign_task) to resolve this subtask."
    
    user_prompt = f"""
    Original Gaps: {json.dumps(state.get('gaps', []))}
    Original Inconsistencies: {json.dumps(state.get('inconsistencies', []))}
    Your Assigned Subtask: {json.dumps(subtask)}
    """
    
    try:
        response, meta = await llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=LLMDecisionOutput
        )
        output = {
            "status": "success", 
            "agent": "Information Agent", 
            "subtask": subtask, 
            "action": response.model_dump()
        }
    except Exception as e:
        print(f"Info Agent failed: {e}")
        output = {
            "status": "failed", 
            "agent": "Information Agent", 
            "subtask": subtask, 
            "error": str(e)
        }
        
    new_outputs = list(state.get("agent_outputs", []))
    new_outputs.append(output)
    return {"agent_outputs": new_outputs, "current_subtask_index": idx + 1}

async def exception_agent_node(state: AgentState):
    print("--- EXCEPTION HANDLING AGENT ---")
    idx = state.get("current_subtask_index", 0)
    subtask = state["subtasks"][idx]
    
    llm = get_llm_provider()
    system_prompt = "You are the Exception Handling Agent. Investigate the conflict and propose an action."
    
    user_prompt = f"""
    Original Gaps: {json.dumps(state.get('gaps', []))}
    Original Inconsistencies: {json.dumps(state.get('inconsistencies', []))}
    Your Assigned Subtask: {json.dumps(subtask)}
    """
    
    try:
        response, meta = await llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=LLMDecisionOutput
        )
        output = {
            "status": "success", 
            "agent": "Exception Agent", 
            "subtask": subtask, 
            "action": response.model_dump()
        }
    except Exception as e:
        print(f"Exception Agent failed: {e}")
        output = {
            "status": "failed", 
            "agent": "Exception Agent", 
            "subtask": subtask, 
            "error": str(e)
        }
        
    new_outputs = list(state.get("agent_outputs", []))
    new_outputs.append(output)
    return {"agent_outputs": new_outputs, "current_subtask_index": idx + 1}

async def consolidation_node(state: AgentState):
    print("--- COORDINATOR CONSOLIDATING ---")
    agent_outputs = state.get("agent_outputs", [])
    pending = []
    
    for out in agent_outputs:
        if out["status"] == "success":
            proposed_action = ProposedAction(
                action_id=uuid.uuid4(),
                action=LLMDecisionOutput(**out["action"]),
                agent_source=out["agent"],
                subtask_id=out["subtask"]["id"]
            )
            pending.append(proposed_action.model_dump(mode="json"))
            
    if not pending:
        return {"pending_actions": [], "execution_result": "All subtasks failed or no valid actions generated."}
        
    return {"pending_actions": pending}

async def validate_actions_node(state: AgentState):
    print("--- VALIDATING ACTIONS ---")
    pending = state.get("pending_actions", [])
    valid_actions = []
    
    for p in pending:
        try:
            LLMDecisionOutput.model_validate(p.get("action", {}))
            valid_actions.append(p)
        except Exception as e:
            print(f"Validation failed for action: {e}")
            
    if not valid_actions:
        return {"pending_actions": [], "execution_result": "No valid actions passed schema validation."}
        
    return {"pending_actions": valid_actions}

def route_after_validation(state: AgentState):
    if state.get("pending_actions"):
        return "human_approval"
    return "end"

async def human_interrupt_node(state: AgentState):
    print("--- WAITING FOR HUMAN APPROVAL ---")
    pending = state.get("pending_actions", [])
    
    if not pending:
        return {"human_decision": "aborted"}

    current_action = pending[0]
    
    human_input = interrupt({
        "message": f"Human approval required for proposed action by {current_action.get('agent_source', 'Agent')}.",
        "action_data": current_action
    })
    
    if isinstance(human_input, dict) and human_input.get("decision") == "modified":
        return {
            "human_decision": "modified",
            "modified_data": human_input.get("modified_data"),
            "pending_actions": [] 
        }
    elif human_input == "approved":
        # FIX: Store the approved action ID
        return {
            "human_decision": "approved",
            "approved_action_id": current_action.get("action_id")
        }
    
    return {"human_decision": human_input}

def route_human_decision(state: AgentState):
    decision = state.get("human_decision")
    if decision == "approved":
        return "executor"
    elif decision == "modified":
        return "coordinator"
    else:
        return "end"

async def executor_node(state: AgentState):
    print("--- EXECUTOR AGENT: RUNNING TOOL ---")
    pending = state.get("pending_actions", [])
    decision = state.get("human_decision")
    approved_id = state.get("approved_action_id")
    
    if decision != "approved" or not pending:
        return {"execution_result": "Action was not approved or queue is empty."}

    # FIX: Find the exact action that was approved
    current_action = None
    for a in pending:
        if a.get("action_id") == approved_id:
            current_action = a
            break
    
    if not current_action:
        # Fallback to first if not found (should not happen)
        current_action = pending[0]

    action_data = current_action.get("action", {})
    tool = action_data.get("tool")
    
    if tool == "send_email":
        recipient = action_data.get("recipient")
        subject = action_data.get("subject")
        with open("sent_emails.log", "a") as f:
            f.write(f"To: {recipient}\nSubject: {subject}\n---\n")
        result = f"Mock Email sent to {recipient}"
    elif tool == "assign_task":
        role = action_data.get("role")
        desc = action_data.get("description")
        with open("assigned_tasks.log", "a") as f:
            f.write(f"Role: {role}\nTask: {desc}\n---\n")
        result = f"Mock Task assigned to {role}"
    elif tool == "update_database":
        field = action_data.get("field")
        new_value = action_data.get("new_value")
        with open("db_updates.log", "a") as f:
            f.write(f"Field: {field} = {new_value}\n---\n")
        result = f"Mock Database updated: {field}"
    else:
        result = "Unknown tool."

    # Remove the executed action from the queue
    remaining_pending = [a for a in pending if a.get("action_id") != approved_id]
    
    return {"execution_result": result, "pending_actions": remaining_pending, "approved_action_id": None}

def route_after_execution(state: AgentState):
    if state.get("pending_actions"):
        return "human_approval"
    return "end"

# ------------------------------------------------------------------
# Graph Builder
# ------------------------------------------------------------------
def build_agent_graph(checkpointer: AsyncPostgresSaver):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("info_agent", info_agent_node)
    workflow.add_node("exception_agent", exception_agent_node)
    workflow.add_node("consolidation", consolidation_node)
    workflow.add_node("validate_actions", validate_actions_node)
    workflow.add_node("human_approval", human_interrupt_node)
    workflow.add_node("executor", executor_node)
    
    workflow.set_entry_point("coordinator")
    
    workflow.add_conditional_edges("coordinator", route_subtasks, {"info_agent": "info_agent", "exception_agent": "exception_agent", "consolidate": "consolidation", "end": END})
    workflow.add_conditional_edges("info_agent", route_subtasks, {"info_agent": "info_agent", "exception_agent": "exception_agent", "consolidate": "consolidation", "end": END})
    workflow.add_conditional_edges("exception_agent", route_subtasks, {"info_agent": "info_agent", "exception_agent": "exception_agent", "consolidate": "consolidation", "end": END})
    
    workflow.add_edge("consolidation", "validate_actions")
    workflow.add_conditional_edges("validate_actions", route_after_validation, {"human_approval": "human_approval", "end": END})
    
    workflow.add_conditional_edges("human_approval", route_human_decision, {"executor": "executor", "coordinator": "coordinator", "end": END})
    workflow.add_conditional_edges("executor", route_after_execution, {"human_approval": "human_approval", "end": END})
    
    return workflow.compile(checkpointer=checkpointer)