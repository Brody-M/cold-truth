# Phase C8c — Offline Isolated Execution-Adapter Report

## Result

The isolated C8 request-shape adapter passed all offline tests. It accepts only an in-memory hypothetical C8 record, the exact invented fixture text, the exact locked Mia profile, one contained disposable output reference, and the exact test-only fake inspector. It always returns `execution_authorized: false`.

No authorization artifact, executable client, network path, audio, or media was created.

## Isolation boundary

The adapter imports only the non-executable C8a structural validator and the exact C8c test client. It does not import or call:

- C4 approval code;
- C5 preflight code;
- C6 narration validation or adapters;
- C7 runtime `NarrationProviderAdapter`;
- any agent runner, provider SDK, transport, browser, MCP, shell, or process facility.

It derives no permission from C3, C4, C5, C6, or C7 runtime state. The only C7 material used is the static provider-request contract object and sanitized-request allowlist embedded in the future C8 contract. Their canonical SHA-256 hashes are independently required by the hypothetical authorization record.

The future contract additionally pins the exact authorized invented-text SHA-256 and locked-profile file SHA-256. A different but internally self-consistent text or profile therefore cannot pass.

> **C8d path note:** Output authorization now binds the exact path relative to `automation/`; resolution is centralized by the C8d readiness contract to the single workspace-root canonical file under `automation/fixtures/.../future_c8/disposable_output/`.

## Sanitized request fields

Top level:

- `schema_version`
- `request_kind`
- `synthetic_text`
- `voice_profile`
- `output_format`
- `output_reference`
- `output_path_binding_sha256`
- `isolation`
- `permissions`

Voice profile:

- `voice_profile_name`
- `stability`
- `similarity_boost`
- `style`
- `speed`
- `use_speaker_boost`

Isolation:

- `test_classification`
- `real_case_content_allowed`
- `real_script_approval_used`
- `c4_approval_artifact_allowed`
- `c3_fixture_state_must_remain`

Permissions include one hypothetical future synthetic provider operation set true. Execution, network use, provider invocation, audio creation, retry, redirects, fallback, alternate providers, batching, multi-output, assets, assembly, rendering, upload, scheduling, publishing, and real production are all false. Request and output counts are exactly one.

## Client interface

No default client exists. The only accepted client is the exact `C8cAllowlistedFakeClient` type with:

- exact test-only identity;
- immutable capability declarations;
- no network, provider, subprocess, environment/configuration, secret, browser, MCP, SDK, shell, filesystem-audio, or arbitrary-wrapper capability;
- the original `inspect_request` method with no instance replacement.

Missing, unknown, unsafe, default, fallback, wrapped, subclassed, or altered-method clients are rejected before their method can run.

The fake inspector records only the request object in memory and returns deterministic metadata containing a request hash, zero audio bytes, and false external/provider/network/audio flags. It writes nothing.

## Validation and replay

Every isolation constant, hash, path, format, one-attempt rule, authorization ID, timestamp, status, and permission is revalidated. Absolute, escaping, external, existing, or non-MP3 paths block.

Replay is tracked only in adapter memory. The hypothetical record is neither mutated nor marked consumed. A second use blocks without persisting any state.

## No C4 bypass or authorization creation

C3/C4/C5/C6 artifacts, hashes, handoffs, state overrides, case IDs, real-case text, production scripts, and existing-media references are rejected as additional fields. The adapter contains no authorization writer, validator for C4, or live execution method.

The future directory still contains no valid C8 authorization instance. Successful C8c validation reports both `authorization_artifact_created: false` and `authorization_record_consumed: false`.

## Test results

- C8c isolated adapter: 16/16 passed; real invocation not requested.
- C8b contract alignment: 12/12 passed; real invocation not requested.
- C8a authorization schema: 15/15 passed; real invocation not requested.
- C7 mock provider adapter: 19/19 passed; real invocation not requested.
- C6 synthetic narration adapter: 18/18 passed; real invocation not requested.
- C5 narration preflight: 16/16 passed; real invocation not requested.
- C4 script approval gate: 18/18 passed; real invocation not requested.
- C3 Writer/Editor chain: 6/6 passed; real invocation not requested.
- C2 Research Verifier: 8/8 passed; real invocation not requested.
- C1 provider safety: 17/17 passed; real invocation not requested.
- Combined total: 145/145 passed.

## Activity confirmation and blocker

C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed. Publishing and real production remain disabled.

Only local offline Python tests ran. No provider/network call, secret/configuration access, narration, audio/media creation, real-case access, rendering, upload, scheduling, publishing, or production activity occurred.

After human review, a new separately authorized one-time C8 live synthetic-provider request may be considered.
