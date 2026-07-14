from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

import l8_one_time_piper_synthetic_runner as runner_module
from l7_piper_synthetic_authorization_contract import (
    CONFIG_SHA256,
    EXECUTION_PROVIDER,
    L8_AUDIT_ROOT,
    L8_AUTHORIZATION_CONSUMED,
    L8_AUTHORIZATION_ROOT,
    L8_AUTHORIZED_NOT_EXECUTED,
    L8_EXECUTABLE_OUTPUT_FILENAME,
    L8_EXECUTABLE_OUTPUT_ROOT,
    L8_EXECUTABLE_SCHEMA_VERSION,
    MODEL_ID,
    MODEL_SHA256,
    OUTPUT_FORMAT,
    PIPER_VERSION,
    ROUTE_ID,
    SYNTHETIC_AUTHORIZATION_PURPOSE,
)
from l8_one_time_piper_synthetic_runner import execute_one_time_piper_synthetic


AUTOMATION = Path(__file__).resolve().parent
RUNNER_SOURCE = AUTOMATION / "l8_one_time_piper_synthetic_runner.py"
FAKE_TEXT = "Offline synthetic fixture only; no case material."
FAKE_WAV_BYTES = b"L7C_FAKE_NON_AUDIO_BYTES"


def valid_authorization():
    return {
        "schema_version": L8_EXECUTABLE_SCHEMA_VERSION,
        "authorization_id": "L8-SYNTHETIC-123e4567-e89b-42d3-a456-426614174000",
        "single_use_nonce": "a" * 64,
        "expiration_timestamp": "2026-07-14T00:00:00Z",
        "lifecycle_status": L8_AUTHORIZED_NOT_EXECUTED,
        "authorization_purpose": SYNTHETIC_AUTHORIZATION_PURPOSE,
        "synthetic_test_only": True,
        "non_case_text_only": True,
        "no_personal_data": True,
        "route_id": ROUTE_ID,
        "piper_version": PIPER_VERSION,
        "model_id": MODEL_ID,
        "model_sha256": MODEL_SHA256,
        "config_sha256": CONFIG_SHA256,
        "execution_provider": EXECUTION_PROVIDER,
        "output_format": OUTPUT_FORMAT,
        "text_sha256": hashlib.sha256(FAKE_TEXT.encode("utf-8")).hexdigest(),
        "maximum_runtime_process_count": 1,
        "maximum_session_initialization_count": 1,
        "maximum_synthesis_attempt_count": 1,
        "maximum_text_input_count": 1,
        "maximum_output_file_count": 1,
        "maximum_output_write_count": 1,
        "maximum_retry_count": 0,
        "maximum_fallback_count": 0,
        "maximum_voice_count": 1,
        "allowed_voice_ids": [MODEL_ID],
        "output_root": L8_EXECUTABLE_OUTPUT_ROOT,
        "output_filename": L8_EXECUTABLE_OUTPUT_FILENAME,
        "authorization_root": L8_AUTHORIZATION_ROOT,
        "audit_root": L8_AUDIT_ROOT,
        "exclusive_create_only": True,
        "output_root_must_be_absent": True,
        "target_output_must_not_exist": True,
        "disallow_output_mutation": True,
        "stop_after_first_attempt": True,
    }


class FakeClock:
    def __init__(self, trace, label="clock", *, fail=False, fail_on_call=None):
        self.trace = trace
        self.label = label
        self.fail = fail
        self.fail_on_call = fail_on_call
        self.calls = 0

    def now_utc(self):
        self.calls += 1
        self.trace.append(self.label)
        if self.fail or self.calls == self.fail_on_call:
            raise RuntimeError("fake_clock_failure")
        return datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)


class FakeFileSystemBoundary:
    def __init__(self, trace, *, fail_at=None):
        self.trace = trace
        self.fail_at = fail_at

    def preflight_output_absent(self):
        self.trace.append("output_preflight")
        safe = self.fail_at != "output_preflight"
        return {
            "root_absent": safe,
            "target_absent": safe,
            "canonical_containment": safe,
            "root_would_be_regular": safe,
            "non_link": safe,
            "non_reparse": safe,
            "exclusive_create_supported": safe,
        }

    def create_root_exclusive(self):
        self.trace.append("create_root")
        if self.fail_at == "create_root":
            raise RuntimeError("fake_root_failure")
        return {
            "created_exclusively": True,
            "empty": True,
            "canonical_containment": True,
            "regular_directory": True,
            "non_link": True,
            "non_reparse": True,
        }


