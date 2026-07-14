from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_runner import AgentRunBlocked, AgentRunner
from agent_runtime import ProviderRegistry
from audit_event_chain import read_events
from fixtures.simulated_agents.mock_runtime import SyntheticAgentProvider
from orchestrator import CaseQueueOrchestrator, OrchestrationError, atomic_write_json, read_json


AUTOMATION = Path(__file__).resolve().parent
CONTRACTS = AUTOMATION / "contracts"
FIXTURE_ROOT = AUTOMATION / "fixtures" / "simulated_agents"
QUEUE = AUTOMATION / "fixtures" / "simulated_case" / "queue.json"
ALL_CONTRACTS = [
    "cold-truth.strategist",
    "cold-truth.research-verifier",
    "cold-truth.writer",
    "cold-truth.editor",
    "cold-truth.visual-producer",
    "cold-truth.shorts-editor",
    "cold-truth.upload-manager",
]


class EpisodeIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def orchestrator(self, episode_id: str = "episode-h6-primary") -> CaseQueueOrchestrator:
        return CaseQueueOrchestrator(
            QUEUE,
            self.root / "run",
            run_id="h6-identity-run",
            episode_id=episode_id,
            dry_run=True,
        )

    @staticmethod
    def script_approval(orch: CaseQueueOrchestrator, *, episode_id: str | None = None) -> dict:
        packet = read_json(orch.artifact_dir / "checkpoint_1_packet.json")
        return {
            "schema_version": "cold_truth.human_approval.v1",
            "approval_id": "h6-script-approval-0001",
            "purpose": "approve_script_for_canonicalization",
            "checkpoint": "script",
            "run_id": orch.run_id,
            "case_id": packet["case_id"],
            "episode_id": episode_id or orch.episode_id,
            "reviewer_role": "human_owner",
            "human_approved": True,
            "approved_by": "Synthetic Reviewer",
            "reason": "H6 offline identity test",
            "issued_at_utc": "2026-07-01T12:00:00Z",
            "expires_at_utc": "2099-07-01T12:00:00Z",
            "status": "active",
            "single_use": True,
            "consumed": False,
            "consumption_count": 0,
            "only_allowed_next_state": "SCRIPT_APPROVED",
            "publishing_enabled": False,
            "real_production_enabled": False,
            "reverse_outline_sha256": packet["reverse_outline"]["sha256"],
            "script_draft_sha256": packet["reviewed_draft"]["sha256"],
        }

    def runner(self, run_root: Path | None = None) -> AgentRunner:
        provider = SyntheticAgentProvider(FIXTURE_ROOT)
        registry = ProviderRegistry()
        registry.register(provider, ALL_CONTRACTS)
        return AgentRunner(CONTRACTS, run_root or self.root / "agent-run", registry, mode="synthetic")

    @staticmethod
    def strategist_inputs() -> dict:
        return {
            "candidate_queue": QUEUE,
            "batch_size": 3,
            "content_standard": FIXTURE_ROOT / "content_standard_fixture.md",
        }

    def test_episode_id_matches_state_manifest_status_packet_and_every_event(self) -> None:
        orch = self.orchestrator()
        state = orch.run_until_blocked()
        manifest = read_json(orch.manifest_path)
        status = read_json(orch.status_path)
        packet = read_json(orch.artifact_dir / "checkpoint_1_packet.json")
        self.assertEqual(state["episode_id"], orch.episode_id)
        self.assertEqual(manifest["episode_id"], orch.episode_id)
        self.assertEqual(status["episode_id"], orch.episode_id)
        self.assertEqual(packet["episode_id"], orch.episode_id)
        self.assertTrue(read_events(orch.event_path))
        self.assertTrue(all(event["episode_id"] == orch.episode_id for event in read_events(orch.event_path)))

    def test_resume_with_different_episode_id_is_rejected(self) -> None:
        self.orchestrator("episode-h6-first").run_until_blocked()
        mismatched = self.orchestrator("episode-h6-second")
        with self.assertRaisesRegex(OrchestrationError, "Run identity"):
            mismatched.run_until_blocked()

    def test_manifest_episode_substitution_is_rejected_on_resume(self) -> None:
        orch = self.orchestrator()
        orch.run_until_blocked()
        manifest = read_json(orch.manifest_path)
        manifest["episode_id"] = "episode-substituted"
        atomic_write_json(orch.manifest_path, manifest)
        with self.assertRaisesRegex(OrchestrationError, "Manifest identity"):
            orch.run_until_blocked()

    def test_wrong_episode_approval_creates_no_consumption_record(self) -> None:
        orch = self.orchestrator()
        orch.run_until_blocked()
        atomic_write_json(
            orch.script_approval,
            self.script_approval(orch, episode_id="episode-wrong-substitution"),
        )
        with self.assertRaisesRegex(OrchestrationError, "episode_id"):
            orch.run_until_blocked()
        self.assertFalse(orch.approval_consumption_root.exists())

    def test_consumption_record_retains_exact_episode_binding(self) -> None:
        orch = self.orchestrator()
        orch.run_until_blocked()
        atomic_write_json(orch.script_approval, self.script_approval(orch))
        orch.run_until_blocked()
        record_paths = list(orch.approval_consumption_root.glob("*.json"))
        self.assertEqual(len(record_paths), 1)
        self.assertEqual(read_json(record_paths[0])["episode_id"], orch.episode_id)

    def test_agent_idempotency_and_handoff_are_episode_bound(self) -> None:
        runner = self.runner()
        first = runner.run(
            "cold-truth.strategist",
            run_id="h6-agent-run",
            case_id="synthetic-queue",
            episode_id="episode-h6-agent-one",
            stage="strategist_intake",
            inputs=self.strategist_inputs(),
        )
        second = runner.run(
            "cold-truth.strategist",
            run_id="h6-agent-run",
            case_id="synthetic-queue",
            episode_id="episode-h6-agent-two",
            stage="strategist_intake",
            inputs=self.strategist_inputs(),
        )
        self.assertNotEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(first.handoff["episode_id"], "episode-h6-agent-one")
        self.assertEqual(second.handoff["episode_id"], "episode-h6-agent-two")

    def test_agent_handoff_episode_mismatch_fails_contract_validation(self) -> None:
        runner = self.runner(self.root / "mismatch-agent-run")
        with self.assertRaisesRegex(AgentRunBlocked, "episode_id"):
            runner.run(
                "cold-truth.strategist",
                run_id="h6-agent-mismatch",
                case_id="synthetic-queue",
                episode_id="episode-h6-expected",
                stage="strategist_intake",
                inputs=self.strategist_inputs(),
                failure_mode="episode_mismatch",
            )

    def test_common_handoff_schema_requires_episode_id(self) -> None:
        schema = json.loads((CONTRACTS / "common_handoff.schema.json").read_text(encoding="utf-8"))
        self.assertIn("episode_id", schema["required"])
        self.assertEqual(schema["properties"]["episode_id"]["minLength"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
