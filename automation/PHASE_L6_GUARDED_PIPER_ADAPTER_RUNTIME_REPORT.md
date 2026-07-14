# Cold Truth — L6 Guarded Piper Adapter/Runtime Report

Date: 2026-07-13  
Phase: L6 — guarded real-runtime identity and health wiring only  
Outcome: **READY FOR L7 PRE-SYNTHESIS AUTHORIZATION-CONTRACT REVIEW**

## Scope completed

L6 adds a separate guarded integration surface that binds the immutable L2 route/version/model declarations to the exact sealed Piper runtime identity without attaching L2's fake transport or fake writer and without exposing any synthesis-capable or output-capable public method.

Exactly one sealed Piper health/runtime process was launched:

`C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe -B test_l6_guarded_piper_adapter_integration.py`

That single process initialized the exact CPU session once, inspected safe session metadata, exercised guarded rejection categories, released only in-process session references at process exit, and exited with code 0. There was no second sealed-runtime process and no retry.

The separately required L2, K1, and C1–C8o offline validation processes ran only after L6 passed. They did not import, attach to, or invoke the sealed Piper runtime.

## Files created

1. `automation/providers/l6_guarded_piper_runtime.py`
2. `automation/test_l6_guarded_piper_adapter_integration.py`
3. `automation/PHASE_L6_GUARDED_PIPER_ADAPTER_RUNTIME_REPORT.md`

No existing L1–L5, L2 fake transport/writer, K1–K2a, C1–C8o, provider-registry, production, configuration, authorization, audit, historical-record, media, or approval-state file was changed.

The guarded wrapper's own deterministic ledger provides the required spy function, so no separate duplicate spy module was necessary.

## Locked runtime identity

| Field | Required and observed value | Result |
|---|---|---|
| Sealed interpreter | `C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe` | Pass |
| Piper version | `1.4.2` | Pass |
| ONNX Runtime version | `1.27.0` | Pass |
| Model ID | `en_US-ljspeech-high` | Pass |
| Model path | `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx` | Pass |
| Config path | `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx.json` | Pass |
| Provider declaration | `CPUExecutionProvider` | Pass |
| Active session providers | `CPUExecutionProvider` only | Pass |

The wrapper rejects every other declared interpreter, engine version, model ID, model/config path, hash, or provider before a session load is possible.

## Locked file and structural verification

| Artifact | Locked and observed SHA-256 | Safety result |
|---|---|---|
| `en_US-ljspeech-high.onnx` | `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a` | Regular file, non-link, non-reparse, contained, exact hash |
| `en_US-ljspeech-high.onnx.json` | `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14` | Regular file, non-link, non-reparse, contained, exact hash |

The config JSON passed the same bounded identity and structure requirements used in L5: LJSpeech, `en_US`, 22,050 Hz metadata, `high` configuration quality, one speaker, and the required typed configuration sections.

Asset inventory before and after session initialization remained exactly:

1. `en_US-ljspeech-high.onnx`
2. `en_US-ljspeech-high.onnx.json`

No output or unexpected artifact appeared.

## Guarded wrapper surface

The wrapper accepts only the exact locked interpreter/runtime declaration, Piper version, model ID, model/config paths, hashes, and CPU provider. Its public safe operations are limited to:

- construct exact locked identity;
- initialize and inspect the single CPU session;
- return frozen safe identity metadata;
- return frozen safe session metadata;
- reject a fixed operation category without accepting a payload;
- return a frozen safe ledger snapshot;
- report process initialization count.

No public method accepts or exposes:

- text, phonemes, IDs, tokens, scales, input lengths, or tensors;
- voice/model overrides;
- arbitrary ONNX input;
- output paths or output formats for execution;
- writers or byte buffers;
- Piper synthesis/stream/phonemization methods;
- ONNX `run` or `run_with_iobinding`;
- CLI, subprocess, server, queue, retry, fallback, polling, background-task, copy, rename, overwrite, or artifact-cleanup behavior.

The private process-exit reference release does not delete, move, rewrite, or clean up any artifact and is not available to an adapter request.

## L2 binding validator

The L6 binding validator accepts only an exact `GuardedPiperRuntime` instance and a frozen no-text binding probe containing:

- L6's fixed fake binding-probe kind and marker;
- L2 route `local_piper_1_4_2_en_us_ljspeech_high`;
- engine version `1.4.2`;
- model ID `en_US-ljspeech-high`;
- fixed model-source marker;
- future output declaration `wav`.

It contains no text field, output path, writer, media buffer, or execution request. The exact probe binds successfully and reports `output_handling_available: false`.

Wrong route, version, model, source marker, or future format is rejected before guarded-runtime interaction. A non-fake request kind is also rejected before runtime interaction. Passing an output path or writer is a type error because neither is part of the interface.

L2 remains fake-only and unchanged. L6 does not attach to L2's transport, writer, workspace, request execution, or result path.

## Runtime/session metadata

Session load: **passed**  
Available provider metadata: `AzureExecutionProvider`, `CPUExecutionProvider`  
Active provider: **`CPUExecutionProvider` only**

No Azure or remote operation occurred; provider availability was metadata only.

Safe input declarations:

