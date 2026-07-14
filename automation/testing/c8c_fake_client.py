"""Exact test-only in-memory inspector for the isolated C8c adapter."""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Any


EXPECTED_CAPABILITIES = MappingProxyType({
    "test_only": True,
    "in_memory_only": True,
    "network_capable": False,
    "provider_capable": False,
    "subprocess_capable": False,
    "environment_reading": False,
    "config_reading": False,
    "secret_reading": False,
    "browser_capable": False,
    "mcp_capable": False,
    "sdk_capable": False,
    "shell_capable": False,
    "filesystem_audio_capable": False,
    "arbitrary_callable_wrapper": False
})


class C8cAllowlistedFakeClient:
    test_only_identity = "cold-truth-c8c-isolated-fake-inspector"
    capability_declarations = EXPECTED_CAPABILITIES

    def __init__(self) -> None:
        self.call_count = 0
        self.last_request: dict[str, Any] | None = None

    def inspect_request(self, request: dict[str, Any]) -> dict[str, Any]:
        self.call_count += 1
        self.last_request = request
        canonical = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "metadata_kind": "c8c_deterministic_zero_audio_inspection",
            "request_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "external_call_made": False,
            "provider_invoked": False,
            "network_invoked": False,
            "audio_bytes": 0,
            "audio_file_created": False
        }
