from __future__ import annotations

import copy
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from c8a_authorization_schema_validator import BLOCKED, PASSED, InMemoryReplayRegistry, text_sha256, validate_hypothetical_record
from json_schema_subset import validate_schema_compatibility
from providers.narration_provider_adapter import NarrationProviderAdapter
from test_c8a_authorization_schema import (
    AUTOMATION, CONTRACT_PATH, DISPOSABLE, FIXTURE, FUTURE, OUTPUT_PATH,
    SCHEMA_PATH, binding_values, hypothetical_record, post_attempt_artifacts_are_closed,
)

LIVE = FIXTURE / "output" / "c3_real_writer_editor_chain"
C8B_TEST_TEMP_ROOT = FIXTURE / "narration_preflight" / "output"


class C8bContractAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=C8B_TEST_TEMP_ROOT)
        self.root = DISPOSABLE
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def tearDown(self):
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])
        self.temp.cleanup()

    def run_record(self, record=None, expected=None, registry=None):
        return validate_hypothetical_record(
            record=record or hypothetical_record(), schema=self.schema,
            expected_bindings=expected or binding_values(), future_c8_root=FUTURE,
            disposable_output_root=self.root,
            replay_registry=registry or InMemoryReplayRegistry(),
        )

    def test_01_shape_validates_only_as_isolated_connectivity_test(self):
        result = self.run_record(); self.assertEqual(result["state"], PASSED)
        record = hypothetical_record()
        self.assertEqual(record["test_classification"], "isolated_synthetic_provider_connectivity_test")
        self.assertFalse(record["real_case_content_allowed"]); self.assertFalse(record["real_script_approval_used"])
        self.assertFalse(record["c4_approval_artifact_allowed"]); self.assertFalse(result["execution_authorized"])

    def test_02_c4_c3_writer_editor_and_real_workflow_fields_are_rejected(self):
        fields = ("c4_script_approval_sha256", "c4_approval_artifact", "c3_approval_state_override",
                  "writer_handoff", "editor_handoff", "case_id", "real_case_text",
                  "production_script_reference", "c5_passed_preflight_result_sha256",
                  "c6_synthetic_authorization_sha256")
        for field in fields:
            record = hypothetical_record(); record[field] = "disallowed"
            with self.subTest(field=field): self.assertEqual(self.run_record(record)["state"], BLOCKED)

    def test_03_isolation_constants_are_exact_and_fail_independently(self):
        changes = {
            "test_classification": "real_workflow_narration",
            "real_case_content_allowed": True,
            "real_script_approval_used": True,
            "c4_approval_artifact_allowed": True,
            "c3_fixture_state_must_remain": "SCRIPT_APPROVED_FOR_PREFLIGHT",
            "fixture_id": "real-case",
        }
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field): self.assertEqual(self.run_record(record)["state"], BLOCKED)

    def test_04_c3_remains_exactly_awaiting_script_approval(self):
        state = json.loads((LIVE / "chain_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"]); self.assertFalse(state["real_production_enabled"])
        self.assertEqual(hypothetical_record()["c3_fixture_state_must_remain"], state["state"])

    def test_05_c8b_has_no_c4_create_consume_modify_or_validate_route(self):
        helper = (AUTOMATION / "c8a_authorization_schema_validator.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("from c4", helper); self.assertNotIn("import c4", helper)
        for term in ("create_c4", "consume_c4", "modify_c4", "validate_c4"):
            self.assertNotIn(term, helper)
        self.assertNotIn("c4_script_approval_sha256", self.schema["properties"])

    def test_06_retained_hashes_and_path_binding_fail_independently(self):
        fields = ("fixture_text_sha256", "locked_mia_profile_sha256",
                  "c7_provider_request_contract_sha256", "provider_request_allowlist_sha256",
                  "authorized_output_path_sha256", "authorized_output_directory_path_sha256",
                  "allowed_runtime_result_shapes")
        for field in fields:
            record = hypothetical_record()
            record[field] = ["mcp_audio_resource"] if field == "allowed_runtime_result_shapes" else "0" * 64
            with self.subTest(field=field): self.assertEqual(self.run_record(record)["state"], BLOCKED)
        record = hypothetical_record(); record["authorized_output_relative_path"] = "attempt-0002/other.mp3"; record["authorized_output_path_sha256"] = text_sha256(record["authorized_output_relative_path"])
        self.assertEqual(self.run_record(record)["state"], BLOCKED)

    def test_07_format_one_attempt_and_later_permissions_fail_closed(self):
        changes = {"output_format": "wav", "retry_allowed": True,
                   "maximum_mcp_operation_count": 2, "maximum_provider_request_count": 2,
                   "authorized_output_count": 2, "redirect_allowed": True,
                   "fallback_allowed": True, "alternate_provider_allowed": True,
                   "provider_discovery_allowed": True, "batch_mode_allowed": True,
                   "multi_output_allowed": True, "status_or_polling_allowed": True,
                   "cleanup_or_delete_allowed": True, "asset_authorized": True,
                   "assembly_authorized": True, "rendering_authorized": True,
                   "upload_authorized": True, "scheduling_authorized": True,
                   "publishing_enabled": True, "real_production_enabled": True}
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field): self.assertEqual(self.run_record(record)["state"], BLOCKED)

    def test_08_contract_explicitly_retains_and_removes_correct_dependencies(self):
        retained = self.contract["dependencies_retained"]
        for field in ("exact_synthetic_fixture_text_hash", "locked_mia_profile_hash",
                      "c7_provider_request_contract_hash", "c7_provider_request_allowlist_hash",
                      "contained_output_path_and_hash", "contained_output_directory_path_and_hash",
                      "runtime_result_shape_allowlist_binding", "one_exact_result_finalization_action",
                      "one_attempt_restrictions"):
            self.assertIs(retained[field], True)
        removed = self.contract["dependencies_removed"]
        for field in ("c3_writer_editor_permission_state", "c4_script_approval_hash",
                      "c5_preflight_result_hash", "c6_synthetic_authorization_hash",
                      "c7_runtime_execute_path"):
            self.assertIn(field, removed)
        self.assertTrue(self.contract["real_workflow_c4_gate_unchanged"])

    def test_09_schema_contains_no_transitive_c4_c5_c6_or_case_dependency(self):
        properties = set(self.schema["properties"])
        forbidden = {"case_id", "c4_script_approval_sha256", "c5_passed_preflight_result_sha256", "c6_synthetic_authorization_sha256", "writer_handoff", "editor_handoff"}
        self.assertTrue(properties.isdisjoint(forbidden))
        self.assertTrue(set(self.schema["required"]).isdisjoint(forbidden))

    def test_10_no_valid_authorization_instance_or_execution_object_exists(self):
        self.assertTrue(post_attempt_artifacts_are_closed())
        result = self.run_record()
        for field in ("authorization_artifact_created", "execution_authorized", "provider_invoked", "network_invoked", "audio_file_created"):
            self.assertIs(result[field], False)

    def test_11_no_live_provider_secret_config_or_audio_route_exists(self):
        helper = (AUTOMATION / "c8a_authorization_schema_validator.py").read_text(encoding="utf-8")
        for term in ("import requests", "import httpx", "import urllib", "import socket", "import subprocess", "os.environ", "getenv(", "write_bytes", "write_text", "open(", "http://", "https://"):
            self.assertNotIn(term, helper)
        adapter = inspect.getsource(NarrationProviderAdapter).lower()
        for term in ("c8", "live_client", "create_authorization", "validate_authorization"):
            self.assertNotIn(term, adapter)

    def test_12_schema_is_strict_and_contract_is_nonexecuting(self):
        validate_schema_compatibility(self.schema)
        self.assertTrue(self.contract["schema_only"]); self.assertFalse(self.contract["provider_neutral"])
        self.assertEqual(self.contract["active_execution_route"]["execution_transport"], "existing_configured_elevenlabs_mcp")
        for field in ("creation_permitted_in_c7", "validation_permitted_in_c7", "consumption_permitted_in_c7", "execution_permitted_in_c7", "creation_permitted_in_c8a", "execution_permitted_in_c8a", "creation_permitted_in_c8b", "execution_permitted_in_c8b"):
            self.assertIs(self.contract[field], False)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8bContractAlignmentTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c8b_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
