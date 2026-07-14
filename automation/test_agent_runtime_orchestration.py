from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agent_runner import AgentRunner
from agent_runtime import ProviderRegistry
from fixtures.simulated_agents.mock_runtime import SyntheticAgentProvider
from orchestrator import CaseQueueOrchestrator, OrchestrationError, atomic_write_json, read_json
from runtime_readiness_check import readiness


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
MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mp3", ".wav", ".m4a", ".aac", ".flac"}


class AgentRuntimeEndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run_root = self.root / "synthetic-run"
        self.provider = SyntheticAgentProvider(FIXTURE_ROOT)
        self.registry = ProviderRegistry()
        self.registry.register(self.provider, ALL_CONTRACTS)
        self.runner = AgentRunner(CONTRACTS, self.run_root, self.registry, mode="synthetic")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def orchestrator(self, *, failures=None, retries=None, registry=None) -> CaseQueueOrchestrator:
        runner = self.runner
        if registry is not None:
            runner = AgentRunner(CONTRACTS, self.run_root, registry, mode="synthetic")
        return CaseQueueOrchestrator(
            QUEUE,
            self.run_root,
            run_id="phase-b-synthetic",
            dry_run=True,
            agent_runner=runner,
            agent_failure_modes=failures,
            agent_retry_limits=retries,
        )

    @staticmethod
    def approve_script(orch: CaseQueueOrchestrator) -> None:
        packet = read_json(orch.artifact_dir / "checkpoint_1_packet.json")
        atomic_write_json(
            orch.script_approval,
            {
                "schema_version": "cold_truth.human_approval.v1",
                "approval_id": f"script-{orch.run_id}-0001",
                "purpose": "approve_script_for_canonicalization",
                "checkpoint": "script",
                "run_id": orch.run_id,
                "case_id": packet["case_id"],
                "episode_id": packet["episode_id"],
                "reviewer_role": "human_owner",
                "human_approved": True,
                "approved_by": "Synthetic Reviewer",
                "reason": "Fixture-only approval",
                "issued_at_utc": "2026-07-11T01:00:00Z",
                "expires_at_utc": "2099-07-11T01:00:00Z",
                "status": "active",
                "single_use": True,
                "consumed": False,
                "consumption_count": 0,
                "only_allowed_next_state": "SCRIPT_APPROVED",
                "publishing_enabled": False,
                "real_production_enabled": False,
                "reverse_outline_sha256": packet["reverse_outline"]["sha256"],
                "script_draft_sha256": packet["reviewed_draft"]["sha256"],
            },
        )

    @staticmethod
    def approve_assembly(orch: CaseQueueOrchestrator) -> None:
        packet = read_json(orch.artifact_dir / "checkpoint_2_packet.json")
        atomic_write_json(
            orch.assembly_approval,
            {
                "schema_version": "cold_truth.human_approval.v1",
                "approval_id": f"assembly-{orch.run_id}-0001",
                "purpose": "approve_assembly_for_dry_run_render_plan",
                "checkpoint": "assembly",
                "run_id": orch.run_id,
                "case_id": packet["case_id"],
                "episode_id": packet["episode_id"],
                "reviewer_role": "human_owner",
                "human_approved": True,
                "render_authorized": True,
                "approved_by": "Synthetic Reviewer",
                "reason": "Fixture-only assembly approval",
                "issued_at_utc": "2026-07-11T01:05:00Z",
                "expires_at_utc": "2099-07-11T01:05:00Z",
                "status": "active",
                "single_use": True,
                "consumed": False,
                "consumption_count": 0,
                "only_allowed_next_state": "ASSEMBLY_APPROVED",
                "publishing_enabled": False,
                "real_production_enabled": False,
                "longform_assembly_sha256": packet["longform_assembly"]["sha256"],
                "shorts_assembly_sha256": packet["shorts_assembly"]["sha256"],
            },
        )

    def run_to_checkpoint_two(self, orch: CaseQueueOrchestrator) -> None:
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.approve_script(orch)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_ASSEMBLY_APPROVAL")

    def run_to_completion(self, orch: CaseQueueOrchestrator) -> dict:
        self.run_to_checkpoint_two(orch)
        self.approve_assembly(orch)
        return orch.run_until_blocked()

    def test_autonomous_synthetic_end_to_end_with_two_hard_stops(self) -> None:
        orch = self.orchestrator()
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertEqual(state["selected_case"]["candidate_id"], "cedar-grove-placeholder")
        self.assertEqual(set(state["agent_records"]), {"strategist_intake", "research_verification", "writer", "editor"})
        self.assertFalse((orch.artifact_dir / "narration_descriptor.json").exists())
        state_again = orch.run_until_blocked()
        self.assertEqual(state_again["state"], "AWAITING_SCRIPT_APPROVAL")
        self.approve_script(orch)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_ASSEMBLY_APPROVAL")
        self.assertIn("visual_producer", state["agent_records"])
        self.assertIn("shorts_editor", state["agent_records"])
        self.assertFalse((orch.artifact_dir / "render_plan.json").exists())
        self.approve_assembly(orch)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "DRY_RUN_COMPLETE")
        self.assertIn("upload_manager_metadata", state["agent_records"])
        self.assertFalse(read_json(orch.artifact_dir / "render_plan.json")["media_created"])
        self.assertFalse(read_json(orch.manifest_path)["publishing_enabled"])
        event_text = orch.event_path.read_text(encoding="utf-8").lower()
        self.assertNotIn('"action": "publish"', event_text)
        self.assertNotIn('"action": "upload"', event_text)

    def test_invalid_contract_handoff_blocks_progression(self) -> None:
        orch = self.orchestrator(failures={"writer": "malformed_handoff"})
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AGENT_BLOCKED")
        self.assertIn("contract validation failed", state["last_error"].lower())
        self.assertFalse((orch.artifact_dir / "Script_Draft.md").exists())

    def test_retry_reuses_same_idempotency_key(self) -> None:
        orch = self.orchestrator(failures={"strategist_intake": "fail_once"}, retries={"strategist_intake": 1})
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        record = state["agent_records"]["strategist_intake"]
        self.assertEqual(record["attempt_count"], 2)
        key_root = self.run_root / "agent_runs" / record["idempotency_key"]
        self.assertTrue((key_root / "attempt-001" / "record.json").is_file())
        self.assertTrue((key_root / "attempt-002" / "record.json").is_file())
        request = read_json(key_root / "request.json")
        self.assertEqual(request["idempotency_key"], record["idempotency_key"])

    def test_script_revision_invalidates_all_downstream_and_stale_approval_blocks(self) -> None:
        orch = self.orchestrator()
        state = self.run_to_completion(orch)
        self.assertIn("assembly_approval", state)
        state = orch.register_script_revision("# Revised synthetic reviewed draft\n\nNew fixture version.")
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        for name in ("narration_descriptor.json", "longform_assets.json", "shorts_assets.json", "longform_assembly.json", "validated_local_renders.json", "Upload_Package.md"):
            self.assertIn(name, state["stale_artifacts"])
        self.assertNotIn("script_approval", state)
        self.assertNotIn("assembly_approval", state)
        with self.assertRaises(OrchestrationError):
            orch.run_until_blocked()

    def test_missing_adapter_blocks_safely(self) -> None:
        registry = ProviderRegistry()
        registry.register(self.provider, ["cold-truth.strategist", "cold-truth.research-verifier"])
        orch = self.orchestrator(registry=registry)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AGENT_BLOCKED")
        self.assertIn("no configured runtime adapter", state["last_error"].lower())

    def test_malicious_path_escape_is_rejected_without_escape_write(self) -> None:
        orch = self.orchestrator(failures={"writer": "path_escape"})
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AGENT_BLOCKED")
        self.assertIn("escapes", state["last_error"].lower())
        self.assertEqual(list(self.root.rglob("escape.txt")), [])

    def test_idempotent_fixture_handoff_hash_is_stable(self) -> None:
        inputs = {
            "candidate_queue": QUEUE,
            "batch_size": 3,
            "content_standard": FIXTURE_ROOT / "content_standard_fixture.md",
        }
        first = self.runner.run("cold-truth.strategist", run_id="direct-fixture", case_id="synthetic-queue", stage="strategist_intake", inputs=inputs)
        second = self.runner.run("cold-truth.strategist", run_id="direct-fixture", case_id="synthetic-queue", stage="strategist_intake", inputs=inputs)
        self.assertFalse(first.cache_hit)
        self.assertTrue(second.cache_hit)
        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(hashlib.sha256(first.handoff_path.read_bytes()).hexdigest(), hashlib.sha256(second.handoff_path.read_bytes()).hexdigest())
        second_root = self.root / "independent-synthetic-run"
        second_registry = ProviderRegistry()
        second_registry.register(self.provider, ALL_CONTRACTS)
        independent_runner = AgentRunner(CONTRACTS, second_root, second_registry, mode="synthetic")
        independent = independent_runner.run("cold-truth.strategist", run_id="direct-fixture", case_id="synthetic-queue", stage="strategist_intake", inputs=inputs)
        first_hashes = {item["name"]: item["sha256"] for item in first.handoff["outputs"]}
        independent_hashes = {item["name"]: item["sha256"] for item in independent.handoff["outputs"]}
        self.assertEqual(first_hashes, independent_hashes)

    def test_no_external_commands_apis_media_or_real_case_paths(self) -> None:
        orch = self.orchestrator()
        self.run_to_completion(orch)
        media = [path for path in self.run_root.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES]
        self.assertEqual(media, [])
        for record_path in self.run_root.rglob("record.json"):
            record = read_json(record_path)
            self.assertEqual(record["runtime"]["runtime"], "python-in-process")
            self.assertEqual(record["runtime"]["model"], "none")
            self.assertFalse(record["publishing_enabled"])
        all_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in self.run_root.rglob("*") if path.is_file())
        self.assertNotIn("Jodi Huisentruit", all_text)
        self.assertNotIn("Amy Mihaljevic", all_text)
        self.assertNotIn("Springfield Three", all_text)
        self.assertNotIn("https://", all_text)

    def test_runtime_readiness_check_is_non_invoking_and_real_mode_off(self) -> None:
        report = readiness()
        self.assertTrue(report["fixture_mode_available"])
        self.assertTrue(report["required_contract_files_present"])
        self.assertFalse(report["real_production_mode_enabled"])
        self.assertFalse(report["publishing_enabled"])
        self.assertFalse(report["runtime_invoked"])
        self.assertEqual(report["external_calls"], 0)
        self.assertFalse(report["secrets_read_or_printed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
