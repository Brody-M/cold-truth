from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from c5_narration_preflight_gate import BLOCKED, LOCKED_PROFILE, PASSED, run_preflight
from json_schema_subset import validate_schema_compatibility


AUTOMATION = Path(__file__).resolve().parent
FIXTURE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace"
C5 = FIXTURE / "narration_preflight"
LIVE = FIXTURE / "output" / "c3_real_writer_editor_chain"
WRITER = next((LIVE / "writer" / "agent_runs").rglob("strategist_handoff.json"))
EDITOR = next((LIVE / "editor" / "agent_runs").rglob("strategist_handoff.json"))
APPROVAL = C5 / "synthetic_valid_script_approval.json"
PROFILE = C5 / "synthetic_locked_narration_profile.json"
APPROVAL_SCHEMA = FIXTURE / "approval_gate" / "script_approval.schema.json"
REQUEST_SCHEMA = C5 / "narration_preflight_request.schema.json"
RESULT_SCHEMA = C5 / "narration_preflight_result.schema.json"


def base_request(identifier: str = "C5-PREFLIGHT-REQUEST-0001") -> dict:
    return {
        "schema_version": "1.0", "request_id": identifier,
        "case_id": "glass-river-writing-fixture",
        "requested_stage": "narration_preflight_only",
        "requested_output_path": "proposed/synthetic_mia_narration.mp3",
        "requested_output_format": "mp3_44100_128",
        "create_output_file": False, "invoke_provider": False,
        "narration_authorized": False, "network_authorized": False,
        "asset_authorized": False, "assembly_authorized": False,
        "rendering_authorized": False, "upload_authorized": False,
        "scheduling_authorized": False, "publishing_enabled": False,
        "real_production_enabled": False,
    }


