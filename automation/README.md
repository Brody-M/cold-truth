# Cold Truth Backend Orchestration

The stateful orchestrator is `automation/orchestrator.py`. It defaults to dry-run, validates deterministic case selection and the two human checkpoints, writes an append-only audit manifest, and never publishes. Phase B adds a provider-neutral agent runner with contract validation and immutable per-attempt records.

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation/orchestrator.py `
  --queue-file automation/fixtures/simulated_case/queue.json `
  --run-root automation/runs/example
```

Agent contracts are versioned JSON files under `automation/contracts/`. The synthetic regression suite is `automation/test_orchestrator.py`.

## Fixture-only agent orchestration

Run both fixture suites with the bundled Python runtime:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation/test_agent_runtime_orchestration.py
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation/test_orchestrator.py
```

The Phase B suite creates its run roots in temporary directories and removes them afterward. It uses only the in-process fixtures under `automation/fixtures/simulated_agents/`; it cannot call Codex, MCP, browsers, APIs, media providers, FFmpeg, WhisperX, or platform services.

To run a persistent fixture demonstration that stops at Human Checkpoint 1:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation/orchestrator.py `
  --queue-file automation/fixtures/simulated_case/queue.json `
  --run-root automation/runs/phase-b-fixture `
  --run-id phase-b-fixture `
  --synthetic-agent-runtime
```

Rerun the same command after adding matching fixture approval metadata to resume to the next checkpoint. The orchestrator refuses a non-fixture queue in synthetic-agent mode.

## Inspecting run records and blocked states

For a retained run root, inspect:

```text
run_state.json                         Current state and blocking reason
manifest.json                          Run-level event index
event_log.jsonl                        Append-only transitions
agent_runs/<idempotency-key>/request.json
agent_runs/<idempotency-key>/attempt-*/record.json
agent_runs/<idempotency-key>/attempt-*/stdout.txt
agent_runs/<idempotency-key>/attempt-*/stderr.txt
agent_runs/<idempotency-key>/completed.json
```

`AGENT_BLOCKED` means a missing adapter, provider failure, malformed handoff, contract violation, prohibited action, or path escape stopped progression. Do not edit an immutable attempt record. Correct the provider/input and start with an explicitly changed reset token or a new run.

## Runtime readiness

This check is read-only. It does not invoke Codex or any provider and never prints command values or secrets:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation/runtime_readiness_check.py
```

## Adding a future provider safely

1. Implement the generic `AgentProvider.execute(request, isolated_output_root, attempt)` interface.
2. Obtain runtime commands/provider details only through `runtime_config.json` and the named environment variable. Never put secrets in configuration or logs.
3. Map filesystem roots and tool permissions from the contract; deny everything else.
4. Require a `common_handoff.schema.json` artifact and validate all contract result/output fields.
5. Capture exit code, duration, sanitized stdout/stderr, artifact hashes, and runtime/model metadata.
6. Test timeout, malformed output, retry, path escape, missing tool, and checkpoint behavior independently.
7. Mark the adapter configured only after those tests pass.

`real_production_enabled` in `runtime_config.json` must remain `false` until every required adapter is independently tested and one controlled real-agent run is separately authorized. Enabling a runtime provider does not authorize a real case, media generation, or publishing.

Publishing remains unimplemented and disabled. Upload Manager produces local metadata only and receives no platform permissions.

## Phase C1: fixture-only real Codex test

The disposable workspace is `automation/fixtures/real_codex_fixture_workspace/`. It contains no real cases or secrets. The C1 provider is `automation/providers/codex_exec_provider.py`, and its safety/controlled test runner is `automation/test_real_codex_fixture.py`.

Run non-invoking safety tests:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B automation/test_real_codex_fixture.py
```

Only after those tests pass and a separate C1 authorization exists, supply the executable path to the runner:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B automation/test_real_codex_fixture.py `
  --run-real `
  --codex-executable '<installed-codex-executable>'
```

