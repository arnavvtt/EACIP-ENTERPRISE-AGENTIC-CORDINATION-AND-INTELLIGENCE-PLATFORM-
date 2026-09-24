"""
Requirement registry — baseline requirements per EACIP use case.

AUTHORITATIVE SOURCE for what each use case requires.

The engine reads this registry to obtain baseline requirements.
The LLM may SUGGEST additional task-specific requirements, but
those are candidates only — the registry remains authoritative.

DO NOT hardcode supplier-specific (or any use-case-specific) logic
into engine code. Everything use-case-specific lives HERE.

Stage 12 note:
    This module will be replaced by a YAML-driven loader. The
    dataclass shape should remain compatible.
"""

from dataclasses import dataclass

from app.requirement_taxonomy import (
    CATEGORY_CUSTOMER,
    CATEGORY_HR,
    CATEGORY_INCIDENT,
    CATEGORY_PROCUREMENT,
    CATEGORY_SUPPLIER,
)


@dataclass(frozen=True)
class RegistryRequirement:
    """A single baseline requirement defined in the registry."""

    requirement_type: str
    description: str
    is_mandatory: bool
    source_hint: str | None
    priority: int  # 1 = highest


@dataclass(frozen=True)
class UseCaseRequirements:
    """All baseline requirements for one use case."""

    use_case: str
    category: str  # used by validator for cross-domain rejection
    requirements: tuple[RegistryRequirement, ...]


# ---------------------------------------------------------------------
# Registry (5 use cases, 29 baseline requirements total)
# ---------------------------------------------------------------------

