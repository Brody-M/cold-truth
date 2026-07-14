"""Offline-only active C8h contract for one future ElevenLabs MCP operation."""
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping


EXECUTION_TRANSPORT = "existing_configured_elevenlabs_mcp"
TEST_CLASSIFICATION = "isolated_synthetic_provider_connectivity_test"
OPERATION_SCOPE = "one_synthetic_narration_mcp_operation_only"

ACTIVE_MCP_ROUTE = MappingProxyType({
    "execution_transport": EXECUTION_TRANSPORT,
    "mcp_operation_allowed": True,
    "maximum_mcp_operation_count": 1,
    "maximum_provider_request_count": 1,
    "retry_allowed": False,
    "redirect_allowed": False,
    "fallback_allowed": False,
    "alternate_provider_allowed": False,
    "provider_discovery_allowed": False,
    "batch_mode_allowed": False,
    "multi_output_allowed": False,
    "status_or_polling_allowed": False,
    "cleanup_or_delete_allowed": False,
    "credential_access_allowed": False,
    "configuration_inspection_allowed": False,
    "environment_access_allowed": False,
    "voice_identifier_inspection_allowed": False,
    "account_data_access_allowed": False,
    "other_mcp_tools_allowed": False,
})

HISTORICAL_ROUTES = MappingProxyType({
    "direct_http_transport_active": False,
    "local_python_runner_active": False,
    "opaque_capability_slots_active": False,
    "option_a_environment_injection_active": False,
    "option_b_private_config_active": False,
})

FORBIDDEN_ACTIVE_AUTHORIZATION_FIELDS = frozenset({
    "runner_identity", "local_python_runner_launch_authorized",
    "maximum_runner_launch_count", "opaque_capability_handoff_authorized",
    "in_process_http_request_authorized", "provider_api_credential",
    "locked_voice_identifier", "environment_variable_names",
    "local_config_path", "direct_http_transport", "http_client",
    "endpoint", "api_key", "voice_id", "account_data", "headers",
    "case_id", "real_case_text", "real_script_reference", "writer_handoff",
    "editor_handoff", "c4_approval", "c5_preflight", "c6_authorization",
    "c7_runtime_execute_path",
})

SAFE_RESULT_FIELDS = frozenset({
    "authorization_relative_path", "output_exists", "byte_count", "sha256",
    "extension", "containment_result", "request_succeeded",
})


def active_route_is_exact(route: Mapping[str, Any]) -> bool:
    return isinstance(route, Mapping) and dict(route) == dict(ACTIVE_MCP_ROUTE)


def authorization_contains_no_inactive_or_sensitive_field(record: Mapping[str, Any]) -> bool:
    return isinstance(record, Mapping) and set(record).isdisjoint(FORBIDDEN_ACTIVE_AUTHORIZATION_FIELDS)


def safe_result_shape_is_exact(record: Mapping[str, Any]) -> bool:
    return isinstance(record, Mapping) and set(record) == SAFE_RESULT_FIELDS


def historical_routes_are_inactive(status: Mapping[str, Any]) -> bool:
    return isinstance(status, Mapping) and dict(status) == dict(HISTORICAL_ROUTES)

