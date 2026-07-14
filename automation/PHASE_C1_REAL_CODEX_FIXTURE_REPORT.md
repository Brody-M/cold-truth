# Cold Truth Phase C1 Real Codex Fixture Report

**Date:** 2026-07-11  
**Outcome:** BLOCKED during the single authorized Phase C1.1 npm-wrapper invocation  
**Provider invocation attempted:** yes, exactly once  
**Codex Node process started:** no  
**Real cases/media/platforms:** untouched

## Provider implementation

`providers/codex_exec_provider.py` implements the generic `AgentProvider.execute()` interface for one narrowed Strategist fixture. It:

- reads only `COLD_TRUTH_CODEX_RUNTIME_COMMAND`;
- requires the value to be a JSON string array beginning with `codex exec`;
- uses `subprocess` with `shell=false`;
- passes the prompt through stdin rather than the command line;
- pins process `cwd` and Codex `--cd` to the disposable fixture workspace;
- forces `--sandbox workspace-write`;
- requests JSONL with `--json`;
- supplies the self-contained fixture schema through `--output-schema`;
- writes only the final message through `--output-last-message` inside the assigned attempt folder;
- uses `--ephemeral` and an explicit timeout;
- captures exit code, sanitized stdout/stderr, duration, safe runtime/model/thread metadata, and local schema status;
- exposes no credential or full command value in records.

## Non-secret command shape

```text
codex exec
  --sandbox workspace-write
  --cd <fixture-root>
  --json
  --output-schema <fixture-schema>
  --output-last-message <attempt-output>/strategist_handoff.json
  --ephemeral
  -
```

The final `-` means the constrained prompt is supplied on stdin. The executable path and environment-command value are not stored in run records.

## Sandbox and directory enforcement

- Fixture root: `automation/fixtures/real_codex_fixture_workspace/`.
- Provider construction rejects schemas/templates outside that root.
- Every file input is rejected if it escapes the fixture root.
- Process `cwd` and `--cd` are both fixed to the fixture root.
- Attempt output must be beneath the fixture root.
- Last-message output must be beneath the assigned attempt output folder.
- The child environment is replaced with `{NO_COLOR: 1}`; credentials and parent environment values are not inherited.
- No shell is used.

## Structured output validation

The narrowed fixture contract requires one implicit handoff and no side artifacts. The schema fixes:

- fictional case ID `glass-harbor-fixture`;
- claim IDs `SYN-C1-01`, `SYN-C1-02`, and `SYN-C1-03` in order;
- supplied viability, score, risk, and disposition;
- exact request identity and three request input records;
- empty outputs and tool calls;
- `publishing_enabled: false`.

The local schema-subset validator accepts the expected handoff and rejects changed claim IDs. The existing contract validator additionally checks run/case/stage/contract/idempotency identity and exact input-envelope equality.

No real Codex-produced handoff exists because the process never started.

## Safety regression history

### Initial run

- 10 tests executed.
- 7 passed; 3 errored before fake process execution.
- Cause: absolute fixture input paths inherited the workspace folder name, which contains a platform word prohibited by the prompt scanner.
- Fix: candidate JSON and the synthetic standard are now passed as hashed inline values. The prompt contains no filesystem paths.

### Corrected run

- 10 tests passed; 0 failed.

Passing checks:

1. Required `codex exec`, workspace-write, fixture `cwd`, JSONL, output schema, last-message file, ephemeral mode, and stdin prompt shape.
2. Rejection of `--yolo`, approval/sandbox bypass, danger-full-access, full-auto, and ignore-rules.
3. Rejection of working/output paths outside their allowed roots.
4. Rejection of real-case, tool, media, network, credential, and platform prompt content.
5. Rejection of permissions/actions beyond the narrowed Strategist contract.
6. Runtime command values and credential-shaped arguments cannot enter logs.
7. Static check confirms the provider reads one environment reference only.
8. Expected fixture handoff passes local schema and contract validation; altered claims fail.
9. Malformed final output is recorded and blocked.
10. Timeout and nonzero-exit simulations are recorded and blocked.

## Real invocation outcome

The one authorized command submission was rejected by the execution approval layer before the Python test runner began:

