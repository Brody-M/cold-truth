# Cold Truth — H8 Visual Track Isolation Certification Report

## Result

`H8 REGRESSION-CERTIFIED — 85/85 PASSED`

H8 establishes explicit, separately validated visual tracks for YouTube long-form and Shorts. The orchestrator now requires canonical synthetic asset manifests and proves zero intersection across multiple asset identities before creating any assembly artifact.

## Certified behavior

- The only accepted visual-track labels are `youtube-longform` and `shorts`.
- Long-form accepts only `case_broll` and `case_graphic` records.
- Shorts accepts only separately licensed `orbital_gameplay` records.
- Every manifest and every contained asset must carry the exact assigned track.
- Every manifest declares `shared_assets_allowed: false`, `synthetic: true`, and `media_created: false` in this offline control plane.
- Asset records require a unique asset ID, unique source identity, ready status, local record, and license record.
- Optional content hashes and canonical paths are strictly formed when present.
- Cross-track reuse is detected by asset ID, source identity, content SHA-256, or canonical path, so relabeling cannot bypass the gate.
- Duplicate identities within one track fail closed.
- The isolation report binds the exact SHA-256 of both manifests and records both track asset counts.
- A malformed manifest or any shared identity stops orchestration before `longform_assembly.json`, `shorts_assembly.json`, or checkpoint 2 can be created.
- The gate does not inspect, decode, create, source, download, or render media.

## Exact validation invocations and results

All commands ran once from `C:\Youtube Automation Obsidian\automation` using the bundled offline Python runtime, in the order shown.

1. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_track_isolation.py`
   - Exit code: `0`
   - Result: `12/12` passed
2. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_canonical_artifact_identity.py`
   - Exit code: `0`
   - Result: `8/8` passed
3. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_episode_identity.py`
   - Exit code: `0`
   - Result: `8/8` passed
4. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_legacy_pipeline_quarantine.py`
   - Exit code: `0`
   - Result: `10/10` passed
5. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_status_view.py`
   - Exit code: `0`
   - Result: `7/7` passed
6. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_artifact_invalidation.py`
   - Exit code: `0`
   - Result: `7/7` passed
7. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_audit_event_chain.py`
   - Exit code: `0`
   - Result: `6/6` passed
8. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_human_approval_lifecycle.py`
   - Exit code: `0`
   - Result: `12/12` passed
9. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_orchestrator.py`
   - Exit code: `0`
   - Result: `6/6` passed
10. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_agent_runtime_orchestration.py`
    - Exit code: `0`
    - Result: `9/9` passed

Combined result: `85/85` passed.

No suite failed, no nonzero exit occurred, and no retry, fallback, alternate harness, or second invocation was used. No L7/L8 or provider suite ran.

## Certified implementation hashes

- `automation/track_isolation.py`: `C9BF10B18406B0589CCC05B773E2132A68CE3A44974BFCFA1FC206B7C9073758`
- `automation/orchestrator.py`: `EB1DAF16B10EC8E6AE84D3BC63B19D774BC4F63632F80A2A7D4518DD4A3E33C3`
- `automation/contracts/asset_manifest.schema.json`: `0DA15F4C5462304951425EF48F56BB10E498948295A206EF663A8CD3FF4D1151`
- `automation/contracts/track_isolation.schema.json`: `225B7B4E92A44CB23B95A5E24A129BBB48BB8FC166C143541028A56505EAF9D6`
- `automation/fixtures/simulated_case/queue.json`: `8823F466CBD54D5190BB91A822253E6F6F98E6B73627115F49A290C710ADDD89`
- `automation/fixtures/simulated_agents/responses.json`: `B2C2EDA659E88F69C0E41C6C08C531314CA752CF3198F01BE643E3EDC685B45E`
- `automation/test_track_isolation.py`: `98955A209526E86B631ECB1A8AD7D111793EA3D2B5F72787E8F8CACC9B538779`

## Files changed

- `automation/track_isolation.py`
- `automation/orchestrator.py`
- `automation/contracts/asset_manifest.schema.json`
- `automation/contracts/track_isolation.schema.json`
- `automation/fixtures/simulated_case/queue.json`
- `automation/fixtures/simulated_agents/responses.json`
- `automation/test_track_isolation.py`
- `automation/PHASE_H8_VISUAL_TRACK_ISOLATION_REPORT.md`

The fixture changes add metadata records only. They do not add, access, create, or represent actual visual media. No H1–H7 report, L7/L8 implementation, provider adapter, runtime asset, dependency, configuration, real-case material, account, media, or production file was changed.

## Safety confirmation

All tests used synthetic metadata fixtures and temporary roots that were cleaned afterward. No actual long-form footage, case graphic, Orbital gameplay, audio, or video was accessed or created. No real case entered the orchestration path.

No L7/L8 authorization was created, validated, inspected, persisted, consumed, reset, or executed. No provider/network activity, Piper/ONNX import, sealed interpreter, model load, text handoff to a model, inference, synthesis, secret access, C3/C4 access, rendering, upload, scheduling, publishing, account action, or production change occurred.

C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed. L8 remains blocked. Real production and publishing remain disabled.

## Stop

`H8 REGRESSION-CERTIFIED — LONG-FORM AND SHORTS VISUAL TRACKS ARE ZERO-INTERSECTION`

This certification authorizes no subsequent hardening slice, adapter action, asset sourcing, media generation, L8 action, or production action.
