"""Append-only SHA-256 event-chain primitives for the Cold Truth orchestrator."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


CHAIN_SCHEMA_VERSION = "cold_truth.audit_event_chain.v1"
ZERO_HASH = "0" * 64


class AuditChainError(RuntimeError):
    """The append-only event ledger is missing, malformed, or inconsistent."""


def _canonical_bytes(event_without_hash: dict[str, Any]) -> bytes:
    return json.dumps(
        event_without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _event_hash(event: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in event.items() if key != "event_sha256"}
    return hashlib.sha256(_canonical_bytes(unsigned)).hexdigest()


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise AuditChainError(f"Event ledger is not valid UTF-8: {path}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line:
            raise AuditChainError(f"Event ledger contains a blank line at {line_number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AuditChainError(f"Event ledger contains invalid JSON at line {line_number}") from exc
        if not isinstance(value, dict):
            raise AuditChainError(f"Event ledger line {line_number} is not an object")
        events.append(value)
    return events


def verify_event_chain(
    path: Path,
    *,
    expected_count: int | None = None,
    expected_head: str | None = None,
    expected_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    events = read_events(path)
    previous = ZERO_HASH
    for sequence, event in enumerate(events, start=1):
        if event.get("chain_schema_version") != CHAIN_SCHEMA_VERSION:
            raise AuditChainError(f"Event {sequence} has the wrong chain schema")
        if event.get("sequence") != sequence:
            raise AuditChainError(f"Event {sequence} has a non-contiguous sequence")
        if event.get("previous_event_sha256") != previous:
            raise AuditChainError(f"Event {sequence} has a broken previous-hash link")
        actual_hash = event.get("event_sha256")
        if not isinstance(actual_hash, str) or actual_hash != _event_hash(event):
            raise AuditChainError(f"Event {sequence} has an invalid event hash")
        previous = actual_hash

    if expected_count is not None and len(events) != expected_count:
        raise AuditChainError(
            f"Event ledger count {len(events)} does not match manifest count {expected_count}"
        )
    if expected_head is not None and previous != expected_head:
        raise AuditChainError("Event ledger head does not match manifest head")
    if expected_entries is not None and events != expected_entries:
        raise AuditChainError("Event ledger does not exactly match manifest entries")
    return {"event_count": len(events), "chain_head_sha256": previous, "events": events}


def append_event(
    path: Path,
    event: dict[str, Any],
    *,
    expected_count: int,
    expected_head: str,
    expected_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_event_chain(
        path,
        expected_count=expected_count,
        expected_head=expected_head,
        expected_entries=expected_entries,
    )
    sealed = {
        **event,
        "chain_schema_version": CHAIN_SCHEMA_VERSION,
        "sequence": expected_count + 1,
        "previous_event_sha256": expected_head,
    }
    sealed["event_sha256"] = _event_hash(sealed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(sealed, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return sealed