```text
BLOCKED_BEFORE_PROCESS_START
Reason category: current Codex session usage limit / execution approval unavailable
```

No retry was attempted. No alternative tool was used. Permissions were not widened. Earlier local `codex exec --help` checks also returned Windows `Access is denied`, including the approved retry, so CLI accessibility remains a separate unresolved concern.

## Filesystem containment

- Safety tests wrote only temporary files beneath the fixture output directory and removed them normally.
- The blocked-status record is inside the fixture output directory.
- No real production or candidate directory was inspected or changed.
- No media file was created.

Containment is established by construction and path-rejection tests; no parent or real-case directory enumeration was performed.

## External activity

- Real Codex process starts: 0.
- MCP calls: 0.
- Browser/research calls: 0.
- External APIs: 0.
- Downloads: 0.
- Media generation/assembly/render: 0.
- Platform/upload/publish actions: 0.

## Configuration status

- `real_production_enabled`: false.
- Runtime config provider enablement: unchanged.
- Publishing: unimplemented and disabled.
- No global or machine environment variable was changed.

## Next prerequisite

Authorize one narrowly scoped child-environment compatibility change that lets the verified npm `codex.cmd` resolve its existing `node` executable without inheriting the full parent environment. After that change is independently safety-tested, a fresh authorization is required for another C1 fixture attempt. Do not proceed to a real Research Verifier until C1 produces a schema-valid, contract-valid handoff and containment evidence from an actually started Codex process.

## Resume CLI diagnostic — 2026-07-11

The scoped diagnostic resolved two packaged applications:

1. `C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources\codex.exe`
2. the sibling extensionless `codex` file.

PowerShell selects `codex.exe`. Direct execution with `--version` failed before process start with Windows `Access is denied` (`ResourceUnavailable`, `NativeCommandFailed`). In accordance with the diagnostic stop rule, `exec --help`, the sibling file, any diagnostic subcommand, and the fixture runner were not attempted.

C1 remains **BLOCKED**. The next prerequisite is an officially accessible Codex CLI path that successfully runs both `--version` and `exec --help` from an ordinary PowerShell process. Real-production mode and publishing remain disabled.

## Authorized npm CLI fixture attempt — 2026-07-11

The user confirmed the normal CMD resolution and preflight for:

`C:\Users\brody\AppData\Roaming\npm\codex.cmd`

The provider was changed only to support an absolute `.cmd` entry point. Python retained `shell=false` and constructed this controlled wrapper:

```text
cmd.exe /d /s /c "<verified-npm-codex.cmd> exec
  --sandbox workspace-write
  --cd <fixture-root>
  --json
  --output-schema <fixture-schema>
  --output-last-message <attempt-output>/strategist_handoff.json
  --ephemeral -"
```

The WindowsApps launcher is now explicitly rejected. `--dangerously-bypass-hook-trust` and `--add-dir` were added to the prohibited-option set. Twelve non-invoking safety tests passed before the real attempt.

Exactly one provider invocation ran. It exited in 31 milliseconds with code 1. Sanitized stderr was:

```text
'"node"' is not recognized as an internal or external command,
operable program or batch file.
```

The provider deliberately supplies only `{NO_COLOR: 1}` to the child and does not inherit `PATH`. Therefore the npm wrapper started, but it could not locate Node and the Codex JavaScript CLI did not start. No retry or environment expansion occurred.

### Validation outcome

- Provider: `codex-exec-controlled-fixture-v1`.
- Mode: `controlled-real-fixture`.
- Exit status: 1, non-retryable.
- Run-record validation: `blocked_provider_failure`.
- Output-schema validation: `not-run`.
- Final handoff: absent.
- Contract validation of a real response: not run.
- Publishing enabled: false.

### Immutable run records

The approved fixture-run folder contains only:

- `REAL_INVOCATION_ATTEMPT.json`;
- `request.json`;
- `attempt-001/record.json`;
- `attempt-001/stdout.txt` (0 bytes);
- `attempt-001/stderr.txt` (97 bytes).

No handoff or media file exists. No file was created outside the disposable fixture/run-record tree. The npm wrapper failure occurred before any Codex transport, model, tool, network, schema-output, or platform activity.

C1 remains **BLOCKED**. Real-production mode and publishing remain disabled.

