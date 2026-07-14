# Cold Truth Agent-Runtime Adapter Design

**Status:** Phase B synthetic implementation specification  
**Real-case execution:** disabled  
**Publishing:** not implemented

## Purpose

The adapter layer sits between the stateful orchestrator and specialized agent providers. The orchestrator decides which contract may run and when. The adapter packages only the contract-approved inputs and permissions, invokes a configured provider, captures the execution record, validates the structured handoff, and returns a validated result. Unstructured chat text is never a state-transition signal.

## Provider-neutral interface

Every provider implements one operation:

```text
execute(request_envelope, isolated_output_root, attempt_number) -> runtime_result
```

The provider is selected by configuration. The interface does not assume Codex CLI, an API, MCP, or a particular model. Phase B enables only the in-process synthetic provider. A future Codex provider may translate the same envelope into its supported invocation format after a controlled test and security review.

The runtime result contains:

- exit code;
- sanitized stdout and stderr;
- start/end timestamps and duration;
- provider, runtime, model, and version metadata without credentials;
- retryability classification;
- path to exactly one structured handoff artifact;
- declared output paths.

## Standard request envelope

The orchestrator creates an immutable JSON request with:

- `schema_version`, `run_id`, `case_id`, `stage`;
- `contract_id` and exact `contract_version`;
- deterministic `idempotency_key`;
- `mode`: `synthetic`, `dry-run`, or `real-production`;
- named inputs containing either a value hash or a file path plus SHA-256;
- a permission block copied from the contract;
- an isolated output root;
- redacted runtime metadata and settings hash.

Only contract-required inputs are admitted. Unknown inputs are rejected unless the contract explicitly declares them optional. The provider receives no environment dump, credential file, API key, or unrelated case path.

## Permission model

Permissions are deny-by-default:

- `allowed_actions` must exactly match or be a subset of the contract’s actions.
- Network access, external commands, media creation, platform access, secrets, and paths outside the isolated run root are false unless a future independently tested adapter and contract explicitly enable them.
- Synthetic agents have `network=false`, `external_commands=false`, `external_tools=false`, `media_creation=false`, and `publishing=false`.
- Upload Manager is limited to local metadata creation. Upload, schedule, publish, OAuth, and platform API actions are permanently denied in this architecture.

The validator rejects a handoff containing a tool action outside the permission set, a publishing flag, external-tool activity in synthetic mode, or an output path outside the isolated agent attempt folder.

## Structured handoffs

An agent must write a single handoff conforming to `common_handoff.schema.json` and the matching contract’s `handoff_schema.result_fields`. Required contract outputs must exist, remain inside the allowed output root, and match their declared SHA-256 and byte count.

The handoff includes:

- run, case, stage, contract, attempt, and idempotency identity;
- deterministic status and result fields;
- input and output artifact records;
- decisions, warnings, errors, and retryability;
- sanitized tool-call declarations;
- provider/runtime/model metadata;
- `publishing_enabled: false`.

Stdout may explain an execution, but the orchestrator ignores it for progression. Only a successful, validated handoff can authorize a transition.

## Validation sequence

1. Validate the contract against `contract.schema.json`.
2. Validate request identity, required input names/types, hashes, and permissions.
3. Invoke the configured provider inside the isolated attempt directory.
4. Capture exit code, duration, stdout, stderr, and safe runtime metadata.
5. If exit code is nonzero, record failure and apply retry policy; do not inspect prose as success.
6. Parse the handoff JSON.
7. Validate the common envelope.
8. Validate contract identity/version and every contract-specific result field.
9. Validate required output files, hashes, sizes, and path containment.
10. Validate tool actions and prohibited publishing/external activity.
11. Commit an immutable success record and completed-idempotency pointer.
12. Return the validated handoff to the orchestrator.

Any failure produces `AGENT_BLOCKED` with a precise reason. The orchestrator does not infer missing fields, repair malformed output, or continue.

## Execution capture and immutable records

Each idempotency key owns:

```text
<run_root>/agent_runs/<idempotency_key>/
  request.json
  attempt-001/
    record.json
    stdout.txt
    stderr.txt
    output/...
  attempt-002/...
  completed.json
```

Records include timestamps, elapsed milliseconds, exit code, provider/runtime/model identifiers, input/output hashes, validation outcome, and retry classification. Secret-like values and media paths are redacted before logs are written. Existing attempt records are never overwritten.

## Errors and retries

| Failure | Handling |
|---|---|
| Timeout | Record failure; retry with the same idempotency key up to configured limit. |
| Retryable provider failure | Same key, next immutable attempt. |
| Malformed JSON or contract failure | Non-retryable until inputs/provider output change. |
| Missing adapter | Block immediately with `adapter_unavailable`. |
| Unavailable MCP/tool | Block; retry only when explicitly classified as transient. |
| Path escape or prohibited action | Security failure; never retry automatically. |
| Ambiguous credit-consuming provider result | Do not retry automatically; future adapter must inspect expected output first. |

A retry reuses the same idempotency key. An operator can intentionally reset only by supplying a new reset token, which changes the settings hash and is recorded.

## Idempotency

The key is derived from:

```text
run_id + case_id + stage + contract_id/version
+ ordered input names/types/hashes
+ permission/settings hash + optional explicit reset token
```

A completed matching key is a cache hit: the prior handoff is revalidated and returned without invoking the provider. Failed attempts remain immutable. This prevents duplicate research/voice/provider work on ordinary reruns.

## Mode isolation

- **Synthetic:** only the in-process fixture provider; output root must be under the configured synthetic run root; no commands, network, APIs, MCP, media, or real-case paths.
- **Dry-run:** validates intended provider/configuration and records plans; external execution remains disabled.
- **Real-production:** disabled unless `real_production_enabled` is explicitly true and the requested provider plus every downstream adapter is independently marked tested. Phase B configuration keeps this false.

Mode is part of the request and run record. A synthetic provider refuses a non-synthetic request. A real provider may never fall back to a synthetic success or vice versa.

## Human checkpoints

The adapter cannot decide approvals. After Editor success, the orchestrator constructs and hashes the Checkpoint 1 packet and enters `AWAITING_SCRIPT_APPROVAL`. No adapter invocation is permitted until a matching human approval is present.

After assembly creation, the orchestrator enters `AWAITING_ASSEMBLY_APPROVAL`. Render and Upload Manager metadata completion remain blocked until matching assembly hashes and `render_authorized: true` exist. Approval permits local render only; publishing remains impossible.

## Manual/direct work

An adapter-run record has `execution_origin: "orchestrated_agent"`. Work performed outside the orchestrator has `execution_origin: "manual_direct"` and must append a conforming entry to `direct_generation_manifest.json` with operator/tool, timestamp, sanitized settings, source/license details, inputs/outputs/hashes, verification, and the reason orchestration was bypassed.

Manual work is never silently imported as agent success. The orchestrator must explicitly register and validate its manifest entry and artifact hashes before treating it as an input.

## Future Codex provider

A future provider configuration will identify an executable or runtime service indirectly—never embed secrets in code. It must map the standard request envelope to a sandboxed Codex task, restrict filesystem roots and tool allowlists to the contract, require the handoff file, and return the generic runtime result. Phase B readiness checking may report whether such configuration appears present, but it must not invoke it.
