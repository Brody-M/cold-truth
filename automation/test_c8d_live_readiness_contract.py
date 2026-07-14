from __future__ import annotations

import inspect
import json
import pickle
import tempfile
import unittest
from pathlib import Path

import c8d_live_readiness_contract as readiness
from c8d_live_readiness_contract import (
    AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION,
    CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE,
    CANONICAL_OUTPUT_ROOT_WORKSPACE_RELATIVE,
    OPAQUE_PROVIDER_CAPABILITIES, OPAQUE_PROVIDER_INTERFACE_ID,
    OPAQUE_PROVIDER_METHOD, OUTPUT_PATH_BASIS, TRANSPORT_CAPABILITIES,
    TRANSPORT_INTERFACE_ID, TRANSPORT_METHOD, opaque_provider_declaration_is_compatible,
    resolve_canonical_c8_output, transport_declaration_is_compatible
)
from test_c8a_authorization_schema import AUTOMATION, CONTRACT_PATH, DISPOSABLE, FUTURE, post_attempt_artifacts_are_closed


WORKSPACE = AUTOMATION.parent


class C8dLiveReadinessContractTests(unittest.TestCase):
    def tearDown(self):
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])

    def test_01_canonical_authorization_path_resolves_exactly(self):
        resolved = resolve_canonical_c8_output(
            workspace_root=WORKSPACE,
            authorization_relative_path=AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION
        )
        self.assertEqual(resolved.canonical_output_root, (WORKSPACE / CANONICAL_OUTPUT_ROOT_WORKSPACE_RELATIVE).resolve())
        self.assertEqual(resolved.canonical_output_file, (WORKSPACE / CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE).resolve())
        self.assertEqual(resolved.authorization_relative_path, AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION)
        self.assertEqual(resolved.workspace_relative_path, CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE)

    def test_02_contract_documents_both_path_forms_and_basis_exactly(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8")); paths = contract["canonical_output_paths"]
        self.assertEqual(paths["path_basis"], OUTPUT_PATH_BASIS)
        self.assertEqual(paths["canonical_output_root_workspace_relative"], CANONICAL_OUTPUT_ROOT_WORKSPACE_RELATIVE)
        self.assertEqual(paths["canonical_output_file_workspace_relative"], CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE)
        self.assertEqual(paths["authorization_output_relative_to_automation"], AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION)

    def test_03_ambiguous_absolute_escaping_duplicate_alternate_and_nonmp3_paths_block(self):
        paths = (
            CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE,
            "automation/" + AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION,
            "../" + AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION,
            "./" + AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION,
            "/" + AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION,
            r"C:\outside\c8_isolated_synthetic_connectivity.mp3",
            AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION.replace("fixtures/", "other/"),
            AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION.replace(".mp3", ".wav"),
            AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION.replace("/", "\\")
        )
        for value in paths:
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_canonical_c8_output(workspace_root=WORKSPACE, authorization_relative_path=value)

    def test_04_existing_canonical_target_blocks_without_creating_audio_file(self):
        target = WORKSPACE / CANONICAL_OUTPUT_FILE_WORKSPACE_RELATIVE
        target.mkdir(parents=True)
        try:
            with self.assertRaises(FileExistsError):
                resolve_canonical_c8_output(workspace_root=WORKSPACE, authorization_relative_path=AUTHORIZATION_OUTPUT_RELATIVE_TO_AUTOMATION)
            self.assertTrue(target.is_dir()); self.assertFalse(target.is_file())
        finally:
            target.rmdir()

    def test_05_transport_contract_is_declarative_and_exact(self):
        self.assertTrue(transport_declaration_is_compatible(
            identity=TRANSPORT_INTERFACE_ID, capabilities=TRANSPORT_CAPABILITIES,
            method_names={TRANSPORT_METHOD}
        ))
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["future_live_transport_interface"]
        self.assertEqual(contract["interface_identity"], TRANSPORT_INTERFACE_ID)
        self.assertEqual(contract["required_method"], TRANSPORT_METHOD)
        for key, value in TRANSPORT_CAPABILITIES.items(): self.assertIs(contract[key], value)

    def test_06_transport_missing_unknown_unsafe_or_extra_capabilities_block(self):
        self.assertFalse(transport_declaration_is_compatible(identity="unknown", capabilities=TRANSPORT_CAPABILITIES, method_names={TRANSPORT_METHOD}))
        self.assertFalse(transport_declaration_is_compatible(identity=TRANSPORT_INTERFACE_ID, capabilities={}, method_names={TRANSPORT_METHOD}))
        for field in TRANSPORT_CAPABILITIES:
            changed = dict(TRANSPORT_CAPABILITIES); changed[field] = not changed[field]
            with self.subTest(field=field): self.assertFalse(transport_declaration_is_compatible(identity=TRANSPORT_INTERFACE_ID, capabilities=changed, method_names={TRANSPORT_METHOD}))
        self.assertFalse(transport_declaration_is_compatible(identity=TRANSPORT_INTERFACE_ID, capabilities=TRANSPORT_CAPABILITIES, method_names={TRANSPORT_METHOD, "retry"}))

    def test_07_no_default_global_discovered_or_instantiated_transport_exists(self):
        self.assertFalse(TRANSPORT_CAPABILITIES["default_instance_available"])
        self.assertFalse(TRANSPORT_CAPABILITIES["global_registration_available"])
        runtime_objects = [value for name, value in vars(readiness).items() if not name.startswith("_") and not inspect.isclass(value) and hasattr(value, TRANSPORT_METHOD)]
        self.assertEqual(runtime_objects, [])

    def test_08_opaque_provider_contract_is_declarative_and_exact(self):
        self.assertTrue(opaque_provider_declaration_is_compatible(
            identity=OPAQUE_PROVIDER_INTERFACE_ID,
            capabilities=OPAQUE_PROVIDER_CAPABILITIES,
            method_names={OPAQUE_PROVIDER_METHOD}
        ))
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["future_opaque_provider_capability_interface"]
        self.assertEqual(contract["interface_identity"], OPAQUE_PROVIDER_INTERFACE_ID)
        self.assertEqual(contract["required_method"], OPAQUE_PROVIDER_METHOD)
        for key, value in OPAQUE_PROVIDER_CAPABILITIES.items(): self.assertIs(contract[key], value)

    def test_09_opaque_provider_missing_unknown_unsafe_or_wrapped_declarations_block(self):
        self.assertFalse(opaque_provider_declaration_is_compatible(identity="unknown", capabilities=OPAQUE_PROVIDER_CAPABILITIES, method_names={OPAQUE_PROVIDER_METHOD}))
        self.assertFalse(opaque_provider_declaration_is_compatible(identity=OPAQUE_PROVIDER_INTERFACE_ID, capabilities={}, method_names={OPAQUE_PROVIDER_METHOD}))
        for field in OPAQUE_PROVIDER_CAPABILITIES:
            changed = dict(OPAQUE_PROVIDER_CAPABILITIES); changed[field] = not changed[field]
            with self.subTest(field=field): self.assertFalse(opaque_provider_declaration_is_compatible(identity=OPAQUE_PROVIDER_INTERFACE_ID, capabilities=changed, method_names={OPAQUE_PROVIDER_METHOD}))
        self.assertFalse(opaque_provider_declaration_is_compatible(identity=OPAQUE_PROVIDER_INTERFACE_ID, capabilities=OPAQUE_PROVIDER_CAPABILITIES, method_names={OPAQUE_PROVIDER_METHOD, "read_config"}))

    def test_10_test_placeholder_capability_reveals_and_serializes_nothing(self):
        class TestOnlyOpaquePlaceholder:
            def __repr__(self): return "<opaque-provider-capability>"
            __str__ = __repr__
            def __reduce__(self): raise TypeError("opaque capability is non-serializable")
        capability = TestOnlyOpaquePlaceholder()
        self.assertEqual(repr(capability), "<opaque-provider-capability>")
        with self.assertRaises(TypeError): json.dumps(capability)
        with self.assertRaises(TypeError): pickle.dumps(capability)
        self.assertEqual(vars(capability), {})

    def test_11_module_has_no_transport_network_provider_or_runtime_import(self):
        source = Path(readiness.__file__).read_text(encoding="utf-8")
        for term in ("import requests", "import httpx", "import urllib", "import socket", "import subprocess", "os.environ", "getenv(", "http://", "https://", "from c4", "from c5", "from c6", "narration_provider_adapter", "write_bytes", "write_text", "open("):
            self.assertNotIn(term, source)

    def test_12_no_authorization_live_client_real_capability_or_media_artifact_exists(self):
        self.assertTrue(post_attempt_artifacts_are_closed())
        self.assertFalse(json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["execution_permitted_in_c8d"])
        media = []
        for extension in ("*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"):
            media.extend(path for path in DISPOSABLE.rglob(extension) if path.is_file())
        self.assertEqual(media, [])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C8dLiveReadinessContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c8d_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
