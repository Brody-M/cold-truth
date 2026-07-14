from __future__ import annotations

import ast
import inspect
import json
import re
import unittest
from pathlib import Path

import c8f_configuration_plan_contract as plan
from c8e_runner_boundary_contract import FIXED_OPAQUE_CONFIGURATION_SLOTS, RUNNER_IDENTITY
from test_c8a_authorization_schema import post_attempt_artifacts_are_closed


AUTOMATION = Path(__file__).resolve().parent
WORKSPACE = AUTOMATION.parent
FUTURE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace" / "narration_preflight" / "future_c8"
DISPOSABLE = FUTURE / "disposable_output"
CHAIN_STATE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace" / "output" / "c3_real_writer_editor_chain" / "chain_state.json"
PRIVATE_CONFIG = WORKSPACE / Path(plan.OPTION_B_CONFIG_PATH_WORKSPACE_RELATIVE)
OPTION_A_GUIDE = AUTOMATION / "C8_OPTION_A_TEMPORARY_ENVIRONMENT_SETUP.md"


def option_a() -> dict:
    return {
        "mechanism": plan.OPTION_A,
        "requested_slots": FIXED_OPAQUE_CONFIGURATION_SLOTS,
        "environment_variable_names": plan.OPTION_A_ENVIRONMENT_VARIABLE_NAMES,
    }


def option_b() -> dict:
    return {
        "mechanism": plan.OPTION_B,
        "requested_slots": FIXED_OPAQUE_CONFIGURATION_SLOTS,
        "local_config_path": plan.OPTION_B_CONFIG_PATH_WORKSPACE_RELATIVE,
        "local_config_fields": plan.OPTION_B_CONFIG_FIELDS,
    }


