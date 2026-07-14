from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from agent_runner import AgentRunBlocked, AgentRunner
from agent_runtime import ProviderRegistry
from c2_fixture_normalization import APPROVED, NORMALIZATION_KIND, REJECTED, SOURCE_CONFLICTS, UNSUPPORTED_MATERIAL, ResearchVerifierNormalizationError, normalize_c2_research_verifier_handoff
from handoff_validator import file_sha256, load_contract, validate_handoff
from json_schema_subset import SchemaSubsetError, validate as validate_schema, validate_schema_compatibility
from providers.codex_exec_provider import (
    INJECTED_RUNTIME_VERIFICATION_SUCCESS,
    CodexExecProvider,
    CodexProviderConfigurationError,
    RuntimeVerificationResult,
)
from providers.research_verifier_codex_provider import ResearchVerifierCodexProvider
from run_records import atomic_json


AUTOMATION = Path(__file__).resolve().parent
WORKSPACE = AUTOMATION / "fixtures" / "real_research_verifier_fixture_workspace"
CONTRACTS = WORKSPACE / "contracts"
REMOTE_SCHEMA = WORKSPACE / "research_verifier_remote.schema.json"
CANONICAL_SCHEMA = WORKSPACE / "research_verifier_canonical.schema.json"
PROMPT = WORKSPACE / "research_verifier_prompt_template.txt"
STRATEGIST = WORKSPACE / "synthetic_strategist_handoff.json"
LEDGER = WORKSPACE / "synthetic_source_ledger.json"
BOUNDARIES = WORKSPACE / "synthetic_research_boundaries.json"
VERIFIED_NODE = Path(r"C:\Program Files\nodejs\node.exe")
NPM_ROOT = Path(r"C:\Users\brody\AppData\Roaming\npm")
CODEX_ENTRY = NPM_ROOT / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
CHILD_TEMP = WORKSPACE / "output" / "c2_child_tmp"
COMMAND_ENV = "COLD_TRUTH_CODEX_RUNTIME_COMMAND"
MINIMAL_C2_FIXTURE_FILES = (
    "research_verifier_remote.schema.json",
    "research_verifier_canonical.schema.json",
    "research_verifier_prompt_template.txt",
    "synthetic_strategist_handoff.json",
    "synthetic_source_ledger.json",
    "synthetic_research_boundaries.json",
    "contracts/research_verifier.contract.json",
)


@contextmanager
def temporary_runtime_command(tokens: list[str]):
    if COMMAND_ENV in os.environ:
        raise RuntimeError(f"{COMMAND_ENV} must be absent; its value was not read")
    os.environ[COMMAND_ENV] = json.dumps(tokens)
    try:
        yield
    finally:
        os.environ.pop(COMMAND_ENV, None)


