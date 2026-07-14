from __future__ import annotations

import inspect
import json
import unittest

import c8i_mcp_output_finalization_contract as finalization
from c8a_authorization_schema_validator import BLOCKED, PASSED, InMemoryReplayRegistry, validate_hypothetical_record
from json_schema_subset import validate_schema_compatibility
from test_c8a_authorization_schema import (
    AUTOMATION, CONTRACT_PATH, DISPOSABLE, FUTURE, SCHEMA_PATH, STAGING_PATH,
    binding_values, hypothetical_record, post_attempt_artifacts_are_closed,
)


CHAIN_STATE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace" / "output" / "c3_real_writer_editor_chain" / "chain_state.json"


def entry(name="generated.mp3", **changes):
    value = {
        "name": name, "entry_type": "regular_file", "direct_child": True,
        "newly_created": True, "is_link": False,
    }
    value.update(changes)
    return value


class C8iMcpOutputFinalizationContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def validate(self, record):
        return validate_hypothetical_record(
            record=record, schema=self.schema, expected_bindings=binding_values(),
            future_c8_root=FUTURE, disposable_output_root=DISPOSABLE,
            replay_registry=InMemoryReplayRegistry(),
        )

    def test_01_c8i_staging_contract_is_historical_and_inactive(self):
        boundary = self.contract["historical_c8i_staging_finalization_boundary"]
        self.assertTrue(boundary["historical_inactive"])
        self.assertFalse(boundary["mcp_output_filename_parameter_supported"])
        self.assertTrue(boundary["mcp_output_directory_required"])
        self.assertNotIn("authorized_staging_directory_relative_path", hypothetical_record())
        self.assertTrue(finalization.path_bindings_are_exact(
            staging_directory=STAGING_PATH,
            final_output=binding_values()["authorized_output_relative_path"],
        ))

    def test_02_one_mcp_operation_and_one_local_rename_only(self):
        record = hypothetical_record()
        self.assertEqual(record["maximum_mcp_operation_count"], 1)
        self.assertEqual(record["maximum_provider_request_count"], 1)
        self.assertEqual(record["maximum_local_rename_count"], 1)
        self.assertTrue(record["local_finalization_action_allowed"])
        self.assertTrue(finalization.finalization_boundary_is_exact(finalization.FINALIZATION_BOUNDARY))

    def test_03_final_destination_and_rename_plan_are_exact(self):
        plan = finalization.exact_rename_plan("generated.mp3")
        self.assertEqual(plan["destination_relative_path"], finalization.FINAL_OUTPUT)
        self.assertEqual(plan["source_relative_path"], f"{finalization.STAGING_DIRECTORY}/generated.mp3")
        self.assertEqual(plan["rename_count"], 1)
        self.assertTrue(plan["atomic_same_filesystem"])
        self.assertFalse(plan["overwrite"])
        self.assertFalse(finalization.path_bindings_are_exact(staging_directory=STAGING_PATH, final_output="other.mp3"))

    def test_04_staging_path_mutations_fail_closed(self):
        for path in ("../mcp_staging", "*/mcp_staging", r"C:\outside\mcp_staging",
                     f"{STAGING_PATH}/nested", f"{STAGING_PATH}.mp3", "other/mcp_staging"):
            record = hypothetical_record(); record["authorized_staging_directory_relative_path"] = path
            with self.subTest(path=path): self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_05_zero_multiple_nonmp3_link_directory_and_nested_entries_block(self):
        cases = (
            ([], finalization.BLOCKED_EMPTY),
            ([entry(), entry("second.mp3")], finalization.BLOCKED_MULTIPLE),
            ([entry("generated.wav")], finalization.BLOCKED_ENTRY),
            ([entry("nested/generated.mp3")], finalization.BLOCKED_ENTRY),
            ([entry("../generated.mp3")], finalization.BLOCKED_ENTRY),
            ([entry("*.mp3")], finalization.BLOCKED_ENTRY),
            ([entry(is_link=True)], finalization.BLOCKED_ENTRY),
            ([entry(entry_type="directory")], finalization.BLOCKED_ENTRY),
            ([entry(direct_child=False)], finalization.BLOCKED_ENTRY),
            ([entry(newly_created=False)], finalization.BLOCKED_ENTRY),
        )
        for entries, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(finalization.evaluate_staging_snapshot(entries, destination_exists=False), expected)

    def test_06_destination_exists_and_rename_failure_stop_without_retry(self):
        self.assertEqual(finalization.evaluate_staging_snapshot([entry()], destination_exists=True), finalization.BLOCKED_DESTINATION)
        self.assertEqual(finalization.evaluate_staging_snapshot([entry()], destination_exists=False, rename_failed=True), finalization.BLOCKED_RENAME_FAILURE)
        record = hypothetical_record()
        for field in ("retry_allowed", "rename_retry_allowed", "overwrite_allowed", "copy_allowed",
                      "second_rename_allowed", "post_rename_cleanup_allowed", "cleanup_or_delete_allowed"):
            self.assertFalse(record[field])

    def test_07_no_audio_processing_or_later_stage_behavior_is_permitted(self):
        record = hypothetical_record()
        for field in ("audio_processing_allowed", "asset_authorized", "assembly_authorized",
                      "rendering_authorized", "upload_authorized", "scheduling_authorized",
                      "publishing_enabled", "real_production_enabled"):
            self.assertFalse(record[field])

    def test_08_contract_module_invokes_no_mcp_network_shell_or_external_command(self):
        source = inspect.getsource(finalization).lower()
        for term in ("mcp__", "tool_search", "import requests", "import httpx", "import urllib",
                     "import socket", "import subprocess", "os.system", "shell=true", "http://", "https://"):
            with self.subTest(term=term): self.assertNotIn(term, source)

    def test_09_no_configuration_credential_environment_or_provider_access_exists(self):
        source = inspect.getsource(finalization).lower()
        for term in ("os.environ", "getenv(", "api_key", "voice_id", "endpoint", "account_data",
                     "private_config", "login_state"):
            with self.subTest(term=term): self.assertNotIn(term, source)
        record = hypothetical_record()
        for field in ("credential_access_allowed", "configuration_inspection_allowed",
                      "environment_access_allowed", "voice_identifier_inspection_allowed",
                      "account_data_access_allowed"):
            self.assertFalse(record[field])

    def test_10_output_directory_and_final_hashes_are_required_and_fail_independently(self):
        for field in ("authorized_output_directory_path_sha256", "authorized_output_path_sha256"):
            record = hypothetical_record(); record[field] = "0" * 64
            with self.subTest(field=field): self.assertEqual(self.validate(record)["state"], BLOCKED)
        self.assertIn("authorized_output_directory_path_sha256", self.contract["required_immutable_bindings"])

    def test_11_single_use_replay_and_fifteen_minute_limit_remain_required(self):
        record = hypothetical_record()
        self.assertTrue(record["single_use"]); self.assertFalse(record["consumed"])
        self.assertEqual(record["consumption_count"], 0)
        record["expires_at_utc"] = "2026-07-12T15:00:00Z"
        self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_12_c3_c4_and_real_case_boundaries_remain_closed(self):
        state = json.loads(CHAIN_STATE.read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"])
        record = hypothetical_record()
        self.assertFalse(record["real_case_content_allowed"])
        self.assertFalse(record["real_script_approval_used"])
        self.assertFalse(record["c4_approval_artifact_allowed"])

    def test_13_no_authorization_instance_audio_or_media_exists(self):
        self.assertTrue(post_attempt_artifacts_are_closed())
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])

    def test_14_safe_audit_shape_is_closed_and_contains_no_raw_provider_data(self):
        safe = {field: False for field in finalization.SAFE_AUDIT_FIELDS}
        self.assertTrue(finalization.safe_audit_shape_is_exact(safe))
        for field in ("raw_response", "credential", "voice_id", "endpoint", "account_data"):
            changed = dict(safe); changed[field] = "disallowed"
            self.assertFalse(finalization.safe_audit_shape_is_exact(changed))

    def test_15_schema_is_strict_and_c8i_is_nonexecuting(self):
        validate_schema_compatibility(self.schema)
        self.assertFalse(self.contract["creation_permitted_in_c8i"])
        self.assertFalse(self.contract["execution_permitted_in_c8i"])
        self.assertTrue(self.contract["schema_only"])

    def test_16_no_generic_filesystem_operation_api_or_mutation_exists(self):
        source = inspect.getsource(finalization)
        for term in (".rename(", ".replace(", "shutil", "copyfile", "unlink(", "rmdir(", "write_bytes", "open("):
            with self.subTest(term=term): self.assertNotIn(term, source)
        self.assertEqual(finalization.evaluate_staging_snapshot([entry()], destination_exists=False), finalization.READY)

    def test_17_live_authorization_uses_only_canonical_rename_count_field(self):
        record = hypothetical_record()
        self.assertEqual(record["maximum_local_rename_count"], 1)
        self.assertEqual(self.validate(record)["state"], PASSED)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(self.schema["properties"]["maximum_local_rename_count"]["enum"], [1])
        self.assertNotIn("maximum_local_finalization_rename_count", self.schema["properties"])
        incorrect = hypothetical_record()
        incorrect["maximum_local_finalization_rename_count"] = incorrect.pop("maximum_local_rename_count")
        self.assertEqual(self.validate(incorrect)["state"], BLOCKED)
        missing = hypothetical_record(); missing.pop("maximum_local_rename_count")
        self.assertEqual(self.validate(missing)["state"], BLOCKED)
        wrong = hypothetical_record(); wrong["maximum_local_rename_count"] = 0
        self.assertEqual(self.validate(wrong)["state"], BLOCKED)
        self.assertEqual(self.contract["active_result_shape_finalization_boundary"]["maximum_local_rename_count"], 1)
        self.assertEqual(self.contract["one_attempt_rules"]["maximum_local_rename_count"], 1)
        self.assertTrue(post_attempt_artifacts_are_closed())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8iMcpOutputFinalizationContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "c8i_offline_tests": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "mcp_invocation": "not_performed",
        "authorization_artifact": "not_created",
        "audio_or_media_creation": "not_performed",
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