## Phase C1.1 minimal child PATH and fresh attempt — 2026-07-11

### Safe discovery and child environment

The authorized read-only checks found:

- Node executable: `C:\Program Files\nodejs\node.exe`;
- Node version: `v24.15.0`;
- Node parent: `C:\Program Files\nodejs`;
- npm wrapper directory: `C:\Users\brody\AppData\Roaming\npm`.

The provider now replaces the child environment with an exact allowlist containing only `PATH`, `SystemRoot`, `ComSpec`, `TEMP`, and `TMP`. `PATH` contains only the verified Node parent and npm wrapper directory. `TEMP` and `TMP` point to the fixture-local `output/c1_child_tmp/` directory. No parent environment is inherited.

Run records expose only these safe assertions:

```text
node_path_present: true
npm_wrapper_path_present: true
child_environment_mode: minimal_allowlist
inherited_environment: false
```

They do not contain the full PATH or child environment.

Fourteen non-invoking safety tests passed before the real attempt. The suite verified the exact minimal PATH composition, absence of unrelated environment keys, no inherited secrets, WindowsApps rejection, Python `shell=false`, the controlled `.cmd` wrapper, fixture-only CWD/output/schema paths, unchanged timeout and flags, and all prior schema/contract safety behavior.

### Exactly one fresh invocation

One fresh invocation was made through `codex_exec_provider.py` using:

```text
cmd.exe /d /s /c "C:\Users\brody\AppData\Roaming\npm\codex.cmd" exec
  --sandbox workspace-write
  --cd <fixture-root>
  --json
  --output-schema <fixture-schema>
  --output-last-message <attempt-output>/strategist_handoff.json
  --ephemeral -
```

Python retained `shell=false`. The child started with both verified path assertions true, proving the prior Node-resolution blocker was corrected. The invocation then exited once, without retry, with code 2 after 109 milliseconds. Sanitized stderr was:

```text
error: unexpected argument 'Obsidian\automation\fixtures\real_codex_fixture_workspace"' found

Usage: codex exec [OPTIONS] [PROMPT]
       codex exec [OPTIONS] <COMMAND> [ARGS]

For more information, try '--help'.
```

This is a Windows `.cmd` argument-quoting failure for the fixture path containing spaces. It occurred during local CLI argument parsing, before transport, model execution, schema output, handoff creation, or tool activity.

### Validation and containment

- Outcome: `BLOCKED`.
- Exit code: 2, non-retryable.
- Run-record validation: `blocked_provider_failure`.
- Output-schema validation: `not-run`.
- Contract validation: not run because no handoff exists.
- Claim-ID validation: not run; no synthetic or other claim IDs were returned.
- Model/version/thread metadata: not reported; thread list empty.
- Publishing enabled: false.
- Real production enabled: false.

The new attempt folder contains only the marker, request record, sanitized run record, empty stdout, and 220-byte stderr. No output was created outside the disposable fixture and its dedicated run-record tree. No unexpected external tool, network, API, media, platform, rendering, download, upload, scheduling, or publishing activity occurred.

### Next prerequisite before Phase C2

C1 remains **BLOCKED**. The one specific prerequisite is a separately reviewed correction to the controlled Windows `.cmd` wrapper quoting so paths containing spaces reach `codex exec` as single arguments, followed by separate authorization for one fresh fixture attempt. Phase C2 must not begin until a real fixture response passes both schema and contract validation.

## Phase C1.2 direct Node provider correction — 2026-07-11

### Narrow npm-shim verification

The verified npm wrapper matched the expected shim format. Its contents were not logged. Safe results:

```text
wrapper_format_valid: true
verified_node_path: C:\Program Files\nodejs\node.exe
js_entry_path_exists: true
js_entry_path_is_under_expected_npm_root: true
normalized_entry_identifier: node_modules/@openai/codex/bin/codex.js
wrapper_js_entry_count: 1
wrapper_node_variable_valid: true
npm_local_node_absent: true
```

The shim's Node variable resolves only through the minimal C1 child PATH to the verified Node executable. The single JavaScript entry is present beneath the exact verified user-level npm root.

### Provider correction

`codex_exec_provider.py` no longer constructs a `cmd.exe /d /s /c` wrapper. It now constructs a Python argument list with separate items:

