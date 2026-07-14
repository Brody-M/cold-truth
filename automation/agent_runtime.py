"""Generic provider abstraction and runtime request/result types."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class AdapterUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeResult:
    exit_code: int
    stdout: str
    stderr: str
    started_at: str
    completed_at: str
    duration_ms: int
    handoff_path: Path | None
    retryable: bool
    runtime_metadata: dict[str, Any]


class AgentProvider(Protocol):
    provider_id: str

    def execute(self, request: dict[str, Any], output_root: Path, attempt: int) -> RuntimeResult:
        ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AgentProvider] = {}
        self._agent_provider: dict[str, str] = {}

    def register(self, provider: AgentProvider, contract_ids: list[str]) -> None:
        self._providers[provider.provider_id] = provider
        for contract_id in contract_ids:
            self._agent_provider[contract_id] = provider.provider_id

    def provider_for(self, contract_id: str) -> AgentProvider:
        provider_id = self._agent_provider.get(contract_id)
        if not provider_id or provider_id not in self._providers:
            raise AdapterUnavailableError(f"No configured runtime adapter for {contract_id}")
        return self._providers[provider_id]
