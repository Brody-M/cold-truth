"""Provider-neutral L2 Piper boundary with fake dependencies only.

L2 contains no route to Piper, ONNX Runtime, a model, executable, package,
server, subprocess, shell, provider, network transport, configuration source,
environment value, or audio runtime.
"""
from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from testing.l2_fake_piper_transport import (
    DETERMINISTIC_NON_AUDIO_BYTES,
    L2FakeExclusiveCreateWriter,
    L2FakePiperTransport,
)


ROUTE_IDENTIFIER = "local_piper_1_4_2_en_us_ljspeech_high"
LOCKED_ENGINE_VERSION = "1.4.2"
LOCKED_MODEL_ID = "en_US-ljspeech-high"
LOCKED_MODEL_SOURCE_MARKER = (
    "rhasspy_piper_voices_v1_0_0_en_en_us_ljspeech_high"
)
SUPPORTED_FUTURE_OUTPUT_FORMAT = "wav"
FAKE_TEST_MARKER = "l2_fake_piper_transport_only"
FAKE_TEXT_PREFIX = "[L2 PIPER FAKE] "
MAXIMUM_INPUT_CHARACTERS = 600
MAXIMUM_FAKE_RESPONSE_BYTES = 4_096
FAKE_OUTPUT_SUFFIX = ".l2fixture"

ResultStatus = Literal["success", "failure"]
SafeErrorCategory = Literal[
    "adapter_reused",
    "invalid_request_type",
    "invalid_route_identifier",
    "invalid_engine_version",
    "invalid_model_id",
    "invalid_model_source_marker",
    "missing_fake_test_marker",
    "invalid_text",
    "text_too_long",
    "invalid_maximum_input_length",
    "unsupported_output_format",
    "unsafe_output_path",
    "output_destination_mismatch",
    "destination_exists",
    "destination_is_directory",
    "destination_is_link",
    "destination_is_reparse_point",
    "destination_is_unsafe",
    "transport_failure",
    "unexpected_transport_result",
    "writer_failure",
]


@dataclass(frozen=True, slots=True)
class PiperSynthesisRequest:
    text: str
    route_identifier: str
    engine_version: str
    model_id: str
    model_source_marker: str
    output_format: str
    output_relative_path: str
    maximum_input_characters: int
    fake_test_marker: str


@dataclass(frozen=True, slots=True)
class PiperSafeAudit:
    route_identifier: str
    locked_engine_version: str
    locked_model_id: str
    fake_test_marker: str
    outcome_category: str
    fake_call_count: int
    output_byte_count: int | None


@dataclass(frozen=True, slots=True)
class PiperSynthesisResult:
    status: ResultStatus
    safe_error_category: SafeErrorCategory | None
    output_path: str | None
    byte_count: int | None
    audit: PiperSafeAudit


def _safe_relative_fixture_path(value: object) -> bool:
    if type(value) is not str or not value or "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1:
        return False
    return (
        path.parts not in {(), (".",), ("..",)}
        and path.suffix == FAKE_OUTPUT_SUFFIX
    )


