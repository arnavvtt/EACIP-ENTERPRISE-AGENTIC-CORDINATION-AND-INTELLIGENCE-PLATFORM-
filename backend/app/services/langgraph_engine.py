"""
LangGraph True Agentic Engine with Human-in-the-Loop (HITL).
"""

from typing import TypedDict, List, Dict, Any
import uuid
import json
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.llm import get_llm_provider
from app.services.agent_models import LLMDecisionOutput, ProposedAction

# ------------------------------------------------------------------
# 1. Define State
# ------------------------------------------------------------------
class AgentState(TypedDict):
    task_id: str
    gaps: List[dict]
    inconsistencies: List[dict]
    proposed_action: dict  # Stored as dict for JSON serialization
    human_decision: str    # "approved" | "rejected" | "modified"
    execution_result: str

# ------------------------------------------------------------------
# 2. Nodes
# ------------------------------------------------------------------
async def planner_node(state: AgentState):
    print("--- PLANNER AGENT THINKING ---")
    gaps = state.get("gaps", [])
    inconsistencies = state.get("inconsistencies", [])

    if not gaps and not inconsistencies:
        return {"proposed_action": None, "execution_result": "No gaps found."}

    context = f"Gaps: {json.dumps(gaps)}\nInconsistencies: {json.dumps(inconsistencies)}"
    
    system_prompt = """
    You are an AI Planner for EACIP. Analyze the gaps and choose exactly ONE tool:
    1. 'send_email' (for missing documents/data)
    2. 'assign_task' (for internal missing processes)
    3. 'update_database' (for data conflicts/inconsistencies)
    
    Return a valid JSON matching the schema.
    If you are using 'send_email', you MUST provide recipient, subject, and body.
    If you are using 'assign_task', you MUST provide role and description.
    If you are using 'update_database', you MUST provide field and new_value.
    Set unused parameters to null.
    """
    
    llm = get_llm_provider()
    
    try:
        response, meta = await llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=context,
            response_schema=LLMDecisionOutput
        )
        
        # BACKEND generates the action_id
        proposed_action = ProposedAction(
            action_id=uuid.uuid4(),
            action=response
        )
        
        return {"proposed_action": proposed_action.model_dump(mode="json")}
        
    except Exception as e:
        print(f"LLM Planning Failed: {e}")
        return {"proposed_action": None, "execution_result": f"Failed to plan: {str(e)}"}

async def human_interrupt_node(state: AgentState):
    print("--- WAITING FOR HUMAN APPROVAL ---")
    proposed_action = state.get("proposed_action")
    
    if not proposed_action:
        return {"human_decision": "aborted"}

    human_input = interrupt({
        "message": "Human approval required for proposed action.",
        "action_data": proposed_action
    })
    
    return {"human_decision": human_input}

async def executor_node(state: AgentState):
    print("--- EXECUTOR AGENT: RUNNING TOOL ---")
    proposed_action = state.get("proposed_action")
    decision = state.get("human_decision")
    
    if decision != "approved" or not proposed_action:
        return {"execution_result": "Action was not approved."}

    # Flat schema extraction
    action_data = proposed_action.get("action", {})
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

    return {"execution_result": result}

# ------------------------------------------------------------------
# 3. Routing
# ------------------------------------------------------------------
def route_human_decision(state: AgentState):
    decision = state.get("human_decision")
    if decision == "approved":
        return "executor"
    elif decision == "modified":
        return "planner"
    else:
        return "end"

# ------------------------------------------------------------------
# 4. Build Graph
# ------------------------------------------------------------------
def build_agent_graph(checkpointer: AsyncPostgresSaver):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("human_approval", human_interrupt_node)
    workflow.add_node("executor", executor_node)
    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "human_approval")
    
    workflow.add_conditional_edges(
        "human_approval",
        route_human_decision,
        {
            "executor": "executor",
            "planner": "planner",
            "end": END
        }
    )
    
    workflow.add_edge("executor", END)
    
    return workflow.compile(checkpointer=checkpointer)