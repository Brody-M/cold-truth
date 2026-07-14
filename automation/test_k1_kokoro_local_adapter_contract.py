from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from providers.kokoro_local_adapter_contract import (
    FAKE_TEXT_PREFIX,
    FAKE_TEST_MARKER,
    MAXIMUM_INPUT_CHARACTERS,
    ROUTE_IDENTIFIER,
    SUPPORTED_OUTPUT_FORMAT,
    KokoroLocalAdapterContract,
    KokoroSynthesisRequest,
)
from testing.k1_fake_kokoro_transport import (
    DETERMINISTIC_NON_AUDIO_BYTES,
    K1FakeExclusiveCreateWriter,
    K1FakeKokoroTransport,
)


AUTOMATION = Path(__file__).resolve().parent
OUTPUT_NAME = "k1_fake_output.fixture"


class Harness:
    def __init__(self, *, transport=None, writer_options=None):
        self.temp = tempfile.TemporaryDirectory(prefix="cold_truth_k1_")
        self.root = Path(self.temp.name)
        self.transport = transport or K1FakeKokoroTransport()
        self.writer = K1FakeExclusiveCreateWriter(
            workspace_root=self.root, **(writer_options or {})
        )
        self.adapter = KokoroLocalAdapterContract(
            transport=self.transport,
            exclusive_writer=self.writer,
            isolated_workspace=self.root,
            exact_output_relative_path=OUTPUT_NAME,
        )

    def close(self):
        self.temp.cleanup()

    def request(self, **changes):
        values = {
            "text": FAKE_TEXT_PREFIX + "A deterministic synthetic contract sentence.",
            "voice_identifier": "fixture_voice_alpha",
            "output_format": SUPPORTED_OUTPUT_FORMAT,
            "output_relative_path": OUTPUT_NAME,
            "maximum_input_characters": MAXIMUM_INPUT_CHARACTERS,
        }
        values.update(changes)
        return KokoroSynthesisRequest(**values)


class K1KokoroLocalAdapterContractTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()

    def tearDown(self):
        self.h.close()

    def test_01_happy_path_calls_fake_transport_and_exclusive_writer_once(self):
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output_path, OUTPUT_NAME)
        self.assertEqual(result.byte_count, len(DETERMINISTIC_NON_AUDIO_BYTES))
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 1)
        self.assertEqual((self.h.root / OUTPUT_NAME).read_bytes(), DETERMINISTIC_NON_AUDIO_BYTES)

    def test_02_exact_destination_and_safe_relative_path_are_enforced(self):
        for output, category in (
            ("other.fixture", "output_destination_mismatch"),
            ("../escape.fixture", "unsafe_output_path"),
            ("nested/escape.fixture", "unsafe_output_path"),
            (r"C:\escape.fixture", "unsafe_output_path"),
            ("output.wav", "unsafe_output_path"),
        ):
            h = Harness()
            try:
                result = h.adapter.execute(h.request(output_relative_path=output))
                with self.subTest(output=output):
                    self.assertEqual(result.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
                    self.assertEqual(h.writer.call_count, 0)
            finally:
                h.close()

    def test_03_existing_destination_fails_before_transport(self):
        (self.h.root / OUTPUT_NAME).write_bytes(b"preexisting-test-data")
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.safe_error_category, "destination_exists")
        self.assertEqual(self.h.transport.call_count, 0)
        self.assertEqual(self.h.writer.call_count, 0)

    def test_04_directory_link_reparse_and_unsafe_targets_fail_closed(self):
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

    def test_05_empty_oversized_and_invalid_text_fail_before_transport(self):
        invalid = (
            ("", "invalid_text"),
            (FAKE_TEXT_PREFIX + "   ", "invalid_text"),
            ("real-looking text without fake marker", "invalid_text"),
            (FAKE_TEXT_PREFIX + ("x" * MAXIMUM_INPUT_CHARACTERS), "text_too_long"),
            (123, "invalid_text"),
        )
        for text, category in invalid:
            h = Harness()
            try:
                result = h.adapter.execute(h.request(text=text))
                with self.subTest(category=category):
                    self.assertEqual(result.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_06_declared_maximum_input_length_is_exact_and_bounded(self):
        for limit in (0, MAXIMUM_INPUT_CHARACTERS - 1, MAXIMUM_INPUT_CHARACTERS + 1, True):
            h = Harness()
            try:
                result = h.adapter.execute(h.request(maximum_input_characters=limit))
                with self.subTest(limit=limit):
                    self.assertEqual(result.safe_error_category, "invalid_maximum_input_length")
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_07_missing_or_unsupported_fixture_voice_fails_before_transport(self):
        for voice, category in (
            ("", "missing_voice_identifier"),
            (None, "missing_voice_identifier"),
            ("fixture_voice_beta", "unsupported_voice_identifier"),
            ("af_heart", "unsupported_voice_identifier"),
        ):
            h = Harness()
            try:
                result = h.adapter.execute(h.request(voice_identifier=voice))
                with self.subTest(voice=voice):
                    self.assertEqual(result.safe_error_category, category)
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_08_alternate_or_invalid_output_format_fails_before_transport(self):
        for value in ("mp3", "flac", "fixture", "", None):
            h = Harness()
            try:
                result = h.adapter.execute(h.request(output_format=value))
                with self.subTest(value=value):
                    self.assertEqual(result.safe_error_category, "unsupported_output_format")
                    self.assertEqual(h.transport.call_count, 0)
            finally:
                h.close()

    def test_09_fake_transport_failure_has_no_retry_or_output(self):
        self.h.close()
        self.h = Harness(transport=K1FakeKokoroTransport(fail=True))
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.safe_error_category, "transport_failure")
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 0)
        self.assertFalse((self.h.root / OUTPUT_NAME).exists())

    def test_10_fake_writer_failure_has_no_retry_or_second_transport_call(self):
        self.h.close()
        self.h = Harness(writer_options={"fail": True})
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.safe_error_category, "writer_failure")
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 1)
        self.assertFalse((self.h.root / OUTPUT_NAME).exists())

    def test_11_unexpected_fake_result_shapes_fail_closed(self):
        for response in ({"bytes": "fake"}, bytearray(DETERMINISTIC_NON_AUDIO_BYTES), b"", b"RIFFfake"):
            h = Harness(transport=K1FakeKokoroTransport(response=response))
            try:
                result = h.adapter.execute(h.request())
                with self.subTest(response_type=type(response).__name__):
                    self.assertEqual(result.safe_error_category, "unexpected_transport_result")
                    self.assertEqual(h.transport.call_count, 1)
                    self.assertEqual(h.writer.call_count, 0)
                    self.assertFalse((h.root / OUTPUT_NAME).exists())
            finally:
                h.close()

    def test_12_adapter_is_single_use_with_no_second_synthesis_call(self):
        first = self.h.adapter.execute(self.h.request())
        second = self.h.adapter.execute(self.h.request())
        self.assertEqual(first.status, "success")
        self.assertEqual(second.safe_error_category, "adapter_reused")
        self.assertEqual(self.h.transport.call_count, 1)
        self.assertEqual(self.h.writer.call_count, 1)

    def test_13_safe_result_and_audit_expose_only_operational_facts(self):
        result = self.h.adapter.execute(self.h.request())
        self.assertEqual(result.audit.route_identifier, ROUTE_IDENTIFIER)
        self.assertEqual(result.audit.fake_test_marker, FAKE_TEST_MARKER)
        self.assertEqual(result.audit.output_byte_count, len(DETERMINISTIC_NON_AUDIO_BYTES))
        rendered = json.dumps({
            "status": result.status,
            "category": result.safe_error_category,
            "output_path": result.output_path,
            "byte_count": result.byte_count,
            "audit": {
                "route_identifier": result.audit.route_identifier,
                "fake_test_marker": result.audit.fake_test_marker,
                "result_category": result.audit.result_category,
                "output_byte_count": result.audit.output_byte_count,
                "transport_call_count": result.audit.transport_call_count,
                "writer_call_count": result.audit.writer_call_count,
            },
        }).lower()
        for forbidden in ("credential", "secret", "model_path", "configuration", "endpoint"):
            self.assertNotIn(forbidden, rendered)

    def test_14_only_exact_fake_dependencies_are_constructible_and_no_real_runtime_is_imported(self):
        class LookalikeTransport:
            pass

        with self.assertRaises(TypeError):
            KokoroLocalAdapterContract(
                transport=LookalikeTransport(),
                exclusive_writer=self.h.writer,
                isolated_workspace=self.h.root,
                exact_output_relative_path=OUTPUT_NAME,
            )
        with self.assertRaises(TypeError):
            KokoroLocalAdapterContract(
                transport=self.h.transport,
                exclusive_writer=object(),
                isolated_workspace=self.h.root,
                exact_output_relative_path=OUTPUT_NAME,
            )

        files = (
            AUTOMATION / "providers" / "kokoro_local_adapter_contract.py",
            AUTOMATION / "testing" / "k1_fake_kokoro_transport.py",
        )
        imported_roots = set()
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])
        self.assertTrue(imported_roots.isdisjoint({
            "kokoro", "torch", "transformers", "huggingface_hub", "subprocess",
            "socket", "requests", "httpx", "urllib", "browser", "mcp",
        }))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        K1KokoroLocalAdapterContractTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "k1_offline_fake_contract_tests": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "real_kokoro_runtime": "not_installed_or_invoked",
        "audio_or_media_creation": "not_performed",
        "provider_or_network_activity": "not_performed",
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
