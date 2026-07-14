from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import inspect
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from agent_runner import AgentRunBlocked, AgentRunner
from agent_runtime import ProviderRegistry
from c1_fixture_normalization import CLAIMS, FixtureNormalizationError, NORMALIZATION_KIND, REMOTE_FIELDS, normalize_c1_fixture_handoff
from handoff_validator import load_contract, validate_handoff
from json_schema_subset import SchemaCompatibilityError, SchemaSubsetError, validate as validate_schema, validate_schema_compatibility
from providers.codex_exec_provider import (
    INJECTED_RUNTIME_VERIFICATION_SUCCESS,
    CodexExecProvider,
    CodexProviderConfigurationError,
    RuntimeVerificationResult,
)
from run_records import atomic_json


AUTOMATION = Path(__file__).resolve().parent
WORKSPACE = AUTOMATION / "fixtures" / "real_codex_fixture_workspace"
CONTRACTS = WORKSPACE / "contracts"
SCHEMA = WORKSPACE / "strategist_handoff_output.schema.json"
CANONICAL_SCHEMA = WORKSPACE / "strategist_handoff_canonical.schema.json"
PROMPT = WORKSPACE / "strategist_prompt_template.txt"
INPUT = WORKSPACE / "synthetic_case_input.json"
STANDARD = WORKSPACE / "content_standard_fixture.md"
COMMAND_ENV = "COLD_TRUTH_CODEX_RUNTIME_COMMAND"
VERIFIED_NODE = Path(r"C:\Program Files\nodejs\node.exe")
NPM_WRAPPER_DIRECTORY = Path(r"C:\Users\brody\AppData\Roaming\npm")
CODEX_JS_ENTRY = NPM_WRAPPER_DIRECTORY / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
CHILD_TEMP_DIRECTORY = WORKSPACE / "output" / "c1_child_tmp"


@contextmanager
def temporary_runtime_command(tokens: list[str]):
    if COMMAND_ENV in os.environ:
        raise RuntimeError(f"{COMMAND_ENV} must be absent before the fixture test; its existing value was not read")
    os.environ[COMMAND_ENV] = json.dumps(tokens)
    try:
        yield
    finally:
        os.environ.pop(COMMAND_ENV, None)


def provider(*, process_runner=None, timeout=15.0, runtime_verifier=None) -> CodexExecProvider:
    return CodexExecProvider(
        WORKSPACE,
        SCHEMA,
        CANONICAL_SCHEMA,
        PROMPT,
        VERIFIED_NODE,
        NPM_WRAPPER_DIRECTORY,
        CODEX_JS_ENTRY,
        CHILD_TEMP_DIRECTORY,
        timeout_seconds=timeout,
        process_runner=process_runner,
        runtime_verifier=runtime_verifier,
    )


def exact_runtime_allowlist_verifier(node_path: Path, codex_entry_path: Path) -> RuntimeVerificationResult:
    expected_node = Path(r"C:\Program Files\nodejs\node.exe")
    expected_entry = Path(r"C:\Users\brody\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js")
    accepted = (
        node_path.is_absolute()
        and codex_entry_path.is_absolute()
        and os.path.normcase(os.path.abspath(node_path)) == os.path.normcase(os.path.abspath(expected_node))
        and os.path.normcase(os.path.abspath(codex_entry_path)) == os.path.normcase(os.path.abspath(expected_entry))
    )
    return RuntimeVerificationResult(
        accepted,
        INJECTED_RUNTIME_VERIFICATION_SUCCESS if accepted else "static_runtime_path_mismatch",
    )


def safe_tokens(*extra: str) -> list[str]:
    return [str(NPM_WRAPPER_DIRECTORY / "codex.cmd"), "exec", *extra]


