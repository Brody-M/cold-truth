# Cold Truth — H6 Episode Identity Binding Certification Report

## Result

`H6 REGRESSION-CERTIFIED — 65/65 PASSED`

H6 establishes one stable `episode_id` across the certified synthetic control plane. The same normalized identity is now bound to persistent run state, the manifest, every orchestrator audit event, the canonical status view, both human-approval checkpoints, approval-consumption records, agent request/idempotency envelopes, agent attempt/completion records, and validated handoffs.

## Certified identity behavior

- A `CaseQueueOrchestrator` receives an explicit normalized `episode_id` or deterministically derives `episode-{normalized_run_id}` once at construction.
- Resuming a persisted run under a different episode identity fails closed.
- Manifest or event identity substitution fails closed before progression.
- Every emitted event carries the exact `run_id` and `episode_id` pair and is checked during chain verification.
- Status and checkpoint packets expose the same stable episode identity.
- Human approvals must match the exact episode identity before consumption; a mismatch creates no consumption record.
- Successful one-time approval consumption preserves the exact episode identity in its safe durable record.
- Agent idempotency keys include the episode identity, so two episodes cannot alias the same run-stage request.
- Agent handoffs must echo the request episode identity; mismatch fails contract validation.
- Common handoff, human approval, and status schemas require a nonempty `episode_id`.

## Exact validation invocations and results

All commands ran once from `C:\Youtube Automation Obsidian\automation` using the bundled offline Python runtime, in the order shown.

1. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_episode_identity.py`
   - Exit code: `0`
   - Result: `8/8` passed
2. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_legacy_pipeline_quarantine.py`
   - Exit code: `0`
   - Result: `10/10` passed
3. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_status_view.py`
   - Exit code: `0`
   - Result: `7/7` passed
4. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_artifact_invalidation.py`
   - Exit code: `0`
   - Result: `7/7` passed
5. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_audit_event_chain.py`
   - Exit code: `0`
   - Result: `6/6` passed
6. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_human_approval_lifecycle.py`
   - Exit code: `0`
   - Result: `12/12` passed
7. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_orchestrator.py`
   - Exit code: `0`
   - Result: `6/6` passed
8. `& 'C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B .\test_agent_runtime_orchestration.py`
   - Exit code: `0`
   - Result: `9/9` passed

Combined result: `65/65` passed.

No suite failed, no nonzero exit occurred, and no retry, fallback, alternate harness, or second invocation was used. No L7/L8 or provider suite ran.

## Certified implementation hashes

- `automation/agent_runner.py`: `5D91A7C2C7D339644F333686B176EE1008F885AE034E312607034F588E6B1027`
- `automation/fixtures/simulated_agents/mock_runtime.py`: `83F77EADF8392870ABD4AD69B2227E5D00D9940C9147B759417581832FDDCF6F`
- `automation/handoff_validator.py`: `E4F663A1EF2A7BDAEE069AE11045F53B2FC76C021513010D508F262562394E2E`
- `automation/human_approval_lifecycle.py`: `B50BFBCD9C89A711E75C0E5C1E843C81A86F177ACCD1E819D4B767D9C4806C8B`
- `automation/status_view.py`: `DD3D67F558B87299D7925AFCF2F6558E2CB8D362899BF275BB02256BB304B326`
- `automation/orchestrator.py`: `669934FF069D6850BEF94E5604F98750AE944E9462B39D6B2C7D7B44634551D2`
- `automation/contracts/common_handoff.schema.json`: `F347C36C2C4F508D9C6AE332EEB120E7EE43BFE2864611635D9F340CE7EF258D`
- `automation/contracts/human_approval.schema.json`: `0468096F0DB7B3C25B4D604AA92734E2B786156B1FE7DFF194B74E43CB0210B7`
- `automation/contracts/status_view.schema.json`: `88B28F3A77FEA72F37E2BAACFAF95DF8EAEC96FE8C1C66772C18109FE0C8FD76`
- `automation/test_episode_identity.py`: `FDB30CCB7B975B05897307B5115CA4B9F9E6E8051521FB5622DD1B35A5CCB17E`
- `automation/test_human_approval_lifecycle.py`: `D560B28C8322D9ADABEEC16D200845BB7F866A0399FFEC337B99945800536079`
- `automation/test_orchestrator.py`: `34FE73EF4E1C6B323028238C5B43C5721FAF9FC1E3088992238DBE7F35DC3170`
- `automation/test_agent_runtime_orchestration.py`: `6AE5F505D34CD8E8F1162AFF53CFA267CCF85453A301337F41F8240A64E8AC60`
- `automation/test_status_view.py`: `0D81F2B8DAB93266BE9EFD19F1373AE7C8D82EBD1FE3610061B981AA0C4F1737`

## Files changed

- `automation/agent_runner.py`
- `automation/fixtures/simulated_agents/mock_runtime.py`
- `automation/handoff_validator.py`
- `automation/human_approval_lifecycle.py`
- `automation/status_view.py`
- `automation/orchestrator.py`
- `automation/contracts/common_handoff.schema.json`
- `automation/contracts/human_approval.schema.json`
- `automation/contracts/status_view.schema.json`
- `automation/test_episode_identity.py`
- `automation/test_human_approval_lifecycle.py`
- `automation/test_orchestrator.py`
- `automation/test_agent_runtime_orchestration.py`
- `automation/test_status_view.py`
- `automation/PHASE_H6_EPISODE_IDENTITY_BINDING_REPORT.md`

This workspace has no Git repository metadata, so the inventory is based on the scoped H6 edits and the observed test run. No L7/L8 implementation, provider adapter, runtime asset, dependency, configuration, real-case material, account, media, or production file was changed.

## Safety confirmation

All tests used synthetic fixtures and temporary roots that were cleaned afterward. No real case entered the orchestration path. No provider or network call, external command, account action, environment-secret access, or production mutation occurred.

No L7/L8 authorization was created, validated, inspected, persisted, consumed, reset, or executed. No Piper/ONNX import, sealed interpreter, model load, text handoff to a model, inference, synthesis, audio/media creation, C3/C4 access, rendering, upload, scheduling, publishing, or production change occurred.

C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 approval was created or consumed. L8 remains blocked. Real production and publishing remain disabled.

## Stop

`H6 REGRESSION-CERTIFIED — STABLE EPISODE IDENTITY IS BOUND END TO END`

This certification authorizes no subsequent hardening slice, L8 action, provider execution, media generation, or production action.
