"""Offline-only contract for selecting one future C8 configuration source."""
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from c8e_runner_boundary_contract import (
    FIXED_OPAQUE_CONFIGURATION_SLOTS,
    RUNNER_IDENTITY,
)


OPTION_A = "process_environment_injection"
OPTION_B = "dedicated_ignored_local_json_file"
CONFIGURATION_MECHANISMS = (OPTION_A, OPTION_B)

OPTION_A_ENVIRONMENT_VARIABLE_NAMES = (
    "COLD_TRUTH_C8_PROVIDER_API_CREDENTIAL",
    "COLD_TRUTH_C8_LOCKED_VOICE_IDENTIFIER",
)
OPTION_B_CONFIG_PATH_WORKSPACE_RELATIVE = (
    "automation/private/c8_one_time_provider_config.json"
)
OPTION_B_CONFIG_FIELDS = FIXED_OPAQUE_CONFIGURATION_SLOTS
ACTIVE_FOR_CURRENT_C8 = False

OPTION_A_DESCRIPTOR_FIELDS = frozenset({
    "mechanism", "requested_slots", "environment_variable_names"
})
OPTION_B_DESCRIPTOR_FIELDS = frozenset({
    "mechanism", "requested_slots", "local_config_path", "local_config_fields"
})

FUTURE_CONFIGURATION_CAPABILITIES = MappingProxyType({
    "explicit_future_c8_authorization_required": True,
    "exactly_one_mechanism_required": True,
    "raw_values_transport_boundary_only": True,
    "generic_environment_access": False,
    "environment_enumeration": False,
    "generic_config_read": False,
    "directory_scan": False,
    "config_discovery": False,
    "fallback_source": False,
    "alternate_names": False,
    "wildcard_lookup": False,
    "arbitrary_slot_lookup": False,
    "path_traversal_lookup": False,
    "additional_slot_lookup": False,
    "credential_write": False,
    "credential_rotate": False,
    "credential_export": False,
    "credential_validate": False,
    "raw_value_print": False,
    "raw_value_log": False,
    "raw_value_serialize": False,
    "raw_value_hash": False,
    "raw_value_return": False,
    "raw_value_report": False,
    "raw_value_audit": False,
    "provider_execution_present_in_c8f": False,
    "network_present_in_c8f": False,
    "configuration_read_present_in_c8f": False,
})

PROHIBITED_RAW_VALUE_OPERATIONS = frozenset({
    "print", "log", "serialize", "hash", "return", "report", "audit",
    "exception", "test_output", "export", "validate", "copy"
})
ONLY_ALLOWED_RAW_VALUE_OPERATION = "pass_directly_to_single_authorized_transport"


def _exact_string_tuple(value: Any, expected: tuple[str, ...]) -> bool:
    return isinstance(value, tuple) and value == expected


def configuration_descriptor_is_compatible(descriptor: Mapping[str, Any]) -> bool:
    """Validate future selection metadata without reading any configuration value."""
    if not isinstance(descriptor, Mapping):
        return False
    mechanism = descriptor.get("mechanism")
    if mechanism not in CONFIGURATION_MECHANISMS:
        return False
    if not _exact_string_tuple(
        descriptor.get("requested_slots"), FIXED_OPAQUE_CONFIGURATION_SLOTS
    ):
        return False
    if mechanism == OPTION_A:
        return (
            set(descriptor) == OPTION_A_DESCRIPTOR_FIELDS
            and _exact_string_tuple(
                descriptor.get("environment_variable_names"),
                OPTION_A_ENVIRONMENT_VARIABLE_NAMES,
            )
        )
    return (
        set(descriptor) == OPTION_B_DESCRIPTOR_FIELDS
        and descriptor.get("local_config_path")
        == OPTION_B_CONFIG_PATH_WORKSPACE_RELATIVE
        and _exact_string_tuple(
            descriptor.get("local_config_fields"), OPTION_B_CONFIG_FIELDS
        )
    )


def selection_is_exclusive(
    *, option_a_selected: bool, option_b_selected: bool
) -> bool:
    return isinstance(option_a_selected, bool) and isinstance(
        option_b_selected, bool
    ) and option_a_selected is not option_b_selected


def future_source_may_be_available(
    *, descriptor: Mapping[str, Any], future_c8_authorization_valid: bool,
    runner_identity: str
) -> bool:
    """Declare availability only; this function never acquires a value."""
    return False


def raw_value_operation_is_allowed(operation: str) -> bool:
    return operation == ONLY_ALLOWED_RAW_VALUE_OPERATION


def redacted_boundary_is_compatible(
    *, raw_value_included: bool, raw_value_hashed: bool,
    raw_value_in_exception: bool, raw_value_in_audit: bool,
    raw_value_in_return: bool
) -> bool:
    return not any((
        raw_value_included,
        raw_value_hashed,
        raw_value_in_exception,
        raw_value_in_audit,
        raw_value_in_return,
    ))
