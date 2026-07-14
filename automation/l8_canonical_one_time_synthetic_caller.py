"""Canonical zero-argument ordinary caller for one future authorized L8 attempt.

Importing this module is inert. The public entrypoint is not exercised by L7H;
offline tests use only the private dependency seam with in-memory fakes.
"""
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from l7_piper_synthetic_authorization_contract import (
    L8ExecutableSyntheticAuthorizationValidator,
    create_l8_executable_synthetic_authorization,
)
from l8_local_dependency_adapters import (
    SafeL8LifecycleAuditSink,
    UtcL8Clock,
    _FIXED_TEXT_SHA256,
)
from l8_one_time_piper_synthetic_runner import (
    L8SyntheticRunnerResult,
    execute_one_time_piper_synthetic,
)
from l8_sealed_interpreter_boundary import CanonicalL8SealedInterpreterBoundary

__all__ = ["main"]

_AUTHORIZATION_LIFETIME = timedelta(minutes=10)


class _FreshIdentitySource:
    __slots__ = ()

    def fresh_authorization_id(self) -> str:
        return f"L8-SYNTHETIC-{uuid.uuid4()}"

    def fresh_nonce(self) -> str:
        return uuid.uuid4().hex + uuid.uuid4().hex


def _has_exact_interface(value: object, methods: tuple[str, ...]) -> bool:
    if value is None:
        return False
    public_methods = {
        name
        for name, member in type(value).__dict__.items()
        if not name.startswith("_") and callable(member)
    }
    return public_methods == set(methods)


def _safe_failure(category: str) -> L8SyntheticRunnerResult:
    return L8SyntheticRunnerResult(
        outcome="EXECUTION_FAILED_CLOSED",
        safe_error_category=category,
        authorization_id=None,
        nonce_fingerprint=None,
        lifecycle_status=None,
        sealed_interpreter_process_count=0,
        runtime_process_count=0,
        session_initialization_count=0,
        text_input_count=0,
        synthesis_attempt_count=0,
        output_file_count=0,
        output_write_count=0,
        output_state_unknown=False,
        retry_count=0,
        fallback_count=0,
        output_path=None,
        output_byte_count=None,
        output_sha256=None,
    )


def _expiration_from(now: object) -> str | None:
    if type(now) is not datetime or now.tzinfo is None:
        return None
    expiration = now.astimezone(timezone.utc) + _AUTHORIZATION_LIFETIME
    return expiration.isoformat(timespec="seconds").replace("+00:00", "Z")


def _execute_with_dependencies(
    *,
    clock: object,
    identity_source: object,
    safe_audit_sink: object,
    sealed_interpreter_boundary: object,
) -> L8SyntheticRunnerResult:
    interfaces = (
        (clock, ("now_utc",)),
        (
            identity_source,
            ("fresh_authorization_id", "fresh_nonce"),
        ),
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
        return _safe_failure("caller_dependency_interface_invalid")
    try:
        now = clock.now_utc()
        expiration = _expiration_from(now)
        authorization_id = identity_source.fresh_authorization_id()
        nonce = identity_source.fresh_nonce()
        if expiration is None:
            return _safe_failure("caller_clock_invalid")
        candidate = create_l8_executable_synthetic_authorization(
            text_sha256=_FIXED_TEXT_SHA256,
            expiration_timestamp=expiration,
            preflight_validated=True,
            authorization_id=authorization_id,
            single_use_nonce=nonce,
        )
    except Exception:
        return _safe_failure("candidate_construction_failed")
    validation = (
        L8ExecutableSyntheticAuthorizationValidator()
        .validate_l8_executable_synthetic_authorization(candidate)
    )
    if not validation.valid:
        return _safe_failure(
            validation.safe_error_category or "authorization_preflight_failed"
        )
    return execute_one_time_piper_synthetic(
        authorization=candidate,
        clock=clock,
        safe_audit_sink=safe_audit_sink,
        sealed_interpreter_boundary=sealed_interpreter_boundary,
    )


def _execute_canonical_one_time_synthetic() -> L8SyntheticRunnerResult:
    return _execute_with_dependencies(
        clock=UtcL8Clock(),
        identity_source=_FreshIdentitySource(),
        safe_audit_sink=SafeL8LifecycleAuditSink(),
        sealed_interpreter_boundary=CanonicalL8SealedInterpreterBoundary(),
    )


def main() -> int:
    if len(sys.argv) != 1:
        return 2
    result = _execute_canonical_one_time_synthetic()
    print(json.dumps(asdict(result), sort_keys=True))
    return 0 if result.outcome == "ONE_SYNTHETIC_OUTPUT_CREATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
