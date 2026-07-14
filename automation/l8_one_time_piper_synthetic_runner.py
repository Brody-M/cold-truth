"""Bounded future L8 synthetic Piper runner.

This module contains coordination logic only. It imports no Piper/ONNX/TTS,
process, environment, network, provider, media, or production dependency. All
operational boundaries are explicit injections and are exercised with fakes in
L7C. The single public execution entry point accepts no raw text or path.
"""
from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PureWindowsPath
from typing import Literal

from l7_piper_synthetic_authorization_contract import (
    CONFIG_SHA256,
    EXECUTION_PROVIDER,
    L8_AUTHORIZATION_CONSUMED,
    L8_AUTHORIZED_NOT_EXECUTED,
    L8_REQUIRED_FIELDS,
    L8_EXECUTABLE_OUTPUT_FILENAME,
    L8_EXECUTABLE_OUTPUT_ROOT,
    L8_EXECUTABLE_SCHEMA_VERSION,
    L8ExecutableSyntheticAuthorizationValidator,
    MODEL_ID,
    MODEL_SHA256,
    OUTPUT_FORMAT,
    PIPER_VERSION,
    ROUTE_ID,
    validate_l8_durable_authorization_record,
)


_MAXIMUM_TEXT_CHARACTERS = 160
_claimed_authorization_ids: set[str] = set()
_claimed_nonce_fingerprints: set[str] = set()
_process_execution_claimed = False
_sealed_execution_claimed = False
_SAFE_CHILD_ERROR_CATEGORIES = {
    "approval_linkage_forbidden",
    "authorization_expired",
    "authorization_expired_before_attempt",
    "authorization_id_invalid",
    "clock_failed",
    "created_root_invalid",
    "created_root_unsafe",
    "durable_authorization_binding_invalid",
    "durable_authorization_invalid",
    "ephemeral_text_envelope_invalid",
    "ephemeral_text_invalid",
    "ephemeral_text_supplier_failed",
    "exclusive_write_failed",
    "expiration_invalid",
    "injected_interface_invalid",
    "invalid_authorization_type",
    "lifecycle_invalid",
    "non_synthetic_text_rejected",
    "nonce_fingerprint_invalid",
    "output_preflight_failed",
    "output_preflight_invalid",
    "output_preflight_rejected",
    "output_root_create_failed",
    "raw_text_forbidden",
    "runtime_factory_failed",
    "runtime_identity_inspection_failed",
    "runtime_identity_mismatch",
    "runtime_interface_invalid",
    "runtime_preflight_failed",
    "runtime_preflight_identity_mismatch",
    "sealed_bootstrap_failed",
    "sealed_launch_failed",
    "sealed_runner_already_used",
    "session_initialization_failed",
    "session_interface_invalid",
    "synthesis_failed",
    "synthesis_result_invalid",
    "text_hash_invalid",
    "text_hash_mismatch",
    "unexpected_execution_failure",
    "unknown_or_missing_fields",
    "writer_result_invalid",
}
_SAFE_CHILD_UNKNOWN_OUTPUT_CATEGORIES = {
    "exclusive_write_failed",
    "unexpected_execution_failure",
    "writer_result_invalid",
}

