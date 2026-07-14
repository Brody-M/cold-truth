# Cold Truth — L2 Piper Adapter Contract Report

Date: 2026-07-13  
Phase: L2 — offline-only fake transport and fake writer  
Outcome: **PASSED**

## Scope completed

L2 adds a provider-neutral, fake-only Piper boundary identified exactly as:

`local_piper_1_4_2_en_us_ljspeech_high`

The boundary can be constructed only with the exact L2 fake in-memory transport and exact L2 fake exclusive-create writer classes. It has no real Piper executable, Python package, ONNX Runtime, model, voice, CLI, API, local server, provider, configuration, environment, credential, network, subprocess, shell, or audio-generation route.

## Files created

1. `automation/providers/piper_local_adapter_contract.py`
2. `automation/testing/l2_fake_piper_transport.py`
3. `automation/test_l2_piper_local_adapter_contract.py`
4. `automation/PHASE_L2_PIPER_ADAPTER_CONTRACT_REPORT.md`

No existing C1–C8o, K1, K2/K2a, authorization, audit, historical-record, configuration, provider-runtime, production, or approval-gate file was modified.

## Locked contract identifiers

| Field | Exact value |
|---|---|
| Route identifier | `local_piper_1_4_2_en_us_ljspeech_high` |
| Engine version | `1.4.2` |
| Model ID | `en_US-ljspeech-high` |
| Model source/version marker | `rhasspy_piper_voices_v1_0_0_en_en_us_ljspeech_high` |
| Future output-format declaration | `wav` |
| Fake-test marker | `l2_fake_piper_transport_only` |
| Maximum fake input length | 600 characters |

The source/version marker is a test-only immutable identity field. L2 does not download, open, validate, or execute a model.

## Contract controls

- Strict frozen request, result, and safe-audit dataclasses.
- Request permits only fake-marked text, the exact locked route/version/model/source values, the future `wav` declaration, one exact relative fixture destination, the fixed input bound, and the exact fake-test marker.
- Every other Piper model or voice is rejected before transport, including all Lessac variants and other LJSpeech qualities.
- L2 writes only a `.l2fixture` file containing the exact deterministic byte sequence `L2_PIPER_NON_AUDIO_FIXTURE_BYTES_V1`; it never creates a `.wav`, `.mp3`, `.pcm`, or valid audio container.
- The fake writer accepts only an OS-temporary workspace whose directory name begins with `cold_truth_l2_` and is bound to one exact fixture filename.
- Absolute paths, traversal, nested paths, alternate suffixes, and destination changes fail before transport.
- Existing files, directories, links, reparse points, and unsafe targets fail before transport.
- The transport may return only the exact fixed L2 non-audio bytes in memory.
- The writer uses exclusive-create mode and independently rejects destination changes and traversal.
- The adapter is single-use. Fake transport and writer calls are limited to one each.
- No retry, fallback, queue, polling, background task, auto-chunking, crash recovery, reprocessing, overwrite, copy, rename, second call, or adapter cleanup behavior exists.
- Transport, malformed-result, and writer failures return safe categories only and do not expose raw exceptions.
- Failure results contain neither an output path nor a byte count. Both appear only after successful exclusive creation.
- Safe audit data is limited to route identifier, locked version, locked model ID, fake-test marker, outcome category, fake call count, and successful output byte count.
- Safe audit data contains no text, raw error, filesystem location, system detail, provider command, arbitrary argument, model path, environment/configuration field, or secret-adjacent field.
- Constructor identity checks reject subclasses, lookalikes, arbitrary callables, and any non-L2 dependency.
- Static import tests reject Piper, ONNX Runtime, Torch, subprocess, network, browser, MCP, and audio-library imports.

## L2 focused validation

Command:

`C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe test_l2_piper_local_adapter_contract.py`

Result: **16/16 passed**

The suite verifies:

- One fake call and one exclusive fixture write on success.
- Exact route, version, model, source marker, fake marker, and input bound.
- Rejection of every alternate Piper voice/model before transport.
- Empty, oversized, or non-fake text rejection before transport.
- Rejection of every output-format declaration except future `wav`.
- Existing, directory, link, reparse, unsafe, absolute, traversal, nested, and mismatched targets.
- No retry or second call after fake transport or fake writer failure.
- Fail-closed handling of malformed or unexpected transport responses.
- Single-use behavior and strict safe result/audit shapes.
- Temporary-workspace containment and the writer's independent traversal rejection.
- Absence of real-runtime imports and absence of any valid audio artifact.

## K1 focused validation

Command:

`C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe test_k1_kokoro_local_adapter_contract.py`

Result: **14/14 passed**

K1 remains fake-only and unchanged.

## C1–C8o offline regression

The established suites ran in order only after L2 and K1 passed:

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

C1–C8o regression result: **266/266 passed**  
L2 + K1 + C1–C8o result: **296/296 passed**

No suite invoked a real model, Piper runtime, provider, MCP tool, browser, network request, or audio/media generator.

## Safety and state confirmation

- Piper package, executable, ONNX Runtime, model, voice, voice repository, installer, or binary downloaded or installed: no
- Piper, ONNX Runtime, model, voice, CLI, API, local server, inference, demo, or TTS command imported or executed: no
- Virtual environment created or modified: no
- WAV, MP3, PCM, waveform, spectrogram, valid audio, or other media artifact created: no
- Test fixture bytes: fixed non-audio bytes only, written inside automatically isolated OS-temporary test workspaces and removed by normal test-framework cleanup
- External provider, MCP, API, browser automation, network request, download, or account action: no
- Credential, API key, environment variable, private configuration, browser/account data, voice ID, endpoint, token, or secret accessed: no
- Authorization created, inspected, consumed, validated, or changed: no
- Frozen Kokoro environment/cache accessed, imported, executed, repaired, modified, uninstalled, or reused: no
- Voicebox installer or download accessed: no
- ElevenLabs MCP or direct ElevenLabs route invoked: no
- C1–C8o, K1, K2/K2a, Codebase Memory configuration, historical records, approval gates, rendering, upload, scheduling, publishing, or production settings changed: no
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: none
- Publishing and real-production modes remain disabled

## Remaining blocker

The next possible phase is a separately authorized **L3 Piper package/model provenance readiness phase**. L3 may inspect and stage explicitly pinned official artifacts only if separately approved. Synthesis, inference, model execution, voice use, and audio creation remain prohibited.

STOP FOR HUMAN REVIEW.
