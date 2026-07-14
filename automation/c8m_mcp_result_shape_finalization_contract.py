"""Offline-only C8m result-shape and one-action finalization contract."""
from __future__ import annotations

from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Sequence


OUTPUT_DIRECTORY = "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output"
FINAL_OUTPUT = f"{OUTPUT_DIRECTORY}/c8_isolated_synthetic_connectivity.mp3"
RESULT_SHAPES = ("returned_contained_local_mp3_path", "mcp_audio_resource")

FINALIZATION_BOUNDARY = MappingProxyType({
    "allowed_runtime_result_shapes": RESULT_SHAPES,
    "exactly_one_runtime_result_shape_required_after_mcp": True,
    "local_finalization_action_allowed": True,
    "maximum_local_rename_count": 1,
    "maximum_resource_materialization_write_count": 1,
    "maximum_final_output_count": 1,
    "maximum_safe_audit_record_count": 1,
    "atomic_same_filesystem_rename_required": True,
    "exclusive_create_required": True,
    "destination_must_be_absent": True,
    "retry_allowed": False,
    "second_mcp_operation_allowed": False,
    "second_finalization_action_allowed": False,
    "second_rename_allowed": False,
    "rename_retry_allowed": False,
    "copy_allowed": False,
    "overwrite_allowed": False,
    "remote_reference_allowed": False,
    "attachment_download_reference_allowed": False,
    "metadata_only_success_allowed": False,
    "mixed_result_shapes_allowed": False,
    "resource_url_fetch_allowed": False,
    "resource_content_inspection_allowed": False,
    "resource_content_retention_allowed": False,
    "temporary_media_allowed": False,
    "cleanup_allowed": False,
    "deletion_allowed": False,
    "polling_allowed": False,
    "status_call_allowed": False,
    "follow_up_allowed": False,
    "post_rename_cleanup_allowed": False,
    "audio_processing_allowed": False,
})

READY_LOCAL_PATH = "C8M_LOCAL_PATH_READY_NON_EXECUTABLE"
READY_AUDIO_RESOURCE = "C8M_AUDIO_RESOURCE_READY_NON_EXECUTABLE"
BLOCKED_SHAPE = "C8M_BLOCKED_RESULT_SHAPE"
BLOCKED_COUNT = "C8M_BLOCKED_RESULT_COUNT"
BLOCKED_LOCAL_PATH = "C8M_BLOCKED_LOCAL_PATH"
BLOCKED_RESOURCE = "C8M_BLOCKED_AUDIO_RESOURCE"
BLOCKED_DESTINATION = "C8M_BLOCKED_DESTINATION_EXISTS"
BLOCKED_FINALIZATION = "C8M_BLOCKED_FINALIZATION_FAILURE_NO_RETRY"


class OpaqueMcpAudioResource:
    """Test-only identity marker; it contains and exposes no audio content."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<opaque-mcp-audio-resource>"


def runtime_result_shape_allowlist_is_valid(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and tuple(value) == RESULT_SHAPES


def finalization_boundary_is_exact(value: Mapping[str, Any]) -> bool:
    if not isinstance(value, Mapping):
        return False
    normalized = dict(value)
    normalized["allowed_runtime_result_shapes"] = tuple(
        normalized.get("allowed_runtime_result_shapes", ())
    )
    return normalized == dict(FINALIZATION_BOUNDARY)


def _valid_direct_contained_mp3_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or any(char in value for char in ("\\", "*", "?")):
        return False
    if "://" in value:
        return False
    path = PurePosixPath(value)
    root = PurePosixPath(OUTPUT_DIRECTORY)
    if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".mp3":
        return False
    return path.parent == root and len(path.parts) == len(root.parts) + 1


def _local_result_is_exact(result: Any) -> bool:
    if not isinstance(result, Mapping):
        return False
    expected_fields = {
        "path", "entry_type", "direct_child", "newly_created",
        "preexisting", "is_link", "link_kind",
    }
    if set(result) != expected_fields or not _valid_direct_contained_mp3_path(result.get("path")):
        return False
    return (
        result["entry_type"] == "regular_file"
        and result["direct_child"] is True
        and result["newly_created"] is True
        and result["preexisting"] is False
        and result["is_link"] is False
        and result["link_kind"] is None
    )


def classify_runtime_result(
    results: Sequence[Any], *, allowed_runtime_result_shapes: Sequence[str],
) -> str | None:
    """Classify one returned MCP result without exposing or retaining its payload."""
    if not runtime_result_shape_allowlist_is_valid(allowed_runtime_result_shapes):
        return None
    if len(results) != 1:
        return None
    result = results[0]
    if _local_result_is_exact(result):
        return RESULT_SHAPES[0]
    if type(result) is OpaqueMcpAudioResource:
        return RESULT_SHAPES[1]
    return None


def evaluate_local_path_result(
    results: Sequence[Mapping[str, Any]], *, classified_shape: str,
    destination_exists: bool, rename_failed: bool = False,
) -> str:
    if classified_shape != RESULT_SHAPES[0]:
        return BLOCKED_SHAPE
    if destination_exists:
        return BLOCKED_DESTINATION
    if len(results) != 1:
        return BLOCKED_COUNT
    if not _local_result_is_exact(results[0]):
        return BLOCKED_LOCAL_PATH
    if rename_failed:
        return BLOCKED_FINALIZATION
    return READY_LOCAL_PATH


def local_path_rename_plan(path: str) -> Mapping[str, Any] | None:
    if not _valid_direct_contained_mp3_path(path):
        return None
    return MappingProxyType({
        "source_relative_path": path,
        "destination_relative_path": FINAL_OUTPUT,
        "rename_count": 1,
        "atomic_same_filesystem": True,
        "overwrite": False,
    })


def evaluate_audio_resource_result(
    resources: Sequence[Any], *, classified_shape: str,
    destination_exists: bool, write_failed: bool = False,
) -> str:
    if classified_shape != RESULT_SHAPES[1]:
        return BLOCKED_SHAPE
    if destination_exists:
        return BLOCKED_DESTINATION
    if len(resources) != 1:
        return BLOCKED_COUNT
    if type(resources[0]) is not OpaqueMcpAudioResource:
        return BLOCKED_RESOURCE
    if write_failed:
        return BLOCKED_FINALIZATION
    return READY_AUDIO_RESOURCE


def audio_resource_materialization_plan(resource: Any) -> Mapping[str, Any] | None:
    if type(resource) is not OpaqueMcpAudioResource:
        return None
    return MappingProxyType({
        "destination_relative_path": FINAL_OUTPUT,
        "materialization_write_count": 1,
        "exclusive_create": True,
        "overwrite": False,
    })

