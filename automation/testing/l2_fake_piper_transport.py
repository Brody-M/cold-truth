"""L2-only deterministic fake Piper transport and test-owned writer.

These helpers deliberately have no Piper, ONNX, model, provider, network,
subprocess, shell, configuration, environment, or audio-runtime capability.
"""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


DETERMINISTIC_NON_AUDIO_BYTES = b"L2_PIPER_NON_AUDIO_FIXTURE_BYTES_V1"
FAKE_OUTPUT_SUFFIX = ".l2fixture"
FAKE_CAPABILITIES = {
    "test_only": True,
    "in_memory_synthesis_only": True,
    "real_runtime_capable": False,
    "network_capable": False,
    "subprocess_capable": False,
    "shell_capable": False,
    "environment_access": False,
    "configuration_access": False,
    "model_access": False,
    "audio_generation_capable": False,
}


def _safe_fixture_name(value: object) -> bool:
    if type(value) is not str or not value or "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and len(path.parts) == 1
        and path.parts not in {(), (".",), ("..",)}
        and path.suffix == FAKE_OUTPUT_SUFFIX
    )


class L2FakePiperTransport:
    """Return deterministic non-audio bytes in memory and record one call."""

    capabilities = FAKE_CAPABILITIES

    def __init__(self, *, fail: bool = False, response: Any = None) -> None:
        self.fail = fail
        self.response = (
            DETERMINISTIC_NON_AUDIO_BYTES if response is None else response
        )
        self.call_count = 0
        self.last_request: Mapping[str, object] | None = None

    def synthesize(self, request: Mapping[str, object]) -> Any:
        self.call_count += 1
        self.last_request = dict(request)
        if self.fail:
            raise RuntimeError("deterministic L2 fake transport failure")
        return self.response


class L2FakeExclusiveCreateWriter:
    """Write only the fixed fixture bytes beneath one OS-temporary test root."""

    capabilities = FAKE_CAPABILITIES
    TARGET_STATES = {
        "missing",
        "regular_file",
        "directory",
        "link",
        "reparse",
        "unsafe",
    }

    def __init__(
        self,
        *,
        workspace_root: Path,
        exact_relative_path: str,
        fail: bool = False,
        forced_target_state: str | None = None,
    ) -> None:
        root = workspace_root.resolve()
        temporary_root = Path(tempfile.gettempdir()).resolve()
        try:
            root.relative_to(temporary_root)
        except ValueError as error:
            raise ValueError("L2 writer requires an OS-temporary workspace") from error
        if not root.name.startswith("cold_truth_l2_"):
            raise ValueError("L2 writer requires a test-owned workspace")
        if not _safe_fixture_name(exact_relative_path):
            raise ValueError("L2 writer requires one safe fixture filename")

        self.workspace_root = root
        self.exact_relative_path = exact_relative_path
        self.fail = fail
        self.forced_target_state = forced_target_state
        self.call_count = 0
        self.inspect_count = 0
        self.last_relative_path: str | None = None
        self.last_byte_count: int | None = None

    def inspect_target(self, relative_path: str) -> str:
        self.inspect_count += 1
        if (
            not _safe_fixture_name(relative_path)
            or relative_path != self.exact_relative_path
        ):
            return "unsafe"
        if self.forced_target_state is not None:
            if self.forced_target_state not in self.TARGET_STATES:
                return "unsafe"
            return self.forced_target_state

        target = self.workspace_root / relative_path
        try:
            metadata = os.lstat(target)
        except FileNotFoundError:
            return "missing"
        except OSError:
            return "unsafe"

        attributes = getattr(metadata, "st_file_attributes", 0)
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            return "reparse"
        if stat.S_ISLNK(metadata.st_mode):
            return "link"
        if stat.S_ISDIR(metadata.st_mode):
            return "directory"
        if stat.S_ISREG(metadata.st_mode):
            return "regular_file"
        return "unsafe"

    def write_exclusive(self, *, relative_path: str, data: bytes) -> None:
        self.call_count += 1
        self.last_relative_path = relative_path
        self.last_byte_count = len(data)
        if self.fail:
            raise OSError("deterministic L2 fake writer failure")
        if (
            relative_path != self.exact_relative_path
            or not _safe_fixture_name(relative_path)
        ):
            raise ValueError("L2 writer rejected an unsafe destination")
        if data != DETERMINISTIC_NON_AUDIO_BYTES:
            raise ValueError("L2 writer accepts only its fixed non-audio bytes")
        target = self.workspace_root / relative_path
        with target.open("xb") as output:
            output.write(data)