| Name | Shape | Type |
|---|---|---|
| `input` | `['batch_size', 'phonemes']` | `tensor(int64)` |
| `input_lengths` | `['batch_size']` | `tensor(int64)` |
| `scales` | `[3]` | `tensor(float)` |

Safe output declaration:

| Name | Shape | Type |
|---|---|---|
| `output` | `['batch_size', 1, 1, 'Unsqueezeoutput_dim_3']` | `tensor(float)` |

These declarations were read from session metadata only. No tensor was constructed, populated, bound, or executed.

## Deterministic guarded-runtime ledger

Primary live-runtime ledger totals after focused validation:

| Counter | Total |
|---|---:|
| Runtime initializations | 1 |
| Text inputs accepted | 0 |
| Inference calls | 0 |
| Synthesis calls | 0 |
| Phonemization calls | 0 |
| Output writes | 0 |
| Fixed blocked operation categories exercised | 31 |

The 31 primary-ledger blocks cover text, phoneme, tensor, scales, input-length, voice override, ONNX execution, profiling, warm-up, benchmark, synthesis, stream, phonemization, output, CLI, subprocess, server, queue, retry, fallback, auto-chunking, polling, background task, cleanup request, copy, rename, overwrite, second initialization, and real-writer attachment categories.

One additional newly constructed wrapper was used only to prove the process-wide second-initialization latch. Its initialization was blocked before file or session work and its isolated ledger recorded one `second_runtime_initialization` block. The process-wide successful initialization count remained exactly 1. This isolated guard event is intentionally not added to the primary live-runtime ledger's 31-category total.

No ledger stores text, payloads, tensors, errors, secrets, credentials, arbitrary paths, or model input.

## Focused L6 validation

Result: **12/12 passed**

The suite proved:

1. Exact real-runtime CPU health and metadata-only session initialization.
2. Exact L2 route/version/model binding with no output handling.
3. Wrong version, voice/model, path, hash, or provider rejection before session load.
4. Wrong L2 probe values and non-fake paths reject before runtime interaction.
5. No text, output-path, or writer interface exists.
6. All 31 inference/output/orchestration categories are blocked.
7. A second runtime initialization is blocked process-wide.
8. No public inference, synthesis, or output method exists.
9. No production pipeline or provider-registry import exists.
10. Ledger counters remain zero for inputs, inference, synthesis, phonemization, and writes.
11. Asset inventory contains no media or unexpected output.

Bytecode output was disabled with `-B`, so the focused run created no incidental `__pycache__` artifact.

## Regression validation

### L2

Result: **16/16 passed**

### K1

Result: **14/14 passed**

### C1–C8o

| Suite | Result |
|---|---:|
| C1 | 19/19 passed |
| C2 | 13/13 passed |
| C3 | 6/6 passed |
| C4 | 18/18 passed |
| C5 | 16/16 passed |
| C6 | 18/18 passed |
| C7 | 19/19 passed |
| C8a | 16/16 passed |
| C8b | 12/12 passed |
| C8c | 16/16 passed |
| C8d | 12/12 passed |
| C8e | 12/12 passed |
| C8f/C8g | 18/18 passed |
| C8h | 16/16 passed |
| C8i/C8j | 17/17 passed |
| C8m | 18/18 passed |
| C8n | 9/9 passed |
| C8o | 11/11 passed |

C1–C8o: **266/266 passed**  
L2 + K1 + C1–C8o: **296/296 passed**  
L6 + L2 + K1 + C1–C8o: **308/308 passed**

All validation processes used `-B` to avoid incidental bytecode files. No regression connected to the sealed L6 runtime.

## Activity and state confirmation

- Sealed Piper runtime processes: exactly 1
- Successful session initializations: exactly 1
- Runtime retry, fallback, second session, subprocess, CLI, server, or background task: none
- Text, phoneme, ID, token, scale, input-length, tensor, or model input supplied: none
- Piper synthesis, streaming, phonemization, demo, example, benchmark, or test-generation call: none
- ONNX `run`, `run_with_iobinding`, profiling, warm-up, benchmark, or equivalent execution: none
- WAV, MP3, PCM, audio buffer, waveform, spectrogram, temporary media, fixture output, or other media/output artifact: none
- Network, download, provider, MCP, browser, cloud, API, ElevenLabs, Voicebox, or Kokoro activity: none
- Credential, API-key, token, environment-variable, browser/account, secret, or provider-configuration access: none
- Authorization or historical audit access, creation, validation, consumption, or mutation: none
- L2 fake transport/writer alteration or attachment: none
- Provider registry or production narration integration: none
- Codebase Memory indexing/watch activity: none
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: none
- Publishing and real-production modes remain disabled

## Remaining blocker and proposed L7

The remaining blocker is human review of L6.

A future, separately authorized L7 may define a pre-synthesis authorization contract only. It may specify immutable approval fields, one-time scope, exact model/runtime/output declarations, exclusive destination preconditions, no-retry rules, safe audit fields, and fail-closed consumption semantics.

L7 must still not submit text to Piper, call phonemization or inference, invoke ONNX execution, create audio/media/output, attach to production, or publish.

STOP FOR HUMAN REVIEW.
