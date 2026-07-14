"""Offline-only C8i contract for one deterministic post-MCP local rename."""
from __future__ import annotations

from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Sequence


STAGING_DIRECTORY = "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output/mcp_staging"
FINAL_OUTPUT = "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output/c8_isolated_synthetic_connectivity.mp3"

FINALIZATION_BOUNDARY = MappingProxyType({
    "mcp_output_filename_parameter_supported": False,
    "mcp_output_directory_required": True,
    "local_finalization_action_allowed": True,
    "maximum_local_rename_count": 1,
    "atomic_same_filesystem_rename_required": True,
    "destination_must_be_absent": True,
    "overwrite_allowed": False,
    "copy_allowed": False,
    "second_rename_allowed": False,
    "rename_retry_allowed": False,
    "staging_directory_must_be_empty_or_absent": True,
    "staging_required_new_entry_count": 1,
    "staging_nested_entries_allowed": False,
    "staging_links_allowed": False,
    "staging_non_mp3_entries_allowed": False,
    "post_rename_cleanup_allowed": False,
    "audio_processing_allowed": False,
    "maximum_safe_audit_record_count": 1,
})

SAFE_AUDIT_FIELDS = frozenset({
    "authorization_relative_staging_directory", "staging_entry_count",
    "source_relative_path", "final_relative_path", "source_exists",
    "final_exists", "byte_count", "sha256", "extension",
    "containment_result", "rename_attempted", "rename_succeeded",
    "safe_reason_code",
})

READY = "C8I_EXACT_LOCAL_RENAME_READY_NON_EXECUTABLE"
BLOCKED_EMPTY = "C8I_BLOCKED_ZERO_STAGING_FILES"
BLOCKED_MULTIPLE = "C8I_BLOCKED_MULTIPLE_STAGING_ENTRIES"
BLOCKED_ENTRY = "C8I_BLOCKED_INVALID_STAGING_ENTRY"
BLOCKED_DESTINATION = "C8I_BLOCKED_DESTINATION_EXISTS"
BLOCKED_RENAME_FAILURE = "C8I_BLOCKED_RENAME_FAILURE_NO_RETRY"


def finalization_boundary_is_exact(value: Mapping[str, Any]) -> bool:
    return isinstance(value, Mapping) and dict(value) == dict(FINALIZATION_BOUNDARY)


def path_bindings_are_exact(*, staging_directory: str, final_output: str) -> bool:
    return staging_directory == STAGING_DIRECTORY and final_output == FINAL_OUTPUT


def _valid_direct_mp3_name(name: Any) -> bool:
    if not isinstance(name, str) or not name or any(char in name for char in ("/", "\\", "*", "?")):
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and len(path.parts) == 1 and name not in (".", "..") and path.suffix.lower() == ".mp3"


def evaluate_staging_snapshot(
    entries: Sequence[Mapping[str, Any]], *, destination_exists: bool,
    rename_failed: bool = False,
) -> str:
    """Evaluate sanitized metadata only; this function performs no filesystem action."""
    if destination_exists:
        return BLOCKED_DESTINATION
    if len(entries) == 0:
        return BLOCKED_EMPTY
    if len(entries) != 1:
        return BLOCKED_MULTIPLE
    entry = entries[0]
    if set(entry) != {"name", "entry_type", "direct_child", "newly_created", "is_link"}:
        return BLOCKED_ENTRY
    if not _valid_direct_mp3_name(entry["name"]):
        return BLOCKED_ENTRY
    if entry["entry_type"] != "regular_file" or entry["direct_child"] is not True:
        return BLOCKED_ENTRY
    if entry["newly_created"] is not True or entry["is_link"] is not False:
        return BLOCKED_ENTRY
    if rename_failed:
        return BLOCKED_RENAME_FAILURE
    return READY


def exact_rename_plan(source_name: str) -> Mapping[str, Any] | None:
    """Return the sole allowed rename declaration; never executes it."""
    if not _valid_direct_mp3_name(source_name):
        return None
    return MappingProxyType({
        "source_relative_path": f"{STAGING_DIRECTORY}/{source_name}",
        "destination_relative_path": FINAL_OUTPUT,
        "rename_count": 1,
        "atomic_same_filesystem": True,
        "overwrite": False,
    })


def safe_audit_shape_is_exact(value: Mapping[str, Any]) -> bool:
    return isinstance(value, Mapping) and set(value) == SAFE_AUDIT_FIELDS
