from __future__ import annotations

import ast
import inspect
import json
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from providers.l6_guarded_piper_runtime import (
    FORBIDDEN_OPERATION_CATEGORIES,
    LOCKED_ASSET_ROOT,
    LOCKED_CONFIG_PATH,
    LOCKED_CONFIG_SHA256,
    LOCKED_MODEL_ID,
    LOCKED_MODEL_PATH,
    LOCKED_MODEL_SHA256,
    LOCKED_PIPER_VERSION,
    LOCKED_PROVIDER,
    L6AdapterRuntimeBindingValidator,
    GuardedPiperRuntime,
    L6BindingProbe,
    SEALED_INTERPRETER,
    exact_l6_probe,
)


AUTOMATION = Path(__file__).resolve().parent
WRAPPER_SOURCE = AUTOMATION / "providers" / "l6_guarded_piper_runtime.py"


class L6GuardedPiperAdapterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asset_inventory_before = tuple(
            sorted(item.name for item in LOCKED_ASSET_ROOT.iterdir())
        )
        cls.runtime = GuardedPiperRuntime.exact_locked()
        cls.metadata = cls.runtime.initialize_and_inspect()

    @classmethod
    def tearDownClass(cls):
        cls.asset_inventory_after = tuple(
            sorted(item.name for item in LOCKED_ASSET_ROOT.iterdir())
        )
        cls.runtime._release_at_process_exit()

    def test_01_real_runtime_health_is_cpu_only_and_metadata_only(self):
        self.assertEqual(self.metadata.active_providers, (LOCKED_PROVIDER,))
        self.assertIn(LOCKED_PROVIDER, self.metadata.available_providers)
        self.assertTrue(self.metadata.config_structure_valid)
        self.assertTrue(self.metadata.asset_inventory_unchanged)
        self.assertEqual(
            tuple(item.name for item in self.metadata.inputs),
            ("input", "input_lengths", "scales"),
        )
        self.assertEqual(
            tuple(item.name for item in self.metadata.outputs),
            ("output",),
        )
        self.assertEqual(
            GuardedPiperRuntime.process_runtime_initialization_count(), 1
        )

    def test_02_exact_l2_identity_binds_without_output_handling(self):
        validator = L6AdapterRuntimeBindingValidator(
            guarded_runtime=self.runtime
        )
        result = validator.validate_probe(exact_l6_probe())
        self.assertEqual(result.status, "bound")
        self.assertIsNone(result.safe_error_category)
        self.assertEqual(result.engine_version, LOCKED_PIPER_VERSION)
        self.assertEqual(result.model_id, LOCKED_MODEL_ID)
        self.assertEqual(result.future_output_format, "wav")
        self.assertFalse(result.output_handling_available)
        self.assertEqual(result.runtime_interaction_count, 1)

    def test_03_wrong_declared_runtime_identity_fails_before_session_load(self):
        base = {
            "interpreter_path": SEALED_INTERPRETER,
            "engine_version": LOCKED_PIPER_VERSION,
            "model_id": LOCKED_MODEL_ID,
            "model_path": LOCKED_MODEL_PATH,
            "config_path": LOCKED_CONFIG_PATH,
            "model_sha256": LOCKED_MODEL_SHA256,
            "config_sha256": LOCKED_CONFIG_SHA256,
            "provider": LOCKED_PROVIDER,
        }
        cases = (
            {"engine_version": "1.4.1"},
            {"model_id": "en_US-lessac-medium"},
            {"model_id": "en_US-ljspeech-medium"},
            {"model_path": LOCKED_ASSET_ROOT / "other.onnx"},
            {"config_path": LOCKED_ASSET_ROOT / "other.onnx.json"},
            {"model_sha256": "0" * 64},
            {"config_sha256": "f" * 64},
            {"provider": "CUDAExecutionProvider"},
        )
        for changes in cases:
            values = dict(base)
            values.update(changes)
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    GuardedPiperRuntime(**values)
                self.assertEqual(
                    GuardedPiperRuntime.process_runtime_initialization_count(),
                    1,
                )

    def test_04_wrong_l2_probe_values_fail_before_runtime_interaction(self):
        cases = (
            ({"route_identifier": "other"}, "route_mismatch"),
            ({"engine_version": "1.4.1"}, "engine_version_mismatch"),
            ({"model_id": "en_US-lessac-medium"}, "model_id_mismatch"),
            (
                {"model_id": "en_US-ljspeech-medium"},
                "model_id_mismatch",
            ),
            ({"model_source_marker": "main"}, "model_source_mismatch"),
            ({"future_output_format": "mp3"}, "future_output_format_mismatch"),
        )
        for changes, expected in cases:
            validator = L6AdapterRuntimeBindingValidator(
                guarded_runtime=self.runtime
            )
            probe = replace(exact_l6_probe(), **changes)
            result = validator.validate_probe(probe)
            with self.subTest(changes=changes):
                self.assertEqual(result.status, "rejected")
                self.assertEqual(result.safe_error_category, expected)
                self.assertEqual(result.runtime_interaction_count, 0)

    def test_05_non_fake_path_is_rejected_before_runtime_interaction(self):
        validator = L6AdapterRuntimeBindingValidator(
            guarded_runtime=self.runtime
        )
        before = self.runtime.ledger_snapshot().identity_inspections
        result = validator.validate_probe(
            replace(exact_l6_probe(), probe_kind="narration_request")
        )
        after = self.runtime.ledger_snapshot().identity_inspections
        self.assertEqual(result.safe_error_category, "non_fake_request_path")
        self.assertEqual(result.runtime_interaction_count, 0)
        self.assertEqual(before, after)

    def test_06_no_text_output_path_or_writer_surface_exists(self):
        forbidden_parameter_names = {
            "text",
            "phonemes",
            "ids",
            "tokens",
            "tensors",
            "scales",
            "input_lengths",
            "voice",
            "voice_id",
            "output_path",
            "writer",
        }
        for name, member in inspect.getmembers(
            GuardedPiperRuntime, predicate=inspect.isfunction
        ):
            if name.startswith("_"):
                continue
            parameters = set(inspect.signature(member).parameters)
            self.assertTrue(
                parameters.isdisjoint(forbidden_parameter_names),
                msg=f"unsafe public parameters on {name}",
            )

        self.assertNotIn(
            "output_path", inspect.signature(L6BindingProbe).parameters
        )
        self.assertNotIn("writer", inspect.signature(L6BindingProbe).parameters)
        with self.assertRaises(TypeError):
            L6BindingProbe(**asdict(exact_l6_probe()), output_path="blocked")
        with self.assertRaises(TypeError):
            L6AdapterRuntimeBindingValidator(
                guarded_runtime=self.runtime,
                writer=object(),
            )

    def test_07_all_inference_output_and_orchestration_operations_are_blocked(self):
        before = self.runtime.ledger_snapshot().blocked_operation_count
        for operation in FORBIDDEN_OPERATION_CATEGORIES:
            self.runtime.reject_operation(operation)
        after = self.runtime.ledger_snapshot()
        self.assertEqual(
            after.blocked_operation_count - before,
            len(FORBIDDEN_OPERATION_CATEGORIES),
        )
        self.assertEqual(after.text_inputs, 0)
        self.assertEqual(after.inference_calls, 0)
        self.assertEqual(after.synthesis_calls, 0)
        self.assertEqual(after.phonemization_calls, 0)
        self.assertEqual(after.output_writes, 0)
        self.assertTrue(
            all(count == 1 for _, count in after.blocked_by_category)
        )

    def test_08_second_runtime_initialization_is_blocked(self):
        second = GuardedPiperRuntime.exact_locked()
        with self.assertRaises(RuntimeError):
            second.initialize_and_inspect()
        self.assertEqual(
            GuardedPiperRuntime.process_runtime_initialization_count(), 1
        )
        self.assertEqual(second.ledger_snapshot().blocked_operation_count, 1)

    def test_09_no_public_inference_or_output_methods_exist(self):
        forbidden_method_names = {
            "synthesize",
            "synthesize_wav",
            "stream",
            "phonemize",
            "run",
            "run_with_iobinding",
            "write",
            "write_output",
            "retry",
            "poll",
            "enqueue",
            "start_server",
            "cleanup",
            "copy",
            "rename",
            "overwrite",
        }
        public = {
            name
            for name in dir(GuardedPiperRuntime)
            if not name.startswith("_")
        }
        self.assertTrue(public.isdisjoint(forbidden_method_names))

    def test_10_integration_has_no_production_or_provider_registry_route(self):
        tree = ast.parse(WRAPPER_SOURCE.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

        forbidden_roots = {
            "cold_truth_pipeline",
            "provider_registry",
            "subprocess",
            "socket",
            "requests",
            "httpx",
            "urllib",
            "mcp",
            "browser",
            "wave",
            "soundfile",
        }
        self.assertTrue(
            all(name.split(".")[0] not in forbidden_roots for name in imported)
        )
        source = WRAPPER_SOURCE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "production narration",
            "provider_registry",
            "upload",
            "publish",
            "elevenlabs",
        ):
            self.assertNotIn(forbidden, source)

    def test_11_ledger_contains_categories_only_and_zero_inputs_or_outputs(self):
        ledger = self.runtime.ledger_snapshot()
        rendered = json.dumps(asdict(ledger), sort_keys=True).lower()
        self.assertEqual(ledger.runtime_initializations, 1)
        self.assertGreaterEqual(ledger.identity_inspections, 1)
        self.assertEqual(ledger.text_inputs, 0)
        self.assertEqual(ledger.inference_calls, 0)
        self.assertEqual(ledger.synthesis_calls, 0)
        self.assertEqual(ledger.phonemization_calls, 0)
        self.assertEqual(ledger.output_writes, 0)
        for forbidden in (
            "credential",
            "secret",
            "api_key",
            "narration text",
            "output destination",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_12_asset_inventory_has_no_media_or_unexpected_output(self):
        current = tuple(sorted(item.name for item in LOCKED_ASSET_ROOT.iterdir()))
        self.assertEqual(current, self.asset_inventory_before)
        self.assertEqual(
            current,
            ("en_US-ljspeech-high.onnx", "en_US-ljspeech-high.onnx.json"),
        )
        self.assertFalse(
            any(
                item.suffix.lower()
                in {".wav", ".mp3", ".pcm", ".flac", ".m4a", ".ogg"}
                for item in LOCKED_ASSET_ROOT.iterdir()
            )
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L6GuardedPiperAdapterIntegrationTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    runtime = L6GuardedPiperAdapterIntegrationTests.runtime
    ledger = runtime.ledger_snapshot()
    print(
        json.dumps(
            {
                "l6_guarded_runtime_tests": (
                    "passed" if result.wasSuccessful() else "failed"
                ),
                "tests_run": result.testsRun,
                "sealed_runtime_processes": 1,
                "runtime_initializations": (
                    GuardedPiperRuntime.process_runtime_initialization_count()
                ),
                "text_inputs": ledger.text_inputs,
                "inference_calls": ledger.inference_calls,
                "synthesis_calls": ledger.synthesis_calls,
                "phonemization_calls": ledger.phonemization_calls,
                "output_writes": ledger.output_writes,
                "blocked_operations": ledger.blocked_operation_count,
                "audio_or_media_creation": "not_performed",
                "network_or_provider_activity": "not_performed",
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)

