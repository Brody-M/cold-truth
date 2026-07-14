# Phase L7B — Executable L8 Authorization Alignment Report

Date: 2026-07-13  
Scope: offline authorization-contract repair and tests only.

## Result

L7B adds a separate, pure in-memory L8 executable synthetic-authorization
shape validator and future-runner candidate factory. The existing L7A
fake-fixture validator remains unchanged: it is fake-only, non-executable,
non-consumable, and cannot persist a live authorization.

The only permitted L8 purpose is `synthetic_local_connectivity_test`. The
contract rejects raw text, C3/C4 linkage, real-narration purposes, unknown
fields, identity mismatches, limits above the locked one-attempt values,
unsafe output semantics, malformed/expired/reused IDs or nonces, and all
lifecycle states other than `AUTHORIZED_NOT_EXECUTED` at preflight.

## Fixed future locations

- Output root: `C:\ColdTruthLocalTools\piper-l8a-synthetic-connectivity-tests`
- Output file: `l8_piper_synthetic_test.wav`
- Authorization root: `C:\ColdTruthLocalTools\piper-l8a-synthetic-authorizations`
- Audit root: `C:\ColdTruthLocalTools\piper-l8a-synthetic-authorization-audit`

The legacy proposed output root `C:\ColdTruthLocalTools\piper-l8-synthetic-test`
is rejected. The contract fixes the external authorization and audit roots,
requires exclusive creation, and requires the output root and target to be
absent; it does not inspect or create any of those locations in L7B.

## Verification

Executed offline only:

```text
C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe automation\test_l7_piper_synthetic_authorization_contract.py
```

Result: `23` test methods passed. The runner reported zero Piper/ONNX imports,
runtime processes, model loads, text inputs, inference or synthesis calls,
audio/media artifacts, output directories/files, network/provider activity,
executable authorizations created, and authorizations consumed.

## Explicitly not authorized or performed

L7B did not authorize or execute L8. It created no authorization, audit record,
output directory, WAV, Piper process, model load, text input, synthesis, or
production action. C3 remains `AWAITING_SCRIPT_APPROVAL`; no C4 artifact was
created or consumed. Publishing and production remain disabled.
