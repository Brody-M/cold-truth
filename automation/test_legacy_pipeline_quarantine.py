from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cold_truth_pipeline as legacy


class LegacyPipelineQuarantineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_handoff_requires_explicit_fixture_mode_and_root(self) -> None:
        with self.assertRaisesRegex(legacy.LegacyPipelineQuarantined, "fixture-only"):
            legacy.write_handoff("Synthetic", "write", {"status": "planned"}, isolated_root=self.root)
        with self.assertRaisesRegex(legacy.LegacyPipelineQuarantined, "explicit isolated"):
            legacy.write_handoff("Synthetic", "write", {"status": "planned"}, fixture_only=True)
        self.assertEqual(list(self.root.rglob("*.json")), [])

    def test_workspace_and_canonical_vault_roots_are_rejected(self) -> None:
        for root in (legacy.ROOT, legacy.VAULT, legacy.VAULT / "2_IN_PRODUCTION"):
            with self.assertRaisesRegex(legacy.LegacyPipelineQuarantined, "outside"):
                legacy.write_handoff(
                    "Synthetic",
                    "write",
                    {"status": "planned"},
                    isolated_root=root,
                    fixture_only=True,
                )

    def test_isolated_handoff_is_non_authoritative_and_contained(self) -> None:
        path = legacy.write_handoff(
            "Synthetic / Fixture",
            "../../write",
            {"status": "planned", "publishing_enabled": False},
            isolated_root=self.root,
            fixture_only=True,
        )
        path.relative_to(self.root)
        self.assertNotIn("..", path.name)
        manifest_path = path.parent / "legacy_fixture_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertFalse(manifest["authoritative"])
        self.assertEqual(manifest["canonical_state_owner"], "automation/orchestrator.py")
        self.assertFalse(manifest["publishing_enabled"])
        self.assertFalse((path.parent / "pipeline_manifest.json").exists())

    def test_provider_execution_helpers_always_fail_closed(self) -> None:
        with self.assertRaisesRegex(legacy.LegacyPipelineQuarantined, "Pexels execution"):
            legacy.pexels_search("synthetic query", True)
        with self.assertRaisesRegex(legacy.LegacyPipelineQuarantined, "ElevenLabs execution"):
            legacy.elevenlabs_voice("synthetic text", self.root / "forbidden.mp3", True)
        self.assertFalse((self.root / "forbidden.mp3").exists())

    def test_voice_planning_does_not_use_environment_override(self) -> None:
        with patch.dict(os.environ, {"ELEVENLABS_VOICE_ID": "forbidden-environment-value"}):
            config = legacy.narration_voice_config()
        self.assertNotEqual(config["voice_id"], "forbidden-environment-value")

    def test_cli_requires_quarantine_flags_before_any_write(self) -> None:
        argv = ["cold_truth_pipeline.py", "write", "--case", "Synthetic", "--source", "fixture"]
        with patch.object(sys, "argv", argv), self.assertRaisesRegex(SystemExit, "quarantined"):
            legacy.main()
        self.assertEqual(list(self.root.rglob("*.json")), [])

    def test_cli_rejects_execute_before_provider_or_input_access(self) -> None:
        missing = self.root / "missing.txt"
        argv = [
            "cold_truth_pipeline.py", "voice", "--case", "Synthetic",
            "--text-file", str(missing), "--target-format", "youtube-longform",
            "--execute", "--fixture-only", "--isolated-run-root", str(self.root),
        ]
        with patch.object(sys, "argv", argv), self.assertRaisesRegex(SystemExit, "--execute is forbidden"):
            legacy.main()
        self.assertEqual(list(self.root.rglob("*.json")), [])

    def test_cli_rejects_inputs_outside_isolated_root(self) -> None:
        outside = Path(tempfile.gettempdir()).resolve() / "h5-outside-script.md"
        if self.root in outside.parents:
            outside = self.root.parent / "h5-outside-script.md"
        argv = [
            "cold_truth_pipeline.py", "visuals", "--case", "Synthetic",
            "--script-file", str(outside), "--video-id", "fixture-video",
            "--fixture-only", "--isolated-run-root", str(self.root),
        ]
        with patch.object(sys, "argv", argv), self.assertRaisesRegex(legacy.LegacyPipelineQuarantined, "inside"):
            legacy.main()
        self.assertEqual(list(self.root.rglob("*.json")), [])

    def test_cli_writes_only_an_isolated_fixture_preview(self) -> None:
        argv = [
            "cold_truth_pipeline.py", "write", "--case", "Synthetic Fixture",
            "--source", "synthetic", "--fixture-only", "--isolated-run-root", str(self.root),
        ]
        output = io.StringIO()
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
            legacy.main()
        response = json.loads(output.getvalue())
        handoff = Path(response["handoff"])
        handoff.relative_to(self.root)
        self.assertTrue(handoff.is_file())
        self.assertTrue((handoff.parent / "legacy_fixture_manifest.json").is_file())

    def test_source_contains_no_http_client_or_provider_endpoint(self) -> None:
        source = Path(legacy.__file__).read_text(encoding="utf-8")
        for forbidden in ("urlopen", "urllib.request", "api.pexels.com", "api.elevenlabs.io"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
