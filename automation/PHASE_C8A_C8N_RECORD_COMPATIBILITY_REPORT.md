# Cold Truth — C8a/C8n Historical Record Compatibility Report

## Status

`C8A HARNESS REPAIR PASSED — ORDERED REGRESSION STOPPED AT C8B`

## Latest validation update

The C8a harness-owned temporary directory was moved from `future_c8/disposable_output` to the exact test-only parent:

`automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/output`

No arbitrary directory exemption, wildcard, alternate name, or scanner relaxation was added. The strict unexpected-artifact scan is unchanged.

Latest ordered results:

- Focused C8a historical-record test: **1/1 passed**
- Complete C8a suite: **16/16 passed**
- C8b: **11/12 passed; 1 failed**
- C8c through C8n: not run after the required stop
- C8o focused suite: not run after the required stop
- C1 through C7: not run after the required stop

Failing C8b test:

`test_10_no_valid_authorization_instance_or_execution_object_exists`

Safe cause: C8b has its own independent `TemporaryDirectory(dir=DISPOSABLE)` setup. It creates a harness-owned directory inside the same scanned `future_c8/disposable_output` tree before calling C8a's strict metadata helper. The helper correctly returns false. No historical-record content was opened or parsed.

Per the stop rule, C8b was not retried or repaired and no later suite ran. No combined total is claimed. A separate C8b test-harness authorization is required to relocate its temporary directory outside the scanned tree without weakening the scanner.

The C8a historical-record helper was converted from content parsing to strict `lstat` metadata checks for the four immutable C8/C8n records. The first focused test then failed because C8a's existing `Harness.setUp()` creates its own temporary directory under `future_c8/disposable_output` before the test body runs, and the newly strict unexpected-artifact scan correctly classified that directory as an output artifact.

Per the authorization stop rule, no repair, retry, complete C8a run, later regression, or C8o test was attempted.

## Files inspected and changed

Inspected:

- `automation/test_c8a_authorization_schema.py`

Changed:

- `automation/test_c8a_authorization_schema.py`
- `automation/PHASE_C8A_C8N_RECORD_COMPATIBILITY_REPORT.md`

No C8a production validator/schema/contract, C7 file, C8o file, C8b-through-C8n logic, historical record, README, C9 file, renderer, uploader, publisher, or production file was modified.

## Exact recognized historical paths

Relative to `automation/`:

1. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8_one_time_live_authorization.json`
2. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8_one_time_live_safe_audit.json`
3. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8n_one_time_live_authorization.json`
4. `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8n_one_time_live_safe_audit.json`

## Metadata-only behavior

The updated helper uses `lstat` only. It requires each exact path to be:

- a regular file;
- link count exactly `1`;
- not a Windows reparse point; and
- metadata-identical before and after the focused C8a static-source check.

The fingerprint contains device, file identity, mode, link count, size, modification time, creation/change time, and file attributes. The helper does not open, read, parse, deserialize, validate, hash, copy, rename, alter, consume, or delete historical records.

## Focused test result

Focused test:

`test_02_no_new_or_unconsumed_authorization_instance_or_creation_function_exists`

Result: **0/1 passed; 1 failed**

Exact safe failure condition:

`unexpected_historical_artifacts()` returned one path matching the test harness's newly created temporary directory under `disposable_output`.

The observed basename was a disposable runtime-generated test name. It contained no historical record and was not opened or inspected. The test harness cleaned it through its normal teardown.

## Tests not run after the required stop

- Complete C8a suite: not run
- C8b through C8n: not run
- C8o focused suite: not run
- C1 through C7: not run

No combined total is claimed.

## Safety and state confirmation

- No MCP tool, ElevenLabs/provider request, network/API action, Node process, Codex process, browser, or external service was invoked.
- No authorization or audit artifact was created or issued.
- No historical-record content was accessed.
- No credential, configuration, environment value, API key, voice ID, endpoint, account data, private file, or login state was accessed.
- No audio, MP3, media, staging output, rendering, upload, scheduling, publishing, or production activity occurred.
- No real-case or production content was accessed.
- C3 remains `AWAITING_SCRIPT_APPROVAL`; this phase made no state change.
- No C4 approval was created, referenced, or consumed.
- Publishing and real-production modes remain disabled.

## Remaining blocker

A separate authorization is required to reconcile C8a's metadata-only unexpected-artifact scan with the test harness's own pre-existing-per-test temporary directory. The repair must distinguish only that exact harness-owned directory without allowing arbitrary C8 output artifacts, then rerun the focused test and the remaining ordered suites.
