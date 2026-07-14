from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest


_RUNTIME_MODULES_BEFORE_IMPORT = {
    name for name in sys.modules if name == "onnxruntime" or name.startswith("piper")
}
import l8_one_time_piper_synthetic_runner as runner_module
import l8_local_dependency_adapters as adapter_module
_RUNTIME_MODULES_AFTER_IMPORT = {
    name for name in sys.modules if name == "onnxruntime" or name.startswith("piper")
}


class L8SealedInterpreterParseabilityTests(unittest.TestCase):
    def test_01_canonical_future_entrypoint_parses_without_execution(self):
        source = runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        self.assertIs(
            compile(
                source,
                "<l8-sealed-entrypoint>",
                "exec",
                flags=ast.PyCF_ONLY_AST,
                dont_inherit=True,
            ).__class__,
            ast.Module,
        )
        self.assertFalse(runner_module._process_execution_claimed)

    def test_02_exact_validator_accepts_only_the_canonical_source(self):
        source = runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        self.assertIs(
            runner_module._validate_sealed_interpreter_entrypoint_source(source),
            source,
        )
        for candidate in (None, "", source + "\n# mutation", source[:-1]):
            with self.subTest(candidate_type=type(candidate).__name__):
                with self.assertRaisesRegex(
                    ValueError, "sealed_entrypoint_source_mismatch"
                ):
                    runner_module._validate_sealed_interpreter_entrypoint_source(
                        candidate
                    )

    def test_03_prior_sanitized_hash_assignment_reproduces_parse_failure(self):
        safe_hash = "7bf2ac457b61fd5e9dc260adec980f39a3d9a6e76ec9f2e449000c04cf70828b"
        malformed = "text_sha256 = " + safe_hash
        with self.assertRaises(SyntaxError) as caught:
            ast.parse(malformed, filename="<prior-sanitized-fragment>", mode="exec")
        self.assertEqual(caught.exception.lineno, 1)
        self.assertEqual(caught.exception.msg, "invalid decimal literal")

    def test_04_repaired_source_uses_no_native_double_quote_characters(self):
        source = runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        self.assertNotIn('"', source)
        projected = source.replace('"', "")
        self.assertEqual(projected, source)
        self.assertIsInstance(ast.parse(projected, mode="exec"), ast.Module)

    def test_05_import_is_inert_and_adds_no_piper_onnx_or_tts_module(self):
        self.assertEqual(
            _RUNTIME_MODULES_AFTER_IMPORT - _RUNTIME_MODULES_BEFORE_IMPORT,
            set(),
        )
        self.assertNotIn("onnxruntime", runner_module.__dict__)
        self.assertNotIn("PiperVoice", runner_module.__dict__)
        self.assertNotIn("onnxruntime", adapter_module.__dict__)
        self.assertNotIn("PiperVoice", adapter_module.__dict__)

    def test_06_parseability_path_cannot_execute_project_entrypoint(self):
        source = runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        before = runner_module._process_execution_claimed
        tree = ast.parse(source, mode="exec")
        after = runner_module._process_execution_claimed
        self.assertIsInstance(tree, ast.Module)
        self.assertFalse(before)
        self.assertFalse(after)

    def test_07_entrypoint_contains_no_raw_text_or_external_input_route(self):
        source = runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        self.assertIn("CanonicalL8DurableAuthorizationReader", source)
        self.assertIn("read_authorization_once()", source)
        self.assertNotIn("_FIXED_TEXT_UTF8", source)
        lowered = source.lower()
        for forbidden in (
            "input(",
            "open(",
            "clipboard",
            "os.environ",
            "getenv",
            "sys.argv",
            "requests",
            "socket",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_08_entrypoint_has_no_shell_process_network_or_fallback_api(self):
        tree = ast.parse(
            runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE, mode="exec"
        )
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
                {
                    "subprocess",
                    "socket",
                    "requests",
                    "httpx",
                    "urllib",
                    "browser",
                    "mcp",
                    "piper",
                    "onnxruntime",
                }
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "exec",
                    "eval",
                    "open",
                    "system",
                    "Popen",
                    "run",
                    "getenv",
                }
            )
        )

    def test_09_public_l7c_and_l7d_interfaces_are_l7f_aligned(self):
        self.assertEqual(
            tuple(
                inspect.signature(
                    runner_module.execute_one_time_piper_synthetic
                ).parameters
            ),
            (
                "authorization",
                "clock",
                "safe_audit_sink",
                "sealed_interpreter_boundary",
            ),
        )
        expected = (
            (adapter_module.CanonicalL8FileSystemBoundary, ("preflight_output_absent", "create_root_exclusive")),
            (adapter_module.CanonicalL8DurableAuthorizationReader, ("read_authorization_once",)),
            (adapter_module.SafeL8LifecycleAuditSink, ("create_authorization_exclusive", "consume_authorization_exclusive", "create_audit_exclusive")),
            (adapter_module.FixedEphemeralSyntheticTextSupplier, ("supply_ephemeral_text_once",)),
            (adapter_module.UtcL8Clock, ("now_utc",)),
            (adapter_module.LockedLocalPiperRuntimeFactory, ("preflight_locked_runtime", "create_locked_runtime")),
            (adapter_module.CanonicalExclusiveWavWriter, ("write_wav_exclusive",)),
        )
        for adapter_type, methods in expected:
            value = adapter_type()
            with self.subTest(adapter=adapter_type.__name__):
                self.assertTrue(runner_module._has_exact_interface(value, methods))

    def test_10_prior_authorization_is_not_embedded_reset_or_reused(self):
        source = runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        lowered = source.lower()
        self.assertNotIn("uuid", lowered)
        self.assertNotIn("secrets", lowered)
        self.assertNotIn("single_use_nonce", lowered)
        self.assertNotIn("create_l8_executable_synthetic_authorization", source)
        self.assertIn("read_authorization_once()", source)
        for forbidden in (
            "authorization_reset",
            "reuse_authorization",
            "clone_authorization",
            "reissue_authorization",
            "prior_authorization_id",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_11_l7e_test_module_has_no_launch_or_external_capability(self):
        module_globals = vars(sys.modules[__name__])
        for forbidden in (
            "subprocess",
            "socket",
            "requests",
            "httpx",
            "urllib",
            "browser",
            "mcp",
            "piper",
            "onnxruntime",
        ):
            self.assertNotIn(forbidden, module_globals)
        self.assertFalse(runner_module._process_execution_claimed)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L8SealedInterpreterParseabilityTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        json.dumps(
            {
                "l7e_offline_parseability_tests": (
                    "passed" if result.wasSuccessful() else "failed"
                ),
                "tests_run": result.testsRun,
                "sealed_interpreter_launches": 0,
                "l8_authorizations_or_audits": 0,
                "filesystem_or_output_root_interactions": 0,
                "piper_or_onnx_imports": 0,
                "runtime_processes": 0,
                "model_loads": 0,
                "text_handoffs": 0,
                "inference_or_synthesis_calls": 0,
                "audio_or_media_artifacts": 0,
                "network_or_provider_activity": 0,
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)