class FakeTextSupplier:
    def __init__(self, trace, *, fail_at=None, text=FAKE_TEXT, synthetic=True):
        self.trace = trace
        self.fail_at = fail_at
        self.text = text
        self.synthetic = synthetic
        self.last_envelope = None

    def supply_ephemeral_text_once(self, expected_sha256):
        self.trace.append("text_supplier")
        if self.fail_at == "text_supplier":
            raise RuntimeError("fake_text_supplier_failure")
        supplied = self.text
        self.text = None
        self.last_envelope = {
            "text": supplied,
            "synthetic_test_only": self.synthetic,
            "non_case_text_only": self.synthetic,
            "no_personal_data": self.synthetic,
        }
        return self.last_envelope


class FakeSession:
    def __init__(self, trace, *, fail_at=None):
        self.trace = trace
        self.fail_at = fail_at

    def locked_identity(self):
        self.trace.append("runtime_identity")
        if self.fail_at == "runtime_identity":
            return {"piper_version": "wrong"}
        return {
            "route_id": ROUTE_ID,
            "piper_version": PIPER_VERSION,
            "model_id": MODEL_ID,
            "model_sha256": MODEL_SHA256,
            "config_sha256": CONFIG_SHA256,
            "execution_provider": EXECUTION_PROVIDER,
            "voice_id": MODEL_ID,
            "output_format": OUTPUT_FORMAT,
        }

    def synthesize_once(self, text):
        self.trace.append(("synthesize", hashlib.sha256(text.encode()).hexdigest()))
        if self.fail_at == "synthesis":
            raise RuntimeError("fake_synthesis_failure")
        return FAKE_WAV_BYTES


class FakeRuntime:
    def __init__(self, trace, *, fail_at=None):
        self.trace = trace
        self.fail_at = fail_at

    def initialize_locked_session(self):
        self.trace.append("session_initialize")
        if self.fail_at == "session_initialize":
            raise RuntimeError("fake_session_failure")
        return FakeSession(self.trace, fail_at=self.fail_at)


class FakeRuntimeFactory:
    def __init__(self, trace, *, fail_at=None):
        self.trace = trace
        self.fail_at = fail_at

    def preflight_locked_runtime(self):
        self.trace.append("runtime_preflight")
        if self.fail_at == "runtime_preflight":
            raise RuntimeError("fake_runtime_preflight_failure")
        return {
            "sealed_interpreter_exact": True,
            "piper_version": PIPER_VERSION,
            "onnxruntime_version": "1.27.0",
            "model_sha256": MODEL_SHA256,
            "config_sha256": CONFIG_SHA256,
            "execution_provider": EXECUTION_PROVIDER,
            "voice_id": MODEL_ID,
            "output_format": OUTPUT_FORMAT,
        }

    def create_locked_runtime(self):
        self.trace.append("runtime_create")
        if self.fail_at == "runtime_create":
            raise RuntimeError("fake_runtime_failure")
        return FakeRuntime(self.trace, fail_at=self.fail_at)


class FakeExclusiveWriter:
    def __init__(self, trace, *, fail_at=None):
        self.trace = trace
        self.fail_at = fail_at
        self.calls = 0

    def write_wav_exclusive(self, wav_bytes):
        self.calls += 1
        self.trace.append(("write", len(wav_bytes)))
        if self.fail_at == "writer":
            raise RuntimeError("fake_writer_failure")
        return {
            "exclusive_create": True,
            "output_file_count": 1,
            "output_write_count": 1,
            "byte_count": len(wav_bytes),
            "sha256": hashlib.sha256(wav_bytes).hexdigest(),
        }


class FakeAuditSink:
    def __init__(self, trace, *, fail_at=None):
        self.trace = trace
        self.fail_at = fail_at
        self.authorization_records = []
        self.consumed_records = []
        self.audit_records = []

    def create_authorization_exclusive(self, record):
        self.trace.append("authorization_create")
        if self.fail_at == "authorization_create":
            raise RuntimeError("fake_authorization_create_failure")
        self.authorization_records.append(copy.deepcopy(record))

    def consume_authorization_exclusive(self, record):
        self.trace.append("authorization_consume")
        if not self.authorization_records or self.consumed_records:
            raise RuntimeError("fake_consumption_order_failure")
        if self.fail_at == "authorization_consume":
            raise RuntimeError("fake_authorization_consume_failure")
        self.consumed_records.append(copy.deepcopy(record))

    def create_audit_exclusive(self, record):
        self.trace.append("audit_create")
        if not self.consumed_records or self.audit_records:
            raise RuntimeError("fake_audit_order_failure")
        if self.fail_at == "audit_create":
            raise RuntimeError("fake_audit_failure")
        self.audit_records.append(copy.deepcopy(record))


