# Cold Truth Orchestration Test Report

**Test date:** 2026-07-10  
**Scope:** synthetic fixture only  
**External API calls:** 0  
**Media generated/downloaded/rendered:** none  
**Publishing actions:** none

## Command

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' automation\test_orchestrator.py
```

## Result

**6 tests passed; 0 failed.**

| Test | Result | Demonstrated behavior |
|---|---|---|
| Candidate ranking and Checkpoint 1 | Pass | Two viable synthetic candidates were ranked deterministically; the higher source-depth tie-break selected `cedar-grove-placeholder`. The run stopped at `AWAITING_SCRIPT_APPROVAL`. |
| Resume after two approvals | Pass | No post-script work occurred until hash-bound script approval existed. The run then stopped at `AWAITING_ASSEMBLY_APPROVAL` and resumed only after hash-bound assembly approval with explicit local-render authorization. Dry-run created a non-executed render plan only. |
| Rejection/backlog return | Pass | A queue with no verified viable candidates entered `RETURNED_TO_BACKLOG`; no Writer artifact was produced. |
| Script revision invalidation | Pass | A revised reviewed draft returned the run to `AWAITING_SCRIPT_APPROVAL` and marked narration, preflight, alignment, both asset branches, assemblies, and render plan stale. Assembly approval was cleared from active state. |
| Under-eight-minute gate | Pass | Synthetic duration `479.999` seconds produced `BLOCKED_RUNTIME`, `assembly_allowed: false`, and no assembly artifact. |
| No render or publish before approval | Pass | Before Checkpoint 2 approval, no render plan or render event existed. The manifest retained `publishing_enabled: false`; no publish event existed. |

## Additional validation

- Python syntax parsed successfully for `orchestrator.py`, `cold_truth_pipeline.py`, and `test_orchestrator.py`.
- All eight contract/schema JSON files and the synthetic queue fixture parsed as valid JSON.
- Long-form readiness requires every synthetic asset to be `ready`, local, and licensed.
- Shorts readiness requires every synthetic asset to be `ready`, local, and licensed plus a verified gameplay-license record.
- Track-isolation validation blocks any shared asset ID.
- The synthetic completion creates metadata/audit plans but no media.

## Deliberate remaining adapter boundary

The implementation provides queue normalization, deterministic selection, state/approval enforcement, hashing, invalidation, manifests, duration policy, asset-readiness checks, track isolation, and dry-run simulation. Real autonomous execution still requires configured adapters for the Codex agent runtime, research browsing, WhisperX, asset downloads/license capture, FCPXML assembly, and local rendering. `--local-production` stops when a required adapter is absent rather than improvising or falsely marking work complete.

Publishing is not implemented.
