from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from c5_narration_preflight_gate import LOCKED_PROFILE
from c6_synthetic_narration_gate import BLOCKED, READY, path_text_sha256
from json_schema_subset import validate_schema_compatibility
from providers.synthetic_narration_adapter import SyntheticNarrationAdapter


AUTOMATION = Path(__file__).resolve().parent
FIXTURE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace"
C5 = FIXTURE / "narration_preflight"
C6_OUTPUT = C5 / "output" / "c6_synthetic_narration_adapter"
LIVE = FIXTURE / "output" / "c3_real_writer_editor_chain"
WRITER = next((LIVE / "writer" / "agent_runs").rglob("strategist_handoff.json"))
EDITOR = next((LIVE / "editor" / "agent_runs").rglob("strategist_handoff.json"))
C4_APPROVAL = C5 / "synthetic_valid_script_approval.json"
C5_PREFLIGHT = C5 / "synthetic_passed_preflight_result.json"
PROFILE = C5 / "synthetic_locked_narration_profile.json"
C6_AUTH = C5 / "synthetic_narration_authorization.json"
REQUEST = C5 / "synthetic_narration_request.json"
C4_SCHEMA = FIXTURE / "approval_gate" / "script_approval.schema.json"
C5_SCHEMA = C5 / "narration_preflight_result.schema.json"
C6_SCHEMA = C5 / "narration_authorization.schema.json"
REQUEST_SCHEMA = C5 / "synthetic_narration_request.schema.json"