def provider(*, process_runner=None, timeout=15.0, runtime_verifier=None) -> ResearchVerifierCodexProvider:
    return ResearchVerifierCodexProvider(
        WORKSPACE, REMOTE_SCHEMA, CANONICAL_SCHEMA, PROMPT,
        VERIFIED_NODE, NPM_ROOT, CODEX_ENTRY, CHILD_TEMP,
        timeout_seconds=timeout, process_runner=process_runner,
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


@contextmanager
def isolated_c2_provider_test_workspace():
    with tempfile.TemporaryDirectory(prefix="c2-provider-test-", dir=AUTOMATION) as temporary:
        test_workspace = Path(temporary) / "fixture"
        for relative_name in MINIMAL_C2_FIXTURE_FILES:
            source = WORKSPACE / relative_name
            destination = test_workspace / relative_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        output = test_workspace / "output" / "provider-test"
        output.mkdir(parents=True, exist_ok=True)
        contracts = test_workspace / "contracts"
        request = request_envelope(output, test_workspace, contracts)
        yield test_workspace, output, request


def isolated_fake_provider(*, test_workspace: Path, process_runner, runtime_verifier) -> ResearchVerifierCodexProvider:
    return ResearchVerifierCodexProvider(
        test_workspace,
        test_workspace / "research_verifier_remote.schema.json",
        test_workspace / "research_verifier_canonical.schema.json",
        test_workspace / "research_verifier_prompt_template.txt",
        VERIFIED_NODE,
        NPM_ROOT,
        CODEX_ENTRY,
        test_workspace / "output" / "c2_child_tmp",
        timeout_seconds=15.0,
        process_runner=process_runner,
        runtime_verifier=runtime_verifier,
    )


def input_descriptors(workspace: Path = WORKSPACE) -> list[dict]:
    declared = {
        "synthetic_research_boundaries": ("synthetic_research_boundaries", workspace / "synthetic_research_boundaries.json"),
        "synthetic_source_ledger": ("synthetic_source_ledger", workspace / "synthetic_source_ledger.json"),
        "synthetic_strategist_handoff": ("synthetic_strategist_handoff", workspace / "synthetic_strategist_handoff.json"),
    }
    return [
        {"name": name, "type": item_type, "kind": "file", "path": str(path.resolve()), "sha256": file_sha256(path), "size_bytes": path.stat().st_size}
        for name, (item_type, path) in sorted(declared.items())
    ]


def request_envelope(output_root: Path, workspace: Path = WORKSPACE, contracts: Path = CONTRACTS) -> dict:
    actions = list(load_contract(contracts / "research_verifier.contract.json")["allowed_actions"])
    return {
        "schema_version": "1.0",
        "run_id": "phase-c2-research-verifier-fixture",
        "case_id": "glass-river-research-fixture",
        "stage": "research_verification_fixture",
        "contract_id": "cold-truth.research-verifier",
        "contract_version": "1.0.0-c2-fixture",
        "inputs": input_descriptors(workspace),
        "permissions": {"allowed_actions": actions, "network": False, "external_commands": False, "external_tools": False, "media_creation": False, "publishing": False, "platform_api": False, "secrets": False},
        "mode": "controlled-real-fixture",
        "provider_id": provider().provider_id,
        "failure_mode": None,
        "reset_token": "",
        "idempotency_key": "0" * 64,
        "output_root": str(output_root.resolve()),
        "execution_origin": "orchestrated_agent",
    }


def remote_handoff(output_root: Path, request: dict | None = None) -> dict:
    request = request or request_envelope(output_root)
    hashes = {item["name"]: item["sha256"] for item in request["inputs"]}
    return {
        "schema_version": "1.0", "contract_id": "cold-truth.research-verifier", "contract_version": "1.0.0-c2-fixture",
        "run_id": "phase-c2-research-verifier-fixture", "case_id": "glass-river-research-fixture", "stage": "research_verification_fixture",
        "attempt": 1, "idempotency_key": "0" * 64, "status": "success",
        "started_at": "2026-07-11T00:00:00Z", "completed_at": "2026-07-11T00:00:00Z", "inputs": request["inputs"], "outputs": [],
        "result": {
            "upstream_strategist_handoff_hash": hashes["synthetic_strategist_handoff"],
            "ledger_hash": hashes["synthetic_source_ledger"], "boundaries_hash": hashes["synthetic_research_boundaries"],
            "approved_claim_1": APPROVED[0], "approved_claim_2": APPROVED[1], "approved_claim_3": APPROVED[2],
            "rejected_claim_1": REJECTED[0][0], "rejected_reason_1": REJECTED[0][1],
            "rejected_claim_2": REJECTED[1][0], "rejected_reason_2": REJECTED[1][1],
            "rejected_claim_3": REJECTED[2][0], "rejected_reason_3": REJECTED[2][1],
            "source_conflicts": list(SOURCE_CONFLICTS), "unsupported_or_creator_derived_material": list(UNSUPPORTED_MATERIAL), "verification_status": "approved_with_exclusions",
            "proceed_to_writer": True, "required_human_escalation": False, "artifact_hashes": {},
            "external_research_performed": False, "browser_used": False, "mcp_used": False, "network_used": False,
        },
        "decisions": [{"rule": "synthetic_fixture_only", "result": "pass"}], "warnings": [], "errors": [], "retryable": False, "tool_calls": [],
        "runtime": {"provider": "codex-exec", "runtime": "controlled-real-fixture", "model": "not-reported", "version": "not-reported"},
        "publishing_enabled": False, "real_production_enabled": False,
    }


class ResearchVerifierFixtureTests(unittest.TestCase):
    def test_synthetic_inputs_are_exact_and_offline(self) -> None:
        strategist = json.loads(STRATEGIST.read_text(encoding="utf-8"))
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        boundaries = json.loads(BOUNDARIES.read_text(encoding="utf-8"))
        self.assertEqual(strategist["claim_ids"], [*APPROVED, *(item[0] for item in REJECTED)])
        self.assertEqual([item["supports"][0] for item in ledger["sources"]], list(APPROVED))
        self.assertEqual([item["claim_id"] for item in boundaries["rejected_claims"]], [item[0] for item in REJECTED])
        combined = " ".join(path.read_text(encoding="utf-8") for path in (STRATEGIST, LEDGER, BOUNDARIES, PROMPT)).lower()
        self.assertNotIn("http://", combined)
        self.assertNotIn("https://", combined)

    def test_remote_schema_normalization_canonical_schema_and_contract_pass(self) -> None:
        output = WORKSPACE / "output" / "schema-test"
        remote_schema = json.loads(REMOTE_SCHEMA.read_text(encoding="utf-8"))
        validate_schema_compatibility(remote_schema)
        remote = remote_handoff(output)
        validate_schema(remote, remote_schema)
        canonical = normalize_c2_research_verifier_handoff(remote, request_envelope(output))
        validate_schema(canonical, json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8")))
        validate_handoff(canonical, load_contract(CONTRACTS / "research_verifier.contract.json"), request_envelope(output), output)
        self.assertEqual(canonical["result"]["approved_claim_ids"], list(APPROVED))
        self.assertEqual(canonical["result"]["rejected_claims"], [{"claim_id": c, "reason_code": r} for c, r in REJECTED])
        self.assertEqual(canonical["result"]["source_conflicts"], list(SOURCE_CONFLICTS))
        self.assertEqual(canonical["result"]["unsupported_or_creator_derived_material"], list(UNSUPPORTED_MATERIAL))

    def test_claim_and_reason_mutations_block(self) -> None:
        output = WORKSPACE / "output" / "mutation-test"
        base = remote_handoff(output)
        mutations = []
        for index in range(1, 4):
            for field in (f"approved_claim_{index}", f"rejected_claim_{index}", f"rejected_reason_{index}"):
                altered = copy.deepcopy(base); altered["result"][field] = "SYNTHETIC-INVALID"; mutations.append((field, altered))
                missing = copy.deepcopy(base); del missing["result"][field]; mutations.append((f"missing-{field}", missing))
        for label, value in mutations:
            with self.subTest(label=label), self.assertRaises(ResearchVerifierNormalizationError):
                normalize_c2_research_verifier_handoff(value, request_envelope(output))

    def test_hash_mismatch_blocks(self) -> None:
        output = WORKSPACE / "output" / "hash-test"
        remote = remote_handoff(output)
        remote["result"]["ledger_hash"] = "f" * 64
        with self.assertRaises(ResearchVerifierNormalizationError):
            normalize_c2_research_verifier_handoff(remote, request_envelope(output))

    def test_conflict_and_unsupported_classification_is_exact(self) -> None:
        output = WORKSPACE / "output" / "conflict-test"
        base = remote_handoff(output)
        malformed_values = (
            ("empty-conflict", []),
            ("changed-conflict", ["SYN-RV-X3: changed"]),
            ("duplicate-conflict", [*SOURCE_CONFLICTS, *SOURCE_CONFLICTS]),
            ("extra-conflict", [*SOURCE_CONFLICTS, "SYN-RV-X2: extra"]),
        )
        for label, conflicts in malformed_values:
            malformed = copy.deepcopy(base); malformed["result"]["source_conflicts"] = conflicts
            with self.subTest(label=label), self.assertRaises(ResearchVerifierNormalizationError):
                normalize_c2_research_verifier_handoff(malformed, request_envelope(output))
        x3_as_unsupported = copy.deepcopy(base)
        x3_as_unsupported["result"]["unsupported_or_creator_derived_material"] = ["SYN-RV-X3"]
        with self.assertRaises(ResearchVerifierNormalizationError):
            normalize_c2_research_verifier_handoff(x3_as_unsupported, request_envelope(output))

    def test_expected_fixed_values_and_external_activity_are_enforced(self) -> None:
        output = WORKSPACE / "output" / "fixed-test"
        schema = json.loads(REMOTE_SCHEMA.read_text(encoding="utf-8"))
        for field, value in (("proceed_to_writer", False), ("external_research_performed", True), ("browser_used", True), ("mcp_used", True), ("network_used", True)):
            malformed = remote_handoff(output); malformed["result"][field] = value
            with self.subTest(field=field), self.assertRaises(SchemaSubsetError): validate_schema(malformed, schema)
        for field in ("publishing_enabled", "real_production_enabled"):
            malformed = remote_handoff(output); malformed[field] = True
            with self.subTest(field=field), self.assertRaises(SchemaSubsetError): validate_schema(malformed, schema)
        tool = remote_handoff(output); tool["tool_calls"] = [{}]
        canonical = normalize_c2_research_verifier_handoff(tool, request_envelope(output))
        with self.assertRaises(SchemaSubsetError): validate_schema(canonical, json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8")))
        external = remote_handoff(output); external["result"]["unsupported_or_creator_derived_material"] = ["external-source"]
        with self.assertRaises(ResearchVerifierNormalizationError): normalize_c2_research_verifier_handoff(external, request_envelope(output))

    def test_path_escape_and_broader_permissions_block(self) -> None:
        output = WORKSPACE / "output" / "containment-test"
        request = request_envelope(output)
        request["inputs"][0]["path"] = str((WORKSPACE.parent / "outside-not-read.json").resolve())
        with self.assertRaises(CodexProviderConfigurationError): provider().validate_request(request, output)
        request = request_envelope(output); request["permissions"]["network"] = True
        with self.assertRaises(CodexProviderConfigurationError): provider().validate_request(request, output)

    def test_provider_uses_direct_node_and_records_normalization(self) -> None:
        with isolated_c2_provider_test_workspace() as (test_workspace, output, request):
            observed = {}
            fake_call_count = 0

            def fake(command, **kwargs):
                nonlocal fake_call_count
                fake_call_count += 1
                observed["command"] = command
                observed.update(kwargs)
                path = Path(command[command.index("--output-last-message") + 1])
                path.write_text(json.dumps(remote_handoff(output, request)) + "\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout='{"type":"fixture"}\n', stderr="")

            isolated_provider = isolated_fake_provider(
                test_workspace=test_workspace,
                process_runner=fake,
                runtime_verifier=exact_runtime_allowlist_verifier,
            )
            with temporary_runtime_command([str(NPM_ROOT / "codex.cmd"), "exec"]):
                result = isolated_provider.execute(request, output, 1)

            self.assertEqual(result.exit_code, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(fake_call_count, 1)
            self.assertIs(isolated_provider.runtime_verifier, exact_runtime_allowlist_verifier)
            self.assertEqual(observed["command"][:3], [os.path.abspath(VERIFIED_NODE), os.path.abspath(CODEX_ENTRY), "exec"])
            self.assertIs(observed["shell"], False)
            self.assertEqual(Path(observed["cwd"]), test_workspace.resolve())
            self.assertTrue(result.runtime_metadata["remote_output_normalized"])
            self.assertEqual(result.runtime_metadata["normalization_kind"], NORMALIZATION_KIND)
            self.assertEqual(set(observed["env"]), {"PATH", "SystemRoot", "ComSpec", "TEMP", "TMP"})

    def test_default_provider_retains_installed_filesystem_runtime_verification(self) -> None:
        default_provider = provider()
        self.assertIsNone(default_provider.runtime_verifier)
        source = inspect.getsource(CodexExecProvider.verify_runtime_paths)
        self.assertIn("self.runtime_verifier is None", source)
        self.assertIn("self.node_executable.is_file()", source)
        self.assertIn("self.codex_js_entry.is_file()", source)

    def test_injected_runtime_verifier_is_exact_and_rejects_altered_or_relative_paths(self) -> None:
        accepted = exact_runtime_allowlist_verifier(VERIFIED_NODE, CODEX_ENTRY)
        self.assertEqual(accepted, RuntimeVerificationResult(True, INJECTED_RUNTIME_VERIFICATION_SUCCESS))
        rejected = (
            exact_runtime_allowlist_verifier(Path("node.exe"), CODEX_ENTRY),
            exact_runtime_allowlist_verifier(VERIFIED_NODE.with_name("other.exe"), CODEX_ENTRY),
            exact_runtime_allowlist_verifier(VERIFIED_NODE, CODEX_ENTRY.with_name("other.js")),
        )
        for result in rejected:
            self.assertEqual(result, RuntimeVerificationResult(False, "static_runtime_path_mismatch"))

    def test_injected_runtime_verifier_has_no_filesystem_process_or_external_capability(self) -> None:
        source = inspect.getsource(exact_runtime_allowlist_verifier).lower()
        for forbidden in ("exists(", "is_file(", "stat(", "access(", "get-item", "subprocess", "system(", "popen(", "http://", "https://"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_injected_runtime_verifier_failure_is_fail_closed_and_sanitized(self) -> None:
        rejecting = provider(runtime_verifier=lambda _node, _entry: RuntimeVerificationResult(False, "static_runtime_path_mismatch"))
        with self.assertRaisesRegex(CodexProviderConfigurationError, "rejected the static runtime paths") as caught:
            rejecting.verify_runtime_paths()
        self.assertNotIn(str(VERIFIED_NODE), str(caught.exception))
        self.assertNotIn(str(CODEX_ENTRY), str(caught.exception))

    def test_oserror_runtime_result_is_sanitized_without_absolute_path(self) -> None:
        with isolated_c2_provider_test_workspace() as (test_workspace, output, request):
            def failing_fake(_command, **_kwargs):
                raise PermissionError(5, "Access is denied", r"C:\private\not-for-output.txt")
            isolated_provider = isolated_fake_provider(
                test_workspace=test_workspace,
                process_runner=failing_fake,
                runtime_verifier=exact_runtime_allowlist_verifier,
            )
            with temporary_runtime_command([str(NPM_ROOT / "codex.cmd"), "exec"]):
                result = isolated_provider.execute(request, output, 1)
            self.assertEqual(result.exit_code, 126)
            self.assertEqual(result.stderr, "Codex local runtime or test-output operation failed: PermissionError")
            self.assertNotIn("C:\\", result.stderr)


def run_real_once(codex_executable: Path) -> dict:
    run_root = WORKSPACE / "output" / "c2_final_research_verifier_run"
    marker = run_root / "REAL_INVOCATION_ATTEMPT.json"
    if marker.exists(): return {"status": "BLOCKED_ALREADY_ATTEMPTED", "marker": str(marker)}
    run_root.mkdir(parents=True, exist_ok=True)
    atomic_json(marker, {"status": "STARTED", "fixture_only": True, "real_production_enabled": False, "publishing_enabled": False})
    result = {"status": "BLOCKED", "fixture_only": True, "real_production_enabled": False, "publishing_enabled": False}
    try:
        with temporary_runtime_command([str(codex_executable.resolve()), "exec"]):
            registry = ProviderRegistry(); registry.register(provider(timeout=120), ["cold-truth.research-verifier"])
            runner = AgentRunner(CONTRACTS, run_root, registry, mode="controlled-real-fixture")
            execution = runner.run("cold-truth.research-verifier", run_id="phase-c2-research-verifier-fixture", case_id="glass-river-research-fixture", stage="research_verification_fixture", inputs={"synthetic_strategist_handoff": STRATEGIST, "synthetic_source_ledger": LEDGER, "synthetic_research_boundaries": BOUNDARIES})
            if execution.handoff["result"]["approved_claim_ids"] != list(APPROVED): raise RuntimeError("Approved claims mismatch")
            result = {"status": "PASSED", "fixture_only": True, "idempotency_key": execution.idempotency_key, "handoff_sha256": hashlib.sha256(execution.handoff_path.read_bytes()).hexdigest(), "record_path": str(execution.record_path), "real_production_enabled": False, "publishing_enabled": False}
    except (AgentRunBlocked, CodexProviderConfigurationError, OSError, RuntimeError) as exc:
        result["blocker"] = f"{type(exc).__name__}: {exc}"
    atomic_json(marker, result); return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase C2 synthetic Research Verifier fixture")
    parser.add_argument("--run-real", action="store_true")
    parser.add_argument("--codex-executable", type=Path)
    args = parser.parse_args()
    tests = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ResearchVerifierFixtureTests))
    if not tests.wasSuccessful(): raise SystemExit(1)
    if not args.run_real:
        print(json.dumps({"c2_offline_tests": "passed", "real_invocation": "not_requested"}, indent=2)); return
    if args.codex_executable is None: raise SystemExit("--codex-executable is required")
    result = run_real_once(args.codex_executable); print(json.dumps({"c2_offline_tests": "passed", "real_invocation": result}, indent=2))
    if result["status"] != "PASSED": raise SystemExit(2)


if __name__ == "__main__": main()
