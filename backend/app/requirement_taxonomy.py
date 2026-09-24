"""
Global requirement taxonomy.

Single source of truth for VALID requirement_type values across EACIP.

The LLM may only suggest requirement_type values present in this
taxonomy. Any suggestion outside this set is REJECTED by the
deterministic validator (not silently accepted).

WHY THIS EXISTS:
    Prevents LLM from inventing arbitrary identifiers such as
    "supplier_has_magic_powers". Keeps the requirement space bounded
    and evaluation-friendly.

CATEGORIES (31 types):
    - supplier      (7)
    - procurement   (6)
    - incident      (6)
    - hr            (6)
    - customer      (6)

Stage 12 note:
    The registry + taxonomy will be replaced by YAML-driven config.
    The validator logic remains unchanged.
"""

# ---------------------------------------------------------------------
# Category constants (used by the registry + validator)
# ---------------------------------------------------------------------

CATEGORY_SUPPLIER = "supplier"
CATEGORY_PROCUREMENT = "procurement"
CATEGORY_INCIDENT = "incident"
CATEGORY_HR = "hr"
CATEGORY_CUSTOMER = "customer"


# ---------------------------------------------------------------------
# The 31 valid requirement types, grouped by category
# ---------------------------------------------------------------------

REQUIREMENT_TAXONOMY: dict[str, str] = {
    # --- Supplier (7) ---
    "financial_info": "Financial Information",
    "compliance_certification": "Compliance Certifications",
    "quality_history": "Quality History",
    "esg_evidence": "ESG Evidence",
    "delivery_performance": "Delivery Performance",
    "risk_assessment": "Risk Assessment",
    "contract_info": "Contract Information",

    # --- Procurement (6) ---
    "purchase_order_details": "Purchase Order Details",
    "delivery_status": "Delivery Status",
    "supplier_commitment": "Supplier Commitment",
    "inventory_levels": "Inventory Levels",
    "production_impact": "Production Impact",
    "alternative_suppliers": "Alternative Suppliers",

    # --- Incident (6) ---
    "incident_record": "Incident Record",
    "system_logs": "System Logs",
    "deployment_history": "Deployment History",
    "service_dependencies": "Service Dependencies",
    "previous_incidents": "Previous Incidents",
    "runbook_references": "Runbook References",

    # --- HR (6) ---
    "employee_documents": "Employee Documents",
    "identity_verification": "Identity Verification",
    "manager_info": "Manager Information",
    "department_info": "Department Information",
    "access_requirements": "Access Requirements",
    "training_plan": "Training Plan",

    # --- Customer (6) ---
    "customer_history": "Customer History",
    "order_details": "Order Details",
    "transaction_records": "Transaction Records",
    "support_tickets": "Support Tickets",
    "communication_history": "Communication History",
    "relevant_policies": "Relevant Policies",
}


# ---------------------------------------------------------------------
# Category groupings (used by validator rule 5 — cross-domain rejection)
# ---------------------------------------------------------------------

CATEGORY_TYPES: dict[str, tuple[str, ...]] = {
    CATEGORY_SUPPLIER: (
        "financial_info",
        "compliance_certification",
        "quality_history",
        "esg_evidence",
        "delivery_performance",
        "risk_assessment",
        "contract_info",
    ),
    CATEGORY_PROCUREMENT: (
        "purchase_order_details",
        "delivery_status",
        "supplier_commitment",
        "inventory_levels",
        "production_impact",
        "alternative_suppliers",
    ),
    CATEGORY_INCIDENT: (
        "incident_record",
        "system_logs",
        "deployment_history",
        "service_dependencies",
        "previous_incidents",
        "runbook_references",
    ),
    CATEGORY_HR: (
        "employee_documents",
        "identity_verification",
        "manager_info",
        "department_info",
        "access_requirements",
        "training_plan",
    ),
    CATEGORY_CUSTOMER: (
        "customer_history",
        "order_details",
        "transaction_records",
        "support_tickets",
        "communication_history",
        "relevant_policies",
    ),
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def is_valid_type(requirement_type: str) -> bool:
    """Return True if the requirement_type is in the taxonomy."""
    return requirement_type in REQUIREMENT_TAXONOMY


def get_allowed_types_for_category(category: str) -> tuple[str, ...]:
    """Return the tuple of valid types for a given category."""
    return CATEGORY_TYPES.get(category, ())


def taxonomy_summary() -> dict[str, int]:
    """Return a per-category count (useful for tests/debugging)."""
    return {cat: len(types) for cat, types in CATEGORY_TYPES.items()}   
# ---------------------------------------------------------------------
# Default source hints per requirement type (deterministic routing)
# ---------------------------------------------------------------------
# WHY:
#   The LLM must NOT choose sources (unreliable). When the LLM suggests
#   a new requirement type, the system assigns its source using this
#   deterministic mapping. Stage 6 (Retrieval) uses this hint.
#
# Invariant (verified by test):
#   set(DEFAULT_SOURCE_HINT) == set(REQUIREMENT_TAXONOMY)

DEFAULT_SOURCE_HINT: dict[str, str] = {
    # Supplier
    "financial_info": "supplier-db",
    "compliance_certification": "document-repo",
    "quality_history": "quality-system",
    "esg_evidence": "document-repo",
    "delivery_performance": "procurement-db",
    "risk_assessment": "document-repo",
    "contract_info": "document-repo",

    # Procurement
    "purchase_order_details": "procurement-db",
    "delivery_status": "procurement-db",
    "supplier_commitment": "comms-archive",
    "inventory_levels": "inventory-db",
    "production_impact": "production-schedule",
    "alternative_suppliers": "supplier-db",

    # Incident
    "incident_record": "incident-db",
    "system_logs": "logs-store",
    "deployment_history": "deployment-db",
    "service_dependencies": "service-catalog",
    "previous_incidents": "incident-db",
    "runbook_references": "document-repo",

    # HR
    "employee_documents": "hr-db",
    "identity_verification": "hr-db",
    "manager_info": "hr-db",
    "department_info": "hr-db",
    "access_requirements": "access-system",
    "training_plan": "document-repo",

    # Customer
    "customer_history": "crm-db",
    "order_details": "orders-db",
    "transaction_records": "orders-db",
    "support_tickets": "tickets-db",
    "communication_history": "comms-archive",
    "relevant_policies": "document-repo",
}


def get_default_source_hint(requirement_type: str) -> str | None:
    """Return the deterministic default source hint for a type."""
    return DEFAULT_SOURCE_HINT.get(requirement_type)