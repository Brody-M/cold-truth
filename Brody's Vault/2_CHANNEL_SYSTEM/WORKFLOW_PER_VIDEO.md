# WORKFLOW_PER_VIDEO

## System links

[[CHANNEL_SYSTEM]] · [[CONTENT_FORMAT_STANDARD]] · [[ROLE_STRATEGIST]] · [[ROLE_WRITER]] · [[ROLE_EDITOR]] · [[ROLE_FILMER]] · [[ROLE_SHORTS_EDITOR]] · [[ROLE_UPLOAD_MANAGER]]

## Finalized subagent chain

```text
Strategist → vetted ledger → viability gate → Writer draft → Editor reverse outline → HUMAN APPROVES OUTLINE + FULL DRAFT → Script_Final
                                                                                                                    ├→ Mia narration → audio preflight
                                                                                                                    ├→ Visual Producer → YouTube B-roll/case graphics
                                                                                                                    ├→ Upload Manager → Long-form upload package
                                                                                                                    └→ Shorts Editor → separate licensed Orbital track
```

The human-approved full draft becomes `Script_Final.md` only after its source-bound reverse outline is approved at the same checkpoint. That final script is the single factual source for both branches. Long-form uses relevant B-roll/case graphics; TikTok and Shorts use a separate licensed Orbital gameplay track behind factual overlays. The two visual pools never share assets.

## Phase 1 — Select the case

**Owner:** [[ROLE_STRATEGIST]] / `$cold-truth-strategist`  
**Input:** backlog or a case/region/time-period request.  
**Output:** ranked, verifiable ideas with hook, fit rationale, and risk flag; then one case marked for research in `1_IDEAS/Backlog.md`.

Reject overexposed cases, legally sensitive recent cases, cases with weak public sourcing, or cases that cannot be covered respectfully.

## Phase 2 — Research and outline

**Owner:** Human research review plus [[ROLE_STRATEGIST]] viability gate.  
**Input:** selected case and public sources.  
**Output:** `2_IN_PRODUCTION/[CASE]/Research_Source_Ledger.md` containing claim IDs, sources, chronology, investigation, present status, uncertainties, and exclusions; plus a recorded viability result.

No script proceeds while key claims are unverified or ambiguities are unflagged. Before Writer work, the Strategist must assess whether the vetted ledger can support a cohesive eight-minute episode without padding and record exactly one result:

- `Standard long-form viable`
- `Short-Format exception — requires human approval`
- `Backlog — insufficient long-form material`

Writer work is blocked unless standard viability passes or the human explicitly approves the documented Short-Format exception. Never force a thin case into long-form.

## Phase 3 — Write the long-form draft

**Owner:** [[ROLE_WRITER]] / `$cold-truth-writer`  
**Input:** research brief and any requested angle.  
**Output:** `Script_Draft.md`, normally 1,150–1,450 spoken words, with hook, essential setup, chronological events, evidence/investigation context, verified current status, closing, source/uncertainty flags, and non-graphic `[B-ROLL: ...]` markers.

Target 8–10 minutes and prefer 8:15–10:30, but treat word count only as a drafting aid. Add length only through distinct ledger-supported chronology, personal/routine context, evidence explanation, confirmed investigative action, or current status. Repetition, generic commentary, slowed narration, filler transitions, speculation, dramatization, and unsupported claims are prohibited padding.

The certified orchestrator owns the Writer handoff and records it in the run ledger. Do not invoke the quarantined legacy pipeline for a real case.

## Phase 4 — Edit and approve

**Owner:** [[ROLE_EDITOR]] / `$cold-truth-editor`  
**Input:** `Script_Draft.md`.  
**Output before human approval:** editorial notes, a source-bound reverse outline, and the full revised draft.  
**Output after paired human approval:** `Script_Final.md`.

Check factual attribution, timeline, natural narration, respectful tone, six-section structure, and B-roll placement. Before final approval, create a reverse outline that records each section's narrative purpose, supporting ledger claims, transition into the next section, and intentionally excluded material. The script must contain a purposeful hook, essential setup, chronological event narrative, investigation/evidence context, verified current status, and a respectful conclusion.

Disconnected fact-card writing fails editorial review even when every sentence is sourced. A repetition scan is required, but repetition cleanup alone cannot pass the script. A first-time background listener must be able to explain the complete story after one listen.

**Hard human checkpoint:** the human reviewer must approve the reverse outline and full draft together. Do not create `Script_Final.md` before that approval. Until the paired approval is explicit and the final script exists, do not generate narration, run alignment, derive Shorts, source visuals, assemble a timeline, or render media. The finalized script is the canonical source; do not independently alter facts in either visual branch.