class Harness:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(dir=C5 / "output")
        self.root = Path(self.temp.name)

    def close(self): self.temp.cleanup()

    def put(self, name: str, value: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return path

    def run(self, *, request: dict | None = None, approval: dict | None = None,
            profile: dict | None = None, approval_path: Path | None | str = "default",
            writer: Path = WRITER, editor: Path = EDITOR):
        request_path = self.put("request.json", request or base_request())
        profile_path = self.put("profile.json", profile or copy.deepcopy(LOCKED_PROFILE))
        if approval_path == "default":
            if approval is None: path = APPROVAL
            else: path = self.put("approval.json", approval)
        else: path = approval_path
        return run_preflight(
            fixture_root=FIXTURE, writer_path=writer, editor_path=editor,
            approval_path=path, profile_path=profile_path, request_path=request_path,
            state_root=self.root / "state", approval_schema_path=APPROVAL_SCHEMA,
            request_schema_path=REQUEST_SCHEMA, result_schema_path=RESULT_SCHEMA,
        )


class C5NarrationPreflightTests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def tearDown(self): self.h.close()

    def test_01_valid_fixture_passes_preflight_only(self):
        result = self.h.run()
        self.assertEqual(result["state"], PASSED)
        self.assertEqual(result["next_required_authorization"], "separate_human_authorization_for_synthetic_narration_test")

    def test_02_pass_creates_no_audio_file(self):
        result = self.h.run()
        proposed = C5 / "output" / result["requested_output_path"]
        self.assertFalse(proposed.exists())
        self.assertFalse(result["output_file_created"])
        self.assertEqual(list(self.h.root.rglob("*.mp3")), [])
        self.assertEqual(list(self.h.root.rglob("*.wav")), [])

    def test_03_pass_authorizes_no_generation_or_network(self):
        result = self.h.run()
        for field in ("narration_generation_authorized", "network_authorized", "asset_authorized",
                      "assembly_authorized", "rendering_authorized", "upload_authorized",
                      "scheduling_authorized", "publishing_enabled", "real_production_enabled"):
            self.assertIs(result[field], False)

    def test_04_every_locked_profile_mismatch_blocks(self):
        changes = {
            "stability": 0.71, "similarity_boost": 0.75, "style": 0.04,
            "speed": 1.0, "use_speaker_boost": False,
            "output_format": "mp3_22050_64",
        }
        for field, replacement in changes.items():
            profile = copy.deepcopy(LOCKED_PROFILE); profile[field] = replacement
            with self.subTest(field=field): self.assertEqual(self.h.run(profile=profile)["state"], BLOCKED)

    def test_05_missing_rejected_and_stale_approval_block(self):
        self.assertEqual(self.h.run(approval_path=None)["state"], BLOCKED)
        approved = json.loads(APPROVAL.read_text(encoding="utf-8"))
        rejected = copy.deepcopy(approved); rejected["decision"] = "reject"
        self.assertEqual(self.h.run(approval=rejected)["state"], BLOCKED)
        stale = copy.deepcopy(approved); stale["upstream_writer_handoff_hash"] = "0" * 64
        self.assertEqual(self.h.run(approval=stale)["state"], BLOCKED)

    def test_06_replayed_or_consumed_approval_blocks(self):
        self.assertEqual(self.h.run()["state"], PASSED)
        self.assertEqual(self.h.run()["state"], BLOCKED)

    def test_07_writer_editor_and_script_hash_mismatches_block(self):
        approved = json.loads(APPROVAL.read_text(encoding="utf-8"))
        for field in ("upstream_writer_handoff_hash", "upstream_editor_handoff_hash", "approved_script_hash"):
            item = copy.deepcopy(approved); item[field] = "0" * 64
            with self.subTest(field=field): self.assertEqual(self.h.run(approval=item)["state"], BLOCKED)

    def test_08_changed_script_text_blocks(self):
        changed = json.loads(WRITER.read_text(encoding="utf-8"))
        changed["result"]["narration_text"] += " Changed synthetic text."
        changed_path = self.h.put("changed_writer.json", changed)
        self.assertEqual(self.h.run(writer=changed_path)["state"], BLOCKED)

    def test_09_invalid_reviewer_blocks(self):
        item = json.loads(APPROVAL.read_text(encoding="utf-8")); item["reviewer_role"] = "editor_agent"
        self.assertEqual(self.h.run(approval=item)["state"], BLOCKED)

    def test_10_output_path_escape_and_absolute_path_block(self):
        for index, value in enumerate(("../escaped.mp3", r"C:\production\real.mp3"), 1):
            request = base_request(f"C5-PATH-REQUEST-{index:04d}"); request["requested_output_path"] = value
            with self.subTest(value=value): self.assertEqual(self.h.run(request=request)["state"], BLOCKED)

    def test_11_forbidden_external_or_secret_fields_block(self):
        for index, field in enumerate(("api_key", "voice_id", "url", "endpoint", "credential", "external_service"), 1):
            request = base_request(f"C5-FORBIDDEN-{index:04d}"); request[field] = "synthetic-disallowed-value"
            with self.subTest(field=field): self.assertEqual(self.h.run(request=request)["state"], BLOCKED)

    def test_12_permission_escalations_block(self):
        fields = ("narration_authorized", "network_authorized", "asset_authorized",
                  "assembly_authorized", "rendering_authorized", "upload_authorized",
                  "scheduling_authorized", "publishing_enabled", "real_production_enabled",
                  "create_output_file", "invoke_provider")
        for index, field in enumerate(fields, 1):
            request = base_request(f"C5-PERMISSION-{index:04d}"); request[field] = True
            with self.subTest(field=field): self.assertEqual(self.h.run(request=request)["state"], BLOCKED)

    def test_13_invalid_stage_and_format_block(self):
        request = base_request("C5-STAGE-REQUEST-0001"); request["requested_stage"] = "narration_generation"
        self.assertEqual(self.h.run(request=request)["state"], BLOCKED)
        request = base_request("C5-FORMAT-REQUEST-0001"); request["requested_output_format"] = "wav"
        self.assertEqual(self.h.run(request=request)["state"], BLOCKED)

    def test_14_profile_denial_flags_are_exact(self):
        for field in ("audio_generation_authorized", "network_authorized", "real_production_enabled", "publishing_enabled"):
            profile = copy.deepcopy(LOCKED_PROFILE); profile[field] = True
            with self.subTest(field=field): self.assertEqual(self.h.run(profile=profile)["state"], BLOCKED)

    def test_15_schemas_are_strictly_compatible(self):
        for path in (REQUEST_SCHEMA, RESULT_SCHEMA, APPROVAL_SCHEMA):
            validate_schema_compatibility(json.loads(path.read_text(encoding="utf-8")))

    def test_16_gate_has_no_process_or_network_runtime(self):
        source = (AUTOMATION / "c5_narration_preflight_gate.py").read_text(encoding="utf-8")
        for forbidden in ("subprocess", "socket", "requests.", "urllib", "codex exec", "ElevenLabs"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(self.h.run()["state"], PASSED)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C5NarrationPreflightTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c5_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
