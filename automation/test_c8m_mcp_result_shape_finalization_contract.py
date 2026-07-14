from __future__ import annotations

import inspect
import json
import unittest

import c8m_mcp_result_shape_finalization_contract as result_contract
from c8a_authorization_schema_validator import BLOCKED, PASSED, InMemoryReplayRegistry, validate_hypothetical_record
from json_schema_subset import validate_schema_compatibility
from test_c8a_authorization_schema import (
    AUTOMATION, CONTRACT_PATH, DISPOSABLE, FUTURE, OUTPUT_DIRECTORY_PATH,
    SCHEMA_PATH, binding_values, hypothetical_record, post_attempt_artifacts_are_closed,
)


CHAIN_STATE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace" / "output" / "c3_real_writer_editor_chain" / "chain_state.json"


def local_result(path=None, **changes):
    value = {
        "path": path or f"{result_contract.OUTPUT_DIRECTORY}/generated.mp3",
        "entry_type": "regular_file", "direct_child": True,
        "newly_created": True, "preexisting": False,
        "is_link": False, "link_kind": None,
    }
    value.update(changes)
    return value


class C8mMcpResultShapeFinalizationContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def validate(self, record, expected=None):
        return validate_hypothetical_record(
            record=record, schema=self.schema, expected_bindings=expected or binding_values(),
            future_c8_root=FUTURE, disposable_output_root=DISPOSABLE,
            replay_registry=InMemoryReplayRegistry(),
        )

    def test_01_exact_runtime_result_shape_allowlist_is_authorization_bound(self):
        self.assertEqual(result_contract.RESULT_SHAPES, (
            "returned_contained_local_mp3_path", "mcp_audio_resource"
        ))
        self.assertTrue(result_contract.runtime_result_shape_allowlist_is_valid(
            list(result_contract.RESULT_SHAPES)
        ))
        for value in (None, "", [], [result_contract.RESULT_SHAPES[0]],
                      list(reversed(result_contract.RESULT_SHAPES)),
                      [*result_contract.RESULT_SHAPES, "other"]):
            self.assertFalse(result_contract.runtime_result_shape_allowlist_is_valid(value))
        missing = hypothetical_record(); missing.pop("allowed_runtime_result_shapes")
        self.assertEqual(self.validate(missing)["state"], BLOCKED)

    def test_02_runtime_classification_accepts_exactly_one_recognized_shape(self):
        allowed = list(result_contract.RESULT_SHAPES)
        self.assertEqual(result_contract.classify_runtime_result(
            [local_result()], allowed_runtime_result_shapes=allowed,
        ), result_contract.RESULT_SHAPES[0])
        resource = result_contract.OpaqueMcpAudioResource()
        self.assertEqual(result_contract.classify_runtime_result(
            [resource], allowed_runtime_result_shapes=allowed,
        ), result_contract.RESULT_SHAPES[1])
        self.assertIsNone(result_contract.classify_runtime_result(
            [], allowed_runtime_result_shapes=allowed,
        ))

    def test_03_local_path_accepts_one_new_contained_direct_regular_mp3(self):
        result = local_result()
        self.assertEqual(result_contract.evaluate_local_path_result(
            [result], classified_shape="returned_contained_local_mp3_path",
            destination_exists=False,
        ), result_contract.READY_LOCAL_PATH)
        plan = result_contract.local_path_rename_plan(result["path"])
        self.assertEqual(plan["rename_count"], 1)
        self.assertTrue(plan["atomic_same_filesystem"])
        self.assertEqual(plan["destination_relative_path"], result_contract.FINAL_OUTPUT)
        self.assertFalse(plan["overwrite"])

    def test_04_local_path_rejects_traversal_absolute_outside_nested_and_nonmp3(self):
        paths = (
            "../generated.mp3", "/outside/generated.mp3", r"C:\outside\generated.mp3",
            "https://example.invalid/generated.mp3", f"{result_contract.OUTPUT_DIRECTORY}/nested/generated.mp3",
            f"{result_contract.OUTPUT_DIRECTORY}/generated.wav", f"{result_contract.OUTPUT_DIRECTORY}/*.mp3",
            "other/generated.mp3",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(result_contract.evaluate_local_path_result(
                    [local_result(path)], classified_shape="returned_contained_local_mp3_path",
                    destination_exists=False,
                ), result_contract.BLOCKED_LOCAL_PATH)

    def test_05_local_path_rejects_links_directories_preexisting_and_bad_counts(self):
        cases = (
            [], [local_result(), local_result(f"{result_contract.OUTPUT_DIRECTORY}/second.mp3")],
            [local_result(entry_type="directory")], [local_result(direct_child=False)],
            [local_result(newly_created=False)], [local_result(preexisting=True)],
            [local_result(is_link=True, link_kind="symlink")],
            [local_result(is_link=True, link_kind="junction")],
            [local_result(is_link=True, link_kind="hardlink")],
        )
        for values in cases:
            state = result_contract.evaluate_local_path_result(
                values, classified_shape="returned_contained_local_mp3_path",
                destination_exists=False,
            )
            self.assertNotEqual(state, result_contract.READY_LOCAL_PATH)

    def test_06_audio_resource_accepts_one_exact_opaque_resource_only(self):
        resource = result_contract.OpaqueMcpAudioResource()
        self.assertEqual(result_contract.evaluate_audio_resource_result(
            [resource], classified_shape="mcp_audio_resource", destination_exists=False,
        ), result_contract.READY_AUDIO_RESOURCE)
        plan = result_contract.audio_resource_materialization_plan(resource)
        self.assertEqual(plan["materialization_write_count"], 1)
        self.assertTrue(plan["exclusive_create"])
        self.assertEqual(plan["destination_relative_path"], result_contract.FINAL_OUTPUT)
        self.assertNotIn("resource", plan)

    def test_07_audio_resource_rejects_missing_multiple_urls_attachments_bytes_and_metadata(self):
        resource = result_contract.OpaqueMcpAudioResource()
        cases = ([], [resource, resource], ["https://example.invalid/audio"],
                 [{"attachment": "download"}], [b"audio"], [bytearray(b"audio")],
                 [memoryview(b"audio")], [{"metadata": "only"}], [object()])
        for values in cases:
            with self.subTest(kind=type(values[0]).__name__ if values else "empty"):
                self.assertNotEqual(result_contract.evaluate_audio_resource_result(
                    values, classified_shape="mcp_audio_resource", destination_exists=False,
                ), result_contract.READY_AUDIO_RESOURCE)

    def test_08_mixed_path_and_resource_results_are_ambiguous_and_blocked(self):
        resource = result_contract.OpaqueMcpAudioResource()
        allowed = list(result_contract.RESULT_SHAPES)
        for values in ([], [local_result(), resource], [resource, resource],
                       ["https://example.invalid/audio"], [{"metadata": "only"}], [b"audio"]):
            self.assertIsNone(result_contract.classify_runtime_result(
                values, allowed_runtime_result_shapes=allowed,
            ))
        self.assertIsNone(result_contract.classify_runtime_result(
            [resource], allowed_runtime_result_shapes=[result_contract.RESULT_SHAPES[1]],
        ))

    def test_09_destination_exists_and_finalization_failures_block_without_retry(self):
        resource = result_contract.OpaqueMcpAudioResource()
        self.assertEqual(result_contract.evaluate_local_path_result(
            [local_result()], classified_shape=result_contract.RESULT_SHAPES[0], destination_exists=True,
        ), result_contract.BLOCKED_DESTINATION)
        self.assertEqual(result_contract.evaluate_local_path_result(
            [local_result()], classified_shape=result_contract.RESULT_SHAPES[0], destination_exists=False,
            rename_failed=True,
        ), result_contract.BLOCKED_FINALIZATION)
        self.assertEqual(result_contract.evaluate_audio_resource_result(
            [resource], classified_shape=result_contract.RESULT_SHAPES[1], destination_exists=True,
        ), result_contract.BLOCKED_DESTINATION)
        self.assertEqual(result_contract.evaluate_audio_resource_result(
            [resource], classified_shape=result_contract.RESULT_SHAPES[1], destination_exists=False,
            write_failed=True,
        ), result_contract.BLOCKED_FINALIZATION)

    def test_10_one_mcp_one_output_and_one_action_limits_are_unchanged(self):
        record = hypothetical_record()
        self.assertEqual(record["maximum_mcp_operation_count"], 1)
        self.assertEqual(record["maximum_provider_request_count"], 1)
        self.assertEqual(record["authorized_output_count"], 1)
        self.assertEqual(record["maximum_local_rename_count"], 1)
        self.assertEqual(record["maximum_resource_materialization_write_count"], 1)
        self.assertTrue(result_contract.finalization_boundary_is_exact(
            self.contract["active_result_shape_finalization_boundary"]
        ))

    def test_11_retry_followup_copy_overwrite_cleanup_and_processing_remain_forbidden(self):
        record = hypothetical_record()
        for field in ("retry_allowed", "redirect_allowed", "fallback_allowed",
                      "alternate_provider_allowed", "provider_discovery_allowed",
                      "status_or_polling_allowed", "cleanup_or_delete_allowed",
                      "copy_allowed", "overwrite_allowed", "second_rename_allowed",
                      "rename_retry_allowed", "post_rename_cleanup_allowed",
                      "audio_processing_allowed", "remote_reference_allowed",
                      "attachment_download_reference_allowed", "metadata_only_success_allowed",
                      "mixed_result_shapes_allowed", "resource_url_fetch_allowed"):
            self.assertFalse(record[field])

    def test_12_output_directory_and_final_path_bindings_are_exact(self):
        record = hypothetical_record()
        self.assertEqual(record["authorized_output_directory_relative_path"], OUTPUT_DIRECTORY_PATH)
        self.assertEqual(record["authorized_output_relative_path"], result_contract.FINAL_OUTPUT)
        self.assertNotIn("authorized_staging_directory_relative_path", record)
        for field in ("authorized_output_directory_path_sha256", "authorized_output_path_sha256"):
            changed = hypothetical_record(); changed[field] = "0" * 64
            self.assertEqual(self.validate(changed)["state"], BLOCKED)

    def test_13_schema_is_strict_for_both_result_shapes(self):
        validate_schema_compatibility(self.schema)
        self.assertFalse(self.schema["additionalProperties"])
        shape_schema = self.schema["properties"]["allowed_runtime_result_shapes"]
        self.assertEqual(shape_schema["type"], "array")
        self.assertEqual(shape_schema["items"]["enum"], list(result_contract.RESULT_SHAPES))
        extra = hypothetical_record(); extra["result_shape_two"] = "mcp_audio_resource"
        self.assertEqual(self.validate(extra)["state"], BLOCKED)

    def test_14_single_use_replay_and_max_fifteen_minute_expiry_remain_required(self):
        record = hypothetical_record(); registry = InMemoryReplayRegistry()
        self.assertEqual(validate_hypothetical_record(
            record=record, schema=self.schema, expected_bindings=binding_values(),
            future_c8_root=FUTURE, disposable_output_root=DISPOSABLE,
            replay_registry=registry,
        )["state"], PASSED)
        self.assertEqual(validate_hypothetical_record(
            record=record, schema=self.schema, expected_bindings=binding_values(),
            future_c8_root=FUTURE, disposable_output_root=DISPOSABLE,
            replay_registry=registry,
        )["state"], BLOCKED)
        too_long = hypothetical_record(); too_long["expires_at_utc"] = "2026-07-12T15:00:00Z"
        self.assertEqual(self.validate(too_long)["state"], BLOCKED)

    def test_15_module_has_no_mcp_provider_network_shell_or_external_command(self):
        source = inspect.getsource(result_contract).lower()
        for term in ("mcp__", "tool_search", "import requests", "import httpx", "import urllib",
                     "import socket", "import subprocess", "os.system", "shell=true",
                     "powershell", "node", "codex", "browser", "http://", "https://"):
            self.assertNotIn(term, source)

    def test_16_module_has_no_environment_configuration_secret_or_provider_value_access(self):
        source = inspect.getsource(result_contract).lower()
        for term in ("os.environ", "getenv(", "api_key", "voice_id", "endpoint", "headers",
                     "account_data", "private_config", "login_state", "credential"):
            self.assertNotIn(term, source)

    def test_17_c3_c4_real_case_and_production_boundaries_remain_closed(self):
        state = json.loads(CHAIN_STATE.read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"])
        record = hypothetical_record()
        self.assertFalse(record["c4_approval_artifact_allowed"])
        self.assertFalse(record["real_case_content_allowed"])
        self.assertFalse(record["publishing_enabled"])
        self.assertFalse(record["real_production_enabled"])
        self.assertNotIn("c4_script_approval_sha256", self.schema["properties"])

    def test_18_no_live_artifact_audio_media_or_executable_finalizer_is_created(self):
        self.assertTrue(post_attempt_artifacts_are_closed())
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])
        source = inspect.getsource(result_contract)
        for term in ("write_bytes", "write_text", "open(", ".rename(", ".replace(",
                     "shutil", "copyfile", "unlink(", "rmdir("):
            self.assertNotIn(term, source)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8mMcpResultShapeFinalizationContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "c8m_offline_tests": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "mcp_invocation": "not_performed",
        "authorization_artifact": "not_created",
        "audio_or_media_creation": "not_performed",
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
