# Cold Truth Approval and Escalation Templates

> **BLANK, REUSABLE, NON-AUTHORIZING TEMPLATES**

Version: `1.0`  
Controlling references: [[COLD_TRUTH_MASTER_EXECUTION_PLAN|Master Execution Plan]], [[CONTENT_FORMAT_STANDARD|Content Format Standard]], [[COLD_TRUTH_EXECUTION_STATE.json|Execution State]], [[COLD_TRUTH_BRAND_GOVERNANCE_KIT|Brand and Governance Kit]], [[COLD_TRUTH_EDITORIAL_GOVERNANCE_CHECKLIST|Editorial Governance Checklist]]

These structures define required fields only. They are not approval records, cannot be consumed, and must never be copied into an active location with prefilled approval values. Every real approval requires a separate explicit human-owner decision bound to exact current inputs.

## Template A — C3 paired script-approval request and review

Template status: `BLANK_NON_AUTHORIZING`

### Request identity

- Schema/version: `[BLANK]`
- Approval request ID: `[BLANK]`
- Purpose: `paired_script_review`
- Run ID: `[BLANK]`
- Case ID: `[BLANK]`
- Episode ID: `[BLANK]`
- Current prerequisite state: `[BLANK]`
- Requested only next state: `[BLANK]`

### Exact reviewed inputs

- Vetted source-ledger path/SHA-256: `[BLANK]`
- Reverse-outline path/SHA-256: `[BLANK]`
- Full-draft path/SHA-256: `[BLANK]`
- Narrative-QA path/SHA-256: `[BLANK]`
- Editorial exclusions path/SHA-256: `[BLANK]`
- Viability decision and exception binding: `[BLANK]`

### Human review

- Reviewer: `[BLANK — HUMAN OWNER ONLY]`
- Decision: `[BLANK — APPROVE / REJECT / REVISE / ESCALATE]`
- Decision reason: `[BLANK]`
- Required changes/exclusions: `[BLANK]`
- Issued date/time: `[BLANK]`
- Expiry, if applicable: `[BLANK]`
- Exact approved hashes repeated by reviewer: `[BLANK]`
- Single use: `[BLANK]`
- Consumption state/count: `[BLANK]`
- Publishing enabled: `false`
- Real production enabled: `false`

C3 approves only the exact reverse outline and full draft together for canonical script creation. It does not authorize C4, narration, playback, providers, sourcing, media, assembly, rendering, upload, scheduling, or publishing.

## Template B — C4 exact narration-approval request and review

Template status: `BLANK_NON_AUTHORIZING`

### Request identity and prerequisite

- Schema/version: `[BLANK]`
- Approval request ID: `[BLANK]`
- Purpose: `exact_narration_generation_review`
- Run/case/episode ID: `[BLANK]`
- Valid consumed C3 approval ID/path/SHA-256: `[BLANK]`
- Script_Final canonical path/SHA-256/size: `[BLANK]`
- Target format: `[BLANK — youtube-longform OR shorts]`

### Exact execution binding

- Provider ID: `[BLANK]`
- Model ID/version: `[BLANK]`
- Voice ID/version: `[BLANK]`
- Language and settings: `[BLANK]`
- Output format: `[BLANK]`
- Canonical output root/path: `[BLANK]`
- Total attempt budget: `[BLANK — INTEGER 1 TO 3]`
- Provider fallback: `false`
- Alternate model/voice/provider/path/format allowed: `false`
- Retry rule: `only provider-declared retryable failure with unused approved budget`
- Text handoff count and exact-script rule: `[BLANK]`
- Required audit/QA outputs: `[BLANK]`

### Human review

- Reviewer: `[BLANK — HUMAN OWNER ONLY]`
- Decision: `[BLANK — APPROVE / REJECT / REVISE / ESCALATE]`
- Decision reason: `[BLANK]`
- Issued date/time and expiry: `[BLANK]`
- Single-use and consumption fields: `[BLANK]`
- Publishing enabled: `false`
- Real production enabled: `false`

