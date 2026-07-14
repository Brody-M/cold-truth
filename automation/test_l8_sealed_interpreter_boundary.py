from __future__ import annotations

import ast
import importlib
import json
import sys
import unittest
from pathlib import Path

import l8_sealed_interpreter_boundary as boundary_module
import l8_one_time_piper_synthetic_runner as runner_module


BOUNDARY_SOURCE = Path(__file__).with_name("l8_sealed_interpreter_boundary.py")


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout


class FakeFixedProcessLauncher:
    def __init__(self, *, result: object | None = None, raises: bool = False) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.result = result
        self.raises = raises

    def launch_fixed_once(self, command: tuple[str, str, str]) -> object:
        self.calls.append(command)
        if self.raises:
            raise RuntimeError("untrusted fake failure detail")
        if self.result is None:
            return _FakeCompletedProcess(
                returncode=0,
                stdout=json.dumps(valid_child_result(), sort_keys=True),
            )
        return self.result


def valid_child_result() -> dict[str, object]:
    return {
        "outcome": "EXECUTION_FAILED_CLOSED",
        "safe_error_category": "text_hash_mismatch",
        "interface_binding": "succeeded",
        "authorization_id": "L8-SYNTHETIC-123e4567-e89b-42d3-a456-426614174000",
        "nonce_fingerprint": "a" * 64,
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


class L8SealedInterpreterBoundaryTests(unittest.TestCase):
    def test_01_import_is_inert_and_has_no_runtime_modules(self):
        importlib.reload(boundary_module)
        self.assertNotIn("onnxruntime", sys.modules)
        self.assertNotIn("piper.voice", sys.modules)
        self.assertFalse(boundary_module.CanonicalL8SealedInterpreterBoundary()._launch_claimed)

    def test_02_valid_fake_launch_uses_only_fixed_interpreter_and_entrypoint(self):
        launcher = FakeFixedProcessLauncher()
        boundary = boundary_module.CanonicalL8SealedInterpreterBoundary(
            process_launcher=launcher
        )
        result = boundary.launch_canonical_once(
            runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
        )
        self.assertEqual(launcher.calls, [
            (
                r"C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe",
                "-c",
                runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE,
            )
        ])
        self.assertEqual(result, valid_child_result())

    def test_03_invalid_entrypoint_and_overrides_cannot_reach_fake_launcher(self):
        launcher = FakeFixedProcessLauncher()
        boundary = boundary_module.CanonicalL8SealedInterpreterBoundary(
            process_launcher=launcher
        )
        for value in (
            None,
            "alternate source",
            runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE + " ",
            (runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE,),
        ):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    boundary.launch_canonical_once(value)
        self.assertEqual(launcher.calls, [])
        with self.assertRaises(TypeError):
            boundary.launch_canonical_once(
                runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE,
                interpreter="alternate",
            )
        self.assertEqual(launcher.calls, [])
        with self.assertRaises(ValueError):
            boundary_module.CanonicalL8SealedInterpreterBoundary(
                process_launcher=object()
            )

    def test_04_second_call_rejects_before_fake_launcher(self):
        launcher = FakeFixedProcessLauncher()
        boundary = boundary_module.CanonicalL8SealedInterpreterBoundary(
            process_launcher=launcher
        )
        boundary.launch_canonical_once(runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE)
        with self.assertRaisesRegex(RuntimeError, "sealed_boundary_already_used"):
            boundary.launch_canonical_once(runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE)
        self.assertEqual(len(launcher.calls), 1)

    def test_05_launcher_failure_is_safe_single_attempt_without_raw_detail(self):
        launcher = FakeFixedProcessLauncher(raises=True)
        boundary = boundary_module.CanonicalL8SealedInterpreterBoundary(
            process_launcher=launcher
        )
        result = boundary.launch_canonical_once(runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE)
        self.assertEqual(result["safe_error_category"], "sealed_bootstrap_failed")
        self.assertEqual(len(launcher.calls), 1)
        self.assertNotIn("untrusted fake failure detail", json.dumps(result, sort_keys=True))

    def test_06_nonzero_or_unsafe_fake_result_is_reduced_to_safe_bootstrap_failure(self):
        cases = (
            _FakeCompletedProcess(returncode=1, stdout="ignored"),
            _FakeCompletedProcess(returncode=0, stdout="not json"),
            _FakeCompletedProcess(
                returncode=0,
                stdout=json.dumps({"raw_text": "not permitted"}),
            ),
        )
        for completed in cases:
            launcher = FakeFixedProcessLauncher(result=completed)
            boundary = boundary_module.CanonicalL8SealedInterpreterBoundary(
                process_launcher=launcher
            )
            with self.subTest(returncode=completed.returncode):
                result = boundary.launch_canonical_once(
                    runner_module._SEALED_INTERPRETER_ENTRYPOINT_SOURCE
                )
                self.assertEqual(result["safe_error_category"], "sealed_bootstrap_failed")
                self.assertEqual(len(launcher.calls), 1)
                self.assertNotIn("raw_text", json.dumps(result, sort_keys=True))

    def test_07_source_has_one_fixed_nonshell_process_route_and_no_other_capability(self):
        source = BOUNDARY_SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(BOUNDARY_SOURCE))
        top_level_imports = {
            alias.name.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn("subprocess", top_level_imports)
        self.assertNotIn("os", top_level_imports)
        self.assertNotIn("socket", top_level_imports)
        self.assertNotIn("requests", top_level_imports)
        self.assertNotIn("piper", top_level_imports)
        self.assertNotIn("onnxruntime", top_level_imports)
        self.assertEqual(source.count("subprocess.run("), 1)
        self.assertIn("shell=False", source)
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("Path", called_names)
        for forbidden in (
            "Popen(", "shell=True", "os.environ", "env=", "cwd=", "cmd.exe",
            "powershell", "piper.voice", "onnxruntime", "create_authorization",
            "consume_authorization", "create_audit", "write_wav", "synthesize",
            "supply_ephemeral_text", "open(", "mkdir("
        ):
            self.assertNotIn(forbidden, source)

    def test_08_public_boundary_shape_and_l7c_l7f_order_contract_remain_exact(self):
        public_methods = {
            name
            for name, member in boundary_module.CanonicalL8SealedInterpreterBoundary.__dict__.items()
            if not name.startswith("_") and callable(member)
        }
        self.assertEqual(public_methods, {"launch_canonical_once"})
        runner_source = Path(runner_module.__file__).read_text(encoding="utf-8")
        runner_tree = ast.parse(runner_source, filename=str(runner_module.__file__))
        execution_functions = [
            node
            for node in runner_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "execute_one_time_piper_synthetic"
        ]
        self.assertEqual(len(execution_functions), 1)
        execution_function = execution_functions[0]
        expected_calls = (
            ("safe_audit_sink", "create_authorization_exclusive"),
            ("sealed_interpreter_boundary", "launch_canonical_once"),
            ("safe_audit_sink", "consume_authorization_exclusive"),
            ("safe_audit_sink", "create_audit_exclusive"),
        )
        call_lines = {target: [] for target in expected_calls}
        for node in ast.walk(execution_function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
            ):
                target = (node.func.value.id, node.func.attr)
                if target in call_lines:
                    call_lines[target].append(node.lineno)
        self.assertEqual(
            {target: len(lines) for target, lines in call_lines.items()},
            {target: 1 for target in expected_calls},
        )
        ordered_lines = [call_lines[target][0] for target in expected_calls]
        self.assertEqual(ordered_lines, sorted(ordered_lines))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L8SealedInterpreterBoundaryTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "l7g_offline_sealed_boundary_tests": "passed" if result.wasSuccessful() else "failed",
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