def inner_dependencies(trace, *, fail_at=None, text=FAKE_TEXT, synthetic=True):
    return {
        "runtime_factory": FakeRuntimeFactory(trace, fail_at=fail_at),
        "exclusive_wav_writer": FakeExclusiveWriter(trace, fail_at=fail_at),
        "clock": FakeClock(
            trace,
            "inside_clock",
            fail_on_call=(
                1
                if fail_at == "inside_clock_1"
                else 2 if fail_at == "inside_clock_2" else None
            ),
        ),
        "file_system_boundary": FakeFileSystemBoundary(trace, fail_at=fail_at),
        "ephemeral_test_text_supplier": FakeTextSupplier(
            trace, fail_at=fail_at, text=text, synthetic=synthetic
        ),
    }


class FakeSealedInterpreterBoundary:
    def __init__(self, trace, audit_sink, *, fail_at=None, text=FAKE_TEXT, synthetic=True):
        self.trace = trace
        self.audit_sink = audit_sink
        self.fail_at = fail_at
        self.inner = inner_dependencies(
            trace, fail_at=fail_at, text=text, synthetic=synthetic
        )
        self.calls = 0

    def launch_canonical_once(self, source):
        self.calls += 1
        self.trace.append("sealed_launch")
        if source is not runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE:
            raise RuntimeError("noncanonical_source")
        if self.fail_at == "sealed_launch":
            raise RuntimeError("fake_launch_failure")
        if self.fail_at == "bootstrap_failure":
            return {
                "outcome": "EXECUTION_FAILED_CLOSED",
                "safe_error_category": "sealed_bootstrap_failed",
                "interface_binding": "failed_before_runner_result",
                "authorization_id": None,
                "nonce_fingerprint": None,
                "lifecycle_status": L8_AUTHORIZED_NOT_EXECUTED,
                "sealed_interpreter_process_count": 1,
                "runtime_process_count": 0,
                "session_initialization_count": 0,
                "text_input_count": 0,
                "synthesis_attempt_count": 0,
                "output_file_count": 0,
                "output_write_count": 0,
                "output_state_unknown": False,
                "retry_count": 0,
                "fallback_count": 0,
                "output_path": None,
                "output_byte_count": None,
                "output_sha256": None,
            }
        self.trace.append("authorization_read")
        record = copy.deepcopy(self.audit_sink.authorization_records[0])
        if self.fail_at == "authorization_read":
            record["model_sha256"] = "0" * 64
        result = runner_module._execute_inside_sealed_interpreter(
            durable_authorization_record=record,
            **self.inner,
        )
        if self.fail_at == "malformed_result":
            return {"outcome": "EXECUTION_FAILED_CLOSED", "raw_text": self.inner}
        serialized = {
            **{name: getattr(result, name) for name in result.__slots__},
            "interface_binding": "succeeded",
        }
        if self.fail_at == "container_result":
            serialized["interface_binding"] = ["succeeded"]
        return serialized


def dependencies(*, fail_at=None, text=FAKE_TEXT, synthetic=True):
    trace = []
    sink = FakeAuditSink(trace, fail_at=fail_at)
    launcher = FakeSealedInterpreterBoundary(
        trace, sink, fail_at=fail_at, text=text, synthetic=synthetic
    )
    return trace, {
        "clock": FakeClock(
            trace, "caller_clock", fail=fail_at == "caller_clock"
        ),
        "safe_audit_sink": sink,
        "sealed_interpreter_boundary": launcher,
    }