# Canonical source for a future separately authorized one-process sealed launch.
# The prior ephemeral launch used double-quoted Python literals; Windows native
# argument serialization removed those quotes before Python parsed the payload.
# This source intentionally uses only single-quoted literals and contains no raw
# synthetic text, authorization identifier, nonce, path override, or option.
_SEALED_INTERPRETER_ENTRYPOINT_SOURCE = """from dataclasses import asdict
import json

from l8_one_time_piper_synthetic_runner import _execute_inside_sealed_interpreter
from l8_local_dependency_adapters import CanonicalExclusiveWavWriter, CanonicalL8DurableAuthorizationReader, CanonicalL8FileSystemBoundary, FixedEphemeralSyntheticTextSupplier, LockedLocalPiperRuntimeFactory, UtcL8Clock

try:
    durable_authorization_record = CanonicalL8DurableAuthorizationReader().read_authorization_once()
    result = _execute_inside_sealed_interpreter(
        durable_authorization_record=durable_authorization_record,
        runtime_factory=LockedLocalPiperRuntimeFactory(),
        exclusive_wav_writer=CanonicalExclusiveWavWriter(),
        clock=UtcL8Clock(),
        file_system_boundary=CanonicalL8FileSystemBoundary(),
        ephemeral_test_text_supplier=FixedEphemeralSyntheticTextSupplier(),
    )
    summary = asdict(result)
    summary['interface_binding'] = 'succeeded'
except Exception:
    summary = {
        'outcome': 'EXECUTION_FAILED_CLOSED',
        'safe_error_category': 'sealed_bootstrap_failed',
        'interface_binding': 'failed_before_runner_result',
        'authorization_id': None,
        'nonce_fingerprint': None,
        'lifecycle_status': 'AUTHORIZED_NOT_EXECUTED',
        'sealed_interpreter_process_count': 1,
        'runtime_process_count': 0,
        'session_initialization_count': 0,
        'text_input_count': 0,
        'synthesis_attempt_count': 0,
        'output_file_count': 0,
        'output_write_count': 0,
        'output_state_unknown': False,
        'retry_count': 0,
        'fallback_count': 0,
        'output_path': None,
        'output_byte_count': None,
        'output_sha256': None,
    }
print(json.dumps(summary, sort_keys=True))
"""

RunnerOutcome = Literal["ONE_SYNTHETIC_OUTPUT_CREATED", "EXECUTION_FAILED_CLOSED"]


@dataclass(frozen=True, slots=True)
class L8SyntheticRunnerResult:
    outcome: RunnerOutcome
    safe_error_category: str | None
    authorization_id: str | None
    nonce_fingerprint: str | None
    lifecycle_status: str | None
    sealed_interpreter_process_count: int
    runtime_process_count: int
    session_initialization_count: int
    text_input_count: int
    synthesis_attempt_count: int
    output_file_count: int
    output_write_count: int
    output_state_unknown: bool
    retry_count: int
    fallback_count: int
    output_path: str | None
    output_byte_count: int | None
    output_sha256: str | None


class _RunnerFailure(Exception):
    __slots__ = ("category",)

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def _validate_sealed_interpreter_entrypoint_source(candidate: object) -> str:
    """Validate the exact inert future source without compiling to bytecode."""
    if type(candidate) is not str or candidate != _SEALED_INTERPRETER_ENTRYPOINT_SOURCE:
        raise ValueError("sealed_entrypoint_source_mismatch")
    if '"' in candidate:
        raise ValueError("sealed_entrypoint_double_quote_forbidden")
    try:
        ast.parse(candidate, filename="<l8-sealed-entrypoint>", mode="exec")
    except SyntaxError:
        raise ValueError("sealed_entrypoint_parse_failure") from None
    return candidate


def _result(
    *,
    category: str | None,
    authorization_id: str | None,
    nonce_fingerprint: str | None,
    lifecycle_status: str | None,
    sealed_interpreter_process_count: int = 0,
    counts: dict[str, int] | None = None,
    output_path: str | None = None,
    output_byte_count: int | None = None,
    output_sha256: str | None = None,
    output_state_unknown: bool = False,
) -> L8SyntheticRunnerResult:
    current = counts or {}
    return L8SyntheticRunnerResult(
        outcome=(
            "ONE_SYNTHETIC_OUTPUT_CREATED"
            if category is None
            else "EXECUTION_FAILED_CLOSED"
        ),
        safe_error_category=category,
        authorization_id=authorization_id,
        nonce_fingerprint=nonce_fingerprint,
        lifecycle_status=lifecycle_status,
        sealed_interpreter_process_count=sealed_interpreter_process_count,
        runtime_process_count=current.get("runtime_process", 0),
        session_initialization_count=current.get("session_initialization", 0),
        text_input_count=current.get("text_input", 0),
        synthesis_attempt_count=current.get("synthesis_attempt", 0),
        output_file_count=current.get("output_file", 0),
        output_write_count=current.get("output_write", 0),
        output_state_unknown=output_state_unknown,
        retry_count=0,
        fallback_count=0,
        output_path=output_path,
        output_byte_count=output_byte_count,
        output_sha256=output_sha256,
    )


def _has_exact_interface(value: object, method_names: tuple[str, ...]) -> bool:
    if value is None:
        return False
    declared = {
        name
        for name, member in vars(type(value)).items()
        if not name.startswith("_") and callable(member)
    }
    return declared == set(method_names)