```text
<node.exe> <codex-entry.js> exec
  --sandbox workspace-write
  --cd <fixture-root>
  --json
  --output-schema <fixture-schema>
  --output-last-message <attempt-output>/strategist_handoff.json
  --ephemeral -
```

The provider enforces the exact verified Node executable, npm root, npm wrapper identity, and Codex JavaScript entry. It rejects `cmd.exe`, PowerShell, WindowsApps, dangerous flags, permission bypasses, and alternate package paths. Each path containing spaces remains one unquoted Python list item. Python `shell=false`, fixture CWD, stdin prompt delivery, explicit timeout, minimal child environment, redaction, and containment checks remain unchanged.

### Local non-network validation

Fourteen tests passed, zero failed. The tests verify direct list construction, exact Node and entry positions, `exec`, workspace-write sandboxing, one-item fixture/schema/handoff paths, ephemeral mode, `shell=false`, prohibited launcher/flag rejection, minimal non-inherited environment, schema/contract behavior, and fixture containment.

The test command did not include `--run-real`. Tests that inspect execution arguments use injected fake runners. Therefore:

- real fixture invocations: 0;
- Codex/Node CLI processes: 0;
- transport/model/network calls: 0;
- MCP/browser/API/external research calls: 0;
- real-case or production access: 0;
- media/download/render/platform actions: 0;
- real-production and publishing enablement: false.

### Current gate

The provider construction correction is complete and locally tested. C1 remains blocked from Phase C2 because this task did not authorize a real fixture invocation. The next prerequisite is separate human authorization for exactly one fresh C1 fixture attempt using this direct Node argument-list path.

## Phase C1 final direct-Node fixture invocation — 2026-07-11

### Authorized execution outcome

The local safety suite passed 14/14 immediately before execution. Exactly one fresh fixture invocation then ran through `codex_exec_provider.py`. No retry occurred.

Safe runtime identity:

```text
node: C:\Program Files\nodejs\node.exe
entry: node_modules/@openai/codex/bin/codex.js
command shape: <node.exe> <codex-entry.js> exec --sandbox workspace-write --cd <fixture-root> --json --output-schema <schema> --output-last-message <attempt-output>/strategist_handoff.json --ephemeral -
shell: false
```

The direct Node process started successfully and created one ephemeral Codex thread. This proves the Node, JavaScript-entry, path-with-spaces, stdin, and transport launch path is operational. The invocation exited with code 1 after 4,640 milliseconds and was recorded as `blocked_provider_failure`.

Sanitized error:

```text
invalid_request_error / invalid_json_schema (HTTP 400)
Invalid schema for response_format 'codex_output_schema':
In context=('properties', 'schema_version'), schema must have a 'type' key.
```

The service rejected the existing fixture output schema before model output. No final handoff was created.

### Validation results

- Output-schema validation: not run locally because no handoff exists.
- Strategist contract validation: not run because no handoff exists.
- Fixture claim validation: not run; no claim IDs were returned.
- Output-hash validation: not run; no output artifact exists.
- Request identity: `glass-harbor-fixture`, `controlled-real-fixture`, and the expected provider ID were recorded.
- Request idempotency key: valid 64-character SHA-256 form.
- Inputs: exactly `batch_size`, `candidate_queue`, and `content_standard`; all three recorded hashes have valid SHA-256 form.
- Publishing permission and recorded publishing state: false.
- Real-production state: false.

### Records and containment

The isolated `output/c1_final_real_agent_run/` tree contains only:

- `REAL_INVOCATION_ATTEMPT.json`;
- the immutable `request.json`;
- `attempt-001/record.json`;
- `attempt-001/stdout.txt` containing sanitized JSONL runtime events;
- `attempt-001/stderr.txt` (empty).

No `strategist_handoff.json`, completion artifact, media artifact, or platform artifact exists. No file was created outside the disposable fixture and approved agent-run tree.

The only external/network activity was the explicitly authorized Codex transport request, which returned the schema-validation HTTP 400. No model output, tool call, MCP, browser, research API, media, download, render, upload, scheduling, publishing, or production activity occurred.

### Current gate before Phase C2

