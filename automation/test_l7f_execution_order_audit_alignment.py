from __future__ import annotations

import ast
import copy
import json
import sys
import unittest

import l8_one_time_piper_synthetic_runner as runner_module
from l7_piper_synthetic_authorization_contract import (
    L8_AUTHORIZATION_CONSUMED,
    L8_AUTHORIZED_NOT_EXECUTED,
    validate_l8_durable_authorization_record,
)
from test_l8_one_time_piper_synthetic_runner import (
    FAKE_TEXT,
    dependencies,
    valid_authorization,
)


class L7FExecutionOrderAuditAlignmentTests(unittest.TestCase):
    def setUp(self):
        runner_module._reset_process_state_for_offline_tests()

    def test_01_valid_future_sequence_matches_the_canonical_order(self):
        trace, deps = dependencies()
        result = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        labels = [item if isinstance(item, str) else item[0] for item in trace]
        self.assertEqual(result.lifecycle_status, L8_AUTHORIZATION_CONSUMED)
        self.assertEqual(result.outcome, "ONE_SYNTHETIC_OUTPUT_CREATED")
        self.assertEqual(
            labels,
            [
                "caller_clock",
                "authorization_create",
                "sealed_launch",
                "authorization_read",
                "inside_clock",
                "output_preflight",
                "create_root",
                "runtime_preflight",
                "inside_clock",
                "text_supplier",
                "runtime_create",
                "session_initialize",
                "runtime_identity",
                "synthesize",
                "write",
                "authorization_consume",
                "audit_create",
            ],
        )

    def test_02_invalid_in_memory_authorization_creates_nothing_and_never_launches(self):
        for field, value in (
            ("schema_version", "wrong"),
            ("authorization_purpose", "real_narration"),
            ("single_use_nonce", ""),
            ("expiration_timestamp", "bad"),
            ("maximum_retry_count", 1),
            ("output_filename", "alternate.wav"),
        ):
            runner_module._reset_process_state_for_offline_tests()
            trace, deps = dependencies()
            candidate = valid_authorization()
            candidate[field] = value
            with self.subTest(field=field):
                result = runner_module.execute_one_time_piper_synthetic(
                    authorization=candidate, **deps
                )
                self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
                self.assertEqual(trace, [])
                self.assertEqual(deps["safe_audit_sink"].authorization_records, [])
                self.assertEqual(deps["safe_audit_sink"].audit_records, [])

    def test_03_durable_authorization_precedes_the_only_fake_launch(self):
        trace, deps = dependencies()
        runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertLess(trace.index("authorization_create"), trace.index("sealed_launch"))
        self.assertEqual(trace.count("authorization_create"), 1)
        self.assertEqual(trace.count("sealed_launch"), 1)
        record = deps["safe_audit_sink"].authorization_records[0]
        self.assertEqual(record["lifecycle_status"], L8_AUTHORIZED_NOT_EXECUTED)

    def test_04_filesystem_and_runtime_preflight_exist_only_inside_launch(self):
        trace, deps = dependencies()
        runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        labels = [item if isinstance(item, str) else item[0] for item in trace]
        for inside in ("authorization_read", "output_preflight", "create_root", "runtime_preflight"):
            self.assertLess(labels.index("sealed_launch"), labels.index(inside))
        self.assertLess(labels.index("output_preflight"), labels.index("create_root"))
        self.assertLess(labels.index("create_root"), labels.index("runtime_preflight"))
        for later in ("text_supplier", "runtime_create", "synthesize", "write"):
            self.assertLess(labels.index("runtime_preflight"), labels.index(later))

    def test_05_consumption_precedes_the_single_safe_audit(self):
        trace, deps = dependencies()
        runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        sink = deps["safe_audit_sink"]
        self.assertEqual(trace.count("authorization_consume"), 1)
        self.assertEqual(trace.count("audit_create"), 1)
        self.assertLess(trace.index("authorization_consume"), trace.index("audit_create"))
        self.assertEqual(sink.consumed_records[0]["lifecycle_status"], L8_AUTHORIZATION_CONSUMED)
        self.assertEqual(sink.audit_records[0]["lifecycle_status"], L8_AUTHORIZATION_CONSUMED)

    def test_06_each_post_create_boundary_failure_consumes_and_audits_once(self):
        stages = (
            "sealed_launch",
            "bootstrap_failure",
            "malformed_result",
            "container_result",
            "authorization_read",
            "inside_clock_1",
            "inside_clock_2",
            "output_preflight",
            "create_root",
            "runtime_preflight",
            "text_supplier",
            "runtime_create",
            "session_initialize",
            "runtime_identity",
            "synthesis",
            "writer",
        )
        for stage in stages:
            runner_module._reset_process_state_for_offline_tests()
            trace, deps = dependencies(fail_at=stage)
            result = runner_module.execute_one_time_piper_synthetic(
                authorization=valid_authorization(), **deps
            )
            with self.subTest(stage=stage):
                self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
                self.assertEqual(trace.count("authorization_create"), 1)
                self.assertEqual(trace.count("sealed_launch"), 1)
                self.assertEqual(trace.count("authorization_consume"), 1)
                self.assertEqual(trace.count("audit_create"), 1)
                self.assertEqual(result.sealed_interpreter_process_count, 1)
                self.assertEqual(result.retry_count, 0)
                self.assertEqual(result.fallback_count, 0)
                if stage in {
                    "sealed_launch",
                    "malformed_result",
                    "container_result",
                    "writer",
                }:
                    self.assertTrue(result.output_state_unknown)
                    self.assertTrue(
                        deps["safe_audit_sink"].audit_records[0][
                            "output_state_unknown"
                        ]
                    )
                else:
                    self.assertFalse(result.output_state_unknown)

    def test_07_authorization_create_failure_has_no_launch_consumption_or_audit(self):
        trace, deps = dependencies(fail_at="caller_clock")
        clock_failure = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(clock_failure.safe_error_category, "clock_failed")
        self.assertEqual(trace, ["caller_clock"])

        runner_module._reset_process_state_for_offline_tests()
        trace, deps = dependencies(fail_at="authorization_create")
        result = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.safe_error_category, "authorization_create_failed")
        self.assertEqual(trace, ["caller_clock", "authorization_create"])
        self.assertNotIn("sealed_launch", trace)
        self.assertNotIn("authorization_consume", trace)
        self.assertNotIn("audit_create", trace)

    def test_08_consumption_failure_cannot_create_an_early_or_invalid_audit(self):
        trace, deps = dependencies(fail_at="authorization_consume")
        result = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(
            result.safe_error_category,
            "authorization_consumption_failed_closed",
        )
        self.assertEqual(trace.count("authorization_consume"), 1)
        self.assertEqual(trace.count("audit_create"), 0)
        self.assertEqual(result.retry_count, 0)

        runner_module._reset_process_state_for_offline_tests()
        trace, deps = dependencies(fail_at="audit_create")
        audit_failure = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(audit_failure.safe_error_category, "audit_create_failed_closed")
        self.assertEqual(trace.count("authorization_consume"), 1)
        self.assertEqual(trace.count("audit_create"), 1)
        self.assertEqual(audit_failure.retry_count, 0)

    def test_09_raw_text_and_raw_nonce_are_absent_from_all_durable_results(self):
        _, deps = dependencies()
        result = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        sink = deps["safe_audit_sink"]
        rendered = json.dumps(
            {
                "result": {name: getattr(result, name) for name in result.__slots__},
                "authorized": sink.authorization_records,
                "consumed": sink.consumed_records,
                "audit": sink.audit_records,
            },
            default=str,
        )
        self.assertNotIn(FAKE_TEXT, rendered)
        self.assertNotIn("a" * 64, rendered)
        self.assertNotIn("single_use_nonce", rendered)
        self.assertIn("nonce_fingerprint", rendered)

        runner_module._reset_process_state_for_offline_tests()
        malicious_text = "malicious raw child sentinel"
        _, malicious_deps = dependencies(text=malicious_text)
        failure = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **malicious_deps
        )
        malicious_sink = malicious_deps["safe_audit_sink"]
        failure_rendered = json.dumps(
            {
                "result": {
                    name: getattr(failure, name) for name in failure.__slots__
                },
                "authorized": malicious_sink.authorization_records,
                "consumed": malicious_sink.consumed_records,
                "audit": malicious_sink.audit_records,
            },
            default=str,
        )
        self.assertEqual(failure.safe_error_category, "text_hash_mismatch")
        self.assertNotIn(malicious_text, failure_rendered)

        runner_module._reset_process_state_for_offline_tests()
        _, malformed_deps = dependencies(fail_at="malformed_result")
        malformed = runner_module.execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **malformed_deps
        )
        malformed_rendered = json.dumps(
            {
                "result": {
                    name: getattr(malformed, name)
                    for name in malformed.__slots__
                },
                "audit": malformed_deps["safe_audit_sink"].audit_records,
            },
            default=str,
        )
        self.assertEqual(malformed.safe_error_category, "sealed_result_invalid")
        self.assertNotIn("raw_text", malformed_rendered)

    def test_10_linkage_fields_fail_before_durable_creation(self):
        for field in ("c3_status", "c4_approval", "case_id", "script", "research", "channel", "production"):
            runner_module._reset_process_state_for_offline_tests()
            trace, deps = dependencies()
            candidate = valid_authorization()
            candidate[field] = "forbidden"
            with self.subTest(field=field):
                result = runner_module.execute_one_time_piper_synthetic(
                    authorization=candidate, **deps
                )
                self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
                self.assertEqual(trace, [])

    def test_11_durable_validator_requires_complete_fingerprint_only_snapshot(self):
        record = runner_module._safe_authorization_record(
            valid_authorization(), L8_AUTHORIZED_NOT_EXECUTED
        )
        self.assertTrue(
            validate_l8_durable_authorization_record(
                record, expected_lifecycle=L8_AUTHORIZED_NOT_EXECUTED
            ).valid
        )
        for mutation in (
            {**record, "single_use_nonce": "a" * 64},
            {key: value for key, value in record.items() if key != "nonce_fingerprint"},
            {**record, "output_filename": "other.wav"},
            {**record, "lifecycle_status": "RESET"},
        ):
            with self.subTest(fields=len(mutation)):
                self.assertFalse(
                    validate_l8_durable_authorization_record(
                        mutation, expected_lifecycle=L8_AUTHORIZED_NOT_EXECUTED
                    ).valid
                )
        self.assertFalse(
            validate_l8_durable_authorization_record(
                record, expected_lifecycle=[]
            ).valid
        )

    def test_12_canonical_entrypoint_and_child_result_binding_are_fail_closed(self):
        source = runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        self.assertIsInstance(ast.parse(source, mode="exec"), ast.Module)
        self.assertNotIn('"', source)
        self.assertIn("read_authorization_once()", source)
        for forbidden in (
            "uuid",
            "secrets",
            "single_use_nonce",
            "create_authorization_exclusive",
            "consume_authorization_exclusive",
            "create_audit_exclusive",
            "subprocess",
            "Popen",
            "system(",
            "os.environ",
            "sys.argv",
        ):
            self.assertNotIn(forbidden, source)
        self.assertFalse(runner_module._process_execution_claimed)
        self.assertFalse(runner_module._sealed_execution_claimed)
        self.assertNotIn("piper.voice", sys.modules)
        self.assertNotIn("onnxruntime", sys.modules)

        record = runner_module._safe_authorization_record(
            valid_authorization(), L8_AUTHORIZED_NOT_EXECUTED
        )
        valid = runner_module._execute_inside_sealed_interpreter(
            durable_authorization_record=record,
            **dependencies()[1]["sealed_interpreter_boundary"].inner,
        )
        serialized = {
            **{name: getattr(valid, name) for name in valid.__slots__},
            "interface_binding": "succeeded",
        }
        malicious_cases = (
            {**serialized, "safe_error_category": "arbitrary_child_error", "outcome": "EXECUTION_FAILED_CLOSED", "output_file_count": 0, "output_path": None, "output_byte_count": None, "output_sha256": None},
            {**serialized, "output_sha256": "z" * 64},
            {**serialized, "output_path": r"C:\Other\escape.wav"},
            {**serialized, "raw_text": "forbidden"},
            {**serialized, "interface_binding": ["succeeded"]},
            {**serialized, "safe_error_category": {"unsafe": "container"}, "outcome": "EXECUTION_FAILED_CLOSED", "output_file_count": 0, "output_path": None, "output_byte_count": None, "output_sha256": None},
        )
        for candidate in malicious_cases:
            with self.subTest(fields=len(candidate)):
                self.assertIsNone(
                    runner_module._validate_child_result(candidate, record)
                )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L7FExecutionOrderAuditAlignmentTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        json.dumps(
            {
                "l7f_offline_alignment_tests": (
                    "passed" if result.wasSuccessful() else "failed"
                ),
                "tests_run": result.testsRun,
                "real_authorizations_or_audits": 0,
                "authorization_or_audit_root_interactions": 0,
                "filesystem_or_output_root_interactions": 0,
                "sealed_interpreter_launches": 0,
                "piper_or_onnx_imports": 0,
                "runtime_processes": 0,
                "model_loads": 0,
                "real_text_handoffs": 0,
                "inference_or_synthesis_calls": 0,
                "audio_or_media_artifacts": 0,
                "network_or_provider_activity": 0,
                "secret_or_environment_access": 0,
                "c3_c4_or_production_access": 0,
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)
