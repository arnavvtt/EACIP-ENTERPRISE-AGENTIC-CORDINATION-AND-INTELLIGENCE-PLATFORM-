"""
Stage 8 correlation engine tests.

Covers: anchor selection, exact-id / business-key basis, secondary
correlations, dedup, self-reference, relationship mapping/fallback,
confidence range, whitelist enforcement, supplier_name anchor
resolution, and secondary-pair anchor-identity exclusion.
"""

from types import SimpleNamespace
from uuid import uuid4

from app.correlation.engine import run_correlation_engine
from app.correlation.rules import resolve_relationship_type
from app.correlation.types import EntityRef


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def rec(external_id: str, record_type: str, data: dict):
    return SimpleNamespace(
        id=uuid4(),
        external_id=external_id,
        record_type=record_type,
        data=data,
    )


def ent(t: str, v: str, c: float = 0.9) -> EntityRef:
    return EntityRef(type=t, value=v, confidence=c)


# ---------------------------------------------------------------------
# 1. Anchor selection by preference
# ---------------------------------------------------------------------

def test_anchor_selection_by_preference():
    records = [
        rec("S-1042", "supplier", {"supplier_id": "S-1042",
                                   "supplier_name": "ABC Components"}),
    ]
    entities = [
        ent("supplier_name", "ABC Components", 0.99),
        ent("supplier_id", "S-1042", 0.50),
    ]
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=entities,
        records=records,
    )
    assert result.anchor is not None
    assert result.anchor.matched_field in ("external_id", "supplier_id")
    assert result.anchor.record_external_id == "S-1042"


# ---------------------------------------------------------------------
# 2. Correlation via exact_id
# ---------------------------------------------------------------------

def test_correlation_via_exact_id():
    s = rec("S-1042", "supplier", {"supplier_id": "S-1042",
                                   "supplier_name": "ABC Components",
                                   "gstin": "GST123"})
    po = rec("PO-4821", "purchase_order", {"po_number": "PO-4821",
                                           "supplier_id": "S-1042"})
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s, po],
    )
    assert len(result.correlations) == 1
    c = result.correlations[0]
    assert c.basis == "exact_id"
    assert c.confidence == 0.95
    assert c.relationship_type == "supplier_has_purchase_order"


# ---------------------------------------------------------------------
# 3. Correlation via business_key
# ---------------------------------------------------------------------

def test_correlation_via_business_key():
    s = rec("S-1042", "supplier", {"supplier_id": "S-1042",
                                   "gstin": "GST123"})
    cert = rec("CERT-1", "certificate", {"gstin": "GST123"})
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s, cert],
    )
    assert len(result.correlations) == 1
    c = result.correlations[0]
    assert c.basis == "business_key"
    assert c.confidence == 0.85


# ---------------------------------------------------------------------
# 4. Secondary correlation — with a NON-anchor shared key
# ---------------------------------------------------------------------

def test_secondary_correlation():
    # Anchor = S-1042. Two certificates share gstin but neither is anchor.
    # gstin is not the anchor's identity, so this secondary correlation
    # IS legitimate.
    s = rec("S-1042", "supplier", {"supplier_id": "S-1042",
                                   "gstin": "GST123"})
    c1 = rec("CERT-1", "certificate", {"gstin": "GST999"})
    c2 = rec("CERT-2", "certificate", {"gstin": "GST999"})
    # Note: gstin="GST999" is deliberately NOT the supplier's gstin.
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s, c1, c2],
    )
    # Expect: anchor->CERT1? No (they don't share any approved field).
    # anchor->CERT2? No.
    # CERT1<->CERT2? Yes (share gstin="GST999").
    assert len(result.correlations) == 1
    c = result.correlations[0]
    assert {c.record_a_id, c.record_b_id} == {c1.id, c2.id}
    assert c.basis == "business_key"


# ---------------------------------------------------------------------
# 5. Duplicate prevention
# ---------------------------------------------------------------------

