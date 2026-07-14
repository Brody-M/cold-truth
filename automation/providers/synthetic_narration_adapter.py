"""Two-mode, offline-only adapter for the Phase C6 synthetic fixture."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from c6_synthetic_narration_gate import BLOCKED, READY, blocked_result, validate_synthetic_narration
from run_records import atomic_json, sanitize_value


class SyntheticNarrationAdapter:
    MODES = {"validate_request", "fake_runner"}

    def __init__(self, *, fixture_root: Path, state_root: Path) -> None:
        self.fixture_root = fixture_root.resolve()
        self.c6_output = self.fixture_root / "narration_preflight" / "output" / "c6_synthetic_narration_adapter"
        self.state_root = state_root.resolve()

    def execute(self, mode: str, *, write_fake_artifact: bool = False, **paths: Any) -> dict[str, Any]:
        if mode not in self.MODES:
            return blocked_result("unsupported_adapter_mode")
        try:
            request = json.loads(Path(paths["request_path"]).read_text(encoding="utf-8"))
        except (KeyError, OSError, json.JSONDecodeError):
            return blocked_result("request_unreadable")
        if mode == "validate_request" and (write_fake_artifact or request.get("write_fake_artifact") is True):
            return blocked_result("fake_artifact_not_allowed_in_validation_mode")
        result = validate_synthetic_narration(
            fixture_root=self.fixture_root, state_root=self.state_root, **paths
        )
        if result.get("state") != READY:
            return result
        if mode == "validate_request":
            return result
        metadata = {
            "schema_version": "1.0",
            "artifact_type": "non_audio_fixture_metadata",
            "request_id": request["request_id"],
            "deterministic_fake_duration_ms": 0,
            "deterministic_fake_audio_bytes": 0,
            "provider_invoked": False,
            "network_invoked": False,
            "audio_file_created": False,
            "real_production_enabled": False,
        }
        fake_path = None
        if write_fake_artifact or request.get("write_fake_artifact") is True:
            fake_path = self.state_root / "fake_artifacts" / f"{request['request_id']}.fake.json"
            if fake_path.exists():
                return blocked_result("fake_artifact_replay")
            atomic_json(fake_path, sanitize_value(metadata))
        return {"decision": result, "fake_metadata": metadata,
                "fake_artifact_relative_path": None if fake_path is None else str(fake_path.relative_to(self.c6_output))}