C1 remains **BLOCKED**. The exact next prerequisite is a separately reviewed fixture output-schema correction that supplies a valid JSON Schema `type` for `properties.schema_version` and verifies the complete schema is accepted by the Codex structured-output endpoint. After that correction passes local non-network tests, a new explicit authorization would be required for any further real fixture attempt. Phase C2 must not begin before a real handoff passes both schema and Strategist contract validation.

## Phase C1.3 local schema repair — 2026-07-11

The fixture output schema was repaired and validated locally only. No Codex process or network request was made.

Issues corrected include untyped constant fields, unexpanded object constants, incomplete input-item objects, untyped array items, and the local validator's lack of `anyOf` evaluation. Every property is now explicitly typed. Every object defines properties, requires all declared properties, and disables additional properties. Every array defines typed items. Fixed primitive values use typed singleton enums, and the claim arrays enforce the exact ordered three-item value.

One non-nullable `anyOf` remains necessary for the heterogeneous `batch_size`, `candidate_queue`, and `content_standard` input-record shapes. Each option is fully typed and closed. The local contract validator still requires the handoff inputs to equal the supplied request exactly, preserving their values and hashes.

The offline suite passed 15/15 tests. It confirms:

- JSON parsing and strict compatibility validation pass;
- the known-good fixture handoff passes schema and Strategist contract validation;
- missing `schema_version.type` fails compatibility validation;
- altered claims fail schema validation;
- `publishing_enabled: true` fails schema validation;
- case, viability, score, risk, disposition, empty output/tool arrays, and publishing state remain constrained;
- provider command, containment, environment, timeout, error-recording, and permission regressions still pass without a real process.

Remote structured-output acceptance has not been retested. The next step requires separate authorization for exactly one fresh real C1 fixture invocation. Phase C2 remains blocked until that invocation returns a handoff that passes both schema and contract validation.

## Phase C1 final retry structured-handoff run — 2026-07-11

The offline preflight passed 15/15 tests. Exactly one fresh direct-Node fixture invocation then ran through `codex_exec_provider.py`; no retry occurred.

### Outcome

- Status: `BLOCKED`.
- Exit code: 1, non-retryable.
- Runtime: 2,453 milliseconds.
- Direct Node and transport: passed; one ephemeral thread started.
- Remote schema acceptance: failed before model output.
- Local handoff schema validation: not run because no handoff exists.
- Strategist contract validation: not run because no handoff exists.

Sanitized remote error:

```text
invalid_request_error / invalid_json_schema (HTTP 400)
context=('properties', 'inputs', 'items', 'anyof', '1', 'properties',
'value', 'properties', 'claim_ids')
Unexpected constant value: ['SYN-C1-01', 'SYN-C1-02', 'SYN-C1-03'].
```

The structured-output endpoint accepted the repaired explicit typing far enough to reach the first array-valued `const`, then rejected that construct. No model output or final handoff was created.

### Fixed-field, claim, and hash result

- Request case/mode/provider identity: recorded correctly for the synthetic fixture.
- Request idempotency and input hashes: retained in the immutable request record.
- Handoff claim order, fixed fields, output hashes, empty output/tool arrays, and publishing state: not validated because no handoff exists.
- Recorded publishing state and real-production state: false.

### Records and containment

The isolated `output/c1_final_retry_real_agent_run/` tree contains only the attempt marker, immutable request record, attempt record, sanitized JSONL stdout, and empty stderr. No handoff, completion artifact, media artifact, or platform artifact exists. No file was created outside the approved disposable fixture/run-record tree.

The only network activity was the authorized Codex structured-output request that returned HTTP 400. No model output, tool call, MCP, browser, research API, media, render, upload, scheduling, publishing, or production action occurred.

### Current gate

C1 is **not complete**. The exact next prerequisite is a separately reviewed local schema correction that removes or replaces the unsupported array-valued `const` while preserving exact ordered claim validation through endpoint-supported schema constructs plus the existing local contract/run validation. That correction must pass offline tests. Any additional real fixture invocation requires new explicit authorization. Phase C2 remains blocked.

## Phase C1.4 offline remote-schema normalization — 2026-07-11

The unsupported array-valued claim constants were removed from the remote output schema. Both the result and echoed synthetic candidate input now require three closed, typed scalar fields: `claim_1`, `claim_2`, and `claim_3`, each constrained to its exact ordered synthetic ID.

