"""Fixed, import-inert boundary for one future L8 sealed-interpreter launch.

This module deliberately owns no authorization, audit, filesystem, model, text,
or media capability.  The L7C caller validates and durably records authorization
before it invokes this boundary.  L7G tests inject only a narrow fake process
launcher; the default launcher is never called during offline certification.
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import PureWindowsPath

from l7_piper_synthetic_authorization_contract import (
    L8_AUTHORIZED_NOT_EXECUTED,
    L8_EXECUTABLE_OUTPUT_FILENAME,
    L8_EXECUTABLE_OUTPUT_ROOT,
)
from l8_one_time_piper_synthetic_runner import (
    L8SyntheticRunnerResult,
    _SAFE_CHILD_ERROR_CATEGORIES,
    _SAFE_CHILD_UNKNOWN_OUTPUT_CATEGORIES,
    _SEALED_INTERPRETER_ENTRYPOINT_SOURCE,
)

__all__ = ["CanonicalL8SealedInterpreterBoundary"]

_SEALED_INTERPRETER_PATH = (
    r"C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe"
)
_FIXED_ARGUMENT_FLAG = "-c"
_MAXIMUM_SAFE_CHILD_STDOUT_CHARACTERS = 8192
_EXPECTED_CHILD_FIELDS = frozenset(L8SyntheticRunnerResult.__slots__) | {
    "interface_binding"
}
_EXPECTED_OUTPUT_PATH = str(
    PureWindowsPath(L8_EXECUTABLE_OUTPUT_ROOT)
    / L8_EXECUTABLE_OUTPUT_FILENAME
)
_AUTHORIZATION_ID_PATTERN = re.compile(
    r"L8-SYNTHETIC-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_COUNT_FIELDS = (
    "sealed_interpreter_process_count",
    "runtime_process_count",
    "session_initialization_count",
    "text_input_count",
    "synthesis_attempt_count",
    "output_file_count",
    "output_write_count",
)


class _FixedSubprocessLauncher:
    """The only production launcher; invoked only by the public boundary."""

    def launch_fixed_once(self, command: tuple[str, str, str]) -> object:
        # Delayed import keeps module import inert during offline certification.
        import subprocess

        return subprocess.run(
            command,
            check=False,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )


def _has_exact_fixed_launcher_interface(value: object) -> bool:
    if value is None:
        return False
    public_methods = {
        name
        for name, member in type(value).__dict__.items()
        if not name.startswith("_") and callable(member)
    }
    return public_methods == {"launch_fixed_once"}


def _is_authorization_id(value: object) -> bool:
    if type(value) is not str or _AUTHORIZATION_ID_PATTERN.fullmatch(value) is None:
        return False
    try:
        parsed = uuid.UUID(value[len("L8-SYNTHETIC-") :])
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value[len("L8-SYNTHETIC-") :]


def _is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256_PATTERN.fullmatch(value) is not None


def _safe_bootstrap_failure() -> dict[str, object]:
    return {
        "outcome": "EXECUTION_FAILED_CLOSED",
        "safe_error_category": "sealed_bootstrap_failed",
        "interface_binding": "failed_before_runner_result",
        "authorization_id": None,
        "nonce_fingerprint": None,
        "lifecycle_status": L8_AUTHORIZED_NOT_EXECUTED,
        "sealed_interpreter_process_count": 1,
        "runtime_process_count": 0,
        "session_initialization_count": 0,
        "text_input_count": 0,
        "synthesis_attempt_count": 0,
        "output_file_count": 0,
        "output_write_count": 0,
        "output_state_unknown": False,
        "retry_count": 0,
        "fallback_count": 0,
        "output_path": None,
        "output_byte_count": None,
        "output_sha256": None,
    }


def _safe_child_result(value: object) -> dict[str, object] | None:
    if type(value) is not str or len(value) > _MAXIMUM_SAFE_CHILD_STDOUT_CHARACTERS:
        return None
    try:
        payload = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if type(payload) is not dict or set(payload) != _EXPECTED_CHILD_FIELDS:
        return None
    if type(payload["interface_binding"]) is not str or payload["interface_binding"] not in (
        "succeeded",
        "failed_before_runner_result",
    ):
        return None
    if type(payload["outcome"]) is not str or payload["outcome"] not in (
        "ONE_SYNTHETIC_OUTPUT_CREATED",
        "EXECUTION_FAILED_CLOSED",
    ):
        return None
    if payload["outcome"] == "ONE_SYNTHETIC_OUTPUT_CREATED":
        if payload["safe_error_category"] is not None:
            return None
    elif (
        type(payload["safe_error_category"]) is not str
        or payload["safe_error_category"] not in _SAFE_CHILD_ERROR_CATEGORIES
    ):
        return None
    if payload["authorization_id"] is not None and not _is_authorization_id(
        payload["authorization_id"]
    ):
        return None
    if payload["nonce_fingerprint"] is not None and not _is_sha256(
        payload["nonce_fingerprint"]
    ):
        return None
    if (
        type(payload["lifecycle_status"]) is not str
        or payload["lifecycle_status"] != L8_AUTHORIZED_NOT_EXECUTED
    ):
        return None
    if any(type(payload[field]) is not int or payload[field] < 0 or payload[field] > 1 for field in _COUNT_FIELDS):
        return None
    if (
        type(payload["output_state_unknown"]) is not bool
        or type(payload["retry_count"]) is not int
        or payload["retry_count"] != 0
        or type(payload["fallback_count"]) is not int
        or payload["fallback_count"] != 0
    ):
        return None
    if (
        payload["output_path"] is not None
        and (
            type(payload["output_path"]) is not str
            or payload["output_path"] != _EXPECTED_OUTPUT_PATH
        )
    ):
        return None
    if payload["output_byte_count"] is not None and (
        type(payload["output_byte_count"]) is not int
        or payload["output_byte_count"] <= 0
    ):
        return None
    if payload["output_sha256"] is not None and not _is_sha256(
        payload["output_sha256"]
    ):
        return None
    if (
        payload["output_state_unknown"]
        and payload["safe_error_category"] not in _SAFE_CHILD_UNKNOWN_OUTPUT_CATEGORIES
    ):
        return None
    return {field: payload[field] for field in _EXPECTED_CHILD_FIELDS}


class CanonicalL8SealedInterpreterBoundary:
    """One-shot fixed boundary compatible with L7C's existing launch call."""

    def __init__(self, *, process_launcher: object | None = None) -> None:
        candidate = _FixedSubprocessLauncher() if process_launcher is None else process_launcher
        if not _has_exact_fixed_launcher_interface(candidate):
            raise ValueError("fixed_process_launcher_interface_invalid")
        self._process_launcher = candidate
        self._launch_claimed = False

    def launch_canonical_once(self, entrypoint_source: object) -> dict[str, object]:
        """Launch only the exact existing L7E entrypoint, once, without a shell."""
        if self._launch_claimed:
            raise RuntimeError("sealed_boundary_already_used")
        if entrypoint_source is not _SEALED_INTERPRETER_ENTRYPOINT_SOURCE:
            raise ValueError("sealed_entrypoint_source_mismatch")
        self._launch_claimed = True
        command = (
            _SEALED_INTERPRETER_PATH,
            _FIXED_ARGUMENT_FLAG,
            _SEALED_INTERPRETER_ENTRYPOINT_SOURCE,
        )
        try:
            completed = self._process_launcher.launch_fixed_once(command)
        except Exception:
            return _safe_bootstrap_failure()
        returncode = getattr(completed, "returncode", None)
        stdout = getattr(completed, "stdout", None)
        if type(returncode) is not int or returncode != 0:
            return _safe_bootstrap_failure()
        safe_result = _safe_child_result(stdout)
        return safe_result if safe_result is not None else _safe_bootstrap_failure()
