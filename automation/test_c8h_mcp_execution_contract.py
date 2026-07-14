from __future__ import annotations

import copy
import inspect
import json
import unittest
from pathlib import Path

import c8h_mcp_execution_contract as mcp_contract
from c8a_authorization_schema_validator import BLOCKED, InMemoryReplayRegistry, validate_hypothetical_record
from json_schema_subset import validate_schema_compatibility
from test_c8a_authorization_schema import (
    AUTOMATION, CONTRACT_PATH, DISPOSABLE, FUTURE, SCHEMA_PATH,
    binding_values, hypothetical_record, post_attempt_artifacts_are_closed,
)


CHAIN_STATE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace" / "output" / "c3_real_writer_editor_chain" / "chain_state.json"
OPTION_A_GUIDE = AUTOMATION / "C8_OPTION_A_TEMPORARY_ENVIRONMENT_SETUP.md"


class C8hMcpExecutionContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def validate(self, record):
        return validate_hypothetical_record(
            record=record, schema=self.schema, expected_bindings=binding_values(),
            future_c8_root=FUTURE, disposable_output_root=DISPOSABLE,
            replay_registry=InMemoryReplayRegistry(),
        )

    def test_01_active_route_is_exactly_existing_elevenlabs_mcp(self):
        self.assertTrue(mcp_contract.active_route_is_exact(self.contract["active_execution_route"]))
        self.assertEqual(hypothetical_record()["execution_transport"], mcp_contract.EXECUTION_TRANSPORT)

    def test_02_direct_http_runner_option_a_option_b_and_slots_are_inactive(self):
        self.assertTrue(mcp_contract.historical_routes_are_inactive({
            key: self.contract["historical_route_status"][key]
            for key in mcp_contract.HISTORICAL_ROUTES
        }))
        self.assertTrue(self.contract["historical_route_status"]["c8d_through_c8g_artifacts_are_historical_only"])
        self.assertTrue(mcp_contract.authorization_contains_no_inactive_or_sensitive_field(hypothetical_record()))

    def test_03_exactly_one_mcp_operation_and_no_followup_behavior(self):
        changes = {
            "maximum_mcp_operation_count": 2, "maximum_provider_request_count": 2,
            "retry_allowed": True, "redirect_allowed": True, "fallback_allowed": True,
            "alternate_provider_allowed": True, "provider_discovery_allowed": True,
            "batch_mode_allowed": True, "multi_output_allowed": True,
            "status_or_polling_allowed": True, "cleanup_or_delete_allowed": True,
        }
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_04_credential_configuration_environment_voice_and_account_access_fail(self):
        for field in ("credential_access_allowed", "configuration_inspection_allowed",
                      "environment_access_allowed", "voice_identifier_inspection_allowed",
                      "account_data_access_allowed", "other_mcp_tools_allowed"):
            record = hypothetical_record(); record[field] = True
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_05_direct_or_non_elevenlabs_route_and_old_configuration_fields_fail(self):
        record = hypothetical_record(); record["execution_transport"] = "direct_http"
        self.assertEqual(self.validate(record)["state"], BLOCKED)
        for field in mcp_contract.FORBIDDEN_ACTIVE_AUTHORIZATION_FIELDS:
            record = hypothetical_record(); record[field] = "disallowed"
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_06_hash_bindings_format_and_output_path_fail_independently(self):
        for field in ("fixture_text_sha256", "locked_mia_profile_sha256",
                      "c7_provider_request_contract_sha256", "provider_request_allowlist_sha256",
                      "authorized_output_path_sha256", "authorized_output_directory_path_sha256"):
            record = hypothetical_record(); record[field] = "0" * 64
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)
        record = hypothetical_record(); record["output_format"] = "wav"
        self.assertEqual(self.validate(record)["state"], BLOCKED)
        record = hypothetical_record(); record["authorized_output_relative_path"] = "other.mp3"
        self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_07_isolation_c3_and_c4_boundaries_fail_independently(self):
        changes = {
            "test_classification": "real_case", "real_case_content_allowed": True,
            "real_script_approval_used": True, "c4_approval_artifact_allowed": True,
            "c3_fixture_state_must_remain": "SCRIPT_APPROVED_FOR_PREFLIGHT",
        }
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_08_replay_expiry_and_single_use_remain_required(self):
        for field, value in (("single_use", False), ("consumed", True),
                             ("consumption_count", 1), ("authorization_status", "consumed"),
                             ("expires_at_utc", "2026-07-12T15:00:00Z")):
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_09_assets_production_and_later_permissions_fail(self):
        for field in ("asset_authorized", "assembly_authorized", "rendering_authorized",
                      "upload_authorized", "scheduling_authorized", "publishing_enabled",
                      "real_production_enabled"):
            record = hypothetical_record(); record[field] = True
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_10_safe_result_shape_excludes_provider_configuration_and_raw_response(self):
        safe = {key: False for key in mcp_contract.SAFE_RESULT_FIELDS}
        self.assertTrue(mcp_contract.safe_result_shape_is_exact(safe))
        for field in ("api_key", "voice_id", "endpoint", "headers", "raw_response", "account_data"):
            changed = dict(safe); changed[field] = "disallowed"
            with self.subTest(field=field): self.assertFalse(mcp_contract.safe_result_shape_is_exact(changed))

    def test_11_module_is_declarative_and_invokes_no_mcp_network_or_external_tool(self):
        source = inspect.getsource(mcp_contract).lower()
        for term in ("import requests", "import httpx", "import urllib", "import socket",
                     "import subprocess", "os.environ", "getenv(", "mcp__", "tool_search",
                     "http://", "https://", "write_bytes", "open("):
            with self.subTest(term=term): self.assertNotIn(term, source)

    def test_12_active_schema_is_strict_and_nonexecuting_in_c8h(self):
        validate_schema_compatibility(self.schema)
        self.assertTrue(self.contract["schema_only"])
        self.assertFalse(self.contract["creation_permitted_in_c8h"])
        self.assertFalse(self.contract["execution_permitted_in_c8h"])

    def test_13_option_a_guide_is_historical_and_no_values_were_used(self):
        guide = OPTION_A_GUIDE.read_text(encoding="utf-8")
        self.assertIn("NOT USED FOR CURRENT C8 MCP ROUTE", guide)
        self.assertIn("No values were ever entered or accessed", guide)

    def test_14_c3_remains_awaiting_and_no_c4_dependency_is_permitted(self):
        state = json.loads(CHAIN_STATE.read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"])
        self.assertNotIn("c4_script_approval_sha256", self.schema["properties"])

    def test_15_no_authorization_instance_audio_or_media_exists(self):
        self.assertTrue(post_attempt_artifacts_are_closed())
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])

    def test_16_contract_retains_exact_profile_format_and_output_binding(self):
        record = hypothetical_record()
        self.assertEqual(record["output_format"], "mp3_44100_128")
        self.assertEqual(record["operation_scope"], mcp_contract.OPERATION_SCOPE)
        self.assertEqual(record["authorized_output_relative_path"], binding_values()["authorized_output_relative_path"])
        self.assertEqual(record["authorized_output_directory_relative_path"], binding_values()["authorized_output_directory_relative_path"])
        self.assertEqual(self.contract["locked_mia_profile"]["voice_profile_name"], "Mia")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8hMcpExecutionContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "c8h_offline_tests": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "real_invocation": "not_requested",
        "mcp_invocation": "not_performed",
        "configuration_access": "not_performed",
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
