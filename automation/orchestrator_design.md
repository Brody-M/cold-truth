# Cold Truth Case-Queue Orchestrator Design

## Objective

Operate the complete local episode pipeline with only two routine human decisions:

1. Approve the exact source-bound reverse outline and full draft.
2. Approve the exact unrendered long-form and Shorts assemblies and authorize local render.

Publishing is a separate, disabled capability. The orchestrator does not upload, schedule, publish, or contact platform APIs.

## Operating modes

- `dry-run` — default. Validates queue, contracts, state transitions, approvals, and intended actions without external calls, media creation, downloads, assembly, or rendering.
- `local-production` — must be explicitly selected. Permits only the stage adapters enabled in configuration and only after required approval/hash checks.
- `publishing` — intentionally not implemented. A future implementation requires a separate security/design review, platform credentials, and an explicit enablement flag.

## Deterministic selection policy

1. Read candidates from `Backlog.md`, candidate folders, or a normalized queue JSON.
2. Reject entries whose Research Verifier does not pass.
3. Keep only `Standard long-form viable` cases, plus a Short-Format case only when matching human exception metadata exists.
4. Sort by total score descending.
5. Break ties by: source-depth score descending, legal/misinformation score descending, chronology score descending, normalized case name ascending.
6. Select exactly one case. Persist the ranked inputs and policy version so the choice is reproducible.

Public interest is not a selection field.

## State machine

```text
QUEUED
  -> STRATEGIST_INTAKE
  -> RESEARCH_VERIFICATION
       -> RETURNED_TO_BACKLOG (verification or viability failure)
  -> VIABILITY_RANKED
  -> CASE_SELECTED
  -> WRITER_COMPLETE
  -> EDITOR_REVIEW_COMPLETE
  -> AWAITING_SCRIPT_APPROVAL            [HUMAN CHECKPOINT 1]
       -> SCRIPT_REJECTED -> WRITER_COMPLETE or RETURNED_TO_BACKLOG
       -> SCRIPT_APPROVED
  -> NARRATION_GENERATED
  -> AUDIO_PREFLIGHT_PASSED
       -> BLOCKED_RUNTIME (no valid exception)
  -> WHISPERX_ALIGNED
  -> LONGFORM_ASSETS_READY
  -> SHORTS_PACKAGE_READY
  -> TRACK_ISOLATION_VALIDATED
  -> ASSEMBLIES_READY
  -> AWAITING_ASSEMBLY_APPROVAL          [HUMAN CHECKPOINT 2]
       -> ASSEMBLY_REJECTED -> appropriate upstream stage
       -> ASSEMBLY_APPROVED
  -> LOCAL_RENDER_VALIDATED
  -> METADATA_AND_AUDIT_READY
  -> COMPLETE_LOCAL
```

`FAILED` is reachable from every operational state. Failures record the stage, error class, retryability, attempt, and last known valid state. No transition exists from any state to upload, schedule, or publish.

## Allowed transitions and stop conditions

- Transitions are allowlisted in code; an unknown or skipped transition is rejected.
- `AWAITING_SCRIPT_APPROVAL` and `AWAITING_ASSEMBLY_APPROVAL` always stop the run.
- Missing approval files, false approval, blank approver/reason/timestamp, wrong case/run, or artifact hash mismatch always stop.
- Research conflict, insufficient viable material, suspect-claim failure, unresolved media gap, license failure, track collision, missing current audio preflight, adapter error, or runtime failure always stop.
- A stop preserves all valid artifacts and never creates a substitute.

## Artifact layout

```text
automation/runs/<run_id>/
  run_state.json
  queue_snapshot.json
  ranked_candidates.json
  event_log.jsonl
  manifest.json
  checkpoint_1_packet.json
  checkpoint_2_packet.json
  approvals/
    script_approval.json
    assembly_approval.json

Brody's Vault/2_IN_PRODUCTION/<case>/
  Research_Source_Ledger.md
  Editorial/
    Strategist_Viability_Assessment.md
    Research_Verification.json
    Reverse_Outline.md
    Script_Draft.md
    Script_Final.md
  Audio/
    longform/<version>/...
    shorts/<short_id>/<version>/...
  Visuals/
    longform/<version>/...
    shorts/<short_id>/<version>/...
  Assembly/
    longform/<version>/...
    shorts/<short_id>/<version>/...
  Metadata/
  Automation/
    preflight*.json
    direct_generation_manifest.json
    artifact_registry.json
```

