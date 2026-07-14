# Cold Truth Phase B Test Report

**Date:** 2026-07-11  
**Scope:** agent-runtime adapter and autonomous synthetic orchestration only  
**Real cases:** not used  
**External calls/media/platform actions:** none

## Test commands

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation\test_agent_runtime_orchestration.py
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation\test_orchestrator.py
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation\runtime_readiness_check.py
```

## Test-run history

### Initial Phase B run

- 8 tests executed.
- 6 passed, 1 failed, 1 errored.
- The failure was confined to run-record redaction: an overly broad secret-value expression redacted legitimate 64-character SHA-256/idempotency values. That made a completed handoff path unreadable on cache reuse and changed the recorded key.
- Correction: structured secret-labeled fields remain redacted, but normal SHA-256/idempotency values are preserved. Recognizable bearer/prefixed credential formats remain redacted.

### Corrected Phase B run

- 8 tests executed.
- 8 passed, 0 failed.

### Final Phase B run after readiness coverage

- 9 Phase B tests executed.
- 9 passed, 0 failed.
- 6 original orchestrator regression tests executed.
- 6 passed, 0 failed.

**Final total:** 15 passing tests, 0 failures.

## Autonomous state transitions observed

```text
QUEUED
-> STRATEGIST_COMPLETE
-> RESEARCH_VERIFIED
-> CASE_SELECTED
-> WRITER_COMPLETE
-> AWAITING_SCRIPT_APPROVAL
-> SCRIPT_APPROVED
-> NARRATION_GENERATED
-> AUDIO_PREFLIGHT_PASSED
-> WHISPERX_ALIGNED
-> LONGFORM_ASSETS_READY
-> SHORTS_PACKAGE_READY
-> TRACK_ISOLATION_VALIDATED
-> AWAITING_ASSEMBLY_APPROVAL
-> ASSEMBLY_APPROVED
-> DRY_RUN_COMPLETE
```

The synthetic Strategist selected `cedar-grove-placeholder`, which matched the orchestrator’s independent deterministic ranking.

## Agent handoff validation

Normal contract-compliant handoffs passed for:

- Strategist
- Research Verifier
- Writer
- Editor
- Visual Producer
- Shorts Editor
- Upload Manager

For every agent, validation confirmed contract/version/run/case/stage identity, required input names, contract result fields, required outputs, output path containment, file existence, SHA-256, byte count, allowed tool actions, synthetic no-network status, and `publishing_enabled: false`.

Negative validation tests confirmed:

- A malformed Writer handoff entered `AGENT_BLOCKED`; no draft was adopted.
- A malicious output path outside its attempt output root entered `AGENT_BLOCKED`; no escape file was created.
- A missing Writer adapter entered `AGENT_BLOCKED` with `adapter_unavailable` detail.
- A configured first-attempt provider failure retried once using the same idempotency key and preserved both immutable attempt records.
- A repeated identical agent request returned a cache hit and the same handoff hash without invoking the fixture again.

## Human Checkpoint 1 evidence

- Editor produced the reverse outline, reviewed draft, editorial artifacts, and a structured handoff.
- The orchestrator rebuilt a canonical Checkpoint 1 packet bound to the exact outline and draft hashes.
- Execution stopped at `AWAITING_SCRIPT_APPROVAL`.
- No narration descriptor existed before matching approval metadata was added.
- A stale approval after script revision failed the hash check and could not resume.

## Human Checkpoint 2 evidence

- After valid script approval, the synthetic flow produced narration/preflight/alignment records, long-form asset records, Shorts asset records, zero-shared-asset validation, and two unrendered assembly records.
- Execution stopped at `AWAITING_ASSEMBLY_APPROVAL`.
- No render plan existed before matching assembly approval with `render_authorized: true`.
- After approval, dry-run created only a `media_created: false` synthetic render record and local metadata artifacts.

## Revision invalidation evidence

A synthetic reviewed-script revision invalidated and marked stale:

- final script;
- narration and preflight;
- alignment;
- long-form visual timeline/assets;
- Shorts package/timeline/assets;
- track-isolation result;
- both assemblies and Checkpoint 2 packet;
- render/validated-render records;
- Upload Manager package and metadata/audit completion.

Both active approvals were removed from run state. Existing approval files could not be reused because their hashes were stale.

## No-external-activity evidence

- Provider runtime for every attempt: `python-in-process`.
- Model: `none`.
- External commands: 0.
- Runtime-readiness external calls: 0.
- No URL appeared in any synthetic run artifact.
- No MP4, MOV, MKV, AVI, WEBM, MP3, WAV, M4A, AAC, or FLAC was created.
- No Jodi Huisentruit, Amy Mihaljevic, or Springfield Three name/path appeared in a synthetic run.
- No upload, schedule, publish, OAuth, platform, browser, MCP, API, Codex, FFmpeg, WhisperX, Pexels, ElevenLabs, or gameplay-download action occurred.

## Runtime-readiness result

- Codex executable discoverable: **yes**.
- Configured runtime command present: **no**.
- Required contract/schema files present: **yes**.
- Fixture mode available: **yes**.
- Real-production mode enabled: **no**.
- Publishing enabled/implemented: **no/no**.
- Real research adapter configured: **no**.
- Narration adapter configured: **no**.
- Alignment adapter configured: **no**.
- Long-form asset adapter configured: **no**.
- Shorts asset adapter configured: **no**.
- Assembly adapter configured: **no**.
- Render adapter configured: **no**.
- Ready for controlled real-agent fixture test: **no**; the executable is discoverable, but the generic provider/command is not configured.
- Ready for real-production enable review: **no**.
- Secrets read or printed: **no**.
- Runtime invoked: **no**.

## Remaining blockers before one controlled real-agent test

1. Implement a generic Codex provider translating the standard request envelope into a sandboxed runtime task.
2. Configure its command indirectly through `COLD_TRUTH_CODEX_RUNTIME_COMMAND`; never store the command’s credentials in the vault.
3. Independently test tool/filesystem permission mapping, timeout, malformed output, unavailable-tool behavior, retry classification, redaction, and output-root containment.
4. Implement and test the real Research Verifier/research adapter without enabling any real production package.
5. Keep narration, alignment, asset, assembly, and render adapters disabled for the first controlled agent-only test.
6. Obtain separate human authorization for one synthetic-to-real-agent test using a non-case fixture.
7. Do not set `real_production_enabled: true`; that flag remains reserved until all downstream adapters have independent validation.

Publishing remains unimplemented and cannot be enabled by the agent-runtime adapter.
