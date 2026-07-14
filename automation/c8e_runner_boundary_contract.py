"""Declarative offline contract for one future C8 local Python runner launch."""
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping, Protocol

from c8d_live_readiness_contract import FutureC8LiveTransport, FutureOpaqueProviderCapabilitySource


RUNNER_IDENTITY = "c8_one_time_isolated_provider_runner"
RUNNER_METHOD = "run_once_with_consumed_authorization"
FIXED_OPAQUE_CONFIGURATION_SLOTS = (
    "provider_api_credential",
    "locked_voice_identifier"
)
RUNNER_CAPABILITIES = MappingProxyType({
    "future_authorized_local_python_launch_count": 1,
    "valid_c8_authorization_required": True,
    "authorization_must_be_consumed_before_request": True,
    "maximum_http_request_count": 1,
    "maximum_mp3_output_count": 1,
    "maximum_safe_audit_record_count": 1,
    "child_process_capable": False,
    "subprocess_capable": False,
    "shell_capable": False,
    "powershell_capable": False,
    "cmd_capable": False,
    "node_capable": False,
    "browser_capable": False,
    "mcp_capable": False,
    "codex_capable": False,
    "external_command_capable": False,
    "retry_capable": False,
    "redirect_capable": False,
    "fallback_capable": False,
    "discovery_capable": False,
    "polling_capable": False,
    "status_request_capable": False,
    "follow_up_capable": False,
    "cleanup_request_capable": False,
    "deletion_request_capable": False,
    "batch_capable": False,
    "multi_output_capable": False,
    "reusable": False,
    "scheduled": False,
    "default_registered": False,
    "global_registered": False,
    "production_enabled": False
})


class FutureC8OneTimeRunner(Protocol):
    runner_identity: str
    capability_declarations: Mapping[str, Any]

    def run_once_with_consumed_authorization(
        self, authorization_digest: str,
        live_transport: FutureC8LiveTransport,
        opaque_capability_source: FutureOpaqueProviderCapabilitySource
    ) -> Mapping[str, Any]: ...


def runner_declaration_is_compatible(*, identity: str, capabilities: Mapping[str, Any], method_names: set[str]) -> bool:
    return identity == RUNNER_IDENTITY and dict(capabilities) == dict(RUNNER_CAPABILITIES) and method_names == {RUNNER_METHOD}


def opaque_slot_request_is_compatible(requested_slots: tuple[str, ...]) -> bool:
    return requested_slots == FIXED_OPAQUE_CONFIGURATION_SLOTS


def opaque_capability_shape_is_compatible(
    *, public_field_names: set[str], method_names: set[str],
    printable: bool, serializable: bool
) -> bool:
    return not public_field_names and not method_names and printable is False and serializable is False
