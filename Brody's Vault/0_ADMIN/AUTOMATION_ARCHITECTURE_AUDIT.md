# Cold Truth Automation Architecture Audit

**Audit date:** 2026-07-10  
**Scope:** backend orchestration only; no real case production work  
**Authority reviewed:** `AGENTS.md`, `WORKFLOW_PER_VIDEO.md`, `CONTENT_FORMAT_STANDARD.md`, six role files, six reusable skills, `Backlog.md`, `automation/cold_truth_pipeline.py`, `automation/README.md`, the locked Mia configuration, and existing JSON handoffs/manifests.

## Executive finding

The vault has strong editorial rules and several useful stage helpers, but it does not yet have an autonomous pipeline. `cold_truth_pipeline.py` writes isolated handoffs and can call Pexels search or ElevenLabs, yet it has no queue, durable run state, deterministic case selection, approval verification, dependency graph, stale-artifact invalidation, retry policy, assembly stage, render gate, or consistent manifest schema. Most real Jodi work was coordinated manually and reconstructed afterward in `direct_generation_manifest.json`.

The safe reset is a stateful orchestrator above the existing adapters. It must default to dry-run, hash every approved/input artifact, stop at exactly two human checkpoints, invalidate downstream work after upstream changes, and treat publishing as an unavailable capability until separately enabled.

## Existing agents and present behavior

| Agent | What it already does | Current automation level | Current handoff quality |
|---|---|---|---|
| Strategist | Finds/evaluates cases and applies the eight-minute viability gate. | Prompt/skill-driven. Batch intake has been performed manually. | Markdown ledgers, risk notes, viability assessments, and scorecards are useful but lack a shared JSON schema or queue status record. |
| Writer | Drafts source-bound long-form narration with B-roll markers. | Prompt/skill-driven; backend only writes `write.json` saying the skill is ready. | `write.json` is machine-readable but contains no input hashes, viability proof, output path, schema version, or completion result. |
| Editor | Checks tone, facts, pacing, repetition, and Narrative Coherence Gate. | Prompt/skill-driven. | Markdown outputs are reviewable, but paired outline/draft approval is not represented in a standard machine approval file. |
| Visual Producer | Converts approved narration into long-form shot requirements. | The skill is prompt-driven. Backend `visuals` estimates timing from text; `broll --execute` searches only. | Existing JSON is a plan, not WhisperX-timestamped sourcing or an asset-complete manifest. No download/license/integrity gate exists. |
| Shorts Editor | Produces standalone Shorts scripts and overlays for separate Orbital gameplay. | Prompt/skill-driven. | No standard per-Short JSON contract, audio/preflight linkage, overlay alignment record, gameplay license record, or assembly status. |
| Upload Manager | Produces titles, description, tags, thumbnail copy, and settings. | Backend generates a generic draft; skill work is prompt-driven. | JSON exists but includes placeholders and no source/script hash. It cannot be considered approved or publish-ready. |

## Automated versus manual stages

### Presently automated or callable

- Writing a minimal stage handoff JSON.
- Parsing the locked Mia voice preset from `NARRATION_VOICE.md`.
- Planning or executing one ElevenLabs narration call.
- Measuring actual audio duration with FFprobe and enforcing the long-form/Shorts runtime gates.
- Planning or executing a Pexels search request; no asset download or license record.
- Generating generic metadata, thumbnail prompts, and text-estimated visual timelines.
- Writing per-stage JSON files beneath a real case `Automation` folder.

### Presently manual or prompt-driven

- Reading and normalizing `Backlog.md`.
- Batch case discovery and research.
- Source validation and claim-ledger integrity review.
- Viability ranking and deterministic case selection.
- Creating the production package and canonical artifact paths.
- Running Writer and Editor and assembling the checkpoint packet.
- Recording paired script approval and verifying approved hashes.
- WhisperX alignment.
- Beat-level Pexels sourcing, actual downloads, asset suitability review, and licenses.
- Orbital gameplay acquisition/license verification.
- Long-form and Shorts assembly.
- Assembly approval and render authorization.
- Local render execution and post-render validation.
- Consistent manifest logging and downstream invalidation.
- Returning rejected/deferred cases to backlog without losing research.

## Machine-readable handoffs

### Existing machine-readable artifacts

- `write.json`: minimal stage/skill/source pointer.
- `voice.json`, `metadata.json`, `thumbnail.json`, `visuals.json`: stage-specific JSON with incompatible structures and no common envelope.
- `preflight.json`: strongest current artifact; records target format, exact narration path, measured duration, rule, flags, and `assembly_allowed`.
- `direct_generation_manifest.json`: valuable chronological record of manual work, but its 20 entries use inconsistent field names (`input`/`inputs`, `output`/`outputs`, optional verification/settings) and lack stable event IDs, hashes, outcomes, and a formal schema.

