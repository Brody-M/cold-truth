from __future__ import annotations

import ast
import copy
import json
import unittest
from dataclasses import fields
from pathlib import Path

from l7_piper_synthetic_authorization_contract import (
    APPROVAL_LINKAGE_FIELD_NAMES,
    APPROVED_FUTURE_TEST_ROOT,
    CONFIG_SHA256,
    EXECUTION_PROVIDER,
    FAKE_TEXT_SHA256,
    L8_AUTHORIZATION_CONSUMED,
    L8_AUTHORIZATION_ROOT,
    L8_AUDIT_ROOT,
    L8_AUTHORIZED_NOT_EXECUTED,
    L8_EXECUTABLE_OUTPUT_FILENAME,
    L8_EXECUTABLE_OUTPUT_ROOT,
    L8ExecutableSyntheticAuthorizationValidator,
    L7FakeAuthorizationValidator,
    L7FakeValidationResult,
    MAXIMUM_TEXT_CHARACTERS,
    MODEL_ID,
    MODEL_SHA256,
    OUTPUT_FORMAT,
    PIPER_VERSION,
    REAL_NARRATION_GUARD,
    ROUTE_ID,
    SAFE_OUTCOMES,
    SYNTHETIC_AUTHORIZATION_PURPOSE,
)


AUTOMATION = Path(__file__).resolve().parent
FIXTURES = AUTOMATION / "fixtures"
VALID_FIXTURE = FIXTURES / "l7_piper_synthetic_authorization_valid.json"
CONTRACT_SOURCE = AUTOMATION / "l7_piper_synthetic_authorization_contract.py"


def load_valid_fixture():
    return json.loads(VALID_FIXTURE.read_text(encoding="utf-8"))


def validate_once(fixture):
    return L7FakeAuthorizationValidator().validate_fake_fixture(fixture)


def valid_l8_authorization_stub():
    """Static in-memory test stub; it is never persisted or passed to the factory."""
    return {
        "schema_version": "cold_truth.l7b.l8_executable_synthetic_authorization.v1",
        "authorization_id": "L8-SYNTHETIC-123e4567-e89b-42d3-a456-426614174000",
        "single_use_nonce": "a" * 64,
        "expiration_timestamp": "2026-07-14T00:00:00Z",
        "lifecycle_status": L8_AUTHORIZED_NOT_EXECUTED,
        "authorization_purpose": SYNTHETIC_AUTHORIZATION_PURPOSE,
        "synthetic_test_only": True, "non_case_text_only": True, "no_personal_data": True,
        "route_id": ROUTE_ID, "piper_version": PIPER_VERSION, "model_id": MODEL_ID,
        "model_sha256": MODEL_SHA256, "config_sha256": CONFIG_SHA256,
        "execution_provider": EXECUTION_PROVIDER, "output_format": OUTPUT_FORMAT,
        "text_sha256": "b" * 64,
        "maximum_runtime_process_count": 1, "maximum_session_initialization_count": 1,
        "maximum_synthesis_attempt_count": 1, "maximum_text_input_count": 1,
        "maximum_output_file_count": 1, "maximum_output_write_count": 1,
        "maximum_retry_count": 0, "maximum_fallback_count": 0,
        "maximum_voice_count": 1, "allowed_voice_ids": [MODEL_ID],
        "output_root": L8_EXECUTABLE_OUTPUT_ROOT,
        "output_filename": L8_EXECUTABLE_OUTPUT_FILENAME,
        "authorization_root": L8_AUTHORIZATION_ROOT, "audit_root": L8_AUDIT_ROOT,
        "exclusive_create_only": True, "output_root_must_be_absent": True,
        "target_output_must_not_exist": True, "disallow_output_mutation": True,
        "stop_after_first_attempt": True,
    }


def validate_l8_once(authorization):
    return L8ExecutableSyntheticAuthorizationValidator().validate_l8_executable_synthetic_authorization(authorization)


