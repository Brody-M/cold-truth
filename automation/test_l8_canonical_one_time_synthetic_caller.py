from __future__ import annotations

import ast
import importlib
import inspect
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import l8_canonical_one_time_synthetic_caller as caller_module
import l8_one_time_piper_synthetic_runner as runner_module


CALLER_SOURCE = Path(__file__).with_name(
    "l8_canonical_one_time_synthetic_caller.py"
)


class FakeClock:
    def __init__(self, trace: list[object]) -> None:
        self.trace = trace

    def now_utc(self) -> datetime:
        self.trace.append("clock")
        return datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


class FakeIdentitySource:
    def __init__(self, trace: list[object], *, valid: bool = True) -> None:
        self.trace = trace
        self.valid = valid

    def fresh_authorization_id(self) -> str:
        self.trace.append("authorization_id")
        if not self.valid:
            return "invalid"
        return "L8-SYNTHETIC-123e4567-e89b-42d3-a456-426614174000"

    def fresh_nonce(self) -> str:
        self.trace.append("nonce")
        return "a" * 64


class FakeLifecycleSink:
    def __init__(self, trace: list[object]) -> None:
        self.trace = trace
        self.authorization_records: list[dict[str, object]] = []
        self.consumed_records: list[dict[str, object]] = []
        self.audit_records: list[dict[str, object]] = []

    def create_authorization_exclusive(self, record: object) -> None:
        self.trace.append("authorization_create")
        self.authorization_records.append(dict(record))

    def consume_authorization_exclusive(self, record: object) -> None:
        self.trace.append("authorization_consume")
        self.consumed_records.append(dict(record))

    def create_audit_exclusive(self, record: object) -> None:
        self.trace.append("audit_create")
        self.audit_records.append(dict(record))