The fixture/test runner uses an isolated temporary run root and never writes a real production package.

## Common handoff envelope

Every agent handoff contains:

- `schema_version`, `contract_id`, `contract_version`
- `run_id`, `case_id`, `stage`, `attempt`
- `started_at`, `completed_at`, `status`
- `inputs[]` and `outputs[]`, each with absolute/portable path, SHA-256, type, and version
- `policy_versions[]`
- `decisions[]` with rule ID and result
- `warnings[]`, `errors[]`, `retryable`
- `tool_calls[]` with tool/provider, action, timestamp, parameters with secrets redacted, result, and produced paths

`manifest.json` is the run index. `event_log.jsonl` is append-only. Direct/manual work must additionally be recorded in the episode’s `direct_generation_manifest.json` using the same event fields.

## Human approval records

### Script approval

Required fields:

```json
{
  "schema_version": "1.0",
  "checkpoint": "script",
  "run_id": "...",
  "case_id": "...",
  "human_approved": true,
  "approved_by": "Brody",
  "approved_at": "ISO-8601 timestamp",
  "reverse_outline_sha256": "...",
  "script_draft_sha256": "...",
  "reason": "..."
}
```

The approved draft is copied/versioned as `Script_Final.md`; it is not regenerated after approval.

### Assembly approval

Required fields include `checkpoint: "assembly"`, the long-form and Shorts assembly hashes, `human_approved: true`, `render_authorized: true`, approver, timestamp, and reason. Approval authorizes local render only. It does not authorize upload or publication.

## Idempotency and overwrite rules

- A stage key is `run_id + case_id + stage + input_hashes + contract_version + settings_hash`.
- A successful matching stage is reused and logged as `cache_hit`; external calls are not repeated.
- Approved artifacts are immutable. Revisions create new versions.
- Writes use a temporary file plus atomic replacement for state/manifest files.
- A retry never deletes the prior attempt; it adds a new attempt record.
- Asset downloads use provider asset ID plus checksum to prevent duplicates.

## Stale-artifact invalidation

Dependency order:

```text
ledger -> outline/draft -> final script -> narration -> preflight -> alignment
       -> long-form assets -> long-form assembly
       -> Shorts scripts -> Shorts narration/preflight/alignment -> Shorts assets -> Shorts assembly
       -> assembly approval -> renders -> metadata/audit completion
```

Any upstream hash change marks every dependent artifact `stale`, clears both downstream approval bindings where applicable, and returns the state to the earliest valid gate. A script change always invalidates narration, preflight, alignment, both visual branches, both assemblies, assembly approval, and renders.

## Failure and retry behavior

- Validation/policy/source/license/hash failures are non-retryable until inputs change.
- Network timeouts, provider 429/5xx responses, and transient file locks may retry up to the configured limit with bounded exponential backoff.
- Credit-consuming voice generation is never retried automatically after an ambiguous response; first check whether the expected output exists and validates.
- Pexels search may broaden approved phrases, but an unmatched beat remains a blocking gap. No unrelated substitute is allowed.
- Paid asset acquisition and acceptance of new license terms pause for human action.

## Rejection, deferral, and backlog return

- `rejected`: fails source integrity, safety, or audience rules; record the reason and do not auto-research again until policy/input changes.
- `deferred`: potentially viable but blocked by missing public records, current-status confirmation, or source depth; record required source categories.
- `returned_to_backlog`: selected/drafted case fails viability or human script review; preserve research and version history.

No rejected/deferred case is silently replaced mid-run. Selection begins a new logged run from the remaining queue.

## Required validators

- Agent-contract input/output validator.
- Research ledger/claim threshold validator.
- Narrative Coherence Gate and paired-approval hash validator.
- Mia preset parser and deviation-approval validator.
- FFprobe actual-audio-duration preflight.
- WhisperX word-timestamp and script-match validator.
- Asset file/license/readiness validator.
- Long-form/Shorts asset-set intersection validator (must equal zero).
- Assembly duration/gap/overlap validator.
- Render authorization and post-render FFprobe validator.
- Secret redaction and Git-ignore validator.

## Manual actions that remain

- Human Checkpoint 1 and Human Checkpoint 2.
- Any documented runtime/voice exception.
- Paid-license purchase/login or new terms acceptance.
- GitHub account/repository connection and remote push authorization.
- Platform developer registrations, OAuth configuration, and any future explicit publishing-mode approval.
