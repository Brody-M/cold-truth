# Editorial workflow

## The standard path

Cold Truth produces source-backed, respectful true-crime stories. The [working plan](<../Brody's Vault/0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md>) defines current priorities; the [vault workflow](<../Brody's Vault/2_CHANNEL_SYSTEM/WORKFLOW_PER_VIDEO.md>) is the detailed stage reference. “Phase 2” refers only to explicit media-production authorization.

| Stage | Owner | Key output | Gate |
| --- | --- | --- | --- |
| 1. Research and viability | Strategist | Verified ledger, risk notes, one viability result | Standard long-form, approved exception, or backlog. |
| 2. Draft | Writer | Cohesive full draft and claim map | Distinct, ledger-supported material only. |
| 3. Editorial and human review | Editor + Brody | Reverse outline and full draft approved together | Only then create the canonical final script. |
| 4. Authorized narration and preflight | Narration operator | Exact audio and measured-duration record | Explicit generation scope; required runtime and exact inputs. |
| 5. Alignment and visuals | Visual Producer / Shorts Editor | Separate plans and verified local assets | Production scope, current preflight, licenses and no shared visuals. |
| 6. Assembly and review | Assembly operator + Brody | Reviewable local masters and QA | Current prerequisites; explicit Phase 2 for render. |
| 7. Packaging and publishing | Upload Manager + Brody | Reviewed metadata, thumbnail and exact publish packet | Separate publishing authority for the exact account/files/settings. |
| 8. Results review | Strategist | Actual platform observations | Keep track metrics separate; no unsupported performance claims. |

Shorts scripts may be derived after Stage 3 from the approved script and vetted ledger. Their media remains separately authorized. Real canonical audio-preflight integration is still missing; the legacy helper's CLI is fixture-only and must not be used to write real episode state.

## Research and viability

Every suspect-related claim needs corroboration from law enforcement, a charging document, or a court finding. Private-investigator claims, tips, rumors, and speculation may appear only when clearly identified as unverified.

Before writing begins, the Strategist records exactly one result:

- `Standard long-form viable`
- `Short-Format exception — requires human approval`
- `Backlog — insufficient long-form material`

The goal is to avoid turning a thin case into a padded video. A short-form exception is an explicit human decision, not a workaround for incomplete research.

## Narrative coherence gate

The Editor builds a reverse outline before final approval. Each section identifies:

1. Its narrative purpose.
2. The source-ledger claims supporting it.
3. The transition to the next section.
4. Facts deliberately excluded because they are unsupported, repetitive, or unhelpful.

The human reviewer then approves the reverse outline and full draft together. Until that happens, `Script_Final.md`, narration, visuals, Shorts derivation, assembly, and rendering are blocked.

## Format and runtime rules

Long-form work declares `youtube-longform`; Shorts declares `shorts`.

- **Long-form:** target 8–10 minutes; actual approved narration audio must be at least 480.000 seconds unless valid `short-format` approval metadata exists.
- **Shorts:** target 30–60 seconds; audio over 60.000 seconds requires `shorts-over-60` approval metadata.
- **No padding:** duration may come only from distinct verified chronology, relevant context, evidence explanation, confirmed investigative actions, or current status.

The measured duration of the current audio is authoritative. Word count and estimated reading time are planning aids only.

## Visual isolation

Long-form uses B-roll and case graphics. Shorts use separately licensed Orbital gameplay and factual overlays. The branches may never share visual assets—even when both tell the same story.

The visual plan is not ready until its required materials exist, and assembly requires a matching `Automation/preflight.json` that permits it.

## Operational status

This repository documents and validates the process. It does not grant production authority. Any real narration, media download, rendering, upload, or scheduling remains subject to explicit human authorization and the controls in [`CONTENT_FORMAT_STANDARD.md`](<../Brody's Vault/0_ADMIN/CONTENT_FORMAT_STANDARD.md>).
