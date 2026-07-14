# Cold Truth — C8o Direct ElevenLabs API Design Report

## Status

`IMPLEMENTED OFFLINE — REGRESSION CERTIFICATION BLOCKED AT C7`

The C8o focused adapter contract passed all offline mock-only tests. The ordered C1-through-C8n regression run stopped at C7 because its existing historical-record allowlist does not yet recognize the immutable C8n authorization and audit records. No retry or compatibility repair was attempted.

## Files created or changed

- `automation/c8o_direct_elevenlabs_api_contract.py`
- `automation/test_c8o_direct_elevenlabs_api_contract.py`
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/README.md`
- `automation/README.md`
- `automation/PHASE_C8O_DIRECT_ELEVENLABS_API_DESIGN_REPORT.md`

No historical C8 or C8n authorization/audit record, C1-through-C7 implementation, production adapter, real-case fixture, C9 file, renderer, uploader, or MCP configuration was modified.

## Future route and boundary

The only future route identifier is:

`direct_elevenlabs_https_api`

The ElevenLabs MCP route is retired for future C8 narration-connectivity testing. Its prior fail-closed authorization and audit records remain immutable historical evidence.

C8o permits, only under a later separate authorization:

- one dependency-injected POST transport call;
- one response with status `200`, content type `audio/mpeg`, non-empty bytes, a minimal MP3 signature, and a maximum size of 5 MiB;
- one dependency-injected exclusive-create write request to the exact canonical output path;
- one closed safe audit result; and
- no retry or later action.

The adapter rejects changed text, model, voice settings, speed, output format, route, output path, authorization binding, or opaque injected-value presence before transport execution. It also rejects an existing destination, non-success response, empty response, malformed/non-audio response, oversized response, unknown response fields, bytes-like non-`bytes` payloads, transport failure, write failure, and authorization replay.

The writer boundary receives only the exact canonical relative path, returned fake MP3 bytes, and `exclusive_create: true`. The offline tests use an in-memory writer; no filesystem audio is created.

## Future placeholder names

- `COLD_TRUTH_ELEVENLABS_API_KEY`
- `COLD_TRUTH_ELEVENLABS_MIA_VOICE_ID`

They are names only. Their values and presence were not read, checked, enumerated, set, printed, logged, hashed, serialized, or persisted.

## Focused test result

`test_c8o_direct_elevenlabs_api_contract.py`: **11/11 passed**

The suite used only an in-memory fake transport, opaque placeholder objects, and an in-memory exclusive writer. It made no MCP, provider, API, or network request and created no audio or media file.

## Ordered regression result

- C1: 19/19 passed
- C2: 13/13 passed
- C3: 6/6 passed
- C4: 18/18 passed
- C5: 16/16 passed
- C6: 18/18 passed
- C1 through C6 subtotal: **90/90 passed**
- C7: **18/19 passed; 1 failed**
- C8a through C8n: **not run after the required stop**

Failing test:

`test_17_c7_cannot_create_or_validate_c8_authorization`

Confirmed cause: the C7 test's exact historical-record allowlist contains the original consumed C8 authorization/audit pair but not the later immutable files:

- `c8n_one_time_live_authorization.json`
- `c8n_one_time_live_safe_audit.json`

This is a stale test expectation, not a C7 runtime behavior failure and not a C8o adapter failure. No combined C1-through-C8n total is claimed because the full ordered baseline did not complete.

## Safety and state confirmation

- No MCP tool, ElevenLabs/provider request, network/API call, live authorization, credential/configuration/environment access, or account access occurred.
- No actual credential or voice-identifier value was read or tested for presence.
- No audio/media file, output file, authorization artifact, or safe-audit artifact was created by C8o.
- No real-case, existing-script, production, rendering, upload, scheduling, publishing, or media-workflow activity occurred.
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`.
- No C4 approval was created, referenced, validated, or consumed.
- Publishing and real-production modes remain disabled.

## Remaining blocker

A separately authorized test-only C7 compatibility update must add the two immutable C8n historical records to C7's exact inert allowlist without changing C7 runtime behavior. After that, C7 and the remaining C8a-through-C8n regressions must pass before C8o can be declared fully regression-certified. A live direct-API authorization remains separately required after certification and human review.
