# Phase C4 — Synthetic Human Script-Approval Gate Report

## Result

Phase C4 implementation and offline validation passed. The synthetic C3 chain remains unchanged at `AWAITING_SCRIPT_APPROVAL`. No approval decision was inferred from an agent handoff and no real provider process was started.

## Fixture boundary

The gate operates only within `automation/fixtures/real_writer_editor_fixture_workspace/`. Approval schemas are in its `approval_gate/` directory, and submitted decision records are confined to `output/c4_script_approval_gate/decision_records/` (or an equally contained fixture-output path used by offline tests). A path outside the fixture or its output tree blocks processing.

## Human-decision artifacts

Approval and rejection are separate, strict, closed schemas. Both require:

- schema, approval, case, timestamp, human-reviewer, and note fields;
- the exact SHA-256 hashes of the C3 Writer and Editor handoff files;
- the SHA-256 hash of the exact Writer `result.narration_text` UTF-8 bytes;
- false narration, asset, rendering, publishing, and real-production flags.

Approval additionally requires `decision: approve` and `permitted_next_stage: narration_preflight_only`. That stage changes state only to `SCRIPT_APPROVED_FOR_PREFLIGHT`; it does not authorize narration generation.

Rejection additionally requires `decision: reject`, one of the four locked rejection reason codes, and `required_return_stage: WRITER_REVISION_REQUIRED`. It cannot advance to Editor, narration, assets, assembly, render, or publishing.

Current synthetic binding values at implementation time:

- Writer handoff SHA-256: `fa74fa01838651b8e893159c1c689e443588a3b3cfb2db553aae1f27506db1fb`
- Editor handoff SHA-256: `b7a52f22457d427f9a2666ea3a949ed35f8ff9511073897fab793beb4df30ec7`

The script hash is calculated independently from the exact narration text, so a changed script invalidates an otherwise matching decision. The implementation recalculates all three bindings at evaluation time rather than trusting stored or agent-supplied values.

## State transitions

- `AWAITING_SCRIPT_APPROVAL` + valid approval → `SCRIPT_APPROVED_FOR_PREFLIGHT`
- `AWAITING_SCRIPT_APPROVAL` + valid rejection → `WRITER_REVISION_REQUIRED`
- Missing artifact → state remains `AWAITING_SCRIPT_APPROVAL`
- Invalid source state, artifact, reviewer, hash, decision, permission, stage, replay, or path → `BLOCKED`

Every submitted, non-replayed decision receives a sanitized immutable JSON record containing its artifact hash and evaluation result. A previously recorded `approval_id` cannot be reused, including with changed content.

## Offline tests

`automation/test_script_approval_gate.py` passed 18/18 tests:

1. valid approval reaches preflight only;
2. all production permission fields remain false;
3. valid rejection returns only to Writer revision;
4. missing artifact preserves the awaiting state;
5. Editor-hash mismatch blocks;
6. Writer-hash mismatch blocks;
7. case mismatch blocks;
8. script-hash mismatch blocks;
9. missing or agent reviewer blocks;
10. invalid decision or next stage blocks;
11. narration authorization blocks;
12. asset, rendering, publishing, or real-production authorization blocks;
13. rejection to a forward stage blocks;
14. replayed approval ID blocks;
15. a changed C3 Writer handoff invalidates an earlier approval;
16. path escape blocks;
17. both schemas pass strict local compatibility validation;
18. immutable records show no process or external capability invocation.

Regression results:

- C3 Writer/Editor offline suite: 6/6 passed; real invocation not requested.
- C2 Research Verifier offline suite: 8/8 passed; real invocation not requested.
- C1 provider safety suite: 17/17 passed; real invocation not requested.
- Total C4 plus regression checks: 49/49 passed.

## Prohibited activity confirmation

No Node or Codex process, provider request, model call, network access, MCP, browser, research, external API, narration, media generation, asset sourcing, alignment, assembly, rendering, download, upload, scheduling, publishing, real case, production adapter, or real-production action occurred. All guarded permission flags remain false.

## Next prerequisite

Before any Phase C5 work, the human owner must separately review and authorize a scoped narration-preflight design. C4 approval semantics do not authorize narration generation or any production activity.
