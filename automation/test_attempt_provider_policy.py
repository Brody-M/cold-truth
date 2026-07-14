from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_runner import AgentRunBlocked, AgentRunner
from agent_runtime import ProviderRegistry
from fixtures.simulated_agents.mock_runtime import SyntheticAgentProvider
from handoff_validator import ContractValidationError
from orchestrator import read_json


AUTOMATION = Path(__file__).resolve().parent
CONTRACTS = AUTOMATION / "contracts"
FIXTURE_ROOT = AUTOMATION / "fixtures" / "simulated_agents"
QUEUE = AUTOMATION / "fixtures" / "simulated_case" / "queue.json"
CONTRACT_ID = "cold-truth.strategist"
PROVIDER_ID = "synthetic-in-process-v1"


class AttemptProviderPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        registry = ProviderRegistry()
        registry.register(SyntheticAgentProvider(FIXTURE_ROOT), [CONTRACT_ID])
        self.runner = AgentRunner(CONTRACTS, self.root / "run", registry, mode="synthetic")

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def inputs() -> dict:
        return {
            "candidate_queue": QUEUE,
            "batch_size": 3,
            "content_standard": FIXTURE_ROOT / "content_standard_fixture.md",
        }

    def run_agent(self, *, max_retries: int = 0, failure_mode: str | None = None):
        return self.runner.run(
            CONTRACT_ID,
            run_id="h9-attempt-policy-run",
            case_id="synthetic-queue",
            episode_id="episode-h9-attempt-policy",
            stage="strategist_intake",
            inputs=self.inputs(),
            max_retries=max_retries,
            failure_mode=failure_mode,
        )

    def key_roots(self) -> list[Path]:
        root = self.root / "run" / "agent_runs"
        return sorted(path for path in root.iterdir() if path.is_dir())

    def test_single_attempt_policy_is_explicit_and_provider_fixed(self) -> None:
        execution = self.run_agent()
        request = read_json(self.root / "run" / "agent_runs" / execution.idempotency_key / "request.json")
        self.assertEqual(request["provider_id"], PROVIDER_ID)
        self.assertEqual(request["attempt_policy"], {
            "max_attempts": 1,
            "max_retries": 0,
            "retry_requires_provider_retryable": True,
            "provider_fallback": False,
            "fixed_provider_id": PROVIDER_ID,
        })
        record = read_json(execution.record_path)
        self.assertEqual(record["attempt_policy"], request["attempt_policy"])
        self.assertEqual(record["provider_id"], PROVIDER_ID)

    def test_attempt_budget_changes_idempotency_identity(self) -> None:
        one_attempt = self.run_agent(max_retries=0)
        two_attempts = self.run_agent(max_retries=1)
        self.assertNotEqual(one_attempt.idempotency_key, two_attempts.idempotency_key)

    def test_retryable_failure_uses_exact_budget_and_same_provider(self) -> None:
        execution = self.run_agent(max_retries=1, failure_mode="fail_once")
        self.assertEqual(execution.attempt_count, 2)
        key_root = self.root / "run" / "agent_runs" / execution.idempotency_key
        first = read_json(key_root / "attempt-001" / "record.json")
        second = read_json(key_root / "attempt-002" / "record.json")
        self.assertEqual(first["provider_id"], PROVIDER_ID)
        self.assertEqual(second["provider_id"], PROVIDER_ID)
        self.assertEqual(first["attempt_policy"], second["attempt_policy"])
        self.assertFalse(first["attempt_policy"]["provider_fallback"])

    def test_retryable_failure_without_retry_budget_stops_after_one(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "exited with code 75"):
            self.run_agent(max_retries=0, failure_mode="fail_once")
        key_root = self.key_roots()[0]
        self.assertTrue((key_root / "attempt-001" / "record.json").is_file())
        self.assertFalse((key_root / "attempt-002").exists())

    def test_nonretryable_failure_never_spends_remaining_budget(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "exited with code 70"):
            self.run_agent(max_retries=2, failure_mode="agent_error")
        key_root = self.key_roots()[0]
        self.assertTrue((key_root / "attempt-001" / "record.json").is_file())
        self.assertFalse((key_root / "attempt-002").exists())

    def test_invalid_or_unbounded_retry_values_fail_before_request_creation(self) -> None:
        for value in (-1, 3, True, 1.5):
            with self.subTest(value=value), self.assertRaisesRegex(ContractValidationError, "max_retries"):
                self.run_agent(max_retries=value)  # type: ignore[arg-type]
        self.assertEqual(self.key_roots(), [])

    def test_handoff_provider_substitution_is_rejected(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "provider_id"):
            self.run_agent(failure_mode="provider_id_mismatch")

    def test_handoff_runtime_provider_substitution_is_rejected(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "runtime provider"):
            self.run_agent(failure_mode="runtime_provider_mismatch")

    def test_runtime_result_provider_substitution_is_rejected_before_handoff(self) -> None:
        with self.assertRaisesRegex(AgentRunBlocked, "Runtime result provider identity mismatch"):
            self.run_agent(failure_mode="result_provider_mismatch")
        record = read_json(self.key_roots()[0] / "attempt-001" / "record.json")
        self.assertEqual(record["validation"]["status"], "blocked_provider_identity")

    def test_common_handoff_schema_requires_provider_identity(self) -> None:
        schema = json.loads((CONTRACTS / "common_handoff.schema.json").read_text(encoding="utf-8"))
        self.assertIn("provider_id", schema["required"])
        self.assertEqual(schema["properties"]["provider_id"]["minLength"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
