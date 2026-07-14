# Cold Truth — L7A Synthetic-Test vs Real-Narration Eligibility Alignment

## Outcome

`PASSED — OFFLINE CONTRACT REPAIR AND REGRESSION VALIDATION COMPLETE`

L7A now distinguishes a future fixed-text, non-case local-Piper connectivity test from any real-case or production narration request. This phase created no executable authorization and did not authorize or perform L8.

## Files changed or created

Changed:

- `automation/l7_piper_synthetic_authorization_contract.py`
- `automation/test_l7_piper_synthetic_authorization_contract.py`
- `automation/fixtures/l7_piper_synthetic_authorization_valid.json`
- `automation/fixtures/l7_piper_synthetic_authorization_invalid_prerequisite.json`

Created:

- `automation/PHASE_L7A_SYNTHETIC_VS_REAL_ELIGIBILITY_ALIGNMENT_REPORT.md`

No L1-L6, C1-C8o, runtime, provider, production, historical-record, or other file was changed.

## Exact synthetic-only eligibility rule

The L7A fixture schema is `cold_truth.l7a.piper_fake_authorization_fixture.v1` and permits exactly:

```text
authorization_purpose: synthetic_local_connectivity_test
synthetic_test_only: true
non_case_text_only: true
no_personal_data: true
```

Eligibility additionally requires the previously locked Piper 1.4.2 route, `en_US-ljspeech-high` model and hashes, `CPUExecutionProvider`, WAV output, maximum 160 declared characters, SHA-256 only with no durable raw text, one process, one attempt, one voice, one exclusive-created output, zero retries, and zero fallbacks. The validator remains fake-fixture-only and can return only a non-executing authorization result.

The newly declared future test-only root is:

```text
C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests
```

L7A did not create, inspect, or write that directory. The fixture declares the future target directory and output as absent, new, empty, contained, non-link, non-reparse, and exclusive-create-only.

The synthetic fixture contains no C3 or C4 field. It does not inspect or evaluate C3/C4 state or records. Any attached C3/C4 path, hash, approval, approved-script linkage, or production-case reference fails closed.

Real-case, research, script, channel, victim, suspect, personal, biographical, production, or narratively meaningful content fails closed. Production-pipeline advancement, rendering, upload, scheduling, and publishing capabilities are explicitly prohibited alongside the existing queueing, batching, chunking, multi-speaker, cloning, effects, server, network, MCP, cloud, copy, rename, overwrite, cleanup, and deletion prohibitions.

## Permanent real-narration rejection rule

Every `authorization_purpose` other than exactly `synthetic_local_connectivity_test` is rejected by L7A. This synthetic contract cannot be reused for real narration and does not implement a real-narration authorization schema.

The permanent guard is:

```text
outside_l7a_requires_c3_approved_script_state_and_c4_approval_chain
```

C3/C4 are deliberately not evaluated for a synthetic connectivity test. They remain mandatory for any future real-case narration contract, which is outside L7/L7A scope.

## Validation results

- L7 focused suite: **17/17 passed**
- L2 focused suite: **16/16 passed**
- K1 focused suite: **14/14 passed**
- C1: **19/19 passed**
- C2: **13/13 passed**
- C3: **6/6 passed**
- C4: **18/18 passed**
- C5: **16/16 passed**
- C6: **18/18 passed**
- C7: **19/19 passed**
- C8a: **16/16 passed**
- C8b: **12/12 passed**
- C8c: **16/16 passed**
- C8d: **12/12 passed**
- C8e: **12/12 passed**
- C8f/C8g: **18/18 passed**
- C8h: **16/16 passed**
- C8i/C8j: **17/17 passed**
- C8m: **18/18 passed**
- C8n: **9/9 passed**
- C8o: **11/11 passed**

C1-C8o combined: **266/266 passed**. Total validation executed in L7A: **313/313 passed**.

L6 was not run because it launches the sealed Piper runtime/model-load boundary prohibited by this phase. Its prior 12/12 result remains historical evidence only. L2 and L6 were not modified and remain unreachable from L7A.

## Activity attestations

- Piper or ONNX import/runtime activity: 0
- Runtime processes or L6 invocations: 0
- Model or config loads: 0
- Text, phoneme, tensor, or model inputs: 0
- Inference or synthesis calls: 0
- Audio, media, WAV, MP3, PCM, waveform, or spectrogram artifacts: 0
- Test-output directories or files created: 0
- Network, provider, API, MCP, browser, or download activity: 0
- Credential, secret, environment-variable, provider-configuration, or account access: 0
- Authorization instances created, validated, consumed, or modified: 0
- Historical authorization/audit record access: 0
- Rendering, upload, scheduling, publishing, or production activity: 0

C3 remains exactly `AWAITING_SCRIPT_APPROVAL`. No C4 approval was created or consumed. Publishing and real production remain disabled.

## Remaining blocker

Human review is required. L8 remains blocked until a new, separate, explicit human authorization permits one bounded synthetic local WAV attempt.
