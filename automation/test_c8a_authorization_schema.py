from __future__ import annotations

import copy
import hashlib
import inspect
import json
import stat
import tempfile
import unittest
from pathlib import Path
from typing import Any

from c8a_authorization_schema_validator import (
    BLOCKED, PASSED, InMemoryReplayRegistry, canonical_sha256, text_sha256,
    validate_hypothetical_record,
)
from handoff_validator import file_sha256
from json_schema_subset import validate_schema_compatibility
from providers.narration_provider_adapter import NarrationProviderAdapter


AUTOMATION = Path(__file__).resolve().parent
FIXTURE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace"
C5 = FIXTURE / "narration_preflight"
C8A_TEST_TEMP_ROOT = C5 / "output"
FUTURE = C5 / "future_c8"
DISPOSABLE = FUTURE / "disposable_output"
SCHEMA_PATH = FUTURE / "one_time_live_synthetic_provider_authorization.schema.json"
CONTRACT_PATH = FUTURE / "one_time_live_synthetic_provider_authorization.contract.json"
PROFILE = C5 / "synthetic_locked_narration_profile.json"
FIXTURE_TEXT = "This is a controlled synthetic narration test. It contains no real case details and is used only to validate the Cold Truth narration-provider connection."
OUTPUT_PATH = "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output/c8_isolated_synthetic_connectivity.mp3"
STAGING_PATH = "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output/mcp_staging"
OUTPUT_DIRECTORY_PATH = "fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output"
POST_ATTEMPT_ARTIFACT_NAMES = {
    "c8_one_time_live_authorization.json",
    "c8_one_time_live_safe_audit.json",
    "c8n_one_time_live_authorization.json",
    "c8n_one_time_live_safe_audit.json",
}


def historical_record_metadata_snapshot() -> dict[str, tuple[int, ...]] | None:
    snapshot = {}
    for name in sorted(POST_ATTEMPT_ARTIFACT_NAMES):
        try:
            metadata = (FUTURE / name).lstat()
        except OSError:
            return None
        file_attributes = getattr(metadata, "st_file_attributes", 0)
        if not stat.S_ISREG(metadata.st_mode):
            return None
        if metadata.st_nlink != 1:
            return None
        if file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            return None
        snapshot[name] = (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_nlink,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
            file_attributes,
        )
    return snapshot


