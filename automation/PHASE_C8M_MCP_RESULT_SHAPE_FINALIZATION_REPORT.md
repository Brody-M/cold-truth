# Cold Truth — Phase C8m MCP Result-Shape Finalization Report

## Status

`C8M_FOCUSED_TESTS_PASSED_REGRESSION_BLOCKED_AT_C7`

## Result-shape redesign

The active authorization schema now requires exactly one selected result shape:

1. `returned_contained_local_mp3_path`
2. `mcp_audio_resource`

The prior active staging-directory assumption has been removed from the authorization shape and retained only as inactive C8i history. Future authorizations bind the exact disposable-output directory and canonical final path rather than a dedicated staging directory.

### Local-path branch

One newly produced direct regular `.mp3` inside the exact disposable C8 output directory may be atomically renamed once to the canonical final path. Copy, overwrite, retry, a second rename, cleanup, and deletion remain forbidden.

### MCP-audio-resource branch

One exact opaque MCP audio-resource interface may be materialized once to the canonical final path using exclusive create. The declarative finalizer exposes no generic filesystem, URL, transport, MCP, provider, configuration, audio-inspection, decoding, playback, or media-processing capability.

## Fail-closed cases

Both branches block on no output, multiple outputs, mixed path/resource results, remote URLs, attachment/download references, metadata-only results, non-audio resources, bytes-like arbitrary payloads, output outside the authorized boundary, traversal, absolute paths, nested paths, links, junctions, directories, non-MP3 files, pre-existing files, destination existence, or finalization failure.

Blocked outcomes permit no retry, second MCP operation, second finalization action, copy, overwrite, cleanup, deletion, polling, status call, follow-up, temporary media, or audio processing.

## Focused validation

- C8m focused suite: 18/18 passed.
- No MCP/provider/network action, authorization creation, or media creation occurred.

## Regression run

The full run stopped at the first failure:

| Phase | Result |
|---|---:|
| C1 | 19/19 passed |
| C2 | 13/13 passed |
| C3 | 6/6 passed |
| C4 | 18/18 passed |
| C5 | 16/16 passed |
| C6 | 18/18 passed |
| C7 | 18/19; one failure |

Failing test:

`test_17_c7_cannot_create_or_validate_c8_authorization`

The test still asserts that no non-schema/non-contract JSON exists in the future-C8 directory. The directory now intentionally retains the previously consumed one-time C8 authorization and its safe audit. C8m did not modify the C7 test because C1–C7 logic/tests are outside this phase's permitted modification surface. No C8a–C8L regression suite was run after the C7 stop.

No combined regression total is claimed.

## Files created or changed

- `automation/c8m_mcp_result_shape_finalization_contract.py`
- `automation/test_c8m_mcp_result_shape_finalization_contract.py`
- `automation/c8a_authorization_schema_validator.py`
- `automation/test_c8a_authorization_schema.py`
- `automation/test_c8b_contract_alignment.py`
- `automation/test_c8_isolated_provider_execution_adapter.py`
- `automation/test_c8d_live_readiness_contract.py`
- `automation/test_c8e_runner_boundary_contract.py`
- `automation/test_c8f_configuration_plan_contract.py`
- `automation/test_c8h_mcp_execution_contract.py`
- `automation/test_c8i_mcp_output_finalization_contract.py`
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/one_time_live_synthetic_provider_authorization.schema.json`
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/one_time_live_synthetic_provider_authorization.contract.json`
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/README.md`
- `automation/README.md`
- `automation/PHASE_C8M_MCP_RESULT_SHAPE_FINALIZATION_REPORT.md`

## Boundary confirmation

- MCP/provider/network action: not performed
- New authorization issuance or consumption: not performed
- Configuration, credential, environment, endpoint, voice-ID, account, or login access: not performed
- Audio/media creation or processing: not performed
- Real-case or production access: not performed
- Rendering, upload, scheduling, publishing, or production activity: not performed

C3 remains `AWAITING_SCRIPT_APPROVAL`. No C4 approval was created or consumed. Publishing and real-production modes remain disabled.

## Narrowest next prerequisite

A separate authorization is required to update the stale C7 regression expectation so it recognizes only the exact closed historical consumed C8 authorization and safe audit while still proving C7 cannot create, validate, or execute C8. After that compatibility repair, the full regression sequence must be rerun before C8m can be certified or a new live C8 authorization can be considered.
