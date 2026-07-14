from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agent_runner import AgentRunBlocked, AgentRunner
from agent_runtime import ProviderRegistry
from fixtures.simulated_agents.mock_runtime import SyntheticAgentProvider
from handoff_validator import ContractValidationError, validate_request_envelope
from orchestrator import read_json


AUTOMATION = Path(__file__).resolve().parent
CONTRACTS = AUTOMATION / "contracts"
FIXTURE_ROOT = AUTOMATION / "fixtures" / "simulated_agents"
QUEUE = AUTOMATION / "fixtures" / "simulated_case" / "queue.json"
CONTRACT_ID = "cold-truth.strategist"


class CanonicalArtifactIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = ProviderRegistry()
        self.registry.register(SyntheticAgentProvider(FIXTURE_ROOT), [CONTRACT_ID])
        self.runner = AgentRunner(CONTRACTS, self.root / "run", self.registry, mode="synthetic")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def inputs(self, *, queue: Path = QUEUE) -> dict:
        return {
            "candidate_queue": queue,
            "batch_size": 3,
            "content_standard": FIXTURE_ROOT / "content_standard_fixture.md",
        }

    def run_agent(self, *, failure_mode: str | None = None, inputs: dict | None = None):
        return self.runner.run(
            CONTRACT_ID,
            run_id="h7-canonical-artifact-run",
            case_id="synthetic-queue",
            episode_id="episode-h7-canonical-artifact",
            stage="strategist_intake",
            inputs=inputs or self.inputs(),
            failure_mode=failure_mode,
        )

    def attempt_record(self, execution) -> dict:
        return read_json(execution.record_path)

    def test_attempt_record_binds_canonical_inputs_and_exact_expected_outputs(self) -> None:
        execution = self.run_agent()
        record = self.attempt_record(execution)
        for item in record["inputs"]:
            if item["kind"] == "file":
                path = Path(item["path"])
                self.assertTrue(path.is_absolute())
                self.assertEqual(item["path"], str(path.resolve()))
                self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(item["size_bytes"], path.stat().st_size)
            else:
                encoded = json.dumps(item["value"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                self.assertEqual(item["sha256"], hashlib.sha256(encoded).hexdigest())
        output_by_name = {item["name"]: item for item in execution.handoff["outputs"]}
        self.assertEqual(set(output_by_name), {item["name"] for item in record["expected_outputs"]})
        for expected in record["expected_outputs"]:
            self.assertEqual(output_by_name[expected["name"]]["path"], expected["path"])

    def test_mutated_input_is_rejected_before_handoff_acceptance(self) -> None:
        mutable = self.root / "mutable-queue.json"
        mutable.write_bytes(QUEUE.read_bytes())
        with self.assertRaisesRegex(AgentRunBlocked, "Input (hash|size) mismatch"):
            self.run_agent(failure_mode="mutate_input", inputs=self.inputs(queue=mutable))

    def test_attempt_identity_substitution_is_rejected(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "attempt"):
            self.run_agent(failure_mode="attempt_mismatch")

    def test_duplicate_output_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "unique"):
            self.run_agent(failure_mode="duplicate_output")

    def test_undeclared_output_is_rejected(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "undeclared outputs"):
            self.run_agent(failure_mode="unexpected_output")

    def test_noncanonical_output_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "not canonical"):
            self.run_agent(failure_mode="noncanonical_output_path")

    def test_noncanonical_input_descriptor_is_rejected(self) -> None:
        contract = json.loads((CONTRACTS / "strategist.contract.json").read_text(encoding="utf-8"))
        queue = QUEUE.resolve()
        envelope = {
            "schema_version": "1.0",
            "run_id": "h7-request",
            "case_id": "synthetic-queue",
            "episode_id": "episode-h7-request",
            "stage": "strategist_intake",
            "contract_id": contract["contract_id"],
            "contract_version": contract["contract_version"],
            "idempotency_key": "0" * 64,
            "mode": "synthetic",
            "provider_id": "synthetic-in-process-v1",
            "attempt_policy": {
                "max_attempts": 1,
                "max_retries": 0,
                "retry_requires_provider_retryable": True,
                "provider_fallback": False,
                "fixed_provider_id": "synthetic-in-process-v1",
            },
            "inputs": [
                {
                    "name": "candidate_queue",
                    "type": "backlog_or_queue",
                    "kind": "file",
                    "path": str(queue.parent / "." / queue.name),
                    "sha256": hashlib.sha256(queue.read_bytes()).hexdigest(),
                    "size_bytes": queue.stat().st_size,
                },
                {"name": "batch_size", "type": "integer", "kind": "value", "value": 3, "sha256": hashlib.sha256(b"3").hexdigest()},
                {
                    "name": "content_standard",
                    "type": "policy_document",
                    "kind": "file",
                    "path": str((FIXTURE_ROOT / "content_standard_fixture.md").resolve()),
                    "sha256": hashlib.sha256((FIXTURE_ROOT / "content_standard_fixture.md").read_bytes()).hexdigest(),
                    "size_bytes": (FIXTURE_ROOT / "content_standard_fixture.md").stat().st_size,
                },
            ],
            "permissions": {
                "allowed_actions": contract["allowed_actions"],
                "network": False,
                "external_commands": False,
                "external_tools": False,
                "media_creation": False,
                "publishing": False,
                "platform_api": False,
                "secrets": False,
            },
            "output_root": str((self.root / "output").resolve()),
        }
        envelope["inputs"][0]["path"] = str(queue.parent / "nonexistent" / ".." / queue.name)
        with self.assertRaisesRegex(ContractValidationError, "not canonical"):
            validate_request_envelope(envelope, contract)

    def test_cache_hit_revalidates_exact_output_paths(self) -> None:
        first = self.run_agent()
        second = self.run_agent()
        self.assertFalse(first.cache_hit)
        self.assertTrue(second.cache_hit)
        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(first.handoff, second.handoff)


if __name__ == "__main__":
    unittest.main(verbosity=2)
