"""Allowlisted, test-only, in-memory client for Phase C7.

This module intentionally imports no external-execution, connectivity, account,
browser, or configuration facility.
"""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Any


EXPECTED_CAPABILITIES = MappingProxyType({
    "test_only": True,
    "in_memory_only": True,
    "network_capable": False,
    "live_provider_capable": False,
    "subprocess_capable": False,
    "environment_reading": False,
    "config_reading": False,
    "credential_reading": False,
    "secret_reading": False,
    "browser_capable": False,
    "mcp_capable": False,
    "sdk_capable": False,
    "filesystem_audio_capable": False,
    "arbitrary_callable_wrapper": False,
})


class C7AllowlistedFakeLocalHttpClient:
    """Exact allowlisted fake. It only records one request in memory."""

    test_only_identity = "cold-truth-c7-allowlisted-fake-local-http-client"
    capability_declarations = EXPECTED_CAPABILITIES

    def __init__(self) -> None:
        self.call_count = 0
        self.last_request: dict[str, Any] | None = None

    def send_mock(self, request: dict[str, Any]) -> dict[str, Any]:
        self.call_count += 1
        self.last_request = request
        canonical = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "response_kind": "deterministic_non_audio_mock_metadata",
            "request_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "status": "mock_contract_accepted",
            "provider_invoked": False,
            "network_invoked": False,
            "audio_bytes": 0,
            "audio_file_created": False,
        }
