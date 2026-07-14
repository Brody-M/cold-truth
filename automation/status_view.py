"""Deterministic machine-readable status projection for one Cold Truth run."""
from __future__ import annotations

import hashlib
import json
from typing import Any


STATUS_SCHEMA_VERSION = "cold_truth.run_status.v1"

TERMINAL_OR_REVIEW_STATES = {
    "AWAITING_SCRIPT_APPROVAL",
    "AWAITING_ASSEMBLY_APPROVAL",
    "BLOCKED_RUNTIME",
    "RETURNED_TO_BACKLOG",
    "FAILED",
    "AGENT_BLOCKED",
    "DRY_RUN_COMPLETE",
    "COMPLETE_LOCAL",
    "INVALIDATED_UPSTREAM_CHANGE",
}

STATE_ACTIONS = {
    "QUEUED": ("RUN_DETERMINISTIC_CASE_SELECTION", False),
    "STRATEGIST_COMPLETE": ("RUN_RESEARCH_VERIFICATION", False),
    "RESEARCH_VERIFIED": ("RUN_VIABILITY_AND_CASE_SELECTION", False),
    "CASE_SELECTED": ("RUN_WRITER_DRAFT", False),
    "WRITER_COMPLETE": ("RUN_EDITOR_REVERSE_OUTLINE_AND_FULL_DRAFT", False),
    "AWAITING_SCRIPT_APPROVAL": ("HUMAN_REVIEW_REVERSE_OUTLINE_AND_FULL_DRAFT", True),
    "SCRIPT_APPROVED": ("RUN_DRY_RUN_NARRATION_DESCRIPTOR", False),
    "NARRATION_GENERATED": ("RUN_EXACT_AUDIO_RUNTIME_PREFLIGHT", False),
    "AUDIO_PREFLIGHT_PASSED": ("RUN_ALIGNMENT", False),
    "WHISPERX_ALIGNED": ("RUN_LONGFORM_VISUAL_PLANNING", False),
    "LONGFORM_ASSETS_READY": ("RUN_STANDALONE_SHORTS_PLANNING", False),
    "SHORTS_PACKAGE_READY": ("RUN_TRACK_ISOLATION_VALIDATION", False),
    "TRACK_ISOLATION_VALIDATED": ("BUILD_DRY_RUN_ASSEMBLY_RECORDS", False),
    "AWAITING_ASSEMBLY_APPROVAL": ("HUMAN_REVIEW_DRY_RUN_ASSEMBLIES", True),
    "ASSEMBLY_APPROVED": ("BUILD_NON_MEDIA_DRY_RUN_RELEASE_RECORDS", False),
    "DRY_RUN_COMPLETE": ("STOP_FOR_HUMAN_REVIEW", True),
    "COMPLETE_LOCAL": ("STOP_FOR_HUMAN_REVIEW", True),
    "RETURNED_TO_BACKLOG": ("STOP_OR_AUTHORIZE_DIFFERENT_CASE_SCOPE", True),
    "BLOCKED_RUNTIME": ("STOP_AND_REVISE_SOURCE_BOUND_SCRIPT_OR_APPROVE_EXCEPTION", True),
    "FAILED": ("STOP_AND_AUTHORIZE_A_BOUNDED_REPAIR", True),
    "AGENT_BLOCKED": ("STOP_AND_AUTHORIZE_A_BOUNDED_REPAIR", True),
}

ARTIFACT_ORDER = [
    "ranked_candidates.json",
    "Research_Source_Ledger.md",
    "Research_Verification.json",
    "Script_Draft.md",
    "Reverse_Outline.md",
    "Script_Draft_Reviewed.md",
    "checkpoint_1_packet.json",
    "Script_Final.md",
    "narration_descriptor.json",
    "preflight.json",
    "longform_alignment.json",
    "YouTube_Visual_Timeline.md",
    "longform_assets.json",
    "Shorts_Package.md",
    "Shorts_Visual_Timeline.md",
    "shorts_assets.json",
    "track_isolation.json",
    "longform_assembly.json",
    "shorts_assembly.json",
    "checkpoint_2_packet.json",
    "render_plan.json",
    "validated_local_renders.json",
    "Upload_Package.md",
    "metadata_plan.json",
    "audit_completion.json",
]


