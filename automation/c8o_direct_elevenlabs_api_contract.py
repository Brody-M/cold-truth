"""Offline-only C8o contract for a future direct ElevenLabs HTTPS request."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from types import MappingProxyType
from typing import Any, Callable, Mapping


DIRECT_ROUTE = "direct_elevenlabs_https_api"
CREDENTIAL_PLACEHOLDER_NAMES = (
    "COLD_TRUTH_ELEVENLABS_API_KEY",
    "COLD_TRUTH_ELEVENLABS_MIA_VOICE_ID",
)
SYNTHETIC_TEXT = (
    "This is a controlled synthetic narration test. It contains no real case details "
    "and is used only to validate the Cold Truth narration-provider connection."
)
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
OUTPUT_PATH = (
    "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/"
    "disposable_output/c8_isolated_synthetic_connectivity.mp3"
)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_AUTHORIZATION_LIFETIME_SECONDS = 900

LOCKED_SETTINGS = MappingProxyType({
    "stability": 0.72,
    "similarity_boost": 0.76,
    "style": 0.05,
    "speed": 0.94,
    "use_speaker_boost": True,
})

AUTHORIZATION_FIELDS = frozenset({
    "schema_version", "authorization_phase", "authorization_id", "fixture_id",
    "test_classification", "real_case_content_allowed", "c4_approval_artifact_allowed",
    "c3_fixture_state_must_remain", "decision", "reviewer_role", "issued_at_utc",
    "expires_at_utc", "authorization_status", "consumed", "consumption_count",
    "single_use", "execution_transport", "maximum_transport_call_count",
    "authorized_output_count", "maximum_exclusive_create_write_count",
    "synthetic_text_sha256", "locked_profile_sha256", "authorized_output_path_sha256",
    "authorized_output_relative_path", "output_format", "retry_allowed",
    "redirect_allowed", "fallback_allowed", "polling_allowed", "status_call_allowed",
    "cleanup_allowed", "deletion_allowed", "copy_allowed", "overwrite_allowed",
    "batch_mode_allowed", "multi_output_allowed", "alternate_provider_allowed",
    "publishing_enabled", "real_production_enabled",
})

AUDIT_FIELDS = frozenset({
    "authorization_relative_path", "exists", "byte_count", "sha256", "extension",
    "contained", "transport_count", "success",
})

STATIC_AUTHORIZATION_VALUES = MappingProxyType({
    "schema_version": "1.0",
    "authorization_phase": "C8",
    "fixture_id": "c8-isolated-connectivity-fixture",
    "test_classification": "isolated_synthetic_provider_connectivity_test",
    "real_case_content_allowed": False,
    "c4_approval_artifact_allowed": False,
    "c3_fixture_state_must_remain": "AWAITING_SCRIPT_APPROVAL",
    "decision": "authorize_one_direct_elevenlabs_https_api_request",
    "reviewer_role": "human_owner",
    "authorization_status": "issued_unconsumed",
    "consumed": False,
    "consumption_count": 0,
    "single_use": True,
    "execution_transport": DIRECT_ROUTE,
    "maximum_transport_call_count": 1,
    "authorized_output_count": 1,
    "maximum_exclusive_create_write_count": 1,
    "synthetic_text_sha256": None,
    "locked_profile_sha256": None,
    "authorized_output_path_sha256": None,
    "authorized_output_relative_path": OUTPUT_PATH,
    "output_format": OUTPUT_FORMAT,
    "retry_allowed": False,
    "redirect_allowed": False,
    "fallback_allowed": False,
    "polling_allowed": False,
    "status_call_allowed": False,
    "cleanup_allowed": False,
    "deletion_allowed": False,
    "copy_allowed": False,
    "overwrite_allowed": False,
    "batch_mode_allowed": False,
    "multi_output_allowed": False,
    "alternate_provider_allowed": False,
    "publishing_enabled": False,
    "real_production_enabled": False,
})

READY = "C8O_DIRECT_API_FAKE_RESPONSE_WRITTEN"
BLOCKED = "C8O_DIRECT_API_BLOCKED"


def _canonical_sha256(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


SYNTHETIC_TEXT_SHA256 = _text_sha256(SYNTHETIC_TEXT)
LOCKED_PROFILE_SHA256 = _canonical_sha256({
    "model_id": MODEL_ID,
    "voice_settings": dict(LOCKED_SETTINGS),
    "output_format": OUTPUT_FORMAT,
})
OUTPUT_PATH_SHA256 = _text_sha256(OUTPUT_PATH)


def authorization_bindings() -> Mapping[str, str]:
    return MappingProxyType({
        "synthetic_text_sha256": SYNTHETIC_TEXT_SHA256,
        "locked_profile_sha256": LOCKED_PROFILE_SHA256,
        "authorized_output_path_sha256": OUTPUT_PATH_SHA256,
    })


def validate_authorization(record: Mapping[str, Any], *, now_utc: datetime) -> bool:
    if not isinstance(record, Mapping) or set(record) != AUTHORIZATION_FIELDS:
        return False
    expected = dict(STATIC_AUTHORIZATION_VALUES)
    expected.update(authorization_bindings())
    for field, value in expected.items():
        if record.get(field) != value:
            return False
    authorization_id = record.get("authorization_id")
    if not isinstance(authorization_id, str) or not re.fullmatch(r"C8O-[A-Z0-9_-]{16,92}", authorization_id):
        return False
    try:
        issued = datetime.strptime(record["issued_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
        expires = datetime.strptime(record["expires_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return False
    lifetime = (expires - issued).total_seconds()
    return 0 < lifetime <= MAX_AUTHORIZATION_LIFETIME_SECONDS and issued <= now_utc < expires


def _request_body_is_exact(
    *, text: str, model_id: str, voice_settings: Mapping[str, Any], output_format: str,
) -> bool:
    return (
        text == SYNTHETIC_TEXT
        and model_id == MODEL_ID
        and isinstance(voice_settings, Mapping)
        and dict(voice_settings) == dict(LOCKED_SETTINGS)
        and output_format == OUTPUT_FORMAT
    )


def _safe_audit(*, exists: bool, body: bytes | None, transport_count: int) -> Mapping[str, Any]:
    return MappingProxyType({
        "authorization_relative_path": OUTPUT_PATH,
        "exists": exists,
        "byte_count": len(body) if exists and body is not None else 0,
        "sha256": hashlib.sha256(body).hexdigest() if exists and body is not None else None,
        "extension": ".mp3",
        "contained": True,
        "transport_count": transport_count,
        "success": exists,
    })


def _blocked(reason: str, *, transport_count: int = 0) -> Mapping[str, Any]:
    return MappingProxyType({
        "state": BLOCKED,
        "safe_reason_code": reason,
        "audit": _safe_audit(exists=False, body=None, transport_count=transport_count),
    })


def _response_is_valid(response: Any) -> bool:
    if not isinstance(response, Mapping) or set(response) != {"status_code", "content_type", "body"}:
        return False
    if response["status_code"] != 200 or response["content_type"] != "audio/mpeg":
        return False
    body = response["body"]
    if not isinstance(body, bytes) or not body or len(body) > MAX_RESPONSE_BYTES:
        return False
    return body.startswith(b"ID3") or (
        len(body) >= 2 and body[0] == 0xFF and body[1] & 0xE0 == 0xE0
    )


class DirectElevenLabsApiAdapter:
    """Single-use adapter with injected transport and narrow exclusive writer only."""

    def __init__(self) -> None:
        self._consumed_authorization_ids: set[str] = set()

    def execute(
        self, *, authorization: Mapping[str, Any], now_utc: datetime,
        transport: Callable[..., Mapping[str, Any]], exclusive_writer: Callable[..., None],
        api_credential: Any, voice_identifier: Any, destination_exists: bool,
        text: str = SYNTHETIC_TEXT, model_id: str = MODEL_ID,
        voice_settings: Mapping[str, Any] = LOCKED_SETTINGS,
        output_format: str = OUTPUT_FORMAT, route: str = DIRECT_ROUTE,
        output_path: str = OUTPUT_PATH,
    ) -> Mapping[str, Any]:
        if not validate_authorization(authorization, now_utc=now_utc):
            return _blocked("authorization_invalid_or_expired")
        authorization_id = authorization["authorization_id"]
        if authorization_id in self._consumed_authorization_ids:
            return _blocked("authorization_replayed")
        if route != DIRECT_ROUTE or output_path != OUTPUT_PATH:
            return _blocked("route_or_output_binding_mismatch")
        if not _request_body_is_exact(
            text=text, model_id=model_id, voice_settings=voice_settings,
            output_format=output_format,
        ):
            return _blocked("synthetic_request_binding_mismatch")
        if destination_exists:
            return _blocked("destination_exists")
        if api_credential is None or voice_identifier is None:
            return _blocked("opaque_injected_value_missing")
        if not callable(transport) or not callable(exclusive_writer):
            return _blocked("injected_boundary_missing")

        self._consumed_authorization_ids.add(authorization_id)
        request_body = {
            "text": SYNTHETIC_TEXT,
            "model_id": MODEL_ID,
            "voice_settings": dict(LOCKED_SETTINGS),
        }
        try:
            response = transport(
                method="POST",
                route=DIRECT_ROUTE,
                credential=api_credential,
                voice_identifier=voice_identifier,
                output_format=OUTPUT_FORMAT,
                body=request_body,
            )
        except Exception:
            return _blocked("transport_failed_no_retry", transport_count=1)
        if not _response_is_valid(response):
            return _blocked("response_invalid_no_retry", transport_count=1)
        body = response["body"]
        try:
            exclusive_writer(relative_path=OUTPUT_PATH, data=body, exclusive_create=True)
        except Exception:
            return _blocked("exclusive_write_failed_no_retry", transport_count=1)
        return MappingProxyType({
            "state": READY,
            "safe_reason_code": "fake_mp3_response_exclusively_written",
            "audit": _safe_audit(exists=True, body=body, transport_count=1),
        })
