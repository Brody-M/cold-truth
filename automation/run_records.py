"""Immutable, redacted local records for agent-runtime attempts."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


SECRET_KEY_RE = re.compile(r"(?i)(api[_-]?key|secret|token|authorization|credential|password)")
SECRET_VALUE_RE = re.compile(r"(?i)(bearer\s+\S+|(?:sk|xi|key)[-_][A-Za-z0-9_\-]{20,})")
MEDIA_PATH_RE = re.compile(r"(?i)(?:[A-Z]:\\|/)[^\r\n\"']+\.(?:mp4|mov|mkv|avi|webm|mp3|wav|m4a|aac|flac)")


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
        handle.write(content)
        temporary = handle.name
    os.replace(temporary, path)


def sanitize_text(value: str, limit: int = 65536) -> str:
    value = MEDIA_PATH_RE.sub("[MEDIA_PATH_REDACTED]", value)
    value = SECRET_VALUE_RE.sub("[REDACTED]", value)
    return value[:limit]


def sanitize_value(value: Any, key: str = "") -> Any:
    if SECRET_KEY_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): sanitize_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item, key) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


class RunRecordStore:
    def __init__(self, run_root: Path) -> None:
        self.root = run_root.resolve() / "agent_runs"
        self.root.mkdir(parents=True, exist_ok=True)

    def key_root(self, idempotency_key: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", idempotency_key):
            raise ValueError("Invalid idempotency key")
        return self.root / idempotency_key

    def write_request_once(self, idempotency_key: str, request: dict[str, Any]) -> Path:
        path = self.key_root(idempotency_key) / "request.json"
        sanitized = sanitize_value(request)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != sanitized:
                raise RuntimeError("Idempotency key collision with a different request")
            return path
        atomic_json(path, sanitized)
        return path

    def attempt_root(self, idempotency_key: str, attempt: int) -> Path:
        if attempt < 1:
            raise ValueError("attempt must be at least 1")
        return self.key_root(idempotency_key) / f"attempt-{attempt:03d}"

    def write_attempt_once(
        self,
        idempotency_key: str,
        attempt: int,
        record: dict[str, Any],
        stdout: str,
        stderr: str,
    ) -> Path:
        folder = self.attempt_root(idempotency_key, attempt)
        record_path = folder / "record.json"
        if record_path.exists():
            raise RuntimeError(f"Attempt record already exists: {record_path}")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "stdout.txt").write_text(sanitize_text(stdout), encoding="utf-8")
        (folder / "stderr.txt").write_text(sanitize_text(stderr), encoding="utf-8")
        atomic_json(record_path, sanitize_value(record))
        return record_path

    def completed(self, idempotency_key: str) -> dict[str, Any] | None:
        path = self.key_root(idempotency_key) / "completed.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def mark_completed_once(self, idempotency_key: str, value: dict[str, Any]) -> Path:
        path = self.key_root(idempotency_key) / "completed.json"
        sanitized = sanitize_value(value)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != sanitized:
                raise RuntimeError("Completed idempotency record is immutable")
            return path
        atomic_json(path, sanitized)
        return path
