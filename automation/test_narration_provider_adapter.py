from __future__ import annotations

import copy
import inspect
import json
import stat
import tempfile
import unittest
from pathlib import Path

from c5_narration_preflight_gate import LOCKED_PROFILE
from c6_synthetic_narration_gate import path_text_sha256
from handoff_validator import file_sha256
from json_schema_subset import validate_schema_compatibility
from providers.narration_provider_adapter import (
    ALLOWED_PROFILE_KEYS, ALLOWED_REQUEST_KEYS, C7_BLOCKED, C7_READY,
    PERMISSION_KEYS, NarrationProviderAdapter,
)
from testing.c7_fake_http_client import C7AllowlistedFakeLocalHttpClient


AUTOMATION = Path(__file__).resolve().parent
FIXTURE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace"
C5 = FIXTURE / "narration_preflight"
C6_OUTPUT = C5 / "output" / "c6_synthetic_narration_adapter"
C7_OUTPUT = C5 / "output" / "c7_mock_provider_adapter"
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
C8_ROOT = C5 / "future_c8"
C8_SCHEMA = C8_ROOT / "one_time_live_synthetic_provider_authorization.schema.json"


class Harness:
    def __init__(self):
        C6_OUTPUT.mkdir(parents=True, exist_ok=True); C7_OUTPUT.mkdir(parents=True, exist_ok=True)
        self.c6_temp = tempfile.TemporaryDirectory(dir=C6_OUTPUT)
        self.c7_temp = tempfile.TemporaryDirectory(dir=C7_OUTPUT)
        self.c6_root = Path(self.c6_temp.name)
        self.c7_root = Path(self.c7_temp.name)
        self.adapter = NarrationProviderAdapter(
            fixture_root=FIXTURE, c6_state_root=self.c6_root / "state",
            c7_output_root=self.c7_root,
        )

    def close(self):
        self.c6_temp.cleanup(); self.c7_temp.cleanup()

    def put(self, name: str, value: dict) -> Path:
        path = self.c6_root / name
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

    def run(self, client=None, **overrides):
        return self.adapter.execute(client=client, **self.paths(**overrides))