def _parse_expiration(value: object) -> datetime | None:
    if type(value) is not str or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _safe_call(callable_value, category: str, *args):
    try:
        return callable_value(*args)
    except Exception as exc:
        raise _RunnerFailure(category) from None


def _validate_output_preflight(value: object) -> None:
    required = {
        "root_absent",
        "target_absent",
        "canonical_containment",
        "root_would_be_regular",
        "non_link",
        "non_reparse",
        "exclusive_create_supported",
    }
    if type(value) is not dict or set(value) != required:
        raise _RunnerFailure("output_preflight_invalid")
    if any(value[field] is not True for field in required):
        raise _RunnerFailure("output_preflight_rejected")


def _validate_created_root(value: object) -> None:
    required = {
        "created_exclusively",
        "empty",
        "canonical_containment",
        "regular_directory",
        "non_link",
        "non_reparse",
    }
    if type(value) is not dict or set(value) != required:
        raise _RunnerFailure("created_root_invalid")
    if any(value[field] is not True for field in required):
        raise _RunnerFailure("created_root_unsafe")


def _safe_authorization_record(
    authorization: dict[str, object], lifecycle_status: str
) -> dict[str, object]:
    safe = {
        field: authorization[field]
        for field in L8_REQUIRED_FIELDS
        if field != "single_use_nonce"
    }
    safe["allowed_voice_ids"] = list(authorization["allowed_voice_ids"])
    safe["nonce_fingerprint"] = hashlib.sha256(
        str(authorization["single_use_nonce"]).encode("ascii")
    ).hexdigest()
    safe["lifecycle_status"] = lifecycle_status
    safe["voice_id"] = MODEL_ID
    safe["output_path"] = str(
        PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
        / L8_EXECUTABLE_OUTPUT_FILENAME
    )
    return safe


def _safe_audit_payload(
    durable_authorization_record: dict[str, object],
    outcome: str,
    counts: dict[str, int],
    failure_category: str | None,
    output_path: str | None,
    output_byte_count: int | None,
    output_sha256: str | None,
    output_state_unknown: bool = False,
) -> dict[str, object]:
    return {
        "audit_event_id": f'{durable_authorization_record["authorization_id"]}:FINAL',
        "authorization_id": durable_authorization_record["authorization_id"],
        "nonce_fingerprint": durable_authorization_record["nonce_fingerprint"],
        "lifecycle_status": L8_AUTHORIZATION_CONSUMED,
        "attempt_outcome": outcome,
        "failure_category": failure_category,
        "route_id": ROUTE_ID,
        "piper_version": PIPER_VERSION,
        "model_id": MODEL_ID,
        "model_sha256": MODEL_SHA256,
        "config_sha256": CONFIG_SHA256,
        "execution_provider": EXECUTION_PROVIDER,
        "voice_id": MODEL_ID,
        "output_format": OUTPUT_FORMAT,
        "output_path": output_path,
        "output_byte_count": output_byte_count,
        "output_sha256": output_sha256,
        "output_state_unknown": output_state_unknown,
        "runtime_process_count": counts["runtime_process"],
        "session_initialization_count": counts["session_initialization"],
        "text_input_count": counts["text_input"],
        "synthesis_attempt_count": counts["synthesis_attempt"],
        "output_file_count": counts["output_file"],
        "output_write_count": counts["output_write"],
        "retry_count": 0,
        "fallback_count": 0,
    }


def _counts_from_result(result: L8SyntheticRunnerResult) -> dict[str, int]:
    return {
        "runtime_process": result.runtime_process_count,
        "session_initialization": result.session_initialization_count,
        "text_input": result.text_input_count,
        "synthesis_attempt": result.synthesis_attempt_count,
        "output_file": result.output_file_count,
        "output_write": result.output_write_count,
    }


def _unknown_child_result(
    authorization_record: dict[str, object], category: str
) -> L8SyntheticRunnerResult:
    """Return conservative one-shot bounds when no trustworthy child result exists."""
    return _result(
        category=category,
        authorization_id=str(authorization_record["authorization_id"]),
        nonce_fingerprint=str(authorization_record["nonce_fingerprint"]),
        lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
        sealed_interpreter_process_count=1,
        counts={
            "runtime_process": 1,
            "session_initialization": 1,
            "text_input": 1,
            "synthesis_attempt": 1,
            "output_file": 1,
            "output_write": 1,
        },
        output_path=str(
            PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
            / L8_EXECUTABLE_OUTPUT_FILENAME
        ),
        output_state_unknown=True,
    )


