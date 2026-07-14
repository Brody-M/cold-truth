"""Direct-Node Codex provider restricted to the synthetic Phase C2 verifier fixture."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from c2_fixture_normalization import NORMALIZATION_KIND, normalize_c2_research_verifier_handoff
from providers.codex_exec_provider import CodexExecProvider, CodexProviderConfigurationError, SENSITIVE_ARGUMENT_RE


def _under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class ResearchVerifierCodexProvider(CodexExecProvider):
    provider_id = "codex-exec-controlled-research-verifier-v1"
    normalization_kind = NORMALIZATION_KIND
    required_input_names = {
        "synthetic_strategist_handoff",
        "synthetic_source_ledger",
        "synthetic_research_boundaries",
    }
    allowed_actions = {
        "compare supplied synthetic claims to supplied synthetic sources",
        "apply supplied synthetic research boundaries",
        "classify supplied synthetic claims as approved or rejected",
    }

    def validate_request(self, request: dict[str, Any], output_root: Path) -> None:
        if request.get("mode") != "controlled-real-fixture":
            raise CodexProviderConfigurationError("Research Verifier fixture requires controlled-real-fixture mode")
        if request.get("contract_id") != "cold-truth.research-verifier" or request.get("contract_version") != "1.0.0-c2-fixture":
            raise CodexProviderConfigurationError("Only the fixture Research Verifier contract is allowed")
        if request.get("case_id") != "glass-river-research-fixture" or request.get("stage") != "research_verification_fixture":
            raise CodexProviderConfigurationError("Research Verifier fixture identity mismatch")
        if not _under(self.fixture_root, output_root):
            raise CodexProviderConfigurationError("Attempt output root escapes the Research Verifier fixture")
        permissions = request.get("permissions", {})
        for flag in ("network", "external_commands", "external_tools", "media_creation", "publishing", "platform_api", "secrets"):
            if permissions.get(flag) is not False:
                raise CodexProviderConfigurationError(f"Fixture request grants prohibited permission: {flag}")
        if set(permissions.get("allowed_actions", [])) != self.allowed_actions:
            raise CodexProviderConfigurationError("Fixture actions differ from the exact Research Verifier allowlist")
        inputs = request.get("inputs", [])
        if {item.get("name") for item in inputs} != self.required_input_names:
            raise CodexProviderConfigurationError("Research Verifier fixture requires exactly three synthetic inputs")
        for item in inputs:
            if item.get("kind") != "file":
                raise CodexProviderConfigurationError("Research Verifier inputs must be fixture files")
            path = Path(str(item.get("path", "")))
            if not _under(self.fixture_root, path) or not path.is_file():
                raise CodexProviderConfigurationError("Research Verifier input escapes the synthetic fixture")

    def build_prompt(self, request: dict[str, Any]) -> str:
        documents: dict[str, Any] = {}
        for item in request["inputs"]:
            path = Path(item["path"])
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CodexProviderConfigurationError(f"Synthetic input is not valid JSON: {item['name']}") from exc
            if not isinstance(value, dict) or value.get("fixture") is not True or value.get("case_id") != "glass-river-research-fixture":
                raise CodexProviderConfigurationError("Input is not the expected synthetic Research Verifier fixture")
            documents[item["name"]] = value
        template = self.prompt_template.read_text(encoding="utf-8")
        identity = {key: request[key] for key in ("schema_version", "contract_id", "contract_version", "run_id", "case_id", "stage", "idempotency_key")}
        prompt = template
        prompt = prompt.replace("{{REQUEST_IDENTITY_JSON}}", json.dumps(identity, sort_keys=True))
        prompt = prompt.replace("{{REQUEST_INPUTS_JSON}}", json.dumps(request["inputs"], sort_keys=True))
        prompt = prompt.replace("{{SYNTHETIC_STRATEGIST_HANDOFF_JSON}}", json.dumps(documents["synthetic_strategist_handoff"], sort_keys=True))
        prompt = prompt.replace("{{SYNTHETIC_SOURCE_LEDGER_JSON}}", json.dumps(documents["synthetic_source_ledger"], sort_keys=True))
        prompt = prompt.replace("{{SYNTHETIC_RESEARCH_BOUNDARIES_JSON}}", json.dumps(documents["synthetic_research_boundaries"], sort_keys=True))
        lowered = prompt.lower()
        if "http://" in lowered or "https://" in lowered or SENSITIVE_ARGUMENT_RE.search(prompt):
            raise CodexProviderConfigurationError("Synthetic prompt contains an external location or credential-shaped value")
        return prompt

    def normalize_remote_handoff(self, remote_handoff: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        return normalize_c2_research_verifier_handoff(remote_handoff, request)