class L8OneTimePiperSyntheticRunnerTests(unittest.TestCase):
    def setUp(self):
        runner_module._reset_process_state_for_offline_tests()

    def test_01_valid_fake_sequence_is_exact_and_single_use(self):
        trace, deps = dependencies()
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.outcome, "ONE_SYNTHETIC_OUTPUT_CREATED")
        self.assertEqual(result.lifecycle_status, L8_AUTHORIZATION_CONSUMED)
        self.assertEqual(
            (
                result.sealed_interpreter_process_count,
                result.runtime_process_count,
                result.session_initialization_count,
                result.text_input_count,
                result.synthesis_attempt_count,
                result.output_file_count,
                result.output_write_count,
                result.retry_count,
                result.fallback_count,
            ),
            (1, 1, 1, 1, 1, 1, 1, 0, 0),
        )
        labels = [item if isinstance(item, str) else item[0] for item in trace]
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

    def test_02_durable_and_audit_records_never_retain_raw_text_or_nonce(self):
        _, deps = dependencies()
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        sink = deps["safe_audit_sink"]
        rendered = json.dumps(
            {
                "result": {name: getattr(result, name) for name in result.__slots__},
                "authorization": sink.authorization_records,
                "consumed": sink.consumed_records,
                "audit": sink.audit_records,
            },
            default=str,
        )
        self.assertNotIn(FAKE_TEXT, rendered)
        self.assertNotIn("a" * 64, rendered)
        self.assertIn("nonce_fingerprint", rendered)
        self.assertNotIn("single_use_nonce", rendered)

    def test_03_invalid_authorization_reaches_no_caller_or_inside_boundary(self):
        trace, deps = dependencies()
        authorization = valid_authorization()
        authorization["piper_version"] = "wrong"
        result = execute_one_time_piper_synthetic(authorization=authorization, **deps)
        self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
        self.assertEqual(trace, [])

    def test_04_locked_fields_and_limits_fail_before_durable_creation(self):
        cases = (
            ("schema_version", "wrong"),
            ("output_root", r"C:\Other"),
            ("output_filename", "other.wav"),
            ("model_sha256", "0" * 64),
            ("config_sha256", "0" * 64),
            ("execution_provider", "CUDAExecutionProvider"),
            ("allowed_voice_ids", ["other"]),
            ("maximum_runtime_process_count", 2),
            ("maximum_retry_count", 1),
            ("maximum_fallback_count", 1),
            ("lifecycle_status", L8_AUTHORIZATION_CONSUMED),
        )
        for field, value in cases:
            runner_module._reset_process_state_for_offline_tests()
            trace, deps = dependencies()
            authorization = valid_authorization()
            authorization[field] = value
            with self.subTest(field=field):
                result = execute_one_time_piper_synthetic(
                    authorization=authorization, **deps
                )
                self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
                self.assertEqual(trace, [])

    def test_05_c3_c4_case_script_research_channel_and_production_linkage_rejects(self):
        for field in (
            "c3_status",
            "c4_approval",
            "approved_script_path",
            "case_id",
            "real_case",
            "script",
            "research",
            "channel",
            "production",
        ):
            runner_module._reset_process_state_for_offline_tests()
            trace, deps = dependencies()
            authorization = valid_authorization()
            authorization[field] = "forbidden"
            with self.subTest(field=field):
                self.assertEqual(
                    execute_one_time_piper_synthetic(
                        authorization=authorization, **deps
                    ).outcome,
                    "EXECUTION_FAILED_CLOSED",
                )
                self.assertEqual(trace, [])

    def test_06_filesystem_failure_is_inside_launch_then_consumed_and_audited(self):
        trace, deps = dependencies(fail_at="output_preflight")
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.safe_error_category, "output_preflight_rejected")
        self.assertLess(trace.index("sealed_launch"), trace.index("output_preflight"))
        self.assertNotIn("create_root", trace)
        self.assertNotIn("runtime_preflight", trace)
        self.assertNotIn("text_supplier", trace)
        self.assertEqual(trace[-2:], ["authorization_consume", "audit_create"])

    def test_07_runtime_hash_preflight_precedes_text_and_failure_stops_there(self):
        trace, deps = dependencies(fail_at="runtime_preflight")
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.safe_error_category, "runtime_preflight_failed")
        self.assertLess(trace.index("create_root"), trace.index("runtime_preflight"))
        self.assertNotIn("text_supplier", trace)
        self.assertNotIn("runtime_create", trace)
        self.assertEqual(trace[-2:], ["authorization_consume", "audit_create"])

    def test_08_text_boundary_failure_occurs_after_root_and_hash_preflight(self):
        trace, deps = dependencies(text="wrong offline fixture")
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.safe_error_category, "text_hash_mismatch")
        self.assertLess(trace.index("runtime_preflight"), trace.index("text_supplier"))
        self.assertNotIn("runtime_create", trace)
        self.assertEqual(trace[-2:], ["authorization_consume", "audit_create"])

    def test_09_session_and_synthesis_failures_consume_and_audit_once(self):
        for stage in ("session_initialize", "synthesis"):
            runner_module._reset_process_state_for_offline_tests()
            trace, deps = dependencies(fail_at=stage)
            result = execute_one_time_piper_synthetic(
                authorization=valid_authorization(), **deps
            )
            with self.subTest(stage=stage):
                self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
                self.assertEqual(trace.count("authorization_consume"), 1)
                self.assertEqual(trace.count("audit_create"), 1)
                self.assertEqual(result.retry_count, 0)
                self.assertEqual(result.fallback_count, 0)

    def test_10_writer_failure_is_one_attempt_with_no_second_output(self):
        trace, deps = dependencies(fail_at="writer")
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.safe_error_category, "exclusive_write_failed")
        self.assertEqual(result.output_write_count, 1)
        self.assertEqual(result.output_file_count, 1)
        self.assertTrue(result.output_state_unknown)
        self.assertEqual(deps["sealed_interpreter_boundary"].inner["exclusive_wav_writer"].calls, 1)
        self.assertEqual(trace.count("authorization_consume"), 1)
        self.assertEqual(trace.count("audit_create"), 1)

    def test_11_launch_failure_after_durable_creation_is_consumed_then_audited(self):
        trace, deps = dependencies(fail_at="sealed_launch")
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.safe_error_category, "sealed_launch_failed")
        self.assertTrue(result.output_state_unknown)
        self.assertEqual(
            trace,
            [
                "caller_clock",
                "authorization_create",
                "sealed_launch",
                "authorization_consume",
                "audit_create",
            ],
        )

    def test_12_second_reuse_reset_clone_or_reissue_cannot_launch(self):
        _, deps = dependencies()
        first = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(first.lifecycle_status, L8_AUTHORIZATION_CONSUMED)
        for candidate in (
            valid_authorization(),
            copy.deepcopy(valid_authorization()),
            {**valid_authorization(), "lifecycle_status": L8_AUTHORIZED_NOT_EXECUTED},
        ):
            trace, next_deps = dependencies()
            result = execute_one_time_piper_synthetic(
                authorization=candidate, **next_deps
            )
            self.assertEqual(result.safe_error_category, "runner_already_used")
            self.assertEqual(trace, [])

    def test_13_public_api_is_caller_only_and_module_has_no_process_or_io_import(self):
        signature = inspect.signature(execute_one_time_piper_synthetic)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "authorization",
                "clock",
                "safe_audit_sink",
                "sealed_interpreter_boundary",
            ),
        )
        local_public_functions = {
            name
            for name, value in inspect.getmembers(runner_module, inspect.isfunction)
            if value.__module__ == runner_module.__name__ and not name.startswith("_")
        }
        self.assertEqual(local_public_functions, {"execute_one_time_piper_synthetic"})
        tree = ast.parse(RUNNER_SOURCE.read_text(encoding="utf-8"))
        imported_roots = {
            alias.name.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertTrue(
            imported_roots.isdisjoint(
                {"piper", "onnxruntime", "os", "subprocess", "socket", "requests"}
            )
        )

    def test_14_inner_api_has_no_lifecycle_sink_and_no_cleanup_or_mutation_path(self):
        signature = inspect.signature(runner_module._execute_inside_sealed_interpreter)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "durable_authorization_record",
                "runtime_factory",
                "exclusive_wav_writer",
                "clock",
                "file_system_boundary",
                "ephemeral_test_text_supplier",
            ),
        )
        source = RUNNER_SOURCE.read_text(encoding="utf-8")
        inner_source = source.split("def _execute_inside_sealed_interpreter", 1)[1].split(
            "def execute_one_time_piper_synthetic", 1
        )[0]
        for forbidden in (
            "create_authorization_exclusive",
            "consume_authorization_exclusive",
            "create_audit_exclusive",
            ".cleanup(",
            ".delete(",
            ".move(",
            ".rename(",
            ".overwrite(",
            ".publish(",
        ):
            self.assertNotIn(forbidden, inner_source)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L8OneTimePiperSyntheticRunnerTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        json.dumps(
            {
                "l7c_offline_runner_tests": (
                    "passed" if result.wasSuccessful() else "failed"
                ),
                "tests_run": result.testsRun,
                "real_authorizations_or_audits": 0,
                "filesystem_or_output_root_interactions": 0,
                "sealed_interpreter_launches": 0,
                "piper_or_onnx_imports": 0,
                "runtime_processes": 0,
                "model_loads": 0,
                "real_text_inputs": 0,
                "inference_or_synthesis_calls": 0,
                "audio_or_media_artifacts": 0,
                "network_or_provider_activity": 0,
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)