REQUIREMENT_REGISTRY: dict[str, UseCaseRequirements] = {
    # ---------------------------------------------------------------
    # 1. Supplier Qualification & Onboarding
    # ---------------------------------------------------------------
    "supplier_qualification": UseCaseRequirements(
        use_case="supplier_qualification",
        category=CATEGORY_SUPPLIER,
        requirements=(
            RegistryRequirement(
                requirement_type="financial_info",
                description="Financial stability, revenue, credit rating",
                is_mandatory=True,
                source_hint="supplier-db",
                priority=1,
            ),
            RegistryRequirement(
                requirement_type="compliance_certification",
                description="GST, ISO, regulatory certifications",
                is_mandatory=True,
                source_hint="document-repo",
                priority=2,
            ),
            RegistryRequirement(
                requirement_type="quality_history",
                description="Past quality incidents and audit results",
                is_mandatory=True,
                source_hint="quality-system",
                priority=3,
            ),
            RegistryRequirement(
                requirement_type="esg_evidence",
                description="Environmental, Social, Governance documentation",
                is_mandatory=True,
                source_hint="document-repo",
                priority=4,
            ),
            RegistryRequirement(
                requirement_type="delivery_performance",
                description="Historical on-time delivery metrics",
                is_mandatory=False,
                source_hint="procurement-db",
                priority=5,
            ),
        ),
    ),

    # ---------------------------------------------------------------
    # 2. Critical Purchase Delay Resolution
    # ---------------------------------------------------------------
    "purchase_delay": UseCaseRequirements(
        use_case="purchase_delay",
        category=CATEGORY_PROCUREMENT,
        requirements=(
            RegistryRequirement(
                requirement_type="purchase_order_details",
                description="PO number, quantity, agreed delivery date",
                is_mandatory=True,
                source_hint="procurement-db",
                priority=1,
            ),
            RegistryRequirement(
                requirement_type="delivery_status",
                description="Current shipment / delivery status",
                is_mandatory=True,
                source_hint="procurement-db",
                priority=2,
            ),
            RegistryRequirement(
                requirement_type="supplier_commitment",
                description="Latest supplier communication on ETA",
                is_mandatory=True,
                source_hint="comms-archive",
                priority=3,
            ),
            RegistryRequirement(
                requirement_type="production_impact",
                description="Effect on downstream production lines",
                is_mandatory=True,
                source_hint="production-schedule",
                priority=4,
            ),
            RegistryRequirement(
                requirement_type="inventory_levels",
                description="Current stock of affected material",
                is_mandatory=False,
                source_hint="inventory-db",
                priority=5,
            ),
            RegistryRequirement(
                requirement_type="alternative_suppliers",
                description="Backup suppliers for this material",
                is_mandatory=False,
                source_hint="supplier-db",
                priority=6,
            ),
        ),
    ),

    # ---------------------------------------------------------------
    # 3. Incident Investigation + Remediation
    # ---------------------------------------------------------------
    "incident_investigation": UseCaseRequirements(
        use_case="incident_investigation",
        category=CATEGORY_INCIDENT,
        requirements=(
            RegistryRequirement(
                requirement_type="incident_record",
                description="Incident ID, timestamp, severity",
                is_mandatory=True,
                source_hint="incident-db",
                priority=1,
            ),
            RegistryRequirement(
                requirement_type="system_logs",
                description="Application and system logs around incident window",
                is_mandatory=True,
                source_hint="logs-store",
                priority=2,
            ),
            RegistryRequirement(
                requirement_type="deployment_history",
                description="Recent deployments preceding the incident",
                is_mandatory=True,
                source_hint="deployment-db",
                priority=3,
            ),
            RegistryRequirement(
                requirement_type="service_dependencies",
                description="Upstream/downstream service map",
                is_mandatory=True,
                source_hint="service-catalog",
                priority=4,
            ),
            RegistryRequirement(
                requirement_type="previous_incidents",
                description="Similar incidents in the past",
                is_mandatory=False,
                source_hint="incident-db",
                priority=5,
            ),
            RegistryRequirement(
                requirement_type="runbook_references",
                description="Relevant runbooks / SOPs",
                is_mandatory=False,
                source_hint="document-repo",
                priority=6,
            ),
        ),
    ),

    # ---------------------------------------------------------------
    # 4. Employee Onboarding
    # ---------------------------------------------------------------
    "employee_onboarding": UseCaseRequirements(
        use_case="employee_onboarding",
        category=CATEGORY_HR,
        requirements=(
            RegistryRequirement(
                requirement_type="employee_documents",
                description="Offer letter, resume, signed agreements",
                is_mandatory=True,
                source_hint="hr-db",
                priority=1,
            ),
            RegistryRequirement(
                requirement_type="identity_verification",
                description="ID proof, address proof",
                is_mandatory=True,
                source_hint="hr-db",
                priority=2,
            ),
            RegistryRequirement(
                requirement_type="manager_info",
                description="Reporting manager and their department",
                is_mandatory=True,
                source_hint="hr-db",
                priority=3,
            ),
            RegistryRequirement(
                requirement_type="department_info",
                description="Department, role, location",
                is_mandatory=True,
                source_hint="hr-db",
                priority=4,
            ),
            RegistryRequirement(
                requirement_type="access_requirements",
                description="Systems, tools, and permissions needed",
                is_mandatory=True,
                source_hint="access-system",
                priority=5,
            ),
            RegistryRequirement(
                requirement_type="training_plan",
                description="Recommended onboarding training modules",
                is_mandatory=False,
                source_hint="document-repo",
                priority=6,
            ),
        ),
    ),

    # ---------------------------------------------------------------
    # 5. Customer Issue Resolution
    # ---------------------------------------------------------------
    "customer_issue": UseCaseRequirements(
        use_case="customer_issue",
        category=CATEGORY_CUSTOMER,
        requirements=(
            RegistryRequirement(
                requirement_type="customer_history",
                description="Customer profile, tier, previous interactions",
                is_mandatory=True,
                source_hint="crm-db",
                priority=1,
            ),
            RegistryRequirement(
                requirement_type="order_details",
                description="Order ID, items, delivery date",
                is_mandatory=True,
                source_hint="orders-db",
                priority=2,
            ),
            RegistryRequirement(
                requirement_type="support_tickets",
                description="Related support tickets and their status",
                is_mandatory=True,
                source_hint="tickets-db",
                priority=3,
            ),
            RegistryRequirement(
                requirement_type="communication_history",
                description="Emails / chats with the customer",
                is_mandatory=True,
                source_hint="comms-archive",
                priority=4,
            ),
            RegistryRequirement(
                requirement_type="transaction_records",
                description="Payment / refund transactions",
                is_mandatory=False,
                source_hint="orders-db",
                priority=5,
            ),
            RegistryRequirement(
                requirement_type="relevant_policies",
                description="Return / refund / SLA policies",
                is_mandatory=False,
                source_hint="document-repo",
                priority=6,
            ),
        ),
    ),
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def get_baseline(use_case: str) -> UseCaseRequirements | None:
    """Return the registry entry for a use case, or None."""
    return REQUIREMENT_REGISTRY.get(use_case)


def get_allowed_types_for_use_case(use_case: str) -> tuple[str, ...]:
    """
    Return the tuple of types ALLOWED for this use case.

    This is broader than the baseline (LLM may suggest additional
    types from the same category).
    """
    from app.requirement_taxonomy import get_allowed_types_for_category

    entry = REQUIREMENT_REGISTRY.get(use_case)
    if entry is None:
        return ()
    return get_allowed_types_for_category(entry.category)