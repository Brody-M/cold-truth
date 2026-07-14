from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from human_approval_lifecycle import ApprovalLifecycleError, validate_and_consume


NOW = datetime(2026, 7, 14, 16, 0, 0, tzinfo=timezone.utc)
HASH_A = "a" * 64
HASH_B = "b" * 64


class HumanApprovalLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.approval_path = self.root / "approval.json"
        self.consumption_root = self.root / "consumptions"
        self.expected = {
            "purpose": "approve_script_for_canonicalization",
            "run_id": "synthetic-h1-run",
            "case_id": "synthetic-case",
            "episode_id": "episode-synthetic-h1",
            "checkpoint": "script",
            "only_allowed_next_state": "SCRIPT_APPROVED",
            "bound_hashes": {
                "reverse_outline_sha256": HASH_A,
                "script_draft_sha256": HASH_B,
            },
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def candidate(self, **changes: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": "cold_truth.human_approval.v1",
            "approval_id": "h1-script-approval-0001",
            "purpose": "approve_script_for_canonicalization",
            "run_id": "synthetic-h1-run",
            "case_id": "synthetic-case",
            "episode_id": "episode-synthetic-h1",
            "checkpoint": "script",
            "reviewer_role": "human_owner",
            "human_approved": True,
            "approved_by": "Synthetic Human Owner",
            "reason": "H1 offline lifecycle test",
            "issued_at_utc": "2026-07-14T15:00:00Z",
            "expires_at_utc": "2026-07-14T17:00:00Z",
            "status": "active",
            "single_use": True,
            "consumed": False,
            "consumption_count": 0,
            "only_allowed_next_state": "SCRIPT_APPROVED",
            "publishing_enabled": False,
            "real_production_enabled": False,
            "reverse_outline_sha256": HASH_A,
            "script_draft_sha256": HASH_B,
        }
        value.update(changes)
        return value

    def write(self, value: dict[str, object]) -> None:
        self.approval_path.write_text(json.dumps(value), encoding="utf-8")

    def consume(self) -> dict[str, object]:
        return validate_and_consume(
            self.approval_path,
            self.consumption_root,
            expected=self.expected,
            clock=lambda: NOW,
        )

    def assert_rejected_without_artifact(self, **changes: object) -> None:
        self.write(self.candidate(**changes))
        with self.assertRaises(ApprovalLifecycleError):
            self.consume()
        self.assertEqual(list(self.consumption_root.glob("*.json")) if self.consumption_root.exists() else [], [])

    def test_valid_candidate_is_consumed_once_with_safe_record(self) -> None:
        self.write(self.candidate())
        result = self.consume()
        self.assertTrue(result["consumed"])
        self.assertEqual(result["consumption_count"], 1)
        record = json.loads(Path(str(result["consumption_record_path"])).read_text(encoding="utf-8"))
        self.assertEqual(record["status"], "consumed")
        self.assertFalse(record["publishing_enabled"])
        self.assertFalse(record["real_production_enabled"])
        self.assertNotIn("approved_by", record)
        self.assertNotIn("reason", record)

    def test_replay_is_rejected_without_second_record(self) -> None:
        self.write(self.candidate())
        self.consume()
        with self.assertRaisesRegex(ApprovalLifecycleError, "already consumed"):
            self.consume()
        self.assertEqual(len(list(self.consumption_root.glob("*.json"))), 1)

    def test_expired_candidate_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(expires_at_utc="2026-07-14T16:00:00Z")

    def test_future_candidate_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(issued_at_utc="2026-07-14T16:00:01Z")

    def test_non_human_owner_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(reviewer_role="editor_agent")

    def test_wrong_purpose_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(purpose="approve_assembly_for_dry_run_render_plan")

    def test_wrong_run_scope_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(run_id="different-run")

    def test_stale_hash_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(script_draft_sha256="c" * 64)

    def test_premarked_consumed_candidate_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(status="consumed", consumed=True, consumption_count=1)

    def test_production_or_publishing_enablement_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(publishing_enabled=True)
        self.assert_rejected_without_artifact(real_production_enabled=True)

    def test_invalid_approval_id_creates_no_record(self) -> None:
        self.assert_rejected_without_artifact(approval_id="../escape")
        self.assertFalse((self.root.parent / "escape.json").exists())

    def test_assembly_render_flag_false_is_rejected_before_consumption(self) -> None:
        self.expected = {
            "purpose": "approve_assembly_for_dry_run_render_plan",
            "run_id": "synthetic-h1-run",
            "case_id": "synthetic-case",
            "episode_id": "episode-synthetic-h1",
            "checkpoint": "assembly",
            "only_allowed_next_state": "ASSEMBLY_APPROVED",
            "bound_hashes": {
                "longform_assembly_sha256": HASH_A,
                "shorts_assembly_sha256": HASH_B,
            },
            "required_exact": {"render_authorized": True},
        }
        self.write(
            self.candidate(
                approval_id="h1-assembly-approval-0001",
                purpose="approve_assembly_for_dry_run_render_plan",
                checkpoint="assembly",
                only_allowed_next_state="ASSEMBLY_APPROVED",
                reverse_outline_sha256=None,
                script_draft_sha256=None,
                longform_assembly_sha256=HASH_A,
                shorts_assembly_sha256=HASH_B,
                render_authorized=False,
            )
        )
        with self.assertRaisesRegex(ApprovalLifecycleError, "render_authorized"):
            self.consume()
        self.assertEqual(list(self.consumption_root.glob("*.json")) if self.consumption_root.exists() else [], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