class PiperLocalAdapterContract:
    """Single-use L2 adapter accepting only the exact L2 fake classes."""

    def __init__(
        self,
        *,
        transport: L2FakePiperTransport,
        exclusive_writer: L2FakeExclusiveCreateWriter,
        isolated_workspace: Path,
        exact_output_relative_path: str,
    ) -> None:
        if type(transport) is not L2FakePiperTransport:
            raise TypeError("L2 accepts only L2FakePiperTransport")
        if type(exclusive_writer) is not L2FakeExclusiveCreateWriter:
            raise TypeError("L2 accepts only L2FakeExclusiveCreateWriter")

        workspace = isolated_workspace.resolve()
        metadata = workspace.lstat()
        attributes = getattr(metadata, "st_file_attributes", 0)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise ValueError("isolated L2 workspace is unsafe")
        if not workspace.name.startswith("cold_truth_l2_"):
            raise ValueError("L2 workspace is not a test-owned temporary directory")
        if exclusive_writer.workspace_root != workspace:
            raise ValueError("fake writer is not bound to the isolated L2 workspace")
        if not _safe_relative_fixture_path(exact_output_relative_path):
            raise ValueError("exact L2 output path is unsafe")
        if exclusive_writer.exact_relative_path != exact_output_relative_path:
            raise ValueError("fake writer is not bound to the exact L2 output path")

        self.transport = transport
        self.exclusive_writer = exclusive_writer
        self.isolated_workspace = workspace
        self.exact_output_relative_path = exact_output_relative_path
        self._used = False

    def _result(
        self,
        *,
        status: ResultStatus,
        category: SafeErrorCategory | None,
        byte_count: int | None = None,
    ) -> PiperSynthesisResult:
        success = status == "success"
        outcome = "fake_synthesis_succeeded" if success else str(category)
        return PiperSynthesisResult(
            status=status,
            safe_error_category=None if success else category,
            output_path=self.exact_output_relative_path if success else None,
            byte_count=byte_count if success else None,
            audit=PiperSafeAudit(
                route_identifier=ROUTE_IDENTIFIER,
                locked_engine_version=LOCKED_ENGINE_VERSION,
                locked_model_id=LOCKED_MODEL_ID,
                fake_test_marker=FAKE_TEST_MARKER,
                outcome_category=outcome,
                fake_call_count=self.transport.call_count,
                output_byte_count=byte_count if success else None,
            ),
        )

    def execute(self, request: PiperSynthesisRequest) -> PiperSynthesisResult:
        if self._used:
            return self._result(status="failure", category="adapter_reused")
        self._used = True

        category = self._validate_request(request)
        if category is not None:
            return self._result(status="failure", category=category)

        target_state = self.exclusive_writer.inspect_target(
            request.output_relative_path
        )
        target_failures: dict[str, SafeErrorCategory] = {
            "regular_file": "destination_exists",
            "directory": "destination_is_directory",
            "link": "destination_is_link",
            "reparse": "destination_is_reparse_point",
            "unsafe": "destination_is_unsafe",
        }
        if target_state != "missing":
            return self._result(
                status="failure",
                category=target_failures.get(
                    target_state, "destination_is_unsafe"
                ),
            )

        try:
            response = self.transport.synthesize(
                {
                    "text": request.text,
                    "route_identifier": request.route_identifier,
                    "engine_version": request.engine_version,
                    "model_id": request.model_id,
                    "model_source_marker": request.model_source_marker,
                    "output_format": request.output_format,
                    "fake_test_marker": request.fake_test_marker,
                }
            )
        except Exception:
            return self._result(status="failure", category="transport_failure")

        if (
            type(response) is not bytes
            or response != DETERMINISTIC_NON_AUDIO_BYTES
            or not 0 < len(response) <= MAXIMUM_FAKE_RESPONSE_BYTES
        ):
            return self._result(
                status="failure", category="unexpected_transport_result"
            )

        try:
            self.exclusive_writer.write_exclusive(
                relative_path=request.output_relative_path,
                data=response,
            )
        except Exception:
            return self._result(status="failure", category="writer_failure")

        return self._result(
            status="success", category=None, byte_count=len(response)
        )

    def _validate_request(
        self, request: object
    ) -> SafeErrorCategory | None:
        if type(request) is not PiperSynthesisRequest:
            return "invalid_request_type"
        if request.route_identifier != ROUTE_IDENTIFIER:
            return "invalid_route_identifier"
        if request.engine_version != LOCKED_ENGINE_VERSION:
            return "invalid_engine_version"
        if request.model_id != LOCKED_MODEL_ID:
            return "invalid_model_id"
        if request.model_source_marker != LOCKED_MODEL_SOURCE_MARKER:
            return "invalid_model_source_marker"
        if request.fake_test_marker != FAKE_TEST_MARKER:
            return "missing_fake_test_marker"
        if type(request.text) is not str or not request.text.startswith(
            FAKE_TEXT_PREFIX
        ):
            return "invalid_text"
        if not request.text[len(FAKE_TEXT_PREFIX) :].strip():
            return "invalid_text"
        if (
            type(request.maximum_input_characters) is not int
            or request.maximum_input_characters != MAXIMUM_INPUT_CHARACTERS
        ):
            return "invalid_maximum_input_length"
        if len(request.text) > request.maximum_input_characters:
            return "text_too_long"
        if request.output_format != SUPPORTED_FUTURE_OUTPUT_FORMAT:
            return "unsupported_output_format"
        if not _safe_relative_fixture_path(request.output_relative_path):
            return "unsafe_output_path"
        if request.output_relative_path != self.exact_output_relative_path:
            return "output_destination_mismatch"
        return None
