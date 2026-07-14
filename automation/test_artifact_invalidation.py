from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_invalidation import ARTIFACT_DEPENDENCIES, GRAPH_VERSION
from orchestrator import CaseQueueOrchestrator, OrchestrationError


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "simulated_case" / "queue.json"


class ArtifactInvalidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.orchestrator = CaseQueueOrchestrator(
            FIXTURE,
            self.root / "run",
            run_id="h3-invalidation-test",
            dry_run=True,
        )
        self.orchestrator.initialize()
        state = self.orchestrator.load_state()
        names = set(ARTIFACT_DEPENDENCIES)
        for parents in ARTIFACT_DEPENDENCIES.values():
            names.update(parents)
        for name in sorted(names):
            path = self.orchestrator.artifact_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{name} v1", encoding="utf-8")
            state["artifact_registry"][name] = self.orchestrator._artifact_record(path)
        state["script_approval"] = {"approval_id": "synthetic-script-approval"}
        state["assembly_approval"] = {"approval_id": "synthetic-assembly-approval"}
        state["state"] = "DRY_RUN_COMPLETE"
        self.orchestrator._save_state(state)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def revise(self, name: str):
        return self.orchestrator.register_artifact_revision(name, f"{name} v2")

    def test_research_change_invalidates_all_editorial_and_production_descendants(self) -> None:
        state = self.revise("Research_Source_Ledger.md")
        for name in (
            "Research_Verification.json",
            "Script_Draft.md",
            "Script_Final.md",
            "narration_descriptor.json",
            "longform_alignment.json",
            "longform_assets.json",
            "shorts_assets.json",
            "longform_assembly.json",
            "render_plan.json",
            "metadata_plan.json",
        ):
            self.assertIn(name, state["stale_artifacts"])
            self.assertNotIn(name, state["artifact_registry"])
        self.assertIn("Research_Source_Ledger.md", state["artifact_registry"])
        self.assertNotIn("script_approval", state)
        self.assertNotIn("assembly_approval", state)
        self.assertEqual(state["next_required_checkpoint"], "RESEARCH_VERIFICATION_AND_VIABILITY")

    def test_script_change_invalidates_both_approvals_and_all_media_descendants(self) -> None:
        state = self.revise("Script_Final.md")
        self.assertNotIn("script_approval", state)
        self.assertNotIn("assembly_approval", state)
        self.assertIn("narration_descriptor.json", state["stale_artifacts"])
        self.assertIn("audit_completion.json", state["stale_artifacts"])
        self.assertNotIn("Reverse_Outline.md", state["stale_artifacts"])
        self.assertEqual(state["next_required_checkpoint"], "PAIRED_SCRIPT_REVIEW")

    def test_narration_change_preserves_script_approval_but_invalidates_assembly(self) -> None:
        state = self.revise("narration_descriptor.json")
        self.assertIn("script_approval", state)
        self.assertNotIn("assembly_approval", state)
        self.assertIn("preflight.json", state["stale_artifacts"])
        self.assertIn("longform_alignment.json", state["stale_artifacts"])
        self.assertIn("render_plan.json", state["stale_artifacts"])
        self.assertEqual(state["next_required_checkpoint"], "NARRATION_AND_RUNTIME_PREFLIGHT")

    def test_alignment_change_invalidates_visuals_and_assemblies_only(self) -> None:
        state = self.revise("longform_alignment.json")
        self.assertIn("script_approval", state)
        self.assertNotIn("assembly_approval", state)
        self.assertNotIn("narration_descriptor.json", state["stale_artifacts"])
        self.assertNotIn("preflight.json", state["stale_artifacts"])
        self.assertIn("longform_assets.json", state["stale_artifacts"])
        self.assertIn("shorts_assets.json", state["stale_artifacts"])
        self.assertIn("longform_assembly.json", state["stale_artifacts"])
        self.assertEqual(state["next_required_checkpoint"], "ALIGNMENT_AND_VISUAL_PLANNING")

    def test_longform_visual_change_invalidates_both_visual_branches_downstream(self) -> None:
        state = self.revise("longform_assets.json")
        self.assertIn("script_approval", state)
        self.assertNotIn("assembly_approval", state)
        for name in ("Shorts_Package.md", "shorts_assets.json", "track_isolation.json", "longform_assembly.json", "shorts_assembly.json", "render_plan.json"):
            self.assertIn(name, state["stale_artifacts"])
        self.assertNotIn("longform_alignment.json", state["stale_artifacts"])
        self.assertEqual(state["next_required_checkpoint"], "LONGFORM_VISUAL_REVIEW")

    def test_superseded_files_and_records_are_preserved_for_audit(self) -> None:
        original = self.orchestrator.load_state()["artifact_registry"]["narration_descriptor.json"]
        state = self.revise("narration_descriptor.json")
        records = state["stale_artifact_records"]
        source_records = [item for item in records if item["name"] == "narration_descriptor.json"]
        self.assertEqual(len(source_records), 1)
        self.assertEqual(source_records[0]["sha256"], original["sha256"])
        self.assertEqual(source_records[0]["dependency_graph_version"], GRAPH_VERSION)
        self.assertTrue(Path(original["path"]).is_file())

    def test_unchanged_hash_creates_no_revision_or_invalidation(self) -> None:
        with self.assertRaisesRegex(OrchestrationError, "unchanged"):
            self.orchestrator.register_artifact_revision(
                "narration_descriptor.json",
                "narration_descriptor.json v1",
            )
        state = self.orchestrator.load_state()
        self.assertNotIn("invalidation_history", state)
        self.assertFalse((self.orchestrator.artifact_dir / "revisions").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
