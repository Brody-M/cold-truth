# Cold Truth — C7/C8 Record Compatibility Report

## Status

`COMPLETE — OFFLINE REGRESSION CERTIFIED`

The C7 regression now distinguishes the two pre-existing, consumed C8 records from a C7-created authorization artifact. C7 still has no ability to create, validate, consume, or modify a C8 authorization.

## Test-only compatibility change

Changed only `automation/test_narration_provider_adapter.py`, in `test_17_c7_cannot_create_or_validate_c8_authorization`.

The obsolete assertion that no C8 JSON record may exist was replaced with an exact inert allowlist containing only:

- `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8_one_time_live_authorization.json`
- `fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/c8_one_time_live_safe_audit.json`

The C7 test treats those files as historical records using filesystem metadata only. It does not open, read, parse, deserialize, hash, or validate their contents. Before and after the C7 rejection check, it:

- requires both exact paths to exist as regular files;
- rejects a directory, symbolic link, or Windows reparse point at either path;
- fingerprints device, file identity, mode, size, modification time, creation/change time, and file attributes through `lstat`;
- requires the before/after fingerprints to match exactly;
- scans only the deterministic C8 fixture root for an unexpected authorization, audit, JSON, staging, or output artifact;
- continues to verify statically that the C7 adapter contains no C8 creation or validation route; and
- confirms a request containing a `c8_authorization` field is blocked before the fake client executes.

No C7 runtime, C8 schema, C8 validator, C8 contract, C8m implementation, provider adapter, MCP integration, or historical C8 record was changed.

## Ordered test results

All tests used the approved local Python 3.12.13 interpreter. No test was retried.

| Order | Suite | Result |
|---:|---|---:|
| Focused | C7 `test_17_c7_cannot_create_or_validate_c8_authorization` | 1/1 passed |
| 1 | C7 complete suite | 19/19 passed |
| 2 | C1 | 19/19 passed |
| 3 | C2 | 13/13 passed |
| 4 | C3 | 6/6 passed |
| 5 | C4 | 18/18 passed |
| 6 | C5 | 16/16 passed |
| 7 | C6 | 18/18 passed |
| 8 | C8a | 16/16 passed |
| 9 | C8b | 12/12 passed |
| 10 | C8c | 16/16 passed |
| 11 | C8d | 12/12 passed |
| 12 | C8e | 12/12 passed |
| 13 | C8f/C8g | 18/18 passed |
| 14 | C8h | 16/16 passed |
| 15 | C8i/C8j | 17/17 passed |
| 16 | C8m | 18/18 passed |

The focused test is a subset of the complete C7 suite and is not double-counted. The unique C1-through-C8m regression total is **246/246 passed**:

- C1 through C6: 90/90
- C7: 19/19
- C8a through C8m: 137/137

C8m is therefore regression-certified against the repaired C7 expectation.

## Safety and state confirmation

- The prior C8 authorization remains consumed with count `1`; no new or unconsumed authorization was created.
- No MCP tool, provider request, network request, model request, Node process, Codex process, browser, media generator, narration operation, or production operation was invoked.
- No audio or media output was created, renamed, copied, processed, rendered, uploaded, scheduled, or published.
- No credentials, secrets, provider configuration, account data, or protected environment values were accessed.
- No real-case, existing-script, production, or media material was accessed.
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`.
- No C4 approval was created or consumed.
- Publishing and real-production modes remain disabled.

## Next prerequisite

Human review of this C7 compatibility update. Any later live C8 action requires a new, separate, explicit authorization; this phase grants none.
