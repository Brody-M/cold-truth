# Cold Truth — L7C Bounded L8 Execution Runner Report

Date: 2026-07-13  
Scope: offline implementation and fake-only validation. L8 was not authorized or
executed.

## Result

L7C created a dedicated dependency-injected runner design for one future L8
synthetic attempt. All required focused and regression suites passed:

| Suite | Passed/total |
|---|---:|
| L7C focused | 14/14 |
| L7/L7A/L7B focused | 23/23 |
| L2 focused | 16/16 |
| K1 focused | 14/14 |
| C1–C8o | 266/266 |
| **Combined** | **333/333** |

Every suite exited `0`; there was no failure or early stop point. L6 was not run.

All suites used the accepted bundled interpreter with `-B` from
`C:\Youtube Automation Obsidian\automation`. C1 used its native offline
invocation without `-q`.

## Files created or changed

Created:

- `automation/l8_one_time_piper_synthetic_runner.py`
- `automation/test_l8_one_time_piper_synthetic_runner.py`
- `automation/PHASE_L7C_BOUNDED_L8_EXECUTION_RUNNER_REPORT.md`

No existing source, test, fixture, report, runtime asset, package environment,
configuration, provider route, C3/C4 file, or production file was changed.

## Public runner contract

The runner exposes one public execution entry point:

```python
execute_one_time_piper_synthetic(
    *,
    authorization,
    runtime_factory,
    exclusive_wav_writer,
    clock,
    file_system_boundary,
    safe_audit_sink,
    ephemeral_test_text_supplier,
)
```

It accepts no text, path, output root, filename, model, voice, provider, format,
runtime option, command-line option, configuration, credential, or production
argument.

Exact injected interfaces:

- `runtime_factory.create_locked_runtime(...)`
- returned runtime: `initialize_locked_session()`
- returned session: `locked_identity()` and `synthesize_once(text)`
- `exclusive_wav_writer.write_wav_exclusive(root, filename, payload)`
- `clock.now_utc()`
- `file_system_boundary.preflight_output_absent(root, filename)` and
  `create_root_exclusive(root)`
- `safe_audit_sink.create_authorization_exclusive(record)`,
  `consume_authorization_exclusive(record)`, and
  `create_audit_exclusive(record)`
- `ephemeral_test_text_supplier.supply_ephemeral_text_once()`

The runner rejects missing interfaces and any injected object with additional
public callable capabilities.

## Locked values and enforced limits

The runner reconstructs operational arguments internally from the L7B locked
constants and permits only:

- Route: `local_piper_1_4_2_en_us_ljspeech_high`
- Piper: `1.4.2`
- Model and voice: `en_US-ljspeech-high`
- Model SHA-256:
  `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a`
- Config SHA-256:
  `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14`
- Provider: `CPUExecutionProvider`
- Format: `wav`
- Root: `C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests`
- Filename: `l8_piper_synthetic_test.wav`

Enforced maximums are one runtime factory/process claim, one session
initialization, one text input, one synthesis attempt, one output file, one
exclusive write, one model/voice/provider/format, zero retries, and zero
fallbacks. A process-wide one-attempt gate rejects all second invocations,
including reset, clone, reissue, reuse, and post-consumption calls.

The provided authorization lifecycle is set to `AUTHORIZATION_CONSUMED` after
the first simulated execution attempt whether runtime or writer succeeds or
fails. Safe dependency exceptions are reduced to fixed categories; raw
exception text is never returned or audited.

## Fail-closed conditions

The runner stops before operational dependencies for any invalid L7B schema,
field set, purpose, authorization ID, nonce, expiry, lifecycle state, identity,
hash, provider, voice, output, limit, content flag, C3/C4 linkage, case/script/
research/production linkage, raw-text field, unknown field, or prior-use state.

It also fails closed for:

- schema-version mismatch;
- missing or expanded injected interfaces;
- malformed clock values, expired authorization, or expiry immediately before
  the attempt boundary;
- wrong/unsafe/existing output root or target, failed containment, link or
  reparse status, non-regular/nonempty root, or lack of exclusive creation;
- missing, malformed, oversized, hash-mismatched, or non-synthetic ephemeral
  text envelope;
- authorization-record or root exclusive-creation failure;
- runtime factory, runtime interface, session initialization, session interface,
  runtime identity, or synthesis failure;
- empty/non-byte synthesis result;
- writer failure, nonexclusive result, wrong file/write count, invalid byte
  count, or invalid output hash shape;
- authorization-consumption, safe-audit creation, or any unexpected execution
  exception.

There is no cleanup, deletion, copy, move, rename, overwrite, conversion,
playback, decoding, transcription, analysis, rendering, upload, scheduling, or
publishing path. There is no retry or fallback loop.

## Offline-test and safety confirmations

- L7C tests used spies and in-memory fakes only. Their payload was explicitly
  fake and non-audio; no real authorization or audit record was created.
- The fake success path proved the exact future call sequence and one-call
  limits. Fake runtime and writer failures proved immediate single consumption,
  no retry/fallback, and no second write.
- Supplied fake text was cleared from the ephemeral envelope and was absent from
  results, authorization/audit payloads, errors, and runner durable state.
- Zero operational L8 authorization/audit/output activity occurred.
- Zero Piper/ONNX imports, sealed-runtime processes, model/config loads, real
  runtime text inputs, inference, synthesis, audio/media creation, output-root
  inspection or creation, filesystem output writes, network/provider/MCP/browser
  activity, secret/credential/environment-value access, C3/C4 activity, or
  production changes occurred.
- C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed.
  Publishing and production remain disabled.

## Remaining blocker

Human review is required. Any real attempt then requires a fresh, separate,
one-time L8 authorization using the new L7C runner and trusted concrete injected
boundaries.

STOP FOR HUMAN REVIEW.
