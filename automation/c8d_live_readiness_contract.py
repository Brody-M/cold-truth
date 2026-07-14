"""Declarative, offline-only readiness contract for a future isolated C8 call."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Protocol


CANONICAL_OUTPUT_ROOT_WORKSPACE_RELATIVE = "automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output"
CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE = CANONICAL_OUTPUT_ROOT_WORKSPACE_RELATIVE + "/c8_isolated_synthetic_connectivity.mp3"
AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION = "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output/c8_isolated_synthetic_connectivity.mp3"
OUTPUT_PATH_BASIS = "relative_to_automation_directory"

TRANSPORT_INTERFACE_ID = "future-c8-injected-single-request-in-process-transport"
TRANSPORT_METHOD = "perform_single_authorized_request"
TRANSPORT_CAPABILITIES = MappingProxyType({
    "in_process_only": True,
    "subprocess_capable": False,
    "browser_capable": False,
    "mcp_capable": False,
    "node_capable": False,
    "retry_capable": False,
    "redirect_capable": False,
    "fallback_capable": False,
    "discovery_capable": False,
    "batch_capable": False,
    "multi_output_capable": False,
    "follow_up_capable": False,
    "polling_capable": False,
    "status_request_capable": False,
    "cleanup_request_capable": False,
    "deletion_request_capable": False,
    "maximum_outbound_request_count": 1,
    "raw_response_exposure": False,
    "endpoint_exposure": False,
    "header_exposure": False,
    "account_detail_exposure": False,
    "filesystem_audio_capable": False,
    "arbitrary_request_capable": False,
    "default_instance_available": False,
    "global_registration_available": False
})

OPAQUE_PROVIDER_INTERFACE_ID = "future-c8-injected-opaque-provider-capability-source"
OPAQUE_PROVIDER_METHOD = "acquire_one_opaque_capability"
OPAQUE_PROVIDER_CAPABILITIES = MappingProxyType({
    "explicit_injection_only": True,
    "default_instance_available": False,
    "environment_reading": False,
    "configuration_reading": False,
    "raw_secret_returning": False,
    "endpoint_returning": False,
    "voice_identifier_returning": False,
    "header_returning": False,
    "account_detail_returning": False,
    "serializable_capability": False,
    "printable_capability": False,
    "credential_write_capable": False,
    "credential_rotate_capable": False,
    "credential_export_capable": False,
    "credential_validate_capable": False,
    "generic_configuration_api": False,
    "arbitrary_callable_wrapper": False,
    "arbitrary_slot_lookup": False,
    "wildcard_slot_lookup": False,
    "configuration_enumeration": False,
    "path_traversal_lookup": False
})


class FutureOpaqueProviderCapability(Protocol):
    """Marker passed directly from its source to the future transport."""


class FutureOpaqueProviderCapabilitySource(Protocol):
    interface_identity: str
    capability_declarations: Mapping[str, bool]

    def acquire_one_opaque_capability(
        self, runner_identity: str, authorization_digest: str,
        requested_slots: tuple[str, ...]
    ) -> FutureOpaqueProviderCapability: ...


class FutureC8LiveTransport(Protocol):
    interface_identity: str
    capability_declarations: Mapping[str, bool]

    def perform_single_authorized_request(
        self, sanitized_request: Mapping[str, Any],
        opaque_provider_capability: FutureOpaqueProviderCapability
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class ResolvedC8Output:
    canonical_output_root: Path
    canonical_output_file: Path
    authorization_relative_path: str
    workspace_relative_path: str


def resolve_canonical_c8_output(
    *, workspace_root: Path, authorization_relative_path: str,
    require_absent: bool = True
) -> ResolvedC8Output:
    if not isinstance(authorization_relative_path, str) or "\\" in authorization_relative_path:
        raise ValueError("authorization output must be a forward-slash relative path")
    pure = PurePosixPath(authorization_relative_path)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ValueError("authorization output path is absolute or escaping")
    if authorization_relative_path != AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION:
        raise ValueError("authorization output path is not the one canonical automation-relative path")
    workspace = workspace_root.resolve()
    automation_root = (workspace / "automation").resolve()
    canonical_root = (workspace / Path(CANONICAL_OUTPUT_ROOT_WORKSPACE_RELATIVE)).resolve()
    resolved = (automation_root / Path(*pure.parts)).resolve()
    expected = (workspace / Path(CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE)).resolve()
    try:
        resolved.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError("authorization output escapes canonical C8 root") from exc
    if resolved != expected or resolved.parent != canonical_root or resolved.suffix.lower() != ".mp3":
        raise ValueError("authorization output does not resolve to the exact canonical C8 file")
    if require_absent and resolved.exists():
        raise FileExistsError("canonical C8 output already exists")
    return ResolvedC8Output(
        canonical_output_root=canonical_root,
        canonical_output_file=resolved,
        authorization_relative_path=authorization_relative_path,
        workspace_relative_path=CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE
    )


def transport_declaration_is_compatible(*, identity: str, capabilities: Mapping[str, Any], method_names: set[str]) -> bool:
    return identity == TRANSPORT_INTERFACE_ID and dict(capabilities) == dict(TRANSPORT_CAPABILITIES) and method_names == {TRANSPORT_METHOD}


def opaque_provider_declaration_is_compatible(*, identity: str, capabilities: Mapping[str, Any], method_names: set[str]) -> bool:
    return identity == OPAQUE_PROVIDER_INTERFACE_ID and dict(capabilities) == dict(OPAQUE_PROVIDER_CAPABILITIES) and method_names == {OPAQUE_PROVIDER_METHOD}
