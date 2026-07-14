"""Provider-neutral K1 Kokoro boundary with fake dependencies only.

K1 contains no route to a real Kokoro package, model, voicepack, executable,
server, provider, network transport, configuration source, or audio runtime.
"""
from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from testing.k1_fake_kokoro_transport import (
    DETERMINISTIC_NON_AUDIO_BYTES,
    K1FakeExclusiveCreateWriter,
    K1FakeKokoroTransport,
)


ROUTE_IDENTIFIER = "local_kokoro_isolated_adapter"
FAKE_TEST_MARKER = "k1_fake_transport_only"
FAKE_TEXT_PREFIX = "[K1 FAKE] "
FIXTURE_VOICE_IDENTIFIERS = frozenset({"fixture_voice_alpha"})
SUPPORTED_OUTPUT_FORMAT = "wav"
MAXIMUM_INPUT_CHARACTERS = 500
MAXIMUM_FAKE_RESPONSE_BYTES = 4_096

ResultStatus = Literal["success", "failure"]
SafeErrorCategory = Literal[
    "adapter_reused",
    "invalid_request_type",
    "invalid_text",
    "text_too_long",
    "invalid_maximum_input_length",
    "missing_voice_identifier",
    "unsupported_voice_identifier",
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
class KokoroSynthesisRequest:
    text: str
    voice_identifier: str
    output_format: str
    output_relative_path: str
    maximum_input_characters: int


@dataclass(frozen=True, slots=True)
class KokoroSafeAudit:
    route_identifier: str
    fake_test_marker: str
    result_category: str
    output_byte_count: int | None
    transport_call_count: int
    writer_call_count: int


@dataclass(frozen=True, slots=True)
class KokoroSynthesisResult:
    status: ResultStatus
    safe_error_category: SafeErrorCategory | None
    output_path: str | None
    byte_count: int | None
    audit: KokoroSafeAudit


def _safe_relative_output_path(value: object) -> bool:
    if type(value) is not str or not value or "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1:
        return False
    return path.parts not in {(), (".",), ("..",)} and path.suffix == ".fixture"


class KokoroLocalAdapterContract:
    """Single-use K1 adapter that accepts only exact allowlisted fake classes."""

    def __init__(
        self,
        *,
        transport: K1FakeKokoroTransport,
        exclusive_writer: K1FakeExclusiveCreateWriter,
        isolated_workspace: Path,
        exact_output_relative_path: str,
    ) -> None:
        if type(transport) is not K1FakeKokoroTransport:
            raise TypeError("K1 accepts only K1FakeKokoroTransport")
        if type(exclusive_writer) is not K1FakeExclusiveCreateWriter:
            raise TypeError("K1 accepts only K1FakeExclusiveCreateWriter")
        workspace = isolated_workspace.resolve()
        metadata = workspace.lstat()
        attributes = getattr(metadata, "st_file_attributes", 0)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise ValueError("isolated K1 workspace is unsafe")
        if exclusive_writer.workspace_root != workspace:
            raise ValueError("fake writer is not bound to the isolated K1 workspace")
        if not _safe_relative_output_path(exact_output_relative_path):
            raise ValueError("exact K1 output path is unsafe")

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
    ) -> KokoroSynthesisResult:
        success = status == "success"
        result_category = "fake_synthesis_succeeded" if success else str(category)
        return KokoroSynthesisResult(
            status=status,
            safe_error_category=None if success else category,
            output_path=self.exact_output_relative_path if success else None,
            byte_count=byte_count if success else None,
            audit=KokoroSafeAudit(
                route_identifier=ROUTE_IDENTIFIER,
                fake_test_marker=FAKE_TEST_MARKER,
                result_category=result_category,
                output_byte_count=byte_count if success else None,
                transport_call_count=self.transport.call_count,
                writer_call_count=self.exclusive_writer.call_count,
            ),
        )

    def execute(self, request: KokoroSynthesisRequest) -> KokoroSynthesisResult:
        if self._used:
            return self._result(status="failure", category="adapter_reused")
        self._used = True

        category = self._validate_request(request)
        if category is not None:
            return self._result(status="failure", category=category)

        target_state = self.exclusive_writer.inspect_target(request.output_relative_path)
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
                category=target_failures.get(target_state, "destination_is_unsafe"),
            )

        try:
            response = self.transport.synthesize({
                "text": request.text,
                "voice_identifier": request.voice_identifier,
                "output_format": request.output_format,
            })
        except Exception:
            return self._result(status="failure", category="transport_failure")

        if (
            type(response) is not bytes
            or response != DETERMINISTIC_NON_AUDIO_BYTES
            or not 0 < len(response) <= MAXIMUM_FAKE_RESPONSE_BYTES
        ):
            return self._result(status="failure", category="unexpected_transport_result")

        try:
            self.exclusive_writer.write_exclusive(
                relative_path=request.output_relative_path,
                data=response,
            )
        except Exception:
            return self._result(status="failure", category="writer_failure")
        return self._result(status="success", category=None, byte_count=len(response))

    def _validate_request(self, request: object) -> SafeErrorCategory | None:
        if type(request) is not KokoroSynthesisRequest:
            return "invalid_request_type"
        if type(request.text) is not str or not request.text.startswith(FAKE_TEXT_PREFIX):
            return "invalid_text"
        if not request.text[len(FAKE_TEXT_PREFIX):].strip():
            return "invalid_text"
        if type(request.maximum_input_characters) is not int or request.maximum_input_characters != MAXIMUM_INPUT_CHARACTERS:
            return "invalid_maximum_input_length"
        if len(request.text) > request.maximum_input_characters:
            return "text_too_long"
        if type(request.voice_identifier) is not str or not request.voice_identifier:
            return "missing_voice_identifier"
        if request.voice_identifier not in FIXTURE_VOICE_IDENTIFIERS:
            return "unsupported_voice_identifier"
        if type(request.output_format) is not str or request.output_format != SUPPORTED_OUTPUT_FORMAT:
            return "unsupported_output_format"
        if not _safe_relative_output_path(request.output_relative_path):
            return "unsafe_output_path"
        if request.output_relative_path != self.exact_output_relative_path:
            return "output_destination_mismatch"
        return None
