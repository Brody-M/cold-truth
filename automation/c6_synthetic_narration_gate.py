"""Offline validation gate for the fixture-only Phase C6 narration adapter."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from c4_script_approval_gate import CASE_ID, expected_bindings, file_sha256
from c5_narration_preflight_gate import LOCKED_PROFILE
from json_schema_subset import SchemaSubsetError, validate
from run_records import atomic_json, sanitize_value


READY = "SYNTHETIC_NARRATION_READY"
BLOCKED = "SYNTHETIC_NARRATION_BLOCKED"
NEXT_AUTHORIZATION = "separate_human_authorization_for_one_synthetic_provider_call"
FORBIDDEN_KEYS = (
    "voice_id", "endpoint", "credential", "external_service", "provider_config",
    "provider_name", "api_url", "access_token", "auth_token", "secret",
    "environment", "env_var", "production_path",
)
FORBIDDEN_VALUES = re.compile(
    r"(?i)(https?://|\bapi[ _-]?key\b|\bvoice[ _-]?id\b|\bendpoint\b|"
    r"\bcredential\b|\bexternal[ _-]?service\b|\bos\.environ\b|\$\{[^}]+\}|"
    r"%[A-Za-z_][A-Za-z0-9_]*%|(?:^|\s)(?:sk|xi)[-_][A-Za-z0-9_-]{12,}|"
    r"^[A-Za-z]:[\\/]|^\\\\)"
)


def ready_result() -> dict[str, Any]:
    return {
        "state": READY,
        "provider_invoked": False,
        "network_invoked": False,
        "audio_file_created": False,
        "real_production_enabled": False,
        "next_required_authorization": NEXT_AUTHORIZATION,
    }


def blocked_result(reason: str) -> dict[str, Any]:
    return {
        "state": BLOCKED,
        "provider_invoked": False,
        "network_invoked": False,
        "audio_file_created": False,
        "real_production_enabled": False,
        "safe_reason_code": reason,
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root is not an object")
    return value


def _forbidden(value: Any, key: str = "") -> bool:
    lowered = key.lower()
    allowed_control_keys = {"api_key_required_for_generation", "invoke_provider"}
    if key not in allowed_control_keys and (
        "api_key" in lowered or any(part in lowered for part in FORBIDDEN_KEYS)
    ):
        return True
    if isinstance(value, dict):
        return any(_forbidden(item, str(name)) for name, item in value.items())
    if isinstance(value, list):
        return any(_forbidden(item, key) for item in value)
    return isinstance(value, str) and FORBIDDEN_VALUES.search(value) is not None


def path_text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_synthetic_narration(
    *, fixture_root: Path, writer_path: Path, editor_path: Path,
    c4_approval_path: Path | None, c5_preflight_path: Path | None,
    profile_path: Path, c6_authorization_path: Path | None,
    request_path: Path, c4_approval_schema_path: Path,
    c5_result_schema_path: Path, c6_authorization_schema_path: Path,
    request_schema_path: Path, state_root: Path,
) -> dict[str, Any]:
    c6_output = fixture_root.resolve() / "narration_preflight" / "output" / "c6_synthetic_narration_adapter"
    if not _inside(state_root, c6_output):
        return blocked_result("state_path_escape")
    if c4_approval_path is None:
        return blocked_result("c4_approval_missing")
    if c5_preflight_path is None:
        return blocked_result("c5_preflight_missing")
    if c6_authorization_path is None:
        return blocked_result("c6_authorization_missing")
    inputs = [writer_path, editor_path, c4_approval_path, c5_preflight_path,
              profile_path, c6_authorization_path, request_path,
              c4_approval_schema_path, c5_result_schema_path,
              c6_authorization_schema_path, request_schema_path]
    if any(not _inside(path, fixture_root) for path in inputs):
        return blocked_result("input_path_escape")
    try:
        writer = _load(writer_path)
        approval = _load(c4_approval_path)
        preflight = _load(c5_preflight_path)
        profile = _load(profile_path)
        authorization = _load(c6_authorization_path)
        request = _load(request_path)
        approval_schema = _load(c4_approval_schema_path)
        preflight_schema = _load(c5_result_schema_path)
        authorization_schema = _load(c6_authorization_schema_path)
        request_schema = _load(request_schema_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return blocked_result("fixture_input_unreadable")

    request_id = request.get("request_id", "") if isinstance(request.get("request_id"), str) else ""
    authorization_id = authorization.get("narration_authorization_id", "") if isinstance(authorization.get("narration_authorization_id"), str) else ""

    def record(result: dict[str, Any]) -> dict[str, Any]:
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{7,95}", request_id):
            record_path = state_root.resolve() / "validation_records" / f"{request_id}.json"
            if not record_path.exists():
                atomic_json(record_path, sanitize_value({
                    "schema_version": "1.0", "request_id": request_id,
                    "narration_authorization_id": authorization_id,
                    "result": result, "fixture_only": True,
                    "provider_invoked": False, "network_invoked": False,
                    "audio_file_created": False, "real_production_enabled": False,
                }))
        return result

    def block(reason: str) -> dict[str, Any]:
        return record(blocked_result(reason))

    if any(_forbidden(value) for value in (approval, preflight, profile, authorization, request)):
        return block("forbidden_secret_external_or_production_reference")
    try:
        validate(approval, approval_schema)
        validate(preflight, preflight_schema)
        validate(authorization, authorization_schema)
        validate(request, request_schema)
    except SchemaSubsetError:
        return block("schema_validation_failed")
    if approval.get("decision") != "approve" or approval.get("reviewer_role") != "human_owner":
        return block("invalid_c4_approval")
    expected = expected_bindings(writer_path, editor_path)
    for field, expected_value in expected.items():
        if approval.get(field) != expected_value or authorization.get(field) != expected_value:
            return block(f"{field}_mismatch")
    if approval.get("permitted_next_stage") != "narration_preflight_only":
        return block("invalid_c4_stage")
    if any(approval.get(field) is not False for field in (
        "narration_authorized", "asset_authorized", "rendering_authorized",
        "publishing_enabled", "real_production_enabled"
    )):
        return block("c4_permission_escalation")
    if preflight.get("state") != "NARRATION_PREFLIGHT_PASSED":
        return block("c5_preflight_not_passed")
    if preflight.get("approval_id") != approval.get("approval_id"):
        return block("c5_approval_binding_mismatch")
    if any(preflight.get(field) is not False for field in (
        "narration_generation_authorized", "network_authorized", "output_file_created",
        "asset_authorized", "assembly_authorized", "rendering_authorized",
        "upload_authorized", "scheduling_authorized", "publishing_enabled",
        "real_production_enabled"
    )):
        return block("c5_permission_escalation")
    if profile != LOCKED_PROFILE:
        return block("locked_profile_mismatch")
    if authorization.get("approval_id") != approval.get("approval_id"):
        return block("c6_approval_binding_mismatch")
    if authorization.get("narration_preflight_result_hash") != file_sha256(c5_preflight_path):
        return block("preflight_result_hash_mismatch")
    if authorization.get("locked_profile_hash") != file_sha256(profile_path):
        return block("locked_profile_hash_mismatch")
    if authorization.get("decision") != "approve_synthetic_narration_test" or authorization.get("reviewer_role") != "human_owner":
        return block("invalid_c6_authorization")
    if authorization.get("permitted_action") != "synthetic_narration_generation_only":
        return block("invalid_c6_action")
    if authorization.get("network_authorized") is not False or authorization.get("narration_generation_authorized") is not True:
        return block("invalid_c6_narration_boundary")
    if any(authorization.get(field) is not False for field in (
        "asset_authorized", "assembly_authorized", "rendering_authorized",
        "upload_authorized", "scheduling_authorized", "publishing_enabled",
        "real_production_enabled"
    )):
        return block("c6_permission_escalation")
    if request.get("requested_action") != "synthetic_narration_generation_only":
        return block("invalid_requested_action")
    if any(request.get(field) is not False for field in (
        "invoke_actual_narration", "invoke_provider", "network_requested",
        "asset_authorized", "assembly_authorized", "rendering_authorized",
        "upload_authorized", "scheduling_authorized", "publishing_enabled",
        "real_production_enabled"
    )):
        return block("request_permission_or_provider_escalation")
    relative_text = request.get("requested_output_relative_path", "")
    if relative_text != authorization.get("requested_output_relative_path") or relative_text != preflight.get("requested_output_path"):
        return block("requested_output_path_mismatch")
    if authorization.get("requested_output_path_hash") != path_text_sha256(relative_text):
        return block("requested_output_path_hash_mismatch")
    relative_path = Path(relative_text)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return block("requested_output_path_escape")
    proposed_audio = (c6_output / relative_path).resolve()
    if not _inside(proposed_audio, c6_output):
        return block("requested_output_path_escape")
    if proposed_audio.exists():
        return block("existing_audio_or_output_path")
    if request.get("requested_output_format") != "mp3_44100_128" or authorization.get("requested_output_format") != "mp3_44100_128" or preflight.get("output_format") != "mp3_44100_128":
        return block("output_format_mismatch")
    if preflight.get("voice_profile_name") != "Mia" or preflight.get("case_id") != CASE_ID or authorization.get("case_id") != CASE_ID or request.get("case_id") != CASE_ID:
        return block("fixture_identity_mismatch")
    consumed = state_root.resolve() / "consumed_authorization_ids" / f"{authorization_id}.json"
    if consumed.exists():
        return block("narration_authorization_replayed")
    validation_record = state_root.resolve() / "validation_records" / f"{request_id}.json"
    if validation_record.exists():
        return blocked_result("request_id_replayed")
    result = ready_result()
    atomic_json(consumed, sanitize_value({
        "schema_version": "1.0", "narration_authorization_id": authorization_id,
        "request_id": request_id, "state": READY, "single_use_consumed": True,
        "provider_invoked": False, "network_invoked": False,
        "audio_file_created": False, "real_production_enabled": False,
    }))
    atomic_json(validation_record, sanitize_value({
        "schema_version": "1.0", "request_id": request_id,
        "narration_authorization_id": authorization_id, "result": result,
        "fixture_only": True, "provider_invoked": False,
        "network_invoked": False, "audio_file_created": False,
        "real_production_enabled": False,
    }))
    return result
