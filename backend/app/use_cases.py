"""
Use-case registry.

Single source of truth for the EACIP use cases currently supported.

WHY THIS EXISTS:
    The 5 use cases are NOT part of the engine's contract — they are
    configuration. Keeping them here (not in the prompt, not in the
    schema) means:
      - Prompt text can stay generic.
      - A future real LLM integration receives them via system_prompt.
      - Stage 12 can replace this module with a YAML-driven loader
        without touching prompts, services, or schemas.

SCOPE (Stage 4.3):
    Only identifiers + short labels for prompt injection.
    No sources, requirements, rules, workflows — those come later.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class UseCase:
    """A registered EACIP use case."""

    id: str
    """Machine identifier, e.g., 'supplier_qualification'."""

    label: str
    """Human-readable label for prompts and UI."""


# ---------------------------------------------------------------------
# Registry — currently 5 use cases (locked for the prototype)
# ---------------------------------------------------------------------

USE_CASES: tuple[UseCase, ...] = (
    UseCase(
        id="supplier_qualification",
        label="Supplier Qualification & Onboarding",
    ),
    UseCase(
        id="purchase_delay",
        label="Critical Purchase Delay Resolution",
    ),
    UseCase(
        id="incident_investigation",
        label="Incident Investigation + Remediation",
    ),
    UseCase(
        id="employee_onboarding",
        label="Employee Onboarding",
    ),
    UseCase(
        id="customer_issue",
        label="Customer Issue Resolution",
    ),
)


def get_use_case_ids() -> list[str]:
    """Return the list of valid use-case identifiers."""
    return [uc.id for uc in USE_CASES]


def render_use_case_list() -> str:
    """
    Render the registry as a bullet list for the LLM prompt.

    Output example:
        * supplier_qualification — Supplier Qualification & Onboarding
        * purchase_delay — Critical Purchase Delay Resolution
        ...
    """
    lines = [f"  * {uc.id} — {uc.label}" for uc in USE_CASES]
    return "\n".join(lines)