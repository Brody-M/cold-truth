from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator import CaseQueueOrchestrator, atomic_write_json, read_json
from status_view import STATUS_SCHEMA_VERSION, build_status_view


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "simulated_case" / "queue.json"
SCHEMA = Path(__file__).resolve().parent / "contracts" / "status_view.schema.json"


class StatusViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def orchestrator(self, queue: Path = FIXTURE, run_id: str = "h4-status-test") -> CaseQueueOrchestrator:
        return CaseQueueOrchestrator(queue, self.root / run_id, run_id=run_id, dry_run=True)

    @staticmethod
    def approve_script(orch: CaseQueueOrchestrator) -> None:
        packet = read_json(orch.artifact_dir / "checkpoint_1_packet.json")
        atomic_write_json(
            orch.script_approval,
            {
                "schema_version": "cold_truth.human_approval.v1",
                "approval_id": f"script-{orch.run_id}-h4-0001",
                "purpose": "approve_script_for_canonicalization",
                "checkpoint": "script",
                "run_id": orch.run_id,
                "case_id": packet["case_id"],
                "episode_id": packet["episode_id"],
                "reviewer_role": "human_owner",
                "human_approved": True,
                "approved_by": "Synthetic Reviewer",
                "reason": "H4 offline status test",
                "issued_at_utc": "2026-07-01T12:00:00Z",
                "expires_at_utc": "2099-07-14T12:00:00Z",
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
                "approval_id": f"assembly-{orch.run_id}-h4-0001",
                "purpose": "approve_assembly_for_dry_run_render_plan",
                "checkpoint": "assembly",
                "run_id": orch.run_id,
                "case_id": packet["case_id"],
                "episode_id": packet["episode_id"],
                "reviewer_role": "human_owner",
                "human_approved": True,
                "render_authorized": True,
                "approved_by": "Synthetic Reviewer",
                "reason": "H4 offline status test",
                "issued_at_utc": "2026-07-01T12:05:00Z",
                "expires_at_utc": "2099-07-14T12:05:00Z",
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

    def test_script_checkpoint_reports_one_human_action_and_last_clean_artifact(self) -> None:
        orch = self.orchestrator()
        orch.run_until_blocked()
        status = read_json(orch.status_path)
        self.assertEqual(status["schema_version"], STATUS_SCHEMA_VERSION)
        self.assertEqual(status["current_checkpoint"], "AWAITING_SCRIPT_APPROVAL")
        self.assertEqual(status["blocker"]["code"], "HUMAN_APPROVAL_REQUIRED")
        self.assertEqual(status["last_clean_artifact"]["name"], "checkpoint_1_packet.json")
        self.assertEqual(status["next_permitted_action"]["action"], "HUMAN_REVIEW_REVERSE_OUTLINE_AND_FULL_DRAFT")
        self.assertEqual(status["next_permitted_action"]["maximum_action_count"], 1)
        self.assertFalse(status["approvals"]["script"]["present"])

    def test_assembly_checkpoint_reports_consumed_script_and_missing_assembly_approval(self) -> None:
        orch = self.orchestrator(run_id="h4-assembly-status")
        orch.run_until_blocked()
        self.approve_script(orch)
        orch.run_until_blocked()
        status = read_json(orch.status_path)
        self.assertEqual(status["current_checkpoint"], "AWAITING_ASSEMBLY_APPROVAL")
        self.assertTrue(status["approvals"]["script"]["consumed"])
        self.assertEqual(status["approvals"]["script"]["consumption_count"], 1)
        self.assertFalse(status["approvals"]["assembly"]["present"])
        self.assertEqual(status["last_clean_artifact"]["name"], "checkpoint_2_packet.json")

    def test_runtime_block_reports_exact_blocker_and_no_downstream_action(self) -> None:
        queue = json.loads(FIXTURE.read_text(encoding="utf-8"))
        queue["synthetic_stage_data"]["narration_duration_seconds"] = 479.999
        queue_path = self.root / "short_queue.json"
        atomic_write_json(queue_path, queue)
        orch = self.orchestrator(queue_path, "h4-runtime-block")
        orch.run_until_blocked()
        self.approve_script(orch)
        orch.run_until_blocked()
        status = read_json(orch.status_path)
        self.assertEqual(status["current_checkpoint"], "BLOCKED_RUNTIME")
        self.assertEqual(status["blocker"]["code"], "BLOCKED_RUNTIME")
        self.assertIn("480.000", status["blocker"]["message"])
        self.assertEqual(status["next_permitted_action"]["action"], "STOP_AND_REVISE_SOURCE_BOUND_SCRIPT_OR_APPROVE_EXCEPTION")

    def test_complete_status_keeps_all_external_capabilities_false(self) -> None:
        orch = self.orchestrator(run_id="h4-complete-status")
        orch.run_until_blocked()
        self.approve_script(orch)
        orch.run_until_blocked()
        self.approve_assembly(orch)
        orch.run_until_blocked()
        status = read_json(orch.status_path)
        self.assertEqual(status["current_checkpoint"], "DRY_RUN_COMPLETE")
        self.assertEqual(status["next_permitted_action"]["action"], "STOP_FOR_HUMAN_REVIEW")
        self.assertTrue(all(value is False for value in status["capabilities"].values()))
        self.assertTrue(status["approvals"]["assembly"]["consumed"])

    def test_invalidation_status_reports_stale_items_and_exact_restart(self) -> None:
        orch = self.orchestrator(run_id="h4-invalidation-status")
        orch.run_until_blocked()
        self.approve_script(orch)
        orch.run_until_blocked()
        state = orch.register_artifact_revision(
            "narration_descriptor.json",
            {"schema_version": "1.0", "status": "revised-offline-descriptor"},
        )
        self.assertEqual(state["state"], "INVALIDATED_UPSTREAM_CHANGE")
        status = read_json(orch.status_path)
        self.assertEqual(status["blocker"]["code"], "UPSTREAM_HASH_CHANGED")
        self.assertGreater(status["stale_artifact_count"], 0)
        self.assertGreater(status["stale_record_count"], 0)
        self.assertEqual(status["next_permitted_action"]["action"], "RETURN_TO_NARRATION_AND_RUNTIME_PREFLIGHT")
        self.assertTrue(status["approvals"]["script"]["present"])
        self.assertFalse(status["approvals"]["assembly"]["present"])

    def test_status_hash_is_deterministic_for_identical_state(self) -> None:
        state = {
            "run_id": "deterministic-status",
            "episode_id": "episode-deterministic-status",
            "state": "QUEUED",
            "dry_run": True,
            "selected_case": None,
            "artifact_registry": {},
            "stale_artifacts": [],
        }
        self.assertEqual(build_status_view(state), build_status_view(state))

    def test_status_schema_is_valid_json_and_covers_emitted_top_level_fields(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        emitted = build_status_view({"run_id": "schema-test", "episode_id": "episode-schema-test", "state": "QUEUED", "dry_run": True})
        self.assertEqual(set(schema["required"]), set(emitted))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
