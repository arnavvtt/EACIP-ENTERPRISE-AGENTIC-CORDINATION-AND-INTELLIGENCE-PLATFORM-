"""
Correlation rules and configuration.

All correlation-specific configuration lives here. Keeps the engine
logic generic across the 5 EACIP use cases.
"""

# ---------------------------------------------------------------------
# Anchor preference — deterministic ordered list of preferred entity types
# ---------------------------------------------------------------------

ANCHOR_PREFERENCE: dict[str, tuple[str, ...]] = {
    "supplier_qualification": ("supplier_id", "supplier_name", "supplier"),
    "purchase_delay":         ("po_number", "purchase_order_id", "purchase_order"),
    "incident_investigation": ("incident_id", "incident"),
    "employee_onboarding":    ("employee_id", "employee"),
    "customer_issue":         ("customer_id", "order_id", "customer"),
}


# ---------------------------------------------------------------------
# Anchor resolution — approved fields used to find the anchor record
# ---------------------------------------------------------------------
# NOTE: LLMs often return generic entity types like "supplier" (not
# "supplier_id" or "supplier_name"). Each generic type maps to the
# canonical field(s) to search in the record data.

ANCHOR_RESOLUTION_FIELDS: dict[str, tuple[str, ...]] = {
    # ID-style
    "supplier_id":   ("external_id", "supplier_id"),
    "po_number":     ("external_id", "po_number"),
    "incident_id":   ("external_id", "incident_id"),
    "employee_id":   ("external_id", "employee_id"),
    "customer_id":   ("external_id", "customer_id"),
    "order_id":      ("external_id", "order_id"),

    # Name-style
    "supplier_name": ("supplier_name",),

    # Generic (what LLMs usually extract)
    "supplier":      ("supplier_name",),
    "purchase_order": ("external_id", "po_number"),
    "incident":      ("external_id", "incident_id"),
    "employee":      ("external_id", "employee_id"),
    "customer":      ("external_id", "customer_id"),
}


# ---------------------------------------------------------------------
# Correlatable fields — ONLY these may create correlations
# ---------------------------------------------------------------------

CORRELATABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "supplier":         ("supplier_id", "supplier_name", "gstin"),
    "purchase_order":   ("po_number", "supplier_id"),
    "quality_incident": ("incident_id", "supplier_id"),
    "certificate":      ("supplier_id", "gstin"),
    "policy":           (),
    "email":            ("supplier_id",),
}


# ---------------------------------------------------------------------
# Relationship types — record_type pair -> relationship name
# ---------------------------------------------------------------------

RELATIONSHIP_TYPES: dict[frozenset, str] = {
    frozenset({"supplier", "purchase_order"}):   "supplier_has_purchase_order",
    frozenset({"supplier", "quality_incident"}): "supplier_has_quality_incident",
    frozenset({"supplier", "certificate"}):      "supplier_has_certificate",
    frozenset({"supplier", "email"}):            "supplier_has_communication",
    frozenset({"purchase_order", "quality_incident"}):
        "purchase_order_has_quality_incident",
    frozenset({"purchase_order", "email"}): "purchase_order_has_communication",
}


def resolve_relationship_type(a_type: str, b_type: str) -> str:
    """Return relationship name; generic fallback if not mapped."""
    key = frozenset({a_type, b_type})
    if key in RELATIONSHIP_TYPES:
        return RELATIONSHIP_TYPES[key]
    a, b = sorted([a_type, b_type])
    return f"{a}_related_to_{b}"


# ---------------------------------------------------------------------
# Confidence — HEURISTIC STRENGTH SCORES (not calibrated probabilities)
# ---------------------------------------------------------------------

CONFIDENCE: dict[str, float] = {
    "exact_id":     0.95,
    "business_key": 0.85,
}

BASIS_PRIORITY: tuple[str, ...] = ("exact_id", "business_key")