### Missing machine-readable guarantees

- `schema_version`, `run_id`, `case_id`, `stage`, `attempt`, timestamps, input hashes, output hashes, policy version, status, errors, and retryability in one common envelope.
- A queue record that differentiates discovered, researched, viable, selected, deferred, rejected, and returned-to-backlog cases.
- Approval files bound to exact reverse-outline, script, narration, and assembly hashes.
- A dependency registry showing which artifacts become stale after a revision.
- A source-verification result that the Writer can consume without interpreting prose.
- A complete asset manifest with provider IDs/URLs, local files, license/credit, hashes, dimensions, duration, track ownership, and review status.

## Places that currently require manual choice or instruction

1. Selecting how many cases to research.
2. Choosing a case after scorecards are produced.
3. Telling the Writer to start.
4. Telling the Editor to run and deciding whether its reverse outline is acceptable.
5. Manually authorizing voice, alignment, every visual-source pass, gameplay acquisition, assembly, and render.
6. Choosing substitutes when a stock search fails.
7. Detecting stale narration/timings after script changes.
8. Deciding whether an asset plan means “ready,” despite the locked rule requiring actual files.
9. Reconciling inconsistent stage artifacts and reconstructing the run manifest.

The intended model removes items 1–9 from normal operation except the two explicit approvals. Failures and unresolved sourcing gaps remain stop conditions, not new creative checkpoints.

## Missing components for autonomous operation

- Durable case queue and deterministic ranking policy.
- Research Verifier between Strategist and Writer.
- Versioned agent contracts and common handoff schema.
- Run-level state machine with allowed transitions.
- Artifact hashing, dependency graph, and stale invalidation.
- Idempotent stage cache and attempt/retry records.
- Script-approval and assembly-approval schemas.
- Approval-packet generators.
- Adapters for Writer/Editor execution, ElevenLabs, FFprobe, WhisperX, Pexels download/verification, Orbital-license registration, FCPXML assembly, and local render.
- Track-isolation validator proving no asset ID/path/hash is shared between long-form and Shorts.
- Asset-completion validator proving files exist and required license/credit records are present.
- Consistent append-only manifest and decision log.
- Explicit failure states and return-to-backlog behavior.
- Publishing capability flag that remains absent/false by default.

## Rule conflicts and outdated instructions discovered

- `ROLE_WRITER.md` still says 1,500–2,000 words/10–15 minutes and describes the old 800–1,200-word Short-Format rule. The locked standard is 1,150–1,450 words as a planning range and at least 480.000 seconds of actual approved narration.
- `ROLE_WRITER.md` permits researching from a case name, bypassing the vetted-ledger and viability gates.
- `ROLE_EDITOR.md` lacks the current mandatory reverse-outline, paired-approval, no-padding, and actual-duration gates found in the newer Editor skill.
- `ROLE_SHORTS_EDITOR.md` says to wait for Brody to choose moments, conflicting with the desired autonomous path between checkpoints.
- `ROLE_FILMER.md` is based on estimated timestamps and DaVinci instructions; the current production standard requires WhisperX-based timing, actual source files, licensing, and gap stops.
- `ROLE_UPLOAD_MANAGER.md` describes taking a finished video and preparing publishing settings but does not encode the absolute publishing prohibition.
- `automation/README.md` describes isolated stages and “Phase 2” rather than the two new checkpoints.
- Validation-case `visuals.json` contains legacy Minecraft/Subway language and text-estimated timings; it is not compliant evidence for the current Orbital/WhisperX workflow.

These conflicts are documented here. This reset adds enforceable contracts without silently rewriting the legacy role prose; a later documentation-normalization pass should reconcile those files against the locked skills and standard.

## Rules that must remain human-controlled or non-automated

- Human Checkpoint 1: paired approval of the exact reverse outline and full draft.
- Human Checkpoint 2: approval of exact unrendered long-form and Shorts assemblies and explicit local-render authorization.
- Any Short-Format or over-60-second Shorts exception.
- Any episode-level deviation from Mia’s preset.
- Any source-boundary expansion involving a suspect allegation, sensitive victim detail, disputed claim, or legal-risk judgment that the verifier cannot resolve.
- Acquisition of paid/licensed assets where purchase, login, or acceptance of terms is required.
- Enabling publishing mode, platform developer registration, OAuth consent, upload, scheduling, or publication.

## Safety conclusion

Autonomy is appropriate between the two checkpoints only when every stage operates under a validated contract. Missing sources, failed verification, under-minimum audio, unlicensed assets, unmatched beats, track sharing, hash mismatch, or adapter failure must stop the run. The orchestrator may retry deterministic/transient operations within policy; it may never invent, substitute loosely related media, weaken a source boundary, or bypass approval.
