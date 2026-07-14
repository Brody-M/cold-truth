# Cold Truth — L8R One-Time Piper Synthetic Connectivity Report

Date: 2026-07-14  
Outcome: **BLOCKED AT PREFLIGHT — NO SEALED-INTERPRETER LAUNCH; NO RETRY AUTHORIZED**

## Preflight result

Static identity and interface review confirmed that the unchanged L7B, L7C,
L7D, and L7E components retain the requested fixed values and one-attempt
limits. Operational compatibility did not pass, however, because the required
L8R ordering cannot be performed by the certified implementation without a
prohibited wrapper, extraction/reconstruction step, alternate entrypoint, or
code change.

The first stop point was reached before any L8R authorization candidate or
durable record, filesystem inspection, process, runtime, text handoff, or output
activity.

### Fail-closed incompatibilities

1. The repaired canonical entrypoint exists only as the private embedded string
   `_SEALED_INTERPRETER_ENTRYPOINT_SOURCE` in
   `automation/l8_one_time_piper_synthetic_runner.py`. It is not a standalone
   executable launcher, public getter, or module entry point. Supplying its
   value as a `-c` argument would require extracting, importing, copying,
   inlining, or reserializing it. L8R expressly prohibits inline `-c`
   reconstruction, wrappers, temporary launchers, alternate quoting, and
   substitution.
2. The canonical source performs L7D output-root/target preflight only after
   the sealed interpreter has launched. L8R requires a failed preflight to stop
   before any process launch and requires the L7D path-bound check before that
   launch. Both conditions cannot be true with the unchanged canonical source.
3. The certified runner's supported sequence is: sealed-process launch;
   in-memory candidate creation; authorization/interface/expiry validation;
   L7D absence preflight; fixed-text supply and hash validation; durable
   authorization creation; output-root creation; runtime/session initialization;
   model/config rehash; synthesis; exclusive WAV write; authorization
   consumption; final audit creation. L8R instead lists authorization, audit,
   and output-root creation before the sealed-process launch.
4. `SafeL8LifecycleAuditSink.create_audit_exclusive()` fails closed unless
   `consume_authorization_exclusive()` has already succeeded. Therefore an audit
   cannot be created at L8R permitted-sequence step 2 and then have the
   authorization consumed at step 10. The certified order is consumption first,
   final audit second.
5. The runner may obtain the one-use synthetic text after in-memory validation
   and L7D absence preflight but before durable authorization creation. L8R says
   any failed preflight must stop before a text handoff. Changing this ordering
   is outside the authorization.

L8R authorizes no implementation repair, clarification-by-assumption, alternate
command, or substitution. The only compliant action was therefore to stop
before launch.

## Static compatibility and locked bindings

The following source bindings match the L8R request:

| Binding | Static result |
|---|---|
| Authorization schema | `cold_truth.l7b.l8_executable_synthetic_authorization.v1` |
| Purpose | `synthetic_local_connectivity_test` |
| Route | `local_piper_1_4_2_en_us_ljspeech_high` |
| Piper | `1.4.2` |
| ONNX Runtime | `1.27.0` |
| Model and voice | `en_US-ljspeech-high` |
| Model SHA-256 | `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a` |
| Config SHA-256 | `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14` |
| Provider | `CPUExecutionProvider` |
| Format | `wav` |
| Sealed interpreter | `C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe` |
| Model path | `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx` |
| Config path | `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx.json` |
| Authorization root | `C:\ColdTruthLocalTools\piper-l8a-synthetic-authorizations` |
| Audit root | `C:\ColdTruthLocalTools\piper-l8a-synthetic-authorization-audit` |
| Output root | `C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests` |
| Output filename | `l8_piper_synthetic_test.wav` |
| Exact output path | `C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests\l8_piper_synthetic_test.wav` |
| Maximum runtime/session/text/synthesis/output/write counts | `1` each |
| Maximum retries/fallbacks | `0` each |

The L7B factory/validator, L7C runner signature, L7D concrete adapter
interfaces, and L7E private canonical source were not changed.

Dynamic model/config hash verification, provider/session verification, and
output containment/absence verification were **not reached**. Reporting the
static locked values above is not a claim that the assets, provider, output
root, or target were inspected during L8R.

## Authorization, audit, process, and output status

- Fresh L8R authorization candidate created: **no**
- Authorization record created: **no**
- Authorization ID: `not_created`
- Nonce fingerprint: `not_created`
- Final lifecycle state: `NOT_CREATED — PREFLIGHT_BLOCKED`
- Safe audit record created: **no**
- Authorization root inspected or created: **no**
- Audit root inspected or created: **no**
- Output root/target inspected: **no**
- Output root created: **no**
- Sealed-interpreter process launches: **0**
- Runtime-factory/process claims: **0**
- Runtime/session initializations: **0**
- Model/config loads or runtime hash reads: **0**
- Text handoffs: **0**
- Synthesis attempts: **0**
- Output files: **0**
- Output writes: **0**
- WAV path, byte count, and SHA-256: `not applicable — no WAV exists from L8R`
- Retries: **0**
- Fallbacks: **0**
- Alternate launches or commands: **0**
- Additional processes or outputs: **0**

No L8R process was launched, so there is no sealed-interpreter exit code. No
test, runtime diagnostic, cleanup, deletion, playback, or audio inspection was
performed.

## Boundary confirmations

- The exhausted prior L8 authorization and its records were not read, altered,
  reused, reset, cloned, mutated, reissued, or replaced during L8R.
- No raw synthetic text was placed in source, command construction, logs,
  report metadata, authorization/audit data, filenames, or environment data.
- Network/provider/API/MCP/browser activity, credential or secret access,
  environment-variable access, case/script/research/channel use, and C3/C4
  access were all **0**.
- Playback, decoding, transcription, duration inspection, waveform/spectrogram
  generation, audio QA, editing, rendering, upload, scheduling, publishing, and
  production activity were all **0**.
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`. No C4 approval was created or
  consumed. Publishing and production remain disabled.

## Remaining blocker

Human review is required to resolve the incompatibility between L8R's mandated
pre-launch/audit ordering and the certified runner/adapters' supported order,
and to provide an authorized direct mechanism for materializing the private
canonical entrypoint if execution is still desired. No retry, second launch,
repair, alternate invocation, or new authorization is authorized under L8R.

**STOP FOR HUMAN REVIEW.**
