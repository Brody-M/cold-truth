# Phase C6 — Synthetic Narration Adapter Report

## Result

Phase C6 implementation and offline validation passed. The fixture-only adapter has exactly two modes—`validate_request` and `fake_runner`—and neither mode can contact a narration provider or create playable audio. The actual C3 state remains `AWAITING_SCRIPT_APPROVAL`.

## C4 → C5 → C6 authorization chain

1. The synthetic C4 approval is validated against its strict schema and bound to the exact current Writer handoff, Editor handoff, and narration-text SHA-256 hashes.
2. The synthetic passed C5 result is validated against the C5 result schema. It must reference the same C4 approval, proposed relative output path, `Mia` profile name, and `mp3_44100_128` format while keeping generation, networking, file creation, and all production permissions false.
3. The C6 authorization binds the exact Writer, Editor, narration-text, passed-preflight-file, locked-profile-file, and relative-output-path SHA-256 hashes. Its one valid decision is `approve_synthetic_narration_test`, by `human_owner`, for `synthetic_narration_generation_only`.
4. A successful validation consumes the C6 narration authorization ID in an immutable fixture-local record. Reuse blocks.

The C6 artifact's `narration_generation_authorized: true` means only that this inert fixture adapter may validate the proposed synthetic test. It is not a real narration authorization and does not permit a provider call, networking, credentials, audio creation, normal pipeline use, or work on any real case.

## Locked synthetic Mia settings

- profile name: `Mia`
- stability: `0.72`
- similarity boost: `0.76`
- style: `0.05`
- speed: `0.94`
- speaker boost: `true`
- output format: `mp3_44100_128`

The profile explicitly keeps audio generation, networking, real production, and publishing disabled. Its API-key-required boolean is informational only; C6 reads no key, voice ID, endpoint, environment variable, provider configuration, or real narration setting.

## Adapter modes

### `validate_request`

Validates the full C4/C5/C6 hash chain, strict schemas, profile, permissions, replay state, and path containment. It creates only immutable sanitized JSON validation/consumption records. It creates no proposed output and invokes nothing external.

### `fake_runner`

Performs the same validation. In memory it returns deterministic metadata stating zero fake duration, zero fake audio bytes, no provider, no network, and no audio creation. When explicitly requested by an offline test, it may write only a `.fake.json` metadata artifact beneath the C6 fixture output tree. MP3, WAV, and other playable formats are never written.

Any third mode blocks.

## Readiness requirements

`SYNTHETIC_NARRATION_READY` requires:

- contained fixture-only input, state, and proposed-output paths;
- valid human-owner C4 approval with exact Writer, Editor, and script hashes;
- valid passed C5 result tied to that approval, profile identity, format, and proposed path;
- valid unconsumed C6 authorization with exact Writer, Editor, script, C5-result, profile, and path hashes;
- exact locked Mia profile and `mp3_44100_128` format;
- exact `synthetic_narration_generation_only` action;
- no existing proposed audio file;
- network, provider invocation, assets, assembly, rendering, upload, scheduling, publishing, and real production disabled.

The ready result explicitly reports `provider_invoked: false`, `network_invoked: false`, `audio_file_created: false`, `real_production_enabled: false`, and `next_required_authorization: separate_human_authorization_for_one_synthetic_provider_call`.

## Blocking conditions

The gate blocks missing, rejected, blocked, stale, altered, malformed, mismatched, or replayed C4/C5/C6 artifacts; changed Writer, Editor, or narration text; any Writer/Editor/script/profile/preflight/path hash mismatch; any locked-profile or format mismatch; absolute, escaping, real-production, non-fixture, or existing-audio paths; secret, key, voice-ID, endpoint, URL, credential, provider-configuration, external-service, environment, or production references; any network, actual narration, provider, subprocess, or audio-creation request; any asset, assembly, render, upload, schedule, publish, or real-production permission; and every unsupported adapter mode.

## Validation results

- C6 adapter suite: 18/18 passed; real invocation not requested.
- C5 preflight regression: 16/16 passed; real invocation not requested.
- C4 approval regression: 18/18 passed; real invocation not requested.
- C3 Writer/Editor regression: 6/6 passed; real invocation not requested.
- C2 Research Verifier regression: 8/8 passed; real invocation not requested.
- C1 provider-safety regression: 17/17 passed; real invocation not requested.
- Total: 83/83 passed.

## Activity confirmation and next prerequisite

Only local offline Python test processes ran. No Codex or Node process, provider, model, network, MCP, browser, API, research, secret access, real-case access, narration, playable audio, media generation, assembly, rendering, download, upload, scheduling, publishing, or real-production action occurred.

One synthetic provider call would require a new, explicit, one-time human authorization after C6. Nothing in C6 supplies that authorization.