def test_duplicate_prevention():
    s = rec("S-1042", "supplier", {"supplier_id": "S-1042",
                                   "gstin": "GST123"})
    c1 = rec("CERT-1", "certificate", {"supplier_id": "S-1042",
                                       "gstin": "GST123"})
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s, c1],
    )
    assert len(result.correlations) == 1
    c = result.correlations[0]
    assert "supplier_id" in c.metadata["matched_fields"]
    assert "gstin" in c.metadata["matched_fields"]


# ---------------------------------------------------------------------
# 6. Self-reference prevention
# ---------------------------------------------------------------------

def test_self_reference_prevention():
    s = rec("S-1042", "supplier", {"supplier_id": "S-1042"})
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s],
    )
    assert len(result.correlations) == 0


# ---------------------------------------------------------------------
# 7. Relationship mapping + fallback
# ---------------------------------------------------------------------

def test_relationship_mapping_and_fallback():
    assert resolve_relationship_type("supplier", "purchase_order") \
        == "supplier_has_purchase_order"
    assert resolve_relationship_type("certificate", "email") \
        == "certificate_related_to_email"
    assert resolve_relationship_type("purchase_order", "supplier") \
        == "supplier_has_purchase_order"


# ---------------------------------------------------------------------
# 8. Confidence range
# ---------------------------------------------------------------------

def test_confidence_range():
    s = rec("S-1042", "supplier", {"supplier_id": "S-1042",
                                   "gstin": "GST123"})
    po = rec("PO-1", "purchase_order", {"supplier_id": "S-1042"})
    cert = rec("CERT-1", "certificate", {"gstin": "GST999"})
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s, po, cert],
    )
    assert len(result.correlations) > 0
    for c in result.correlations:
        assert 0.0 <= c.confidence <= 1.0


# ---------------------------------------------------------------------
# 9. Arbitrary generic-value matches must be rejected
# ---------------------------------------------------------------------

def test_rejects_arbitrary_generic_matches():
    s1 = rec("S-1042", "supplier", {"supplier_id": "S-1042",
                                    "country": "India"})
    s2 = rec("S-2051", "supplier", {"supplier_id": "S-2051",
                                    "country": "India"})
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s1, s2],
    )
    assert len(result.correlations) == 0


# ---------------------------------------------------------------------
# 10. Anchor resolution via supplier_name
# ---------------------------------------------------------------------

def test_anchor_resolves_via_supplier_name():
    s = rec("S-1042", "supplier", {
        "supplier_id": "S-1042",
        "supplier_name": "ABC Components",
        "gstin": "GST123",
    })
    po = rec("PO-4821", "purchase_order", {"supplier_id": "S-1042"})
    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_name", "ABC Components", 0.95)],
        records=[s, po],
    )
    assert result.anchor is not None
    assert result.anchor.record_external_id == "S-1042"
    assert result.anchor.matched_field == "supplier_name"
    assert result.anchor.matched_value == "ABC Components"
    assert len(result.correlations) == 1
    assert result.correlations[0].relationship_type \
        == "supplier_has_purchase_order"


# ---------------------------------------------------------------------
# 11. Secondary pairs must NOT correlate on the anchor's identity value
# ---------------------------------------------------------------------

def test_secondary_excludes_anchor_identity_value():
    """
    Two POs both referencing supplier_id='S-1042' must NOT correlate
    with each other — sharing the anchor's ID is not a distinct signal.
    """
    s = rec("S-1042", "supplier", {"supplier_id": "S-1042"})
    po1 = rec("PO-4821", "purchase_order", {"supplier_id": "S-1042"})
    po2 = rec("PO-4830", "purchase_order", {"supplier_id": "S-1042"})

    result = run_correlation_engine(
        use_case="supplier_qualification",
        entities=[ent("supplier_id", "S-1042", 1.0)],
        records=[s, po1, po2],
    )

    assert result.anchor is not None
    assert result.anchor.record_external_id == "S-1042"

    pair_ids = [
        frozenset({c.record_a_id, c.record_b_id})
        for c in result.correlations
    ]
    assert frozenset({po1.id, po2.id}) not in pair_ids
    assert len(result.correlations) == 2
    for c in result.correlations:
        assert c.basis == "exact_id"