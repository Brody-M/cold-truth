from __future__ import annotations

import copy
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from c8a_authorization_schema_validator import text_sha256
from providers.c8_isolated_provider_execution_adapter import (
    ALLOWED_PROFILE_FIELDS, ALLOWED_REQUEST_FIELDS, BLOCKED, ISOLATION_FIELDS,
    PERMISSION_FIELDS, READY, C8IsolatedProviderExecutionAdapter
)
from test_c8a_authorization_schema import (
    CONTRACT_PATH, DISPOSABLE, FIXTURE_TEXT, FUTURE, OUTPUT_PATH, PROFILE,
    SCHEMA_PATH, hypothetical_record, post_attempt_artifacts_are_closed
)
from testing.c8c_fake_client import C8cAllowlistedFakeClient

_DEFAULT_CLIENT = object()
C8C_TEST_TEMP_ROOT = FUTURE.parent / "output"


class Harness:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(dir=C8C_TEST_TEMP_ROOT)
        self.root = Path(self.temp.name)
        self.adapter = C8IsolatedProviderExecutionAdapter(
            future_c8_root=FUTURE, disposable_output_root=DISPOSABLE,
            schema_path=SCHEMA_PATH, contract_path=CONTRACT_PATH,
            locked_profile_path=PROFILE
        )
        self.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def close(self): self.temp.cleanup()

    def run(self, *, record=None, text=FIXTURE_TEXT, profile=None,
            output=OUTPUT_PATH, client=_DEFAULT_CLIENT):
        return self.adapter.validate_and_inspect(
            authorization_record=record or hypothetical_record(), fixture_text=text,
            locked_profile=self.profile if profile is None else profile,
            output_relative_path=output,
            client=C8cAllowlistedFakeClient() if client is _DEFAULT_CLIENT else client
        )


