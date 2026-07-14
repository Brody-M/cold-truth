# Phase C8f — Offline One-Time Provider Configuration Plan

## Result

C8f implementation and its focused offline validation are complete. The approved bundled project runtime, Python 3.12.13, started without escalation and passed all 12 C8f checks.

The C1-through-C8e regression sequence was then started with the same interpreter. C8e through C3 passed, but C2 failed one of eight checks because the synthetic Research Verifier provider result returned exit code `126` where the test expected `0`. Execution stopped immediately as required, and C1 was not run. No workaround or retry was attempted.

No provider call, network request, configuration read, environment read, authorization artifact, runner, audio, media, or production activity occurred.

## Files and scope

- `automation/c8f_configuration_plan_contract.py` defines a non-executable future configuration-selection contract.
- `automation/test_c8f_configuration_plan_contract.py` defines 12 focused offline checks.
- `automation/fixtures/real_writer_editor_fixture_workspace/narration_preflight/future_c8/README.md` documents both future mechanisms.
- `automation/README.md` documents the C8f phase and offline test command.
- `.gitignore` excludes the exact future private configuration file.

The private configuration file was not created.

## Mutually exclusive future mechanisms

### Option A — process environment injection

The later human-configured runner may use only these exact placeholder names:

- `COLD_TRUTH_C8_PROVIDER_API_CREDENTIAL`
- `COLD_TRUTH_C8_LOCKED_VOICE_IDENTIFIER`

The future source may not enumerate the environment, use generic environment access, try alternate names, or request additional values.

### Option B — dedicated ignored local JSON

The later human may create exactly:

`automation/private/c8_one_time_provider_config.json`

It may contain only:

- `provider_api_credential`
- `locked_voice_identifier`

The future source may not list directories, discover configuration, follow references, try fallback paths, use alternate files, or modify the file.

Option A and Option B are not active in C8f. A later C8 authorization must select exactly one; selecting neither or both fails closed.

## Fail-closed configuration rules

The ordered conceptual slot request must be exactly:

1. `provider_api_credential`
2. `locked_voice_identifier`

Empty, partial, reordered, wildcard, arbitrary, traversal-like, additional, and unknown requests fail. A future source remains unavailable unless a valid future C8 authorization selects the mechanism and the runner identity is exactly `c8_one_time_isolated_provider_runner`.

## Redaction and value containment

Raw values may only pass directly to the single authorized transport inside the future one-time runner boundary. Printing, logging, serialization, hashing, returning, reporting, auditing, exception inclusion, test-output inclusion, export, validation, and copying are prohibited.

C8f contains no environment/configuration reader, live client, HTTP or network library, provider SDK, endpoint, authorization instance, runner implementation, or output writer.

## Offline validation status

Selected interpreter:

`C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

Version: Python 3.12.13

C8f command:

```powershell
& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B automation\test_c8f_configuration_plan_contract.py
```

Result: **12/12 passed**. The suite reported `real_invocation: not_requested`, `environment_access: not_performed`, and `configuration_file_access: not_performed`.

Regression results reached before the required stop:

- C8e: 12/12 passed.
- C8d: 12/12 passed.
- C8c: 16/16 passed.
- C8b: 12/12 passed.
- C8a: 15/15 passed.
- C7: 19/19 passed.
- C6: 18/18 passed.
- C5: 16/16 passed.
- C4: 18/18 passed.
- C3: 6/6 passed.
- C2: 7/8 passed; `test_provider_uses_direct_node_and_records_normalization` failed because `result.exit_code` was `126`, not `0`.
- C1: not run because execution stopped at the C2 failure.

No combined C1-through-C8f total is claimed. The last fully verified C1-through-C8e baseline remains 169/169 from the prior phase; this recovery run did not complete that entire regression chain.

## Preserved state

C3 remains `AWAITING_SCRIPT_APPROVAL`. No C4 approval was created or consumed. Publishing and real production remain disabled. Existing C8 controls, isolated fixture boundaries, Mia profile, output format, one-request limit, and all no-retry/no-child-process/no-production restrictions remain unchanged.

## Remaining human action

The C2 regression failure must be reviewed under a separately authorized diagnostic task before the complete regression chain can be certified. Only after all regressions pass is the next C8f human decision Option A or Option B for a separately authorized future live C8 attempt.
