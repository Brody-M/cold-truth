"""Permission-scoped agent runner with validation, retries, and idempotency."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_runtime import AdapterUnavailableError, ProviderRegistry
from handoff_validator import ContractValidationError, file_sha256, load_contract, validate_handoff, validate_request_envelope
from run_records import RunRecordStore


MAX_AGENT_ATTEMPTS = 3


class AgentRunBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentExecution:
    handoff: dict[str, Any]
    handoff_path: Path
    record_path: Path
    idempotency_key: str
    cache_hit: bool
    attempt_count: int


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _is_under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class AgentRunner:
    def __init__(
        self,
        contracts_root: Path,
        run_root: Path,
        registry: ProviderRegistry,
        *,
        mode: str = "synthetic",
    ) -> None:
        if mode not in {"synthetic", "controlled-real-fixture", "dry-run", "real-production"}:
            raise ValueError("Unsupported agent-runtime mode")
        self.contracts_root = contracts_root.resolve()
        self.run_root = run_root.resolve()
        self.registry = registry
        self.mode = mode
        self.records = RunRecordStore(self.run_root)

    def contract_path(self, contract_id: str) -> Path:
        slug = contract_id.removeprefix("cold-truth.").replace("-", "_")
        path = self.contracts_root / f"{slug}.contract.json"
        if not path.is_file():
            raise AdapterUnavailableError(f"Contract file is unavailable for {contract_id}")
        return path

    def run(
        self,
        contract_id: str,
        *,
        run_id: str,
        case_id: str,
        episode_id: str | None = None,
        stage: str,
        inputs: dict[str, Any],
        failure_mode: str | None = None,
        max_retries: int = 0,
        reset_token: str = "",
    ) -> AgentExecution:
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or not 0 <= max_retries < MAX_AGENT_ATTEMPTS:
            raise ContractValidationError(f"max_retries must be an integer from 0 to {MAX_AGENT_ATTEMPTS - 1}")
        contract = load_contract(self.contract_path(contract_id))
        provider = self.registry.provider_for(contract_id)
        bound_provider_id = provider.provider_id
        if not isinstance(bound_provider_id, str) or not bound_provider_id.strip():
            raise ContractValidationError("Configured provider_id is required")
        descriptors = self._input_descriptors(contract, inputs)
        permissions = {
            "allowed_actions": list(contract["allowed_actions"]),
            "network": False,
            "external_commands": False,
            "external_tools": False,
            "media_creation": False,
            "publishing": False,
            "platform_api": False,
            "secrets": False,
        }
        bound_episode_id = episode_id or f"episode-{run_id}"
        if not isinstance(bound_episode_id, str) or not bound_episode_id.strip():
            raise ContractValidationError("episode_id is required")
        attempt_policy = {
            "max_attempts": max_retries + 1,
            "max_retries": max_retries,
            "retry_requires_provider_retryable": True,
            "provider_fallback": False,
            "fixed_provider_id": bound_provider_id,
        }
        identity = {
            "run_id": run_id,
            "case_id": case_id,
            "episode_id": bound_episode_id,
            "stage": stage,
            "contract_id": contract["contract_id"],
            "contract_version": contract["contract_version"],
            "inputs": descriptors,
            "permissions": permissions,
            "mode": self.mode,
            "provider_id": bound_provider_id,
            "attempt_policy": attempt_policy,
            "failure_mode": failure_mode,
            "reset_token": reset_token,
        }
        idempotency_key = hashlib.sha256(_canonical(identity)).hexdigest()
        key_root = self.records.key_root(idempotency_key)
        envelope = {
            "schema_version": "1.0",
            **identity,
            "idempotency_key": idempotency_key,
            "output_root": str((key_root / "attempt-output").resolve()),
            "execution_origin": "orchestrated_agent",
        }
        validate_request_envelope(envelope, contract)
        self.records.write_request_once(idempotency_key, envelope)

        completed = self.records.completed(idempotency_key)
        if completed:
            handoff_path = Path(completed["handoff_path"])
            handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
            output_root = Path(completed["output_root"])
            cached_envelope = self._attempt_envelope(
                envelope, contract, output_root, int(completed["attempt_count"])
            )
            validate_handoff(handoff, contract, cached_envelope, output_root)
            return AgentExecution(
                handoff=handoff,
                handoff_path=handoff_path,
                record_path=Path(completed["record_path"]),
                idempotency_key=idempotency_key,
                cache_hit=True,
                attempt_count=int(completed["attempt_count"]),
            )

        attempts_allowed = attempt_policy["max_attempts"]
        last_reason = "agent execution did not start"
        for attempt in range(1, attempts_allowed + 1):
            if provider.provider_id != bound_provider_id:
                raise AgentRunBlocked("Configured provider identity changed; provider fallback is prohibited")
            attempt_root = self.records.attempt_root(idempotency_key, attempt)
            output_root = attempt_root / "output"
            output_root.mkdir(parents=True, exist_ok=True)
            attempt_envelope = self._attempt_envelope(envelope, contract, output_root, attempt)
            validate_request_envelope(attempt_envelope, contract)
            result = provider.execute(attempt_envelope, output_root, attempt)
            record = {
                "schema_version": "1.0",
                "execution_origin": "orchestrated_agent",
                "idempotency_key": idempotency_key,
                "attempt": attempt,
                "contract_id": contract_id,
                "run_id": run_id,
                "case_id": case_id,
                "episode_id": bound_episode_id,
                "stage": stage,
                "mode": self.mode,
                "provider_id": bound_provider_id,
                "attempt_policy": attempt_policy,
                "inputs": attempt_envelope["inputs"],
                "expected_outputs": attempt_envelope["expected_outputs"],
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "duration_ms": result.duration_ms,
                "exit_code": result.exit_code,
                "retryable": result.retryable,
                "runtime": result.runtime_metadata,
                "validation": {"status": "not_run", "errors": []},
                "handoff": None,
                "publishing_enabled": False,
            }
            if result.runtime_metadata.get("provider") != bound_provider_id:
                last_reason = "Runtime result provider identity mismatch"
                record["validation"] = {"status": "blocked_provider_identity", "errors": [last_reason]}
                record_path = self.records.write_attempt_once(idempotency_key, attempt, record, result.stdout, result.stderr)
                raise AgentRunBlocked(f"{last_reason}; record: {record_path}")
            if result.exit_code != 0:
                last_reason = f"Agent exited with code {result.exit_code}"
                record["validation"] = {"status": "blocked_provider_failure", "errors": [last_reason]}
                record_path = self.records.write_attempt_once(idempotency_key, attempt, record, result.stdout, result.stderr)
                if result.retryable and attempt < attempts_allowed:
                    continue
                raise AgentRunBlocked(f"{last_reason}; record: {record_path}")
            if result.handoff_path is None:
                last_reason = "Agent returned no handoff artifact"
                record["validation"] = {"status": "blocked_missing_handoff", "errors": [last_reason]}
                record_path = self.records.write_attempt_once(idempotency_key, attempt, record, result.stdout, result.stderr)
                raise AgentRunBlocked(f"{last_reason}; record: {record_path}")
            try:
                if not _is_under(output_root, result.handoff_path):
                    raise ContractValidationError("Handoff path escapes the isolated output root")
                handoff = json.loads(result.handoff_path.read_text(encoding="utf-8"))
                validate_handoff(handoff, contract, attempt_envelope, output_root)
            except (OSError, json.JSONDecodeError, ContractValidationError) as exc:
                last_reason = str(exc)
                record["validation"] = {"status": "blocked_contract_failure", "errors": [last_reason]}
                record_path = self.records.write_attempt_once(idempotency_key, attempt, record, result.stdout, result.stderr)
                raise AgentRunBlocked(f"Contract validation failed: {last_reason}; record: {record_path}") from exc
            record["validation"] = {"status": "pass", "errors": []}
            record["handoff"] = {"path": str(result.handoff_path.resolve()), "sha256": file_sha256(result.handoff_path), "size_bytes": result.handoff_path.stat().st_size}
            record_path = self.records.write_attempt_once(idempotency_key, attempt, record, result.stdout, result.stderr)
            completed_value = {
                "schema_version": "1.0",
                "idempotency_key": idempotency_key,
                "attempt_count": attempt,
                "episode_id": bound_episode_id,
                "provider_id": bound_provider_id,
                "attempt_policy": attempt_policy,
                "handoff_path": str(result.handoff_path.resolve()),
                "handoff_sha256": file_sha256(result.handoff_path),
                "output_root": str(output_root.resolve()),
                "record_path": str(record_path.resolve()),
            }
            self.records.mark_completed_once(idempotency_key, completed_value)
            return AgentExecution(handoff, result.handoff_path, record_path, idempotency_key, False, attempt)
        raise AgentRunBlocked(last_reason)

    @staticmethod
    def _attempt_envelope(
        envelope: dict[str, Any],
        contract: dict[str, Any],
        output_root: Path,
        attempt: int,
    ) -> dict[str, Any]:
        canonical_root = output_root.resolve()
        expected_outputs = [
            {"name": item["name"], "path": str((canonical_root / item["name"]).resolve())}
            for item in contract["required_outputs"]
            if not item["name"].endswith("_handoff.json")
        ]
        return {
            **envelope,
            "attempt": attempt,
            "output_root": str(canonical_root),
            "expected_outputs": expected_outputs,
        }

    @staticmethod
    def _input_descriptors(contract: dict[str, Any], values: dict[str, Any]) -> list[dict[str, Any]]:
        declared = {item["name"]: item for item in contract["required_inputs"]}
        descriptors: list[dict[str, Any]] = []
        for name in sorted(values):
            if name not in declared:
                raise ContractValidationError(f"Input is not declared by the contract: {name}")
            value = values[name]
            item_type = declared[name].get("type", "unspecified")
            if isinstance(value, Path):
                path = value.resolve()
                if not path.is_file():
                    raise ContractValidationError(f"Input file does not exist: {name}")
                descriptors.append({"name": name, "type": item_type, "kind": "file", "path": str(path), "sha256": file_sha256(path), "size_bytes": path.stat().st_size})
            else:
                digest = hashlib.sha256(_canonical(value)).hexdigest()
                descriptors.append({"name": name, "type": item_type, "kind": "value", "value": value, "sha256": digest})
        return descriptors
