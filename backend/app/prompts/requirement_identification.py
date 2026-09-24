"""
Prompts for Requirement Identification (Stage 5).

The LLM's role: suggest MAX 5 task-specific requirements beyond the
registry baseline. It must only use valid taxonomy types.

The LLM does NOT produce the final authoritative set. Deterministic
code (requirement_service) validates and merges.
"""

from app.requirement_registry import RegistryRequirement
from app.requirement_taxonomy import REQUIREMENT_TAXONOMY


def build_requirement_system_prompt(
    *,
    allowed_types: tuple[str, ...],
    max_candidates: int,
) -> str:
    """
    Build the system prompt for requirement candidate suggestion.

    Injects:
    - allowed requirement types (same category as use case)
    - max candidate count
    """
    allowed_lines = "\n".join(
        f"  * {t} — {REQUIREMENT_TAXONOMY[t]}"
        for t in allowed_types
        if t in REQUIREMENT_TAXONOMY
    )

    return f"""\
You are the Requirement Identification component of EACIP.

Your job: given a task and its baseline requirements, suggest at most
{max_candidates} ADDITIONAL task-specific requirements that are clearly
justified by the task text.

STRICT RULES:
1. Only use requirement types from the ALLOWED list below.
   Do NOT invent new types.
2. Do NOT duplicate any baseline requirement.
3. Only suggest a requirement if the task text explicitly or strongly
   implies it. Do NOT speculate.
4. Return AT MOST {max_candidates} candidates. Empty list is valid.
5. Every candidate must include:
   - requirement_type (from allowed list)
   - description (why this requirement applies, max 500 chars)
   - is_mandatory (your opinion; system will downgrade to false)
   - rationale (1-2 sentences)
   - confidence (0.0-1.0)
6. Do NOT make business decisions or resolve conflicts.

ALLOWED requirement types:
{allowed_lines}

If nothing genuinely task-specific is needed beyond the baseline,
return an empty candidates list.
"""


def build_requirement_user_prompt(
    *,
    title: str,
    description: str,
    use_case: str,
    intent: str | None,
    entities: list[dict] | None,
    baseline: tuple[RegistryRequirement, ...],
) -> str:
    """
    Build the user prompt with task + baseline context.
    """
    baseline_lines = "\n".join(
        f"  * {r.requirement_type}"
        f"{' (mandatory)' if r.is_mandatory else ''}"
        f" — {r.description}"
        for r in baseline
    )

    entities_text = "None"
    if entities:
        entities_text = ", ".join(
            f"{e.get('type', '?')}={e.get('value', '?')}"
            for e in entities
        )

    return f"""\
TASK TITLE:
{title.strip()}

TASK DESCRIPTION:
{description.strip()}

USE CASE: {use_case}
INTENT: {intent or "(unknown)"}
ENTITIES: {entities_text}

BASELINE REQUIREMENTS (already handled — do NOT duplicate):
{baseline_lines}

Suggest additional task-specific requirements (max 5) that the task
clearly implies beyond the baseline. If none, return an empty list.
"""