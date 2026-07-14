from __future__ import annotations

import ast
import copy
import inspect
import json
import sys
import unittest
from pathlib import Path


_RUNTIME_MODULES_BEFORE_IMPORT = {
    name for name in sys.modules if name == "onnxruntime" or name.startswith("piper")
}
import l8_local_dependency_adapters as adapters
_RUNTIME_MODULES_AFTER_IMPORT = {
    name for name in sys.modules if name == "onnxruntime" or name.startswith("piper")
}

import l8_one_time_piper_synthetic_runner as runner_module
from l7_piper_synthetic_authorization_contract import (
    L8_AUTHORIZATION_CONSUMED,
    L8_AUTHORIZED_NOT_EXECUTED,
)
from l8_one_time_piper_synthetic_runner import execute_one_time_piper_synthetic
from test_l8_one_time_piper_synthetic_runner import dependencies, valid_authorization


AUTOMATION = Path(__file__).resolve().parent
ADAPTER_SOURCE = AUTOMATION / "l8_local_dependency_adapters.py"


class L8LocalDependencyAdapterTests(unittest.TestCase):
    def setUp(self):
        runner_module._reset_process_state_for_offline_tests()

    def test_01_module_import_is_inert_and_imports_no_piper_or_onnx(self):
        self.assertEqual(
            _RUNTIME_MODULES_AFTER_IMPORT - _RUNTIME_MODULES_BEFORE_IMPORT,
            set(),
        )
        self.assertNotIn("onnxruntime", adapters.__dict__)
        self.assertNotIn("PiperVoice", adapters.__dict__)

    def test_02_exact_adapter_interfaces_are_minimal(self):
        cases = (
            (
                adapters.CanonicalL8FileSystemBoundary(),
                ("preflight_output_absent", "create_root_exclusive"),
            ),
            (
                adapters.CanonicalL8DurableAuthorizationReader(),
                ("read_authorization_once",),
            ),
            (
                adapters.SafeL8LifecycleAuditSink(),
                (
                    "create_authorization_exclusive",
                    "consume_authorization_exclusive",
                    "create_audit_exclusive",
                ),
            ),
            (
                adapters.FixedEphemeralSyntheticTextSupplier(),
                ("supply_ephemeral_text_once",),
            ),
            (adapters.UtcL8Clock(), ("now_utc",)),
            (
                adapters.LockedLocalPiperRuntimeFactory(),
                ("preflight_locked_runtime", "create_locked_runtime"),
            ),
            (
                adapters.CanonicalExclusiveWavWriter(),
                ("write_wav_exclusive",),
            ),
        )
        for value, methods in cases:
            with self.subTest(adapter=type(value).__name__):
                self.assertTrue(runner_module._has_exact_interface(value, methods))

    def test_03_constructors_accept_no_paths_options_or_dependencies(self):
        for adapter_type in (
            adapters.CanonicalL8FileSystemBoundary,
            adapters.CanonicalL8DurableAuthorizationReader,
            adapters.SafeL8LifecycleAuditSink,
            adapters.FixedEphemeralSyntheticTextSupplier,
            adapters.UtcL8Clock,
            adapters.LockedLocalPiperRuntimeFactory,
            adapters.CanonicalExclusiveWavWriter,
        ):
            with self.subTest(adapter=adapter_type.__name__):
                self.assertEqual(tuple(inspect.signature(adapter_type).parameters), ())

    def test_04_filesystem_boundary_remains_path_bound_and_caller_cannot_invoke_it(self):
        boundary = adapters.CanonicalL8FileSystemBoundary()
        self.assertEqual(tuple(inspect.signature(boundary.preflight_output_absent).parameters), ())
        self.assertEqual(tuple(inspect.signature(boundary.create_root_exclusive).parameters), ())
        with self.assertRaises(TypeError):
            boundary.preflight_output_absent(r"C:\Other", "other.wav")
        with self.assertRaises(TypeError):
            boundary.create_root_exclusive(r"C:\Other")
        caller_parameters = inspect.signature(
            execute_one_time_piper_synthetic
        ).parameters
        self.assertNotIn("file_system_boundary", caller_parameters)

    def test_05_durable_reader_is_parameterless_one_shot_and_has_no_path_selector(self):
        reader = adapters.CanonicalL8DurableAuthorizationReader()
        self.assertEqual(tuple(inspect.signature(reader.read_authorization_once).parameters), ())
        with self.assertRaises(TypeError):
            reader.read_authorization_once(r"C:\Other")
        source = ADAPTER_SOURCE.read_text(encoding="utf-8")
        section = source.split("class CanonicalL8DurableAuthorizationReader", 1)[1].split(
            "class SafeL8LifecycleAuditSink", 1
        )[0]
        self.assertIn("_AUTHORIZATION_ROOT", section)
        self.assertIn("authorization_root_entry_count_invalid", section)
        self.assertNotIn("glob(", section)
        self.assertNotIn("rglob(", section)

    def test_06_writer_is_path_bound_and_rejects_nonbytes_before_io(self):
        writer = adapters.CanonicalExclusiveWavWriter()
        self.assertEqual(
            tuple(inspect.signature(writer.write_wav_exclusive).parameters),
            ("wav_bytes",),
        )
        with self.assertRaises(TypeError):
            writer.write_wav_exclusive(r"C:\Other", b"fake")
        with self.assertRaisesRegex(ValueError, "wav_payload_invalid"):
            writer.write_wav_exclusive("not-bytes")

    def test_07_fixed_text_supplier_rejects_wrong_hash_without_releasing_text(self):
        supplier = adapters.FixedEphemeralSyntheticTextSupplier()
        with self.assertRaisesRegex(ValueError, "expected_text_hash_mismatch"):
            supplier.supply_ephemeral_text_once("0" * 64)
        self.assertFalse(supplier._used)

    def test_08_expanded_durable_record_is_complete_and_nonce_fingerprint_only(self):
        record = runner_module._safe_authorization_record(
            valid_authorization(), L8_AUTHORIZED_NOT_EXECUTED
        )
        validated = adapters._validate_authorization_record(
            record, L8_AUTHORIZED_NOT_EXECUTED
        )
        self.assertEqual(validated, record)
        self.assertNotIn("single_use_nonce", record)
        self.assertIn("nonce_fingerprint", record)
        for field in (
            "schema_version",
            "synthetic_test_only",
            "non_case_text_only",
            "no_personal_data",
            "allowed_voice_ids",
            "authorization_root",
            "audit_root",
            "output_root",
            "output_filename",
            "output_path",
            "exclusive_create_only",
            "disallow_output_mutation",
        ):
            self.assertIn(field, record)

    def test_09_lifecycle_sink_rejects_raw_text_nonce_and_unknown_fields_before_io(self):
        safe = runner_module._safe_authorization_record(
            valid_authorization(), L8_AUTHORIZED_NOT_EXECUTED
        )
        for field in (
            "text",
            "raw_text",
            "single_use_nonce",
            "secret",
            "environment",
            "c3_status",
            "c4_approval",
            "case_id",
            "script",
            "production",
            "unexpected",
        ):
            sink = adapters.SafeL8LifecycleAuditSink()
            record = copy.deepcopy(safe)
            record[field] = "forbidden"
            with self.subTest(field=field), self.assertRaisesRegex(
                ValueError, "authorization_record_shape_invalid"
            ):
                sink.create_authorization_exclusive(record)
            self.assertFalse(sink._authorization_created)
            self.assertTrue(sink._authorization_create_attempted)

    def test_10_audit_allowlist_rejects_raw_unknown_and_unsafe_metadata(self):
        durable = runner_module._safe_authorization_record(
            valid_authorization(), L8_AUTHORIZATION_CONSUMED
        )
        base = runner_module._safe_audit_payload(
            durable,
            "EXECUTION_FAILED_CLOSED",
            {
                "runtime_process": 0,
                "session_initialization": 0,
                "text_input": 0,
                "synthesis_attempt": 0,
                "output_file": 0,
                "output_write": 0,
            },
            "runtime_preflight_failed",
            None,
            None,
            None,
        )
        self.assertEqual(adapters._validate_audit_record(base), base)
        for field in ("raw_text", "single_use_nonce", "secret", "c3_artifact", "case_id", "unexpected"):
            record = copy.deepcopy(base)
            record[field] = "forbidden"
            with self.subTest(field=field), self.assertRaisesRegex(
                ValueError, "audit_record_shape_invalid"
            ):
                adapters._validate_audit_record(record)

        arbitrary_category = copy.deepcopy(base)
        arbitrary_category["failure_category"] = "arbitrary_but_well_formed"
        with self.assertRaisesRegex(ValueError, "audit_failure_category_invalid"):
            adapters._validate_audit_record(arbitrary_category)

        unknown = runner_module._safe_audit_payload(
            durable,
            "EXECUTION_FAILED_CLOSED",
            {
                "runtime_process": 1,
                "session_initialization": 1,
                "text_input": 1,
                "synthesis_attempt": 1,
                "output_file": 1,
                "output_write": 1,
            },
            "sealed_result_invalid",
            str(adapters._OUTPUT_PATH),
            None,
            None,
            True,
        )
        self.assertEqual(adapters._validate_audit_record(unknown), unknown)

        writer_unknown = copy.deepcopy(unknown)
        writer_unknown["failure_category"] = "exclusive_write_failed"
        self.assertEqual(
            adapters._validate_audit_record(writer_unknown), writer_unknown
        )

    def test_11_runtime_preflight_is_required_before_runtime_construction(self):
        factory = adapters.LockedLocalPiperRuntimeFactory()
        self.assertEqual(
            tuple(inspect.signature(factory.preflight_locked_runtime).parameters), ()
        )
        self.assertEqual(
            tuple(inspect.signature(factory.create_locked_runtime).parameters), ()
        )
        with self.assertRaisesRegex(RuntimeError, "runtime_factory_not_permitted"):
            factory.create_locked_runtime()
        source = ADAPTER_SOURCE.read_text(encoding="utf-8")
        preflight = source.split("def preflight_locked_runtime", 1)[1].split(
            "def create_locked_runtime", 1
        )[0]
        self.assertIn("MODEL_SHA256", preflight)
        self.assertIn("CONFIG_SHA256", preflight)
        self.assertNotIn('import_module("piper.voice")', preflight)

    def test_12_runtime_imports_remain_lazy_and_absent_at_module_import(self):
        tree = ast.parse(ADAPTER_SOURCE.read_text(encoding="utf-8"))
        top_level_imports = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_level_imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_level_imports.add(node.module.split(".")[0])
        self.assertTrue(top_level_imports.isdisjoint({"piper", "onnxruntime"}))
        self.assertNotIn("piper.voice", sys.modules)
        self.assertNotIn("onnxruntime", sys.modules)

    def test_13_valid_flow_uses_only_fakes_in_l7f_order(self):
        trace, deps = dependencies()
        result = execute_one_time_piper_synthetic(
            authorization=valid_authorization(), **deps
        )
        self.assertEqual(result.outcome, "ONE_SYNTHETIC_OUTPUT_CREATED")
        labels = [item if isinstance(item, str) else item[0] for item in trace]
        self.assertLess(labels.index("authorization_create"), labels.index("sealed_launch"))
        self.assertLess(labels.index("sealed_launch"), labels.index("output_preflight"))
        self.assertLess(labels.index("create_root"), labels.index("runtime_preflight"))
        self.assertLess(labels.index("runtime_preflight"), labels.index("text_supplier"))
        self.assertLess(labels.index("authorization_consume"), labels.index("audit_create"))

    def test_14_invalid_authorization_reaches_no_fake_dependency(self):
        trace, deps = dependencies()
        authorization = valid_authorization()
        authorization["piper_version"] = "wrong"
        result = execute_one_time_piper_synthetic(authorization=authorization, **deps)
        self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
        self.assertEqual(trace, [])

    def test_15_post_create_failures_consume_then_audit_without_retry(self):
        for stage in ("sealed_launch", "output_preflight", "runtime_preflight", "writer"):
            runner_module._reset_process_state_for_offline_tests()
            trace, deps = dependencies(fail_at=stage)
            result = execute_one_time_piper_synthetic(
                authorization=valid_authorization(), **deps
            )
            with self.subTest(stage=stage):
                self.assertEqual(result.outcome, "EXECUTION_FAILED_CLOSED")
                self.assertEqual(trace.count("authorization_consume"), 1)
                self.assertEqual(trace.count("audit_create"), 1)
                self.assertLess(trace.index("authorization_consume"), trace.index("audit_create"))
                self.assertEqual(result.retry_count, 0)
                self.assertEqual(result.fallback_count, 0)

    def test_16_no_raw_text_in_fake_result_lifecycle_audit_or_adapter_source(self):
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
        self.assertNotIn("Offline synthetic fixture only", rendered)
        source = ADAPTER_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("This is a local synthetic speech test", source)

    def test_17_no_forbidden_general_purpose_capabilities_exist(self):
        source = ADAPTER_SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = set()
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertTrue(
            imported_roots.isdisjoint(
                {"subprocess", "socket", "requests", "httpx", "urllib", "browser", "mcp"}
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {"getenv", "system", "Popen", "run", "glob", "rglob", "unlink", "remove", "rmdir", "rename", "replace", "copy", "move"}
            )
        )
        lowered = source.lower()
        for forbidden in ("os.environ", "api_key", "credential", "c3_artifact", "c4_artifact"):
            self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L8LocalDependencyAdapterTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        json.dumps(
            {
                "l7d_offline_dependency_adapter_tests": (
                    "passed" if result.wasSuccessful() else "failed"
                ),
                "tests_run": result.testsRun,
                "real_authorizations_or_audits": 0,
                "filesystem_or_output_root_interactions": 0,
                "sealed_interpreter_launches": 0,
                "piper_or_onnx_imports": 0,
                "runtime_processes": 0,
                "model_loads": 0,
                "real_text_handoffs": 0,
                "inference_or_synthesis_calls": 0,
                "audio_or_media_artifacts": 0,
                "network_or_provider_activity": 0,
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)
