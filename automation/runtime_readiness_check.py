"""Read-only runtime readiness report. Never invokes a runtime or provider."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any


AUTOMATION = Path(__file__).resolve().parent
REQUIRED_CONTRACTS = [
    "contract.schema.json",
    "common_handoff.schema.json",
    "strategist.contract.json",
    "research_verifier.contract.json",
    "writer.contract.json",
    "editor.contract.json",
    "visual_producer.contract.json",
    "shorts_editor.contract.json",
    "upload_manager.contract.json",
]


def readiness(config_path: Path = AUTOMATION / "runtime_config.json") -> dict[str, Any]:
    errors: list[str] = []
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        config = {}
        errors.append("runtime configuration file is missing")
    except json.JSONDecodeError:
        config = {}
        errors.append("runtime configuration file is invalid JSON")
    contract_root = AUTOMATION / "contracts"
    missing_contracts = [name for name in REQUIRED_CONTRACTS if not (contract_root / name).is_file()]
    fixture_root = AUTOMATION / "fixtures" / "simulated_agents"
    fixture_available = all((fixture_root / name).is_file() for name in ("mock_runtime.py", "responses.json", "content_standard_fixture.md", "licensed_gameplay_record.json"))
    command_env_name = config.get("runtime_command_env") if isinstance(config.get("runtime_command_env"), str) else None
    command_configured = bool(command_env_name and os.environ.get(command_env_name))
    adapters = config.get("future_adapters") if isinstance(config.get("future_adapters"), dict) else {}
    adapter_status = {name: adapters.get(name) is True for name in ("research", "narration", "alignment", "long_form_assets", "shorts_assets", "assembly", "render")}
    real_enabled = config.get("real_production_enabled") is True
    publishing_enabled = config.get("publishing_enabled") is True
    controlled_test_outstanding = []
    if not command_configured:
        controlled_test_outstanding.append("Configure a tested generic Codex runtime command indirectly through the named environment variable.")
    if shutil.which("codex") is None:
        controlled_test_outstanding.append("Install or expose the Codex executable to the current shell.")
    controlled_test_outstanding.append("Implement and independently test the generic Codex provider against synthetic inputs only.")
    production_outstanding = []
    for name, enabled in adapter_status.items():
        if not enabled:
            production_outstanding.append(f"Independently implement and test the {name.replace('_', ' ')} adapter.")
    if missing_contracts:
        controlled_test_outstanding.append("Restore missing contract files.")
    production_outstanding.extend([
        "Run one separately authorized controlled synthetic-to-real agent test before enabling any real case.",
        "Keep publishing disabled; no platform provider exists."
    ])
    codex_discoverable = shutil.which("codex") is not None
    controlled_ready = bool(codex_discoverable and command_configured and not missing_contracts and fixture_available and not real_enabled and not publishing_enabled)
    return {
        "schema_version": "1.0",
        "check_type": "read_only_no_invocation",
        "codex_executable_discoverable": codex_discoverable,
        "configured_runtime_command_present": command_configured,
        "required_contract_files_present": not missing_contracts,
        "missing_contract_files": missing_contracts,
        "fixture_mode_available": fixture_available,
        "real_production_mode_enabled": real_enabled,
        "real_production_mode_required_value": False,
        "publishing_enabled": publishing_enabled,
        "publishing_implemented": False,
        "future_adapters_configured": adapter_status,
        "ready_for_controlled_real_agent_fixture_test": controlled_ready,
        "ready_for_real_production_enable_review": bool(controlled_ready and all(adapter_status.values())),
        "manual_setup_outstanding_for_controlled_agent_test": controlled_test_outstanding,
        "manual_setup_outstanding_for_production": production_outstanding,
        "errors": errors,
        "secrets_read_or_printed": False,
        "runtime_invoked": False,
        "external_calls": 0
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Cold Truth agent-runtime readiness check")
    parser.add_argument("--config", type=Path, default=AUTOMATION / "runtime_config.json")
    args = parser.parse_args()
    print(json.dumps(readiness(args.config), indent=2))


if __name__ == "__main__":
    main()
