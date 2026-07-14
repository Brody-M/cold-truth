# Cold Truth — L7D Concrete L8 Dependency Implementations Report

Date: 2026-07-13  
Scope: offline implementation and fake-only validation. L8 was not authorized or
executed.

## Result

Concrete, fixed-binding local dependency adapters now exist for every injected
L7C runner boundary. They are inert at import and construction and were never
invoked against real runtime, filesystem, authorization, audit, text, or media
resources during L7D.

All required suites passed:

| Suite | Passed/total |
|---|---:|
| L7D focused | 17/17 |
| L7C focused | 14/14 |
| L7/L7A/L7B focused | 23/23 |
| L2 focused | 16/16 |
| K1 focused | 14/14 |
| C1–C8o | 266/266 |
| **Combined** | **350/350** |

Every invocation exited `0`; there was no failure or stop point. L6 was not run.
C1 used its native R1-approved offline invocation without `-q`.

## Files created or changed

Created:

- `automation/l8_local_dependency_adapters.py`
- `automation/test_l8_local_dependency_adapters.py`
- `automation/PHASE_L7D_CONCRETE_L8_DEPENDENCY_IMPLEMENTATIONS_REPORT.md`

Minimally changed for exact interface wiring:

- `automation/l8_one_time_piper_synthetic_runner.py`
- `automation/test_l8_one_time_piper_synthetic_runner.py`

No L1–L7B, L2 fake dependency, K1–K2a, C1–C8o, runtime asset,
package environment, provider configuration, historical record, Codebase Memory,
C3/C4, or production file was changed.

## Exact concrete interfaces

All adapter constructors are parameterless.

- `CanonicalL8FileSystemBoundary.preflight_output_absent()`
- `CanonicalL8FileSystemBoundary.create_root_exclusive()`
- `SafeL8LifecycleAuditSink.create_authorization_exclusive(record)`
- `SafeL8LifecycleAuditSink.consume_authorization_exclusive(record)`
- `SafeL8LifecycleAuditSink.create_audit_exclusive(record)`
- `FixedEphemeralSyntheticTextSupplier.supply_ephemeral_text_once(expected_sha256)`
- `UtcL8Clock.now_utc()`
- `LockedLocalPiperRuntimeFactory.create_locked_runtime()`
- returned runtime: `initialize_locked_session()`
- returned session: `locked_identity()` and `synthesize_once(text)`
- `CanonicalExclusiveWavWriter.write_wav_exclusive(wav_bytes)`

The runner remains dependency-injected and retains exactly one public execution
entry point: `execute_one_time_piper_synthetic(...)`.

## Fixed binding constraints

The filesystem adapter accepts no path argument. It is internally bound to:

- authorization root:
  `C:\ColdTruthLocalTools\piper-l8a-synthetic-authorizations`
- audit root:
  `C:\ColdTruthLocalTools\piper-l8a-synthetic-authorization-audit`
- output root:
  `C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests`
- output filename: `l8_piper_synthetic_test.wav`

Its future operational methods permit only absent fixed roots, direct canonical
containment under `C:\ColdTruthLocalTools`, safe regular directories, non-link/
non-reparse state, an absent target, exclusive directory creation, and an empty
new output root. It exposes no path override, browsing, globbing, deletion,
cleanup, copy, move, rename, overwrite, or conversion API.

The lifecycle/audit sink uses only the fixed authorization and audit roots and
direct exclusive JSON creation. It permits exact schemas only. Persisted
lifecycle records contain a SHA-256 nonce fingerprint rather than the raw nonce.
Audit metadata is limited to the authorization/safe event identifiers,
lifecycle/outcome/failure category, bounded counts, locked identity, canonical
output metadata, byte count, and SHA-256. Raw text, raw nonce, secrets,
credentials, environment data, C3/C4, case/script/production content,
tracebacks, exception objects, and unknown fields are rejected.

The text supplier accepts only the expected SHA-256, reconstructs the fixed
future non-case text in memory only after that hash matches, independently
rehashes it, and permits one release. It has no text constructor argument,
setter, file/clipboard/command-line/environment/network/configuration input, or
arbitrary selection API. L7D never called its valid release path.

The runtime factory accepts no identity, path, model, voice, provider, format,
CLI, server, or runtime option. It is permanently bound to:

- interpreter:
  `C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe`
- Piper `1.4.2`
- ONNX Runtime `1.27.0`
- model/voice `en_US-ljspeech-high`
- model SHA-256
  `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a`
- config SHA-256
  `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14`
- `CPUExecutionProvider`
- WAV output

Piper and ONNX imports are lazy inside the future session-initialization method,
after interpreter, package version, asset type, link/reparse, and hash checks.
The factory/session are one-use and expose no arbitrary run, tensor, phoneme,
stream, server, CLI, benchmark, profiling, or model-session API.

The WAV writer accepts bytes only and has no path or format argument. It is
permanently bound to the canonical final WAV and uses one direct exclusive
create/write. It creates no temporary file and exposes no inspection, decode,
playback, conversion, copy, move, rename, overwrite, cleanup, or deletion path.
Byte count and SHA-256 are produced only after a successful complete write.

## Runner wiring changes

- The runtime factory call is now parameterless; locked identity values cannot
  be supplied or overridden by callers.
- Filesystem preflight/root creation and WAV writing no longer accept paths.
- The runner passes only the authorization text hash to the one-shot supplier.
- Authorization lifecycle payloads use a nonce fingerprint, never a raw nonce.
- Final audit payloads now include safe failure and output metadata needed by the
  strict concrete audit schema.
- The one-invocation process gate is claimed immediately after exclusive fake or
  future authorization creation, preventing a later invocation after any
  post-claim failure.

## Offline-test and boundary confirmations

- Concrete modules imported without importing Piper, ONNX Runtime, or a TTS
  dependency.
- Tests used spies, fakes, pure schema validation, and pre-body invalid-argument
  rejection only. No valid concrete filesystem, text-release, runtime,
  authorization/audit-write, or WAV-write operation was invoked.
- Fake success, runtime-failure, writer-failure, invalid-authorization,
  wrong-identity, replay, and second-invocation paths confirmed the exact
  sequence, one-use lifecycle, one-call limits, zero retry/fallback, and no
  second write.
- No raw text appeared in fake lifecycle/audit records, runner results, errors,
  logs, or concrete source literals.
- Zero real L8 authorization/audit/output activity occurred.
- Zero authorization/audit/output-directory inspection or creation occurred.
- Zero Piper/ONNX runtime imports, processes, model/config loads, real text
  handoffs, inference, synthesis, audio/media creation, filesystem output writes,
  network/provider/MCP/browser activity, secret/credential/environment-value
  access, C3/C4 access, rendering, upload, scheduling, publishing, or production
  changes occurred.
- C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed.
  Publishing and production remain disabled.

## Remaining blocker

Human review is required. A real operation then requires a fresh, separate,
one-time L8 authorization using the existing L7C runner and the now-available
concrete L7D dependency adapters.

STOP FOR HUMAN REVIEW.
