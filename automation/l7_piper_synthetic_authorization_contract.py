"""Offline-only L7 fake authorization contract for a future L8 design.

The validator accepts in-memory fake fixture objects only. It cannot create,
consume, persist, execute, or transport an authorization and has no runtime,
writer, process, network, provider, registry, or narration dependency.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PureWindowsPath
from typing import Literal


SCHEMA_VERSION = "cold_truth.l7a.piper_fake_authorization_fixture.v1"
SYNTHETIC_AUTHORIZATION_PURPOSE = "synthetic_local_connectivity_test"
REAL_NARRATION_GUARD = (
    "outside_l7a_requires_c3_approved_script_state_and_c4_approval_chain"
)
ROUTE_ID = "local_piper_1_4_2_en_us_ljspeech_high"
PIPER_VERSION = "1.4.2"
MODEL_ID = "en_US-ljspeech-high"
MODEL_SHA256 = (
    "5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a"
)
CONFIG_SHA256 = (
    "7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14"
)
EXECUTION_PROVIDER = "CPUExecutionProvider"
OUTPUT_FORMAT = "wav"
MAXIMUM_TEXT_CHARACTERS = 160
MAXIMUM_RUNTIME_PROCESS_COUNT = 1
MAXIMUM_SYNTHESIS_ATTEMPT_COUNT = 1
MAXIMUM_OUTPUT_FILE_COUNT = 1
MAXIMUM_OUTPUT_WRITE_COUNT = 1
MAXIMUM_RETRY_COUNT = 0
MAXIMUM_FALLBACK_COUNT = 0
MAXIMUM_VOICE_COUNT = 1
ALLOWED_VOICE_IDS = [MODEL_ID]

FAKE_HUMAN_AUTHORIZATION_MARKER = (
    "L7_FAKE_HUMAN_AUTHORIZATION_SCHEMA_MARKER_ONLY"
)
FAKE_TEXT_SHA256 = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)
FAKE_VALIDATION_INSTANT = datetime(2026, 7, 13, tzinfo=timezone.utc)
APPROVED_FUTURE_TEST_ROOT = (
    r"C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests"
)
EXPECTED_TARGET_DIRECTORY_NAME = "l8_piper_synthetic_test_l7_fake_0001"
EXPECTED_OUTPUT_FILENAME = "l8_piper_synthetic_test.wav"

SAFE_OUTCOMES = (
    "AUTHORIZED_NOT_EXECUTED",
    "VALIDATION_REJECTED",
    "EXECUTION_FAILED_CLOSED",
    "ONE_SYNTHETIC_OUTPUT_CREATED",
    "OUTPUT_CONTAINMENT_FAILURE",
    "AUTHORIZATION_CONSUMED",
)

SafeOutcome = Literal[
    "AUTHORIZED_NOT_EXECUTED",
    "VALIDATION_REJECTED",
    "EXECUTION_FAILED_CLOSED",
    "ONE_SYNTHETIC_OUTPUT_CREATED",
    "OUTPUT_CONTAINMENT_FAILURE",
    "AUTHORIZATION_CONSUMED",
]

SafeErrorCategory = Literal[
    "invalid_fixture_type",
    "raw_text_forbidden",
    "unknown_or_missing_fields",
    "fixture_boundary_violation",
    "authorization_purpose_forbidden",
    "approval_linkage_forbidden",
    "authorization_id_invalid",
    "authorization_id_reusable",
    "expiration_invalid",
    "locked_identity_mismatch",
    "content_boundary_violation",
    "text_hash_invalid",
    "text_limit_invalid",
    "operation_limit_violation",
    "voice_limit_violation",
    "output_contract_violation",
    "output_state_violation",
    "prohibited_capability_requested",
]

PROHIBITED_CONTENT_FIELDS = (
    "real_case",
    "research",
    "script",
    "channel",
    "victim",
    "suspect",
    "personal",
    "biographical",
    "production",
    "narratively_meaningful",
)

PROHIBITED_CAPABILITY_FIELDS = (
    "queueing",
    "batching",
    "auto_chunking",
    "multi_speaker",
    "voice_cloning",
    "effects",
    "phonemization_override",
    "speed_override",
    "arbitrary_cli_arguments",
    "subprocess_expansion",
    "server_mode",
    "network",
    "mcp",
    "cloud_provider",
    "copy",
    "rename",
    "overwrite",
    "cleanup",
    "deletion",
    "production_pipeline_advancement",
    "rendering",
    "upload",
    "scheduling",
    "publishing",
)

APPROVAL_LINKAGE_FIELD_NAMES = {
    "requires_c3_approved_at_execution",
    "requires_c4_approval_at_execution",
    "c3_status",
    "c3_approved_script_state",
    "c3_artifact_path",
    "c3_approval_artifact_path",
    "c3_artifact_hash",
    "c3_approval",
    "c4_artifact_path",
    "c4_approval_artifact_path",
    "c4_artifact_hash",
    "c4_approval",
    "approved_script_path",
    "approved_script_hash",
    "production_case_id",
}

RAW_TEXT_FIELD_NAMES = {
    "text",
    "raw_text",
    "narration",
    "script_text",
    "prompt",
    "phonemes",
    "tokens",
    "tensors",
}

REQUIRED_FIELDS = {
    "schema_version",
    "fixture_only",
    "executable",
    "consumable",
    "authorization_id",
    "single_use",
    "reuse_allowed",
    "authorization_consumed",
    "live_human_authorization_granted",
    "human_authorization_marker",
    "expiration_timestamp",
    "authorization_purpose",
    "synthetic_test_only",
    "non_case_text_only",
    "no_personal_data",
    "route_id",
    "piper_version",
    "model_id",
    "model_sha256",
    "config_sha256",
    "execution_provider",
    "output_format",
    "maximum_text_characters",
    "declared_text_character_count",
    "text_sha256",
    "maximum_runtime_process_count",
    "maximum_synthesis_attempt_count",
    "maximum_output_file_count",
    "maximum_output_write_count",
    "maximum_retry_count",
    "maximum_fallback_count",
    "maximum_voice_count",
    "requested_runtime_process_count",
    "requested_synthesis_attempt_count",
    "requested_output_file_count",
    "requested_output_write_count",
    "requested_retry_count",
    "requested_fallback_count",
    "requested_voice_count",
    "prior_synthesis_attempt_count",
    "allowed_voice_ids",
    "approved_output_root",
    "target_directory_name",
    "expected_output_filename",
    "exclusive_create",
    "target_output_must_not_exist",
    "target_directory_must_be_new",
    "target_directory_must_be_empty",
    "target_directory_must_not_be_link",
    "target_directory_must_not_be_reparse",
    "directory_containment_required",
    "stop_after_first_attempt",
    "target_directory_observed_state",
    "target_output_observed_state",
    "prohibited_content",
    "prohibited_capabilities",
}


@dataclass(frozen=True, slots=True)
class L7FakeValidationResult:
    outcome: SafeOutcome
    safe_error_category: SafeErrorCategory | None
    fixture_valid: bool
    executable_authorization_created: bool
    authorization_consumed: bool
    runtime_interactions: int
    writer_interactions: int
    output_artifacts: int


def _result(category: SafeErrorCategory | None) -> L7FakeValidationResult:
    valid = category is None
    return L7FakeValidationResult(
        outcome="AUTHORIZED_NOT_EXECUTED" if valid else "VALIDATION_REJECTED",
        safe_error_category=category,
        fixture_valid=valid,
        executable_authorization_created=False,
        authorization_consumed=False,
        runtime_interactions=0,
        writer_interactions=0,
        output_artifacts=0,
    )


def _valid_fake_authorization_id(value: object) -> bool:
    if type(value) is not str or not value.startswith("L7-FAKE-"):
        return False
    raw_uuid = value[len("L7-FAKE-") :]
    try:
        parsed = uuid.UUID(raw_uuid)
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == raw_uuid.lower()


def _valid_future_expiration(value: object) -> bool:
    if type(value) is not str or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed > FAKE_VALIDATION_INSTANT


def _safe_target_directory_name(value: object) -> bool:
    if type(value) is not str or not value:
        return False
    path = PureWindowsPath(value)
    return (
        not path.is_absolute()
        and len(path.parts) == 1
        and path.parts not in {(), (".",), ("..",)}
        and "/" not in value
        and "\\" not in value
        and ":" not in value
    )


class L7FakeAuthorizationValidator:
    """In-memory validator for non-executable L7 JSON fixtures only."""

    __slots__ = ("_seen_fixture_ids",)

    def __init__(self) -> None:
        self._seen_fixture_ids: set[str] = set()

    def validate_fake_fixture(self, fixture: object) -> L7FakeValidationResult:
        if type(fixture) is not dict:
            return _result("invalid_fixture_type")

        if RAW_TEXT_FIELD_NAMES.intersection(fixture):
            return _result("raw_text_forbidden")

        if APPROVAL_LINKAGE_FIELD_NAMES.intersection(fixture):
            return _result("approval_linkage_forbidden")

        fields = set(fixture)
        if fields != REQUIRED_FIELDS:
            return _result("unknown_or_missing_fields")

        if fixture["authorization_purpose"] != SYNTHETIC_AUTHORIZATION_PURPOSE:
            return _result("authorization_purpose_forbidden")

        if (
            fixture["schema_version"] != SCHEMA_VERSION
            or fixture["fixture_only"] is not True
            or fixture["executable"] is not False
            or fixture["consumable"] is not False
            or fixture["single_use"] is not True
            or fixture["reuse_allowed"] is not False
            or fixture["authorization_consumed"] is not False
            or fixture["live_human_authorization_granted"] is not False
            or fixture["human_authorization_marker"]
            != FAKE_HUMAN_AUTHORIZATION_MARKER
        ):
            return _result("fixture_boundary_violation")

        authorization_id = fixture["authorization_id"]
        if not _valid_fake_authorization_id(authorization_id):
            return _result("authorization_id_invalid")
        if authorization_id in self._seen_fixture_ids:
            return _result("authorization_id_reusable")

        if not _valid_future_expiration(fixture["expiration_timestamp"]):
            return _result("expiration_invalid")

        locked_identity = {
            "route_id": ROUTE_ID,
            "piper_version": PIPER_VERSION,
            "model_id": MODEL_ID,
            "model_sha256": MODEL_SHA256,
            "config_sha256": CONFIG_SHA256,
            "execution_provider": EXECUTION_PROVIDER,
            "output_format": OUTPUT_FORMAT,
        }
        if any(fixture[field] != value for field, value in locked_identity.items()):
            return _result("locked_identity_mismatch")

        if (
            fixture["synthetic_test_only"] is not True
            or fixture["non_case_text_only"] is not True
            or fixture["no_personal_data"] is not True
        ):
            return _result("content_boundary_violation")

        text_hash = fixture["text_sha256"]
        if (
            type(text_hash) is not str
            or re.fullmatch(r"[0-9a-f]{64}", text_hash) is None
            or text_hash != FAKE_TEXT_SHA256
        ):
            return _result("text_hash_invalid")
        if (
            type(fixture["maximum_text_characters"]) is not int
            or fixture["maximum_text_characters"] != MAXIMUM_TEXT_CHARACTERS
            or type(fixture["declared_text_character_count"]) is not int
            or not 0 < fixture["declared_text_character_count"]
            <= MAXIMUM_TEXT_CHARACTERS
        ):
            return _result("text_limit_invalid")

        maximums = {
            "maximum_runtime_process_count": MAXIMUM_RUNTIME_PROCESS_COUNT,
            "maximum_synthesis_attempt_count": MAXIMUM_SYNTHESIS_ATTEMPT_COUNT,
            "maximum_output_file_count": MAXIMUM_OUTPUT_FILE_COUNT,
            "maximum_output_write_count": MAXIMUM_OUTPUT_WRITE_COUNT,
            "maximum_retry_count": MAXIMUM_RETRY_COUNT,
            "maximum_fallback_count": MAXIMUM_FALLBACK_COUNT,
        }
        requests = {
            "requested_runtime_process_count": MAXIMUM_RUNTIME_PROCESS_COUNT,
            "requested_synthesis_attempt_count": MAXIMUM_SYNTHESIS_ATTEMPT_COUNT,
            "requested_output_file_count": MAXIMUM_OUTPUT_FILE_COUNT,
            "requested_output_write_count": MAXIMUM_OUTPUT_WRITE_COUNT,
            "requested_retry_count": MAXIMUM_RETRY_COUNT,
            "requested_fallback_count": MAXIMUM_FALLBACK_COUNT,
            "prior_synthesis_attempt_count": 0,
        }
        if any(
            type(fixture[field]) is not int or fixture[field] != value
            for field, value in {**maximums, **requests}.items()
        ):
            return _result("operation_limit_violation")

        if (
            type(fixture["maximum_voice_count"]) is not int
            or fixture["maximum_voice_count"] != MAXIMUM_VOICE_COUNT
            or type(fixture["requested_voice_count"]) is not int
            or fixture["requested_voice_count"] != MAXIMUM_VOICE_COUNT
            or type(fixture["allowed_voice_ids"]) is not list
            or fixture["allowed_voice_ids"] != ALLOWED_VOICE_IDS
        ):
            return _result("voice_limit_violation")

        if (
            fixture["approved_output_root"] != APPROVED_FUTURE_TEST_ROOT
            or fixture["target_directory_name"]
            != EXPECTED_TARGET_DIRECTORY_NAME
            or not _safe_target_directory_name(fixture["target_directory_name"])
            or fixture["expected_output_filename"] != EXPECTED_OUTPUT_FILENAME
            or fixture["exclusive_create"] is not True
            or fixture["target_output_must_not_exist"] is not True
            or fixture["target_directory_must_be_new"] is not True
            or fixture["target_directory_must_be_empty"] is not True
            or fixture["target_directory_must_not_be_link"] is not True
            or fixture["target_directory_must_not_be_reparse"] is not True
            or fixture["directory_containment_required"] is not True
            or fixture["stop_after_first_attempt"] is not True
        ):
            return _result("output_contract_violation")

        if (
            fixture["target_directory_observed_state"] != "absent"
            or fixture["target_output_observed_state"] != "absent"
        ):
            return _result("output_state_violation")

        prohibited_content = fixture["prohibited_content"]
        if (
            type(prohibited_content) is not dict
            or set(prohibited_content) != set(PROHIBITED_CONTENT_FIELDS)
            or any(prohibited_content[field] is not False for field in PROHIBITED_CONTENT_FIELDS)
        ):
            return _result("content_boundary_violation")

        prohibited_capabilities = fixture["prohibited_capabilities"]
        if (
            type(prohibited_capabilities) is not dict
            or set(prohibited_capabilities) != set(PROHIBITED_CAPABILITY_FIELDS)
            or any(
                prohibited_capabilities[field] is not False
                for field in PROHIBITED_CAPABILITY_FIELDS
            )
        ):
            return _result("prohibited_capability_requested")

        self._seen_fixture_ids.add(authorization_id)
        return _result(None)


# L7B deliberately defines only an in-memory, future L8 authorization shape.
# Nothing below creates directories, audit records, output files, or processes.
L8_EXECUTABLE_SCHEMA_VERSION = "cold_truth.l7b.l8_executable_synthetic_authorization.v1"
L8_AUTHORIZATION_ROOT = r"C:\ColdTruthLocalTools\piper-l8a-synthetic-authorizations"
L8_AUDIT_ROOT = r"C:\ColdTruthLocalTools\piper-l8a-synthetic-authorization-audit"
L8_EXECUTABLE_OUTPUT_ROOT = APPROVED_FUTURE_TEST_ROOT
L8_EXECUTABLE_OUTPUT_FILENAME = "l8_piper_synthetic_test.wav"
L8_AUTHORIZED_NOT_EXECUTED = "AUTHORIZED_NOT_EXECUTED"
L8_AUTHORIZATION_CONSUMED = "AUTHORIZATION_CONSUMED"
L8_REQUIRED_FIELDS = {
    "schema_version", "authorization_id", "single_use_nonce", "expiration_timestamp",
    "lifecycle_status", "authorization_purpose", "synthetic_test_only",
    "non_case_text_only", "no_personal_data", "route_id", "piper_version",
    "model_id", "model_sha256", "config_sha256", "execution_provider",
    "output_format", "text_sha256", "maximum_runtime_process_count",
    "maximum_session_initialization_count", "maximum_synthesis_attempt_count",
    "maximum_text_input_count", "maximum_output_file_count",
    "maximum_output_write_count", "maximum_retry_count", "maximum_fallback_count",
    "maximum_voice_count", "allowed_voice_ids", "output_root", "output_filename",
    "authorization_root", "audit_root", "exclusive_create_only",
    "output_root_must_be_absent", "target_output_must_not_exist",
    "disallow_output_mutation", "stop_after_first_attempt",
}
L8_DURABLE_AUTHORIZATION_RECORD_FIELDS = (
    L8_REQUIRED_FIELDS - {"single_use_nonce"}
) | {"nonce_fingerprint", "voice_id", "output_path"}


@dataclass(frozen=True, slots=True)
class L8ExecutableAuthorizationValidationResult:
    valid: bool
    lifecycle_status: str | None
    safe_error_category: str | None
    persisted: bool = False
    runtime_interactions: int = 0
    writer_interactions: int = 0
    output_artifacts: int = 0


def _l8_result(category: str | None) -> L8ExecutableAuthorizationValidationResult:
    return L8ExecutableAuthorizationValidationResult(
        valid=category is None,
        lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED if category is None else None,
        safe_error_category=category,
    )


def _valid_l8_authorization_id(value: object) -> bool:
    if type(value) is not str or not value.startswith("L8-SYNTHETIC-"):
        return False
    try:
        parsed = uuid.UUID(value[len("L8-SYNTHETIC-") :])
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value[len("L8-SYNTHETIC-") :].lower()


def _valid_nonce(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


class L8ExecutableSyntheticAuthorizationValidator:
    """Pure in-memory preflight validator for a future single-use L8 runner.

    It neither inspects the fixed roots nor writes an authorization or audit record.
    A future runner is responsible for exclusive creation only after this preflight.
    """

    __slots__ = ("_seen_authorization_ids", "_seen_nonces")

    def __init__(self) -> None:
        self._seen_authorization_ids: set[str] = set()
        self._seen_nonces: set[str] = set()

    def validate_l8_executable_synthetic_authorization(
        self, authorization: object
    ) -> L8ExecutableAuthorizationValidationResult:
        if type(authorization) is not dict:
            return _l8_result("invalid_authorization_type")
        if RAW_TEXT_FIELD_NAMES.intersection(authorization):
            return _l8_result("raw_text_forbidden")
        if APPROVAL_LINKAGE_FIELD_NAMES.intersection(authorization):
            return _l8_result("approval_linkage_forbidden")
        if set(authorization) != L8_REQUIRED_FIELDS:
            return _l8_result("unknown_or_missing_fields")
        if authorization["schema_version"] != L8_EXECUTABLE_SCHEMA_VERSION:
            return _l8_result("schema_version_invalid")
        if authorization["authorization_purpose"] != SYNTHETIC_AUTHORIZATION_PURPOSE:
            return _l8_result("authorization_purpose_forbidden")
        if authorization["lifecycle_status"] != L8_AUTHORIZED_NOT_EXECUTED:
            return _l8_result("lifecycle_invalid")
        authorization_id = authorization["authorization_id"]
        nonce = authorization["single_use_nonce"]
        if not _valid_l8_authorization_id(authorization_id):
            return _l8_result("authorization_id_invalid")
        if not _valid_nonce(nonce):
            return _l8_result("nonce_invalid")
        if authorization_id in self._seen_authorization_ids or nonce in self._seen_nonces:
            return _l8_result("authorization_reused")
        if not _valid_future_expiration(authorization["expiration_timestamp"]):
            return _l8_result("expiration_invalid")
        identity = {
            "route_id": ROUTE_ID, "piper_version": PIPER_VERSION,
            "model_id": MODEL_ID, "model_sha256": MODEL_SHA256,
            "config_sha256": CONFIG_SHA256,
            "execution_provider": EXECUTION_PROVIDER, "output_format": OUTPUT_FORMAT,
        }
        if any(authorization[field] != value for field, value in identity.items()):
            return _l8_result("locked_identity_mismatch")
        if any(authorization[field] is not True for field in (
            "synthetic_test_only", "non_case_text_only", "no_personal_data",
        )):
            return _l8_result("content_boundary_violation")
        if not _valid_nonce(authorization["text_sha256"]):
            return _l8_result("text_hash_invalid")
        limits = {
            "maximum_runtime_process_count": 1,
            "maximum_session_initialization_count": 1,
            "maximum_synthesis_attempt_count": 1,
            "maximum_text_input_count": 1,
            "maximum_output_file_count": 1,
            "maximum_output_write_count": 1,
            "maximum_retry_count": 0,
            "maximum_fallback_count": 0,
            "maximum_voice_count": 1,
        }
        if any(type(authorization[field]) is not int or authorization[field] != value for field, value in limits.items()):
            return _l8_result("operation_limit_violation")
        if authorization["allowed_voice_ids"] != [MODEL_ID]:
            return _l8_result("voice_limit_violation")
        if (
            authorization["output_root"] != L8_EXECUTABLE_OUTPUT_ROOT
            or authorization["output_filename"] != L8_EXECUTABLE_OUTPUT_FILENAME
            or authorization["authorization_root"] != L8_AUTHORIZATION_ROOT
            or authorization["audit_root"] != L8_AUDIT_ROOT
        ):
            return _l8_result("output_contract_violation")
        if any(authorization[field] is not True for field in (
            "exclusive_create_only", "output_root_must_be_absent",
            "target_output_must_not_exist", "disallow_output_mutation",
            "stop_after_first_attempt",
        )):
            return _l8_result("output_contract_violation")
        self._seen_authorization_ids.add(authorization_id)
        self._seen_nonces.add(nonce)
        return _l8_result(None)


def validate_l8_durable_authorization_record(
    record: object, *, expected_lifecycle: str
) -> L8ExecutableAuthorizationValidationResult:
    """Purely revalidate one nonce-fingerprint-only durable lifecycle record."""
    if (
        type(expected_lifecycle) is not str
        or expected_lifecycle
        not in (L8_AUTHORIZED_NOT_EXECUTED, L8_AUTHORIZATION_CONSUMED)
    ):
        return _l8_result("lifecycle_invalid")
    if type(record) is not dict:
        return _l8_result("invalid_authorization_type")
    if RAW_TEXT_FIELD_NAMES.intersection(record):
        return _l8_result("raw_text_forbidden")
    if APPROVAL_LINKAGE_FIELD_NAMES.intersection(record):
        return _l8_result("approval_linkage_forbidden")
    if set(record) != L8_DURABLE_AUTHORIZATION_RECORD_FIELDS:
        return _l8_result("unknown_or_missing_fields")
    if not _valid_l8_authorization_id(record["authorization_id"]):
        return _l8_result("authorization_id_invalid")
    if not _valid_nonce(record["nonce_fingerprint"]):
        return _l8_result("nonce_fingerprint_invalid")
    if not _valid_future_expiration(record["expiration_timestamp"]):
        return _l8_result("expiration_invalid")
    if not _valid_nonce(record["text_sha256"]):
        return _l8_result("text_hash_invalid")
    expected = {
        "schema_version": L8_EXECUTABLE_SCHEMA_VERSION,
        "authorization_purpose": SYNTHETIC_AUTHORIZATION_PURPOSE,
        "lifecycle_status": expected_lifecycle,
        "synthetic_test_only": True,
        "non_case_text_only": True,
        "no_personal_data": True,
        "route_id": ROUTE_ID,
        "piper_version": PIPER_VERSION,
        "model_id": MODEL_ID,
        "model_sha256": MODEL_SHA256,
        "config_sha256": CONFIG_SHA256,
        "execution_provider": EXECUTION_PROVIDER,
        "voice_id": MODEL_ID,
        "output_format": OUTPUT_FORMAT,
        "output_path": str(
            PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
            / L8_EXECUTABLE_OUTPUT_FILENAME
        ),
        "maximum_runtime_process_count": 1,
        "maximum_session_initialization_count": 1,
        "maximum_text_input_count": 1,
        "maximum_synthesis_attempt_count": 1,
        "maximum_output_file_count": 1,
        "maximum_output_write_count": 1,
        "maximum_retry_count": 0,
        "maximum_fallback_count": 0,
        "maximum_voice_count": 1,
        "allowed_voice_ids": [MODEL_ID],
        "output_root": L8_EXECUTABLE_OUTPUT_ROOT,
        "output_filename": L8_EXECUTABLE_OUTPUT_FILENAME,
        "authorization_root": L8_AUTHORIZATION_ROOT,
        "audit_root": L8_AUDIT_ROOT,
        "exclusive_create_only": True,
        "output_root_must_be_absent": True,
        "target_output_must_not_exist": True,
        "disallow_output_mutation": True,
        "stop_after_first_attempt": True,
    }
    if any(
        type(record[field]) is not type(value) or record[field] != value
        for field, value in expected.items()
    ):
        return _l8_result("durable_authorization_binding_invalid")
    return L8ExecutableAuthorizationValidationResult(
        valid=True,
        lifecycle_status=expected_lifecycle,
        safe_error_category=None,
    )


def create_l8_executable_synthetic_authorization(
    *, text_sha256: str, expiration_timestamp: str, preflight_validated: bool,
    authorization_id: str, single_use_nonce: str,
) -> dict[str, object]:
    """Return an unpersisted future-runner candidate after its preflight signal.

    This factory does not create a live authorization; exclusive persistence and
    audit creation belong to the future L8 runner and are intentionally absent.
    """
    if preflight_validated is not True:
        raise ValueError("L8 authorization factory requires completed preflight")
    return {
        "schema_version": L8_EXECUTABLE_SCHEMA_VERSION,
        "authorization_id": authorization_id,
        "single_use_nonce": single_use_nonce,
        "expiration_timestamp": expiration_timestamp,
        "lifecycle_status": L8_AUTHORIZED_NOT_EXECUTED,
        "authorization_purpose": SYNTHETIC_AUTHORIZATION_PURPOSE,
        "synthetic_test_only": True, "non_case_text_only": True, "no_personal_data": True,
        "route_id": ROUTE_ID, "piper_version": PIPER_VERSION, "model_id": MODEL_ID,
        "model_sha256": MODEL_SHA256, "config_sha256": CONFIG_SHA256,
        "execution_provider": EXECUTION_PROVIDER, "output_format": OUTPUT_FORMAT,
        "text_sha256": text_sha256,
        "maximum_runtime_process_count": 1, "maximum_session_initialization_count": 1,
        "maximum_synthesis_attempt_count": 1, "maximum_text_input_count": 1,
        "maximum_output_file_count": 1, "maximum_output_write_count": 1,
        "maximum_retry_count": 0, "maximum_fallback_count": 0,
        "maximum_voice_count": 1, "allowed_voice_ids": [MODEL_ID],
        "output_root": L8_EXECUTABLE_OUTPUT_ROOT,
        "output_filename": L8_EXECUTABLE_OUTPUT_FILENAME,
        "authorization_root": L8_AUTHORIZATION_ROOT, "audit_root": L8_AUDIT_ROOT,
        "exclusive_create_only": True, "output_root_must_be_absent": True,
        "target_output_must_not_exist": True, "disallow_output_mutation": True,
        "stop_after_first_attempt": True,
    }