C4 authorizes only the exact stated narration request when every prerequisite and binding matches. It does not authorize fallback, extra attempts, audio listening/QA beyond its explicit scope, visuals, sourcing, assembly, render, upload, scheduling, publishing, or future episodes.

## Template C — Correction or escalation decision record

Template status: `BLANK_NON_AUTHORIZING`

- Record ID/version: `[BLANK]`
- Intake date/time: `[BLANK]`
- Reporter/claimant minimum necessary identity: `[BLANK]`
- Issue class: `[BLANK — FACT / PRIVACY / SAFETY / LEGAL / COPYRIGHT / IDENTITY / OTHER]`
- Affected episode/artifact/platform item: `[BLANK]`
- Exact affected path/SHA-256/timestamp or statement: `[BLANK]`
- Evidence supplied and provenance: `[BLANK]`
- Immediate hold required: `[BLANK — NO ACTION WITHOUT AUTHORITY]`
- Source-ledger and rights-record comparison: `[BLANK]`
- Risk assessment and qualified-review requirement: `[BLANK]`
- Downstream artifacts/approvals to invalidate: `[BLANK]`
- Decision class: `[BLANK]`
- Decision rationale: `[BLANK]`
- Human-owner approval ID for corrective/platform action: `[BLANK]`
- Exact allowed corrective action: `[BLANK]`
- Public correction language, if separately approved: `[BLANK]`
- Previous version preserved as audit-only: `[BLANK]`
- Completion evidence/path/hash: `[BLANK]`
- Exact next allowed action: `[BLANK]`

This record does not authorize contact, takedown, deletion, dispute, counter-notice, edit, upload, or republication.

## Template D — Episode-level definition-of-done checklist

Template status: `BLANK_NON_AUTHORIZING`

### Identity and governance

- [ ] Stable case, episode, run, and Short IDs are recorded.
- [ ] Production Summary and append-only manifest are current.
- [ ] No active artifact is stale, audit-only, ambiguous, or outside its canonical root.

### Research and editorial

- [ ] Vetted claim-level source ledger and research verification pass.
- [ ] Viability records one allowed result; any exception is explicit and current.
- [ ] Reverse outline and full draft form one coherent, respectful story.
- [ ] C3 binds and approves both exact hashes; Script_Final matches exactly.

### Narration and timing

- [ ] C4 binds exact script/provider/model/voice/settings/path/attempt budget with no fallback.
- [ ] Narration manifest and exact-script QA pass.
- [ ] Long-form audio is at least `480.000` seconds or has a valid exception.
- [ ] Each Short is within 30–60 seconds or has its own valid exception.
- [ ] Preflight and alignment bind exact current script/audio.

### Visual tracks and rights

- [ ] Long-form manifest uses `youtube-longform` with only `case_broll`/`case_graphic`.
- [ ] Shorts manifest uses `shorts` with only separately licensed `orbital_gameplay`.
- [ ] H8 confirms zero collision by asset ID, source identity, content SHA-256, and canonical path.
- [ ] Every active asset has complete source, license, credit, canonical path, hash, and track records.

### Assembly, packaging, and release

- [ ] Exact-input assemblies and whole-edit creative reviews pass.
- [ ] Explicit render authority and technical master QA pass.
- [ ] Metadata and thumbnail are factual, non-sensational, current, and approved.
- [ ] Release-readiness has no stale, unlicensed, unresolved, or cross-track item.
- [ ] Upload packet remains blocked until a separate exact G09 publish approval.
- [ ] Correct account/channel, files, hashes, metadata, visibility, and schedule are bound before platform action.

### Disposition — leave blank

- Checklist record ID: `[BLANK]`
- Episode ID: `[BLANK]`
- Reviewer: `[BLANK]`
- Result: `[BLANK — NOT READY / READY FOR NEXT HUMAN GATE]`
- Blockers: `[BLANK]`
- Exact next allowed action: `[BLANK]`
- Approval reference: `[BLANK]`

Checking every box demonstrates readiness evidence only. It never substitutes for C3, C4, render, release-master, or publish approval.
