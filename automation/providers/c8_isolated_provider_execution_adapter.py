"""Non-executable isolated C8 request-shape adapter for offline Phase C8c."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from c8a_authorization_schema_validator import (
    PASSED, InMemoryReplayRegistry, canonical_sha256, text_sha256,
    validate_hypothetical_record,
)
from testing.c8c_fake_client import C8cAllowlistedFakeClient, EXPECTED_CAPABILITIES


READY = "C8C_REQUEST_SHAPE_READY_NON_EXECUTABLE"
BLOCKED = "C8C_REQUEST_SHAPE_BLOCKED"
ALLOWED_REQUEST_FIELDS = {
    "schema_version", "request_kind", "synthetic_text", "voice_profile",
    "output_format", "output_reference", "output_path_binding_sha256",
    "isolation", "permissions"
}
ALLOWED_PROFILE_FIELDS = {
    "voice_profile_name", "stability", "similarity_boost", "style", "speed",
    "use_speaker_boost"
}
ISOLATION_FIELDS = {
    "test_classification", "real_case_content_allowed", "real_script_approval_used",
    "c4_approval_artifact_allowed", "c3_fixture_state_must_remain"
}
PERMISSION_FIELDS = {
    "synthetic_provider_operation_hypothetically_authorized",
    "execution_authorized", "network_authorized", "provider_invoked",
    "audio_file_created", "retry_allowed", "maximum_provider_request_count",
    "redirects_allowed", "fallback_allowed", "alternate_provider_allowed",
    "batch_allowed", "multi_output_allowed", "authorized_output_count",
    "asset_authorized", "assembly_authorized", "rendering_authorized",
    "upload_authorized", "scheduling_authorized", "publishing_enabled",
    "real_production_enabled"
}
ALLOWLISTED_INSPECTION_METHOD = C8cAllowlistedFakeClient.inspect_request


def _blocked(reason: str) -> dict[str, Any]:
    return {
        "state": BLOCKED, "safe_reason_code": reason,
        "execution_authorized": False, "client_method_invoked": False,
        "external_call_made": False, "provider_invoked": False,
        "network_invoked": False, "audio_file_created": False,
        "publishing_enabled": False, "real_production_enabled": False
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class C8IsolatedProviderExecutionAdapter:
    """Validates and inspects one hypothetical request; it cannot execute it."""

    def __init__(self, *, future_c8_root: Path, disposable_output_root: Path,
                 schema_path: Path, contract_path: Path, locked_profile_path: Path) -> None:
        self.future_root = future_c8_root.resolve()
        self.output_root = disposable_output_root.resolve()
        self.schema_path = schema_path.resolve()
        self.contract_path = contract_path.resolve()
        self.profile_path = locked_profile_path.resolve()
        if self.output_root != (self.future_root / "disposable_output").resolve():
            raise ValueError("C8c output root escapes future C8 disposable boundary")
        if not _inside(self.schema_path, self.future_root) or not _inside(self.contract_path, self.future_root):
            raise ValueError("C8c schema or contract path escapes future C8 boundary")
        narration_root = self.future_root.parent
        if not _inside(self.profile_path, narration_root):
            raise ValueError("Locked profile path escapes narration fixture boundary")
        self._replay_registry = InMemoryReplayRegistry()

    @staticmethod
    def _client_is_allowlisted(client: Any) -> bool:
        return (
            type(client) is C8cAllowlistedFakeClient
            and client.test_only_identity == "cold-truth-c8c-isolated-fake-inspector"
            and client.capability_declarations == EXPECTED_CAPABILITIES
            and type(client).inspect_request is ALLOWLISTED_INSPECTION_METHOD
            and "inspect_request" not in getattr(client, "__dict__", {})
        )

    def validate_and_inspect(self, *, authorization_record: dict[str, Any],
                             fixture_text: str, locked_profile: dict[str, Any],
                             output_relative_path: str, client: Any) -> dict[str, Any]:
        if client is None:
            return _blocked("injected_test_client_missing")
        if not self._client_is_allowlisted(client):
            return _blocked("injected_test_client_not_exactly_allowlisted")
        try:
            schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
            contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
            profile_fixture = json.loads(self.profile_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return _blocked("static_fixture_specification_unreadable")
        if text_sha256(fixture_text) != contract.get("isolated_fixture_text_sha256"):
            return _blocked("invented_fixture_text_mismatch")
        if _file_sha256(self.profile_path) != contract.get("locked_mia_profile_file_sha256"):
            return _blocked("locked_profile_file_hash_mismatch")
        if locked_profile != profile_fixture:
            return _blocked("locked_profile_input_mismatch")
        profile_values = {key: profile_fixture[key] for key in contract["locked_mia_profile"]}
        if profile_values != contract["locked_mia_profile"]:
            return _blocked("locked_profile_contract_mismatch")
        expected_bindings = {
            "fixture_text_sha256": contract["isolated_fixture_text_sha256"],
            "locked_mia_profile_sha256": contract["locked_mia_profile_file_sha256"],
            "c7_provider_request_contract_sha256": canonical_sha256(contract["c7_provider_request_contract"]),
            "provider_request_allowlist_sha256": canonical_sha256(contract["c7_sanitized_request_allowlist"]),
            "authorized_output_relative_path": output_relative_path,
            "authorized_output_path_sha256": text_sha256(output_relative_path)
        }
        before = canonical_sha256(authorization_record)
        validation = validate_hypothetical_record(
            record=authorization_record, schema=schema,
            expected_bindings=expected_bindings, future_c8_root=self.future_root,
            disposable_output_root=self.output_root,
            replay_registry=self._replay_registry
        )
        if validation.get("state") != PASSED:
            return _blocked("isolated_c8_authorization_shape_invalid")
        if canonical_sha256(authorization_record) != before:
            return _blocked("authorization_record_mutated")
        permissions = {
            "synthetic_provider_operation_hypothetically_authorized": True,
            "execution_authorized": False, "network_authorized": False,
            "provider_invoked": False, "audio_file_created": False,
            "retry_allowed": False, "maximum_provider_request_count": 1,
            "redirects_allowed": False, "fallback_allowed": False,
            "alternate_provider_allowed": False, "batch_allowed": False,
            "multi_output_allowed": False, "authorized_output_count": 1,
            "asset_authorized": False, "assembly_authorized": False,
            "rendering_authorized": False, "upload_authorized": False,
            "scheduling_authorized": False, "publishing_enabled": False,
            "real_production_enabled": False
        }
        request = {
            "schema_version": "1.0",
            "request_kind": "isolated_synthetic_provider_connectivity_preview",
            "synthetic_text": fixture_text,
            "voice_profile": {key: profile_values[key] for key in ALLOWED_PROFILE_FIELDS},
            "output_format": profile_fixture["output_format"],
            "output_reference": output_relative_path,
            "output_path_binding_sha256": text_sha256(output_relative_path),
            "isolation": {
                "test_classification": authorization_record["test_classification"],
                "real_case_content_allowed": False,
                "real_script_approval_used": False,
                "c4_approval_artifact_allowed": False,
                "c3_fixture_state_must_remain": "AWAITING_SCRIPT_APPROVAL"
            },
            "permissions": permissions
        }
        if set(request) != ALLOWED_REQUEST_FIELDS or set(request["voice_profile"]) != ALLOWED_PROFILE_FIELDS:
            return _blocked("sanitized_request_allowlist_violation")
        if set(request["isolation"]) != ISOLATION_FIELDS or set(request["permissions"]) != PERMISSION_FIELDS:
            return _blocked("sanitized_boundary_allowlist_violation")
        fake_metadata = client.inspect_request(request)
        expected_metadata_fields = {
            "metadata_kind", "request_sha256", "external_call_made", "provider_invoked",
            "network_invoked", "audio_bytes", "audio_file_created"
        }
        if set(fake_metadata) != expected_metadata_fields or any((
            fake_metadata["external_call_made"], fake_metadata["provider_invoked"],
            fake_metadata["network_invoked"], fake_metadata["audio_file_created"],
            fake_metadata["audio_bytes"]
        )):
            return _blocked("fake_client_metadata_boundary_violation")
        return {
            "state": READY, "execution_authorized": False,
            "sanitized_request": request, "fake_metadata": fake_metadata,
            "client_method_invoked": True, "external_call_made": False,
            "provider_invoked": False, "network_invoked": False,
            "audio_file_created": False, "authorization_artifact_created": False,
            "authorization_record_consumed": False,
            "publishing_enabled": False, "real_production_enabled": False
        }
