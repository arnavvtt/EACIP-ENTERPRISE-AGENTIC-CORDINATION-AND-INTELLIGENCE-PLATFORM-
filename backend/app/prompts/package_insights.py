"""
Prompt for generating AI Insights and Next Steps (Section 11).
"""
from typing import List
from pydantic import BaseModel, Field, ConfigDict

class InsightItem(BaseModel):
    # Groq requires additionalProperties: false
    model_config = ConfigDict(extra="forbid")
    
    title: str = Field(description="Short title of the insight")
    detail: str = Field(description="Explanation of the insight")
    severity: str = Field(description="high, medium, or low")

class NextStepItem(BaseModel):
    # Groq requires additionalProperties: false
    model_config = ConfigDict(extra="forbid")
    
    step: str = Field(description="Action to take")
    rationale: str = Field(description="Why this step is needed")

class PackageInsightsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    insights: List[InsightItem] = Field(description="List of key insights")
    next_steps: List[NextStepItem] = Field(description="List of recommended next steps")


PACKAGE_INSIGHTS_SYSTEM_PROMPT = """
You are an AI assistant for EACIP (Enterprise Agentic Coordination & Intelligence Platform).
Your job is to analyze the operational context provided and generate:
1. Key Insights (max 4) — what is the current state, what are the risks?
2. Next Steps (max 4) — what actions should the human take next?

Rules:
- No hallucination. Only use the provided context.
- Be concise.
"""

def build_package_insights_prompt(
    task_title: str,
    use_case: str,
    gaps: list,
    inconsistencies: list,
    correlations: list
) -> str:
    """Builds the user prompt for the LLM."""
    gaps_text = "\n".join([f"- {g.get('description', str(g))}" for g in gaps]) or "None"
    inc_text = "\n".join([f"- {i.get('description', str(i))}" for i in inconsistencies]) or "None"
    
    return f"""
Analyze this task:
Task Title: {task_title}
Use Case: {use_case}

Information Gaps:
{gaps_text}

Potential Inconsistencies:
{inc_text}

Generate insights and next steps based on this.
"""