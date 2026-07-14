# Cold Truth — H7 Canonical Artifact Identity Certification Report

## Result

`H7 REGRESSION-CERTIFIED — 73/73 PASSED`

H7 binds every synthetic agent attempt to immutable canonical input identities and exact expected output paths. Inputs and outputs are verified by canonical absolute path, SHA-256, and byte size; attempts, declarations, and output names fail closed against substitution or ambiguity.

## Certified behavior

- Every attempt envelope carries the exact positive attempt number, canonical attempt output root, and complete expected-output path set from its versioned contract.
- File inputs use canonical absolute paths plus exact SHA-256 and byte size; value inputs use deterministic canonical JSON hashes.
- Input descriptors are revalidated after provider return and before handoff acceptance, detecting in-attempt mutation.
- A handoff must match the exact attempt identity and echo the exact request input descriptors.
- Output names must be unique, declared by the contract, complete, and mapped to their exact expected canonical paths.
- Path escapes, noncanonical paths, undeclared outputs, duplicate names, missing files, media outputs, hash mismatches, and size mismatches fail closed.
- Cached handoffs are revalidated against the reconstructed exact attempt envelope before reuse.
- Attempt records preserve the exact verified inputs and expected outputs used for audit.

## Minimal repair history

The initial H7 focused invocation stopped before test execution because a helper named `run` shadowed `unittest.TestCase.run`. That incomplete result was reported without repair or retry. Under a new explicit continuation task, the helper alone was renamed to `run_agent` and its internal call sites were updated. No implementation behavior changed during the repair.

## Exact certification invocations and results

All commands below ran once from `C:\Youtube Automation Obsidian\automation` using the bundled offline Python runtime, in the order shown.

1. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_canonical_artifact_identity.py`
   - Exit code: `0`
   - Result: `8/8` passed
2. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_episode_identity.py`
   - Exit code: `0`
   - Result: `8/8` passed
3. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_legacy_pipeline_quarantine.py`
   - Exit code: `0`
   - Result: `10/10` passed
4. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_status_view.py`
   - Exit code: `0`
   - Result: `7/7` passed
5. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_artifact_invalidation.py`
   - Exit code: `0`
   - Result: `7/7` passed
6. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_audit_event_chain.py`
   - Exit code: `0`
   - Result: `6/6` passed
7. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_human_approval_lifecycle.py`
   - Exit code: `0`
   - Result: `12/12` passed
8. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_orchestrator.py`
   - Exit code: `0`
   - Result: `6/6` passed
9. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_agent_runtime_orchestration.py`
   - Exit code: `0`
   - Result: `9/9` passed

Combined certification result: `73/73` passed.

No certification suite failed, no nonzero exit occurred, and no retry, fallback, alternate harness, or second certification invocation was used. No L7/L8 or provider suite ran.

## Certified implementation hashes

- `automation/handoff_validator.py`: `A33B5AEC8DE8BE382E9715AD82018CFB48637397CDCCE4820E96315E4C06233A`
- `automation/agent_runner.py`: `73668725EFE8FB2CFAD28222A2429C02EFAA007160DE9C3699AD7F29DF5B1A36`
- `automation/fixtures/simulated_agents/mock_runtime.py`: `D32FA40F09F54EB454FBD6A3EBBCCDE4AF8D7E7A04589A57E20CF413D89CC89F`
- `automation/test_canonical_artifact_identity.py`: `F22F64DCC9D16BF34AE3EDA759C1C98AD82B27BA00DB17195A26185CE1761BAA`

## Files changed across H7 and its repair

- `automation/handoff_validator.py`
- `automation/agent_runner.py`
- `automation/fixtures/simulated_agents/mock_runtime.py`
- `automation/test_canonical_artifact_identity.py`
- `automation/PHASE_H7_CANONICAL_ARTIFACT_IDENTITY_REPORT.md`

No H1–H6 report, L7/L8 implementation, provider adapter, runtime asset, dependency, configuration, real-case material, account, media, or production file was changed.

## Safety confirmation

All certification tests used synthetic fixtures and temporary roots that were cleaned afterward. No real case entered the orchestration path. No provider/network call, external command, account action, environment-secret access, or production mutation occurred.

No L7/L8 authorization was created, validated, inspected, persisted, consumed, reset, or executed. No Piper/ONNX import, sealed interpreter, model load, text handoff to a model, inference, synthesis, audio/media creation, C3/C4 access, rendering, upload, scheduling, publishing, or production change occurred.

C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed. L8 remains blocked. Real production and publishing remain disabled.

## Stop

`H7 REGRESSION-CERTIFIED — CANONICAL ARTIFACT IDENTITY IS BOUND PER ATTEMPT`

This certification authorizes no subsequent hardening slice, adapter action, L8 action, media generation, or production action.
