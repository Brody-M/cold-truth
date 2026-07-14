# Cold Truth — L5 Piper Runtime Health Report

Date: 2026-07-13  
Phase: L5 — import and structural runtime health only  
Outcome: **READY FOR L6 GUARDED ADAPTER/RUNTIME INTEGRATION REVIEW**

## Scope completed

Exactly one sealed-runtime health-check process was launched with:

`C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe`

That process imported the installed Piper package and ONNX Runtime, verified the locked files and configuration, initialized the exact ONNX session on CPU, read only safe session metadata, released the session references, and exited successfully.

No second sealed-runtime process or retry occurred. The separately mandated L2, K1, and C1–C8o offline test processes ran only after the health process passed; none connected to or invoked the sealed Piper runtime.

## Runtime identity

| Field | Observed value | Required value | Result |
|---|---|---|---|
| Interpreter | `C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe` | Same exact sealed path | Pass |
| Python | `3.12.13` | L4 environment Python | Pass |
| Piper | `1.4.2` | `1.4.2` | Pass |
| ONNX Runtime | `1.27.0` | `1.27.0` | Pass |

Versions were read from installed package metadata after the authorized imports. No package command, CLI entry point, demo, example, test, server, or synthesis method was invoked.

## Locked asset safety and identity

Asset root:

`C:\ColdTruthLocalTools\piper-1.4.2-assets`

The asset inventory before and after the process was exactly:

1. `en_US-ljspeech-high.onnx`
2. `en_US-ljspeech-high.onnx.json`

| Artifact | SHA-256 observed | Locked SHA-256 | Result |
|---|---|---|---|
| `en_US-ljspeech-high.onnx` | `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a` | `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a` | Exact match |
| `en_US-ljspeech-high.onnx.json` | `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14` | `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14` | Exact match |

For both files, the process confirmed:

- exact locked filename;
- regular-file status;
- no link or Windows reparse-point attribute;
- resolved parent equal to the locked asset root;
- no path escape;
- no asset inventory change during the process.

No file was copied, renamed, altered, deleted, or created.

## Structural config validation

Result: **passed**

The JSON decoded as an object and contained the required typed fields for:

- dataset identity;
- audio metadata;
- eSpeak metadata;
- language metadata;
- inference configuration;
- phoneme type and maps;
- symbol and speaker counts;
- Piper model-version metadata.

The bounded identity checks confirmed:

| Field | Verified value |
|---|---|
| Dataset | `ljspeech` |
| Locale | `en_US` |
| Sample rate metadata | `22050` |
| Configuration quality | `high` |
| Speaker count | `1` |

The configuration was read only for structure and locked identity. No phoneme, identifier, token, or configuration value was supplied as model input.

## Session load and CPU health

Model/session initialization result: **passed**

`PiperVoice.load` was called only with:

- the exact locked ONNX path;
- the exact locked config path;
- CUDA disabled;
- the existing locked asset directory as the non-operative download-directory value.

No download occurred. No model execution method was called.

ONNX Runtime reported these available providers:

- `AzureExecutionProvider`
- `CPUExecutionProvider`

The initialized session used only:

- `CPUExecutionProvider`

CPU execution availability: **confirmed**. No Azure, cloud, remote, GPU, provider, API, or network operation occurred.

## Safe tensor metadata

Only `get_inputs`, `get_outputs`, `get_providers`, and provider-availability metadata were read. No tensor was constructed or supplied.

### Inputs

| Name | Shape | Type |
|---|---|---|
| `input` | `['batch_size', 'phonemes']` | `tensor(int64)` |
| `input_lengths` | `['batch_size']` | `tensor(int64)` |
| `scales` | `[3]` | `tensor(float)` |

### Outputs

| Name | Shape | Type |
|---|---|---|
| `output` | `['batch_size', 1, 1, 'Unsqueezeoutput_dim_3']` | `tensor(float)` |

These are schema/shape declarations from session metadata only. They were not populated, bound, or executed.

## Prohibited-call confirmation

- Text supplied to Piper or ONNX Runtime: **zero**
- Phonemes, IDs, tokens, scales, or tensors supplied as model input: **zero**
- Piper synthesis calls: **zero**
- Piper stream, phonemization, WAV, CLI, demo, example, test, benchmark, server, or entry-point calls: **zero**
- ONNX Runtime `run` calls: **zero**
- ONNX Runtime `run_with_iobinding`, warm-up, profiling, benchmark, or equivalent execution calls: **zero**
- Inference calls: **zero**
- Output destinations created: **zero**
- WAV, MP3, PCM, audio buffer, waveform, spectrogram, temporary media, or other media artifacts created: **zero**
- Asset inventory changes: **zero**

Session references were released and the single process exited with code 0.

## Regression validation

### L2 focused suite

Result: **16/16 passed**

L2 remains fake-only, unchanged, and disconnected from the real environment.

### K1 focused suite

Result: **14/14 passed**

Kokoro remains frozen, blocked, fake-only, and untouched.

### C1–C8o baseline

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

C1–C8o result: **266/266 passed**  
L2 + K1 + C1–C8o result: **296/296 passed**

No validation suite imported, initialized, or connected to the sealed Piper runtime.

## Files changed

Created:

- `automation/PHASE_L5_PIPER_RUNTIME_HEALTH_REPORT.md`

No other source, report, package, environment, asset, configuration, authorization, audit, production, or media file was created, changed, copied, renamed, or deleted.

## State confirmation

- Sealed-runtime health processes: exactly one
- Retry or fallback: none
- Network or download activity: none
- Provider, MCP, ElevenLabs, Voicebox, Kokoro, browser, cloud, or API activity: none
- Environment-variable, credential, API-key, token, browser/account, secret, or provider-configuration access: none
- C8/C8o/historical authorization or audit access: none
- L2/runtime connection or provider-registry change: none
- Codebase Memory index/watch activity: none
- Real-case, production-script, visual, or media access: none
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: none
- Publishing and real-production modes remain disabled

## Proposed L6 boundary

Only after separate human authorization, L6 may implement and test a guarded adapter-to-runtime integration that:

1. Preserves the exact Piper 1.4.2, model, config, path, and hash locks.
2. Uses a spy/guarded runtime seam to prove request validation, exclusive destination handling, single-call bounds, zero retry, and fail-closed behavior.
3. Prevents any real synthesis method, ONNX execution method, phonemization method, or audio writer from being reached.
4. Produces only non-audio fixture/guard evidence inside an isolated test workspace.
5. Remains disconnected from L2, the production pipeline, provider registries, approval gates, and publishing.

L6 must still prohibit real text-to-speech inference, model output, WAV/MP3/PCM creation, audio buffers, provider activity, real-case use, rendering, uploading, scheduling, and publishing.

Remaining blocker: human review of L5, followed by a separate explicit L6 authorization.

STOP FOR HUMAN REVIEW.