The runner creates `COLD_TRUTH_CODEX_RUNTIME_COMMAND` only inside its own Python process as a JSON array, removes it afterward, and never changes user/machine environment variables. The provider reads no other environment value and never logs the command value.

C1 safety properties:

- `codex exec` only; no interactive TUI;
- `workspace-write`, fixture-only `cwd` and `--cd`;
- stdin prompt, JSONL events, output schema, last-message artifact, and ephemeral mode;
- no inherited credentials, tools, parent paths, side artifacts, media, or publishing;
- malformed output, timeout, nonzero exit, unsafe flags, broad permissions, and path escapes block safely.

A passing C1 test authorizes nothing beyond the disposable fixture. It does not authorize real-case access, research, browsing, MCP, narration, media sourcing, alignment, assembly, rendering, upload, scheduling, or publishing. `real_production_enabled` must remain false.

## Phase C2: synthetic Research Verifier

Phase C2 adds a separate disposable workspace at `automation/fixtures/real_research_verifier_fixture_workspace/`. It proves offline that a Research Verifier handoff can be remote-schema-shaped, deterministically normalized, hash-bound to three synthetic inputs, and validated against a fixture-specific canonical schema and contract without weakening C1.

Run the offline C2 suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' automation\test_real_research_verifier_fixture.py
```

Then run the non-invoking C1 regression suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' automation\test_real_codex_fixture.py
```

Do not add `--run-real` during ordinary validation. Both commands must report that the real invocation was not requested.

The C2 implementation permits no browser research, web access, MCP, external API, external source, real case, real candidate, media provider, production tool, platform action, or publishing action. Its provider accepts only three synthetic JSON inputs inside its isolated fixture root. `real_production_enabled` remains false.

Even a future passing real C2 fixture test would authorize only that disposable synthetic run. It would not authorize a real-case Research Verifier, browsing, source collection, Writer progression, production adapters, media generation, rendering, upload, scheduling, or publishing. Exactly one real C2 fixture invocation requires a separate explicit human authorization.

The first authorized real C2 fixture request reached Codex and passed remote structured-output generation, but canonical validation blocked because the response listed the explicitly rejected conflict claim in `source_conflicts` while the fixture canonical schema required an empty array. No retry occurred. C2 remains incomplete pending a human-reviewed fixture semantics decision, offline regression testing, and separate authorization for any future real attempt.

The C2.1 human fixture decision resolved that contradiction: canonical `source_conflicts` must contain exactly `SYN-RV-X3: source_ledger_conflict`, while `unsupported_or_creator_derived_material` must contain only `SYN-RV-X1` and `SYN-RV-X2`. The corrected offline C2 suite passed 8/8 and C1 regressions passed 17/17. No real retry occurred. A new real C2 fixture attempt still requires separate explicit one-time authorization.

The final authorized C2 fixture run subsequently passed end to end: remote schema acceptance, deterministic normalization, canonical schema validation, Research Verifier contract validation, hash binding, immutable records, and containment all succeeded. Phase C2 is complete. This does not authorize Writer progression, real-case Research Verifier work, browsing, MCP, production adapters, media, or publishing; Phase C3 requires a separate human authorization and scoped plan.

## Phase C3: synthetic Writer and Editor chain

Phase C3 uses `automation/fixtures/real_writer_editor_fixture_workspace/` to test an invented, three-claim Writer-to-Editor chain offline. It produces no real script and contains no real case information. The Writer must attribute every factual sentence to one approved synthetic claim; the Editor applies exact exclusion, unsupported-material, coherence, and zero-tolerance redundancy checks.