class C7NarrationProviderAdapterTests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def tearDown(self):
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in (C5 / "output").rglob(extension) if path.is_file())
        self.assertEqual(media, [])
        self.h.close()

    def test_01_valid_chain_and_fake_client_build_sanitized_memory_request(self):
        client = C7AllowlistedFakeLocalHttpClient(); result = self.h.run(client)
        self.assertEqual(result["state"], C7_READY); self.assertEqual(client.call_count, 1)
        request = result["sanitized_request"]
        self.assertEqual(set(request), ALLOWED_REQUEST_KEYS)
        self.assertEqual(set(request["voice_profile"]), ALLOWED_PROFILE_KEYS)
        self.assertEqual(set(request["permissions"]), PERMISSION_KEYS)
        self.assertFalse(any(request["permissions"].values()))
        self.assertIs(client.last_request, request)

    def test_02_fake_metadata_is_deterministic_and_non_audio(self):
        first = self.h.run(C7AllowlistedFakeLocalHttpClient())
        self.assertEqual(first["fake_response_metadata"]["audio_bytes"], 0)
        self.assertFalse(first["provider_invoked"]); self.assertFalse(first["network_invoked"])
        self.assertFalse(first["audio_file_created"])
        self.assertEqual(list(self.h.c7_root.rglob("*.*")), [])

    def test_03_no_injected_client_fails_closed_and_no_default_exists(self):
        result = self.h.run(None); self.assertEqual(result["state"], C7_BLOCKED)
        parameter = inspect.signature(NarrationProviderAdapter.execute).parameters["client"]
        self.assertIs(parameter.default, inspect.Parameter.empty)

    def test_04_unsafe_and_unknown_clients_rejected_before_method_execution(self):
        labels = ("default", "fallback", "auto_discovery", "live_provider", "network", "subprocess",
                  "unknown", "environment", "config", "credential", "secret", "browser", "mcp",
                  "sdk", "shell", "filesystem_audio", "arbitrary_callable")
        for label in labels:
            class UnsafeClient:
                def __init__(self): self.call_count = 0; self.label = label
                def send_mock(self, request): self.call_count += 1; raise AssertionError("must not execute")
            client = UnsafeClient(); result = self.h.run(client)
            with self.subTest(label=label):
                self.assertEqual(result["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)

    def test_05_spoofed_subclass_or_instance_callable_rejected_before_execution(self):
        class Spoofed(C7AllowlistedFakeLocalHttpClient): pass
        spoofed = Spoofed(); self.assertEqual(self.h.run(spoofed)["state"], C7_BLOCKED); self.assertEqual(spoofed.call_count, 0)
        client = C7AllowlistedFakeLocalHttpClient(); client.send_mock = lambda request: (_ for _ in ()).throw(AssertionError("must not execute"))
        self.assertEqual(self.h.run(client)["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)

    def test_06_no_live_client_fallback_or_transport_code_exists(self):
        source = (AUTOMATION / "providers" / "narration_provider_adapter.py").read_text(encoding="utf-8")
        fake_source = (AUTOMATION / "testing" / "c7_fake_http_client.py").read_text(encoding="utf-8")
        for term in ("import requests", "import httpx", "import urllib", "import socket", "import subprocess", "Popen(", "os.environ", "getenv(", "http://", "https://"):
            self.assertNotIn(term, source); self.assertNotIn(term, fake_source)

    def test_07_changed_writer_editor_or_script_binding_blocks_before_client(self):
        writer = json.loads(WRITER.read_text(encoding="utf-8")); writer["result"]["narration_text"] += " Changed."
        editor = json.loads(EDITOR.read_text(encoding="utf-8")); editor["result"]["redundancy_check"] = "failed"
        for field, path in (("writer", self.h.put("changed_writer.json", writer)), ("editor", self.h.put("changed_editor.json", editor))):
            client = C7AllowlistedFakeLocalHttpClient(); key = "writer_path" if field == "writer" else "editor_path"
            with self.subTest(field=field): self.assertEqual(self.h.run(client, **{key: path})["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)

    def test_08_changed_c5_profile_or_c6_hash_bindings_block(self):
        cases = []
        preflight = json.loads(C5_PREFLIGHT.read_text(encoding="utf-8")); preflight["reason"] = "altered"; cases.append(("c5_preflight_path", self.h.put("changed_preflight.json", preflight)))
        profile = copy.deepcopy(LOCKED_PROFILE); profile["stability"] = 0.71; cases.append(("profile_path", self.h.put("changed_profile.json", profile)))
        auth = json.loads(C6_AUTH.read_text(encoding="utf-8")); auth["locked_profile_hash"] = "0" * 64; cases.append(("c6_authorization_path", self.h.put("changed_auth.json", auth)))
        for field, path in cases:
            client = C7AllowlistedFakeLocalHttpClient()
            with self.subTest(field=field): self.assertEqual(self.h.run(client, **{field: path})["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)

    def test_09_replayed_stale_malformed_or_mismatched_c6_authorization_blocks(self):
        client = C7AllowlistedFakeLocalHttpClient(); self.assertEqual(self.h.run(client)["state"], C7_READY)
        second = C7AllowlistedFakeLocalHttpClient(); self.assertEqual(self.h.run(second)["state"], C7_BLOCKED); self.assertEqual(second.call_count, 0)
        stale = json.loads(C6_AUTH.read_text(encoding="utf-8")); stale["approved_script_hash"] = "0" * 64
        third = C7AllowlistedFakeLocalHttpClient(); self.assertEqual(self.h.run(third, c6_authorization_path=self.h.put("stale_auth.json", stale))["state"], C7_BLOCKED); self.assertEqual(third.call_count, 0)
        malformed = self.h.c6_root / "malformed.json"; malformed.write_text("{")
        fourth = C7AllowlistedFakeLocalHttpClient(); self.assertEqual(self.h.run(fourth, c6_authorization_path=malformed)["state"], C7_BLOCKED); self.assertEqual(fourth.call_count, 0)

    def test_10_every_locked_profile_or_format_deviation_blocks(self):
        changes = {"stability": 0.7, "similarity_boost": 0.7, "style": 0.1, "speed": 1.0,
                   "use_speaker_boost": False, "output_format": "wav"}
        for index, (field, replacement) in enumerate(changes.items(), 1):
            profile = copy.deepcopy(LOCKED_PROFILE); profile[field] = replacement
            client = C7AllowlistedFakeLocalHttpClient()
            with self.subTest(field=field): self.assertEqual(self.h.run(client, profile_path=self.h.put(f"profile_{index}.json", profile))["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)

    def test_11_forbidden_request_fields_block_under_closed_allowlist(self):
        source = json.loads(REQUEST.read_text(encoding="utf-8"))
        fields = ("endpoint", "service_name", "url", "api_key", "token", "authorization_header", "voice_id", "secret", "environment_reference", "config_reference")
        for index, field in enumerate(fields, 1):
            value = copy.deepcopy(source); value["request_id"] = f"C7-FORBIDDEN-{index:04d}"; value[field] = "disallowed"
            client = C7AllowlistedFakeLocalHttpClient()
            with self.subTest(field=field): self.assertEqual(self.h.run(client, request_path=self.h.put(f"forbidden_{index}.json", value))["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)

    def test_12_sanitized_request_contains_only_explicit_safe_fields(self):
        result = self.h.run(C7AllowlistedFakeLocalHttpClient()); request = result["sanitized_request"]
        forbidden = {"endpoint", "provider", "service", "url", "api_key", "token", "authorization", "voice_id", "secret", "credential", "environment", "config"}
        rendered = json.dumps(request).lower()
        for term in forbidden: self.assertNotIn(f'"{term}"', rendered)
        self.assertTrue(request["output_reference"].endswith(".request.json"))
        self.assertNotIn(".mp3", request["output_reference"].lower())

    def test_13_absolute_escape_and_audio_target_fields_block(self):
        source = json.loads(REQUEST.read_text(encoding="utf-8"))
        for index, output in enumerate(("../escape.mp3", r"C:\production\audio.mp3", "proposed/audio.wav"), 1):
            value = copy.deepcopy(source); value["request_id"] = f"C7-PATH-{index:04d}"; value["requested_output_relative_path"] = output
            client = C7AllowlistedFakeLocalHttpClient()
            with self.subTest(output=output): self.assertEqual(self.h.run(client, request_path=self.h.put(f"path_{index}.json", value))["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)
        value = copy.deepcopy(source); value["output_target"] = "audio.mp3"
        client = C7AllowlistedFakeLocalHttpClient(); self.assertEqual(self.h.run(client, request_path=self.h.put("target.json", value))["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)

    def test_14_existing_audio_named_target_is_rejected_without_creating_audio_file(self):
        target = C6_OUTPUT / "proposed" / "synthetic_mia_narration.mp3"
        target.mkdir(parents=True, exist_ok=False)
        try:
            client = C7AllowlistedFakeLocalHttpClient(); result = self.h.run(client)
            self.assertEqual(result["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)
            self.assertTrue(target.is_dir()); self.assertFalse(target.is_file())
        finally:
            target.rmdir()
            if not target.parent.iterdir(): target.parent.rmdir()

    def test_15_c7_output_root_cannot_escape_fixture(self):
        with self.assertRaises(ValueError):
            NarrationProviderAdapter(fixture_root=FIXTURE, c6_state_root=self.h.c6_root, c7_output_root=FIXTURE.parent)

    def test_16_all_later_stage_permissions_remain_false(self):
        result = self.h.run(C7AllowlistedFakeLocalHttpClient())
        self.assertEqual(result["state"], C7_READY)
        self.assertFalse(result["publishing_enabled"]); self.assertFalse(result["real_production_enabled"])
        permissions = result["sanitized_request"]["permissions"]
        for field in ("asset_authorized", "assembly_authorized", "rendering_authorized", "upload_authorized", "scheduling_authorized", "publishing_enabled", "real_production_enabled"):
            self.assertIs(permissions[field], False)

    def test_17_c7_cannot_create_or_validate_c8_authorization(self):
        self.assertTrue(C8_SCHEMA.exists())
        validate_schema_compatibility(json.loads(C8_SCHEMA.read_text(encoding="utf-8")))

        allowed_record_names = {
            "c8_one_time_live_authorization.json",
            "c8_one_time_live_safe_audit.json",
            "c8n_one_time_live_authorization.json",
            "c8n_one_time_live_safe_audit.json",
        }
        allowed_records = tuple(C8_ROOT / name for name in sorted(allowed_record_names))

        def record_metadata(path: Path) -> tuple[int, ...]:
            metadata = path.lstat()
            self.assertTrue(stat.S_ISREG(metadata.st_mode), f"C8 record is not a regular file: {path.name}")
            self.assertEqual(metadata.st_nlink, 1, f"C8 record is hard-linked: {path.name}")
            file_attributes = getattr(metadata, "st_file_attributes", 0)
            self.assertFalse(
                file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                f"C8 record is a reparse point: {path.name}",
            )
            return (
                metadata.st_dev,
                metadata.st_ino,
                metadata.st_mode,
                metadata.st_nlink,
                metadata.st_size,
                metadata.st_mtime_ns,
                metadata.st_ctime_ns,
                file_attributes,
            )

        def unexpected_c8_artifacts() -> list[str]:
            unexpected = []
            for path in C8_ROOT.rglob("*"):
                relative = path.relative_to(C8_ROOT).as_posix()
                lowered_name = path.name.lower()
                lowered_parts = tuple(part.lower() for part in path.relative_to(C8_ROOT).parts)
                if relative in allowed_record_names:
                    continue
                if lowered_name.endswith(".schema.json") or lowered_name.endswith(".contract.json"):
                    continue
                is_json = path.suffix.lower() == ".json"
                is_record_named = "authorization" in lowered_name or "audit" in lowered_name
                is_output_artifact = (
                    any(part in {"output", "outputs", "staging", "disposable_output"}
                        for part in lowered_parts[:-1])
                    and lowered_name != "readme.md"
                )
                is_backup_or_substitute = any(
                    marker in lowered_name
                    for marker in ("backup", "copy", "renamed", "substitute", ".bak", ".old", ".tmp")
                )
                if is_json or is_record_named or is_output_artifact or is_backup_or_substitute:
                    unexpected.append(relative)
            return sorted(unexpected)

        before = {path.name: record_metadata(path) for path in allowed_records}
        self.assertEqual(unexpected_c8_artifacts(), [])
        adapter_source = inspect.getsource(NarrationProviderAdapter).lower()
        for term in ("c8", "live_authorization", "create_authorization", "validate_authorization"):
            self.assertNotIn(term, adapter_source)
        request = json.loads(REQUEST.read_text(encoding="utf-8")); request["c8_authorization"] = {}
        client = C7AllowlistedFakeLocalHttpClient(); self.assertEqual(self.h.run(client, request_path=self.h.put("c8_attempt.json", request))["state"], C7_BLOCKED); self.assertEqual(client.call_count, 0)
        after = {path.name: record_metadata(path) for path in allowed_records}
        self.assertEqual(after, before)
        self.assertEqual(unexpected_c8_artifacts(), [])

    def test_18_no_audio_or_external_execution_artifact_exists(self):
        result = self.h.run(C7AllowlistedFakeLocalHttpClient()); self.assertEqual(result["state"], C7_READY)
        self.assertEqual(list(self.h.c7_root.rglob("*.*")), [])
        self.assertEqual(result["fake_response_metadata"]["audio_bytes"], 0)

    def test_19_c3_state_unchanged_and_no_persistent_c4_consumption(self):
        state = json.loads((LIVE / "chain_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"]); self.assertFalse(state["real_production_enabled"])
        persistent_c4_records = [
            path for path in (FIXTURE / "output").rglob("*.json")
            if "decision_records" in path.parts and "C5-SYNTHETIC-APPROVAL-ONLY-0001" in path.name
        ]
        self.assertEqual(persistent_c4_records, [])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C7NarrationProviderAdapterTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c7_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
