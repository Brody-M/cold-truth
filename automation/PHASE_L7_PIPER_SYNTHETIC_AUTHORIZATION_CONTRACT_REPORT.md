# Cold Truth — L7 Piper First-Synthesis Authorization Contract Report

## Outcome

`STOPPED_DURING_REGRESSION_VALIDATION`

The fake-only L7 contract implementation and its focused validation completed successfully. L2 and K1 also passed. The ordered C1-C8o regression sequence stopped before any C1 test ran because the C1 harness rejected the supplied `-q` command-line argument with exit code 2. In accordance with the stop-on-first-failure rule, C1 was not retried and no later C suite was run.

## Files created

- `automation/l7_piper_synthetic_authorization_contract.py`
- `automation/test_l7_piper_synthetic_authorization_contract.py`
- `automation/fixtures/l7_piper_synthetic_authorization_valid.json`
- `automation/fixtures/l7_piper_synthetic_authorization_invalid_identity.json`
- `automation/fixtures/l7_piper_synthetic_authorization_invalid_raw_text.json`
- `automation/fixtures/l7_piper_synthetic_authorization_invalid_prerequisite.json`
- `automation/fixtures/l7_piper_synthetic_authorization_invalid_output.json`
- `automation/fixtures/l7_piper_synthetic_authorization_invalid_authorization_id.json`
- `automation/PHASE_L7_PIPER_SYNTHETIC_AUTHORIZATION_CONTRACT_REPORT.md`

No pre-existing implementation, runtime, provider, authorization, production, or media file was changed.

## Contract boundary

This phase creates only an inert, fake-fixture authorization schema and validator. It cannot create, grant, persist, consume, or execute a live authorization. A valid fake fixture returns only `AUTHORIZED_NOT_EXECUTED`.

Locked declarations include:

- Route: `local_piper_1_4_2_en_us_ljspeech_high`
- Piper version: `1.4.2`
- Model: `en_US-ljspeech-high`
- Execution provider declaration: `CPUExecutionProvider`
- Future output format declaration: `WAV`
- One attempt, one process, one voice, one output, zero retries, and zero fallbacks
- A hash and declared character count only; raw synthesis text is forbidden
- Fake-fixture identity, future expiry, unique fake authorization ID, and explicit non-executable/non-consumable flags
- Future C3 approval and C4 approval prerequisites must both be declared required
- Unsafe paths, pre-existing targets, links, reparse points, extra fields, extra capabilities, real-case content, personal data, production content, and reusable authorization IDs fail closed

The future output path declaration is constrained to the test-only root `C:\ColdTruthLocalTools\piper-l8-synthetic-tests`, directory `l8_piper_synthetic_test_l7_fake_0001`, and filename `l8_piper_synthetic_test.wav`. L7 neither creates nor inspects that location.

## Validation results

1. L7 focused fake-contract suite: **17/17 passed**.
2. L2 Piper adapter fake-contract suite: **16/16 passed**.
3. K1 Kokoro adapter fake-contract suite: **14/14 passed**.
4. L6: **not run**, as required by the corrected offline boundary. Its prior 12/12 result remains historical only and was not re-certified here.
5. C1: **no tests ran**. The harness rejected `-q` as an unrecognized argument and exited 2.
6. C2-C8o: **not run** because validation stopped at C1.

Exact safe C1 failure:

```text
usage: test_real_codex_fixture.py [-h] [--run-real]
                                  [--codex-executable CODEX_EXECUTABLE]
test_real_codex_fixture.py: error: unrecognized arguments: -q
```

No combined regression total is claimed.

## Activity attestations

- Piper imports: 0
- ONNX imports: 0
- Runtime processes started by L7: 0
- Model or config loads: 0
- Raw synthesis text inputs: 0
- Inference or synthesis calls: 0
- Audio or media artifacts: 0
- Output directories or files created by the contract: 0
- Network, provider, API, MCP, or browser activity: 0
- Credentials, environment variables, configuration values, voice IDs, or account data accessed: 0
- Executable authorizations created or consumed: 0
- Real-case, rendering, upload, scheduling, publishing, or production activity: 0

C3 remains exactly `AWAITING_SCRIPT_APPROVAL`. No C4 approval was created or consumed. Publishing and real production remain disabled.

## Remaining blocker

Human review is required. A separately authorized validation task may rerun the C1-C8o regression sequence using each harness's accepted established invocation. L8 remains blocked: no bounded synthetic WAV attempt is authorized by this phase.