class L7PiperSyntheticAuthorizationContractTests(unittest.TestCase):
    def test_01_valid_fake_fixture_is_authorized_not_executed(self):
        logical_c3_state = "AWAITING_SCRIPT_APPROVAL"
        c4_approval_artifact = None
        result = validate_once(load_valid_fixture())
        self.assertEqual(logical_c3_state, "AWAITING_SCRIPT_APPROVAL")
        self.assertIsNone(c4_approval_artifact)
        self.assertEqual(result.outcome, "AUTHORIZED_NOT_EXECUTED")
        self.assertTrue(result.fixture_valid)
        self.assertIsNone(result.safe_error_category)
        self.assertFalse(result.executable_authorization_created)
        self.assertFalse(result.authorization_consumed)
        self.assertEqual(result.runtime_interactions, 0)
        self.assertEqual(result.writer_interactions, 0)
        self.assertEqual(result.output_artifacts, 0)

    def test_02_all_locked_identity_mismatches_fail_closed(self):
        cases = (
            ("route_id", "other"),
            ("piper_version", "1.4.1"),
            ("model_id", "en_US-lessac-medium"),
            ("model_sha256", "0" * 64),
            ("config_sha256", "f" * 64),
            ("execution_provider", "CUDAExecutionProvider"),
            ("output_format", "mp3"),
        )
        for field, value in cases:
            fixture = load_valid_fixture()
            fixture[field] = value
            result = validate_once(fixture)
            with self.subTest(field=field):
                self.assertEqual(result.outcome, "VALIDATION_REJECTED")
                self.assertEqual(
                    result.safe_error_category, "locked_identity_mismatch"
                )
                self.assertEqual(result.runtime_interactions, 0)
                self.assertEqual(result.writer_interactions, 0)

    def test_03_purpose_is_synthetic_only_and_c3_c4_linkage_fails_closed(self):
        valid = load_valid_fixture()
        self.assertEqual(
            valid["authorization_purpose"], SYNTHETIC_AUTHORIZATION_PURPOSE
        )
        self.assertTrue(set(valid).isdisjoint(APPROVAL_LINKAGE_FIELD_NAMES))

        for purpose in (
            "real_narration",
            "production_narration",
            "case_narration",
            "synthetic_test",
            "",
            None,
        ):
            fixture = load_valid_fixture()
            fixture["authorization_purpose"] = purpose
            with self.subTest(purpose=purpose):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "authorization_purpose_forbidden",
                )

        for field in sorted(APPROVAL_LINKAGE_FIELD_NAMES):
            fixture = load_valid_fixture()
            fixture[field] = "fixture-only-inert-value"
            with self.subTest(field=field):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "approval_linkage_forbidden",
                )

        missing_purpose = load_valid_fixture()
        del missing_purpose["authorization_purpose"]
        self.assertEqual(
            validate_once(missing_purpose).safe_error_category,
            "unknown_or_missing_fields",
        )

        unknown_attachment = load_valid_fixture()
        unknown_attachment["c4_approval_record"] = "fixture-only"
        self.assertEqual(
            validate_once(unknown_attachment).safe_error_category,
            "unknown_or_missing_fields",
        )

        unknown_c3_attachment = load_valid_fixture()
        unknown_c3_attachment["c3_record"] = "fixture-only"
        self.assertEqual(
            validate_once(unknown_c3_attachment).safe_error_category,
            "unknown_or_missing_fields",
        )

        for absent_field in (
            "requires_c3_approved_at_execution",
            "requires_c4_approval_at_execution",
            "c3_artifact_path",
            "c4_artifact_path",
        ):
            self.assertEqual(
                absent_field in valid,
                False,
            )

    def test_04_raw_text_and_text_hash_failures_are_rejected(self):
        raw_field_fixture = load_valid_fixture()
        raw_field_fixture["text"] = None
        self.assertEqual(
            validate_once(raw_field_fixture).safe_error_category,
            "raw_text_forbidden",
        )

        for value in ("", "0" * 63, "g" * 64, "f" * 64, None):
            fixture = load_valid_fixture()
            fixture["text_sha256"] = value
            with self.subTest(value=value):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "text_hash_invalid",
                )

        self.assertEqual(load_valid_fixture()["text_sha256"], FAKE_TEXT_SHA256)

    def test_05_fixed_text_limit_and_declared_count_are_enforced(self):
        cases = (
            ("maximum_text_characters", 159),
            ("maximum_text_characters", "160"),
            ("declared_text_character_count", 0),
            ("declared_text_character_count", 161),
            ("declared_text_character_count", True),
        )
        for field, value in cases:
            fixture = load_valid_fixture()
            fixture[field] = value
            with self.subTest(field=field, value=value):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "text_limit_invalid",
                )
        self.assertEqual(MAXIMUM_TEXT_CHARACTERS, 160)

    def test_06_real_case_personal_and_production_markers_fail_closed(self):
        for marker in (
            "real_case",
            "research",
            "script",
            "channel",
            "victim",
            "suspect",
            "personal",
            "biographical",
            "production",
            "narratively_meaningful",
        ):
            fixture = load_valid_fixture()
            fixture["prohibited_content"][marker] = True
            with self.subTest(marker=marker):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "content_boundary_violation",
                )

        for marker in (
            "synthetic_test_only",
            "non_case_text_only",
            "no_personal_data",
        ):
            fixture = load_valid_fixture()
            fixture[marker] = False
            self.assertEqual(
                validate_once(fixture).safe_error_category,
                "content_boundary_violation",
            )

    def test_07_attempt_output_voice_process_retry_and_fallback_limits(self):
        cases = (
            ("requested_synthesis_attempt_count", 2),
            ("prior_synthesis_attempt_count", 1),
            ("requested_retry_count", 1),
            ("requested_fallback_count", 1),
            ("requested_output_file_count", 2),
            ("requested_output_write_count", 2),
            ("requested_runtime_process_count", 2),
        )
        for field, value in cases:
            fixture = load_valid_fixture()
            fixture[field] = value
            with self.subTest(field=field):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "operation_limit_violation",
                )

        voice_cases = (
            ("maximum_voice_count", 2),
            ("requested_voice_count", 2),
            ("allowed_voice_ids", [MODEL_ID, "en_US-lessac-medium"]),
            ("allowed_voice_ids", ["en_US-lessac-medium"]),
        )
        for field, value in voice_cases:
            fixture = load_valid_fixture()
            fixture[field] = value
            with self.subTest(field=field):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "voice_limit_violation",
                )

    def test_08_queue_chunking_clone_effect_and_other_capabilities_reject(self):
        for capability in load_valid_fixture()["prohibited_capabilities"]:
            fixture = load_valid_fixture()
            fixture["prohibited_capabilities"][capability] = True
            with self.subTest(capability=capability):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "prohibited_capability_requested",
                )

    def test_09_output_contract_paths_and_exclusive_semantics_reject(self):
        cases = (
            ("approved_output_root", r"C:\OtherRoot"),
            ("target_directory_name", "../escape"),
            ("target_directory_name", r"C:\absolute"),
            ("target_directory_name", "nested/path"),
            ("expected_output_filename", "alternate.wav"),
            ("expected_output_filename", "l8_piper_synthetic_test.mp3"),
            ("exclusive_create", False),
            ("target_output_must_not_exist", False),
            ("target_directory_must_be_new", False),
            ("target_directory_must_be_empty", False),
            ("target_directory_must_not_be_link", False),
            ("target_directory_must_not_be_reparse", False),
            ("directory_containment_required", False),
            ("stop_after_first_attempt", False),
        )
        for field, value in cases:
            fixture = load_valid_fixture()
            fixture[field] = value
            with self.subTest(field=field, value=value):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "output_contract_violation",
                )
        self.assertEqual(
            load_valid_fixture()["approved_output_root"],
            APPROVED_FUTURE_TEST_ROOT,
        )

    def test_10_existing_link_reparse_and_nonempty_states_reject(self):
        for state in ("existing_empty", "nonempty", "link", "reparse", "unsafe"):
            fixture = load_valid_fixture()
            fixture["target_directory_observed_state"] = state
            with self.subTest(directory_state=state):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "output_state_violation",
                )

        for state in ("existing", "link", "reparse", "unsafe"):
            fixture = load_valid_fixture()
            fixture["target_output_observed_state"] = state
            with self.subTest(output_state=state):
                self.assertEqual(
                    validate_once(fixture).safe_error_category,
                    "output_state_violation",
                )

    def test_11_expired_malformed_missing_and_reusable_ids_reject(self):
        cases = (
            ("authorization_id", "L7-FAKE-MALFORMED", "authorization_id_invalid"),
            ("authorization_id", "", "authorization_id_invalid"),
            ("expiration_timestamp", "2026-07-12T00:00:00Z", "expiration_invalid"),
            ("expiration_timestamp", "malformed", "expiration_invalid"),
        )
        for field, value, expected in cases:
            fixture = load_valid_fixture()
            fixture[field] = value
            with self.subTest(field=field, value=value):
                self.assertEqual(
                    validate_once(fixture).safe_error_category, expected
                )

        missing = load_valid_fixture()
        del missing["authorization_id"]
        self.assertEqual(
            validate_once(missing).safe_error_category,
            "unknown_or_missing_fields",
        )

        reusable = load_valid_fixture()
        reusable["reuse_allowed"] = True
        self.assertEqual(
            validate_once(reusable).safe_error_category,
            "fixture_boundary_violation",
        )

        validator = L7FakeAuthorizationValidator()
        first = validator.validate_fake_fixture(load_valid_fixture())
        second = validator.validate_fake_fixture(load_valid_fixture())
        self.assertEqual(first.outcome, "AUTHORIZED_NOT_EXECUTED")
        self.assertEqual(second.safe_error_category, "authorization_id_reusable")
        self.assertFalse(second.authorization_consumed)

    def test_12_unknown_top_level_and_nested_fields_reject(self):
        top_level = load_valid_fixture()
        top_level["unexpected"] = False
        self.assertEqual(
            validate_once(top_level).safe_error_category,
            "unknown_or_missing_fields",
        )

        nested = load_valid_fixture()
        nested["prohibited_capabilities"]["unexpected"] = False
        self.assertEqual(
            validate_once(nested).safe_error_category,
            "prohibited_capability_requested",
        )

        content_nested = load_valid_fixture()
        content_nested["prohibited_content"]["unexpected"] = False
        self.assertEqual(
            validate_once(content_nested).safe_error_category,
            "content_boundary_violation",
        )

    def test_13_fixture_boundary_never_grants_or_consumes_live_authorization(self):
        cases = (
            ("fixture_only", False),
            ("executable", True),
            ("consumable", True),
            ("single_use", False),
            ("authorization_consumed", True),
            ("live_human_authorization_granted", True),
            ("human_authorization_marker", "LIVE"),
        )
        for field, value in cases:
            fixture = load_valid_fixture()
            fixture[field] = value
            result = validate_once(fixture)
            with self.subTest(field=field):
                self.assertEqual(
                    result.safe_error_category, "fixture_boundary_violation"
                )
                self.assertFalse(result.executable_authorization_created)
                self.assertFalse(result.authorization_consumed)

        public = {
            name
            for name in dir(L7FakeAuthorizationValidator)
            if not name.startswith("_")
        }
        self.assertEqual(public, {"validate_fake_fixture"})

    def test_14_safe_outcomes_and_result_shape_are_exact(self):
        self.assertEqual(
            SAFE_OUTCOMES,
            (
                "AUTHORIZED_NOT_EXECUTED",
                "VALIDATION_REJECTED",
                "EXECUTION_FAILED_CLOSED",
                "ONE_SYNTHETIC_OUTPUT_CREATED",
                "OUTPUT_CONTAINMENT_FAILURE",
                "AUTHORIZATION_CONSUMED",
            ),
        )
        self.assertEqual(
            [field.name for field in fields(L7FakeValidationResult)],
            [
                "outcome",
                "safe_error_category",
                "fixture_valid",
                "executable_authorization_created",
                "authorization_consumed",
                "runtime_interactions",
                "writer_interactions",
                "output_artifacts",
            ],
        )

    def test_15_invalid_patch_fixtures_all_reject_without_raw_text(self):
        invalid_paths = sorted(
            FIXTURES.glob("l7_piper_synthetic_authorization_invalid_*.json")
        )
        self.assertEqual(len(invalid_paths), 5)
        for path in invalid_paths:
            patch = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(patch.pop("fixture_patch_only"))
            self.assertEqual(
                patch.pop("fixture_base"),
                "l7_piper_synthetic_authorization_valid.json",
            )
            fixture = load_valid_fixture()
            fixture.update(patch)
            result = validate_once(fixture)
            with self.subTest(path=path.name):
                self.assertEqual(result.outcome, "VALIDATION_REJECTED")
                self.assertEqual(result.runtime_interactions, 0)
                self.assertEqual(result.writer_interactions, 0)
                self.assertEqual(result.output_artifacts, 0)

        raw_fixture = json.loads(
            (FIXTURES / "l7_piper_synthetic_authorization_invalid_raw_text.json")
            .read_text(encoding="utf-8")
        )
        self.assertIsNone(raw_fixture["text"])

    def test_16_validator_has_no_runtime_writer_network_or_production_route(self):
        source = CONTRACT_SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = set()
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".")[0] for alias in node.names
                )
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
                    "piper",
                    "onnxruntime",
                    "numpy",
                    "subprocess",
                    "socket",
                    "requests",
                    "httpx",
                    "urllib",
                    "os",
                    "shutil",
                    "wave",
                    "soundfile",
                    "mcp",
                    "browser",
                    "cold_truth_pipeline",
                    "provider_registry",
                }
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "open",
                    "write",
                    "write_bytes",
                    "write_text",
                    "mkdir",
                    "touch",
                    "unlink",
                    "rename",
                    "replace",
                    "run",
                    "Popen",
                    "system",
                }
            )
        )
        lowered = source.lower()
        for forbidden in (
            "l6_guarded_piper_runtime",
            "piper_local_adapter_contract",
            "cold_truth_pipeline",
            "provider_registry",
            "inferencesession",
            "pipervoice",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_17_locked_constants_are_exact_and_no_raw_text_is_stored(self):
        self.assertEqual(ROUTE_ID, "local_piper_1_4_2_en_us_ljspeech_high")
        self.assertEqual(PIPER_VERSION, "1.4.2")
        self.assertEqual(MODEL_ID, "en_US-ljspeech-high")
        self.assertEqual(
            MODEL_SHA256,
            "5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a",
        )
        self.assertEqual(
            CONFIG_SHA256,
            "7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14",
        )
        self.assertEqual(EXECUTION_PROVIDER, "CPUExecutionProvider")
        self.assertEqual(OUTPUT_FORMAT, "wav")
        self.assertEqual(
            SYNTHETIC_AUTHORIZATION_PURPOSE,
            "synthetic_local_connectivity_test",
        )
        self.assertEqual(
            REAL_NARRATION_GUARD,
            "outside_l7a_requires_c3_approved_script_state_and_c4_approval_chain",
        )
        self.assertEqual(
            APPROVED_FUTURE_TEST_ROOT,
            r"C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests",
        )

        valid = load_valid_fixture()
        self.assertTrue(set(valid).isdisjoint(APPROVAL_LINKAGE_FIELD_NAMES))
        self.assertTrue(set(valid).isdisjoint({"text", "raw_text", "narration"}))
        rendered = json.dumps(valid).lower()
        for forbidden in (
            "victim name",
            "suspect name",
            "case details",
            "narration payload",
            "personal data",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_18_l8_static_in_memory_shape_validates_without_persistence(self):
        result = validate_l8_once(valid_l8_authorization_stub())
        self.assertTrue(result.valid)
        self.assertEqual(result.lifecycle_status, L8_AUTHORIZED_NOT_EXECUTED)
        self.assertIsNone(result.safe_error_category)
        self.assertFalse(result.persisted)
        self.assertEqual(result.runtime_interactions, 0)
        self.assertEqual(result.writer_interactions, 0)
        self.assertEqual(result.output_artifacts, 0)

    def test_19_l8_canonical_root_filename_and_fixed_record_roots_are_locked(self):
        self.assertEqual(L8_EXECUTABLE_OUTPUT_ROOT, APPROVED_FUTURE_TEST_ROOT)
        self.assertEqual(L8_EXECUTABLE_OUTPUT_FILENAME, "l8_piper_synthetic_test.wav")
        self.assertEqual(
            L8_EXECUTABLE_OUTPUT_ROOT,
            r"C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests",
        )
        for field, value in (
            ("output_root", r"C:\ColdTruthLocalTools\piper-l8-synthetic-test"),
            ("output_filename", "alternate.wav"),
            ("authorization_root", r"C:\ColdTruthLocalTools\other"),
            ("audit_root", r"C:\ColdTruthLocalTools\other-audit"),
        ):
            authorization = valid_l8_authorization_stub()
            authorization[field] = value
            with self.subTest(field=field):
                self.assertEqual(validate_l8_once(authorization).safe_error_category, "output_contract_violation")

    def test_20_l8_identity_limits_voice_and_unsafe_output_behavior_fail_closed(self):
        for field, value in (
            ("piper_version", "1.0"), ("model_id", "other"),
            ("model_sha256", "0" * 64), ("config_sha256", "0" * 64),
            ("execution_provider", "CUDAExecutionProvider"), ("output_format", "mp3"),
            ("maximum_session_initialization_count", 2),
            ("maximum_text_input_count", 2), ("maximum_output_write_count", 2),
            ("maximum_retry_count", 1), ("maximum_fallback_count", 1),
            ("maximum_voice_count", 2), ("allowed_voice_ids", [MODEL_ID, "other"]),
            ("exclusive_create_only", False), ("output_root_must_be_absent", False),
            ("target_output_must_not_exist", False), ("disallow_output_mutation", False),
            ("stop_after_first_attempt", False),
        ):
            authorization = valid_l8_authorization_stub()
            authorization[field] = value
            result = validate_l8_once(authorization)
            with self.subTest(field=field):
                self.assertFalse(result.valid)
                self.assertEqual(result.runtime_interactions, 0)
                self.assertEqual(result.writer_interactions, 0)

    def test_21_l8_content_purpose_text_and_c3_c4_linkage_fail_closed(self):
        for field, value in (
            ("text", "never durable"), ("text_sha256", ""),
            ("synthetic_test_only", False), ("non_case_text_only", False),
            ("no_personal_data", False), ("c3_status", "AWAITING_SCRIPT_APPROVAL"),
            ("c4_approval", "none"), ("real_case", False), ("script", False),
            ("research", False), ("production", False),
        ):
            authorization = valid_l8_authorization_stub()
            authorization[field] = value
            with self.subTest(field=field):
                self.assertFalse(validate_l8_once(authorization).valid)
        for purpose in ("real_narration", "case_narration", "", None, "unknown"):
            authorization = valid_l8_authorization_stub()
            authorization["authorization_purpose"] = purpose
            with self.subTest(purpose=purpose):
                self.assertEqual(validate_l8_once(authorization).safe_error_category, "authorization_purpose_forbidden")

    def test_22_l8_reuse_expiration_nonce_and_lifecycle_mutations_fail_closed(self):
        validator = L8ExecutableSyntheticAuthorizationValidator()
        first = validator.validate_l8_executable_synthetic_authorization(valid_l8_authorization_stub())
        reused = validator.validate_l8_executable_synthetic_authorization(valid_l8_authorization_stub())
        self.assertTrue(first.valid)
        self.assertEqual(reused.safe_error_category, "authorization_reused")
        for field, value in (
            ("authorization_id", "bad"), ("single_use_nonce", ""),
            ("expiration_timestamp", "2026-07-12T00:00:00Z"),
            ("expiration_timestamp", "bad"),
            ("lifecycle_status", L8_AUTHORIZATION_CONSUMED),
            ("lifecycle_status", "RESET"),
        ):
            authorization = valid_l8_authorization_stub()
            authorization[field] = value
            with self.subTest(field=field):
                self.assertFalse(validate_l8_once(authorization).valid)
        missing_nonce = valid_l8_authorization_stub()
        del missing_nonce["single_use_nonce"]
        self.assertEqual(validate_l8_once(missing_nonce).safe_error_category, "unknown_or_missing_fields")

    def test_23_l8_factory_is_future_only_and_contract_has_no_io_calls(self):
        source = CONTRACT_SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(CONTRACT_SOURCE))
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
        self.assertIn("def create_l8_executable_synthetic_authorization", source)
        self.assertIn("preflight_validated is not True", source)
        self.assertNotIn("Path", called_names)
        self.assertNotIn("mkdir", called_attributes)
        self.assertNotIn("write_text", called_attributes)
        self.assertNotIn("write_bytes", called_attributes)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        L7PiperSyntheticAuthorizationContractTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        json.dumps(
            {
                "l7_offline_fake_authorization_contract": (
                    "passed" if result.wasSuccessful() else "failed"
                ),
                "tests_run": result.testsRun,
                "piper_or_onnx_imports": 0,
                "runtime_processes": 0,
                "model_loads": 0,
                "text_inputs": 0,
                "inference_calls": 0,
                "synthesis_calls": 0,
                "audio_or_media_artifacts": 0,
                "output_directories_or_files": 0,
                "network_or_provider_activity": 0,
                "executable_authorizations_created": 0,
                "authorizations_consumed": 0,
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)
