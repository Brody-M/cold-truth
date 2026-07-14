# Cold Truth — H9 Bounded Attempt and Fixed Provider Certification Report

## Result

`H9 REGRESSION-CERTIFIED — 95/95 PASSED`

H9 binds an explicit attempt budget and one fixed provider identity into every agent request and its idempotency key. Retries can occur only inside that budget, only after a provider-declared retryable failure, and never through fallback or provider substitution.

## Certified behavior

- `max_retries` must be an integer from `0` through `2`, establishing one to three total attempts.
- Invalid, negative, boolean, fractional, or unbounded retry values fail before request creation or provider invocation.
- The exact `max_attempts`, `max_retries`, fixed provider ID, retry rule, and no-fallback rule are part of the idempotency identity.
- Changing the attempt budget creates a different idempotency key rather than silently widening an existing request.
- Every request explicitly declares `provider_fallback: false` and `retry_requires_provider_retryable: true`.
- Every attempt and completion record preserves the exact fixed provider and attempt policy.
- A retryable failure with no remaining budget stops permanently.
- A nonretryable failure stops after its first attempt even when unused budget remains.
- A retryable failure may consume only the exact remaining authorized attempts and uses the same provider throughout.
- Runtime-result, handoff, and handoff-runtime provider identities must all equal the fixed request provider.
- Provider substitution at any of those boundaries fails closed and cannot trigger fallback.
- The common handoff schema now requires a nonempty `provider_id`.

## Minimal repair history

The first H9 regression chain stopped in H7 because one manually constructed request fixture predated the new required provider and attempt-policy fields. The stop was reported without repair or retry. Under a new explicit continuation task, only that fixture was updated with the fixed synthetic provider and a one-attempt/no-fallback policy; no H9 implementation behavior changed during repair.

## Exact certification invocations and results

All commands below ran once from `C:\Youtube Automation Obsidian\automation` using the bundled offline Python runtime, in the order shown.

1. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_attempt_provider_policy.py`
   - Exit code: `0`
   - Result: `10/10` passed
2. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_track_isolation.py`
   - Exit code: `0`
   - Result: `12/12` passed
3. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_canonical_artifact_identity.py`
   - Exit code: `0`
   - Result: `8/8` passed
4. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_episode_identity.py`
   - Exit code: `0`
   - Result: `8/8` passed
5. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_legacy_pipeline_quarantine.py`
   - Exit code: `0`
   - Result: `10/10` passed
6. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_status_view.py`
   - Exit code: `0`
   - Result: `7/7` passed
7. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_artifact_invalidation.py`
   - Exit code: `0`
   - Result: `7/7` passed
8. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_audit_event_chain.py`
   - Exit code: `0`
   - Result: `6/6` passed
9. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_human_approval_lifecycle.py`
   - Exit code: `0`
   - Result: `12/12` passed
10. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_orchestrator.py`
    - Exit code: `0`
    - Result: `6/6` passed
11. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_agent_runtime_orchestration.py`
    - Exit code: `0`
    - Result: `9/9` passed

Combined certification result: `95/95` passed.

No certification suite failed, no nonzero exit occurred, and no retry, fallback, alternate harness, or second certification invocation was used. The synthetic retry tests exercised only their declared in-memory failure fixtures. No L7/L8 or real-provider suite ran.

## Certified implementation hashes

- `automation/handoff_validator.py`: `3E218EB515331480B5632E6691316872EEC13B0320D6B1C622560B121C5D79F3`
- `automation/agent_runner.py`: `3FFCB964A96049B350C17C8D1B9705D342F7798CF48BA4165EF9AA27A6AD6779`
- `automation/fixtures/simulated_agents/mock_runtime.py`: `EEE882E1DE255C8D8FB0DB0EA0E597B8D4F29382A76991EFDF53D0902A3DF35A`
- `automation/contracts/common_handoff.schema.json`: `0868B36D1D954BF442BD538C44A5DAA0E88903930565225779B293529C8F1232`
- `automation/test_attempt_provider_policy.py`: `5A92F4D9A66F2076FC145D90BC77B64C3CC464B91CCBB70B30F3163B702F6A16`
- `automation/test_canonical_artifact_identity.py`: `3248798294AE1656E4B68C8408FA42060FA112E1D00D39A0FE4E374B8E512E82`

## Files changed across H9 and its repair

- `automation/handoff_validator.py`
- `automation/agent_runner.py`
- `automation/fixtures/simulated_agents/mock_runtime.py`
- `automation/contracts/common_handoff.schema.json`
- `automation/test_attempt_provider_policy.py`
- `automation/test_canonical_artifact_identity.py`
- `automation/PHASE_H9_BOUNDED_ATTEMPT_PROVIDER_POLICY_REPORT.md`

No H1–H8 report, L7/L8 implementation, real provider adapter, runtime asset, dependency, configuration, real-case material, account, media, or production file was changed.

## Safety confirmation

All tests used synthetic fixtures and temporary roots that were cleaned afterward. The fixed provider was the deterministic in-process synthetic fixture only. No actual provider was contacted and no fallback was attempted.

No L7/L8 authorization was created, validated, inspected, persisted, consumed, reset, or executed. No network activity, Piper/ONNX import, sealed interpreter, model load, model input, inference, synthesis, media access or creation, secret access, C3/C4 access, rendering, upload, scheduling, publishing, account action, or production change occurred.

C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed. L8 remains blocked. Real production and publishing remain disabled.

## Stop

`H9 REGRESSION-CERTIFIED — ATTEMPTS ARE BOUNDED AND PROVIDER FALLBACK IS PROHIBITED`

This certification authorizes no subsequent stage, adapter action, provider connection, L8 action, media generation, or production action.
