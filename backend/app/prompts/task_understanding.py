"""
Prompts for the Task Understanding stage.

The system prompt sets the LLM's role and rules.
The user prompt is built from the actual task.

DESIGN:
    The list of valid use cases is NOT hardcoded here.
    It is injected at runtime from app.use_cases (the registry).
    Stage 12 will replace that registry with a YAML-driven loader,
    so this file stays unchanged.
"""

from app.use_cases import render_use_case_list


# ---------------------------------------------------------------------
# System prompt (built dynamically from the registry)
# ---------------------------------------------------------------------

def build_task_understanding_system_prompt() -> str:
    """
    Build the system prompt, injecting valid use cases at runtime.

    Called per request. Cheap to build; keeps the prompt aligned with
    whatever the registry currently contains.
    """
    use_case_block = render_use_case_list()
    return f"""\
You are the Task Understanding component of EACIP, an enterprise
operational coordination platform.

Your job: read an operational task and produce a structured
interpretation.

Extract:
- intent: a short verb describing the goal
  (e.g., "qualify", "resolve", "investigate", "onboard", "review", "verify").
- use_case: the best-fit EACIP use case, or null if none apply.
  Valid use-case identifiers (from the current registry):
{use_case_block}
- summary: one sentence describing what the user wants.
- entities: identifiers or names extracted from the task
  (e.g., supplier names, order IDs, employee IDs).
- confidence: how confident you are (0.0 to 1.0).
- rationale: 1-2 sentences explaining your choice. Not a step-by-step
  thinking process.

Rules:
- Always return valid JSON matching the requested schema.
- Do NOT invent values not present in the task.
- If the use_case is unclear, set it to null.
- Do NOT resolve inconsistencies or make business decisions.
"""


# ---------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------

def build_task_understanding_user_prompt(
    *,
    title: str,
    description: str,
    use_case_hint: str | None = None,
) -> str:
    """
    Build the user prompt from a task.

    Args:
        title: Task title (short).
        description: Full task description.
        use_case_hint: Optional user-provided use case (treated as a hint).
    """
    parts = [
        "TASK TITLE:",
        title.strip(),
        "",
        "TASK DESCRIPTION:",
        description.strip(),
    ]
    if use_case_hint:
        parts.extend([
            "",
            "USER-PROVIDED USE CASE HINT (may be wrong; verify):",
            use_case_hint,
        ])
    return "\n".join(parts)