Run the offline C3 suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' automation\test_writer_editor_fixture.py
```

The only successful terminal state is `AWAITING_SCRIPT_APPROVAL`. Narration, assets, assembly, rendering, upload, scheduling, publishing, and real production remain unauthorized. C3 offline validation does not authorize a real provider run; any real Writer/Editor fixture execution requires a separate explicit human authorization and isolated no-retry plan.

The authorized synthetic C3 Writer-to-Editor fixture chain subsequently passed end to end. Writer and Editor each passed remote validation, normalization, canonical schema, contract, hash, and containment checks, and the chain stopped at `AWAITING_SCRIPT_APPROVAL`. Phase C3 is complete, but narration, assets, assembly, rendering, publishing, and real production remain unauthorized; Phase C4 requires a separate human authorization and scoped plan.

## Phase C4: synthetic human script-approval gate

Phase C4 adds an offline, fixture-only human decision gate under `automation/fixtures/real_writer_editor_fixture_workspace/approval_gate/`. Agent handoffs cannot approve their own work. A separate decision artifact must identify `reviewer_role: human_owner` and match the exact SHA-256 hashes of the C3 Writer handoff, Editor handoff, and Writer narration text.

Run the offline C4 suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_script_approval_gate.py
```

A valid approval changes only `AWAITING_SCRIPT_APPROVAL` to `SCRIPT_APPROVED_FOR_PREFLIGHT` and permits only `narration_preflight_only`. This is a validation/design boundary and does not authorize narration generation. A valid rejection changes state only to `WRITER_REVISION_REQUIRED`. Missing or stale artifacts, agent reviewers, changed hashes, replayed IDs, path escapes, forward stages, and any enabled narration, asset, rendering, publishing, or real-production flag block safely.

Submitted decisions create immutable sanitized records inside the fixture output tree. C4 passed 18/18 offline tests; non-invoking regressions also passed C3 6/6, C2 8/8, and C1 17/17. No real process, network, model, tool, media, platform, or production activity is part of this phase.

## Phase C5: synthetic narration preflight

Phase C5 adds a fixture-only preflight gate under `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/`. It consumes only the synthetic Writer and Editor handoffs, an explicitly test-only C4 approval, a non-secret locked Mia profile, and a proposed relative output filename.

Run the offline C5 suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_narration_preflight_gate.py
```

The gate recalculates the Writer, Editor, and exact narration-text SHA-256 hashes, enforces the locked synthetic Mia settings, rejects replayed approvals, and resolves the proposed filename beneath the C5 fixture output directory. It never creates the proposed audio file. A pass returns `NARRATION_PREFLIGHT_PASSED` while keeping narration generation, networking, assets, assembly, rendering, upload, scheduling, publishing, and real production false.

No API-key value, real voice ID, endpoint, environment configuration, or production narration setup is read. The profile's `api_key_required_for_generation: true` is a boolean warning only: a future synthetic generation test would require separate explicit human authorization.

C5 passed 16/16 offline tests. Non-invoking regressions passed C4 18/18, C3 6/6, C2 8/8, and C1 17/17. No real invocation was requested in any suite.

## Phase C6: synthetic narration adapter

Phase C6 adds `automation/providers/synthetic_narration_adapter.py` and a fixture-only authorization gate. It is not wired into the normal narration implementation or production pipeline. It supports only `validate_request` and `fake_runner`; every other mode blocks.

The C6 authorization is one-time and bound to the exact Writer handoff, Editor handoff, narration text, passed C5 preflight result, locked profile, and proposed relative output path hashes. Its `narration_generation_authorized: true` applies only to validation of this inert synthetic fixture adapter. It does not authorize a provider call or audio creation.

Run the offline C6 suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_synthetic_narration_adapter.py
```

`validate_request` produces only immutable sanitized fixture JSON records. `fake_runner` returns deterministic zero-audio metadata in memory and may write only an explicitly requested `.fake.json` test artifact beneath the C6 fixture output directory. Neither mode reads credentials or environment variables, uses networking, invokes a provider/process, or creates MP3/WAV media.

C6 passed 18/18 offline tests. Non-invoking regressions passed C5 16/16, C4 18/18, C3 6/6, C2 8/8, and C1 17/17, for 83/83 total checks. One synthetic provider call would require a separate explicit one-time human authorization after C6.

## Phase C7: provider-neutral mock interface