Project narration must be projected at 8:00 or longer. A projection under 8:00 fails unless the human approves a documented Short-Format exception. Projection and word count do not replace the actual-audio preflight after Mia narration is generated.

The certified orchestrator owns the Editor handoff and paired-approval checkpoint. Do not invoke the quarantined legacy pipeline for a real case.

## Phase 5 — Create the narration request

**Owner:** ElevenLabs adapter.  
**Input:** `Script_Final.md`.  
**Output:** Mia narration plus an audio-measured `Automation/preflight.json`.

During Phase 1 this remains a planned request only. Even after general Phase 2 approval, voice generation remains blocked until the reverse outline and full draft have received explicit paired human approval and `Script_Final.md` exists. Declare `--target-format youtube-longform` for the narration branch.

After generation, run `preflight` against the exact current narration. FFprobe—not word count—measures duration. Audio below 480.000 seconds blocks alignment, visual sourcing, and assembly unless a valid human-approved `short-format` exception JSON is supplied. Audio from 480.000–494.999 seconds passes the release minimum but is flagged below the preferred range; 495.000–630.000 seconds is preferred; audio above 630.000 seconds receives an editorial-review flag. No video is rendered here.

## Phase 6A — Plan and source YouTube visuals

**Owner:** [[ROLE_FILMER]] / `$cold-truth-visual-producer`  
**Input:** `Script_Final.md`, current Mia narration, and matching `Automation/preflight.json` with `assembly_allowed: true`.  
**Output:** `Shot_List.md` with timestamps, narration cues, B-roll/case-graphic descriptions, Pexels search terms, durations, overlays, and pacing flags.

Only search or collect landscape B-roll/case graphics that support the narration. Never use Orbital gameplay in this branch. Refuse downstream visual sourcing when the exact current narration lacks a passing preflight. Use `broll` handoffs for Pexels searches; Phase 1 does not download or render media.

## Phase 6B — Plan TikTok/Shorts (separate visual branch)

**Owner:** [[ROLE_SHORTS_EDITOR]] / `$cold-truth-shorts-editor`  
**Input:** the completed long-form script, after long-form approval.  
**Output:** 3–5 standalone short scripts targeting 30–60 seconds of actual narration, each with a sub-15-word hook and `[OVERLAY: ...]` cues for every key fact.

Every short must use a completely separate licensed Orbital gameplay visual track. It must not reuse long-form Pexels clips, B-roll, case graphics, shots, or visual assets. Keep it source-backed; do not invite theories, imply suspects, make uncorroborated suspect claims, or add unsupported context. Actual narration may not exceed 60.000 seconds without valid `shorts-over-60` human approval metadata. Run the `shorts` preflight after narration generation.

## Phase 7 — Package metadata

**Owner:** [[ROLE_UPLOAD_MANAGER]] / `$cold-truth-upload-manager`  
**Input:** `Script_Final.md` and case summary.  
**Output:** three under-60-character titles, 150–250-word description, 15–20 tags, two thumbnail text options, and scheduled publish settings.

The certified orchestrator owns the metadata handoff after its prerequisites pass. The quarantined legacy pipeline cannot create canonical metadata state.

## Phase 8 — Prepare upload (blocked until Phase 2)

**Owner:** upload adapter + human final review.  
**Input:** approved metadata, final render, thumbnail, and OAuth authorization.  
**Output:** a validated upload manifest.

The certified orchestrator may prepare a blocked, local upload packet after release-readiness passes. The quarantined legacy pipeline cannot create a canonical upload manifest. Actual uploading, scheduling, rendering, and video generation start only after explicit Phase 2 approval.

## Per-video checklist

- [ ] Case is lesser-known, suitable, and supported by public sources.
- [ ] Research brief has sources and uncertainty flags.
- [ ] Strategist viability result is recorded from the vetted ledger; weak cases remain in backlog.
- [ ] Draft follows the Cold Truth structure and tone.
- [ ] Editor created a source-bound reverse outline with purpose, claim IDs, transitions, and exclusions for every section.
- [ ] Script contains hook, setup, chronological events, contextualized evidence/investigation, verified current status, and conclusion.
- [ ] Script reads as one cohesive spoken story rather than disconnected fact cards.
- [ ] Repetition scan is complete, but was not used as the sole approval criterion.
- [ ] Human approved the reverse outline and full draft together before `Script_Final.md` was created.
- [ ] Long-form narration declares `youtube-longform` and measures at least 480.000 seconds, or valid Short-Format approval metadata is attached.
- [ ] Runtime was verified from the actual Mia audio, not word count alone.
- [ ] Added duration uses distinct ledger-supported material and contains no padding.
- [ ] Long-form visual plan uses only B-roll/case graphics.
- [ ] Shorts narration targets 30–60 seconds and uses only separate licensed Orbital gameplay plus factual overlays.
- [ ] The two visual tracks share no assets.
- [ ] Metadata is accurate, searchable, and non-sensational.
- [ ] Phase 2 approval exists before any voice generation, media download, render, upload, or scheduling.

