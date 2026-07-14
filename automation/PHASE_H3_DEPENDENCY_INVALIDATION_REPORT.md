# Cold Truth — H3 Dependency-Driven Invalidation Certification Report

## Result

`H3 REGRESSION-CERTIFIED — 40/40 PASSED`

H3 replaces the script-only downstream list with one versioned canonical artifact-dependency graph. A changed upstream hash now invalidates every active transitive descendant, revokes each affected approval, preserves superseded files and records for audit, records the exact restart checkpoint, and stops in `INVALIDATED_UPSTREAM_CHANGE` unless the existing paired-script revision route explicitly returns to its human gate.

## Certified behavior

- Research-ledger or verification changes invalidate viability-dependent editorial work and every affected downstream artifact.
- Script/draft/outline/final changes invalidate narration, preflight, alignment, both visual branches, assembly, render planning, and packaging; both script and assembly approvals are revoked.
- Narration changes preserve the paired script approval while invalidating preflight and everything downstream, including assembly approval.
- Alignment changes preserve narration and preflight while invalidating visuals, track isolation, assemblies, and assembly approval.
- Long-form visual changes invalidate dependent Shorts planning/assets, track isolation, both assemblies, render planning, and assembly approval.
- Revision roots are allowlisted and written beneath the isolated artifact revision directory.
- Identical hashes are rejected before a revision file or invalidation record is created.
- Superseded source and descendant files remain on disk; their exact records move to `stale_artifact_records` with old/new hashes, cause, timestamp, and dependency-graph version.
- Active registry entries for invalidated descendants are removed.
- Every invalidation is recorded through the H2 append-only event chain.

Canonical graph version: `cold_truth.artifact_dependencies.v1`.

## Exact validation invocations and results

All commands ran once from `C:\Youtube Automation Obsidian\automation` using the bundled offline Python runtime.

1. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B test_artifact_invalidation.py`
   - Exit code: `0`
   - Result: `7/7` passed
2. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B test_audit_event_chain.py`
   - Exit code: `0`
   - Result: `6/6` passed
3. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B test_human_approval_lifecycle.py`
   - Exit code: `0`
   - Result: `12/12` passed
4. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B test_orchestrator.py`
   - Exit code: `0`
   - Result: `6/6` passed
5. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B test_agent_runtime_orchestration.py`
   - Exit code: `0`
   - Result: `9/9` passed

Combined result: `40/40` passed.

No suite failed, no nonzero exit occurred, and no retry, fallback, alternate harness, or second invocation was used.

## Certified implementation hashes

- `automation/artifact_invalidation.py`: `A246DA77E887127ECF2A498EA96DC35085733D7F9DFF5BC4C0FB561514B1B1A7`
- `automation/orchestrator.py`: `6166830E76D82A7B7B4DB7A5E17C3398EBFC0A33CF1933E315548BD06725334F`
- `automation/test_artifact_invalidation.py`: `DEDD0C35D6FC01327946A7F6BE51B4C8D81B194C709E4E45861AED348FE4874E`

Unchanged regression inputs:

- `automation/audit_event_chain.py`: `2E5FC10F5C38CB900A4E092AF8F83338CB47AAE1D8A1A1AE62E5C5E609448D94`
- `automation/test_audit_event_chain.py`: `0AB468F772AE31511650C21646E393FD8AC4C9D4C3D82959A20C543D7C2EEA64`
- `automation/human_approval_lifecycle.py`: `2792D5986D57EA2DEFEAABC042FEA7D87A8FA52971D57A460B199928D10D1CD4`
- `automation/test_human_approval_lifecycle.py`: `E0D15803B9AE5C52105DB88463B7CD34F7F97D304AF0AC6E2184239D9C68FCD7`
- `automation/test_orchestrator.py`: `0E849CB920C5348FBB12A480820A846A0576CE4AB85F38A054C4B50300AD20DE`
- `automation/test_agent_runtime_orchestration.py`: `EBB732E1B4B7BE7CCF3979D8737BDAD94306D21147CDD61E4B409081BBB434C3`

Static scanning found no network, provider, subprocess, Piper, ONNX, production-enable, or publish-enable path in the H3 module or focused tests.

## Files changed

- `automation/artifact_invalidation.py`
- `automation/orchestrator.py`
- `automation/test_artifact_invalidation.py`
- `automation/PHASE_H3_DEPENDENCY_INVALIDATION_REPORT.md`

No standalone pipeline, approval lifecycle, event-chain module, L7/L8, provider, fixture-state, media, runtime asset, dependency, configuration, channel account, or production file changed.

## Safety confirmation

All tests used temporary synthetic run roots and cleaned them afterward. No L7/L8 authorization was created, validated, inspected, persisted, consumed, reset, or executed. No Piper/ONNX import, runtime process, model load, text handoff, inference, synthesis, audio/media, network/provider activity, credential or secret access, C3/C4 access, account action, rendering, upload, scheduling, publishing, or production change occurred.

C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed. L8 remains blocked. Real production and publishing remain disabled.

## Stop

`H3 REGRESSION-CERTIFIED — READY FOR BRODY REVIEW`

This certification authorizes no subsequent hardening slice or production action.
