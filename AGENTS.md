# Cold Truth — Agent Guide

## Project overview

Cold Truth is a faceless true-crime YouTube channel. Episodes use AI narration and are repurposed into TikTok and YouTube Shorts. The long-form and short-form versions are related editorially, but use different visual tracks.

## Non-negotiable visual rule

- **YouTube long-form:** use case-appropriate B-roll and case graphics.
- **TikTok/Shorts:** use a separately licensed Orbital gameplay background track with factual text overlays.
- Never reuse or share visual assets between those two tracks.
- Do not render video, generate final visual media, or upload unless the user explicitly authorizes Phase 2.

## Non-negotiable editorial and production rules

- **Audience:** women 25-45, especially background listeners and mothers who want calm, reliable storytelling.
- **Source threshold:** no suspect claim may appear in narration unless it is corroborated by law enforcement, a charging document, or a court finding. Private-investigator claims, tips, rumors, and speculation may appear only when explicitly labeled unverified.
- **Long-form runtime:** target 8-10 minutes and prefer 8:15-10:30. Release minimum: at least 480.000 seconds of actual approved narration audio. Draft normally at 1,150-1,450 spoken words, but word count never verifies duration.
- **Short-Format exception:** narration below 8:00 is blocked unless the human explicitly approves a machine-documented `short-format` exception. Label the episode `Short-Format` in its Production Summary.
- **No padding:** added runtime must come from distinct, verified ledger-supported chronology, personal/routine context, evidence explanation, confirmed investigative action, or current status. Never pad with repetition, generic commentary, slowed narration, filler transitions, speculation, dramatization, or unsupported claims.
- **Shorts quantity:** 1-2 strong Shorts are acceptable for a Short-Format episode; standard episodes require 3-5.
- **Shorts runtime:** target 30-60 seconds and never exceed 60.000 seconds without explicit machine-documented human approval. Shorts use a standalone source-backed script and a completely separate licensed Orbital gameplay track; they may not invite theories or add unsupported context.
- **Direct generation:** direct/manual tooling is permitted only when an Automation manifest records the tool, timestamp, settings, and every output path.
- **Visual completion:** a visual timeline is not `ready` until its Pexels clips are downloaded and its separately licensed or recorded Shorts gameplay exists.

## Narrative Coherence Gate

- Before any final-script approval, the Editor must create a source-bound reverse outline that identifies the purpose, verified claim support, and transition for every story section.
- The human reviewer must approve the reverse outline and full draft together before `Script_Final.md` is created. Approval of facts, a prior draft, or a repetition pass alone does not satisfy this gate.
- Every long-form script must contain a purposeful hook, essential setup, chronological event narrative, investigation/evidence context that explains why each detail matters, verified current status, and a respectful conclusion.
- Disconnected fact-card writing fails editorial review even when every individual statement is sourced.
- Repetition scanning alone cannot pass editorial review. The script must also work as one understandable spoken story for a first-time background listener.
- No narration, forced alignment, visual sourcing, Shorts derivation, assembly, or rendering may begin until the reverse outline and full draft receive explicit paired human approval and the approved `Script_Final.md` exists.

## Strategist viability gate

- Before Writer work begins, the Strategist must determine whether the vetted research ledger can support a cohesive eight-minute episode without padding.
- Record exactly one result: `Standard long-form viable`, `Short-Format exception — requires human approval`, or `Backlog — insufficient long-form material`.
- Do not force a weak or thinly sourced case into long-form. Writer work is blocked unless standard viability passes or the human approves the documented exception.

## Runtime preflight

- Every narration branch must declare `youtube-longform` or `shorts`.
- After narration generation, run the machine preflight against the exact current audio. Long-form audio below 480.000 seconds blocks downstream production unless valid Short-Format approval metadata is present.
- Word count and projected reading time are editorial aids only; actual audio duration is authoritative.
- Assembly requires a matching `Automation/preflight.json` with `assembly_allowed: true`.
- See [CONTENT_FORMAT_STANDARD](Brody's Vault/0_ADMIN/CONTENT_FORMAT_STANDARD.md) for the locked rules and exception schema.

## Subagent definitions

- [ROLE_STRATEGIST](Brody's Vault/0_ADMIN/ROLE_STRATEGIST.md) — case research, ranking, evaluation, calendars.
- [ROLE_WRITER](Brody's Vault/0_ADMIN/ROLE_WRITER.md) — long-form narration drafts.
- [ROLE_EDITOR](Brody's Vault/0_ADMIN/ROLE_EDITOR.md) — factual, tonal, and pacing edits.
- [ROLE_FILMER](Brody's Vault/0_ADMIN/ROLE_FILMER.md) — long-form B-roll and case-graphics shot lists.
- [ROLE_SHORTS_EDITOR](Brody's Vault/0_ADMIN/ROLE_SHORTS_EDITOR.md) — short extraction and vertical text-overlay scripts.
- [ROLE_UPLOAD_MANAGER](Brody's Vault/0_ADMIN/ROLE_UPLOAD_MANAGER.md) — titles, descriptions, tags, thumbnails, publish settings.

Reusable Codex skills live in `/skills`; use the appropriate one for each stage.
