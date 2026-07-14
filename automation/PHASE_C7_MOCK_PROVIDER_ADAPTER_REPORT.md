# Phase C7 — Mock Provider Adapter Report

## Result

Phase C7 implementation and offline mock validation passed. The provider-neutral adapter accepts only the exact allowlisted test-only in-memory client. It builds a sanitized request in memory, receives deterministic non-audio metadata, and creates no output file.

The real C3 fixture state remains `AWAITING_SCRIPT_APPROVAL`. C7 neither created nor consumed a persistent C4 approval record.

## C4 → C5 → C6 proof requirement

Before constructing a request, the adapter reruns the existing C6 validation gate in a disposable fixture state. This rechecks:

- the exact C4 Writer, Editor, and narration-text hash bindings;
- the passed C5 result, locked profile, format, approval ID, permissions, and path binding;
- the one-time C6 authorization and its Writer, Editor, script, C5-result, profile, and path hashes;
- the exact locked Mia profile and all fixture/path boundaries.

Any failure returns `C7_MOCK_PROVIDER_REQUEST_BLOCKED` before the injected client's method can run.

## Injected-client contract

There is no default client, fallback client, auto-discovery, live-client constructor, transport, provider SDK, endpoint, credential lookup, environment lookup, or network library.

The only accepted client is the exact `C7AllowlistedFakeLocalHttpClient` type. Acceptance requires:

- exact class identity, not a subclass or wrapper;
- exact test-only identity string;
- exact immutable capability declarations showing no network, live provider, subprocess, environment, configuration, credentials, secrets, browser, MCP, SDK, filesystem audio, or arbitrary-callable capability;
- the original allowlisted `send_mock` method;
- no instance-level method replacement.

Unknown, missing, spoofed, default, fallback, auto-discovery, live-provider, network-capable, subprocess-capable, environment-reading, configuration-reading, credential-reading, secret-reading, browser, MCP, SDK, shell, filesystem-audio, and arbitrary-callable clients are rejected before any client method executes.

## Sanitized in-memory request allowlist

The exact top-level fields are:

- `schema_version`
- `request_kind`
- `synthetic_text`
- `voice_profile`
- `output_format`
- `output_reference`
- `source_output_binding_sha256`
- `permissions`

The exact `voice_profile` fields are:

- `voice_profile_name`
- `stability`
- `similarity_boost`
- `style`
- `speed`
- `use_speaker_boost`

The exact permission fields are provider/network invocation, audio creation, assets, assembly, rendering, upload, scheduling, publishing, and real production. Every value is false.

The original C6 `.mp3` proposal is used only to verify its SHA-256 binding. It is never accepted as the C7 output target or copied into the output reference. C7 derives a fixture-contained `.request.json` reference and never writes it.

Explicitly blocked or excluded fields include endpoints, provider/service names, URLs, API keys, tokens, authorization headers, voice IDs, secrets, credentials, environment/configuration references, arbitrary fields, execution commands, and absolute, escaping, existing-audio, or audio-extension targets.

## Fake-client response

The fake client records the sanitized request only in memory and returns these deterministic metadata fields:

- response kind and request SHA-256;
- mock contract status;
- provider and network invoked: false;
- audio bytes: `0`;
- audio file created: false.

It imports no live transport or external-execution facility and writes nothing.

## Future C8 boundary

The `future_c8/` directory contains only:

- a strict shape-only authorization schema;
- a contract declaring creation, validation, consumption, and execution forbidden in C7;
- a README explaining the boundary.

No C8 authorization instance, endpoint, credential placeholder, live client, command, or execution route exists. The C7 adapter has no C8 create/validate method, and its closed C6 input schema rejects an attempted C8 artifact field. Tests confirmed C7 cannot produce or validate a C8 authorization.

## Block conditions

C7 blocks for a missing or non-allowlisted client; altered client method/capabilities; any C4/C5/C6 validation failure; changed Writer, Editor, narration, preflight, profile, authorization, format, or path binding; stale, malformed, mismatched, consumed, or replayed C6 authorization; locked-profile deviations; forbidden or extra fields; absolute/path-traversal/outside-fixture paths; audio extensions or existing audio-named targets; later-stage permission; or any attempt to introduce a live/external capability.

## Test results

- C7 mock provider adapter: 19/19 passed; real invocation not requested.
- C6 synthetic narration adapter: 18/18 passed; real invocation not requested.
- C5 narration preflight: 16/16 passed; real invocation not requested.
- C4 script approval gate: 18/18 passed; real invocation not requested.
- C3 Writer/Editor chain: 6/6 passed; real invocation not requested.
- C2 Research Verifier: 8/8 passed; real invocation not requested.
- C1 provider safety: 17/17 passed; real invocation not requested.
- Total: 102/102 passed.

## Activity confirmation and blocker

Only ordinary local Python tests ran. No real Codex/Node process, model, network, HTTP transport, provider, API, secret, environment/configuration access, browser, MCP, research, real-case access, narration, audio/media creation, assembly, rendering, upload, scheduling, publishing, or real-production action occurred.

The remaining blocker is intentional: one future C8 live synthetic-provider test requires a separate, explicit, one-time human authorization.