class Harness:
    def __init__(self):
        C6_OUTPUT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=C6_OUTPUT)
        self.root = Path(self.temp.name)
        self.adapter = SyntheticNarrationAdapter(fixture_root=FIXTURE, state_root=self.root / "state")

    def close(self): self.temp.cleanup()

    def put(self, name: str, value: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return path

    def paths(self, **overrides):
        values = {
            "writer_path": WRITER, "editor_path": EDITOR,
            "c4_approval_path": C4_APPROVAL, "c5_preflight_path": C5_PREFLIGHT,
            "profile_path": PROFILE, "c6_authorization_path": C6_AUTH,
            "request_path": REQUEST, "c4_approval_schema_path": C4_SCHEMA,
            "c5_result_schema_path": C5_SCHEMA,
            "c6_authorization_schema_path": C6_SCHEMA,
            "request_schema_path": REQUEST_SCHEMA,
        }
        values.update(overrides)
        return values

    def run(self, mode="validate_request", **overrides):
        write = overrides.pop("write_fake_artifact", False)
        return self.adapter.execute(mode, write_fake_artifact=write, **self.paths(**overrides))


class C6SyntheticNarrationTests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def tearDown(self): self.h.close()

    def test_01_valid_chain_reaches_ready_only(self):
        result = self.h.run()
        self.assertEqual(result, {
            "state": READY, "provider_invoked": False, "network_invoked": False,
            "audio_file_created": False, "real_production_enabled": False,
            "next_required_authorization": "separate_human_authorization_for_one_synthetic_provider_call",
        })

    def test_02_ready_creates_no_audio_or_provider_activity(self):
        result = self.h.run()
        self.assertFalse(result["provider_invoked"]); self.assertFalse(result["network_invoked"])
        self.assertFalse(result["audio_file_created"])
        self.assertEqual(list(self.h.root.rglob("*.mp3")), [])
        self.assertEqual(list(self.h.root.rglob("*.wav")), [])

    def test_03_fake_runner_returns_and_writes_metadata_only(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8")); request["request_id"] = "C6-FAKE-RUNNER-0001"; request["write_fake_artifact"] = True
        request_path = self.h.put("fake_request.json", request)
        outcome = self.h.run("fake_runner", request_path=request_path, write_fake_artifact=True)
        self.assertEqual(outcome["decision"]["state"], READY)
        self.assertEqual(outcome["fake_metadata"]["artifact_type"], "non_audio_fixture_metadata")
        self.assertEqual(outcome["fake_metadata"]["deterministic_fake_audio_bytes"], 0)
        fake_files = list(self.h.root.rglob("*.fake.json")); self.assertEqual(len(fake_files), 1)
        self.assertEqual(list(self.h.root.rglob("*.mp3")), []); self.assertEqual(list(self.h.root.rglob("*.wav")), [])

    def test_04_authorization_consumed_once_and_replay_blocks(self):
        self.assertEqual(self.h.run()["state"], READY)
        self.assertEqual(self.h.run()["state"], BLOCKED)

    def test_05_missing_c4_c5_or_c6_artifact_blocks(self):
        for field in ("c4_approval_path", "c5_preflight_path", "c6_authorization_path"):
            with self.subTest(field=field): self.assertEqual(self.h.run(**{field: None})["state"], BLOCKED)

    def test_06_rejected_or_altered_c4_approval_blocks(self):
        value = json.loads(C4_APPROVAL.read_text(encoding="utf-8")); value["decision"] = "reject"
        self.assertEqual(self.h.run(c4_approval_path=self.h.put("rejected_c4.json", value))["state"], BLOCKED)
        value = json.loads(C4_APPROVAL.read_text(encoding="utf-8")); value["approved_script_hash"] = "0" * 64
        self.assertEqual(self.h.run(c4_approval_path=self.h.put("altered_c4.json", value))["state"], BLOCKED)

    def test_07_blocked_stale_or_altered_c5_result_blocks(self):
        for index, (field, replacement) in enumerate((("state", "NARRATION_PREFLIGHT_BLOCKED"), ("approval_id", "C5-OTHER-APPROVAL-0001"), ("output_format", "wav")), 1):
            value = json.loads(C5_PREFLIGHT.read_text(encoding="utf-8")); value[field] = replacement
            path = self.h.put(f"changed_c5_{index}.json", value)
            with self.subTest(field=field): self.assertEqual(self.h.run(c5_preflight_path=path)["state"], BLOCKED)

    def test_08_malformed_altered_or_hash_mismatched_c6_authorization_blocks(self):
        source = json.loads(C6_AUTH.read_text(encoding="utf-8"))
        for index, field in enumerate(("upstream_writer_handoff_hash", "upstream_editor_handoff_hash", "approved_script_hash", "narration_preflight_result_hash", "locked_profile_hash", "requested_output_path_hash"), 1):
            value = copy.deepcopy(source); value[field] = "0" * 64
            with self.subTest(field=field): self.assertEqual(self.h.run(c6_authorization_path=self.h.put(f"auth_{index}.json", value))["state"], BLOCKED)
        malformed = self.h.root / "malformed.json"; malformed.write_text("{")
        self.assertEqual(self.h.run(c6_authorization_path=malformed)["state"], BLOCKED)

    def test_09_changed_writer_script_or_editor_blocks(self):
        writer = json.loads(WRITER.read_text(encoding="utf-8")); writer["result"]["narration_text"] += " Changed."
        self.assertEqual(self.h.run(writer_path=self.h.put("changed_writer.json", writer))["state"], BLOCKED)
        editor = json.loads(EDITOR.read_text(encoding="utf-8")); editor["result"]["redundancy_check"] = "failed"
        self.assertEqual(self.h.run(editor_path=self.h.put("changed_editor.json", editor))["state"], BLOCKED)

    def test_10_every_locked_profile_mismatch_blocks(self):
        changes = {"stability": 0.71, "similarity_boost": 0.75, "style": 0.04,
                   "speed": 1.0, "use_speaker_boost": False, "output_format": "wav"}
        for index, (field, replacement) in enumerate(changes.items(), 1):
            value = copy.deepcopy(LOCKED_PROFILE); value[field] = replacement
            with self.subTest(field=field): self.assertEqual(self.h.run(profile_path=self.h.put(f"profile_{index}.json", value))["state"], BLOCKED)

    def test_11_forbidden_secret_service_or_environment_fields_block(self):
        source = json.loads(REQUEST.read_text(encoding="utf-8"))
        for index, field in enumerate(("api_key", "voice_id", "endpoint", "url", "credential", "provider_config", "external_service", "environment_variable"), 1):
            value = copy.deepcopy(source); value["request_id"] = f"C6-FORBIDDEN-{index:04d}"; value[field] = "disallowed-reference"
            with self.subTest(field=field): self.assertEqual(self.h.run(request_path=self.h.put(f"forbidden_{index}.json", value))["state"], BLOCKED)

    def test_12_absolute_and_escaping_output_paths_block(self):
        source_request = json.loads(REQUEST.read_text(encoding="utf-8")); source_auth = json.loads(C6_AUTH.read_text(encoding="utf-8"))
        for index, output in enumerate(("../escape.mp3", r"C:\production\real.mp3"), 1):
            request = copy.deepcopy(source_request); request["request_id"] = f"C6-PATH-{index:04d}"; request["requested_output_relative_path"] = output
            auth = copy.deepcopy(source_auth); auth["narration_authorization_id"] = f"C6-PATH-AUTH-{index:04d}"; auth["requested_output_relative_path"] = output; auth["requested_output_path_hash"] = path_text_sha256(output)
            with self.subTest(output=output): self.assertEqual(self.h.run(request_path=self.h.put(f"path_req_{index}.json", request), c6_authorization_path=self.h.put(f"path_auth_{index}.json", auth))["state"], BLOCKED)

    def test_13_network_provider_subprocess_or_audio_requests_block(self):
        source = json.loads(REQUEST.read_text(encoding="utf-8"))
        for index, field in enumerate(("network_requested", "invoke_provider", "invoke_actual_narration"), 1):
            value = copy.deepcopy(source); value["request_id"] = f"C6-INVOKE-{index:04d}"; value[field] = True
            with self.subTest(field=field): self.assertEqual(self.h.run(request_path=self.h.put(f"invoke_{index}.json", value))["state"], BLOCKED)
        for index, field in enumerate(("invoke_subprocess", "create_audio_file"), 1):
            value = copy.deepcopy(source); value["request_id"] = f"C6-EXTRA-{index:04d}"; value[field] = True
            with self.subTest(field=field): self.assertEqual(self.h.run(request_path=self.h.put(f"extra_{index}.json", value))["state"], BLOCKED)

    def test_14_all_later_production_permissions_block(self):
        source = json.loads(REQUEST.read_text(encoding="utf-8"))
        for index, field in enumerate(("asset_authorized", "assembly_authorized", "rendering_authorized", "upload_authorized", "scheduling_authorized", "publishing_enabled", "real_production_enabled"), 1):
            value = copy.deepcopy(source); value["request_id"] = f"C6-PERMISSION-{index:04d}"; value[field] = True
            with self.subTest(field=field): self.assertEqual(self.h.run(request_path=self.h.put(f"permission_{index}.json", value))["state"], BLOCKED)

    def test_15_only_two_adapter_modes_exist(self):
        self.assertEqual(SyntheticNarrationAdapter.MODES, {"validate_request", "fake_runner"})
        self.assertEqual(self.h.run("actual_provider")["state"], BLOCKED)

    def test_16_validation_mode_cannot_write_fake_artifact(self):
        self.assertEqual(self.h.run("validate_request", write_fake_artifact=True)["state"], BLOCKED)
        self.assertEqual(list(self.h.root.rglob("*.fake.json")), [])

    def test_17_schemas_are_strictly_compatible(self):
        for path in (C4_SCHEMA, C5_SCHEMA, C6_SCHEMA, REQUEST_SCHEMA):
            validate_schema_compatibility(json.loads(path.read_text(encoding="utf-8")))

    def test_18_implementation_has_no_external_runtime_route(self):
        source = (AUTOMATION / "c6_synthetic_narration_gate.py").read_text(encoding="utf-8") + (AUTOMATION / "providers" / "synthetic_narration_adapter.py").read_text(encoding="utf-8")
        for term in ("subprocess", "socket", "requests.", "urllib", "os.environ", "codex exec", "ElevenLabs", "ffmpeg"):
            self.assertNotIn(term, source)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C6SyntheticNarrationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c6_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
