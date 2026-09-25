"""
Validation rules and configuration.

All validation-specific config lives here. Keeps the service logic
generic across the 5 EACIP use cases.

Sections:
    COMPARABLE_FIELDS       approved fields for inconsistency detection
    GAP_SEVERITY            severity for missing-requirement gaps
    INCONSISTENCY_SEVERITY  severity for inconsistencies
"""

# ---------------------------------------------------------------------
# Comparable fields — ONLY these are compared across correlated records
# ---------------------------------------------------------------------
# Rule: a field is compared only if present in both records.
# supplier_id is intentionally excluded (it is the anchor key, not an
# attribute to compare).

COMPARABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "supplier":    ("supplier_name", "gstin", "registered_city", "country"),
    "certificate": ("supplier_name", "gstin", "registered_city", "country"),
    # Future record types can be added here.
}


# ---------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------

GAP_SEVERITY_MANDATORY = "high"
GAP_SEVERITY_OPTIONAL = "low"
INCONSISTENCY_SEVERITY = "medium"