Phase C7 adds `automation/providers/narration_provider_adapter.py`. It reruns the complete C6 fixture validation chain and then builds only a sanitized in-memory provider-contract preview. The original C6 `.mp3` proposal remains a hash binding, not a C7 output target; C7 derives a non-audio `.request.json` reference and never writes it.

The adapter has no default or fallback client. It accepts only the exact allowlisted `C7AllowlistedFakeLocalHttpClient` from the test-only automation helper, with immutable declarations denying network, live-provider, subprocess, environment/configuration, credential/secret, browser, MCP, SDK, filesystem-audio, and arbitrary-callable capabilities. Unknown, spoofed, subclassed, or method-replaced clients fail before execution.

Run the offline C7 suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_narration_provider_adapter.py
```

The `narration_preflight/future_c8/` fixture area defines only a strict future authorization schema and a contract that forbids C7 creation, validation, consumption, or execution. It contains no authorization instance, endpoint, credential placeholder, live implementation, or command.

C7 passed 19/19 offline tests. Non-invoking regressions passed C6 18/18, C5 16/16, C4 18/18, C3 6/6, C2 8/8, and C1 17/17, for 102/102 total checks. C3 remains `AWAITING_SCRIPT_APPROVAL`; no persistent C4 approval was created or consumed. Any C8 live synthetic-provider test requires a separate explicit one-time human authorization.

## Phase C8a: offline future-authorization repair

Phase C8a repairs only the shape and offline validation rules for a future one-time C8 authorization. It creates no authorization instance and adds no live client, provider, endpoint, credential, environment/configuration lookup, network path, or execution capability.

The strict schema now requires exact hashes for the synthetic text, C4 approval, locked Mia profile, passed C5 result, C6 authorization, C7 provider-request contract, C7 request allowlist, and contained relative output path. It fixes the format to `mp3_44100_128`, request/output counts to one, and retry, redirects, fallback, alternate providers, batching, multi-output, real-case use, assets, assembly, rendering, upload, scheduling, publishing, and real production to disabled.

Run the offline C8a suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_c8a_authorization_schema.py
```

The helper validates hypothetical records only in memory, tracks replay only in memory, creates no artifact, and always keeps execution unauthorized. C8a passed 15/15 tests; C1–C7 regressions passed 102/102, for 117/117 total offline checks. A fresh separate one-time human authorization remains required for any actual C8 provider request.

## Phase C8b: isolated-connectivity contract alignment

C8b supersedes C8a's original dependency selection without changing the underlying one-attempt safety mechanics. C5 and C6 cannot be reused by isolated C8 because both are transitively bound to C4 approval. C8 therefore removes C3 permission, C4 approval, C5 preflight, C6 authorization, and the C7 runtime `execute` path from its future authorization shape. The real C4→C5→C6 workflow remains unchanged and mandatory for real-case narration.

Future C8 now requires `test_classification: isolated_synthetic_provider_connectivity_test`, forbids real-case content and script-approval artifacts, and asserts that C3 remains `AWAITING_SCRIPT_APPROVAL`. It retains the exact invented-text hash, locked Mia-profile hash, C7 request-contract and allowlist hashes, contained output binding, `mp3_44100_128`, and all single-request/no-retry/no-redirect/no-fallback restrictions.

Run the offline C8b suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_c8b_contract_alignment.py
```

C8b passed 12/12. C8a and C1–C7 regressions passed 117/117, for 129/129 total checks. No valid C8 authorization exists, and a fresh separate one-time human authorization remains required before any live synthetic connectivity request.

## Phase C8c: offline isolated execution-adapter boundary

C8c adds `automation/providers/c8_isolated_provider_execution_adapter.py`. It is separate from the C7 runtime adapter and imports no C4, C5, C6, or C7 runtime behavior. It uses only the isolated C8 schema, the non-executable C8a validator, and canonical hashes of the static C7 provider-request contract object and allowlist embedded in the future C8 contract.

The contract now pins the exact invented fixture-text hash and locked Mia-profile file hash. The adapter accepts no self-selected text/profile, default client, or live capability. Its exact test-only client returns deterministic zero-audio metadata in memory and writes nothing.

Run the offline C8c suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_c8_isolated_provider_execution_adapter.py
```

