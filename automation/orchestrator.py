"""Stateful Cold Truth orchestration with two human checkpoints.

Dry-run is the default and never calls external providers, creates media, renders,
or publishes. The synthetic fixture exercises policy and state transitions only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_runtime import AdapterUnavailableError
from agent_runner import AgentRunBlocked, AgentRunner
from audit_event_chain import AuditChainError, CHAIN_SCHEMA_VERSION, ZERO_HASH, append_event, verify_event_chain
from artifact_invalidation import GRAPH_VERSION, affected_approvals, downstream_artifacts, restart_checkpoint
from human_approval_lifecycle import ApprovalLifecycleError, validate_and_consume
from status_view import build_status_view
from track_isolation import TrackIsolationError, build_track_isolation_report


SCHEMA_VERSION = "1.0"
POLICY_VERSION = "2026-07-10"
STANDARD_VIABLE = "Standard long-form viable"
TERMINAL_STATES = {
    "AWAITING_SCRIPT_APPROVAL",
    "AWAITING_ASSEMBLY_APPROVAL",
    "BLOCKED_RUNTIME",
    "RETURNED_TO_BACKLOG",
    "FAILED",
    "AGENT_BLOCKED",
    "DRY_RUN_COMPLETE",
    "COMPLETE_LOCAL",
    "INVALIDATED_UPSTREAM_CHANGE",
}


class OrchestrationError(RuntimeError):
    """Policy, validation, or state error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
        handle.write(data)
        temp_name = handle.name
    os.replace(temp_name, path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OrchestrationError(f"Required JSON does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise OrchestrationError(f"Invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise OrchestrationError(f"Expected a JSON object: {path}")
    return value


def normalized_case_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unnamed-case"


def discover_vault_candidates(vault: Path, batch_size: int) -> list[dict[str, Any]]:
    """Normalize existing candidate folders without changing them.

    Missing verification stays pending; this function does not pretend that a
    Markdown ledger has passed the separate Research Verifier contract.
    """
    candidate_root = vault / "1_IDEAS" / "Candidates"
    candidates: list[dict[str, Any]] = []
    if not candidate_root.is_dir():
        return candidates
    for folder in sorted((p for p in candidate_root.iterdir() if p.is_dir()), key=lambda p: p.name.lower()):
        score_path = folder / "Candidate_Scorecard.md"
        viability_path = folder / "Strategist_Viability_Assessment_v1.md"
        ledger_path = folder / "Source_Ledger_Draft.md"
        risk_path = folder / "Case_Risk_Notes.md"
        if not all(path.is_file() for path in (score_path, viability_path, ledger_path, risk_path)):
            continue
        score_text = score_path.read_text(encoding="utf-8")
        viability_text = viability_path.read_text(encoding="utf-8")
        total_match = re.search(r"\*\*(\d+)\s*/\s*35\*\*", score_text)
        viability = STANDARD_VIABLE if re.search(r"STANDARD LONG-FORM VIABLE", viability_text, re.I) else "Not viable"
        candidates.append(
            {
                "candidate_id": normalized_case_id(folder.name),
                "case_name": folder.name,
                "total_score": int(total_match.group(1)) if total_match else 0,
                "score_breakdown": {},
                "viability": viability,
                "verification_status": "pending",
                "artifact_paths": {
                    "ledger": str(ledger_path.resolve()),
                    "viability": str(viability_path.resolve()),
                    "risk": str(risk_path.resolve()),
                    "scorecard": str(score_path.resolve()),
                },
            }
        )
    return candidates[:batch_size]


class CaseQueueOrchestrator:
    """Deterministic, idempotent state machine for one queue run."""

    def __init__(
        self,
        queue_file: Path,
        run_root: Path,
        *,
        run_id: str = "cold-truth-run",
        episode_id: str | None = None,
        dry_run: bool = True,
        script_approval: Path | None = None,
        assembly_approval: Path | None = None,
        agent_runner: AgentRunner | None = None,
        agent_failure_modes: dict[str, str] | None = None,
        agent_retry_limits: dict[str, int] | None = None,
    ) -> None:
        self.queue_file = queue_file.resolve()
        self.run_root = run_root.resolve()
        self.run_id = run_id
        self.episode_id = episode_id or f"episode-{normalized_case_id(run_id)}"
        if normalized_case_id(self.episode_id) != self.episode_id:
            raise OrchestrationError("episode_id must be a normalized lowercase identifier")
        self.dry_run = dry_run
        self.script_approval = script_approval.resolve() if script_approval else self.run_root / "approvals" / "script_approval.json"
        self.assembly_approval = assembly_approval.resolve() if assembly_approval else self.run_root / "approvals" / "assembly_approval.json"
        self.agent_runner = agent_runner
        self.agent_failure_modes = agent_failure_modes or {}
        self.agent_retry_limits = agent_retry_limits or {}
        self.synthetic_agent_fixture_root = Path(__file__).resolve().parent / "fixtures" / "simulated_agents"
        self.state_path = self.run_root / "run_state.json"
        self.status_path = self.run_root / "status.json"
        self.manifest_path = self.run_root / "manifest.json"
        self.event_path = self.run_root / "event_log.jsonl"
        self.artifact_dir = self.run_root / "artifacts"
        self.approval_consumption_root = self.run_root / "approval_consumptions"

    def initialize(self) -> dict[str, Any]:
        if self.state_path.exists():
            state = self.load_state()
            if state.get("run_id") != self.run_id or state.get("episode_id") != self.episode_id:
                raise OrchestrationError("Run identity does not match the persisted run_id and episode_id")
            self._verify_audit_chain(state)
            self._write_status_view(state)
            return state
        queue = read_json(self.queue_file)
        if queue.get("schema_version") != SCHEMA_VERSION:
            raise OrchestrationError("Queue schema_version must be 1.0")
        if self.agent_runner is not None and self.agent_runner.mode == "synthetic" and queue.get("fixture") is not True:
            raise OrchestrationError("Synthetic agent runtime refuses a non-fixture queue")
        candidates = queue.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise OrchestrationError("Queue requires at least one candidate")
        self.run_root.mkdir(parents=True, exist_ok=True)
        snapshot_path = self.run_root / "queue_snapshot.json"
        atomic_write_json(snapshot_path, queue)
        state = {
            "schema_version": SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "state": "QUEUED",
            "dry_run": self.dry_run,
            "publishing_enabled": False,
            "selected_case": None,
            "ranked_candidates": [],
            "returned_to_backlog": [],
            "artifact_registry": {},
            "stale_artifacts": [],
            "last_error": None,
            "agent_runtime_enabled": self.agent_runner is not None,
            "agent_records": {},
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        atomic_write_json(self.state_path, state)
        atomic_write_json(
            self.manifest_path,
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": self.run_id,
                "episode_id": self.episode_id,
                "case": None,
                "dry_run": self.dry_run,
                "publishing_enabled": False,
                "chain_schema_version": CHAIN_SCHEMA_VERSION,
                "event_count": 0,
                "chain_head_sha256": ZERO_HASH,
                "entries": [],
            },
        )
        self._record("initialize", "completed", outputs=[snapshot_path, self.state_path, self.manifest_path])
        return state

    def load_state(self) -> dict[str, Any]:
        return read_json(self.state_path)

    def _verify_audit_chain(self, state: dict[str, Any] | None = None) -> None:
        manifest = read_json(self.manifest_path)
        if manifest.get("run_id") != self.run_id or manifest.get("episode_id") != self.episode_id:
            raise OrchestrationError("Manifest identity does not match run_id and episode_id")
        if manifest.get("chain_schema_version") != CHAIN_SCHEMA_VERSION:
            raise OrchestrationError("Manifest has the wrong audit-chain schema")
        try:
            verified = verify_event_chain(
                self.event_path,
                expected_count=manifest.get("event_count"),
                expected_head=manifest.get("chain_head_sha256"),
                expected_entries=manifest.get("entries"),
            )
        except AuditChainError as exc:
            raise OrchestrationError(str(exc)) from exc
        if any(
            event.get("run_id") != self.run_id or event.get("episode_id") != self.episode_id
            for event in verified["events"]
        ):
            raise OrchestrationError("Audit event identity does not match run_id and episode_id")
        active_state = state if state is not None else self.load_state()
        state_anchor = active_state.get("audit_chain")
        if state_anchor is not None and state_anchor != {
            "chain_schema_version": CHAIN_SCHEMA_VERSION,
            "event_count": verified["event_count"],
            "chain_head_sha256": verified["chain_head_sha256"],
        }:
            raise OrchestrationError("Run state audit-chain anchor does not match the event ledger")

    def _save_state(self, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, state)
        self._write_status_view(state)

    def _write_status_view(self, state: dict[str, Any]) -> None:
        atomic_write_json(self.status_path, build_status_view(state))

    def _record(
        self,
        stage: str,
        status: str,
        *,
        inputs: list[Path] | None = None,
        outputs: list[Path] | None = None,
        decisions: list[dict[str, Any]] | None = None,
        errors: list[str] | None = None,
    ) -> None:
        timestamp = utc_now()
        event = {
            "event_id": sha256_bytes(f"{self.run_id}|{stage}|{timestamp}".encode())[:16],
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "stage": stage,
            "timestamp": timestamp,
            "status": status,
            "tool_calls": [{"tool": "local_orchestrator", "action": stage, "external": False, "dry_run": self.dry_run}],
            "inputs": [self._artifact_record(path) for path in (inputs or []) if path.exists()],
            "outputs": [self._artifact_record(path) for path in (outputs or []) if path.exists()],
            "decisions": decisions or [],
            "errors": errors or [],
        }
        manifest = read_json(self.manifest_path)
        if manifest.get("run_id") != self.run_id or manifest.get("episode_id") != self.episode_id:
            raise OrchestrationError("Manifest identity does not match run_id and episode_id")
        try:
            sealed_event = append_event(
                self.event_path,
                event,
                expected_count=manifest["event_count"],
                expected_head=manifest["chain_head_sha256"],
                expected_entries=manifest["entries"],
            )
        except (AuditChainError, KeyError, TypeError) as exc:
            raise OrchestrationError(f"Audit chain append refused: {exc}") from exc
        manifest["entries"].append(sealed_event)
        manifest["event_count"] = sealed_event["sequence"]
        manifest["chain_head_sha256"] = sealed_event["event_sha256"]
        state = self.load_state() if self.state_path.exists() else None
        if state:
            manifest["case"] = (state.get("selected_case") or {}).get("case_name")
        atomic_write_json(self.manifest_path, manifest)
        if state:
            state["audit_chain"] = {
                "chain_schema_version": CHAIN_SCHEMA_VERSION,
                "event_count": manifest["event_count"],
                "chain_head_sha256": manifest["chain_head_sha256"],
            }
            atomic_write_json(self.state_path, state)
            self._write_status_view(state)

    @staticmethod
    def _artifact_record(path: Path) -> dict[str, Any]:
        return {"path": str(path.resolve()), "sha256": sha256_path(path), "size_bytes": path.stat().st_size}

    def _write_artifact(self, name: str, data: str | dict[str, Any], state: dict[str, Any]) -> Path:
        path = self.artifact_dir / name
        if isinstance(data, dict):
            atomic_write_json(path, data)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8")
        state["artifact_registry"][name] = self._artifact_record(path)
        return path

    def _adopt_agent_outputs(self, execution, state: dict[str, Any]) -> dict[str, Path]:
        adopted: dict[str, Path] = {}
        for output in execution.handoff["outputs"]:
            source = Path(output["path"])
            destination = self.artifact_dir / output["name"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            state["artifact_registry"][output["name"]] = self._artifact_record(destination)
            adopted[output["name"]] = destination
        return adopted

    def _invoke_agent(
        self,
        contract_id: str,
        stage: str,
        case_id: str,
        inputs: dict[str, Any],
        state: dict[str, Any],
    ):
        if self.agent_runner is None:
            raise OrchestrationError("Agent runner is not configured")
        try:
            execution = self.agent_runner.run(
                contract_id,
                run_id=self.run_id,
                case_id=case_id,
                episode_id=self.episode_id,
                stage=stage,
                inputs=inputs,
                failure_mode=self.agent_failure_modes.get(stage),
                max_retries=self.agent_retry_limits.get(stage, 0),
            )
        except (AgentRunBlocked, AdapterUnavailableError) as exc:
            state["state"] = "AGENT_BLOCKED"
            state["last_error"] = str(exc)
            self._save_state(state)
            self._record(stage, "agent_blocked", errors=[str(exc)])
            return None
        state["agent_records"][stage] = {
            "contract_id": contract_id,
            "episode_id": self.episode_id,
            "idempotency_key": execution.idempotency_key,
            "record_path": str(execution.record_path),
            "handoff_path": str(execution.handoff_path),
            "cache_hit": execution.cache_hit,
            "attempt_count": execution.attempt_count,
        }
        self._save_state(state)
        return execution

    def _transition(self, state: dict[str, Any], expected: str, target: str) -> None:
        if state["state"] != expected:
            raise OrchestrationError(f"Illegal transition: expected {expected}, found {state['state']}")
        state["state"] = target
        self._save_state(state)

    def _fixture(self) -> dict[str, Any]:
        return read_json(self.run_root / "queue_snapshot.json").get("synthetic_stage_data", {})

    @staticmethod
    def _ranking_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
        scores = candidate.get("score_breakdown") or {}
        return (
            -int(candidate.get("total_score", 0)),
            -int(scores.get("long_form_source_depth", 0)),
            -int(scores.get("legal_and_misinformation_risk", 0)),
            -int(scores.get("clear_chronological_narrative", 0)),
            str(candidate.get("case_name", "")).casefold(),
        )

    def advance_once(self) -> dict[str, Any]:
        state = self.initialize()
        current = state["state"]
        queue = read_json(self.run_root / "queue_snapshot.json")

        if current == "QUEUED":
            if self.agent_runner is not None:
                policy_path = self.synthetic_agent_fixture_root / "content_standard_fixture.md"
                execution = self._invoke_agent(
                    "cold-truth.strategist",
                    "strategist_intake",
                    "synthetic-queue",
                    {
                        "candidate_queue": self.run_root / "queue_snapshot.json",
                        "batch_size": len(queue["candidates"]),
                        "content_standard": policy_path,
                    },
                    state,
                )
                if execution is None:
                    return state
                self._adopt_agent_outputs(execution, state)
                state["runtime_candidate_id"] = execution.handoff["result"]["candidate_id"]
                state["state"] = "STRATEGIST_COMPLETE"
                self._save_state(state)
                self._record("strategist_intake", "validated_agent_handoff", inputs=[self.run_root / "queue_snapshot.json", policy_path], outputs=list(self._paths_for_stage(state, "strategist_intake")))
                return state
            candidates = queue["candidates"]
            ranked = sorted(
                [c for c in candidates if c.get("verification_status") == "pass" and c.get("viability") == STANDARD_VIABLE],
                key=self._ranking_key,
            )
            state["returned_to_backlog"] = [
                {"candidate_id": c.get("candidate_id"), "reason": "verification_or_viability_gate_failed"}
                for c in candidates if c not in ranked
            ]
            state["ranked_candidates"] = [c.get("candidate_id") for c in ranked]
            ranked_path = self._write_artifact("ranked_candidates.json", {"policy_version": POLICY_VERSION, "candidates": ranked}, state)
            if not ranked:
                state["state"] = "RETURNED_TO_BACKLOG"
                self._save_state(state)
                self._record("candidate_ranking", "blocked", inputs=[self.queue_file], outputs=[ranked_path], decisions=[{"rule": "viability_and_verification", "result": "no_viable_case"}])
                return state
            state["selected_case"] = ranked[0]
            state["state"] = "CASE_SELECTED"
            self._save_state(state)
            self._record("candidate_ranking", "completed", inputs=[self.queue_file], outputs=[ranked_path], decisions=[{"rule": "deterministic_ranking", "selected": ranked[0]["candidate_id"]}])
            return state

        if current == "STRATEGIST_COMPLETE":
            policy_path = self.synthetic_agent_fixture_root / "content_standard_fixture.md"
            execution = self._invoke_agent(
                "cold-truth.research-verifier",
                "research_verification",
                state["runtime_candidate_id"],
                {
                    "Source_Ledger_Draft.md": self.artifact_dir / "Source_Ledger_Draft.md",
                    "Case_Risk_Notes.md": self.artifact_dir / "Case_Risk_Notes.md",
                    "source_threshold_policy": policy_path,
                },
                state,
            )
            if execution is None:
                return state
            self._adopt_agent_outputs(execution, state)
            if execution.handoff["result"]["verification_status"] != "pass":
                return self._fail(state, "research_verification", "Research Verifier did not pass the synthetic ledger")
            state["state"] = "RESEARCH_VERIFIED"
            self._save_state(state)
            self._record("research_verification", "validated_agent_handoff")
            return state

        if current == "RESEARCH_VERIFIED":
            candidates = queue["candidates"]
            ranked = sorted(
                [c for c in candidates if c.get("verification_status") == "pass" and c.get("viability") == STANDARD_VIABLE],
                key=self._ranking_key,
            )
            if not ranked:
                state["state"] = "RETURNED_TO_BACKLOG"
                state["last_error"] = "No verified viable synthetic candidate"
                self._save_state(state)
                return state
            if ranked[0]["candidate_id"] != state.get("runtime_candidate_id"):
                state["state"] = "AGENT_BLOCKED"
                state["last_error"] = "Strategist handoff conflicts with deterministic queue ranking"
                self._save_state(state)
                return state
            state["ranked_candidates"] = [candidate["candidate_id"] for candidate in ranked]
            state["selected_case"] = ranked[0]
            ranked_path = self._write_artifact("ranked_candidates.json", {"policy_version": POLICY_VERSION, "candidates": ranked}, state)
            state["state"] = "CASE_SELECTED"
            self._save_state(state)
            self._record("candidate_ranking", "completed_after_agent_validation", outputs=[ranked_path])
            return state

        if current == "CASE_SELECTED":
            if self.agent_runner is not None:
                execution = self._invoke_agent(
                    "cold-truth.writer",
                    "writer",
                    state["selected_case"]["candidate_id"],
                    {
                        "Research_Source_Ledger.md": self.artifact_dir / "Research_Source_Ledger.md",
                        "Research_Verification.json": self.artifact_dir / "Research_Verification.json",
                        "viability_result": state["selected_case"]["viability"],
                        "content_standard": self.synthetic_agent_fixture_root / "content_standard_fixture.md",
                    },
                    state,
                )
                if execution is None:
                    return state
                self._adopt_agent_outputs(execution, state)
                state["state"] = "WRITER_COMPLETE"
                self._save_state(state)
                self._record("writer", "validated_agent_handoff", outputs=[self.artifact_dir / "Script_Draft.md"])
                return state
            fixture = self._fixture()
            draft = fixture.get("script_draft")
            if not isinstance(draft, str) or not draft.strip():
                return self._fail(state, "writer", "No Writer adapter output or synthetic draft supplied")
            draft_path = self._write_artifact("Script_Draft.md", draft, state)
            self._transition(state, "CASE_SELECTED", "WRITER_COMPLETE")
            self._record("writer", "completed", outputs=[draft_path])
            return state

        if current == "WRITER_COMPLETE":
            if self.agent_runner is not None:
                writer_handoff = Path(state["agent_records"]["writer"]["handoff_path"])
                execution = self._invoke_agent(
                    "cold-truth.editor",
                    "editor",
                    state["selected_case"]["candidate_id"],
                    {
                        "Script_Draft.md": self.artifact_dir / "Script_Draft.md",
                        "Research_Source_Ledger.md": self.artifact_dir / "Research_Source_Ledger.md",
                        "writer_handoff.json": writer_handoff,
                    },
                    state,
                )
                if execution is None:
                    return state
                self._adopt_agent_outputs(execution, state)
                outline_path = self.artifact_dir / "Reverse_Outline.md"
                reviewed_path = self.artifact_dir / "Script_Draft_Reviewed.md"
                packet = {
                    "schema_version": SCHEMA_VERSION,
                    "checkpoint": "script",
                    "run_id": self.run_id,
                    "case_id": state["selected_case"]["candidate_id"],
                    "episode_id": self.episode_id,
                    "reverse_outline": self._artifact_record(outline_path),
                    "reviewed_draft": self._artifact_record(reviewed_path),
                    "required_approval_file": str(self.script_approval),
                    "agent_handoff_sha256": sha256_path(execution.handoff_path),
                }
                packet_path = self._write_artifact("checkpoint_1_packet.json", packet, state)
                state["state"] = "AWAITING_SCRIPT_APPROVAL"
                self._save_state(state)
                self._record("editor", "validated_agent_handoff_stop_checkpoint_1", outputs=[outline_path, reviewed_path, packet_path])
                return state
            fixture = self._fixture()
            outline = fixture.get("reverse_outline")
            reviewed = fixture.get("reviewed_draft")
            if not all(isinstance(value, str) and value.strip() for value in (outline, reviewed)):
                return self._fail(state, "editor", "Editor reverse outline and reviewed draft are required")
            outline_path = self._write_artifact("Reverse_Outline.md", outline, state)
            reviewed_path = self._write_artifact("Script_Draft_Reviewed.md", reviewed, state)
            packet = {
                "schema_version": SCHEMA_VERSION,
                "checkpoint": "script",
                "run_id": self.run_id,
                "case_id": state["selected_case"]["candidate_id"],
                "episode_id": self.episode_id,
                "reverse_outline": self._artifact_record(outline_path),
                "reviewed_draft": self._artifact_record(reviewed_path),
                "required_approval_file": str(self.script_approval),
            }
            packet_path = self._write_artifact("checkpoint_1_packet.json", packet, state)
            self._transition(state, "WRITER_COMPLETE", "AWAITING_SCRIPT_APPROVAL")
            self._record("editor", "completed_stop_checkpoint_1", inputs=[self.artifact_dir / "Script_Draft.md"], outputs=[outline_path, reviewed_path, packet_path])
            return state

        if current == "AWAITING_SCRIPT_APPROVAL":
            packet = read_json(self.artifact_dir / "checkpoint_1_packet.json")
            approval = self._validate_approval(self.script_approval, "script", state, packet)
            final_path = self.artifact_dir / "Script_Final.md"
            approved_draft_path = Path(packet["reviewed_draft"]["path"])
            shutil.copyfile(approved_draft_path, final_path)
            state["artifact_registry"]["Script_Final.md"] = self._artifact_record(final_path)
            state["script_approval"] = {**approval, "metadata_path": str(self.script_approval)}
            self._transition(state, "AWAITING_SCRIPT_APPROVAL", "SCRIPT_APPROVED")
            self._record("script_approval", "approved_and_consumed", inputs=[self.script_approval, Path(approval["consumption_record_path"]), self.artifact_dir / "Reverse_Outline.md", self.artifact_dir / "Script_Draft_Reviewed.md"], outputs=[final_path])
            return state

        if current == "SCRIPT_APPROVED":
            duration = self._fixture().get("narration_duration_seconds")
            if not isinstance(duration, (int, float)) or duration <= 0:
                return self._fail(state, "narration", "Narration adapter supplied no measurable duration")
            descriptor = {
                "schema_version": SCHEMA_VERSION,
                "status": "simulated_not_generated" if self.dry_run else "adapter_required",
                "script_sha256": state["artifact_registry"]["Script_Final.md"]["sha256"],
                "duration_seconds": float(duration),
                "voice": "Mia locked preset",
                "external_call": False,
                "media_created": False,
            }
            descriptor_path = self._write_artifact("narration_descriptor.json", descriptor, state)
            self._transition(state, "SCRIPT_APPROVED", "NARRATION_GENERATED")
            self._record("narration", "simulated" if self.dry_run else "blocked_adapter_required", outputs=[descriptor_path])
            return state

        if current == "NARRATION_GENERATED":
            descriptor = read_json(self.artifact_dir / "narration_descriptor.json")
            duration = float(descriptor["duration_seconds"])
            exception = self._fixture().get("short_format_exception_approved") is True
            allowed = duration >= 480.0 or exception
            preflight = {
                "schema_version": SCHEMA_VERSION,
                "target_format": "youtube-longform",
                "narration_duration_seconds": duration,
                "duration_source": "synthetic_fixture_only" if self.dry_run else "ffprobe_audio_stream_required",
                "word_count_used_for_duration": False,
                "assembly_allowed": allowed,
                "status": "pass" if allowed else "blocked_under_8_minimum",
                "exception_approved": exception,
            }
            preflight_path = self._write_artifact("preflight.json", preflight, state)
            if not allowed:
                state["state"] = "BLOCKED_RUNTIME"
                state["last_error"] = "Narration is under 480.000 seconds without an approved Short-Format exception"
                self._save_state(state)
                self._record("audio_preflight", "blocked", inputs=[self.artifact_dir / "narration_descriptor.json"], outputs=[preflight_path], decisions=[{"rule": "longform_release_minimum", "duration": duration, "allowed": False}])
                return state
            self._transition(state, "NARRATION_GENERATED", "AUDIO_PREFLIGHT_PASSED")
            self._record("audio_preflight", "passed", outputs=[preflight_path], decisions=[{"rule": "longform_release_minimum", "duration": duration, "allowed": True}])
            return state

        if current == "AUDIO_PREFLIGHT_PASSED":
            alignment = {"schema_version": SCHEMA_VERSION, "method": "synthetic_whisperx_fixture", "word_timestamps": self._fixture().get("word_timestamps", []), "external_call": False}
            path = self._write_artifact("longform_alignment.json", alignment, state)
            self._transition(state, "AUDIO_PREFLIGHT_PASSED", "WHISPERX_ALIGNED")
            self._record("whisperx_alignment", "simulated", outputs=[path])
            return state

        if current == "WHISPERX_ALIGNED":
            if self.agent_runner is not None:
                execution = self._invoke_agent(
                    "cold-truth.visual-producer",
                    "visual_producer",
                    state["selected_case"]["candidate_id"],
                    {
                        "Script_Final.md": self.artifact_dir / "Script_Final.md",
                        "script_approval.json": self.script_approval,
                        "longform_preflight.json": self.artifact_dir / "preflight.json",
                        "longform_alignment.json": self.artifact_dir / "longform_alignment.json",
                    },
                    state,
                )
                if execution is None:
                    return state
                self._adopt_agent_outputs(execution, state)
                state["state"] = "LONGFORM_ASSETS_READY"
                self._save_state(state)
                self._record("visual_producer", "validated_agent_handoff")
                return state
            assets = self._fixture().get("longform_assets", [])
            gaps = [
                asset for asset in assets
                if asset.get("status") != "ready" or asset.get("local_record") is not True or asset.get("licensed_record") is not True
            ] if isinstance(assets, list) else ["invalid"]
            if not assets or gaps:
                return self._fail(state, "visual_producer", f"Unresolved long-form asset gaps: {len(gaps)}")
            path = self._write_artifact("longform_assets.json", {
                "schema_version": "cold_truth.asset_manifest.v1",
                "track": "youtube-longform",
                "shared_assets_allowed": False,
                "synthetic": True,
                "media_created": False,
                "assets": assets,
            }, state)
            self._transition(state, "WHISPERX_ALIGNED", "LONGFORM_ASSETS_READY")
            self._record("visual_producer", "simulated", outputs=[path])
            return state

        if current == "LONGFORM_ASSETS_READY":
            if self.agent_runner is not None:
                execution = self._invoke_agent(
                    "cold-truth.shorts-editor",
                    "shorts_editor",
                    state["selected_case"]["candidate_id"],
                    {
                        "Script_Final.md": self.artifact_dir / "Script_Final.md",
                        "Research_Source_Ledger.md": self.artifact_dir / "Research_Source_Ledger.md",
                        "script_approval.json": self.script_approval,
                        "licensed_gameplay_record": self.synthetic_agent_fixture_root / "licensed_gameplay_record.json",
                    },
                    state,
                )
                if execution is None:
                    return state
                self._adopt_agent_outputs(execution, state)
                state["state"] = "SHORTS_PACKAGE_READY"
                self._save_state(state)
                self._record("shorts_editor", "validated_agent_handoff")
                return state
            shorts = self._fixture().get("shorts", {})
            assets = shorts.get("assets", []) if isinstance(shorts, dict) else []
            incomplete = [
                asset for asset in assets
                if asset.get("status") != "ready" or asset.get("local_record") is not True or asset.get("licensed_record") is not True
            ]
            if not assets or incomplete or not shorts.get("license_verified"):
                return self._fail(state, "shorts_editor", "Licensed Shorts asset record is incomplete")
            path = self._write_artifact("shorts_assets.json", {
                "schema_version": "cold_truth.asset_manifest.v1",
                "track": "shorts",
                "shared_assets_allowed": False,
                "synthetic": True,
                "media_created": False,
                **shorts,
            }, state)
            self._transition(state, "LONGFORM_ASSETS_READY", "SHORTS_PACKAGE_READY")
            self._record("shorts_editor", "simulated", outputs=[path])
            return state

        if current == "SHORTS_PACKAGE_READY":
            try:
                isolation = build_track_isolation_report(
                    self.artifact_dir / "longform_assets.json",
                    self.artifact_dir / "shorts_assets.json",
                )
            except TrackIsolationError as exc:
                return self._fail(state, "track_isolation", str(exc))
            path = self._write_artifact("track_isolation.json", isolation, state)
            if not isolation["passed"]:
                return self._fail(state, "track_isolation", f"Shared assets detected: {isolation['shared_asset_identities']}")
            self._transition(state, "SHORTS_PACKAGE_READY", "TRACK_ISOLATION_VALIDATED")
            self._record("track_isolation", "passed", outputs=[path])
            return state

        if current == "TRACK_ISOLATION_VALIDATED":
            fixture = self._fixture()
            long_assembly = self._write_artifact("longform_assembly.json", {"status": "synthetic_unrendered", "duration_seconds": fixture["narration_duration_seconds"], "rendered": False}, state)
            shorts_assembly = self._write_artifact("shorts_assembly.json", {"status": "synthetic_unrendered", "duration_seconds": fixture.get("shorts", {}).get("duration_seconds", 45.0), "rendered": False}, state)
            packet = {
                "schema_version": SCHEMA_VERSION,
                "checkpoint": "assembly",
                "run_id": self.run_id,
                "case_id": state["selected_case"]["candidate_id"],
                "episode_id": self.episode_id,
                "longform_assembly": self._artifact_record(long_assembly),
                "shorts_assembly": self._artifact_record(shorts_assembly),
                "required_approval_file": str(self.assembly_approval),
            }
            packet_path = self._write_artifact("checkpoint_2_packet.json", packet, state)
            self._transition(state, "TRACK_ISOLATION_VALIDATED", "AWAITING_ASSEMBLY_APPROVAL")
            self._record("assembly", "completed_stop_checkpoint_2", outputs=[long_assembly, shorts_assembly, packet_path])
            return state

        if current == "AWAITING_ASSEMBLY_APPROVAL":
            packet = read_json(self.artifact_dir / "checkpoint_2_packet.json")
            approval = self._validate_approval(self.assembly_approval, "assembly", state, packet)
            state["assembly_approval"] = {**approval, "metadata_path": str(self.assembly_approval)}
            self._transition(state, "AWAITING_ASSEMBLY_APPROVAL", "ASSEMBLY_APPROVED")
            self._record("assembly_approval", "approved_and_consumed", inputs=[self.assembly_approval, Path(approval["consumption_record_path"])])
            return state

        if current == "ASSEMBLY_APPROVED":
            if not self.dry_run:
                return self._fail(state, "local_render", "No local-production render adapter is configured; refusing to improvise")
            render_plan = self._write_artifact("render_plan.json", {"status": "not_executed_dry_run", "authorized": True, "media_created": False, "upload": False, "publish": False}, state)
            if self.agent_runner is not None:
                render_manifest = self._write_artifact("validated_local_renders.json", {"synthetic": True, "media_created": False, "render_authorized": True, "render_hashes": ["synthetic-render-record"]}, state)
                execution = self._invoke_agent(
                    "cold-truth.upload-manager",
                    "upload_manager_metadata",
                    state["selected_case"]["candidate_id"],
                    {
                        "Script_Final.md": self.artifact_dir / "Script_Final.md",
                        "Research_Source_Ledger.md": self.artifact_dir / "Research_Source_Ledger.md",
                        "validated_local_renders": render_manifest,
                    },
                    state,
                )
                if execution is None:
                    return state
                self._adopt_agent_outputs(execution, state)
            metadata_plan = self._write_artifact("metadata_plan.json", {"status": "planned_after_validated_render", "script_hash_bound": True, "publishing_enabled": False}, state)
            audit_completion = self._write_artifact("audit_completion.json", {"status": "dry_run_complete", "manifest": str(self.manifest_path), "external_calls": 0, "media_created": False, "publishing_enabled": False}, state)
            self._transition(state, "ASSEMBLY_APPROVED", "DRY_RUN_COMPLETE")
            self._record("local_render_and_metadata", "not_executed_dry_run", outputs=[render_plan, metadata_plan, audit_completion], decisions=[{"rule": "publishing_disabled", "result": True}])
            return state

        return state

    def _paths_for_stage(self, state: dict[str, Any], stage: str) -> list[Path]:
        record = state.get("agent_records", {}).get(stage)
        if not record:
            return []
        return [Path(record["handoff_path"]), Path(record["record_path"])]

    def run_until_blocked(self, max_steps: int = 50) -> dict[str, Any]:
        state = self.initialize()
        for _ in range(max_steps):
            if state["state"] in TERMINAL_STATES:
                if state["state"] == "AWAITING_SCRIPT_APPROVAL" and self.script_approval.exists():
                    pass
                elif state["state"] == "AWAITING_ASSEMBLY_APPROVAL" and self.assembly_approval.exists():
                    pass
                else:
                    return state
            state = self.advance_once()
        raise OrchestrationError("Maximum state transitions exceeded")

    def _validate_approval(self, path: Path, checkpoint: str, state: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
        if checkpoint == "script":
            purpose = "approve_script_for_canonicalization"
            only_allowed_next_state = "SCRIPT_APPROVED"
            bound_hashes = {
                "reverse_outline_sha256": packet["reverse_outline"]["sha256"],
                "script_draft_sha256": packet["reviewed_draft"]["sha256"],
            }
        else:
            purpose = "approve_assembly_for_dry_run_render_plan"
            only_allowed_next_state = "ASSEMBLY_APPROVED"
            bound_hashes = {
                "longform_assembly_sha256": packet["longform_assembly"]["sha256"],
                "shorts_assembly_sha256": packet["shorts_assembly"]["sha256"],
            }
        try:
            return validate_and_consume(
                path,
                self.approval_consumption_root,
                expected={
                    "purpose": purpose,
                    "run_id": self.run_id,
                    "case_id": state["selected_case"]["candidate_id"],
                    "episode_id": self.episode_id,
                    "checkpoint": checkpoint,
                    "only_allowed_next_state": only_allowed_next_state,
                    "bound_hashes": bound_hashes,
                    "required_exact": {"render_authorized": True} if checkpoint == "assembly" else {},
                },
            )
        except ApprovalLifecycleError as exc:
            raise OrchestrationError(str(exc)) from exc

    def register_script_revision(self, revised_text: str) -> dict[str, Any]:
        state = self.load_state()
        if not state.get("selected_case"):
            raise OrchestrationError("No selected case to revise")
        revised_path = self.artifact_dir / "Script_Draft_Reviewed_v2.md"
        revised_path.write_text(revised_text, encoding="utf-8")
        old_record = state["artifact_registry"].get("Script_Draft_Reviewed.md")
        if old_record is None:
            raise OrchestrationError("Script_Draft_Reviewed.md is not active")
        new_record = self._artifact_record(revised_path)
        if new_record["sha256"] == old_record["sha256"]:
            raise OrchestrationError("Revision hash is unchanged")
        stale_names, invalidated_approvals = self._apply_dependency_invalidation(
            state, "Script_Draft_Reviewed.md", old_record, new_record
        )
        packet = read_json(self.artifact_dir / "checkpoint_1_packet.json")
        packet["reviewed_draft"] = new_record
        atomic_write_json(self.artifact_dir / "checkpoint_1_packet.json", packet)
        state["artifact_registry"]["checkpoint_1_packet.json"] = self._artifact_record(self.artifact_dir / "checkpoint_1_packet.json")
        state["state"] = "AWAITING_SCRIPT_APPROVAL"
        self._save_state(state)
        self._record("script_revision_invalidation", "completed", inputs=[revised_path], outputs=[self.artifact_dir / "checkpoint_1_packet.json"], decisions=[{"rule": GRAPH_VERSION, "stale": stale_names, "invalidated_approvals": invalidated_approvals}])
        return state

    def register_artifact_revision(self, name: str, data: str | dict[str, Any]) -> dict[str, Any]:
        """Register one offline revision and invalidate every active descendant."""
        state = self.load_state()
        if name not in state.get("artifact_registry", {}):
            raise OrchestrationError(f"Artifact is not active and cannot be revised: {name}")
        if name not in {"Research_Source_Ledger.md", "Research_Verification.json", "Script_Draft.md", "Reverse_Outline.md", "Script_Draft_Reviewed.md", "Script_Final.md", "narration_descriptor.json", "preflight.json", "longform_alignment.json", "YouTube_Visual_Timeline.md", "longform_assets.json", "Shorts_Package.md", "Shorts_Visual_Timeline.md", "shorts_assets.json", "track_isolation.json", "longform_assembly.json", "shorts_assembly.json"}:
            raise OrchestrationError(f"Artifact is not an authorized revision root: {name}")
        revision_number = 1 + sum(
            1 for item in state.get("invalidation_history", []) if item.get("changed_artifact") == name
        )
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
        revision_path = self.artifact_dir / "revisions" / f"{safe_name}.revision-{revision_number:03d}"
        old_record = state["artifact_registry"][name]
        if isinstance(data, dict):
            serialized = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        else:
            serialized = data.encode("utf-8")
        if sha256_bytes(serialized) == old_record["sha256"]:
            raise OrchestrationError("Revision hash is unchanged")
        if isinstance(data, dict):
            atomic_write_json(revision_path, data)
        else:
            revision_path.parent.mkdir(parents=True, exist_ok=True)
            revision_path.write_text(data, encoding="utf-8")
        new_record = self._artifact_record(revision_path)
        stale_names, invalidated_approvals = self._apply_dependency_invalidation(
            state, name, old_record, new_record
        )
        checkpoint = restart_checkpoint(name)
        state["state"] = "INVALIDATED_UPSTREAM_CHANGE"
        state["next_required_checkpoint"] = checkpoint
        self._save_state(state)
        self._record(
            "artifact_dependency_invalidation",
            "completed_stop_for_review",
            inputs=[revision_path],
            decisions=[{
                "rule": GRAPH_VERSION,
                "changed_artifact": name,
                "stale": stale_names,
                "invalidated_approvals": invalidated_approvals,
                "next_required_checkpoint": checkpoint,
            }],
        )
        return state

    def _apply_dependency_invalidation(
        self,
        state: dict[str, Any],
        name: str,
        old_record: dict[str, Any],
        new_record: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        stale_names = downstream_artifacts(name, state["artifact_registry"])
        stale_records = state.setdefault("stale_artifact_records", [])
        changed_at = utc_now()
        stale_records.append({
            **old_record,
            "name": name,
            "superseded_by_sha256": new_record["sha256"],
            "invalidated_at": changed_at,
            "dependency_graph_version": GRAPH_VERSION,
        })
        for stale_name in stale_names:
            stale_record = state["artifact_registry"].pop(stale_name)
            stale_records.append({
                **stale_record,
                "name": stale_name,
                "invalidated_by": name,
                "invalidated_by_sha256": new_record["sha256"],
                "invalidated_at": changed_at,
                "dependency_graph_version": GRAPH_VERSION,
            })
        invalidated_approvals = affected_approvals(name, stale_names)
        for approval_name in invalidated_approvals:
            state.pop(approval_name, None)
        state["artifact_registry"][name] = {
            **new_record,
            "revision_of_sha256": old_record["sha256"],
            "dependency_graph_version": GRAPH_VERSION,
        }
        state["stale_artifacts"] = sorted(set(state.get("stale_artifacts", [])) | set(stale_names))
        state.setdefault("invalidation_history", []).append({
            "dependency_graph_version": GRAPH_VERSION,
            "changed_artifact": name,
            "old_sha256": old_record["sha256"],
            "new_sha256": new_record["sha256"],
            "stale_artifacts": stale_names,
            "invalidated_approvals": invalidated_approvals,
            "recorded_at": changed_at,
        })
        return stale_names, invalidated_approvals

    def _fail(self, state: dict[str, Any], stage: str, message: str) -> dict[str, Any]:
        state["state"] = "FAILED"
        state["last_error"] = message
        self._save_state(state)
        self._record(stage, "failed", errors=[message])
        return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cold Truth stateful orchestrator; dry-run by default and publishing disabled")
    parser.add_argument("--queue-file", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--run-id", default="cold-truth-run")
    parser.add_argument("--script-approval", type=Path)
    parser.add_argument("--assembly-approval", type=Path)
    parser.add_argument("--local-production", action="store_true", help="Enable configured local adapters; still never publishes")
    parser.add_argument("--synthetic-agent-runtime", action="store_true", help="Use only deterministic in-process fixture agents")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.local_production:
        config_path = Path(__file__).resolve().parent / "runtime_config.json"
        config = read_json(config_path)
        if config.get("real_production_enabled") is not True:
            raise SystemExit("Real-production mode is disabled by automation/runtime_config.json")
    if args.local_production and args.synthetic_agent_runtime:
        raise SystemExit("Synthetic agent runtime cannot be combined with local production")
    agent_runner = None
    if args.synthetic_agent_runtime:
        from agent_runtime import ProviderRegistry
        from fixtures.simulated_agents.mock_runtime import SyntheticAgentProvider

        contract_ids = [
            "cold-truth.strategist", "cold-truth.research-verifier", "cold-truth.writer",
            "cold-truth.editor", "cold-truth.visual-producer", "cold-truth.shorts-editor",
            "cold-truth.upload-manager",
        ]
        automation_root = Path(__file__).resolve().parent
        registry = ProviderRegistry()
        registry.register(SyntheticAgentProvider(automation_root / "fixtures" / "simulated_agents"), contract_ids)
        agent_runner = AgentRunner(automation_root / "contracts", args.run_root, registry, mode="synthetic")
    orchestrator = CaseQueueOrchestrator(
        args.queue_file,
        args.run_root,
        run_id=args.run_id,
        dry_run=not args.local_production,
        script_approval=args.script_approval,
        assembly_approval=args.assembly_approval,
        agent_runner=agent_runner,
    )
    state = orchestrator.run_until_blocked()
    print(json.dumps({"state": state["state"], "run_root": str(orchestrator.run_root), "publishing_enabled": False}, indent=2))


if __name__ == "__main__":
    main()
