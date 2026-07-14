"""Deterministic in-process agent provider with no external capabilities."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from agent_runtime import RuntimeResult


FIXED_START = "2026-07-11T00:00:00Z"
FIXED_END = "2026-07-11T00:00:00.001Z"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError("Synthetic fixture attempted a path escape") from exc
    return candidate


class SyntheticAgentProvider:
    provider_id = "synthetic-in-process-v1"

    def __init__(self, fixture_root: Path) -> None:
        self.fixture_root = fixture_root.resolve()
        self.specs = json.loads((self.fixture_root / "responses.json").read_text(encoding="utf-8"))

    def execute(self, request: dict[str, Any], output_root: Path, attempt: int) -> RuntimeResult:
        if request.get("mode") != "synthetic":
            return self._result(78, "", "Synthetic provider refuses non-synthetic mode", None, False)
        failure = request.get("failure_mode")
        if failure == "fail_once" and attempt == 1:
            return self._result(75, "", "Configured retryable synthetic failure", None, True)
        if failure == "agent_error":
            return self._result(70, "", "Configured non-retryable synthetic failure", None, False)
        spec = self.specs.get(request["contract_id"])
        if not spec:
            return self._result(69, "", "No synthetic response configured", None, False)
        output_root.mkdir(parents=True, exist_ok=True)
        records: dict[str, dict[str, Any]] = {}
        input_hashes = {item["name"]: item["sha256"] for item in request["inputs"]}
        for output in spec["outputs"]:
            name = output["name"]
            path = _safe(output_root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if "json_content" in output:
                content = self._resolve(output["json_content"], records, input_hashes)
                path.write_text(json.dumps(content, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            else:
                path.write_text(str(output.get("content", "")), encoding="utf-8")
            records[name] = {"name": name, "type": path.suffix.lstrip(".") or "file", "path": str(path), "sha256": _sha(path), "size_bytes": path.stat().st_size}
        result = self._resolve(spec["result"], records, input_hashes)
        allowed_action = request["permissions"]["allowed_actions"][0]
        handoff = {
            "schema_version": "1.0",
            "contract_id": request["contract_id"],
            "contract_version": request["contract_version"],
            "run_id": request["run_id"],
            "case_id": request["case_id"],
            "episode_id": request["episode_id"],
            "provider_id": request["provider_id"],
            "stage": request["stage"],
            "attempt": attempt,
            "idempotency_key": request["idempotency_key"],
            "status": "success",
            "started_at": FIXED_START,
            "completed_at": FIXED_END,
            "inputs": request["inputs"],
            "outputs": list(records.values()),
            "result": result,
            "decisions": [{"rule": "synthetic_fixture_only", "result": "pass"}],
            "warnings": [],
            "errors": [],
            "retryable": False,
            "tool_calls": [{"tool": "synthetic_fixture", "action": allowed_action, "external": False, "network": False}],
            "runtime": {"provider": self.provider_id, "runtime": "python-in-process", "model": "none", "version": "1.0", "external_commands": 0},
            "publishing_enabled": False
        }
        if failure == "malformed_handoff":
            handoff.pop("result")
        elif failure == "path_escape":
            handoff["outputs"][0]["path"] = str((output_root.parent.parent / "escape.txt").resolve())
        elif failure == "unexpected_tool":
            handoff["tool_calls"][0]["action"] = "publish to platform"
        elif failure == "episode_mismatch":
            handoff["episode_id"] = "wrong-episode"
        elif failure == "attempt_mismatch":
            handoff["attempt"] = attempt + 1
        elif failure == "duplicate_output":
            handoff["outputs"].append(dict(handoff["outputs"][0]))
        elif failure == "unexpected_output":
            unexpected = _safe(output_root, "undeclared-output.txt")
            unexpected.write_text("synthetic undeclared output", encoding="utf-8")
            handoff["outputs"].append({
                "name": "undeclared-output.txt",
                "type": "txt",
                "path": str(unexpected),
                "sha256": _sha(unexpected),
                "size_bytes": unexpected.stat().st_size,
            })
        elif failure == "noncanonical_output_path":
            (output_root / "unused").mkdir(exist_ok=True)
            name = handoff["outputs"][0]["name"]
            handoff["outputs"][0]["path"] = str(output_root / "unused" / ".." / name)
        elif failure == "mutate_input":
            file_input = next(item for item in request["inputs"] if item.get("kind") == "file")
            Path(file_input["path"]).write_text("synthetic input mutation", encoding="utf-8")
        elif failure == "provider_id_mismatch":
            handoff["provider_id"] = "synthetic-substituted-provider"
        elif failure == "runtime_provider_mismatch":
            handoff["runtime"]["provider"] = "synthetic-substituted-provider"
        handoff_path = _safe(output_root, "handoff.json")
        handoff_path.write_text(json.dumps(handoff, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        runtime_result = self._result(0, f"Synthetic {request['contract_id']} completed", "", handoff_path, False)
        if failure == "result_provider_mismatch":
            runtime_result = replace(runtime_result, runtime_metadata={**runtime_result.runtime_metadata, "provider": "synthetic-substituted-provider"})
        return runtime_result

    def _resolve(self, value: Any, records: dict[str, dict[str, Any]], input_hashes: dict[str, str]) -> Any:
        if isinstance(value, dict):
            return {key: self._resolve(item, records, input_hashes) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve(item, records, input_hashes) for item in value]
        if value == "$ALL_OUTPUT_HASHES":
            return {name: record["sha256"] for name, record in sorted(records.items())}
        if isinstance(value, str) and value.startswith("$OUTPUT_SHA256:"):
            return records[value.split(":", 1)[1]]["sha256"]
        if isinstance(value, str) and value.startswith("$INPUT_SHA256:"):
            return input_hashes[value.split(":", 1)[1]]
        return value

    @staticmethod
    def _result(exit_code: int, stdout: str, stderr: str, handoff: Path | None, retryable: bool) -> RuntimeResult:
        return RuntimeResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            started_at=FIXED_START,
            completed_at=FIXED_END,
            duration_ms=1,
            handoff_path=handoff,
            retryable=retryable,
            runtime_metadata={"provider": "synthetic-in-process-v1", "runtime": "python-in-process", "model": "none", "version": "1.0"},
        )
