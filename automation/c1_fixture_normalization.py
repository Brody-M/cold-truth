"""Deterministic Phase C1-only normalization for the synthetic Strategist fixture."""
from __future__ import annotations

import copy
from typing import Any


class FixtureNormalizationError(ValueError):
    pass


CLAIMS = ("SYN-C1-01", "SYN-C1-02", "SYN-C1-03")
REMOTE_FIELDS = ("claim_1", "claim_2", "claim_3")
NORMALIZATION_KIND = "fixture_claim_fields_to_claim_ids"


def _normalize_claim_container(container: dict[str, Any], path: str) -> None:
    if not isinstance(container, dict):
        raise FixtureNormalizationError(f"{path} must be an object")
    if "claim_ids" in container:
        raise FixtureNormalizationError(f"{path} must not contain canonical claim_ids before normalization")
    observed = tuple(container.get(name) for name in REMOTE_FIELDS)
    if observed != CLAIMS:
        raise FixtureNormalizationError(f"{path} remote claim fields are missing, altered, duplicated, or reordered")
    for name in REMOTE_FIELDS:
        del container[name]
    container["claim_ids"] = list(CLAIMS)


def normalize_c1_fixture_handoff(remote_handoff: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical handoff or fail; never repair an invalid remote claim set."""
    if not isinstance(remote_handoff, dict):
        raise FixtureNormalizationError("Remote handoff must be an object")
    if remote_handoff.get("case_id") != "glass-harbor-fixture":
        raise FixtureNormalizationError("Normalizer is restricted to the Phase C1 fixture")
    normalized = copy.deepcopy(remote_handoff)
    _normalize_claim_container(normalized.get("result"), "$.result")

    inputs = normalized.get("inputs")
    if not isinstance(inputs, list):
        raise FixtureNormalizationError("$.inputs must be an array")
    candidates = [item for item in inputs if isinstance(item, dict) and item.get("name") == "candidate_queue"]
    if len(candidates) != 1:
        raise FixtureNormalizationError("Exactly one candidate_queue input is required")
    _normalize_claim_container(candidates[0].get("value"), "$.inputs[candidate_queue].value")
    return normalized