def request_envelope(output_root: Path) -> dict:
    fixture_value = json.loads(INPUT.read_text(encoding="utf-8"))
    standard_value = STANDARD.read_text(encoding="utf-8")
    canonical_fixture = json.dumps(fixture_value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    canonical_standard = json.dumps(standard_value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    inputs = [
        {"name": "batch_size", "type": "integer", "kind": "value", "value": 1, "sha256": hashlib.sha256(b"1").hexdigest()},
        {"name": "candidate_queue", "type": "backlog_or_queue", "kind": "value", "value": fixture_value, "sha256": hashlib.sha256(canonical_fixture).hexdigest()},
        {"name": "content_standard", "type": "policy_document", "kind": "value", "value": standard_value, "sha256": hashlib.sha256(canonical_standard).hexdigest()},
    ]
    return {
        "schema_version": "1.0",
        "run_id": "phase-c1-real-codex-fixture",
        "case_id": "glass-harbor-fixture",
        "stage": "strategist_fixture",
        "contract_id": "cold-truth.strategist",
        "contract_version": "1.0.0-c1-fixture",
        "inputs": inputs,
        "permissions": {
            "allowed_actions": [
                "select supplied synthetic candidate",
                "list supplied synthetic claim ids",
                "assign supplied synthetic viability status",
            ],
            "network": False,
            "external_commands": False,
            "external_tools": False,
            "media_creation": False,
            "publishing": False,
            "platform_api": False,
            "secrets": False,
        },
        "mode": "controlled-real-fixture",
        "provider_id": "codex-exec-controlled-fixture-v1",
        "failure_mode": None,
        "reset_token": "",
        "idempotency_key": "0" * 64,
        "output_root": str(output_root.resolve()),
        "execution_origin": "orchestrated_agent",
    }


def canonical_handoff(output_root: Path) -> dict:
    request = request_envelope(output_root)
    return {
        "schema_version": "1.0",
        "contract_id": "cold-truth.strategist",
        "contract_version": "1.0.0-c1-fixture",
        "run_id": "phase-c1-real-codex-fixture",
        "case_id": "glass-harbor-fixture",
        "stage": "strategist_fixture",
        "attempt": 1,
        "idempotency_key": "0" * 64,
        "status": "success",
        "started_at": "2026-07-11T00:00:00Z",
        "completed_at": "2026-07-11T00:00:00Z",
        "inputs": request["inputs"],
        "outputs": [],
        "result": {
            "candidate_id": "glass-harbor-fixture",
            "claim_ids": list(CLAIMS),
            "viability": "Standard long-form viable",
            "score_total": 30,
            "score_breakdown": {"long_form_source_depth": 5, "clear_chronological_narrative": 4, "legal_and_misinformation_risk": 5},
            "risk_level": "synthetic-none",
            "artifact_hashes": {},
            "recommended_disposition": "select",
        },
        "decisions": [{"rule": "fixture_input_only", "result": "pass"}],
        "warnings": [],
        "errors": [],
        "retryable": False,
        "tool_calls": [],
        "runtime": {"provider": "codex-exec", "runtime": "controlled-real-fixture", "model": "not-reported", "version": "not-reported"},
        "publishing_enabled": False,
    }


def remote_handoff(output_root: Path) -> dict:
    remote = copy.deepcopy(canonical_handoff(output_root))
    candidate = next(item for item in remote["inputs"] if item["name"] == "candidate_queue")["value"]
    del candidate["claim_ids"]
    result = remote["result"]
    del result["claim_ids"]
    for name, claim in zip(REMOTE_FIELDS, CLAIMS):
        candidate[name] = claim
        result[name] = claim
    return remote


class CodexProviderSafetyTests(unittest.TestCase):
    def test_fixture_schema_is_strict_and_codex_compatible(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validate_schema_compatibility(schema)
        self.assertEqual(schema["properties"]["schema_version"], {"type": "string", "enum": ["1.0"]})
        self.assertEqual(schema["properties"]["case_id"]["enum"], ["glass-harbor-fixture"])
        result_properties = schema["properties"]["result"]["properties"]
        self.assertEqual(result_properties["claim_1"], {"type": "string", "enum": ["SYN-C1-01"]})
        self.assertEqual(result_properties["claim_2"], {"type": "string", "enum": ["SYN-C1-02"]})
        self.assertEqual(result_properties["claim_3"], {"type": "string", "enum": ["SYN-C1-03"]})
        self.assertEqual(schema["properties"]["result"]["properties"]["viability"]["enum"], ["Standard long-form viable"])
        self.assertEqual(schema["properties"]["result"]["properties"]["score_total"]["enum"], [30])
        self.assertEqual(schema["properties"]["publishing_enabled"], {"type": "boolean", "enum": [False]})

        missing_type = copy.deepcopy(schema)
        del missing_type["properties"]["schema_version"]["type"]
        with self.assertRaises(SchemaCompatibilityError):
            validate_schema_compatibility(missing_type)

        former_array_const = {
            "type": "object",
            "required": ["claim_ids"],
            "properties": {
                "claim_ids": {"type": "array", "const": list(CLAIMS), "items": {"type": "string"}}
            },
            "additionalProperties": False,
        }
        with self.assertRaises(SchemaCompatibilityError):
            validate_schema_compatibility(former_array_const)

    def test_fixture_claim_normalization_is_strict_and_canonical(self) -> None:
        output = WORKSPACE / "output" / "normalization-test"
        remote_schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        canonical_schema = json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8"))
        remote = remote_handoff(output)
        validate_schema(remote, remote_schema)
        normalized = normalize_c1_fixture_handoff(remote)
        self.assertEqual(normalized["result"]["claim_ids"], list(CLAIMS))
        candidate = next(item for item in normalized["inputs"] if item["name"] == "candidate_queue")["value"]
        self.assertEqual(candidate["claim_ids"], list(CLAIMS))
        self.assertTrue(all(name not in normalized["result"] and name not in candidate for name in REMOTE_FIELDS))
        validate_schema(normalized, canonical_schema)
        validate_handoff(normalized, load_contract(CONTRACTS / "strategist.contract.json"), request_envelope(output), output)

        containers = {
            "result": lambda handoff: handoff["result"],
            "candidate_input": lambda handoff: next(item for item in handoff["inputs"] if item["name"] == "candidate_queue")["value"],
        }
        for label, select in containers.items():
            for name in REMOTE_FIELDS:
                altered = copy.deepcopy(remote)
                select(altered)[name] = "SYN-C1-99"
                with self.subTest(container=label, altered=name), self.assertRaises(FixtureNormalizationError):
                    normalize_c1_fixture_handoff(altered)
                missing = copy.deepcopy(remote)
                del select(missing)[name]
                with self.subTest(container=label, missing=name), self.assertRaises(FixtureNormalizationError):
                    normalize_c1_fixture_handoff(missing)

        extra = copy.deepcopy(remote)
        extra["result"]["claim_4"] = "SYN-C1-04"
        with self.assertRaises(SchemaSubsetError):
            validate_schema(extra, remote_schema)
        publishing = {**remote, "publishing_enabled": True}
        with self.assertRaises(SchemaSubsetError):
            validate_schema(publishing, remote_schema)

    def test_provider_records_fixture_normalization_metadata(self) -> None:
        output = WORKSPACE / "output" / "provider-normalization-test"
        output.mkdir(parents=True, exist_ok=True)

        fake_call_count = 0

        def remote_runner(command, **kwargs):
            nonlocal fake_call_count
            fake_call_count += 1
            path = Path(command[command.index("--output-last-message") + 1])
            path.write_text(json.dumps(remote_handoff(output)) + "\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout='{"type":"fixture"}\n', stderr="")

        with temporary_runtime_command(safe_tokens()):
            result = provider(process_runner=remote_runner, runtime_verifier=exact_runtime_allowlist_verifier).execute(request_envelope(output), output, 1)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(fake_call_count, 1)
        self.assertEqual(result.runtime_metadata["runtime_verification_mode"], "explicit_injected_test_dependency")
        self.assertTrue(result.runtime_metadata["remote_output_normalized"])
        self.assertEqual(result.runtime_metadata["normalization_kind"], NORMALIZATION_KIND)
        normalized = json.loads(result.handoff_path.read_text(encoding="utf-8"))
        self.assertEqual(normalized["result"]["claim_ids"], list(CLAIMS))
        self.assertTrue((output / "remote_strategist_handoff.json").is_file())

    def test_minimal_child_environment_is_exact_and_not_inherited(self) -> None:
        instance = provider(runtime_verifier=exact_runtime_allowlist_verifier)
        child = instance.minimal_child_environment()
        self.assertEqual(set(child), {"PATH", "SystemRoot", "ComSpec", "TEMP", "TMP"})
        self.assertEqual(child["PATH"].split(";"), [str(VERIFIED_NODE.parent), str(NPM_WRAPPER_DIRECTORY)])
        self.assertEqual(Path(child["TEMP"]), CHILD_TEMP_DIRECTORY.resolve())
        self.assertEqual(child["TMP"], child["TEMP"])
        self.assertFalse(any(name.upper() in {"API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"} for name in child))
        self.assertEqual(instance.child_environment_metadata(), {
            "node_path_present": True,
            "npm_wrapper_path_present": True,
            "child_environment_mode": "minimal_allowlist",
            "runtime_verification_mode": "explicit_injected_test_dependency",
            "inherited_environment": False,
        })

    def test_process_launch_preserves_shell_false_and_minimal_environment(self) -> None:
        observed = {}

        def fake_runner(command, **kwargs):
            observed["command"] = command
            observed.update(kwargs)
            return subprocess.CompletedProcess(command, 7, stdout="", stderr="fixture stop")

        output = WORKSPACE / "output" / "environment-launch-test"
        output.mkdir(parents=True, exist_ok=True)
        with temporary_runtime_command([r"C:\Users\brody\AppData\Roaming\npm\codex.cmd", "exec"]):
            provider(process_runner=fake_runner, runtime_verifier=exact_runtime_allowlist_verifier).execute(request_envelope(output), output, 1)
        self.assertIs(observed["shell"], False)
        self.assertEqual(set(observed["env"]), {"PATH", "SystemRoot", "ComSpec", "TEMP", "TMP"})
        self.assertEqual(observed["env"]["PATH"].split(";"), [str(VERIFIED_NODE.parent), str(NPM_WRAPPER_DIRECTORY)])
        self.assertEqual(Path(observed["cwd"]), WORKSPACE.resolve())
        self.assertIsInstance(observed["command"], list)
        self.assertEqual(observed["command"][0], os.path.abspath(VERIFIED_NODE))
        self.assertEqual(observed["command"][1], os.path.abspath(CODEX_JS_ENTRY))

    def test_command_shape_enforces_exec_workspace_json_schema_and_ephemeral(self) -> None:
        output = WORKSPACE / "output" / "shape-test"
        with temporary_runtime_command(safe_tokens()):
            command = provider(runtime_verifier=exact_runtime_allowlist_verifier).build_command(output, output / "strategist_handoff.json")
        self.assertIsInstance(command, list)
        self.assertEqual(command[0], os.path.abspath(VERIFIED_NODE))
        self.assertEqual(command[1], os.path.abspath(CODEX_JS_ENTRY))
        self.assertEqual(command[2], "exec")
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
        cd_value = command[command.index("--cd") + 1]
        self.assertEqual(Path(cd_value), WORKSPACE.resolve())
        self.assertFalse(cd_value.startswith(('"', "'")))
        self.assertIn("--json", command)
        self.assertIn("--output-schema", command)
        self.assertIn("--output-last-message", command)
        schema_value = command[command.index("--output-schema") + 1]
        handoff_value = command[command.index("--output-last-message") + 1]
        self.assertEqual(Path(schema_value), SCHEMA.resolve())
        self.assertEqual(Path(handoff_value), (output / "strategist_handoff.json").resolve())
        self.assertFalse(schema_value.startswith(('"', "'")))
        self.assertFalse(handoff_value.startswith(('"', "'")))
        self.assertIn("--ephemeral", command)
        self.assertEqual(command[-1], "-")

    def test_dangerous_runtime_options_are_rejected(self) -> None:
        for flag in ("--yolo", "--dangerously-bypass-approvals-and-sandbox", "--dangerously-bypass-hook-trust", "danger-full-access", "--full-auto", "--ignore-rules", "--add-dir"):
            with self.subTest(flag=flag), temporary_runtime_command(safe_tokens(flag)):
                with self.assertRaises(CodexProviderConfigurationError):
                    provider().runtime_tokens()

    def test_verified_npm_cmd_builds_direct_node_argument_list(self) -> None:
        npm_cli = r"C:\Users\brody\AppData\Roaming\npm\codex.cmd"
        output = WORKSPACE / "output" / "npm-wrapper-test"
        with temporary_runtime_command([npm_cli, "exec"]):
            command = provider(runtime_verifier=exact_runtime_allowlist_verifier).build_command(output, output / "strategist_handoff.json")
        self.assertEqual(command[:3], [os.path.abspath(VERIFIED_NODE), os.path.abspath(CODEX_JS_ENTRY), "exec"])
        lowered = " ".join(command).lower()
        for prohibited in ("cmd.exe", "powershell.exe", "windowsapps", "--yolo", "--dangerously-bypass-approvals-and-sandbox", "--dangerously-bypass-hook-trust", "danger-full-access", "--full-auto", "--ignore-rules", "--add-dir"):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, lowered)

    def test_windowsapps_launcher_is_rejected(self) -> None:
        blocked = r"C:\Program Files\WindowsApps\OpenAI.Codex_fixture\app\resources\codex.exe"
        with temporary_runtime_command([blocked, "exec"]):
            with self.assertRaises(CodexProviderConfigurationError):
                provider().runtime_tokens()

    def test_working_and_output_paths_are_contained(self) -> None:
        outside = WORKSPACE.parent / "outside-not-created"
        with temporary_runtime_command(safe_tokens()):
            with self.assertRaises(CodexProviderConfigurationError):
                provider().build_command(outside, outside / "handoff.json")
            valid_root = WORKSPACE / "output" / "contained"
            with self.assertRaises(CodexProviderConfigurationError):
                provider().build_command(valid_root, WORKSPACE / "output" / "wrong-folder.json")
        self.assertFalse(outside.exists())

    def test_prompt_rejects_real_case_tool_media_network_and_platform_content(self) -> None:
        rejected = [
            "Open 2_IN_PRODUCTION\\Named Case",
            "Use MCP",
            "Browse for facts",
            "Call ElevenLabs",
            "Create an FCPXML",
            "Upload to a platform",
            "Authorization: Bearer fixturecredentialvalue123456",
        ]
        for value in rejected:
            with self.subTest(value=value):
                with self.assertRaises(CodexProviderConfigurationError):
                    provider().validate_prompt(value)

    def test_request_with_broader_tools_is_rejected(self) -> None:
        output = WORKSPACE / "output" / "request-test"
        request = request_envelope(output)
        request["permissions"]["external_tools"] = True
        with self.assertRaises(CodexProviderConfigurationError):
            provider().validate_request(request, output)
        request = request_envelope(output)
        request["permissions"]["allowed_actions"].append("perform unrelated work")
        with self.assertRaises(CodexProviderConfigurationError):
            provider().validate_request(request, output)

    def test_runtime_command_value_is_not_exposed_and_secret_arguments_are_rejected(self) -> None:
        sensitive = "api_key=fixture-sensitive-value-1234567890"
        with temporary_runtime_command(safe_tokens("--config", sensitive)):
            with self.assertRaises(CodexProviderConfigurationError):
                provider().runtime_tokens()
        shape_text = json.dumps(provider().safe_command_shape())
        self.assertNotIn("FixtureOnly", shape_text)
        self.assertNotIn("sensitive", shape_text)

    def test_provider_reads_only_allowed_environment_reference(self) -> None:
        source = (AUTOMATION / "providers" / "codex_exec_provider.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        environment_reads = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"get", "getenv"}:
                target = node.func.value
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "os" and target.attr == "environ":
                    environment_reads.append(node)
                if isinstance(target, ast.Name) and target.id == "os" and node.func.attr == "getenv":
                    environment_reads.append(node)
        self.assertEqual(len(environment_reads), 1)

    def test_local_schema_and_contract_accept_only_expected_fixture_handoff(self) -> None:
        output = WORKSPACE / "output" / "schema-test"
        request = request_envelope(output)
        handoff = canonical_handoff(output)
        validate_schema(handoff, json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8")))
        validate_handoff(handoff, load_contract(CONTRACTS / "strategist.contract.json"), request, output)
        malformed = {**handoff, "result": {**handoff["result"], "claim_ids": ["SYN-C1-01", "SYN-C1-02", "SYN-C1-02"]}}
        with self.assertRaises(SchemaSubsetError):
            validate_schema(malformed, json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8")))
        publishing_enabled = {**handoff, "publishing_enabled": True}
        with self.assertRaises(SchemaSubsetError):
            validate_schema(publishing_enabled, json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8")))

    def test_malformed_final_artifact_is_blocked_and_recorded(self) -> None:
        def malformed_runner(command, **kwargs):
            path = Path(command[command.index("--output-last-message") + 1])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout='{"type":"fixture"}\n', stderr="")

        with tempfile.TemporaryDirectory(dir=WORKSPACE / "output") as temp, temporary_runtime_command(safe_tokens()):
            run_root = Path(temp)
            registry = ProviderRegistry()
            registry.register(provider(process_runner=malformed_runner, runtime_verifier=exact_runtime_allowlist_verifier), ["cold-truth.strategist"])
            runner = AgentRunner(CONTRACTS, run_root, registry, mode="controlled-real-fixture")
            with self.assertRaises(AgentRunBlocked):
                runner.run(
                    "cold-truth.strategist",
                    run_id="phase-c1-real-codex-fixture",
                    case_id="glass-harbor-fixture",
                    stage="strategist_fixture",
                    inputs={"candidate_queue": json.loads(INPUT.read_text(encoding="utf-8")), "batch_size": 1, "content_standard": STANDARD.read_text(encoding="utf-8")},
                )
            records = list(run_root.rglob("record.json"))
            self.assertEqual(len(records), 1)
            record = json.loads(records[0].read_text(encoding="utf-8"))
            self.assertEqual(record["validation"]["status"], "blocked_provider_failure")
            self.assertEqual(record["exit_code"], 65)

    def test_timeout_and_nonzero_exit_are_blocked_and_recorded(self) -> None:
        def timeout_runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        def nonzero_runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 7, stdout="", stderr="configured fixture failure")

        for label, fake, expected in (("timeout", timeout_runner, 124), ("nonzero", nonzero_runner, 7)):
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=WORKSPACE / "output") as temp, temporary_runtime_command(safe_tokens()):
                run_root = Path(temp)
                registry = ProviderRegistry()
                registry.register(provider(process_runner=fake, timeout=1, runtime_verifier=exact_runtime_allowlist_verifier), ["cold-truth.strategist"])
                runner = AgentRunner(CONTRACTS, run_root, registry, mode="controlled-real-fixture")
                with self.assertRaises(AgentRunBlocked):
                    runner.run(
                        "cold-truth.strategist",
                        run_id="phase-c1-real-codex-fixture",
                        case_id="glass-harbor-fixture",
                        stage="strategist_fixture",
                        inputs={"candidate_queue": json.loads(INPUT.read_text(encoding="utf-8")), "batch_size": 1, "content_standard": STANDARD.read_text(encoding="utf-8")},
                    )
                record_path = next(run_root.rglob("record.json"))
                record = json.loads(record_path.read_text(encoding="utf-8"))
                self.assertEqual(record["exit_code"], expected)
                self.assertEqual(record["validation"]["status"], "blocked_provider_failure")

    def test_injected_runtime_verifier_is_lexical_exact_and_metadata_free(self) -> None:
        accepted = exact_runtime_allowlist_verifier(VERIFIED_NODE, CODEX_JS_ENTRY)
        self.assertEqual(accepted, RuntimeVerificationResult(True, INJECTED_RUNTIME_VERIFICATION_SUCCESS))
        rejected = (
            exact_runtime_allowlist_verifier(Path("node.exe"), CODEX_JS_ENTRY),
            exact_runtime_allowlist_verifier(VERIFIED_NODE.with_name("altered.exe"), CODEX_JS_ENTRY),
            exact_runtime_allowlist_verifier(VERIFIED_NODE, CODEX_JS_ENTRY.with_name("altered.js")),
        )
        for result in rejected:
            self.assertEqual(result, RuntimeVerificationResult(False, "static_runtime_path_mismatch"))
        source = inspect.getsource(exact_runtime_allowlist_verifier).lower()
        for forbidden in ("exists(", "is_file(", "stat(", "access(", "get-item", "subprocess", "system(", "popen(", "http://", "https://"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_default_provider_still_uses_installed_filesystem_verification(self) -> None:
        default_provider = provider()
        self.assertIsNone(default_provider.runtime_verifier)
        source = inspect.getsource(CodexExecProvider.verify_runtime_paths)
        self.assertIn("self.runtime_verifier is None", source)
        self.assertIn("self.node_executable.is_file()", source)
        self.assertIn("self.codex_js_entry.is_file()", source)


def run_real_once(codex_executable: Path) -> dict:
    run_root = WORKSPACE / "output" / "c1_remote_normalized_final_run"
    marker = run_root / "REAL_INVOCATION_ATTEMPT.json"
    if marker.exists():
        return {"status": "BLOCKED_ALREADY_ATTEMPTED", "marker": str(marker)}
    run_root.mkdir(parents=True, exist_ok=True)
    atomic_json(marker, {"status": "STARTED", "fixture_only": True, "real_production_enabled": False, "publishing_enabled": False})
    result = {"status": "BLOCKED", "fixture_only": True, "real_production_enabled": False, "publishing_enabled": False}
    try:
        with temporary_runtime_command([str(codex_executable.resolve()), "exec"]):
            registry = ProviderRegistry()
            registry.register(provider(timeout=120), ["cold-truth.strategist"])
            runner = AgentRunner(CONTRACTS, run_root, registry, mode="controlled-real-fixture")
            try:
                execution = runner.run(
                    "cold-truth.strategist",
                    run_id="phase-c1-real-codex-fixture",
                    case_id="glass-harbor-fixture",
                    stage="strategist_fixture",
                    inputs={"candidate_queue": json.loads(INPUT.read_text(encoding="utf-8")), "batch_size": 1, "content_standard": STANDARD.read_text(encoding="utf-8")},
                )
                fixture = json.loads(INPUT.read_text(encoding="utf-8"))
                if execution.handoff["result"]["claim_ids"] != fixture["claim_ids"]:
                    raise RuntimeError("Validated handoff claim IDs do not match fixture")
                result = {
                    "status": "PASSED",
                    "fixture_only": True,
                    "idempotency_key": execution.idempotency_key,
                    "handoff_sha256": hashlib.sha256(execution.handoff_path.read_bytes()).hexdigest(),
                    "record_path": str(execution.record_path),
                    "real_production_enabled": False,
                    "publishing_enabled": False,
                }
            except AgentRunBlocked as exc:
                result["blocker"] = str(exc)
    except (CodexProviderConfigurationError, OSError, RuntimeError) as exc:
        result["blocker"] = f"{type(exc).__name__}: {exc}"
    atomic_json(marker, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase C1 controlled real Codex fixture test")
    parser.add_argument("--run-real", action="store_true", help="After safety tests, attempt exactly one real Codex fixture invocation")
    parser.add_argument("--codex-executable", type=Path, help="Explicit non-secret path used only to set the process-local runtime command")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CodexProviderSafetyTests)
    tests = unittest.TextTestRunner(verbosity=2).run(suite)
    if not tests.wasSuccessful():
        raise SystemExit(1)
    if not args.run_real:
        print(json.dumps({"safety_tests": "passed", "real_invocation": "not_requested"}, indent=2))
        return
    if args.codex_executable is None:
        print(json.dumps({"safety_tests": "passed", "real_invocation": "BLOCKED", "blocker": "--codex-executable is required"}, indent=2))
        raise SystemExit(2)
    result = run_real_once(args.codex_executable)
    print(json.dumps({"safety_tests": "passed", "real_invocation": result}, indent=2))
    if result["status"] != "PASSED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
