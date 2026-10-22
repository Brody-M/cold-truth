# Testing guide

## Scope

Cold Truth’s automated checks are designed to be safe to run locally. They exercise synthetic fixtures, contracts, state transitions, identity binding, and capability restrictions. They do not generate final media, publish, schedule, or intentionally invoke a live production provider.

Run commands from the repository root. Use the Python runtime that is available in your environment.

## Fast confidence checks

```powershell
python -B automation/test_orchestrator.py
python -B automation/test_agent_runtime_orchestration.py
python -B automation/test_track_isolation.py
python -B automation/test_script_approval_gate.py
python -B automation/test_narration_preflight_gate.py
```

These cover state-machine behavior, synthetic agent handoffs, visual-track separation, and fixture script/pre-generation approval rules. `test_narration_preflight_gate.py` is a synthetic request gate; it does not measure real audio with FFprobe or certify a real episode's runtime. Passing these modules is not complete production certification.

## Direct pilot evidence checks

`python -B automation/test_pilot_evidence.py` exercises the separate direct-route checker with disposable byte fixtures and mocked probes. It covers paired-input binding, unrounded 480/60 boundaries, exceptions, probe failures/timeouts, stale inputs, real-file rights evidence, visual separation and the JSON/SRT alignment interface. It never calls a provider or generates/decodes media. `automation/pilot_evidence.py --help` lists validation commands; see the [Amy runbook](<../Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/Pilot_Runbook.md>) for receipt formats and operator responsibilities. These checks do not enable the orchestrator or certify real media.

On Windows, if the sandbox's default temporary directory is unavailable, run unittest with a process-local `tempfile.tempdir` inside a newly created disposable workspace directory. Validate its resolved parent before cleanup; do not change global TEMP settings.

## Vault navigation

```powershell
python -B automation/test_vault_audit.py
python -B automation/vault_audit.py --strict --output docs/vault_audit.json
```

The audit checks local file targets, duplicate basenames, disconnected notes, native canvas references and forward reachability from `00_START_HERE.md`. `--strict` fails when a note links back to a hub but cannot be reached by following links from Home. It excludes code examples, personal notes, credential notes and hidden plugin content. It does not verify external sources, heading anchors, media rights or human approvals. `docs/vault_audit_before.json` preserves the September baseline; dated October before/after reports are retained separately.

## Broader regression suite

The repository keeps independent test modules so a focused change can be validated close to its boundary:

| Change area | Start with |
| --- | --- |
| Contracts and runtime handoffs | `automation/test_agent_runtime_orchestration.py` |
| Audit or status behavior | `automation/test_audit_event_chain.py`, `automation/test_status_view.py` |
| Approval or invalidation rules | `automation/test_human_approval_lifecycle.py`, `automation/test_artifact_invalidation.py` |
| Narration safety boundaries | `automation/test_synthetic_narration_adapter.py`, `automation/test_narration_provider_adapter.py` |
| Isolated provider contracts | `automation/test_c8_isolated_provider_execution_adapter.py` and `automation/test_c8*.py` |
| Local TTS contract adapters | `automation/test_k1_kokoro_local_adapter_contract.py`, `automation/test_l2_piper_local_adapter_contract.py` |
| One-time Piper authorization flow | `automation/test_l7_piper_synthetic_authorization_contract.py`, `automation/test_l8_one_time_piper_synthetic_runner.py` |

`automation/README.md` contains phase-specific commands and the historical rationale for each boundary.

## Read-only readiness check

To inspect local runtime readiness without requesting a provider call:

```powershell
python automation/runtime_readiness_check.py
```

The check is intended to avoid printing sensitive command values or secrets. Do not alter production settings merely to make it pass.

## Linting

This repository currently has no committed lint-tool configuration or dependency manifest. The documentation change is validated with a Markdown structure check, and the available Python regression modules are run directly. If a formatter or linter is introduced later, pin its configuration and document the command before making it required in CI.

## Interpreting failures

Treat a failed safety check as a block, not an invitation to bypass the guardrail. In particular:

- Do not edit immutable attempt records to force a transition.
- Do not loosen a contract simply to accept malformed output.
- Do not use a synthetic test pass as authority for real-case or production work.
- Do not add secrets or credentials to make a local adapter runnable.

Fix the input, implementation, or explicitly authorized configuration change, then rerun the relevant test.
