# Cold Truth Phase C1 CLI Diagnostic

**Date:** 2026-07-11  
**Workspace:** disposable Phase C1 fixture only  
**Original PowerShell outcome:** BLOCKED — WindowsApps executable could not start  
**Superseding normal-CMD preflight:** npm CLI resolved and passed version/help  
**Controlled fixture outcome:** BLOCKED — npm wrapper could not resolve Node in the minimal child environment

## Commands executed

All commands ran with the process working directory set to:

`automation/fixtures/real_codex_fixture_workspace/`

### 1. Command discovery

```powershell
Get-Command codex -All
```

Result: two applications were returned, in this resolution order:

1. `codex.exe`
2. `codex`

### 2. PATH resolution

```powershell
where.exe codex
```

Result:

```text
C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources\codex
C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources\codex.exe
```

### 3. Alias check

```powershell
Get-Alias codex -ErrorAction SilentlyContinue
```

Result: exit code 1 with no output. No `codex` alias exists.

### 4. Exact command type and path

```powershell
Get-Command codex -All | Format-List CommandType,Name,Source,Path,Definition
```

Result:

```text
CommandType: Application
Name: codex.exe
Path: C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources\codex.exe

CommandType: Application
Name: codex
Path: C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources\codex
```

PowerShell normal command resolution selects `codex.exe`, the first application returned by `Get-Command codex -All`.

### 5. Selected executable version check

```powershell
& 'C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources\codex.exe' --version
```

Result: exit code 1. Safe error output:

```text
Program 'codex.exe' failed to run: Access is denied
CategoryInfo: ResourceUnavailable
FullyQualifiedErrorId: NativeCommandFailed
```

## Checks intentionally not executed

The instructions require an immediate stop when CLI execution remains blocked by `Access is denied`. Therefore these were not run:

- `codex.exe exec --help`;
- the extensionless sibling executable;
- any Codex diagnostic/report subcommand;
- `automation/test_real_codex_fixture.py --run-real`;
- any login, update, reinstall, alias, PATH, registry, or permission operation.

## Usability decision

**The installed CLI is not currently usable by `codex_exec_provider.py`.** Windows denies process creation before Codex can report a version, parse flags, authenticate, or create a run record.

The provider, schema, contract, and fixture remain unchanged. No runtime-command environment value was set.

## Minimal next action

Restore ordinary execute access to the packaged Codex CLI—or provide an officially installed Codex CLI path that can run from a normal PowerShell process—then verify both of these read-only checks return successfully:

```text
codex --version
codex exec --help
```

Only after both checks pass should a fresh session receive authorization for exactly one C1 fixture invocation. Do not connect the real Research Verifier before that fixture produces a schema-valid and contract-valid handoff.

## Superseding npm CLI diagnostic and controlled attempt

The user later supplied a successful preflight from a normal CMD window:

```text
where.exe codex
  C:\Users\brody\AppData\Roaming\npm\codex
  C:\Users\brody\AppData\Roaming\npm\codex.cmd

codex --version
  codex-cli 0.144.0

codex exec --help
  succeeded
```

This changes the earlier conclusion: the Codex CLI installation is usable from the normal CMD environment, and the WindowsApps path must not be used.

The one authorized provider attempt used exactly:

`C:\Users\brody\AppData\Roaming\npm\codex.cmd`

through a `cmd.exe /d /s /c` compatibility wrapper with Python `shell=false`. The wrapper began but exited with code 1 because the provider's intentionally minimal child environment does not inherit `PATH`, so `codex.cmd` could not resolve `node`.

No retry was attempted. The new minimal prerequisite is not a CLI reinstall or PATH change: it is a separately authorized, narrowly scoped provider change that exposes only the existing Node executable location to this child process without inheriting the full parent environment. C1 must then be reauthorized and passed before Phase C2.

## Phase C1.1 factual update

The scoped Node checks confirmed `C:\Program Files\nodejs\node.exe` (`v24.15.0`) and the npm wrapper directory. The provider's minimal allowlist now gives the child only the verified Node parent, npm wrapper directory, required Windows process variables, and fixture-local temporary directories. Fourteen safety tests passed.

