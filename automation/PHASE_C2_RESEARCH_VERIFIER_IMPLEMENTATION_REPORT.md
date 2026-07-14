# Phase C2 Research Verifier Implementation Report

**Date:** 2026-07-12  
**Scope:** Synthetic Research Verifier implementation and offline validation only  
**Real C2 invocation:** Not authorized and not run  
**Real production:** Disabled

## Synthetic-only fixture

The isolated workspace is `automation/fixtures/real_research_verifier_fixture_workspace/`. It has a separate output tree and contains only:

- an invented Strategist handoff;
- an invented source ledger;
- invented research boundaries;
- fixture-specific remote and canonical schemas;
- a fixture-specific contract and prompt;
- an output README.

The inputs use the fictional case ID `glass-river-research-fixture`, invented record identifiers, future invented dates, and non-routable `example:` locations. They contain no URLs, real people, real institutions, real events, personal data, credentials, media, or production paths. Every input is marked `fixture: true`, and the provider refuses a different case identity or any input outside this fixture root.

## Expected verification result

Approved claims:

- `SYN-RV-01`
- `SYN-RV-02`
- `SYN-RV-03`

Rejected claims and fixed reason codes:

- `SYN-RV-X1` — `unverified_unnamed_allegation`
- `SYN-RV-X2` — `unverified_online_theory`
- `SYN-RV-X3` — `source_ledger_conflict`

The canonical result requires `approved_with_exclusions`, `proceed_to_writer: true`, `required_human_escalation: false`, empty outputs/tools/artifact hashes, and publishing/real-production states of false.

## Remote schema, canonical schema, and contract

The remote schema uses explicit types, closed objects, complete required fields, primitive singleton enums, typed arrays, and no unsupported remote constructs. Claim decisions are represented as ordered scalar fields so the remote endpoint is not asked to emit array-valued constants.

The canonical schema restores strict ordered arrays for approved and rejected claims. The fixture-specific Research Verifier contract requires the three synthetic file inputs, permits only three local comparison/classification actions, declares no side outputs, and stops for human review rather than transitioning to Writer.

## Fixture-only normalization

`c2_fixture_normalization.py` verifies every remote approved claim, rejected claim, and reason code. It rejects missing, altered, duplicated, reordered, or canonical-prepopulated claims. It also verifies three result hashes against the immutable request input descriptors:

```text
synthetic_strategist_handoff SHA-256 -> upstream_strategist_handoff_hash
synthetic_source_ledger SHA-256      -> ledger_hash
synthetic_research_boundaries SHA-256 -> boundaries_hash
```

Only after all checks pass does it construct canonical approved/rejected arrays. The provider then validates the canonical schema, and `AgentRunner` validates the Research Verifier contract and exact input-envelope equality.

Successful future normalization records:

```text
remote_output_normalized: true
normalization_kind: fixture_research_claim_fields_to_canonical_lists
```

## Offline C2 validation

Command:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' automation\test_real_research_verifier_fixture.py
```

Result: **7 passed, 0 failed**. The runner reported `real_invocation: not_requested`.

Coverage includes remote-subset compatibility, canonical schema and contract validation, exact approvals/rejections/reason codes, input hash binding, fixed status flags, empty outputs/tools/artifact hashes, malformed/missing/altered claims, hash mismatch, prohibited external activity declarations, tool declarations, path escape, broader permissions, direct-Node argument construction, `shell=False`, minimal environment, and normalization metadata.

## C1 regression

Command:

```powershell
& 'C:\Users\brody\AppData\Local\Programs\Python\Python311\python.exe' automation\test_real_codex_fixture.py
```

Result: **17 passed, 0 failed**. The runner reported `real_invocation: not_requested`.

C1 direct-Node construction, remote compatibility, deterministic normalization, canonical Strategist validation, containment, permissions, redaction, and failure recording remain intact.

## Containment and blocking conditions

The C2 provider blocks on an incorrect fixture identity, undeclared/missing input, path escape, non-file input, changed input hash, broader permission, malformed remote output, missing/altered claim, changed reason code, incorrect fixed status, nonempty tool/output/artifact declarations, external research/browser/MCP/network declaration, publishing enablement, real-production enablement, unsupported output field, schema failure, contract failure, nonzero provider exit, or absent handoff.

Offline tests used fake in-process runners only. No Node process, Codex process, model request, network request, MCP, browser, external research, API, media, render, upload, scheduling, publishing, or production action occurred.

## Gate before a real C2 fixture run

A real Research Verifier fixture invocation remains prohibited until the human provides a new, explicit, one-time authorization naming `automation/test_real_research_verifier_fixture.py --run-real` and the disposable C2 fixture. That authorization may permit exactly one invocation with no retry. A passing fixture would still not authorize real-case research, browsing, MCP, production adapters, Writer transition, media work, or publishing.

## First authorized real C2 fixture run — 2026-07-12

The offline preflight passed 7/7 tests. Exactly one real direct-Node Research Verifier fixture invocation then ran; no retry occurred.

### Outcome

- Status: `BLOCKED`.
- Exit code: 65, non-retryable.
- Runtime: 20,578 milliseconds.
- Codex request started: yes.
- Remote structured-output schema accepted by the service: yes.
- Remote response created inside the assigned attempt output directory: yes.
- Local remote-schema fields, fixed claims, reason codes, hashes, and safety flags: valid.
- Canonical schema validation: failed.
- Research Verifier contract validation: not run because canonical validation failed.

The remote response approved exactly `SYN-RV-01`, `SYN-RV-02`, and `SYN-RV-03`; rejected exactly `SYN-RV-X1`, `SYN-RV-X2`, and `SYN-RV-X3`; used all required rejection reason codes; repeated all three immutable input hashes correctly; declared empty outputs, tools, and artifact hashes; and kept publishing and real production false.

The sole mismatch was:

```text
$.result.source_conflicts has too many items
```

The remote response returned:

```text
source_conflicts: ["SYN-RV-X3: source_ledger_conflict"]
```

The canonical fixture schema requires `source_conflicts` to be empty. Normalization therefore was not committed, `remote_output_normalized` remained false, and no canonical handoff or completion record was created.

The attempt tree contains only the marker, immutable request, attempt record, sanitized stdout/stderr, and the remote handoff. All remain under `output/c2_real_research_verifier_run/`. The only external activity was the authorized Codex request and response. No tool, MCP, browser, research, external API, media, render, upload, scheduling, publishing, Writer transition, or production action occurred.

Phase C2 is not complete. The next prerequisite is a human-reviewed local decision defining whether the explicitly rejected `SYN-RV-X3` conflict must appear in canonical `source_conflicts` or whether that field must remain empty. Any resulting fixture-only schema/prompt/normalization correction must pass C2 offline tests and C1 regressions. A further real attempt would require a new explicit one-time authorization.

## Phase C2.1 canonical conflict alignment — 2026-07-12

The human fixture decision resolved the internal contradiction: `SYN-RV-X3` is rejected because it conflicts with the supplied ledger, so it must also appear exactly once in canonical `source_conflicts`. It is not merely unsupported material.

The revised canonical expectation is:

```text
source_conflicts:
  ["SYN-RV-X3: source_ledger_conflict"]