C8c passed 16/16. C8b through C1 regressions passed 129/129, for 145/145 total checks. No authorization artifact or executable route exists; any live C8 connectivity request still requires a new separate one-time authorization.

## Phase C8d: offline live-readiness contract

C8d resolves the remaining path and dependency-injection ambiguity without creating a live client. The authorization path is now explicitly relative to `automation/`, while the one canonical filesystem output is documented relative to the workspace root under `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output/`.

`automation/c8d_live_readiness_contract.py` defines only two future protocols: one injected, in-process, single-request transport and one injected opaque provider-capability source. Neither has a default instance or implementation. Capability declarations prohibit subprocesses, browser/MCP/Node use, retry, redirects, fallback, discovery, batch/multi-output, generic requests, raw secret/configuration exposure, serialization, and credential mutation.

Run the offline C8d suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_c8d_live_readiness_contract.py
```

C8d passed 12/12. C8c through C1 regressions passed 145/145, for 157/157 total checks. A fresh separate C8 authorization is still required and must explicitly permit only one injected in-process HTTP call plus opaque capability use, with no subprocess and no retry.

## Phase C8e: offline one-runner boundary

C8e corrects the process boundary: a future C8 authorization may launch exactly one local Python process named `c8_one_time_isolated_provider_runner`. That top-level launch is distinct from child execution—the runner is contractually unable to spawn subprocesses, shells, PowerShell/cmd, Node, browsers, MCP, Codex, or external commands.

The future runner may validate and consume one authorization, request one opaque capability, make one in-process HTTP request, write one authorized MP3 plus one safe audit record, and stop. Retry, redirect, fallback, discovery, polling, status/follow-up, cleanup/deletion, batch, multi-output, reuse, scheduling, default/global registration, and production enablement remain disabled.

Opaque configuration is limited to the abstract ordered slots `provider_api_credential` and `locked_voice_identifier`. These are not environment-variable or config-file names, and no real lookup or capability source exists in C8e.

Run the offline C8e suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_c8e_runner_boundary_contract.py
```

C8e passed 12/12. C8d through C1 regressions passed 157/157, for 169/169 total checks. A fresh C8 authorization remains required for one runner launch, one opaque handoff, and one in-process HTTP request.

## Phase C8f: offline one-time configuration plan

C8f defines—but does not activate—two mutually exclusive future configuration mechanisms for the isolated C8 runner. A later live authorization must select either process-only injection through the exact placeholder names `COLD_TRUTH_C8_PROVIDER_API_CREDENTIAL` and `COLD_TRUTH_C8_LOCKED_VOICE_IDENTIFIER`, or the dedicated ignored JSON file `automation/private/c8_one_time_provider_config.json` with exactly the conceptual fields `provider_api_credential` and `locked_voice_identifier`.

The C8f contract performs no environment access, config-file access, directory scan, discovery, network request, provider call, authorization creation, or audio generation. It rejects missing/both mechanisms, partial or reordered slots, unknown fields, wildcard/generic lookups, alternate names or paths, fallback, traversal, and raw-value print/log/serialization/hash/return/report/audit behavior. The future source remains unavailable without a separate valid C8 authorization.

