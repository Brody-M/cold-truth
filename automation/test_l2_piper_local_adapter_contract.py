from __future__ import annotations

import ast
import json
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from providers.piper_local_adapter_contract import (
    FAKE_TEST_MARKER,
    FAKE_TEXT_PREFIX,
    LOCKED_ENGINE_VERSION,
    LOCKED_MODEL_ID,
    LOCKED_MODEL_SOURCE_MARKER,
    MAXIMUM_INPUT_CHARACTERS,
    ROUTE_IDENTIFIER,
    SUPPORTED_FUTURE_OUTPUT_FORMAT,
    PiperLocalAdapterContract,
    PiperSafeAudit,
    PiperSynthesisRequest,
    PiperSynthesisResult,
)
from testing.l2_fake_piper_transport import (
    DETERMINISTIC_NON_AUDIO_BYTES,
    L2FakeExclusiveCreateWriter,
    L2FakePiperTransport,
)


AUTOMATION = Path(__file__).resolve().parent
OUTPUT_NAME = "l2_fake_piper_output.l2fixture"


class Harness:
    def __init__(self, *, transport=None, writer_options=None):
        self.temp = tempfile.TemporaryDirectory(prefix="cold_truth_l2_")
        self.root = Path(self.temp.name)
        self.transport = transport or L2FakePiperTransport()
        self.writer = L2FakeExclusiveCreateWriter(
            workspace_root=self.root,
            exact_relative_path=OUTPUT_NAME,
            **(writer_options or {}),
        )
        self.adapter = PiperLocalAdapterContract(
            transport=self.transport,
            exclusive_writer=self.writer,
            isolated_workspace=self.root,
            exact_output_relative_path=OUTPUT_NAME,
        )

    def close(self):
        self.temp.cleanup()

    def request(self, **changes):
        values = {
            "text": FAKE_TEXT_PREFIX
            + "A deterministic synthetic Piper contract sentence.",
            "route_identifier": ROUTE_IDENTIFIER,
            "engine_version": LOCKED_ENGINE_VERSION,
            "model_id": LOCKED_MODEL_ID,
            "model_source_marker": LOCKED_MODEL_SOURCE_MARKER,
            "output_format": SUPPORTED_FUTURE_OUTPUT_FORMAT,
            "output_relative_path": OUTPUT_NAME,
            "maximum_input_characters": MAXIMUM_INPUT_CHARACTERS,
            "fake_test_marker": FAKE_TEST_MARKER,
        }
        values.update(changes)
        return PiperSynthesisRequest(**values)


class L2PiperLocalAdapterContractTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()

    def tearDown(self):
        self.h.close()

    def test_01_happy_path_calls_fake_transport_and_writer_once(self):
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output_path, OUTPUT_NAME)
        self.assertEqual(result.byte_count, len(DETERMINISTIC_NON_AUDIO_BYTES))
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 1)
        self.assertEqual(
            (self.h.root / OUTPUT_NAME).read_bytes(),
            DETERMINISTIC_NON_AUDIO_BYTES,
        )

    def test_02_route_version_model_and_source_are_exact(self):
        cases = (
            ({"route_identifier": "local_piper_other"}, "invalid_route_identifier"),
            ({"engine_version": "1.4.1"}, "invalid_engine_version"),
            ({"model_id": "en_US-ljspeech-medium"}, "invalid_model_id"),
            ({"model_source_marker": "main"}, "invalid_model_source_marker"),
        )
        for changes, category in cases:
            h = Harness()
            try:
                result = h.adapter.execute(h.request(**changes))
                with self.subTest(category=category):
                    self.assertEqual(result.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
                    self.assertEqual(h.writer.call_count, 0)
            finally:
                h.close()

    def test_03_every_other_piper_voice_is_rejected_before_transport(self):
        for model_id in (
            "en_US-lessac-high",
            "en_US-lessac-medium",
            "en_US-amy-medium",
            "en_US-ljspeech-medium",
            "",
            None,
        ):
            h = Harness()
            try:
                result = h.adapter.execute(h.request(model_id=model_id))
                with self.subTest(model_id=model_id):
                    self.assertEqual(result.safe_error_category, "invalid_model_id")
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_04_empty_oversized_or_nonfake_text_fails_before_transport(self):
        cases = (
            ("", "invalid_text"),
            (FAKE_TEXT_PREFIX + "   ", "invalid_text"),
            ("ordinary narration text", "invalid_text"),
            (FAKE_TEXT_PREFIX + ("x" * MAXIMUM_INPUT_CHARACTERS), "text_too_long"),
            (123, "invalid_text"),
        )
        for text, category in cases:
            h = Harness()
            try:
                result = h.adapter.execute(h.request(text=text))
                with self.subTest(category=category):
                    self.assertEqual(result.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_05_fake_marker_and_declared_length_are_exact(self):
        cases = (
            ({"fake_test_marker": ""}, "missing_fake_test_marker"),
            ({"fake_test_marker": "other"}, "missing_fake_test_marker"),
            ({"maximum_input_characters": 0}, "invalid_maximum_input_length"),
            (
                {"maximum_input_characters": MAXIMUM_INPUT_CHARACTERS + 1},
                "invalid_maximum_input_length",
            ),
            ({"maximum_input_characters": True}, "invalid_maximum_input_length"),
        )
        for changes, category in cases:
            h = Harness()
            try:
                result = h.adapter.execute(h.request(**changes))
                with self.subTest(category=category):
                    self.assertEqual(result.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_06_only_future_wav_declaration_is_accepted(self):
        for value in ("mp3", "flac", "pcm", "wave", "", None):
            h = Harness()
            try:
                result = h.adapter.execute(h.request(output_format=value))
                with self.subTest(value=value):
                    self.assertEqual(
                        result.safe_error_category, "unsupported_output_format"
                    )
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_07_absolute_traversal_nested_and_alternate_paths_fail_closed(self):
        cases = (
            ("other.l2fixture", "output_destination_mismatch"),
            ("../escape.l2fixture", "unsafe_output_path"),
            ("nested/escape.l2fixture", "unsafe_output_path"),
            (r"C:\escape.l2fixture", "unsafe_output_path"),
            ("/absolute.l2fixture", "unsafe_output_path"),
            ("output.wav", "unsafe_output_path"),
        )
        for output, category in cases:
            h = Harness()
            try:
                result = h.adapter.execute(
                    h.request(output_relative_path=output)
                )
                with self.subTest(output=output):
                    self.assertEqual(result.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
                    self.assertEqual(h.writer.call_count, 0)
            finally:
                h.close()

    def test_08_existing_target_fails_before_transport(self):
        (self.h.root / OUTPUT_NAME).write_bytes(b"preexisting-test-data")
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.safe_error_category, "destination_exists")
        self.assertEqual(self.h.transport.call_count, 0)
        self.assertEqual(self.h.writer.call_count, 0)

    def test_09_directory_link_reparse_and_unsafe_targets_fail_before_transport(self):
        (self.h.root / OUTPUT_NAME).mkdir()
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.safe_error_category, "destination_is_directory")
        self.assertEqual(self.h.transport.call_count, 0)

        for state, category in (
            ("link", "destination_is_link"),
            ("reparse", "destination_is_reparse_point"),
            ("unsafe", "destination_is_unsafe"),
        ):
            h = Harness(writer_options={"forced_target_state": state})
            try:
                outcome = h.adapter.execute(h.request())
                with self.subTest(state=state):
                    self.assertEqual(outcome.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
                    self.assertEqual(h.writer.call_count, 0)
            finally:
                h.close()

    def test_10_transport_failure_has_no_retry_or_output(self):
        self.h.close()
        self.h = Harness(transport=L2FakePiperTransport(fail=True))
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.safe_error_category, "transport_failure")
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 0)
        self.assertFalse((self.h.root / OUTPUT_NAME).exists())

    def test_11_writer_failure_has_no_retry_or_second_transport_call(self):
        self.h.close()
        self.h = Harness(writer_options={"fail": True})
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.safe_error_category, "writer_failure")
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 1)
        self.assertFalse((self.h.root / OUTPUT_NAME).exists())

    def test_12_malformed_transport_results_fail_closed(self):
        for response in (
            {"bytes": "fake"},
            bytearray(DETERMINISTIC_NON_AUDIO_BYTES),
            b"",
            b"RIFFfakeWAVE",
            b"unexpected fake bytes",
        ):
            h = Harness(transport=L2FakePiperTransport(response=response))
            try:
                result = h.adapter.execute(h.request())
                with self.subTest(response_type=type(response).__name__):
                    self.assertEqual(
                        result.safe_error_category,
                        "unexpected_transport_result",
                    )
                    self.assertEqual(h.transport.call_count, 1)
                    self.assertEqual(h.writer.call_count, 0)
                    self.assertFalse((h.root / OUTPUT_NAME).exists())
            finally:
                h.close()

    def test_13_adapter_is_single_use_and_cannot_reprocess(self):
        first = self.h.adapter.execute(self.h.request())
        second = self.h.adapter.execute(self.h.request())
        self.assertEqual(first.status, "success")
        self.assertEqual(second.safe_error_category, "adapter_reused")
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 1)

    def test_14_result_and_audit_shapes_are_strict_and_safe(self):
        self.assertEqual(
            [field.name for field in fields(PiperSynthesisResult)],
            ["status", "safe_error_category", "output_path", "byte_count", "audit"],
        )
        self.assertEqual(
            [field.name for field in fields(PiperSafeAudit)],
            [
                "route_identifier",
                "locked_engine_version",
                "locked_model_id",
                "fake_test_marker",
                "outcome_category",
                "fake_call_count",
                "output_byte_count",
            ],
        )
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.audit.route_identifier, ROUTE_IDENTIFIER)
        self.assertEqual(result.audit.locked_engine_version, LOCKED_ENGINE_VERSION)
        self.assertEqual(result.audit.locked_model_id, LOCKED_MODEL_ID)
        self.assertEqual(result.audit.fake_test_marker, FAKE_TEST_MARKER)
        self.assertEqual(result.audit.fake_call_count, 1)
        rendered_audit = json.dumps(
            {
                field.name: getattr(result.audit, field.name)
                for field in fields(PiperSafeAudit)
            }
        ).lower()
        self.assertNotIn("deterministic synthetic piper", rendered_audit)
        for forbidden in (
            "credential",
            "secret",
            "model_path",
            "configuration",
            "endpoint",
            str(self.h.root).lower(),
        ):
            self.assertNotIn(forbidden, rendered_audit)

    def test_15_only_exact_fake_dependencies_can_be_constructed(self):
        class LookalikeTransport:
            pass

        class FakeSubclass(L2FakePiperTransport):
            pass

        with self.assertRaises(TypeError):
            PiperLocalAdapterContract(
                transport=LookalikeTransport(),
                exclusive_writer=self.h.writer,
                isolated_workspace=self.h.root,
                exact_output_relative_path=OUTPUT_NAME,
            )
        with self.assertRaises(TypeError):
            PiperLocalAdapterContract(
                transport=FakeSubclass(),
                exclusive_writer=self.h.writer,
                isolated_workspace=self.h.root,
                exact_output_relative_path=OUTPUT_NAME,
            )
        with self.assertRaises(TypeError):
            PiperLocalAdapterContract(
                transport=self.h.transport,
                exclusive_writer=object(),
                isolated_workspace=self.h.root,
                exact_output_relative_path=OUTPUT_NAME,
            )

    def test_16_no_real_runtime_import_or_valid_audio_artifact_exists(self):
        files_to_scan = (
            AUTOMATION / "providers" / "piper_local_adapter_contract.py",
            AUTOMATION / "testing" / "l2_fake_piper_transport.py",
        )
        imported_roots = set()
        for path in files_to_scan:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(
                        alias.name.split(".")[0] for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])
        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "piper",
                    "onnxruntime",
                    "torch",
                    "subprocess",
                    "socket",
                    "requests",
                    "httpx",
                    "urllib",
                    "browser",
                    "mcp",
                    "wave",
                    "soundfile",
                    "scipy",
                }
            )
        )

        result = self.h.adapter.execute(self.h.request())
        fixture = (self.h.root / OUTPUT_NAME).read_bytes()
        self.assertEqual(result.status, "success")
        self.assertFalse(fixture.startswith(b"RIFF"))
        self.assertNotIn(b"WAVE", fixture)
        self.assertFalse(any(self.h.root.glob("*.wav")))
        self.assertFalse(any(self.h.root.glob("*.mp3")))
        self.assertFalse(any(self.h.root.glob("*.pcm")))

        outside = self.h.root.parent / "l2_escape_attempt.l2fixture"
        try:
            with self.assertRaises(ValueError):
                self.h.writer.write_exclusive(
                    relative_path="../l2_escape_attempt.l2fixture",
                    data=DETERMINISTIC_NON_AUDIO_BYTES,
                )
            self.assertFalse(outside.exists())
        finally:
            if outside.exists():
                self.fail("L2 containment test unexpectedly created an outside file")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L2PiperLocalAdapterContractTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        json.dumps(
            {
                "l2_offline_fake_contract_tests": (
                    "passed" if result.wasSuccessful() else "failed"
                ),
                "tests_run": result.testsRun,
                "real_piper_runtime": "not_installed_or_invoked",
                "audio_or_media_creation": "not_performed",
                "provider_or_network_activity": "not_performed",
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)