unsupported_or_creator_derived_material:
  ["SYN-RV-X1", "SYN-RV-X2"]
```

The canonical schema now enforces both arrays as exact ordered values. The fixture contract explicitly requires the X3 ledger conflict and restricts unsupported material to X1/X2. The prompt states both expected arrays without ambiguity. The normalizer independently rejects empty, changed, duplicated, reordered, extra, or misclassified entries before canonical validation.

The first real C2 response was therefore semantically correct and safely blocked only because the old canonical schema contradicted the fixture boundaries. Its blocked attempt remains immutable and was not retried.

Offline results after correction:

- C2 fixture suite: 8 passed, 0 failed; `real_invocation: not_requested`.
- C1 regression suite: 17 passed, 0 failed; `real_invocation: not_requested`.

No Node or Codex process, model request, network request, API, MCP, browser, external research, media, render, upload, scheduling, publishing, Writer transition, or production action occurred during C2.1. Another real C2 attempt requires separate explicit one-time authorization.

## Final successful real C2 fixture run — 2026-07-12

The C2 offline preflight passed 8/8 tests. Exactly one newly authorized direct-Node Research Verifier request then ran; no retry occurred.

### Execution and validation

- Status: `PASSED`.
- Exit code: 0.
- Runtime: 21,250 milliseconds.
- Remote structured-output schema: accepted.
- Local remote-schema validation: pass.
- Fixture normalization: pass.
- `remote_output_normalized`: true.
- `normalization_kind`: `fixture_research_claim_fields_to_canonical_lists`.
- Canonical schema validation: pass.
- Research Verifier contract validation: pass with no errors.

### Exact canonical result

Approved claims: `SYN-RV-01`, `SYN-RV-02`, `SYN-RV-03`.

Rejected claims:

- `SYN-RV-X1` — `unverified_unnamed_allegation`;
- `SYN-RV-X2` — `unverified_online_theory`;
- `SYN-RV-X3` — `source_ledger_conflict`.

Classification:

```text
source_conflicts:
  ["SYN-RV-X3: source_ledger_conflict"]

unsupported_or_creator_derived_material:
  ["SYN-RV-X1", "SYN-RV-X2"]
```

`verification_status` is `approved_with_exclusions`; `proceed_to_writer` is true; `required_human_escalation` is false. Outputs, tool calls, and artifact hashes are empty. Publishing and real production are false. The adapter did not transition to Writer.

All three canonical input hashes match the immutable request descriptors. Canonical handoff SHA-256 `e714bee319714fb99a75d97ad7ed577d2ffed347fabc6072c973d51f76585c1d` matches both attempt and completion records.

### Containment and external activity

The dedicated run tree contains the marker, immutable request, completion record, attempt record, sanitized stdout/stderr, remote handoff, and normalized canonical handoff. All remain beneath `output/c2_final_research_verifier_run/`.

The only external activity was the single authorized Codex structured request and response. Runtime events were limited to thread/turn lifecycle and one completed response item. There were no tool, MCP, browser, web-research, external-API, media, render, upload, scheduling, publishing, Writer, or production events.

### Phase decision

**Phase C2 is formally complete.** The exact next prerequisite before Phase C3 is a new human authorization and scoped Phase C3 implementation plan. C2 does not authorize a Writer adapter, real-case research, browsing, production tools, broader filesystem access, media work, or publishing.