def _is_lower_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_child_result(
    value: object, authorization_record: dict[str, object]
) -> L8SyntheticRunnerResult | None:
    interface_binding: str | None = None
    if type(value) is dict:
        expected_fields = set(L8SyntheticRunnerResult.__slots__)
        candidate_binding = value.get("interface_binding")
        if (
            set(value) != expected_fields | {"interface_binding"}
            or type(candidate_binding) is not str
            or candidate_binding
            not in ("succeeded", "failed_before_runner_result")
        ):
            return None
        interface_binding = candidate_binding
        try:
            value = L8SyntheticRunnerResult(
                **{field: value[field] for field in L8SyntheticRunnerResult.__slots__}
            )
        except (KeyError, TypeError, ValueError):
            return None
    if type(value) is not L8SyntheticRunnerResult:
        return None
    if (
        value.authorization_id is None
        and value.nonce_fingerprint is None
        and value.outcome == "EXECUTION_FAILED_CLOSED"
        and value.safe_error_category == "sealed_bootstrap_failed"
        and value.lifecycle_status == L8_AUTHORIZED_NOT_EXECUTED
        and type(value.sealed_interpreter_process_count) is int
        and value.sealed_interpreter_process_count == 1
        and all(
            type(count) is int and count == 0
            for count in _counts_from_result(value).values()
        )
        and value.output_state_unknown is False
        and type(value.retry_count) is int
        and value.retry_count == 0
        and type(value.fallback_count) is int
        and value.fallback_count == 0
        and value.output_path is None
        and value.output_byte_count is None
        and value.output_sha256 is None
    ):
        if interface_binding not in (None, "failed_before_runner_result"):
            return None
        value = _result(
            category="sealed_bootstrap_failed",
            authorization_id=str(authorization_record["authorization_id"]),
            nonce_fingerprint=str(authorization_record["nonce_fingerprint"]),
            lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
            sealed_interpreter_process_count=1,
        )
    elif interface_binding == "failed_before_runner_result":
        return None
    if (
        value.authorization_id != authorization_record["authorization_id"]
        or value.nonce_fingerprint != authorization_record["nonce_fingerprint"]
        or value.lifecycle_status != L8_AUTHORIZED_NOT_EXECUTED
        or type(value.output_state_unknown) is not bool
        or type(value.sealed_interpreter_process_count) is not int
        or value.sealed_interpreter_process_count != 1
        or type(value.retry_count) is not int
        or value.retry_count != 0
        or type(value.fallback_count) is not int
        or value.fallback_count != 0
    ):
        return None
    counts = _counts_from_result(value)
    if any(type(count) is not int or count < 0 or count > 1 for count in counts.values()):
        return None
    if (
        value.output_file_count > value.output_write_count
        or value.output_write_count > value.synthesis_attempt_count
        or value.synthesis_attempt_count > value.session_initialization_count
        or value.session_initialization_count > value.runtime_process_count
        or value.runtime_process_count > value.text_input_count
    ):
        return None
    if value.outcome == "ONE_SYNTHETIC_OUTPUT_CREATED":
        if (
            value.safe_error_category is not None
            or value.output_state_unknown is not False
            or any(count != 1 for count in counts.values())
            or value.output_file_count != 1
            or value.output_write_count != 1
            or value.output_path
            != str(
                PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
                / L8_EXECUTABLE_OUTPUT_FILENAME
            )
            or type(value.output_byte_count) is not int
            or value.output_byte_count <= 0
            or not _is_lower_sha256(value.output_sha256)
        ):
            return None
    elif value.outcome == "EXECUTION_FAILED_CLOSED":
        if (
            type(value.safe_error_category) is not str
            or value.safe_error_category not in _SAFE_CHILD_ERROR_CATEGORIES
        ):
            return None
        if value.output_state_unknown:
            if (
                value.safe_error_category
                not in _SAFE_CHILD_UNKNOWN_OUTPUT_CATEGORIES
                or any(count != 1 for count in counts.values())
                or value.output_path
                != str(
                    PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
                    / L8_EXECUTABLE_OUTPUT_FILENAME
                )
                or value.output_byte_count is not None
                or value.output_sha256 is not None
            ):
                return None
        elif value.output_file_count != 0 or any(
            item is not None
            for item in (value.output_path, value.output_byte_count, value.output_sha256)
        ):
            return None
    else:
        return None
    return value


