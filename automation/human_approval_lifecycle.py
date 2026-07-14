"""Fail-closed, single-use lifecycle for Cold Truth dry-run human approvals."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = "cold_truth.human_approval.v1"
APPROVAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")


class ApprovalLifecycleError(RuntimeError):
    """The candidate approval is malformed, stale, unsafe, or already used."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ApprovalLifecycleError(f"Approval field {field} is required")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ApprovalLifecycleError(f"Approval field {field} must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ApprovalLifecycleError(f"Approval field {field} must be UTC")
    return parsed


def _read_candidate(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ApprovalLifecycleError(f"Approval does not exist: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApprovalLifecycleError(f"Approval is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ApprovalLifecycleError("Approval must be a JSON object")
    return value, raw


def _atomic_exclusive_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ApprovalLifecycleError(f"Approval was already consumed: {payload['approval_id']}") from exc


def validate_and_consume(
    approval_path: Path,
    consumption_root: Path,
    *,
    expected: dict[str, Any],
    clock: Callable[[], datetime] = utc_now,
) -> dict[str, Any]:
    """Validate every binding, then create exactly one safe consumption record."""
    approval_path = approval_path.resolve()
    consumption_root = consumption_root.resolve()
    approval, raw = _read_candidate(approval_path)

    required_exact = {
        "schema_version": SCHEMA_VERSION,
        "purpose": expected["purpose"],
        "run_id": expected["run_id"],
        "case_id": expected["case_id"],
        "episode_id": expected["episode_id"],
        "checkpoint": expected["checkpoint"],
        "reviewer_role": "human_owner",
        "human_approved": True,
        "status": "active",
        "single_use": True,
        "consumed": False,
        "consumption_count": 0,
        "only_allowed_next_state": expected["only_allowed_next_state"],
        "publishing_enabled": False,
        "real_production_enabled": False,
    }
    additional_exact = expected.get("required_exact", {})
    if not isinstance(additional_exact, dict):
        raise ApprovalLifecycleError("Expected exact approval requirements must be an object")
    required_exact.update(additional_exact)
    for field, value in required_exact.items():
        if approval.get(field) != value:
            raise ApprovalLifecycleError(f"Approval field {field} must equal {value!r}")

    approval_id = approval.get("approval_id")
    if not isinstance(approval_id, str) or not APPROVAL_ID_PATTERN.fullmatch(approval_id):
        raise ApprovalLifecycleError("Approval field approval_id has an invalid format")
    for field in ("approved_by", "reason"):
        if not isinstance(approval.get(field), str) or not approval[field].strip():
            raise ApprovalLifecycleError(f"Approval field {field} is required")

    issued_at = _parse_utc(approval.get("issued_at_utc"), "issued_at_utc")
    expires_at = _parse_utc(approval.get("expires_at_utc"), "expires_at_utc")
    now = clock()
    if now.tzinfo is None:
        raise ApprovalLifecycleError("Approval clock must be timezone-aware")
    now = now.astimezone(timezone.utc)
    if issued_at > now:
        raise ApprovalLifecycleError("Approval is not active yet")
    if expires_at <= issued_at:
        raise ApprovalLifecycleError("Approval expiry must be after issuance")
    if now >= expires_at:
        raise ApprovalLifecycleError("Approval has expired")

    bound_hashes = expected.get("bound_hashes")
    if not isinstance(bound_hashes, dict) or not bound_hashes:
        raise ApprovalLifecycleError("Expected approval bindings are missing")
    for field, digest in bound_hashes.items():
        if approval.get(field) != digest:
            raise ApprovalLifecycleError(f"Approval hash mismatch for {field}")

    record_path = (consumption_root / f"{approval_id}.json").resolve()
    try:
        record_path.relative_to(consumption_root)
    except ValueError as exc:
        raise ApprovalLifecycleError("Approval consumption path escapes its root") from exc

    consumed_at = now.isoformat().replace("+00:00", "Z")
    safe_record = {
        "schema_version": "cold_truth.human_approval_consumption.v1",
        "approval_id": approval_id,
        "purpose": approval["purpose"],
        "run_id": approval["run_id"],
        "case_id": approval["case_id"],
        "episode_id": approval["episode_id"],
        "checkpoint": approval["checkpoint"],
        "reviewer_role": approval["reviewer_role"],
        "source_approval_sha256": hashlib.sha256(raw).hexdigest(),
        "bound_hashes": {field: bound_hashes[field] for field in sorted(bound_hashes)},
        "status": "consumed",
        "single_use": True,
        "consumed": True,
        "consumption_count": 1,
        "consumed_at_utc": consumed_at,
        "only_allowed_next_state": approval["only_allowed_next_state"],
        "publishing_enabled": False,
        "real_production_enabled": False,
    }
    _atomic_exclusive_json(record_path, safe_record)
    return {
        **approval,
        "status": "consumed",
        "consumed": True,
        "consumption_count": 1,
        "consumed_at_utc": consumed_at,
        "consumption_record_path": str(record_path),
        "source_approval_sha256": safe_record["source_approval_sha256"],
    }
