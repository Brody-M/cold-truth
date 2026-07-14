"""Non-executable, in-memory validator for the future C8 authorization shape."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from json_schema_subset import SchemaSubsetError, validate
from c8d_live_readiness_contract import OUTPUT_PATH_BASIS, resolve_canonical_c8_output


PASSED = "C8A_STRUCTURAL_VALIDATION_PASSED_NON_EXECUTABLE"
BLOCKED = "C8A_STRUCTURAL_VALIDATION_BLOCKED"
MAX_LIFETIME_SECONDS = 900
FORBIDDEN_TEXT = re.compile(
    r"(?i)(url|endpoint|provider|service|api[ _-]?key|token|authorization[ _-]?header|"
    r"voice[ _-]?id|secret|credential|environment|config|command|exec|shell)"
)


class InMemoryReplayRegistry:
    """Test-only registry; it has no persistence or execution behavior."""

    def __init__(self) -> None:
        self._records: dict[str, str] = {}

    def contains(self, authorization_id: str) -> bool:
        return authorization_id in self._records

    def remember(self, authorization_id: str, record_sha256: str) -> None:
        self._records[authorization_id] = record_sha256


def canonical_sha256(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _result(state: str, reason: str) -> dict[str, Any]:
    return {
        "state": state,
        "safe_reason_code": reason,
        "structurally_valid": state == PASSED,
        "authorization_artifact_created": False,
        "execution_authorized": False,
        "provider_invoked": False,
        "network_invoked": False,
        "audio_file_created": False,
        "publishing_enabled": False,
        "real_production_enabled": False,
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_hypothetical_record(
    *, record: dict[str, Any], schema: dict[str, Any],
    expected_bindings: dict[str, str], future_c8_root: Path,
    disposable_output_root: Path, replay_registry: InMemoryReplayRegistry,
) -> dict[str, Any]:
    allowed_output_root = future_c8_root.resolve() / "disposable_output"
    if disposable_output_root.resolve() != allowed_output_root.resolve():
        return _result(BLOCKED, "disposable_output_root_escape")
    try:
        validate(record, schema)
    except SchemaSubsetError:
        return _result(BLOCKED, "strict_schema_validation_failed")
    for field, expected in expected_bindings.items():
        if record.get(field) != expected:
            return _result(BLOCKED, f"binding_mismatch_{field}")
    if FORBIDDEN_TEXT.search(record["authorization_id"]):
        return _result(BLOCKED, "forbidden_authorization_identifier")
    relative_text = record["authorized_output_relative_path"]
    if FORBIDDEN_TEXT.search(relative_text):
        return _result(BLOCKED, "forbidden_output_reference")
    if record.get("output_path_basis") != OUTPUT_PATH_BASIS:
        return _result(BLOCKED, "authorized_output_path_basis_mismatch")
    try:
        resolve_canonical_c8_output(
            workspace_root=future_c8_root.resolve().parents[4],
            authorization_relative_path=relative_text,
            require_absent=True
        )
    except FileExistsError:
        return _result(BLOCKED, "authorized_output_target_already_exists")
    except ValueError:
        return _result(BLOCKED, "authorized_output_path_escape")
    if record["authorized_output_path_sha256"] != text_sha256(relative_text):
        return _result(BLOCKED, "authorized_output_path_hash_mismatch")
    output_directory_relative = record["authorized_output_directory_relative_path"]
    if record["authorized_output_directory_path_sha256"] != text_sha256(output_directory_relative):
        return _result(BLOCKED, "authorized_output_directory_path_hash_mismatch")
    workspace_root = future_c8_root.resolve().parents[4]
    output_directory = (workspace_root / "automation" / output_directory_relative).resolve()
    if output_directory != allowed_output_root.resolve():
        return _result(BLOCKED, "authorized_output_directory_not_exact")
    if not output_directory.is_dir() or output_directory.is_symlink():
        return _result(BLOCKED, "authorized_output_directory_not_regular_directory")
    try:
        issued = datetime.strptime(record["issued_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
        expires = datetime.strptime(record["expires_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return _result(BLOCKED, "invalid_authorization_timestamp")
    lifetime = (expires - issued).total_seconds()
    if lifetime <= 0 or lifetime > MAX_LIFETIME_SECONDS:
        return _result(BLOCKED, "invalid_authorization_lifetime")
    authorization_id = record["authorization_id"]
    if replay_registry.contains(authorization_id):
        return _result(BLOCKED, "authorization_id_replayed")
    replay_registry.remember(authorization_id, canonical_sha256(record))
    return _result(PASSED, "hypothetical_shape_valid_non_executable")