def _execute_inside_sealed_interpreter(
    *,
    durable_authorization_record: object,
    runtime_factory: object,
    exclusive_wav_writer: object,
    clock: object,
    file_system_boundary: object,
    ephemeral_test_text_supplier: object,
) -> L8SyntheticRunnerResult:
    """Execute only the inside-sealed portion; lifecycle remains caller-owned."""
    global _sealed_execution_claimed

    authorization_id = (
        durable_authorization_record.get("authorization_id")
        if type(durable_authorization_record) is dict
        and type(durable_authorization_record.get("authorization_id")) is str
        else None
    )
    nonce_fingerprint = (
        durable_authorization_record.get("nonce_fingerprint")
        if type(durable_authorization_record) is dict
        and type(durable_authorization_record.get("nonce_fingerprint")) is str
        else None
    )
    if _sealed_execution_claimed:
        return _result(
            category="sealed_runner_already_used",
            authorization_id=authorization_id,
            nonce_fingerprint=nonce_fingerprint,
            lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
            sealed_interpreter_process_count=1,
        )
    _sealed_execution_claimed = True

    validation = validate_l8_durable_authorization_record(
        durable_authorization_record,
        expected_lifecycle=L8_AUTHORIZED_NOT_EXECUTED,
    )
    if not validation.valid:
        return _result(
            category=validation.safe_error_category or "durable_authorization_invalid",
            authorization_id=authorization_id,
            nonce_fingerprint=nonce_fingerprint,
            lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
            sealed_interpreter_process_count=1,
        )

    interfaces = (
        (runtime_factory, ("preflight_locked_runtime", "create_locked_runtime")),
        (exclusive_wav_writer, ("write_wav_exclusive",)),
        (clock, ("now_utc",)),
        (file_system_boundary, ("preflight_output_absent", "create_root_exclusive")),
        (ephemeral_test_text_supplier, ("supply_ephemeral_text_once",)),
    )
    if any(not _has_exact_interface(value, methods) for value, methods in interfaces):
        return _result(
            category="injected_interface_invalid",
            authorization_id=authorization_id,
            nonce_fingerprint=nonce_fingerprint,
            lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
            sealed_interpreter_process_count=1,
        )

    counts = {
        "runtime_process": 0,
        "session_initialization": 0,
        "text_input": 0,
        "synthesis_attempt": 0,
        "output_file": 0,
        "output_write": 0,
    }
    output_path: str | None = None
    output_byte_count: int | None = None
    output_sha256: str | None = None
    text: str | None = None

    try:
        now = _safe_call(clock.now_utc, "clock_failed")
        expiration = _parse_expiration(durable_authorization_record["expiration_timestamp"])
        if (
            type(now) is not datetime
            or now.tzinfo is None
            or expiration is None
            or expiration <= now.astimezone(timezone.utc)
        ):
            raise _RunnerFailure("authorization_expired")

        output_preflight = _safe_call(
            file_system_boundary.preflight_output_absent,
            "output_preflight_failed",
        )
        _validate_output_preflight(output_preflight)
        created_root = _safe_call(
            file_system_boundary.create_root_exclusive,
            "output_root_create_failed",
        )
        _validate_created_root(created_root)

        runtime_preflight = _safe_call(
            runtime_factory.preflight_locked_runtime,
            "runtime_preflight_failed",
        )
        expected_runtime_preflight = {
            "sealed_interpreter_exact": True,
            "piper_version": PIPER_VERSION,
            "onnxruntime_version": "1.27.0",
            "model_sha256": MODEL_SHA256,
            "config_sha256": CONFIG_SHA256,
            "execution_provider": EXECUTION_PROVIDER,
            "voice_id": MODEL_ID,
            "output_format": OUTPUT_FORMAT,
        }
        if (
            type(runtime_preflight) is not dict
            or set(runtime_preflight) != set(expected_runtime_preflight)
            or any(
                runtime_preflight[field] != expected
                for field, expected in expected_runtime_preflight.items()
            )
        ):
            raise _RunnerFailure("runtime_preflight_identity_mismatch")

        now_before_attempt = _safe_call(clock.now_utc, "clock_failed")
        if (
            type(now_before_attempt) is not datetime
            or now_before_attempt.tzinfo is None
            or expiration <= now_before_attempt.astimezone(timezone.utc)
        ):
            raise _RunnerFailure("authorization_expired_before_attempt")

        counts["text_input"] = 1
        envelope = _safe_call(
            ephemeral_test_text_supplier.supply_ephemeral_text_once,
            "ephemeral_text_supplier_failed",
            durable_authorization_record["text_sha256"],
        )
        envelope_fields = {
            "text",
            "synthetic_test_only",
            "non_case_text_only",
            "no_personal_data",
        }
        if type(envelope) is not dict or set(envelope) != envelope_fields:
            raise _RunnerFailure("ephemeral_text_envelope_invalid")
        if any(
            envelope[field] is not True
            for field in (
                "synthetic_test_only",
                "non_case_text_only",
                "no_personal_data",
            )
        ):
            envelope["text"] = None
            raise _RunnerFailure("non_synthetic_text_rejected")
        text = envelope["text"]
        envelope["text"] = None
        if type(text) is not str or not 0 < len(text) <= _MAXIMUM_TEXT_CHARACTERS:
            text = None
            raise _RunnerFailure("ephemeral_text_invalid")
        if (
            hashlib.sha256(text.encode("utf-8")).hexdigest()
            != durable_authorization_record["text_sha256"]
        ):
            text = None
            raise _RunnerFailure("text_hash_mismatch")

        counts["runtime_process"] = 1
        runtime = _safe_call(
            runtime_factory.create_locked_runtime,
            "runtime_factory_failed",
        )
        if not _has_exact_interface(runtime, ("initialize_locked_session",)):
            raise _RunnerFailure("runtime_interface_invalid")

        counts["session_initialization"] = 1
        session = _safe_call(
            runtime.initialize_locked_session,
            "session_initialization_failed",
        )
        if not _has_exact_interface(session, ("locked_identity", "synthesize_once")):
            raise _RunnerFailure("session_interface_invalid")

        runtime_identity = _safe_call(
            session.locked_identity,
            "runtime_identity_inspection_failed",
        )
        expected_runtime_identity = {
            "route_id": ROUTE_ID,
            "piper_version": PIPER_VERSION,
            "model_id": MODEL_ID,
            "model_sha256": MODEL_SHA256,
            "config_sha256": CONFIG_SHA256,
            "execution_provider": EXECUTION_PROVIDER,
            "voice_id": MODEL_ID,
            "output_format": OUTPUT_FORMAT,
        }
        if (
            type(runtime_identity) is not dict
            or set(runtime_identity) != set(expected_runtime_identity)
            or any(
                runtime_identity[field] != expected
                for field, expected in expected_runtime_identity.items()
            )
        ):
            raise _RunnerFailure("runtime_identity_mismatch")

        counts["synthesis_attempt"] = 1
        wav_bytes = _safe_call(session.synthesize_once, "synthesis_failed", text)
        text = None
        if type(wav_bytes) is not bytes or not wav_bytes:
            raise _RunnerFailure("synthesis_result_invalid")

        counts["output_write"] = 1
        write_result = _safe_call(
            exclusive_wav_writer.write_wav_exclusive,
            "exclusive_write_failed",
            wav_bytes,
        )
        wav_bytes = b""
        expected_write_fields = {
            "exclusive_create",
            "output_file_count",
            "output_write_count",
            "byte_count",
            "sha256",
        }
        if type(write_result) is not dict or set(write_result) != expected_write_fields:
            raise _RunnerFailure("writer_result_invalid")
        if (
            write_result["exclusive_create"] is not True
            or type(write_result["output_file_count"]) is not int
            or write_result["output_file_count"] != 1
            or type(write_result["output_write_count"]) is not int
            or write_result["output_write_count"] != 1
            or type(write_result["byte_count"]) is not int
            or write_result["byte_count"] <= 0
            or not _is_lower_sha256(write_result["sha256"])
        ):
            raise _RunnerFailure("writer_result_invalid")
        counts["output_file"] = 1
        output_path = str(
            PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
            / L8_EXECUTABLE_OUTPUT_FILENAME
        )
        output_byte_count = write_result["byte_count"]
        output_sha256 = write_result["sha256"]
    except _RunnerFailure as failure:
        text = None
        output_state_unknown = (
            counts["output_write"] == 1 and counts["output_file"] == 0
        )
        if output_state_unknown:
            counts["output_file"] = 1
            output_path = str(
                PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
                / L8_EXECUTABLE_OUTPUT_FILENAME
            )
        return _result(
            category=failure.category,
            authorization_id=authorization_id,
            nonce_fingerprint=nonce_fingerprint,
            lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
            sealed_interpreter_process_count=1,
            counts=counts,
            output_path=output_path,
            output_byte_count=output_byte_count,
            output_sha256=output_sha256,
            output_state_unknown=output_state_unknown,
        )
    except Exception:
        text = None
        output_state_unknown = (
            counts["output_write"] == 1 and counts["output_file"] == 0
        )
        if output_state_unknown:
            counts["output_file"] = 1
            output_path = str(
                PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
                / L8_EXECUTABLE_OUTPUT_FILENAME
            )
        return _result(
            category="unexpected_execution_failure",
            authorization_id=authorization_id,
            nonce_fingerprint=nonce_fingerprint,
            lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
            sealed_interpreter_process_count=1,
            counts=counts,
            output_path=output_path,
            output_byte_count=output_byte_count,
            output_sha256=output_sha256,
            output_state_unknown=output_state_unknown,
        )
    return _result(
        category=None,
        authorization_id=authorization_id,
        nonce_fingerprint=nonce_fingerprint,
        lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
        sealed_interpreter_process_count=1,
        counts=counts,
        output_path=output_path,
        output_byte_count=output_byte_count,
        output_sha256=output_sha256,
    )


