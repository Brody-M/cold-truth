"""Fixture-only, offline narration-preflight gate for Phase C5."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from c4_script_approval_gate import CASE_ID, expected_bindings
from json_schema_subset import SchemaSubsetError, validate
from run_records import atomic_json, sanitize_value


PASSED = "NARRATION_PREFLIGHT_PASSED"
BLOCKED = "NARRATION_PREFLIGHT_BLOCKED"
NEXT_AUTHORIZATION = "separate_human_authorization_for_synthetic_narration_test"
LOCKED_PROFILE: dict[str, Any] = {
    "schema_version": "1.0",
    "voice_profile_name": "Mia",
    "stability": 0.72,
    "similarity_boost": 0.76,
    "style": 0.05,
    "speed": 0.94,
    "use_speaker_boost": True,
    "output_format": "mp3_44100_128",
    "audio_generation_authorized": False,
    "network_authorized": False,
    "api_key_required_for_generation": True,
    "real_production_enabled": False,
    "publishing_enabled": False,
}
FORBIDDEN_KEY_PARTS = (
    "voice_id", "endpoint", "credential", "external_service", "access_token",
    "auth_token", "secret", "provider_command", "provider_url", "api_url",
)
FORBIDDEN_VALUE = re.compile(
    r"(?i)(https?://|\bapi[ _-]?key\b|\bvoice[ _-]?id\b|\bendpoint\b|"
    r"\bcredential\b|\bexternal[ _-]?service\b|(?:^|\s)(?:sk|xi)[-_][A-Za-z0-9_-]{12,}|"
    r"^[A-Za-z]:[\\/]|^\\\\)"
)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_result(
    state: str, reason: str, *, request_id: str = "", approval_id: str = "",
    requested_output_path: str = "", output_format: str = "",
    voice_profile_name: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "1.0", "request_id": request_id,
        "approval_id": approval_id, "case_id": CASE_ID, "state": state,
        "reason": reason, "requested_output_path": requested_output_path,
        "output_format": output_format, "voice_profile_name": voice_profile_name,
        "narration_generation_authorized": False, "network_authorized": False,
        "output_file_created": False,
        "next_required_authorization": NEXT_AUTHORIZATION,
        "asset_authorized": False, "assembly_authorized": False,
        "rendering_authorized": False, "upload_authorized": False,
        "scheduling_authorized": False, "publishing_enabled": False,
        "real_production_enabled": False,
    }


def _contains_forbidden(value: Any, key: str = "") -> bool:
    lowered = key.lower()
    if key != "api_key_required_for_generation" and (
        "api_key" in lowered or any(part in lowered for part in FORBIDDEN_KEY_PARTS)
    ):
        return True
    if isinstance(value, dict):
        return any(_contains_forbidden(item, str(name)) for name, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden(item, key) for item in value)
    return isinstance(value, str) and FORBIDDEN_VALUE.search(value) is not None


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def run_preflight(
    *, fixture_root: Path, writer_path: Path, editor_path: Path,
    approval_path: Path | None, profile_path: Path, request_path: Path,
    state_root: Path, approval_schema_path: Path, request_schema_path: Path,
    result_schema_path: Path,
) -> dict[str, Any]:
    c5_root = fixture_root.resolve() / "narration_preflight"
    output_root = c5_root / "output"
    if not _inside(state_root, output_root):
        return _safe_result(BLOCKED, "state_path_escape")
    inputs = [writer_path, editor_path, profile_path, request_path,
              approval_schema_path, request_schema_path, result_schema_path]
    if approval_path is not None:
        inputs.append(approval_path)
    if any(not _inside(path, fixture_root) for path in inputs):
        return _safe_result(BLOCKED, "input_path_escape")
    if approval_path is None or not approval_path.exists():
        return _safe_result(BLOCKED, "approval_artifact_missing")
    try:
        request = _load_object(request_path)
        approval = _load_object(approval_path)
        profile = _load_object(profile_path)
        approval_schema = _load_object(approval_schema_path)
        request_schema = _load_object(request_schema_path)
        result_schema = _load_object(result_schema_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return _safe_result(BLOCKED, "fixture_input_unreadable")
    ids = {
        "request_id": request.get("request_id", "") if isinstance(request.get("request_id", ""), str) else "",
        "approval_id": approval.get("approval_id", "") if isinstance(approval.get("approval_id", ""), str) else "",
        "requested_output_path": request.get("requested_output_path", "") if isinstance(request.get("requested_output_path", ""), str) else "",
        "output_format": request.get("requested_output_format", "") if isinstance(request.get("requested_output_format", ""), str) else "",
        "voice_profile_name": profile.get("voice_profile_name", "") if isinstance(profile.get("voice_profile_name", ""), str) else "",
    }

    def block(reason: str) -> dict[str, Any]:
        result = _safe_result(BLOCKED, reason, **ids)
        validate(result, result_schema)
        return result

    if _contains_forbidden(request) or _contains_forbidden(approval) or _contains_forbidden(profile):
        return block("forbidden_external_or_secret_field")
    try:
        validate(request, request_schema)
        validate(approval, approval_schema)
    except SchemaSubsetError as exc:
        return block(f"schema_validation_failed: {exc}")
    if approval.get("decision") != "approve":
        return block("approval_decision_not_approve")
    if approval.get("reviewer_role") != "human_owner":
        return block("invalid_reviewer_role")
    expected = expected_bindings(writer_path, editor_path)
    for field, expected_value in expected.items():
        if approval.get(field) != expected_value:
            return block(f"{field}_mismatch")
    if approval.get("permitted_next_stage") != "narration_preflight_only":
        return block("invalid_next_stage")
    approval_denials = ("narration_authorized", "asset_authorized", "rendering_authorized",
                        "publishing_enabled", "real_production_enabled")
    if any(approval.get(field) is not False for field in approval_denials):
        return block("approval_permission_escalation")
    if profile != LOCKED_PROFILE:
        return block("locked_narration_profile_mismatch")
    request_denials = ("create_output_file", "invoke_provider", "narration_authorized",
                       "network_authorized", "asset_authorized", "assembly_authorized",
                       "rendering_authorized", "upload_authorized", "scheduling_authorized",
                       "publishing_enabled", "real_production_enabled")
    if any(request.get(field) is not False for field in request_denials):
        return block("request_permission_escalation")
    relative_text = request["requested_output_path"]
    relative_path = Path(relative_text)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return block("requested_output_path_escape")
    proposed_output = (output_root / relative_path).resolve()
    if not _inside(proposed_output, output_root):
        return block("requested_output_path_escape")
    if proposed_output.exists():
        return block("proposed_output_already_exists")
    if request["requested_output_format"] != profile["output_format"]:
        return block("requested_output_format_mismatch")
    consumed_path = state_root.resolve() / "consumed_approval_ids" / f"{approval['approval_id']}.json"
    if consumed_path.exists():
        return block("approval_id_replayed_or_consumed")
    record_path = state_root.resolve() / "preflight_records" / f"{request['request_id']}.json"
    if record_path.exists():
        return block("request_id_replay")
    result = _safe_result(PASSED, "all_fixture_preflight_checks_passed", **ids)
    validate(result, result_schema)
    atomic_json(consumed_path, sanitize_value({
        "schema_version": "1.0", "approval_id": approval["approval_id"],
        "request_id": request["request_id"], "state": PASSED,
        "audio_created": False, "external_process_invoked": False,
        "real_production_enabled": False, "publishing_enabled": False,
    }))
    atomic_json(record_path, sanitize_value(result))
    return result
