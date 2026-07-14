# Cold Truth — C8n Runtime Result-Shape Selection Report

## Status

`COMPLETE — OFFLINE CONTRACT AND REGRESSION TESTS PASSED`

C8n replaces C8m's preselected result-shape requirement with an authorization-bound canonical allowlist. It adds no live authorization, provider implementation, MCP operation, executable finalizer, or media operation.

## Canonical authorization allowlist

The required `allowed_runtime_result_shapes` value is exactly:

```json
[
  "returned_contained_local_mp3_path",
  "mcp_audio_resource"
]
```

The authorization schema declares a closed array whose items can only be those two strings. The in-memory validator binds the whole array to the exact expected value, so empty, partial, reversed, duplicated, wildcard, arbitrary, or extended arrays fail closed.

The obsolete `selected_result_shape` authorization field was removed from the active schema, contract, hypothetical record, and tests. Historical consumed C8 authorization and audit records were not modified.

## Runtime classification boundary

The offline C8m/C8n contract helper now classifies the single returned MCP result only after the one operation. Classification requires the exact canonical authorization allowlist and accepts exactly one of:

- one well-formed, newly created, direct, contained regular MP3 path; or
- one exact opaque MCP audio-resource object.

It returns no classification for zero results, multiple results, mixed path/resource results, unknown objects, metadata-only values, URLs, download or attachment references, non-audio strings, bytes-like values, malformed path records, nested/outside paths, or link records. It exposes and retains no raw MCP output or audio content.

## Finalization boundaries retained

- Local path: existing containment checks remain mandatory; at most one atomic same-filesystem rename may target the exact canonical MP3 destination.
- MCP audio resource: existing opaque-resource checks remain mandatory; at most one exclusive-create materialization write may target the exact canonical MP3 destination.
- Both branches preserve one MCP operation, one provider request, one output, one finalization action, and one safe audit record maximum.
- Retry, a second MCP operation, polling, status, follow-up, cleanup, deletion, copying, overwrite, fallback, alternate provider, discovery, batch mode, multi-output, audio processing, configuration access, credential access, environment access, endpoint exposure, and account-data access remain prohibited.

The canonical destination remains:

`fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/disposable_output/c8_isolated_synthetic_connectivity.mp3`

## Test results

The approved local Python 3.12.13 interpreter ran all tests with no retry.

### C8n focused suite

- `test_c8n_runtime_result_shape_selection_contract.py`: **9/9 passed**

### C1 through C8m regression baseline

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

The unchanged unique C1-through-C8m baseline is **246/246 passed**. Including the new C8n-focused suite, this phase executed **255/255 offline tests**.

## Files changed or created

- `automation/c8m_mcp_result_shape_finalization_contract.py`
- `automation/test_c8m_mcp_result_shape_finalization_contract.py`
- `automation/test_c8n_runtime_result_shape_selection_contract.py`
- `automation/test_c8a_authorization_schema.py`
- `automation/test_c8b_contract_alignment.py`
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/one_time_live_synthetic_provider_authorization.schema.json`
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/one_time_live_synthetic_provider_authorization.contract.json`
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/README.md`
- `automation/README.md`
- `automation/PHASE_C8N_RUNTIME_RESULT_SHAPE_SELECTION_REPORT.md`

## Safety and state confirmation

- No MCP tool, provider request, network/API action, Node process, Codex process, browser, or external service was invoked.
- No live C8 authorization was issued. The prior C8 authorization remains consumed.
- No credentials, configuration, environment values, voice identifiers, endpoints, headers, account data, private files, or login state were accessed.
- No audio, media, staging directory, or provider-output artifact was created.
- No real-case, existing-script, Jodi, production, rendering, upload, scheduling, publishing, or media-workflow activity occurred.
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`.
- No C4 approval was created, referenced, or consumed.
- Publishing and real-production modes remain disabled.

## Remaining blocker

Human review of C8n, followed by a new, separate, explicit one-time C8 authorization allowing exactly one ElevenLabs MCP narration operation and one runtime-classified bounded finalization action.
