# Cold Truth — K1 Kokoro Adapter Contract Report

Date: 2026-07-13  
Phase: K1 — fake transport only  
Outcome: **PASSED**

## Scope completed

K1 adds a provider-neutral, offline-only narration boundary identified exactly as:

`local_kokoro_isolated_adapter`

The boundary can be constructed only with the exact K1 fake in-memory transport and exact K1 fake exclusive-create writer classes. It has no real Kokoro runtime, model, voicepack, executable, server, provider, configuration, environment, credential, network, subprocess, or audio-generation route.

## Files created

1. `automation/providers/kokoro_local_adapter_contract.py`
2. `automation/testing/k1_fake_kokoro_transport.py`
3. `automation/test_k1_kokoro_local_adapter_contract.py`
4. `automation/PHASE_K1_KOKORO_ADAPTER_CONTRACT_REPORT.md`

No existing C1–C8o source, test, report, authorization, audit, configuration, or historical-record file was modified.

## Contract controls

- Strict typed request and result dataclasses.
- Fake text must begin with the exact K1 fake marker and is bounded to 500 characters.
- The only voice identifier is the explicitly fake `fixture_voice_alpha`.
- The only declared future output format is `wav`; K1 itself writes only a `.fixture` file containing fixed non-audio bytes.
- The caller binds one exact, single-component relative output destination beneath an isolated temporary test workspace.
- Absolute paths, traversal, nested paths, alternate suffixes, and destination changes fail before synthesis.
- Existing files, directories, links, reparse points, and unsafe targets fail before synthesis.
- The transport may return only the exact deterministic K1 non-audio byte sequence in memory.
- The writer uses exclusive-create mode and accepts only those exact deterministic fixture bytes.
- Transport and writer calls are limited to one each. The adapter is single-use.
- No retry, fallback, queue, polling, background work, auto-chunking, replay, overwrite, cleanup, copy, rename, or second synthesis call exists.
- Failure results contain only a safe category. Output path and byte count appear only on success.
- Safe audit data is limited to route identifier, fake-test marker, result category, successful byte count, and fake call counts.
- Constructor identity checks reject subclasses, lookalikes, arbitrary callables, and any non-K1 dependency.

## K1 focused validation

Command:

`C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe test_k1_kokoro_local_adapter_contract.py`

Result: **14/14 passed**

The focused suite verifies happy-path call counts and exclusive creation; exact destination containment; all required request, voice, format, target, transport, writer, and result-shape failures; single-use behavior; the safe audit shape; and the absence of real-runtime imports.

## C1–C8o offline regression

The established suites ran in order after K1 passed:

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

Regression result: **266/266 passed**  
K1 plus regression result: **280/280 passed**

Every suite reported offline-only execution. No real Codex/model invocation, MCP invocation, provider request, network request, or audio/media creation occurred.

## Safety and state confirmation

- Kokoro and Voicebox were not installed, imported, downloaded, accessed, launched, or executed.
- No model, voicepack, candidate real voice, local server, audio, or media file was created.
- No ElevenLabs, ElevenLabs MCP, direct HTTPS provider, other provider, browser automation, Node runtime, external service, or network request was used.
- No credentials, API keys, environment variables, private configuration, account data, browser data, or secrets were accessed.
- No authorization was created, inspected, consumed, or changed.
- Immutable historical C8/C8n contents were not opened, parsed, hashed, validated, or mutated; existing regression checks used metadata-only handling.
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`.
- No C4 approval was created or consumed.
- Rendering, upload, scheduling, publishing, and real production remain disabled.

## Remaining blocker

The next possible phase is a separately authorized **K2 local-environment readiness** phase. K2 may inspect and install explicitly approved local packages, but it must remain separately gated and may not generate audio.

STOP FOR HUMAN REVIEW.
