"""Provider-neutral Phase C7 interface with an exact fake-client allowlist."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from c6_synthetic_narration_gate import READY, validate_synthetic_narration
from testing.c7_fake_http_client import C7AllowlistedFakeLocalHttpClient, EXPECTED_CAPABILITIES


C7_READY = "C7_MOCK_PROVIDER_REQUEST_READY"
C7_BLOCKED = "C7_MOCK_PROVIDER_REQUEST_BLOCKED"
ALLOWED_REQUEST_KEYS = {
    "schema_version", "request_kind", "synthetic_text", "voice_profile",
    "output_format", "output_reference", "source_output_binding_sha256",
    "permissions",
}
ALLOWED_PROFILE_KEYS = {
    "voice_profile_name", "stability", "similarity_boost", "style", "speed",
    "use_speaker_boost",
}
PERMISSION_KEYS = {
    "provider_invoked", "network_invoked", "audio_file_created",
    "asset_authorized", "assembly_authorized", "rendering_authorized",
    "upload_authorized", "scheduling_authorized", "publishing_enabled",
    "real_production_enabled",
}
ALLOWLISTED_SEND_METHOD = C7AllowlistedFakeLocalHttpClient.send_mock


def _blocked(reason: str) -> dict[str, Any]:
    return {
        "state": C7_BLOCKED, "safe_reason_code": reason,
        "client_method_invoked": False, "provider_invoked": False,
        "network_invoked": False, "audio_file_created": False,
        "publishing_enabled": False, "real_production_enabled": False,
    }


class NarrationProviderAdapter:
    """Builds one sanitized in-memory contract and calls only the exact fake type."""

    def __init__(self, *, fixture_root: Path, c6_state_root: Path, c7_output_root: Path) -> None:
        self.fixture_root = fixture_root.resolve()
        self.c6_state_root = c6_state_root.resolve()
        self.c7_output_root = c7_output_root.resolve()
        expected_c7_root = self.fixture_root / "narration_preflight" / "output" / "c7_mock_provider_adapter"
        try:
            self.c7_output_root.relative_to(expected_c7_root.resolve())
        except ValueError as exc:
            raise ValueError("C7 output root escapes fixture boundary") from exc

    @staticmethod
    def _client_is_allowlisted(client: Any) -> bool:
        return (
            type(client) is C7AllowlistedFakeLocalHttpClient
            and client.test_only_identity == "cold-truth-c7-allowlisted-fake-local-http-client"
            and client.capability_declarations == EXPECTED_CAPABILITIES
            and type(client).send_mock is ALLOWLISTED_SEND_METHOD
            and "send_mock" not in getattr(client, "__dict__", {})
        )

    def execute(self, *, client: Any, **c6_paths: Any) -> dict[str, Any]:
        if client is None:
            return _blocked("injected_client_missing")
        if not self._client_is_allowlisted(client):
            return _blocked("injected_client_not_exactly_allowlisted")
        c6_result = validate_synthetic_narration(
            fixture_root=self.fixture_root, state_root=self.c6_state_root, **c6_paths
        )
        if c6_result.get("state") != READY:
            return _blocked("c6_validation_failed")
        try:
            writer = json.loads(Path(c6_paths["writer_path"]).read_text(encoding="utf-8"))
            profile = json.loads(Path(c6_paths["profile_path"]).read_text(encoding="utf-8"))
            c6_request = json.loads(Path(c6_paths["request_path"]).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, KeyError):
            return _blocked("validated_fixture_input_unreadable")
        request_id = c6_request["request_id"]
        output_reference = Path("mock_requests") / f"{request_id}.request.json"
        resolved_reference = (self.c7_output_root / output_reference).resolve()
        try:
            resolved_reference.relative_to(self.c7_output_root)
        except ValueError:
            return _blocked("sanitized_output_reference_escape")
        if resolved_reference.suffix.lower() != ".json" or any(
            suffix in resolved_reference.name.lower() for suffix in (".mp3", ".wav", ".ogg", ".m4a")
        ):
            return _blocked("audio_extension_forbidden")
        source_binding = c6_request["requested_output_relative_path"]
        sanitized_request = {
            "schema_version": "1.0",
            "request_kind": "synthetic_narration_contract_preview",
            "synthetic_text": writer["result"]["narration_text"],
            "voice_profile": {
                "voice_profile_name": profile["voice_profile_name"],
                "stability": profile["stability"],
                "similarity_boost": profile["similarity_boost"],
                "style": profile["style"],
                "speed": profile["speed"],
                "use_speaker_boost": profile["use_speaker_boost"],
            },
            "output_format": profile["output_format"],
            "output_reference": output_reference.as_posix(),
            "source_output_binding_sha256": hashlib.sha256(source_binding.encode("utf-8")).hexdigest(),
            "permissions": {key: False for key in sorted(PERMISSION_KEYS)},
        }
        if set(sanitized_request) != ALLOWED_REQUEST_KEYS:
            return _blocked("sanitized_request_allowlist_violation")
        if set(sanitized_request["voice_profile"]) != ALLOWED_PROFILE_KEYS:
            return _blocked("sanitized_profile_allowlist_violation")
        if set(sanitized_request["permissions"]) != PERMISSION_KEYS or any(sanitized_request["permissions"].values()):
            return _blocked("sanitized_permission_violation")
        fake_metadata = client.send_mock(sanitized_request)
        expected_response_keys = {
            "response_kind", "request_sha256", "status", "provider_invoked",
            "network_invoked", "audio_bytes", "audio_file_created",
        }
        if set(fake_metadata) != expected_response_keys or any(
            (fake_metadata["provider_invoked"], fake_metadata["network_invoked"],
             fake_metadata["audio_file_created"], fake_metadata["audio_bytes"])
        ):
            return _blocked("fake_client_response_capability_violation")
        return {
            "state": C7_READY,
            "sanitized_request": sanitized_request,
            "fake_response_metadata": fake_metadata,
            "client_method_invoked": True,
            "provider_invoked": False,
            "network_invoked": False,
            "audio_file_created": False,
            "publishing_enabled": False,
            "real_production_enabled": False,
        }
