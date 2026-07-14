from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from orchestrator import CaseQueueOrchestrator, atomic_write_json, read_json
from track_isolation import TrackIsolationError, build_track_isolation_report


AUTOMATION = Path(__file__).resolve().parent
QUEUE = AUTOMATION / "fixtures" / "simulated_case" / "queue.json"
CONTRACTS = AUTOMATION / "contracts"


class TrackIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def asset(track: str, asset_id: str, source_identity: str) -> dict:
        return {
            "asset_id": asset_id,
            "source_identity": source_identity,
            "track": track,
            "asset_class": "case_broll" if track == "youtube-longform" else "orbital_gameplay",
            "status": "ready",
            "local_record": True,
            "licensed_record": True,
        }

    @staticmethod
    def manifest(track: str, assets: list[dict]) -> dict:
        return {
            "schema_version": "cold_truth.asset_manifest.v1",
            "track": track,
            "shared_assets_allowed": False,
            "synthetic": True,
            "media_created": False,
            "assets": assets,
        }

    def write_pair(self, longform: dict, shorts: dict) -> tuple[Path, Path]:
        long_path = self.root / "longform_assets.json"
        short_path = self.root / "shorts_assets.json"
        atomic_write_json(long_path, longform)
        atomic_write_json(short_path, shorts)
        return long_path, short_path

    def valid_pair(self) -> tuple[dict, dict]:
        return (
            self.manifest("youtube-longform", [self.asset("youtube-longform", "lf-001", "pexels:001")]),
            self.manifest("shorts", [self.asset("shorts", "sh-001", "orbital:001")]),
        )

    def test_valid_manifests_bind_exact_tracks_hashes_and_zero_intersection(self) -> None:
        paths = self.write_pair(*self.valid_pair())
        report = build_track_isolation_report(*paths)
        self.assertTrue(report["passed"])
        self.assertEqual(report["longform_track"], "youtube-longform")
        self.assertEqual(report["shorts_track"], "shorts")
        self.assertEqual(report["shared_asset_count"], 0)
        self.assertFalse(report["shared_assets_allowed"])
        self.assertFalse(report["media_inspected"])
        self.assertFalse(report["media_created"])
        self.assertEqual(report["longform_manifest_sha256"], hashlib.sha256(paths[0].read_bytes()).hexdigest())
        self.assertEqual(report["shorts_manifest_sha256"], hashlib.sha256(paths[1].read_bytes()).hexdigest())

    def test_manifest_track_substitution_is_rejected(self) -> None:
        longform, shorts = self.valid_pair()
        shorts["track"] = "youtube-longform"
        with self.assertRaisesRegex(TrackIsolationError, "track mismatch"):
            build_track_isolation_report(*self.write_pair(longform, shorts))

    def test_asset_track_substitution_is_rejected(self) -> None:
        longform, shorts = self.valid_pair()
        shorts["assets"][0]["track"] = "youtube-longform"
        with self.assertRaisesRegex(TrackIsolationError, "Asset track mismatch"):
            build_track_isolation_report(*self.write_pair(longform, shorts))

    def test_visual_class_policy_is_track_specific(self) -> None:
        longform, shorts = self.valid_pair()
        longform["assets"][0]["asset_class"] = "orbital_gameplay"
        with self.assertRaisesRegex(TrackIsolationError, "Prohibited asset class"):
            build_track_isolation_report(*self.write_pair(longform, shorts))
        longform, shorts = self.valid_pair()
        shorts["assets"][0]["asset_class"] = "case_broll"
        with self.assertRaisesRegex(TrackIsolationError, "Prohibited asset class"):
            build_track_isolation_report(*self.write_pair(longform, shorts))

    def assert_collision(self, field: str, value: str) -> None:
        longform, shorts = self.valid_pair()
        longform["assets"][0][field] = value
        shorts["assets"][0][field] = value
        report = build_track_isolation_report(*self.write_pair(longform, shorts))
        self.assertFalse(report["passed"])
        self.assertEqual(report["shared_asset_count"], 1)
        self.assertEqual(report["shared_asset_identities"], [{"identity_kind": field, "identity": value}])

    def test_shared_asset_id_is_detected(self) -> None:
        self.assert_collision("asset_id", "shared-id")

    def test_relabelled_shared_source_identity_is_detected(self) -> None:
        self.assert_collision("source_identity", "shared-source-record")

    def test_relabelled_shared_content_hash_is_detected(self) -> None:
        self.assert_collision("content_sha256", "a" * 64)

    def test_relabelled_shared_canonical_path_is_detected_without_media_access(self) -> None:
        self.assert_collision("canonical_path", str((self.root / "synthetic-record.bin").resolve()))

    def test_duplicate_identity_within_one_track_is_rejected(self) -> None:
        longform, shorts = self.valid_pair()
        duplicate = copy.deepcopy(longform["assets"][0])
        duplicate["source_identity"] = "pexels:002"
        longform["assets"].append(duplicate)
        with self.assertRaisesRegex(TrackIsolationError, "Duplicate asset_id"):
            build_track_isolation_report(*self.write_pair(longform, shorts))

    def approve_script(self, orch: CaseQueueOrchestrator) -> None:
        packet = read_json(orch.artifact_dir / "checkpoint_1_packet.json")
        atomic_write_json(orch.script_approval, {
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
            "reason": "H8 fixture-only approval",
            "issued_at_utc": "2026-07-14T00:00:00Z",
            "expires_at_utc": "2099-07-14T00:00:00Z",
            "status": "active",
            "single_use": True,
            "consumed": False,
            "consumption_count": 0,
            "only_allowed_next_state": "SCRIPT_APPROVED",
            "publishing_enabled": False,
            "real_production_enabled": False,
            "reverse_outline_sha256": packet["reverse_outline"]["sha256"],
            "script_draft_sha256": packet["reviewed_draft"]["sha256"],
        })

    def test_orchestrator_writes_passing_isolation_before_assembly_checkpoint(self) -> None:
        orch = CaseQueueOrchestrator(QUEUE, self.root / "passing-run", run_id="h8-passing", dry_run=True)
        orch.run_until_blocked()
        self.approve_script(orch)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_ASSEMBLY_APPROVAL")
        report = read_json(orch.artifact_dir / "track_isolation.json")
        self.assertTrue(report["passed"])
        self.assertEqual(report["shared_asset_count"], 0)

    def test_orchestrator_collision_blocks_before_any_assembly_artifact(self) -> None:
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        queue["synthetic_stage_data"]["shorts"]["assets"][0]["source_identity"] = queue["synthetic_stage_data"]["longform_assets"][0]["source_identity"]
        queue_path = self.root / "collision-queue.json"
        atomic_write_json(queue_path, queue)
        orch = CaseQueueOrchestrator(queue_path, self.root / "collision-run", run_id="h8-collision", dry_run=True)
        orch.run_until_blocked()
        self.approve_script(orch)
        state = orch.run_until_blocked()
        self.assertEqual(state["state"], "FAILED")
        self.assertIn("Shared assets detected", state["last_error"])
        self.assertFalse((orch.artifact_dir / "longform_assembly.json").exists())
        self.assertFalse((orch.artifact_dir / "shorts_assembly.json").exists())

    def test_track_schemas_lock_labels_and_no_media_flags(self) -> None:
        asset_schema = json.loads((CONTRACTS / "asset_manifest.schema.json").read_text(encoding="utf-8"))
        isolation_schema = json.loads((CONTRACTS / "track_isolation.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(asset_schema["properties"]["track"]["enum"], ["youtube-longform", "shorts"])
        self.assertEqual(asset_schema["properties"]["shared_assets_allowed"]["const"], False)
        self.assertEqual(isolation_schema["properties"]["media_inspected"]["const"], False)
        self.assertEqual(isolation_schema["properties"]["media_created"]["const"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
