from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

import c8d_live_readiness_contract as readiness
import c8e_runner_boundary_contract as runner_contract
from c8a_authorization_schema_validator import BLOCKED, InMemoryReplayRegistry, validate_hypothetical_record
from c8d_live_readiness_contract import OPAQUE_PROVIDER_CAPABILITIES, TRANSPORT_CAPABILITIES
from c8e_runner_boundary_contract import (
    FIXED_OPAQUE_CONFIGURATION_SLOTS, RUNNER_CAPABILITIES, RUNNER_IDENTITY,
    RUNNER_METHOD, opaque_capability_shape_is_compatible,
    opaque_slot_request_is_compatible, runner_declaration_is_compatible
)
from test_c8a_authorization_schema import (
    AUTOMATION, CONTRACT_PATH, DISPOSABLE, FUTURE, SCHEMA_PATH,
    binding_values, hypothetical_record, post_attempt_artifacts_are_closed
)


class C8eRunnerBoundaryContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def tearDown(self):
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])

    def test_01_runner_identity_method_and_capabilities_are_exact(self):
        self.assertEqual(RUNNER_IDENTITY, "c8_one_time_isolated_provider_runner")
        self.assertTrue(runner_declaration_is_compatible(
            identity=RUNNER_IDENTITY, capabilities=RUNNER_CAPABILITIES,
            method_names={RUNNER_METHOD}
        ))
        contract = self.contract["future_runner_contract"]
        self.assertEqual(contract["runner_identity"], RUNNER_IDENTITY)
        self.assertEqual(contract["required_method"], RUNNER_METHOD)
        for key, value in RUNNER_CAPABILITIES.items(): self.assertIs(contract[key], value)

    def test_02_historical_runner_is_deactivated_by_active_mcp_authorization(self):
        self.assertEqual(RUNNER_CAPABILITIES["future_authorized_local_python_launch_count"], 1)
        for field in ("child_process_capable", "subprocess_capable", "shell_capable",
                      "powershell_capable", "cmd_capable", "node_capable",
                      "browser_capable", "mcp_capable", "codex_capable",
                      "external_command_capable"):
            self.assertIs(RUNNER_CAPABILITIES[field], False)
        record = hypothetical_record()
        for field in ("runner_identity", "local_python_runner_launch_authorized",
                      "maximum_runner_launch_count", "runner_child_process_allowed",
                      "opaque_capability_handoff_authorized", "in_process_http_request_authorized"):
            self.assertNotIn(field, record)
        self.assertEqual(record["execution_transport"], "existing_configured_elevenlabs_mcp")
        self.assertEqual(record["maximum_mcp_operation_count"], 1)
        self.assertFalse(self.contract["historical_route_status"]["local_python_runner_active"])

    def test_03_runner_reuse_schedule_default_global_or_unsafe_changes_block(self):
        for field in RUNNER_CAPABILITIES:
            changed = dict(RUNNER_CAPABILITIES)
            current = changed[field]; changed[field] = 2 if isinstance(current, int) and not isinstance(current, bool) else not current
            with self.subTest(field=field): self.assertFalse(runner_declaration_is_compatible(identity=RUNNER_IDENTITY, capabilities=changed, method_names={RUNNER_METHOD}))
        self.assertFalse(runner_declaration_is_compatible(identity="other", capabilities=RUNNER_CAPABILITIES, method_names={RUNNER_METHOD}))
        self.assertFalse(runner_declaration_is_compatible(identity=RUNNER_IDENTITY, capabilities=RUNNER_CAPABILITIES, method_names={RUNNER_METHOD, "run_again"}))

    def test_04_future_transport_allows_one_operation_and_no_followup_behavior(self):
        self.assertEqual(TRANSPORT_CAPABILITIES["maximum_outbound_request_count"], 1)
        for field in ("retry_capable", "redirect_capable", "fallback_capable",
                      "discovery_capable", "polling_capable", "status_request_capable",
                      "follow_up_capable", "cleanup_request_capable",
                      "deletion_request_capable", "batch_capable", "multi_output_capable",
                      "arbitrary_request_capable"):
            self.assertIs(TRANSPORT_CAPABILITIES[field], False)
        method = inspect.signature(readiness.FutureC8LiveTransport.perform_single_authorized_request)
        self.assertEqual(tuple(method.parameters), ("self", "sanitized_request", "opaque_provider_capability"))

    def test_05_opaque_configuration_slots_are_fixed_and_exact(self):
        self.assertEqual(FIXED_OPAQUE_CONFIGURATION_SLOTS, ("provider_api_credential", "locked_voice_identifier"))
        self.assertEqual(tuple(self.contract["opaque_configuration_slot_allowlist"]), FIXED_OPAQUE_CONFIGURATION_SLOTS)
        self.assertTrue(opaque_slot_request_is_compatible(FIXED_OPAQUE_CONFIGURATION_SLOTS))
        self.assertFalse(self.contract["historical_route_status"]["opaque_capability_slots_active"])
        for slots in ((), ("provider_api_credential",), ("*",), ("../secret",),
                      ("provider_api_credential", "locked_voice_identifier", "extra"),
                      tuple(reversed(FIXED_OPAQUE_CONFIGURATION_SLOTS))):
            with self.subTest(slots=slots): self.assertFalse(opaque_slot_request_is_compatible(slots))

    def test_06_opaque_source_cannot_read_enumerate_expose_or_modify_raw_values(self):
        for field in ("environment_reading", "configuration_reading", "raw_secret_returning",
                      "endpoint_returning", "voice_identifier_returning", "header_returning",
                      "account_detail_returning", "serializable_capability", "printable_capability",
                      "credential_write_capable", "credential_rotate_capable",
                      "credential_export_capable", "credential_validate_capable",
                      "generic_configuration_api", "arbitrary_callable_wrapper",
                      "arbitrary_slot_lookup", "wildcard_slot_lookup",
                      "configuration_enumeration", "path_traversal_lookup"):
            self.assertIs(OPAQUE_PROVIDER_CAPABILITIES[field], False)
        self.assertTrue(opaque_capability_shape_is_compatible(public_field_names=set(), method_names=set(), printable=False, serializable=False))
        unsafe = (
            {"public_field_names": {"secret"}, "method_names": set(), "printable": False, "serializable": False},
            {"public_field_names": set(), "method_names": {"export"}, "printable": False, "serializable": False},
            {"public_field_names": set(), "method_names": set(), "printable": True, "serializable": False},
            {"public_field_names": set(), "method_names": set(), "printable": False, "serializable": True}
        )
        for shape in unsafe: self.assertFalse(opaque_capability_shape_is_compatible(**shape))

    def test_07_authorization_runner_constants_are_strict_and_fail_closed(self):
        changes = {"runner_identity": "other", "local_python_runner_launch_authorized": False,
                   "maximum_runner_launch_count": 2, "runner_reuse_allowed": True,
                   "runner_scheduling_allowed": True, "runner_default_registration_allowed": True,
                   "runner_global_registration_allowed": True, "runner_child_process_allowed": True,
                   "opaque_capability_handoff_authorized": False,
                   "in_process_http_request_authorized": False}
        for field, value in changes.items():
            record = hypothetical_record(); record[field] = value
            result = validate_hypothetical_record(
                record=record, schema=self.schema, expected_bindings=binding_values(),
                future_c8_root=FUTURE, disposable_output_root=DISPOSABLE,
                replay_registry=InMemoryReplayRegistry()
            )
            with self.subTest(field=field): self.assertEqual(result["state"], BLOCKED)

    def test_08_contract_contains_no_live_runner_or_execution_permission_in_c8e(self):
        self.assertFalse(self.contract["creation_permitted_in_c8e"])
        self.assertFalse(self.contract["execution_permitted_in_c8e"])
        runtime_objects = [value for name, value in vars(runner_contract).items() if not name.startswith("_") and not inspect.isclass(value) and hasattr(value, RUNNER_METHOD)]
        self.assertEqual(runtime_objects, [])

    def test_09_modules_import_no_network_provider_process_shell_or_runtime_path(self):
        sources = [Path(readiness.__file__).read_text(encoding="utf-8"), Path(runner_contract.__file__).read_text(encoding="utf-8")]
        for source in sources:
            for term in ("import requests", "import httpx", "import urllib", "import socket", "import subprocess", "os.environ", "getenv(", "http://", "https://", "from c4", "from c5", "from c6", "narration_provider_adapter", "write_bytes", "write_text", "open("):
                self.assertNotIn(term, source)

    def test_10_no_valid_authorization_runner_capability_audio_or_media_exists(self):
        self.assertTrue(post_attempt_artifacts_are_closed())
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])

    def test_11_runner_contract_preserves_isolated_nonproduction_boundary(self):
        record = hypothetical_record()
        self.assertEqual(record["test_classification"], "isolated_synthetic_provider_connectivity_test")
        self.assertFalse(record["real_case_content_allowed"])
        self.assertFalse(record["c4_approval_artifact_allowed"])
        self.assertEqual(record["c3_fixture_state_must_remain"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(record["publishing_enabled"]); self.assertFalse(record["real_production_enabled"])
        self.assertFalse(RUNNER_CAPABILITIES["production_enabled"])

    def test_12_no_operational_runner_or_external_activity_is_requested(self):
        self.assertTrue(self.contract["schema_only"])
        self.assertFalse(self.contract["live_transport_present"])
        self.assertFalse(self.contract["credential_lookup_present"])
        self.assertFalse(self.contract["environment_lookup_present"])
        self.assertFalse(self.contract["configuration_lookup_present"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8eRunnerBoundaryContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c8e_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