Run the offline C8f suite:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' -B automation\test_c8f_configuration_plan_contract.py
```

## Phase C8g: selected Option A setup guide

Brody selected temporary process-environment injection for a future, separately authorized one-time C8 connectivity test. The human-only setup instructions are in `automation/C8_OPTION_A_TEMPORARY_ENVIRONMENT_SETUP.md`. C8g does not set or inspect environment values, activate a configuration source, create an authorization artifact, implement or launch a runner, contact a provider, or create audio. A new explicit live C8 authorization remains mandatory before either placeholder is replaced locally or any attempt begins.

## Phase C8h: existing ElevenLabs MCP route

C8h supersedes the direct HTTP and manual configuration plan. Option A and Option B are inactive historical documentation. The only active future C8 transport is `existing_configured_elevenlabs_mcp`, limited to one narration operation, one provider request, no retry or follow-up, and no credential/configuration/environment/voice-ID/account inspection. C8h is offline-only; it creates no authorization instance and invokes no MCP tool. A fresh explicit one-time live C8 authorization remains required.

## Phase C8i: MCP directory-output reconciliation

C8i keeps the C8 external boundary at exactly one configured ElevenLabs MCP narration operation while defining one future, authorization-bound staging directory and at most one deterministic local atomic rename to the canonical C8 MP3 path. The staging directory must contain exactly one newly created direct regular MP3; zero, multiple, nested, linked, non-MP3, or unexpected entries fail closed. Destination existence or rename failure also stops without retry, copy, overwrite, cleanup, deletion, or a second MCP operation.

The C8i module is declarative and non-executing. It does not create an authorization artifact, staging directory, audio, runner, provider call, or generic filesystem-operation API. A fresh separate one-time C8 live authorization remains required.

Future C8 authorization wording must use only `maximum_local_rename_count: 1`. The noncanonical longer field is rejected because the authorization schema retains `additionalProperties: false`.

## Phase C8m: MCP result-shape finalization

C8o retires the ElevenLabs MCP route for future C8 narration-connectivity tests and defines the offline-only `direct_elevenlabs_https_api` adapter contract. It accepts only injected opaque credential/voice values, one injected POST transport call, one bounded MP3-byte response, one injected exclusive-create write to the canonical destination, and one closed non-sensitive audit result. It has no default HTTP client, environment/configuration lookup, MCP integration, SDK, subprocess, retry, redirect, fallback, polling, cleanup, overwrite, copy, batch, multi-output, or production route. C8n remains historical evidence for the fail-closed MCP result-shape boundary.

No-output, multiple, mixed, remote/download, metadata-only, non-audio, non-MP3, linked, nested, outside-boundary, pre-existing, or failed-finalization results block without retry, another MCP operation, another finalization action, copy, overwrite, cleanup, deletion, polling, status, follow-up, temporary media, or audio processing. C8m contains no executable provider or finalizer and requires fresh human review before any future live authorization.

## Quarantined legacy stage helper

`automation/cold_truth_pipeline.py` is no longer a canonical pipeline or state owner. The certified `automation/orchestrator.py` exclusively owns run state, approvals, invalidation, status, and the append-only event ledger.

The legacy module retains pure planning/preflight helpers and may write only non-authoritative synthetic handoffs beneath an explicit isolated fixture root outside this workspace. It rejects canonical vault roots, missing fixture flags, every `--execute` request, Pexels execution, ElevenLabs execution, and inputs outside the isolated root.

Fixture-only example:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation/cold_truth_pipeline.py write --case "Synthetic Fixture" --source "synthetic" --fixture-only --isolated-run-root "$env:TEMP\cold-truth-legacy-fixture"
```

Its isolated `legacy_fixture_manifest.json` declares `authoritative: false` and `canonical_state_owner: automation/orchestrator.py`. It must never be copied into an episode Automation directory or used to advance canonical state. Provider execution, narration generation, downloads, upload, and publishing are unavailable through this legacy route.

The current orchestrator safely implements state, selection, approval, invalidation, runtime, track-isolation, and dry-run behavior. Real agent-runtime, WhisperX, asset-download/license, assembly, and render adapters must be configured before `--local-production` can succeed; the orchestrator stops instead of improvising when an adapter is absent.

Set secrets only in the process environment: `OBSIDIAN_API_URL`, `OBSIDIAN_API_KEY`, `PEXELS_API_KEY`, `ELEVENLABS_API_KEY`, and optionally `ELEVENLABS_VOICE_ID`. Do not place secrets in the vault.