def unexpected_historical_artifacts() -> list[str]:
    unexpected = []
    for path in FUTURE.rglob("*"):
        relative = path.relative_to(FUTURE).as_posix()
        lowered_name = path.name.lower()
        lowered_parts = tuple(part.lower() for part in path.relative_to(FUTURE).parts)
        if relative in POST_ATTEMPT_ARTIFACT_NAMES:
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
        is_media = path.suffix.lower() in {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac"}
        is_backup_or_substitute = any(
            marker in lowered_name
            for marker in ("backup", "copy", "renamed", "substitute", ".bak", ".old", ".tmp")
        )
        if is_json or is_record_named or is_output_artifact or is_media or is_backup_or_substitute:
            unexpected.append(relative)
    return sorted(unexpected)


def post_attempt_artifacts_are_closed() -> bool:
    return historical_record_metadata_snapshot() is not None and not unexpected_historical_artifacts()


def binding_values() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return {
        "fixture_text_sha256": text_sha256(FIXTURE_TEXT),
        "locked_mia_profile_sha256": file_sha256(PROFILE),
        "c7_provider_request_contract_sha256": canonical_sha256(contract["c7_provider_request_contract"]),
        "provider_request_allowlist_sha256": canonical_sha256(contract["c7_sanitized_request_allowlist"]),
        "authorized_output_relative_path": OUTPUT_PATH,
        "authorized_output_path_sha256": text_sha256(OUTPUT_PATH),
        "authorized_output_directory_relative_path": OUTPUT_DIRECTORY_PATH,
        "authorized_output_directory_path_sha256": text_sha256(OUTPUT_DIRECTORY_PATH),
        "allowed_runtime_result_shapes": [
            "returned_contained_local_mp3_path",
            "mcp_audio_resource",
        ],
    }


def hypothetical_record() -> dict:
    return {
        "schema_version": "1.0", "authorization_phase": "C8",
        "authorization_id": "C8-HYPOTHETICAL-AUTH-0001",
        "fixture_id": "c8-isolated-connectivity-fixture",
        "test_classification": "isolated_synthetic_provider_connectivity_test",
        "real_case_content_allowed": False,
        "real_script_approval_used": False,
        "c4_approval_artifact_allowed": False,
        "c3_fixture_state_must_remain": "AWAITING_SCRIPT_APPROVAL",
        "decision": "authorize_one_existing_elevenlabs_mcp_operation",
        "reviewer_role": "human_owner",
        "issued_at_utc": "2026-07-12T14:00:00Z",
        "expires_at_utc": "2026-07-12T14:10:00Z",
        "authorization_status": "issued_unconsumed", "consumed": False,
        "consumption_count": 0, "single_use": True,
        "execution_transport": "existing_configured_elevenlabs_mcp",
        "mcp_operation_allowed": True,
        "maximum_mcp_operation_count": 1,
        "other_mcp_tools_allowed": False,
        "direct_http_transport_allowed": False,
        "option_a_environment_injection_allowed": False,
        "option_b_private_config_allowed": False,
        "direct_exact_filename_input_supported": False,
        "allowed_runtime_result_shapes": [
            "returned_contained_local_mp3_path",
            "mcp_audio_resource",
        ],
        "result_shape_must_be_single": True,
        "local_finalization_action_allowed": True,
        "maximum_local_rename_count": 1,
        "maximum_resource_materialization_write_count": 1,
        "atomic_same_filesystem_rename_required": True,
        "exclusive_create_required": True,
        "destination_must_be_absent": True,
        "overwrite_allowed": False,
        "copy_allowed": False,
        "second_rename_allowed": False,
        "rename_retry_allowed": False,
        "remote_reference_allowed": False,
        "attachment_download_reference_allowed": False,
        "metadata_only_success_allowed": False,
        "mixed_result_shapes_allowed": False,
        "resource_url_fetch_allowed": False,
        "resource_content_inspection_allowed": False,
        "resource_content_retention_allowed": False,
        "temporary_media_allowed": False,
        "post_rename_cleanup_allowed": False,
        "audio_processing_allowed": False,
        "maximum_safe_audit_record_count": 1,
        **binding_values(),
        "output_path_basis": "relative_to_automation_directory",
        "output_format": "mp3_44100_128",
        "operation_scope": "one_synthetic_narration_mcp_operation_only",
        "retry_allowed": False, "maximum_provider_request_count": 1,
        "redirect_allowed": False, "fallback_allowed": False,
        "alternate_provider_allowed": False, "provider_discovery_allowed": False,
        "batch_mode_allowed": False, "multi_output_allowed": False,
        "status_or_polling_allowed": False, "cleanup_or_delete_allowed": False,
        "credential_access_allowed": False, "configuration_inspection_allowed": False,
        "environment_access_allowed": False, "voice_identifier_inspection_allowed": False,
        "account_data_access_allowed": False, "authorized_output_count": 1,
        "network_authorized": True, "synthetic_provider_call_authorized": True,
        "audio_output_authorized": True,
        "asset_authorized": False, "assembly_authorized": False,
        "rendering_authorized": False, "upload_authorized": False,
        "scheduling_authorized": False, "publishing_enabled": False,
        "real_production_enabled": False,
    }


class Harness:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(dir=C8A_TEST_TEMP_ROOT)
        self.root = DISPOSABLE
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.registry = InMemoryReplayRegistry()

    def close(self): self.temp.cleanup()

    def run(self, record=None, registry=None, output_root=None):
        return validate_hypothetical_record(
            record=record or hypothetical_record(), schema=self.schema,
            expected_bindings=binding_values(), future_c8_root=FUTURE,
            disposable_output_root=output_root or self.root,
            replay_registry=registry or self.registry,
        )


class C8aAuthorizationSchemaTests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def tearDown(self):
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])
        self.h.close()

    def test_01_complete_hypothetical_shape_validates_non_executable_only(self):
        result = self.h.run()
        self.assertEqual(result["state"], PASSED); self.assertTrue(result["structurally_valid"])
        for field in ("authorization_artifact_created", "execution_authorized", "provider_invoked", "network_invoked", "audio_file_created", "publishing_enabled", "real_production_enabled"):
            self.assertIs(result[field], False)

    def test_02_no_new_or_unconsumed_authorization_instance_or_creation_function_exists(self):
        before = historical_record_metadata_snapshot()
        self.assertIsNotNone(before)
        self.assertEqual(unexpected_historical_artifacts(), [])
        source = (AUTOMATION / "c8a_authorization_schema_validator.py").read_text(encoding="utf-8")
        for term in ("write_text", "write_bytes", "atomic_json", "open(", "execute_provider", "live_client"):
            self.assertNotIn(term, source)
        self.assertEqual(historical_record_metadata_snapshot(), before)
        self.assertEqual(unexpected_historical_artifacts(), [])

    def test_03_each_required_hash_binding_fails_independently(self):
        fields = ("fixture_text_sha256", "locked_mia_profile_sha256",
                  "c7_provider_request_contract_sha256", "provider_request_allowlist_sha256",
                  "authorized_output_path_sha256", "authorized_output_directory_path_sha256")
        for field in fields:
            record = hypothetical_record(); record[field] = "0" * 64
            with self.subTest(field=field): self.assertEqual(self.h.run(record, registry=InMemoryReplayRegistry())["state"], BLOCKED)

    def test_04_missing_null_additional_misspelled_and_loose_types_block(self):
        mutations = []
        missing = hypothetical_record(); missing.pop("retry_allowed"); mutations.append(missing)
        null = hypothetical_record(); null["fixture_text_sha256"] = None; mutations.append(null)
        extra = hypothetical_record(); extra["endpoint"] = "disallowed"; mutations.append(extra)
        misspelled = hypothetical_record(); misspelled["retry_allowd"] = misspelled.pop("retry_allowed"); mutations.append(misspelled)
        loose = hypothetical_record(); loose["maximum_provider_request_count"] = "1"; mutations.append(loose)
        for index, record in enumerate(mutations, 1):
            with self.subTest(index=index): self.assertEqual(self.h.run(record, registry=InMemoryReplayRegistry())["state"], BLOCKED)

    def test_05_one_attempt_retry_redirect_fallback_and_batch_rules_are_exact(self):
        changes = {"retry_allowed": True, "maximum_provider_request_count": 2,
                   "maximum_mcp_operation_count": 2, "redirect_allowed": True,
                   "fallback_allowed": True, "alternate_provider_allowed": True,
                   "provider_discovery_allowed": True, "batch_mode_allowed": True,
                   "multi_output_allowed": True, "status_or_polling_allowed": True,
                   "cleanup_or_delete_allowed": True, "authorized_output_count": 2}
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field): self.assertEqual(self.h.run(record, registry=InMemoryReplayRegistry())["state"], BLOCKED)

    def test_06_format_scope_and_all_denied_permissions_are_exact(self):
        changes = {"output_format": "wav", "operation_scope": "multiple_requests",
                   "execution_transport": "direct_http", "mcp_operation_allowed": False,
                   "other_mcp_tools_allowed": True, "direct_http_transport_allowed": True,
                   "option_a_environment_injection_allowed": True,
                   "option_b_private_config_allowed": True,
                   "credential_access_allowed": True, "configuration_inspection_allowed": True,
                   "environment_access_allowed": True, "voice_identifier_inspection_allowed": True,
                   "account_data_access_allowed": True,
                   "direct_exact_filename_input_supported": True,
                   "allowed_runtime_result_shapes": ["other"], "result_shape_must_be_single": False,
                   "local_finalization_action_allowed": False,
                   "maximum_local_rename_count": 2,
                   "maximum_resource_materialization_write_count": 2,
                   "atomic_same_filesystem_rename_required": False,
                   "exclusive_create_required": False,
                   "destination_must_be_absent": False, "overwrite_allowed": True,
                   "copy_allowed": True, "second_rename_allowed": True,
                   "rename_retry_allowed": True, "remote_reference_allowed": True,
                   "attachment_download_reference_allowed": True,
                   "metadata_only_success_allowed": True, "mixed_result_shapes_allowed": True,
                   "resource_url_fetch_allowed": True, "resource_content_inspection_allowed": True,
                   "resource_content_retention_allowed": True, "temporary_media_allowed": True,
                   "post_rename_cleanup_allowed": True, "audio_processing_allowed": True,
                   "maximum_safe_audit_record_count": 2,
                   "real_case_content_allowed": True, "real_script_approval_used": True,
                   "c4_approval_artifact_allowed": True, "asset_authorized": True,
                   "assembly_authorized": True, "rendering_authorized": True,
                   "upload_authorized": True, "scheduling_authorized": True,
                   "publishing_enabled": True, "real_production_enabled": True}
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field): self.assertEqual(self.h.run(record, registry=InMemoryReplayRegistry())["state"], BLOCKED)

    def test_07_secret_provider_endpoint_environment_command_fields_block(self):
        fields = ("url", "endpoint", "provider_name", "service_name", "api_key", "token",
                  "authorization_header", "voice_id", "secret", "environment_reference",
                  "config_reference", "command", "execution_route", "runner_identity",
                  "provider_api_credential", "locked_voice_identifier")
        for field in fields:
            record = hypothetical_record(); record[field] = "disallowed"
            with self.subTest(field=field): self.assertEqual(self.h.run(record, registry=InMemoryReplayRegistry())["state"], BLOCKED)

    def test_08_absolute_traversal_external_and_nonapproved_paths_block(self):
        paths = ("../escape.mp3", r"C:\outside\audio.mp3", "/outside/audio.mp3",
                 "attempt-0001/audio.wav", "attempt-0001/provider_output.mp3")
        for path in paths:
            record = hypothetical_record(); record["authorized_output_relative_path"] = path; record["authorized_output_path_sha256"] = text_sha256(path)
            expected = binding_values(); expected["authorized_output_relative_path"] = path; expected["authorized_output_path_sha256"] = text_sha256(path)
            result = validate_hypothetical_record(record=record, schema=self.h.schema, expected_bindings=expected,
                future_c8_root=FUTURE, disposable_output_root=self.h.root, replay_registry=InMemoryReplayRegistry())
            with self.subTest(path=path): self.assertEqual(result["state"], BLOCKED)

    def test_09_existing_audio_named_target_blocks_without_audio_creation(self):
        target = DISPOSABLE / "c8_isolated_synthetic_connectivity.mp3"; target.mkdir(parents=True)
        try:
            result = self.h.run(registry=InMemoryReplayRegistry())
            self.assertEqual(result["state"], BLOCKED); self.assertTrue(target.is_dir()); self.assertFalse(target.is_file())
        finally:
            target.rmdir()

    def test_10_output_root_escape_blocks(self):
        self.assertEqual(self.h.run(output_root=FUTURE.parent)["state"], BLOCKED)

    def test_11_replay_and_changed_record_with_same_id_block(self):
        registry = InMemoryReplayRegistry(); self.assertEqual(self.h.run(registry=registry)["state"], PASSED)
        self.assertEqual(self.h.run(registry=registry)["state"], BLOCKED)
        changed = hypothetical_record(); changed["expires_at_utc"] = "2026-07-12T14:05:00Z"
        self.assertEqual(self.h.run(changed, registry=registry)["state"], BLOCKED)

    def test_12_timestamp_order_format_and_lifetime_are_strict(self):
        values = (("issued_at_utc", "not-a-time"), ("expires_at_utc", "2026-07-12T13:59:59Z"),
                  ("expires_at_utc", "2026-07-12T15:00:00Z"))
        for field, value in values:
            record = hypothetical_record(); record[field] = value
            with self.subTest(field=field, value=value): self.assertEqual(self.h.run(record, registry=InMemoryReplayRegistry())["state"], BLOCKED)

    def test_13_schema_contract_and_allowlist_are_strict_and_provider_neutral(self):
        validate_schema_compatibility(self.h.schema)
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertTrue(contract["schema_only"]); self.assertFalse(contract["provider_neutral"])
        self.assertEqual(contract["active_execution_route"]["execution_transport"], "existing_configured_elevenlabs_mcp")
        for field in ("creation_permitted_in_c7", "validation_permitted_in_c7", "consumption_permitted_in_c7", "execution_permitted_in_c7", "creation_permitted_in_c8a", "execution_permitted_in_c8a", "creation_permitted_in_c8b", "execution_permitted_in_c8b"):
            self.assertIs(contract[field], False)
        self.assertEqual(binding_values()["provider_request_allowlist_sha256"], canonical_sha256(contract["c7_sanitized_request_allowlist"]))

    def test_14_c7_still_has_no_c8_creation_or_validation_route(self):
        source = inspect.getsource(NarrationProviderAdapter).lower()
        for term in ("c8", "create_authorization", "validate_authorization", "live_client"):
            self.assertNotIn(term, source)

    def test_15_helper_imports_no_execution_or_connectivity_facility(self):
        source = (AUTOMATION / "c8a_authorization_schema_validator.py").read_text(encoding="utf-8")
        for term in ("import requests", "import httpx", "import urllib", "import socket", "import subprocess", "os.environ", "getenv(", "http://", "https://"):
            self.assertNotIn(term, source)

    def test_16_local_rename_count_field_name_is_canonical_and_closed(self):
        valid = hypothetical_record()
        self.assertEqual(valid["maximum_local_rename_count"], 1)
        self.assertEqual(self.h.run(valid, registry=InMemoryReplayRegistry())["state"], PASSED)
        self.assertFalse(self.h.schema["additionalProperties"])
        self.assertIn("maximum_local_rename_count", self.h.schema["required"])
        self.assertNotIn("maximum_local_finalization_rename_count", self.h.schema["properties"])
        invalid = hypothetical_record()
        invalid["maximum_local_finalization_rename_count"] = invalid.pop("maximum_local_rename_count")
        self.assertEqual(self.h.run(invalid, registry=InMemoryReplayRegistry())["state"], BLOCKED)
        missing = hypothetical_record(); missing.pop("maximum_local_rename_count")
        self.assertEqual(self.h.run(missing, registry=InMemoryReplayRegistry())["state"], BLOCKED)
        wrong = hypothetical_record(); wrong["maximum_local_rename_count"] = 2
        self.assertEqual(self.h.run(wrong, registry=InMemoryReplayRegistry())["state"], BLOCKED)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8aAuthorizationSchemaTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c8a_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