def _canonical_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _approval_view(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"present": False, "status": "missing", "consumed": False, "consumption_count": 0}
    return {
        "present": True,
        "approval_id": value.get("approval_id"),
        "purpose": value.get("purpose"),
        "status": value.get("status", "unknown"),
        "consumed": value.get("consumed") is True,
        "consumption_count": value.get("consumption_count", 0),
        "only_allowed_next_state": value.get("only_allowed_next_state"),
        "source_approval_sha256": value.get("source_approval_sha256"),
    }


def _last_clean_artifact(registry: dict[str, Any]) -> dict[str, Any] | None:
    for name in reversed(ARTIFACT_ORDER):
        record = registry.get(name)
        if isinstance(record, dict):
            return {
                "name": name,
                "path": record.get("path"),
                "sha256": record.get("sha256"),
                "size_bytes": record.get("size_bytes"),
            }
    return None


def build_status_view(state: dict[str, Any]) -> dict[str, Any]:
    current_state = str(state.get("state", "UNKNOWN"))
    action, human_authority = STATE_ACTIONS.get(
        current_state,
        ("STOP_UNKNOWN_OR_UNMAPPED_STATE", True),
    )
    if current_state == "INVALIDATED_UPSTREAM_CHANGE":
        restart = state.get("next_required_checkpoint", "UNKNOWN_CHECKPOINT")
        action = f"RETURN_TO_{restart}"
        human_authority = True

    selected_case = state.get("selected_case") if isinstance(state.get("selected_case"), dict) else {}
    registry = state.get("artifact_registry") if isinstance(state.get("artifact_registry"), dict) else {}
    stale = sorted(set(state.get("stale_artifacts") or []))
    last_error = state.get("last_error")
    if current_state.startswith("AWAITING_"):
        blocker = {"code": "HUMAN_APPROVAL_REQUIRED", "message": None}
    elif current_state == "INVALIDATED_UPSTREAM_CHANGE":
        blocker = {"code": "UPSTREAM_HASH_CHANGED", "message": state.get("next_required_checkpoint")}
    elif current_state in {"BLOCKED_RUNTIME", "FAILED", "AGENT_BLOCKED"}:
        blocker = {"code": current_state, "message": last_error}
    else:
        blocker = None

    view: dict[str, Any] = {
        "schema_version": STATUS_SCHEMA_VERSION,
        "run_id": state.get("run_id"),
        "episode_id": state.get("episode_id"),
        "case": {
            "case_id": selected_case.get("candidate_id"),
            "case_name": selected_case.get("case_name"),
        },
        "current_checkpoint": current_state,
        "terminal_or_human_review_state": current_state in TERMINAL_OR_REVIEW_STATES,
        "dry_run": state.get("dry_run") is True,
        "blocker": blocker,
        "last_clean_artifact": _last_clean_artifact(registry),
        "active_artifact_count": len(registry),
        "stale_artifacts": stale,
        "stale_artifact_count": len(stale),
        "stale_record_count": len(state.get("stale_artifact_records") or []),
        "approvals": {
            "script": _approval_view(state.get("script_approval")),
            "assembly": _approval_view(state.get("assembly_approval")),
        },
        "audit_chain": state.get("audit_chain"),
        "next_permitted_action": {
            "action": action,
            "human_authority_required": human_authority,
            "offline_only": True,
            "maximum_action_count": 1,
        },
        "capabilities": {
            "network_enabled": False,
            "provider_enabled": False,
            "media_creation_enabled": False,
            "rendering_enabled": False,
            "upload_enabled": False,
            "scheduling_enabled": False,
            "publishing_enabled": False,
            "real_production_enabled": False,
        },
    }
    view["status_sha256"] = _canonical_hash(view)
    return view