## Backend handoffs

## Permanent workflow rules

- **Research files:** `Research.md` and `Research_Source_Ledger.md` are both valid research inputs.
- **Claim threshold:** no suspect claim may appear unless corroborated by law enforcement, a charging document, or a court finding. Private-investigator claims, tips, rumors, and speculation may be mentioned only when explicitly labeled unverified.
- **Long-form runtime:** target 8–10 minutes and prefer 8:15–10:30. Release minimum: at least 480.000 seconds of actual approved narration audio. Draft normally at 1,150–1,450 spoken words, but never use word count as duration verification.
- **Short-Format:** projected or measured narration below 8:00 is blocked unless explicit human approval metadata records a `short-format` exception. Label approved exceptions `Short-Format` in `Production_Summary.md`.
- **No padding:** add duration only through distinct verified chronology, relevant personal/routine context, evidence explanation, confirmed investigative action, or current status. Prohibit repeated facts/evidence, generic commentary, slowed narration, filler transitions, speculation, dramatization, and unsupported claims.
- **Voice:** use the locked Mia preset in [[NARRATION_VOICE]] unless an episode-level exception is documented in an Automation manifest.
- **Audio revision safeguard:** any time a long-form or Shorts script is revised after audio generation, regenerate the corresponding audio and explicitly verify it against the current script before assembly. Stale audio may never be assembled against an updated script.
- **Shorts quantity:** 1-2 strong Shorts are acceptable for a Short-Format episode; standard episodes require 3-5.
- **Shorts format:** target 30–60 seconds, block audio over 60.000 seconds without valid human approval metadata, use a standalone source-backed script, and use a completely separate licensed Orbital gameplay track. No theory invitations, suspect implication, or unsupported context.
- **Direct/manual generation:** when a tool outside the certified orchestrator is explicitly authorized, create `2_IN_PRODUCTION/[CASE]/Automation/direct_generation_manifest.json` recording the tool, timestamp, settings, and every output path.
- **Visual readiness:** a timeline is not `ready` in `Production_Summary.md` until its Pexels clips are downloaded and its separately licensed Orbital gameplay exists. The two tracks may never share assets.
- **Narrative Coherence Gate:** before final-script creation, the Editor must create a source-bound reverse outline. The human must approve that outline and the full draft together. Disconnected fact-card writing fails even when sourced, and repetition cleanup alone is insufficient. No `Script_Final.md` or media work may begin before paired approval.
- **Strategist viability:** before Writer work, classify the vetted ledger as `Standard long-form viable`, `Short-Format exception — requires human approval`, or `Backlog — insufficient long-form material`.
- **Runtime preflight:** assembly requires a matching `Automation/preflight.json` for the exact current audio with `assembly_allowed: true`. The preflight uses FFprobe audio duration and never treats word count as verification.

See [[CONTENT_FORMAT_STANDARD]] and `automation/README.md`. Only the certified orchestrator may advance canonical state or write canonical machine handoffs under `2_IN_PRODUCTION/[CASE]/Automation/`. API keys stay outside this vault and require a separately certified adapter and explicit execution authority.

## Backend planning extensions

### Narration voice configuration

The planned narration voice is stored in [[NARRATION_VOICE]]. A future certified narration adapter must bind the exact approved voice ID without delegating configuration lookup to the quarantined legacy helper. Explicitly authorized short comparison clips are permitted for voice selection; they are not episode narration and do not authorize a final render.

### Thumbnail prompt package (no publication)

Thumbnail prompt planning must run through the certified orchestrator or a separately authorized direct-generation manifest. The quarantined legacy helper may produce only isolated synthetic fixture previews outside the workspace. Generated images still require explicit authorization and the backend never publishes them.

### Two-track edit plan (no render)

The certified orchestrator creates the separate no-render visual plans from approved, hash-bound inputs. The YouTube timeline contains landscape B-roll/case-graphic references only; the Shorts timeline contains only a separately licensed Orbital gameplay reference plus factual overlay text. The plan declares `shared_assets: false`; it does not download footage or render video.

### Metadata handoff

The certified orchestrator creates an editable, fact-check-required metadata package only after its prerequisites pass. Resolve location/year placeholders from the approved research ledger before any upload preparation.
