"""Deterministic normalization for the synthetic Phase C2 Research Verifier fixture."""
from __future__ import annotations

import copy
from typing import Any


class ResearchVerifierNormalizationError(ValueError):
    pass


NORMALIZATION_KIND = "fixture_research_claim_fields_to_canonical_lists"
APPROVED = ("SYN-RV-01", "SYN-RV-02", "SYN-RV-03")
REJECTED = (
    ("SYN-RV-X1", "unverified_unnamed_allegation"),
    ("SYN-RV-X2", "unverified_online_theory"),
    ("SYN-RV-X3", "source_ledger_conflict"),
)
SOURCE_CONFLICTS = ("SYN-RV-X3: source_ledger_conflict",)
UNSUPPORTED_MATERIAL = ("SYN-RV-X1", "SYN-RV-X2")


def normalize_c2_research_verifier_handoff(remote: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(remote, dict) or remote.get("case_id") != "glass-river-research-fixture":
        raise ResearchVerifierNormalizationError("Normalizer is restricted to the synthetic Phase C2 fixture")
    result = remote.get("result")
    if not isinstance(result, dict):
        raise ResearchVerifierNormalizationError("Remote result must be an object")
    if "approved_claim_ids" in result or "rejected_claims" in result:
        raise ResearchVerifierNormalizationError("Remote result must not prepopulate canonical claim fields")

    approved = tuple(result.get(f"approved_claim_{index}") for index in range(1, 4))
    rejected = tuple(
        (result.get(f"rejected_claim_{index}"), result.get(f"rejected_reason_{index}"))
        for index in range(1, 4)
    )
    if approved != APPROVED:
        raise ResearchVerifierNormalizationError("Approved claim fields are missing, altered, duplicated, or reordered")
    if rejected != REJECTED:
        raise ResearchVerifierNormalizationError("Rejected claim fields or reason codes are missing, altered, duplicated, or reordered")
    if tuple(result.get("source_conflicts", [])) != SOURCE_CONFLICTS:
        raise ResearchVerifierNormalizationError("Source conflicts must contain only the documented X3 ledger conflict")
    if tuple(result.get("unsupported_or_creator_derived_material", [])) != UNSUPPORTED_MATERIAL:
        raise ResearchVerifierNormalizationError("Unsupported material must contain only X1 and X2 in order")

    input_hashes = {item.get("name"): item.get("sha256") for item in request.get("inputs", []) if isinstance(item, dict)}
    expected_hashes = {
        "upstream_strategist_handoff_hash": input_hashes.get("synthetic_strategist_handoff"),
        "ledger_hash": input_hashes.get("synthetic_source_ledger"),
        "boundaries_hash": input_hashes.get("synthetic_research_boundaries"),
    }
    if any(not value for value in expected_hashes.values()):
        raise ResearchVerifierNormalizationError("Request is missing a required synthetic input hash")
    for field, expected in expected_hashes.items():
        if result.get(field) != expected:
            raise ResearchVerifierNormalizationError(f"Remote result hash mismatch: {field}")

    normalized = copy.deepcopy(remote)
    normalized_result = normalized["result"]
    for index in range(1, 4):
        del normalized_result[f"approved_claim_{index}"]
        del normalized_result[f"rejected_claim_{index}"]
        del normalized_result[f"rejected_reason_{index}"]
    normalized_result["approved_claim_ids"] = list(APPROVED)
    normalized_result["rejected_claims"] = [
        {"claim_id": claim_id, "reason_code": reason_code}
        for claim_id, reason_code in REJECTED
    ]
    return normalized