class C8cIsolatedExecutionAdapterTests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def tearDown(self):
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])
        self.h.close()

    def test_01_complete_hypothetical_record_builds_only_sanitized_memory_request(self):
        client = C8cAllowlistedFakeClient(); result = self.h.run(client=client)
        self.assertEqual(result["state"], READY); self.assertEqual(client.call_count, 1)
        request = result["sanitized_request"]
        self.assertEqual(set(request), ALLOWED_REQUEST_FIELDS)
        self.assertEqual(set(request["voice_profile"]), ALLOWED_PROFILE_FIELDS)
        self.assertEqual(set(request["isolation"]), ISOLATION_FIELDS)
        self.assertEqual(set(request["permissions"]), PERMISSION_FIELDS)
        self.assertIs(client.last_request, request)

    def test_02_execution_is_always_false_and_metadata_is_zero_audio(self):
        result = self.h.run()
        for field in ("execution_authorized", "external_call_made", "provider_invoked",
                      "network_invoked", "audio_file_created", "authorization_artifact_created",
                      "authorization_record_consumed", "publishing_enabled", "real_production_enabled"):
            self.assertIs(result[field], False)
        self.assertEqual(result["fake_metadata"]["audio_bytes"], 0)
        self.assertFalse(result["sanitized_request"]["permissions"]["execution_authorized"])

    def test_03_adapter_has_no_c4_c5_c6_or_c7_runtime_import_or_call(self):
        source = inspect.getsource(C8IsolatedProviderExecutionAdapter).lower()
        for term in ("from c4", "import c4", "from c5", "import c5", "from c6", "import c6",
                     "narrationprovideradapter", "validate_synthetic_narration", "agent_runner"):
            self.assertNotIn(term, source)
        self.assertNotIn("fallback", source.replace('"fallback_allowed"', ""))

    def test_04_each_core_hash_binding_fails_independently_before_client(self):
        fields = ("fixture_text_sha256", "locked_mia_profile_sha256",
                  "c7_provider_request_contract_sha256", "provider_request_allowlist_sha256",
                  "authorized_output_path_sha256")
        for field in fields:
            record = hypothetical_record(); record[field] = "0" * 64
            client = C8cAllowlistedFakeClient(); result = self.h.run(record=record, client=client)
            with self.subTest(field=field): self.assertEqual(result["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_05_text_profile_output_reference_and_format_deviations_block(self):
        client = C8cAllowlistedFakeClient(); self.assertEqual(self.h.run(text=FIXTURE_TEXT + " changed", client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)
        profile = copy.deepcopy(self.h.profile); profile["speed"] = 1.0
        client = C8cAllowlistedFakeClient(); self.assertEqual(self.h.run(profile=profile, client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)
        client = C8cAllowlistedFakeClient(); self.assertEqual(self.h.run(output="attempt-0002/other.mp3", client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)
        record = hypothetical_record(); record["output_format"] = "wav"
        client = C8cAllowlistedFakeClient(); self.assertEqual(self.h.run(record=record, client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_06_isolation_constants_fail_independently(self):
        changes = {"test_classification": "real_workflow", "real_case_content_allowed": True,
                   "real_script_approval_used": True, "c4_approval_artifact_allowed": True,
                   "c3_fixture_state_must_remain": "SCRIPT_APPROVED_FOR_PREFLIGHT",
                   "fixture_id": "real-case"}
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value; client = C8cAllowlistedFakeClient()
            with self.subTest(field=field): self.assertEqual(self.h.run(record=record, client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_07_authorization_id_expiry_status_and_consumed_state_block(self):
        changes = {"authorization_id": "invalid", "expires_at_utc": "2026-07-12T15:00:00Z",
                   "authorization_status": "consumed", "consumed": True,
                   "consumption_count": 1, "single_use": False}
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value; client = C8cAllowlistedFakeClient()
            with self.subTest(field=field): self.assertEqual(self.h.run(record=record, client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_08_c3_c4_c5_c6_and_real_workflow_references_block(self):
        fields = ("case_id", "real_case_text", "production_script_reference", "existing_media_reference",
                  "c3_approval_state_override", "c4_approval_artifact", "c4_script_approval_sha256",
                  "c5_passed_preflight_result_sha256", "c6_synthetic_authorization_sha256",
                  "writer_handoff", "editor_handoff")
        for field in fields:
            record = hypothetical_record(); record[field] = "disallowed"; client = C8cAllowlistedFakeClient()
            with self.subTest(field=field): self.assertEqual(self.h.run(record=record, client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_09_all_one_attempt_and_later_permission_deviations_block(self):
        changes = {"retry_allowed": True, "maximum_provider_request_count": 2,
                   "redirects_allowed": True, "fallback_allowed": True,
                   "alternate_provider_allowed": True, "batch_allowed": True,
                   "multi_output_allowed": True, "authorized_output_count": 2,
                   "asset_authorized": True, "assembly_authorized": True,
                   "rendering_authorized": True, "upload_authorized": True,
                   "scheduling_authorized": True, "publishing_enabled": True,
                   "real_production_enabled": True}
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value; client = C8cAllowlistedFakeClient()
            with self.subTest(field=field): self.assertEqual(self.h.run(record=record, client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_10_absolute_escape_external_existing_and_nonmp3_outputs_block(self):
        for output in ("../escape.mp3", r"C:\outside\audio.mp3", "/outside/audio.mp3", "attempt/audio.wav"):
            client = C8cAllowlistedFakeClient()
            with self.subTest(output=output): self.assertEqual(self.h.run(output=output, client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)
        target = DISPOSABLE / "c8_isolated_synthetic_connectivity.mp3"; target.mkdir(parents=True)
        try:
            client = C8cAllowlistedFakeClient(); self.assertEqual(self.h.run(client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)
            self.assertTrue(target.is_dir()); self.assertFalse(target.is_file())
        finally:
            target.rmdir()

    def test_11_missing_unknown_and_unsafe_clients_fail_before_method(self):
        self.assertEqual(self.h.run(client=None)["state"], BLOCKED)
        labels = ("network", "provider", "subprocess", "environment", "config", "secret",
                  "browser", "mcp", "sdk", "shell", "filesystem_audio", "arbitrary",
                  "default", "fallback", "wrapped", "unknown")
        for label in labels:
            class Unsafe:
                def __init__(self): self.call_count = 0; self.label = label
                def inspect_request(self, request): self.call_count += 1; raise AssertionError("must not run")
            client = Unsafe(); result = self.h.run(client=client)
            with self.subTest(label=label): self.assertEqual(result["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_12_subclass_and_altered_method_clients_fail_before_execution(self):
        class Subclass(C8cAllowlistedFakeClient): pass
        client = Subclass(); self.assertEqual(self.h.run(client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)
        client = C8cAllowlistedFakeClient(); client.inspect_request = lambda request: (_ for _ in ()).throw(AssertionError("must not run"))
        self.assertEqual(self.h.run(client=client)["state"], BLOCKED); self.assertEqual(client.call_count, 0)

    def test_13_no_default_client_and_no_external_runtime_facility(self):
        parameter = inspect.signature(C8IsolatedProviderExecutionAdapter.validate_and_inspect).parameters["client"]
        self.assertIs(parameter.default, inspect.Parameter.empty)
        source = (Path(__file__).parent / "providers" / "c8_isolated_provider_execution_adapter.py").read_text(encoding="utf-8")
        fake = (Path(__file__).parent / "testing" / "c8c_fake_client.py").read_text(encoding="utf-8")
        for term in ("import requests", "import httpx", "import urllib", "import socket", "import subprocess", "os.environ", "getenv(", "http://", "https://", "write_bytes", "write_text", "open("):
            self.assertNotIn(term, source); self.assertNotIn(term, fake)

    def test_14_authorization_record_is_not_mutated_consumed_or_persisted(self):
        record = hypothetical_record(); before = json.dumps(record, sort_keys=True)
        result = self.h.run(record=record)
        self.assertEqual(result["state"], READY); self.assertEqual(json.dumps(record, sort_keys=True), before)
        self.assertFalse(result["authorization_artifact_created"]); self.assertFalse(result["authorization_record_consumed"])
        self.assertTrue(post_attempt_artifacts_are_closed())

    def test_15_replay_blocks_in_memory_without_marking_artifact_consumed(self):
        record = hypothetical_record(); self.assertEqual(self.h.run(record=record)["state"], READY)
        client = C8cAllowlistedFakeClient(); second = self.h.run(record=record, client=client)
        self.assertEqual(second["state"], BLOCKED); self.assertEqual(client.call_count, 0)
        self.assertFalse(record["consumed"]); self.assertEqual(record["consumption_count"], 0)

    def test_16_no_audio_binary_or_media_file_is_created(self):
        result = self.h.run(); self.assertEqual(result["state"], READY)
        self.assertEqual(result["fake_metadata"]["audio_bytes"], 0)
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8cIsolatedExecutionAdapterTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c8c_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
