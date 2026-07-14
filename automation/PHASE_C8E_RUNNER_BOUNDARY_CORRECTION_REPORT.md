# Phase C8e — Offline Live-Runner Boundary Correction Report

## Result

C8e corrected the future execution boundary entirely offline. A later, separately authorized C8 phase may launch exactly one named local Python runner process. That future runner is simultaneously prohibited from launching any child process, shell, Node, browser, MCP, Codex, or external command.

C8e creates no runner implementation, authorization artifact, provider capability, transport, network route, audio, or media.

## Exact future runner identity

`c8_one_time_isolated_provider_runner`

The only conceptual runner method is:

`run_once_with_consumed_authorization(authorization_digest, live_transport, opaque_capability_source)`

Future authorized sequence:

1. Launch the named local Python runner once.
2. Validate one future C8 authorization.
3. Require that authorization to be consumed before the request.
4. Obtain one opaque capability for the fixed slot set.
5. Make at most one in-process HTTP request.
6. Write at most one authorized MP3 and one safe audit record.
7. Stop.

The authorization schema now fixes:

- runner identity;
- local Python runner launch authorized: true;
- maximum runner launch count: `1`;
- runner reuse, scheduling, default registration, and global registration: false;
- runner child-process permission: false;
- opaque capability handoff and one in-process HTTP request: true.

## Prohibited child-process behavior

The runner declaration fixes all of these capabilities false:

- child process and subprocess;
- shell, PowerShell, and cmd.exe;
- Node, browser, MCP, and Codex;
- external commands;
- retry, redirect, fallback, and discovery;
- polling, status, follow-up, cleanup, and deletion requests;
- batch and multi-output;
- reuse, scheduling, default/global registration, and production enablement.

This distinguishes the one future top-level Python runner launch from any process the runner might attempt to spawn.

## Opaque configuration handoff

The only abstract configuration slots are:

- `provider_api_credential`
- `locked_voice_identifier`

They are conceptual slot identifiers, not environment-variable names, config paths, keys, endpoints, or values. The slot request must match this exact ordered tuple. Empty, partial, reordered, wildcard, traversal-like, additional, or arbitrary slot requests fail.

The future capability source remains explicitly injected and may expose only `acquire_one_opaque_capability(runner_identity, authorization_digest, requested_slots)`. Declarations prohibit:

- arbitrary or wildcard lookups;
- environment/configuration reading and enumeration;
- path traversal;
- returning raw secrets, endpoints, voice identifiers, headers, or account details;
- printable or serializable capabilities;
- credential writing, rotation, export, or validation;
- generic configuration APIs and arbitrary callable wrappers.

The conceptual capability shape must have no public fields or methods and must be non-printable and non-serializable.

## Future transport boundary

The only transport method remains:

`perform_single_authorized_request(sanitized_request, opaque_provider_capability)`

The declaration fixes maximum outbound requests to one and disables retry, redirects, fallback, discovery, polling, status, follow-up, cleanup, deletion, batching, multi-output, generic requests, raw-response exposure, endpoint/header/account exposure, and unrestricted filesystem-audio access.

No HTTP implementation, provider SDK, endpoint, transport instance, or network import exists in C8e.

## Non-executable proof

- C8e defines protocols, frozen declarations, slot validation, and declaration comparison only.
- The future contract declares C8e creation and execution false.
- No operational runner object is instantiated or registered.
- No real capability/configuration source exists.
- No authorization instance exists.
- No provider/network/process execution path or audio/media output exists.
- C4→C5→C6 and C3 state are unchanged.

## Test results

- C8e runner boundary: 12/12 passed; real invocation not requested.
- C8d live-readiness contract: 12/12 passed; real invocation not requested.
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
- Combined total: 169/169 passed.

## State, activity, and blocker

C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed. Publishing and production remain disabled.

Only local offline Python tests ran. No provider, network, credential/configuration access, narration, audio/media creation, real-case access, rendering, upload, scheduling, publishing, or production activity occurred.

After C8e review, a fresh C8 authorization must explicitly permit one local Python runner launch, one opaque allowlisted provider-configuration handoff, and one in-process HTTP request, with no child process and no retry.
