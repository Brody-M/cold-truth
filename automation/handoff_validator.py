"""Contract, request-envelope, and handoff validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


COMMON_HANDOFF_FIELDS = {
    "schema_version", "contract_id", "contract_version", "run_id", "case_id", "episode_id",
    "stage", "attempt", "idempotency_key", "status", "started_at", "completed_at",
    "inputs", "outputs", "result", "decisions", "warnings", "errors", "retryable",
    "tool_calls", "runtime", "provider_id", "publishing_enabled",
}
MEDIA_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mp3", ".wav", ".m4a", ".aac", ".flac"}


class ContractValidationError(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_contract(path: Path) -> dict[str, Any]:
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"Cannot load contract: {path}") from exc
    required = {
        "schema_version", "contract_id", "contract_version", "agent", "required_inputs",
        "allowed_actions", "required_outputs", "success_criteria", "failure_criteria",
        "prohibited_actions", "handoff_schema", "autonomy",
    }
    missing = sorted(required - set(contract))
    if missing:
        raise ContractValidationError(f"Contract missing fields: {', '.join(missing)}")
    if contract["schema_version"] != "1.0":
        raise ContractValidationError("Unsupported contract schema_version")
    return contract


def _under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _non_handoff_outputs(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["name"]: item
        for item in contract["required_outputs"]
        if not item["name"].endswith("_handoff.json")
    }


def _validate_input_descriptors(inputs: Any) -> None:
    if not isinstance(inputs, list):
        raise ContractValidationError("Request inputs must be an array")
    names: set[str] = set()
    for record in inputs:
        if not isinstance(record, dict) or not isinstance(record.get("name"), str):
            raise ContractValidationError("Request input descriptor is invalid")
        name = record["name"]
        if name in names:
            raise ContractValidationError(f"Duplicate request input: {name}")
        names.add(name)
        if record.get("kind") == "file":
            raw_path = record.get("path")
            if not isinstance(raw_path, str):
                raise ContractValidationError(f"Input path is missing: {name}")
            path = Path(raw_path)
            if not path.is_absolute() or raw_path != str(path.resolve()):
                raise ContractValidationError(f"Input path is not canonical: {name}")
            if not path.is_file():
                raise ContractValidationError(f"Input file does not exist: {name}")
            if record.get("sha256") != file_sha256(path):
                raise ContractValidationError(f"Input hash mismatch: {name}")
            if record.get("size_bytes") != path.stat().st_size:
                raise ContractValidationError(f"Input size mismatch: {name}")
        elif record.get("kind") == "value":
            if "value" not in record:
                raise ContractValidationError(f"Input value is missing: {name}")
            expected = hashlib.sha256(_canonical(record["value"])).hexdigest()
            if record.get("sha256") != expected:
                raise ContractValidationError(f"Input value hash mismatch: {name}")
        else:
            raise ContractValidationError(f"Unsupported input descriptor kind: {name}")


def validate_request_envelope(envelope: dict[str, Any], contract: dict[str, Any]) -> None:
    for field in ("schema_version", "run_id", "case_id", "episode_id", "stage", "contract_id", "contract_version", "idempotency_key", "mode", "provider_id", "attempt_policy", "inputs", "permissions", "output_root"):
        if field not in envelope:
            raise ContractValidationError(f"Request missing {field}")
    if envelope["contract_id"] != contract["contract_id"] or envelope["contract_version"] != contract["contract_version"]:
        raise ContractValidationError("Request contract identity mismatch")
    if not isinstance(envelope["provider_id"], str) or not envelope["provider_id"].strip():
        raise ContractValidationError("Request provider_id is required")
    policy = envelope["attempt_policy"]
    if not isinstance(policy, dict):
        raise ContractValidationError("Request attempt_policy must be an object")
    if policy.get("fixed_provider_id") != envelope["provider_id"]:
        raise ContractValidationError("Attempt policy provider identity mismatch")
    if policy.get("provider_fallback") is not False or policy.get("retry_requires_provider_retryable") is not True:
        raise ContractValidationError("Attempt policy must prohibit fallback and require retryable results")
    max_attempts = policy.get("max_attempts")
    max_retries = policy.get("max_retries")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or not 1 <= max_attempts <= 3:
        raise ContractValidationError("Attempt policy max_attempts must be between 1 and 3")
    if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries != max_attempts - 1:
        raise ContractValidationError("Attempt policy max_retries is inconsistent")
    _validate_input_descriptors(envelope["inputs"])
    supplied = {item.get("name") for item in envelope["inputs"]}
    required = {
        item["name"] for item in contract["required_inputs"]
        if item.get("required") is True or item.get("required_for_assembly") is True
    }
    missing = sorted(required - supplied)
    if missing:
        raise ContractValidationError(f"Request missing contract inputs: {', '.join(missing)}")
    allowed_names = {item["name"] for item in contract["required_inputs"]}
    extras = sorted(supplied - allowed_names)
    if extras:
        raise ContractValidationError(f"Request includes undeclared inputs: {', '.join(extras)}")
    permissions = envelope["permissions"]
    if not set(permissions.get("allowed_actions", [])).issubset(set(contract["allowed_actions"])):
        raise ContractValidationError("Request grants an action outside the contract")
    for flag in ("publishing", "platform_api", "secrets", "media_creation"):
        if permissions.get(flag) is not False:
            raise ContractValidationError(f"Permission {flag} must remain false")
    if envelope["mode"] in {"synthetic", "controlled-real-fixture"}:
        for flag in ("network", "external_commands", "external_tools"):
            if permissions.get(flag) is not False:
                raise ContractValidationError(f"Synthetic permission {flag} must remain false")
    raw_output_root = envelope["output_root"]
    if not isinstance(raw_output_root, str):
        raise ContractValidationError("Request output_root must be a path string")
    output_root = Path(raw_output_root)
    if not output_root.is_absolute() or raw_output_root != str(output_root.resolve()):
        raise ContractValidationError("Request output_root is not canonical")
    if "attempt" in envelope:
        if not isinstance(envelope["attempt"], int) or envelope["attempt"] < 1:
            raise ContractValidationError("Request attempt must be a positive integer")
        expected = envelope.get("expected_outputs")
        if not isinstance(expected, list):
            raise ContractValidationError("Attempt request missing expected_outputs")
        expected_by_name = {item.get("name"): item for item in expected if isinstance(item, dict)}
        declared = _non_handoff_outputs(contract)
        if len(expected_by_name) != len(expected) or set(expected_by_name) != set(declared):
            raise ContractValidationError("Attempt request expected_outputs do not match the contract")
        for name, record in expected_by_name.items():
            exact_path = (output_root / name).resolve()
            if record.get("path") != str(exact_path) or not _under(output_root, exact_path):
                raise ContractValidationError(f"Expected output path mismatch: {name}")


def validate_handoff(
    handoff: dict[str, Any],
    contract: dict[str, Any],
    request: dict[str, Any],
    allowed_root: Path,
) -> list[Path]:
    _validate_input_descriptors(request.get("inputs"))
    missing = sorted(COMMON_HANDOFF_FIELDS - set(handoff))
    if missing:
        raise ContractValidationError(f"Handoff missing common fields: {', '.join(missing)}")
    for field in ("schema_version", "contract_id", "contract_version", "run_id", "case_id", "episode_id", "stage", "attempt", "idempotency_key", "provider_id"):
        expected = request[field]
        if handoff.get(field) != expected:
            raise ContractValidationError(f"Handoff identity mismatch: {field}")
    if handoff["status"] != "success":
        raise ContractValidationError(f"Handoff status is not success: {handoff['status']}")
    if handoff.get("inputs") != request.get("inputs"):
        raise ContractValidationError("Handoff input records do not match the request envelope")
    if handoff.get("publishing_enabled") is not False:
        raise ContractValidationError("Publishing must remain disabled")
    runtime = handoff.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("provider") != request["provider_id"]:
        raise ContractValidationError("Handoff runtime provider identity mismatch")
    result = handoff.get("result")
    if not isinstance(result, dict):
        raise ContractValidationError("Handoff result must be an object")
    required_result_fields = set(contract.get("handoff_schema", {}).get("result_fields", []))
    absent_results = sorted(required_result_fields - set(result))
    if absent_results:
        raise ContractValidationError(f"Handoff missing contract result fields: {', '.join(absent_results)}")
    outputs = handoff.get("outputs")
    if not isinstance(outputs, list):
        raise ContractValidationError("Handoff outputs must be an array")
    output_by_name = {item.get("name"): item for item in outputs if isinstance(item, dict)}
    if len(output_by_name) != len(outputs):
        raise ContractValidationError("Handoff output names must be unique records")
    implicit_handoff_names = {item["name"] for item in contract["required_outputs"] if item["name"].endswith("_handoff.json")}
    required_outputs = {
        item["name"] for item in contract["required_outputs"]
        if item["name"] not in implicit_handoff_names and not (item.get("conditional") and handoff["status"] != "success")
    }
    absent_outputs = sorted(required_outputs - set(output_by_name))
    if absent_outputs:
        raise ContractValidationError(f"Handoff missing required outputs: {', '.join(absent_outputs)}")
    unexpected_outputs = sorted(set(output_by_name) - set(_non_handoff_outputs(contract)))
    if unexpected_outputs:
        raise ContractValidationError(f"Handoff includes undeclared outputs: {', '.join(unexpected_outputs)}")
    expected_paths = {item["name"]: item["path"] for item in request.get("expected_outputs", [])}
    validated_paths: list[Path] = []
    for name, record in output_by_name.items():
        raw_path = record.get("path")
        if not isinstance(raw_path, str):
            raise ContractValidationError(f"Output path is missing: {name}")
        path = Path(raw_path)
        if not path.is_absolute() or raw_path != str(path.resolve()):
            raise ContractValidationError(f"Output path is not canonical: {name}")
        if not _under(allowed_root, path):
            raise ContractValidationError(f"Output escapes allowed root: {name}")
        if expected_paths.get(name) != raw_path:
            raise ContractValidationError(f"Output path does not match the expected path: {name}")
        if path.suffix.lower() in MEDIA_EXTENSIONS:
            raise ContractValidationError(f"Synthetic agent declared prohibited media output: {name}")
        if not path.is_file():
            raise ContractValidationError(f"Declared output does not exist: {name}")
        if record.get("sha256") != file_sha256(path):
            raise ContractValidationError(f"Output hash mismatch: {name}")
        if record.get("size_bytes") != path.stat().st_size:
            raise ContractValidationError(f"Output size mismatch: {name}")
        validated_paths.append(path)
    allowed_actions = set(request["permissions"]["allowed_actions"])
    for call in handoff.get("tool_calls", []):
        if call.get("action") not in allowed_actions:
            raise ContractValidationError("Handoff reports a tool action outside its permission set")
        if request["mode"] in {"synthetic", "controlled-real-fixture"} and (call.get("external") is not False or call.get("network") is not False):
            raise ContractValidationError("Fixture handoff reports external or network tool activity")
        action_text = str(call.get("action", "")).lower()
        if any(word in action_text for word in ("publish", "upload", "schedule", "oauth")):
            raise ContractValidationError("Publishing-related tool action is prohibited")
    return validated_paths
