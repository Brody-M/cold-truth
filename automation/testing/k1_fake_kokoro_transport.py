"""K1-only deterministic fake transport and exclusive-create writer.

These helpers deliberately have no Kokoro, provider, network, subprocess,
configuration, environment, or audio-runtime capability.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any, Mapping


DETERMINISTIC_NON_AUDIO_BYTES = b"K1_NON_AUDIO_FIXTURE_BYTES_V1"
FAKE_CAPABILITIES = {
    "test_only": True,
    "in_memory_synthesis_only": True,
    "real_runtime_capable": False,
    "network_capable": False,
    "subprocess_capable": False,
    "environment_access": False,
    "configuration_access": False,
    "audio_generation_capable": False,
}


class K1FakeKokoroTransport:
    """Return deterministic non-audio bytes in memory and record one call."""

    capabilities = FAKE_CAPABILITIES

    def __init__(self, *, fail: bool = False, response: Any = None) -> None:
        self.fail = fail
        self.response = DETERMINISTIC_NON_AUDIO_BYTES if response is None else response
        self.call_count = 0
        self.last_request: Mapping[str, object] | None = None

    def synthesize(self, request: Mapping[str, object]) -> Any:
        self.call_count += 1
        self.last_request = dict(request)
        if self.fail:
            raise RuntimeError("deterministic K1 fake transport failure")
        return self.response


class K1FakeExclusiveCreateWriter:
    """Write only deterministic fixture bytes beneath one temporary workspace."""

    capabilities = FAKE_CAPABILITIES
    TARGET_STATES = {"missing", "regular_file", "directory", "link", "reparse", "unsafe"}

    def __init__(
        self,
        *,
        workspace_root: Path,
        fail: bool = False,
        forced_target_state: str | None = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.fail = fail
        self.forced_target_state = forced_target_state
        self.call_count = 0
        self.inspect_count = 0
        self.last_relative_path: str | None = None
        self.last_byte_count: int | None = None

    def inspect_target(self, relative_path: str) -> str:
        self.inspect_count += 1
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
            raise OSError("deterministic K1 fake writer failure")
        if data != DETERMINISTIC_NON_AUDIO_BYTES:
            raise ValueError("K1 writer accepts only its deterministic non-audio fixture bytes")
        target = self.workspace_root / relative_path
        with target.open("xb") as output:
            output.write(data)