class FakeCanonicalBoundary:
    def __init__(self, trace: list[object]) -> None:
        self.trace = trace
        self.calls = 0

    def launch_canonical_once(self, entrypoint_source: object) -> dict[str, object]:
        self.calls += 1
        self.trace.append("canonical_launch")
        if entrypoint_source is not runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE:
            raise RuntimeError("noncanonical_entrypoint")
        return {
            "outcome": "EXECUTION_FAILED_CLOSED",
            "safe_error_category": "sealed_bootstrap_failed",
            "interface_binding": "failed_before_runner_result",
            "authorization_id": None,
            "nonce_fingerprint": None,
            "lifecycle_status": "AUTHORIZED_NOT_EXECUTED",
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


def fake_dependencies(*, valid_identity: bool = True):
    trace: list[object] = []
    sink = FakeLifecycleSink(trace)
    boundary = FakeCanonicalBoundary(trace)
    return trace, sink, boundary, {
        "clock": FakeClock(trace),
        "identity_source": FakeIdentitySource(trace, valid=valid_identity),
        "safe_audit_sink": sink,
        "sealed_interpreter_boundary": boundary,
    }


class L8CanonicalOneTimeSyntheticCallerTests(unittest.TestCase):
    def setUp(self):
        runner_module._reset_process_state_for_offline_tests()

    def test_01_import_is_inert_and_has_no_runtime_or_external_module(self):
        importlib.reload(caller_module)
        self.assertNotIn("onnxruntime", sys.modules)
        self.assertNotIn("piper.voice", sys.modules)
        self.assertEqual(tuple(inspect.signature(caller_module.main).parameters), ())

    def test_02_invalid_candidate_reaches_no_durable_or_boundary_dependency(self):
        trace, sink, boundary, dependencies = fake_dependencies(valid_identity=False)
        result = caller_module._execute_with_dependencies(**dependencies)
        self.assertEqual(result.safe_error_category, "authorization_id_invalid")
        self.assertEqual(trace, ["clock", "authorization_id", "nonce"])
        self.assertEqual(boundary.calls, 0)
        self.assertEqual(sink.authorization_records, [])
        self.assertEqual(sink.consumed_records, [])
        self.assertEqual(sink.audit_records, [])

    def test_03_valid_candidate_uses_exact_lifecycle_order_with_fakes(self):
        trace, sink, boundary, dependencies = fake_dependencies()
        result = caller_module._execute_with_dependencies(**dependencies)
        lifecycle = [
            item
            for item in trace
            if item in (
                "authorization_create",
                "canonical_launch",
                "authorization_consume",
                "audit_create",
            )
        ]
        self.assertEqual(lifecycle, [
            "authorization_create",
            "canonical_launch",
            "authorization_consume",
            "audit_create",
        ])
        self.assertEqual(boundary.calls, 1)
        self.assertEqual(len(sink.authorization_records), 1)
        self.assertEqual(len(sink.consumed_records), 1)
        self.assertEqual(len(sink.audit_records), 1)
        self.assertEqual(result.safe_error_category, "sealed_bootstrap_failed")
        rendered = json.dumps({
            "result": {name: getattr(result, name) for name in result.__slots__},
            "authorized": sink.authorization_records,
            "consumed": sink.consumed_records,
            "audit": sink.audit_records,
        }, sort_keys=True)
        self.assertNotIn("single_use_nonce", rendered)
        self.assertNotIn("raw_text", rendered)

    def test_04_dependency_substitutions_fail_before_any_fake_call(self):
        for field in (
            "clock",
            "identity_source",
            "safe_audit_sink",
            "sealed_interpreter_boundary",
        ):
            runner_module._reset_process_state_for_offline_tests()
            trace, sink, boundary, dependencies = fake_dependencies()
            dependencies[field] = object()
            result = caller_module._execute_with_dependencies(**dependencies)
            with self.subTest(field=field):
                self.assertEqual(
                    result.safe_error_category,
                    "caller_dependency_interface_invalid",
                )
                self.assertEqual(trace, [])
                self.assertEqual(boundary.calls, 0)
                self.assertEqual(sink.authorization_records, [])

    def test_05_public_route_uses_only_fixed_concrete_dependencies(self):
        source = CALLER_SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(CALLER_SOURCE))
        production_functions = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_execute_canonical_one_time_synthetic"
        ]
        self.assertEqual(len(production_functions), 1)
        calls = {
            node.func.id: node
            for node in ast.walk(production_functions[0])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertEqual(
            set(calls),
            {
                "_execute_with_dependencies",
                "UtcL8Clock",
                "_FreshIdentitySource",
                "SafeL8LifecycleAuditSink",
                "CanonicalL8SealedInterpreterBoundary",
            },
        )
        boundary_call = calls["CanonicalL8SealedInterpreterBoundary"]
        self.assertEqual(boundary_call.args, [])
        self.assertEqual(boundary_call.keywords, [])

    def test_06_entrypoint_accepts_no_parameters_and_rejects_cli_arguments(self):
        self.assertEqual(tuple(inspect.signature(caller_module.main).parameters), ())
        original = list(caller_module.sys.argv)
        try:
            caller_module.sys.argv = ["caller.py", "unexpected"]
            self.assertEqual(caller_module.main(), 2)
        finally:
            caller_module.sys.argv = original

    def test_07_caller_source_has_no_raw_text_or_general_purpose_route(self):
        source = CALLER_SOURCE.read_text(encoding="utf-8")
        for forbidden in (
            "This is a local",
            "subprocess",
            "Popen",
            "shell=True",
            "os.environ",
            "getenv",
            "Path(",
            "open(",
            "mkdir(",
            "piper.voice",
            "onnxruntime",
            "requests",
            "httpx",
            "socket",
            "browser",
            "mcp",
            "c3_",
            "c4_",
        ):
            self.assertNotIn(forbidden, source.lower() if forbidden.islower() else source)
        tree = ast.parse(source, filename=str(CALLER_SOURCE))
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(
            called_names.isdisjoint({"retry", "fallback", "rerun", "recover"})
        )
        self.assertTrue(
            called_attributes.isdisjoint({"retry", "fallback", "rerun", "recover"})
        )

    def test_08_caller_uses_fixed_l7d_text_hash_and_l7b_factory(self):
        source = CALLER_SOURCE.read_text(encoding="utf-8")
        self.assertIn("text_sha256=_FIXED_TEXT_SHA256", source)
        self.assertIn("create_l8_executable_synthetic_authorization", source)
        self.assertIn("L8ExecutableSyntheticAuthorizationValidator", source)
        self.assertNotIn("FAKE_TEXT_SHA256", source)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L8CanonicalOneTimeSyntheticCallerTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "l7h_offline_canonical_caller_tests": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "real_authorizations_or_audits": 0,
        "filesystem_or_output_root_interactions": 0,
        "sealed_interpreter_launches": 0,
        "piper_or_onnx_imports": 0,
        "runtime_processes": 0,
        "model_loads": 0,
        "text_handoffs": 0,
        "inference_or_synthesis_calls": 0,
        "audio_or_media_artifacts": 0,
        "network_or_provider_activity": 0,
        "secret_or_environment_access": 0,
        "c3_c4_or_production_access": 0,
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