class C8fConfigurationPlanContractTests(unittest.TestCase):
    def tearDown(self):
        self.assertFalse(PRIVATE_CONFIG.exists())
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])

    def test_01_both_future_mechanisms_are_exact_and_mutually_exclusive(self):
        self.assertEqual(plan.CONFIGURATION_MECHANISMS, (plan.OPTION_A, plan.OPTION_B))
        self.assertTrue(plan.selection_is_exclusive(option_a_selected=True, option_b_selected=False))
        self.assertTrue(plan.selection_is_exclusive(option_a_selected=False, option_b_selected=True))
        self.assertFalse(plan.selection_is_exclusive(option_a_selected=False, option_b_selected=False))
        self.assertFalse(plan.selection_is_exclusive(option_a_selected=True, option_b_selected=True))

    def test_02_option_a_uses_only_exact_placeholder_names_and_slots(self):
        self.assertEqual(plan.OPTION_A_ENVIRONMENT_VARIABLE_NAMES, (
            "COLD_TRUTH_C8_PROVIDER_API_CREDENTIAL",
            "COLD_TRUTH_C8_LOCKED_VOICE_IDENTIFIER",
        ))
        self.assertTrue(plan.configuration_descriptor_is_compatible(option_a()))

    def test_03_option_b_uses_only_exact_ignored_path_fields_and_slots(self):
        self.assertEqual(
            plan.OPTION_B_CONFIG_PATH_WORKSPACE_RELATIVE,
            "automation/private/c8_one_time_provider_config.json",
        )
        self.assertEqual(plan.OPTION_B_CONFIG_FIELDS, FIXED_OPAQUE_CONFIGURATION_SLOTS)
        self.assertTrue(plan.configuration_descriptor_is_compatible(option_b()))
        gitignore = (WORKSPACE / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("automation/private/c8_one_time_provider_config.json", gitignore.splitlines())

    def test_04_empty_partial_reordered_wildcard_extra_and_unknown_slots_fail(self):
        unsafe = (
            (),
            ("provider_api_credential",),
            tuple(reversed(FIXED_OPAQUE_CONFIGURATION_SLOTS)),
            ("*", "locked_voice_identifier"),
            ("provider_api_credential", "locked_voice_identifier", "extra"),
            ("unknown", "locked_voice_identifier"),
        )
        for slots in unsafe:
            descriptor = option_a(); descriptor["requested_slots"] = slots
            with self.subTest(slots=slots):
                self.assertFalse(plan.configuration_descriptor_is_compatible(descriptor))

    def test_05_alternate_names_additional_fields_and_both_option_fields_fail(self):
        changed = option_a(); changed["environment_variable_names"] = ("alternate", "alternate2")
        self.assertFalse(plan.configuration_descriptor_is_compatible(changed))
        changed = option_a(); changed["local_config_path"] = plan.OPTION_B_CONFIG_PATH_WORKSPACE_RELATIVE
        self.assertFalse(plan.configuration_descriptor_is_compatible(changed))
        changed = option_b(); changed["environment_variable_names"] = plan.OPTION_A_ENVIRONMENT_VARIABLE_NAMES
        self.assertFalse(plan.configuration_descriptor_is_compatible(changed))
        changed = option_b(); changed["extra"] = True
        self.assertFalse(plan.configuration_descriptor_is_compatible(changed))

    def test_06_alternate_paths_traversal_discovery_and_fallback_fail(self):
        for path in ("other.json", "../private.json", "/absolute/private.json", "automation/private/*.json"):
            descriptor = option_b(); descriptor["local_config_path"] = path
            with self.subTest(path=path):
                self.assertFalse(plan.configuration_descriptor_is_compatible(descriptor))
        for field in ("directory_scan", "config_discovery", "fallback_source", "alternate_names", "generic_config_read", "generic_environment_access", "environment_enumeration"):
            self.assertIs(plan.FUTURE_CONFIGURATION_CAPABILITIES[field], False)

    def test_07_raw_value_output_hash_logging_return_and_audit_are_forbidden(self):
        for operation in plan.PROHIBITED_RAW_VALUE_OPERATIONS:
            with self.subTest(operation=operation):
                self.assertFalse(plan.raw_value_operation_is_allowed(operation))
        self.assertTrue(plan.raw_value_operation_is_allowed(plan.ONLY_ALLOWED_RAW_VALUE_OPERATION))
        unsafe = (
            {"raw_value_included": True}, {"raw_value_hashed": True},
            {"raw_value_in_exception": True}, {"raw_value_in_audit": True},
            {"raw_value_in_return": True},
        )
        base = dict(raw_value_included=False, raw_value_hashed=False,
                    raw_value_in_exception=False, raw_value_in_audit=False,
                    raw_value_in_return=False)
        self.assertTrue(plan.redacted_boundary_is_compatible(**base))
        for update in unsafe:
            candidate = dict(base); candidate.update(update)
            self.assertFalse(plan.redacted_boundary_is_compatible(**candidate))

    def test_08_historical_configuration_sources_are_inactive_for_current_c8(self):
        self.assertFalse(plan.ACTIVE_FOR_CURRENT_C8)
        for descriptor in (option_a(), option_b()):
            self.assertFalse(plan.future_source_may_be_available(
                descriptor=descriptor, future_c8_authorization_valid=False,
                runner_identity=RUNNER_IDENTITY,
            ))
            self.assertFalse(plan.future_source_may_be_available(
                descriptor=descriptor, future_c8_authorization_valid=True,
                runner_identity="other",
            ))
            self.assertFalse(plan.future_source_may_be_available(
                descriptor=descriptor, future_c8_authorization_valid=True,
                runner_identity=RUNNER_IDENTITY,
            ))

    def test_09_c8f_module_has_no_live_config_network_provider_or_file_access(self):
        source = inspect.getsource(plan)
        forbidden = (
            "os.environ", "getenv(", "environ[", "import requests", "import httpx",
            "import urllib", "import socket", "http://", "https://", "write_bytes",
            "read_text(", "read_bytes(", "open(", "provider sdk", "subprocess",
        )
        for term in forbidden:
            with self.subTest(term=term): self.assertNotIn(term, source.lower())
        self.assertIs(plan.FUTURE_CONFIGURATION_CAPABILITIES["network_present_in_c8f"], False)
        self.assertIs(plan.FUTURE_CONFIGURATION_CAPABILITIES["configuration_read_present_in_c8f"], False)

    def test_10_no_private_config_authorization_instance_audio_or_media_exists(self):
        self.assertFalse(PRIVATE_CONFIG.exists())
        self.assertTrue(post_attempt_artifacts_are_closed())

    def test_11_existing_c8_controls_and_c3_state_remain_unchanged(self):
        state = json.loads(CHAIN_STATE.read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"])
        self.assertFalse(state["assets_authorized"])
        self.assertFalse(state["real_production_enabled"])
        for field in ("credential_write", "credential_rotate", "credential_export", "credential_validate", "provider_execution_present_in_c8f"):
            self.assertIs(plan.FUTURE_CONFIGURATION_CAPABILITIES[field], False)

    def test_12_c8f_is_declarative_and_creates_no_operational_objects(self):
        functions = {name for name, value in vars(plan).items() if inspect.isfunction(value) and value.__module__ == plan.__name__}
        self.assertEqual(functions, {
            "_exact_string_tuple", "configuration_descriptor_is_compatible",
            "selection_is_exclusive", "future_source_may_be_available",
            "raw_value_operation_is_allowed", "redacted_boundary_is_compatible",
        })
        self.assertFalse(plan.FUTURE_CONFIGURATION_CAPABILITIES["provider_execution_present_in_c8f"])


class C8gOptionASetupGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guide = OPTION_A_GUIDE.read_text(encoding="utf-8")
        cls.lowered = cls.guide.lower()

    def test_01_option_a_is_historical_and_option_b_is_unused(self):
        self.assertIn("not used for current c8 mcp route", self.lowered)
        self.assertIn("option a is inactive", self.lowered)
        self.assertIn("option b was never selected and remains unused", self.lowered)

    def test_02_only_exact_variable_names_and_placeholders_appear(self):
        variable_names = set(re.findall(r"COLD_TRUTH_C8_[A-Z_]+", self.guide))
        placeholders = set(re.findall(r"<PASTE_[A-Z_]+>", self.guide))
        self.assertEqual(variable_names, {
            "COLD_TRUTH_C8_PROVIDER_API_CREDENTIAL",
            "COLD_TRUTH_C8_LOCKED_VOICE_IDENTIFIER",
        })
        self.assertEqual(placeholders, {
            "<PASTE_PROVIDER_API_KEY_HERE>",
            "<PASTE_LOCKED_MIA_VOICE_ID_HERE>",
        })

    def test_03_guide_forbids_persistence_storage_logging_and_disclosure(self):
        required = (
            "do not use `setx`", "windows user or system environment settings",
            "`.env` files", "automation/private/c8_one_time_provider_config.json",
            "git", "logs", "screenshots", "do not paste either value into codex",
            "do not print, log, serialize, hash, return, validate, copy, or report",
            "persistent configuration is not authorized or recommended",
        )
        for phrase in required:
            with self.subTest(phrase=phrase): self.assertIn(phrase, self.lowered)

    def test_04_separate_live_authorization_precedes_setting_or_execution(self):
        self.assertIn("do not set either variable", self.lowered)
        self.assertIn("new, explicit, one-time c8 live authorization", self.lowered)
        self.assertLess(
            self.lowered.index("issue a separate, explicit, one-time c8 live authorization"),
            self.lowered.index("open a new windows powershell window"),
        )
        self.assertIn("close the powershell window immediately after the attempt", self.lowered)

    def test_05_later_runner_is_limited_to_two_names_without_enumeration(self):
        self.assertIn("may read only these two exact names", self.lowered)
        self.assertIn("must not enumerate the environment", self.lowered)
        self.assertIn("read any other variable", self.lowered)

    def test_06_c8g_tests_contain_no_environment_or_configuration_access(self):
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        environment_operations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "os" and node.attr in {"environ", "getenv", "putenv", "unsetenv"}:
                    environment_operations.append((node.value.id, node.attr))
            if isinstance(node, ast.Name) and node.id in {"GetEnvironmentVariable", "EnvironmentVariableTarget"}:
                environment_operations.append(("name", node.id))
        self.assertEqual(environment_operations, [])
        self.assertFalse(PRIVATE_CONFIG.exists())


if __name__ == "__main__":
    suite = unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(C8fConfigurationPlanContractTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(C8gOptionASetupGuideTests),
    ))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "c8f_c8g_offline_tests": "passed" if result.wasSuccessful() else "failed",
        "c8f_contract_test_count": 12,
        "c8g_option_a_guide_test_count": 6,
        "tests_run": result.testsRun,
        "real_invocation": "not_requested",
        "environment_access": "not_performed",
        "configuration_file_access": "not_performed",
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
