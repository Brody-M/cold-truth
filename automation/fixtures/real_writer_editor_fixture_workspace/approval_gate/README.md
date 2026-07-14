# Phase C4 synthetic human script-approval gate

This directory defines the separate human-owned approval and rejection artifacts for the invented C3 fixture. Agent handoffs cannot grant approval.

An approval is bound to the SHA-256 hashes of the exact Writer handoff, Editor handoff, and Writer `result.narration_text`. It advances only from `AWAITING_SCRIPT_APPROVAL` to `SCRIPT_APPROVED_FOR_PREFLIGHT`. The permitted next stage, `narration_preflight_only`, authorizes validation/preflight design only; it does not authorize narration generation or any later production activity.

A rejection is bound to the same three hashes and returns only to `WRITER_REVISION_REQUIRED`. Submitted decisions receive an immutable, sanitized record under the fixture `output/c4_script_approval_gate/decision_records/` tree. Reusing an approval ID is blocked.

All narration, asset, rendering, publishing, and real-production flags must remain false.
