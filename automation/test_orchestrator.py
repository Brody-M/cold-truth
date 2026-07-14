from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator import CaseQueueOrchestrator, atomic_write_json, read_json


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "simulated_case" / "queue.json"


class OrchestratorSimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run_root = self.root / "run"
        self.orchestrator = CaseQueueOrchestrator(FIXTURE, self.run_root, run_id="synthetic-test", dry_run=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def approve_script(self, orchestrator: CaseQueueOrchestrator | None = None) -> None:
        orch = orchestrator or self.orchestrator
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
                "reason": "Synthetic approval for state-machine testing",
                "issued_at_utc": "2026-07-10T12:00:00Z",
                "expires_at_utc": "2099-07-10T12:00:00Z",
                "status": "active",
                "single_use": True,
                "consumed": False,
                "consumption_count": 0,
                "only_allowed_next_state": "SCRIPT_APPROVED",
                "publishing_enabled": False,
                "real_production_enabled": False,
                "reverse_outline_sha256": packet["reverse_outline"]["sha256"],
                "script_draft_sha256": packet["reviewed_draft"]["sha256"]
            },
        )

    def approve_assembly(self, orchestrator: CaseQueueOrchestrator | None = None) -> None:
        orch = orchestrator or self.orchestrator
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
                "reason": "Synthetic approval for state-machine testing",
                "issued_at_utc": "2026-07-10T12:05:00Z",
                "expires_at_utc": "2099-07-10T12:05:00Z",
                "status": "active",
                "single_use": True,
                "consumed": False,
                "consumption_count": 0,
                "only_allowed_next_state": "ASSEMBLY_APPROVED",
                "publishing_enabled": False,
                "real_production_enabled": False,
                "longform_assembly_sha256": packet["longform_assembly"]["sha256"],
                "shorts_assembly_sha256": packet["shorts_assembly"]["sha256"]
            },
        )

    def test_ranking_and_checkpoint_one_stop(self) -> None:
        state = self.orchestrator.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertEqual(state["selected_case"]["candidate_id"], "cedar-grove-placeholder")
        self.assertFalse((self.orchestrator.artifact_dir / "narration_descriptor.json").exists())

    def test_resume_only_after_both_approvals(self) -> None:
        self.orchestrator.run_until_blocked()
        self.approve_script()
        state = self.orchestrator.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_ASSEMBLY_APPROVAL")
        self.assertFalse((self.orchestrator.artifact_dir / "render_plan.json").exists())
        self.approve_assembly()
        state = self.orchestrator.run_until_blocked()
        self.assertEqual(state["state"], "DRY_RUN_COMPLETE")
        render_plan = read_json(self.orchestrator.artifact_dir / "render_plan.json")
        self.assertFalse(render_plan["media_created"])
        self.assertFalse(render_plan["publish"])

    def test_rejection_returns_to_backlog(self) -> None:
        queue = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for candidate in queue["candidates"]:
            candidate["verification_status"] = "fail"
            candidate["viability"] = "Backlog — insufficient long-form material"
        queue_path = self.root / "rejected_queue.json"
        atomic_write_json(queue_path, queue)
        orch = CaseQueueOrchestrator(queue_path, self.root / "rejected_run", run_id="rejected-test", dry_run=True)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "RETURNED_TO_BACKLOG")
        self.assertEqual(len(state["returned_to_backlog"]), 3)

    def test_script_revision_invalidates_downstream(self) -> None:
        self.orchestrator.run_until_blocked()
        self.approve_script()
        self.orchestrator.run_until_blocked()
        state = self.orchestrator.register_script_revision("# Revised synthetic draft\n\nChanged fixture content.")
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertIn("narration_descriptor.json", state["stale_artifacts"])
        self.assertIn("longform_assembly.json", state["stale_artifacts"])
        self.assertNotIn("assembly_approval", state)

    def test_under_eight_minutes_blocks_assembly(self) -> None:
        queue = json.loads(FIXTURE.read_text(encoding="utf-8"))
        queue["synthetic_stage_data"]["narration_duration_seconds"] = 479.999
        queue_path = self.root / "short_queue.json"
        atomic_write_json(queue_path, queue)
        orch = CaseQueueOrchestrator(queue_path, self.root / "short_run", run_id="short-test", dry_run=True)
        orch.run_until_blocked()
        self.approve_script(orch)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "BLOCKED_RUNTIME")
        self.assertFalse(read_json(orch.artifact_dir / "preflight.json")["assembly_allowed"])
        self.assertFalse((orch.artifact_dir / "longform_assembly.json").exists())

    def test_no_render_or_publish_before_assembly_approval(self) -> None:
        self.orchestrator.run_until_blocked()
        self.approve_script()
        state = self.orchestrator.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_ASSEMBLY_APPROVAL")
        manifest = read_json(self.orchestrator.manifest_path)
        self.assertFalse(manifest["publishing_enabled"])
        self.assertFalse((self.orchestrator.artifact_dir / "render_plan.json").exists())
        event_text = self.orchestrator.event_path.read_text(encoding="utf-8")
        self.assertNotIn('"action": "local_render"', event_text)
        self.assertNotIn('"action": "publish"', event_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
