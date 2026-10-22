# Episode workflow

[[00_START_HERE|Home]] → [[0_ADMIN/PROJECT_DASHBOARD|Dashboard]] → [[0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2|Working plan]] → [[0_ADMIN/ROLE_HUB|Roles]]

Use **Stage 1–8** for editorial/production order. **Phase 2** means Brody's explicit media-production authorization; it never means the research stage. Arrows show dependencies, not permissions.

## Stage 1 → Verify research and select one viable case

Start at [[1_IDEAS/RESEARCH_HUB|the research hub]]. The [[0_ADMIN/ROLE_STRATEGIST|Strategist]] reads underlying sources and records claim-level support, access dates, conflicts and exclusions. Use law-enforcement, charging-document or court corroboration for suspect claims. Compare evidence before promoting a candidate into an episode.

Record exactly one result: `Standard long-form viable`, `Short-Format exception — requires human approval`, or `Backlog — insufficient long-form material`. Writer work requires standard viability or the human-approved documented exception.

## Stage 2 → Draft a coherent story

The [[0_ADMIN/ROLE_WRITER|Writer]] uses the vetted ledger to create `Script_Draft.md` and a claim map. Normally 1,150–1,450 spoken words, with hook, setup, chronological events, evidence/investigation context, current status and respectful closing. The 8–10-minute target cannot be verified from word count. Never pad.

## Stage 3 → Edit and request paired human review

The [[0_ADMIN/ROLE_EDITOR|Editor]] checks facts and the complete spoken narrative, revising structure if necessary. Produce a reverse outline with purpose, ledger claim IDs, transition and exclusions for every section. Present that exact outline and full draft together. Stop for Brody's paired approval.

Only after approval may the approved draft become `Script_Final.md`. Bind the decision to exact inputs. A prior final filename or self-QA pass is insufficient.

## Stage 4 → Authorized narration and actual-audio preflight

Obtain explicit narration/Phase 2 scope before invoking the selected [[2_CHANNEL_SYSTEM/NARRATION_VOICE|Mia profile]]. Record tool, timestamp, script hash, provider/model/voice/settings, target format, attempt budget and every output path. No provider fallback or voice change without Brody's decision.

Measure the exact current narration audio using FFprobe. Long-form requires at least 480.000 seconds unless a valid human-approved Short-Format exception exists. Failed duration returns to evidence-based editorial revision and paired reapproval, not slowing or repetition. Follow [[0_ADMIN/CONTENT_FORMAT_STANDARD|the runtime rules]]. The old legacy CLI is quarantined; real canonical preflight integration remains an implementation task.

## Stage 5 → Align and prepare separate visuals

After the approved script and exact-audio preflight pass, align narration and prepare the [[0_ADMIN/ROLE_FILMER|long-form shot list]]. Download/source assets only within authorized production scope. Long-form uses case-appropriate B-roll and graphics with traceable rights.

After Stage 3, [[0_ADMIN/ROLE_SHORTS_EDITOR|Shorts editorial work]] may use the approved script and ledger; it does not require waiting for a released long-form video. Create 3–5 standalone Shorts for standard episodes, or 1–2 for approved Short-Format episodes. Each has separate narration and a separately licensed Orbital visual track. No long-form visual assets are shared.

Each track may be prepared independently. Record track-level asset preparation separately, but do not label the overall visual timeline ready until required Pexels clips are downloaded and the separately licensed or recorded Orbital gameplay exists, as required by `AGENTS.md`. Validate actual files, rights and cross-track isolation before assembly; the current synthetic-only checker cannot certify real assets.

## Stage 6 → Assemble and review locally

Require a current `Automation/preflight.json` with `assembly_allowed: true`, exact input identities, alignment, downloaded/verified assets and rights evidence. Assemble within explicit scope. Phase 2 authorization is required for rendering. Review technical timing and creative coherence, then record exact masters and QA. Passing a synthetic fixture is not a real master.

## Stage 7 → Package and publish only with explicit authority

The [[0_ADMIN/ROLE_UPLOAD_MANAGER|Upload Manager]] prepares separate metadata, source/rights credits and thumbnail briefs. Review the master, thumbnail and metadata. Obtain exact account/file/visibility/schedule authority before any upload or publication. Phase 2 rendering permission alone does not authorize publishing.

## Stage 8 → Review results

After an authorized release, record actual platform results and compare long-form and Shorts performance separately. Set review times or automation only when requested. Use evidence to improve story clarity and packaging; never weaken factual standards for engagement.

## State and revision rules

[[0_ADMIN/COLD_TRUTH_EXECUTION_STATE.json|Channel planning state]] is separate from the orchestrator's episode run state. Keep original paths for historical artifacts and approvals. An upstream change makes affected downstream script approvals, audio, alignment, preflight, visuals and masters stale. Revalidate exact dependencies before reuse.

See [[2_IN_PRODUCTION/PRODUCTION_HUB|the production hub]] for current editorial work and retained history, and [[0_ADMIN/PROJECT_REASSESSMENT_2026_10_16|the current assessment]] for implementation limitations.
