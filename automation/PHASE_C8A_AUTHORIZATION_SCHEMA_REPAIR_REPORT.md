# Phase C8a — Offline Authorization-Schema Repair Report

> **C8b alignment notice:** C8a's original C4/C5/C6 dependency model was superseded by C8b because those artifacts are transitively tied to script approval. The current schema is an isolated connectivity-test contract that retains only synthetic text, locked profile, C7 request contract/allowlist, output, replay, and one-attempt bindings. See `PHASE_C8B_CONTRACT_ALIGNMENT_REPORT.md` for the authoritative current model.

## Result

The future C8 authorization schema and contract were repaired and passed offline validation. C8a created no authorization instance, provider client, execution route, audio, or media. The validator can assess a hypothetical record only in memory and always returns `execution_authorized: false`.

## Required authorization fields

Identity and decision:

- `schema_version`
- `authorization_phase`
- `authorization_id`
- `case_id`
- `decision`
- `reviewer_role`
- `issued_at_utc`
- `expires_at_utc`

Replay and consumption state:

- `authorization_status: issued_unconsumed`
- `consumed: false`
- `consumption_count: 0`
- `single_use: true`

Immutable chain bindings:

- `fixture_text_sha256`
- `c4_script_approval_sha256`
- `locked_mia_profile_sha256`
- `c5_passed_preflight_result_sha256`
- `c6_synthetic_authorization_sha256`
- `c7_provider_request_contract_sha256`
- `provider_request_allowlist_sha256`

Output binding:

- `authorized_output_relative_path`
- `authorized_output_path_sha256`
- `output_format: mp3_44100_128`
- `authorized_output_count: 1`

One-operation limits:

- `operation_scope: one_synthetic_text_to_speech_request_only`
- `retry_allowed: false`
- `maximum_provider_request_count: 1`
- `redirects_allowed: false`
- `fallback_allowed: false`
- `alternate_provider_allowed: false`
- `batch_allowed: false`
- `multi_output_allowed: false`

Future-call boundary fields:

- `network_authorized: true`
- `synthetic_provider_call_authorized: true`
- `audio_output_authorized: true`

Denied permissions:

- `real_case_use_authorized: false`
- `asset_authorized: false`
- `assembly_authorized: false`
- `rendering_authorized: false`
- `upload_authorized: false`
- `scheduling_authorized: false`
- `publishing_enabled: false`
- `real_production_enabled: false`

## Contract and allowlist binding

The provider-neutral contract embeds both the C7 provider-request contract object and exact sanitized-request allowlist. A future authorization must bind the canonical SHA-256 of each object independently. This adds machine-checkable C7 binding without changing C7 behavior or adding a provider identity, endpoint, transport, credential, environment lookup, or configuration lookup.

The locked profile recorded in the contract is Mia with stability `0.72`, similarity boost `0.76`, style `0.05`, speed `0.94`, speaker boost enabled, and `mp3_44100_128` output.

## Strict validation

The closed schema requires every declared field, rejects additional properties and null/loose types, and fixes all decisions, counts, scopes, formats, statuses, and permission values with singleton enums.

The non-executable semantic validator additionally:

- compares every supplied chain and output binding to exact expected values;
- requires a contained relative `.mp3` path under the future disposable C8 output root;
- rejects absolute paths, traversal, outside roots, existing targets, non-approved extensions, and provider/service-like path text;
- verifies the exact path-text SHA-256;
- parses UTC timestamps and requires expiry after issue with a maximum 15-minute lifetime;
- records the hypothetical authorization ID and record hash only in memory;
- rejects reuse of the ID, including a modified record using the same ID;
- always reports that no artifact was created and no execution/network/provider/audio action is authorized by C8a.

Secret-like, endpoint-like, provider-like, environment/configuration-like, command-like, and arbitrary execution fields fail through the closed schema. No artifact creation or persistence function exists in the helper.

## C7 and C8a boundary

The contract continues to declare C7 creation, validation, consumption, and execution forbidden. It also declares C8a creation and execution forbidden. C7 has no C8 create/validate route, and the future directory contains only schemas, contracts, READMEs, and an empty disposable-output boundary—no authorization instance.

## Test results

- C8a authorization schema: 15/15 passed; real invocation not requested.
- C7 mock provider adapter: 19/19 passed; real invocation not requested.
- C6 synthetic narration adapter: 18/18 passed; real invocation not requested.
- C5 narration preflight: 16/16 passed; real invocation not requested.
- C4 script approval gate: 18/18 passed; real invocation not requested.
- C3 Writer/Editor chain: 6/6 passed; real invocation not requested.
- C2 Research Verifier: 8/8 passed; real invocation not requested.
- C1 provider safety: 17/17 passed; real invocation not requested.
- Combined total: 117/117 passed.

## State and activity confirmation

C3 remains `AWAITING_SCRIPT_APPROVAL`, and no persistent C4 approval was created or consumed. Publishing and real-production modes remain disabled.

Only local offline Python test execution occurred. No secret, environment/configuration value, provider detail, endpoint, network/API call, live client, narration, audio/media creation, real-case access, rendering, upload, scheduling, publishing, or real-production activity occurred.

## Remaining blocker

After human review of C8a, any actual C8 live synthetic-provider request requires a fresh, separate, explicit, one-time authorization.