The original strict canonical schema is retained separately. A Phase C1-only deterministic normalizer validates both remote claim triples, removes the scalar fields, reconstructs `claim_ids` in exact order, then validates the canonical handoff against the strict canonical schema and Strategist contract. It blocks missing, altered, duplicated, reordered, canonical-prepopulated, or extra claims and never repairs an invalid response.

Successful normalization adds these runtime record fields:

```text
remote_output_normalized: true
normalization_kind: fixture_claim_fields_to_claim_ids
```

The remote compatibility checker now rejects array/object-valued const or enum values, tuple-style array items, array cardinality/containment keywords, unsupported composition and conditional keywords, recursive references, pattern/unevaluated properties, nullable type unions, unknown keywords, untyped properties, open objects, and root-level `anyOf`. The one existing nested non-nullable `anyOf` remains for the three heterogeneous input-record shapes.

Seventeen offline tests passed with zero failures. They cover remote-schema compatibility, known-good remote validation, both claim-location normalizations, canonical schema and contract validation, altered/missing/extra claims, legacy array-const rejection, disabled publishing, normalization metadata, provider command invariants, containment, and failure recording.

No real invocation, Codex process, network request, model, tool, MCP, browser, research, media, render, upload, scheduling, publishing, or production action occurred. The next step requires separate authorization for exactly one fresh real C1 fixture invocation. Phase C2 remains blocked until a real normalized handoff passes all validation.

## Phase C1 successful remote-normalized fixture run — 2026-07-11

The offline preflight passed 17/17 tests. Exactly one authorized direct-Node Codex request then ran through `codex_exec_provider.py`; no retry occurred.

### Execution and remote acceptance

- Status: `PASSED`.
- Exit code: 0.
- Runtime: 21,781 milliseconds.
- Remote structured-output schema: accepted.
- Remote schema validation: pass.
- One ephemeral Codex thread; no tool events.

The remote handoff was written only inside the assigned attempt output directory. It contained the exact required `claim_1`, `claim_2`, and `claim_3` values in both applicable synthetic containers and contained no canonical `claim_ids` fields before normalization.

### Normalization and canonical validation

- `remote_output_normalized`: true.
- `normalization_kind`: `fixture_claim_fields_to_claim_ids`.
- Canonical claim order: `SYN-C1-01`, `SYN-C1-02`, `SYN-C1-03`.
- Remote-only claim fields removed from both canonical containers: pass.
- Canonical schema validation: pass.
- Strategist contract validation: pass.
- Run-record validation status: pass, no errors.

### Fixed fields and hashes

- Schema version: `1.0`.
- Case ID: `glass-harbor-fixture`.
- Viability: `Standard long-form viable`.
- Score: 30.
- Risk: `synthetic-none`.
- Disposition: `select`.
- All three input hashes match the immutable request records and have SHA-256 form.
- Outputs: empty.
- Tool calls: empty.
- Result artifact hashes: empty.
- Publishing enabled: false.
- Real production enabled: false.
- Canonical handoff SHA-256: `2512383244b31d5e41b5e48ebc5158a9b3510be63d6a7dd4f21c8cc565614f23`; matches attempt and completion records.

### Records and containment

The dedicated run tree contains the attempt marker, immutable request, completion record, attempt record, sanitized stdout/stderr, remote handoff, and normalized canonical handoff. All artifacts remain beneath `output/c1_remote_normalized_final_run/`. No unexpected file was created outside the approved fixture/run-record tree.

The only external activity was the authorized Codex structured-output request. Runtime events were limited to thread start, turn start, one completed response item, and turn completion. No MCP, browser, research, external API, command/tool call, media, render, upload, scheduling, publishing, or production activity occurred.

### Phase decision

**Phase C1 is formally complete.** The real controlled provider produced a remote-schema-valid response, deterministic fixture normalization succeeded, and the canonical handoff passed both schema and Strategist contract validation with complete containment evidence.

The exact next prerequisite before Phase C2 is human authorization and a scoped implementation plan for the real Research Verifier adapter. C1 fixture permissions do not authorize Phase C2, real-case access, production adapters, research, external tools, or broader filesystem/network scope.
