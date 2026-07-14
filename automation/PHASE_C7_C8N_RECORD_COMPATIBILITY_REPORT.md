# Cold Truth — C7/C8n Historical Record Compatibility Report

## Status

`C7 COMPATIBILITY COMPLETE — ORDERED REGRESSION STOPPED AT C8A`

The authorized C7 test-only update passed its focused and complete suites. The ordered run then stopped at the first C8a failure because C8a's separate historical-record helper still expects only the original two C8 records and does not yet recognize the immutable C8n pair. No retry or repair was attempted.

## Files inspected and changed

Inspected:

- `automation/test_narration_provider_adapter.py`

Changed:

- `automation/test_narration_provider_adapter.py`
- `automation/PHASE_C7_C8N_RECORD_COMPATIBILITY_REPORT.md`

No C7 runtime source, C8o source/test, C8 schema/contract, historical authorization/audit record, README, production file, or media file was modified.

## Exact inert allowlist

The C7 test recognizes exactly these four paths relative to `automation/`:

1. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8_one_time_live_authorization.json`
2. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8_one_time_live_safe_audit.json`
3. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8n_one_time_live_authorization.json`
4. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8n_one_time_live_safe_audit.json`

## Metadata-only behavior

The C7 test uses `lstat` metadata only. For every exact path it requires:

- a regular file;
- link count exactly `1`;
- no Windows reparse-point attribute;
- identical device, file identity, mode, link count, size, modification time, creation/change time, and file attributes before and after the C7 rejection check.

It does not open, read, parse, deserialize, hash, validate, issue, consume, replay, or modify any historical record. Its bounded scan remains inside the deterministic `future_c8` fixture and rejects extra JSON, authorization, audit, staging, non-README output, backup, copy, renamed, temporary, or substitute artifacts.

## Ordered test results

- Focused C7 historical-record test: **1/1 passed**
- Complete C7 suite: **19/19 passed**
- C1 through C6: **90/90 passed**
- C8a: **15/16 passed; 1 failed**
- C8b through C8n: **not run after the required stop**
- C8o focused suite: **not run after the required stop**

Failing C8a test:

`test_02_no_new_or_unconsumed_authorization_instance_or_creation_function_exists`

Safe diagnosis: C8a's separate `post_attempt_artifacts_are_closed()` helper still requires the historical JSON-name set to equal only the original C8 authorization/audit pair. The two immutable C8n records make that stale equality check false. Because the name-set check fails first, that helper returns before opening or parsing historical-record content in this run.

No combined total is claimed because the complete ordered suite did not pass.

## Safety and state confirmation

- No MCP tool, ElevenLabs/provider request, network/API action, Node process, Codex process, browser, or external service was invoked.
- No authorization or audit artifact was issued or created.
- No historical-record content was accessed by the C7 compatibility test or by the failing C8a helper path.
- No credential, configuration, environment value, API key, voice ID, endpoint, account data, private file, or login state was accessed.
- No audio, MP3, media, staging, rendering, upload, scheduling, publishing, or production activity occurred.
- No real-case or production content was accessed.
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`.
- No C4 approval was created, referenced, or consumed.
- Publishing and real-production modes remain disabled.

## Remaining blocker

A separately authorized C8a-focused test compatibility update must extend its immutable historical-record expectation to the exact C8n pair while preserving its safety checks. After that, C8a through C8n and the C8o focused suite must be rerun in order before C8o can be declared regression-certified.