The single fresh fixture attempt confirms that the npm wrapper can now resolve Node. It then stopped during local CLI argument parsing with exit code 2 because the controlled `cmd.exe /d /s /c` command did not preserve the fixture path containing spaces as one `--cd` argument. No handoff, transport/model metadata, or tool activity occurred, and no retry was made.

The CLI installation remains usable, but the controlled provider is not yet usable for fixture execution. The next prerequisite is a separately reviewed `.cmd` wrapper quoting correction and a separately authorized fresh fixture attempt. C1 remains blocked before Phase C2.

## Phase C1.2 factual update

The npm shim was narrowly validated without logging its contents. It references one existing Codex JavaScript entry beneath the verified user-level npm root, and its Node variable resolves through the minimal child PATH to `C:\Program Files\nodejs\node.exe`.

The controlled provider no longer uses `cmd.exe`; it now builds a direct Python argument list beginning with `<node.exe> <codex-entry.js> exec`. Fourteen local non-network tests passed. No real Codex process or fixture invocation was authorized or launched.

The provider's command-construction blocker is corrected, but end-to-end C1 remains unproven. The next prerequisite before Phase C2 is separate authorization for one fresh controlled fixture attempt and successful schema/contract validation of its handoff.

## Phase C1 final factual update

The single authorized direct-Node fixture invocation started successfully, created one ephemeral Codex thread, and reached the structured-output service. The direct launch and path-with-spaces issues are resolved.

The request was rejected before model output with HTTP 400 `invalid_json_schema`: the fixture schema's `properties.schema_version` definition lacks the `type` required by the Codex structured-output endpoint. Exit code was 1; runtime was 4,640 milliseconds; no handoff was created and no retry occurred.

The CLI and controlled provider launch path are usable. End-to-end C1 is now blocked specifically on fixture output-schema compatibility. A separately reviewed schema correction and local validation are required before any separately authorized future real attempt or Phase C2 work.

## Phase C1.3 factual update

The fixture schema compatibility defect has been repaired locally. All fields are explicitly typed; object and array schemas are strict and recursive; and the local validator now checks the necessary heterogeneous-input `anyOf` branches. Fifteen offline tests passed.

No CLI or network call was made, so remote schema acceptance remains unverified. The next prerequisite is separate authorization for exactly one fresh controlled C1 fixture invocation. Phase C2 remains blocked until a returned handoff passes both schema and contract validation.

## Phase C1 final retry factual update

The one authorized direct-Node retry reached the structured-output endpoint and was blocked before model output with HTTP 400 `invalid_json_schema`. Explicit property typing passed the earlier failure point, but the endpoint rejected the array-valued `const` used for the synthetic claim list as an unexpected constant value.

Exit code was 1 and runtime was 2,453 milliseconds. No handoff was created and no retry occurred. The CLI/provider transport path remains operational; C1 is now blocked specifically on replacing the unsupported array constant without weakening exact claim validation. Phase C2 remains blocked.

## Phase C1.4 factual update

The unsupported remote array constant has been replaced locally with three typed scalar claim fields and a deterministic fixture-only normalization layer. The direct-Node launch command and environment are unchanged. Seventeen offline tests passed; no CLI or network request was made.

Remote acceptance of the normalized schema remains unverified. The next prerequisite is separate authorization for exactly one fresh controlled C1 fixture invocation. Phase C2 remains blocked until its normalized handoff passes the canonical schema and Strategist contract.

## Phase C1 successful completion

The single authorized remote-normalized fixture invocation passed with exit code 0 in 21,781 milliseconds. The direct-Node CLI path, remote structured-output schema, fixture-only normalization, canonical schema, and Strategist contract all validated successfully. The handoff and immutable records remained contained under the dedicated fixture run tree.

Phase C1 is formally complete. The next prerequisite is separate human authorization and a scoped Phase C2 plan for the real Research Verifier adapter; no C1 permission carries forward automatically.
