"""Offline, fixture-only human script-approval gate for Phase C4."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from json_schema_subset import SchemaSubsetError, validate
from run_records import atomic_json, sanitize_value


AWAITING = "AWAITING_SCRIPT_APPROVAL"
APPROVED = "SCRIPT_APPROVED_FOR_PREFLIGHT"
REVISION = "WRITER_REVISION_REQUIRED"
BLOCKED = "BLOCKED"
CASE_ID = "glass-river-writing-fixture"
REJECTION_CODES = {
    "factual_clarity_revision",
    "redundancy_revision",
    "narrative_coherence_revision",
    "human_editorial_preference",
}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def script_sha256(writer_handoff: dict[str, Any]) -> str:
    text = writer_handoff.get("result", {}).get("narration_text")
    if not isinstance(text, str) or not text:
        raise ValueError("Writer handoff has no approved narration_text")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_bindings(writer_path: Path, editor_path: Path) -> dict[str, str]:
    writer = json.loads(writer_path.read_text(encoding="utf-8"))
    return {
        "upstream_writer_handoff_hash": file_sha256(writer_path),
        "upstream_editor_handoff_hash": file_sha256(editor_path),
        "approved_script_hash": script_sha256(writer),
    }


def _blocked(reason: str) -> dict[str, Any]:
    return {"state": BLOCKED, "reason": reason, "narration_authorized": False,
            "asset_authorized": False, "rendering_authorized": False,
            "publishing_enabled": False, "real_production_enabled": False}


def evaluate_decision(
    current_state: str,
    artifact: dict[str, Any],
    writer_path: Path,
    editor_path: Path,
    approval_schema: dict[str, Any],
    rejection_schema: dict[str, Any],
) -> dict[str, Any]:
    if current_state != AWAITING:
        return _blocked("invalid_source_state")
    decision = artifact.get("decision")
    schema = approval_schema if decision == "approve" else rejection_schema if decision == "reject" else None
    if schema is None:
        return _blocked("invalid_decision")
    try:
        validate(artifact, schema)
    except SchemaSubsetError as exc:
        return _blocked(f"schema_validation_failed: {exc}")
    if artifact.get("reviewer_role") != "human_owner":
        return _blocked("invalid_reviewer")
    expected = expected_bindings(writer_path, editor_path)
    for field, value in expected.items():
        if artifact.get(field) != value:
            return _blocked(f"{field}_mismatch")
    if artifact.get("case_id") != CASE_ID:
        return _blocked("case_id_mismatch")
    guarded = ("narration_authorized", "asset_authorized", "rendering_authorized",
               "publishing_enabled", "real_production_enabled")
    if any(artifact.get(field) is not False for field in guarded):
        return _blocked("permission_escalation")
    if decision == "approve":
        if artifact.get("permitted_next_stage") != "narration_preflight_only":
            return _blocked("invalid_approval_stage")
        state = APPROVED
    else:
        if artifact.get("rejection_reason_code") not in REJECTION_CODES:
            return _blocked("invalid_rejection_reason")
        if artifact.get("required_return_stage") != REVISION:
            return _blocked("invalid_rejection_return_stage")
        state = REVISION
    return {"state": state, "decision": decision, "approval_id": artifact["approval_id"],
            "narration_authorized": False, "asset_authorized": False,
            "rendering_authorized": False, "publishing_enabled": False,
            "real_production_enabled": False}


def process_decision(
    *, fixture_root: Path, output_root: Path, current_state: str,
    artifact_path: Path | None, writer_path: Path, editor_path: Path,
    approval_schema_path: Path, rejection_schema_path: Path,
) -> dict[str, Any]:
    allowed_output = fixture_root.resolve() / "output"
    if not _inside(output_root, allowed_output):
        return _blocked("output_path_escape")
    if artifact_path is None:
        return {"state": current_state, "reason": "approval_artifact_missing",
                "narration_authorized": False, "asset_authorized": False,
                "rendering_authorized": False, "publishing_enabled": False,
                "real_production_enabled": False}
    if not _inside(artifact_path, fixture_root) or not _inside(writer_path, fixture_root) or not _inside(editor_path, fixture_root):
        return _blocked("input_path_escape")
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        if not isinstance(artifact, dict):
            return _blocked("artifact_not_object")
    except (OSError, json.JSONDecodeError):
        return _blocked("artifact_unreadable")
    approval_id = artifact.get("approval_id")
    if not isinstance(approval_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{7,79}", approval_id):
        return _blocked("invalid_approval_id")
    record_path = output_root.resolve() / "decision_records" / f"{approval_id}.json"
    if record_path.exists():
        return _blocked("approval_id_replay")
    result = evaluate_decision(
        current_state, artifact, writer_path, editor_path,
        json.loads(approval_schema_path.read_text(encoding="utf-8")),
        json.loads(rejection_schema_path.read_text(encoding="utf-8")),
    )
    record = {
        "schema_version": "1.0",
        "approval_id": approval_id,
        "artifact_sha256": file_sha256(artifact_path),
        "artifact": sanitize_value(artifact),
        "result": result,
        "fixture_only": True,
        "external_process_invoked": False,
        "real_production_enabled": False,
        "publishing_enabled": False,
    }
    if record_path.exists():
        return _blocked("approval_id_replay")
    atomic_json(record_path, record)
    return result