def execute_one_time_piper_synthetic(
    *,
    authorization: object,
    clock: object,
    safe_audit_sink: object,
    sealed_interpreter_boundary: object,
) -> L8SyntheticRunnerResult:
    """Validate, persist, launch once, then consume and audit in caller order."""
    global _process_execution_claimed

    authorization_id = (
        authorization.get("authorization_id")
        if type(authorization) is dict
        and type(authorization.get("authorization_id")) is str
        else None
    )
    if _process_execution_claimed:
        return _result(
            category="runner_already_used",
            authorization_id=authorization_id,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )
    if type(authorization) is not dict:
        return _result(
            category="invalid_authorization_type",
            authorization_id=None,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )
    nonce = authorization.get("single_use_nonce")
    nonce_fingerprint_candidate = (
        hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        if type(nonce) is str
        else None
    )
    if (
        type(authorization_id) is str
        and authorization_id in _claimed_authorization_ids
    ) or (
        nonce_fingerprint_candidate is not None
        and nonce_fingerprint_candidate in _claimed_nonce_fingerprints
    ):
        return _result(
            category="authorization_reused",
            authorization_id=authorization_id,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )

    validation = (
        L8ExecutableSyntheticAuthorizationValidator()
        .validate_l8_executable_synthetic_authorization(authorization)
    )
    if not validation.valid:
        return _result(
            category=validation.safe_error_category or "authorization_invalid",
            authorization_id=authorization_id,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )
    if authorization["schema_version"] != L8_EXECUTABLE_SCHEMA_VERSION:
        return _result(
            category="schema_version_invalid",
            authorization_id=authorization_id,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )
    interfaces = (
        (clock, ("now_utc",)),
        (
            safe_audit_sink,
            (
                "create_authorization_exclusive",
                "consume_authorization_exclusive",
                "create_audit_exclusive",
            ),
        ),
        (sealed_interpreter_boundary, ("launch_canonical_once",)),
    )
    if any(not _has_exact_interface(value, methods) for value, methods in interfaces):
        return _result(
            category="caller_interface_invalid",
            authorization_id=authorization_id,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )
    try:
        now = _safe_call(clock.now_utc, "clock_failed")
    except _RunnerFailure as failure:
        return _result(
            category=failure.category,
            authorization_id=authorization_id,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )
    expiration = _parse_expiration(authorization["expiration_timestamp"])
    if (
        type(now) is not datetime
        or now.tzinfo is None
        or expiration is None
        or expiration <= now.astimezone(timezone.utc)
    ):
        return _result(
            category="authorization_expired",
            authorization_id=authorization_id,
            nonce_fingerprint=None,
            lifecycle_status=None,
        )

    authorized_record = _safe_authorization_record(
        authorization, L8_AUTHORIZED_NOT_EXECUTED
    )
    durable_validation = validate_l8_durable_authorization_record(
        authorized_record,
        expected_lifecycle=L8_AUTHORIZED_NOT_EXECUTED,
    )
    if not durable_validation.valid:
        return _result(
            category=durable_validation.safe_error_category
            or "durable_authorization_projection_invalid",
            authorization_id=authorization_id,
            nonce_fingerprint=authorized_record["nonce_fingerprint"],
            lifecycle_status=None,
        )

    _process_execution_claimed = True
    try:
        safe_audit_sink.create_authorization_exclusive(authorized_record)
    except Exception:
        return _result(
            category="authorization_create_failed",
            authorization_id=authorization_id,
            nonce_fingerprint=authorized_record["nonce_fingerprint"],
            lifecycle_status=None,
        )

    _claimed_authorization_ids.add(str(authorization_id))
    _claimed_nonce_fingerprints.add(str(authorized_record["nonce_fingerprint"]))
    try:
        launched = sealed_interpreter_boundary.launch_canonical_once(
            _SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        )
    except Exception:
        child_result = _unknown_child_result(
            authorized_record, "sealed_launch_failed"
        )
    else:
        try:
            child_result = _validate_child_result(launched, authorized_record)
        except Exception:
            child_result = None
        if child_result is None:
            child_result = _unknown_child_result(
                authorized_record, "sealed_result_invalid"
            )
    counts = _counts_from_result(child_result)
    consumed_record = dict(authorized_record)
    consumed_record["allowed_voice_ids"] = list(
        authorized_record["allowed_voice_ids"]
    )
    consumed_record["lifecycle_status"] = L8_AUTHORIZATION_CONSUMED
    try:
        safe_audit_sink.consume_authorization_exclusive(consumed_record)
    except Exception:
        return _result(
            category="authorization_consumption_failed_closed",
            authorization_id=authorization_id,
            nonce_fingerprint=authorized_record["nonce_fingerprint"],
            lifecycle_status=L8_AUTHORIZED_NOT_EXECUTED,
            sealed_interpreter_process_count=1,
            counts=counts,
            output_path=child_result.output_path,
            output_byte_count=child_result.output_byte_count,
            output_sha256=child_result.output_sha256,
            output_state_unknown=child_result.output_state_unknown,
        )

    try:
        safe_audit_sink.create_audit_exclusive(
            _safe_audit_payload(
                consumed_record,
                child_result.outcome,
                counts,
                child_result.safe_error_category,
                child_result.output_path,
                child_result.output_byte_count,
                child_result.output_sha256,
                child_result.output_state_unknown,
            )
        )
    except Exception:
        return _result(
            category="audit_create_failed_closed",
            authorization_id=authorization_id,
            nonce_fingerprint=authorized_record["nonce_fingerprint"],
            lifecycle_status=L8_AUTHORIZATION_CONSUMED,
            sealed_interpreter_process_count=1,
            counts=counts,
            output_path=child_result.output_path,
            output_byte_count=child_result.output_byte_count,
            output_sha256=child_result.output_sha256,
            output_state_unknown=child_result.output_state_unknown,
        )
    return _result(
        category=child_result.safe_error_category,
        authorization_id=authorization_id,
        nonce_fingerprint=authorized_record["nonce_fingerprint"],
        lifecycle_status=L8_AUTHORIZATION_CONSUMED,
        sealed_interpreter_process_count=1,
        counts=counts,
        output_path=child_result.output_path,
        output_byte_count=child_result.output_byte_count,
        output_sha256=child_result.output_sha256,
        output_state_unknown=child_result.output_state_unknown,
    )


def _reset_process_state_for_offline_tests() -> None:
    global _process_execution_claimed, _sealed_execution_claimed
    _process_execution_claimed = False
    _sealed_execution_claimed = False
    _claimed_authorization_ids.clear()
    _claimed_nonce_fingerprints.clear()
