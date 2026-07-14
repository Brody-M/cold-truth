"""Synthetic-only Writer/Editor normalization and checkpoint logic for Phase C3."""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

APPROVED = ("SYN-RV-01", "SYN-RV-02", "SYN-RV-03")
EXCLUDED = ("SYN-RV-X1", "SYN-RV-X2", "SYN-RV-X3")
SENTENCES = (
    "A fictional official record fixes the event date as April 17, 2042.",
    "A second fictional official record places the event at Glass River Annex in Example District.",
    "A fictional archive records a current-status update dated September 8, 2044.",
)
SECTIONS = ("event_date", "event_location", "current_status")


class C3FixtureError(ValueError): pass


def validate_fixture_paths(request: dict[str, Any], fixture_root: Path) -> None:
    root=fixture_root.resolve()
    for item in request.get("inputs",[]):
        path=Path(str(item.get("path",""))).resolve()
        try: path.relative_to(root)
        except ValueError as exc: raise C3FixtureError("C3 input path escapes fixture root") from exc
        if item.get("kind")!="file" or not path.is_file(): raise C3FixtureError("C3 input must be an existing fixture file")


def _input_hash(request: dict[str, Any], name: str) -> str:
    matches = [item.get("sha256") for item in request.get("inputs", []) if item.get("name") == name]
    if len(matches) != 1 or not matches[0]: raise C3FixtureError(f"Missing input hash: {name}")
    return matches[0]


def normalize_writer(remote: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    result = remote.get("result")
    if remote.get("case_id") != "glass-river-writing-fixture" or not isinstance(result, dict): raise C3FixtureError("Writer fixture identity mismatch")
    if result.get("upstream_research_verifier_handoff_hash") != _input_hash(request, "synthetic_research_verifier_handoff"): raise C3FixtureError("Writer upstream hash mismatch")
    approved = tuple(result.get(f"approved_claim_{i}") for i in range(1,4)); excluded = tuple(result.get(f"excluded_claim_{i}") for i in range(1,4))
    sentences = tuple(result.get(f"sentence_{i}") for i in range(1,4)); sections = tuple(result.get(f"section_{i}") for i in range(1,4)); attrs = tuple(result.get(f"attribution_{i}") for i in range(1,4))
    if approved != APPROVED or excluded != EXCLUDED: raise C3FixtureError("Writer claim boundary mismatch")
    if sentences != SENTENCES or sections != SECTIONS or attrs != APPROVED: raise C3FixtureError("Writer sentence attribution or fixture text mismatch")
    if result.get("narration_text") != " ".join(SENTENCES) or result.get("word_count") != 38: raise C3FixtureError("Writer narration or word count mismatch")
    if any(claim in result["narration_text"] for claim in EXCLUDED): raise C3FixtureError("Excluded claim appears in narration")
    normalized=copy.deepcopy(remote); out=normalized["result"]
    for i in range(1,4):
        for prefix in ("approved_claim_","excluded_claim_","section_","sentence_","attribution_"): del out[f"{prefix}{i}"]
    out["approved_claim_ids"]=list(APPROVED); out["excluded_claim_ids"]=list(EXCLUDED)
    out["script_sections"]=[{"section":s,"sentence":t} for s,t in zip(SECTIONS,SENTENCES)]
    out["claim_attribution_map"]=[{"sentence_index":i,"claim_id":c} for i,c in enumerate(APPROVED,1)]
    return normalized


def redundancy_findings(writer: dict[str, Any]) -> list[str]:
    result=writer["result"]; sections=result["script_sections"]; findings=[]
    normalized=[re.sub(r"[^a-z0-9]+"," ",item["sentence"].lower()).strip() for item in sections]
    if len(set(normalized)) != len(normalized): findings.append("duplicate_or_near_duplicate_sentence")
    claims=[item["claim_id"] for item in result["claim_attribution_map"]]
    if len(set(claims)) != len(claims): findings.append("claim_restatement_across_sections")
    for phrase in ("april 17 2042","glass river annex","example district","september 8 2044"):
        if sum(phrase in text for text in normalized) > 1: findings.append(f"repeated_named_phrase:{phrase}")
    return findings


def normalize_editor(remote: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    result=remote.get("result")
    if remote.get("case_id") != "glass-river-writing-fixture" or not isinstance(result,dict): raise C3FixtureError("Editor fixture identity mismatch")
    if result.get("upstream_writer_handoff_hash") != _input_hash(request,"synthetic_writer_handoff"): raise C3FixtureError("Editor upstream hash mismatch")
    seen=tuple(result.get(f"approved_seen_{i}") for i in range(1,4)); absent=tuple(result.get(f"excluded_absent_{i}") for i in range(1,4))
    if seen!=APPROVED or absent!=EXCLUDED: raise C3FixtureError("Editor claim boundary mismatch")
    required={"factual_attribution_check":"passed","unsupported_material_check":"passed","redundancy_check":"passed","narrative_coherence_check":"passed","editor_decision":"ready_for_human_script_review","simulated_human_checkpoint_required":True,"handoff_to_human_review":True,"later_stage_requested":False}
    if any(result.get(k)!=v for k,v in required.items()) or result.get("redundancy_findings")!=[]: raise C3FixtureError("Editor checks do not permit human checkpoint readiness")
    normalized=copy.deepcopy(remote); out=normalized["result"]
    for i in range(1,4): del out[f"approved_seen_{i}"]; del out[f"excluded_absent_{i}"]
    out["approved_claim_ids_seen"]=list(APPROVED); out["excluded_claim_ids_absent"]=list(EXCLUDED)
    return normalized


def simulated_checkpoint(writer: dict[str, Any], editor: dict[str, Any]) -> dict[str, Any]:
    if redundancy_findings(writer): raise C3FixtureError("Deterministic redundancy gate failed")
    if editor["result"].get("editor_decision")!="ready_for_human_script_review": raise C3FixtureError("Editor did not reach review")
    return {"state":"AWAITING_SCRIPT_APPROVAL","simulated_human_checkpoint_required":True,"narration_authorized":False,"assets_authorized":False,"real_production_enabled":False}
