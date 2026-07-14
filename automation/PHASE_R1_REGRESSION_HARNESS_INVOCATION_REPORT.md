# Cold Truth — R1 Regression Harness Invocation Report

## Result

`PASSED — C1-C8o OFFLINE REGRESSION CERTIFIED 266/266`

All existing C1-C8o suites were invoked exactly once, unchanged, in the required order. Every suite exited 0. No retry, repair, alternate invocation, or later-stage activity occurred.

## Interpreter and invocation discovery

Interpreter used for every suite:

```text
C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

`-B` was supplied to the Python interpreter only to prevent bytecode-cache output. No option was passed to any test harness.

C1, C2, and C3 are direct Python/unittest harnesses with custom `argparse` entry points. Their accepted offline invocation is the script with no harness arguments. C4-C8o are direct Python/unittest harnesses with no command-line parser and likewise require no harness arguments.

### Why C1 rejected `-q`

Static inspection of `automation/test_real_codex_fixture.py` found that its `ArgumentParser` declares only:

- `--run-real`
- `--codex-executable`

The parser uses `parse_args()`, so the unrecognized harness argument `-q` is rejected before test loading. The accepted C1 command used in R1 was:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B test_real_codex_fixture.py
```

## Accepted invocations and results

All commands below ran from `C:\Youtube Automation Obsidian\automation`.

| Stage | Accepted invocation after the interpreter and `-B` | Exit | Passed |
|---|---|---:|---:|
| C1 | `test_real_codex_fixture.py` | 0 | 19/19 |
| C2 | `test_real_research_verifier_fixture.py` | 0 | 13/13 |
| C3 | `test_writer_editor_fixture.py` | 0 | 6/6 |
| C4 | `test_script_approval_gate.py` | 0 | 18/18 |
| C5 | `test_narration_preflight_gate.py` | 0 | 16/16 |
| C6 | `test_synthetic_narration_adapter.py` | 0 | 18/18 |
| C7 | `test_narration_provider_adapter.py` | 0 | 19/19 |
| C8a | `test_c8a_authorization_schema.py` | 0 | 16/16 |
| C8b | `test_c8b_contract_alignment.py` | 0 | 12/12 |
| C8c | `test_c8_isolated_provider_execution_adapter.py` | 0 | 16/16 |
| C8d | `test_c8d_live_readiness_contract.py` | 0 | 12/12 |
| C8e | `test_c8e_runner_boundary_contract.py` | 0 | 12/12 |
| C8f/C8g | `test_c8f_configuration_plan_contract.py` | 0 | 18/18 |
| C8h | `test_c8h_mcp_execution_contract.py` | 0 | 16/16 |
| C8i/C8j | `test_c8i_mcp_output_finalization_contract.py` | 0 | 17/17 |
| C8m | `test_c8m_mcp_result_shape_finalization_contract.py` | 0 | 18/18 |
| C8n | `test_c8n_runtime_result_shape_selection_contract.py` | 0 | 9/9 |
| C8o | `test_c8o_direct_elevenlabs_api_contract.py` | 0 | 11/11 |

Combined result: **266/266 passed**.

There was no failure or early stop point.

## Boundary confirmations

- No source, test, fixture, lock, dependency, virtual-environment, runner-configuration, or pre-existing report file was changed.
- This R1 report is the only file created or changed by R1.
- L5 and L6 were not run. Piper, ONNX Runtime, the sealed Piper environment, local TTS runtimes, model assets, and model/config loading were not invoked or imported.
- No narration text was submitted and no inference or synthesis occurred.
- No WAV, MP3, PCM, waveform, spectrogram, audio/media artifact, output directory, or L8 authorization was created.
- No ElevenLabs, Voicebox, Kokoro, MCP, provider API, network TTS, browser automation, local server, render, upload, scheduling, publishing, or production activity occurred.
- No credential, secret, API key, environment-variable value, provider configuration, browser/account data, or runtime configuration was accessed.
- No historical C8/C8o authorization or audit record was opened, parsed, hashed, validated, consumed, or modified. Existing tests retained their metadata-only and hands-off boundaries.
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`.
- No C4 approval was created or consumed.
- Publishing and real production remain disabled.

## Certification and next gate

L7 is regression-certified against the unchanged C1-C8o baseline. L8 remains blocked and requires a fresh, separate, explicit human authorization before any bounded synthetic WAV attempt.
