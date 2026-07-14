"""Concrete, inert-until-invoked local dependencies for the L7C L8 runner.

Importing this module performs no filesystem inspection, runtime import, model
load, text handoff, authorization/audit write, or media operation. Every public
adapter is parameterless and bound to the immutable L7B/L7D constants.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path, PureWindowsPath

from l7_piper_synthetic_authorization_contract import (
    CONFIG_SHA256,
    EXECUTION_PROVIDER,
    L8_AUDIT_ROOT,
    L8_AUTHORIZATION_CONSUMED,
    L8_AUTHORIZATION_ROOT,
    L8_AUTHORIZED_NOT_EXECUTED,
    L8_DURABLE_AUTHORIZATION_RECORD_FIELDS,
    L8_EXECUTABLE_OUTPUT_FILENAME,
    L8_EXECUTABLE_OUTPUT_ROOT,
    MODEL_ID,
    MODEL_SHA256,
    OUTPUT_FORMAT,
    PIPER_VERSION,
    ROUTE_ID,
    validate_l8_durable_authorization_record,
)


_LOCAL_TOOLS_ROOT = Path(r"C:\ColdTruthLocalTools")
_SEALED_INTERPRETER = Path(
    r"C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe"
)
_LOCKED_ASSET_ROOT = Path(r"C:\ColdTruthLocalTools\piper-1.4.2-assets")
_LOCKED_MODEL_PATH = _LOCKED_ASSET_ROOT / "en_US-ljspeech-high.onnx"
_LOCKED_CONFIG_PATH = _LOCKED_ASSET_ROOT / "en_US-ljspeech-high.onnx.json"
_LOCKED_ONNXRUNTIME_VERSION = "1.27.0"
_OUTPUT_ROOT = Path(L8_EXECUTABLE_OUTPUT_ROOT)
_OUTPUT_PATH = _OUTPUT_ROOT / L8_EXECUTABLE_OUTPUT_FILENAME
_AUTHORIZATION_ROOT = Path(L8_AUTHORIZATION_ROOT)
_AUDIT_ROOT = Path(L8_AUDIT_ROOT)
_FIXED_TEXT_SHA256 = (
    "7bf2ac457b61fd5e9dc260adec980f39a3d9a6e76ec9f2e449000c04cf70828b"
)
_FIXED_TEXT_UTF8 = (
    84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 108, 111, 99, 97, 108,
    32, 115, 121, 110, 116, 104, 101, 116, 105, 99, 32, 115, 112, 101,
    101, 99, 104, 32, 116, 101, 115, 116, 46, 32, 73, 116, 32, 99, 111,
    110, 116, 97, 105, 110, 115, 32, 110, 111, 32, 114, 101, 97, 108,
    32, 99, 97, 115, 101, 32, 109, 97, 116, 101, 114, 105, 97, 108, 46,
)
_AUTHORIZATION_ID_PATTERN = re.compile(
    r"L8-SYNTHETIC-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_SAFE_CATEGORY_PATTERN = re.compile(r"[a-z0-9_]{1,96}")
_SAFE_AUDIT_FAILURE_CATEGORIES = {
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
    "sealed_result_invalid",
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
_UNKNOWN_OUTPUT_FAILURE_CATEGORIES = {
    "exclusive_write_failed",
    "sealed_launch_failed",
    "sealed_result_invalid",
    "unexpected_execution_failure",
    "writer_result_invalid",
}

_AUTHORIZATION_RECORD_FIELDS = set(L8_DURABLE_AUTHORIZATION_RECORD_FIELDS)

_AUDIT_RECORD_FIELDS = {
    "audit_event_id",
    "authorization_id",
    "nonce_fingerprint",
    "lifecycle_status",
    "attempt_outcome",
    "failure_category",
    "route_id",
    "piper_version",
    "model_id",
    "model_sha256",
    "config_sha256",
    "execution_provider",
    "voice_id",
    "output_format",
    "output_path",
    "output_byte_count",
    "output_sha256",
    "output_state_unknown",
    "runtime_process_count",
    "session_initialization_count",
    "text_input_count",
    "synthesis_attempt_count",
    "output_file_count",
    "output_write_count",
    "retry_count",
    "fallback_count",
}


def _is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256_PATTERN.fullmatch(value) is not None


def _is_safe_regular(value: Path) -> bool:
    info = os.lstat(value)
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return (
        stat.S_ISREG(info.st_mode)
        and not stat.S_ISLNK(info.st_mode)
        and not attributes & reparse
    )


def _is_safe_directory(value: Path) -> bool:
    info = os.lstat(value)
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return (
        stat.S_ISDIR(info.st_mode)
        and not stat.S_ISLNK(info.st_mode)
        and not attributes & reparse
    )


def _require_fixed_direct_child(path: Path) -> None:
    candidate = PureWindowsPath(str(path))
    root = PureWindowsPath(str(_LOCAL_TOOLS_ROOT))
    if not candidate.is_absolute() or candidate.parent != root:
        raise RuntimeError("fixed_root_containment_failure")
    if any(part in {".", ".."} for part in candidate.parts):
        raise RuntimeError("fixed_root_traversal_rejected")


def _require_safe_local_tools_root() -> None:
    if not _LOCAL_TOOLS_ROOT.exists() or not _is_safe_directory(_LOCAL_TOOLS_ROOT):
        raise RuntimeError("local_tools_root_unsafe")


def _exclusive_json_write(path: Path, payload: dict[str, object]) -> int:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        written = os.write(descriptor, encoded)
        if written != len(encoded):
            raise RuntimeError("exclusive_record_write_incomplete")
    finally:
        os.close(descriptor)
    return len(encoded)


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("authorization_record_duplicate_field")
        result[key] = value
    return result


def _read_strict_json_object(path: Path) -> dict[str, object]:
    if not _is_safe_regular(path):
        raise RuntimeError("authorization_record_unsafe")
    with path.open("rb") as handle:
        encoded = handle.read(16_385)
    if not encoded or len(encoded) > 16_384:
        raise RuntimeError("authorization_record_size_invalid")
    try:
        decoded = json.loads(
            encoded.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise RuntimeError("authorization_record_json_invalid") from None
    if type(decoded) is not dict:
        raise RuntimeError("authorization_record_json_invalid")
    return decoded


def _validate_authorization_record(
    record: object, expected_lifecycle: str
) -> dict[str, object]:
    if type(record) is not dict or set(record) != _AUTHORIZATION_RECORD_FIELDS:
        raise ValueError("authorization_record_shape_invalid")
    validation = validate_l8_durable_authorization_record(
        record, expected_lifecycle=expected_lifecycle
    )
    if not validation.valid:
        raise ValueError(
            validation.safe_error_category or "authorization_record_invalid"
        )
    return dict(record)


def _validate_audit_record(record: object) -> dict[str, object]:
    if type(record) is not dict or set(record) != _AUDIT_RECORD_FIELDS:
        raise ValueError("audit_record_shape_invalid")
    authorization_id = record["authorization_id"]
    if (
        type(authorization_id) is not str
        or _AUTHORIZATION_ID_PATTERN.fullmatch(authorization_id) is None
        or record["audit_event_id"] != f"{authorization_id}:FINAL"
    ):
        raise ValueError("audit_identifier_invalid")
    if not _is_sha256(record["nonce_fingerprint"]):
        raise ValueError("audit_nonce_fingerprint_invalid")
    expected_identity = {
        "lifecycle_status": L8_AUTHORIZATION_CONSUMED,
        "route_id": ROUTE_ID,
        "piper_version": PIPER_VERSION,
        "model_id": MODEL_ID,
        "model_sha256": MODEL_SHA256,
        "config_sha256": CONFIG_SHA256,
        "execution_provider": EXECUTION_PROVIDER,
        "voice_id": MODEL_ID,
        "output_format": OUTPUT_FORMAT,
    }
    if any(record[field] != value for field, value in expected_identity.items()):
        raise ValueError("audit_identity_invalid")
    if (
        type(record["attempt_outcome"]) is not str
        or record["attempt_outcome"]
        not in ("ONE_SYNTHETIC_OUTPUT_CREATED", "EXECUTION_FAILED_CLOSED")
    ):
        raise ValueError("audit_outcome_invalid")
    category = record["failure_category"]
    if category is not None and (
        type(category) is not str
        or _SAFE_CATEGORY_PATTERN.fullmatch(category) is None
        or category not in _SAFE_AUDIT_FAILURE_CATEGORIES
    ):
        raise ValueError("audit_failure_category_invalid")
    count_limits = {
        "runtime_process_count": 1,
        "session_initialization_count": 1,
        "text_input_count": 1,
        "synthesis_attempt_count": 1,
        "output_file_count": 1,
        "output_write_count": 1,
        "retry_count": 0,
        "fallback_count": 0,
    }
    for field, maximum in count_limits.items():
        if (
            type(record[field]) is not int
            or record[field] < 0
            or record[field] > maximum
        ):
            raise ValueError("audit_count_invalid")
    if record["retry_count"] != 0 or record["fallback_count"] != 0:
        raise ValueError("audit_retry_or_fallback_invalid")
    if (
        record["output_file_count"] > record["output_write_count"]
        or record["output_write_count"] > record["synthesis_attempt_count"]
        or record["synthesis_attempt_count"]
        > record["session_initialization_count"]
        or record["session_initialization_count"]
        > record["runtime_process_count"]
        or record["runtime_process_count"] > record["text_input_count"]
    ):
        raise ValueError("audit_count_order_invalid")
    if type(record["output_state_unknown"]) is not bool:
        raise ValueError("audit_output_state_invalid")
    if record["output_state_unknown"]:
        if (
            record["attempt_outcome"] != "EXECUTION_FAILED_CLOSED"
            or category not in _UNKNOWN_OUTPUT_FAILURE_CATEGORIES
            or record["output_file_count"] != 1
            or record["output_write_count"] != 1
            or record["output_path"] != str(_OUTPUT_PATH)
            or record["output_byte_count"] is not None
            or record["output_sha256"] is not None
        ):
            raise ValueError("audit_unknown_output_state_invalid")
    elif record["output_file_count"] == 1:
        if (
            record["output_path"] != str(_OUTPUT_PATH)
            or type(record["output_byte_count"]) is not int
            or record["output_byte_count"] <= 0
            or not _is_sha256(record["output_sha256"])
        ):
            raise ValueError("audit_output_invalid")
    elif any(
        record[field] is not None
        for field in ("output_path", "output_byte_count", "output_sha256")
    ):
        raise ValueError("audit_output_invalid")
    if record["attempt_outcome"] == "ONE_SYNTHETIC_OUTPUT_CREATED":
        if (
            category is not None
            or record["output_state_unknown"]
            or any(
                record[field] != 1
                for field in (
                    "runtime_process_count",
                    "session_initialization_count",
                    "text_input_count",
                    "synthesis_attempt_count",
                    "output_file_count",
                    "output_write_count",
                )
            )
        ):
            raise ValueError("audit_success_state_invalid")
    else:
        if category is None:
            raise ValueError("audit_failure_category_missing")
        if not record["output_state_unknown"] and record["output_file_count"] != 0:
            raise ValueError("audit_failure_output_state_invalid")
    return dict(record)


class CanonicalL8FileSystemBoundary:
    """Fixed-root inspection and one exclusive output-root creation only."""

    __slots__ = ("_preflight_attempted", "_preflight_complete", "_root_created")

    def __init__(self) -> None:
        self._preflight_attempted = False
        self._preflight_complete = False
        self._root_created = False

    def preflight_output_absent(self) -> dict[str, bool]:
        if self._preflight_attempted or self._root_created:
            raise RuntimeError("filesystem_boundary_already_used")
        self._preflight_attempted = True
        _require_safe_local_tools_root()
        _require_fixed_direct_child(_AUTHORIZATION_ROOT)
        if not _is_safe_directory(_AUTHORIZATION_ROOT):
            raise RuntimeError("authorization_root_unsafe")
        for absent_root in (_AUDIT_ROOT, _OUTPUT_ROOT):
            _require_fixed_direct_child(absent_root)
            if os.path.lexists(absent_root):
                raise FileExistsError("fixed_l8_root_exists")
        if os.path.lexists(_OUTPUT_PATH):
            raise FileExistsError("canonical_output_exists")
        self._preflight_complete = True
        return {
            "root_absent": True,
            "target_absent": True,
            "canonical_containment": True,
            "root_would_be_regular": True,
            "non_link": True,
            "non_reparse": True,
            "exclusive_create_supported": True,
        }

    def create_root_exclusive(self) -> dict[str, bool]:
        if not self._preflight_complete or self._root_created:
            raise RuntimeError("output_root_creation_not_permitted")
        self._root_created = True
        os.mkdir(_OUTPUT_ROOT, 0o700)
        if not _is_safe_directory(_OUTPUT_ROOT):
            raise RuntimeError("created_output_root_unsafe")
        with os.scandir(_OUTPUT_ROOT) as entries:
            if next(entries, None) is not None:
                raise RuntimeError("created_output_root_not_empty")
        return {
            "created_exclusively": True,
            "empty": True,
            "canonical_containment": True,
            "regular_directory": True,
            "non_link": True,
            "non_reparse": True,
        }


class CanonicalL8DurableAuthorizationReader:
    """Read exactly one fresh fixed-root authorization without path selection."""

    __slots__ = ("_used",)

    def __init__(self) -> None:
        self._used = False

    def read_authorization_once(self) -> dict[str, object]:
        if self._used:
            raise RuntimeError("authorization_reader_already_used")
        self._used = True
        _require_safe_local_tools_root()
        _require_fixed_direct_child(_AUTHORIZATION_ROOT)
        if not _is_safe_directory(_AUTHORIZATION_ROOT):
            raise RuntimeError("authorization_root_unsafe")
        with os.scandir(_AUTHORIZATION_ROOT) as entries:
            paths = [Path(entry.path) for entry in entries]
        if len(paths) != 1:
            raise RuntimeError("authorization_root_entry_count_invalid")
        path = paths[0]
        if not path.name.endswith(".authorized.json"):
            raise RuntimeError("authorization_record_filename_invalid")
        safe = _validate_authorization_record(
            _read_strict_json_object(path), L8_AUTHORIZED_NOT_EXECUTED
        )
        expected_name = f'{safe["authorization_id"]}.authorized.json'
        if path.name != expected_name:
            raise RuntimeError("authorization_record_filename_invalid")
        return safe


class SafeL8LifecycleAuditSink:
    """Strict fixed-root authorization lifecycle and final safe audit sink."""

    __slots__ = (
        "_authorization_id",
        "_nonce_fingerprint",
        "_authorization_create_attempted",
        "_authorization_created",
        "_authorization_consume_attempted",
        "_authorization_consumed",
        "_audit_create_attempted",
        "_audit_created",
    )

    def __init__(self) -> None:
        self._authorization_id: str | None = None
        self._nonce_fingerprint: str | None = None
        self._authorization_create_attempted = False
        self._authorization_created = False
        self._authorization_consume_attempted = False
        self._authorization_consumed = False
        self._audit_create_attempted = False
        self._audit_created = False

    def create_authorization_exclusive(self, record: object) -> None:
        if self._authorization_create_attempted:
            raise RuntimeError("authorization_already_created")
        self._authorization_create_attempted = True
        safe = _validate_authorization_record(
            record, L8_AUTHORIZED_NOT_EXECUTED
        )
        _require_safe_local_tools_root()
        _require_fixed_direct_child(_AUTHORIZATION_ROOT)
        os.mkdir(_AUTHORIZATION_ROOT, 0o700)
        if not _is_safe_directory(_AUTHORIZATION_ROOT):
            raise RuntimeError("authorization_root_unsafe")
        authorization_id = str(safe["authorization_id"])
        _exclusive_json_write(
            _AUTHORIZATION_ROOT / f"{authorization_id}.authorized.json", safe
        )
        self._authorization_id = authorization_id
        self._nonce_fingerprint = str(safe["nonce_fingerprint"])
        self._authorization_created = True

    def consume_authorization_exclusive(self, record: object) -> None:
        if (
            not self._authorization_created
            or self._authorization_consume_attempted
        ):
            raise RuntimeError("authorization_consumption_not_permitted")
        self._authorization_consume_attempted = True
        safe = _validate_authorization_record(record, L8_AUTHORIZATION_CONSUMED)
        if (
            safe["authorization_id"] != self._authorization_id
            or safe["nonce_fingerprint"] != self._nonce_fingerprint
        ):
            raise ValueError("authorization_consumption_binding_invalid")
        _exclusive_json_write(
            _AUTHORIZATION_ROOT
            / f"{self._authorization_id}.consumed.json",
            safe,
        )
        self._authorization_consumed = True

    def create_audit_exclusive(self, record: object) -> None:
        if (
            not self._authorization_consumed
            or self._audit_create_attempted
            or self._authorization_id is None
        ):
            raise RuntimeError("audit_creation_not_permitted")
        self._audit_create_attempted = True
        safe = _validate_audit_record(record)
        if (
            safe["authorization_id"] != self._authorization_id
            or safe["nonce_fingerprint"] != self._nonce_fingerprint
        ):
            raise ValueError("audit_binding_invalid")
        _require_safe_local_tools_root()
        _require_fixed_direct_child(_AUDIT_ROOT)
        os.mkdir(_AUDIT_ROOT, 0o700)
        if not _is_safe_directory(_AUDIT_ROOT):
            raise RuntimeError("audit_root_unsafe")
        _exclusive_json_write(
            _AUDIT_ROOT / f"{self._authorization_id}.final.audit.json", safe
        )
        self._audit_created = True


class FixedEphemeralSyntheticTextSupplier:
    """One-use fixed text reconstruction guarded by the approved SHA-256."""

    __slots__ = ("_used",)

    def __init__(self) -> None:
        self._used = False

    def supply_ephemeral_text_once(
        self, expected_sha256: object
    ) -> dict[str, object]:
        if self._used:
            raise RuntimeError("ephemeral_text_already_supplied")
        if expected_sha256 != _FIXED_TEXT_SHA256:
            raise ValueError("expected_text_hash_mismatch")
        text = bytes(_FIXED_TEXT_UTF8).decode("utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != _FIXED_TEXT_SHA256:
            text = ""
            raise RuntimeError("fixed_text_integrity_failure")
        self._used = True
        return {
            "text": text,
            "synthetic_test_only": True,
            "non_case_text_only": True,
            "no_personal_data": True,
        }


class UtcL8Clock:
    """Minimal timezone-aware clock with no environment dependency."""

    __slots__ = ()

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


class _LockedPiperSession:
    __slots__ = ("_voice", "_used")

    def __init__(self, voice: object) -> None:
        self._voice = voice
        self._used = False

    def locked_identity(self) -> dict[str, str]:
        return {
            "route_id": ROUTE_ID,
            "piper_version": PIPER_VERSION,
            "model_id": MODEL_ID,
            "model_sha256": MODEL_SHA256,
            "config_sha256": CONFIG_SHA256,
            "execution_provider": EXECUTION_PROVIDER,
            "voice_id": MODEL_ID,
            "output_format": OUTPUT_FORMAT,
        }

    def synthesize_once(self, text: object) -> bytes:
        if self._used:
            raise RuntimeError("session_already_used")
        if type(text) is not str or not text:
            raise ValueError("synthetic_text_invalid")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != _FIXED_TEXT_SHA256:
            raise ValueError("synthetic_text_hash_mismatch")
        self._used = True
        import io
        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_handle:
            self._voice.synthesize_wav(text, wav_handle)
        result = buffer.getvalue()
        if not result:
            raise RuntimeError("empty_synthesis_result")
        return result


class _LockedPiperRuntime:
    __slots__ = ("_initialized",)

    def __init__(self) -> None:
        self._initialized = False

    def initialize_locked_session(self) -> _LockedPiperSession:
        if self._initialized:
            raise RuntimeError("runtime_already_initialized")
        self._initialized = True
        piper_voice_module = importlib.import_module("piper.voice")
        voice = piper_voice_module.PiperVoice.load(
            model_path=_LOCKED_MODEL_PATH,
            config_path=_LOCKED_CONFIG_PATH,
            use_cuda=False,
            download_dir=_LOCKED_ASSET_ROOT,
        )
        if tuple(voice.session.get_providers()) != (EXECUTION_PROVIDER,):
            raise RuntimeError("non_cpu_provider_active")
        return _LockedPiperSession(voice)


class LockedLocalPiperRuntimeFactory:
    """Parameterless one-use factory for the exact sealed local identity."""

    __slots__ = ("_preflight_attempted", "_preflight_complete", "_used")

    def __init__(self) -> None:
        self._preflight_attempted = False
        self._preflight_complete = False
        self._used = False

    def preflight_locked_runtime(self) -> dict[str, object]:
        if self._preflight_attempted or self._used:
            raise RuntimeError("runtime_preflight_already_used")
        self._preflight_attempted = True
        if Path(sys.executable).resolve(strict=True) != _SEALED_INTERPRETER.resolve(
            strict=True
        ):
            raise RuntimeError("sealed_interpreter_mismatch")
        if metadata.version("piper-tts") != PIPER_VERSION:
            raise RuntimeError("piper_version_mismatch")
        if metadata.version("onnxruntime") != _LOCKED_ONNXRUNTIME_VERSION:
            raise RuntimeError("onnxruntime_version_mismatch")
        if not _is_safe_directory(_LOCKED_ASSET_ROOT):
            raise RuntimeError("locked_asset_root_unsafe")
        verified: dict[str, str] = {}
        for name, path, expected_hash in (
            ("model_sha256", _LOCKED_MODEL_PATH, MODEL_SHA256),
            ("config_sha256", _LOCKED_CONFIG_PATH, CONFIG_SHA256),
        ):
            if not _is_safe_regular(path):
                raise RuntimeError("locked_asset_unsafe")
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            actual = digest.hexdigest()
            if actual != expected_hash:
                raise RuntimeError("locked_asset_hash_mismatch")
            verified[name] = actual
        onnxruntime = importlib.import_module("onnxruntime")
        if EXECUTION_PROVIDER not in tuple(onnxruntime.get_available_providers()):
            raise RuntimeError("cpu_provider_unavailable")
        self._preflight_complete = True
        return {
            "sealed_interpreter_exact": True,
            "piper_version": PIPER_VERSION,
            "onnxruntime_version": _LOCKED_ONNXRUNTIME_VERSION,
            "model_sha256": verified["model_sha256"],
            "config_sha256": verified["config_sha256"],
            "execution_provider": EXECUTION_PROVIDER,
            "voice_id": MODEL_ID,
            "output_format": OUTPUT_FORMAT,
        }

    def create_locked_runtime(self) -> _LockedPiperRuntime:
        if not self._preflight_complete or self._used:
            raise RuntimeError("runtime_factory_not_permitted")
        self._used = True
        return _LockedPiperRuntime()


class CanonicalExclusiveWavWriter:
    """Direct one-write exclusive creator bound to the canonical WAV path."""

    __slots__ = ("_used",)

    def __init__(self) -> None:
        self._used = False

    def write_wav_exclusive(self, wav_bytes: object) -> dict[str, object]:
        if self._used:
            raise RuntimeError("wav_writer_already_used")
        if type(wav_bytes) is not bytes or not wav_bytes:
            raise ValueError("wav_payload_invalid")
        self._used = True
        if not _is_safe_directory(_OUTPUT_ROOT):
            raise RuntimeError("output_root_unsafe")
        if os.path.lexists(_OUTPUT_PATH):
            raise FileExistsError("canonical_output_exists")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_BINARY", 0)
        descriptor = os.open(_OUTPUT_PATH, flags, 0o600)
        try:
            written = os.write(descriptor, wav_bytes)
            if written != len(wav_bytes):
                raise RuntimeError("exclusive_wav_write_incomplete")
        finally:
            os.close(descriptor)
        return {
            "exclusive_create": True,
            "output_file_count": 1,
            "output_write_count": 1,
            "byte_count": len(wav_bytes),
            "sha256": hashlib.sha256(wav_bytes).hexdigest(),
        }
