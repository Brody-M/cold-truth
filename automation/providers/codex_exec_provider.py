"""Constrained Codex non-interactive provider for a real synthetic fixture test."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from agent_runtime import RuntimeResult
from c1_fixture_normalization import FixtureNormalizationError, NORMALIZATION_KIND, normalize_c1_fixture_handoff
from json_schema_subset import SchemaSubsetError, validate as validate_schema
from run_records import sanitize_text


class CodexProviderConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeVerificationResult:
    verified: bool
    reason_code: str


RuntimeVerifier = Callable[[Path, Path], RuntimeVerificationResult]
INJECTED_RUNTIME_VERIFICATION_SUCCESS = "injected_runtime_paths_verified"


BANNED_FLAGS = {
    "--yolo",
    "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-bypass-hook-trust",
    "danger-full-access",
    "--full-auto",
    "--ignore-rules",
    "--add-dir",
}
REAL_CASE_TERMS = (
    "jodi huisentruit",
    "amy mihaljevic",
    "springfield three",
    "backlog.md",
    "2_in_production",
    "1_ideas\\candidates",
    "1_ideas/candidates",
)
PROHIBITED_PROMPT_TERMS = (
    "elevenlabs", "pexels", "whisperx", "ffmpeg", "fcpxml", "orbital",
    "github", "youtube", "tiktok", "mcp", "browser", "browse", "download",
    "render", "upload", "schedule", "call an api", "external api",
)
SENSITIVE_ARGUMENT_RE = re.compile(r"(?i)(api[_-]?key|secret|token|authorization|credential|password|bearer\s+|(?:sk|xi|key)[-_][A-Za-z0-9_-]{12,})")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class CodexExecProvider:
    provider_id = "codex-exec-controlled-fixture-v1"
    normalization_kind = NORMALIZATION_KIND

    def __init__(
        self,
        fixture_root: Path,
        output_schema: Path,
        canonical_schema: Path,
        prompt_template: Path,
        node_executable: Path,
        npm_wrapper_directory: Path,
        codex_js_entry: Path,
        child_temp_directory: Path,
        *,
        timeout_seconds: float = 120.0,
        runtime_command_env: str = "COLD_TRUTH_CODEX_RUNTIME_COMMAND",
        process_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        runtime_verifier: RuntimeVerifier | None = None,
    ) -> None:
        self.fixture_root = fixture_root.resolve()
        self.output_schema = output_schema.resolve()
        self.canonical_schema = canonical_schema.resolve()
        self.prompt_template = prompt_template.resolve()
        self.node_executable = node_executable.resolve()
        self.npm_wrapper_directory = npm_wrapper_directory.resolve()
        self.codex_js_entry = codex_js_entry.resolve()
        self.child_temp_directory = child_temp_directory.resolve()
        self.timeout_seconds = float(timeout_seconds)
        self.runtime_command_env = runtime_command_env
        self.process_runner = process_runner or subprocess.run
        self.runtime_verifier = runtime_verifier
        if self.timeout_seconds <= 0 or self.timeout_seconds > 300:
            raise CodexProviderConfigurationError("Timeout must be greater than 0 and no more than 300 seconds")
        for path in (self.fixture_root, self.output_schema, self.canonical_schema, self.prompt_template):
            if not _under(self.fixture_root, path):
                raise CodexProviderConfigurationError("Provider configuration path escapes the fixture root")
        if not self.output_schema.is_file() or not self.canonical_schema.is_file() or not self.prompt_template.is_file():
            raise CodexProviderConfigurationError("Fixture remote schema, canonical schema, and prompt template are required")

    def minimal_child_environment(self) -> dict[str, str]:
        expected_output_root = (self.fixture_root / "output").resolve()
        if self.runtime_verifier is None:
            if not self.node_executable.is_file():
                raise CodexProviderConfigurationError("Verified Node executable is unavailable")
            if not self.npm_wrapper_directory.is_dir():
                raise CodexProviderConfigurationError("Verified npm wrapper directory is unavailable")
        if self.child_temp_directory.parent != expected_output_root or not _under(expected_output_root, self.child_temp_directory):
            raise CodexProviderConfigurationError("Child temporary directory must be a direct child of the fixture output directory")
        self.child_temp_directory.mkdir(parents=True, exist_ok=True)
        return {
            "PATH": f"{self.node_executable.parent};{self.npm_wrapper_directory}",
            "SystemRoot": r"C:\Windows",
            "ComSpec": r"C:\Windows\System32\cmd.exe",
            "TEMP": str(self.child_temp_directory),
            "TMP": str(self.child_temp_directory),
        }

    def child_environment_metadata(self) -> dict[str, Any]:
        if self.runtime_verifier is not None:
            return {
                "node_path_present": True,
                "npm_wrapper_path_present": True,
                "child_environment_mode": "minimal_allowlist",
                "runtime_verification_mode": "explicit_injected_test_dependency",
                "inherited_environment": False,
            }
        return {
            "node_path_present": self.node_executable.is_file(),
            "npm_wrapper_path_present": self.npm_wrapper_directory.is_dir(),
            "child_environment_mode": "minimal_allowlist",
            "runtime_verification_mode": "installed_filesystem",
            "inherited_environment": False,
        }

    def verify_runtime_paths(self) -> RuntimeVerificationResult:
        if self.runtime_verifier is None:
            if not self.node_executable.is_file():
                raise CodexProviderConfigurationError("Verified Node executable is unavailable")
            if not self.codex_js_entry.is_file():
                raise CodexProviderConfigurationError("Verified Codex JavaScript entry is unavailable or outside the expected npm package path")
            return RuntimeVerificationResult(True, "installed_runtime_paths_verified")
        try:
            result = self.runtime_verifier(self.node_executable, self.codex_js_entry)
        except CodexProviderConfigurationError:
            raise
        except Exception as exc:
            raise CodexProviderConfigurationError(
                f"Injected runtime verifier failed closed: {type(exc).__name__}"
            ) from exc
        if type(result) is not RuntimeVerificationResult:
            raise CodexProviderConfigurationError("Injected runtime verifier returned an invalid result shape")
        if result.verified is not True or result.reason_code != INJECTED_RUNTIME_VERIFICATION_SUCCESS:
            raise CodexProviderConfigurationError("Injected runtime verifier rejected the static runtime paths")
        return result

    def execute(self, request: dict[str, Any], output_root: Path, attempt: int) -> RuntimeResult:
        started_at = _utc()
        start = time.monotonic()
        output_root = output_root.resolve()
        try:
            self.validate_request(request, output_root)
            handoff_path = output_root / "strategist_handoff.json"
            command = self.build_command(output_root, handoff_path)
            prompt = self.build_prompt(request)
            child_environment = self.minimal_child_environment()
            completed = self.process_runner(
                command,
                cwd=str(self.fixture_root),
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
                env=child_environment,
            )
            elapsed = int((time.monotonic() - start) * 1000)
            metadata = self._runtime_metadata(command, completed.stdout)
            exit_code = int(completed.returncode)
            stderr = completed.stderr or ""
            validated_handoff = handoff_path if handoff_path.is_file() else None
            if exit_code == 0:
                if validated_handoff is None:
                    exit_code = 65
                    stderr = f"{stderr}\nStructured output artifact was not created".strip()
                    metadata["output_schema_validation"] = "missing"
                else:
                    try:
                        remote_handoff = json.loads(validated_handoff.read_text(encoding="utf-8"))
                        remote_schema = json.loads(self.output_schema.read_text(encoding="utf-8"))
                        validate_schema(remote_handoff, remote_schema)
                        canonical_handoff = self.normalize_remote_handoff(remote_handoff, request)
                        canonical_schema = json.loads(self.canonical_schema.read_text(encoding="utf-8"))
                        validate_schema(canonical_handoff, canonical_schema)
                        remote_copy = output_root / "remote_strategist_handoff.json"
                        remote_copy.write_text(json.dumps(remote_handoff, indent=2) + "\n", encoding="utf-8")
                        validated_handoff.write_text(json.dumps(canonical_handoff, indent=2) + "\n", encoding="utf-8")
                        metadata["output_schema_validation"] = "pass"
                        metadata["remote_output_normalized"] = True
                        metadata["normalization_kind"] = self.normalization_kind
                    except (OSError, ValueError) as exc:
                        exit_code = 65
                        stderr = f"{stderr}\nOutput schema validation failed: {exc}".strip()
                        metadata["output_schema_validation"] = "failed"
                        validated_handoff = None
            else:
                metadata["output_schema_validation"] = "not-run"
            return RuntimeResult(
                exit_code=exit_code,
                stdout=sanitize_text(completed.stdout or ""),
                stderr=sanitize_text(stderr),
                started_at=started_at,
                completed_at=_utc(),
                duration_ms=elapsed,
                handoff_path=validated_handoff,
                retryable=exit_code in {408, 429, 500, 502, 503, 504},
                runtime_metadata=metadata,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            return RuntimeResult(
                exit_code=124,
                stdout=sanitize_text(self._timeout_text(exc.stdout)),
                stderr=sanitize_text(self._timeout_text(exc.stderr) or "Codex fixture invocation timed out"),
                started_at=started_at,
                completed_at=_utc(),
                duration_ms=elapsed,
                handoff_path=None,
                retryable=True,
                runtime_metadata={
                    **self.child_environment_metadata(),
                    "provider": self.provider_id,
                    "runtime": "codex-exec",
                    "model": "not-reported",
                    "version": "not-reported",
                    "command_shape": self.safe_command_shape(),
                    "timeout_seconds": self.timeout_seconds,
                    "sandbox": "workspace-write",
                    "working_directory": "<fixture-root>",
                    "thread_ids": [],
                    "output_schema_validation": "not-run",
                },
            )
        except CodexProviderConfigurationError:
            raise
        except OSError as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            return RuntimeResult(
                exit_code=126,
                stdout="",
                stderr=sanitize_text(f"Codex local runtime or test-output operation failed: {type(exc).__name__}"),
                started_at=started_at,
                completed_at=_utc(),
                duration_ms=elapsed,
                handoff_path=None,
                retryable=False,
                runtime_metadata={
                    **self.child_environment_metadata(),
                    "provider": self.provider_id,
                    "runtime": "codex-exec",
                    "model": "not-reported",
                    "version": "not-reported",
                    "command_shape": self.safe_command_shape(),
                    "timeout_seconds": self.timeout_seconds,
                    "sandbox": "workspace-write",
                    "working_directory": "<fixture-root>",
                    "thread_ids": [],
                    "output_schema_validation": "not-run",
                },
            )

    def validate_request(self, request: dict[str, Any], output_root: Path) -> None:
        if request.get("mode") != "controlled-real-fixture":
            raise CodexProviderConfigurationError("Codex fixture provider requires controlled-real-fixture mode")
        if request.get("contract_id") != "cold-truth.strategist":
            raise CodexProviderConfigurationError("Only the Strategist fixture contract is allowed")
        if not _under(self.fixture_root, output_root):
            raise CodexProviderConfigurationError("Attempt output root escapes the disposable fixture workspace")
        permissions = request.get("permissions", {})
        for flag in ("network", "external_commands", "external_tools", "media_creation", "publishing", "platform_api", "secrets"):
            if permissions.get(flag) is not False:
                raise CodexProviderConfigurationError(f"Fixture request grants prohibited permission: {flag}")
        declared_actions = set(permissions.get("allowed_actions", []))
        fixture_actions = {
            "select supplied synthetic candidate",
            "list supplied synthetic claim ids",
            "assign supplied synthetic viability status",
        }
        if not declared_actions or not declared_actions.issubset(fixture_actions):
            raise CodexProviderConfigurationError("Fixture request declares actions beyond the narrowed Strategist contract")
        for item in request.get("inputs", []):
            if item.get("kind") == "file":
                path = Path(str(item.get("path", "")))
                if not _under(self.fixture_root, path):
                    raise CodexProviderConfigurationError("Fixture input path escapes the disposable workspace")

    def normalize_remote_handoff(self, remote_handoff: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        return normalize_c1_fixture_handoff(remote_handoff)

    def runtime_tokens(self) -> list[str]:
        raw = os.environ.get(self.runtime_command_env)
        if not raw:
            raise CodexProviderConfigurationError(f"{self.runtime_command_env} is not set for this process")
        try:
            tokens = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CodexProviderConfigurationError("Runtime command must be a JSON array") from exc
        if not isinstance(tokens, list) or not tokens or not all(isinstance(item, str) and item for item in tokens):
            raise CodexProviderConfigurationError("Runtime command must be a non-empty JSON string array")
        lowered = [item.lower() for item in tokens]
        executable_name = Path(tokens[0]).name.lower()
        if executable_name not in {"codex", "codex.exe", "codex.cmd"}:
            raise CodexProviderConfigurationError("Runtime executable must be Codex")
        if "\\windowsapps\\openai.codex_" in tokens[0].lower():
            raise CodexProviderConfigurationError("The blocked WindowsApps Codex launcher is prohibited for this fixture")
        if executable_name == "codex.cmd" and not Path(tokens[0]).is_absolute():
            raise CodexProviderConfigurationError("The Windows npm codex.cmd path must be absolute")
        if len(tokens) < 2 or lowered[1] != "exec":
            raise CodexProviderConfigurationError("Runtime command must use codex exec")
        combined = " ".join(lowered)
        for banned in BANNED_FLAGS:
            if banned in combined:
                raise CodexProviderConfigurationError(f"Prohibited Codex option: {banned}")
        if any(SENSITIVE_ARGUMENT_RE.search(item) for item in tokens):
            raise CodexProviderConfigurationError("Credentials and secret-shaped values are prohibited in the runtime command")
        return tokens

    def build_command(self, output_root: Path, handoff_path: Path) -> list[str]:
        output_root = output_root.resolve()
        handoff_path = handoff_path.resolve()
        if not _under(self.fixture_root, output_root):
            raise CodexProviderConfigurationError("Output root escapes the fixture workspace")
        if not _under(output_root, handoff_path):
            raise CodexProviderConfigurationError("Last-message output must stay inside the assigned attempt directory")
        tokens = self.runtime_tokens()
        if self.runtime_verifier is None:
            expected_node = Path(r"C:\Program Files\nodejs\node.exe").resolve()
            expected_npm_root = Path(r"C:\Users\brody\AppData\Roaming\npm").resolve()
            expected_wrapper = (self.npm_wrapper_directory / "codex.cmd").resolve()
            expected_entry = (self.npm_wrapper_directory / "node_modules" / "@openai" / "codex" / "bin" / "codex.js").resolve()
            same_path = lambda left, right: left == right
        else:
            expected_node = Path(r"C:\Program Files\nodejs\node.exe")
            expected_npm_root = Path(r"C:\Users\brody\AppData\Roaming\npm")
            expected_wrapper = expected_npm_root / "codex.cmd"
            expected_entry = expected_npm_root / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
            same_path = lambda left, right: os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))
        if not same_path(self.node_executable, expected_node):
            raise CodexProviderConfigurationError("Only the verified Node executable is allowed")
        if not same_path(self.npm_wrapper_directory, expected_npm_root):
            raise CodexProviderConfigurationError("Only the verified user-level npm root is allowed")
        runtime_wrapper = Path(tokens[0]).resolve() if self.runtime_verifier is None else Path(tokens[0])
        if not same_path(runtime_wrapper, expected_wrapper):
            raise CodexProviderConfigurationError("Only the verified user-level npm Codex wrapper is allowed")
        if not same_path(self.codex_js_entry, expected_entry):
            raise CodexProviderConfigurationError("Verified Codex JavaScript entry is unavailable or outside the expected npm package path")
        self.verify_runtime_paths()
        reserved = {"--sandbox", "--cd", "--json", "--output-schema", "--output-last-message", "--ephemeral"}
        if any(token.lower() in reserved for token in tokens[2:]):
            raise CodexProviderConfigurationError("Runtime base command may not override provider-controlled safety options")
        effective = [
            str(self.node_executable),
            str(self.codex_js_entry),
            *tokens[1:],
            "--sandbox", "workspace-write",
            "--cd", str(self.fixture_root),
            "--json",
            "--output-schema", str(self.output_schema),
            "--output-last-message", str(handoff_path),
            "--ephemeral",
            "-",
        ]
        prohibited_launchers = {"cmd.exe", "powershell.exe", "pwsh.exe"}
        if any(Path(item).name.lower() in prohibited_launchers for item in effective):
            raise CodexProviderConfigurationError("Shell wrappers are prohibited from the direct Node launch")
        lowered_effective = " ".join(item.lower() for item in effective)
        if "windowsapps" in lowered_effective or any(flag in lowered_effective for flag in BANNED_FLAGS):
            raise CodexProviderConfigurationError("Direct Node launch contains a prohibited path or option")
        return effective

    def build_prompt(self, request: dict[str, Any]) -> str:
        template = self.prompt_template.read_text(encoding="utf-8")
        input_record = next((item for item in request["inputs"] if item["name"] == "candidate_queue"), None)
        if not input_record or input_record.get("kind") != "value" or not isinstance(input_record.get("value"), dict):
            raise CodexProviderConfigurationError("Synthetic candidate_queue JSON value is required")
        if input_record["value"].get("fixture") is not True:
            raise CodexProviderConfigurationError("Candidate input is not marked as a fixture")
        synthetic_input = json.dumps(input_record["value"], sort_keys=True)
        identity = {
            key: request[key]
            for key in ("schema_version", "contract_id", "contract_version", "run_id", "case_id", "stage", "idempotency_key")
        }
        prompt = template.replace("{{REQUEST_IDENTITY_JSON}}", json.dumps(identity, sort_keys=True)).replace("{{REQUEST_INPUTS_JSON}}", json.dumps(request["inputs"], sort_keys=True)).replace("{{SYNTHETIC_CASE_JSON}}", synthetic_input)
        self.validate_prompt(prompt)
        return prompt

    @staticmethod
    def validate_prompt(prompt: str) -> None:
        lowered = prompt.lower()
        check_text = lowered.replace('"publishing_enabled": false', "")
        if any(term in check_text for term in REAL_CASE_TERMS):
            raise CodexProviderConfigurationError("Prompt contains a prohibited real-case reference")
        if any(term in check_text for term in PROHIBITED_PROMPT_TERMS):
            raise CodexProviderConfigurationError("Prompt contains a prohibited tool, media, network, or platform instruction")
        if SENSITIVE_ARGUMENT_RE.search(prompt):
            raise CodexProviderConfigurationError("Prompt contains a credential-shaped value")

    def safe_command_shape(self) -> list[str]:
        return [
            "<node.exe>", "<codex-entry.js>", "exec", "--sandbox", "workspace-write", "--cd", "<fixture-root>",
            "--json", "--output-schema", "<schema>", "--output-last-message",
            "<attempt-output>/strategist_handoff.json", "--ephemeral", "-",
        ]

    def _runtime_metadata(self, command: list[str], stdout: str) -> dict[str, Any]:
        thread_ids: list[str] = []
        model = "not-reported"
        runtime_version = "not-reported"
        for line in (stdout or "").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in ("thread_id", "threadId", "session_id", "sessionId", "run_id", "runId"):
                value = event.get(key)
                if isinstance(value, str) and value and value not in thread_ids:
                    thread_ids.append(value)
            if isinstance(event.get("model"), str):
                model = event["model"]
            if isinstance(event.get("version"), str):
                runtime_version = event["version"]
        return {
            **self.child_environment_metadata(),
            "provider": self.provider_id,
            "runtime": "codex-exec",
            "model": model,
            "version": runtime_version,
            "command_shape": self.safe_command_shape(),
            "timeout_seconds": self.timeout_seconds,
            "sandbox": "workspace-write",
            "working_directory": "<fixture-root>",
            "jsonl_events": True,
            "output_schema": True,
            "ephemeral": True,
            "thread_ids": thread_ids,
            "command_value_logged": False,
            "remote_output_normalized": False,
            "normalization_kind": "not-run",
        }

    @staticmethod
    def _timeout_text(value: str | bytes | None) -> str:
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value or ""
