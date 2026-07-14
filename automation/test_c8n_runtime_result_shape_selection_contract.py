from __future__ import annotations

import inspect
import json
import unittest

import c8m_mcp_result_shape_finalization_contract as result_contract
from c8a_authorization_schema_validator import (
    BLOCKED, PASSED, InMemoryReplayRegistry, validate_hypothetical_record,
)
from test_c8a_authorization_schema import (
    AUTOMATION, CONTRACT_PATH, DISPOSABLE, FUTURE, SCHEMA_PATH,
    binding_values, hypothetical_record,
)


CHAIN_STATE = (
    AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace" / "output"
    / "c3_real_writer_editor_chain" / "chain_state.json"
)


def local_result(path: str | None = None, **changes):
    value = {
        "path": path or f"{result_contract.OUTPUT_DIRECTORY}/generated.mp3",
        "entry_type": "regular_file",
        "direct_child": True,
        "newly_created": True,
        "preexisting": False,
        "is_link": False,
        "link_kind": None,
    }
    value.update(changes)
    return value


class C8nRuntimeResultShapeSelectionContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def validate(self, record):
        return validate_hypothetical_record(
            record=record,
            schema=self.schema,
            expected_bindings=binding_values(),
            future_c8_root=FUTURE,
            disposable_output_root=DISPOSABLE,
            replay_registry=InMemoryReplayRegistry(),
        )

    def test_01_exact_canonical_two_shape_allowlist_validates(self):
        record = hypothetical_record()
        self.assertEqual(record["allowed_runtime_result_shapes"], list(result_contract.RESULT_SHAPES))
        self.assertTrue(result_contract.runtime_result_shape_allowlist_is_valid(
            record["allowed_runtime_result_shapes"]
        ))
        self.assertEqual(self.validate(record)["state"], PASSED)

    def test_02_noncanonical_allowlists_fail_closed(self):
        local_shape, resource_shape = result_contract.RESULT_SHAPES
        invalid = (
            [], [local_shape], [resource_shape], [resource_shape, local_shape],
            [local_shape, local_shape], [local_shape, resource_shape, resource_shape],
            ["*", resource_shape], ["arbitrary", resource_shape],
            [local_shape, resource_shape, "additional"],
        )
        for value in invalid:
            record = hypothetical_record()
            record["allowed_runtime_result_shapes"] = value
            with self.subTest(value=value):
                self.assertFalse(result_contract.runtime_result_shape_allowlist_is_valid(value))
                self.assertEqual(self.validate(record)["state"], BLOCKED)

    def test_03_classifier_accepts_exactly_one_recognized_runtime_shape(self):
        allowed = list(result_contract.RESULT_SHAPES)
        classifier = self.contract["runtime_result_classifier"]
        self.assertEqual(classifier["classification_timing"], "after_single_mcp_operation")
        self.assertEqual(classifier["allowed_runtime_result_shapes"], allowed)
        self.assertEqual(classifier["required_recognized_result_shape_count"], 1)
        local = local_result()
        resource = result_contract.OpaqueMcpAudioResource()
        self.assertEqual(result_contract.classify_runtime_result(
            [local], allowed_runtime_result_shapes=allowed,
        ), result_contract.RESULT_SHAPES[0])
        self.assertEqual(result_contract.classify_runtime_result(
            [resource], allowed_runtime_result_shapes=allowed,
        ), result_contract.RESULT_SHAPES[1])

    def test_04_zero_multiple_mixed_and_unknown_results_fail_closed(self):
        allowed = list(result_contract.RESULT_SHAPES)
        resource = result_contract.OpaqueMcpAudioResource()
        cases = (
            [], [local_result(), local_result()], [resource, resource],
            [local_result(), resource], [object()],
        )
        for values in cases:
            with self.subTest(count=len(values)):
                self.assertIsNone(result_contract.classify_runtime_result(
                    values, allowed_runtime_result_shapes=allowed,
                ))

    def test_05_unsafe_and_malformed_result_shapes_fail_closed(self):
        allowed = list(result_contract.RESULT_SHAPES)
        cases = (
            ["https://example.invalid/audio.mp3"],
            [{"download": "reference"}],
            [{"attachment": "reference"}],
            [{"metadata": "only"}],
            ["non-audio text"],
            [b"audio"], [bytearray(b"audio")], [memoryview(b"audio")],
            [{"path": f"{result_contract.OUTPUT_DIRECTORY}/generated.mp3"}],
            [local_result(f"{result_contract.OUTPUT_DIRECTORY}/nested/generated.mp3")],
            [local_result("../outside.mp3")],
            [local_result(is_link=True, link_kind="symlink")],
        )
        for values in cases:
            with self.subTest(kind=type(values[0]).__name__):
                self.assertIsNone(result_contract.classify_runtime_result(
                    values, allowed_runtime_result_shapes=allowed,
                ))

    def test_06_local_path_retains_one_atomic_rename_boundary(self):
        result = local_result()
        shape = result_contract.classify_runtime_result(
            [result], allowed_runtime_result_shapes=list(result_contract.RESULT_SHAPES),
        )
        self.assertEqual(result_contract.evaluate_local_path_result(
            [result], classified_shape=shape, destination_exists=False,
        ), result_contract.READY_LOCAL_PATH)
        plan = result_contract.local_path_rename_plan(result["path"])
        self.assertEqual(plan["rename_count"], 1)
        self.assertTrue(plan["atomic_same_filesystem"])
        self.assertFalse(plan["overwrite"])
        self.assertEqual(plan["destination_relative_path"], result_contract.FINAL_OUTPUT)

    def test_07_audio_resource_retains_one_exclusive_create_boundary(self):
        resource = result_contract.OpaqueMcpAudioResource()
        shape = result_contract.classify_runtime_result(
            [resource], allowed_runtime_result_shapes=list(result_contract.RESULT_SHAPES),
        )
        self.assertEqual(result_contract.evaluate_audio_resource_result(
            [resource], classified_shape=shape, destination_exists=False,
        ), result_contract.READY_AUDIO_RESOURCE)
        plan = result_contract.audio_resource_materialization_plan(resource)
        self.assertEqual(plan["materialization_write_count"], 1)
        self.assertTrue(plan["exclusive_create"])
        self.assertFalse(plan["overwrite"])
        self.assertEqual(plan["destination_relative_path"], result_contract.FINAL_OUTPUT)
        self.assertNotIn("resource", plan)

    def test_08_one_operation_one_output_and_no_retry_limits_remain_exact(self):
        record = hypothetical_record()
        self.assertEqual(record["execution_transport"], "existing_configured_elevenlabs_mcp")
        for field in ("maximum_mcp_operation_count", "maximum_provider_request_count",
                      "authorized_output_count", "maximum_local_rename_count",
                      "maximum_resource_materialization_write_count",
                      "maximum_safe_audit_record_count"):
            self.assertEqual(record[field], 1)
        for field in ("retry_allowed", "redirect_allowed", "fallback_allowed",
                      "alternate_provider_allowed", "provider_discovery_allowed",
                      "batch_mode_allowed", "multi_output_allowed", "status_or_polling_allowed",
                      "cleanup_or_delete_allowed", "copy_allowed", "overwrite_allowed"):
            self.assertFalse(record[field])
        self.assertTrue(result_contract.finalization_boundary_is_exact(
            self.contract["active_result_shape_finalization_boundary"]
        ))

    def test_09_contract_is_offline_and_production_boundaries_remain_closed(self):
        source = inspect.getsource(result_contract).lower()
        for term in ("mcp__", "tool_search", "import requests", "import httpx", "import urllib",
                     "import socket", "import subprocess", "os.system", "shell=true",
                     "powershell", "node", "codex", "browser", "os.environ", "getenv(",
                     "api_key", "voice_id", "endpoint", "headers", "account_data",
                     "private_config", "login_state", "credential", "write_bytes",
                     "write_text", "open(", ".rename(", ".replace("):
            self.assertNotIn(term, source)
        state = json.loads(CHAIN_STATE.read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"])
        record = hypothetical_record()
        self.assertFalse(record["c4_approval_artifact_allowed"])
        self.assertFalse(record["real_case_content_allowed"])
        self.assertFalse(record["publishing_enabled"])
        self.assertFalse(record["real_production_enabled"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        C8nRuntimeResultShapeSelectionContractTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "c8n_offline_tests": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "mcp_invocation": "not_performed",
        "authorization_artifact": "not_created",
        "audio_or_media_creation": "not_performed",
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
