# Editorial workflow

## The standard path

Cold Truth produces source-backed, respectful true-crime stories. A case advances only when its evidence, narrative purpose, and approvals support the next stage.

| Stage | Owner | Key output | Gate |
| --- | --- | --- | --- |
| 1. Research | Strategist | Source ledger, risk notes, viability assessment | Claims are sourced and uncertainty is labeled. |
| 2. Viability | Strategist | One required classification | Standard long-form, human-approved Short-Format exception, or backlog. |
| 3. Draft | Writer | Cohesive long-form draft | Distinct, ledger-supported story material only. |
| 4. Editorial review | Editor | Reverse outline, factual and narrative review | Every section has purpose, sources, and a transition. |
| 5. Final script | Human reviewer | Paired approval + `Script_Final.md` | The outline and full draft are approved together. |
| 6. Narration preflight | Narration adapter | Current-audio `preflight.json` | Exact audio meets format duration rules. |
| 7. Visual planning | Visual Producer / Shorts Editor | Separate long-form and Shorts plans | No cross-track visual assets. |
| 8. Metadata | Upload Manager | Editable local package | Accurate and non-sensational. |
| 9. Production action | Human-authorized tools | Media, render, or upload packet | Explicit Phase 2 / execution authority required. |

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
